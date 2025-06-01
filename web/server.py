#!/usr/bin/env python3
"""
MCP Hub Download Service
Simple web service that serves the bootstrap installer script.
Can be deployed to any hosting service or used as a reference.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse
import requests
from flask import Flask, Response, request, jsonify, render_template_string

app = Flask(__name__)

# Configuration
GITHUB_REPO = "saxyguy81/mcp-hub"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"
INSTALL_SCRIPT_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/latest/download/install.sh"
)

# HTML template for the landing page
LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Hub - Easy Installation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .install-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }
        .command {
            background: #1e1e1e;
            color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            overflow-x: auto;
            margin: 10px 0;
        }
        .copy-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 10px;
        }
        .copy-btn:hover {
            background: #0056b3;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .feature h3 {
            color: #495057;
            margin-bottom: 10px;
        }
        .links {
            text-align: center;
            margin-top: 30px;
        }
        .links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }
        .links a:hover {
            background: #218838;
        }
        .secondary-link {
            background: #6c757d !important;
        }
        .secondary-link:hover {
            background: #545b62 !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 MCP Hub</h1>
        <p style="text-align: center; font-size: 1.2em; color: #666;">
            The easiest way to manage Model Context Protocol servers
        </p>
        
        <div class="install-section">
            <h2>📦 Quick Install</h2>
            <p>Install MCP Hub with a single command:</p>
            <div class="command" id="install-command">curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash</div>
            <button class="copy-btn" onclick="copyToClipboard('install-command')">Copy Command</button>
            
            <h3>🔧 Options</h3>
            <div class="command">
# Build from source (slower but always works)<br>
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash -s -- --build-from-source<br><br>
# Skip dependency installation<br>
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash -s -- --skip-deps
            </div>
        </div>

        <div class="features">
            <div class="feature">
                <h3>🐳 Container Ready</h3>
                <p>Run MCP servers in isolated Docker containers with zero configuration</p>
            </div>
            <div class="feature">
                <h3>🎨 Beautiful GUI</h3>
                <p>Intuitive desktop app with setup wizard for non-technical users</p>
            </div>
            <div class="feature">
                <h3>⚡ Powerful CLI</h3>
                <p>Full-featured command line tool for developers and power users</p>
            </div>
            <div class="feature">
                <h3>🔒 Secure</h3>
                <p>Image digest locking and dependency isolation for reproducible deployments</p>
            </div>
        </div>

        <div class="install-section">
            <h2>📋 Requirements</h2>
            <p><strong>Required:</strong> Docker (or Vessel on macOS), Git</p>
            <p><strong>Optional:</strong> Python 3.8+ (for enhanced CLI features)</p>
            <p><strong>Supported:</strong> macOS, Linux, Windows</p>
        </div>

        <div class="links">
            <a href="https://github.com/{{ repo }}" target="_blank">📚 Documentation</a>
            <a href="https://github.com/{{ repo }}/releases" target="_blank" class="secondary-link">📦 Releases</a>
            <a href="https://github.com/{{ repo }}/issues" target="_blank" class="secondary-link">🐛 Issues</a>
        </div>
    </div>

    <script>
        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent;
            navigator.clipboard.writeText(text).then(() => {
                const btn = element.parentNode.querySelector('.copy-btn');
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = '#28a745';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '#007bff';
                }, 2000);
            });
        }
    </script>
</body>
</html>
"""


@app.route("/")
def landing_page():
    """Serve the landing page with installation instructions."""
    return render_template_string(LANDING_PAGE, repo=GITHUB_REPO)


@app.route("/install.sh")
@app.route("/")
def install_script():
    """
    Serve the installation script.
    If accessed via curl, return the script directly.
    If accessed via browser, show the landing page.
    """
    user_agent = request.headers.get("User-Agent", "").lower()

    # If it's curl, wget, or similar, serve the script
    if any(tool in user_agent for tool in ["curl", "wget", "httpie"]):
        try:
            # Fetch the latest install script from GitHub releases
            response = requests.get(INSTALL_SCRIPT_URL, timeout=10)
            if response.status_code == 200:
                return Response(
                    response.content,
                    mimetype="text/plain",
                    headers={
                        "Content-Disposition": "inline; filename=install.sh",
                        "Cache-Control": "no-cache",
                    },
                )
            else:
                # Fallback to local script if GitHub is unavailable
                script_path = Path(__file__).parent.parent / "scripts" / "install.sh"
                if script_path.exists():
                    with open(script_path, "r") as f:
                        return Response(
                            f.read(),
                            mimetype="text/plain",
                            headers={
                                "Content-Disposition": "inline; filename=install.sh",
                                "Cache-Control": "no-cache",
                            },
                        )
                else:
                    return Response(
                        "# Installation script not found\n# Please visit https://github.com/{GITHUB_REPO}\n",
                        mimetype="text/plain",
                        status=404,
                    )
        except Exception as e:
            return Response(
                f"# Error fetching installation script: {e}\n# Please visit https://github.com/{GITHUB_REPO}\n",
                mimetype="text/plain",
                status=500,
            )
    else:
        # Browser request, show landing page
        return landing_page()


@app.route("/api/releases")
def api_releases():
    """API endpoint to get release information."""
    try:
        response = requests.get(f"{GITHUB_API_BASE}/releases", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch releases"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/latest")
def api_latest():
    """API endpoint to get latest release information."""
    try:
        response = requests.get(f"{GITHUB_API_BASE}/releases/latest", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return (
                jsonify({"error": "Failed to fetch latest release"}),
                response.status_code,
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "service": "MCP Hub Download Service",
            "github_repo": GITHUB_REPO,
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    print(f"🚀 Starting MCP Hub Download Service on port {port}")
    print(f"📦 GitHub Repository: {GITHUB_REPO}")
    print(f"🔗 Install URL: http://localhost:{port}")

    app.run(host="0.0.0.0", port=port, debug=debug)
