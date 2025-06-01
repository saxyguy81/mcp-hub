#!/usr/bin/env python3
"""
MCP Hub Proxy Demo
Test the aggregation proxy functionality
"""

import asyncio
import json

import aiohttp


async def test_proxy():
    """Test the MCP proxy functionality"""

    print("🧪 Testing MCP Hub Proxy")
    print("========================")

    async with aiohttp.ClientSession() as session:

        # Test 1: Health check
        print("\n1. Health Check")
        try:
            async with session.get("http://localhost:3000/health") as resp:
                data = await resp.json()
                print(f"   ✅ Proxy health: {data['status']}")
                print(f"   📊 Servers: {data['healthy_servers']}/{data['servers']}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return

        # Test 2: Initialize MCP connection
        print("\n2. MCP Initialize")
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-hub-test", "version": "1.0.0"},
            },
        }

        try:
            async with session.post(
                "http://localhost:3000",
                json=initialize_request,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json()
                capabilities = data.get("result", {}).get("capabilities", {})
                print(
                    f"   ✅ Protocol version: {data.get('result', {}).get('protocolVersion')}"
                )
                print(f"   🔧 Aggregated capabilities: {list(capabilities.keys())}")
        except Exception as e:
            print(f"   ❌ Initialize failed: {e}")

        # Test 3: List tools
        print("\n3. List Available Tools")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        try:
            async with session.post(
                "http://localhost:3000",
                json=tools_request,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json()
                tools = data.get("result", {}).get("tools", [])
                print(f"   ✅ Found {len(tools)} tools across all servers:")
                for tool in tools[:5]:  # Show first 5
                    server = tool.get("_server", "unknown")
                    name = tool.get("name", "unnamed")
                    print(f"      🔧 {name} (from {server})")
                if len(tools) > 5:
                    print(f"      ... and {len(tools) - 5} more")
        except Exception as e:
            print(f"   ❌ Tools list failed: {e}")

        # Test 4: List resources
        print("\n4. List Available Resources")
        resources_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {},
        }

        try:
            async with session.post(
                "http://localhost:3000",
                json=resources_request,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json()
                resources = data.get("result", {}).get("resources", [])
                print(f"   ✅ Found {len(resources)} resources across all servers:")
                for resource in resources[:3]:  # Show first 3
                    server = resource.get("_server", "unknown")
                    uri = resource.get("uri", "no-uri")
                    print(f"      📄 {uri} (from {server})")
                if len(resources) > 3:
                    print(f"      ... and {len(resources) - 3} more")
        except Exception as e:
            print(f"   ❌ Resources list failed: {e}")

    print("\n🎉 Proxy test complete!")
    print("\n📋 To use with your LLM client:")
    print("   1. Configure MCP server: http://localhost:3000")
    print("   2. All tools/resources from backend servers are available")
    print("   3. No need to configure individual endpoints!")


if __name__ == "__main__":
    asyncio.run(test_proxy())
