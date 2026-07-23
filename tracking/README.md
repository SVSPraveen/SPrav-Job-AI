# Tracking & Notifications (`tracking/`)

The `tracking` directory contains post-application utilities. Once the `apply` module successfully submits a resume, these scripts take over to monitor the outcome of that application.

---

## 📬 Inbox Monitoring (`gmail_tracker.py`)

This script uses the Gmail API (or IMAP) to monitor your inbox for responses from companies you applied to.
- **Interview Detection**: Scans incoming emails from known ATS domains or company domains for intent signals (e.g., "schedule a time", "next steps", "availability"). 
- **Rejection Detection**: Scans for standard rejection boilerplate (e.g., "moved forward with other candidates", "not a fit at this time").
- **Database Syncing**: When a signal is detected, it queries the local `jobs.db` for the corresponding company and updates the job's status to `interview` or `rejected`, allowing the Analytics dashboard to correctly track pipeline conversion rates.

## 🔔 System Alerts (`notifier.py`)

Handles pushing alerts to the user so you don't have to constantly monitor the dashboard.
- Dispatches notifications (via desktop toasts, Slack, or email) when:
  - An interview is secured.
  - The Auto-Apply Circuit Breaker is triggered (e.g., due to an IP block).
  - A high-value job lands in the "Human Apply" queue and requires manual intervention.
