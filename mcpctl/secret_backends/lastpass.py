"""
LastPass secret backend using lpass CLI
"""

import json
import subprocess
from typing import Dict

from .base import SecretBackend


class LastPassBackend(SecretBackend):
    """LastPass secret backend using lpass command line tool"""

    def __init__(self, folder: str = "mcp-hub"):
        self.folder = folder
        self._check_lpass_available()

    def _check_lpass_available(self):
        """Check if lpass is installed and user is logged in"""
        try:
            subprocess.run(
                ["lpass", "status"], check=True, capture_output=True, text=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "LastPass CLI not available or not logged in. "
                "Install with 'brew install lastpass-cli' and login with 'lpass login'"
            )

    def _get_secret_name(self, name: str) -> str:
        """Get the full LastPass secret name"""
        return f"{self.folder}/{name}"

    def get_secret(self, name: str) -> str:
        """Retrieve a secret from LastPass"""
        full_name = self._get_secret_name(name)
        try:
            result = subprocess.run(
                ["lpass", "show", "--password", full_name],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise KeyError(f"Secret '{name}' not found in LastPass")

    def set_secret(self, name: str, value: str) -> None:
        """Store a secret in LastPass"""
        full_name = self._get_secret_name(name)
        # Create a secure note with the secret
        process = subprocess.Popen(
            ["lpass", "add", "--non-interactive", "--note", full_name],
            stdin=subprocess.PIPE,
            text=True,
        )
        process.communicate(input=value)
        if process.returncode != 0:
            raise RuntimeError(f"Failed to store secret '{name}' in LastPass")

    def list_secrets(self) -> Dict[str, str]:
        """List all secrets in the MCP folder"""
        try:
            result = subprocess.run(
                ["lpass", "ls", self.folder], check=True, capture_output=True, text=True
            )
            secrets = {}
            for line in result.stdout.strip().split("\n"):
                if line and "/" in line:
                    # Parse LastPass ls output
                    name = line.split("/")[-1].split(" [")[0]
                    secrets[name] = f"{self.folder}/{name}"
            return secrets
        except subprocess.CalledProcessError:
            return {}

    def delete_secret(self, name: str) -> None:
        """Delete a secret from LastPass"""
        full_name = self._get_secret_name(name)
        try:
            subprocess.run(["lpass", "rm", full_name], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise KeyError(f"Secret '{name}' not found in LastPass")
