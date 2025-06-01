"""
MCP Hub Workspace Management
Handles portable, shareable MCP server configurations
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import typer

# Use safe yaml loading - install pyyaml if needed
try:
    import yaml
except ImportError:
    print("Warning: PyYAML not found. Install with: pip install pyyaml")
    # Fallback to JSON for now
    yaml = None

@dataclass
class MCPWorkspace:
    """A portable MCP configuration workspace"""
    name: str
    description: str
    version: str = "1.0"
    created_at: str = ""
    updated_at: str = ""
    author: str = ""
    
    # Core configuration
    services: Dict[str, Any] = None  # Service definitions
    networks: Dict[str, Any] = None  # Network configuration
    volumes: Dict[str, Any] = None   # Volume configuration
    secrets: Dict[str, str] = None   # Secret mappings (not values!)
    
    # Platform compatibility
    platforms: List[str] = None      # ["macos", "linux", "windows"]
    requirements: Dict[str, str] = None  # {"docker": ">=20.0", "python": ">=3.8"}
    
    # Metadata
    tags: List[str] = None          # ["web-scraping", "ai", "development"]
    readme: str = ""                # Documentation
    
    def __post_init__(self):
        if self.services is None:
            self.services = {}
        if self.networks is None:
            self.networks = {"mcp-network": {"driver": "bridge"}}
        if self.volumes is None:
            self.volumes = {}
        if self.secrets is None:
            self.secrets = {}
        if self.platforms is None:
            self.platforms = ["macos", "linux", "windows"]
        if self.requirements is None:
            self.requirements = {"docker": ">=20.0"}
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class WorkspaceManager:
    """Manages MCP workspaces - creation, import, export, sharing"""
    
    def __init__(self, workspaces_dir: Optional[Path] = None):
        self.workspaces_dir = workspaces_dir or (Path.home() / ".mcpctl" / "workspaces")
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        self.active_workspace_file = Path.home() / ".mcpctl" / "active_workspace"
    
    def create_workspace(self, name: str, description: str = "", author: str = "") -> MCPWorkspace:
        """Create a new workspace"""
        workspace = MCPWorkspace(
            name=name,
            description=description,
            author=author
        )
        
        workspace_dir = self.workspaces_dir / name
        workspace_dir.mkdir(exist_ok=True)
        
        self.save_workspace(workspace)
        return workspace
    
    def save_workspace(self, workspace: MCPWorkspace) -> None:
        """Save workspace to disk"""
        workspace.updated_at = datetime.now().isoformat()
        workspace_dir = self.workspaces_dir / workspace.name
        workspace_dir.mkdir(exist_ok=True)
        
        # Save workspace metadata
        workspace_file = workspace_dir / "workspace.yml"
        
        # Prepare workspace data for saving
        workspace_data = asdict(workspace)
        
        # Handle encrypted secrets specially
        if isinstance(workspace.secrets, dict) and workspace.secrets.get("encrypted"):
            # Secrets are encrypted - save as-is in YAML
            # This means encrypted secrets will be committed to git
            workspace_data["secrets"] = workspace.secrets
        else:
            # Legacy unencrypted secrets - convert to template format
            if workspace.secrets:
                workspace_data["secrets_template"] = workspace.secrets
                workspace_data["secrets"] = {"encrypted": False}
        
        if yaml:
            with open(workspace_file, 'w') as f:
                yaml.dump(workspace_data, f, default_flow_style=False)
        else:
            with open(workspace_file, 'w') as f:
                json.dump(workspace_data, f, indent=2)
        
        # Save docker-compose.yml
        compose_data = {
            "version": "3.8",
            "services": workspace.services,
            "networks": workspace.networks,
            "volumes": workspace.volumes
        }
        
        compose_file = workspace_dir / "docker-compose.yml"
        if yaml:
            with open(compose_file, 'w') as f:
                yaml.dump(compose_data, f, default_flow_style=False)
        else:
            with open(compose_file, 'w') as f:
                json.dump(compose_data, f, indent=2)
        
        # Save individual service files
        services_dir = workspace_dir / "services"
        services_dir.mkdir(exist_ok=True)
        
        for service_name, service_config in workspace.services.items():
            service_file = services_dir / f"{service_name}.yml"
            service_data = {"services": {service_name: service_config}}
            
            if yaml:
                with open(service_file, 'w') as f:
                    yaml.dump(service_data, f, default_flow_style=False)
            else:
                with open(service_file, 'w') as f:
                    json.dump(service_data, f, indent=2)
        
        # Handle secrets based on encryption status
        if isinstance(workspace.secrets, dict) and workspace.secrets.get("encrypted"):
            # Encrypted secrets - create info file instead of template
            secrets_info = workspace_dir / "secrets.info"
            with open(secrets_info, 'w') as f:
                f.write(f"""# MCP Hub Encrypted Secrets
# Workspace: {workspace.name}
# 
# This workspace uses encrypted secrets stored in the git repository.
# When importing this workspace, you'll be prompted for the encryption key.
#
# The encryption key can be:
# 1. Retrieved automatically from LastPass (if configured)
# 2. Entered manually (you'll need to remember/share it)
#
# Encrypted secrets are stored in workspace.yml and are safe to commit to git.
""")
        else:
            # Legacy unencrypted - create template
            secrets_template = workspace_data.get("secrets_template", {})
            if secrets_template:
                secrets_file = workspace_dir / "secrets.env.template"
                with open(secrets_file, 'w') as f:
                    f.write("# MCP Hub Secrets Template\n")
                    f.write("# Copy this file to secrets.env and fill in your values\n\n")
                    for key, description in secrets_template.items():
                        f.write(f"# {description}\n")
                        f.write(f"{key}=\n\n")
        
        # Save README
        if workspace.readme:
            readme_file = workspace_dir / "README.md"
            with open(readme_file, 'w') as f:
                f.write(workspace.readme)
    
    def load_workspace(self, name: str) -> Optional[MCPWorkspace]:
        """Load workspace from disk"""
        workspace_file = self.workspaces_dir / name / "workspace.yml"
        if not workspace_file.exists():
            return None
        
        try:
            if yaml:
                with open(workspace_file, 'r') as f:
                    data = yaml.safe_load(f)
            else:
                with open(workspace_file, 'r') as f:
                    data = json.load(f)
            
            # Handle legacy format conversion
            if "secrets_template" in data:
                # Convert old template format to new format
                data["secrets"] = data.pop("secrets_template")
            
            return MCPWorkspace(**data)
        except Exception as e:
            typer.echo(f"Error loading workspace {name}: {e}", err=True)
            return None
    
    def decrypt_workspace_secrets(self, workspace: MCPWorkspace) -> Optional[Dict[str, str]]:
        """Decrypt secrets from workspace if encrypted"""
        if not isinstance(workspace.secrets, dict):
            return workspace.secrets or {}
        
        if workspace.secrets.get("encrypted"):
            try:
                from .encryption import EncryptionManager
                encryption_manager = EncryptionManager()
                
                encrypted_data = workspace.secrets["data"]
                return encryption_manager.decrypt_secrets(encrypted_data, workspace.name)
            except Exception as e:
                typer.echo(f"❌ Failed to decrypt secrets: {e}", err=True)
                return None
        else:
            # Unencrypted secrets
            return workspace.secrets or {}
    
    def list_workspaces(self) -> List[str]:
        """List all available workspaces"""
        if not self.workspaces_dir.exists():
            return []
        
        workspaces = []
        for item in self.workspaces_dir.iterdir():
            if item.is_dir() and (item / "workspace.yml").exists():
                workspaces.append(item.name)
        return sorted(workspaces)
    
    def export_workspace(self, name: str, output_path: Path, format: str = "bundle") -> None:
        """Export workspace for sharing"""
        workspace = self.load_workspace(name)
        if not workspace:
            raise ValueError(f"Workspace '{name}' not found")
        
        workspace_dir = self.workspaces_dir / name
        
        if format == "bundle":
            # Create a tar.gz bundle
            import tarfile
            with tarfile.open(output_path, "w:gz") as tar:
                tar.add(workspace_dir, arcname=name)
        
        elif format == "git":
            # Create a git repository structure
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Copy all files
            shutil.copytree(workspace_dir, output_path / name, dirs_exist_ok=True)
            
            # Create .gitignore
            gitignore = output_path / name / ".gitignore"
            with open(gitignore, 'w') as f:
                f.write("secrets.env\n*.log\ndata/\n.env\n")
            
            # Create installation script
            install_script = output_path / name / "install.sh"
            with open(install_script, 'w') as f:
                f.write(f"""#!/bin/bash
# MCP Hub Workspace: {workspace.name}
# {workspace.description}

set -e

echo "🚀 Installing MCP workspace: {workspace.name}"

# Check if MCP Hub is installed
if ! command -v mcpctl >/dev/null 2>&1; then
    echo "❌ MCP Hub not found. Installing..."
    curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash
fi

# Import workspace
mcpctl workspace import . --activate

echo "✅ Workspace '{workspace.name}' installed and activated!"
echo "📝 Don't forget to copy secrets.env.template to secrets.env and fill in your values"
""")
            os.chmod(install_script, 0o755)
        
        elif format == "json":
            # Export as single JSON file
            with open(output_path, 'w') as f:
                json.dump(asdict(workspace), f, indent=2)
    
    def import_workspace(self, source_path: Path, activate: bool = False) -> str:
        """Import workspace from various sources"""
        if source_path.suffix == ".gz":
            # Import from tar.gz bundle
            import tarfile
            with tarfile.open(source_path, "r:gz") as tar:
                tar.extractall(self.workspaces_dir)
                # Get the workspace name from the extracted directory
                extracted_dirs = [name for name in tar.getnames() if '/' not in name]
                workspace_name = extracted_dirs[0] if extracted_dirs else source_path.stem
        
        elif source_path.suffix == ".json":
            # Import from JSON file
            with open(source_path, 'r') as f:
                data = json.load(f)
            workspace = MCPWorkspace(**data)
            self.save_workspace(workspace)
            workspace_name = workspace.name
        
        elif source_path.is_dir():
            # Import from directory (git clone, etc.)
            workspace_file = source_path / "workspace.yml"
            if not workspace_file.exists():
                raise ValueError("Invalid workspace directory: missing workspace.yml")
            
            workspace = self.load_workspace_from_path(source_path)
            self.save_workspace(workspace)
            workspace_name = workspace.name
        
        else:
            raise ValueError(f"Unsupported import format: {source_path}")
        
        if activate:
            self.activate_workspace(workspace_name)
        
        return workspace_name
    
    def load_workspace_from_path(self, path: Path) -> MCPWorkspace:
        """Load workspace from a directory path"""
        workspace_file = path / "workspace.yml"
        with open(workspace_file, 'r') as f:
            data = yaml.safe_load(f)
        return MCPWorkspace(**data)
    
    def activate_workspace(self, name: str) -> None:
        """Set active workspace"""
        workspace = self.load_workspace(name)
        if not workspace:
            raise ValueError(f"Workspace '{name}' not found")
        
        with open(self.active_workspace_file, 'w') as f:
            f.write(name)
    
    def get_active_workspace(self) -> Optional[str]:
        """Get currently active workspace name"""
        if not self.active_workspace_file.exists():
            return None
        
        try:
            with open(self.active_workspace_file, 'r') as f:
                return f.read().strip()
        except:
            return None
    
    def generate_from_current(self, name: str, description: str = "") -> MCPWorkspace:
        """Generate workspace from current MCP Hub state"""
        from .cli import load_config
        from .compose_gen import ComposeGenerator
        
        config = load_config()
        
        # Read current services
        services_dir = Path(config.services_dir)
        services = {}
        
        if services_dir.exists():
            for service_file in services_dir.glob("*.yml"):
                with open(service_file, 'r') as f:
                    service_data = yaml.safe_load(f)
                    if 'services' in service_data:
                        services.update(service_data['services'])
        
        # Read current compose file
        compose_file = Path(config.compose_file)
        networks = {"mcp-network": {"driver": "bridge"}}
        volumes = {}
        
        if compose_file.exists():
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
                networks = compose_data.get('networks', networks)
                volumes = compose_data.get('volumes', volumes)
        
        # Extract secrets from environment variables
        secrets = {}
        for service_name, service_config in services.items():
            env_vars = service_config.get('environment', [])
            for env_var in env_vars:
                if isinstance(env_var, str) and '=${' in env_var:
                    # Extract variable name from ${VAR_NAME} format
                    var_name = env_var.split('=${')[1].rstrip('}')
                    secrets[var_name] = f"Secret for {service_name}"
        
        workspace = MCPWorkspace(
            name=name,
            description=description,
            services=services,
            networks=networks,
            volumes=volumes,
            secrets=secrets,
            author=os.environ.get('USER', 'unknown')
        )
        
        return workspace
