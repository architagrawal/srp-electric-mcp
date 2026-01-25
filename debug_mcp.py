import asyncio
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.srp.server"],
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            end = datetime.now()
            start = end - timedelta(days=7)
            
            result = await session.call_tool("get_daily_energy_usage", {
                "account_id": os.getenv("SRP_ACCOUNT_ID"),
                "start_date": start.strftime("%m-%d-%Y"),
                "end_date": end.strftime("%m-%d-%Y")
            })
            
            # Print type and keys
            resp_text = result.content[0].text
            try:
                data = json.loads(resp_text)
                print(f"Type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    if 'dailyReceivedList' in data:
                        print(f"Daily List Len: {len(data['dailyReceivedList'])}")
                elif isinstance(data, list):
                    print(f"List Len: {len(data)}")
                    if len(data) > 0:
                         print(f"First Item Keys: {list(data[0].keys())}")
                
                # Print a snippet
                print(json.dumps(data, indent=2)[:500])
                
            except Exception as e:
                print(f"JSON Parse Error: {e}")
                print(resp_text[:500])

if __name__ == "__main__":
    asyncio.run(main())
