import streamlit as st
import pandas as pd
import requests

API_BASE = "http://127.0.0.1:8000"

headers = {
    "Authorization": f"Bearer {st.session_state.token}"
}

st.title("🔎 AI Stock Screener")

query = st.text_input("Enter Query")

if st.button("Run Scan"):

    response = requests.get(
        f"{API_BASE}/screen",
        params={"query": query},
        headers=headers
    )

    if response.status_code == 401:
        st.error("Session expired. Login again.")
        st.session_state.logged_in = False
        st.rerun()

    data = response.json()

    if "error" in data:
        st.error(data["error"])

    elif data.get("count", 0) == 0:
        st.warning("No matching stocks found.")

    else:
        df = pd.DataFrame(data["results"])
        st.dataframe(df, width="stretch")
