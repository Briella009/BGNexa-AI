from __future__ import annotations

import streamlit as st


_PRODUCT_CSS = """
<style>
:root {
  --bgnexa-ink: #17233C;
  --bgnexa-muted: #64748B;
  --bgnexa-coral: #FF4D6D;
  --bgnexa-orange: #FF8A3D;
  --bgnexa-indigo: #5B5DF0;
  --bgnexa-blue: #2563EB;
  --bgnexa-bg: #F8FBFF;
  --bgnexa-card: #FFFFFF;
  --bgnexa-line: #E5EAF2;
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 88% 3%, rgba(91,93,240,.09), transparent 28%),
    radial-gradient(circle at 6% 15%, rgba(255,77,109,.08), transparent 24%),
    var(--bgnexa-bg);
  color: var(--bgnexa-ink);
}
[data-testid="stHeader"] { background: rgba(248,251,255,.88); }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#FFFFFF 0%,#F3F7FF 100%);
  border-right: 1px solid var(--bgnexa-line);
}
.block-container { max-width: 1500px; padding-top: 1.6rem; padding-bottom: 3rem; }
h1,h2,h3 { color: var(--bgnexa-ink); letter-spacing: -.02em; }
p,li,label { line-height: 1.55; }

[data-testid="stMetric"] {
  background: rgba(255,255,255,.92);
  border: 1px solid var(--bgnexa-line);
  border-radius: 16px;
  padding: .85rem 1rem;
  box-shadow: 0 8px 24px rgba(23,35,60,.05);
}
[data-testid="stMetricLabel"] { color: var(--bgnexa-muted); }

[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
  background: #FFFFFF;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--bgnexa-line);
}

.stButton > button, .stDownloadButton > button {
  border-radius: 12px;
  min-height: 2.65rem;
  font-weight: 700;
  border: 1px solid #DDE4EF;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(100deg,var(--bgnexa-coral),var(--bgnexa-orange));
  border: 0;
  box-shadow: 0 10px 22px rgba(255,77,109,.18);
}

[data-testid="stTabs"] button { font-weight: 700; }
[data-testid="stExpander"] {
  border-radius: 12px;
  border-color: var(--bgnexa-line);
  background: rgba(255,255,255,.72);
}

.bgnexa-hero {
  padding: 1.45rem 1.55rem;
  border-radius: 22px;
  background: linear-gradient(105deg,#FF4D6D 0%,#FF8A3D 43%,#5B5DF0 100%);
  color: white;
  box-shadow: 0 18px 40px rgba(91,93,240,.16);
  margin-bottom: 1.05rem;
}
.bgnexa-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: .45rem;
  font-size: .77rem;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
  opacity: .94;
}
.bgnexa-hero h1 {
  color: white;
  font-size: clamp(2rem,4vw,3.25rem);
  line-height: 1.04;
  margin: .55rem 0 .45rem;
}
.bgnexa-hero p { margin: 0; font-size: 1.04rem; max-width: 900px; color: rgba(255,255,255,.94); }
.bgnexa-badge {
  display: inline-block;
  margin-top: .85rem;
  padding: .3rem .62rem;
  border-radius: 999px;
  background: rgba(255,255,255,.18);
  border: 1px solid rgba(255,255,255,.32);
  font-size: .78rem;
  font-weight: 700;
}

.bgnexa-flow {
  display: grid;
  grid-template-columns: repeat(4,minmax(0,1fr));
  gap: .65rem;
  margin: .7rem 0 1.2rem;
}
.bgnexa-step {
  background: rgba(255,255,255,.9);
  border: 1px solid var(--bgnexa-line);
  border-radius: 15px;
  padding: .8rem .9rem;
  min-height: 78px;
}
.bgnexa-step strong { display:block; color:var(--bgnexa-ink); margin-bottom:.18rem; }
.bgnexa-step span { color:var(--bgnexa-muted); font-size:.84rem; }
.bgnexa-step.active { border-color:#FF9AAF; box-shadow:0 8px 20px rgba(255,77,109,.08); }
.bgnexa-step .num {
  display:inline-grid; place-items:center; width:24px; height:24px; border-radius:999px;
  margin-right:.35rem; background:#FFF0F3; color:#C92749; font-weight:800; font-size:.78rem;
}

.bgnexa-card {
  background: rgba(255,255,255,.92);
  border: 1px solid var(--bgnexa-line);
  border-radius: 18px;
  padding: 1rem 1.05rem;
  box-shadow: 0 10px 26px rgba(23,35,60,.045);
  height: 100%;
}
.bgnexa-card h4 { margin:0 0 .3rem; color:var(--bgnexa-ink); }
.bgnexa-card p { margin:0; color:var(--bgnexa-muted); font-size:.9rem; }
.bgnexa-kicker { color:var(--bgnexa-muted); font-size:.92rem; margin-top:-.2rem; }

@media (max-width: 900px) {
  .bgnexa-flow { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 560px) {
  .bgnexa-flow { grid-template-columns: 1fr; }
  .block-container { padding-left: .85rem; padding-right: .85rem; }
}
</style>
"""


def apply_product_ui() -> None:
    st.markdown(_PRODUCT_CSS, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, *, eyebrow: str = "BGNexa AI", badge: str = "Public beta") -> None:
    st.markdown(
        f"""
        <section class="bgnexa-hero">
          <div class="bgnexa-eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
          <span class="bgnexa-badge">{badge}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_flow(active_step: int = 1) -> None:
    steps = [
        (1, "Scope", "Choose the organisation profile and framework packs."),
        (2, "Evidence", "Upload authorised evidence or use the fictional demo pack."),
        (3, "Assess", "Review readiness, evidence quality and unresolved decisions."),
        (4, "Assure", "Test controls, request evidence and track findings/actions."),
    ]
    cards = []
    for number, title, text in steps:
        active = " active" if number == active_step else ""
        cards.append(
            f'<div class="bgnexa-step{active}"><strong><span class="num">{number}</span>{title}</strong><span>{text}</span></div>'
        )
    st.markdown(f'<div class="bgnexa-flow">{"".join(cards)}</div>', unsafe_allow_html=True)


def info_card(title: str, text: str) -> str:
    return f'<div class="bgnexa-card"><h4>{title}</h4><p>{text}</p></div>'
