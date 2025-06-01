"""
MCP Hub LLM Testing and Verification System
Comprehensive testing for Claude Desktop, OpenAI API, and custom LLM endpoints
"""

import json
import time
import requests
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path

class LLMTester:
    """Test and verify LLM backend connections"""
    
    def __init__(self):
        self.timeout = 10  # seconds
        self.test_message = "Hello! This is a connection test. Please respond with 'OK'."
    
    def test_claude_desktop(self) -> Dict[str, Any]:
        """Test Claude Desktop connection via local MCP ports"""
        start_time = time.time()
        
        # Claude Desktop typically runs on these ports
        ports = [52262, 52263, 52264]
        
        for port in ports:
            try:
                response = requests.get(
                    f"http://localhost:{port}/status",
                    timeout=5
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "backend": "claude-desktop",
                        "port": port,
                        "duration": round(duration, 2),
                        "status_code": response.status_code,
                        "message": f"✅ Claude Desktop connected on port {port}",
                        "details": {
                            "connection_type": "Local MCP",
                            "response_time": f"{duration:.2f}s",
                            "availability": "Ready"
                        }
                    }
            
            except requests.exceptions.RequestException:
                continue
        
        duration = time.time() - start_time
        return {
            "success": False,
            "backend": "claude-desktop",
            "duration": round(duration, 2),
            "status_code": 0,
            "message": "❌ Claude Desktop not found. Make sure Claude Desktop is running.",
            "details": {
                "checked_ports": ports,
                "suggestion": "Start Claude Desktop application and try again"
            }
        }
    
    def test_openai_api(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Test OpenAI API connection"""
        start_time = time.time()
        
        if not api_key:
            import os
            api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            return {
                "success": False,
                "backend": "openai",
                "duration": 0,
                "status_code": 0,
                "message": "❌ OpenAI API key not provided",
                "details": {
                    "required": "OPENAI_API_KEY environment variable or explicit key",
                    "suggestion": "Set OPENAI_API_KEY or provide key via --api-key"
                }
            }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": self.test_message}],
                    "max_tokens": 10
                },
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "backend": "openai",
                    "duration": round(duration, 2),
                    "status_code": response.status_code,
                    "message": "✅ OpenAI API connection successful",
                    "details": {
                        "model": data.get("model", "gpt-3.5-turbo"),
                        "response_time": f"{duration:.2f}s",
                        "usage": data.get("usage", {}),
                        "response": data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    }
                }
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                return {
                    "success": False,
                    "backend": "openai",
                    "duration": round(duration, 2),
                    "status_code": response.status_code,
                    "message": f"❌ OpenAI API error: {response.status_code}",
                    "details": {
                        "error": error_data.get("error", {}).get("message", "Unknown error"),
                        "type": error_data.get("error", {}).get("type", "unknown"),
                        "suggestion": "Check API key validity and account status"
                    }
                }
        
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "backend": "openai",
                "duration": round(duration, 2),
                "status_code": 0,
                "message": f"❌ Connection error: {str(e)}",
                "details": {
                    "error_type": type(e).__name__,
                    "suggestion": "Check internet connection and API endpoint"
                }
            }
    
    def test_custom_llm(self, base_url: str, api_key: Optional[str] = None, 
                       model: Optional[str] = None) -> Dict[str, Any]:
        """Test custom LLM endpoint (OpenAI-compatible API)"""
        start_time = time.time()
        
        if not base_url:
            return {
                "success": False,
                "backend": "custom",
                "duration": 0,
                "status_code": 0,
                "message": "❌ Base URL is required",
                "details": {
                    "required": "Base URL for the custom LLM endpoint",
                    "example": "https://api.your-llm-provider.com"
                }
            }
        
        # Normalize URL
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"
        
        # Default model for testing
        test_model = model or "gpt-3.5-turbo"
        
        # Construct endpoint URL
        if not base_url.endswith('/'):
            base_url += '/'
        
        endpoint_url = f"{base_url}v1/chat/completions"
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": test_model,
            "messages": [{"role": "user", "content": self.test_message}],
            "max_tokens": 20,
            "temperature": 0.1
        }
        
        try:
            # First, try a simple health check if available
            health_endpoints = [
                f"{base_url}health",
                f"{base_url}v1/models",
                endpoint_url
            ]
            
            response = None
            endpoint_used = None
            
            for check_url in health_endpoints:
                try:
                    if check_url == endpoint_url:
                        # Full API test
                        response = requests.post(
                            check_url,
                            headers=headers,
                            json=payload,
                            timeout=self.timeout
                        )
                    else:
                        # Health/models check
                        response = requests.get(
                            check_url,
                            headers=headers,
                            timeout=5
                        )
                    
                    endpoint_used = check_url
                    break
                
                except requests.exceptions.RequestException:
                    continue
            
            if response is None:
                duration = time.time() - start_time
                return {
                    "success": False,
                    "backend": "custom",
                    "duration": round(duration, 2),
                    "status_code": 0,
                    "message": f"❌ No response from {base_url}",
                    "details": {
                        "attempted_endpoints": health_endpoints,
                        "suggestion": "Check URL and ensure the service is running"
                    }
                }
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check if it's a chat completion response
                    if "choices" in data:
                        assistant_response = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        return {
                            "success": True,
                            "backend": "custom",
                            "url": base_url,
                            "duration": round(duration, 2),
                            "status_code": response.status_code,
                            "message": "✅ Custom LLM connection successful",
                            "details": {
                                "endpoint": endpoint_used,
                                "model": data.get("model", test_model),
                                "response_time": f"{duration:.2f}s",
                                "response": assistant_response,
                                "usage": data.get("usage", {}),
                                "api_type": "OpenAI-compatible"
                            }
                        }
                    
                    # Check if it's a models list response
                    elif "data" in data:
                        models = [model.get("id", "unknown") for model in data.get("data", [])]
                        return {
                            "success": True,
                            "backend": "custom",
                            "url": base_url,
                            "duration": round(duration, 2),
                            "status_code": response.status_code,
                            "message": "✅ Custom LLM service reachable",
                            "details": {
                                "endpoint": endpoint_used,
                                "available_models": models[:5],  # Show first 5 models
                                "total_models": len(models),
                                "response_time": f"{duration:.2f}s",
                                "api_type": "Models endpoint"
                            }
                        }
                    
                    # Generic success response
                    else:
                        return {
                            "success": True,
                            "backend": "custom",
                            "url": base_url,
                            "duration": round(duration, 2),
                            "status_code": response.status_code,
                            "message": "✅ Custom LLM service reachable",
                            "details": {
                                "endpoint": endpoint_used,
                                "response_time": f"{duration:.2f}s",
                                "api_type": "Health check"
                            }
                        }
                
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "backend": "custom",
                        "url": base_url,
                        "duration": round(duration, 2),
                        "status_code": response.status_code,
                        "message": "✅ Custom LLM service reachable (non-JSON response)",
                        "details": {
                            "endpoint": endpoint_used,
                            "response_time": f"{duration:.2f}s",
                            "content_type": response.headers.get("content-type", "unknown")
                        }
                    }
            
            else:
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                except:
                    error_message = f"HTTP {response.status_code}"
                
                return {
                    "success": False,
                    "backend": "custom",
                    "url": base_url,
                    "duration": round(duration, 2),
                    "status_code": response.status_code,
                    "message": f"❌ Custom LLM error: {error_message}",
                    "details": {
                        "endpoint": endpoint_used,
                        "status_code": response.status_code,
                        "suggestion": "Check authentication and endpoint configuration"
                    }
                }
        
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "backend": "custom",
                "url": base_url,
                "duration": round(duration, 2),
                "status_code": 0,
                "message": f"❌ Connection error: {str(e)}",
                "details": {
                    "error_type": type(e).__name__,
                    "suggestion": "Check URL, network connection, and SSL certificates"
                }
            }
    
    def test_all_backends(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Test all configured LLM backends"""
        results = {}
        
        # Test Claude Desktop
        results["claude"] = self.test_claude_desktop()
        
        # Test OpenAI API
        if config.get("openai_api_key"):
            results["openai"] = self.test_openai_api(config["openai_api_key"])
        
        # Test Custom LLM
        if config.get("custom_llm_url"):
            results["custom"] = self.test_custom_llm(
                config["custom_llm_url"],
                config.get("custom_llm_api_key"),
                config.get("custom_llm_model")
            )
        
        return results
    
    def format_test_result(self, result: Dict[str, Any], verbose: bool = False) -> str:
        """Format test result for display"""
        lines = []
        
        # Header
        backend = result.get("backend", "unknown").title()
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        lines.append(f"{backend}: {status}")
        
        # Basic info
        lines.append(f"  Duration: {result.get('duration', 0)}s")
        if result.get("status_code"):
            lines.append(f"  Status: {result['status_code']}")
        
        # Message
        lines.append(f"  {result['message']}")
        
        # Verbose details
        if verbose and "details" in result:
            lines.append("  Details:")
            for key, value in result["details"].items():
                if isinstance(value, (list, dict)):
                    lines.append(f"    {key}: {json.dumps(value, indent=6)}")
                else:
                    lines.append(f"    {key}: {value}")
        
        return "\n".join(lines)

def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration from various sources"""
    config = {}
    
    # Try to load from MCP Hub config
    try:
        config_file = Path.home() / ".mcpctl" / "config.toml"
        if config_file.exists():
            import toml
            with open(config_file, 'r') as f:
                mcp_config = toml.load(f)
                # Map MCP Hub config to LLM test config
                if "llm_backend" in mcp_config:
                    config["backend"] = mcp_config["llm_backend"]
                if "openai_api_key" in mcp_config:
                    config["openai_api_key"] = mcp_config["openai_api_key"]
                if "custom_llm_url" in mcp_config:
                    config["custom_llm_url"] = mcp_config["custom_llm_url"]
                if "custom_llm_api_key" in mcp_config:
                    config["custom_llm_api_key"] = mcp_config["custom_llm_api_key"]
    except Exception:
        pass
    
    # Environment variables
    import os
    if "OPENAI_API_KEY" in os.environ:
        config["openai_api_key"] = os.environ["OPENAI_API_KEY"]
    if "CUSTOM_LLM_URL" in os.environ:
        config["custom_llm_url"] = os.environ["CUSTOM_LLM_URL"]
    if "CUSTOM_LLM_API_KEY" in os.environ:
        config["custom_llm_api_key"] = os.environ["CUSTOM_LLM_API_KEY"]
    
    return config
