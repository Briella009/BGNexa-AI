# Stage 4 - International Expansion, Applicability Guardrails and Evidence Reuse

Stage 4 expands the Copilot from a Nigeria-first readiness engine into a multi-jurisdiction product while preserving strict separation between laws, regulatory frameworks, voluntary guidance and certification standards.

## Delivered

### 1. CBN OFI 2022 direct source closure

The correct 43-page CBN OFI document was supplied privately as an image-only PDF and visually reviewed across all pages. The project records its SHA-256, page count and control-to-page mappings without bundling the source file. Because the source is visibly marked confidential, it is intentionally excluded from the public repository.

The OFI seed pack now contains 21 directly verified selected controls covering governance, CISO responsibilities, policy review, risk assessment, annual self-assessment, cyber-threat intelligence, quarterly reporting, 24-hour incident reporting, regulatory compliance, access control, secure configuration, awareness, data security, secure SDLC, vulnerability management, privileged/vendor access, monitoring, and incident response/recovery.

### 2. NIST CSF 2.0

A complete machine-readable pack of all 106 CSF 2.0 Core Subcategories is included. NIST is represented as a voluntary framework, not a certification or legal regime. All outcomes receive equal product weight so the product does not imply NIST ranks Core outcomes by importance.

### 3. GDPR organisational readiness pack

The GDPR pack contains 18 selected high-value readiness areas rather than pretending to provide exhaustive legal coverage. It covers principles/accountability, lawful basis, transparency, rights operations, controller accountability, privacy by design/default, processor governance, RoPA, security, breach response, DPIA, DPO and Chapter V international transfers.

Article 3 territorial scope is never delegated to the LLM. A non-binding triage helper identifies explicit Article 3 triggers, but confirmed scope must be recorded separately. Conditional obligations (RoPA, DPIA, DPO, processor use and international transfer) also remain human-confirmed profile inputs.

### 4. Framework-type separation

Every framework now carries a `framework_type`. UI and reports expose the type so evidence-readiness scores are not presented as interchangeable across:

- laws;
- regulatory implementation guidance;
- regulatory frameworks;
- international standards; and
- voluntary frameworks.

### 5. Potential evidence reuse view

The crosswalk now ranks shared capability topics by number of frameworks and mapped controls. This helps identify potential evidence reuse while explicitly rejecting a claim of control equivalence.

### 6. Stage 4 deterministic evaluation

The golden retrieval suite now includes 66 cases across Nigerian privacy, both CBN packs, ISO summaries, GDPR and NIST. Current regression results:

- Recall@1: 0.9848
- Recall@3: 1.0000
- MRR: 0.9924
- provenance errors: 0
- provenance warnings: 0
- prompt-injection/Copilot exclusion: pass

These are synthetic regression results, not real-world compliance accuracy claims.

## Product trust boundaries

1. Retrieval is not proof of control satisfaction.
2. AI evidence judgement remains reviewable.
3. Legal/regulatory applicability is deterministic/human-confirmed.
4. Readiness is not compliance.
5. Shared capability is not legal/control equivalence.
6. Private/confidential/licensed framework source files are not redistributed.
7. Unknown applicability reduces coverage instead of inflating readiness.

## Next evaluation stage

The next quality milestone should use a larger anonymised policy corpus with intentionally conflicting, stale, incomplete and misleading evidence. Measure at least:

- retrieval recall/precision;
- false-support rate;
- false-gap rate;
- citation correctness;
- applicability guardrail failure rate;
- human reviewer agreement;
- robustness against prompt injection and policy-text manipulation.
