# ❓ SPrav™ Job AI — Frequently Asked Questions (FAQ)

---

## 🔒 Privacy, Security & Data Ownership

### Q1: Where is my master resume, contact info, and job history stored?
**100% on your local machine.** All data resides inside `%LOCALAPPDATA%\SPravJobAI\` (or `~/.spravjobai/` on UNIX systems). Your resume and credentials are never uploaded to our servers or any 3rd-party database.

### Q2: Does SPrav track or sell my personal job search activity?
**No.** The application is an independent freeware desktop client. The only telemetry sent is an anonymous application start heartbeat (anonymous user ID and timestamp) to monitor active installations. Zero personal details, resumes, or company names are ever transmitted.

### Q3: Why is SPrav free? Is there a hidden catch?
**No catch.** SPrav was engineered by **SVS Praveen** as an independent personal freeware initiative to level the playing field for developers and job seekers navigating a broken hiring market.

---

## 🤖 AI Execution & Hardware Requirements

### Q4: Do I need a high-end GPU or gaming laptop?
**No.** You can run SPrav on any standard Windows 10/11 laptop (even with integrated graphics) by using **free Google Gemini 2.0 Flash or Groq API keys**. Cloud inference completes in <1 second with 0% CPU or GPU strain.

### Q5: How much do the AI API keys cost?
**₹0 / $0.** Both Google AI Studio and Groq offer generous free tiers that easily support hundreds of job evaluations and cover note generations daily without requiring a credit card.

### Q6: Can I run SPrav completely offline without any internet connection?
**Yes.** If you install Ollama locally with `qwen2.5-coder:7b`, SPrav will perform all skill parsing, ATS matching, and cover note drafting 100% offline on your local GPU.

---

## ⚡ Job Discovery, Matching & Dispatch

### Q7: How does SPrav find 28,700+ jobs?
SPrav connects directly to 1st-party public ATS endpoints (**Greenhouse, Lever, Ashby, Workday, SmartRecruiters**) and verified tech company career portals, ingesting live openings continuously without relying on delayed third-party scrapers.

### Q8: What makes SPrav different from automated auto-apply spam bots?
Auto-apply bots blindly spam 1,000s of generic applications, causing immediate ATS rejections, email blacklisting, and candidate confusion during interview calls. SPrav does 99% of the computational research in the background, but surfaces roles into a **1-Click Guided Dispatch Queue** where **you give explicit 1-click permission before anything is submitted**.

### Q9: What happens when an ATS score is below 65%?
SPrav quarantines the position into your background backlog so your daily **Action Required** queue remains high-signal, authentic, and actionable.

---

## 🔄 Updates, Migration & Support

### Q10: How do I update to newer versions without losing my data?
Simply download the new portable zip from Google Drive and extract it. Because your database and resume are stored in `%LOCALAPPDATA%\SPravJobAI`, **100% of your data and application history are automatically preserved**.

### Q11: Can I use SPrav on multiple computers?
Yes. You can copy your `%LOCALAPPDATA%\SPravJobAI` folder (containing `jobs.db` and `me.json`) to your other PC to sync your exact candidate profile and application history.

### Q12: Is there a macOS or Linux version coming?
Yes. Linux and macOS standalone packages are on the product roadmap.

### Q13: How do I report a bug or request a feature?
* Email creator **SVS Praveen** directly at **`svspraveens@gmail.com`**.
* Or click the **💬 Feedback / Bug** button directly in the application navbar.
