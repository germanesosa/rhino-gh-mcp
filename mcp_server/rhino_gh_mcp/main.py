#!/usr/bin/env python3
"""
RhinoMCP with UV - Main entry point

This script serves as a convenience wrapper to start the RhinoMCP server.
"""

import sys
import argparse
from . import server

def parse_args():
    parser = argparse.ArgumentParser(description="RhinoMCP with UV - Main entry point")
    parser.add_argument('--tools', type=str, default="grasshopper",
                        help="Comma-separated list of tools to load: rhino,grasshopper,replicate,utility (default: grasshopper)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    server.main(tools=args.tools)