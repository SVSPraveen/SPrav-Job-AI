import argparse
import json
import os
from engine.tailor import tailor_resume

def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"MODE": "free"}

def main():
    parser = argparse.ArgumentParser(description="Tailor resume to a job description, discover jobs, auto-apply, or track emails.")
    parser.add_argument("--jd", required=False, help="Path to the Job Description text file for tailoring")
    parser.add_argument("--discover", action="store_true", help="Run job discovery and scoring")
    parser.add_argument("--apply", action="store_true", help="Run Tier 1 auto-apply pipeline")
    parser.add_argument("--track", action="store_true", help="Scan Gmail for status updates and print digest")
    args = parser.parse_args()

    # Load provider mode
    config = load_config()
    mode = config.get("MODE", "free")
    
    if args.track:
        from tracking.gmail_tracker import scan_inbox, generate_digest
        print("Starting Email Tracker...")
        scan_inbox()
        generate_digest()
        return
        
    if args.apply:
        print("Tier 1 auto-apply is now managed securely by the LangGraph daemon.")
        print("Please use the React dashboard to monitor application dispatch.")
        return
        
    if args.discover:
        from discovery.db import init_db, save_job
        from discovery.scraper import run_all_scrapers
        from discovery.classifier import score_job
        
        print(f"Starting Job Discovery... (LLM Mode: {mode})")
        init_db()
        jobs = run_all_scrapers()
        print(f"Found {len(jobs)} jobs in target locations.")
        
        for job in jobs:
            print(f"Scoring: {job['title']} at {job['company']}")
            scored_job = score_job(job, mode=mode)
            save_job(scored_job)
            
        print("Discovery complete. Jobs saved to jobs.db")
        return

    if not args.jd:
        print("Error: --jd is required unless running --discover, --apply, or --track.")
        return

    if not os.path.exists(args.jd):
        print(f"Error: Job description file '{args.jd}' not found.")
        return

    with open(args.jd, "r", encoding="utf-8") as f:
        jd_text = f.read()

    print(f"Using LLM provider mode: {mode}")

    print("Tailoring resume... this may take a moment.")
    try:
        # We need to make sure the env vars are loaded if they exist
        from dotenv import load_dotenv
        load_dotenv()

        from engine.tailor import tailor_resume, load_kb

        tailored_resume = tailor_resume(jd_text)
        kb = load_kb()
        
        print("\n--- Tailored Resume (JSON) ---")
        print(json.dumps(tailored_resume, indent=2))

        print("\nGenerating DOCX...")
        output_docx = "output/tailored_resume.docx"
        generate_docx(tailored_resume, kb, output_docx)
        print(f"Saved: {output_docx}")

        print("Generating PDF...")
        output_pdf = "output/tailored_resume.pdf"
        if generate_pdf(output_docx, output_pdf):
            print(f"Saved: {output_pdf}")
        else:
            print("PDF generation failed.")
        
    except Exception as e:
        print(f"\nAn error occurred during tailoring: {e}")

if __name__ == "__main__":
    main()
