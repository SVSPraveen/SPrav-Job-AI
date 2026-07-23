import sqlite3
import os
from datetime import datetime, timedelta
from engine.db_utils import db_mutex
from engine.llm_provider import generate
from engine.strategy_generator import generate_followup_email

DB_PATH = "jobs.db"

def run_compaction():
    print("\n[Compaction Engine] Waking up. Initializing Daily Transcript Compaction...")
    
    followup_jobs = []  # Initialize before the with block to prevent NameError
    
    with db_mutex:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Ensure daily_summaries table exists
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                date TEXT PRIMARY KEY,
                summary TEXT
            )
        ''')
        
        # Ensure jobs has updated_at column
        try:
            c.execute("ALTER TABLE jobs ADD COLUMN updated_at TEXT")
            conn.commit()
        except:
            pass
            
        # Get yesterday's date (or today's, depending on when it runs)
        # Since it runs at 3AM, we want to summarize the previous 24 hours.
        target_date = (datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%d')
        
        # Check if already compacted
        c.execute("SELECT summary FROM daily_summaries WHERE date = ?", (target_date,))
        if c.fetchone():
            print(f"[Compaction Engine] Transcript for {target_date} already compacted. Going back to sleep.")
            conn.close()
            return
            
        # Pull all job activity from the target date
        c.execute("SELECT company, title, status, missing_skills, scam_flags FROM jobs WHERE updated_at LIKE ?", (f"{target_date}%",))
        rows = c.fetchall()
        
        # --- FOLLOW-UP CADENCE CHECK ---
        print("\n[Compaction Engine] Checking Follow-Up Cadences (7-day and 14-day silence)...")
        # Find jobs applied to exactly 7 or 14 days ago
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        fourteen_days_ago = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        
        c.execute("SELECT id, company, title, updated_at FROM jobs WHERE status = 'applied' AND (updated_at LIKE ? OR updated_at LIKE ?)", 
                  (f"{seven_days_ago}%", f"{fourteen_days_ago}%"))
        followup_jobs = c.fetchall()
        
        for f_job in followup_jobs:
            job_id, company, title, updated_at = f_job
            days_silent = 7 if updated_at.startswith(seven_days_ago) else 14
            print(f"[Follow-Up Scanner] Drafting {days_silent}-day check-in for {title} at {company}...")
            # We call this outside the db_mutex block ideally, but we have the lock right now.
            # generate_followup_email handles its own db_mutex so we must be careful!
            # Let's just collect the IDs and call it after releasing this mutex block.
            
    # --- END DB MUTEX BLOCK 1 ---
    
    # Process follow-ups (outside main DB lock to prevent deadlocks since generate_followup_email has its own lock)
    for f_job in followup_jobs:
        job_id, company, title, updated_at = f_job
        days_silent = 7 if updated_at.startswith(seven_days_ago) else 14
        generate_followup_email(job_id, company, title, days_silent)
        
    print(f"\n[Compaction Engine] Extracted {len(rows)} raw activity logs. Engaging LLM compression...")
    
    # Build raw context
    raw_log = ""
    for r in rows:
        company, title, status, missing_skills, scam_flags = r
        raw_log += f"[{status.upper()}] {title} at {company} | Missing: {missing_skills} | Flags: {scam_flags}\n"
            
    # Release DB lock before calling LLM
    prompt = f"""You are the SPrav AI Analytics Engine.
Compress this massive raw SQLite log of yesterday's job hunting activity into a dense, 500-token Executive Summary.
Focus on:
1. Total metrics (Applied, Rejected, Ghosts Detected).
2. The most common Missing Skills (what do we need to learn?).
3. Any notable companies we applied to.

RAW SQLITE LOG ({target_date}):
{raw_log}

Output ONLY the formatted Executive Summary in clean Markdown."""

    summary = generate(prompt, use_case="hard_filter")
    
    with db_mutex:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO daily_summaries (date, summary) VALUES (?, ?)", (target_date, summary))
        conn.commit()
        conn.close()
        
    print(f"\n[Compaction Engine] Auto-Save Hook Complete. Summary for {target_date} archived safely.")

if __name__ == "__main__":
    run_compaction()
