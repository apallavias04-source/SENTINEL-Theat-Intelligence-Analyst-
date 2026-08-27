import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="SENTINEL — Threat Intelligence", page_icon="🛡️", layout="wide")

# ── Session state ─────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = None


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


# ── Login / Signup screen ──────────────────────────────────────────
def show_auth_screen():
    st.title("🛡️ SENTINEL")
    st.caption("Autonomous cybersecurity threat intelligence")

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log In", type="primary"):
            resp = requests.post(
                f"{API_URL}/login",
                data={"username": email, "password": password}
            )
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
            resp = requests.post(
                f"{API_URL}/signup",
                json={"email": new_email, "password": new_password}
            )
            if resp.status_code == 200:
                st.session_state.token = resp.json()["access_token"]
                st.session_state.email = new_email
                st.rerun()
            else:
                detail = resp.json().get("detail", "Signup failed.")
                st.error(detail)


# ── Main app (only reachable once logged in) ────────────────────────
def show_main_app():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("🛡️ SENTINEL")
        st.caption(f"Logged in as {st.session_state.email}")
    with col2:
        if st.button("Log Out"):
            st.session_state.token = None
            st.session_state.email = None
            st.rerun()

    topic = st.text_input("Enter a topic (e.g. ransomware, phishing, CVEs):")

    if st.button("Generate Report"):
        if topic.strip() == "":
            st.warning("Please enter a topic.")
        else:
            resp = requests.post(
                f"{API_URL}/reports",
                json={"topic": topic},
                headers=auth_headers()
            )
            if resp.status_code == 401:
                st.error("Your session expired. Please log in again.")
                st.session_state.token = None
                st.rerun()
            else:
                job_id = resp.json()["job_id"]
                st.info(f"Report started. Job ID: {job_id}")

                status_box = st.empty()
                with st.spinner("Generating report... this can take 1-3 minutes."):
                    while True:
                        check = requests.get(
                            f"{API_URL}/reports/{job_id}",
                            headers=auth_headers()
                        ).json()
                        status = check["status"]
                        status_box.write(f"Status: {status}")
                        if status == "done":
                            st.success("Report ready!")
                            st.markdown(check["report"])
                            break
                        elif status == "failed":
                            st.error(f"Failed: {check.get('error')}")
                            break
                        time.sleep(5)

    st.divider()
    st.subheader("Your Past Reports")
    past_resp = requests.get(f"{API_URL}/reports", headers=auth_headers())
    if past_resp.status_code == 200:
        past = past_resp.json()
        if not past:
            st.write("No reports yet — generate one above.")
        for job in past:
            with st.expander(f"{job['topic']} — {job['status']} — {job['created_at']}"):
                if job["report"]:
                    st.markdown(job["report"])
                else:
                    st.write("No report yet.")


# ── Router: show login screen or main app ────────────────────────────
if st.session_state.token is None:
    show_auth_screen()
else:
    show_main_app()