# Assurance Workspace design

BGNexa AI v0.5 extends the readiness engine into an assurance/GRC workflow without turning the product into an automated auditor.

## Product intent

The readiness engine answers: **what does the supplied evidence currently support?**

The Assurance Workspace answers: **what should a reviewer do next, who owns it, what evidence is still needed, what testing was performed, and how was the issue closed?**

The design deliberately keeps those questions separate.

## Core principles

1. **Assessment status is not an audit finding.** A `not_evidenced`, `partially_supported` or `review_required` result creates review work. A finding only exists after a user records one.
2. **Supported controls still need assurance validation.** They are retained in the workplan as `Validate` tasks rather than silently disappearing.
3. **Applicability remains deterministic.** `not_applicable` controls are excluded from the assurance workplan because applicability is controlled by the organisation profile, not by AI or reviewer override.
4. **Evidence provenance survives the hand-off.** Work items retain evidence source names, hashes, quality flags, assessment rationale and source locator.
5. **Testing is reviewer-owned.** BGNexa proposes a test objective/procedure, but a qualified reviewer chooses the sample, performs the test and records the conclusion.
6. **Management response is separate from the reviewer conclusion.** The workspace gives each its own fields.
7. **Closure is explicit.** Workflow states include remediation, retest and closure rather than treating a recommendation as completed work.
8. **Public-beta audit trail is modestly described.** The current change log is append-only within the Streamlit session; it is not an immutable server audit log or proof of user identity.

## Workflow states

- `open`
- `evidence_requested`
- `under_review`
- `remediation_in_progress`
- `ready_for_retest`
- `closed`
- `risk_accepted`

## Test results

- `not_tested`
- `effective`
- `partially_effective`
- `ineffective`
- `inconclusive`

The test result is an assurance-workpaper field. It does not rewrite the legal/regulatory applicability model and does not by itself create an audit opinion.

## Finding severity

The workspace supports `low`, `moderate`, `high` and `critical` finding severity plus `none`. BGNexa does not auto-assign a finding severity from a readiness weight. That avoids confusing a product prioritisation weight with a formal risk rating.

## Evidence requests

Evidence requests are generated from the project-authored control summary and seeded evidence examples. They are designed to help control owners understand what kind of evidence would be useful. They must not be interpreted as new legal requirements.

## Test procedures

For controls that expect operational evidence, BGNexa suggests a procedure that asks the reviewer to:

- inspect design and current evidence;
- select a risk-based sample where appropriate;
- verify execution, approval, timeliness, exceptions and traceability;
- reconcile exceptions to remediation records;
- document the sample basis and conclusion;
- avoid inferring operating effectiveness from policy text alone.

For design/documentation controls, the suggested procedure focuses on ownership, approval, scope, version and corroborating implementation evidence where relevant.

## Snapshot linkage

The assurance JSON snapshot uses schema `bgnexa-assurance/v1` and records:

- engagement metadata;
- current work items;
- the assessment fingerprint;
- the linked readiness snapshot SHA-256;
- session audit events;
- its own SHA-256 digest.

The digest is tamper-evident only. It is not a digital signature and does not verify reviewer identity.

## Public-beta limitations

The current workspace is session-based and deliberately does not claim:

- durable multi-user projects;
- SSO or role-based access control;
- immutable server-side audit logging;
- production tenant isolation;
- cryptographic reviewer attestation;
- encrypted customer evidence persistence;
- workflow notifications/integrations;
- formal sampling-engine conclusions;
- an audit opinion.

Those belong to a production hosted edition rather than an open Streamlit demonstration.
