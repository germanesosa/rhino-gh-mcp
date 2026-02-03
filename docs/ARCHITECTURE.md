# Architecture

This document explains the architecture and design decisions of the Rhino & Grasshopper MCP integration.

## System Overview

The system consists of three main components that communicate to enable AI-assisted 3D modeling:

```
┌──────────────────────────────────┐
│   Claude AI / MCP Client         │
│   (Claude Desktop, Cursor IDE)   │
└────────────┬─────────────────────┘
             │ stdio (MCP protocol)
             ▼
┌──────────────────────────────────┐
│      MCP Server (Python)         │
│   ┌──────────────────────────┐   │
│   │   FastMCP Server         │   │
│   │  - RhinoTools           │   │
│   │  - GrasshopperTools     │   │
│   └──────────────────────────┘   │
└──────┬──────────────┬────────────┘
       │              │
   socket (9876)  HTTP (9999)
       │              │
       ▼              ▼
┌─────────────┐ ┌────────────────┐
│ Rhino Plugin│ │ Grasshopper    │
│ (IronPython)│ │ Component (C#) │
│             │ │                │
│ Socket      │ │ HTTP Server    │
│ Server      │ │                │
└─────────────┘ └────────────────┘
```

## Component Details

### 1. MCP Server (Python)

**Location**: `mcp_server/rhino_gh_mcp/`

**Purpose**: Central hub that exposes Rhino and Grasshopper functionality through the Model Context Protocol.

**Technology Stack**:
- **FastMCP**: Anthropic's MCP SDK for Python
- **UV**: Modern Python package manager
- **Python 3.10+**: Runtime environment

**Key Files**:
- `server.py` - Main MCP server with lifecycle management
- `rhino_tools.py` - Rhino integration tools
- `grasshopper_tools.py` - Grasshopper integration tools
- `main.py` - Entry point with CLI argument parsing

**Communication**:
- **Input**: stdio (from Claude AI via MCP protocol)
- **Output**: JSON-RPC responses via stdio
- **To Rhino**: TCP socket on port 9876
- **To Grasshopper**: HTTP requests on port 9999

### 2. Rhino Plugin (IronPython)

**Location**: `rhino_plugin/rhino_client.py`

**Purpose**: Socket server running inside Rhino that receives commands from the MCP server.

**Technology Stack**:
- **IronPython 2.7**: Rhino's embedded Python
- **RhinoCommon API**: Rhino .NET API
- **rhinoscriptsyntax**: Rhino Python wrapper

**Communication Protocol**: Raw JSON over TCP
- **Server Port**: 9876 (default)
- **Buffer Size**: 10MB (for large viewport images)
- **Timeout**: Configurable per command

**Command Format**:
```python
{
  "type": "command_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Response Format**:
```python
{
  "status": "success" | "error",
  "message": "...",
  "data": {...}
}
```

### 3. Grasshopper Component (C#)

**Location**: `grasshopper_component/rhino_gh_mcpComponent.cs`

**Purpose**: HTTP server component in Grasshopper that enables canvas manipulation.

**Technology Stack**:
- **C# 7.0**: .NET Framework 4.8
- **Grasshopper SDK**: Component development framework
- **Eto.Forms**: Cross-platform UI framework (if needed)

**Communication Protocol**: HTTP-like over TCP
- **Server Port**: 9999 (default)
- **Method**: POST with JSON body
- **Headers**: Content-Length, Content-Type

**HTTP Request Format**:
```
POST / HTTP/1.1
Content-Type: application/json
Content-Length: 123

{
  "type": "command_name",
  "param1": "value1"
}
```

**HTTP Response Format**:
```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 456

{
  "status": "success",
  "result": {...}
}
```

## Communication Flows

### Rhino Command Execution

```
1. Claude AI → MCP Server
   "Create a cube at the origin"

2. MCP Server → rhino_tools.py
   execute_rhino_code(code="...")

3. RhinoTools → Rhino Plugin (socket)
   {"type": "execute_code", "params": {"code": "..."}}

4. Rhino Plugin → Rhino API
   Executes IronPython code

5. Rhino Plugin → RhinoTools (socket)
   {"status": "success", "data": {...}}

6. RhinoTools → MCP Server
   Returns result

7. MCP Server → Claude AI
   "Created cube with ID abc123"
```

### Grasshopper Component Update

```
1. Claude AI → MCP Server
   "Update the script component to generate circles"

2. MCP Server → grasshopper_tools.py
   update_script(instance_guid="...", code="...")

3. GrasshopperTools → GH Component (HTTP)
   POST {"type": "update_script", "instance_guid": "..."}

4. GH Component → Grasshopper API
   Modifies script component on UI thread

5. GH Component → GrasshopperTools (HTTP response)
   {"status": "success", "result": {...}}

6. GrasshopperTools → MCP Server
   Returns result

7. MCP Server → Claude AI
   "Updated script component successfully"
```

## Design Decisions

### Why One MCP Server for Both Rhino and Grasshopper?

**Decision**: Use a single MCP server with multiple tool modules.

**Rationale**:
1. **Unified Context**: Rhino and Grasshopper work together in the same document
2. **Simpler Configuration**: Users configure one MCP server, not two
3. **Tool Discovery**: All tools appear in one place via MCP protocol
4. **Graceful Degradation**: Server continues if one component is unavailable
5. **Shared Authentication**: Single point for managing connections

### Why Different Communication Protocols?

**Rhino**: Raw JSON over TCP socket
- IronPython has native socket support
- Simple implementation
- Low overhead
- Persistent connection

**Grasshopper**: HTTP over TCP
- C# HTTP client libraries are robust
- Standard protocol for debugging
- Request/response model fits component updates
- Easier to test with curl/Postman

### Why IronPython for Rhino Plugin?

**Alternatives Considered**:
- C# Rhino plugin
- RhinoCommon .NET plugin
- RhinoScript

**Choice**: IronPython script

**Rationale**:
- No compilation required
- Easy to modify and iterate
- Direct access to RhinoCommon API
- Users can customize without Visual Studio
- Lightweight distribution

### Thread Safety

**Rhino Plugin**:
- Uses `Rhino.RhinoApp.Idle` event for thread-safe execution
- Socket server runs on background thread
- Commands are queued and executed on main thread

**Grasshopper Component**:
- Uses `RhinoApp.InvokeOnUiThread()` for UI operations
- HTTP server runs on background thread
- Component modifications happen on UI thread
- `ManualResetEventSlim` for synchronization

## Data Flow

### Metadata Management

Both Rhino and Grasshopper use a standardized metadata system:

```python
{
  "id": "guid-string",           # Unique identifier
  "short_id": "DDHHMMSS",        # Display identifier
  "name": "Object Name",         # User-friendly name
  "description": "...",          # Description
  "type": "Curve|Surface|...",   # Geometry type
  "layer": "Layer Name",         # Layer assignment
  "bbox": [[x,y,z], ...],       # Bounding box points
  "created_at": "timestamp",     # Creation time
  "user_text": {...}            # Additional key-value pairs
}
```

### Connection Lifecycle

**Startup**:
```
1. MCP server starts (via Claude Desktop)
2. Server attempts to connect to Rhino (port 9876)
   - Success: logs "Connected to Rhino"
   - Failure: logs warning, continues
3. Server checks Grasshopper availability (port 9999)
   - Available: logs "Grasshopper server available"
   - Unavailable: logs warning, continues
4. Server registers tools and prompts
5. Ready to receive commands
```

**Shutdown**:
```
1. MCP server receives shutdown signal
2. Disconnects from Rhino socket
3. Disconnects from Grasshopper
4. Cleans up resources
5. Exits gracefully
```

## Error Handling

### Connection Failures

**Strategy**: Graceful degradation

- If Rhino is unavailable, Grasshopper tools still work
- If Grasshopper is unavailable, Rhino tools still work
- Warnings are logged but server continues
- Tools check connection before executing

### Command Failures

**Strategy**: Detailed error reporting

- Exceptions are caught at each level
- Error messages include context
- Stack traces are logged but not exposed to user
- User sees actionable error message

### Example Error Flow:
```
1. MCP Server receives malformed command
2. Validation fails in rhino_tools.py
3. Returns error to MCP Server
4. MCP Server logs full error
5. Returns user-friendly message to Claude
   "Invalid parameter: expected number, got string"
```

## Security Considerations

### Network Security

- **Localhost Only**: Servers bind to 127.0.0.1
- **No Authentication**: Assumes local trusted environment
- **No Encryption**: Not needed for localhost communication

### Code Execution

- **Rhino Plugin**: Executes arbitrary IronPython code
  - Risk: Code runs with Rhino's permissions
  - Mitigation: Only accepts local connections

- **Grasshopper Component**: Executes Python scripts in GH
  - Risk: Can modify entire Grasshopper definition
  - Mitigation: User must explicitly enable component

### Future Enhancements

For production deployment:
1. Add API token authentication
2. Support remote connections with TLS
3. Implement rate limiting
4. Add command whitelisting
5. Sandboxed code execution

## Performance Considerations

### Buffer Sizes

- **Rhino Socket**: 10MB buffer for large viewport images
- **Grasshopper HTTP**: Dynamic based on Content-Length

### Timeouts

- **Rhino Commands**: 30 seconds default
- **Grasshopper Commands**: 60 seconds default
- **MCP Protocol**: Inherits from FastMCP defaults

### Optimization Strategies

1. **Connection Pooling**: Reuse connections instead of reconnecting
2. **Lazy Loading**: Only load tools when needed
3. **Caching**: Cache scene info to reduce API calls
4. **Async Operations**: Non-blocking I/O where possible

## Extension Points

The architecture supports future extensions:

### Adding New Tools

```python
# In server.py
from .new_tools import NewTools

def load_tools(app, tool_names):
    tool_map = {
        "rhino": ("rhino_gh_mcp.rhino_tools", "RhinoTools"),
        "grasshopper": ("rhino_gh_mcp.grasshopper_tools", "GrasshopperTools"),
        "new_tool": ("rhino_gh_mcp.new_tools", "NewTools"),  # Add here
    }
    # ...
```

### Custom Prompts

```python
@app.prompt()
def my_custom_strategy() -> str:
    """Define custom strategy for Claude"""
    return """Custom guidelines here..."""
```

### Alternative Transports

FastMCP supports multiple transports:
- stdio (default for Claude Desktop)
- SSE (Server-Sent Events for web)
- Custom transport implementations

## Dependencies

### MCP Server

```toml
mcp[cli]>=1.3.0      # Core MCP framework
pillow>=10.0.0       # Image processing
requests>=2.31.0     # HTTP client for Grasshopper
python-dotenv        # Environment variables (optional)
```

### Rhino Plugin

- IronPython 2.7 (bundled with Rhino)
- RhinoCommon API (bundled with Rhino)
- rhinoscriptsyntax (bundled with Rhino)
- No external dependencies

### Grasshopper Component

- .NET Framework 4.8
- Grasshopper SDK
- RhinoCommon API
- Newtonsoft.Json (for JSON parsing)

## Version Compatibility

| Component | Minimum Version | Tested Version |
|-----------|----------------|----------------|
| Rhino | 7.0 | 8.0 |
| Grasshopper | Bundled with Rhino | 8.0 |
| Python | 3.10 | 3.12 |
| MCP Protocol | 1.3.0 | 1.3.0 |
| FastMCP | 1.3.0 | Latest |

## Future Architecture Improvements

### Potential Enhancements

1. **WebSocket Support**: Real-time bidirectional communication
2. **Plugin System**: Hot-reload new tools without restart
3. **State Management**: Persistent session state across restarts
4. **Batch Operations**: Execute multiple commands atomically
5. **Event Streaming**: Stream Rhino/GH events to MCP server
6. **Cloud Deployment**: Host MCP server remotely with secure tunneling

### Migration Path

If moving to WebSocket:
```
Current:  MCP Server → Socket → Rhino
Proposed: MCP Server → WebSocket → Rhino
Benefits: Bidirectional events, connection management
```
