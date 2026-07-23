import sqlite3
import argparse
import sys

DB_PATH = "jobs.db"

def match_invite(email_text: str) -> dict:
    """
    Fuzzy matches the text of an interview invite against applied/matched jobs in jobs.db
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check jobs that were recently processed (we don't strictly enforce time here for simplicity)
    c.execute("SELECT id, company, title, status FROM jobs WHERE status IN ('matched', 'applied', 'interviewing')")
    rows = c.fetchall()
    conn.close()
    
    email_lower = email_text.lower()
    
    best_match = None
    highest_score = 0
    
    for job_id, company, title, status in rows:
        if not company or not title:
            continue
            
        score = 0
        c_lower = company.lower()
        t_lower = title.lower()
        
        # Exact company mention
        if c_lower in email_lower:
            score += 10
            
        # Partial title match (keywords)
        title_words = [w for w in t_lower.split() if len(w) > 3]
        for w in title_words:
            if w in email_lower:
                score += 2
                
        if score > highest_score:
            highest_score = score
            best_match = {
                "id": job_id,
                "company": company,
                "title": title,
                "status": status,
                "confidence_score": score
            }
            
    if best_match and highest_score >= 10:
        return best_match
    else:
        return {"error": "No confident match found. Highest score: " + str(highest_score)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fuzzy match an interview invite email to a job in the database.")
    parser.add_argument("--text", type=str, help="The raw text of the email")
    args = parser.parse_args()
    
    text = args.text
    if not text:
        print("Please provide email text via STDIN or --text flag.")
        text = sys.stdin.read()
        
    result = match_invite(text)
    import pprint
    pprint.pprint(result)
