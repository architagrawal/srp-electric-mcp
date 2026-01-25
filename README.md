# SRP Energy MCP Server

An MCP (Model Context Protocol) server for accessing authentication-protected data from the SRP (Salt River Project) Energy portal.

> [!TIP]
> **Enjoying this tool?** 🌟 **Star this repository** to show your support! It helps others find the project and keeps development active.

---

## 💼 Work with me!
**I am currently open to full-time job opportunities.** If you like this project and are looking for a developer who can build robust API integrations and AI tools, let's chat!

- **LinkedIn**: [Archit Agrawal](https://www.linkedin.com/in/architagrawal/)
- **GitHub**: [@architagrawal](https://github.com/architagrawal)

---

## Quick Start (One-Click Setup)


We provide a user-friendly setup wizard to get you started in seconds.

1.  **Configure Credentials**:
    Double-click **`Setup.bat`**. This will open a browser window where you can securely log in to your SRP account.

2.  **Start the Server**:
    Double-click **`Start.bat`**.

That's it! Your server is now running and ready to accept requests.

## Data Analysis & Features
*   **Hourly & Daily Usage**: Retrieve detailed energy consumption data.
*   **Billing Info**: Get current balance, bill projection, and rate plan details.
*   **Payments**: View payment history and scheduled payments.
*   **Outages**: Check for active outages and view outage history.
*   **Documents**: List available eBills.
*   **Universal Access**: Execute raw API requests against any SRP endpoint.

## Setup

### 1. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```
*Note: Requires `mcp` and `httpx` libraries.*

### 2. Configuration (Environment Variables)
To keep your credentials safe, this server uses environment variables. **Do not hardcode your password in the source code.**

Create a `.env` file in the project root:
```ini
SRP_USERNAME=your_email@example.com
SRP_PASSWORD=your_srp_password
SRP_ACCOUNT_ID=1234567890
```

### 3. Usage with Claude Desktop (or other MCP Clients)
Add the server to your MCP client configuration (e.g., `claude_desktop_config.json`).
Pass the credentials via `env`:

```json
{
  "mcpServers": {
    "srp-energy": {
      "command": "python",
      "args": ["/path/to/SRP/src/srp/server.py"],
      "env": {
        "SRP_USERNAME": "your_email@example.com",
        "SRP_PASSWORD": "your_srp_password",
        "SRP_ACCOUNT_ID": "1234567890"
      }
    }
  }
}
```

## Tools

| Tool Name | Description |
|-----------|-------------|
| `get_billing_info` | Balance, rate plan, and bill projection. |
| `get_payment_history` | Past and scheduled payments. |
| `get_energy_usage` | Hourly energy usage for a date range. |
| `get_daily_energy_usage` | Daily energy usage for a date range. |
| `get_outages` | Active outages and history. |
| `get_user_profile` | Account holder details. |
| `request_srp_api` | Raw access to any SRP API endpoint. |

## Verification
You can use the built-in demo script to test your connection:
```bash
python demo_client.py
```

## Credits

**Developed by Archit**

If you have questions, feedback, or just want to connect, feel free to reach out!
- **GitHub**: github.com/architagrawal


*Built with ❤️ using the Model Context Protocol (MCP).*
