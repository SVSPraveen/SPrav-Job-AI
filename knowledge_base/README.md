# 🧠 Knowledge Base

This folder is the "Brain" of your personal job search. It serves as the single source of truth for the entire AI pipeline. 

> **Important:** The AI is strictly programmed to NEVER hallucinate skills or experience. It relies 100% on the data provided in this folder.

## Key Files

* **`me.json`**: The core data structure. Contains your structured Work Experience, Projects, Education, Certifications, and a master list of `resume_bullets`. The LLM reads from this file to tailor your resume for specific jobs.
* **`custom_instructions`**: Found inside `me.json`, these allow you to provide strict prompting rules to the AI (e.g., "Emphasize my experience with Qdrant when applying to RAG engineering roles").

## Editing your Knowledge Base
While you can edit `me.json` manually in a text editor, it is highly recommended to use the **Knowledge Base Editor** built directly into the SPrav Frontend UI. The UI ensures that JSON structures remain valid and that parent/child IDs (linking bullets to specific projects) do not break.
