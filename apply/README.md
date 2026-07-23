# Application Subsystem (`/apply`)

The Application module is responsible for the execution phase of the pipeline, providing headless browser automation to interface directly with Applicant Tracking Systems (ATS).

## 🏗️ Architectural Overview

Rather than relying on third-party integration APIs that often strip formatting or fail to deliver critical metadata, this module utilizes Playwright to automate native browser interactions. It ensures that applications are submitted exactly as a human would enter them on platforms like Greenhouse and Lever.

## 🧩 Core Components

- **`ats_automation.py`**: The primary Playwright controller. Handles browser instantiation, context management, and DOM interaction.
- **`form_filler.py`**: Intelligent form-mapping logic that pairs the user's canonical `me.json` data with complex, deeply nested web forms.
- **`captcha_handler.py`**: Implements strategies for managing bot-mitigation techniques gracefully, pausing execution for human-in-the-loop intervention when necessary.

## 🛡️ Security & Privacy

This module operates entirely locally. Auth tokens, session cookies, and personal data are never transmitted outside of the direct connection to the target ATS. The headless browser instances are configured for maximum privacy, disabling telemetry and external trackers.
