"""Rhino and Grasshopper Model Context Protocol (MCP) Integration with UV
------------------------------------------------------------------------
A package that allows Claude to interact with Rhino and Grasshopper through the Model Context Protocol
Built with modern UV package management for better dependency handling and performance.
"""

from .server import main

__version__ = "0.1.0"
__all__ = ["main"]