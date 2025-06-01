"""
Base VCS interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class VCSBackend(ABC):
    """Abstract interface for version control systems"""
    
    @abstractmethod
    def create_repository(self, name: str) -> str:
        """Create a new repository"""
        pass
    
    @abstractmethod
    def push_code(self, repo_url: str, local_path: str) -> None:
        """Push local code to repository"""
        pass
