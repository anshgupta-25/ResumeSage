"""
ResumeSage AI — Streamlit front end.

Two tools over the same parsed resume:
  • Parse    — messy resume text into a structured, readable profile.
  • Job Fit  — score that resume against a specific job description.

All prompts and model calls live in core.py; this file is presentation only.
"""

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ResumeSageBot.core import MODEL_NAME, extract_resume, read_resume_file, score_fit

st.set_page_config(page_title="ResumeSage AI", page_icon="📄", layout="wide")

# ── Theme ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    background: transparent !important;
    font-family: 'Inter', sans-serif;
    color: #e6e1d8;
}
[data-testid="stAppViewContainer"] { background: #0d0b14 !important; min-height: 100vh; }
#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* warm ambient wash */
.amber-wash {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
        radial-gradient(ellipse 55% 45% at 15% 5%,  rgba(245,165,36,0.09) 0%, transparent 62%),
        radial-gradient(ellipse 45% 50% at 85% 75%, rgba(167,139,250,0.08) 0%, transparent 62%),
        radial-gradient(ellipse 40% 40% at 50% 50%, rgba(245,165,36,0.03) 0%, transparent 70%);
}
/* faint ruled-paper lines */
.paper-rule {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background: repeating-linear-gradient(180deg,
        transparent 0px, transparent 31px,
        rgba(230,225,216,0.016) 31px, rgba(230,225,216,0.016) 32px);
}

.wrap { position: relative; z-index: 1; max-width: 1040px; margin: 0 auto; padding: 0 1.5rem 6rem; }

/* ══ HERO ══ */
.hero { padding: 3.2rem 0 2.2rem; text-align: center; }
.eyebrow {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 0.24em; text-transform: uppercase;
    color: #f5a524; opacity: 0.75; margin-bottom: 18px;
}
.title {
    font-family: 'Sora', sans-serif; font-weight: 800;
    font-size: clamp(2.6rem, 6.5vw, 4.6rem);
    letter-spacing: -0.035em; line-height: 0.98; color: #f7f3ec;
}
.title .accent {
    background: linear-gradient(100deg, #f5a524 0%, #ffcf70 45%, #a78bfa 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.sub {
    font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
    color: #5b5470; margin-top: 14px; letter-spacing: 0.02em;
}

/* ══ STATUS BAR ══ */
.status {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 18px; margin-bottom: 1.8rem;
    background: rgba(245,165,36,0.05);
    border: 1px solid rgba(245,165,36,0.13); border-radius: 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 0.1em; color: #6b6480;
}
.dot { display:inline-block; width:7px; height:7px; border-radius:50%;
       margin-right:9px; background:#f5a524; animation: blink 2.2s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.25} }
.status .m { color: #a78bfa; }

/* ══ CARDS ══ */
.card {
    background: rgba(255,255,255,0.022);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px; padding: 1.3rem 1.5rem;
    margin-bottom: 1rem; position: relative; overflow: hidden;
}
.card::after {
    content:''; position:absolute; top:0; left:0; right:0; height:1.5px;
    background: linear-gradient(90deg, #f5a524, transparent); opacity:0.45;
}
.card.violet::after { background: linear-gradient(90deg, #a78bfa, transparent); }
.card-label {
    font-family: 'JetBrains Mono', monospace; font-size: 9px;
    letter-spacing: 0.17em; text-transform: uppercase;
    color: #5b5470; margin-bottom: 10px;
}
.card-value { font-size: 0.9rem; color: #b8b1c4; line-height: 1.65; }
.card-value strong { color: #f7f3ec; font-weight: 600; }

/* ══ PROFILE HEADER ══ */
.profile {
    padding: 2rem 2.2rem; margin-bottom: 1.1rem;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 22px; position: relative; overflow: hidden;
}
.profile::before {
    content:''; position:absolute; inset:0;
    background: linear-gradient(135deg, rgba(245,165,36,0.07) 0%, transparent 55%, rgba(167,139,250,0.05) 100%);
}
.profile > * { position: relative; }
.pname {
    font-family: 'Sora', sans-serif; font-weight: 800;
    font-size: clamp(1.7rem, 3.6vw, 2.5rem);
    letter-spacing: -0.03em; color: #f7f3ec; line-height: 1.06;
}
.phead { font-size: 0.95rem; color: #f5a524; margin-top: 6px; font-weight: 500; }
.pmeta { display:flex; flex-wrap:wrap; gap:8px; margin-top: 16px; }
.tag {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    padding: 4px 11px; border-radius: 6px; letter-spacing: 0.05em;
    background: rgba(245,165,36,0.09); border: 1px solid rgba(245,165,36,0.22); color: #f5a524;
}
.tag.v { background: rgba(167,139,250,0.09); border-color: rgba(167,139,250,0.22); color: #a78bfa; }

/* summary */
.summary {
    border-left: 3px solid #f5a524; border-radius: 0 16px 16px 0;
    padding: 1.1rem 1.5rem; margin-bottom: 1.1rem;
    background: rgba(245,165,36,0.035);
}
.summary .hd {
    font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:0.17em;
    text-transform:uppercase; color:#f5a524; opacity:0.65; margin-bottom:9px;
}
.summary .bd { font-size:0.92rem; line-height:1.8; color:#a89fb8; font-style: italic; }

/* chips */
.chips { display:flex; flex-wrap:wrap; gap:6px; }
.chip {
    font-family:'JetBrains Mono',monospace; font-size:10px;
    padding:3.5px 10px; border-radius:5px;
    background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
    color:#7d768f;
}
.chip.a { background:rgba(245,165,36,0.09); border-color:rgba(245,165,36,0.2); color:#f5a524; }
.chip.v { background:rgba(167,139,250,0.09); border-color:rgba(167,139,250,0.2); color:#a78bfa; }
.chip.g { background:rgba(74,222,128,0.09); border-color:rgba(74,222,128,0.2); color:#4ade80; }
.chip.r { background:rgba(248,113,113,0.09); border-color:rgba(248,113,113,0.2); color:#f87171; }

/* timeline */
.tl { border-left: 2px solid rgba(245,165,36,0.22); padding-left: 1.2rem; margin-left: 4px; }
.tl-item { position: relative; padding-bottom: 1.3rem; }
.tl-item:last-child { padding-bottom: 0; }
.tl-item::before {
    content:''; position:absolute; left:-1.68rem; top:5px;
    width:9px; height:9px; border-radius:50%;
    background:#f5a524; box-shadow:0 0 0 3px rgba(245,165,36,0.16);
}
.tl-role { font-family:'Sora',sans-serif; font-weight:600; font-size:1rem; color:#f7f3ec; }
.tl-co { font-size:0.85rem; color:#a78bfa; margin-top:2px; }
.tl-when {
    font-family:'JetBrains Mono',monospace; font-size:9.5px;
    color:#5b5470; letter-spacing:0.06em; margin-top:4px;
}
.tl-hi { margin-top:9px; }
.tl-hi div {
    font-size:0.85rem; color:#8b8399;
    line-height:1.65; padding:3px 0 3px 15px; position:relative;
}
.tl-hi div::before { content:'▸'; position:absolute; left:0; color:#f5a524; font-size:0.65rem; top:7px; }

/* list rows */
.row {
    display:flex; gap:10px; align-items:flex-start;
    padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.045);
    font-size:0.86rem; color:#8b8399; line-height:1.6;
}
.row:last-child { border-bottom:none; }
.bul { flex-shrink:0; font-size:0.7rem; margin-top:4px; color:#f5a524; }
.bul.v { color:#a78bfa; } .bul.g { color:#4ade80; } .bul.r { color:#f87171; }

/* ══ SCORE GAUGE ══ */
.gauge-wrap { display:flex; align-items:center; gap:2rem; flex-wrap:wrap;
              padding:2rem 2.2rem; margin-bottom:1.1rem;
              background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.07);
              border-radius:22px; }
.gauge {
    width:132px; height:132px; border-radius:50%; flex-shrink:0;
    display:grid; place-items:center; position:relative;
}
.gauge::after {
    content:''; position:absolute; inset:9px; border-radius:50%; background:#0d0b14;
}
.gauge-inner { position:relative; z-index:1; text-align:center; }
.gauge-num { font-family:'Sora',sans-serif; font-weight:800; font-size:2.1rem; color:#f7f3ec; line-height:1; }
.gauge-den { font-family:'JetBrains Mono',monospace; font-size:9px; color:#5b5470; letter-spacing:0.14em; margin-top:5px; }
.verdict-t { font-family:'Sora',sans-serif; font-weight:700; font-size:1.5rem; letter-spacing:-0.02em; }
.verdict-s { font-size:0.88rem; color:#8b8399; line-height:1.7; margin-top:8px; max-width:520px; }

/* section heading */
.sec {
    font-family:'JetBrains Mono',monospace; font-size:9.5px;
    letter-spacing:0.2em; text-transform:uppercase; color:#f5a524;
    opacity:0.6; margin:1.9rem 0 0.8rem;
}

/* ══ STREAMLIT WIDGETS ══ */
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(245,165,36,0.18) !important;
    border-radius: 14px !important; color: #e6e1d8 !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.88rem !important;
    line-height: 1.7 !important; caret-color: #f5a524 !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(245,165,36,0.45) !important;
    box-shadow: 0 0 0 3px rgba(245,165,36,0.08) !important; outline: none !important;
}
[data-testid="stTextArea"] textarea::placeholder { color: #3a3450 !important; }

.stButton > button {
    font-family: 'Sora', sans-serif !important; font-weight: 700 !important;
    font-size: 0.92rem !important; letter-spacing: 0.05em !important;
    color: #14100a !important;
    background: linear-gradient(95deg, #f5a524, #ffcf70) !important;
    border: none !important; border-radius: 12px !important;
    padding: 0.68rem 2rem !important; width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 22px rgba(245,165,36,0.24) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 34px rgba(245,165,36,0.38) !important;
}

.stTabs [data-baseweb="tab-list"] { gap: 6px; background: transparent; border-bottom: 1px solid rgba(255,255,255,0.06); }
.stTabs [data-baseweb="tab"] {
    font-family:'JetBrains Mono',monospace !important; font-size:10.5px !important;
    letter-spacing:0.12em !important; color:#5b5470 !important;
    background: transparent !important; border-radius: 10px 10px 0 0 !important;
}
.stTabs [aria-selected="true"] { color:#f5a524 !important; background: rgba(245,165,36,0.06) !important; }

[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(245,165,36,0.22) !important; border-radius: 14px !important;
}
[data-testid="stFileUploader"] small { color:#5b5470 !important; }

[data-testid="stExpander"] {
    background: rgba(0,0,0,0.28) !important;
    border: 1px solid rgba(245,165,36,0.08) !important;
    border-radius: 14px !important; margin-top: 1rem;
}
[data-testid="stExpander"] details summary {
    font-family:'JetBrains Mono',monospace !important; font-size:10.5px !important;
    color:#5b5470 !important; letter-spacing:0.1em !important;
}
.json-pre {
    background:#07050d; border-radius:10px; padding:1.2rem;
    font-family:'JetBrains Mono',monospace; font-size:0.72rem;
    color:#4a4460; overflow-x:auto; white-space:pre; line-height:1.7; margin-top:8px;
}
[data-testid="stSpinner"] p {
    color:#5b5470 !important; font-family:'JetBrains Mono',monospace !important;
    font-size:10px !important; letter-spacing:0.1em !important;
}
.empty { text-align:center; padding:3.5rem 1rem; }
.empty .i { font-size:2.8rem; opacity:0.14; margin-bottom:14px; }
.empty .t { font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:#332e47; line-height:1.8; }

::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(245,165,36,0.18); border-radius:3px; }
</style>

<div class="amber-wash"></div>
<div class="paper-rule"></div>
""",
    unsafe_allow_html=True,
)

# ── State ──────────────────────────────────────────────────────────────────────
for key in ("resume", "fit", "resume_text"):
    st.session_state.setdefault(key, None)


# ── Render helpers ─────────────────────────────────────────────────────────────

def chips(items, style="") -> str:
    if not items:
        return "<span style='color:#332e47;font-size:10px'>—</span>"
    if not isinstance(items, list):
        items = [items]
    return "".join(f'<span class="chip {style}">{i}</span>' for i in items)


def rows(items, bullet="") -> str:
    if not items:
        return "<span style='color:#332e47;font-size:10px'>—</span>"
    if not isinstance(items, list):
        items = [items]
    return "".join(
        f'<div class="row"><span class="bul {bullet}">▸</span>{i}</div>' for i in items
    )


def dash(value, fallback="—"):
    return fallback if value in (None, "", []) else value


def score_color(score: int) -> str:
    if score >= 75:
        return "#4ade80"
    if score >= 50:
        return "#f5a524"
    return "#f87171"


# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="wrap">', unsafe_allow_html=True)
st.markdown(
    """
<div class="hero">
    <div class="eyebrow">◆ structured resume intelligence</div>
    <div class="title">Resume<span class="accent">Sage</span></div>
    <div class="sub">// paste a resume → get a parsed profile and an honest job-fit score //</div>
</div>
<div class="status">
    <div><span class="dot"></span>SYSTEM READY</div>
    <div>MODEL <span class="m">"""
    + MODEL_NAME
    + """</span></div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Input ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">◆ resume input</div>', unsafe_allow_html=True)

uploaded = st.file_uploader("resume file", type=["txt", "md", "pdf"], label_visibility="collapsed")

file_text = ""
if uploaded is not None:
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        file_text = "\n".join(
            page.extract_text() or "" for page in PdfReader(uploaded).pages
        )
    else:
        file_text = uploaded.getvalue().decode("utf-8", errors="ignore")
    st.success(f"Loaded **{uploaded.name}** — {len(file_text):,} characters")

resume_text = st.text_area(
    "resume text",
    value=file_text,
    placeholder="Paste the resume here — name, contact, skills, work history, education, "
    "projects. Formatting does not matter; ResumeSage handles messy text.",
    height=190,
    label_visibility="collapsed",
)

tab_parse, tab_fit = st.tabs(["◆  PARSE RESUME", "◆  JOB FIT SCORE"])

# ── Tab 1: parse ───────────────────────────────────────────────────────────────
with tab_parse:
    if st.button("◆  PARSE RESUME", key="btn_parse"):
        if not resume_text.strip():
            st.warning("Paste a resume or upload a file first.")
        else:
            with st.spinner("PARSING RESUME ···"):
                try:
                    st.session_state.resume = extract_resume(resume_text).model_dump()
                    st.session_state.resume_text = resume_text
                except Exception as exc:  # noqa: BLE001 — surface any model/parse error
                    st.session_state.resume = None
                    st.error(f"Could not parse that resume: {exc}")

    data = st.session_state.resume

    if not data:
        st.markdown(
            '<div class="empty"><div class="i">◆</div>'
            "<div class=\"t\">no resume parsed yet<br>paste or upload one above to begin</div></div>",
            unsafe_allow_html=True,
        )
    else:
        name = dash(data.get("candidate_name"), "UNNAMED CANDIDATE")
        headline = dash(data.get("headline"), "")

        meta = []
        for icon, key in (("✉", "email"), ("☎", "phone"), ("⌖", "location")):
            if data.get(key):
                meta.append(f'<span class="tag">{icon} {data[key]}</span>')
        if data.get("seniority_level"):
            meta.append(f'<span class="tag v">◆ {data["seniority_level"]}</span>')
        if data.get("total_experience_years") is not None:
            meta.append(f'<span class="tag v">⏱ {data["total_experience_years"]} yrs</span>')
        for link in (data.get("links") or [])[:3]:
            meta.append(f'<span class="tag">🔗 {link}</span>')

        st.markdown(
            f"""
<div class="profile">
    <div class="pname">{name}</div>
    {f'<div class="phead">{headline}</div>' if headline else ''}
    <div class="pmeta">{''.join(meta)}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if data.get("summary"):
            st.markdown(
                f'<div class="summary"><div class="hd">candidate summary</div>'
                f'<div class="bd">{data["summary"]}</div></div>',
                unsafe_allow_html=True,
            )

        # skills
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div class="card"><div class="card-label">Technical Skills</div>'
                f'<div class="chips">{chips(data.get("technical_skills"), "a")}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="card violet"><div class="card-label">Soft Skills</div>'
                f'<div class="chips">{chips(data.get("soft_skills"), "v")}</div></div>',
                unsafe_allow_html=True,
            )

        # experience timeline
        if data.get("experience"):
            st.markdown('<div class="sec">◆ work experience</div>', unsafe_allow_html=True)
            items = []
            for job in data["experience"]:
                where = " · ".join(
                    x for x in [job.get("company"), job.get("location")] if x
                )
                highs = "".join(f"<div>{h}</div>" for h in (job.get("highlights") or []))
                items.append(
                    f'<div class="tl-item">'
                    f'<div class="tl-role">{dash(job.get("role"))}</div>'
                    f'<div class="tl-co">{where or "—"}</div>'
                    f'<div class="tl-when">{dash(job.get("duration"))}</div>'
                    f'<div class="tl-hi">{highs}</div></div>'
                )
            st.markdown(f'<div class="tl">{"".join(items)}</div>', unsafe_allow_html=True)

        # education + projects
        if data.get("education"):
            st.markdown('<div class="sec">◆ education</div>', unsafe_allow_html=True)
            for edu in data["education"]:
                extra = " · ".join(
                    x for x in [edu.get("year"), edu.get("score")] if x
                )
                st.markdown(
                    f'<div class="card"><div class="card-label">{dash(edu.get("institution"))}</div>'
                    f'<div class="card-value"><strong>{dash(edu.get("degree"))}</strong>'
                    f'{f" — {extra}" if extra else ""}</div></div>',
                    unsafe_allow_html=True,
                )

        if data.get("projects"):
            st.markdown('<div class="sec">◆ projects</div>', unsafe_allow_html=True)
            for proj in data["projects"]:
                st.markdown(
                    f'<div class="card violet"><div class="card-label">{dash(proj.get("name"))}</div>'
                    f'<div class="card-value">{dash(proj.get("description"))}</div>'
                    f'<div class="chips" style="margin-top:10px">{chips(proj.get("tech_stack"), "v")}</div></div>',
                    unsafe_allow_html=True,
                )

        # judgement
        st.markdown('<div class="sec">◆ recruiter read</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(
                f'<div class="card"><div class="card-label">Strengths</div>'
                f'{rows(data.get("strengths"), "g")}</div>',
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f'<div class="card violet"><div class="card-label">Gaps</div>'
                f'{rows(data.get("gaps"), "r")}</div>',
                unsafe_allow_html=True,
            )

        c5, c6 = st.columns(2)
        with c5:
            st.markdown(
                f'<div class="card"><div class="card-label">Suggested Roles</div>'
                f'<div class="chips">{chips(data.get("suggested_roles"), "a")}</div></div>',
                unsafe_allow_html=True,
            )
        with c6:
            st.markdown(
                f'<div class="card violet"><div class="card-label">ATS Keywords</div>'
                f'<div class="chips">{chips(data.get("keywords"))}</div></div>',
                unsafe_allow_html=True,
            )

        if data.get("certifications") or data.get("achievements"):
            c7, c8 = st.columns(2)
            with c7:
                st.markdown(
                    f'<div class="card"><div class="card-label">Certifications</div>'
                    f'{rows(data.get("certifications"))}</div>',
                    unsafe_allow_html=True,
                )
            with c8:
                st.markdown(
                    f'<div class="card violet"><div class="card-label">Achievements</div>'
                    f'{rows(data.get("achievements"), "v")}</div>',
                    unsafe_allow_html=True,
                )

        with st.expander("◆  RAW JSON OUTPUT"):
            st.markdown(
                f'<div class="json-pre">{json.dumps(data, indent=2, ensure_ascii=False)}</div>',
                unsafe_allow_html=True,
            )

# ── Tab 2: job fit ─────────────────────────────────────────────────────────────
with tab_fit:
    job_description = st.text_area(
        "job description",
        placeholder="Paste the job description here — responsibilities, required skills, "
        "years of experience, nice-to-haves.",
        height=170,
        label_visibility="collapsed",
    )

    if st.button("◆  SCORE THE MATCH", key="btn_fit"):
        if not resume_text.strip():
            st.warning("Paste a resume above first.")
        elif not job_description.strip():
            st.warning("Paste a job description to score against.")
        else:
            with st.spinner("SCORING MATCH ···"):
                try:
                    st.session_state.fit = score_fit(resume_text, job_description).model_dump()
                except Exception as exc:  # noqa: BLE001 — surface any model/parse error
                    st.session_state.fit = None
                    st.error(f"Could not score that match: {exc}")

    fit = st.session_state.fit

    if not fit:
        st.markdown(
            '<div class="empty"><div class="i">◆</div>'
            "<div class=\"t\">no match scored yet<br>add a job description above to compare</div></div>",
            unsafe_allow_html=True,
        )
    else:
        score = fit.get("match_score") or 0
        col = score_color(score)
        verdict = dash(fit.get("verdict"), "No verdict")
        title = dash(fit.get("job_title"), "the role")

        st.markdown(
            f"""
<div class="gauge-wrap">
    <div class="gauge" style="background: conic-gradient({col} 0turn {score / 100}turn, rgba(255,255,255,0.06) {score / 100}turn 1turn);">
        <div class="gauge-inner">
            <div class="gauge-num" style="color:{col}">{score}</div>
            <div class="gauge-den">MATCH SCORE</div>
        </div>
    </div>
    <div>
        <div class="verdict-t" style="color:{col}">{verdict}</div>
        <div class="verdict-s">Scored against <strong style="color:#f7f3ec">{title}</strong>.
        {dash(fit.get("experience_verdict"), "")}</div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # matched skills
        matched = fit.get("matched_skills") or []
        have = [m for m in matched if m.get("present")]
        lack = [m for m in matched if not m.get("present")]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div class="card"><div class="card-label">Skills Evidenced ({len(have)})</div>'
                f'<div class="chips">{chips([m.get("skill") for m in have], "g")}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            missing = fit.get("missing_skills") or [m.get("skill") for m in lack]
            st.markdown(
                f'<div class="card violet"><div class="card-label">Missing Skills ({len(missing)})</div>'
                f'<div class="chips">{chips(missing, "r")}</div></div>',
                unsafe_allow_html=True,
            )

        if fit.get("transferable_skills"):
            st.markdown(
                f'<div class="card"><div class="card-label">Transferable / Partial Cover</div>'
                f'<div class="chips">{chips(fit["transferable_skills"], "a")}</div></div>',
                unsafe_allow_html=True,
            )

        if have:
            st.markdown('<div class="sec">◆ evidence trail</div>', unsafe_allow_html=True)
            for m in have:
                if m.get("evidence"):
                    st.markdown(
                        f'<div class="card"><div class="card-label">{m.get("skill")}</div>'
                        f'<div class="card-value">{m["evidence"]}</div></div>',
                        unsafe_allow_html=True,
                    )

        st.markdown('<div class="sec">◆ how to close the gap</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(
                f'<div class="card"><div class="card-label">Resume Improvements</div>'
                f'{rows(fit.get("resume_improvements"), "g")}</div>',
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f'<div class="card violet"><div class="card-label">Likely Interview Questions</div>'
                f'{rows(fit.get("interview_questions"), "v")}</div>',
                unsafe_allow_html=True,
            )

        with st.expander("◆  RAW JSON OUTPUT"):
            st.markdown(
                f'<div class="json-pre">{json.dumps(fit, indent=2, ensure_ascii=False)}</div>',
                unsafe_allow_html=True,
            )

st.markdown("</div>", unsafe_allow_html=True)
