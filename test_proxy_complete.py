#!/usr/bin/env python3
"""
Comprehensive MCP Hub Proxy Test Suite
Tests the complete proxy implementation
"""

import asyncio
import json
import aiohttp
import subprocess
import time
import os
import signal
from pathlib import Path

class ProxyTestSuite:
    """Complete test suite for MCP Hub proxy functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.test_results = []
        self.proxy_pid = None
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def run_command(self, cmd: list, timeout: int = 30):
        """Run a command and return result"""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def test_mcpctl_available(self):
        """Test that mcpctl command is available"""
        result = self.run_command(["mcpctl", "--version"])
        self.log_test(
            "mcpctl command available",
            result["success"],
            f"Version: {result['stdout'].strip()}" if result["success"] else result["stderr"]
        )
        return result["success"]
    
    def test_proxy_commands_available(self):
        """Test that proxy subcommands are available"""
        result = self.run_command(["mcpctl", "proxy", "--help"])
        self.log_test(
            "Proxy commands available",
            result["success"],
            "Proxy subcommand group registered" if result["success"] else result["stderr"]
        )
        return result["success"]
    
    def test_services_setup(self):
        """Test that basic services are configured"""
        # Check if docker-compose.yml exists
        compose_file = Path("docker-compose.yml")
        if not compose_file.exists():
            # Generate one for testing
            result = self.run_command(["mcpctl", "generate"])
            if not result["success"]:
                self.log_test("Services setup", False, "Failed to generate compose file")
                return False
        
        self.log_test("Services setup", True, "docker-compose.yml available")
        return True
    
    def test_start_services(self):
        """Test starting MCP services"""
        print("\n📦 Starting MCP services...")
        result = self.run_command(["mcpctl", "start"], timeout=60)
        
        if result["success"]:
            # Wait for services to be ready
            time.sleep(5)
        
        self.log_test(
            "Start services",
            result["success"],
            "Services started successfully" if result["success"] else result["stderr"]
        )
        return result["success"]
    
    def test_proxy_start(self):
        """Test starting the proxy"""
        print("\n🚀 Starting MCP proxy...")
        result = self.run_command(["mcpctl", "proxy", "start", "--background"])
        
        if result["success"]:
            # Wait for proxy to start
            time.sleep(3)
        
        self.log_test(
            "Start proxy",
            result["success"],
            "Proxy started in background" if result["success"] else result["stderr"]
        )
        return result["success"]
    
    async def test_proxy_health(self):
        """Test proxy health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.log_test(
                            "Proxy health check",
                            True,
                            f"Status: {data.get('status')}, Servers: {data.get('servers', 0)}"
                        )
                        return True
                    else:
                        self.log_test("Proxy health check", False, f"HTTP {resp.status}")
                        return False
        except Exception as e:
            self.log_test("Proxy health check", False, str(e))
            return False
    
    async def test_mcp_initialize(self):
        """Test MCP initialize protocol"""
        try:
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-hub-test",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=initialize_request,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "result" in data:
                            capabilities = data["result"].get("capabilities", {})
                            self.log_test(
                                "MCP initialize",
                                True,
                                f"Protocol version: {data['result'].get('protocolVersion')}, "
                                f"Capabilities: {list(capabilities.keys())}"
                            )
                            return True
                        else:
                            self.log_test("MCP initialize", False, f"Error: {data.get('error')}")
                            return False
                    else:
                        self.log_test("MCP initialize", False, f"HTTP {resp.status}")
                        return False
        except Exception as e:
            self.log_test("MCP initialize", False, str(e))
            return False
    
    async def test_tools_list(self):
        """Test tools/list aggregation"""
        try:
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=tools_request,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "result" in data:
                            tools = data["result"].get("tools", [])
                            server_count = len(set(tool.get("_server") for tool in tools if tool.get("_server")))
                            self.log_test(
                                "Tools list aggregation",
                                True,
                                f"Found {len(tools)} tools from {server_count} servers"
                            )
                            return True
                        else:
                            self.log_test("Tools list aggregation", False, f"Error: {data.get('error')}")
                            return False
                    else:
                        self.log_test("Tools list aggregation", False, f"HTTP {resp.status}")
                        return False
        except Exception as e:
            self.log_test("Tools list aggregation", False, str(e))
            return False
    
    async def test_resources_list(self):
        """Test resources/list aggregation"""
        try:
            resources_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/list",
                "params": {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=resources_request,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "result" in data:
                            resources = data["result"].get("resources", [])
                            server_count = len(set(res.get("_server") for res in resources if res.get("_server")))
                            self.log_test(
                                "Resources list aggregation",
                                True,
                                f"Found {len(resources)} resources from {server_count} servers"
                            )
                            return True
                        else:
                            self.log_test("Resources list aggregation", False, f"Error: {data.get('error')}")
                            return False
                    else:
                        self.log_test("Resources list aggregation", False, f"HTTP {resp.status}")
                        return False
        except Exception as e:
            self.log_test("Resources list aggregation", False, str(e))
            return False
    
    def test_proxy_status_command(self):
        """Test mcpctl proxy status command"""
        result = self.run_command(["mcpctl", "proxy", "status"])
        self.log_test(
            "Proxy status command",
            result["success"],
            "Status command executed" if result["success"] else result["stderr"]
        )
        return result["success"]
    
    def test_proxy_servers_command(self):
        """Test mcpctl proxy servers command"""
        result = self.run_command(["mcpctl", "proxy", "servers"])
        self.log_test(
            "Proxy servers command",
            result["success"],
            "Servers command executed" if result["success"] else result["stderr"]
        )
        return result["success"]
    
    def test_connect_command(self):
        """Test enhanced mcpctl connect command"""
        result = self.run_command(["mcpctl", "connect"])
        success = result["success"] and "localhost:3000" in result["stdout"]
        self.log_test(
            "Enhanced connect command",
            success,
            "Shows single endpoint mode" if success else "Single endpoint not detected"
        )
        return success
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up...")
        
        # Stop proxy
        result = self.run_command(["mcpctl", "proxy", "stop"])
        if result["success"]:
            print("✅ Proxy stopped")
        
        # Stop services
        result = self.run_command(["mcpctl", "stop"])
        if result["success"]:
            print("✅ Services stopped")
    
    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 MCP Hub Proxy Test Suite")
        print("=" * 40)
        
        # Basic setup tests
        if not self.test_mcpctl_available():
            print("\n❌ mcpctl not available - cannot continue")
            return False
        
        if not self.test_proxy_commands_available():
            print("\n❌ Proxy commands not available - cannot continue")
            return False
        
        if not self.test_services_setup():
            print("\n❌ Services setup failed - cannot continue")
            return False
        
        # Start services and proxy
        if not self.test_start_services():
            print("\n❌ Failed to start services")
            return False
        
        if not self.test_proxy_start():
            print("\n❌ Failed to start proxy")
            return False
        
        # Protocol tests
        await self.test_proxy_health()
        await self.test_mcp_initialize()
        await self.test_tools_list()
        await self.test_resources_list()
        
        # CLI tests
        self.test_proxy_status_command()
        self.test_proxy_servers_command()
        self.test_connect_command()
        
        # Summary
        print("\n📊 Test Results Summary")
        print("=" * 30)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 All tests passed! MCP Hub proxy is working correctly.")
            return True
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            return False

async def main():
    """Main test entry point"""
    test_suite = ProxyTestSuite()
    
    try:
        success = await test_suite.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
