# 🤝 Contributing to SPrav Job AI

First off, thank you for considering contributing to SPrav! This project is built by and for developers who want to take control of their job hunt using local AI.

## 🧠 Philosophy

SPrav is strictly a **local-first** application. 
When proposing changes or new features, please adhere to these core principles:
1. **Zero Data Leakage:** We do not accept PRs that introduce third-party cloud analytics, telemetry, or remote API dependencies for core functionality (unless explicitly opt-in).
2. **MoE Routing:** Avoid massive, monolithic LLM calls. If you are adding a new AI feature, try to route it to a specialized, smaller model.
3. **No Magic:** The system must remain auditable. The SQLite databases should remain easily readable by the user.

## 🛠️ Development Setup

1. Fork the repository and clone your fork.
2. Create a virtual environment: `python -m venv .venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a new branch: `git checkout -b feature/your-feature-name`

## 📝 Pull Request Process

1. **Keep it focused:** PRs should address a single issue or add a single feature.
2. **Update Documentation:** If you add a new API endpoint, update the relevant module's `README.md`.
3. **Test Locally:** Ensure your changes do not break the core LangGraph state machine. Run the system locally and verify the logs before submitting.

We review PRs weekly. Welcome to the resistance!
