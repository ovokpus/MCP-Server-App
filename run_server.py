#!/usr/bin/env python3
"""
Main entry point for running the MCP server.

This script provides a convenient way to start the MCP server from the project root.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    # Import and run the server module
    from server import main
    # The server/main.py has if __name__ == "__main__" that runs mcp.run()
    # But since we're importing it as a module, we need to run it manually
    main.mcp.run(transport="stdio")
