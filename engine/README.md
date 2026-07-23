# ⚙️ SPrav Engine (`/engine`)

The Engine is the central nervous system of SPrav. It is responsible for orchestrating the Mixtrue-of-Experts (MoE) LLM pipeline and enforcing data integrity.

## 🧠 Core Philosophy
Large Language Models hallucinate. To prevent this, the SPrav Engine explicitly forbids generative models from "guessing." Every claim made in a tailored resume is cross-referenced against the local Knowledge Base.

## 🏗️ Components

* **`auth.py`**: Handles local SQLite user authentication and credential obfuscation.
* **`prompts.py`**: Stores the system prompts for Qwen, DeepSeek, and Llama, explicitly engineered to force rigid JSON or strict logic outputs.
* **`llm_router.py`**: The LangGraph state machine that routes data between the localized Ollama instances.

## 🚀 Usage (Internal)
The Engine is not meant to be called directly by the user. It is invoked natively by the FastAPI backend when a new batch of jobs arrives from the Discovery layer.
