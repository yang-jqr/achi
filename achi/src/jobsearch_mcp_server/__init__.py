# src/jobsearch_mcp_server/__init__.py
from . import server

def main():
    """Main entry point for the package."""
    server.main()

__all__ = ["main", "server"]