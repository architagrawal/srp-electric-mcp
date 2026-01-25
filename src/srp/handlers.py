import json
import os
import mcp.types as types
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context
from .client import SrpClient
from .config import Config

class SrpCredentials(BaseModel):
    username: str = Field(description="SRP email address")
    password: str = Field(description="SRP password")

class Confirmation(BaseModel):
    confirmed: bool = Field(description="Confirm to proceed")

async def get_client(ctx: Optional[Context] = None) -> SrpClient:
    """Helper to create and return an authenticated SrpClient."""
    username = Config.get_username()
    password = Config.get_password()
    
    if (not username or not password) and ctx:
        # Use Elicitation to ask user for missing credentials
        result = await ctx.elicit(
            message="SRP credentials are not found in environment. Please provide them to continue.",
            schema=SrpCredentials
        )
        if result.action == "accept" and result.data:
            username = result.data.username
            password = result.data.password
    
    if not username or not password:
        raise ValueError("SRP_USERNAME and SRP_PASSWORD environment variables are not set.")
    return SrpClient(username, password)

def get_account_id(account_id: Optional[str] = None) -> str:
    """Helper to resolve account ID from arguments or environment."""
    aid = account_id or os.getenv("SRP_ACCOUNT_ID")
    if not aid:
        raise ValueError("No Account ID provided or found in SRP_ACCOUNT_ID environment variable.")
    return aid

async def get_energy_usage(account_id: str, start_date: str, end_date: str, ctx: Optional[Context] = None) -> str:
    """
    Fetch hourly energy usage data from SRP for a specific date range.
    
    Args:
        account_id: The SRP billing account number.
        start_date: Start date in MM-DD-YYYY format (e.g., 01-01-2023).
        end_date: End date in MM-DD-YYYY format (e.g., 01-31-2023).
        ctx: Optional MCP Context for elicitation.
    """
    client = await get_client(ctx)
    try:
        await client.login()
        data = await client.get_usage(account_id, start_date, end_date)
        return json.dumps(data, default=str)
    finally:
        await client.close()

async def get_daily_energy_usage(account_id: str, start_date: str, end_date: str, ctx: Optional[Context] = None) -> str:
    """
    Fetch daily energy usage aggregation for a specific date range.
    
    Args:
        account_id: The SRP billing account number.
        start_date: Start date in MM-DD-YYYY format (e.g., 01-01-2023).
        end_date: End date in MM-DD-YYYY format (e.g., 01-31-2023).
        ctx: Optional MCP Context for elicitation.
    """
    client = await get_client(ctx)
    try:
        await client.login()
        data = await client.get_daily_usage(account_id, start_date, end_date)
        return json.dumps(data, default=str)
    finally:
        await client.close()

async def get_user_profile(ctx: Optional[Context] = None) -> str:
    """Fetch the logged-in user profile information."""
    client = await get_client(ctx)
    try:
        await client.login()
        data = await client.get_profile()
        return json.dumps(data, default=str)
    finally:
        await client.close()

async def get_landlord_accounts(ctx: Optional[Context] = None) -> str:
    """Fetch the list of accounts managed under a landlord agreement."""
    client = await get_client(ctx)
    try:
        await client.login()
        data = await client.get_landlord_list()
        return json.dumps(data, default=str)
    finally:
        await client.close()

async def get_billing_info(account_id: Optional[str] = None, ctx: Optional[Context] = None) -> str:
    """
    Fetch current billing information including balance, rate plan, and projected bill amount.
    
    Args:
        account_id: Optional SRP billing account number. Defaults to SRP_ACCOUNT_ID env var.
        ctx: Optional MCP Context for elicitation.
    """
    aid = get_account_id(account_id)
    client = await get_client(ctx)
    try:
        await client.login()
        curr = await client.get_current_bill_info(aid)
        proj = await client.get_bill_projection(aid)
        return json.dumps({"current": curr, "projection": proj}, default=str)
    finally:
        await client.close()

async def get_payment_history(account_id: Optional[str] = None, ctx: Optional[Context] = None) -> str:
    """
    Fetch the payment history and any scheduled future payments for an account.
    
    Args:
        account_id: Optional SRP billing account number. Defaults to SRP_ACCOUNT_ID env var.
        ctx: Optional MCP Context for elicitation.
    """
    aid = get_account_id(account_id)
    client = await get_client(ctx)
    try:
        await client.login()
        history = await client.get_payment_history(aid)
        scheduled = await client.get_scheduled_payments(aid)
        return json.dumps({"history": history, "scheduled": scheduled}, default=str)
    finally:
        await client.close()

async def get_outages(ctx: Optional[Context] = None) -> str:
    """Fetch active power outages and outage reports for the user's service area."""
    client = await get_client(ctx)
    try:
        await client.login()
        data = await client.get_outages()
        return json.dumps(data, default=str)
    finally:
        await client.close()

async def get_documents(account_id: Optional[str] = None, ctx: Optional[Context] = None) -> str:
    """
    Fetch a list of available eBill documents (PDFs) for the specified account.
    
    Args:
        account_id: Optional SRP billing account number. Defaults to SRP_ACCOUNT_ID env var.
        ctx: Optional MCP Context for elicitation.
    """
    aid = get_account_id(account_id)
    client = await get_client(ctx)
    try:
        await client.login()
        data = await client.get_ebill_list(aid)
        return json.dumps(data, default=str)
    finally:
        await client.close()

async def request_srp_api(endpoint: str, method: str = "GET", params: Optional[str] = None, data: Optional[str] = None, ctx: Optional[Context] = None) -> str:
    """
    Perform a raw request to any SRP API endpoint.
    
    Args:
        endpoint: API path (e.g. /accounts/all)
        method: HTTP method (GET/POST)
        params: JSON string of query parameters
        data: JSON string of body data
        ctx: Optional MCP Context for elicitation.
    """
    if method.upper() != "GET" and ctx:
        # Use Elicitation for safety confirmation
        confirm = await ctx.elicit(
            message=f"Caution: You are initiating a {method} request to {endpoint}. Do you want to proceed?",
            schema=Confirmation
        )
        if confirm.action != "accept" or not confirm.data or not confirm.data.confirmed:
            return json.dumps({"status": "error", "message": "Action cancelled by user."})

    client = await get_client(ctx)
    try:
        # Parse JSON params/data if provided
        parsed_params = json.loads(params) if params else None
        parsed_data = json.loads(data) if data else None

        await client.login()
        result = await client.generic_request(endpoint, method, parsed_params, parsed_data)
        return json.dumps(result, default=str)
    finally:
        await client.close()

async def list_srp_endpoints(ctx: Optional[Context] = None) -> str:
    """List all known SRP API endpoints for use with request_srp_api."""
    client = await get_client(ctx)
    try:
        endpoints = await client.list_available_endpoints()
        return json.dumps(endpoints, indent=2)
    finally:
        await client.close()

async def get_smart_summary(account_id: str, days: int = 7, ctx: Context = None) -> str:
    """
    Fetch usage data and use the client's LLM to generate a friendly summary.
    
    Args:
        account_id: SRP billing account number.
        days: Number of days to analyze (max 30).
        ctx: MCP Context required for Sampling.
    """
    if not ctx:
        return "Error: Context is required for smart summary (Sampling capability)."

    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%m-%d-%Y")
    start_date = (datetime.now() - timedelta(days=min(days, 30))).strftime("%m-%d-%Y")

    client = await get_client(ctx)
    try:
        await client.login()
        usage_data = await client.get_daily_usage(account_id, start_date, end_date)
        
        # Prepare content for sampling
        prompt_text = (
            f"Here is the energy usage data for SRP account {account_id} "
            f"from {start_date} to {end_date}:\n"
            f"{json.dumps(usage_data, indent=2)}\n\n"
            "Please provide a concise, friendly summary for the user. "
            "Highlight any significant patterns and offer one concrete tip to save money."
        )

        # Use Sampling to ask the client's LLM for a summary
        response = await ctx.session.create_message(
            messages=[
                types.SamplingMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt_text)
                )
            ],
            max_tokens=300,
            system_prompt="You are a helpful energy savings assistant."
        )
        
        if hasattr(response.content, 'text'):
            return response.content.text
        return str(response.content)

    except Exception as e:
        return f"Error generating summary: {str(e)}"
    finally:
        await client.close()

# --- Resource Logic ---

async def get_accounts_resource() -> str:
    """Fetch all SRP accounts for resource exposure."""
    client = await get_client()
    try:
        await client.login()
        data = await client.get_all_accounts()
        return json.dumps(data, indent=2)
    finally:
        await client.close()

async def get_profile_resource() -> str:
    """Fetch user profile for resource exposure."""
    client = await get_client()
    try:
        await client.login()
        data = await client.get_profile()
        return json.dumps(data, indent=2)
    finally:
        await client.close()

async def get_account_billing_resource(account_id: str) -> str:
    """Fetch specialized billing resource for a specific account."""
    client = await get_client()
    try:
        await client.login()
        curr = await client.get_current_bill_info(account_id)
        proj = await client.get_bill_projection(account_id)
        return json.dumps({"account_id": account_id, "current": curr, "projection": proj}, indent=2)
    finally:
        await client.close()

async def get_account_usage_resource(account_id: str) -> str:
    """Fetch specialized recent usage resource for a specific account."""
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%m-%d-%Y")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%m-%d-%Y")
    
    client = await get_client()
    try:
        await client.login()
        data = await client.get_daily_usage(account_id, start_date, end_date)
        return json.dumps({"account_id": account_id, "period": f"{start_date} to {end_date}", "usage": data}, indent=2)
    finally:
        await client.close()

# --- Prompt Logic ---

def get_analyze_usage_prompt(account_id: str, days: int = 7) -> str:
    """Returns a prompt template for usage analysis."""
    return f"Please analyze the energy usage for SRP account {account_id} over the last {days} days. " \
           "Examine the data for trends, peak usage times, and provide actionable advice on how to reduce consumption."

def get_explain_bill_prompt(account_id: str) -> str:
    """Returns a prompt template for bill explanation."""
    return f"I need an explanation for my current SRP bill (Account: {account_id}). " \
           "Please break down the current balance, rate plan details, and the projected amount for this month."

def get_savings_advisor_prompt(account_id: str) -> str:
    """Returns a structured prompt for energy efficiency consulting."""
    return f"Act as an Energy Savings Advisor for SRP account {account_id}. " \
           "1. Fetch my recent usage and billing data.\n" \
           "2. Compare my current usage to typical efficiency standards.\n" \
           "3. Recommend 3 specific changes I can make this week to save money."

def get_account_comparison_prompt() -> str:
    """Returns a prompt for comparing multiple accounts."""
    return "I have multiple SRP accounts. Please list them all, compare their recent usage and current balances, " \
           "and summarize the total energy footprint across all my properties."
