import streamlit as st
from services import http
import pandas as pd


def render():
    st.markdown('<h2 style="color:#ffffff;margin-top:0;">Signals</h2>', unsafe_allow_html=True)
    st.info("Alerts are informational tools and should not be interpreted as trading advice.")
    st.subheader("Create Alert")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        symbol = st.text_input("Symbol", placeholder="AAPL").upper()
    with c2:
        direction = st.selectbox("Direction", [">", "<", "Above", "Below"])
    with c3:
        threshold = st.number_input("Threshold", min_value=0.0, step=0.1, format="%.2f")
    with c4:
        create = st.button("Create")
    if create:
        try:
            items, _ = http.post("/alerts", {"symbol": symbol, "direction": direction, "threshold": threshold})
            st.session_state["alerts_list"] = None
            st.success(f"Alert created for {items[0]['symbol']}")
        except http.NetworkError as e:
            st.warning(str(e))
    st.divider()
    c5, c6 = st.columns([1, 3])
    with c5:
        if st.button("Load Alerts"):
            try:
                items, _ = http.get("/alerts")
                st.session_state["alerts_list"] = items
            except http.NetworkError as e:
                st.session_state["alerts_list"] = None
                st.warning(str(e))
        run = st.button("Run Checks", type="primary")
        if run:
            try:
                fired, _ = http.post("/alerts/run", {})
                st.session_state["last_alert_run"] = fired
                if fired:
                    st.success(f"Fired {len(fired)} alert(s)")
                else:
                    st.info("No alerts fired")
            except http.NetworkError as e:
                st.warning(str(e))
        if st.button("Clear Banners"):
            st.session_state["last_alert_run"] = []
    with c6:
        alerts = st.session_state.get("alerts_list")
        if alerts is None:
            st.markdown('<div class="qd-banner">Load alerts to view signals</div>', unsafe_allow_html=True)
        else:
            df = pd.DataFrame(alerts)
            st.dataframe(df, use_container_width=True)
    recent = st.session_state.get("last_alert_run") or []
    if recent:
        rf = pd.DataFrame(recent)
        st.markdown('<div class="qd-banner qd-success">Recent Alert Events</div>', unsafe_allow_html=True)
        st.dataframe(rf, use_container_width=True)
