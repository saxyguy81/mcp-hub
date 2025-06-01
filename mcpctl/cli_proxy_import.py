# Add proxy commands import to mcpctl/cli.py
# Add this line after the existing imports

# Import proxy commands (adds proxy subcommand group)
try:
    from . import proxy_commands

    # The proxy_commands module automatically adds itself to the main app
except ImportError as e:
    print(f"Warning: Proxy commands not available: {e}")
