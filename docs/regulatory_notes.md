# Regulatory and Framework Pack Notes

Verified: 2026-08-19.

## Nigeria Data Protection Act 2023

Authority: Nigeria Data Protection Commission (NDPC).

The open-source pack contains selected operational readiness checks, not the whole Act. It includes selected controller/processor obligations, rights, security, breach, transfer and DCPMI registration areas. Summaries are project-authored paraphrases with authority locators.

## NDPC GAID 2025

Authority: Nigeria Data Protection Commission (NDPC).

The GAID pack is treated as implementation guidance alongside the Act. The non-binding Schedule 7 DCPMI triage can surface indicators, but confirmed DCPMI status/tier remain explicit inputs.

Registration exemptions are not generalized across processing roles. The application also preserves an internal wording tension around Compliance Audit Return applicability by sending unresolved tier cases to human review rather than inventing certainty.

## CBN - Other Financial Institutions, 2022

Authority: Central Bank of Nigeria.

The 43-page June 2022 authority source was privately supplied as an image-only scan and fully rendered/reviewed. The source states a full-compliance effective date of January 1, 2023. The selected OFI pack contains 21 direct-source-verified controls with page references.

The source is visibly marked confidential, so it is not redistributed in this repository.

## CBN - DMBs / PSBs, 2024

Authority: Central Bank of Nigeria.

The May 2024 framework is maintained separately from the OFI pack. A privately supplied 61-page CBN authority PDF was directly reviewed, and the 30 selected controls include source page references. The authority PDF is not redistributed.

## ISO/IEC 27001:2022 + Amendment 1:2024

Authority: ISO/IEC.

The open-source pack contains project-authored clause-level readiness summaries only. It does not reproduce the standard or Annex A text. A supplied gap-assessment workbook is treated only as a private secondary aid, not as authority text. Formal conformity work requires lawful access to the actual ISO standard.

## NIST Cybersecurity Framework 2.0

Authority: National Institute of Standards and Technology (NIST).

The pack includes all 106 CSF 2.0 Core Subcategories. It is represented as voluntary, outcome-based guidance rather than a certification or legal compliance regime. Equal product weighting is used only for neutral readiness aggregation and does not imply NIST ranks the outcomes equally or establishes pass/fail thresholds.

## EU GDPR

Authority: European Union, official EUR-Lex regulation text.

The GDPR pack is intentionally a selected organisational readiness surface rather than an exhaustive legal checklist. Article 3 territorial scope is a separate confirmed input. The triage helper can flag explicit Article 3 triggers but cannot make a legal applicability determination.

Controller/processor role is resolved before conditional GDPR obligations. RoPA, DPIA, DPO, controller use of processors and international-transfer controls remain review-required until their applicability is confirmed.

## Source-quality policy

`scripts/audit_framework_sources.py` checks authority-domain provenance, verification states, dates and control source locators. Source identity must be established before any control is promoted to a direct-verification tier.
