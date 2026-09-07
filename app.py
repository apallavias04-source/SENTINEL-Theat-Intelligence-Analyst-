import streamlit as st
import requests
import time
import re

API_URL = "https://sentinel-theat-intelligence-analyst.onrender.com"

st.set_page_config(page_title="SENTINEL — Threat Intelligence", page_icon="🛡️", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = None
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def set_topic(value):
    st.session_state.topic_input = value


# ── CSS (same theme as before) ──────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg-void: #0A0E17;
    --bg-panel: #121826;
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

.hero { border-bottom: 1px solid var(--border); padding-bottom: 1.4rem; margin-bottom: 2rem; }
.hero-title { font-family: 'IBM Plex Mono', monospace; font-size: 2.1rem; font-weight: 700; color: var(--text-primary); margin: 0; }
.hero-title span { color: var(--accent-cyan); }
.hero-sub { color: var(--text-muted); font-size: 0.92rem; margin-top: 0.35rem; }

.stTextInput input {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    border-radius: 4px !important;
}
.stButton button[kind="primary"] {
    background: var(--accent-cyan) !important;
    color: #06110F !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 4px !important;
}
.report-panel {
    background: var(--bg-panel); border: 1px solid var(--border); border-radius: 6px;
    padding: 1.8rem 2rem; margin-top: 1rem;
}
.sev-critical, .sev-high, .sev-medium, .sev-low {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; font-weight: 600;
    padding: 1px 7px; border-radius: 3px;
}
.sev-critical { background: rgba(229,72,77,0.15); color: var(--accent-red); }
.sev-high { background: rgba(245,166,35,0.15); color: var(--accent-amber); }
.sev-medium { background: rgba(79,209,197,0.15); color: var(--accent-cyan); }
.sev-low { background: rgba(124,138,163,0.15); color: var(--text-muted); }
</style>
""", unsafe_allow_html=True)


def highlight_severities(text: str) -> str:
    text = re.sub(r"\bCritical\b", '<span class="sev-critical">CRITICAL</span>', text)
    text = re.sub(r"\bHigh\b", '<span class="sev-high">HIGH</span>', text)
    text = re.sub(r"\bMedium\b", '<span class="sev-medium">MEDIUM</span>', text)
    text = re.sub(r"\bLow\b", '<span class="sev-low">LOW</span>', text)
    return text


# ── Login / Signup screen ──────────────────────────────────────────
def show_auth_screen():
    st.markdown("""
    <div class="hero">
        <div class="hero-title">SENTINEL<span>_</span></div>
        <div class="hero-sub">Autonomous cybersecurity threat intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log In", type="primary"):
            resp = requests.post(f"{API_URL}/login", data={"username": email, "password": password})
            if resp.status_code == 200:
                st.session_state.token = resp.json()["access_token"]
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Incorrect email or password.")

    with tab_signup:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up", type="primary"):
            resp = requests.post(f"{API_URL}/signup", json={"email": new_email, "password": new_password})
            if resp.status_code == 200:
                st.session_state.token = resp.json()["access_token"]
                st.session_state.email = new_email
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Signup failed."))


# ── Main app ─────────────────────────────────────────────────────────
def show_main_app():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("""
        <div class="hero">
            <div class="hero-title">SENTINEL<span>_</span></div>
            <div class="hero-sub">Autonomous cybersecurity threat intelligence</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.write(f"`{st.session_state.email}`")
        if st.button("Log Out"):
            st.session_state.token = None
            st.session_state.email = None
            st.rerun()

    st.markdown('<div style="font-family:IBM Plex Mono; font-size:0.8rem; color:#7C8AA3; margin-bottom:0.4rem;">QUICK TARGETS</div>', unsafe_allow_html=True)
    chip_cols = st.columns(4)
    chips = ["ransomware", "phishing", "supply chain attacks", "zero-day exploits"]
    for col, chip in zip(chip_cols, chips):
        with col:
            st.button(chip, on_click=set_topic, args=(chip,), use_container_width=True)

    topic = st.text_input("TOPIC", key="topic_input", placeholder="e.g. ransomware, CVEs this week", label_visibility="collapsed")
    generate = st.button("▶ RUN INVESTIGATION", type="primary", use_container_width=True)

    if generate:
        if not topic.strip():
            st.warning("Enter a topic first.")
        else:
            resp = requests.post(f"{API_URL}/reports", json={"topic": topic}, headers=auth_headers())
            if resp.status_code == 401:
                st.error("Session expired — please log in again.")
                st.session_state.token = None
                st.rerun()
            else:
                job_id = resp.json()["job_id"]
                with st.spinner("Running investigation... this can take 1-3 minutes."):
                    while True:
                        check = requests.get(f"{API_URL}/reports/{job_id}", headers=auth_headers()).json()
                        if check["status"] == "done":
                            st.session_state.current_report = check["report"]
                            st.session_state.current_topic = topic
                            break
                        elif check["status"] == "failed":
                            st.error(f"Failed: {check.get('error')}")
                            break
                        time.sleep(5)

    if st.session_state.current_report:
        st.markdown(f"""
        <div class="report-panel">
            <div style="font-family:IBM Plex Mono; font-size:0.75rem; color:#7C8AA3; margin-bottom:0.6rem;">
                TARGET: {st.session_state.current_topic.upper()}
            </div>
            {highlight_severities(st.session_state.current_report)}
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="font-family:IBM Plex Mono; font-size:0.9rem;">■ YOUR INVESTIGATION LOG</div>', unsafe_allow_html=True)
    past = requests.get(f"{API_URL}/reports", headers=auth_headers()).json()
    if not past:
        st.write("No reports yet.")
    for job in past:
        with st.expander(f"{job['topic']} — {job['status'].upper()} — {job['created_at'][:19]}"):
            if job.get("report"):
                st.markdown(highlight_severities(job["report"]), unsafe_allow_html=True)
            elif job.get("error"):
                st.error(job["error"])


if st.session_state.token is None:
    show_auth_screen()
else:
    show_main_app()