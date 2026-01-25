import asyncio
import os
import json
from dotenv import load_dotenv
from src.srp.client import SrpClient

# Load environment variables
load_dotenv()

async def main():
    username = os.getenv("SRP_USERNAME")
    password = os.getenv("SRP_PASSWORD")
    account_id = os.getenv("SRP_ACCOUNT_ID")
    
    if not username or not password:
        print("Error: SRP_USERNAME and SRP_PASSWORD must be set in .env")
        return

    if not account_id:
        print("Warning: SRP_ACCOUNT_ID not set in .env. Fetching usage might fail if you don't provide one manually.")
        account_id = input("Enter SRP Account ID: ")

    print(f"Logging in as {username}...")
    client = SrpClient(username, password)
    
    try:
        await client.login()
        print("Login successful! XSRF Token retrieved.")

        # 1. Profile
        print("\n--- Profile ---")
        profile = await client.get_profile()
        print(f"User: {profile.get('email', 'Unknown')}")

        # 2. Billing
        print(f"\n--- Billing Info ({account_id}) ---")
        bill_info = await client.get_current_bill_info(account_id)
        projection = await client.get_bill_projection(account_id)
        print(f"DEBUG RAW BILL: {bill_info}")
        print(f"Current Balance: {bill_info.get('billedAmount', 'N/A')}")
        print(f"Projected Bill: {projection.get('projectedBillAmount', 'N/A')}")

        # 3. Payments
        print("\n--- Payment History ---")
        history = await client.get_payment_history(account_id)
        if history and len(history) > 0:
            last_payment = history[0]
            print(f"Last Payment: {last_payment.get('paymentAmount')} on {last_payment.get('paymentDate')}")
        else:
            print("No recent payments found.")

        # 4. Usage
        start_date = "01-01-2024" 
        end_date = "01-02-2024"
        print(f"\n--- Usage ({start_date} to {end_date}) ---")
        daily = await client.get_daily_usage(account_id, start_date, end_date)
        print(f"Daily Data Points: {len(daily)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

    print("\n--- Testing list_srp_endpoints ---")
    try:
        endpoints = await client.list_available_endpoints()
        # Print just the first few lines to avoid spamming the console
        print("Available SRP API Endpoints:")
        for i, (ep, desc) in enumerate(endpoints.items()):
            if i >= 10:
                print("... (and many more)")
                break
            print(f"- {ep}: {desc}")
    except Exception as e:
        print(f"Error: {e}")
        
    # print("\n--- Testing generic request (Get Rate Code) ---")
    # try:
    #     result = await client.call_tool("request_srp_api", {"endpoint": "accounts/getratecode"})
    #     print(result[0].text)
    # except Exception as e:
    #     print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
