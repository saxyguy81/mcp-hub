"""
MCP Hub Installation State Manager
Handles first-time vs subsequent installations and user onboarding
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class InstallationState:
    """Manages installation state and user experience"""
    
    def __init__(self):
        self.state_dir = Path.home() / ".mcpctl"
        self.state_file = self.state_dir / "installation.json"
        self.state_dir.mkdir(exist_ok=True)
        
    def is_first_installation(self) -> bool:
        """Check if this is the first time MCP Hub is being installed"""
        return not self.state_file.exists()
    
    def get_installation_state(self) -> Dict[str, Any]:
        """Get current installation state"""
        if not self.state_file.exists():
            return {
                "first_installed": None,
                "last_updated": None,
                "version": None,
                "services_configured": False,
                "wizard_completed": False,
                "auto_start_enabled": False,
                "installation_count": 0
            }
        
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception:
            return self.get_installation_state()  # Return default on error
    
    def update_installation_state(self, **updates) -> None:
        """Update installation state"""
        state = self.get_installation_state()
        state.update(updates)
        state["last_updated"] = datetime.now().isoformat()
        state["installation_count"] = state.get("installation_count", 0) + 1
        
        if state.get("first_installed") is None:
            state["first_installed"] = state["last_updated"]
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def mark_wizard_completed(self) -> None:
        """Mark the setup wizard as completed"""
        self.update_installation_state(wizard_completed=True)
    
    def mark_services_configured(self) -> None:
        """Mark that user has configured services"""
        self.update_installation_state(services_configured=True)
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get current server status and URLs"""
        from .container_engine import get_engine_info
        
        status = {
            "engine": "unknown",
            "services": [],
            "urls": [],
            "running": False
        }
        
        try:
            # Check if Docker/Vessel is available
            engine_info = get_engine_info()
            status["engine"] = engine_info.get("type", "unknown")
            
            # Check for running services
            compose_file = Path("docker-compose.yml")
            if compose_file.exists():
                import yaml
                with open(compose_file, 'r') as f:
                    compose_data = yaml.safe_load(f)
                
                services = compose_data.get("services", {})
                for service_name, service_config in services.items():
                    ports = service_config.get("ports", [])
                    for port_mapping in ports:
                        if isinstance(port_mapping, str) and ":" in port_mapping:
                            host_port = port_mapping.split(":")[0]
                            url = f"http://localhost:{host_port}"
                            status["urls"].append({
                                "service": service_name,
                                "url": url,
                                "port": host_port
                            })
                
                status["services"] = list(services.keys())
                
                # Check if services are actually running
                try:
                    import subprocess
                    result = subprocess.run(
                        ["docker", "compose", "ps", "--services", "--filter", "status=running"],
                        cwd=".",
                        capture_output=True,
                        text=True
                    )
                    running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
                    status["running"] = len(running_services) > 0
                    status["running_services"] = running_services
                except:
                    status["running"] = False
        
        except Exception as e:
            status["error"] = str(e)
        
        return status

class OnboardingManager:
    """Manages user onboarding experience"""
    
    def __init__(self):
        self.installation_state = InstallationState()
    
    def show_first_time_welcome(self) -> None:
        """Show welcome message for first-time users"""
        print("🎉 Welcome to MCP Hub!")
        print("======================")
        print()
        print("MCP Hub helps you manage Model Context Protocol servers using Docker containers.")
        print("Let's get you set up with your first MCP configuration!")
        print()
    
    def show_returning_user_message(self, state: Dict[str, Any]) -> None:
        """Show message for returning users"""
        install_count = state.get("installation_count", 0)
        last_updated = state.get("last_updated", "unknown")
        
        print("🔄 MCP Hub Update")
        print("=================")
        print(f"Installation #{install_count} • Last updated: {last_updated[:10]}")
        print()
        
        if state.get("services_configured"):
            print("✅ Your existing services and configurations are preserved")
        else:
            print("💡 Continue where you left off with the setup wizard")
        print()
    
    def run_quick_setup(self) -> bool:
        """Run quick setup for new users"""
        print("🚀 Quick Setup")
        print("==============")
        print()
        
        # Check if user wants to run setup wizard
        response = input("Would you like to run the setup wizard? (Y/n): ").lower()
        if response in ['n', 'no']:
            print("💡 You can run the setup wizard later with: mcpctl setup --wizard")
            return False
        
        # Run basic setup
        try:
            print("📦 Creating sample workspace...")
            from .workspace import WorkspaceManager
            
            manager = WorkspaceManager()
            
            # Create a basic demo workspace
            workspace = manager.create_workspace(
                "demo-workspace", 
                "Demo MCP workspace with sample services"
            )
            
            # Add a simple demo service
            workspace.services = {
                "demo-web": {
                    "image": "nginx:alpine",
                    "ports": ["3002:80"],
                    "environment": ["DEMO_MODE=true"],
                    "restart": "unless-stopped",
                    "networks": ["mcp-network"],
                    "labels": [
                        "mcp-hub.service=demo",
                        "mcp-hub.type=web"
                    ]
                }
            }
            
            manager.save_workspace(workspace)
            manager.activate_workspace("demo-workspace")
            
            print("✅ Demo workspace created and activated")
            
            # Generate compose file
            from .compose_gen import ComposeGenerator
            from .secret_backends.env import EnvBackend
            
            generator = ComposeGenerator(EnvBackend())
            generator.generate_compose_file()
            
            print("✅ Docker compose configuration generated")
            
            # Mark setup as completed
            self.installation_state.mark_wizard_completed()
            self.installation_state.mark_services_configured()
            
            return True
            
        except Exception as e:
            print(f"⚠️  Setup failed: {e}")
            print("💡 You can complete setup manually with: mcpctl setup --wizard")
            return False
    
    def show_service_urls(self) -> None:
        """Show available service URLs"""
        status = self.installation_state.get_server_status()
        
        print("🌐 MCP Server Status")
        print("===================")
        
        if not status["services"]:
            print("❌ No services configured")
            print("💡 Run 'mcpctl setup --wizard' to configure services")
            return
        
        if not status["running"]:
            print("⏸️  Services are configured but not running")
            print("🚀 Start services with: mcpctl start")
            print()
        
        print("📋 Configured Services:")
        for service in status["services"]:
            print(f"  • {service}")
        
        if status["urls"]:
            print()
            print("🔗 Connection URLs:")
            for url_info in status["urls"]:
                running_indicator = "🟢" if status["running"] else "🔴"
                print(f"  {running_indicator} {url_info['service']}: {url_info['url']}")
        
        print()
        if status["running"]:
            print("✅ Services are running and ready to use!")
            print("💡 Connect your LLM client to the URLs above")
        else:
            print("🚀 Start services: mcpctl start")
            print("📊 Check status: mcpctl status")
        
        print()
    
    def show_next_steps(self, is_first_time: bool) -> None:
        """Show appropriate next steps based on user state"""
        if is_first_time:
            print("🎯 Next Steps:")
            print("1. 🔧 Configure services: mcpctl setup --wizard")
            print("2. 🚀 Start services: mcpctl start") 
            print("3. 🔗 Connect your LLM to the provided URLs")
            print()
            print("📚 Learn more:")
            print("• Documentation: https://github.com/saxyguy81/mcp-hub")
            print("• Examples: mcpctl workspace list")
            print("• Help: mcpctl --help")
        else:
            print("🔄 Commands:")
            print("• 📊 Check status: mcpctl status")
            print("• 🚀 Start services: mcpctl start")
            print("• ⏹️  Stop services: mcpctl stop")
            print("• 🔧 Reconfigure: mcpctl setup --wizard")
        
        print()

def handle_installation_flow(version: str = "1.0.0") -> None:
    """Handle the complete installation flow"""
    onboarding = OnboardingManager()
    installation_state = onboarding.installation_state
    
    is_first_time = installation_state.is_first_installation()
    state = installation_state.get_installation_state()
    
    if is_first_time:
        onboarding.show_first_time_welcome()
        
        # Run quick setup
        setup_completed = onboarding.run_quick_setup()
        
        # Update installation state
        installation_state.update_installation_state(
            version=version,
            wizard_completed=setup_completed,
            services_configured=setup_completed
        )
        
        if setup_completed:
            print()
            print("🎉 Setup Complete!")
            print("=================")
            onboarding.show_service_urls()
        
    else:
        onboarding.show_returning_user_message(state)
        
        # Update version
        installation_state.update_installation_state(version=version)
        
        # Show current status
        onboarding.show_service_urls()
    
    # Always show next steps
    onboarding.show_next_steps(is_first_time)

def get_connection_info() -> Dict[str, Any]:
    """Get connection information for LLM clients"""
    installation_state = InstallationState()
    status = installation_state.get_server_status()
    
    return {
        "status": "running" if status["running"] else "stopped",
        "services": status["services"],
        "urls": status["urls"],
        "mcp_endpoints": [url["url"] for url in status["urls"]],
        "primary_url": status["urls"][0]["url"] if status["urls"] else None
    }
