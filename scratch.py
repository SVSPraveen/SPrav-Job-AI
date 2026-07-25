from engine.kb_merger import merge
sources = [
    {
        "source": "manual",
        "personal": {},
        "work_history": [],
        "education": [],
        "certifications": [
            {
                "id": "cert_oraclecloudinfrastructure2025certi",
                "name": "Oracle Cloud Infrastructure 2025 Certi",
                "issuer": "Oracle University",
                "date_earned": "2025-10",
                "expires": "102986081OCI25FNDCFA",
                "credential_id": "",
                "url": "https://catalog-education.oracle.com/p",
                "_source": "manual"
            }
        ],
        "skills": {},
        "github_projects": [],
        "portfolio_projects": []
    }
]
try:
    merge(sources, kb_path="knowledge_base/test_me.json")
except Exception as e:
    import traceback
    traceback.print_exc()
