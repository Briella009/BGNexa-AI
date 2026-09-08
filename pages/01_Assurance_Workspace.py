from __future__ import annotations

import json
from datetime import date

import pandas as pd
import streamlit as st

from src.assurance import (
    FINDING_SEVERITY_OPTIONS,
    TEST_RESULT_OPTIONS,
    WORKFLOW_STATUS_OPTIONS,
    assurance_dataframe,
    build_assurance_snapshot,
    build_assurance_workplan,
    diff_workplan_events,
    evidence_request_dataframe,
    findings_dataframe,
    workspace_fingerprint,
)
from src.review import build_assessment_snapshot


st.markdown(
    """
    <div style="padding:1.1rem 1.25rem;border-radius:18px;background:linear-gradient(100deg,#ff4d6d 0%,#ff8a3d 46%,#5b5df0 100%);color:white;margin-bottom:1rem;">
      <div style="font-size:0.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;opacity:.9;">BGNexa AI</div>
      <div style="font-size:2rem;font-weight:800;line-height:1.15;">Assurance Workspace</div>
      <div style="margin-top:.35rem;font-size:1rem;">Turn readiness results into traceable internal-audit and GRC work.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "This workspace supports evidence requests, control testing, findings, management actions and reviewer sign-off. "
    "It does not issue an audit opinion, legal-compliance determination, certification decision or regulator approval."
)

bundle = st.session_state.get("assessment_bundle")
if not bundle:
    st.warning("Run a readiness assessment on the BGNexa AI home page first. The Assurance Workspace uses that current assessment state as its starting point.")
    st.stop()

profile = dict(st.session_state.get("assessment_profile", {}))
current_fingerprint = workspace_fingerprint(bundle)

if "assurance_workplan_df" not in st.session_state:
    st.session_state["assurance_workplan_df"] = assurance_dataframe(build_assurance_workplan(bundle))
    st.session_state["assurance_fingerprint"] = current_fingerprint
    st.session_state["assurance_audit_events"] = []

saved_df: pd.DataFrame = st.session_state["assurance_workplan_df"]
workspace_stale = st.session_state.get("assurance_fingerprint") != current_fingerprint

if workspace_stale:
    st.warning(
        "The readiness assessment changed after this workplan was generated. Rebuild the workplan before relying on testing, findings or exports."
    )

meta_cols = st.columns(4)
with meta_cols[0]:
    organisation_name = st.text_input(
        "Organisation",
        value=st.session_state.get("assurance_org_name", "Current organisation"),
        key="assurance_org_name",
    )
with meta_cols[1]:
    engagement_title = st.text_input(
        "Engagement / assessment title",
        value=st.session_state.get("assurance_title", "Cybersecurity & privacy assurance review"),
        key="assurance_title",
    )
with meta_cols[2]:
    period_start = st.date_input(
        "Period start",
        value=st.session_state.get("assurance_period_start", date.today().replace(month=1, day=1)),
        key="assurance_period_start",
    )
with meta_cols[3]:
    period_end = st.date_input(
        "Period end",
        value=st.session_state.get("assurance_period_end", date.today()),
        key="assurance_period_end",
    )

people_cols = st.columns(3)
with people_cols[0]:
    prepared_by = st.text_input("Prepared by", value=st.session_state.get("assurance_prepared_by", ""), key="assurance_prepared_by")
with people_cols[1]:
    independent_reviewer = st.text_input(
        "Independent reviewer / supervisor",
        value=st.session_state.get("assurance_reviewer", ""),
        key="assurance_reviewer",
    )
with people_cols[2]:
    audit_objective = st.text_input(
        "Objective",
        value=st.session_state.get(
            "assurance_objective",
            "Evaluate whether available evidence supports the selected cybersecurity/privacy readiness outcomes.",
        ),
        key="assurance_objective",
    )

button_cols = st.columns([1, 4])
with button_cols[0]:
    if st.button("Rebuild from current assessment", type="primary", use_container_width=True):
        st.session_state["assurance_workplan_df"] = assurance_dataframe(build_assurance_workplan(bundle))
        st.session_state["assurance_fingerprint"] = current_fingerprint
        st.session_state["assurance_audit_events"] = []
        st.rerun()
with button_cols[1]:
    st.caption(
        "Beta workspace state is session-based. Export the workplan and snapshot before closing the browser or restarting the app."
    )

saved_df = st.session_state["assurance_workplan_df"]
if not saved_df.empty:
    status_series = saved_df["workflow_status"].astype(str)
    priority_series = saved_df["priority"].astype(str)
    test_series = saved_df["test_result"].astype(str)
    severity_series = saved_df["finding_severity"].astype(str)
    open_items = int((~status_series.isin(["closed", "risk_accepted"])).sum())
    urgent_items = int(priority_series.isin(["Critical", "High"]).sum())
    untested_items = int((test_series == "not_tested").sum())
    findings_count = int((severity_series != "none").sum())
else:
    open_items = urgent_items = untested_items = findings_count = 0

metric_cols = st.columns(4)
metric_cols[0].metric("Open assurance items", open_items)
metric_cols[1].metric("Critical / high priority", urgent_items)
metric_cols[2].metric("Not yet tested", untested_items)
metric_cols[3].metric("Recorded findings", findings_count)

tab_workplan, tab_requests, tab_findings, tab_trail, tab_exports = st.tabs(
    ["Workplan", "Evidence requests", "Findings & actions", "Audit trail", "Exports"]
)

with tab_workplan:
    st.caption(
        "Supported readiness results are still retained as validation tasks. Review-required items remain unresolved rather than being presented as confirmed deficiencies."
    )
    if saved_df.empty:
        st.info("No applicable controls are available in the current assessment.")
    else:
        column_order = [
            "work_item_id",
            "priority",
            "framework_name",
            "reference",
            "control_title",
            "assessment_status",
            "human_validated",
            "evidence_strength",
            "control_owner",
            "assurance_owner",
            "due_date",
            "workflow_status",
            "test_result",
            "sample_reference",
            "finding_title",
            "finding_severity",
            "management_response",
            "action_owner",
            "target_date",
            "reviewer",
            "reviewer_note",
            "closure_evidence",
            "evidence_request",
            "test_objective",
            "suggested_test_procedure",
            "evidence_sources",
            "evidence_hashes",
            "evidence_quality_flags",
            "assessment_rationale",
            "recommendation",
            "framework_id",
            "framework_type",
            "control_id",
            "source_locator",
            "weight",
        ]
        edited_df = st.data_editor(
            saved_df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_order=column_order,
            disabled=[
                "work_item_id",
                "priority",
                "framework_name",
                "framework_type",
                "framework_id",
                "reference",
                "control_id",
                "control_title",
                "source_locator",
                "assessment_status",
                "human_validated",
                "weight",
                "evidence_strength",
                "evidence_sources",
                "evidence_hashes",
                "evidence_quality_flags",
                "assessment_rationale",
                "recommendation",
                "test_objective",
                "suggested_test_procedure",
                "evidence_request",
            ],
            column_config={
                "workflow_status": st.column_config.SelectboxColumn("Workflow status", options=WORKFLOW_STATUS_OPTIONS),
                "test_result": st.column_config.SelectboxColumn("Test result", options=TEST_RESULT_OPTIONS),
                "finding_severity": st.column_config.SelectboxColumn("Finding severity", options=FINDING_SEVERITY_OPTIONS),
                "evidence_request": st.column_config.TextColumn("Evidence request", width="large"),
                "suggested_test_procedure": st.column_config.TextColumn("Suggested test procedure", width="large"),
                "assessment_rationale": st.column_config.TextColumn("Assessment rationale", width="large"),
                "recommendation": st.column_config.TextColumn("Recommendation", width="large"),
            },
            key="assurance_workplan_editor",
        )

        save_cols = st.columns([1, 4])
        with save_cols[0]:
            if st.button("Save workspace changes", use_container_width=True):
                actor = prepared_by or independent_reviewer or "unspecified user"
                events = diff_workplan_events(saved_df, edited_df, actor)
                st.session_state["assurance_audit_events"].extend(events)
                st.session_state["assurance_workplan_df"] = edited_df.copy()
                st.success(f"Workspace saved. {len(events)} change event(s) added to the session audit trail.")
                st.rerun()
        with save_cols[1]:
            st.caption("Use reviewer/sign-off fields for workflow evidence only; identity is not cryptographically verified in the public beta.")

with tab_requests:
    requests_df = evidence_request_dataframe(saved_df)
    st.caption(
        "This register can be sent to control owners as a structured evidence request list. It is generated from the current control summaries and evidence examples, not from invented requirements."
    )
    if requests_df.empty:
        st.success("No open evidence requests in the saved workplan.")
    else:
        st.dataframe(requests_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download evidence request register CSV",
            data=requests_df.to_csv(index=False).encode("utf-8"),
            file_name="bgnexa_evidence_request_register.csv",
            mime="text/csv",
        )

with tab_findings:
    findings_df = findings_dataframe(saved_df)
    st.caption(
        "A finding appears here only after a user records a finding title, severity or management response. BGNexa does not automatically convert readiness gaps into internal-audit findings."
    )
    if findings_df.empty:
        st.info("No findings or management actions have been recorded in this session.")
    else:
        st.dataframe(findings_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download findings & actions CSV",
            data=findings_df.to_csv(index=False).encode("utf-8"),
            file_name="bgnexa_findings_and_actions.csv",
            mime="text/csv",
        )

with tab_trail:
    audit_events = st.session_state.get("assurance_audit_events", [])
    st.caption("This is an append-only session change log for assurance-workspace edits. It is not an identity signature or immutable server audit log.")
    if audit_events:
        audit_df = pd.DataFrame(audit_events)
        st.dataframe(audit_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download session audit trail CSV",
            data=audit_df.to_csv(index=False).encode("utf-8"),
            file_name="bgnexa_assurance_audit_trail.csv",
            mime="text/csv",
        )
    else:
        st.info("No saved workplan changes have been recorded yet.")

with tab_exports:
    metadata = {
        "organisation": organisation_name,
        "engagement_title": engagement_title,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "prepared_by": prepared_by,
        "independent_reviewer": independent_reviewer,
        "objective": audit_objective,
        "session_only": True,
    }
    assessment_snapshot = build_assessment_snapshot(
        bundle,
        profile,
        validations=st.session_state.get("review_validations", []),
        source_records=st.session_state.get("evidence_source_records", []),
    )
    assurance_snapshot = build_assurance_snapshot(
        saved_df,
        metadata=metadata,
        assessment_fingerprint=current_fingerprint,
        assessment_sha256=assessment_snapshot["sha256"],
        audit_events=st.session_state.get("assurance_audit_events", []),
    )

    export_cols = st.columns(3)
    export_cols[0].download_button(
        "Download assurance workplan CSV",
        data=saved_df.to_csv(index=False).encode("utf-8"),
        file_name="bgnexa_assurance_workplan.csv",
        mime="text/csv",
        use_container_width=True,
    )
    export_cols[1].download_button(
        "Download assurance snapshot JSON",
        data=json.dumps(assurance_snapshot, indent=2).encode("utf-8"),
        file_name="bgnexa_assurance_snapshot.json",
        mime="application/json",
        use_container_width=True,
    )
    export_cols[2].download_button(
        "Download linked assessment snapshot",
        data=json.dumps(assessment_snapshot, indent=2).encode("utf-8"),
        file_name="bgnexa_readiness_snapshot.json",
        mime="application/json",
        use_container_width=True,
    )

    st.write(f"**Assurance snapshot SHA-256:** `{assurance_snapshot['sha256']}`")
    st.write(f"**Linked readiness snapshot SHA-256:** `{assessment_snapshot['sha256']}`")
    if workspace_stale:
        st.error("The saved assurance workplan is stale relative to the current assessment. Rebuild before using these exports for review.")
