# Rhino & Grasshopper MCP Server

This is the MCP (Model Context Protocol) server for Rhino and Grasshopper integration.

## Installation

```bash
uv sync
```

## Usage

```bash
# Run the server
uv run rhino-gh-mcp

# Or with specific tools
uv run python -m rhino_gh_mcp.main --tools rhino,grasshopper
```

## Configuration

Copy `.env.sample` to `.env` and configure your settings:

```env
RHINO_HOST=localhost
RHINO_PORT=9876
GRASSHOPPER_HOST=localhost
GRASSHOPPER_PORT=9999
LOG_LEVEL=INFO
```

## Documentation

See the main [README](../README.md) for full documentation.
