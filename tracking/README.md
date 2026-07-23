# 📊 Analytics & Tracking (`/tracking`)

The Tracking module handles the downstream lifecycle of a job application once it has been successfully dispatched by the Execution module.

## 📈 Telemetry Dashboard
The frontend React dashboard heavily relies on this module to populate the user UI. It tracks:
* **Total Applications Sent**
* **Application Success Rate** (Did Playwright successfully submit the form?)
* **Conversion Metrics** (Responses vs Rejections)

## 🗃️ Local Storage
All telemetry is stored in `jobs.db`. No analytics are streamed back to a centralized server. The Tracking module provides read-only API endpoints for the dashboard to render D3.js and Recharts graphs.
