"""
MCP Proxy Server Integration for mcpctl
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional
import typer

from .cli import app as main_app

# Add proxy management commands to the main CLI
proxy_app = typer.Typer(name="proxy", help="Manage MCP Hub proxy server")
main_app.add_typer(proxy_app, name="proxy")

@proxy_app.command("start")
def start_proxy(
    port: int = typer.Option(3000, help="Port for proxy server"),
    background: bool = typer.Option(True, help="Run in background"),
    auto_discover: bool = typer.Option(True, help="Auto-discover services from compose file")
):
    """Start the MCP aggregation proxy server"""
    
    # Check if services are running first
    if not Path("docker-compose.yml").exists():
        typer.echo("❌ No docker-compose.yml found. Run 'mcpctl setup --wizard' first.", err=True)
        raise typer.Exit(1)
    
    try:
        # Check if any services are running
        result = subprocess.run(
            ["docker", "compose", "ps", "--services", "--filter", "status=running"],
            capture_output=True, text=True, check=True
        )
        
        if not result.stdout.strip():
            typer.echo("⚠️  No MCP services running. Starting services first...")
            subprocess.run(["docker", "compose", "up", "-d"], check=True)
            typer.echo("✅ Services started")
    
    except subprocess.CalledProcessError:
        typer.echo("❌ Failed to check/start services", err=True)
        raise typer.Exit(1)
    
    # Start the proxy server
    proxy_script = Path(__file__).parent / "mcp_proxy.py"
    subprocess.run([sys.executable, str(proxy_script), "--port", str(port)])


@proxy_app.command("stop")
def stop_proxy():
    """Stop the MCP proxy server"""
    try:
        # Find and kill proxy process
        result = subprocess.run(
            ["pgrep", "-f", "mcp_proxy.py"],
            capture_output=True, text=True
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(["kill", pid])
            typer.echo(f"✅ Stopped proxy server (PIDs: {', '.join(pids)})")
        else:
            typer.echo("ℹ️  Proxy server not running")
    
    except Exception as e:
        typer.echo(f"❌ Error stopping proxy: {e}", err=True)

@proxy_app.command("status")
def proxy_status():
    """Show proxy server status and connected services"""
    import requests
    
    try:
        response = requests.get("http://localhost:3000/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            typer.echo("🟢 MCP Hub Proxy Status: RUNNING")
            typer.echo(f"📍 Endpoint: http://localhost:3000")
            typer.echo(f"🔗 Backend Servers: {len(data['servers'])}")
            
            for name, info in data['servers'].items():
                status_icon = "🟢" if info['healthy'] else "🔴"
                typer.echo(f"  {status_icon} {name}: {info['url']}")
            
            typer.echo("\n📋 LLM Client Configuration:")
            typer.echo("   Add this single endpoint to your LLM client:")
            typer.echo("   🎯 http://localhost:3000")
        else:
            typer.echo("🔴 Proxy server not responding")
    
    except requests.exceptions.ConnectionError:
        typer.echo("🔴 Proxy server not running")
        typer.echo("💡 Start with: mcpctl proxy start")
    except Exception as e:
        typer.echo(f"❌ Error checking status: {e}")


@main_app.command("connect")
def show_connection_info():
    """Show connection information for LLM clients"""
    
    # Check if proxy is running
    import requests
    proxy_running = False
    
    try:
        response = requests.get("http://localhost:3000/health", timeout=3)
        proxy_running = response.status_code == 200
    except:
        pass
    
    if proxy_running:
        typer.echo("🎯 SINGLE ENDPOINT MODE (Recommended)")
        typer.echo("=====================================")
        typer.echo("✨ Your MCP Hub proxy is running!")
        typer.echo("🔗 Configure your LLM client with:")
        typer.echo("   📍 http://localhost:3000")
        typer.echo()
        typer.echo("✅ This single endpoint provides access to all your MCP servers")
        
        # Show backend status
        try:
            response = requests.get("http://localhost:3000/status", timeout=3)
            data = response.json()
            healthy_count = sum(1 for s in data['servers'].values() if s['healthy'])
            typer.echo(f"📊 Backend: {healthy_count}/{len(data['servers'])} servers healthy")
        except:
            pass
    
    else:
        typer.echo("🔗 MULTI-ENDPOINT MODE")  
        typer.echo("======================")
        typer.echo("⚠️  Using individual server endpoints")
        typer.echo("💡 Consider using proxy mode for easier setup:")
        typer.echo("   mcpctl proxy start")
        typer.echo()
        
        # Show individual endpoints (existing logic)
        from .onboarding import get_connection_info
        connection_info = get_connection_info()
        
        if connection_info["mcp_endpoints"]:
            typer.echo("🔗 Configure your LLM client with these endpoints:")
            for url in connection_info["mcp_endpoints"]:
                typer.echo(f"   📍 {url}")
        else:
            typer.echo("❌ No services running")
            typer.echo("🚀 Start with: mcpctl start")
