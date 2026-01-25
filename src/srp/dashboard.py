import asyncio
import os
import json
import sys
from datetime import datetime, timedelta
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.live import Live
from rich.style import Style
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv()

console = Console()

class SrpDashboard:
    def __init__(self):
        self.data = {}
        self.account_id = os.getenv("SRP_ACCOUNT_ID")

    async def fetch_data(self, session: ClientSession):
        """Fetches all necessary data from SRP via MCP Tools"""
        
        # 0. Ensure Account ID (Fetching profile if needed not strictly implemented here to keep it simple, relying on env)
        if not self.account_id:
            console.log("[yellow]Warning: SRP_ACCOUNT_ID not set. Some data may be missing.[/]")

        # Prepare dates for usage
        end = datetime.now()
        start = end - timedelta(days=30)
        start_str = start.strftime("%m-%d-%Y")
        end_str = end.strftime("%m-%d-%Y")

        # PARALLEL EXECUTION
        # Note: MCP Client isn't fully parallel by default if tools lock, but we'll try asyncio.gather
        # We need to wrap tool calls
        
        async def call_tool(name, args):
            try:
                result = await session.call_tool(name, arguments=args)
                # The server returns JSON *text* inside the tool result
                return json.loads(result.content[0].text)
            except Exception as e:
                return e

        results = await asyncio.gather(
            call_tool("get_billing_info", {"account_id": self.account_id} if self.account_id else {}),
            call_tool("get_daily_energy_usage", {
                "account_id": self.account_id, 
                "start_date": start_str, 
                "end_date": end_str
            }),
            call_tool("get_outages", {}),
            return_exceptions=True
        )

        # Mapping results
        # 0 -> Billing (contains current & projection)
        # 1 -> Usage
        # 2 -> Outages (List or Dict)

        # Bill & Projection
        bill_res = results[0]
        if isinstance(bill_res, dict):
            self.data['bill_info'] = bill_res.get('current', {})
            self.data['projection'] = bill_res.get('projection', {})
        else:
             self.data['bill_info'] = {}
             self.data['projection'] = {}
             console.log(f"[red]Bill/Proj Error: {bill_res}[/]")

        # Usage
        usage_res = results[1]
        
        # Check if usage_res is a dict and has 'dailyReceivedList' (based on debug findings)
        if isinstance(usage_res, dict):
            # Based on debug_mcp.py, the key is 'dailyReadList'
            if 'dailyReadList' in usage_res:
                self.data['usage'] = usage_res['dailyReadList']
            elif 'dailyConsumptionList' in usage_res:
                self.data['usage'] = usage_res['dailyConsumptionList']
            else:
                 console.log(f"[yellow]Usage Dict keys: {list(usage_res.keys())}[/]")
                 self.data['usage'] = []
        elif isinstance(usage_res, list):
            self.data['usage'] = usage_res
        else:
            self.data['usage'] = []
            console.log(f"[red]Usage Error (Type {type(usage_res)}): {str(usage_res)[:100]}...[/]")

        # Outages
        outage_res = results[2]
        self.data['outages'] = outage_res if not isinstance(outage_res, Exception) else {}


    def make_header(self) -> Panel:
        """Creates the dashboard header"""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            "[b]SRP Energy Dashboard[/b] (MCP Client)",
            datetime.now().strftime("%A, %d %B %Y %I:%M %p")
        )
        return Panel(grid, style="white on blue")

    def make_bill_panel(self) -> Panel:
        """Creates the 'My Bill' panel matching Screenshot 1"""
        bill = self.data.get('bill_info', {})
        proj = self.data.get('projection', {})
        
        # Correct keys based on debug_billing.py
        amount = bill.get('accountBalanceAmount', 0.0) # or billedAmount
        
        # Parse Due Date "2026-02-05T00:00:00"
        due_date_raw = bill.get('dueDate', None)
        due_date = "Unknown"
        if due_date_raw:
            try:
                dt = datetime.fromisoformat(due_date_raw.replace("Z", ""))
                due_date = dt.strftime("%m/%d/%Y")
            except:
                due_date = due_date_raw

        # Projection Key
        proj_val = proj.get('amount', 0.0)
        
        amount_str = f"${amount:,.2f}" if isinstance(amount, (int, float)) else str(amount)
        proj_str = f"${proj_val:,.2f}"

        grid = Table.grid(expand=True)
        # Centered Amount
        grid.add_row(Align.center(f"[bold white on blue size=20] {amount_str} [/]", vertical="middle"))
        grid.add_row(Align.center(f"[dim]please pay[/]", vertical="middle"))
        grid.add_row("")
        
        # Details table
        details = Table.grid(expand=True)
        details.add_column(justify="left")
        details.add_column(justify="right")
        details.add_row("Due date", f"[bold]{due_date}[/]")
        details.add_row("Projected bill", proj_str)
        
        grid.add_row(Panel(details, border_style="none"))
        
        return Panel(
            grid, 
            title="[b]My bill[/b]", 
            border_style="blue",
            padding=(1, 2)
        )

    def make_usage_panel(self) -> Panel:
        """Creates the 'My Usage' panel with stacked bar chart"""
        usage_list = self.data.get('usage', [])
        
        # Sort by date
        try:
            usage_list.sort(key=lambda x: x.get('date'))
        except:
            pass
            
        # Get last 7 days (or fewer)
        recent = usage_list[-7:] if len(usage_list) > 7 else usage_list
        
        if not recent:
            return Panel("No usage data available (List empty)", title="My Usage")

        # Yesterday's data (Last valid entry)
        last_day = recent[-1]
        
        # Use onPeakKwh and offPeakKwh
        yesterday_kwh = (last_day.get('onPeakKwh', 0) or 0) + (last_day.get('offPeakKwh', 0) or 0)
        
        # Use dailyCost if available
        yesterday_cost_val = last_day.get('dailyCost', 0.0)
        yesterday_cost = f"${yesterday_cost_val:.2f}"
        
        # Projection for Top Right of Usage Panel
        proj_val = self.data.get('projection', {}).get('amount', 0.0)
        proj_str = f"${proj_val:,.0f}" # User screenshot shows rounded int
        
        # Header Stats
        stats_grid = Table.grid(expand=True)
        stats_grid.add_column(justify="center", ratio=1)
        stats_grid.add_column(justify="center", ratio=1)
        stats_grid.add_row(
            f"[bold size=20]{yesterday_cost}[/]",
            f"[bold size=20]{proj_str}[/]"
        )
        stats_grid.add_row(f"used yesterday ({yesterday_kwh:.1f} kWh)", "projected bill amount")

        # ASCII Chart
        dates = []
        on_peaks = []
        off_peaks = []
        
        for day in recent:
            d_str = day.get('date', '')
            try:
                dt = datetime.fromisoformat(d_str.replace("Z", "+00:00"))
                dates.append(dt.strftime("%a\n%m/%d"))
            except:
                dates.append("?")
            
            # Key Fix: onPeakKwh / offPeakKwh
            on_peaks.append(day.get('onPeakKwh', 0) or 0)
            off_peaks.append(day.get('offPeakKwh', 0) or 0)

        # Draw Chart
        totals = [o + f for o, f in zip(on_peaks, off_peaks)]
        max_val = max(totals) if totals else 10
        height = 8
        
        chart_rows = []
        for h in range(height, 0, -1):
            row_cells = []
            
            for o, f, t in zip(on_peaks, off_peaks, totals):
                bar_h = int((t / max_val) * height)
                
                if bar_h >= h:
                    off_h = int((f / max_val) * height)
                    if h <= off_h:
                        row_cells.append("[blue]█[/]")
                    else:
                        row_cells.append("[red]█[/]")
                else:
                     row_cells.append(" ")
            
            chart_rows.append("   " + "   ".join(row_cells))

        chart_str = "\n".join(chart_rows)
        axis_row = "   " + "   ".join([f"{d}" for d in dates])
        
        chart_panel = Panel(
            Align.center(f"{chart_str}\n[dim]{axis_row}[/]\n\n[blue]●[/] Off-peak  [red]●[/] On-peak"),
            title="7 Day Usage (kWh)",
            border_style="grey50"
        )
        
        layout = Layout()
        layout.split_column(
            Layout(stats_grid, size=4),
            Layout(chart_panel)
        )
        
        return Panel(layout, title="[b]My Usage[/b]", border_style="blue")
    
    def make_outage_panel(self) -> Panel:
        """Creates the 'Outages' panel matching Screenshot"""
        outages = self.data.get('outages', {})
        count = 0
        if isinstance(outages, list):
            count = len(outages)
        elif isinstance(outages, dict):
             count = len(outages.get('outageList', []))

        is_clear = (count == 0)
        
        status_text = "[bold green]No outages[/]" if is_clear else f"[bold red]{count} Active Outage(s)[/]"
        
        grid = Table.grid(expand=True)
        grid.add_row(Align.center(status_text, vertical="middle"))
        grid.add_row("")
        
        btns = Table.grid(padding=(0, 2))
        btns.add_column()
        btns.add_column()
        btns.add_row("[reverse] View map [/]", "[reverse yellow] Report outage [/]")
        
        grid.add_row(Align.center(btns))
        grid.add_row("")
        grid.add_row("[dim]Outage alerts are ON[/]")

        return Panel(
            grid,
            title="[b]Outages[/b]",
            border_style="green" if is_clear else "red"
        )

    # --- Statistical Helpers ---
    def calculate_trend(self, usage_list):
        """Calculates trend using simple linear regression (Least Squares)"""
        if len(usage_list) < 2:
            return 0.0, "stable"
            
        # X = index (0, 1, 2...), Y = total kwh
        n = len(usage_list)
        x = list(range(n))
        y = [(d.get('onPeakKwh', 0) + d.get('offPeakKwh', 0)) for d in usage_list]
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi*yi for xi, yi in zip(x, y))
        sum_xx = sum(xi*xi for xi in x)
        
        # Slope (m)
        try:
            m = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
        except ZeroDivisionError:
            m = 0
            
        strength = "stable"
        if m > 0.5: strength = "[red]INCREASING[/]"
        elif m < -0.5: strength = "[green]DECREASING[/]"
        
        return m, strength

    def detect_anomalies(self, usage_list):
        """Finds days where usage is > 2 Std Dev from mean"""
        if len(usage_list) < 5:
            return []
            
        totals = [(d.get('onPeakKwh', 0) + d.get('offPeakKwh', 0)) for d in usage_list]
        mean = sum(totals) / len(totals)
        
        variance = sum((x - mean) ** 2 for x in totals) / len(totals)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return []
            
        anomalies = []
        for i, val in enumerate(totals):
            z_score = (val - mean) / std_dev
            if z_score > 2.0: # 2 Sigma
                date_str = usage_list[i].get('date', 'Unknown')[:10]
                anomalies.append(f"{date_str} ({val:.1f} kWh)")
                
        return anomalies

    def make_analysis_panel(self) -> Panel:
        """Creates a 'Deep Insights' panel with AI/Stats methods"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        # 1. Rate Status
        is_weekend = (weekday >= 5)
        is_peak = False
        if not is_weekend and 15 <= hour < 18:
            is_peak = True
            
        if is_peak:
            status = "[bold red]⚠ Active Rate: ON-PEAK[/]"
            next_event = "Ends at 6:00 PM"
        else:
            status = "[bold green]✓ Active Rate: OFF-PEAK[/]"
            next_event = "On-peak starts 3:00 PM" if (not is_weekend and hour < 15) else "Off-peak continues"

        usage_list = self.data.get('usage', [])
        
        # 2. Stats Analysis
        avg_kwh = 0
        total_kwh = 0
        efficiency_score = 100
        anomalies = []
        trend_str = "Insufficient Data"
        
        if usage_list:
            # Basic Stats
            totals = [(d.get('onPeakKwh',0)+d.get('offPeakKwh',0)) for d in usage_list]
            total_kwh = sum(totals)
            avg_kwh = total_kwh / len(usage_list)
            
            # Efficiency (Percent of usage OFF peak)
            total_on_peak = sum([d.get('onPeakKwh', 0) for d in usage_list])
            on_peak_percentage = (total_on_peak / total_kwh) if total_kwh > 0 else 0
            # Score: 100 - (OnPeak% * 2) -> If 10% on peak, score 80. If 50% on peak, score 0.
            efficiency_score = max(0, int(100 - (on_peak_percentage * 200))) 
            
            # Trend
            slope, direction = self.calculate_trend(usage_list)
            trend_str = f"{direction} (Slope: {slope:.2f})"
            
            # Anomalies
            anomalies = self.detect_anomalies(usage_list)

        # 3. Layout Construction
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        
        # Col 1: Real-time
        col1 = f"[u b blue]Real-Time[/]\n\n{status}\n[dim]{next_event}[/]\n\n[bold]Projection:[/]\n${self.data.get('projection', {}).get('amount', 0):.2f}"
        
        # Col 2: Deep Stats
        anomaly_text = "\n".join([f"[red]⚠ Spike: {a}[/]" for a in anomalies[-2:]]) if anomalies else "[green]No anomalies detected[/]"
        col2 = f"[u b purple]Statistical Insights[/]\n\n[bold]Trend Analysis:[/]\n{trend_str}\n\n[bold]Anomaly Detection (Z-Score):[/]\n{anomaly_text}"
        
        # Col 3: Efficiency & Tips
        color = "green" if efficiency_score > 80 else "yellow" if efficiency_score > 50 else "red"
        col3 = f"[u b green]Efficiency[/]\n\n[bold]Grid Efficiency Score:[/]\n[{color} bold size=20]{efficiency_score}/100[/]\n\n[italic]Higher is better (more off-peak)[/]"

        grid.add_row(col1, col2, col3)
        
        return Panel(
            grid,
            title="[b]Advanced Analytics & AI Insights[/b]",
            border_style="purple"
        )

    def make_layout(self) -> Layout:
        """Define the grid layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=2),
            Layout(name="analysis", size=10)
        )
        
        layout["main"].split_row(
            Layout(name="bill", ratio=1),
            Layout(name="usage", ratio=2),
            Layout(name="outage", ratio=1)
        )
        
        layout["header"].update(self.make_header())
        layout["bill"].update(self.make_bill_panel())
        layout["usage"].update(self.make_usage_panel())
        layout["outage"].update(self.make_outage_panel())
        layout["analysis"].update(self.make_analysis_panel())
        
        return layout

    async def run(self):
        # MCP Connection Params
        # We run the server as a subprocess
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "src.srp.server"],
            env=os.environ.copy()
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                with Console().status("[bold green]Connecting to MCP Server...[/]") as status:
                    status.update("[bold green]Fetching data via MCP Tools...[/]")
                    await self.fetch_data(session)

                console.print(self.make_layout())

if __name__ == "__main__":
    # Ensure we run from root so module imports work for the server subprocess
    # But for this script, we can running it as module
    asyncio.run(SrpDashboard().run())
