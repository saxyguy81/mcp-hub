"""
Image Digest Management for reproducible deployments
Handles locking images to specific digest hashes and pull-by-digest operations
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import typer
from . import container_engine

# Make Docker import optional to avoid CI conflicts
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

@dataclass
class ImageDigest:
    """Represents a locked image with its digest"""
    tag: str
    digest: str
    platform: str
    last_updated: str

@dataclass 
class ImagesLock:
    """Container for all locked image digests"""
    version: str = "1.0"
    images: Dict[str, ImageDigest] = None
    
    def __post_init__(self):
        if self.images is None:
            self.images = {}

class DigestManager:
    """Manages image digest locking and pulling"""
    
    def __init__(self, lock_file: str = "images.lock.json"):
        self.lock_file = Path(lock_file)
        self.docker_client = None
        
    def _get_docker_client(self):
        """Get Docker client, handling both Docker and Vessel"""
        if self.docker_client is None:
            if not DOCKER_AVAILABLE:
                typer.echo("⚠️ Docker Python package not available, using CLI fallback", err=True)
                return None
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                typer.echo(f"Warning: Could not connect to Docker API: {e}", err=True)
                typer.echo("Will use CLI commands instead", err=True)
        return self.docker_client

    def gather_digests(self, tags: List[str]) -> Dict[str, ImageDigest]:
        """Gather digest information for a list of image tags"""
        digests = {}
        client = self._get_docker_client()
        
        for tag in tags:
            try:
                if client:
                    # Use Docker API
                    image = client.images.get(tag)
                    repo_digests = image.attrs.get('RepoDigests', [])
                    
                    if repo_digests:
                        digest = repo_digests[0]
                        platform = image.attrs.get('Architecture', 'unknown')
                    else:
                        # Image might be local-only, try to get digest another way
                        digest = image.id
                        platform = 'local'
                else:
                    # Use CLI fallback
                    result = container_engine.run([
                        "inspect", tag, "--format", "{{index .RepoDigests 0}}"
                    ], capture_output=True, text=True)
                    
                    digest = result.stdout.strip()
                    if not digest:
                        digest = tag  # Fallback to tag if no digest available
                    platform = 'unknown'
                
                digests[tag] = ImageDigest(
                    tag=tag,
                    digest=digest,
                    platform=platform,
                    last_updated=self._get_current_timestamp()
                )
                
                typer.echo(f"✓ Locked {tag} -> {digest[:20]}...")
                
            except Exception as e:
                typer.echo(f"⚠ Warning: Could not get digest for {tag}: {e}", err=True)
                # Still create an entry with the tag as fallback
                digests[tag] = ImageDigest(
                    tag=tag,
                    digest=tag,
                    platform='unknown', 
                    last_updated=self._get_current_timestamp()
                )
        
        return digests

    def save_lock_file(self, digests: Dict[str, ImageDigest]) -> None:
        """Save digests to lock file"""
        lock_data = ImagesLock(images=digests)
        
        with open(self.lock_file, 'w') as f:
            json.dump(asdict(lock_data), f, indent=2)
        
        typer.echo(f"💾 Saved {len(digests)} image digests to {self.lock_file}")
    
    def load_lock_file(self) -> ImagesLock:
        """Load digests from lock file"""
        if not self.lock_file.exists():
            return ImagesLock()
        
        try:
            with open(self.lock_file, 'r') as f:
                data = json.load(f)
            
            # Convert dict back to ImageDigest objects
            images = {}
            for tag, img_data in data.get('images', {}).items():
                images[tag] = ImageDigest(**img_data)
            
            return ImagesLock(
                version=data.get('version', '1.0'),
                images=images
            )
        except Exception as e:
            typer.echo(f"Error loading lock file: {e}", err=True)
            return ImagesLock()

    def pull_images_by_digest(self) -> bool:
        """Pull all images using their locked digests"""
        lock = self.load_lock_file()
        
        if not lock.images:
            typer.echo("No locked images found. Run 'lock-images' first.", err=True)
            return False
        
        success = True
        for tag, image_digest in lock.images.items():
            try:
                if image_digest.digest.startswith('sha256:'):
                    # Pull by digest
                    pull_target = image_digest.digest
                else:
                    # Fallback to tag if digest is not available
                    pull_target = tag
                
                typer.echo(f"🔄 Pulling {tag} from {pull_target[:30]}...")
                container_engine.run(["pull", pull_target])
                
                # Tag the image if we pulled by digest
                if pull_target != tag:
                    container_engine.run(["tag", pull_target, tag])
                
                typer.echo(f"✅ {tag} pulled successfully")
                
            except subprocess.CalledProcessError as e:
                typer.echo(f"❌ Failed to pull {tag}: {e}", err=True)
                success = False
        
        return success
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def update_compose_with_digests(self, compose_file: Path) -> None:
        """Update docker-compose.yml to use digest-locked images"""
        import yaml
        
        lock = self.load_lock_file()
        if not lock.images:
            typer.echo("No locked images found", err=True)
            return
        
        try:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            services = compose_data.get('services', {})
            updated = 0
            
            for service_name, service_config in services.items():
                image = service_config.get('image')
                if image and image in lock.images:
                    old_image = image
                    new_image = lock.images[image].digest
                    service_config['image'] = new_image
                    typer.echo(f"📝 {service_name}: {old_image} -> {new_image[:30]}...")
                    updated += 1
            
            if updated > 0:
                # Backup original
                backup_file = compose_file.with_suffix('.yml.backup')
                compose_file.rename(backup_file)
                
                with open(compose_file, 'w') as f:
                    yaml.dump(compose_data, f, default_flow_style=False)
                
                typer.echo(f"✅ Updated {updated} services with digest locks")
                typer.echo(f"📄 Original backed up to {backup_file}")
            else:
                typer.echo("No services found with locked images")
                
        except Exception as e:
            typer.echo(f"Error updating compose file: {e}", err=True)
