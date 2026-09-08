# BGNexa AI public beta launch checklist

## Product

- [x] Evidence-backed readiness engine
- [x] Human validation and reviewer rationale
- [x] Evidence provenance, evidence type and freshness register
- [x] Prompt-injection blocking for automated evidence judgement
- [x] Assessment-aware evidence-grounded Copilot
- [x] Priority remediation queue
- [x] Cross-framework evidence-reuse view with non-equivalence guardrail
- [x] Assurance Workspace for evidence requests, control testing, findings/actions, retest and closure
- [x] Public Beta Guide page
- [x] Bright product UI foundation and mobile-aware layout
- [x] AI provider cooldown/circuit breaker for transient/rate-limit failures

## Quality and trust

- [x] Automated regression suite
- [x] Framework provenance audit
- [x] Deterministic retrieval evaluation
- [x] Offline smoke tests
- [x] Streamlit entrypoints included in Python compile CI
- [x] Explicit read-only GitHub Actions token permission
- [x] Workflow concurrency cancellation
- [x] CI job timeout
- [ ] Require passing CI before direct changes to `main` via GitHub branch protection/ruleset

## Beta positioning

- [x] Product describes evidence-backed readiness rather than legal compliance
- [x] Audit/GRC workflow does not auto-create findings from readiness gaps
- [x] Human/legal applicability decisions remain outside the LLM
- [x] ISO content remains clause-level/reference-only in the public repository
- [x] Public beta data-safety guidance is visible
- [x] Session-based beta limitation is disclosed
- [x] LinkedIn launch copy prepared

## Manual repository-admin action still required

The connected GitHub integration currently exposes repository code/PR actions but not ruleset or branch-protection writes. In GitHub repository settings, configure `main` so that:

1. changes require a pull request before merge;
2. the `test` status check must pass;
3. force pushes are blocked;
4. branch deletion is blocked;
5. administrators should follow the same rule during the public beta unless an emergency bypass process is intentionally documented.

Do not describe branch protection as enabled until this repository-admin setting has actually been applied.
