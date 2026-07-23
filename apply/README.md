# 🤖 Execution & Apply Module (`/apply`)

The final mile of the SPrav pipeline. This module physically executes the application on behalf of the user.

## 🛑 Why not use APIs?
Third-party APIs for job boards are notoriously expensive, rate-limited, and often fail to support complex form logic. By using headless Playwright instances, SPrav mimics human interaction, bypassing API restrictions and ensuring 100% form completion.

## ⚙️ How it works
1. **Intake**: Receives the tailored PDF resume and job URL from the Engine.
2. **Navigation**: Playwright opens the URL and detects the ATS provider (e.g., Greenhouse, Lever, Workday).
3. **Injection**: Injects canonical user data (Name, Email, Phone, LinkedIn URL).
4. **Upload**: Attaches the tailored PDF.
5. **Submission**: Clicks submit and returns the confirmation URL to the Tracking module.

## ⚠️ Circuit Breakers
To protect your professional reputation, this module is strictly rate-limited. If it detects abnormal form behaviors (e.g., unexpected required fields), it immediately aborts the run and flags the job for manual Human Review.
