import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:8000"

st.title("Cybersecurity Intelligence Report Generator")

topic = st.text_input("Enter a topic (e.g. ransomware, phishing, CVEs):")

if st.button("Generate Report"):
    if topic.strip() == "":
        st.warning("Please enter a topic.")
    else:
        response = requests.post(f"{API_URL}/reports", json={"topic": topic})
        job_id = response.json()["job_id"]
        st.info(f"Report started. Job ID: {job_id}")

        status_box = st.empty()
        with st.spinner("Generating report... this can take 1-3 minutes."):
            while True:
                check = requests.get(f"{API_URL}/reports/{job_id}").json()
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
st.subheader("Past Reports")
past = requests.get(f"{API_URL}/reports").json()
for job in past:
    with st.expander(f"{job['topic']} — {job['status']} — {job['created_at']}"):
        if job["report"]:
            st.markdown(job["report"])
        else:
            st.write("No report yet.")