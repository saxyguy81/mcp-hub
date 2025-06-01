"""
Environment/Manual secret backend
"""

import os
from typing import Dict
import typer
from .base import SecretBackend

class EnvBackend(SecretBackend):
    """Manual/Environment variable secret backend"""
    
    def __init__(self):
        self._secrets = {}
    
    def get_secret(self, name: str) -> str:
        """Get secret from environment or prompt user"""
        # First try environment variable
        env_name = f"MCP_{name.upper()}"
        if env_name in os.environ:
            return os.environ[env_name]
        
        # Try cached secrets
        if name in self._secrets:
            return self._secrets[name]
        
        # Prompt user for secret
        value = typer.prompt(f"Enter secret '{name}'", hide_input=True)
        self._secrets[name] = value
        return value
    
    def set_secret(self, name: str, value: str) -> None:
        """Store secret in memory cache"""
        self._secrets[name] = value
    
    def list_secrets(self) -> Dict[str, str]:
        """List all available secrets"""
        secrets = {}
        # Add environment variables
        for key, value in os.environ.items():
            if key.startswith("MCP_"):
                secret_name = key[4:].lower()
                secrets[secret_name] = value
        
        # Add cached secrets
        secrets.update(self._secrets)
        return secrets
    
    def delete_secret(self, name: str) -> None:
        """Delete secret from cache"""
        if name in self._secrets:
            del self._secrets[name]
