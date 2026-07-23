# Discovery Module (`discovery/`)

The `discovery` directory is responsible for the top of the funnel: finding jobs across the internet and persisting the application pipeline state locally. 

This module feeds raw Job Descriptions (JDs) into the `engine` for evaluation.

---

## 📂 Contents

### 1. Database & State Management (`db.py`)
This file manages the local SQLite database (`jobs.db`) which acts as the central nervous system for the pipeline. It stores:
- **`jobs` Table**: Tracks every discovered job through its lifecycle (`active`, `rejected`, `in_scope`, `auto_applied`, `human_review`, etc.).
- **`auto_apply_audit` Table**: A tamper-evident log of every automated submission. Records the exact payload sent to the ATS, ensuring transparency and accountability.
- **`daemon_state` Table**: A key-value store used to persist system state across restarts, such as the Circuit Breaker failure count (which pauses auto-apply if too many consecutive failures occur).

### 2. Job Scrapers
- **`scraper.py`**: The generic job board scraper logic. Designed to periodically poll target keywords and locations to pull down raw JD text and URLs.
- **`classifier.py`**: A fast, pre-filtering classifier that drops obvious spam or heavily miscategorized jobs before they are added to the database.

---

## ⚙️ How it works
1. Scrapers poll job boards or ingest webhooks.
2. New jobs are sanitized and inserted into the SQLite database with a status of `new`.
3. The `engine/daemon.py` constantly monitors the database, picking up `new` jobs and initiating Phase 0 (Verification).
