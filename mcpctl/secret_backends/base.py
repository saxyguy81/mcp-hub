"""
Abstract base class for secret backends
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class SecretBackend(ABC):
    """Abstract interface for secret management backends"""

    @abstractmethod
    def get_secret(self, name: str) -> str:
        """Retrieve a secret by name"""
        pass

    @abstractmethod
    def set_secret(self, name: str, value: str) -> None:
        """Store a secret"""
        pass

    @abstractmethod
    def list_secrets(self) -> Dict[str, str]:
        """List all available secrets"""
        pass

    @abstractmethod
    def delete_secret(self, name: str) -> None:
        """Delete a secret"""
        pass
