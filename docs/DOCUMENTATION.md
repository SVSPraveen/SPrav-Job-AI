# 📘 SPrav™ Job AI — Comprehensive Functional & Module Documentation

This document serves as the exhaustive reference manual for all 12 modules, subsystems, and settings within **SPrav™ Job AI (v2.4.0 Pro Edition)**.

---

## 📑 Table of Modules

1. [Command Center (Dashboard)](#1-command-center-dashboard)
2. [Action Required (Guided 1-Click Dispatch)](#2-action-required-guided-1-click-dispatch)
3. [Full Job Pipeline & Search Explorer](#3-full-job-pipeline--search-explorer)
4. [Application Scope & Targeting Matrix](#4-application-scope--targeting-matrix)
5. [Knowledge Base & Master Resume Vault](#5-knowledge-base--master-resume-vault)
6. [Recruiter Outreach Engine](#6-recruiter-outreach-engine)
7. [Gateway Tests Tracker](#7-gateway-tests-tracker)
8. [Interview Prep Center](#8-interview-prep-center)
9. [Follow-ups & Outreach Cadence](#9-follow-ups--outreach-cadence)
10. [Conversion Analytics & Funnel Telemetry](#10-conversion-analytics--funnel-telemetry)
11. [Weekly Job Digest](#11-weekly-job-digest)
12. [Settings, Multi-Engine AI & Auth](#12-settings-multi-engine-ai--auth)

---

## 1. Command Center (Dashboard)
The primary cockpit for real-time telemetry, discovery loop control, and quick action items.

### Key Components:
* **Active Autonomous Engine Status**: Visual indicator of the continuous ingestion loop (*Scanning*, *Evaluating*, *Idle*).
* **High-Level Metric Cards**:
  * **Action Required Count**: Qualified opportunities ($\text{ATS} \ge 65\% - 80\%+$) awaiting candidate 1-click review.
  * **Pipeline Active**: Current active applications in progress.
  * **Master Resume Fidelity**: Status and filename of the active PDF resume loaded into the local vault.
  * **Discovery Backlog**: Total jobs indexed and scanned in SQLite storage.
* **1-Click Ingestion Trigger**: Button to trigger an immediate, high-priority scan across all 1st-party ATS boards.
* **Recent Activity Feed**: Real-time event log showing new jobs ingested, match scores computed, and application statuses updated.

---

## 2. Action Required (Guided 1-Click Dispatch)
The core high-conversion engine of SPrav. Only jobs meeting the strict ATS quality barrier ($\text{ATS} \ge 65\%$) appear here.

### Interactive Features:
* **Match Breakdown View**: Displays matched skills (green badges) and missing skills (red badges).
* **Live Tailored Cover Note Generator**: Automatically crafts a bespoke cover letter highlighting relevant candidate projects.
* **STAR Alignment Preview**: Shows candidate achievements formatted specifically for the company's tech stack.
* **1-Click Dispatch / Apply Button**: Opens the verified direct employer application portal with pre-filled context, or dispatches directly.
* **Dismiss / Archive**: Removes jobs that do not meet candidate interest into the archive backlog.

---

## 3. Full Job Pipeline & Search Explorer
A high-performance search and filtering explorer across all 13,000+ indexed opportunities.

### Features:
* **Multi-Parameter Search**: Instant full-text search across titles, companies, locations, and required skills.
* **Status Filtering**: Filter by *All, Matched, Applied, Interviewing, Offered, Rejected, Archived*.
* **ATS Score Slider**: Real-time filtering by minimum ATS score threshold ($0\% - 100\%$).
* **Sub-Millisecond Query Response**: Powered by SQLite parameter indexing and WAL mode.

---

## 4. Application Scope & Targeting Matrix
Allows candidates to precisely calibrate the types of jobs SPrav ingests and evaluates.

### Configurable Parameters:
* **Target Job Titles**: Multi-select or custom tags (e.g. *Full Stack Developer, Backend Engineer, Machine Learning Engineer*).
* **Experience & Seniority Levels**: *Entry-Level, Mid-Level, Senior, Staff, Lead*.
* **Geographic Scope**: *Remote, Hybrid, On-site* with country/city whitelisting.
* **Salary Expectations**: Minimum desired base compensation.
* **Excluded Keywords (Negative Constraints)**: Words or technologies to strictly avoid (e.g. *PHP 5, Unpaid, Security Clearance*).

---

## 5. Knowledge Base & Master Resume Vault
The "Ground Truth" candidate profile that powers all semantic matching and cover letter tailoring.

### Capabilities:
* **Master PDF Resume Upload**: Parses `.pdf` resumes locally using PyMuPDF and regex heuristic tokenizers.
* **Semantic Skill Graph**: Groups candidate skills into 10 universal domain categories (AI & Agentic, Retrieval/Search, LLMs/Vector DBs, ML/Evaluation, Full Stack/Backend, Cloud/Security, Design/Product, Business/Operations, Marketing/Sales, and Domain Expertise):
  * AI & Agentic Systems
  * Retrieval & Search Systems
  * LLMs & Vector Databases
  * ML Evaluation & Quality
  * Full Stack & Backend Engineering
  * Cloud, DevOps & Security
* **Work History & Projects Vault**: Stores detailed quantifiable bullet points, STAR stories, GitHub project links, and portfolio URLs.
* **100% Local Storage**: Everything is written to `%LOCALAPPDATA%\SPravJobAI\knowledge_base\me.json` with zero cloud leakage.

---

## 6. Recruiter Outreach Engine
Direct access to technical hiring managers and engineering leads.

### Features:
* **Recruiter Discovery**: Finds verified recruiters and engineering leads associated with target companies.
* **Personalized Outreach Templates**: Generates bespoke LinkedIn connection notes (300 characters) and cold outreach emails referencing specific open roles.
* **Cadence Tracker**: Logs outreach dates and reminds candidates when to send follow-up messages.

---

## 7. Gateway Tests Tracker
Manages take-home technical assessments, HackerRank/LeetCode challenges, and coding tests.

### Capabilities:
* **Deadline Tracking**: Countdown timers for pending coding assessments.
* **Test Status Management**: *Received, In Progress, Submitted, Passed, Failed*.
* **Platform Notes**: Stores problem statements, repository links, and submission artifacts.

---

## 8. Interview Prep Center
A role-specific interview preparation sandbox generated for any matching job.

### Features:
* **Role-Specific Technical Questions**: Predicts the top 10 technical questions likely to be asked based on the job description.
* **System Design Scenarios**: Generates architectural challenges tailored to the company's domain.
* **STAR Story Matcher**: Matches the job requirements to the candidate's actual projects from the Knowledge Base.

---

## 9. Follow-ups & Outreach Cadence
Automated scheduler ensuring applications never go cold.

### Features:
* **Smart Follow-up Windows**: Recommends optimal follow-up timing (typically 5–7 business days post-dispatch).
* **Contextual Follow-up Drafter**: Generates polite, professional check-in emails referencing the original application date.

---

## 10. Conversion Analytics & Funnel Telemetry
Visual telemetry charts tracking candidate conversion efficiency.

### Metrics Tracked:
* **Application-to-Screening Ratio**: Percentage of dispatched applications resulting in recruiter calls.
* **ATS Score vs. Interview Correlation**: Scatter plot showing which match score ranges produce the highest interview yield.
* **Weekly Activity Trends**: Number of jobs discovered, reviewed, and dispatched over time.

---

## 11. Weekly Job Digest
A clean, curated summary of the week's highest-matching opportunities and market trends.

### Features:
* Top 10 High-Fidelity Matches of the week.
* Tech Stack Demand Trends: Which frameworks and tools are surging across your target companies.
* Summary of Dispatched vs. Responded applications.

---

## 12. Settings, Multi-Engine AI & Auth
The configuration hub for AI providers, local storage, and desktop preferences.

### Subsystems:
* **Multi-Engine AI Switcher**:
  * **Google Gemini 2.0 Flash (Recommended)**: Free cloud API key with sub-second response times.
  * **Groq (GPT-OSS 120B / Llama 3.3)**: Ultra-fast free cloud inference.
  * **Ollama (Qwen 2.5 Coder 7B)**: 100% offline local GPU execution.
* **Auto-Update Verifier**: 1-click update check that updates application binaries while preserving 100% of candidate resumes and SQLite databases.
* **Theme Switcher**: Dark Mode / Light Mode toggle.
* **Local Storage Inspector**: View database path and storage utilization.
