# Private Source Verification Record - 2026-08-19

This record documents verification outcomes without redistributing privately supplied source files.

## CBN DMB/PSB 2024

- Expected source: Central Bank of Nigeria, *Risk-Based Cybersecurity Framework and Guidelines for Deposit Money Banks and Payment Service Banks*, May 2024.
- Result: **accepted for direct authority-PDF verification**.
- Page count: 61.
- SHA-256: `057d6c205c03a37ab03ea761fb51ac2e7c4c6eff454cbae1d182cacd73031ade`.
- Verification: structural identity checks plus full/targeted rendered inspection; all 30 seeded controls link to reviewed source pages.
- Repository treatment: source PDF excluded; page references and verification metadata retained.

## CBN OFI 2022 - correct scanned authority document

- Expected source: Central Bank of Nigeria, *Risk-Based Cybersecurity Framework and Guidelines for Other Financial Institutions (OFIs)*, June 2022.
- Result: **accepted after full manual render review**.
- Page count: 43.
- SHA-256: `b2796485512005a79e18ea740a0c73926ad7e2164eb3e0266d9cb6fc2c4dd99c`.
- Source format: image-only scan with no dependable PDF text layer.
- Identity evidence: issuing letter to all OFIs; June 2022 framework cover; OFI-specific governance/risk/resilience/reporting appendices; effective date January 1, 2023.
- Verification: all 43 pages rendered and reviewed. The 21 seeded OFI controls link to relevant source PDF page(s).
- Restriction: every source page is visibly marked `Classified as Confidential`.
- Repository treatment: **do not redistribute the PDF**. Retain only source hash, review metadata, project-authored summaries and page locators.

## Previously supplied mislabeled OFI file

- Result: **rejected**.
- Reason: content identified it as *Financial Sector's Cybersecurity: A Regulatory Digest*, 6th Edition, August 2021, not the CBN OFI framework.
- SHA-256: `42a6915396ade6695ba10549ba4edae7b153d9896191bc3f35678be8ce8d27d7`.
- Lesson: filenames never determine provenance.

## ISO 27001:2022 gap-assessment workbook

- Result: **accepted only as a private secondary assessment/reference aid**.
- SHA-256: `5105f4bf4cd80330c1b5b61c16a9a424d5a563f3d803fbae46532bc609799302`.
- It is not an ISO-issued copy of ISO/IEC 27001:2022.
- Repository treatment: do not redistribute the workbook or copy licensed/copyrighted ISO requirement/control text. The public ISO pack continues to use project-authored clause-level summaries and official ISO references.

## Uploaded 43-page PDF reviewed during Stage 4

The file initially presented for an ISO check was identified as the correct CBN OFI 2022 framework rather than ISO/IEC 27001. It therefore closed the OFI authority-source gap but did not change the ISO authority status.

## Trust rule

Authority-file verification requires source identity checks, structural/visual review, content-to-control cross-checking, page references and recorded verification metadata. A filename alone is never sufficient.
