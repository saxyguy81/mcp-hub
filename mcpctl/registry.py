"""
Registry management for MCP Hub
"""

import docker
from pathlib import Path
from typing import List

class RegistryManager:
    """Manages Docker registry operations"""
    
    def __init__(self, config):
        self.config = config
        self.client = docker.from_env()
    
    def push_images(self, tag: str = "latest") -> None:
        """Push all MCP images to registry"""
        images = self._get_mcp_images()
        
        for image in images:
            registry_tag = f"{self.config.docker_registry}/{image.tags[0]}"
            image.tag(registry_tag, tag)
            
            # Push to registry
            self.client.images.push(registry_tag, tag=tag)
    
    def save_images_tarball(self, tag: str = "latest") -> Path:
        """Save images as tarball for offline distribution"""
        images = self._get_mcp_images()
        image_names = [img.tags[0] for img in images if img.tags]
        
        tarball_path = Path("mcp-hub-images.tar")
        
        # Save images to tarball
        with open(tarball_path, "wb") as f:
            for chunk in self.client.api.get_images(image_names):
                f.write(chunk)
        
        return tarball_path
    
    def _get_mcp_images(self) -> List:
        """Get all MCP-related Docker images"""
        all_images = self.client.images.list()
        mcp_images = []
        
        for image in all_images:
            if image.tags:
                for tag in image.tags:
                    if "mcp" in tag.lower():
                        mcp_images.append(image)
                        break
        
        return mcp_images
