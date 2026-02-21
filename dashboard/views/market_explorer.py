import streamlit as st
from services import http
import pandas as pd


def render():
    st.markdown('<h2 style="color:#ffffff;margin-top:0;">Market Explorer</h2>', unsafe_allow_html=True)
    st.info("These insights are for informational purposes only and do not constitute financial advice.")
    c1, c2 = st.columns([3, 2])
    with c1:
        q = st.text_input("Describe criteria", placeholder="technology market cap above 500 and price below 200")
    with c2:
        sector = st.selectbox("Sector", ["", "Technology", "Financials", "Health Care", "Energy", "Consumer Discretionary"])
        sector = sector if sector else None
    r = st.button("Run Analysis", type="primary")
    if r:
        payload = {"query": q, "sector": sector}
        try:
            items, _ = http.post("/screener", payload)
            st.session_state["explorer_result"] = items
            if not items:
                st.info("No matches found")
        except http.NetworkError as e:
            st.session_state["explorer_result"] = None
            st.warning(str(e))
    data = st.session_state.get("explorer_result")
    if data is None:
        st.markdown('<div class="qd-banner">Ready to explore markets</div>', unsafe_allow_html=True)
        return
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Try refining your query or filters")
