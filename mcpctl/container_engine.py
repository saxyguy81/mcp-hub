"""
Container Engine Abstraction Layer
Supports both Docker and Vessel container runtimes
"""

import shutil
import subprocess
import time
from typing import List, Any, Optional

def _detect_engine() -> str:
    """Detect available container engine"""
    if shutil.which("docker"):
        return "docker"
    if shutil.which("vessel"):
        return "vessel"
    raise RuntimeError("Neither docker nor vessel found. Please install Docker Desktop or Vessel.")

# Global engine detection
ENGINE = _detect_engine()

def run(cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
    """Execute container engine command"""
    full_cmd = [ENGINE] + cmd
    return subprocess.run(full_cmd, check=True, **kwargs)

def compose_up(compose_file: str = "docker-compose.yml", detach: bool = True, 
               build: bool = False, services: Optional[List[str]] = None) -> None:
    """Start services using compose"""
    cmd = ["compose", "-f", compose_file, "up"]
    if detach:
        cmd.append("-d")
    if build:
        cmd.append("--build")
    if services:
        cmd.extend(services)
    
    run(cmd)

def compose_down(compose_file: str = "docker-compose.yml") -> None:
    """Stop services using compose"""
    cmd = ["compose", "-f", compose_file, "down"]
    run(cmd)

def compose_ps(compose_file: str = "docker-compose.yml") -> subprocess.CompletedProcess:
    """List running services"""
    cmd = ["compose", "-f", compose_file, "ps"]
    return run(cmd, capture_output=False)

def exec_service(service_name: str, command: List[str]) -> subprocess.CompletedProcess:
    """Execute command in running service"""
    cmd = ["exec", service_name] + command
    return run(cmd, capture_output=True, text=True)

def health_check(service_name: str) -> bool:
    """Check if service is healthy"""
    try:
        result = exec_service(service_name, ["curl", "-fsSL", "http://localhost:8080/health"])
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def start_vessel_compat_if_needed() -> None:
    """Start Vessel Docker compatibility daemon if using Vessel on macOS"""
    if ENGINE == "vessel":
        try:
            run(["compat"], timeout=10)
            time.sleep(4)  # Wait for dockerd socket to be available
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Compat daemon might already be running
            pass

def get_engine_info() -> dict:
    """Get information about the container engine"""
    return {
        "engine": ENGINE,
        "version": _get_version(),
        "available": True
    }

def _get_version() -> str:
    """Get container engine version"""
    try:
        result = run(["--version"], capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"
