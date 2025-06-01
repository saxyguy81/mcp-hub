"""
Registry management for MCP Hub
"""

import docker
from pathlib import Path
from typing import List
import typer

class RegistryManager:
    """Manages Docker registry operations"""
    
    def __init__(self, config):
        self.config = config
        self.client = docker.from_env()
    
    def push_images(self, tag: str = "latest") -> None:
        """Build and push all MCP images to registry"""
        # First, build the images
        self._build_images(tag)
        
        # Then get the built images and push them
        images = self._get_mcp_images()
        
        if not images:
            typer.echo("No MCP images found to push")
            return
        
        typer.echo(f"Found {len(images)} MCP images to push")
        
        for image in images:
            if not image.tags:
                typer.echo(f"Skipping untagged image: {image.id[:12]}")
                continue
                
            # Images should already be tagged for registry during build
            for image_tag in image.tags:
                if self.config.docker_registry in image_tag:
                    typer.echo(f"Pushing {image_tag}")
                    repository, tag_part = image_tag.split(':') if ':' in image_tag else (image_tag, 'latest')
                    self.client.images.push(repository, tag=tag_part)
                    typer.echo(f"✅ Pushed {image_tag}")
    
    def save_images_tarball(self, tag: str = "latest") -> Path:
        """Build and save images as tarball for offline distribution"""
        # First, build the images
        self._build_images(tag)
        
        # Then get the built images and save them
        images = self._get_mcp_images()
        
        if not images:
            typer.echo("No MCP images found to save")
            # Create empty tarball
            tarball_path = Path("mcp-hub-images.tar")
            tarball_path.touch()
            return tarball_path
        
        image_names = [img.tags[0] for img in images if img.tags]
        typer.echo(f"Saving {len(image_names)} MCP images to tarball")
        
        tarball_path = Path("mcp-hub-images.tar")
        
        # Save images to tarball
        with open(tarball_path, "wb") as f:
            for image_name in image_names:
                typer.echo(f"Exporting {image_name}...")
                # Use the correct Docker API method to get image data
                image_data = self.client.api.get_image(image_name)
                for chunk in image_data:
                    f.write(chunk)
        
        typer.echo(f"✅ Saved images to {tarball_path}")
        return tarball_path
    
    def _build_images(self, tag: str = "latest") -> None:
        """Build MCP Hub Docker images"""
        typer.echo("🔨 Building MCP Hub Docker images...")
        
        # Build web service image
        web_dockerfile = Path("web/Dockerfile")
        if web_dockerfile.exists():
            image_name = f"{self.config.docker_registry}/mcp-hub-web"
            typer.echo(f"Building web service: {image_name}:{tag}")
            
            try:
                # Build the image from repository root to access parent directories
                image, logs = self.client.images.build(
                    path=".",  # Build from repository root
                    dockerfile="web/Dockerfile",  # Dockerfile path relative to root
                    tag=f"{image_name}:{tag}",
                    rm=True,
                    pull=True
                )
                
                # Also tag as latest if not already latest
                if tag != "latest":
                    image.tag(image_name, "latest")
                
                typer.echo(f"✅ Built {image_name}:{tag}")
                
            except Exception as e:
                typer.echo(f"❌ Error building web service: {e}")
                raise
        else:
            typer.echo("⚠️  No web/Dockerfile found, skipping web service build")
        
        # Could add more image builds here in the future
        # e.g., CLI container, additional services, etc.
    
    def _get_mcp_images(self) -> List:
        """Get all MCP-related Docker images"""
        all_images = self.client.images.list()
        mcp_images = []
        
        typer.echo(f"Scanning {len(all_images)} total images for MCP images...")
        
        for image in all_images:
            if image.tags:
                for tag in image.tags:
                    # Look for images with mcp-hub in the name or our registry prefix
                    if ("mcp-hub" in tag.lower() or 
                        "mcp" in tag.lower() or 
                        (self.config.docker_registry and self.config.docker_registry in tag)):
                        mcp_images.append(image)
                        typer.echo(f"Found MCP image: {tag}")
                        break
        
        typer.echo(f"Found {len(mcp_images)} MCP images total")
        return mcp_images
