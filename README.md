# BGNexa AI

**Turn evidence into readiness.**

BGNexa AI is a source-traceable evidence intelligence platform for cybersecurity, privacy and regulatory readiness across Nigerian and international frameworks.

**Current release: v0.4.4**

The project currently supports:

- Nigeria Data Protection Act 2023 - selected operational readiness provisions
- NDPC GAID 2025 - selected implementation provisions with DCPMI applicability guardrails
- CBN Risk-Based Cybersecurity Framework for Other Financial Institutions (OFIs), 2022 - 21 directly verified selected controls
- CBN Risk-Based Cybersecurity Framework for DMBs & PSBs, 2024 - 30 directly verified selected controls
- ISO/IEC 27001:2022 + Amendment 1:2024 - clause-level readiness summaries without redistributing ISO text
- NIST Cybersecurity Framework (CSF) 2.0 - complete 106-subcategory Core outcome pack
- EU GDPR - 18 selected high-value organisational readiness obligations with conservative Article 3 applicability handling

> **Important:** this project reports evidence-backed readiness. It does not determine legal compliance, certify ISO/IEC 27001 conformity, provide regulator approval, or replace qualified legal/privacy/cybersecurity/audit review.

## Why this project is different

The engine separates six problems that basic compliance chatbots often mix together:

1. framework applicability;
2. evidence retrieval;
3. AI evidence judgement;
4. uncertainty and human review;
5. readiness scoring;
6. cross-framework evidence reuse.

A document mentioning a control topic is not automatically treated as proof that the requirement is satisfied. Legal/regulatory scope is kept outside the LLM.

## Core features

- Framework-specific applicability instead of a generic compliance checklist
- NDPA + NDPC GAID with non-binding Schedule 7 DCPMI triage, tier-aware applicability and registration-exemption handling
- Separate CBN OFI and DMB/PSB framework packs
- Direct source-page verification metadata for both CBN packs; source PDFs are not redistributed
- ISO/IEC 27001 clause-level readiness without publishing copyrighted standard text
- Complete NIST CSF 2.0 Core outcome surface (106 Subcategories)
- GDPR Article 3 territorial-scope triage kept separate from confirmed legal scope
- Human-confirmed GDPR conditional applicability for RoPA, DPIA, DPO, processor relationships and international transfers
- PDF, DOCX, TXT and Markdown evidence ingestion
- Hybrid retrieval: local TF-IDF plus optional semantic embeddings with reciprocal-rank fusion
- Safe lexical fallback if embeddings are unavailable
- Optional structured-output AI evidence reviewer
- Prompt-injection detection and automated-review blocking
- Provisional readiness **plus separate resolved coverage**
- Human validation with evidence-confirmation guardrails
- Deterministic evidence-type classification and freshness metadata
- Document-level evidence registry: every supplied source remains visible even when no control retrieves it
- SHA-256 provenance, file size, parse status and source-format metadata for every supplied evidence document
- Filename date fallback for evidence named with an explicit `YYYY-MM-DD` date when content does not expose a reliable document date
- Composite evidence-type tags so operational artefacts can retain training/audit/technical signals without being flattened into policy intent
- Automated quality caps: stale-only evidence and policy-only proof for operational requirements cannot resolve as fully supported
- Assessment-aware evidence-grounded Copilot with citation allow-listing; current scores, control states, human validations and priority gaps are supplied as read-only context for assessment questions
- Priority remediation/review queue
- Cross-framework capability map and potential evidence-reuse view
- CSV, executive HTML and tamper-evident JSON snapshot export
- Authority-domain and verification-tier provenance audit
- Deterministic retrieval and security regression suite
- GitHub Actions quality gates

## Framework types stay separate

The product deliberately labels each pack by source type:

| Pack | Type |
|---|---|
| NDPA 2023 | Law |
| NDPC GAID 2025 | Regulatory implementation guidance |
| CBN OFI 2022 | Regulatory framework |
| CBN DMB/PSB 2024 | Regulatory framework |
| ISO/IEC 27001 | International standard |
| NIST CSF 2.0 | Voluntary framework |
| GDPR | Law |

A readiness percentage inside one pack is therefore **not** treated as interchangeable with another pack and is never described as certification or legal compliance.


## Free-tier AI option (Groq)

BGNexa can run without any API key in deterministic retrieval/manual-review mode. For optional generation, it also supports Groq through its OpenAI-compatible API. When only Groq is configured, generation can be enabled while semantic embeddings stay on the local TF-IDF fallback.

```env
AI_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Never commit real API keys. On Streamlit Community Cloud, store them in **App settings → Secrets**. External-AI mode sends only the retrieved evidence selected for the request to the configured generation provider.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

The app works without an API key. Without AI review, retrieved candidates stay `review_required` until a person validates them. Without embeddings, retrieval safely uses local TF-IDF.

Core checks can run without Streamlit or the OpenAI SDK:

```bash
pip install -r requirements-core.txt
pytest -q
python scripts/audit_framework_sources.py --strict
python scripts/run_evals.py --strict
python scripts/smoke_stage4.py
```

For optional AI review/semantic retrieval:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.6
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

When external AI mode is enabled, relevant evidence may be sent to the configured provider. Do not submit evidence you are not authorised to process externally.

## Assessment states

| State | Meaning |
|---|---|
| `supported` | Evidence supports the requirement, subject to human validation |
| `partially_supported` | Evidence covers a material subset of the requirement |
| `not_evidenced` | Sufficient evidence was not found or a reviewer confirmed the gap |
| `review_required` | Scope/evidence cannot safely be resolved automatically |
| `not_applicable` | Explicit non-AI applicability logic determines the control is out of scope |

## Evidence quality and freshness

BGNexa now records evidence quality separately from retrieval relevance. Each uploaded source is conservatively classified as one of:

- documented intent (policy, procedure, standard, runbook);
- operational record;
- technical evidence;
- audit/test evidence;
- regulatory filing;
- contractual evidence;
- training evidence; or
- unknown.

Where an explicit document date can be extracted from a labelled field such as `Record date`, `Assessment date`, `Approved`, `Effective`, `Issued`, `Reviewed` or `Date`, the app exposes a general freshness signal. If content does not expose a reliable date, an explicit `YYYY-MM-DD` date in the filename is used as a traceable fallback; PDF/DOCX metadata remains a later fallback.

- `current`: 0-365 days old;
- `aging`: 366-730 days old;
- `stale`: more than 730 days old;
- `unknown`: no reliable date, or a future-dated document.

These thresholds are a product-level evidence-age heuristic, **not** a substitute for framework-specific review, retention, recertification or regulatory deadlines. Unknown dates are never invented. Filename-derived dates are visibly marked with `filename:date`. A stale-only evidence set cannot produce an automated `supported` result, and policy/procedure evidence cannot by itself prove an operational requirement where the control expects records, logs, tests, configurations, filings or similar implementation proof.

The evidence register is document-level rather than retrieval-only. A parsed source that is not selected by retrieval is shown as `indexed_not_retrieved`; an unreadable source is shown as `parsed_no_text` or `parse_error`. This prevents an uploaded document from silently disappearing simply because it was not relevant to the selected controls. The tamper-evident JSON snapshot includes the source-level provenance records, and the UI exposes a separate evidence-register CSV export.

## Scoring model

The dashboard intentionally shows two values:

**Provisional readiness** = evidence-weight earned / resolved applicable weight.

**Resolved coverage** = resolved applicable weight / all applicable weight.

`review_required` controls do not inflate readiness. If applicability is unresolved, the app exposes that uncertainty rather than producing an artificially reassuring score.

## Applicability guardrails

### Nigeria / NDPC

The app distinguishes controller, processor and mixed roles. DCPMI status and tier are confirmed profile fields. Schedule 7 triage is advisory only and cannot silently change legal applicability.

### CBN

OFIs use the 2022 pack. DMBs/PSBs use the 2024 pack. The application does not merge those regimes into one generic CBN score.

### GDPR

Article 3 territorial scope is a confirmed human/legal input. A separate triage helper can identify explicit Article 3 indicators, but the AI cannot convert that triage into a legal scope determination. Conditional obligations such as Article 30 RoPA, Article 35 DPIA, Article 37 DPO and Chapter V transfers also remain explicit applicability decisions.

### ISO

The public repository uses project-authored clause-level summaries and official ISO references. It does not include the ISO standard or Annex A control text.

## Cross-framework evidence reuse

Controls use shared capability tags such as `risk_assessment`, `incident_response`, `governance`, `data_security`, `access_control` and `third_party_risk`.

The dashboard ranks high-overlap capability areas to help a team ask: **can one evidence set support review across multiple frameworks?** This is an efficiency hint only, not a declaration that requirements are equivalent.

## AI security

Uploaded documents are treated as untrusted data. The system:

- flags common prompt-injection patterns;
- excludes flagged passages from Copilot evidence context;
- blocks unsafe automated evidence judgement;
- never delegates legal/regulatory applicability to the LLM;
- uses structured outputs for evidence assessment;
- keeps human validation and reviewer rationale in the snapshot.

## Repository layout

```text
.
├── app.py
├── frameworks/
│   ├── eu/
│   ├── international/
│   ├── nigeria/
│   └── source_registry.yaml
├── src/
│   ├── applicability.py
│   ├── authority_verify.py
│   ├── assessor.py
│   ├── copilot.py
│   ├── crosswalk.py
│   ├── dcpmi.py
│   ├── gdpr.py
│   ├── evaluation.py
│   ├── evidence.py
│   ├── evidence_quality.py
│   ├── framework_loader.py
│   ├── provenance.py
│   ├── report.py
│   ├── retriever.py
│   ├── review.py
│   ├── scoring.py
│   └── security.py
├── scripts/
│   ├── audit_framework_sources.py
│   ├── run_evals.py
│   ├── smoke_stage2.py
│   ├── smoke_stage3.py
│   ├── smoke_stage4.py
│   └── verify_authority_pdf.py
├── sample_data/
├── evals/
├── tests/
└── docs/
```

## Stage 4 quality gate

Current deterministic checkpoint:

- **76 automated tests passing**
- **7 framework packs**
- **213 seeded controls/outcomes**
- **106 NIST CSF 2.0 Subcategories**
- **18 selected GDPR readiness controls**
- **21 directly verified CBN OFI controls**
- **30 directly verified CBN DMB/PSB controls**
- **66 golden retrieval cases**
- **Recall@1: 98.48%**
- **Recall@3: 100%**
- **MRR: 0.9924**
- **0 provenance errors**
- **0 provenance warnings**
- prompt-injection/Copilot evidence-exclusion checks passing

The retrieval metrics are measured on synthetic repository fixtures. They are regression metrics, **not** a claim of 100% real-world assessment accuracy.

## Source verification status

- NDPA 2023: selected provisions traced to NDPC-published Act material.
- NDPC GAID 2025: selected implementation provisions traced to NDPC-published GAID material.
- CBN OFI 2022: correct 43-page image-only authority document privately supplied, fully rendered/reviewed, source hash recorded, and 21 seeded controls linked to PDF pages. The source is marked confidential and is not redistributed.
- CBN DMB/PSB 2024: 61-page authority PDF privately supplied and directly reviewed; 30 seeded controls link to PDF pages. The PDF is not redistributed.
- ISO/IEC 27001: official ISO reference metadata only in the public pack; no licensed standard text is included. A previously supplied gap-assessment workbook remains a private secondary aid, not authority text.
- NIST CSF 2.0: complete Core outcome pack derived from the final NIST CSF 2.0 publication and source-traceable identifiers.
- GDPR: selected organisational readiness controls traced to the official EUR-Lex regulation; not an exhaustive legal checklist.

See `docs/source_verification_2026-08-19.md`, `docs/regulatory_notes.md`, `docs/accuracy_policy.md` and `docs/stage4.md`.

## Roadmap

- Real anonymised policy corpus evaluation, including false-support/false-gap measurement
- Framework-specific evidence expiry/supersession rules and superseded-document handling
- Framework-version diffing and update alerts
- More granular GDPR/NIST/CBN crosswalk review with human-approved mappings
- Cryptographically signed reviewer attestations/identity integration
- DOCX/PDF board-ready reports
- Multi-tenant hosted edition with encrypted storage and audit logs

## Security

See `SECURITY.md` before using real organisational evidence or exposing the application externally.

## License

MIT for the software. Third-party laws, regulations and standards retain their own applicable rights and terms. ISO standards are not included in this repository.
