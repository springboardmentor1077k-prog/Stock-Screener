import os
import sys
import streamlit as st
import pandas as pd

root = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.join(os.path.dirname(root), "Streamlit_Dashboard")
utils_dir = os.path.join(dashboard_dir, "utils")
sys.path.append(utils_dir)
from api import post_data, fetch_data

st.set_page_config(page_title="Demo 5: Single-Fire Alert", page_icon="1️⃣", layout="wide")
st.header("Demo 5: Trigger Alert Once")
symbol = st.text_input("Symbol", "AAPL")
condition = st.selectbox("Condition", ["Above price", "Below price"])
value = st.number_input("Value", min_value=0.0, value=1.0)
if st.button("Create Alert"):
    r = post_data("alerts", {"symbol": symbol, "condition": condition, "value": value})
    if r.get("status") == "success":
        st.success("Alert created")
    else:
        st.error(f"{r.get('error_code', 'error')}: {r.get('message', 'Unknown error')}")

if st.button("Check Alerts"):
    r = post_data("alerts/checks", {})
    if r.get("status") == "success":
        new_events = r.get("metrics", {}).get("new_events", 0)
        total_events = r.get("metrics", {}).get("total_events", 0)
        if new_events > 0:
            st.success("Alert fired")
        else:
            st.info("No new firing. Alerts fire once per condition")
        events = r.get("data", [])
        if events:
            st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
        st.metric("New Events", new_events)
        st.metric("Total Events", total_events)
    else:
        st.error(f"{r.get('error_code', 'error')}: {r.get('message', 'Unknown error')}")
