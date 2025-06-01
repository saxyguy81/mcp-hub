#!/usr/bin/env python3
"""
MCP Hub Proxy Server
Aggregates multiple MCP servers behind a single endpoint
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import yaml
from aiohttp import ClientSession, web


@dataclass
class MCPServer:
    """Represents a backend MCP server"""

    name: str
    url: str
    healthy: bool = True
    last_check: float = 0
    capabilities: Dict[str, Any] = None
    error_count: int = 0

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = {}


class MCPProxy:
    """MCP Protocol Proxy and Aggregator"""

    def __init__(self, config_file: str = "docker-compose.yml", port: int = 3000):
        self.servers: Dict[str, MCPServer] = {}
        self.config_file = config_file
        self.port = port
        self.session: Optional[ClientSession] = None
        self.logger = logging.getLogger(__name__)
        self.health_check_task: Optional[asyncio.Task] = None
        self.tool_server_map: Dict[str, str] = {}  # tool_name -> server_name
        self.resource_server_map: Dict[str, str] = {}  # resource_uri -> server_name

    async def start(self):
        """Start the proxy server"""
        self.session = ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        await self.discover_servers()
        await self.initialize_all_servers()
        self.health_check_task = asyncio.create_task(self.health_check_loop())
        self.logger.info("MCP Proxy started successfully")

    async def stop(self):
        """Stop the proxy server"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

        self.logger.info("MCP Proxy stopped")

    async def discover_servers(self):
        """Auto-discover MCP servers from docker-compose.yml"""
        try:
            compose_path = Path(self.config_file)
            if not compose_path.exists():
                self.logger.warning(f"Compose file not found: {self.config_file}")
                return

            with open(compose_path, "r") as f:
                compose_data = yaml.safe_load(f)

            services = compose_data.get("services", {})
            discovered_count = 0

            for service_name, config in services.items():
                # Skip the proxy service itself
                if service_name == "mcp-proxy":
                    continue

                ports = config.get("ports", [])
                for port_mapping in ports:
                    if isinstance(port_mapping, str) and ":" in port_mapping:
                        host_port = port_mapping.split(":")[0]
                        url = f"http://localhost:{host_port}"

                        server = MCPServer(name=service_name, url=url)
                        self.servers[service_name] = server
                        discovered_count += 1
                        self.logger.info(
                            f"Discovered MCP server: {service_name} at {url}"
                        )
                        break

            self.logger.info(f"Discovery complete: {discovered_count} servers found")

        except Exception as e:
            self.logger.error(f"Failed to discover servers: {e}")

    async def initialize_all_servers(self):
        """Initialize all discovered servers"""
        if not self.servers:
            self.logger.warning("No servers to initialize")
            return

        initialization_tasks = []
        for server in self.servers.values():
            task = asyncio.create_task(self.initialize_server(server))
            initialization_tasks.append(task)

        await asyncio.gather(*initialization_tasks, return_exceptions=True)

    async def initialize_server(self, server: MCPServer):
        """Initialize a single MCP server"""
        try:
            initialize_request = {
                "jsonrpc": "2.0",
                "id": f"init_{server.name}",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"roots": {"listChanged": False}, "sampling": {}},
                    "clientInfo": {"name": "mcp-hub-proxy", "version": "1.0.0"},
                },
            }

            async with self.session.post(
                server.url,
                json=initialize_request,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    if "result" in data:
                        server.capabilities = data["result"].get("capabilities", {})
                        server.healthy = True
                        server.error_count = 0

                        # Build tool and resource mappings
                        await self.update_server_mappings(server)

                        self.logger.info(
                            f"Initialized server {server.name} successfully"
                        )
                    else:
                        self.logger.warning(
                            f"Server {server.name} initialization returned error: {data.get('error')}"
                        )
                        server.healthy = False
                else:
                    self.logger.warning(
                        f"Server {server.name} initialization failed: HTTP {resp.status}"
                    )
                    server.healthy = False

        except Exception as e:
            self.logger.error(f"Failed to initialize server {server.name}: {e}")
            server.healthy = False
            server.error_count += 1

    async def update_server_mappings(self, server: MCPServer):
        """Update tool and resource mappings for a server"""
        try:
            # Get tools list
            tools_request = {
                "jsonrpc": "2.0",
                "id": f"tools_{server.name}",
                "method": "tools/list",
                "params": {},
            }

            async with self.session.post(
                server.url,
                json=tools_request,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tools = data.get("result", {}).get("tools", [])

                    for tool in tools:
                        tool_name = tool.get("name")
                        if tool_name:
                            self.tool_server_map[tool_name] = server.name

            # Get resources list
            resources_request = {
                "jsonrpc": "2.0",
                "id": f"resources_{server.name}",
                "method": "resources/list",
                "params": {},
            }

            async with self.session.post(
                server.url,
                json=resources_request,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    resources = data.get("result", {}).get("resources", [])

                    for resource in resources:
                        resource_uri = resource.get("uri")
                        if resource_uri:
                            self.resource_server_map[resource_uri] = server.name

        except Exception as e:
            self.logger.debug(f"Error updating mappings for {server.name}: {e}")

    async def health_check_loop(self):
        """Periodic health checking of backend servers"""
        while True:
            try:
                await self.check_all_servers_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(30)

    async def check_all_servers_health(self):
        """Check health of all backend servers"""
        if not self.servers:
            return

        health_tasks = []
        for server in self.servers.values():
            task = asyncio.create_task(self.check_server_health(server))
            health_tasks.append(task)

        await asyncio.gather(*health_tasks, return_exceptions=True)

    async def check_server_health(self, server: MCPServer):
        """Check health of a single server"""
        try:
            # Try a simple initialize request as health check
            health_request = {
                "jsonrpc": "2.0",
                "id": f"health_{server.name}_{int(time.time())}",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-hub-proxy", "version": "1.0.0"},
                },
            }

            async with self.session.post(
                server.url,
                json=health_request,
                headers={"Content-Type": "application/json"},
            ) as resp:
                was_healthy = server.healthy
                server.healthy = resp.status == 200
                server.last_check = time.time()

                if server.healthy:
                    server.error_count = 0
                    if not was_healthy:
                        self.logger.info(f"Server {server.name} is back online")
                        # Re-initialize and update mappings
                        await self.initialize_server(server)
                else:
                    server.error_count += 1
                    if was_healthy:
                        self.logger.warning(f"Server {server.name} is now offline")

        except Exception as e:
            was_healthy = server.healthy
            server.healthy = False
            server.error_count += 1
            server.last_check = time.time()

            if was_healthy:
                self.logger.warning(f"Server {server.name} health check failed: {e}")

    async def handle_initialize(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request - aggregate all server capabilities"""
        aggregated_capabilities = {
            "tools": {},
            "resources": {},
            "prompts": {},
            "roots": {"listChanged": False},
            "sampling": {},
        }

        # Collect capabilities from all healthy servers
        healthy_servers = [s for s in self.servers.values() if s.healthy]
        self.logger.info(
            f"Aggregating capabilities from {len(healthy_servers)} healthy servers"
        )

        for server in healthy_servers:
            if server.capabilities:
                caps = server.capabilities

                # Merge tools capabilities
                if "tools" in caps:
                    if isinstance(caps["tools"], dict):
                        aggregated_capabilities["tools"].update(caps["tools"])

                # Merge resources capabilities
                if "resources" in caps:
                    if isinstance(caps["resources"], dict):
                        aggregated_capabilities["resources"].update(caps["resources"])

                # Merge prompts capabilities
                if "prompts" in caps:
                    if isinstance(caps["prompts"], dict):
                        aggregated_capabilities["prompts"].update(caps["prompts"])

        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": aggregated_capabilities,
                "serverInfo": {"name": "mcp-hub-proxy", "version": "1.0.0"},
            },
        }

    async def handle_tools_list(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request - aggregate from all servers"""
        all_tools = []

        for server in self.servers.values():
            if not server.healthy:
                continue

            try:
                async with self.session.post(
                    server.url,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "result" in data:
                            tools = data["result"].get("tools", [])

                            # Add server context to each tool
                            for tool in tools:
                                tool["_server"] = server.name
                                tool["_server_url"] = server.url
                                all_tools.append(tool)

                                # Update tool mapping
                                tool_name = tool.get("name")
                                if tool_name:
                                    self.tool_server_map[tool_name] = server.name

            except Exception as e:
                self.logger.error(f"Failed to get tools from {server.name}: {e}")

        self.logger.info(
            f"Aggregated {len(all_tools)} tools from {len(self.servers)} servers"
        )

        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "result": {"tools": all_tools},
        }

    async def handle_tools_call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request - route to appropriate server"""
        tool_name = request_data.get("params", {}).get("name")

        if not tool_name:
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32602,
                    "message": "Invalid params: tool name required",
                },
            }

        # Check if we know which server has this tool
        target_server_name = self.tool_server_map.get(tool_name)

        if target_server_name and target_server_name in self.servers:
            target_server = self.servers[target_server_name]
            if target_server.healthy:
                try:
                    async with self.session.post(
                        target_server.url,
                        json=request_data,
                        headers={"Content-Type": "application/json"},
                    ) as resp:
                        if resp.status == 200:
                            return await resp.json()
                except Exception as e:
                    self.logger.error(
                        f"Failed to call tool {tool_name} on {target_server_name}: {e}"
                    )

        # Fallback: try all healthy servers until one succeeds
        for server in self.servers.values():
            if not server.healthy:
                continue

            try:
                async with self.session.post(
                    server.url,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # If no error, this server handled it successfully
                        if "error" not in data:
                            # Update mapping for future calls
                            self.tool_server_map[tool_name] = server.name
                            return data

            except Exception as e:
                self.logger.debug(f"Tool call failed on {server.name}: {e}")
                continue

        # If no server could handle it, return error
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {
                "code": -32601,
                "message": f"Tool '{tool_name}' not found on any server",
            },
        }

    async def handle_resources_list(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resources/list request - aggregate from all servers"""
        all_resources = []

        for server in self.servers.values():
            if not server.healthy:
                continue

            try:
                async with self.session.post(
                    server.url,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "result" in data:
                            resources = data["result"].get("resources", [])

                            # Add server context
                            for resource in resources:
                                resource["_server"] = server.name
                                resource["_server_url"] = server.url
                                all_resources.append(resource)

                                # Update resource mapping
                                resource_uri = resource.get("uri")
                                if resource_uri:
                                    self.resource_server_map[resource_uri] = server.name

            except Exception as e:
                self.logger.error(f"Failed to get resources from {server.name}: {e}")

        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "result": {"resources": all_resources},
        }

    async def handle_resources_read(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resources/read request - route to appropriate server"""
        resource_uri = request_data.get("params", {}).get("uri")

        if not resource_uri:
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32602,
                    "message": "Invalid params: resource uri required",
                },
            }

        # Check if we know which server has this resource
        target_server_name = self.resource_server_map.get(resource_uri)

        if target_server_name and target_server_name in self.servers:
            target_server = self.servers[target_server_name]
            if target_server.healthy:
                try:
                    async with self.session.post(
                        target_server.url,
                        json=request_data,
                        headers={"Content-Type": "application/json"},
                    ) as resp:
                        if resp.status == 200:
                            return await resp.json()
                except Exception as e:
                    self.logger.error(
                        f"Failed to read resource {resource_uri} from {target_server_name}: {e}"
                    )

        # Fallback: try all healthy servers
        return await self.broadcast_request(request_data)

    async def proxy_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main request handler - routes based on method"""
        method = request_data.get("method")

        if method == "initialize":
            return await self.handle_initialize(request_data)
        elif method == "tools/list":
            return await self.handle_tools_list(request_data)
        elif method == "tools/call":
            return await self.handle_tools_call(request_data)
        elif method == "resources/list":
            return await self.handle_resources_list(request_data)
        elif method == "resources/read":
            return await self.handle_resources_read(request_data)
        elif method == "prompts/list":
            return await self.broadcast_request(request_data)
        elif method == "prompts/get":
            return await self.broadcast_request(request_data)
        else:
            # For other methods, try each server until one succeeds
            return await self.broadcast_request(request_data)

    async def broadcast_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast request to all servers, return first successful response"""
        for server in self.servers.values():
            if not server.healthy:
                continue

            try:
                async with self.session.post(
                    server.url,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "error" not in data:
                            return data

            except Exception:
                continue

        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {"code": -32601, "message": "Method not found on any server"},
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current proxy status"""
        healthy_servers = [s for s in self.servers.values() if s.healthy]

        server_status = {}
        for name, server in self.servers.items():
            server_status[name] = {
                "url": server.url,
                "healthy": server.healthy,
                "last_check": server.last_check,
                "error_count": server.error_count,
                "capabilities": bool(server.capabilities),
            }

        return {
            "proxy_status": "running",
            "total_servers": len(self.servers),
            "healthy_servers": len(healthy_servers),
            "servers": server_status,
            "tool_mappings": len(self.tool_server_map),
            "resource_mappings": len(self.resource_server_map),
        }


# Web server handlers
async def handle_mcp_request(request):
    """HTTP handler for MCP requests"""
    try:
        data = await request.json()
        proxy = request.app["proxy"]
        response = await proxy.proxy_request(data)
        return web.json_response(response)

    except Exception as e:
        logging.error(f"MCP request error: {e}")
        return web.json_response(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            },
            status=500,
        )


async def handle_health(request):
    """Health check endpoint"""
    proxy = request.app["proxy"]
    status = proxy.get_status()

    return web.json_response(
        {
            "status": "healthy",
            "servers": status["total_servers"],
            "healthy_servers": status["healthy_servers"],
            "server_list": [
                name for name, info in status["servers"].items() if info["healthy"]
            ],
        }
    )


async def handle_status(request):
    """Detailed status endpoint"""
    proxy = request.app["proxy"]
    status = proxy.get_status()
    return web.json_response(status)


async def handle_servers(request):
    """List all servers endpoint"""
    proxy = request.app["proxy"]
    servers = []

    for name, server in proxy.servers.items():
        servers.append(
            {
                "name": name,
                "url": server.url,
                "healthy": server.healthy,
                "last_check": (
                    datetime.fromtimestamp(server.last_check).isoformat()
                    if server.last_check
                    else None
                ),
                "error_count": server.error_count,
                "capabilities": server.capabilities,
            }
        )

    return web.json_response({"servers": servers})


async def init_app(config_file: str, port: int):
    """Initialize the web application"""
    app = web.Application()

    # Create and start proxy
    proxy = MCPProxy(config_file, port)
    await proxy.start()
    app["proxy"] = proxy

    # Routes
    app.router.add_post("/", handle_mcp_request)  # Main MCP endpoint
    app.router.add_get("/health", handle_health)
    app.router.add_get("/status", handle_status)
    app.router.add_get("/servers", handle_servers)

    # CORS support for GUI
    app.router.add_options("/{path:.*}", handle_cors)
    app.middlewares.append(cors_middleware)

    # Cleanup handler
    async def cleanup_proxy(app):
        await app["proxy"].stop()

    app.on_cleanup.append(cleanup_proxy)

    return app


async def handle_cors(request):
    """Handle CORS preflight requests"""
    return web.Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )


async def cors_middleware(request, handler):
    """CORS middleware"""
    response = await handler(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MCP Hub Proxy Server")
    parser.add_argument("--port", type=int, default=3000, help="Port to listen on")
    parser.add_argument(
        "--config",
        type=str,
        default="docker-compose.yml",
        help="Docker compose file path",
    )
    parser.add_argument("--log-level", type=str, default="INFO", help="Log level")
    parser.add_argument("--log-file", type=str, help="Log file path")

    args = parser.parse_args()

    # Configure logging
    log_config = {
        "level": getattr(logging, args.log_level.upper()),
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    }

    if args.log_file:
        log_config["filename"] = args.log_file

    logging.basicConfig(**log_config)
    logger = logging.getLogger(__name__)

    # Handle shutdown gracefully
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, stopping proxy...")
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app = await init_app(args.config, args.port)
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, "localhost", args.port)
        await site.start()

        logger.info(f"🚀 MCP Hub Proxy started on http://localhost:{args.port}")
        logger.info(f"📊 Status: http://localhost:{args.port}/status")
        logger.info(f"💚 Health: http://localhost:{args.port}/health")
        logger.info(f"🔗 Servers: http://localhost:{args.port}/servers")

        # Keep running
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
        finally:
            await runner.cleanup()

    except Exception as e:
        logger.error(f"Failed to start proxy: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
