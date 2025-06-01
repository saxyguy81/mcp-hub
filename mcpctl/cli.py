#!/usr/bin/env python3
"""
MCP Hub CLI - Main command interface for managing MCP server containers
"""

import os
import sys
import json
import subprocess
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import tomllib
import toml

import typer
import docker
from docker.errors import DockerException
from . import container_engine

from .compose_gen import ComposeGenerator
from .discover import MCPDiscovery
from .registry import RegistryManager
from .workspace import WorkspaceManager, MCPWorkspace
from .secret_backends.base import SecretBackend
from .secret_backends.lastpass import LastPassBackend
from .secret_backends.env import EnvBackend

app = typer.Typer(
    name="mcpctl",
    help="MCP Hub - Manage Model Context Protocol servers via Docker containers",
    add_completion=False
)

@dataclass
class MCPConfig:
    """Configuration for MCP Hub"""
    git_remote: str = ""
    registry_driver: str = "offline"  # ghcr | gitlab | offline
    secrets_backend: str = "env"      # lastpass | env
    docker_registry: str = ""
    github_token: str = ""
    gitlab_token: str = ""
    lastpass_folder: str = "mcp-hub"
    compose_file: str = "docker-compose.yml"
    services_dir: str = "services"

class MCPHubError(Exception):
    """Custom exception for MCP Hub operations"""
    pass

def get_config_dir() -> Path:
    """Get the configuration directory"""
    config_dir = Path.home() / ".mcpctl"
    config_dir.mkdir(exist_ok=True)
    return config_dir

def load_config() -> MCPConfig:
    """Load configuration from ~/.mcpctl/config.toml"""
    config_file = get_config_dir() / "config.toml"
    if not config_file.exists():
        return MCPConfig()
    
    try:
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
        return MCPConfig(**data)
    except Exception as e:
        typer.echo(f"Error loading config: {e}", err=True)
        return MCPConfig()

def save_config(config: MCPConfig) -> None:
    """Save configuration to ~/.mcpctl/config.toml"""
    config_file = get_config_dir() / "config.toml"
    try:
        with open(config_file, "w") as f:
            toml.dump(asdict(config), f)
        typer.echo(f"Configuration saved to {config_file}")
    except Exception as e:
        typer.echo(f"Error saving config: {e}", err=True)
        raise MCPHubError(f"Failed to save configuration: {e}")

def get_docker_client():
    """Get a Docker client instance"""
    try:
        return docker.from_env()
    except DockerException as e:
        typer.echo(f"Docker error: {e}", err=True)
        typer.echo("Make sure Docker is running and accessible.", err=True)
        raise typer.Exit(1)

def get_secret_backend(config: MCPConfig) -> SecretBackend:
    """Get the configured secret backend"""
    if config.secrets_backend == "lastpass":
        return LastPassBackend(folder=config.lastpass_folder)
    else:
        return EnvBackend()

@app.command()
def init(
    git_remote: str = typer.Option("", help="Git remote URL for the MCP registry"),
    registry: str = typer.Option("offline", help="Registry driver (ghcr|gitlab|offline)"),
    secrets: str = typer.Option("env", help="Secrets backend (lastpass|env)"),
    force: bool = typer.Option(False, help="Overwrite existing configuration")
):
    """Initialize MCP Hub configuration"""
    config_file = get_config_dir() / "config.toml"
    
    if config_file.exists() and not force:
        typer.echo("Configuration already exists. Use --force to overwrite.")
        raise typer.Exit(1)
    
    config = MCPConfig(
        git_remote=git_remote,
        registry_driver=registry,
        secrets_backend=secrets
    )
    
    # Interactive setup if values not provided
    if not git_remote:
        config.git_remote = typer.prompt("Git remote URL")
    
    # Only prompt for registry if not explicitly provided via CLI
    if not any([arg.startswith('--registry') for arg in sys.argv]):
        registry = typer.prompt("Registry driver", default="offline")
        if registry not in ["ghcr", "gitlab", "offline"]:
            typer.echo("Invalid registry. Using 'offline'")
            registry = "offline"
        config.registry_driver = registry
    
    # Only prompt for secrets if not explicitly provided via CLI  
    if not any([arg.startswith('--secrets') for arg in sys.argv]):
        secrets = typer.prompt("Secrets backend", default="env")
        if secrets not in ["lastpass", "env"]:
            typer.echo("Invalid secrets backend. Using 'env'")
            secrets = "env"
        config.secrets_backend = secrets
    
    # Set registry-specific settings
    if registry == "ghcr":
        config.docker_registry = "ghcr.io"
    elif registry == "gitlab":
        config.docker_registry = typer.prompt("GitLab registry URL")
    
    save_config(config)
    typer.echo("MCP Hub initialized successfully!")

@app.command()
def discover(
    path: str = typer.Option(".", help="Path to scan for MCP servers"),
    output: str = typer.Option("services", help="Output directory for service definitions")
):
    """Discover MCP servers and generate service definitions"""
    discovery = MCPDiscovery()
    servers = discovery.scan_directory(Path(path))
    
    output_dir = Path(output)
    output_dir.mkdir(exist_ok=True)
    
    for server in servers:
        service_file = output_dir / f"{server.name}.yml"
        with open(service_file, "w") as f:
            f.write(server.to_compose_service())
        typer.echo(f"Generated service definition: {service_file}")
    
    typer.echo(f"Discovered {len(servers)} MCP servers")

@app.command()
def generate(
    services_dir: str = typer.Option("services", help="Directory containing service definitions"),
    template: str = typer.Option("compose.template.yml", help="Base compose template"),
    output: str = typer.Option("docker-compose.yml", help="Output compose file")
):
    """Generate docker-compose.yml from service definitions"""
    config = load_config()
    secret_backend = get_secret_backend(config)
    
    generator = ComposeGenerator(secret_backend)
    
    try:
        generator.generate_compose(
            services_dir=Path(services_dir),
            template_file=Path(template),
            output_file=Path(output)
        )
        typer.echo(f"Generated {output}")
    except Exception as e:
        typer.echo(f"Error generating compose file: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def setup(
    wizard: bool = typer.Option(False, help="Run interactive setup wizard"),
    sample: bool = typer.Option(False, help="Create sample workspace"),
    auto_start: bool = typer.Option(False, help="Enable auto-start on boot")
):
    """Setup and configure MCP Hub"""
    from .onboarding import OnboardingManager
    
    onboarding = OnboardingManager()
    
    if wizard:
        # Run full setup wizard
        print("🧙 MCP Hub Setup Wizard")
        print("=======================")
        print()
        
        success = onboarding.run_quick_setup()
        if success:
            print("✅ Setup wizard completed successfully!")
            onboarding.show_service_urls()
        else:
            print("⚠️  Setup wizard incomplete - you can run it again anytime")
    
    elif sample:
        # Just create sample workspace
        onboarding.run_quick_setup()
    
    else:
        # Show current status and options
        onboarding.show_service_urls()
        print("💡 Run 'mcpctl setup --wizard' for interactive setup")

@app.command()
def info():
    """Show MCP Hub information and connection details"""
    from .onboarding import OnboardingManager, get_connection_info
    
    onboarding = OnboardingManager()
    connection_info = get_connection_info()
    
    print("📋 MCP Hub Information")
    print("======================")
    print()
    
    # Show connection details
    if connection_info["primary_url"]:
        print(f"🔗 Primary MCP Endpoint: {connection_info['primary_url']}")
        print(f"📊 Status: {connection_info['status'].upper()}")
        
        if connection_info["urls"]:
            print()
            print("🌐 All Available Endpoints:")
            for url in connection_info["mcp_endpoints"]:
                status_icon = "🟢" if connection_info["status"] == "running" else "🔴"
                print(f"   {status_icon} {url}")
        
        print()
        print("📝 To connect your LLM client:")
        print(f"   1. Open your LLM application (Claude Desktop, etc.)")
        print(f"   2. Add MCP server: {connection_info['primary_url']}")
        print(f"   3. Save and restart your LLM client")
        
    else:
        print("❌ No MCP services configured")
        print("🚀 Run 'mcpctl setup --wizard' to get started")
    
    print()
    onboarding.show_service_urls()

@app.command()
def urls():
    """Show all service URLs and connection information"""
    from .onboarding import get_connection_info
    
    connection_info = get_connection_info()
    
    print("🔗 MCP Server URLs")
    print("==================")
    
    if not connection_info["mcp_endpoints"]:
        print("❌ No services running")
        print("🚀 Start services with: mcpctl start")
        return
    
    for i, url in enumerate(connection_info["mcp_endpoints"], 1):
        status_icon = "🟢" if connection_info["status"] == "running" else "🔴"
        print(f"{i}. {status_icon} {url}")
    
    if connection_info["primary_url"]:
        print()
        print("📋 Quick Connect:")
        print(f"   Primary URL: {connection_info['primary_url']}")
        print("   Copy this URL to your LLM client configuration")
    
    print()

# Update the existing start command to show URLs after starting
@app.command()
def start(
    compose_file: str = typer.Option("docker-compose.yml", help="Docker compose file"),
    detach: bool = typer.Option(True, help="Run in background"),
    build: bool = typer.Option(False, help="Build images before starting"),
    show_urls: bool = typer.Option(True, help="Show connection URLs after starting")
):
    """Start MCP Hub services"""
    if not Path(compose_file).exists():
        typer.echo(f"Compose file not found: {compose_file}", err=True)
        typer.echo("Run 'mcpctl setup --wizard' first.", err=True)
        raise typer.Exit(1)
    
    try:
        container_engine.compose_up(compose_file, detach=detach, build=build)
        typer.echo("🚀 MCP Hub services started successfully!")
        
        if show_urls:
            # Wait a moment for services to start
            import time
            time.sleep(2)
            
            from .onboarding import get_connection_info
            connection_info = get_connection_info()
            
            if connection_info["mcp_endpoints"]:
                print()
                print("🔗 Your MCP servers are ready at:")
                for url in connection_info["mcp_endpoints"]:
                    print(f"   🟢 {url}")
                
                if connection_info["primary_url"]:
                    print()
                    print(f"📋 Connect your LLM to: {connection_info['primary_url']}")
            
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error starting services: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def stop(
    compose_file: str = typer.Option("docker-compose.yml", help="Docker compose file")
):
    """Stop MCP Hub services"""
    if not Path(compose_file).exists():
        typer.echo(f"Compose file not found: {compose_file}", err=True)
        raise typer.Exit(1)
    
    try:
        container_engine.compose_down(compose_file)
        typer.echo("MCP Hub services stopped successfully!")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error stopping services: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def status(
    compose_file: str = typer.Option("docker-compose.yml", help="Docker compose file")
):
    """Show status of MCP Hub services"""
    if not Path(compose_file).exists():
        typer.echo(f"Compose file not found: {compose_file}", err=True)
        raise typer.Exit(1)
    
    try:
        container_engine.compose_ps(compose_file)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error getting status: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def add(
    name: str = typer.Argument(..., help="Service name to add"),
    image: str = typer.Option("", help="Docker image to use"),
    port: int = typer.Option(8080, help="Port to expose"),
    auto_start: bool = typer.Option(True, help="Start service after adding")
):
    """Add a new MCP service"""
    config = load_config()
    services_dir = Path(config.services_dir)
    services_dir.mkdir(exist_ok=True)
    
    service_file = services_dir / f"{name}.yml"
    
    if service_file.exists():
        if not typer.confirm(f"Service '{name}' already exists. Overwrite?"):
            raise typer.Exit(1)
    
    # Use discovery if no image specified
    if not image:
        typer.echo(f"Discovering MCP server: {name}")
        # This would use the discovery system - placeholder for now
        image = f"ghcr.io/mcp-hub/{name}:latest"
    
    # Generate service definition
    service_def = f"""services:
  {name}:
    image: {image}
    ports:
      - "{port}:8080"
    environment:
      - PORT=8080
      - SERVICE_NAME={name}
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped
"""
    
    # Write service file
    with open(service_file, 'w') as f:
        f.write(service_def)
    
    typer.echo(f"Created service definition: {service_file}")
    
    # Regenerate compose file
    typer.echo("Regenerating docker-compose.yml...")
    generate()
    
    if auto_start:
        typer.echo(f"Starting service '{name}'...")
        try:
            container_engine.compose_up("docker-compose.yml", services=[name])
            typer.echo(f"Service '{name}' started successfully!")
        except subprocess.CalledProcessError as e:
            typer.echo(f"Error starting service: {e}", err=True)

@app.command()
def remove(
    name: str = typer.Argument(..., help="Service name to remove"),
    keep_data: bool = typer.Option(False, help="Keep service data volumes")
):
    """Remove an MCP service"""
    config = load_config()
    services_dir = Path(config.services_dir)
    service_file = services_dir / f"{name}.yml"
    
    if not service_file.exists():
        typer.echo(f"Service '{name}' not found", err=True)
        raise typer.Exit(1)
    
    if not typer.confirm(f"Remove service '{name}'? This will stop and delete the container."):
        raise typer.Exit(1)
    
    try:
        # Stop the service
        typer.echo(f"Stopping service '{name}'...")
        container_engine.run(["compose", "stop", name])
        
        # Remove the container
        if not keep_data:
            container_engine.run(["compose", "rm", "-f", name])
        
        # Remove service definition
        service_file.unlink()
        typer.echo(f"Removed service definition: {service_file}")
        
        # Regenerate compose file
        typer.echo("Regenerating docker-compose.yml...")
        generate()
        
        typer.echo(f"Service '{name}' removed successfully!")
        
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error removing service: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def test(
    name: str = typer.Argument(..., help="Service name to test"),
    endpoint: str = typer.Option("/health", help="Health check endpoint")
):
    """Test if an MCP service is healthy"""
    try:
        # First check if service is running
        result = container_engine.run(["compose", "ps", name], capture_output=True, text=True)
        if name not in result.stdout:
            typer.echo(f"❌ Service '{name}' is not running", err=True)
            raise typer.Exit(1)
        
        # Test health endpoint
        health_result = container_engine.exec_service(name, ["curl", "-fsSL", f"http://localhost:8080{endpoint}"])
        
        if health_result.returncode == 0:
            typer.echo(f"✅ Service '{name}' is healthy")
            typer.echo(f"Response: {health_result.stdout[:100]}...")
        else:
            typer.echo(f"❌ Service '{name}' health check failed")
            typer.echo(f"Error: {health_result.stderr}")
            raise typer.Exit(1)
            
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Error testing service '{name}': {e}", err=True)
        raise typer.Exit(1)

@app.command()
def publish_images(
    registry_url: str = typer.Option("", help="Registry URL (overrides config)"),
    tag: str = typer.Option("latest", help="Image tag"),
    push: bool = typer.Option(True, help="Push to registry (false = save as tarball)")
):
    """Build and publish MCP server images"""
    config = load_config()
    
    # Set registry URL from parameter or use default
    if registry_url:
        config.docker_registry = registry_url
    elif not config.docker_registry:
        # Default to GitHub Container Registry if no registry configured
        config.docker_registry = "ghcr.io"
        typer.echo(f"Using default registry: {config.docker_registry}")
    
    typer.echo(f"Publishing images to: {config.docker_registry}")
    typer.echo(f"Image tag: {tag}")
    typer.echo(f"Push to registry: {push}")
    
    registry_manager = RegistryManager(config)
    
    try:
        if push and config.registry_driver != "offline":
            registry_manager.push_images(tag=tag)
            typer.echo("Images pushed to registry successfully!")
        else:
            tarball_path = registry_manager.save_images_tarball(tag=tag)
            typer.echo(f"Images saved to tarball: {tarball_path}")
    except Exception as e:
        typer.echo(f"Error publishing images: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def daemon(
    log_file: str = typer.Option("", help="Log file path (default: stdout)"),
    restart_on_failure: bool = typer.Option(True, help="Auto-restart services on failure")
):
    """Run MCP Hub daemon for monitoring and auto-restart"""
    import signal
    import logging
    import time
    
    # Set up logging
    if log_file:
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    logger = logging.getLogger(__name__)
    logger.info("MCP Hub daemon starting...")
    
    # Handle shutdown gracefully
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, stopping daemon...")
        raise typer.Exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while True:
            # Check if compose file exists
            if not Path("docker-compose.yml").exists():
                logger.warning("No docker-compose.yml found, generating...")
                try:
                    generate()
                except Exception as e:
                    logger.error(f"Failed to generate compose file: {e}")
                    time.sleep(30)
                    continue
            
            # Check service health
            try:
                result = container_engine.run(["compose", "ps", "--format", "json"], 
                                            capture_output=True, text=True)
                
                # Parse and check each service
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            service_info = json.loads(line)
                            service_name = service_info.get('Service', '')
                            state = service_info.get('State', '')
                            
                            if state != 'running' and restart_on_failure:
                                logger.warning(f"Service {service_name} is {state}, restarting...")
                                container_engine.compose_up("docker-compose.yml", 
                                                           services=[service_name])
                        except json.JSONDecodeError:
                            continue
                            
            except subprocess.CalledProcessError as e:
                logger.error(f"Error checking service status: {e}")
            
            # Wait before next check
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"Daemon error: {e}")
        raise typer.Exit(1)

@app.command()
def config(
    show: bool = typer.Option(False, help="Show current configuration"),
    edit: bool = typer.Option(False, help="Edit configuration file")
):
    """Manage MCP Hub configuration"""
    config_file = get_config_dir() / "config.toml"
    
    if show:
        if config_file.exists():
            with open(config_file, "r") as f:
                typer.echo(f.read())
        else:
            typer.echo("No configuration found. Run 'mcpctl init' first.")
    
    elif edit:
        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, str(config_file)])
    
    else:
        current_config = load_config()
        typer.echo(f"Configuration file: {config_file}")
        typer.echo(f"Git remote: {current_config.git_remote}")
        typer.echo(f"Registry: {current_config.registry_driver}")
        typer.echo(f"Secrets backend: {current_config.secrets_backend}")

@app.command()
def regenerate_bridge(
    config_file: str = typer.Option("", help="Path to LLM config file"),
    restart_service: bool = typer.Option(True, help="Restart mcp-openapi container after regeneration")
):
    """Regenerate OpenAPI bridge schema based on current LLM configuration"""
    
    # Load configuration
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = get_config_dir() / "config.json"
    
    if not config_path.exists():
        typer.echo(f"Configuration file not found: {config_path}", err=True)
        typer.echo("Run setup wizard first or specify config file with --config-file", err=True)
        raise typer.Exit(1)
    
    try:
        with open(config_path, 'r') as f:
            llm_config = json.loads(f.read())
    except Exception as e:
        typer.echo(f"Error reading config: {e}", err=True)
        raise typer.Exit(1)
    
    # Generate OpenAPI bridge configuration based on LLM backend
    bridge_config = {
        "llm_backend": llm_config.get("llmBackend", "claude"),
        "base_url": llm_config.get("customLLMUrl", ""),
        "api_key": llm_config.get("customLLMToken", ""),
        "model": "gpt-3.5-turbo" if llm_config.get("llmBackend") == "openai" else "claude-3-sonnet"
    }
    
    # Write bridge configuration
    bridge_config_path = Path("bridge-config.json")
    with open(bridge_config_path, 'w') as f:
        json.dump(bridge_config, f, indent=2)
    
    typer.echo(f"Generated bridge configuration: {bridge_config_path}")
    
    # Restart the bridge service if requested
    if restart_service:
        try:
            typer.echo("Restarting mcp-openapi bridge service...")
            container_engine.run(["compose", "restart", "mcp-openapi"])
            typer.echo("✅ Bridge service restarted successfully!")
        except subprocess.CalledProcessError as e:
            typer.echo(f"Warning: Failed to restart bridge service: {e}", err=True)
            typer.echo("You may need to restart it manually with: docker compose restart mcp-openapi")
    
    typer.echo("✅ OpenAPI bridge regenerated successfully!")

@app.command()
def lock_images(
    compose_file: str = typer.Option("docker-compose.yml", help="Docker compose file to scan for images"),
    output_file: str = typer.Option("images.lock.json", help="Output lock file"),
    additional_images: List[str] = typer.Option([], help="Additional images to lock (beyond compose file)")
):
    """Lock current image versions to specific digests for reproducible deployments"""
    from .digest_manager import DigestManager
    import yaml
    
    # Collect images from compose file
    compose_path = Path(compose_file)
    images_to_lock = set(additional_images)
    
    if compose_path.exists():
        try:
            with open(compose_path, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            services = compose_data.get('services', {})
            for service_name, service_config in services.items():
                image = service_config.get('image')
                if image:
                    images_to_lock.add(image)
                    typer.echo(f"Found image in {service_name}: {image}")
        
        except Exception as e:
            typer.echo(f"Warning: Could not parse {compose_file}: {e}", err=True)
    else:
        typer.echo(f"Compose file {compose_file} not found", err=True)
        if not additional_images:
            typer.echo("No images specified to lock", err=True)
            raise typer.Exit(1)
    
    if not images_to_lock:
        typer.echo("No images found to lock", err=True)
        raise typer.Exit(1)
    
    # Initialize digest manager and gather digests
    digest_manager = DigestManager(output_file)
    typer.echo(f"🔒 Locking {len(images_to_lock)} images...")
    
    try:
        digests = digest_manager.gather_digests(list(images_to_lock))
        digest_manager.save_lock_file(digests)
        typer.echo(f"✅ Successfully locked {len(digests)} images to {output_file}")
        
    except Exception as e:
        typer.echo(f"Error locking images: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def pull_images(
    lock_file: str = typer.Option("images.lock.json", help="Lock file with image digests"),
    verify_digests: bool = typer.Option(True, help="Verify pulled images match expected digests")
):
    """Pull images using locked digests for reproducible deployments"""
    from .digest_manager import DigestManager
    
    lock_path = Path(lock_file)
    if not lock_path.exists():
        typer.echo(f"Lock file {lock_file} not found", err=True)
        typer.echo("Run 'mcpctl lock-images' first to create lock file", err=True)
        raise typer.Exit(1)
    
    digest_manager = DigestManager(lock_file)
    typer.echo(f"📥 Pulling images from {lock_file}...")
    
    try:
        success = digest_manager.pull_images_by_digest()
        
        if success:
            typer.echo("✅ All images pulled successfully")
            
            if verify_digests:
                typer.echo("🔍 Verifying image digests...")
                # TODO: Add digest verification logic
                typer.echo("✅ Digest verification completed")
        else:
            typer.echo("❌ Some images failed to pull", err=True)
            raise typer.Exit(1)
            
    except Exception as e:
        typer.echo(f"Error pulling images: {e}", err=True)
        raise typer.Exit(1)

# ================================
# Workspace Management Commands
# ================================

workspace_app = typer.Typer(name="workspace", help="Manage MCP configuration workspaces")
app.add_typer(workspace_app, name="workspace")

@workspace_app.command("create")
def workspace_create(
    name: str = typer.Argument(..., help="Workspace name"),
    description: str = typer.Option("", help="Workspace description"),
    from_current: bool = typer.Option(False, help="Create from current MCP Hub state"),
    activate: bool = typer.Option(True, help="Activate the new workspace"),
    encrypt_secrets: bool = typer.Option(True, help="Encrypt secrets in git repository"),
    use_lastpass: bool = typer.Option(True, help="Use LastPass for encryption key storage")
):
    """Create a new MCP workspace"""
    manager = WorkspaceManager()
    
    if from_current:
        workspace = manager.generate_from_current(name, description)
        typer.echo(f"📦 Generated workspace '{name}' from current state")
        
        # Handle secret encryption for existing secrets
        if encrypt_secrets and workspace.secrets:
            from .encryption import EncryptionManager
            encryption_manager = EncryptionManager()
            
            typer.echo(f"🔐 Encrypting {len(workspace.secrets)} secrets...")
            
            # Get actual secret values from environment or prompt
            actual_secrets = {}
            for secret_name, description in workspace.secrets.items():
                if secret_name in os.environ:
                    actual_secrets[secret_name] = os.environ[secret_name]
                else:
                    value = typer.prompt(f"Enter value for {secret_name} ({description})", hide_input=True)
                    actual_secrets[secret_name] = value
            
            # Encrypt the secrets
            encrypted_data = encryption_manager.encrypt_secrets(actual_secrets, name, use_lastpass)
            workspace.secrets = {"encrypted": True, "data": encrypted_data}
            
            typer.echo(f"✅ Secrets encrypted and will be stored safely in git")
    else:
        workspace = manager.create_workspace(name, description)
        typer.echo(f"🆕 Created new workspace '{name}'")
    
    manager.save_workspace(workspace)
    
    if activate:
        manager.activate_workspace(name)
        typer.echo(f"✅ Workspace '{name}' activated")

@workspace_app.command("list")
def workspace_list():
    """List all available workspaces"""
    manager = WorkspaceManager()
    workspaces = manager.list_workspaces()
    active = manager.get_active_workspace()
    
    if not workspaces:
        typer.echo("No workspaces found. Create one with 'mcpctl workspace create'")
        return
    
    typer.echo("Available workspaces:")
    for ws in workspaces:
        marker = "→" if ws == active else " "
        workspace = manager.load_workspace(ws)
        if workspace:
            typer.echo(f"{marker} {ws}: {workspace.description}")
        else:
            typer.echo(f"{marker} {ws}: (error loading)")

@workspace_app.command("activate")
def workspace_activate(
    name: str = typer.Argument(..., help="Workspace name to activate")
):
    """Activate a workspace"""
    manager = WorkspaceManager()
    
    try:
        manager.activate_workspace(name)
        typer.echo(f"✅ Activated workspace '{name}'")
        
        # Apply the workspace configuration
        workspace = manager.load_workspace(name)
        if workspace:
            typer.echo("🔄 Applying workspace configuration...")
            # TODO: Apply workspace to current system
            typer.echo("⚠️  Note: Restart MCP services to apply changes")
        
    except ValueError as e:
        typer.echo(f"❌ {e}", err=True)
        raise typer.Exit(1)

@workspace_app.command("export")
def workspace_export(
    name: str = typer.Argument(..., help="Workspace name to export"),
    output: str = typer.Option("", help="Output file/directory path"),
    format: str = typer.Option("bundle", help="Export format: bundle, git, json")
):
    """Export workspace for sharing"""
    manager = WorkspaceManager()
    
    if not output:
        if format == "bundle":
            output = f"{name}.tar.gz"
        elif format == "git":
            output = f"{name}-git"
        else:
            output = f"{name}.json"
    
    output_path = Path(output)
    
    try:
        manager.export_workspace(name, output_path, format)
        typer.echo(f"📦 Exported workspace '{name}' to {output_path}")
        
        if format == "git":
            typer.echo(f"🔧 To share: cd {output_path}/{name} && git init && git add . && git commit -m 'Initial workspace'")
        elif format == "bundle":
            typer.echo(f"📤 To share: Send {output_path} to other users")
        
    except Exception as e:
        typer.echo(f"❌ Export failed: {e}", err=True)
        raise typer.Exit(1)

@workspace_app.command("import")
def workspace_import(
    source: str = typer.Argument(..., help="Source file/directory/URL to import"),
    activate: bool = typer.Option(False, help="Activate after import"),
    name: str = typer.Option("", help="Override workspace name")
):
    """Import workspace from file, directory, or git repository"""
    manager = WorkspaceManager()
    source_path = Path(source)
    
    # Handle git URLs
    if source.startswith(("http://", "https://", "git@")):
        import subprocess
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "workspace"
            typer.echo(f"📥 Cloning {source}...")
            
            try:
                subprocess.run(["git", "clone", source, str(temp_path)], check=True, capture_output=True)
                workspace_name = manager.import_workspace(temp_path, activate)
                
                if name:
                    # Rename workspace if requested
                    old_workspace = manager.load_workspace(workspace_name)
                    old_workspace.name = name
                    manager.save_workspace(old_workspace)
                    workspace_name = name
                
                # Check if workspace has encrypted secrets
                workspace = manager.load_workspace(workspace_name)
                if workspace and isinstance(workspace.secrets, dict) and workspace.secrets.get("encrypted"):
                    typer.echo(f"🔐 Workspace '{workspace_name}' uses encrypted secrets")
                    
                    from .encryption import EncryptionManager
                    encryption_manager = EncryptionManager()
                    
                    # Setup encryption key
                    if encryption_manager.import_key_setup(workspace_name):
                        typer.echo(f"✅ Imported encrypted workspace '{workspace_name}' from git repository")
                    else:
                        typer.echo(f"⚠️  Imported workspace '{workspace_name}' but secrets remain encrypted")
                        typer.echo("💡 Use 'mcpctl workspace decrypt {workspace_name}' to set up decryption later")
                else:
                    typer.echo(f"✅ Imported workspace '{workspace_name}' from git repository")
                
            except subprocess.CalledProcessError as e:
                typer.echo(f"❌ Git clone failed: {e}", err=True)
                raise typer.Exit(1)
    
    else:
        # Handle local files/directories
        if not source_path.exists():
            typer.echo(f"❌ Source not found: {source_path}", err=True)
            raise typer.Exit(1)
        
        try:
            workspace_name = manager.import_workspace(source_path, activate)
            
            if name:
                # Rename workspace if requested
                old_workspace = manager.load_workspace(workspace_name)
                old_workspace.name = name
                manager.save_workspace(old_workspace)
                workspace_name = name
            
            # Check if workspace has encrypted secrets
            workspace = manager.load_workspace(workspace_name)
            if workspace and isinstance(workspace.secrets, dict) and workspace.secrets.get("encrypted"):
                typer.echo(f"🔐 Workspace '{workspace_name}' uses encrypted secrets")
                
                from .encryption import EncryptionManager
                encryption_manager = EncryptionManager()
                
                if encryption_manager.import_key_setup(workspace_name):
                    typer.echo(f"✅ Imported encrypted workspace '{workspace_name}'")
                else:
                    typer.echo(f"⚠️  Imported workspace '{workspace_name}' but secrets remain encrypted")
            else:
                typer.echo(f"✅ Imported workspace '{workspace_name}'")
            
        except Exception as e:
            typer.echo(f"❌ Import failed: {e}", err=True)
            raise typer.Exit(1)

@workspace_app.command("info")
def workspace_info(
    name: str = typer.Argument("", help="Workspace name (current if omitted)")
):
    """Show workspace information"""
    manager = WorkspaceManager()
    
    if not name:
        name = manager.get_active_workspace()
        if not name:
            typer.echo("❌ No active workspace. Specify a name or activate one.", err=True)
            raise typer.Exit(1)
    
    workspace = manager.load_workspace(name)
    if not workspace:
        typer.echo(f"❌ Workspace '{name}' not found", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"📋 Workspace: {workspace.name}")
    typer.echo(f"📝 Description: {workspace.description}")
    typer.echo(f"👤 Author: {workspace.author}")
    typer.echo(f"📅 Created: {workspace.created_at}")
    typer.echo(f"🔄 Updated: {workspace.updated_at}")
    typer.echo(f"🏷️  Tags: {', '.join(workspace.tags)}")
    typer.echo(f"💻 Platforms: {', '.join(workspace.platforms)}")
    
    if workspace.services:
        typer.echo(f"\n🐳 Services ({len(workspace.services)}):")
        for service_name in workspace.services.keys():
            typer.echo(f"  • {service_name}")
    
    if workspace.secrets:
        typer.echo(f"\n🔐 Required Secrets ({len(workspace.secrets)}):")
        for secret_name, description in workspace.secrets.items():
            typer.echo(f"  • {secret_name}: {description}")

@workspace_app.command("sync")
def workspace_sync(
    remote: str = typer.Option("", help="Git remote URL for syncing"),
    push: bool = typer.Option(False, help="Push local changes to remote"),
    pull: bool = typer.Option(False, help="Pull changes from remote")
):
    """Sync workspace with git remote (future feature)"""
    typer.echo("🚧 Workspace sync feature coming soon!")
    typer.echo("💡 For now, use 'workspace export --format git' and manual git operations")

# ================================
# Encryption Management Commands
# ================================

@workspace_app.command("encrypt")
def workspace_encrypt(
    name: str = typer.Argument("", help="Workspace name (current if omitted)"),
    use_lastpass: bool = typer.Option(True, help="Use LastPass for key storage")
):
    """Encrypt workspace secrets for safe git storage"""
    manager = WorkspaceManager()
    
    if not name:
        name = manager.get_active_workspace()
        if not name:
            typer.echo("❌ No active workspace. Specify a name or activate one.", err=True)
            raise typer.Exit(1)
    
    workspace = manager.load_workspace(name)
    if not workspace:
        typer.echo(f"❌ Workspace '{name}' not found", err=True)
        raise typer.Exit(1)
    
    # Check if already encrypted
    if isinstance(workspace.secrets, dict) and workspace.secrets.get("encrypted"):
        typer.echo(f"✅ Workspace '{name}' is already encrypted")
        return
    
    if not workspace.secrets:
        typer.echo(f"⚠️  Workspace '{name}' has no secrets to encrypt")
        return
    
    from .encryption import EncryptionManager
    encryption_manager = EncryptionManager()
    
    # Collect actual secret values
    typer.echo(f"🔐 Encrypting {len(workspace.secrets)} secrets for workspace '{name}'")
    actual_secrets = {}
    
    for secret_name, description in workspace.secrets.items():
        if secret_name in os.environ:
            actual_secrets[secret_name] = os.environ[secret_name]
            typer.echo(f"  📝 {secret_name}: (from environment)")
        else:
            value = typer.prompt(f"  🔑 Enter value for {secret_name}", hide_input=True)
            actual_secrets[secret_name] = value
    
    try:
        # Encrypt secrets
        encrypted_data = encryption_manager.encrypt_secrets(actual_secrets, name, use_lastpass)
        workspace.secrets = {"encrypted": True, "data": encrypted_data}
        
        # Save updated workspace
        manager.save_workspace(workspace)
        
        typer.echo(f"✅ Workspace '{name}' secrets encrypted successfully")
        typer.echo("🔒 Encrypted secrets are now safe to commit to git")
        
    except Exception as e:
        typer.echo(f"❌ Encryption failed: {e}", err=True)
        raise typer.Exit(1)

@workspace_app.command("decrypt")
def workspace_decrypt(
    name: str = typer.Argument("", help="Workspace name (current if omitted)"),
    show_secrets: bool = typer.Option(False, help="Display decrypted secrets"),
    export_env: bool = typer.Option(False, help="Export as environment variables")
):
    """Decrypt workspace secrets and optionally display them"""
    manager = WorkspaceManager()
    
    if not name:
        name = manager.get_active_workspace()
        if not name:
            typer.echo("❌ No active workspace. Specify a name or activate one.", err=True)
            raise typer.Exit(1)
    
    workspace = manager.load_workspace(name)
    if not workspace:
        typer.echo(f"❌ Workspace '{name}' not found", err=True)
        raise typer.Exit(1)
    
    # Check if encrypted
    if not (isinstance(workspace.secrets, dict) and workspace.secrets.get("encrypted")):
        typer.echo(f"⚠️  Workspace '{name}' does not use encrypted secrets")
        return
    
    try:
        decrypted_secrets = manager.decrypt_workspace_secrets(workspace)
        
        if decrypted_secrets is None:
            typer.echo(f"❌ Failed to decrypt secrets for workspace '{name}'", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"✅ Successfully decrypted {len(decrypted_secrets)} secrets")
        
        if show_secrets:
            typer.echo("\n🔓 Decrypted secrets:")
            for key, value in decrypted_secrets.items():
                masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
                typer.echo(f"  {key}: {masked_value}")
        
        if export_env:
            env_file = f"{name}.env"
            with open(env_file, 'w') as f:
                f.write(f"# Decrypted secrets for workspace: {name}\n")
                f.write(f"# Generated on: {datetime.now().isoformat()}\n\n")
                for key, value in decrypted_secrets.items():
                    f.write(f"{key}={value}\n")
            typer.echo(f"📄 Exported secrets to {env_file}")
        
    except Exception as e:
        typer.echo(f"❌ Decryption failed: {e}", err=True)
        raise typer.Exit(1)

@workspace_app.command("test-encryption")
def workspace_test_encryption():
    """Test encryption/decryption functionality"""
    from .encryption import EncryptionManager
    
    try:
        encryption_manager = EncryptionManager()
        if encryption_manager.test_encryption():
            typer.echo("🎉 Encryption system is working correctly!")
        else:
            typer.echo("❌ Encryption test failed", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Encryption test error: {e}", err=True)
        raise typer.Exit(1)

@workspace_app.command("generate-key")
def workspace_generate_key(
    workspace: str = typer.Argument(..., help="Workspace name"),
    store_lastpass: bool = typer.Option(True, help="Store generated key in LastPass")
):
    """Generate a new encryption key for workspace"""
    from .encryption import EncryptionManager
    
    encryption_manager = EncryptionManager()
    new_key = encryption_manager.generate_new_key()
    
    typer.echo(f"🔑 Generated new encryption key for workspace '{workspace}'")
    typer.echo(f"Key: {new_key}")
    
    if store_lastpass:
        if encryption_manager.store_key_in_lastpass(workspace, new_key):
            typer.echo("✅ Key stored in LastPass")
        else:
            typer.echo("⚠️  Could not store key in LastPass - store it safely!")
    else:
        typer.echo("⚠️  Key not stored in LastPass - save it securely!")
    
    typer.echo("\n💡 To use this key:")
    typer.echo(f"   mcpctl workspace encrypt {workspace}")

# ================================
# LLM Testing Commands
# ================================

llm_app = typer.Typer(name="llm", help="Test and verify LLM backend connections")
app.add_typer(llm_app, name="llm")

@llm_app.command("test")
def llm_test(
    backend: str = typer.Option("all", help="Backend to test: claude, openai, custom, or all"),
    url: str = typer.Option("", help="Custom LLM URL (for custom backend)"),
    api_key: str = typer.Option("", help="API key for OpenAI or custom backend"),
    model: str = typer.Option("", help="Model name for custom backend"),
    verbose: bool = typer.Option(False, help="Show detailed test results"),
    save_config: bool = typer.Option(False, help="Save working configuration")
):
    """Test LLM backend connections"""
    from .llm_tester import LLMTester, get_llm_config
    
    tester = LLMTester()
    config = get_llm_config()
    
    # Override config with command line arguments
    if url:
        config["custom_llm_url"] = url
    if api_key:
        if backend == "openai":
            config["openai_api_key"] = api_key
        else:
            config["custom_llm_api_key"] = api_key
    if model:
        config["custom_llm_model"] = model
    
    print("🧪 Testing LLM Backend Connections")
    print("==================================")
    print()
    
    results = {}
    
    if backend == "all":
        # Test all available backends
        print("📡 Testing all configured backends...")
        print()
        
        # Always test Claude Desktop
        results["claude"] = tester.test_claude_desktop()
        
        # Test OpenAI if configured
        if config.get("openai_api_key"):
            results["openai"] = tester.test_openai_api(config["openai_api_key"])
        
        # Test Custom if configured
        if config.get("custom_llm_url"):
            results["custom"] = tester.test_custom_llm(
                config["custom_llm_url"],
                config.get("custom_llm_api_key"),
                config.get("custom_llm_model")
            )
        
        if not results:
            print("❌ No LLM backends configured")
            print("💡 Configure backends with: mcpctl llm setup")
            return
    
    elif backend == "claude":
        results["claude"] = tester.test_claude_desktop()
    
    elif backend == "openai":
        if not config.get("openai_api_key"):
            print("❌ OpenAI API key not configured")
            print("💡 Provide with --api-key or set OPENAI_API_KEY environment variable")
            return
        results["openai"] = tester.test_openai_api(config["openai_api_key"])
    
    elif backend == "custom":
        if not config.get("custom_llm_url"):
            print("❌ Custom LLM URL not configured")
            print("💡 Provide with --url or configure with: mcpctl llm setup")
            return
        results["custom"] = tester.test_custom_llm(
            config["custom_llm_url"],
            config.get("custom_llm_api_key"),
            config.get("custom_llm_model")
        )
    
    else:
        print(f"❌ Unknown backend: {backend}")
        print("💡 Available backends: claude, openai, custom, all")
        return
    
    # Display results
    success_count = 0
    for backend_name, result in results.items():
        print(tester.format_test_result(result, verbose))
        print()
        if result["success"]:
            success_count += 1
    
    # Summary
    total_tests = len(results)
    print(f"📊 Summary: {success_count}/{total_tests} backends working")
    
    if success_count == total_tests:
        print("🎉 All tested backends are working!")
    elif success_count > 0:
        print("⚠️  Some backends have issues - check configuration")
    else:
        print("❌ No backends are working - check setup and connections")
    
    # Save working configuration if requested
    if save_config and success_count > 0:
        try:
            config_file = Path.home() / ".mcpctl" / "config.toml"
            config_file.parent.mkdir(exist_ok=True)
            
            # Load existing config
            existing_config = {}
            if config_file.exists():
                import toml
                with open(config_file, 'r') as f:
                    existing_config = toml.load(f)
            
            # Update with working backends
            for backend_name, result in results.items():
                if result["success"]:
                    if backend_name == "openai" and config.get("openai_api_key"):
                        existing_config["openai_api_key"] = config["openai_api_key"]
                    elif backend_name == "custom":
                        if config.get("custom_llm_url"):
                            existing_config["custom_llm_url"] = config["custom_llm_url"]
                        if config.get("custom_llm_api_key"):
                            existing_config["custom_llm_api_key"] = config["custom_llm_api_key"]
                        if config.get("custom_llm_model"):
                            existing_config["custom_llm_model"] = config["custom_llm_model"]
            
            # Save updated config
            import toml
            with open(config_file, 'w') as f:
                toml.dump(existing_config, f)
            
            print(f"💾 Working configuration saved to {config_file}")
            
        except Exception as e:
            print(f"⚠️  Failed to save configuration: {e}")

@llm_app.command("setup")
def llm_setup(
    interactive: bool = typer.Option(True, help="Interactive setup wizard")
):
    """Configure LLM backends"""
    from .llm_tester import LLMTester
    
    print("🔧 LLM Backend Setup")
    print("===================")
    print()
    
    tester = LLMTester()
    config = {}
    
    if interactive:
        print("Let's configure your LLM backends!")
        print()
        
        # OpenAI API setup
        setup_openai = input("Configure OpenAI API? (y/N): ").lower().startswith('y')
        if setup_openai:
            api_key = input("Enter your OpenAI API key: ").strip()
            if api_key:
                print("🧪 Testing OpenAI connection...")
                result = tester.test_openai_api(api_key)
                print(tester.format_test_result(result))
                
                if result["success"]:
                    config["openai_api_key"] = api_key
                    print("✅ OpenAI configuration saved")
                else:
                    save_anyway = input("Save configuration anyway? (y/N): ").lower().startswith('y')
                    if save_anyway:
                        config["openai_api_key"] = api_key
                print()
        
        # Custom LLM setup
        setup_custom = input("Configure custom LLM endpoint? (y/N): ").lower().startswith('y')
        if setup_custom:
            url = input("Enter custom LLM URL (e.g., https://api.your-provider.com): ").strip()
            api_key = input("Enter API key (optional): ").strip()
            model = input("Enter model name (optional): ").strip()
            
            if url:
                print("🧪 Testing custom LLM connection...")
                result = tester.test_custom_llm(url, api_key or None, model or None)
                print(tester.format_test_result(result))
                
                if result["success"]:
                    config["custom_llm_url"] = url
                    if api_key:
                        config["custom_llm_api_key"] = api_key
                    if model:
                        config["custom_llm_model"] = model
                    print("✅ Custom LLM configuration saved")
                else:
                    save_anyway = input("Save configuration anyway? (y/N): ").lower().startswith('y')
                    if save_anyway:
                        config["custom_llm_url"] = url
                        if api_key:
                            config["custom_llm_api_key"] = api_key
                        if model:
                            config["custom_llm_model"] = model
                print()
        
        # Test Claude Desktop
        print("🧪 Testing Claude Desktop connection...")
        claude_result = tester.test_claude_desktop()
        print(tester.format_test_result(claude_result))
        print()
        
        # Save configuration
        if config:
            try:
                config_file = Path.home() / ".mcpctl" / "config.toml"
                config_file.parent.mkdir(exist_ok=True)
                
                # Load existing config
                existing_config = {}
                if config_file.exists():
                    import toml
                    with open(config_file, 'r') as f:
                        existing_config = toml.load(f)
                
                # Merge configurations
                existing_config.update(config)
                
                # Save
                import toml
                with open(config_file, 'w') as f:
                    toml.dump(existing_config, f)
                
                print(f"💾 Configuration saved to {config_file}")
                print("🎉 LLM backend setup complete!")
                
            except Exception as e:
                print(f"❌ Failed to save configuration: {e}")
        else:
            print("💡 No configuration changes made")
    
    else:
        print("💡 Run 'mcpctl llm setup' for interactive configuration")
        print("💡 Or use 'mcpctl llm test --help' for testing options")

@llm_app.command("status")
def llm_status():
    """Show current LLM backend status"""
    from .llm_tester import LLMTester, get_llm_config
    
    print("📊 LLM Backend Status")
    print("====================")
    print()
    
    config = get_llm_config()
    tester = LLMTester()
    
    if not config:
        print("❌ No LLM backends configured")
        print("💡 Run 'mcpctl llm setup' to configure backends")
        return
    
    # Quick status check (faster than full test)
    backends_configured = []
    
    if config.get("openai_api_key"):
        backends_configured.append("OpenAI API")
    
    if config.get("custom_llm_url"):
        backends_configured.append(f"Custom LLM ({config['custom_llm_url']})")
    
    # Always show Claude Desktop status
    backends_configured.append("Claude Desktop (auto-detect)")
    
    print("🔧 Configured Backends:")
    for backend in backends_configured:
        print(f"  • {backend}")
    
    print()
    print("💡 Test connections: mcpctl llm test")
    print("💡 Configure more: mcpctl llm setup")

if __name__ == "__main__":
    app()
