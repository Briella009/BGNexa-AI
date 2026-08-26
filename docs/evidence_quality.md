# Evidence Quality and Freshness

BGNexa v0.4.3 adds a deterministic evidence-quality layer before readiness results are presented.

## Why it exists

Retrieval relevance is not the same as proof quality. A policy can mention a control without proving that the control was executed, and an old test report may no longer demonstrate the present state. BGNexa therefore keeps retrieval score, evidence type and freshness as separate signals.

## Evidence types

The classifier is deliberately rules-based and conservative:

- `documented_intent` - policy, procedure, standard, runbook, playbook or guideline;
- `operational_record` - registers, logs, tickets, minutes and review records;
- `technical_evidence` - configurations, system exports and security-control outputs;
- `audit_test_evidence` - audit reports, assessments, scans, penetration tests and exercise results;
- `regulatory_filing` - filing acknowledgements, submission receipts and registration/return evidence;
- `contractual_evidence` - contracts, DPAs, supplier agreements and SLAs;
- `training_evidence` - attendance and completion records;
- `unknown` - no deterministic rule matched.

Classification is an aid to review, not a legal characterisation of the document.

## Document dates

BGNexa uses only dates it can justify. It first looks for labelled dates such as `Approved`, `Effective`, `Issued`, `Reviewed`, `Last reviewed`, `Document date` or `Date`. If no labelled date is present, PDF/DOCX metadata may be used. Unlabelled dates appearing elsewhere in content are not assumed to be the document date.

## General freshness signal

- `current`: 0-365 days old
- `aging`: 366-730 days old
- `stale`: more than 730 days old
- `unknown`: no reliable date, or the extracted date is in the future

This is a product-level signal only. Framework-specific evidence-review cycles, record-retention periods and statutory deadlines take precedence.

## Automated guardrails

Two deterministic caps apply after an AI evidence judgement:

1. If every supporting candidate is stale, an AI-proposed `supported` result is reduced to `partially_supported`.
2. If a requirement expects operational implementation evidence and every retrieved candidate is only documented intent, an AI-proposed `supported` result is reduced to `partially_supported`.

The reviewer remains responsible for final validation. The guardrails do not assign legal compliance or regulatory applicability.
