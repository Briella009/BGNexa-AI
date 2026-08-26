# Evidence Quality, Source Registry and Freshness

BGNexa v0.4.4 keeps document provenance, retrieval relevance and proof quality as separate signals.

## Why it exists

Retrieval relevance is not the same as proof quality. A policy can mention a control without proving that the control was executed, an old test report may no longer demonstrate the present state, and an uploaded file should not disappear simply because retrieval did not select it for a particular control.

BGNexa therefore keeps two layers:

1. a **document-level source registry** for every supplied file; and
2. **retrieved evidence matches** used for individual framework controls.

## Source registry

Every supplied source receives a document-level record containing:

- source filename;
- full-document SHA-256;
- file size and extension;
- parse status (`parsed`, `parsed_no_text`, or `parse_error`);
- number of indexed chunks;
- primary evidence type plus secondary evidence-type tags;
- document date and the exact date source;
- age and freshness status;
- evidence-quality flags; and
- prompt-injection flag where applicable.

After an assessment, the register also identifies whether a source was `retrieved` for at least one assessed control or was `indexed_not_retrieved`. This distinction prevents a valid uploaded document from silently disappearing from the UI simply because it was not relevant to the current framework/control set.

The tamper-evident JSON assessment snapshot stores these source records independently of retrieved chunks. A separate evidence-register CSV can also be exported.

## Evidence types

The classifier is deliberately rules-based and conservative:

- `documented_intent` - policy, procedure, standard, runbook, playbook or guideline;
- `operational_record` - registers, logs, tickets, minutes, tracked actions and other records of performed activity;
- `technical_evidence` - configurations, system exports and security-control outputs;
- `audit_test_evidence` - audit reports, assessments, scans, penetration tests and exercise results;
- `regulatory_filing` - filing acknowledgements, submission receipts and registration/return proof;
- `contractual_evidence` - contracts, DPAs, supplier agreements and SLAs;
- `training_evidence` - attendance and completion records; and
- `unknown` - no deterministic rule matched.

A mixed artefact may expose more than one evidence-type tag. For example, an operational record can contain both training-completion evidence and internal-audit test results. Its primary classification remains conservative, while the secondary tags are preserved for reviewers and AI context.

Policy/procedure filename or title identity takes precedence over incidental references to records inside the document. Conversely, an explicit `Record type: Operational record` is treated as evidence of performed activity rather than flattened into policy intent.

Negative limitation sections are excluded from positive evidence classification so text such as “this pack does not include a registration certificate” cannot turn a normal evidence file into a false `regulatory_filing`.

Classification is an aid to review, not a legal characterisation of a document.

## Document dates

BGNexa uses only dates it can justify. It first looks for labelled dates, with document-identity dates prioritised over incidental review dates. Examples include:

- `Effective / record date`;
- `Record date`;
- `Effective date`;
- `Assessment date`;
- `Document date`;
- `Issued`;
- `Approved`;
- `Last reviewed` / `Review date`; and
- generic labelled `Date`.

If no reliable labelled date is present, an explicit `YYYY-MM-DD` (or equivalent separator) in the filename is used as a traceable fallback and recorded as `filename:date`. PDF/DOCX embedded metadata is a later fallback. Unlabelled dates appearing elsewhere in content are not assumed to be the document date.

## General freshness signal

- `current`: 0-365 days old
- `aging`: 366-730 days old
- `stale`: more than 730 days old
- `unknown`: no reliable date, a future-dated document, or an unreadable source

This is a product-level signal only. Framework-specific evidence-review cycles, record-retention periods and statutory deadlines take precedence.

## Automated guardrails

Two deterministic caps apply after an AI evidence judgement:

1. If every supporting candidate is stale, an AI-proposed `supported` result is reduced to `partially_supported`.
2. If a requirement expects operational implementation evidence and every retrieved candidate is only documented intent, an AI-proposed `supported` result is reduced to `partially_supported`.

The reviewer remains responsible for final validation. The guardrails do not assign legal compliance, ISO certification or regulatory applicability.
