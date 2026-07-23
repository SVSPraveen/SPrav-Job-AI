# Dashboard Subsystem (`/frontend`)

The Frontend module delivers a comprehensive, real-time React dashboard for monitoring, controlling, and interacting with the SPrav autonomous application pipeline.

## 🏗️ Architectural Overview

Built with React 18 and Vite, the dashboard interfaces with the primary Python FastAPI backend via RESTful endpoints. It provides observability into the LangGraph state machine, allowing users to approve, reject, or manually intervene in the application flow.

## 🧩 Core Features

- **Human-in-the-Loop (HITL) Queue**: An intervention interface for jobs that fall below the auto-apply confidence threshold, requiring manual approval of the tailored resume and cover letter.
- **Knowledge Base Editor**: A structured JSON UI that allows the user to easily manage their canonical career data (`me.json`), bypassing manual file editing.
- **Funnel Analytics**: Visualizes the conversion pipeline from discovery to application to interview, driven by data aggregated from the SQLite database.
- **Secure Authentication**: Implements a localized JWT verification layer to ensure that only the authorized user can trigger ATS dispatch commands.

## 🛠️ Development

```bash
# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
