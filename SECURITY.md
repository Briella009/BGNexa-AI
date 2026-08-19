# Security Policy

## Reporting a vulnerability

Please do not publish exploitable vulnerabilities, secrets, customer evidence, API keys, or sensitive assessment data in a public issue.

For a real deployment, configure a private security-reporting channel before exposing the service to external users.

## AI and evidence security boundaries

- Uploaded evidence is treated as untrusted data.
- Prompt-injection detection is a defensive heuristic, not a guarantee that every malicious instruction will be detected.
- Regulatory applicability is not delegated to the LLM.
- AI-produced evidence judgements remain provisional until human validation.
- When semantic embeddings or AI review are enabled, relevant organisational evidence is sent to the configured external AI provider. Local-only mode keeps retrieval and manual review inside the application process.
- Do not upload evidence to an external provider unless the organisation is authorised to do so and applicable confidentiality/privacy requirements have been addressed.
- Never commit `.env`, API keys, production evidence, customer exports, or assessment snapshots containing sensitive metadata.

## Production hardening still required

The research build is not intended to be internet-exposed with sensitive customer data without additional controls including authentication, tenant isolation, encrypted persistence, secure secret storage, audit logging, rate limiting, malware/file validation, retention/deletion controls, dependency scanning, and deployment-specific threat modelling.
