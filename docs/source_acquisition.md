# Source Acquisition and Private Verification

Verified: 2026-08-19.

This project separates public-source framework development from private authority-file verification.

## Sources already usable from public authority channels

The repository can be developed and maintained from the public NDPC material for the Nigeria Data Protection Act 2023 and NDPC GAID 2025. Their control summaries are project-authored paraphrases with source locators rather than copied legal text.

## CBN authority-file status

### DMB/PSB 2024 - direct verification complete

A privately supplied copy of the **Risk-Based Cybersecurity Framework and Guidelines for Deposit Money Banks and Payment Service Banks (May 2024)** was structurally verified, rendered and manually cross-checked on 2026-08-19.

- Framework ID: `cbn-dmb-psb-2024`.
- Page count: 61.
- Verified SHA-256: `057d6c205c03a37ab03ea761fb51ac2e7c4c6eff454cbae1d182cacd73031ade`.
- All 30 seeded controls now record direct authority-PDF verification and source PDF page references.
- The private source PDF is not redistributed.

### OFI 2022 - correct authority PDF still required

The file supplied under the OFI 2022 filename during the 2026-08-19 verification pass was rejected. Its rendered title/content identified it as the **Financial Sector's Cybersecurity: A Regulatory Digest, 6th Edition, August 2021**, not the CBN OFI 2022 framework. The repository therefore retains the existing archival-text provenance tier for `cbn-ofi-2022` and does not upgrade it to direct verification.

Obtain the original **Risk-Based Cybersecurity Framework and Guidelines for Other Financial Institutions (OFIs) (June 2022)** directly from CBN before changing that source tier. The expected authority URL is recorded in `frameworks/source_registry.yaml`.

Do not commit privately supplied authority PDFs to this repository. The directory `local_authority_sources/` is git-ignored.

After placing a CBN PDF in a private local directory, run:

```bash
python scripts/verify_authority_pdf.py cbn-dmb-psb-2024 /path/to/cbn-dmb-psb-2024.pdf --json /tmp/cbn-dmb-verification.json
python scripts/verify_authority_pdf.py cbn-ofi-2022 /path/to/cbn-ofi-2022.pdf --json /tmp/cbn-ofi-verification.json
```

The verifier records a SHA-256 digest and checks expected structural landmarks. A pass means the file resembles the expected framework; it does **not** independently prove provenance. Retain the original authority download context and manually inspect the PDF before upgrading control verification status.

## ISO/IEC 27001

ISO/IEC 27001:2022 is copyrighted. The open-source repository intentionally contains only project-authored clause-level readiness summaries and official ISO references.

If a maintainer or organisation owns a legitimate licensed copy of ISO/IEC 27001:2022 (and optionally ISO/IEC 27002:2022), it may be used privately to verify mappings. A third-party ISO 27001:2022 gap-assessment workbook may also be used as a secondary implementation aid, but it must not be treated as the authoritative standard. Do not commit, redistribute, quote extensively from, or package licensed ISO text in this repository.

## Organisational policies

Real company policies are **not required** to build the core product. Synthetic evidence fixtures are used for deterministic regression testing.

For later real-world evaluation, use only policies that the organisation is authorised to share. Prefer redacted or anonymised samples. Remove credentials, personal data, customer secrets, incident-sensitive details and other confidential material before uploading to a hosted test environment. Never commit customer policy documents to the public repository.
