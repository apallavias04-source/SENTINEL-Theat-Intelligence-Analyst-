import streamlit as st
import requests
import time
import re

API_URL = "https://sentinel-theat-intelligence-analyst.onrender.com"

st.set_page_config(
    page_title="SENTINEL — Threat Intelligence",
    page_icon="🛡️",
    layout="wide"
)

# ── Session state ─────────────────────────────────────────────────
if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None


def set_topic(value):
    st.session_state.topic_input = value


# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg-void: #0A0E17;
    --bg-panel: #121826;
    --bg-panel-alt: #171E2E;
    --border: #232B3D;
    --text-primary: #E6EDF3;
    --text-muted: #7C8AA3;
    --accent-cyan: #4FD1C5;
    --accent-amber: #F5A623;
    --accent-red: #E5484D;
    --accent-green: #34D399;
}

.stApp {
    background:
        linear-gradient(var(--bg-void), var(--bg-void)),
        repeating-linear-gradient(0deg, rgba(79,209,197,0.035) 0px, rgba(79,209,197,0.035) 1px, transparent 1px, transparent 32px),
        repeating-linear-gradient(90deg, rgba(79,209,197,0.035) 0px, rgba(79,209,197,0.035) 1px, transparent 1px, transparent 32px);
    color: var(--text-primary);
    font-family: 'Inter', sans-serif;
}

#MainMenu, footer, header {visibility: hidden;}

.block-container {max-width: 900px; padding-top: 2rem;}

/* ── Hero ── */
.hero {
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.4rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: "";
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
    animation: scan 4s linear infinite;
}
@keyframes scan { to { left: 100%; } }

.hero-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.1rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: var(--text-primary);
    margin: 0;
}
.hero-title span { color: var(--accent-cyan); }
.hero-sub {
    color: var(--text-muted);
    font-size: 0.92rem;
    margin-top: 0.35rem;
}
.status-pill {
    display: inline-flex; align-items: center; gap: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem; letter-spacing: 0.08em;
    color: var(--accent-green);
    margin-top: 0.7rem;
}
.status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent-green);
    box-shadow: 0 0 8px var(--accent-green);
    animation: pulse 1.6s ease-in-out infinite;
}
@keyframes pulse { 0%,100% {opacity:1;} 50% {opacity:0.35;} }

/* ── Chips ── */
div[data-testid="column"] .stButton button {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    color: var(--text-muted);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    border-radius: 4px;
    padding: 0.3rem 0.7rem;
}
div[data-testid="column"] .stButton button:hover {
    border-color: var(--accent-cyan);
    color: var(--accent-cyan);
}

/* ── Text input ── */
.stTextInput input {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    border-radius: 4px !important;
}
.stTextInput input:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 1px var(--accent-cyan) !important;
}

/* ── Primary button ── */
.stButton button[kind="primary"] {
    background: var(--accent-cyan) !important;
    color: #06110F !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 4px !important;
    letter-spacing: 0.03em;
}
.stButton button[kind="primary"]:hover { opacity: 0.85; }

/* ── Terminal console ── */
.terminal {
    background: #060A10;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem 1.2rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    color: var(--accent-cyan);
    line-height: 1.7;
    min-height: 140px;
}
.terminal .line-done { color: var(--text-muted); }
.terminal .cursor { animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }

/* ── Report panel ── */
.report-panel {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.8rem 2rem;
    margin-top: 1rem;
}
.report-panel h3 {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--accent-cyan);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
}

/* severity badges */
.sev-critical, .sev-high, .sev-medium, .sev-low {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 1px 7px;
    border-radius: 3px;
    letter-spacing: 0.04em;
}
.sev-critical { background: rgba(229,72,77,0.15); color: var(--accent-red); }
.sev-high { background: rgba(245,166,35,0.15); color: var(--accent-amber); }
.sev-medium { background: rgba(79,209,197,0.15); color: var(--accent-cyan); }
.sev-low { background: rgba(124,138,163,0.15); color: var(--text-muted); }

/* ── Past reports ── */
.job-row {
    display: flex; align-items: center; gap: 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}
.job-dot { width: 8px; height: 8px; border-radius: 50%; }
.job-done { background: var(--accent-green); }
.job-pending { background: var(--accent-amber); }
.job-failed { background: var(--accent-red); }

hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)


# ── Hero ────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-title">SENTINEL<span>_</span></div>
    <div class="hero-sub">Autonomous cybersecurity threat intelligence — powered by a LangGraph multi-agent pipeline</div>
    <div class="status-pill"><span class="status-dot"></span> SYSTEM OPERATIONAL</div>
</div>
""", unsafe_allow_html=True)


def highlight_severities(text: str) -> str:
    text = re.sub(r"\bCritical\b", '<span class="sev-critical">CRITICAL</span>', text)
    text = re.sub(r"\bHigh\b", '<span class="sev-high">HIGH</span>', text)
    text = re.sub(r"\bMedium\b", '<span class="sev-medium">MEDIUM</span>', text)
    text = re.sub(r"\bLow\b", '<span class="sev-low">LOW</span>', text)
    return text


# ── Topic input ─────────────────────────────────────────────────
st.markdown('<div style="font-family:IBM Plex Mono; font-size:0.8rem; color:#7C8AA3; margin-bottom:0.4rem;">QUICK TARGETS</div>', unsafe_allow_html=True)
chip_cols = st.columns(4)
chips = ["ransomware", "phishing", "supply chain attacks", "zero-day exploits"]
for col, chip in zip(chip_cols, chips):
    with col:
        st.button(chip, on_click=set_topic, args=(chip,), use_container_width=True)

topic = st.text_input("TOPIC", key="topic_input", placeholder="e.g. ransomware, CVEs this week, phishing campaigns", label_visibility="collapsed")
generate = st.button("▶ RUN INVESTIGATION", type="primary", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Generation flow ─────────────────────────────────────────────
if generate:
    if not topic.strip():
        st.warning("Enter a topic before running an investigation.")
    else:
        resp = requests.post(f"{API_URL}/reports", json={"topic": topic})
        job_id = resp.json()["job_id"]

        console = st.empty()
        progress = st.empty()

        stages = [
            "Connecting to threat intelligence sources...",
            "Threat Intelligence Analyst gathering data...",
            "Vulnerability Researcher cross-referencing CVEs...",
            "Incident Response Advisor formulating recommendations...",
            "Report Writer compiling final output...",
        ]

        start = time.time()
        stage_duration = 25  # approx seconds per stage, for the visual only

        while True:
            elapsed = time.time() - start
            stage_idx = min(int(elapsed // stage_duration), len(stages) - 1)

            log_html = ""
            for i in range(stage_idx + 1):
                cls = "line-done" if i < stage_idx else ""
                cursor = '<span class="cursor">▌</span>' if i == stage_idx else ""
                log_html += f'<div class="{cls}">&gt; {stages[i]} {cursor}</div>'

            console.markdown(f'<div class="terminal">{log_html}</div>', unsafe_allow_html=True)
            progress.progress(min(int((stage_idx + 1) / len(stages) * 90), 90))

            check = requests.get(f"{API_URL}/reports/{job_id}").json()
            status = check["status"]

            if status == "done":
                progress.progress(100)
                console.markdown(f'<div class="terminal"><div class="line-done">&gt; Investigation complete.</div></div>', unsafe_allow_html=True)
                st.session_state.current_report = check["report"]
                st.session_state.current_topic = topic
                break
            elif status == "failed":
                console.markdown(f'<div class="terminal" style="color:#E5484D;">&gt; Investigation failed: {check.get("error")}</div>', unsafe_allow_html=True)
                break

            time.sleep(3)

# ── Report display ──────────────────────────────────────────────
if st.session_state.current_report:
    st.markdown(f"""
    <div class="report-panel">
        <div style="font-family:IBM Plex Mono; font-size:0.75rem; color:#7C8AA3; letter-spacing:0.05em; margin-bottom:0.6rem;">
            TARGET: {st.session_state.current_topic.upper()}
        </div>
        {highlight_severities(st.session_state.current_report)}
    </div>
    """, unsafe_allow_html=True)

# ── Past reports ────────────────────────────────────────────────
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown('<div style="font-family:IBM Plex Mono; font-size:0.9rem; color:#E6EDF3; margin-bottom:0.8rem;">■ INVESTIGATION LOG</div>', unsafe_allow_html=True)

try:
    past = requests.get(f"{API_URL}/reports").json()
    for job in past:
        dot_class = {"done": "job-done", "pending": "job-pending", "failed": "job-failed"}.get(job["status"], "job-pending")
        with st.expander(f"{job['topic']}  —  {job['status'].upper()}  —  {job['created_at'][:19]}"):
            st.markdown(f'<div class="job-row"><span class="job-dot {dot_class}"></span> {job["status"]}</div>', unsafe_allow_html=True)
            if job.get("report"):
                st.markdown(highlight_severities(job["report"]), unsafe_allow_html=True)
            elif job.get("error"):
                st.error(job["error"])
            else:
                st.write("No report yet.")
except Exception as e:
    st.error(f"Could not load past reports: {e}")

st.markdown('<div style="text-align:center; color:#7C8AA3; font-family:IBM Plex Mono; font-size:0.7rem; margin-top:2rem;">SENTINEL · LangGraph · FastAPI · Groq · Exa</div>', unsafe_allow_html=True)