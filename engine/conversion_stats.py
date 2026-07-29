import sqlite3
import os
import json
from engine.utils import get_data_dir

DB_PATH = os.path.join(get_data_dir(), "jobs.db")

def get_conversion_stats() -> dict:
    """
    Computes exact, structured conversion stats per-keyword and per-portal.
    Outcomes can be: 'ghosted', 'rejected', 'interview', 'offer', 'pending'.
    Only applies to jobs where status == 'applied'.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT source, matched_skills, outcome FROM jobs WHERE status = 'applied'")
    rows = cursor.fetchall()
    conn.close()

    portals = {}
    skills = {}
    total_applied = 0
    total_interviews = 0
    total_offers = 0

    for r in rows:
        source = r["source"] or "Unknown"
        outcome = r["outcome"] or "pending"
        matched = r["matched_skills"] or ""
        
        total_applied += 1
        if outcome == "interview": total_interviews += 1
        if outcome == "offer": total_offers += 1

        # Portal tracking
        if source not in portals:
            portals[source] = {"applied": 0, "interview": 0, "offer": 0, "ghosted": 0, "rejected": 0, "pending": 0}
        portals[source]["applied"] += 1
        if outcome in portals[source]:
            portals[source][outcome] += 1
            
        # Skill keyword tracking
        if matched:
            skill_list = [s.strip() for s in matched.split(",") if s.strip()]
            for s in skill_list:
                # Remove the " | Supported: ..." part if present
                if "|" in s: s = s.split("|")[0].strip()
                
                if not s: continue
                
                if s not in skills:
                    skills[s] = {"applied": 0, "interview": 0, "offer": 0, "ghosted": 0, "rejected": 0, "pending": 0}
                skills[s]["applied"] += 1
                if outcome in skills[s]:
                    skills[s][outcome] += 1

    # Calculate conversion rates
    for s in portals.values():
        s["conversion_rate"] = round((s["interview"] + s["offer"]) / s["applied"] * 100, 1) if s["applied"] > 0 else 0.0

    for s in skills.values():
        s["conversion_rate"] = round((s["interview"] + s["offer"]) / s["applied"] * 100, 1) if s["applied"] > 0 else 0.0

    return {
        "summary": {
            "total_applied": total_applied,
            "total_interviews": total_interviews,
            "total_offers": total_offers,
            "overall_conversion_rate": round((total_interviews + total_offers) / total_applied * 100, 1) if total_applied > 0 else 0.0
        },
        "by_portal": portals,
        "by_skill": dict(sorted(skills.items(), key=lambda item: item[1]["conversion_rate"], reverse=True)[:20]) # Top 20 skills
    }
