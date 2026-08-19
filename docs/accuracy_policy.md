# Accuracy and Trust Policy

BGNexa AI is designed to be conservative. A polished answer is less important than an answer that exposes uncertainty.

## Non-negotiable rules

1. **Readiness is not compliance.** The application reports evidence-backed readiness and never represents an automated score as legal compliance, ISO certification, CBN approval, or an audit opinion.
2. **Applicability is resolved outside the LLM.** Organisation type, CBN category, processing role, and DCPMI status are explicit profile inputs. Unknown scope remains `review_required`.
3. **Evidence is untrusted data.** Uploaded content is never treated as instructions. Prompt-like or malicious passages are flagged and blocked from automated judgement.
4. **No evidence means no credit.** A requirement without sufficiently relevant evidence is `not_evidenced`.
5. **Relevant text is not automatically proof.** Retrieval only identifies candidate evidence. Without AI review, candidates remain `review_required`.
6. **AI findings require human review.** Even `supported` AI findings are provisional evidence judgements.
7. **Unresolved controls cannot inflate readiness.** `review_required` controls are excluded from the resolved-score numerator and denominator; coverage is reported separately.
8. **Framework text is versioned and traceable.** Every framework and control records a source locator, verification status, and last-verified date.
9. **Unverified source detail is visible.** The CBN DMB/PSB 2024 seed pack remains explicitly marked as pending paragraph-level direct-authority verification.
10. **ISO copyright is respected.** The public pack uses original clause-level summaries and references, not licensed ISO/IEC 27001 or Annex A text.
11. **Human support decisions require evidence confirmation.** A reviewer cannot resolve a finding as supported/partial without cited evidence and an explicit confirmation step.
12. **Review tasks are not confirmed gaps.** `review_required` may reflect insufficient assessment coverage and is labelled separately from `not_evidenced`.
13. **Copilot citations are allow-listed.** Model-returned citation IDs are rendered only if they were actually supplied in the grounded context.
14. **Snapshots are tamper-evident, not identity-signed.** SHA-256 detects changed snapshot content but does not authenticate the reviewer.
15. **External AI is opt-in and visible.** Local retrieval/manual review is the default. Enabling semantic embeddings or AI review sends relevant evidence to the configured provider and must be authorised by the organisation.
16. **Profile changes invalidate reliance.** Material organisation-scope or framework-selection changes mark the existing assessment stale and disable validation/export until rerun.

## Scoring

For resolved, applicable controls only:

- supported = 1.0 x control weight
- partially supported = 0.5 x control weight
- not evidenced = 0 x control weight

`provisional_readiness = earned_weight / resolved_weight`

`coverage = resolved_weight / applicable_weight`

A high provisional readiness score with low coverage must not be interpreted as strong overall readiness.

## Production gate

Before real organisations rely on a framework pack, the pack should pass:

- direct-authority text verification;
- second-person control review;
- applicability review by a qualified practitioner;
- golden-set evidence evaluations;
- prompt-injection/adversarial testing;
- change monitoring for regulatory amendments;
- versioned release notes and source hashes where licensing permits.

## Stage 4 framework-type and scope rules

- A readiness percentage is always interpreted within its own framework pack. It is not a universal compliance score.
- NIST CSF 2.0 is represented as voluntary guidance, not certification.
- GDPR Article 3 scope is never decided by the LLM. Unknown scope produces `review_required`; confirmed out-of-scope produces `not_applicable` for the assessed scope.
- Conditional GDPR obligations (RoPA, DPIA, DPO, controller-side processor governance, international transfers) remain unresolved until a human-confirmed applicability field is supplied.
- Controller/processor role is resolved before conditional GDPR checks to avoid assigning controller-only review tasks to a processor-only profile.
- Cross-framework capability tags indicate potential evidence reuse only. They never declare controls equivalent or allow one framework's result to auto-satisfy another.
- Image-only authority documents require full render/visual review. Absence of a text layer is not itself a source-verification failure.
- Source files marked confidential or licensed are not redistributed in the repository.
