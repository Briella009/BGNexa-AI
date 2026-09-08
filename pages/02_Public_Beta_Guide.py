from __future__ import annotations

import streamlit as st

from src.ui import apply_product_ui, info_card, render_flow, render_hero


st.set_page_config(page_title="BGNexa AI · Public Beta Guide", page_icon="🧭", layout="wide")
apply_product_ui()

render_hero(
    "Public Beta Guide",
    "A safe, practical route for GRC analysts, internal auditors, cybersecurity assurance teams and control owners to evaluate BGNexa AI.",
    badge="v0.5.1 · public beta",
)
render_flow(active_step=4)

st.markdown("## What BGNexa is for")
cols = st.columns(3)
with cols[0]:
    st.markdown(info_card("Readiness assessment", "Map supplied evidence to selected requirements while preserving evidence quality, provenance, uncertainty and human review."), unsafe_allow_html=True)
with cols[1]:
    st.markdown(info_card("Assurance workflow", "Turn assessment results into evidence requests, control tests, findings, management actions, retest and closure work."), unsafe_allow_html=True)
with cols[2]:
    st.markdown(info_card("Cross-framework reuse", "Identify where the same evidence may support review across multiple frameworks without claiming the requirements are equivalent."), unsafe_allow_html=True)

st.markdown("## 10-minute safe demo")
st.markdown(
    """
1. Return to **BGNexa AI** in the left navigation.
2. Keep **Use fictional sample policies** enabled.
3. Select the framework packs you want to explore.
4. Leave AI review off for a completely local, deterministic walkthrough, or enable it only if a configured provider is available.
5. Run the readiness assessment.
6. Inspect **Evidence quality**, the **Priority remediation queue**, and at least one control's retrieved evidence.
7. Use **Human validation** on one control to see how a reviewer decision changes the readiness state.
8. Open **Assurance Workspace** from the left navigation.
9. Assign an owner, record a test result, and save the workspace change.
10. Export the workplan or tamper-evident JSON snapshot before ending the session.
"""
)

st.markdown("## Suggested beta test scenarios")
scenario_cols = st.columns(2)
with scenario_cols[0]:
    st.markdown(
        """
**Scenario A — GRC evidence gap review**

Use the fictional evidence pack and answer:
- Which controls are not evidenced?
- Which controls merely have policy intent?
- Are any uploaded sources stale or undated?
- Does the remediation queue make sense?
"""
    )
    st.markdown(
        """
**Scenario B — Internal audit workplan**

From the Assurance Workspace:
- assign control and assurance owners;
- record a sample reference and test result;
- create one finding manually;
- capture management response and action owner;
- export the findings register.
"""
    )
with scenario_cols[1]:
    st.markdown(
        """
**Scenario C — Cross-framework review**

Select at least two framework packs and inspect the capability view. Confirm that BGNexa presents evidence-reuse opportunities without implying legal or control equivalence.
"""
    )
    st.markdown(
        """
**Scenario D — AI failure safety**

If AI review is enabled and the external provider becomes unavailable or rate-limited, confirm the assessment remains usable and unresolved items fall back to human review rather than being silently marked supported.
"""
    )

st.markdown("## Data-safety rules for testers")
st.warning(
    "Use fictional, anonymised or explicitly authorised evidence in the public beta. Do not upload secrets, credentials, production customer records, privileged legal material, regulated personal data, or confidential audit workpapers unless your organisation has approved the deployment and external-provider configuration."
)

st.markdown("## What a good beta result looks like")
st.markdown(
    """
A useful test is not one where every control turns green. A useful test is one where BGNexa:

- finds the evidence that a qualified reviewer would expect it to find;
- does **not** treat a policy statement as proof of operating effectiveness where implementation evidence is required;
- exposes uncertainty instead of inventing facts;
- makes missing, weak, stale or unreadable evidence obvious;
- preserves the distinction between readiness, legal compliance, certification and an audit opinion;
- gives auditors and GRC teams a clearer next action than a generic percentage score.
"""
)

st.markdown("## Beta feedback template")
st.code(
    """Role / team:
Frameworks tested:
Evidence type used: fictional / anonymised / authorised real-world

What worked well:

What was confusing:

Evidence BGNexa retrieved incorrectly or missed:

Control status you disagreed with and why:

Assurance-workspace feature that would save you the most time:

Any security, privacy or trust concern:

Would you use this in a real GRC/internal-audit workflow? Why or why not:
""",
    language="text",
)

st.info(
    "Public beta scope: session-based workspace, human-governed readiness and assurance support. BGNexa is not yet a multi-tenant production audit-management system and does not issue legal, regulatory, certification or audit conclusions."
)
