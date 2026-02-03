# Rhino & Grasshopper MCP

Connect Rhino 8 and Grasshopper to Claude AI through the Model Context Protocol (MCP), enabling AI-assisted 3D modeling, parametric design, and scene manipulation.

## Features

### Rhino Integration
- **Two-way communication**: Socket-based connection between Claude AI and Rhino
- **Object manipulation**: Create, modify, and query 3D objects with metadata support
- **Layer management**: Organize and interact with Rhino layers
- **Scene inspection**: Get detailed scene information and viewport captures
- **Code execution**: Run IronPython code directly in Rhino from Claude

### Grasshopper Integration
- **Canvas management**: Inspect and modify Grasshopper definitions
- **Component manipulation**: Create, update, and connect components programmatically
- **Script components**: Modify Python script components with parameter management
- **Real-time feedback**: Get component states, errors, and runtime information
- **Non-blocking communication**: Stable HTTP-based two-way communication

## Architecture

The system consists of three components working together:

```
Claude AI / MCP Client
        ↓ (stdio/MCP protocol)
   MCP Server (Python)
        ├─→ Rhino Plugin (socket: port 9876)
        └─→ Grasshopper Component (HTTP: port 9999)
```

- **MCP Server**: FastMCP-based server that exposes Rhino and Grasshopper tools
- **Rhino Plugin**: IronPython socket server running inside Rhino
- **Grasshopper Component**: C# HTTP server component in Grasshopper

## Installation

### Prerequisites

- **Rhino 8** or newer
- **Python 3.10+** on your system
- **UV package manager** ([install UV](https://docs.astral.sh/uv/))
- **Claude Desktop** or **Cursor IDE** (optional, for AI integration)

### 1. Install the MCP Server

```bash
# Clone the repository
git clone https://github.com/xunliuDesign/rhino-gh-mcp.git
cd rhino-gh-mcp/mcp_server

# Install with UV
uv sync

# Test the installation
uv run rhino-gh-mcp
```

### 2. Install the Rhino Plugin

1. Open Rhino 8
2. Open the Python Editor: `Tools > Python Script > Edit...`
3. Open `rhino_plugin/rhino_client.py`
4. Run the script (F5 or play button)
5. You should see: `RhinoMCP server started on localhost:9876`

**To stop the server**, type in the Python console:
```python
stop_server()
```

### 3. Install the Grasshopper Component

#### Option A: Use Pre-built Component (Recommended)
1. Build the C# project in `grasshopper_component/` (requires Visual Studio)
2. Copy the compiled `.gha` file to your Grasshopper Components folder
3. Restart Rhino and Grasshopper
4. Add the "rhino_gh_mcp MCP Server" component to your canvas
5. Toggle "RunServer" to True

#### Option B: Use GHPython Script (Development)
1. Open Grasshopper
2. Add a GHPython component
3. Load the server script from the C# component code
4. The HTTP server starts on port 9999

### 4. Configure Claude Desktop

Edit your Claude Desktop configuration (`Settings > Developer > Edit Config`):

```json
{
  "mcpServers": {
    "rhino-gh-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/rhino-gh-mcp/mcp_server",
        "run",
        "rhino-gh-mcp"
      ]
    }
  }
}
```

**Important**: Replace `/path/to/rhino-gh-mcp/mcp_server` with your actual path.

### 5. Configure Cursor IDE (Optional)

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "rhino-gh-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/rhino-gh-mcp/mcp_server",
        "run",
        "rhino-gh-mcp"
      ]
    }
  }
}
```

## Usage

### Quick Start

1. **Start Rhino** and run the Rhino plugin script
2. **Start Grasshopper** (optional) and enable the MCP component
3. **Open Claude Desktop** or Cursor IDE
4. **Start a conversation** with Claude

Example prompts:
- "What objects are in my Rhino scene?"
- "Create a cube at the origin with dimensions 10x10x10"
- "Show me the current Grasshopper definition"
- "Create a number slider connected to a script component"

### Available MCP Tools

#### Rhino Tools
- `get_scene_info()` - Get overview of layers and objects
- `get_layers()` - List all layers
- `get_scene_objects_with_metadata()` - Query objects with filtering
- `capture_viewport()` - Take a screenshot of the viewport
- `execute_rhino_code()` - Run IronPython code in Rhino

#### Grasshopper Tools
- `get_gh_context()` - Get full definition graph
- `get_objects()` - Query specific components
- `get_selected()` - Get selected components
- `update_script()` - Modify script component code and parameters
- `add_component_to_canvas()` - Add new components
- `add_slider_to_canvas()` - Add number sliders
- `connect_components()` - Wire components together
- `set_component_parameter()` - Set parameter values
- `recompute_all()` - Recompute the entire definition

## Configuration

### Environment Variables

Create a `.env` file in `mcp_server/` (copy from `.env.sample`):

```env
# Rhino Connection
RHINO_HOST=localhost
RHINO_PORT=9876

# Grasshopper Connection
GRASSHOPPER_HOST=localhost
GRASSHOPPER_PORT=9999

# Logging
LOG_LEVEL=INFO
```

### Port Configuration

If you need to change the default ports:

1. **Rhino Plugin**: Edit `PORT` variable in `rhino_plugin/rhino_client.py`
2. **Grasshopper Component**: Edit the port in the component parameters
3. **MCP Server**: Update the `.env` file

## Troubleshooting

### Connection Issues

**MCP server can't connect to Rhino:**
- Ensure Rhino plugin is running (check Python console)
- Verify port 9876 is not blocked by firewall
- Check `RHINO_PORT` in `.env` matches the plugin port

**MCP server can't connect to Grasshopper:**
- Ensure the Grasshopper component is active (RunServer = True)
- Verify port 9999 is not blocked
- Check component output for error messages

### Common Errors

**"Command not found: uv"**
- Install UV package manager: https://docs.astral.sh/uv/

**"Could not connect to Rhino script"**
- Start the Rhino plugin before launching Claude Desktop
- The server will show warnings but continue (graceful degradation)

**"Grasshopper server is not available"**
- This is normal if you're not using Grasshopper
- Enable the Grasshopper component if needed

For more detailed troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for:
- Setting up a development environment
- Running tests
- Contributing guidelines
- Code structure and architecture

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture and design
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development guide
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Examples

### Create a Parametric Tower in Rhino

```
Claude, please help me create a parametric tower in Rhino:
1. Create a base circle with radius 5 at the origin
2. Copy it upward 20 times, reducing the radius by 0.2 each time
3. Connect them with a loft
4. Capture the viewport to show me the result
```

### Build a Grasshopper Definition

```
Claude, let's create a simple Grasshopper definition:
1. Add a number slider for the count (0-20)
2. Add a script component that creates circles with increasing radii
3. Connect the slider to the script
4. Show me the component graph
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Inspired by [blender_mcp](https://github.com/ahujasid/blender-mcp) - Blender integration with MCP.

## Support

- **Issues**: https://github.com/xunliuDesign/rhino-gh-mcp/issues
- **Discussions**: https://github.com/xunliuDesign/rhino-gh-mcp/discussions

## Changelog

### v1.0.0 (2025-02-02)
- Initial release
- Simplified architecture with one MCP server
- Removed StreamDiffusion, Replicate, and utility tools
- Focus on core Rhino and Grasshopper functionality
- UV package management
