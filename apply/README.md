# 🤖 Execution & Apply Module (`/apply`)

The final mile of the SPrav pipeline. This module physically executes the application on behalf of the user.

## 🛑 Why not use APIs?
Third-party APIs for job boards are notoriously expensive, rate-limited, and often fail to support complex form logic. By using headless Playwright instances, SPrav mimics human interaction, bypassing API restrictions and ensuring reliable form completion.

## ⚙️ How it works
1. **Intake**: Receives the tailored PDF resume and job URL from the Engine.
2. **Navigation**: Playwright opens the URL and detects the ATS provider (e.g., Greenhouse, Lever, Workday).
3. **Injection**: Injects canonical user data (Name, Email, Phone, LinkedIn URL).
4. **Upload**: Attaches the tailored PDF.
5. **Submission**: Clicks submit and returns the confirmation URL to the Tracking module.

## ⚠️ Circuit Breakers & Volume Limits
To protect your professional reputation and prevent ATS ban-hammering, this module is strictly rate-limited using a multi-tiered defense:

1. **Company Cap:** Maximum 5 applications per individual company per day.
2. **Portal Cap:** Maximum 25 applications per job board (e.g., Greenhouse, Lever) per day.
3. **Global Cap:** A hard ceiling of 150 total applications across all pipelines per day.

If the engine detects abnormal form behaviors or consecutive Playwright failures, it immediately trips the `AUTO_APPLY_CIRCUIT_BREAKER_N` flag, aborts the run, and routes the job for manual Human Review.
