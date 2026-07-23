# Analytics & Tracking Subsystem (`/tracking`)

The Tracking module provides post-application telemetry and observability, closing the feedback loop between the automated dispatch system and external email communications.

## 🏗️ Architectural Overview

This subsystem acts as a read-only integration layer with the user's primary communication channels (e.g., Gmail). It uses deterministic matching to correlate incoming email replies with jobs tracked in the local SQLite database.

## 🧩 Core Components

- **`gmail_tracker.py`**: Interacts with the Gmail API via robust, read-only OAuth scopes or App Passwords. 
- **`signal_detector.py`**: Analyzes the contents of incoming emails using NLP techniques to classify the sentiment and intent (e.g., "Interview Request", "Rejection", "Assessment Test").
- **`pipeline_updater.py`**: Executes atomic database updates based on detected signals, ensuring the analytics dashboard always reflects the real-time conversion rates of the application funnel.

## 🔒 Security Posture

The tracking module only reads emails explicitly matching recruiter domains or ATS system addresses associated with active applications. All processing is done locally, and no email data is ever transmitted to a third party or LLM cloud provider.
