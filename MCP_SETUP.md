# How to Connect SRP Server to AI Clients

To use the tools you built (`get_billing_info`, `get_outages`, etc.) inside an AI chat interface, you need to configure your MCP Client.

## Standard Configuration (JSON)

Most MCP clients (like Claude Desktop) use a configuration file. Add this entry to your `mcpServers` list.

### 1. Get your Paths
*   **Python Path**: `python` (or your full path, e.g., `C:\Python312\python.exe`)
*   **Script Path**: `c:\Archit\MyCoding\Development\mcp\SRP\src\srp\server.py`

### 2. The Config Snippet
Add this to your configuration file (usually `claude_desktop_config.json` or similar):

```json
{
  "mcpServers": {
    "srp-energy": {
      "command": "python",
      "args": [
        "c:/Archit/MyCoding/Development/mcp/SRP/src/srp/server.py"
      ],
      "env": {
        "SRP_USERNAME": "YOUR_EMAIL@example.com",
        "SRP_PASSWORD": "YOUR_PASSWORD",
        "SRP_ACCOUNT_ID": "YOUR_ACCOUNT_ID"
      }
    }
  }
}
```

### 3. Restart & Use
1.  Save the config file.
2.  Restart your AI Client.
3.  The AI will now have a "plug" icon or "tools" available.
4.  **Try asking:** *"How much was my last electric bill?"*

## Troubleshooting
*   **"Server not found"**: Make sure the path to `server.py` uses forward slashes `/` or double backslashes `\\`.
*   **"Authentication failed"**: Check your `.env` variables or the `env` section in the JSON above.
