import os
import sys
import streamlit as st
import pandas as pd

root = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.join(os.path.dirname(root), "Streamlit_Dashboard")
utils_dir = os.path.join(dashboard_dir, "utils")
sys.path.append(utils_dir)
from api import fetch_data, post_data

st.set_page_config(page_title="Demo 3: Live Alerts", page_icon="🔔", layout="wide")
st.header("Demo 3: Live Alerts")
col1, col2 = st.columns([2, 1])
with col2:
    symbol = st.text_input("Symbol", "AAPL")
    condition = st.selectbox("Condition", ["Above price", "Below price"])
    value = st.number_input("Value", min_value=0.0, value=100.0)
    if st.button("Create Alert"):
        r = post_data("alerts", {"symbol": symbol, "condition": condition, "value": value})
        if r.get("status") == "success":
            st.success("Alert created")
        else:
            st.error(f"{r.get('error_code', 'error')}: {r.get('message', 'Unknown error')}")

st.subheader("Active Alerts")
alerts = fetch_data("alerts")
if alerts.get("status") == "success":
    data = alerts.get("data", [])
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("No active alerts")
else:
    st.error(f"{alerts.get('error_code', 'error')}: {alerts.get('message', 'Unknown error')}")

st.subheader("Check Alerts")
if st.button("Run Checks"):
    r = post_data("alerts/checks", {})
    if r.get("status") == "success":
        st.metric("New Alerts Fired", r.get("metrics", {}).get("new_events", 0))
        st.metric("Total Alert Events", r.get("metrics", {}).get("total_events", 0))
        events = r.get("data", [])
        if events:
            st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
        st.success(r.get("message", "Done"))
    else:
        st.error(f"{r.get('error_code', 'error')}: {r.get('message', 'Unknown error')}")
