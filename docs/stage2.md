# Stage 2 - Grounded Retrieval, Human Validation and Copilot

Stage 2 changes the project from an assessment demo into a traceable review workflow.

## 1. Hybrid retrieval

`HybridEvidenceRetriever` combines:

- TF-IDF lexical retrieval, available offline; and
- optional semantic embeddings when an embedding provider is configured.

The two ranking systems are combined with reciprocal-rank fusion (RRF) rather than directly averaging incomparable score scales. If the embedding provider fails, the system records the error and safely falls back to lexical retrieval.

The default optional OpenAI embedding model is `text-embedding-3-small`. It can be changed with `OPENAI_EMBEDDING_MODEL`.

## 2. Human validation

Automated findings remain provisional until reviewed. A human reviewer may resolve a finding as:

- supported;
- partially supported;
- not evidenced; or
- review required.

A reviewer cannot mark a control `not_applicable`; applicability belongs to the organisation-profile/applicability engine.

To resolve a finding as supported or partially supported, the reviewer must:

1. have at least one cited evidence candidate;
2. explicitly confirm they inspected that evidence; and
3. provide their name and a rationale note.

## 3. Evidence-grounded Copilot

The Copilot receives only:

- the user's question;
- retrieved organisational evidence that has not been prompt-injection flagged; and
- relevant project-authored framework summaries.

It cannot determine framework applicability. Structured output is used for the answer and citation IDs. Citation IDs returned by the model are checked against the IDs actually supplied to the model; unknown IDs are discarded.

Without an API key, the same interface becomes an evidence explorer: it returns relevant source candidates and framework references but does not fabricate a generative conclusion.

## 4. Tamper-evident assessment snapshots

A JSON assessment snapshot records:

- organisation profile;
- framework IDs, versions, authorities and source-verification dates;
- framework scores;
- control states;
- evidence chunk IDs and hashes;
- AI/human review state; and
- reviewer validation records.

The snapshot includes a SHA-256 digest over its canonical JSON payload. This detects content changes; it is **not** a digital signature and does not prove reviewer identity.

## 5. Reporting

Stage 2 adds:

- a priority remediation/review queue;
- CSV control export;
- a portable executive HTML report; and
- JSON assessment snapshots.

`review_required` is deliberately labelled as a **review task**, not a confirmed gap.

## Offline smoke test

The core pipeline does not require Streamlit or the OpenAI SDK:

```bash
python scripts/smoke_stage2.py
```

This generates an HTML report, JSON snapshot and CSV priority queue under `demo_outputs/`.
