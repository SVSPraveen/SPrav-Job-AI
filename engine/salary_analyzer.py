import sqlite3
import json
import os

DB_PATH = "jobs.db"
CONFIG_PATH = "config.json"

def get_salary_gaps() -> dict:
    """
    Analyzes the gap between the user's target salary (from config) 
    and the actual offered/estimated salaries from Block D in the DB.
    """
    target_salary = 0
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            # Rough parsing of target_salary if it exists (e.g., "$150,000")
            ts = config.get("target_salary", "0")
            if isinstance(ts, str):
                ts = ''.join(c for c in ts if c.isdigit())
            target_salary = int(ts) if ts else 0

    if target_salary == 0:
        return {"error": "No target_salary defined in config.json"}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT company, title, evaluation_rubric FROM jobs WHERE evaluation_rubric IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    
    gaps = []
    total_market_estimate = 0
    valid_estimates = 0
    
    for company, title, rubric_json in rows:
        try:
            rubric = json.loads(rubric_json)
            comp = rubric.get("compensation", {})
            stable_cash = comp.get("expected_stable_cash", "")
            
            # Simple heuristic to extract numbers from a string like "$130k - $150k" or "$140,000"
            numbers = [int(n) for n in ''.join(c if c.isdigit() or c == 'k' else ' ' for c in stable_cash.lower()).split() if n.isdigit() or (n.endswith('k') and n[:-1].isdigit())]
            
            # Convert 'k' to 000
            clean_numbers = []
            for n in stable_cash.lower().split():
                clean_n = ''.join(c for c in n if c.isdigit() or c == 'k')
                if clean_n.endswith('k') and clean_n[:-1].isdigit():
                    clean_numbers.append(int(clean_n[:-1]) * 1000)
                elif clean_n.isdigit():
                    clean_numbers.append(int(clean_n))
            
            if clean_numbers:
                # Take the average if it's a range
                avg_estimate = sum(clean_numbers) / len(clean_numbers)
                
                # Sanity check: if it's too small, maybe they wrote hourly or thousands without 'k'
                if avg_estimate < 1000:
                    avg_estimate *= 1000
                    
                delta = avg_estimate - target_salary
                pct_gap = round((delta / target_salary) * 100, 2)
                
                gaps.append({
                    "company": company,
                    "title": title,
                    "estimated_cash": avg_estimate,
                    "target_salary": target_salary,
                    "delta": delta,
                    "gap_percentage": pct_gap
                })
                
                total_market_estimate += avg_estimate
                valid_estimates += 1
        except Exception:
            continue
            
    market_average = round(total_market_estimate / valid_estimates, 2) if valid_estimates > 0 else 0
    macro_gap = round(((market_average - target_salary) / target_salary) * 100, 2) if target_salary > 0 else 0
    
    return {
        "target_salary": target_salary,
        "market_average": market_average,
        "macro_gap_percentage": macro_gap,
        "job_gaps": sorted(gaps, key=lambda x: x["gap_percentage"])
    }

if __name__ == "__main__":
    import pprint
    pprint.pprint(get_salary_gaps())
