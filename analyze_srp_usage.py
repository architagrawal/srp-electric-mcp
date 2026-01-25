import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import statistics

# Add src to path to import srp
sys.path.append(os.path.join(os.getcwd(), 'src'))
from srp.client import SrpClient

async def analyze_usage():
    load_dotenv()
    
    username = os.getenv('SRP_USERNAME')
    password = os.getenv('SRP_PASSWORD')
    account_id = os.getenv('SRP_ACCOUNT_ID')
    
    if not all([username, password, account_id]):
        print("Error: Missing environment variables (SRP_USERNAME, SRP_PASSWORD, SRP_ACCOUNT_ID).")
        return

    client = SrpClient(username, password)
    
    # Calculate date range for past week (relative to current time 2026-01-25)
    # Actually use current time as reference
    now = datetime(2026, 1, 25) # Using 2026-01-25 as today
    end_date = now.strftime('%m-%d-%Y')
    start_date = (now - timedelta(days=7)).strftime('%m-%d-%Y')
    
    print(f"Fetching usage data from {start_date} to {end_date} for account {account_id}...")
    
    try:
        data = await client.get_usage(account_id, start_date, end_date)
        if 'hourlyUsageList' in data:
            # print(f"Number of hourly entries: {len(data['hourlyUsageList'])}")
            pass
        else:
            print("hourlyUsageList NOT found in response.")
            print(f"Full response: {data}")
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return
    finally:
        await client.close()

    # The structure of data['hourlyUsageList'] needs to be inspected.
    # Assuming it's a list of dictionaries with 'date', 'hour', and 'usage' (or similar).
    # Based on previous common patterns for SRP:
    # hourlyUsageList: list of { date: "MM/DD/YYYY", hour: "X AM/PM", kwh: 1.23, ... }
    
    usage_list = data.get('hourlyUsageList', [])
    if not usage_list:
        print("No usage data found.")
        return

    # Group by hour
    hourly_groups = {} # hour_label -> list of kwh
    for entry in usage_list:
        # The 'hour' field is a timestamp like '2026-01-18T00:00:00'
        # Let's extract just the hour part for grouping
        try:
            dt = datetime.fromisoformat(entry.get('hour'))
            hour_label = dt.strftime('%I %p')
            # Sum up all usage types
            kwh = (entry.get('onPeakKwh', 0) or 0) + \
                  (entry.get('offPeakKwh', 0) or 0) + \
                  (entry.get('shoulderKwh', 0) or 0) + \
                  (entry.get('superOffPeakKwh', 0) or 0)
            
            if hour_label not in hourly_groups:
                hourly_groups[hour_label] = []
            hourly_groups[hour_label].append(float(kwh))
        except (ValueError, TypeError):
            continue

    # Calculate averages and find anomalies
    print("\n--- Hourly Usage Trend (Past Week) ---")
    print(f"{'Hour':<15} | {'Average (kWh)':<15} | {'Max (kWh)':<15} | {'Anomaly?'}")
    print("-" * 65)

    # Sort hours logically
    def parse_hour_label(h_str):
        return datetime.strptime(h_str, '%I %p').hour

    sorted_hours = sorted(hourly_groups.keys(), key=parse_hour_label)

    anomalies = []

    for hour_label in sorted_hours:
        vals = hourly_groups[hour_label]
        if not vals: continue
        avg = statistics.mean(vals)
        max_val = max(vals)
        
        is_anomaly = False
        if len(vals) > 1:
            std_dev = statistics.stdev(vals)
            # Find the specific day for the max_val
            for entry in usage_list:
              dt = datetime.fromisoformat(entry.get('hour'))
              entry_hour_label = dt.strftime('%I %p')
              
              kwh = (entry.get('onPeakKwh', 0) or 0) + \
                    (entry.get('offPeakKwh', 0) or 0) + \
                    (entry.get('shoulderKwh', 0) or 0) + \
                    (entry.get('superOffPeakKwh', 0) or 0)

              if entry_hour_label == hour_label and float(kwh) == max_val:
                anomaly_date = dt.strftime('%m-%d-%Y')
                # Threshold for abnormality: > 2x average (tighter than 1.5x) OR very high spike
                if max_val > avg * 1.8 and max_val > 0.5: # 0.5 kWh min to avoid tiny noise
                    is_anomaly = True
                    anomalies.append({
                        'hour': hour_label,
                        'date': anomaly_date,
                        'usage': max_val,
                        'avg': avg
                    })
                break

        anomaly_str = "YES!" if is_anomaly else ""
        print(f"{hour_label:<15} | {avg:<15.3f} | {max_val:<15.3f} | {anomaly_str}")

    if anomalies:
        print("\n--- Detected Abnormal Usage ---")
        for a in anomalies:
            print(f"Spike detected at {a['hour']} on {a['date']}: {a['usage']} kWh (Avg for this hour: {a['avg']:.3f} kWh)")
    else:
        print("\nNo significant abnormal usage detected based on simple threshold (1.5x avg).")

if __name__ == "__main__":
    asyncio.run(analyze_usage())
