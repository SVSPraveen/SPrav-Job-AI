# 🖥️ SPrav Frontend

This directory contains the sleek, Dark/Light-mode themed React application that serves as your command center for SPrav Job AI.

## Architecture
- **Framework**: React 18 + Vite
- **Styling**: Vanilla CSS (No heavy CSS frameworks to ensure maximum performance and maintainability)
- **Deployment**: During production builds, Vite compiles this into static assets in `dist/`, which are then natively served by the Python FastAPI backend. This eliminates the need for Node.js in the production runtime, significantly lowering memory usage.

## Key Modules & Pages
* **Dashboard / Human Review Queue**: Your main inbox. Review tailored resumes, fit scores, and 1-click apply to jobs.
* **Prep Center (`PrepCenter.jsx`)**: View dynamically generated STAR behavioral stories tailored to specific roles to prep for upcoming interviews.
* **Recruiter Outreach (`RecruiterOutreach.jsx`)**: Manage automatically sourced hiring manager contacts and review auto-drafted networking emails.
* **Watchlist Manager (`WatchlistManager.jsx`)**: Use Typeahead autocomplete to prioritize specific dream companies.
* **Application Scope (`ApplicationScope.jsx`)**: Configure strict inclusion/exclusion rules (e.g., location, visa, remote vs onsite) to prevent the daemon from wasting API tokens on bad jobs.
* **Gateway Tracker (`GatewayTracker.jsx`)**: Track external ATS portals like Workday or SuccessFactors.
* **Copilot & Tour (`Copilot.jsx`, `GuideTour.jsx`)**: Built-in AI assistant and interactive onboarding UI.

## Development
To run the frontend locally with hot-reloading:
```bash
npm install
npm run dev
```
