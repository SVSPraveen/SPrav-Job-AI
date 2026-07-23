import sys
from engine.evaluator import KnowledgeDistiller
from engine.memory_palace import _get_collection
from engine.llm_provider import generate

def get_rejection_gaps():
    """
    Pulls recent technical rejections from the engineering wing.
    """
    collection = _get_collection("engineering")
    if collection.count() == 0:
        return "No technical rejections logged yet."
        
    results = collection.get()
    metadatas = results.get("metadatas", [])
    lessons = [meta.get("lesson", "") for meta in metadatas if "lesson" in meta]
    return "\n".join([f"- {l}" for l in lessons])

def run_project_evaluator():
    print("=========================================")
    print("      SPrav AI Project ROI Evaluator     ")
    print("=========================================")
    print("Paste the Course Syllabus, GitHub README, or Project Idea below.")
    print("Type 'END' on a new line when finished:\n")
    
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
        
    project_data = "\n".join(lines)
    
    if not project_data.strip():
        print("[Evaluator] No data provided. Aborting.")
        sys.exit(0)
        
    archetype = input("\nTarget Role Archetype (e.g. DevOps, Backend, ML): ")
    
    print("\n[Evaluator] Gathering Context...")
    distiller = KnowledgeDistiller()
    master_identity = distiller.get_master_identity()
    rejection_gaps = get_rejection_gaps()
    
    prompt = f"""You are an elite Silicon Valley Tech Recruiter and Time-Management AI.
The user is considering spending 20+ hours building the following project or taking this course.

Target Archetype: {archetype}

USER'S CURRENT SKILLS:
{master_identity}

USER'S RECENT TECHNICAL REJECTION REASONS:
{rejection_gaps}

PROJECT/COURSE SYLLABUS:
{project_data}

Evaluate if this is mathematically worth their time. 
Output exactly in this format:
1. DECISION: [YES or NO]
2. GAP BRIDGE ANALYSIS: (Exactly how this project solves their recent ATS rejections, or why it doesn't)
3. RESUME IMPACT: (Exactly how to format this on a resume to pass the ATS for {archetype})

Be brutal. If it's a generic "To-Do App" or "Titanic ML Dataset", say NO. 
If it doesn't fix their rejection gaps, say NO.
Output ONLY the formatted evaluation in Markdown."""

    print("\n[Evaluator] Engaging DeepSeek-R1 to calculate ROI...")
    
    evaluation = generate(prompt, use_case="hard_filter")
    
    print("\n=========================================")
    print("             ROI EVALUATION              ")
    print("=========================================")
    print(evaluation)
    print("=========================================\n")

if __name__ == "__main__":
    run_project_evaluator()
