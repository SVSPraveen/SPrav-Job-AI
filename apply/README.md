# Apply Module (`apply/`)

The `apply` directory contains the "Last Mile" automation layer of the SPrav pipeline. Once a job has passed the strict Fact Checker and is approved for automated submission, these modules take over.

They are responsible for packaging your tailored PDF resume, filling out the ATS (Applicant Tracking System) specific form fields, and successfully submitting the application without triggering bot detection.

---

## 🧩 Supported ATS Adapters

- **`greenhouse.py`**: Adapter for Greenhouse boards (typically `boards.greenhouse.io`). Parses the dynamic multipart form boundary requirements and handles mandatory custom questions.
- **`lever.py`**: Adapter for Lever boards (typically `jobs.lever.co`). Handles Lever's specific JSON/Form payload structure.

*(More adapters can be added by implementing the standard `submit_application(job_url, user_data, pdf_path)` interface).*

---

## 🛡️ Anti-Bot Mechanics (Jitter)

Automated tracking systems frequently deploy bot-mitigation tools (like Cloudflare or DataDome) that flag applications submitted instantly.

To circumvent this, adapters in this directory utilize **Jitter**:
- **Delays**: Simulates human reading speed by waiting random intervals (e.g. 15-45 seconds) before fetching the form, and another interval before submitting the payload.
- **Header Masking**: Spoofs standard modern browser headers (User-Agent, Accept-Language, Sec-Fetch-Dest) to blend in with legitimate web traffic.
- **Form Parsing**: Dynamically parses hidden CSRF tokens or session IDs required by the ATS rather than hardcoding static requests.

---

## 🛑 Circuit Breaker Integration

If an adapter encounters consecutive failures (e.g., an ATS changes its form structure or blocks the IP), it reports the failure back to the database. The `api.py` monitors these failures and will **pause the entire auto-apply pipeline** (engaging the Circuit Breaker) if the failure threshold is exceeded, preventing silent, repeated failures while you sleep.
