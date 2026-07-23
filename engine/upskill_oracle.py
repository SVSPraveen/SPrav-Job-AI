import os
import chromadb
from engine.llm_provider import generate

CHROMA_PATH = "sprav_memory"

def get_upskill_directive() -> str:
    if not os.path.exists(CHROMA_PATH):
        return "Memory Palace is empty. Get rejected from some jobs first before I can help you."
        
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name="lessons_engineering")
    
    if collection.count() == 0:
        return "Memory Palace is empty. No lessons learned yet."
        
    results = collection.get()
    metadatas = results.get("metadatas", [])
    
    all_lessons = [meta.get("lesson", "") for meta in metadatas if "lesson" in meta]
    
    if not all_lessons:
        return "No actionable lessons found."
        
    lessons_text = "\n".join([f"- {l}" for l in all_lessons])
    
    prompt = f"""You are the Upskill Oracle, a brutal and hyper-analytical career coach.
You are reviewing the exact reasons why this candidate was rejected from their recent job applications.

REJECTION LESSONS (From Memory Palace):
{lessons_text}

Analyze the patterns across all of these rejections. What is the single biggest technical or behavioral gap causing them to lose jobs?
Output a specific, brutal, and highly actionable directive on exactly what they need to learn or build THIS WEEKEND to instantly boost their conversion rate. Do not sugarcoat it.
"""
    return generate(prompt, use_case="hard_filter")

def run_upskill_oracle():
    """
    Scans every single rejection lesson in the ChromaDB Memory Palace,
    analyzes the patterns, and outputs a specific, brutal directive on exactly
    what technology or skill the user needs to learn.
    """
    print("\n[Upskill Oracle] Waking up. Scanning Memory Palace for rejection patterns...")
    directive = get_upskill_directive()
    
    print("\n================== THE ORACLE HAS SPOKEN ==================")
    print(directive)
    print("===========================================================\n")

if __name__ == "__main__":
    run_upskill_oracle()
