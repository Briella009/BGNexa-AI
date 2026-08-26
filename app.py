from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.applicability import recommended_framework_ids, resolve_control_applicability
from src.assessor import assess_control
from src.copilot import answer_copilot_question
from src.crosswalk import capability_crosswalk, evidence_reuse_opportunities
from src.dcpmi import triage_dcpmi
from src.gdpr import triage_gdpr_article3
from src.embeddings import OpenAIEmbedder, can_use_openai_embeddings
from src.evidence import parse_bytes, parse_path
from src.framework_loader import load_frameworks
from src.llm import can_use_llm, llm_model_name, llm_provider
from src.models import AssessmentResult, AssessmentStatus, HumanValidation
from src.report import build_executive_html, evidence_quality_dataframe, priority_gaps_dataframe, results_dataframe
from src.retriever import HybridEvidenceRetriever
from src.review import apply_human_validation, build_assessment_snapshot
from src.scoring import calculate_score


ROOT = Path(__file__).resolve().parent
FRAMEWORK_ROOT = ROOT / "frameworks"
SAMPLE_ROOT = ROOT / "sample_data"

load_dotenv(ROOT / ".env")
st.set_page_config(page_title="BGNexa AI", page_icon="🛡️", layout="wide")


@st.cache_resource
def get_frameworks():
    return load_frameworks(FRAMEWORK_ROOT)


def status_label(status: AssessmentStatus) -> str:
    return {
        AssessmentStatus.SUPPORTED: "Supported",
        AssessmentStatus.PARTIAL: "Partially supported",
        AssessmentStatus.NOT_EVIDENCED: "Not evidenced",
        AssessmentStatus.REVIEW_REQUIRED: "Review required",
        AssessmentStatus.NOT_APPLICABLE: "Not applicable",
    }[status]


def framework_has_pending_authority_verification(framework) -> bool:
    return any("pending_direct" in control.verification_status for control in framework.controls)


def manual_review_count(results: list[AssessmentResult]) -> int:
    return sum(1 for r in results if r.requires_human_review)


def build_chunks(uploaded_files, use_samples: bool, include_injection_test: bool):
    chunks = []
    errors: list[str] = []

    if use_samples:
        names = ["access_control_policy.txt", "incident_response_policy.txt", "privacy_governance.txt"]
        if include_injection_test:
            names.append("prompt_injection_example.txt")
        for name in names:
            try:
                chunks.extend(parse_path(SAMPLE_ROOT / name))
            except Exception as exc:  # pragma: no cover - UI defensive path
                errors.append(f"{name}: {exc}")

    for uploaded in uploaded_files or []:
        try:
            chunks.extend(parse_bytes(uploaded.name, uploaded.getvalue()))
        except Exception as exc:
            errors.append(f"{uploaded.name}: {exc}")

    return chunks, errors


def build_retriever(chunks, use_semantic_retrieval: bool):
    embedder = OpenAIEmbedder() if use_semantic_retrieval and can_use_openai_embeddings() else None
    return HybridEvidenceRetriever(chunks, embedder=embedder)


def run_assessment(
    selected_frameworks,
    retriever,
    use_ai: bool,
    dcpmi_status: str,
    processing_role: str,
    dcpmi_tier: str = "Unknown",
    registration_exempt_status: str = "Unknown",
    gdpr_scope_status: str = "Unknown",
    gdpr_dpo_required_status: str = "Unknown",
    gdpr_cross_border_transfer_status: str = "Unknown",
    gdpr_dpia_required_status: str = "Unknown",
    gdpr_ropa_required_status: str = "Unknown",
    gdpr_uses_processors_status: str = "Unknown",
):
    bundle = {}

    for framework in selected_frameworks:
        results: list[AssessmentResult] = []
        for control in framework.controls:
            pre_decision = resolve_control_applicability(
                framework_id=framework.framework_id,
                control=control,
                dcpmi_status=dcpmi_status,
                processing_role=processing_role,
                dcpmi_tier=dcpmi_tier,
                registration_exempt_status=registration_exempt_status,
                gdpr_scope_status=gdpr_scope_status,
                gdpr_dpo_required_status=gdpr_dpo_required_status,
                gdpr_cross_border_transfer_status=gdpr_cross_border_transfer_status,
                gdpr_dpia_required_status=gdpr_dpia_required_status,
                gdpr_ropa_required_status=gdpr_ropa_required_status,
                gdpr_uses_processors_status=gdpr_uses_processors_status,
            )
            if pre_decision is not None:
                results.append(pre_decision)
                continue

            matches = retriever.retrieve(control, top_k=5)
            try:
                result = assess_control(framework.framework_id, control, matches, use_ai=use_ai)
            except Exception as exc:
                result = AssessmentResult(
                    control_id=control.control_id,
                    framework_id=framework.framework_id,
                    status=AssessmentStatus.REVIEW_REQUIRED,
                    rationale="Automated assessment could not be completed safely.",
                    evidence=matches,
                    recommendation=f"Perform manual evidence review. Technical detail: {type(exc).__name__}",
                    evidence_strength="weak",
                    ai_assessed=False,
                    requires_human_review=True,
                )
            results.append(result)

        bundle[framework.framework_id] = {
            "framework": framework,
            "results": results,
            "score": calculate_score(framework.controls, results),
        }
    return bundle


def recalculate_bundle_scores(bundle) -> None:
    for item in bundle.values():
        item["score"] = calculate_score(item["framework"].controls, item["results"])


def combined_export(bundle) -> pd.DataFrame:
    frames = []
    for item in bundle.values():
        frames.append(results_dataframe(item["framework"], item["results"]))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def render_source_panel(selected_frameworks):
    rows = []
    for fw in selected_frameworks:
        rows.append(
            {
                "Framework": fw.name,
                "Authority": fw.authority,
                "Version": fw.version,
                "Type": fw.framework_type,
                "Last verified": fw.source.last_verified,
                "Source type": fw.source.source_type,
                "Control pack": "Preview / verification pending"
                if framework_has_pending_authority_verification(fw)
                else "Traceable seed pack",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def find_result(bundle, framework_id: str, control_id: str):
    item = bundle[framework_id]
    for index, result in enumerate(item["results"]):
        if result.control_id == control_id:
            return item, index, result
    raise KeyError(f"Unknown result {framework_id}/{control_id}")


frameworks = get_frameworks()

st.title("BGNexa AI")
st.caption("Evidence-backed readiness for Nigerian and international cybersecurity/privacy frameworks")

st.info(
    "This tool measures evidence-backed readiness. It does not issue a legal-compliance determination, ISO certification, "
    "regulatory approval, or audit opinion. Automated findings remain subject to qualified human review."
)

with st.sidebar:
    st.header("Organisation profile")
    organisation_name = st.text_input("Organisation name", value="Demo Organisation")
    operates_in_nigeria = st.checkbox("Operates in Nigeria", value=True)
    processing_role = st.selectbox("Personal-data processing role", ["Both", "Controller", "Processor", "Unsure"], index=0)
    dcpmi_status = st.selectbox(
        "NDPC major-importance status (DCPMI)",
        ["Unknown", "Yes", "No"],
        index=0,
        help="Do not guess. Choose Unknown if status has not been documented against current NDPC guidance.",
    )
    if dcpmi_status == "Yes":
        dcpmi_tier = st.selectbox(
            "Confirmed DCPMI tier",
            ["Unknown", "UHL", "EHL", "OHL"],
            index=0,
            help="Use the documented GAID Schedule 7 tier. The triage helper below does not auto-confirm this field.",
        )
        registration_exempt_status = st.selectbox(
            "NDPC registration exemption",
            ["Unknown", "No", "Yes"],
            index=0,
            help=(
                "Choose Yes only when a current Section 44 / GAID Schedule 7 registration exemption has been documented. "
                "The listed Schedule 7 exemptions are framed for data controllers of major importance."
            ),
        )
    else:
        dcpmi_tier = "Unknown"
        registration_exempt_status = "Unknown"
    if operates_in_nigeria:
        with st.expander("DCPMI Schedule 7 triage", expanded=False):
            st.caption(
                "Non-binding triage only. It highlights explicit GAID 2025 Schedule 7 indicators; "
                "it does not change the confirmed DCPMI status above."
            )
            dcpmi_org_type = st.selectbox(
                "Organisation type",
                [
                    "Other / Unknown",
                    "Commercial bank (national/regional)",
                    "Telecommunication company",
                    "Insurance company",
                    "Multinational company",
                    "Electricity distribution company",
                    "Oil and gas company",
                    "Public social media app provider",
                    "Public email app provider",
                    "Communication device manufacturer",
                    "Payment gateway service provider",
                    "Fintech",
                    "Government MDA",
                    "Microfinance bank",
                    "Higher institution",
                    "Secondary/tertiary hospital",
                    "Mortgage bank",
                    "Primary/secondary school",
                    "Corporate training service provider",
                    "Primary health centre",
                    "Independent medical laboratory",
                    "Hotel/guest house under 50 suites",
                ],
            )
            dcpmi_sector = st.selectbox(
                "Processing sector",
                [
                    "Other / Unknown",
                    "Aviation",
                    "Communication",
                    "Education",
                    "Electric Power",
                    "Export and Import",
                    "Financial",
                    "Health",
                    "Hospitality",
                    "Insurance",
                    "Oil and Gas",
                    "Tourism",
                    "E-Commerce",
                    "Public Service",
                ],
            )
            dcpmi_count_raw = st.text_input(
                "Data subjects processed in last 6 months",
                value="",
                placeholder="e.g. 1250",
            )
            commercial_ict_device_service = st.checkbox(
                "Provides commercial ICT services on another person's data-capable device",
                value=False,
            )
            sensitive_count_raw = st.text_input(
                "Sensitive-data subjects processed commercially (processor only)",
                value="",
                placeholder="Optional",
            )
            if st.button("Run DCPMI triage", use_container_width=True):
                try:
                    dcpmi_count = int(dcpmi_count_raw.replace(",", "")) if dcpmi_count_raw.strip() else None
                    sensitive_count = int(sensitive_count_raw.replace(",", "")) if sensitive_count_raw.strip() else None
                    triage = triage_dcpmi(
                        organisation_type=None if dcpmi_org_type == "Other / Unknown" else dcpmi_org_type,
                        sector=None if dcpmi_sector == "Other / Unknown" else dcpmi_sector,
                        data_subjects_six_months=dcpmi_count,
                        commercial_ict_device_service=commercial_ict_device_service,
                        sensitive_personal_data_commercial_subjects=sensitive_count,
                        processing_role=processing_role,
                    )
                    st.session_state["dcpmi_triage"] = triage
                except ValueError as exc:
                    st.error(f"DCPMI triage input error: {exc}")

            triage = st.session_state.get("dcpmi_triage")
            if triage is not None:
                if triage.candidate_status == "candidate_dcpmi":
                    tier = triage.candidate_tier if triage.candidate_tier != "unknown" else "tier unresolved"
                    st.warning(f"Schedule 7 indicator found: candidate DCPMI ({tier}). Human confirmation required.")
                elif triage.candidate_status == "no_trigger_identified":
                    st.info("No explicit trigger identified from the supplied fields. This is not a legal 'No'.")
                else:
                    st.info("More information is required for Schedule 7 triage.")
                for item in triage.basis:
                    st.caption(f"Basis: {item}")
                for item in triage.ambiguities:
                    st.caption(f"Review: {item}")
    cbn_regulated_type = st.selectbox(
        "CBN regulatory category",
        ["Not CBN-regulated / Unknown", "OFI", "DMB/PSB"],
        index=0,
        help="OFI and DMB/PSB use separate CBN cybersecurity framework packs.",
    )
    include_iso = st.checkbox("Include ISO/IEC 27001 readiness", value=True)
    include_nist = st.checkbox(
        "Include NIST CSF 2.0 readiness",
        value=False,
        help="NIST CSF 2.0 is voluntary, outcome-based guidance. The full 106-subcategory Core pack is included.",
    )

    st.divider()
    st.subheader("EU GDPR scope")
    gdpr_scope_status = st.selectbox(
        "Confirmed GDPR Article 3 territorial scope",
        ["Unknown", "Yes", "No"],
        index=0,
        help="This is a human/legal scope determination. The AI is not allowed to decide GDPR territorial scope.",
    )
    with st.expander("Article 3 scope triage", expanded=False):
        st.caption(
            "Non-binding triage only. It checks the explicit Article 3 territorial-scope triggers and does not change the confirmed field above."
        )
        eu_establishment = st.selectbox("Processing in context of an EU establishment", ["Unknown", "Yes", "No"], index=0)
        offers_eu = st.selectbox("Offers goods/services to people in the EU", ["Unknown", "Yes", "No"], index=0)
        monitors_eu = st.selectbox("Monitors behaviour of people in the EU", ["Unknown", "Yes", "No"], index=0)
        public_international_law = st.selectbox(
            "Member State law applies by public international law", ["Unknown", "Yes", "No"], index=0
        )
        gdpr_triage = triage_gdpr_article3(
            eu_establishment=eu_establishment,
            offers_goods_services_to_people_in_eu=offers_eu,
            monitors_behaviour_in_eu=monitors_eu,
            member_state_law_by_public_international_law=public_international_law,
        )
        if gdpr_triage.candidate_status == "candidate_in_scope":
            st.warning("Article 3 indicator found: GDPR may apply. Human/legal confirmation is still required.")
        elif gdpr_triage.candidate_status == "no_article3_trigger_identified":
            st.info("No Article 3 trigger was identified from the supplied facts. This is not a legal out-of-scope determination.")
        else:
            st.info("More information is required to triage GDPR territorial scope.")
        for item in gdpr_triage.basis:
            st.caption(f"Basis: {item}")

    include_gdpr = st.checkbox(
        "Include GDPR readiness",
        value=gdpr_scope_status == "Yes",
        help="If scope is Unknown, GDPR controls can still be selected but they will remain review-required until scope is confirmed.",
    )
    if include_gdpr:
        st.caption("Conditional GDPR obligations remain human-confirmed rather than AI-inferred.")
        gdpr_uses_processors_status = st.selectbox("Controller uses processors in assessed scope", ["Unknown", "Yes", "No"], index=0)
        gdpr_ropa_required_status = st.selectbox("Article 30 RoPA required", ["Unknown", "Yes", "No"], index=0)
        gdpr_dpia_required_status = st.selectbox("Article 35 DPIA required", ["Unknown", "Yes", "No"], index=0)
        gdpr_dpo_required_status = st.selectbox("Article 37 DPO designation required", ["Unknown", "Yes", "No"], index=0)
        gdpr_cross_border_transfer_status = st.selectbox(
            "Transfers to third countries/international organisations occur", ["Unknown", "Yes", "No"], index=0
        )
    else:
        gdpr_uses_processors_status = "Unknown"
        gdpr_ropa_required_status = "Unknown"
        gdpr_dpia_required_status = "Unknown"
        gdpr_dpo_required_status = "Unknown"
        gdpr_cross_border_transfer_status = "Unknown"

    st.divider()
    st.header("Retrieval and AI")
    semantic_available = can_use_openai_embeddings()
    use_semantic_retrieval = st.toggle(
        "Use semantic embeddings",
        value=False,
        disabled=not semantic_available,
        help="When enabled, evidence retrieval combines TF-IDF with OpenAI embeddings using reciprocal-rank fusion.",
    )
    if semantic_available:
        st.caption(f"Embedding model: {os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')}")
    else:
        st.caption("No API key detected: retrieval uses the deterministic TF-IDF fallback.")

    ai_available = can_use_llm()
    use_ai = st.toggle("Use AI evidence reviewer", value=False, disabled=not ai_available)
    if ai_available:
        provider = llm_provider()
        st.caption(f"Generation provider: {provider}. Reasoning model: {llm_model_name()}. Structured output is used.")
    else:
        st.caption("No supported generation API key detected. Retrieved candidates remain review-required until a person validates them.")

    if use_semantic_retrieval or use_ai:
        providers = []
        if use_semantic_retrieval:
            providers.append("OpenAI embeddings")
        if use_ai and llm_provider():
            providers.append(f"{llm_provider()} generation")
        st.warning(
            "External AI mode is enabled. Relevant organisational evidence will be sent to the configured provider(s): "
            + ", ".join(providers)
            + ". Use only evidence you are authorised to process through those providers."
        )

recommended = recommended_framework_ids(
    operates_in_nigeria=operates_in_nigeria,
    cbn_regulated_type=cbn_regulated_type,
    include_iso=include_iso,
    include_nist=include_nist,
    include_gdpr=include_gdpr,
)

framework_labels = {fid: f"{fw.name} · {fw.framework_type} [{fid}]" for fid, fw in frameworks.items()}
selected_ids = st.multiselect(
    "Framework packs",
    options=list(frameworks.keys()),
    default=[fid for fid in recommended if fid in frameworks],
    format_func=lambda fid: framework_labels[fid],
)
selected_frameworks = [frameworks[fid] for fid in selected_ids]

if any(framework_has_pending_authority_verification(fw) for fw in selected_frameworks):
    pending_names = [fw.name for fw in selected_frameworks if framework_has_pending_authority_verification(fw)]
    st.warning(
        "One or more selected packs still contain direct-authority verification work: " + ", ".join(pending_names) + ". "
        "Those controls remain visibly marked and are not presented as production-complete."
    )

with st.expander("Source and verification status", expanded=False):
    if selected_frameworks:
        render_source_panel(selected_frameworks)
    else:
        st.write("Select at least one framework pack.")

st.subheader("Evidence")
col1, col2 = st.columns([1, 2])
with col1:
    use_samples = st.checkbox("Use fictional sample policies", value=True)
    include_injection_test = st.checkbox("Include prompt-injection test file", value=False, disabled=not use_samples)
with col2:
    uploaded_files = st.file_uploader(
        "Upload organisational evidence",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        help="Files are parsed for evidence. Document text is treated as untrusted data, never as instructions.",
    )

run = st.button("Run readiness assessment", type="primary", disabled=not selected_frameworks)

if run:
    chunks, parse_errors = build_chunks(uploaded_files, use_samples, include_injection_test)
    if parse_errors:
        for error in parse_errors:
            st.error(error)
    if not chunks:
        st.error("No readable evidence was provided. Add sample policies or upload evidence files.")
    else:
        with st.spinner("Retrieving and assessing evidence..."):
            retriever = build_retriever(chunks, use_semantic_retrieval)
            bundle = run_assessment(
                selected_frameworks,
                retriever,
                use_ai=use_ai,
                dcpmi_status=dcpmi_status,
                processing_role=processing_role,
                dcpmi_tier=dcpmi_tier,
                registration_exempt_status=registration_exempt_status,
                gdpr_scope_status=gdpr_scope_status,
                gdpr_dpo_required_status=gdpr_dpo_required_status,
                gdpr_cross_border_transfer_status=gdpr_cross_border_transfer_status,
                gdpr_dpia_required_status=gdpr_dpia_required_status,
                gdpr_ropa_required_status=gdpr_ropa_required_status,
                gdpr_uses_processors_status=gdpr_uses_processors_status,
            )
        st.session_state["assessment_bundle"] = bundle
        st.session_state["evidence_chunks"] = chunks
        st.session_state["evidence_retriever"] = retriever
        st.session_state["review_validations"] = []
        st.session_state["retrieval_mode"] = retriever.mode
        st.session_state["semantic_error"] = retriever.semantic_error
        st.session_state["assessment_profile"] = {
            "operates_in_nigeria": operates_in_nigeria,
            "processing_role": processing_role,
            "dcpmi_status": dcpmi_status,
            "dcpmi_tier": dcpmi_tier,
            "registration_exempt_status": registration_exempt_status,
            "cbn_regulated_type": cbn_regulated_type,
            "include_nist": include_nist,
            "gdpr_scope_status": gdpr_scope_status,
            "gdpr_dpo_required_status": gdpr_dpo_required_status,
            "gdpr_cross_border_transfer_status": gdpr_cross_border_transfer_status,
            "gdpr_dpia_required_status": gdpr_dpia_required_status,
            "gdpr_ropa_required_status": gdpr_ropa_required_status,
            "gdpr_uses_processors_status": gdpr_uses_processors_status,
            "framework_ids": selected_ids,
        }

bundle = st.session_state.get("assessment_bundle")
if bundle:
    current_material_profile = {
        "operates_in_nigeria": operates_in_nigeria,
        "processing_role": processing_role,
        "dcpmi_status": dcpmi_status,
        "dcpmi_tier": dcpmi_tier,
        "registration_exempt_status": registration_exempt_status,
        "cbn_regulated_type": cbn_regulated_type,
        "include_nist": include_nist,
        "gdpr_scope_status": gdpr_scope_status,
        "gdpr_dpo_required_status": gdpr_dpo_required_status,
        "gdpr_cross_border_transfer_status": gdpr_cross_border_transfer_status,
        "gdpr_dpia_required_status": gdpr_dpia_required_status,
        "gdpr_ropa_required_status": gdpr_ropa_required_status,
        "gdpr_uses_processors_status": gdpr_uses_processors_status,
        "framework_ids": selected_ids,
    }
    assessment_profile = st.session_state.get("assessment_profile", current_material_profile)
    assessment_stale = assessment_profile != current_material_profile
    if assessment_stale:
        st.warning(
            "The organisation profile or selected framework packs changed after this assessment was run. "
            "The displayed findings still reflect the previous run. Rerun the assessment before validating or relying on exports."
        )
    st.divider()
    st.subheader("Readiness dashboard")
    framework_type_summary = ", ".join(
        sorted({item["framework"].framework_type.replace("_", " ") for item in bundle.values()})
    )
    st.caption(
        f"Selected source types: {framework_type_summary}. Percentages are evidence-readiness indicators within each pack, not interchangeable legal or certification scores."
    )

    all_controls = []
    all_results: list[AssessmentResult] = []
    for item in bundle.values():
        all_controls.extend(item["framework"].controls)
        all_results.extend(item["results"])
    overall = calculate_score(all_controls, all_results)

    metric_cols = st.columns(5)
    readiness_text = "—" if overall.provisional_readiness_percent is None else f"{overall.provisional_readiness_percent:.1f}%"
    metric_cols[0].metric("Provisional readiness", readiness_text)
    metric_cols[1].metric("Resolved coverage", f"{overall.coverage_percent:.1f}%")
    metric_cols[2].metric("Supported", overall.supported)
    metric_cols[3].metric("Not evidenced", overall.not_evidenced)
    metric_cols[4].metric("Human review", manual_review_count(all_results))

    retrieval_mode = st.session_state.get("retrieval_mode", "lexical_fallback")
    st.caption(
        f"Retrieval mode: {retrieval_mode}. Provisional readiness uses only resolved applicable controls; coverage shows how much "
        "applicable control weight has actually been resolved."
    )
    if st.session_state.get("semantic_error"):
        st.warning(f"Semantic retrieval fell back safely to lexical retrieval: {st.session_state['semantic_error']}")

    quality_df = evidence_quality_dataframe(bundle)
    if not quality_df.empty:
        st.subheader("Evidence quality snapshot")
        freshness_counts = quality_df["freshness"].value_counts().to_dict()
        quality_cols = st.columns(4)
        quality_cols[0].metric("Current sources", freshness_counts.get("current", 0))
        quality_cols[1].metric("Aging sources", freshness_counts.get("aging", 0))
        quality_cols[2].metric("Stale sources", freshness_counts.get("stale", 0))
        quality_cols[3].metric("Undated / unknown", freshness_counts.get("unknown", 0))
        st.caption(
            "General evidence-age signal only: current <=365 days, aging 366-730 days, stale >730 days. "
            "Framework-specific review, retention and recertification rules still take precedence."
        )
        if freshness_counts.get("stale", 0):
            st.warning("Stale evidence is present. BGNexa will not allow stale-only evidence to establish a supported automated result.")
        with st.expander("Show evidence type and freshness register", expanded=False):
            st.dataframe(quality_df, use_container_width=True, hide_index=True)

    gaps = priority_gaps_dataframe(bundle)
    st.subheader("Priority remediation queue")
    if gaps.empty:
        st.success("No unresolved gaps were identified in the assessed control set.")
    else:
        st.dataframe(gaps.head(15), use_container_width=True, hide_index=True)

    st.subheader("Framework results")
    for fid, item in bundle.items():
        fw = item["framework"]
        score = item["score"]
        results = item["results"]
        readiness = "—" if score.provisional_readiness_percent is None else f"{score.provisional_readiness_percent:.1f}%"
        with st.expander(f"{fw.name} | readiness {readiness} | coverage {score.coverage_percent:.1f}%", expanded=True):
            rows = []
            control_map = {c.control_id: c for c in fw.controls}
            for result in results:
                control = control_map[result.control_id]
                rows.append(
                    {
                        "Reference": control.reference,
                        "Control": control.title,
                        "Status": status_label(result.status),
                        "Evidence": result.evidence_strength,
                        "Evidence type": ", ".join(sorted({m.evidence_type.value for m in result.evidence})) or "none",
                        "Freshness": ", ".join(sorted({m.freshness_status.value for m in result.evidence})) or "none",
                        "AI": "Yes" if result.ai_assessed else "No",
                        "Human validated": "Yes" if result.human_validated else "No",
                        "Human review": "Yes" if result.requires_human_review else "No",
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            for result in results:
                control = control_map[result.control_id]
                with st.expander(f"{control.reference} - {control.title}: {status_label(result.status)}", expanded=False):
                    st.write(control.requirement_summary)
                    page_text = f" | PDF pages: {', '.join(map(str, control.source_pdf_pages))}" if control.source_pdf_pages else ""
                    st.caption(f"Source locator: {control.source_locator}{page_text} | verification: {control.verification_status}")
                    st.write(f"**Assessment:** {result.rationale}")
                    if result.recommendation:
                        st.write(f"**Recommendation:** {result.recommendation}")
                    if result.evidence_quality_note:
                        st.caption(f"Evidence quality: {result.evidence_quality_note}")
                    if result.evidence_quality_flags:
                        st.warning("Evidence-quality flags: " + ", ".join(result.evidence_quality_flags))
                    if result.human_validated:
                        st.success(f"Human validated by {result.reviewer} at {result.reviewed_at}")
                        st.write(f"**Reviewer note:** {result.reviewer_note}")
                    if result.evidence:
                        st.write("**Retrieved evidence candidates**")
                        for match in result.evidence:
                            location = f", page {match.page}" if match.page else ""
                            flag = " | prompt-injection flag" if match.injection_flag else ""
                            score_parts = [f"retrieval {match.retrieval_score:.3f}", match.retrieval_method]
                            if match.lexical_score is not None:
                                score_parts.append(f"lexical {match.lexical_score:.3f}")
                            if match.semantic_score is not None:
                                score_parts.append(f"semantic {match.semantic_score:.3f}")
                            quality_parts = [f"type {match.evidence_type.value}", f"freshness {match.freshness_status.value}"]
                            if match.document_date:
                                quality_parts.append(f"document date {match.document_date}")
                            if match.age_days is not None and match.age_days >= 0:
                                quality_parts.append(f"age {match.age_days} days")
                            st.caption(
                                f"{match.source_name}{location} | {' | '.join(score_parts)} | {' | '.join(quality_parts)}{flag}"
                            )
                            st.code(match.excerpt, language="text")

    st.subheader("Human validation")
    st.caption(
        "A person can resolve automated or retrieval-only findings. Supported/partial decisions require explicit evidence confirmation, "
        "including consideration of evidence type and freshness; not-applicable decisions remain controlled by the organisation profile "
        "rather than reviewer override."
    )
    review_options = []
    review_lookup = {}
    for fid, item in bundle.items():
        fw = item["framework"]
        controls = {c.control_id: c for c in fw.controls}
        for result in item["results"]:
            if result.status == AssessmentStatus.NOT_APPLICABLE:
                continue
            control = controls[result.control_id]
            key = f"{fid}|{result.control_id}"
            label = f"{fw.name} | {control.reference} | {control.title} | {status_label(result.status)}"
            review_options.append((key, label))
            review_lookup[key] = (fid, result.control_id)

    if review_options:
        selected_review = st.selectbox(
            "Control to validate",
            options=[key for key, _ in review_options],
            format_func=lambda key: dict(review_options)[key],
        )
        selected_fid, selected_cid = review_lookup[selected_review]
        _, _, current_result = find_result(bundle, selected_fid, selected_cid)
        with st.form("human_validation_form", clear_on_submit=False):
            reviewer = st.text_input("Reviewer name")
            final_status = st.selectbox(
                "Validated status",
                options=[
                    AssessmentStatus.SUPPORTED.value,
                    AssessmentStatus.PARTIAL.value,
                    AssessmentStatus.NOT_EVIDENCED.value,
                    AssessmentStatus.REVIEW_REQUIRED.value,
                ],
                index=3,
            )
            evidence_confirmed = st.checkbox(
                "I inspected the cited evidence, including its type and freshness, and confirm it supports this decision"
            )
            reviewer_note = st.text_area("Reviewer rationale / note")
            submitted = st.form_submit_button("Apply human validation")
        if submitted:
            if assessment_stale:
                st.error("Rerun the assessment after profile/framework changes before recording human validation.")
            else:
                try:
                    item, index, result = find_result(bundle, selected_fid, selected_cid)
                    updated, validation = apply_human_validation(
                        result,
                        AssessmentStatus(final_status),
                        reviewer,
                        reviewer_note,
                        evidence_confirmed,
                    )
                    item["results"][index] = updated
                    recalculate_bundle_scores(bundle)
                    validations: list[HumanValidation] = st.session_state.setdefault("review_validations", [])
                    validations.append(validation)
                    st.session_state["assessment_bundle"] = bundle
                    st.success("Human validation recorded. Scores were recalculated from the validated result.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.subheader("Cross-framework capability view")
    st.caption(
        "Shared tags identify potential evidence reuse only. They do not mean a law, regulation, voluntary framework or standard has equivalent requirements."
    )
    selected_bundle_frameworks = [item["framework"] for item in bundle.values()]
    reuse_rows = evidence_reuse_opportunities(selected_bundle_frameworks, limit=10)
    if reuse_rows:
        st.write("**Highest-overlap evidence areas**")
        st.dataframe(
            pd.DataFrame(reuse_rows)[["capability", "framework_count", "control_count", "frameworks"]],
            use_container_width=True,
            hide_index=True,
        )
        with st.expander("Show complete capability crosswalk", expanded=False):
            st.dataframe(pd.DataFrame(capability_crosswalk(selected_bundle_frameworks)), use_container_width=True, hide_index=True)
    else:
        st.write("Select two or more framework packs to see shared capabilities.")

    st.subheader("Evidence-grounded Copilot")
    st.caption(
        "Ask about uploaded evidence, current assessment results, gaps, or relevant framework requirements. The Copilot receives retrieved "
        "evidence, the current assessment state, and selected framework summaries; flagged prompt-injection passages are excluded."
    )
    question = st.text_input("Ask the Copilot", placeholder="Which evidence supports our incident response readiness?")
    ask = st.button("Ask Copilot", disabled=not question.strip())
    if ask:
        retriever = st.session_state.get("evidence_retriever")
        if retriever is None:
            st.error("Run an assessment first so evidence can be indexed.")
        else:
            evidence_hits = retriever.retrieve_query(question, top_k=6)
            with st.spinner("Grounding answer in evidence..."):
                try:
                    answer = answer_copilot_question(
                        question,
                        evidence_hits,
                        [item["framework"] for item in bundle.values()],
                        use_ai=use_ai,
                        assessment_bundle=bundle,
                    )
                    st.session_state["last_copilot_answer"] = answer
                    st.session_state["last_copilot_hits"] = evidence_hits
                except Exception as exc:
                    st.error(f"Copilot generation failed safely: {type(exc).__name__}. Retrieved evidence is still available for manual review.")

    copilot_answer = st.session_state.get("last_copilot_answer")
    if copilot_answer:
        st.write(copilot_answer.answer)
        st.caption(f"Confidence: {copilot_answer.confidence} | AI generated: {'Yes' if copilot_answer.ai_generated else 'No'}")
        if copilot_answer.blocked_reason:
            st.warning(copilot_answer.blocked_reason)
        if copilot_answer.evidence_citations:
            st.write("**Traceable citations**")
            for citation in copilot_answer.evidence_citations:
                locator = f" | {citation.locator}" if citation.locator else ""
                st.write(f"- {citation.citation_type}: `{citation.citation_id}` | {citation.label}{locator}")
        if copilot_answer.limitations:
            st.write("**Limitations**")
            for limitation in copilot_answer.limitations:
                st.write(f"- {limitation}")

    st.subheader("Exports and assessment snapshot")
    if assessment_stale:
        st.warning("Exports are disabled until the assessment is rerun with the current organisation profile/framework selection.")
    else:
        export_df = combined_export(bundle)
        export_cols = st.columns(3)
        export_cols[0].download_button(
            "Download assessment CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="readiness_assessment.csv",
            mime="text/csv",
        )
        executive_html = build_executive_html(bundle, organisation_name=organisation_name)
        export_cols[1].download_button(
            "Download executive HTML",
            data=executive_html.encode("utf-8"),
            file_name="readiness_executive_report.html",
            mime="text/html",
        )
        profile = {
            "organisation_name": organisation_name,
            "operates_in_nigeria": assessment_profile.get("operates_in_nigeria"),
            "processing_role": assessment_profile.get("processing_role"),
            "dcpmi_status": assessment_profile.get("dcpmi_status"),
            "dcpmi_tier": assessment_profile.get("dcpmi_tier"),
            "registration_exempt_status": assessment_profile.get("registration_exempt_status"),
            "cbn_regulated_type": assessment_profile.get("cbn_regulated_type"),
            "include_nist": assessment_profile.get("include_nist"),
            "gdpr_scope_status": assessment_profile.get("gdpr_scope_status"),
            "gdpr_dpo_required_status": assessment_profile.get("gdpr_dpo_required_status"),
            "gdpr_cross_border_transfer_status": assessment_profile.get("gdpr_cross_border_transfer_status"),
            "gdpr_dpia_required_status": assessment_profile.get("gdpr_dpia_required_status"),
            "gdpr_ropa_required_status": assessment_profile.get("gdpr_ropa_required_status"),
            "gdpr_uses_processors_status": assessment_profile.get("gdpr_uses_processors_status"),
            "framework_ids": assessment_profile.get("framework_ids", []),
        }
        snapshot = build_assessment_snapshot(
            bundle,
            organisation_profile=profile,
            validations=st.session_state.get("review_validations", []),
        )
        export_cols[2].download_button(
            "Download snapshot JSON",
            data=json.dumps(snapshot, indent=2).encode("utf-8"),
            file_name="readiness_snapshot.json",
            mime="application/json",
        )
        st.caption(
            f"Snapshot SHA-256: {snapshot['sha256']}. This digest is tamper-evident, not a cryptographic identity signature."
        )

    with st.expander("How to interpret this result"):
        st.markdown(
            """
- **Supported** means cited evidence supports the readiness requirement; it is not a certification decision.
- **Partially supported** means some evidence exists but a material part of the requirement is missing or unclear.
- **Not evidenced** means no sufficiently relevant evidence was retrieved or a reviewer confirmed the evidence gap.
- **Review required** means applicability or evidence judgement is unresolved, or automated review was deliberately blocked.
- **Not applicable** is assigned only by explicit profile/applicability rules, never by the LLM or reviewer override.
- **Human validated** records a reviewer decision and rationale in the assessment snapshot.
- **Evidence type** distinguishes documented intent from operational records, technical evidence, audit/test evidence, regulatory filings, contractual evidence and training evidence.
- **Freshness** is a general evidence-age signal. Stale-only evidence cannot establish a supported automated result; framework-specific review and retention rules still take precedence.
"""
        )

st.divider()
st.caption(
    "Research build. Regulatory packs are versioned and source-traceable; qualified legal, privacy, regulatory, cybersecurity and audit review remains necessary for real-world reliance."
)
