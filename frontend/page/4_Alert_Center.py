import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:8000"

headers = {
    "Authorization": f"Bearer {st.session_state.token}"
}

st.title("🚨 Alert Center")

st.subheader("Create Alert")

portfolio_id = st.number_input("Portfolio ID", min_value=1)
operation = st.selectbox("Operation", [">", "<", "="])
metric = st.selectbox("Metric", ["upside_percent"])
threshold = st.number_input("Threshold", step=1.0)

if st.button("Create Alert"):

    response = requests.post(
        f"{API_BASE}/alerts",
        json={
            "portfolio_id": portfolio_id,
            "operation": operation,
            "metric": metric,
            "threshold": threshold
        },
        headers=headers
    )

    if response.status_code == 200:
        st.success("Alert created successfully ✅")
    else:
        st.error("Failed ❌")

st.subheader("Alert Events")

if st.button("Show Alert Events"):

    response = requests.get(
        f"{API_BASE}/alert-events",
        headers=headers
    )

    data = response.json()

    if data.get("events"):
        df = pd.DataFrame(data["events"])
        st.dataframe(df, width="stretch")
    else:
        st.warning("No events found")
