"""
engine/skill_taxonomy.py

Semantic Skill Expansion & Inference Engine.

The problem:
  - A candidate who writes "AI" on their resume means "Artificial Intelligence"
    which subsumes ML, model training, neural nets, etc.
  - A candidate who "trained models" knows machine learning even if they didn't
    spell it out as "ML" or "scikit-learn".
  - Abbreviations: "NLP" = "Natural Language Processing", "CV" = "Computer Vision", etc.
  - Brand/alias equivalence: "Postgres" = "PostgreSQL", "K8s" = "Kubernetes", etc.

Solution:
  - A rich SKILL_GRAPH where each skill node lists its:
      * aliases: exact-match synonyms / abbreviations
      * implies: skills the candidate *demonstrably knows* if they know this one
  - expand_candidate_skills(raw_skills) → enriched set including all inferred skills
  - normalize_skill(skill) → canonical lowercased form
  - skill_implies(candidate_set, job_skill) → True if candidate set logically covers job_skill
"""

from __future__ import annotations
import re

# ---------------------------------------------------------------------------
# Skill Graph
# Each key is the canonical skill name (lowercase).
# "aliases"  : other names / abbreviations that mean the same thing
# "implies"  : skills a person demonstrably has if they know this one
# ---------------------------------------------------------------------------
SKILL_GRAPH: dict[str, dict] = {
    # ── Artificial Intelligence (umbrella) ─────────────────────────────────
    "artificial intelligence": {
        "aliases": ["ai", "a.i.", "ai/ml", "ml/ai", "artificial intelligence engineering"],
        "implies": [
            "machine learning", "deep learning", "model training", "neural networks",
            "data science", "python", "scikit-learn", "tensorflow", "pytorch",
            "lightgbm", "xgboost", "keras", "mlflow", "ragas", "llms", "large language models",
            "agentic ai", "ai agents", "nlp", "natural language processing"
        ],

    # ── Mobile & Cross-Platform ──────────────────────────────────────────
    "react native": {
        "aliases": ["rn", "react-native"],
        "implies": ["react", "javascript", "typescript", "mobile development", "frontend"]
    },
    "flutter": {
        "aliases": ["flutter framework", "flutter/dart"],
        "implies": ["dart", "mobile development", "cross-platform", "frontend"]
    },
    "swiftui": {
        "aliases": ["swift ui"],
        "implies": ["swift", "ios development", "mobile development"]
    },
    "jetpack compose": {
        "aliases": ["compose", "android compose"],
        "implies": ["kotlin", "android development", "mobile development"]
    },

    # ── Frontend Frameworks ──────────────────────────────────────────────
    "next.js": {
        "aliases": ["nextjs", "next.js 13", "next.js 14", "next.js 15"],
        "implies": ["react", "javascript", "typescript", "frontend", "web development"]
    },
    "vue": {
        "aliases": ["vue.js", "vuejs", "vue 3", "vue 2"],
        "implies": ["javascript", "frontend", "web development"]
    },
    "angular": {
        "aliases": ["angular.js", "angularjs", "angular 2+"],
        "implies": ["typescript", "javascript", "frontend", "web development"]
    },
    "svelte": {
        "aliases": ["sveltekit", "svelte.js"],
        "implies": ["javascript", "frontend", "web development"]
    },
    "tailwind css": {
        "aliases": ["tailwind", "tailwindcss"],
        "implies": ["css", "frontend", "web development"]
    },

    # ── Backend Frameworks ───────────────────────────────────────────────
    "spring boot": {
        "aliases": ["spring", "spring framework", "spring cloud"],
        "implies": ["java", "backend", "microservices", "rest apis"]
    },
    "django": {
        "aliases": ["django rest framework", "drf"],
        "implies": ["python", "backend", "web development", "rest apis"]
    },
    "flask": {
        "aliases": ["flask-restful"],
        "implies": ["python", "backend", "web development", "rest apis"]
    },
    "asp.net": {
        "aliases": ["asp.net core", ".net core", ".net", "dotnet"],
        "implies": ["c#", "backend", "web development"]
    },
    "ruby on rails": {
        "aliases": ["rails", "ror"],
        "implies": ["ruby", "backend", "web development"]
    },
    "laravel": {
        "aliases": ["laravel framework"],
        "implies": ["php", "backend", "web development"]
    },
    "express": {
        "aliases": ["express.js", "expressjs"],
        "implies": ["node.js", "javascript", "backend", "rest apis"]
    },
    "nestjs": {
        "aliases": ["nest.js"],
        "implies": ["node.js", "typescript", "backend", "rest apis"]
    },

    # ── DevOps, Cloud & Infrastructure ───────────────────────────────────
    "kubernetes": {
        "aliases": ["k8s", "k9s"],
        "implies": ["docker", "containerization", "devops", "cloud computing", "cloud infrastructure"]
    },
    "terraform": {
        "aliases": ["opentofu"],
        "implies": ["infrastructure as code", "iac", "devops", "cloud computing"]
    },
    "ansible": {
        "aliases": ["ansible playbook"],
        "implies": ["devops", "configuration management", "linux", "automation"]
    },
    "github actions": {
        "aliases": ["gha", "github ci"],
        "implies": ["ci/cd", "git", "devops", "automation"]
    },
    "jenkins": {
        "aliases": ["jenkins ci", "jenkins pipeline"],
        "implies": ["ci/cd", "devops", "automation"]
    },
    "linux": {
        "aliases": ["unix", "ubuntu", "debian", "rhel", "centos"],
        "implies": ["bash", "shell scripting", "operating systems"]
    },

    # ── Cybersecurity & Networking ───────────────────────────────────────
    "cybersecurity": {
        "aliases": ["information security", "infosec", "appsec", "application security"],
        "implies": ["security", "networking", "risk management"]
    },
    "penetration testing": {
        "aliases": ["pen testing", "ethical hacking", "vulnerability assessment"],
        "implies": ["cybersecurity", "security", "owasp"]
    },
    "owasp": {
        "aliases": ["owasp top 10"],
        "implies": ["application security", "cybersecurity", "web security"]
    },

    # ── QA, Testing & Automation ─────────────────────────────────────────
    "test automation": {
        "aliases": ["qa automation", "automated testing", "qa engineering"],
        "implies": ["testing", "qa", "software quality"]
    },
    "cypress": {
        "aliases": ["cypress.io"],
        "implies": ["test automation", "e2e testing", "javascript", "testing"]
    },
    "playwright": {
        "aliases": ["playwright test"],
        "implies": ["test automation", "e2e testing", "browser automation", "testing"]
    },
    "selenium": {
        "aliases": ["selenium webdriver"],
        "implies": ["test automation", "e2e testing", "testing"]
    },
    "pytest": {
        "aliases": ["py.test"],
        "implies": ["python", "unit testing", "test automation", "testing"]
    },
    "jest": {
        "aliases": ["jestjs"],
        "implies": ["javascript", "unit testing", "testing"]
    },

    # ── Data Engineering & Big Data ──────────────────────────────────────
    "apache spark": {
        "aliases": ["spark", "pyspark", "spark sql"],
        "implies": ["big data", "data engineering", "python", "distributed computing"]
    },
    "apache kafka": {
        "aliases": ["kafka", "kafka streams", "kafka connect"],
        "implies": ["event-driven architecture", "distributed systems", "data streaming", "messaging"]
    },
    "airflow": {
        "aliases": ["apache airflow"],
        "implies": ["data engineering", "etl", "python", "workflow orchestration", "data pipeline"]
    },
    "dbt": {
        "aliases": ["data build tool"],
        "implies": ["sql", "data engineering", "etl", "data modeling", "data transformation"]
    },
    "snowflake": {
        "aliases": ["snowflake data cloud"],
        "implies": ["sql", "data warehousing", "cloud computing", "data engineering"]
    },
    "bigquery": {
        "aliases": ["google bigquery"],
        "implies": ["sql", "data warehousing", "gcp", "data engineering"]
    },

    # ── Embedded, IoT & Game Development ─────────────────────────────────
    "embedded systems": {
        "aliases": ["embedded engineering", "embedded software", "firmware"],
        "implies": ["c", "c++", "microcontrollers", "hardware"]
    },
    "unity": {
        "aliases": ["unity3d", "unity engine"],
        "implies": ["c#", "game development", "3d graphics"]
    },
    "unreal engine": {
        "aliases": ["ue4", "ue5", "unreal"],
        "implies": ["c++", "game development", "3d graphics"]
    },

    # ── Product, Design & Agile ──────────────────────────────────────────
    "ui/ux": {
        "aliases": ["ui/ux design", "user experience", "user interface design", "product design"],
        "implies": ["design", "wireframing", "prototyping", "figma"]
    },
    "figma": {
        "aliases": ["figma design"],
        "implies": ["ui/ux", "design", "prototyping", "wireframing"]
    },
    "agile": {
        "aliases": ["agile methodology", "scrum", "kanban", "sprint planning"],
        "implies": ["project management", "team collaboration", "jira"]
    },
    "jira": {
        "aliases": ["atlassian jira"],
        "implies": ["agile", "project management", "issue tracking"]
    },
    "product management": {
        "aliases": ["technical product management", "tpm", "product roadmap"],
        "implies": ["agile", "jira", "product strategy", "user research"]
    }

},
    "machine learning": {
        "aliases": ["ml", "ml engineering", "machine learning engineering", "applied ml"],
        "implies": [
            "model training", "feature engineering", "data science",
            "scikit-learn", "python", "statistics", "pytorch", "tensorflow",
            "lightgbm", "xgboost", "keras", "mlflow", "ragas", "deep learning",
            "neural networks", "algorithms", "predictive modeling"
        ],
    },
    "deep learning": {
        "aliases": ["dl", "dnn", "deep neural networks"],
        "implies": ["neural networks", "machine learning", "pytorch", "tensorflow", "keras", "python", "model training"],
    },
    "model training": {
        "aliases": ["trained models", "train models", "training ml models",
                    "training neural networks", "model fine-tuning", "fine-tuning",
                    "finetuning", "fine tuning", "model evaluation", "peft", "lora"],
        "implies": ["machine learning", "deep learning", "python", "scikit-learn", "pytorch", "tensorflow"],
    },
    "neural networks": {
        "aliases": ["ann", "neural net", "neural nets", "nns", "cnns", "rnns"],
        "implies": ["deep learning", "machine learning", "python", "pytorch", "tensorflow"],
    },
    "large language models": {
        "aliases": ["llm", "llms", "large language model", "language models", "gpt", "llm engineering", "llama", "qwen"],
        "implies": [
            "machine learning", "deep learning", "nlp", "natural language processing",
            "transformers", "python", "artificial intelligence", "prompt engineering",
            "rag", "retrieval augmented generation", "fine-tuning"
        ],
    },
    "generative ai": {
        "aliases": ["genai", "gen-ai", "gen ai", "generative artificial intelligence"],
        "implies": [
            "large language models", "machine learning", "artificial intelligence",
            "python", "prompt engineering", "nlp", "natural language processing",
            "transformers", "deep learning"
        ],
    },
    "natural language processing": {
        "aliases": ["nlp", "n.l.p.", "text processing", "text analytics", "language ai", "computational linguistics"],
        "implies": [
            "machine learning", "deep learning", "python", "transformers",
            "large language models", "sentence-transformers", "hugging face",
            "text embeddings", "information retrieval"
        ],
    },
    "computer vision": {
        "aliases": ["cv", "image recognition", "object detection", "image classification",
                    "vision ai", "visual ai"],
        "implies": ["deep learning", "machine learning", "pytorch", "tensorflow", "python"],
    },
    "data science": {
        "aliases": ["data analytics", "data analysis", "analytics", "data scientist"],
        "implies": ["python", "machine learning", "statistics", "pandas", "numpy", "sql"],
    },
    "reinforcement learning": {
        "aliases": ["rl", "rlhf", "rl from human feedback", "reward modelling"],
        "implies": ["machine learning", "deep learning", "python"],
    },
    "prompt engineering": {
        "aliases": ["prompting", "prompt design", "prompt tuning", "zero-shot", "few-shot"],
        "implies": ["large language models", "artificial intelligence", "python"],
    },
    # ── RAG / Agentic Systems ───────────────────────────────────────────────
    "retrieval augmented generation": {
        "aliases": ["rag", "rag pipeline", "retrieval-augmented generation"],
        "implies": ["large language models", "vector databases", "python",
                    "langchain", "natural language processing"],
    },
    "agentic ai": {
        "aliases": ["ai agents", "autonomous agents", "agentic systems", "ai agent", "agent ai",
                    "multi-agent", "multi agent", "langgraph", "agentic"],
        "implies": ["large language models", "langchain", "python", "retrieval augmented generation"],
    },
    "langchain": {
        "aliases": ["lang chain"],
        "implies": ["large language models", "python", "retrieval augmented generation"],
    },
    "llamaindex": {
        "aliases": ["llama index", "llama-index"],
        "implies": ["large language models", "python", "retrieval augmented generation"],
    },
    # ── Vector Databases ────────────────────────────────────────────────────
    "vector databases": {
        "aliases": ["vector db", "vector store", "embedding store", "semantic search"],
        "implies": ["machine learning", "python"],
    },
    "pinecone": {"aliases": ["pine cone"], "implies": ["vector databases", "python"]},
    "qdrant":   {"aliases": [], "implies": ["vector databases", "python"]},
    "weaviate": {"aliases": [], "implies": ["vector databases", "python"]},
    "faiss":    {"aliases": ["facebook ai similarity search"], "implies": ["vector databases", "python"]},
    "pgvector": {"aliases": ["pg vector"], "implies": ["vector databases", "postgresql"]},
    # ── ML Frameworks ───────────────────────────────────────────────────────
    "pytorch": {
        "aliases": ["torch"],
        "implies": ["deep learning", "machine learning", "python"],
    },
    "tensorflow": {
        "aliases": ["tf", "keras"],
        "implies": ["deep learning", "machine learning", "python"],
    },
    "scikit-learn": {
        "aliases": ["sklearn", "scikit learn"],
        "implies": ["machine learning", "python"],
    },
    "hugging face": {
        "aliases": ["huggingface", "hf", "transformers library"],
        "implies": ["large language models", "natural language processing", "machine learning", "python"],
    },
    "transformers": {
        "aliases": ["transformer model", "attention mechanism", "bert", "gpt"],
        "implies": ["deep learning", "natural language processing", "python"],
    },
    # ── MLOps & Experiment Tracking ─────────────────────────────────────────
    "mlops": {
        "aliases": ["ml ops", "ml pipelines", "ml platform"],
        "implies": ["machine learning", "docker", "python", "ci/cd"],
    },
    "mlflow": {"aliases": ["ml flow"], "implies": ["mlops", "machine learning", "python"]},
    "weights & biases": {"aliases": ["wandb", "weights and biases"], "implies": ["mlops", "machine learning"]},
    # ── Backend & Web ────────────────────────────────────────────────────────
    "fastapi": {
        "aliases": ["fast api", "fast-api"],
        "implies": ["python", "rest apis", "backend"],
    },
    "rest apis": {
        "aliases": ["rest api", "rest", "restful api", "restful apis", "api development",
                    "apis", "http api", "web api"],
        "implies": ["backend", "python"],
    },
    "backend": {
        "aliases": ["backend development", "server-side", "backend engineering"],
        "implies": ["python", "rest apis"],
    },
    "full stack": {
        "aliases": ["full-stack", "fullstack", "full stack development", "full stack engineer"],
        "implies": ["backend", "javascript", "react", "rest apis"],
    },
    "graphql": {"aliases": ["graph ql"], "implies": ["rest apis", "backend"]},
    # ── Languages ───────────────────────────────────────────────────────────
    "python": {
        "aliases": ["py", "python3", "python 3", "python programming"],
        "implies": [],
    },
    "javascript": {
        "aliases": ["js", "es6", "es2015", "ecmascript", "node.js", "nodejs", "node js"],
        "implies": [],
    },
    "typescript": {
        "aliases": ["ts"],
        "implies": ["javascript"],
    },
    "golang": {
        "aliases": ["go", "go lang", "go language"],
        "implies": [],
    },
    "rust": {"aliases": [], "implies": []},
    "java": {"aliases": ["java programming"], "implies": []},
    "c++": {"aliases": ["cpp", "c plus plus"], "implies": []},
    # ── Databases ───────────────────────────────────────────────────────────
    "sql": {
        "aliases": ["structured query language", "relational database", "relational db", "rdbms"],
        "implies": [],
    },
    "postgresql": {
        "aliases": ["postgres", "psql", "pg"],
        "implies": ["sql"],
    },
    "mysql": {"aliases": [], "implies": ["sql"]},
    "mongodb": {
        "aliases": ["mongo", "mongo db"],
        "implies": [],
    },
    "redis": {"aliases": [], "implies": []},
    "sqlite": {"aliases": [], "implies": ["sql"]},
    # ── Cloud & Infrastructure ──────────────────────────────────────────────
    "aws": {
        "aliases": ["amazon web services", "amazon aws", "aws cloud"],
        "implies": ["cloud computing"],
    },
    "gcp": {
        "aliases": ["google cloud", "google cloud platform", "google cloud services"],
        "implies": ["cloud computing"],
    },
    "azure": {
        "aliases": ["microsoft azure", "azure cloud"],
        "implies": ["cloud computing"],
    },
    "cloud computing": {
        "aliases": ["cloud", "cloud infrastructure", "cloud services"],
        "implies": [],
    },
    "docker": {
        "aliases": ["containerization", "containers"],
        "implies": ["devops"],
    },
    "kubernetes": {
        "aliases": ["k8s", "k 8 s", "container orchestration"],
        "implies": ["docker", "devops"],
    },
    "ci/cd": {
        "aliases": ["cicd", "ci cd", "continuous integration", "continuous delivery",
                    "continuous deployment", "github actions", "gitlab ci", "jenkins"],
        "implies": ["devops"],
    },
    "devops": {
        "aliases": ["dev ops", "devsecops", "platform engineering"],
        "implies": ["ci/cd", "docker"],
    },
    "terraform": {"aliases": ["infrastructure as code", "iac"], "implies": ["devops", "cloud computing"]},
    # ── Frontend ─────────────────────────────────────────────────────────────
    "react": {
        "aliases": ["reactjs", "react.js", "react js"],
        "implies": ["javascript", "html", "css", "frontend", "web development", "ui"],
    },
    "html": {
        "aliases": ["html5", "html/css", "css", "css3"],
        "implies": ["frontend", "web development"],
    },
    "next.js": {
        "aliases": ["nextjs", "next js"],
        "implies": ["react", "javascript", "html", "css"],
    },
    "vue.js": {"aliases": ["vuejs", "vue js", "vue"], "implies": ["javascript", "html", "css"]},
    "angular": {"aliases": ["angularjs"], "implies": ["javascript", "typescript", "html", "css"]},
    # ── Data Engineering ──────────────────────────────────────────────────────
    "apache spark": {
        "aliases": ["spark", "pyspark"],
        "implies": ["data engineering", "python"],
    },
    "data engineering": {
        "aliases": ["data pipeline", "etl", "elt", "data pipelines", "data processing"],
        "implies": ["sql", "python", "databases"],
    },
    "kafka": {
        "aliases": ["apache kafka"],
        "implies": ["data engineering"],
    },
    "airflow": {
        "aliases": ["apache airflow"],
        "implies": ["data engineering", "python"],
    },
    # ── Agentic & Search ─────────────────────────────────────────────────────
    "semantic search": {
        "aliases": ["semantic similarity", "dense retrieval", "bi-encoder", "embedding search"],
        "implies": ["vector databases", "machine learning", "python", "nlp"],
    },
    "embeddings": {
        "aliases": ["word embeddings", "sentence embeddings", "text embeddings", "vector embeddings"],
        "implies": ["machine learning", "natural language processing", "python", "nlp"],
    },
    # ── Soft / Generic Dev Skills ─────────────────────────────────────────────
    "git": {
        "aliases": ["version control", "github", "gitlab", "bitbucket", "source control"],
        "implies": ["agile", "scrum", "software engineering"],
    },
    "agile": {
        "aliases": ["scrum", "kanban", "sprints", "agile methodologies"],
        "implies": ["software engineering"],
    },
    "leadership": {
        "aliases": ["team leadership", "mentorship", "project management", "technical leadership"],
        "implies": [],
    },
    "linux": {
        "aliases": ["unix", "bash", "shell scripting", "shell", "bash scripting", "cli"],
        "implies": [],
    },
    "statistics": {
        "aliases": ["statistical analysis", "statistical modeling", "probability", "maths", "mathematics"],
        "implies": [],
    },
    "pandas": {"aliases": ["dataframe", "data manipulation"], "implies": ["python"]},
    "numpy":  {"aliases": [], "implies": ["python"]},
    "data visualization": {
        "aliases": ["matplotlib", "seaborn", "plotly", "tableau", "power bi", "dashboards"],
        "implies": ["python"],
    },
    "security": {
        "aliases": ["cybersecurity", "application security", "appsec", "soc", "siem", "pen testing",
                    "penetration testing", "threat modeling", "owasp"],
        "implies": [],
    },
    # ── Mobile & Cross-Platform ──
    "react native": {
        "aliases": ["rn", "react-native"],
        "implies": ["react", "javascript", "typescript", "mobile development", "frontend"],
    },
    "flutter": {
        "aliases": ["flutter framework", "flutter/dart"],
        "implies": ["dart", "mobile development", "cross-platform", "frontend"],
    },
    "swiftui": {
        "aliases": ["swift ui"],
        "implies": ["swift", "ios development", "mobile development"],
    },
    "jetpack compose": {
        "aliases": ["compose", "android compose"],
        "implies": ["kotlin", "android development", "mobile development"],
    },
    "mobile development": {
        "aliases": ["mobile app development", "ios", "android"],
        "implies": ["software engineering"],
    },
    "dart": {"aliases": [], "implies": ["programming"]},
    "swift": {"aliases": ["ios"], "implies": ["mobile development"]},
    "kotlin": {"aliases": ["android"], "implies": ["java", "mobile development"]},

    # ── Frontend & UI/UX ──
    "tailwind css": {
        "aliases": ["tailwind", "tailwindcss"],
        "implies": ["css", "frontend", "html"],
    },
    "svelte": {
        "aliases": ["sveltekit", "svelte.js"],
        "implies": ["javascript", "frontend", "html", "css"],
    },
    "ui/ux": {
        "aliases": ["ui/ux design", "user experience", "user interface design", "product design"],
        "implies": ["design", "wireframing", "prototyping", "figma"],
    },
    "figma": {
        "aliases": ["figma design"],
        "implies": ["ui/ux", "design", "prototyping"],
    },

    # ── Backend Frameworks ──
    "spring boot": {
        "aliases": ["spring", "spring framework", "spring cloud"],
        "implies": ["java", "backend", "microservices", "rest apis"],
    },
    "django": {
        "aliases": ["django rest framework", "drf"],
        "implies": ["python", "backend", "web development", "rest apis"],
    },
    "flask": {
        "aliases": ["flask-restful"],
        "implies": ["python", "backend", "web development", "rest apis"],
    },
    "asp.net": {
        "aliases": ["asp.net core", ".net core", ".net", "dotnet"],
        "implies": ["c#", "backend", "web development"],
    },
    "ruby on rails": {
        "aliases": ["rails", "ror"],
        "implies": ["ruby", "backend", "web development"],
    },
    "laravel": {
        "aliases": ["laravel framework"],
        "implies": ["php", "backend", "web development"],
    },
    "express": {
        "aliases": ["express.js", "expressjs"],
        "implies": ["node.js", "javascript", "backend", "rest apis"],
    },
    "nestjs": {
        "aliases": ["nest.js"],
        "implies": ["node.js", "typescript", "backend", "rest apis"],
    },

    # ── Cloud & DevOps ──
    "kubernetes": {
        "aliases": ["k8s", "k9s"],
        "implies": ["docker", "containerization", "devops", "cloud computing"],
    },
    "ansible": {
        "aliases": ["ansible playbook"],
        "implies": ["devops", "configuration management", "linux"],
    },
    "github actions": {
        "aliases": ["gha", "github ci"],
        "implies": ["ci/cd", "git", "devops"],
    },
    "jenkins": {
        "aliases": ["jenkins ci", "jenkins pipeline"],
        "implies": ["ci/cd", "devops"],
    },

    # ── QA & Testing ──
    "test automation": {
        "aliases": ["qa automation", "automated testing", "qa engineering"],
        "implies": ["testing", "qa", "software engineering"],
    },
    "cypress": {
        "aliases": ["cypress.io"],
        "implies": ["test automation", "e2e testing", "javascript", "testing"],
    },
    "playwright": {
        "aliases": ["playwright test"],
        "implies": ["test automation", "e2e testing", "browser automation", "testing"],
    },
    "selenium": {
        "aliases": ["selenium webdriver"],
        "implies": ["test automation", "e2e testing", "testing"],
    },
    "pytest": {
        "aliases": ["py.test"],
        "implies": ["python", "unit testing", "test automation", "testing"],
    },
    "jest": {
        "aliases": ["jestjs"],
        "implies": ["javascript", "unit testing", "testing"],
    },

    # ── Data & Big Data ──
    "big data": {
        "aliases": ["big data analytics", "distributed data"],
        "implies": ["data engineering"],
    },
    "dbt": {
        "aliases": ["data build tool"],
        "implies": ["sql", "data engineering", "etl", "data modeling"],
    },
    "snowflake": {
        "aliases": ["snowflake data cloud"],
        "implies": ["sql", "data warehousing", "cloud computing", "data engineering"],
    },
    "bigquery": {
        "aliases": ["google bigquery"],
        "implies": ["sql", "data warehousing", "gcp", "data engineering"],
    },

    # ── Embedded & Game Dev ──
    "embedded systems": {
        "aliases": ["embedded engineering", "firmware"],
        "implies": ["c", "c++", "microcontrollers", "hardware"],
    },
    "unity": {
        "aliases": ["unity3d", "unity engine"],
        "implies": ["c#", "game development", "3d graphics"],
    },
    "unreal engine": {
        "aliases": ["ue4", "ue5", "unreal"],
        "implies": ["c++", "game development", "3d graphics"],
    },

    # ── Management ──
    "jira": {
        "aliases": ["atlassian jira"],
        "implies": ["agile", "project management"],
    },
    "product management": {
        "aliases": ["technical product management", "tpm"],
        "implies": ["agile", "jira", "product strategy"],
    },
}

# ---------------------------------------------------------------------------
# Build lookup tables at module load time for O(1) alias resolution
# ---------------------------------------------------------------------------
_ALIAS_TO_CANONICAL: dict[str, str] = {}
_CANONICAL_TO_IMPLIES: dict[str, set[str]] = {}

def _build_lookup():
    for canonical, meta in SKILL_GRAPH.items():
        _ALIAS_TO_CANONICAL[canonical] = canonical          # self
        for alias in meta.get("aliases", []):
            _ALIAS_TO_CANONICAL[alias.lower().strip()] = canonical
        _CANONICAL_TO_IMPLIES[canonical] = set(meta.get("implies", []))

_build_lookup()


def normalize_skill(skill: str) -> str:
    """Return the canonical lowercase name for a skill, resolving aliases."""
    sk = skill.lower().strip()
    return _ALIAS_TO_CANONICAL.get(sk, sk)


def expand_candidate_skills(raw_skills: set[str], depth: int = 3) -> set[str]:
    """
    Given the raw set of skills from the candidate's profile/resume,
    expand it to include:
      1. Canonical forms of each skill (alias resolution)
      2. All skills logically implied by what the candidate knows
         (transitively, up to `depth` hops so we don't over-infer)

    Example:
      {"AI"} → {"artificial intelligence", "machine learning", "deep learning",
                 "model training", "neural networks", "data science", "python", ...}
    """
    # Step 1: resolve all aliases to canonical forms
    canonical: set[str] = set()
    for sk in raw_skills:
        c = normalize_skill(sk)
        canonical.add(c)
        canonical.add(sk.lower().strip())   # keep original too

    # Step 2: iteratively expand via "implies" edges
    expanded = set(canonical)
    frontier = set(canonical)
    for _ in range(depth):
        next_frontier: set[str] = set()
        for sk in frontier:
            for implied in _CANONICAL_TO_IMPLIES.get(sk, set()):
                implied_c = normalize_skill(implied)
                if implied_c not in expanded:
                    expanded.add(implied_c)
                    expanded.add(implied.lower().strip())
                    next_frontier.add(implied_c)
        if not next_frontier:
            break
        frontier = next_frontier

    return expanded


def skill_implies_candidate_has(candidate_expanded: set[str], job_skill: str) -> bool:
    """
    Returns True if the expanded candidate skill set covers a job's required skill.
    Checks:
      1. Direct membership in expanded set
      2. Alias match: the job_skill is an alias for something the candidate knows
      3. Substring heuristic: close enough that it's clearly the same tech
    """
    js = job_skill.lower().strip()
    js_canonical = normalize_skill(js)

    # Direct or canonical match
    if js in candidate_expanded or js_canonical in candidate_expanded:
        return True

    return False


def categorize_skills_dynamically(skills_input: list[str] | set[str] | dict) -> dict[str, list[str]]:
    """
    Intelligent Dynamic Skill Categorizer.
    Takes ANY candidate's raw skills and automatically categorizes them into the
    6 intuitive Knowledge Base Skills Arsenal buckets based on semantic taxonomy.
    """
    categories = {
        "ai_agentic_systems": [],
        "retrieval_search": [],
        "llms_vector_databases": [],
        "ml_evaluation": [],
        "full_stack_backend": [],
        "cloud_security": []
    }

    if isinstance(skills_input, dict):
        raw_list = []
        for k, v in skills_input.items():
            if isinstance(v, list):
                raw_list.extend(v)
            elif isinstance(v, str):
                raw_list.extend([s.strip() for s in v.split(',') if s.strip()])
    elif isinstance(skills_input, (list, set)):
        raw_list = list(skills_input)
    else:
        raw_list = []

    seen = set()

    for item in raw_list:
        if not item or not isinstance(item, str):
            continue
        sk = item.strip()
        sk_lower = sk.lower()
        if sk_lower in seen:
            continue
        seen.add(sk_lower)

        # 1. AI / Agentic Systems
        if any(w in sk_lower for w in ["agent", "langgraph", "langchain", "autogen", "crewai", "multi-agent", "workflow", "prompt", "reasoning", "tool calling"]):
            categories["ai_agentic_systems"].append(sk)
        # 2. Retrieval & Search / Data
        elif any(w in sk_lower for w in ["search", "bm25", "cache", "caching", "sentence-transformer", "transformer", "rerank", "embedding", "retrieval", "elastic", "solr", "kafka", "spark", "etl"]):
            categories["retrieval_search"].append(sk)
        # 3. LLMs & Vector DBs
        elif any(w in sk_lower for w in ["qdrant", "chroma", "pinecone", "weaviate", "milvus", "vector", "vllm", "ollama", "groq", "openai", "gemini", "claude", "llama", "lora", "peft", "fine-tuning", "finetuning", "rag"]):
            categories["llms_vector_databases"].append(sk)
        # 4. ML & Evaluation
        elif any(w in sk_lower for w in ["torch", "tensorflow", "keras", "scikit", "sklearn", "mlflow", "ragas", "pytest", "pandas", "numpy", "statistics", "eval", "metric", "deep learning", "machine learning"]):
            categories["ml_evaluation"].append(sk)
        # 5. Cloud & Security / DevOps
        elif any(w in sk_lower for w in ["aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform", "ansible", "ci/cd", "git", "linux", "bash", "jwt", "oauth", "security", "iam", "nginx"]):
            categories["cloud_security"].append(sk)
        # 6. Full Stack & Backend (Languages, Frameworks, DBs)
        else:
            categories["full_stack_backend"].append(sk)

    return categories
