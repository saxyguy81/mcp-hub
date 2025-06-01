"""
Docker Compose generation from service definitions and templates
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from .secret_backends.base import SecretBackend

class ComposeGenerator:
    """Generates docker-compose.yml files from templates and service definitions"""
    
    def __init__(self, secret_backend: SecretBackend):
        self.secret_backend = secret_backend
    
    def load_template(self, template_file: Path) -> Dict[str, Any]:
        """Load the base compose template"""
        if not template_file.exists():
            # Return minimal template if none exists
            return {
                "version": "3.8",
                "services": {},
                "networks": {
                    "mcp-network": {
                        "driver": "bridge"
                    }
                }
            }
        
        try:
            with open(template_file, 'r') as f:
                template = yaml.safe_load(f)
                if template is None:
                    # Handle empty file case
                    template = {"version": "3.8", "services": {}}
                return template
        except Exception as e:
            print(f"Error loading template: {e}")
            # Return default template on error
            return {
                "version": "3.8", 
                "services": {},
                "networks": {"mcp-network": {"driver": "bridge"}}
            }
    
    def load_service_definitions(self, services_dir: Path) -> List[Dict[str, Any]]:
        """Load all service definition files from a directory"""
        services = []
        
        if not services_dir.exists():
            return services
        
        for service_file in services_dir.glob("*.yml"):
            with open(service_file, 'r') as f:
                service_def = yaml.safe_load(f)
                if service_def:
                    services.append(service_def)
        
        return services
    
    def resolve_secrets(self, data: Any) -> Any:
        """Recursively resolve secret placeholders in data structure"""
        if isinstance(data, dict):
            return {k: self.resolve_secrets(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.resolve_secrets(item) for item in data]
        elif isinstance(data, str) and data.startswith("${SECRET:"):
            # Extract secret name from ${SECRET:secret_name}
            secret_name = data[9:-1]  # Remove ${SECRET: and }
            return self.secret_backend.get_secret(secret_name)
        else:
            return data
    
    def merge_services(self, template: Dict[str, Any], services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge service definitions into the template"""
        result = template.copy()
        
        if "services" not in result:
            result["services"] = {}
        
        for service_def in services:
            if "services" in service_def:
                for service_name, service_config in service_def["services"].items():
                    # Resolve any secrets in the service config
                    resolved_config = self.resolve_secrets(service_config)
                    result["services"][service_name] = resolved_config
        
        return result
    
    def generate_compose(self, services_dir: Path, template_file: Path, output_file: Path) -> None:
        """Generate the final docker-compose.yml file"""
        template = self.load_template(template_file)
        services = self.load_service_definitions(services_dir)
        
        final_compose = self.merge_services(template, services)
        
        with open(output_file, 'w') as f:
            yaml.dump(final_compose, f, default_flow_style=False, indent=2)
