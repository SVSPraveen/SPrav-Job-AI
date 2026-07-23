# Discovery Subsystem (`/discovery`)

The Discovery module operates at the top of the funnel, responsible for continuous job aggregation, parsing, and persistent state management across the application lifecycle.

## 🏗️ Architectural Overview

This module isolates the complexities of web scraping, API polling, and database persistence, ensuring a clean stream of structured job data is fed into the downstream `engine` subsystem.

## 🧩 Core Components

### Database Management (`db.py`)
Provides the central data access layer via SQLite, managing pipeline state and providing tamper-evident auditing.
- **Lifecycle Tracking**: Monitors jobs transitioning through states (`new`, `evaluating`, `auto_applied`, `human_review`).
- **Audit Logging**: Maintains cryptographic-style logs of all automated submissions, recording exact payloads transmitted to native Applicant Tracking Systems.
- **Circuit Breakers**: Persists daemon state metrics, allowing the system to pause execution if upstream API changes or network errors cross failure thresholds.

### Aggregation Services
- **`scraper.py`**: Implements robust, rate-limited polling mechanisms targeting specific job boards and webhook ingest endpoints.
- **`classifier.py`**: A pre-filtering middleware that executes heuristic-based pruning to immediately discard spam, heavily miscategorized postings, or low-quality data before it triggers heavy LLM inference.

## ⚙️ Execution Flow

1. Aggregation services poll configured endpoints and job boards.
2. Raw data is sanitized and committed to the local database with an initial `new` state.
3. The upstream LangGraph daemon consumes the `new` events, triggering the intelligence pipeline.
