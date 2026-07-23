import sqlite3

DB_PATH = "jobs.db"

def get_company_friction_rate(company: str) -> dict:
    """
    Calculates the friction rate for a given company.
    Friction is defined as jobs where status is 'rejected' or ghosted vs total applied.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status FROM jobs WHERE LOWER(company) = ?", (company.lower(),))
    rows = c.fetchall()
    conn.close()

    total = len(rows)
    if total == 0:
        return {"total": 0, "rejected": 0, "friction_rate": 0.0}

    rejected = sum(1 for row in rows if row[0] in ('rejected', 'ghosted'))
    rate = round(rejected / total, 2)
    
    return {
        "company": company,
        "total": total,
        "rejected": rejected,
        "friction_rate": rate
    }

def get_all_friction_rates() -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT company, status FROM jobs")
    rows = c.fetchall()
    conn.close()
    
    company_stats = {}
    for company, status in rows:
        if not company:
            continue
        c_lower = company.lower()
        if c_lower not in company_stats:
            company_stats[c_lower] = {"company": company, "total": 0, "rejected": 0}
            
        company_stats[c_lower]["total"] += 1
        if status in ('rejected', 'ghosted'):
            company_stats[c_lower]["rejected"] += 1
            
    results = []
    for stats in company_stats.values():
        stats["friction_rate"] = round(stats["rejected"] / stats["total"], 2)
        results.append(stats)
        
    return sorted(results, key=lambda x: x["friction_rate"], reverse=True)
