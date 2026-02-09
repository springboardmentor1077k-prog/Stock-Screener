import os
import sys
import streamlit as st
import pandas as pd

root = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.join(os.path.dirname(root), "Streamlit_Dashboard")
utils_dir = os.path.join(dashboard_dir, "utils")
sys.path.append(utils_dir)
from api import post_data

st.set_page_config(page_title="Edge Case: Still True After Firing", page_icon="⚠️", layout="wide")
st.header("Edge Case: Condition True After Firing")
if "first_run_done" not in st.session_state:
    st.session_state.first_run_done = False

symbol = st.text_input("Symbol", "AAPL")
condition = st.selectbox("Condition", ["Above price", "Below price"])
value = st.number_input("Value", min_value=0.0, value=1.0)
col1, col2 = st.columns(2)
with col1:
    if st.button("Run Check 1"):
        r = post_data("alerts/checks", {})
        if r.get("status") == "success":
            st.session_state.first_run_done = True
            st.success(r.get("message", "Done"))
            st.metric("New Events", r.get("metrics", {}).get("new_events", 0))
            st.dataframe(pd.DataFrame(r.get("data", [])), use_container_width=True, hide_index=True)
        else:
            st.error(f"{r.get('error_code', 'error')}: {r.get('message', 'Unknown error')}")
with col2:
    if st.button("Run Check 2"):
        r = post_data("alerts/checks", {})
        if r.get("status") == "success":
            if st.session_state.first_run_done and r.get("metrics", {}).get("new_events", 0) == 0:
                st.info("Condition still true but alert not re-fired")
            else:
                st.success(r.get("message", "Done"))
            st.metric("New Events", r.get("metrics", {}).get("new_events", 0))
            st.dataframe(pd.DataFrame(r.get("data", [])), use_container_width=True, hide_index=True)
        else:
            st.error(f"{r.get('error_code', 'error')}: {r.get('message', 'Unknown error')}")
