# Knowledge Base Schema

The `me.json` file must adhere to the following schema to ensure facts are correctly verified, attributed, and maintained.

## 1. Personal Information
- `name` (string)
- `email` (string)
- `phone` (string)
- `linkedin` (string)
- `github` (string)
- `portfolio` (string)
- `summary` (string) - Base summary paragraph

## 2. Work History
List of employment entries.
- `id` (string): Unique identifier for this role (e.g., `work_acme_swe`)
- `company` (string)
- `role` (string)
- `employment_type` (string): Enum: `full-time`, `part-time`, `internship`, `contract`, `freelance`, `self-employed`
- `start_date` (string)
- `end_date` (string or "Present")
- `in_progress` (boolean): Flag for uncompleted work/roles.
- `last_reviewed` (string): Date (YYYY-MM-DD) this entry was last validated.

## 3. Projects (Manual)
List of personal or side projects added manually.
- `id` (string): Unique identifier (e.g., `proj_tailor_engine`)
- `name` (string)
- `tagline` (string)
- `tech_stack` (list of strings)
- `start_date` (string)
- `end_date` (string or "Present")
- `in_progress` (boolean)
- `last_reviewed` (string)

## 3b. GitHub Projects
List of projects fetched automatically from GitHub.
- `id` (string)
- `name` (string)
- `description` (string)
- `readme_summary` (string)
- `tech_stack` (list of strings)
- `topics` (list of strings)
- `stars` (integer)
- `last_commit_date` (string)
- `user_commit_count` (integer)
- `url` (string)
- `is_fork` (boolean)

## 3c. Portfolio Projects
List of projects fetched heuristically from portfolio website.
- `id` (string)
- `name` (string)
- `description` (string)
- `tech_stack` (list of strings)
- `url` (string)
- `confirmed` (boolean): False if pending user review, True if merged.

## 4. Certifications
Must be strictly separated from work history.
- `id` (string)
- `name` (string)
- `issuer` (string)
- `date_earned` (string)
- `expires` (string or null)
- `credential_id` (string or null)
- `url` (string or null)
- `last_reviewed` (string)

## 5. Resume Bullets
The core atoms of experience. The tailoring engine ONLY selects bullet IDs.
- `id` (string): Unique identifier (e.g., `bullet_acme_api_latency`)
- `parent_id` (string): The ID of the Work History or Project this belongs to. Critical for preventing cross-attribution.
- `text` (string): The actual text of the bullet.
- `metric_verified` (enum): Must be one of `verified` (concrete artifact), `self_reported` (confident, no artifact), or `estimated` (approximate).
- `ats_keywords` (list of strings): Keywords covered by this bullet.
- `themes` (list of strings): Conceptual categories (e.g., "Leadership", "Performance").
- `last_reviewed` (string): Date this bullet was last reviewed.

## 6. Skills
- `languages` (list of strings)
- `frameworks` (list of strings)
- `tools` (list of strings)

## 7. Pending Conflicts
Entries where intake sources disagreed (e.g., LinkedIn vs PDF resume end date).
- `field` (string): Path to conflicted field
- `values` (list of dicts): List of {"source": str, "value": str}

## 8. Needs Detail
List of bullets missing measurable metrics.
- `bullet_id` (string)
- `parent_company` (string)
- `parent_role` (string)
- `current_text` (string)
- `prompt` (string): Guiding question for the user
