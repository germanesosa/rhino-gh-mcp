# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Rhino & Grasshopper MCP integration.

## Quick Diagnostic Checklist

Before diving into specific issues, run through this checklist:

- [ ] Rhino 8 is running
- [ ] Rhino plugin script is running (check Python console)
- [ ] Grasshopper component is active (if using Grasshopper)
- [ ] MCP server is configured in Claude Desktop/Cursor
- [ ] No firewall blocking ports 9876 or 9999
- [ ] Python 3.10+ is installed
- [ ] UV package manager is installed

## Installation Issues

### "Command not found: uv"

**Problem**: UV package manager is not installed or not in PATH.

**Solution**:
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

### "No module named 'mcp'"

**Problem**: Dependencies not installed.

**Solution**:
```bash
cd mcp_server
uv sync  # This installs all dependencies
```

### "Permission denied" when running Rhino plugin

**Problem**: Script file permissions or Rhino scripting disabled.

**Solution**:
```bash
# Make script executable (macOS/Linux)
chmod +x rhino_plugin/rhino_client.py

# In Rhino:
# Tools > Options > RhinoScript > Enable Python scripting
```

## Connection Issues

### "Could not connect to Rhino script"

**Symptoms**: MCP server starts but shows warning about Rhino connection.

**Diagnosis**:
```bash
# Check if Rhino plugin is running
# In Rhino Python console, you should see:
# "RhinoMCP server started on localhost:9876"

# Check if port is listening (macOS/Linux)
lsof -i :9876

# On Windows
netstat -an | findstr :9876
```

**Solutions**:

1. **Start Rhino plugin first**:
   - Open Rhino Python Editor
   - Load and run `rhino_plugin/rhino_client.py`
   - Verify startup message appears
   - Then start MCP server

2. **Check firewall**:
   ```bash
   # macOS: System Preferences > Security & Privacy > Firewall
   # Allow incoming connections for Rhino

   # Windows: Windows Defender Firewall
   # Allow Rhino through firewall
   ```

3. **Try different port**:
   ```bash
   # Edit rhino_plugin/rhino_client.py
   # Change: PORT = 9876 to PORT = 9877

   # Edit mcp_server/.env
   # Change: RHINO_PORT=9876 to RHINO_PORT=9877
   ```

4. **Test connection manually**:
   ```bash
   # Use telnet to test the port
   telnet localhost 9876
   # If connection refused, Rhino plugin is not running
   ```

### "Grasshopper server is not available"

**Symptoms**: MCP server warns that Grasshopper is not available.

**Diagnosis**:
```bash
# Check if component is running
# In Grasshopper, the component should show:
# Status: "Server running on port 9999"

# Test the HTTP endpoint
curl http://localhost:9999
# Should return JSON response
```

**Solutions**:

1. **Enable the component**:
   - Grasshopper component input "RunServer" must be True
   - Use a Boolean Toggle connected to RunServer

2. **Check port availability**:
   ```bash
   # macOS/Linux
   lsof -i :9999

   # Windows
   netstat -an | findstr :9999
   ```

3. **Port conflict**:
   - If another process is using 9999, change the port
   - Update component parameter and .env file

4. **Component not loaded**:
   - Rebuild the C# project
   - Copy .gha to correct Grasshopper Components folder:
     - macOS: `~/Library/Application Support/McNeel/Rhinoceros/8.0/Plug-ins/Grasshopper (xyz)/Components/`
     - Windows: `%APPDATA%\Grasshopper\Libraries\`
   - Restart Rhino and Grasshopper

### "Connection timeout" errors

**Problem**: Commands take too long to execute.

**Solution**:
```python
# Increase timeout in mcp_server/rhino_gh_mcp/rhino_tools.py
class RhinoConnection:
    def __init__(self, host='localhost', port=9876):
        self.timeout = 60.0  # Increase from 30 to 60 seconds
```

## Runtime Errors

### "IronPython syntax error" in Rhino

**Problem**: Code uses Python 3 syntax not supported in IronPython 2.7.

**Common Culprits**:
- f-strings: `f"Hello {name}"` ❌
- Type hints: `def func(x: int) -> str:` ❌
- Walrus operator: `if (n := len(data)) > 10:` ❌

**Solution**:
```python
# Use .format() instead of f-strings
"Hello {0}".format(name)  # ✓

# Remove type hints
def func(x):  # ✓
    return str(x)

# No walrus operator
n = len(data)  # ✓
if n > 10:
    pass
```

### "Object reference not set to an instance" (Grasshopper)

**Problem**: Component reference is invalid or component doesn't exist.

**Diagnosis**:
```
# Check the GUID is correct
# In Grasshopper, select the component
# Right-click > Copy GUID
# Verify it matches the one in your command
```

**Solution**:
1. Use `get_gh_context()` to find correct GUIDs
2. Check that component still exists in definition
3. Verify component hasn't been deleted or recreated

### "Socket connection reset" errors

**Problem**: Rhino plugin crashed or restarted.

**Solutions**:

1. **Check Rhino console for errors**:
   - Look for Python exceptions
   - Check for stack traces

2. **Restart Rhino plugin**:
   ```python
   # In Rhino Python console
   stop_server()
   # Then reload and run rhino_client.py again
   ```

3. **Check for script errors**:
   - Look in Rhino Python editor for syntax errors
   - Check the log file (see logging section below)

## Claude Desktop Integration

### "MCP server not appearing in Claude"

**Problem**: Server not configured or not starting.

**Diagnosis**:
```bash
# Check Claude Desktop config
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json

# Verify JSON is valid
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
```

**Solutions**:

1. **Verify configuration**:
   ```json
   {
     "mcpServers": {
       "rhino-gh-mcp": {
         "command": "uv",
         "args": [
           "--directory",
           "/absolute/path/to/rhino-gh-mcp/mcp_server",
           "run",
           "rhino-gh-mcp"
         ]
       }
     }
   }
   ```

2. **Use absolute paths**, not relative:
   - ❌ `"./mcp_server"`
   - ✓ `"/Users/username/rhino-gh-mcp/mcp_server"`

3. **Restart Claude Desktop** after config changes

4. **Check Claude logs**:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### "Tools not showing up in Claude"

**Problem**: Server starts but tools aren't available.

**Solutions**:

1. **Check tool loading**:
   ```bash
   # In MCP server logs, you should see:
   # "Loaded tools: rhino, grasshopper"
   ```

2. **Verify tools parameter**:
   ```bash
   # Make sure your config loads the right tools
   uv run python -m rhino_gh_mcp.main --tools rhino,grasshopper
   ```

3. **Restart Claude chat**:
   - Close and reopen the chat window
   - Tools are loaded per-session

## Performance Issues

### "Viewport capture is slow"

**Problem**: Taking screenshots takes too long.

**Solutions**:

1. **Reduce viewport resolution**:
   - In Rhino: `ViewCaptureToFile` settings
   - Smaller viewport = faster capture

2. **Simplify display mode**:
   - Use "Wireframe" instead of "Rendered"
   - Disable shadows and anti-aliasing

3. **Reduce scene complexity**:
   - Hide unnecessary layers
   - Simplify geometry

### "Grasshopper recompute hangs"

**Problem**: `recompute_all()` doesn't return.

**Solutions**:

1. **Check for infinite loops** in script components

2. **Simplify definition**:
   - Disable heavy components temporarily
   - Use `expire_and_get_info()` on specific components instead

3. **Increase timeout**:
   ```python
   # In grasshopper_tools.py
   self.timeout = 120.0  # Increase to 2 minutes
   ```

## Debugging

### Enable Debug Logging

```bash
# Method 1: Environment variable
export LOG_LEVEL=DEBUG
uv run rhino-gh-mcp

# Method 2: .env file
# Edit mcp_server/.env
LOG_LEVEL=DEBUG
```

### Check Log Files

**MCP Server Logs**:
```bash
# Logs go to stderr, capture them:
uv run rhino-gh-mcp 2>&1 | tee mcp_server.log
```

**Rhino Plugin Logs**:
```bash
# macOS
cat ~/Library/Application\ Support/RhinoMCP/logs/rhino_mcp.log

# Windows
type %LOCALAPPDATA%\RhinoMCP\logs\rhino_mcp.log
```

**Grasshopper Component Logs**:
```
# Check component output parameter "Debug"
# Also check Rhino command line for WriteLine output
```

### Test Individual Components

**Test Rhino Socket**:
```python
# In Python (not IronPython)
import socket
import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 9876))

cmd = {"type": "get_scene_info", "params": {}}
s.sendall(json.dumps(cmd).encode())

response = s.recv(4096)
print(response.decode())
s.close()
```

**Test Grasshopper HTTP**:
```bash
# Use curl
curl -X POST http://localhost:9999 \
  -H "Content-Type: application/json" \
  -d '{"type": "is_server_available"}'
```

## Platform-Specific Issues

### macOS

**Gatekeeper blocking script**:
```bash
# If "unidentified developer" error
xattr -d com.apple.quarantine rhino_plugin/rhino_client.py
```

**Permission issues**:
```bash
# Grant Rhino access in System Preferences
# Security & Privacy > Privacy > Automation
```

### Windows

**Antivirus blocking connections**:
- Whitelist Rhino.exe in antivirus
- Allow Python scripts in Windows Defender

**Path issues**:
```powershell
# Use forward slashes or escape backslashes in config
"C:/Users/username/rhino-gh-mcp/mcp_server"  # ✓
"C:\\Users\\username\\rhino-gh-mcp\\mcp_server"  # ✓
```

## Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Search [GitHub Issues](https://github.com/xunliuDesign/rhino-gh-mcp/issues)
3. Enable debug logging and collect logs
4. Prepare a minimal reproduction case

### How to Ask for Help

When opening an issue, include:

```markdown
**Environment:**
- OS: macOS 14.2 / Windows 11 / etc.
- Rhino version: 8.4.24010.12305
- Python version: 3.12.1
- UV version: 0.1.18

**What I'm trying to do:**
[Clear description]

**What's happening:**
[Error message or unexpected behavior]

**Steps to reproduce:**
1. ...
2. ...
3. ...

**Logs:**
[Paste relevant logs with DEBUG level enabled]

**Already tried:**
- Restarted Rhino ✓
- Checked firewall ✓
- etc.
```

### Resources

- [GitHub Issues](https://github.com/xunliuDesign/rhino-gh-mcp/issues)
- [GitHub Discussions](https://github.com/xunliuDesign/rhino-gh-mcp/discussions)
- [Rhino Developer Forum](https://discourse.mcneel.com/c/scripting)
- [MCP Documentation](https://modelcontextprotocol.io/)

## Known Issues

### Issue: Large viewport images cause memory errors

**Status**: Known limitation

**Workaround**: Reduce viewport size or image quality

### Issue: Grasshopper component doesn't work in Rhino 7

**Status**: Rhino 8+ required for some features

**Workaround**: Upgrade to Rhino 8

## FAQ

**Q: Can I use this with Rhino 7?**
A: Yes, but Rhino 8 is recommended. Some features may not work in Rhino 7.

**Q: Do both Rhino and Grasshopper need to be running?**
A: No, they're independent. Run only what you need. The MCP server gracefully handles missing components.

**Q: Can I run the MCP server on a different machine?**
A: Currently, only localhost is supported. Remote connections would require authentication and encryption.

**Q: Why are there two different protocols (socket and HTTP)?**
A: Rhino uses IronPython which has native socket support. Grasshopper uses C# where HTTP is more robust. See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

**Q: Can I modify the code that runs in Rhino?**
A: Yes, but be careful with the security implications. Only run code from trusted sources.
