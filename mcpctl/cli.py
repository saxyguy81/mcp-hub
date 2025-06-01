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
def start(
    compose_file: str = typer.Option("docker-compose.yml", help="Docker compose file"),
    detach: bool = typer.Option(True, help="Run in background"),
    build: bool = typer.Option(False, help="Build images before starting")
):
    """Start MCP Hub services"""
    if not Path(compose_file).exists():
        typer.echo(f"Compose file not found: {compose_file}", err=True)
        typer.echo("Run 'mcpctl generate' first.", err=True)
        raise typer.Exit(1)
    
    try:
        container_engine.compose_up(compose_file, detach=detach, build=build)
        typer.echo("MCP Hub services started successfully!")
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
def publish_images(
    registry_url: str = typer.Option("", help="Registry URL (overrides config)"),
    tag: str = typer.Option("latest", help="Image tag"),
    push: bool = typer.Option(True, help="Push to registry (false = save as tarball)")
):
    """Build and publish MCP server images"""
    config = load_config()
    
    if registry_url:
        config.docker_registry = registry_url
    
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

if __name__ == "__main__":
    app()
