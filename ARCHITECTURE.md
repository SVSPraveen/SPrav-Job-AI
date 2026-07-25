# 🏛️ Architecture: SPrav Mixture of Experts (MoE)

The SPrav Job AI is built upon a specialized local-first architecture known as the **SPrav MOE State Machine**. 

Unlike standard AI wrapper applications that blindly forward user prompts to a single, monolithic API (which frequently results in hallucinations, context degradation, and repetitive loops), SPrav implements a strict, multi-agent logic pipeline.

## 🧠 The Mixture of Experts Philosophy

We assign highly specific, granular tasks to highly specialized models. By using smaller, fine-tuned models for exact tasks, we achieve lower latency, deterministic outputs, and strict data integrity.

| Node | Model Constraint | Responsibility | Output Format |
|---|---|---|---|
| **Extractor** | `qwen2.5` | Reads messy HR HTML/text and extracts core requirements. | Strict JSON |
| **Evaluator** | `deepseek-r1:7b` | Calculates holistic Candidate-to-Job Fit Scoring. | Mathematical Float (0.0 to 5.0) |
| **Tailor** | `llama-3.3-70b` | High-prose generative drafting of Resumes & Cold Emails. | Markdown / PDF |
| **Verifier** | `bespoke-minicheck` | Fact-checks generated prose against the user's canonical Knowledge Base. | Boolean Pass/Fail |

## 🔄 The Word Chain Memory Loop

The core innovation of the SPrav Engine is the zero-hallucination **Feedback Loop**. 

When a generative model (like Llama 3.3) attempts to artificially inflate a user's skills to match a job description, standard applications either allow the lie to pass or rely on complex prompt engineering to beg the model not to lie. SPrav uses algorithmic fact-checking.

If the **Verifier** node (`bespoke-minicheck`) detects an ungrounded claim (a hallucination), it rejects the output. However, it does not simply restart the prompt. It generates a "Word Chain":

1. **Context:** The original User profile (`me.json`) and the Job Description.
2. **Draft:** The flawed, generated output.
3. **Diagnosis:** The specific hallucination detected by the Verifier.

This entire block of concatenated state is fed back into the Tailor. By forcing the generative model to explicitly "read" its own mistake alongside the forensic correction, SPrav absolutely guarantees that infinite hallucination loops are broken and that your generated applications remain 100% factually accurate.

## 💾 Local VRAM Constraints (8GB Optimization)

To democratize autonomous job hunting, SPrav is engineered to run on consumer-grade hardware (minimum 8GB VRAM). 

Running four expert LLMs simultaneously would instantly trigger an Out-Of-Memory (OOM) crash. SPrav solves this using **Sequential Thread Locking (`gpu_mutex`)**. 

The state machine strictly enforces that only one expert model occupies the GPU at any given time. When the pipeline transitions from the Extractor to the Evaluator, it explicitly issues a `keep_alive: 0` command to Ollama, forcing an immediate VRAM purge before the next model is loaded into memory. This guarantees zero-downtime execution and complete local privacy without needing a high-end data center GPU.

## 🛑 3-Tier Circuit Breakers

Autonomy without safety is dangerous. To prevent your professional accounts from being flagged as bots, the Execution layer operates behind strict cryptographic and volumetric limits.

- **Company Cap:** Max 5 auto-applications per specific company per day.
- **Portal Cap:** Max 25 auto-applications per ATS platform (e.g., Greenhouse) per day.
- **Global Cap:** Hard ceiling of 150 automated actions across the entire internet per day.

If the Playwright injection engine detects anti-bot captchas or abnormal form logic, the Circuit Breaker trips immediately, aborting the automated run and routing the application to your Dashboard's **Human Review Queue** for manual approval.
