"""
Enhanced MCP Proxy CLI Commands
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests
import typer

# Import from existing CLI
try:
    from .cli import app as main_app
    from .cli import load_config
except ImportError:
    # Fallback for standalone usage
    main_app = typer.Typer()

    def load_config():
        return {}


# Create proxy subcommand group
proxy_app = typer.Typer(name="proxy", help="🎯 Manage MCP Hub aggregation proxy")
main_app.add_typer(proxy_app, name="proxy")

# Global proxy state tracking
PROXY_PID_FILE = Path.home() / ".mcpctl" / "proxy.pid"
PROXY_LOG_FILE = Path.home() / ".mcpctl" / "proxy.log"


def ensure_config_dir():
    """Ensure config directory exists"""
    config_dir = Path.home() / ".mcpctl"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_proxy_pid() -> Optional[int]:
    """Get running proxy PID if any"""
    if PROXY_PID_FILE.exists():
        try:
            with open(PROXY_PID_FILE, "r") as f:
                pid = int(f.read().strip())

            # Check if process is still running
            try:
                os.kill(pid, 0)  # Doesn't actually kill, just checks
                return pid
            except OSError:
                # Process not running, clean up pid file
                PROXY_PID_FILE.unlink()
                return None
        except:
            return None
    return None


def save_proxy_pid(pid: int):
    """Save proxy PID to file"""
    ensure_config_dir()
    with open(PROXY_PID_FILE, "w") as f:
        f.write(str(pid))


def check_proxy_status() -> dict:
    """Check if proxy is running and healthy"""
    try:
        response = requests.get("http://localhost:3000/health", timeout=3)
        return {
            "running": True,
            "healthy": response.status_code == 200,
            "data": response.json() if response.status_code == 200 else None,
        }
    except requests.exceptions.ConnectionError:
        return {"running": False, "healthy": False, "data": None}
    except Exception as e:
        return {"running": False, "healthy": False, "error": str(e)}


@proxy_app.command("start")
def start_proxy(
    port: int = typer.Option(3000, help="Port for proxy server"),
    background: bool = typer.Option(True, help="Run in background"),
    config_file: str = typer.Option("docker-compose.yml", help="Docker compose file"),
    auto_start_services: bool = typer.Option(
        True, help="Auto-start MCP services if not running"
    ),
):
    """🚀 Start the MCP aggregation proxy server"""

    # Check if proxy is already running
    existing_pid = get_proxy_pid()
    if existing_pid:
        status = check_proxy_status()
        if status["running"]:
            typer.echo(f"✅ Proxy already running (PID: {existing_pid})")
            typer.echo(f"📍 Endpoint: http://localhost:3000")
            return
        else:
            typer.echo(f"🧹 Cleaning up stale PID file...")
            PROXY_PID_FILE.unlink(missing_ok=True)

    # Check if compose file exists
    compose_path = Path(config_file)
    if not compose_path.exists():
        typer.echo(f"❌ Compose file not found: {config_file}", err=True)
        typer.echo("💡 Run 'mcpctl setup --wizard' first to create services", err=True)
        raise typer.Exit(1)

    # Check if services are running
    if auto_start_services:
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--services", "--filter", "status=running"],
                cwd=".",
                capture_output=True,
                text=True,
                check=True,
            )

            running_services = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
            if not running_services:
                typer.echo("⚡ No MCP services running. Starting services first...")
                subprocess.run(["docker", "compose", "up", "-d"], check=True, cwd=".")
                typer.echo("✅ Services started")

                # Wait for services to be ready
                typer.echo("⏳ Waiting for services to be ready...")
                time.sleep(5)

        except subprocess.CalledProcessError as e:
            typer.echo(f"❌ Failed to check/start services: {e}", err=True)
            typer.echo("💡 Make sure Docker is running and try again", err=True)
            raise typer.Exit(1)

    # Get proxy script path
    proxy_script = Path(__file__).parent / "mcp_proxy.py"
    if not proxy_script.exists():
        typer.echo(f"❌ Proxy script not found: {proxy_script}", err=True)
        raise typer.Exit(1)

    # Prepare proxy command
    cmd = [
        sys.executable,
        str(proxy_script),
        "--port",
        str(port),
        "--config",
        config_file,
        "--log-level",
        "INFO",
    ]

    if background:
        ensure_config_dir()
        cmd.extend(["--log-file", str(PROXY_LOG_FILE)])

    try:
        if background:
            # Start in background
            typer.echo("🚀 Starting MCP Hub proxy in background...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            save_proxy_pid(process.pid)

            # Wait a moment and check if it started successfully
            time.sleep(2)
            status = check_proxy_status()

            if status["running"] and status["healthy"]:
                typer.echo(f"✅ Proxy started successfully (PID: {process.pid})")
                typer.echo(f"📍 Single endpoint: http://localhost:{port}")

                # Show backend status
                if status["data"]:
                    backend_count = status["data"].get("servers", 0)
                    healthy_count = status["data"].get("healthy_servers", 0)
                    typer.echo(
                        f"📊 Backend: {healthy_count}/{backend_count} servers healthy"
                    )

                typer.echo("\n🎯 LLM Client Configuration:")
                typer.echo(f"   Add this single endpoint to your LLM client:")
                typer.echo(f"   📍 http://localhost:{port}")
                typer.echo("\n💡 Use 'mcpctl proxy status' to monitor health")
            else:
                typer.echo("❌ Proxy failed to start properly", err=True)
                typer.echo("💡 Check logs with: mcpctl proxy logs", err=True)
                raise typer.Exit(1)
        else:
            # Run in foreground
            typer.echo("🚀 Starting MCP Hub proxy (foreground mode)...")
            typer.echo("   Press Ctrl+C to stop")
            subprocess.run(cmd)

    except KeyboardInterrupt:
        typer.echo("\n🛑 Proxy stopped by user")
    except Exception as e:
        typer.echo(f"❌ Failed to start proxy: {e}", err=True)
        raise typer.Exit(1)


@proxy_app.command("stop")
def stop_proxy():
    """🛑 Stop the MCP proxy server"""

    # Check if proxy is running
    pid = get_proxy_pid()
    if not pid:
        status = check_proxy_status()
        if not status["running"]:
            typer.echo("ℹ️  Proxy server not running")
            return
        else:
            typer.echo(
                "⚠️  Proxy running but PID file missing. Trying to stop via HTTP..."
            )

    try:
        if pid:
            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)

            # Wait for graceful shutdown
            for i in range(10):
                try:
                    os.kill(pid, 0)  # Check if still running
                    time.sleep(0.5)
                except OSError:
                    # Process has stopped
                    break
            else:
                # Force kill if graceful shutdown failed
                typer.echo("⚡ Force stopping proxy...")
                os.kill(pid, signal.SIGKILL)

            typer.echo(f"✅ Stopped proxy server (PID: {pid})")

        # Clean up PID file
        PROXY_PID_FILE.unlink(missing_ok=True)

        # Verify it's actually stopped
        status = check_proxy_status()
        if not status["running"]:
            typer.echo("✅ Proxy fully stopped")
        else:
            typer.echo("⚠️  Proxy may still be running on different PID")

    except ProcessLookupError:
        typer.echo("ℹ️  Proxy process already stopped")
        PROXY_PID_FILE.unlink(missing_ok=True)
    except PermissionError:
        typer.echo("❌ Permission denied stopping proxy", err=True)
        typer.echo("💡 Try running with sudo or check process ownership", err=True)
    except Exception as e:
        typer.echo(f"❌ Error stopping proxy: {e}", err=True)


@proxy_app.command("status")
def proxy_status():
    """📊 Show proxy server status and connected services"""

    # Check if proxy process is running
    pid = get_proxy_pid()
    status = check_proxy_status()

    if not status["running"]:
        typer.echo("🔴 MCP Hub Proxy: NOT RUNNING")
        if pid:
            typer.echo(f"⚠️  Stale PID file found (PID: {pid})")
        typer.echo("\n💡 Start with: mcpctl proxy start")
        return

    typer.echo("🟢 MCP Hub Proxy: RUNNING")
    if pid:
        typer.echo(f"📍 PID: {pid}")
    typer.echo(f"📍 Endpoint: http://localhost:3000")

    if status["healthy"] and status["data"]:
        data = status["data"]
        typer.echo(
            f"📊 Backend Servers: {data.get('healthy_servers', 0)}/{data.get('servers', 0)} healthy"
        )

        # Get detailed status
        try:
            response = requests.get("http://localhost:3000/status", timeout=5)
            if response.status_code == 200:
                detailed_status = response.json()

                typer.echo("\n🔗 Backend Services:")
                for name, info in detailed_status.get("servers", {}).items():
                    status_icon = "🟢" if info["healthy"] else "🔴"
                    error_info = (
                        f" (errors: {info['error_count']})"
                        if info["error_count"] > 0
                        else ""
                    )
                    typer.echo(f"  {status_icon} {name}: {info['url']}{error_info}")

                # Show mapping info
                tool_count = detailed_status.get("tool_mappings", 0)
                resource_count = detailed_status.get("resource_mappings", 0)
                typer.echo(
                    f"\n📋 Cached Mappings: {tool_count} tools, {resource_count} resources"
                )

        except Exception as e:
            typer.echo(f"\n⚠️  Could not get detailed status: {e}")

    else:
        typer.echo("🔴 Proxy unhealthy or unreachable")

    typer.echo("\n📋 LLM Client Configuration:")
    typer.echo("   Configure your LLM client with this single endpoint:")
    typer.echo("   🎯 http://localhost:3000")
    typer.echo("\n💡 View logs: mcpctl proxy logs")
    typer.echo("💡 List servers: mcpctl proxy servers")


@proxy_app.command("logs")
def proxy_logs(
    lines: int = typer.Option(50, help="Number of lines to show"),
    follow: bool = typer.Option(False, help="Follow log output"),
):
    """📜 Show proxy server logs"""

    if not PROXY_LOG_FILE.exists():
        typer.echo("📜 No proxy logs found")
        typer.echo("💡 Logs are only created when proxy runs in background mode")
        return

    try:
        if follow:
            # Follow logs (like tail -f)
            typer.echo(f"📜 Following proxy logs from {PROXY_LOG_FILE}")
            typer.echo("   Press Ctrl+C to stop\n")

            subprocess.run(["tail", "-f", "-n", str(lines), str(PROXY_LOG_FILE)])
        else:
            # Show last N lines
            typer.echo(f"📜 Last {lines} lines from {PROXY_LOG_FILE}:\n")

            result = subprocess.run(
                ["tail", "-n", str(lines), str(PROXY_LOG_FILE)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                typer.echo(result.stdout)
            else:
                typer.echo("❌ Failed to read logs")

    except KeyboardInterrupt:
        typer.echo("\n📜 Stopped following logs")
    except Exception as e:
        typer.echo(f"❌ Error reading logs: {e}", err=True)


@proxy_app.command("servers")
def list_servers():
    """🔗 List all backend MCP servers"""

    status = check_proxy_status()
    if not status["running"]:
        typer.echo("❌ Proxy not running")
        typer.echo("💡 Start with: mcpctl proxy start")
        return

    try:
        response = requests.get("http://localhost:3000/servers", timeout=5)
        if response.status_code != 200:
            typer.echo("❌ Failed to get server list")
            return

        data = response.json()
        servers = data.get("servers", [])

        if not servers:
            typer.echo("📭 No servers configured")
            return

        typer.echo(f"🔗 MCP Backend Servers ({len(servers)} total):")
        typer.echo("=" * 50)

        for server in servers:
            status_icon = "🟢" if server["healthy"] else "🔴"
            name = server["name"]
            url = server["url"]

            typer.echo(f"\n{status_icon} {name}")
            typer.echo(f"   URL: {url}")

            if server["last_check"]:
                typer.echo(f"   Last Check: {server['last_check']}")

            if server["error_count"] > 0:
                typer.echo(f"   Errors: {server['error_count']}")

            # Show capabilities if available
            caps = server.get("capabilities", {})
            if caps:
                cap_types = [k for k in caps.keys() if caps[k]]
                if cap_types:
                    typer.echo(f"   Capabilities: {', '.join(cap_types)}")

    except Exception as e:
        typer.echo(f"❌ Error getting server list: {e}", err=True)


@proxy_app.command("restart")
def restart_proxy():
    """🔄 Restart the proxy server"""
    typer.echo("🔄 Restarting MCP Hub proxy...")

    # Stop if running
    try:
        stop_proxy()
        time.sleep(1)
    except:
        pass

    # Start again
    start_proxy()


# Enhanced main connect command
@main_app.command("connect")
def show_connection_info():
    """🔗 Show connection information for LLM clients"""

    # Check if proxy is running
    proxy_status = check_proxy_status()

    if proxy_status["running"] and proxy_status["healthy"]:
        typer.echo("🎯 SINGLE ENDPOINT MODE (Recommended)")
        typer.echo("=" * 40)
        typer.echo("✨ Your MCP Hub proxy is running!")
        typer.echo()
        typer.echo("🔗 Configure your LLM client with:")
        typer.echo("   📍 http://localhost:3000")
        typer.echo()
        typer.echo("✅ This single endpoint provides access to all your MCP servers")

        # Show backend status
        if proxy_status["data"]:
            backend_count = proxy_status["data"].get("servers", 0)
            healthy_count = proxy_status["data"].get("healthy_servers", 0)
            typer.echo(f"📊 Backend: {healthy_count}/{backend_count} servers healthy")

        typer.echo("\n💡 Management commands:")
        typer.echo("   📊 mcpctl proxy status   - Check proxy health")
        typer.echo("   🔗 mcpctl proxy servers  - List backend servers")
        typer.echo("   📜 mcpctl proxy logs     - View proxy logs")

    else:
        typer.echo("🔗 MULTI-ENDPOINT MODE")
        typer.echo("=" * 25)
        typer.echo("⚠️  Proxy not running - using individual server endpoints")
        typer.echo()
        typer.echo("💡 For easier setup, start the proxy:")
        typer.echo("   🚀 mcpctl proxy start")
        typer.echo()

        # Show individual endpoints (fallback mode)
        try:
            from .onboarding import get_connection_info

            connection_info = get_connection_info()

            if connection_info.get("mcp_endpoints"):
                typer.echo("🔗 Individual endpoints (current configuration):")
                for url in connection_info["mcp_endpoints"]:
                    typer.echo(f"   📍 {url}")
            else:
                typer.echo("❌ No services running")
                typer.echo("🚀 Start with: mcpctl start")
        except ImportError:
            typer.echo("📍 Check individual service ports with: mcpctl status")
