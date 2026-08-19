# Changelog

## v0.4.1

- Added Groq as an optional free-tier-friendly generation provider through the existing OpenAI-compatible client.
- Added automatic provider selection with `AI_PROVIDER`, `GROQ_API_KEY`, and `GROQ_MODEL`.
- Kept OpenAI embeddings optional and independent from Groq generation.
- Preserved deterministic/manual-review behavior when no provider key is configured.
- Added provider-selection regression tests.

## 0.4.0 - 2026-08-19

- Rebranded the product as **BGNexa AI** with the tagline "Turn evidence into readiness."
- Identified the newly supplied 43-page PDF as the correct CBN OFI 2022 framework rather than ISO/IEC 27001.
- Completed full rendered visual verification of the image-only CBN OFI source and recorded its SHA-256 without redistributing the confidential PDF.
- Expanded the directly verified CBN OFI selected-control pack to 21 controls with source-page mappings.
- Added image-only authority-document verification handling so lack of a text layer triggers manual visual review rather than false rejection.
- Added the complete NIST CSF 2.0 Core surface with 106 Subcategories and explicit `voluntary_framework` classification.
- Added an 18-control selected GDPR organisational readiness pack sourced to the official regulation.
- Added conservative GDPR Article 3 triage plus human-confirmed scope, controller/processor role, RoPA, DPIA, DPO, processor-use and international-transfer applicability guardrails.
- Added framework-type display to source panels, dashboard/report exports and tamper-evident snapshots.
- Expanded cross-framework mapping into ranked potential evidence-reuse opportunities while preserving a strict non-equivalence disclaimer.
- Expanded golden retrieval evaluation from 45 to 66 cases across Nigerian, CBN, ISO, NIST and GDPR packs.
- Stage 4 deterministic metrics: Recall@1 98.48%, Recall@3 100%, MRR 0.9924; 0 provenance errors/warnings; security checks passing.
- Expanded automated tests from 46 to 62.

## 0.3.1 - 2026-08-19

- Directly verified the 61-page CBN DMB/PSB May 2024 authority PDF supplied privately by the user.
- Upgraded all 30 seeded CBN DMB/PSB controls to `direct_authority_pdf_verified` and added source PDF page references.
- Recorded the verified DMB/PSB authority-file SHA-256 in the source registry without redistributing the PDF.
- Added source-page display support in the framework result UI.
- Added provenance handling and regression tests for the direct-authority verification tier.
- Hardened the authority verifier so failed files emit explicit rejection metadata and missing-marker details rather than pass-oriented boilerplate.
- Rejected a mislabeled OFI 2022 upload after structural/rendered inspection showed that it was a 2021 financial-sector regulatory digest rather than the CBN OFI framework.
- Classified the supplied ISO 27001 gap-assessment workbook as a private secondary implementation aid only; it does not replace authoritative ISO source verification.
- Kept the automated suite at 46 passing tests after the provenance upgrade.

## 0.3.0 - 2026-08-19

- Expanded the NDPA 2023 seed pack to 18 selected operational readiness controls.
- Expanded the NDPC GAID 2025 seed pack to 12 selected implementation controls.
- Added a non-binding GAID Schedule 7 DCPMI triage with conservative boundary handling.
- Added confirmed UHL/EHL/OHL tier inputs, registration-exemption handling and tier-sensitive applicability.
- Preserved the GAID Article 7(c) / Article 10(6) CAR wording tension by requiring human review for OHL CAR applicability.
- Expanded the CBN DMB/PSB 2024 preview from 14 to 30 selected controls while keeping all direct-file verification warnings visible.
- Added a private CBN authority-PDF structural verifier with SHA-256 recording.
- Added explicit provenance tiers and a framework-source audit CLI.
- Expanded the deterministic evaluation set to 45 golden retrieval cases across NDPA, GAID, CBN and ISO packs.
- Added deterministic Recall@1, Recall@3 and MRR evaluation plus prompt-injection/Copilot-context security regression checks.
- Added Stage 3 quality gates to GitHub Actions CI and a Stage 3 smoke runner.
- Corrected documentation mapping: NDPA section 40 covers personal-data breaches, sections 41-43 cover cross-border transfers, and section 44 covers DCPMI registration.
- Expanded automated tests from 26 to 46.

## 0.2.0 - 2026-08-19

- Added hybrid TF-IDF + optional embedding retrieval using reciprocal-rank fusion.
- Added safe lexical fallback when semantic retrieval is unavailable.
- Added evidence chunk SHA-256 hashes.
- Added human validation with evidence-confirmation guardrails and reviewer audit fields.
- Added evidence-grounded Copilot with prompt-injection exclusion and citation allow-listing.
- Added priority remediation/review queue.
- Added executive HTML export.
- Added tamper-evident JSON assessment snapshots.
- Added offline core smoke runner independent of Streamlit/OpenAI.
- Expanded automated tests from 14 to 26.
