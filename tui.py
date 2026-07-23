import sqlite3
import time
import os
import sys

try:
    from rich.live import Live
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.console import Console
    from rich.text import Text
except ImportError:
    print("CRITICAL: Python 'rich' library is missing.")
    print("Please run: pip install rich")
    sys.exit(1)

DB_PATH = "jobs.db"
console = Console()

def fetch_metrics():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
        rows = c.fetchall()
        conn.close()
        
        metrics = {"applied": 0, "rejected": 0, "stale": 0, "new": 0, "manual_review": 0}
        for status, count in rows:
            if status in metrics:
                metrics[status] = count
            else:
                metrics[status] = count
        return metrics
    except:
        return {}

def fetch_latest_jobs():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Query for jobs if updated_at exists, else fallback
        try:
            c.execute("SELECT company, title, status, updated_at, fit_score FROM jobs ORDER BY updated_at DESC LIMIT 15")
        except:
            c.execute("SELECT company, title, status, 'Unknown', 0.0 FROM jobs ORDER BY id DESC LIMIT 15")
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def fetch_latest_summary():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT date, summary FROM daily_summaries ORDER BY date DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        
        if row:
            return f"**Daily Briefing ({row[0]})**\n\n{row[1]}"
        return "No Compaction Summary Generated Yet."
    except:
        return "Waiting for 3:00 AM Auto-Save Hook..."

def generate_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="job_feed", ratio=2),
        Layout(name="daily_summary", ratio=1)
    )
    return layout

def update_ui(layout: Layout):
    metrics = fetch_metrics()
    
    # Header
    pending_approval = metrics.get('pending_cover_letter', 0)
    header_text = Text(
        f"🚀 SPrav AI Pipeline | APPLIED: {metrics.get('applied', 0)} | REJECTED: {metrics.get('rejected', 0)} | NEW: {metrics.get('new', 0)} | ⏳ AWAITING APPROVAL: {pending_approval}",
        style="bold white on blue", justify="center"
    )
    layout["header"].update(Panel(header_text))
    
    # Job Feed Table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Company", style="cyan")
    table.add_column("Title")
    table.add_column("Status", justify="right")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Last Updated", style="dim")
    
    for row in fetch_latest_jobs():
        company, title, status, updated_at, fit_score = row
        
        # Color code status
        if status == 'applied':
            status_text = f"[bold green]{status.upper()}[/bold green]"
        elif status in ['rejected', 'stale', 'repost']:
            status_text = f"[bold red]{status.upper()}[/bold red]"
        else:
            status_text = f"[bold yellow]{status.upper()}[/bold yellow]"
            
        score_str = f"{fit_score:.1f}" if fit_score else "-"
        table.add_row(str(company)[:20], str(title)[:30], status_text, score_str, str(updated_at)[:19])
        
    layout["job_feed"].update(Panel(table, title="[bold]Live Job Feed (Top 15)[/bold]"))
    
    # Daily Summary
    summary_md = Markdown(fetch_latest_summary())
    layout["daily_summary"].update(Panel(summary_md, title="[bold]Nightly Executive Summary[/bold]", border_style="green"))
    
    # Footer
    layout["footer"].update(Panel(Text("Status: SYSTEM ONLINE & MONITORING (Press Ctrl+C to Exit)", style="bold green blinking"), border_style="green"))
    return layout

def run_tui():
    layout = generate_layout()
    with Live(layout, refresh_per_second=1, screen=True):
        while True:
            try:
                update_ui(layout)
                time.sleep(1)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    run_tui()
