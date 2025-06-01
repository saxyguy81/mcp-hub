#!/usr/bin/env python3
"""
Entry point for mcpctl CLI
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import mcpctl
sys.path.insert(0, str(Path(__file__).parent))

from mcpctl.cli import app

if __name__ == "__main__":
    app()
