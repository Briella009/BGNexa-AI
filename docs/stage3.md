# Stage 3 - Regulatory Provenance and Evaluation

Stage 3 makes accuracy claims testable. It does not attempt to prove legal compliance or claim that a synthetic benchmark represents real organisational performance.

## What Stage 3 adds

### 1. Source-provenance audit

Every framework has an authority, source URL and verification date. Every seeded control has a source locator, project-authored requirement summary and verification status.

`src/provenance.py` converts those statuses into explicit tiers:

- `authority_traceable` - traced to authority-published text, a directly verified authority PDF, or official ISO references;
- `authority_metadata_plus_archival_text` - authority publication is identified and text was cross-checked through an archival reproduction where direct retrieval was limited;
- `authority_metadata_plus_secondary_text_pending_direct` - authority metadata is known, but direct paragraph-level authority-file verification remains incomplete.

Run:

```bash
python scripts/audit_framework_sources.py --strict
```

Strict mode fails on provenance errors. A disclosed `pending_direct` state remains a warning for any pack that still lacks direct verification; directly verified authority-PDF controls produce no pending-direct warning.

### 2. Expanded Nigerian privacy packs

The NDPA seed pack now includes selected operational checks covering principles/accountability, lawful basis, consent, transparency, DPIA, processor governance, sensitive data, children/legal capacity, DPO governance, data-subject rights, security, breach management and international transfers.

The GAID pack now includes selected checks covering compliance governance, documented DCPMI designation assessment, registration, compliance audit/return, DPO designation and independence, DPO reporting, security monitoring, training, breach readiness and data-processing agreements.

Stage 3 adds a non-binding Schedule 7 DCPMI triage, tier-aware applicability, and registration-exemption handling. The triage never auto-confirms DCPMI status: the confirmed status/tier remain explicit organisation-profile inputs and the Copilot does not make the legal classification. Exact Schedule 7 volume-boundary cases that are not expressly allocated by the source wording are left for human confirmation.

For CAR filing, the app deliberately preserves the wording tension between GAID Article 7(c) (UHL/EHL) and Article 10(6) (broader DCPMI wording). OHL applicability is therefore `review_required` rather than guessed.

### 3. Deterministic golden retrieval suite

`evals/retrieval_cases.yaml` links framework controls to synthetic evidence documents under `evals/fixtures/`. The baseline evaluates the local TF-IDF retriever without depending on an external model or API.

Metrics:

- Recall@1 - expected evidence appears first;
- Recall@3 - expected evidence appears in the top three;
- MRR - rewards higher ranking of the expected evidence.

Current controlled benchmark:

- 45 golden cases;
- Recall@1: 100%;
- Recall@3: 100%;
- MRR: 1.000.

These figures apply only to the included synthetic fixtures. They are regression metrics, not a claim of 100% accuracy on real policies, regulations or audits.

### 4. Security evaluation

Stage 3 includes a malicious evidence fixture. The deterministic security evaluation verifies that:

1. the fixture is flagged for prompt injection; and
2. flagged evidence is excluded from offline Copilot citations/context.

### 5. CI quality gates

GitHub Actions now runs:

```text
compile
  -> unit/integration tests
  -> provenance audit
  -> deterministic retrieval/security evaluation
  -> Stage 2 offline product smoke test
  -> Stage 3 quality smoke test
```

The evaluation gate currently requires:

- Recall@3 >= 0.90;
- MRR >= 0.75;
- zero provenance errors;
- security evaluation pass.

## Current provenance status

At the Stage 3.1 checkpoint there are 5 framework packs and 79 seeded controls. The CBN DMB/PSB pack contains 30 selected controls covering governance, CISO, risk treatment, recovery, threat intelligence, access control/MFA, PAM, configuration, application/data security, cloud, patching, SOC/logging, incident exercises/forensics and AI-enabled-system security.

On 2026-08-19 a privately supplied 61-page copy of the CBN May 2024 DMB/PSB authority PDF was structurally verified, rendered and manually cross-checked. All 30 seeded DMB/PSB controls now carry `direct_authority_pdf_verified` plus source PDF page references. The verified file SHA-256 is recorded in the source registry; the regulator PDF itself is not redistributed.

The provenance audit therefore reports 0 errors and 0 pending-direct warnings for this pack. This closes the source-verification gap for the selected controls, but it does **not** mean the 30-control seed pack is an exhaustive reproduction of every CBN requirement.

A separately supplied file labeled as the CBN OFI 2022 framework failed verification and was rejected because its actual content was a 2021 financial-sector regulatory digest. The OFI pack consequently remains at its existing archival-text provenance tier until the correct CBN authority PDF is obtained.

## Evaluation limitations

A high deterministic benchmark can still miss real-world failure modes. Production evaluation should later add:

- anonymised, legally shareable real-world policy samples;
- paraphrase/adversarial retrieval cases;
- contradictory evidence;
- stale/superseded policies;
- multilingual evidence where relevant;
- tables and scanned PDFs;
- inter-reviewer agreement measurements;
- false-support and false-gap rates;
- model-version regression tests when AI review is enabled.

The intended standard is evidence-backed, inspectable and conservative behaviour, not an unsupported claim that the system can autonomously determine compliance.
