# Hosting & Integrations Guide

## 1. Local Hosting (Standard)
Currently, your server uses **Stdio** (Standard Input/Output). This is the most secure and common way to run MCP servers.
*   **How it works**: An application (like Claude Desktop or Antigravity) runs the `python src/srp/server.py` command in the background.
*   **Connectivity**: The server and the Agent must be on the **same computer**.
*   **Setup**: Use the JSON config from `MCP_SETUP.md`.

## 2. Remote Hosting (Advanced)
If you want to host this on a server (like AWS, Render, or a VPS) so you can access it from *any* computer, you need to switch to **SSE (Server-Sent Events)**.

### Steps to Convert for Remote Hosting
1.  **Install Uvicorn**: `pip install uvicorn`
2.  **Modify `server.py`**:
    Change the `async with stdio_server()` block to use `mcp.server.sse.SseServerTransport`.
3.  **Run with Uvicorn**:
    ```bash
    uvicorn src.srp.server:app --port 8000
    ```
4.  **Connect**:
    Your Agent config would change from `command` to `url`:
    ```json
    {
      "mcpServers": {
        "srp-remote": {
          "url": "http://your-server-ip:8000/sse"
        }
      }
    }
    ```

## 3. Connecting to Antigravity (Editor Agent)
To connect this server to your AI Code Editor:

1.  **Look for "MCP Settings"**:
    Most MCP-compatible editors have a settings file (often `config.json` or `settings.json`) in their config directory.
2.  **Add the Server**:
    Use the same JSON configuration found in `MCP_SETUP.md`.
3.  **Restart**:
    Restart the editor. The AI agent inside the editor should now have access to your tools.

*Note: Since I am the AI running in your current session, I cannot "hot-plug" new tools into myself instantly. But once you configure the editor, **future** sessions will have access!*
