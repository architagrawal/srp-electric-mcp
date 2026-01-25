import asyncio
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.srp.client import SrpClient

load_dotenv()

async def main():
    username = os.getenv("SRP_USERNAME")
    password = os.getenv("SRP_PASSWORD")
    account_id = os.getenv("SRP_ACCOUNT_ID")
    
    if not username or not password: 
        print("Missing credentials")
        return

    client = SrpClient(username, password)
    await client.login()
    
    # Get last 2 days
    end = datetime.now()
    start = end - timedelta(days=2)
    
    # Fetch Daily
    daily = await client.get_daily_usage(account_id, start.strftime("%m-%d-%Y"), end.strftime("%m-%d-%Y"))
    print("--- Daily Usage Data ---")
    print(f"Type: {type(daily)}")
    print(json.dumps(daily, indent=2))

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
