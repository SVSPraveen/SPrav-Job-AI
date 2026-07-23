# Knowledge Base

This directory acts as the single source of truth for the user's professional identity and application constraints.

- **`me.json`**: The canonical schema of the user's personal info, work history, projects, and skills. Generated and merged by the Intake pipeline, and heavily utilized by the Tailoring and Fact-Checking engines.
- **`scope.json`**: The Application Scope configuration, dictating hard logic gates for roles, locations, job types, and work modes that the pipeline is permitted to apply to.
- **`master_identity.txt`**: A distilled, dense LLM-generated narrative constructed from `me.json` to be injected into prompts for efficient context sharing.
- **`proof_points.md`**: Textual evidence of portfolio projects and open-source contributions.
- **`schema.md`**: Developer documentation describing the exact data shapes expected within `me.json`.
