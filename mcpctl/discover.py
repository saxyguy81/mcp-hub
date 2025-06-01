"""
MCP Server Discovery Module
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class MCPServer:
    """Represents a discovered MCP server"""
    name: str
    path: Path
    language: str
    port: int = 8000
    
    def to_compose_service(self) -> str:
        """Convert to docker-compose service definition"""
        if self.language == "python":
            return f"""services:
  {self.name}:
    build: {self.path}
    ports:
      - "{self.port}:{self.port}"
    networks:
      - mcp-network
    environment:
      - PORT={self.port}
"""
        elif self.language == "node":
            return f"""services:
  {self.name}:
    build: {self.path}
    ports:
      - "{self.port}:{self.port}"
    networks:
      - mcp-network
    environment:
      - PORT={self.port}
"""
        return ""

class MCPDiscovery:
    """Discovers MCP servers in a directory"""
    
    def scan_directory(self, path: Path) -> List[MCPServer]:
        """Scan directory for MCP server implementations"""
        servers = []
        
        for item in path.rglob("*"):
            if item.is_file():
                server = self._analyze_file(item)
                if server:
                    servers.append(server)
        
        return servers
    
    def _analyze_file(self, file_path: Path) -> MCPServer:
        """Analyze a file to determine if it's an MCP server"""
        # Check for Python MCP servers
        if file_path.name == "server.py" or "mcp" in file_path.name.lower():
            return MCPServer(
                name=file_path.parent.name,
                path=file_path.parent,
                language="python"
            )
        
        # Check for Node.js MCP servers
        if file_path.name == "package.json":
            try:
                with open(file_path, 'r') as f:
                    package = json.load(f)
                    if "mcp" in package.get("name", "").lower():
                        return MCPServer(
                            name=package.get("name", file_path.parent.name),
                            path=file_path.parent,
                            language="node"
                        )
            except (json.JSONDecodeError, IOError):
                pass
        
        return None
