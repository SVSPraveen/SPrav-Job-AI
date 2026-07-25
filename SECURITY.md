# Security Policy

## Supported Versions
Currently, only the `main` branch is supported with security updates.

## Reporting a Vulnerability

If you discover a security vulnerability within SPrav Job AI, please do not disclose it publicly.
Instead, report it privately via GitHub:
1. Open a private GitHub Security Advisory on this repository, OR
2. Contact the maintainer via their GitHub Profile: [SVSPraveen](https://github.com/SVSPraveen)

All security vulnerabilities will be promptly addressed.

## Known Security Considerations
- **Credentials & API Keys:** SPrav Job AI uses local credential storage (XOR-encrypted vault in SQLite) for job portal logins. API keys are loaded via a local `.env` file. Do not commit your `users.db` or `.env` files.
- **JWT Auth:** The system uses JWT for frontend-backend authentication. The hardcoded fallback secret vulnerability has been fixed. The application will now fail loudly on startup if `JWT_SECRET` is missing from the `.env` file. Ensure you configure a strong, random secret.
