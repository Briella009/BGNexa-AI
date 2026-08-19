# Architecture

```text
Organisation profile
        |
        v
Applicability engine ----------------------------------------+
        |                                                     |
        v                                                     |
Framework YAML packs                                         |
        |                                                     |
        +----------------------+                              |
                               v                              |
Evidence files -> parser -> hashed chunks -> retrieval index  |
                               |                              |
             +-----------------+-----------------+            |
             |                                   |            |
             v                                   v            |
        TF-IDF rank                    optional embedding rank |
             |                                   |            |
             +------------- RRF ------------------+            |
                               |                              |
                               v                              |
                      candidate evidence                      |
                               |                              |
                    +----------+----------+                    |
                    |                     |                    |
                    v                     v                    |
          prompt-injection gate   optional structured LLM      |
                    |                     |                    |
                    +----------+----------+                    |
                               v                              |
                     provisional finding                      |
                               |                              |
                               v                              |
                    human validation gate                     |
                               |                              |
                               v                              |
                    conservative scoring                      |
                               |                              |
           +-------------------+-------------------+           |
           v                   v                   v           |
       dashboard         grounded Copilot     exports/snapshot
```

## Retrieval design

The offline baseline is TF-IDF. When semantic embeddings are enabled, Stage 2 combines lexical and semantic ranks with reciprocal-rank fusion (RRF). RRF is used because lexical and embedding cosine scores are not assumed to be directly calibrated to the same scale.

If the semantic provider fails, the system records the failure and falls back to lexical retrieval instead of failing the assessment.

## Human-review boundary

Retrieval finds candidate evidence; it does not prove a control is satisfied. AI review is provisional. Human validation can resolve evidence judgements, but cannot override regulatory applicability to `not_applicable`.

Supported/partial human decisions require explicit confirmation of cited evidence.

## Copilot boundary

The Copilot is grounded in retrieved evidence plus project-authored framework summaries. Prompt-injection-flagged evidence is excluded from model context. The model is required to return citation IDs, and the application validates those IDs against the supplied context before rendering citations.

## Auditability

Evidence chunks receive SHA-256 content hashes. Assessment snapshots include framework versions, source-verification dates, findings, evidence references, reviewer records and a deterministic SHA-256 digest. The digest is tamper-evident only; it is not an identity signature.

## Stage 3 provenance and evaluation lane

Framework content and retrieval behaviour are now tested independently of the UI and external AI provider:

```text
framework YAML ---------------------> provenance audit -----+
       |                                                   |
       v                                                   v
seeded controls -> synthetic evidence -> TF-IDF eval -> CI quality gate
                                      |                    |
malicious evidence -----------------> security eval -------+
```

This lane is deliberately deterministic. It gives maintainers a stable regression baseline before optional embeddings or model-based review are introduced. The golden fixtures are synthetic and therefore measure repository regression quality, not general real-world compliance accuracy.

## DCPMI applicability lane

Nigeria privacy applicability is kept outside the LLM. A non-binding GAID Schedule 7 triage can suggest that a profile appears to trigger DCPMI designation and can surface a candidate UHL/EHL/OHL tier, but the user must explicitly confirm status and tier before those values affect assessment applicability. Registration exemptions and tier-sensitive CAR handling are separate inputs/rules so one decision cannot silently imply another.

## Private authority-file verification

CBN controls that were mapped from authority metadata plus archival full text remain machine-readable as `pending_direct`. A privately supplied original CBN PDF can be hashed and structurally checked with `scripts/verify_authority_pdf.py`. The verifier does not auto-upgrade framework provenance; a maintainer must manually review the authority file and then intentionally change the verification metadata.

## Stage 4 applicability and framework-type layer

Stage 4 adds a framework-type boundary above assessment so laws, regulatory frameworks, voluntary guidance and international standards remain distinguishable in UI/report outputs.

GDPR uses two separate concepts:

1. `triage_gdpr_article3()` - a non-binding fact triage that can identify explicit Article 3 indicators;
2. `gdpr_scope_status` - the confirmed human/legal determination used by the assessment engine.

The LLM cannot promote the first into the second. Similar explicit fields control conditional GDPR obligations (RoPA, DPIA, DPO, processor use and international transfers).

The NIST pack is a complete 106-subcategory Core outcome set, while the GDPR pack is intentionally a selected organisational readiness set. This distinction is preserved in framework metadata and reporting.

The crosswalk layer aggregates only shared capability tags and ranks potential evidence-reuse areas. It never mutates control status, applicability or framework scoring.
