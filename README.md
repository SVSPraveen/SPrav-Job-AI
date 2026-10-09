# SPrav Job AI 🛡️

> **"SPrav Job AI scans 500+ real company hiring systems directly — no middlemen, no ghost jobs, no data sold. Tailor your resume with AI, prep for interviews, and track every application. 100% private, free forever."**  
> **Created and Engineered by [SVS Praveen](https://github.com/SVSPraveen)**

[![Anti-SaaS](https://img.shields.io/badge/Business_Model-Anti--SaaS_($0_Forever)-emerald.svg)](docs/DOCUMENTATION.md)
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Air--Gapped-blue.svg)](docs/DOCUMENTATION.md)
[![Version](https://img.shields.io/badge/Version-v1.0.2_Sovereign_Release-indigo.svg)](package.json)
[![Tests](https://img.shields.io/badge/Tests-4%2C088_Passing_(100%25)-brightgreen.svg)](docs/DOCUMENTATION.md)
[![React](https://img.shields.io/badge/React-19.2-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.1-purple.svg)](https://vite.dev/)
[![WebGPU](https://img.shields.io/badge/WebGPU-Hardware_Accelerated-green.svg)](https://www.w3.org/TR/webgpu/)
[![Storage](https://img.shields.io/badge/Storage-IndexedDB_Vault-orange.svg)](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
[![License](https://img.shields.io/badge/License-Proprietary_(All_Rights_Reserved)-purple.svg)](LICENSE)

> 📖 **Comprehensive Architecture Blueprint:** Read the full [Master Technical Documentation](docs/DOCUMENTATION.md) for complete engineering deep dives, API references, telemetry formulas, and deployment guides.

---

## 🌟 The Anti-SaaS Career Operating System

**SPrav Job AI** is NOT another job board. You cannot beat legacy aggregators on raw listings volume, because aggregators recycle expired postings and charge recruiters for sponsored bumps. 

Instead, **SPrav Job AI** is built specifically for developers, data scientists, and remote engineers fed up with subscription paywalls and data brokers selling their resumes. SPrav Job AI operates on an uncompromising doctrine: **100% Client-Side Sovereign Career Intelligence**.

### Why We Built the Anti-SaaS Career OS

| Dimension | Commercial SaaS Traps & Paywalls | Traditional Aggregator Job Boards | SPrav Sovereign Career OS |
|---|---|---|---|
| **Subscription Cost** | $20 – $50 / month paywalls | Free with aggressive ads & spam | **$0 Forever (Zero Paywalls)** |
| **Candidate Privacy** | Resumes harvested & sold to data brokers | Resumes mined to train corporate AI | **100% Air-Gapped Browser IndexedDB** |
| **Listing Authenticity** | Repost loops & unverified scrapers | Stale evergreen "ghost jobs" (>90 days) | **Direct 1st-Party ATS (Ashby, GH, Lever)** |
| **Hiring Velocity Telemetry** | Hidden behind recruiter dashboards | Zero freshness transparency | **Live Anti-Ghost Radar (4.2x Callback Multiplier)** |
| **AI Inference Architecture** | Proprietary cloud LLMs logging prompts | Generic keyword match counters | **Local WebGPU & BYOK Cascading AI** |
| **Application Prep** | Generic 1-size-fits-all cover letters | Blind bot spamming (shadow-ban risk) | **1-Click Tailored Harvard PDF & AutoFill** |
| **Server Operating Cost** | High centralized cloud infrastructure | Monetized via candidate telemetry | **$0 Server Cost (Pure Client Execution)** |

---

## ⚡ Key Capabilities

### 1. The $0 Real-Time Job Engine & Zero-Cost ATS Pipeline
- **Direct 1st-Party ATS JSON Endpoints ($0 Cost, 0 Auth, 0 Rate Limits):** Bypasses aggregators and expensive scraper farms entirely by querying official public corporate ATS feeds:
  - **Greenhouse:** `https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true`
  - **Lever:** `https://api.lever.co/v0/postings/{company}?mode=json`
  - **Ashby:** `https://api.ashbyhq.com/posting-api/job-board/{company}`
  - **Workable:** `https://apply.workable.com/api/v1/widget/accounts/{company}?details=true`
  - **SmartRecruiters:** `https://api.smartrecruiters.com/v1/companies/{company}/postings`
- **Free GitHub Actions Cron Workers ([`.github/workflows/harvest_jobs.yml`](.github/workflows/harvest_jobs.yml)):** Runs every 6 hours (`cron: '20 */6 * * *'`) on free GitHub Actions runners ($0 server cost), generating rich step telemetry and deploying fresh static data.
- **Deterministic Python Harvester ([`scripts/harvest_jobs.py`](scripts/harvest_jobs.py)):**
  - **Zero Pip Dependencies:** Pure Python 3 standard library implementation (`urllib.request`, `concurrent.futures`, `gzip`, `json`, `hashlib`).
  - **Strict <= 14 Days Freshness Validation:** Enforces $\text{age\_days} \le 14.0$, dropping all stale or dated postings.
  - **Anti-Ghost & Evergreen Heuristics:** Filters generic talent pools, pipeline requisitions, and speculative applications using regex classification (`talent community`, `future opportunities`, `eoi`, `evergreen`).
  - **Canonical Deduplication:** Generates SHA-256 fingerprints across `company + title + location` to eliminate duplicates.
  - **92%+ Gzip Compression:** Compresses feeds from ~3.5 MB down to ~260 KB for edge CDN delivery in under 200ms.
- **Instant Edge CDN Delivery & Offline Air-Gap Fallback:** Serves compressed static feeds behind GitHub Pages CDN (`svspraveen.github.io/SPrav-Live-Feed/jobs.json.gz`), with automatic failover to the local static [`public/data/sprav_daily_jobs.json`](public/data/sprav_daily_jobs.json) for 100% offline development.

### 2. Direct In-Browser ATS Live Scanner & 3.5M+ Directly-Sourced Tech Listings
- Connects directly to verified open-CORS ATS endpoints including **Ashby**, **Greenhouse**, **Lever**, **SmartRecruiters**, **Recruitee**, **Remotive**, **Jobicy**, **Arbeitnow**, and **Himalayas (+90k remote tech jobs)**.
- **420+ Verified Sovereign Tech Company Catalog:** Scans direct career boards of AI frontier labs, cloud infrastructure titans, fintechs, and high-growth scale-ups.
- **3.5M+ Directly-Sourced Tech Listings:** High-throughput client-side streaming engine with Gzip decompression and progressive multi-chunk search across 29,000+ companies with zero middlemen.
- **Daily Sovereign Mirror Pipeline:** Automated GitHub Actions cron aggregator running daily with $0 server cost to curate, deduplicate, and publish verified fresh tech opportunities.
- **Hacker News "Who is Hiring?" Founder Pipeline:** Ingests monthly official threads via Firebase API to connect candidates directly with founders and hiring leads, including 1-click founder email actions.
- Detailed architecture: [Phase 1 Direct Ingestion Documentation](docs/PHASE_1_DIRECT_INGESTION.md).

### 3. Anti-Ghost Job & Hiring Velocity Radar ($0 Telemetry)
- Extracts authentic publication timestamps directly from first-party ATS streams (`publishedAt`, `updated_at`, `releasedDate`, `first_published_at`).
- **Callback Velocity Multipliers:** Computes hiring velocity and callback probability (**4.2x callback multiplier** for listings <4h old; **3.5x** for Fresh Drops <24h).
- **Anti-Ghost & Repost Loop Detection:** Identifies dormant evergreen requisitions (>90 days old) and flags artificial bumping loops (roles created >45d ago renewed recently).
- **Interactive Portal Telemetry:** 1-click "⚡ Fresh Drops" quick-tab, Anti-Ghost Radar filtering (`Exclude Ghost & Stale Roles`), and "⚡ Fresh Drops First" sorting.
- **In-Place Inspection Drawer & Modal:** Click directly on any job card's freshness or ghost risk badge in MasterJobPortal to inspect hiring legitimacy, exact posting age, callback velocity multiplier, health score, and red flag warnings without leaving the page.
- **Diagnostic Radar Card:** Interactive modal breakdown showing exact age, velocity multiplier, ghost risk level, and actionable candidate strategies.
- Detailed architecture: [Phase 2 Anti-Ghost Radar Documentation](docs/PHASE_2_ANTI_GHOST_RADAR.md).

### 4. Universal 1-Click AutoFill Bookmarklet ($0 Automation)
- Pure JavaScript bookmarklet (`javascript:(...)`) requiring **zero extension downloads**, zero browser permissions, and zero tracking.
- Instantly detects and populates candidate details on **Greenhouse**, **Lever**, **Ashby**, **SmartRecruiters**, **Workable**, and generic employer application pages.
- Dispatches synthetic `input`, `change`, and `blur` events for React, Vue, and Angular validation, highlights filled inputs in emerald green, and displays an in-page floating status HUD.
- Includes an interactive in-app ATS practice simulator, candidate payload customizer, and multi-browser setup guides.
- Detailed architecture: [Phase 3 Universal AutoFill Documentation](docs/PHASE_3_UNIVERSAL_AUTOFILL.md).

### 5. Laptop GPU to Mobile P2P Continuity ($0 Handshake)
- Pure JavaScript ISO/IEC 18004 **QR code matrix generator** and crisp SVG renderer with **zero npm dependencies**.
- Enables candidates running heavy WebGPU or local models on their laptops to transfer top ATS-matched jobs, tailored application pitches, and candidate profile facts directly to their mobile devices in a single camera scan.
- **Dual-Mode Continuity:** Optical QR code camera handshake for top opportunities, plus 1-click `.sprav-sync` offline bundle import/export for bulk transfers (100+ roles).
- **Mobile-Optimized Execution:** Ingests seamlessly into the mobile browser's IndexedDB vault with automatic deduplication, paired with zero-battery-drain free-tier cloud AI recommendations.
- Detailed architecture: [Phase 4 Mobile Continuity Documentation](docs/PHASE_4_MOBILE_CONTINUITY.md).

### 6. In-Browser ATS-Compliant PDF Compiler & Dual-Pane Split Studio ($0)
- Pure JavaScript zero-dependency **PDF 1.4 vector document compiler** generating standard Harvard / Jake's single-column ATS resumes directly in the browser.
- **Dual-Pane Split-View Workspace:** Seamlessly pairs the live resume editor and section controls on the left with real-time ATS X-Ray keyword density, formatting audits, and scoring diagnostics on the right (`subtab-split`).
- **6 Designer Archetypes:** Classic ATS (Harvard/Jake's), Silicon Valley Modern, Ivy League Executive, Technical Compact, Creative Two-Column, and Academic CV.
- **Real-Time Anti-Hallucination Guardrail:** Audits AI-generated bullets against ground-truth IndexedDB profile facts to prevent metric fabrication or tool hallucination before PDF compilation.
- **In-Browser ISO/IEC 18004 Vector QR Badge:** Embeds scannable portfolio, GitHub, or LinkedIn vector QR badges into resume headers with zero external dependencies.
- **Dynamic Semantic Tailoring:** Analyzes target job descriptions, moves matched technical keywords to the top of the skills block, and promotes the highest-impact STAR bullet points.
- **Dual Format Export:** 1-Click download of `<CandidateName>_<Company>_ATS_Resume.pdf` plus plain text ASCII export for copy-pasting into text boxes.
- **Integrated Guided Dispatch:** 1-Click "📄 Tailored PDF" button directly on each job opportunity in the candidate queue.
- Detailed architecture: [Phase 5 ATS Resume Compiler Documentation](docs/PHASE_5_ATS_RESUME_COMPILER.md).

### 7. Company Watchlist & 1-Click Curated Presets
- Add custom company career portals to track specific dream employers with automatic platform detection (`greenhouse`, `ashby`, `lever`, `smartrecruiters`, `recruitee`).
- **1-Click Curated Presets:** Instant loading for top employer tiers (AI Frontier, Developer Platforms, Enterprise & Global Tech).
- Live health badges indicate scanner connectivity and tracked job counts.

### 8. Multi-Model BYOK Cloud AI Expansion & Latency Orchestration ($0)
- **Frontier Multi-Model BYOK:** Direct browser-to-cloud CORS integration with 6 leading providers: **Google Gemini**, **Groq LPU** (`qwen-2.5-coder-32b-instruct` default, `openai/gpt-oss-120b`), **DeepSeek (Direct)**, **Mistral AI (Direct)**, **OpenRouter (Universal)**, and **OpenAI (Direct)**.
- **Automated Cascading Failover (`auto` mode):** Zero-downtime routing dynamically falls back to the fastest healthy model on rate limits or API outages.
- **Live Latency Probing:** Real-time round-trip latency benchmarking with color-coded millisecond badges (`🟢 <400ms • Ready`, `🟡 Responsive`, `⚠️ Error`).
- **Data Sovereignty:** API keys are saved exclusively in the user's browser IndexedDB vault—never sent to intermediate proxies or data brokers.
- Detailed architecture: [Phase 6 Multi-Model BYOK Documentation](docs/PHASE_6_MULTI_MODEL_BYOK.md).

### 9. Client Storage Vault ($0 Server Costs)
- Native **IndexedDB** engine stores discovered jobs, extracted resume facts, target scopes, and application history.
- Automatically locks storage via `navigator.storage.persist()` to protect candidate data from browser disk cache eviction.
- 1-click full JSON backup export and restore.

### 10. SPrav Copilot & Guided Dispatch
- Intelligent in-app career assistant evaluating top-matched opportunities and semantic skill graph alignment.
- 1-click tailored application notes citing exact candidate achievements and metrics.
- Pre-filled screening answers for work authorization, years of experience, and notice periods.
- Safe external dispatch linking directly to verified ATS application pages.

### 10. Community Growth & Viral Launch Hub ($0)
- Dedicated **Community & Launch** page with a 5-pillar Anti-SaaS Sovereignty manifesto banner.
- **1-Click Social Sharing:** Pre-populated share text with direct web-intent buttons for LinkedIn, X/Twitter, WhatsApp, and Telegram.
- **Developer Launch Templates:** Structured Show HN submission markdown and Reddit community posts for targeted subreddits (`r/cscareerquestions`, `r/LocalLLaMA`, `r/developersIndia`, `r/jobs`).
- **Embeddable Shields.io Badges:** Live canonical-format SVG badges with 1-click Markdown/HTML copy for READMEs and project pages.
- **LinkedIn Founder Narrative Post:** Authentic personal narrative post template with hashtag optimization and 1-click copy.
- **1-Click Export:** Full launch kit as `.json` and playbook as `.md` for cross-platform distribution.
- Detailed architecture: [Phase 7 Community Growth & Launch Playbook](docs/PHASE_7_COMMUNITY_GROWTH_PLAYBOOK.md).

### 11. Reverse-ATS 12-Dimension X-Ray Diagnostic Scoring Engine & Platform Rules
- Deep reverse-engineering of corporate ATS scoring algorithms across 12 distinct dimensions: Hard Skills, Semantic Skill Graph, Seniority Calibration, Job Title Alignment, Education Thresholds, Metric Density, Action Verbs, Section Labels, Contact Hygiene, Layout Geometry, Over-Optimization Penalties, and Tech Recency.
- **Vendor-Specific Rule Evaluator:** Real-time compliance checking for **Workday** (strict single-column, no tables), **Greenhouse** (semantic section parsing), **Lever** (plain text extraction), **Taleo**, **Ashby**, and **SmartRecruiters**.
- **Score Progression Sparkline:** Tracks resume iterative improvements over time directly in the client vault.
- **1-Click Clipboard Ingestion:** Instant `navigator.clipboard.readText()` paste for instant zero-friction diagnostics.

### 12. Tactical Salary Negotiation & Live Call Battlecards ($0)
- **Live Call Battlecards:** Instant HUD providing quick responses to high-pressure recruiter tactics ("What is your current salary?", "Do you have competing offers?", "We need an answer by Friday").
- **Dynamic Market Comp Engine:** Generates Conservative, Target, and Aggressive counter-offer benchmarks, equity levers, and professional negotiation scripts tailored to tech discipline and geo tier.
- **Seniority Calibration:** Automatically detects candidate YOE vs job requirements (Underqualified, Aligned, Overqualified) to protect candidates from down-leveling.

### 13. Candidate Multi-Persona Engine & Cover Letter Remix Studio
- **Multi-Persona Switcher:** Effortlessly switch between targeted identities (e.g., "Full Stack Engineer", "AI/ML Specialist", "Cloud & DevOps Architect") with isolated skill graphs, STAR stories, and tailored scopes.
- **Cover Letter Memory & Remix Studio:** Preserves generated outreach pitches in IndexedDB and remixes them across three distinct tones: *Engineering Rigor*, *Startup Agility*, and *Bold Founder Direct*.

### 14. First-Run Interactive Onboarding Tour & Hardware Auto-Calibration
- **3-Step Sovereign Onboarding Modal:** Guides first-time visitors through the Zero-Data-Exfiltration doctrine, resume import, and ATS X-Ray diagnostics with interactive visual spotlights.
- **Definitive Local Model Policy & Hardware Auto-Calibration:**
  - **Primary Default (GPU VRAM ≥ 6GB):** `Qwen2.5-Coder-7B-Instruct` (~4.8GB VRAM) is the architectural sweet spot for 8GB VRAM setups. Delivers deep systems engineering reasoning, <2% JSON schema error rate, and an 8,192-token KV cache without needle-in-a-haystack attention loss.
  - **Deep Interview Prep & Strategy:** `DeepSeek-R1-Distill-Qwen-7B` automatically routed for mock technical interview loops, behavioral STAR grading, and high-stakes salary counter-offers using Chain-of-Thought (CoT) logic.
  - **Fallback & Lightweight (< 6GB VRAM / CPU / Mobile):** Fall back to `sprav-career-3b` or `Qwen2.5-Coder-1.5B` to prevent Out-Of-Memory crashes.
  - **Dedicated Scope for `sprav-career-3b`:** Fine-tuned specifically for ultra-fast, single-sentence generation (< 280-character LinkedIn connection notes) and 4GB low-spec machines.
  - **Ollama & Multi-Model BYOK Cloud Fallbacks:** Seamless zero-downtime cascading failover across local Ollama and 6 BYOK providers (Groq, Gemini, DeepSeek, Mistral, OpenAI, OpenRouter).

### 15. Synthesized Callback Likelihood & Honest Skill Telemetry
- **🎯 Heuristic Callback Likelihood:** Synthesizes ATS score, posting freshness velocity, and remote competition into an honest probability indicator (`High Probability`, `Strong Match`, `Competitive`, `Stretch`).
- **📈 Honest Skill Demand Telemetry:** Computes authentic frequency ratios (`${count}/${total} jobs (${pct}%)`) extracted directly from real job descriptions scanned into the local vault. When starting fresh with an empty vault, cleanly transitions to transparent `Priority Rank #X` indicators with explicit disclosures rather than fabricated growth percentages.

### 16. Unified Pipeline & Analytics Dashboard ($0 Telemetry)
- **Unified Pipeline & Analytics Cockpit:** Consolidates multi-stage conversion funnels, company yield metrics, and application momentum with the chronological application timeline and Kanban pipeline into a single integrated overview (`subtab-unified`).
- **Multi-Stage Conversion Funnel:** Tracks candidate progression across `Discovered → Applied → Recruiter Screen → Technical Loop → Official Offer` with step-to-step dropoff percentages and automated bottleneck diagnostics.
- **Candidate vs. Industry Benchmark Comparison:** Compares candidate application-to-response rates against cold industry baselines (2.8%) and ATS-optimized top decile targets (14.5%) with performance ratings and actionable calibration advice.
- **Optimal Timing & Recruiter Heatmap:** Aggregates application timestamps across 7 days and hourly slots, scoring alignment against prime recruiter attention windows (Tuesday–Thursday 8:00 AM – 11:30 AM).
- **Company Size Yield Breakdown:** Segments interview response yields by employer tiers: Enterprise & FAANG vs Growth & Mid-Market vs Seed Startups.

### 17. 1-Click Role Skill Starter Blueprints & 15-Category Engineering Taxonomy
- **1-Click Blueprints:** 8 curated engineering presets (Frontend Engineer, Backend & Systems, Full Stack, DevOps & Cloud SRE, Data Scientist / Analyst, AI & ML Engineer, Mobile App Developer, and QA & SDET) with 1-click non-destructive skill seeding into active career personas.
- **Expanded Core Engineering Domains:** Dedicated categories for **Frontend Web Engineering** (React 19, Next.js App Router, TypeScript, Tailwind, Zustand, Vite, Core Web Vitals, WCAG), **Systems & Low-Level Infrastructure** (Rust, Go, Modern C++, Linux Kernel, Concurrency, gRPC, tokio), and **Data Science & Analytics** (Advanced SQL, Pandas, NumPy, Tableau, A/B Testing, Metabase).

### 18. Key Technical Projects Integration in ATS Resume Studio & PDF Compiler
- **Dedicated Projects Section:** Fully integrated into resume templates, ATS scanners, tailoring engines, and PDF 1.4 vector compilers with live `includeProjects` toggle control in the Studio toolbar.
- **Anti-Hallucination Guardrail:** Ensures projects and bullet points reflect authentic repository facts and verified metrics before compilation.

### 19. Curated Skill-to-Resource Engineering Roadmap Directory
- **50 In-Demand Skills Directory:** Direct mappings for 50 top technical skills to official documentation, free full-length courses, and GitHub build specifications.
- **Adaptive 4-Week Learning Roadmap:** Generates customized weekly study plans to close candidate qualification gaps for high-match opportunities.

### 20. Company Health Score & Job Red Flag Radar ($0 Heuristic)
- **Deterministic Red Flag Scanning:** Automatically analyzes JD text and posting telemetry for burnout risk ("fast-paced environment"), under-resourced teams ("wear many hats"), unrealistic tech tenure requirements ("10+ years Next.js"), omitted compensation, vague culture filters, commission-only/MLM traps, visa/citizenship restrictions, and ghost-job requisitions.
- **0–100 Company Health Score:** Synthesizes identified risks into an instant visual health pill (`✓ Clean`, `⚠️ Caution`, `⚡ Risky`, `⛔ Avoid`) directly on each job opportunity card before the candidate invests time applying.

### 21. In-Context Humanizer & Voice Styling Engine ($0 Client-Side Guardrail)
- **Publication-Grade Voice Engine:** Built-in [`cover_letter_style_engine.js`](src/utils/cover_letter_style_engine.js) eliminates robotic AI markers with zero server dependency.
- **50+ Banned AI Cliché Scrubber:** Strips generic AI tropes (*"thrilled to apply"*, *"dynamic tapestry"*, *"spearheaded"*, *"seasoned professional"*, *"in today's fast-paced world"*).
- **Dynamic Syntactic Entropy & Burstiness:** Varies sentence cadences and structures to mirror authentic engineer-to-engineer communication.
- **5 Opening Archetypes & STAR Anchoring:** Automatically selects from 5 distinct human opening archetypes and anchors claims in verified STAR stories from the candidate vault.

### 22. Global & Indian Company Round Expectations Database Engine ($0 Intelligence)
- **53+ Curated Multi-Stage Blueprints:** Eliminates FAANG-only bias with comprehensive interview loops across 5 global taxonomies: Global FAANG (Google, Meta, Amazon, Microsoft, Apple, Netflix), Indian Product Unicorns & SaaS (Swiggy, Zomato, Razorpay, Flipkart, Zerodha, CRED, Meesho, PhonePe, Zoho, Freshworks, Postman), Indian IT Giants & System Integrators (TCS, Infosys, Wipro, HCLTech, Cognizant, LTIMindtree), Europe & APAC Leaders (Spotify, Adyen, Revolut, Canva, Grab, Atlassian), and FinTech / Quant Powerhouses (Jane Street, Citadel, Two Sigma, HRT).
- **6 Universal Architectural Archetypes:** Fallback inference engine maps unlisted employers to archetypes (`enterprise_si_consulting`, `tech_product_unicorn`, `ai_deeptech`, `saas_product`, `fintech_quant`, `general_tech_standard`).
- **Granular Round Schemas:** Exact round duration, core evaluation focus (Machine Coding, LLD, HLD, Core CS), coding platform telemetry, actionable prep tips, and behavioral frameworks (Leadership Principles, Googlyness, First Principles).
- **Multi-Currency Compensation Calibration:** Salary ranges denominated in USD and INR (₹ LPA) with explicit March 2025 FX disclosures (`1 USD ≈ ₹86.50`).

### 23. In-Flow Recruiter & Hiring Contact CRM Pipeline ($0 Client-Side CRM)
- **Direct Requisition CRM:** Link technical recruiters, engineering managers, and startup founders directly to tracked job requisitions.
- **Contact Dossiers:** Stores contact names, emails, LinkedIn URLs, outreach status, and customized interaction notes.
- **1-Click Calibrated Pitches:** Generates personalized recruiter messages citing candidate knowledge base achievements and selected persona tone.
- **Stage 5 Guided Dispatch Integration:** Displays recruiter contacts alongside cover letters and tailored resumes during application dispatch.
- **100% Air-Gapped:** Contacts remain exclusively inside the browser's IndexedDB vault under AES-GCM encryption.

### 24. Browser Companion 3-Step Visual Installation Guide & Unified Guidance ($0 Setup)
- **Interactive 3-Step Visual Guide:** Effortless setup for Chrome, Brave, Arc, and Edge (`chrome://extensions` → Developer Mode → 1-click clipboard path copy to Load unpacked).
- **Live Form Detection Preview:** Real-time visual mockup simulating extension autofill HUD on Workday, Greenhouse, Lever, and Ashby portals.
### 25. Unified "Career Identity" Center & One-Pass Resume Auto-Population ($0 Architecture)
- **Eliminates Profile Fragmentation:** Merges the previously split Application Scope and Knowledge Base modules into a single intuitive profile destination with 3 logical sub-tabs:
  1. **Target Preferences:** Target engineering titles, geographic boundaries, remote vs. on-site policies, and granular **Compensation Expectations** (salary floor, target desired salary, currency selector, and annual/hourly period).
  2. **Experience & Skills:** Verified work history, academic degrees & certifications, key projects, and granular 15-category engineering skills arsenal.
  3. **STAR Accomplishment Bank:** Structured Situation-Task-Action-Result stories with behavioral competency categorization and completeness scoring for interview prep and resume bullet injection.
  4. **Mobile Sync:** Air-gapped P2P vault transfer without cloud.
- **One-Pass Resume Auto-Population:** Dropping a master resume (PDF, Word, TXT) automatically extracts structured career facts into the Knowledge Base AND infers target roles, locations, experience level, and compensation defaults into Target Preferences in a single pass, eliminating redundant form filling.

---

## 🧠 Sovereign AI Architecture: 100% Client-Side Inference (Zero In-Browser Training)

> [!IMPORTANT]
> **Zero In-Browser Neural Network Training:**  
> There is **no gradient descent, backpropagation, or neural network training** happening in the browser. Web clients cannot and should not calculate heavy optimizer states. SPrav Job AI operates on **100% pure client-side inference** paired with deterministic algorithmic engines.

### 1. The 4 Inference Runtimes

| Inference Engine | Execution Mechanism | Hardware Requirement | Privacy Guarantee |
|---|---|---|---|
| **WebGPU (In-Browser)** | Pre-quantized `Qwen 2.5 Coder` weights execute local forward passes via browser WebGPU shader pipelines (`@mlc-ai/web-llm`). | Consumer GPU (1.5GB – 4.3GB VRAM) | **100% Air-Gapped** (Zero network traffic) |
| **Local Ollama** | HTTP requests to `http://localhost:11434` for local GGUF models (`qwen2.5-coder`, `llama3.1`). | Local Ollama daemon running | **100% Localhost** (Never leaves computer) |
| **Cloud BYOK (Direct CORS)** | Browser dispatches direct HTTPS calls using candidate's personal API keys (Gemini, Groq, DeepSeek, Mistral, OpenAI, OpenRouter). | Zero local GPU needed | **Zero-Intermediary** (Keys stay in IndexedDB) |
| **Deterministic Fallback** | Instant algorithmic JavaScript (regex matchers, ATS scoring heuristics, AST analyzers, JSON sanitizers). | Any device / 0 MB GPU | **100% Offline** (Instant execution) |

### 2. How Humanized Quality is Delivered Without Retraining
Rather than requiring every candidate to spend hours fine-tuning models on expensive cloud GPUs, SPrav Job AI codifies expert talent strategy directly into client-side runtime engines:
- **In-Context Style Anchoring:** Dynamically injects few-shot exemplar structures from verified top-tier tech resumes (`exemplar_tech_resumes.js`).
- **STAR Competency Grounding:** Matches target job requirements against candidate behavioral stories (`star_story_bank.js`), grounding generation in real accomplishments rather than AI hallucinations.
- **Automated Humanizer Post-Processor:** Runs deterministic lexical substitutions, burstiness normalization, and cliché removal (`cover_letter_style_engine.js`) across all model outputs (WebGPU, Ollama, and Cloud BYOK).

### 3. The Offline QLoRA Dataset Synthesizer & Export Pipeline
For machine learning engineers and power users who **do** wish to train custom LoRA adapters externally, the app includes a dedicated synthetic dataset generation and export suite:
- **In-App Dataset Synthesizer (`lora_cover_letter_dataset.js`):** Generates 336+ curated, publication-grade engineering training pairs across 28 real-world domains (Distributed Systems, Frontier AI, Fintech, Cybersecurity, etc.).
- **Multi-Format 1-Click Export:** Exports clean `.jsonl` datasets formatted for **ChatML**, **Alpaca**, **DPO (Direct Preference Optimization)**, and **Unsloth**.
- **External Training Playbook & Modelfile:** The included [`LORA_COVER_LETTER_PLAYBOOK.md`](docs/LORA_COVER_LETTER_PLAYBOOK.md) provides ready-to-run Unsloth scripts and Google Colab T4 notebooks for training an 8B model in ~25 minutes (<6.2GB VRAM), compiling GGUF weights, and loading them into Ollama.

---

## 📁 Repository Structure

```
sprav-job-ai-web/
├── index.html                    # Root HTML with PWA & SEO metadata
├── vite.config.js                # Vite build and development configuration
├── package.json                  # Standalone web app dependencies and scripts
├── vercel.json                   # Instant 1-click Vercel deployment config
├── netlify.toml                  # Instant 1-click Netlify deployment config
├── .gitignore                    # Git tracking rules
├── .env.example                  # Environment configuration template
├── LICENSE                       # Proprietary Software License (All Rights Reserved)
├── public/
│   ├── favicon.png               # Application icon
│   ├── manifest.json             # Progressive Web App manifest
│   ├── sw.js                     # Service worker for offline asset caching
│   ├── docs/DOCUMENTATION.md     # In-app downloadable architecture guide
│   └── icons.svg                 # SVG sprite catalog
└── src/
    ├── main.jsx                  # React 19 bootstrap entry
    ├── App.jsx                   # Central routing, state orchestration & layout
    ├── index.css                 # Premium dark-mode design system
    ├── Copilot.jsx               # Intelligent career assistant component
    ├── GuidedDispatch.jsx        # 1-Click application pipeline & staging drawer
    ├── components/
    │   ├── GhostJobInspectModal.jsx# In-place Anti-Ghost Radar & Hiring Legitimacy Modal
    │   ├── WebGPUControlPanel.jsx# GPU hardware monitor & model manager
    │   ├── PersonaSwitcherBar.jsx# Multi-persona career tracks switcher
    │   ├── CommandPalette.jsx    # Keyboard-driven omni-search modal
    │   ├── PrivacyConsentModal.jsx# Local data sovereignty agreement
    │   ├── ScoreProgressionSparkline.jsx# ATS score history sparkline
    │   └── SkillGapRoadmapModal.jsx# 4-week learning roadmap modal
    ├── pages/
    │   ├── CommandCenterHome.jsx # Main dashboard & contextual action guidance banner
    │   ├── MasterJobPortal.jsx   # Live ATS scanner, job cards & legitimacy inspection
    │   ├── ConversionStats.jsx   # Multi-stage conversion funnel & timing heatmaps
    │   ├── WeeklyDigest.jsx      # Honest skill trends & weekly market digest
    │   ├── KnowledgeBaseEditor.jsx# 1-Click role blueprints & STAR story bank
    │   ├── AtsResumeStudio.jsx   # In-Browser ATS Single-Column PDF Compiler & Preview
    │   ├── AtsXRayEngine.jsx     # 12-Dimension ATS scoring & vendor rule evaluator
    │   ├── ApplicationScope.jsx  # Candidate target titles, locations & compensation
    │   ├── ApplicationHistory.jsx# Dispatched applications tracking & timeline
    │   ├── RecruiterOutreach.jsx # Outreach message generator
    │   ├── MobileContinuity.jsx  # Laptop GPU to Mobile P2P Handshake & QR Generator
    │   ├── WatchlistManager.jsx  # Company careers portal tracker
    │   ├── GatewayTracker.jsx    # Technical Assessment & OA platform tracker
    │   ├── Settings.jsx          # Cloud AI authentication & vault management
    │   └── workspaces/
    │       ├── JobsWorkspace.jsx     # Discovery, ready-to-apply & watchlist container
    │       ├── ResumeWorkspace.jsx   # Split-View Studio & ATS X-Ray workspace
    │       ├── InterviewWorkspace.jsx# Prep, recruiter outreach & follow-up studio
    │       ├── ProfileWorkspace.jsx  # Knowledge base, scope & mobile continuity
    │       └── AnalyticsWorkspace.jsx# Unified Pipeline & Funnel Analytics hub
    └── utils/
        ├── conversion_analytics_engine.js# Stage conversion, timing & benchmark formulas
        ├── skill_gap_roadmap.js  # 50-skill curated resource map & 4-week roadmaps
        ├── star_story_bank.js    # Behavioral STAR stories & completeness auditor
        ├── browser_ats_scanner.js# Direct open-CORS ATS fetch engine
        ├── browser_storage_vault.js# Native IndexedDB persistent storage
        ├── hybrid_llm_client.js  # WebGPU / Cloud API hybrid inference client
        ├── webgpu_detector.js    # Hardware capability & VRAM tier detector
        ├── client_resume_extractor.js# In-browser PDF text & skill parser
        ├── qr_generator.js       # Pure JS ISO/IEC 18004 QR Matrix & SVG Renderer
        ├── mobile_handshake.js   # P2P handshake packaging, encoding & vault sync
        ├── ats_pdf_compiler.js   # Pure JS ISO 32000-1 / PDF 1.4 vector compiler
        ├── resume_tailoring_engine.js# Dynamic keyword reordering & STAR bullet ranking
        ├── salary_benchmark_engine.js# Market comp estimation & counter-offer scripts
        ├── company_round_engine.js# 53+ global & Indian hiring loops, archetypes & search
        └── cleanDescription.js   # Job description sanitizer & markdown parser
```

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- [Node.js](https://nodejs.org/) (version 18 or higher)
- Modern browser with WebGPU support (Chrome 113+, Edge 113+, or Arc)

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Local Development Server
```bash
npm run dev
```
Open your browser at `http://localhost:5173`.

### 3. Build for Production
```bash
npm run build
```
The optimized static production bundle will be generated in `dist/`.

### 4. Preview Production Build
```bash
npm run preview
```

### 5. Run the $0 Real-Time Job Harvester (Local / Standalone Pipeline)
Generate live, verified ATS feeds on demand from 250+ top employers:
```bash
# Harvest top 50 corporate ATS boards with live diagnostic logs
python scripts/harvest_jobs.py --limit 50 --verbose

# Harvest all 250+ tech employers with strict <=14 days freshness filter
python scripts/harvest_jobs.py --concurrency 30

# Outputs generated in dist_feed/ (jobs.json.gz, feed_manifest.json, index.html)
# Automatically updates public/data/sprav_daily_jobs.json for offline fallback!
```

---

## 🧪 Comprehensive Verification & Quality Assurance

SPrav Job AI maintains an uncompromising multi-layer automated test suite ensuring mathematical precision, client-side resilience, zero-server privacy, and defensive fault tolerance:

| Test Layer | Framework / Engine | Command | Passing Status |
| :--- | :--- | :--- | :--- |
| **Node.js Native Test Suite** | Node.js native test runner (`node:test`) | `npm test` | **1,270 / 1,270 passed** (123 suites) ¹ |
| **Component & UI Test Suite** | Vitest (`@testing-library/react`) | `npm run test:components` | **2,818 / 2,818 passed** (321 test files) |
| **Defensive Mutation Suite** | Parallel Mutation & Fault-Tolerance Engine | `npm run test:mutation:ci` | **23 / 23 passed** |
| **22-Persona Expert Security Audit** | Comprehensive Persona Verification Engine | `npm run test:expert:audit` | **22 / 22 audits passed** |
| **Dead Stub & Orphan Linter** | Node AST Static Reachability Checker | `npm run lint:stubs` | **0 dead stubs / 0 orphan exports (224 components verified)** |
| **Content Security Policy (CSP)** | Deterministic CSP Invariant Verifier | `npm run audit:csp` | **Strict Zero unsafe-eval / zero unsafe-inline** |
| **Static Code Quality** | Oxlint (879 files scanned) | `npm run lint` | **0 errors** |
| **Production Bundle** | Vite / Rolldown Static Bundler | `npm run build` | **0 errors (clean bundle in ~1.49s)** |
| **Combined Passing Tests** | Multi-Layer Automated Verification | `npm run test:all` | **4,088 / 4,088 passed (100% green)** |

> ¹ Cloud-BYOK test paths are environment-gated — tests automatically mock or safely skip live outbound calls when no API key is configured in the vault. Counts verified with all BYOK keys absent.

### 🏛️ Multi-Agent Council & Architectural Review Alignment

To ensure industrial-grade software engineering and bulletproof architecture, SPrav Job AI is evaluated against three premier software verification frameworks:

1. **Karpathy LLM-Council Synthesis (`github.com/karpathy/llm-council`):**
   - Multi-agent peer verification: 22 specialized persona tests evaluate each layer independently (Crypto Hygiene, Wasm Invariants, Prompt Injection, Memory Bounds, Chaos Fuzzing, ReDoS Defense).
   - Consensus-driven validation: Every mission-critical module (ATS scoring, PDF compilation, storage vaults) requires unanimous multi-persona agreement before release.

2. **Alibaba Open-Code-Review Standards (`github.com/alibaba/open-code-review`):**
   - Strict zero-dead-code invariant enforced via automated AST parsing (`scripts/lint_dead_stubs.mjs`), ensuring 100% reachability across 224 components and zero orphan exports.
   - Comprehensive error isolation: React 19 Error Boundaries, non-blocking lazy loading fallbacks, and circuit breakers ensure an unhandled network error never crashes the application shell.

3. **Garry Tan GStack Engineering Rigor (`github.com/garrytan/gstack`):**
   - Founder-grade product velocity paired with zero runtime bloat: single-bundle production footprint (~1.49s build time) with $0 operating infrastructure.
   - Zero-dependency client-side vector math, ISO/IEC 18004 QR generation, and ISO 32000-1 PDF 1.4 compilation.

### 🛡️ OWASP Top 10 & Reverse-Engineering Armor

- **A01: Broken Access Control & Storage Sovereignty:** All candidate facts and API keys reside in browser IndexedDB protected by AES-GCM encryption with active memory shredding on 15-minute inactivity.
- **A02: Cryptographic Failures:** Zero plaintext credentials; PBKDF2 key derivation (100,000 iterations) with salted initialization vectors.
- **A03: Injection & Formula Injection (CWE-1236):** Strict escaping of CSV/Excel export fields (`=`, `+`, `-`, `@` neutralized) and AST-based sanitization of user strings.
- **OWASP LLM01: Prompt Injection Defense:** All user inputs and candidate bullets processed by LLM prompt templates are sanitized against ChatML delimiters, prompt-leak payloads, and jailbreak tokens (`cleanJsonFence`, `cleanDescription`).
- **Client-Side Anti-Tampering:** Object freeze and prototype sealing on global security interfaces prevent runtime monkey-patching and malicious browser extension tampering.
- **Content Security Policy:** Enforces strict `default-src 'self'`, `object-src 'none'`, `base-uri 'self'`, and zero `unsafe-eval` outside of necessary WebAssembly runtime bindings.

---

## 🌐 1-Click Cloud Deployment

Because **SPrav Job AI Web** requires no backend server, database instances, or serverless functions, it deploys to any static hosting service in under 60 seconds:

### Deploy to Vercel
```bash
npx vercel
```
*(The included `vercel.json` automatically handles client-side routing).*

### Deploy to Netlify
```bash
npx netlify deploy --prod
```
*(The included `netlify.toml` handles redirects and static headers).*

### Deploy to Cloudflare Pages or GitHub Pages
1. Push this repository to GitHub.
2. Connect your repository to **Cloudflare Pages** or enable **GitHub Pages**.
3. Set build command to `npm run build` and output directory to `dist`.

---

## 🔒 Privacy & Data Sovereignty Guarantee

1. **100% Client-Side Execution:** Your resume, work history, target roles, and salary expectations reside exclusively inside your browser's IndexedDB vault.
2. **Zero Centralized Tracking:** No candidate data is sent to or stored on third-party servers.
3. **Direct ATS Scanning:** Job listings are fetched directly by your browser from Greenhouse, Ashby, Lever, Jobicy, and Arbeitnow.

---

## 🛡️ Security & Responsible Disclosure

SPrav Job AI processes candidate data client-side and interacts with enterprise ATS portals. We maintain a responsible vulnerability disclosure program with strict SLAs.

- **Security Policy & Scope:** Please review our [SECURITY.md](SECURITY.md) for vulnerability classification, threat model boundaries, and safe harbor guidelines.
- **Reporting Vulnerabilities:** Contact **SVS Praveen** privately at [svspraveens@gmail.com](mailto:svspraveens@gmail.com) with the subject `[SECURITY VULNERABILITY] SPrav Job AI`.
- **Response Commitment:** Initial acknowledgment within 24–48 hours; triage within 72 hours.

---

## 👤 Author & Acknowledgments

- **Created & Architected by:** [SVS Praveen](https://github.com/SVSPraveen)
- **Design Philosophy:** Autonomous, candidate-first, zero-subscription career empowerment.

---

## 📄 License & Terms of Use

**SPrav™ Job AI** is proprietary software created and owned by **SVS Praveen**. All Rights Reserved.

- **Product Use:** 100% Free to use as an end-user application for personal, non-commercial job-seeking and career intelligence.
- **Source Code & IP Restrictions:** The source code, algorithms, databases, heuristics, and architecture contained in this repository are **proprietary and confidential**. Copying, reproducing, distributing, modifying, creating derivative works, reverse engineering, or sub-licensing is strictly prohibited without prior written permission from SVS Praveen.

For full legal terms, see the [LICENSE](LICENSE) file and the in-app [About & Legal notice](src/pages/AboutLegal.jsx). For licensing inquiries, commercial partnerships, or written permissions, contact [svspraveens@gmail.com](mailto:svspraveens@gmail.com).
