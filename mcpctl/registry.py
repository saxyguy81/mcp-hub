"""
Registry management for MCP Hub with CLI fallback
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import typer

# Try to import docker, but make it optional
try:
    import docker

    DOCKER_API_AVAILABLE = True
except ImportError:
    DOCKER_API_AVAILABLE = False
    docker = None


class RegistryManager:
    """Manages Docker registry operations with CLI fallback"""

    def __init__(self, config):
        self.config = config
        self.client = None

        # Try to initialize Docker client if available
        if DOCKER_API_AVAILABLE:
            try:
                self.client = docker.from_env()
                # Test connection
                self.client.ping()
            except Exception as e:
                typer.echo(f"⚠️  Docker API not available, using CLI fallback: {e}")
                self.client = None

    def push_images(self, tag: str = "latest") -> None:
        """Build and push all MCP images to registry"""
        if self.client:
            self._push_images_api(tag)
        else:
            self._push_images_cli(tag)

    def _push_images_cli(self, tag: str = "latest") -> None:
        """Push images using Docker CLI commands"""
        # First, build the images
        self._build_images_cli(tag)

        # Set default registry if not configured
        registry = self.config.docker_registry or "ghcr.io"

        # Define the images we expect to build
        image_name = f"{registry}/web"
        full_tag = f"{image_name}:{tag}"

        typer.echo(f"Pushing {full_tag} using Docker CLI")

        try:
            # Push the image
            result = subprocess.run(
                ["docker", "push", full_tag], capture_output=True, text=True, check=True
            )

            typer.echo(f"✅ Pushed {full_tag}")

            # Also push latest tag if this isn't latest
            if tag != "latest":
                latest_tag = f"{image_name}:latest"
                typer.echo(f"Pushing {latest_tag}")
                subprocess.run(
                    ["docker", "push", latest_tag],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                typer.echo(f"✅ Pushed {latest_tag}")

        except subprocess.CalledProcessError as e:
            typer.echo(f"❌ Failed to push images: {e}")
            typer.echo(f"stdout: {e.stdout}")
            typer.echo(f"stderr: {e.stderr}")
            raise

    def save_images_tarball(self, tag: str = "latest") -> Path:
        """Build and save images as tarball for offline distribution"""
        if self.client:
            return self._save_images_tarball_api(tag)
        else:
            return self._save_images_tarball_cli(tag)

    def _save_images_tarball_cli(self, tag: str = "latest") -> Path:
        """Save images using Docker CLI commands"""
        # First, build the images
        self._build_images_cli(tag)

        # Set default registry if not configured
        registry = self.config.docker_registry or "ghcr.io"

        # Define the images we expect to build
        image_name = f"{registry}/web"
        images_to_save = [f"{image_name}:{tag}"]

        if tag != "latest":
            images_to_save.append(f"{image_name}:latest")

        typer.echo(
            f"Saving {len(images_to_save)} MCP images to tarball using Docker CLI"
        )

        tarball_path = Path("mcp-hub-images.tar")

        try:
            # Save images to tarball
            cmd = ["docker", "save", "-o", str(tarball_path)] + images_to_save
            subprocess.run(cmd, check=True)

            typer.echo(f"✅ Saved images to {tarball_path}")
            return tarball_path

        except subprocess.CalledProcessError as e:
            typer.echo(f"❌ Failed to save images: {e}")
            raise

    def _build_images_cli(self, tag: str = "latest") -> None:
        """Build MCP Hub Docker images using CLI commands"""
        typer.echo("🔨 Building MCP Hub Docker images using Docker CLI...")

        # Use configured registry or default
        if self.config.docker_registry:
            base_registry = self.config.docker_registry
        else:
            base_registry = "ghcr.io/saxyguy81/mcp-hub"

        # Build web service image
        web_dockerfile = Path("web/Dockerfile")
        if web_dockerfile.exists():
            image_name = f"{base_registry}/web"
            typer.echo(f"Building web service: {image_name}:{tag}")

            try:
                # Build the image from repository root
                cmd = [
                    "docker",
                    "build",
                    "-f",
                    "web/Dockerfile",
                    "-t",
                    f"{image_name}:{tag}",
                    ".",
                ]

                subprocess.run(cmd, check=True)

                # Also tag as latest if not already latest
                if tag != "latest":
                    subprocess.run(
                        [
                            "docker",
                            "tag",
                            f"{image_name}:{tag}",
                            f"{image_name}:latest",
                        ],
                        check=True,
                    )

                typer.echo(f"✅ Built {image_name}:{tag}")

            except subprocess.CalledProcessError as e:
                typer.echo(f"❌ Error building web service: {e}")
                raise
        else:
            typer.echo("⚠️  No web/Dockerfile found, skipping web service build")

    # Legacy API methods for backward compatibility
    def _push_images_api(self, tag: str = "latest") -> None:
        """Push images using Docker Python API - fallback to CLI if needed"""
        try:
            self._build_images_api(tag)
            images = self._get_mcp_images_api()
            registry = self.config.docker_registry or "ghcr.io"

            for image in images:
                if image.tags:
                    for image_tag in image.tags:
                        if registry in image_tag:
                            repository, tag_part = (
                                image_tag.rsplit(":", 1)
                                if ":" in image_tag
                                else (image_tag, "latest")
                            )
                            self.client.images.push(repository, tag=tag_part)
                            typer.echo(f"✅ Pushed {image_tag}")
        except Exception as e:
            typer.echo(f"⚠️ API method failed, falling back to CLI: {e}")
            self._push_images_cli(tag)

    def _build_images_api(self, tag: str = "latest") -> None:
        """Build using API - fallback to CLI if needed"""
        try:
            base_registry = self.config.docker_registry or "ghcr.io/saxyguy81/mcp-hub"
            web_dockerfile = Path("web/Dockerfile")
            if web_dockerfile.exists():
                image_name = f"{base_registry}/web"
                image, logs = self.client.images.build(
                    path=".",
                    dockerfile="web/Dockerfile",
                    tag=f"{image_name}:{tag}",
                    rm=True,
                    pull=True,
                )
                if tag != "latest":
                    image.tag(image_name, "latest")
                typer.echo(f"✅ Built {image_name}:{tag}")
        except Exception as e:
            typer.echo(f"⚠️ API build failed, falling back to CLI: {e}")
            self._build_images_cli(tag)

    def _get_mcp_images_api(self) -> List:
        """Get MCP images using API"""
        all_images = self.client.images.list()
        mcp_images = []
        registry = self.config.docker_registry or "ghcr.io"
        for image in all_images:
            if image.tags:
                for tag in image.tags:
                    if ("mcp-hub" in tag.lower() or "mcp" in tag.lower()) or (
                        registry in tag and ("web" in tag or "mcp" in tag)
                    ):
                        mcp_images.append(image)
                        break
        return mcp_images

    def _save_images_tarball_api(self, tag: str = "latest") -> Path:
        """Save using API - fallback to CLI if needed"""
        try:
            self._build_images_api(tag)
            images = self._get_mcp_images_api()
            if not images:
                return Path("mcp-hub-images.tar")

            image_names = [img.tags[0] for img in images if img.tags]
            tarball_path = Path("mcp-hub-images.tar")
            with open(tarball_path, "wb") as f:
                for image_name in image_names:
                    image_data = self.client.api.get_image(image_name)
                    for chunk in image_data:
                        f.write(chunk)
            return tarball_path
        except Exception as e:
            typer.echo(f"⚠️ API save failed, falling back to CLI: {e}")
            return self._save_images_tarball_cli(tag)
