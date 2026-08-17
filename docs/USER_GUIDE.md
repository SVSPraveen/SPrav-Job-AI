# 📖 SPrav™ Job AI — Comprehensive User Manual & Practical Guide

Welcome to the complete user manual for **SPrav™ Job AI**. This guide provides step-by-step instructions for installation, configuration, AI key setup, resume optimization, and mastering 1-click application dispatch.

---

## 📑 Table of Contents

1. [System Requirements & Compatibility](#1-system-requirements--compatibility)
2. [Step-by-Step Installation (Zero-Install Portable)](#2-step-by-step-installation-zero-install-portable)
3. [Setting Up Free AI Cloud API Keys (0% RAM/GPU)](#3-setting-up-free-ai-cloud-api-keys-0-ramgpu)
4. [Setting Up Local Offline AI with Ollama (Optional)](#4-setting-up-local-offline-ai-with-ollama-optional)
5. [Formatting Your Master PDF Resume for Maximum ATS Fidelity](#5-formatting-your-master-pdf-resume-for-maximum-ats-fidelity)
6. [Calibrating Your Application Scope Matrix](#6-calibrating-your-application-scope-matrix)
7. [The Daily 15-Minute Workflow: Review & 1-Click Dispatch](#7-the-daily-15-minute-workflow-review--1-click-dispatch)
8. [Mastering Recruiter Cold Outreach](#8-mastering-recruiter-cold-outreach)
9. [Backup, Data Migration & Updating SPrav](#9-backup-data-migration--updating-sprav)
10. [Troubleshooting & Diagnostics](#10-troubleshooting--diagnostics)

---

## 1. System Requirements & Compatibility

| Component | Minimum Specification | Recommended Specification |
|---|---|---|
| **Operating System** | Windows 10 (64-bit, Build 19041+) | Windows 11 (64-bit) |
| **Processor** | Intel Core i3 / AMD Ryzen 3 | Intel Core i5 / AMD Ryzen 5 or higher |
| **System Memory (RAM)** | 4 GB | 8 GB or higher |
| **Disk Storage** | 1.5 GB available space | 2.5 GB SSD |
| **Internet Connection** | Broadband (for ATS job feeds) | Broadband |
| **AI Inference** | Free Google Gemini / Groq API Key | Free Gemini 2.0 Flash or Local GPU (Ollama) |

---

## 2. Step-by-Step Installation (Zero-Install Portable)

SPrav is distributed as a **self-contained portable bundle**. You do not need to install Python, Node.js, or any background dependencies.

1. **Download the Official Archive**:
   Download `SPrav_Job_AI_Pro_v2.4_Portable.zip` from the official [Google Drive Releases Folder](https://drive.google.com/drive/folders/1JOm-Rth1HoB5xZqDva61JG9-aonj4jae?usp=sharing).
2. **Extract the Archive**:
   * Right-click the `.zip` file $\rightarrow$ select **Extract All...**.
   * Choose any target directory (e.g. `C:\SPrav Job AI` or your Desktop).
3. **Launch the Application**:
   * Open the extracted folder: `SPrav Job AI/`.
   * Double-click **`SPravJobAI.exe`**.
4. **Desktop Shortcut Creation**:
   * On first launch, a dialog will ask: *"Would you like to create a Desktop Shortcut?"*.
   * Click **Yes** to place `SPrav Job AI.lnk` with the official icon on your desktop.

---

## 3. Setting Up Free AI Cloud API Keys (0% RAM/GPU)

We highly recommend using free cloud keys. They execute in milliseconds and use **0% of your computer's RAM and battery**.

### Option A: Google Gemini 2.0 Flash (Recommended — 100% Free)
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your Google account.
3. Click **Create API Key** and copy the generated key string (`AIzaSy...`).
4. In SPrav, open **Settings & Auth** $\rightarrow$ select **Google Gemini** $\rightarrow$ paste the key and click **Save Settings**.

### Option B: Groq (Ultra-Fast Free Cloud Llama 3.3)
1. Visit [Groq Console](https://console.groq.com/keys).
2. Sign in and click **Create API Key**.
3. Copy the key (`gsk_...`), open SPrav **Settings & Auth** $\rightarrow$ select **Groq** $\rightarrow$ paste and save.

---

## 4. Setting Up Local Offline AI with Ollama (Optional)

If you require 100% offline, air-gapped execution and have a dedicated GPU (NVIDIA RTX 3070 / 4060+ with 8GB+ VRAM):

1. Download and install [Ollama for Windows](https://ollama.com/download/windows).
2. Open PowerShell and pull the recommended coding model:
   ```powershell
   ollama run qwen2.5-coder:7b
   ```
3. In SPrav, open **Settings & Auth** $\rightarrow$ select **Ollama (Local)** $\rightarrow$ ensure the host is `http://localhost:11434` and save.

---

## 5. Formatting Your Master PDF Resume for Maximum ATS Fidelity

SPrav parses your resume to construct your local semantic profile. For best results:
* **File Format**: Standard single-column `.pdf`. Avoid multi-column magazine layouts.
* **Quantifiable Bullets**: Use the Google XYZ formula: *"Accomplished [X] as measured by [Y], by doing [Z]"*.
* **Dedicated Skills Section**: Include a clean `Skills:` block listing programming languages, frameworks, cloud services, and tools clearly.

---

## 6. Calibrating Your Application Scope Matrix

1. Click **Application Scope** in the left sidebar.
2. Select your target roles (e.g. *Full Stack Engineer, Backend Developer, AI Engineer*).
3. Toggle **Remote Only** if you do not want on-site listings.
4. Add **Negative Keywords** (e.g. *Security Clearance, US Citizen Only, Unpaid*) to automatically filter out unsuitable roles.

---

## 7. The Daily 15-Minute Workflow: Review & 1-Click Dispatch

Instead of spending 4 hours applying to jobs every day:
1. Open SPrav once per day.
2. Go to **Action Required (Guided Dispatch)**.
3. You will see 5–15 pre-filtered opportunities that matched your resume with $\text{ATS} \ge 65\% - 80\%+$.
4. For each job:
   * Review the **Matched vs. Missing Skills**.
   * Review the auto-generated **Tailored Cover Note**.
   * Click **1-Click Dispatch / Apply** to submit your application.
5. Done! In under 15 minutes, you have submitted high-quality, targeted applications without burning out.

---

## 8. Mastering Recruiter Cold Outreach

1. Open the **Recruiter Outreach** tab for any matched company.
2. SPrav identifies engineering managers and technical talent partners.
3. Click **Generate LinkedIn Connection Note** (formatted within the 300-character limit).
4. Send the personalized note to the recruiter to bypass the general applicant queue!

---

## 9. Backup, Data Migration & Updating SPrav

* **Data Preservation Guarantee**: All your resume files, settings, and job application history are stored independently in:
  ```text
  %LOCALAPPDATA%\SPravJobAI\
  ```
* **Updating SPrav**: When a new version is released, simply download the new zip file and extract it. Your existing database and master resume will automatically connect with zero data loss.

---

## 10. Troubleshooting & Diagnostics

### App won't launch or black screen:
* Check that your antivirus / Windows SmartScreen did not block the extracted files. Click **More Info $\rightarrow$ Run Anyway**.
* Run the included diagnostic tool:
  ```powershell
  python public_repo\examples\diagnose_system.py
  ```

### Need Support?
Email creator **SVS Praveen** directly at **`svspraveens@gmail.com`**.
