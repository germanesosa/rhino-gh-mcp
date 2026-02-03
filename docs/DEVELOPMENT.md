# Development Guide

This guide covers setting up a development environment and contributing to the Rhino & Grasshopper MCP project.

## Setting Up Development Environment

### Prerequisites

- **Python 3.10+**: System Python installation
- **UV package manager**: Install from https://docs.astral.sh/uv/
- **Rhino 8**: For testing the Rhino plugin
- **Visual Studio 2022** (optional): For Grasshopper component development
- **Git**: For version control

### Clone the Repository

```bash
git clone https://github.com/xunliuDesign/rhino-gh-mcp.git
cd rhino-gh-mcp
```

### Install MCP Server in Development Mode

```bash
cd mcp_server

# Create virtual environment and install dependencies
uv sync

# Install in editable mode for development
uv pip install -e .
```

### Set Up Environment Variables

```bash
# Copy the sample environment file
cp .env.sample .env

# Edit .env with your settings
# RHINO_HOST=localhost
# RHINO_PORT=9876
# GRASSHOPPER_HOST=localhost
# GRASSHOPPER_PORT=9999
# LOG_LEVEL=DEBUG  # Use DEBUG for development
```

## Project Structure

```
rhino-gh-mcp/
├── mcp_server/                 # MCP server package
│   ├── rhino_gh_mcp/           # Python package
│   │   ├── __init__.py         # Package initialization
│   │   ├── server.py           # Main MCP server
│   │   ├── main.py             # CLI entry point
│   │   ├── rhino_tools.py      # Rhino integration
│   │   └── grasshopper_tools.py # Grasshopper integration
│   ├── pyproject.toml          # Package configuration
│   └── .env.sample             # Environment template
│
├── rhino_plugin/               # Rhino plugin
│   └── rhino_client.py         # IronPython socket server
│
├── grasshopper_component/      # Grasshopper component
│   ├── rhino_gh_mcpComponent.cs # Main component
│   ├── rhino_gh_mcpInfo.cs     # Component metadata
│   └── rhino_gh_mcp.csproj     # C# project file
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # Architecture overview
│   ├── DEVELOPMENT.md          # This file
│   └── TROUBLESHOOTING.md      # Troubleshooting guide
│
└── README.md                   # Main documentation
```

## Development Workflow

### Running the MCP Server Locally

```bash
cd mcp_server

# Run with default tools (grasshopper only)
uv run rhino-gh-mcp

# Run with specific tools
uv run python -m rhino_gh_mcp.main --tools rhino,grasshopper

# Run with all tools
uv run python -m rhino_gh_mcp.main --tools all
```

### Testing with Claude Desktop

1. **Configure Claude Desktop** to point to your local development server:

```json
{
  "mcpServers": {
    "rhino-gh-mcp-dev": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/rhino-gh-mcp/mcp_server",
        "run",
        "python",
        "-m",
        "rhino_gh_mcp.main"
      ],
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

2. **Restart Claude Desktop** to reload the configuration

3. **Check logs** in Claude Desktop's developer console

### Testing the Rhino Plugin

```python
# In Rhino Python Editor, load the script
import sys
sys.path.append('/path/to/rhino-gh-mcp/rhino_plugin')
execfile('/path/to/rhino-gh-mcp/rhino_plugin/rhino_client.py')

# The server should start automatically
# Check the console for: "RhinoMCP server started on localhost:9876"
```

### Testing the Grasshopper Component

1. Open Visual Studio 2022
2. Load `grasshopper_component/rhino_gh_mcp.sln`
3. Build the solution (Ctrl+Shift+B)
4. The `.gha` file is output to `bin/`
5. Copy to Grasshopper Components folder
6. Restart Rhino and Grasshopper

## Code Style and Conventions

### Python Code (MCP Server)

```python
# Use type hints
def get_scene_info(self) -> Dict[str, Any]:
    """Get scene information from Rhino.

    Returns:
        Dictionary containing scene data
    """
    pass

# Use f-strings for formatting (Python 3.10+)
message = f"Connected to {self.host}:{self.port}"

# Use logging instead of print
import logging
logger = logging.getLogger(__name__)
logger.info("Server started")
logger.debug(f"Details: {data}")
logger.error(f"Error: {error}")

# Handle errors gracefully
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return {"status": "error", "message": str(e)}
```

### IronPython Code (Rhino Plugin)

```python
# NO f-strings (IronPython 2.7)
message = "Connected to {0}:{1}".format(host, port)

# Use .format() for string formatting
result = "Value: {0}".format(value)

# No type hints
def get_scene_info():
    """Get scene information."""
    pass

# Use Rhino logging
import Rhino
Rhino.RhinoApp.WriteLine("Message to console")
```

### C# Code (Grasshopper Component)

```csharp
// Use PascalCase for public members
public class RhinoGhMcpComponent : GH_Component
{
    // Private fields with _camelCase
    private string _serverStatus;

    // XML documentation comments
    /// <summary>
    /// Gets the current server status
    /// </summary>
    public string ServerStatus => _serverStatus;

    // Use async/await for I/O operations
    private async Task<string> FetchDataAsync()
    {
        // Implementation
    }
}
```

## Testing

### Manual Testing

#### Test MCP Server Startup

```bash
cd mcp_server
uv run rhino-gh-mcp
# Should see: "RhinoMCP server starting up"
# Press Ctrl+C to stop
```

#### Test Rhino Connection

```bash
# Terminal 1: Start Rhino plugin
# (in Rhino Python editor, run rhino_client.py)

# Terminal 2: Start MCP server
cd mcp_server
uv run rhino-gh-mcp

# Should see: "Successfully connected to Rhino script"
```

#### Test Tool Invocation

```bash
# In Claude Desktop or Cursor, try:
# "What objects are in my Rhino scene?"

# Check MCP server logs for:
# - Tool invocation
# - Socket communication
# - Response sent
```

### Unit Testing (Future Enhancement)

```python
# tests/test_rhino_tools.py
import pytest
from rhino_gh_mcp.rhino_tools import RhinoConnection

def test_connection_initialization():
    conn = RhinoConnection(host='localhost', port=9876)
    assert conn.host == 'localhost'
    assert conn.port == 9876

# Run tests
pytest tests/
```

## Debugging

### Enable Debug Logging

```bash
# In .env file
LOG_LEVEL=DEBUG

# Or via environment variable
export LOG_LEVEL=DEBUG
uv run rhino-gh-mcp
```

### Debug MCP Communication

```bash
# Use MCP inspector (if available)
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp_server run rhino-gh-mcp
```

### Debug Rhino Plugin

```python
# Add debug prints in rhino_client.py
def handle_command(command):
    log_message("DEBUG: Received command: {0}".format(command))
    # ... rest of function
```

### Debug Grasshopper Component

```csharp
// In Visual Studio, set breakpoints
// Attach debugger to Rhino.exe process
// Use Debug > Attach to Process > Rhino.exe
```

### Common Debugging Scenarios

**MCP Server not receiving commands:**
1. Check Claude Desktop logs
2. Verify server is running (`ps aux | grep rhino-gh-mcp`)
3. Check MCP configuration in Claude Desktop
4. Restart Claude Desktop

**Rhino plugin not responding:**
1. Check Rhino Python console for errors
2. Verify port 9876 is listening (`lsof -i :9876` on macOS/Linux)
3. Test with telnet: `telnet localhost 9876`
4. Check firewall settings

**Grasshopper component not working:**
1. Check component output for error messages
2. Verify HTTP server is running (check component RunServer parameter)
3. Test with curl: `curl http://localhost:9999`
4. Check RhinoApp.WriteLine output in Rhino command line

## Contributing

### Branch Strategy

- `main`: Stable releases
- `develop`: Integration branch for features
- `feature/xxx`: New features
- `fix/xxx`: Bug fixes

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch from `develop`
3. **Make** your changes
4. **Test** thoroughly
5. **Commit** with clear messages
6. **Push** to your fork
7. **Submit** a pull request to `develop`

### Commit Messages

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build process or tooling changes

**Examples:**
```
feat(rhino): add support for NURBS surfaces

- Implemented surface creation
- Added surface analysis tools
- Updated documentation

Closes #123
```

```
fix(grasshopper): handle connection timeout gracefully

- Added retry logic
- Improved error messages
- Updated tests
```

## Adding New Tools

### 1. Create Tool Module

```python
# mcp_server/rhino_gh_mcp/new_tools.py

from mcp.server.fastmcp import FastMCP
import logging

logger = logging.getLogger(__name__)

class NewTools:
    """New tool functionality"""

    def __init__(self, app: FastMCP):
        self.app = app
        self._register_tools()

    def _register_tools(self):
        """Register all tools with the MCP server"""

        @self.app.tool()
        def my_new_tool(param1: str, param2: int) -> dict:
            """Description of what this tool does

            Args:
                param1: Description of param1
                param2: Description of param2

            Returns:
                Dictionary with results
            """
            try:
                # Implementation
                result = do_something(param1, param2)
                return {"status": "success", "data": result}
            except Exception as e:
                logger.error(f"Tool failed: {e}")
                return {"status": "error", "message": str(e)}
```

### 2. Register Tool in Server

```python
# mcp_server/rhino_gh_mcp/server.py

from .new_tools import NewTools

def load_tools(app, tool_names):
    tool_map = {
        "rhino": ("rhino_gh_mcp.rhino_tools", "RhinoTools"),
        "grasshopper": ("rhino_gh_mcp.grasshopper_tools", "GrasshopperTools"),
        "new": ("rhino_gh_mcp.new_tools", "NewTools"),  # Add here
    }
    # ... rest of function
```

### 3. Test the New Tool

```bash
# Run with new tool enabled
uv run python -m rhino_gh_mcp.main --tools rhino,grasshopper,new

# Test in Claude Desktop
# "Use the my_new_tool with param1='test' and param2=42"
```

## Release Process

### Version Bumping

```bash
# Edit mcp_server/pyproject.toml
# Update version: "1.0.0" → "1.1.0"

# Commit the version change
git commit -am "chore: bump version to 1.1.0"

# Tag the release
git tag -a v1.1.0 -m "Release v1.1.0"

# Push with tags
git push origin main --tags
```

### Building Distribution

```bash
cd mcp_server

# Build the package
uv build

# Check the dist/ folder
ls dist/
# rhino_gh_mcp-1.1.0-py3-none-any.whl
# rhino_gh_mcp-1.1.0.tar.gz
```

### Publishing (Future)

```bash
# Publish to PyPI (when ready)
uv publish
```

## Documentation

### Updating Documentation

- **README.md**: User-facing documentation
- **ARCHITECTURE.md**: System design and technical details
- **DEVELOPMENT.md**: This file - developer guide
- **TROUBLESHOOTING.md**: Common issues and solutions

### Documentation Standards

- Use Markdown
- Include code examples
- Keep examples up-to-date with code
- Add diagrams where helpful (use Mermaid or ASCII)
- Link to related sections

## Resources

### Official Documentation

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [RhinoCommon API](https://developer.rhino3d.com/api/)
- [Grasshopper SDK](https://developer.rhino3d.com/guides/grasshopper/)

### Community

- [GitHub Issues](https://github.com/xunliuDesign/rhino-gh-mcp/issues)
- [GitHub Discussions](https://github.com/xunliuDesign/rhino-gh-mcp/discussions)
- [Rhino Developer Forum](https://discourse.mcneel.com/c/scripting)

## License

All contributions are subject to the MIT License. See LICENSE file.
