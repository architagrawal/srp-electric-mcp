import logging
import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

try:
    from . import handlers
    from .config import Config
    from .token_verifier import IntrospectionTokenVerifier
except ImportError:
    import handlers
    from config import Config
    from token_verifier import IntrospectionTokenVerifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("srp-server")

# OAuth Configuration
def create_oauth_urls() -> dict[str, str]:
    auth_base_url = Config().auth_base_url
    from urllib.parse import urljoin
    return {
        "issuer": auth_base_url,
        "introspection_endpoint": urljoin(auth_base_url, "protocol/openid-connect/token/introspect"),
    }

oauth_urls = create_oauth_urls()
token_verifier = IntrospectionTokenVerifier(
    introspection_endpoint=oauth_urls["introspection_endpoint"],
    server_url=f"http://{Config.get_host()}:{Config.get_port()}",
    client_id=Config.get_oauth_client_id(),
    client_secret=Config.get_oauth_client_secret(),
)

# Initialize FastMCP server with Auth
mcp = FastMCP(
    "srp",
    host=Config.get_host(),
    port=Config.get_port(),
    token_verifier=token_verifier,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(oauth_urls["issuer"]),
        required_scopes=[Config.get_mcp_scope()],
        resource_server_url=AnyHttpUrl(f"http://{Config.get_host()}:{Config.get_port()}"),
    ),
)

# Register tools from handlers
mcp.tool()(handlers.get_energy_usage)
mcp.tool()(handlers.get_daily_energy_usage)
mcp.tool()(handlers.get_user_profile)
mcp.tool()(handlers.get_landlord_accounts)
mcp.tool()(handlers.get_billing_info)
mcp.tool()(handlers.get_payment_history)
mcp.tool()(handlers.get_outages)
mcp.tool()(handlers.get_documents)
mcp.tool()(handlers.request_srp_api)
mcp.tool()(handlers.list_srp_endpoints)
mcp.tool()(handlers.get_smart_summary)

# Register resources
@mcp.resource("srp://accounts")
async def get_accounts() -> str:
    """Provides a list of all linked SRP accounts."""
    return await handlers.get_accounts_resource()

@mcp.resource("srp://profile")
async def get_profile() -> str:
    """Provides the logged-in user's profile information."""
    return await handlers.get_profile_resource()

@mcp.resource("srp://{account_id}/billing")
async def get_account_billing(account_id: str) -> str:
    """Provides detailed billing and projection info for a specific account."""
    return await handlers.get_account_billing_resource(account_id)

@mcp.resource("srp://{account_id}/usage")
async def get_account_usage(account_id: str) -> str:
    """Provides recent (last 7 days) daily usage data for a specific account."""
    return await handlers.get_account_usage_resource(account_id)

# Register prompts
@mcp.prompt("analyze-usage")
def analyze_usage(account_id: str, days: int = 7) -> str:
    """Template for analyzing energy usage over time."""
    return handlers.get_analyze_usage_prompt(account_id, days)

@mcp.prompt("explain-bill")
def explain_bill(account_id: str) -> str:
    """Template for explaining billing details and projections."""
    return handlers.get_explain_bill_prompt(account_id)

@mcp.prompt("savings-advisor")
def savings_advisor(account_id: str) -> str:
    """Structured template for energy efficiency consulting."""
    return handlers.get_savings_advisor_prompt(account_id)

@mcp.prompt("account-comparison")
def account_comparison() -> str:
    """Template for comparing multiple SRP accounts."""
    return handlers.get_account_comparison_prompt()

if __name__ == "__main__":
    mcp.run(transport="stdio")
