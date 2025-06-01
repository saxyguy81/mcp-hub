#!/usr/bin/env python3
"""
MCP Hub CLI - Main command interface for managing MCP server containers
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import tomllib
import toml

import typer
import docker
from docker.errors import DockerException

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
    
    client = get_docker_client()
    
    cmd = ["docker-compose", "-f", compose_file, "up"]
    if detach:
        cmd.append("-d")
    if build:
        cmd.append("--build")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
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
    
    cmd = ["docker-compose", "-f", compose_file, "down"]
    
    try:
        subprocess.run(cmd, check=True)
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
    
    cmd = ["docker-compose", "-f", compose_file, "ps"]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error getting status: {e}", err=True)
        raise typer.Exit(1)

@app.command("publish-images")
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
