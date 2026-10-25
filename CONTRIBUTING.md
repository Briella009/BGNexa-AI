# Contributing to BGNexa AI

Thanks for helping improve BGNexa AI.

The most useful contributions are small, reviewable changes that strengthen evidence quality, framework traceability, tests, usability, or security without overstating compliance.

## Good contribution areas

- add or improve unit tests for applicability, evidence quality, scoring, review, or reporting;
- improve framework-source verification and provenance;
- add safe synthetic/demo evidence cases;
- improve documentation, setup instructions, or accessibility;
- strengthen privacy, file-handling, prompt-injection, or deployment safeguards;
- improve deterministic retrieval/evaluation;
- fix bugs with a reproducible test case.

## Before you start

1. Fork the repository.
2. Create a focused branch.
3. Keep customer, employer, regulator-confidential, or personal evidence out of the repository.
4. Do not paste copyrighted standards text that cannot legally be redistributed.
5. Add or update tests when behaviour changes.
6. Run the relevant quality checks.

```bash
pip install -r requirements-core.txt
pytest -q
python scripts/audit_framework_sources.py --strict
python scripts/run_evals.py --strict
```

## Pull requests

A strong PR should explain:

- the problem;
- the change;
- how it was tested;
- any security/privacy implications;
- any limitations or claims that remain unsupported.

Prefer one coherent improvement per PR.

## Claim discipline

Do not describe BGNexa as certifying compliance, issuing audit opinions, providing legal advice, or replacing qualified human judgement.

External AI-generated assessments remain proposals until the workflow records appropriate human review.

## Security reports

Do not disclose exploitable vulnerabilities, credentials, API keys, or sensitive evidence in public issues or pull requests. Follow `SECURITY.md` for security-reporting guidance.
