import os
import sys
import streamlit as st
import pandas as pd

root = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.join(os.path.dirname(root), "Streamlit_Dashboard")
utils_dir = os.path.join(dashboard_dir, "utils")
sys.path.append(utils_dir)
from api import fetch_data

st.set_page_config(page_title="Demo 2: Portfolio Success", page_icon="✅", layout="wide")
st.header("Demo 2: Portfolio Success Flow")
with st.spinner("Checking portfolio"):
    response = fetch_data("portfolio")

if response.get("status") == "success":
    data = response.get("data", [])
    if data:
        st.success("Portfolio loaded successfully")
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("No holdings found")
else:
    st.error(f"{response.get('error_code', 'error')}: {response.get('message', 'Unknown error')}")
