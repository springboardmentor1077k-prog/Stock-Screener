import os
import sys
import streamlit as st
import pandas as pd

root = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.join(os.path.dirname(root), "Streamlit_Dashboard")
utils_dir = os.path.join(dashboard_dir, "utils")
sys.path.append(utils_dir)
from api import fetch_data, post_data

st.set_page_config(page_title="Sprint 3 Demo", page_icon="📊", layout="wide")
st.title("Sprint 3: Portfolio & Alerts")

st.header("Portfolio")
with st.spinner("Loading portfolio"):
    portfolio_resp = fetch_data("portfolio")

if portfolio_resp.get("status") == "success":
    holdings = portfolio_resp.get("data", [])
    if not holdings:
        st.info("Your portfolio is empty")
    else:
        df = pd.DataFrame(holdings)
        total_value = float((df["current_price"] * df["quantity"]).sum())
        total_profit = float(df["profit_loss"].sum())
        st.metric("Total Portfolio Value", f"${total_value:,.2f}", f"${total_profit:,.2f}")
        st.subheader("Holdings")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "symbol": "Symbol",
                "quantity": "Shares",
                "avg_buy_price": st.column_config.NumberColumn("Avg Price", format="$%.2f"),
                "current_price": st.column_config.NumberColumn("Current Price", format="$%.2f"),
                "profit_loss": st.column_config.NumberColumn("Profit/Loss", format="$%.2f"),
                "company_name": "Company"
            }
        )
else:
    st.error(f"{portfolio_resp.get('error_code', 'error')}: {portfolio_resp.get('message', 'Unknown error')}")

st.divider()
st.header("Alerts")
col_form, col_list = st.columns([1, 2])
with col_form:
    st.subheader("Create Alert")
    symbol = st.text_input("Symbol", "AAPL")
    condition = st.selectbox("Condition", ["Above price", "Below price"])
    value = st.number_input("Value", min_value=0.0, value=100.0)
    if st.button("Create"):
        create_resp = post_data("alerts", {"symbol": symbol, "condition": condition, "value": value})
        if create_resp.get("status") == "success":
            st.success("Alert created")
        else:
            st.error(f"{create_resp.get('error_code', 'error')}: {create_resp.get('message', 'Unknown error')}")

with col_list:
    st.subheader("Active Alerts")
    alerts_resp = fetch_data("alerts")
    if alerts_resp.get("status") == "success":
        alerts = alerts_resp.get("data", [])
        if alerts:
            st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
        else:
            st.info("No active alerts")
    else:
        st.error(f"{alerts_resp.get('error_code', 'error')}: {alerts_resp.get('message', 'Unknown error')}")

st.subheader("Check Alerts & Trigger")
if "last_check_metrics" not in st.session_state:
    st.session_state.last_check_metrics = None
check_col1, check_col2 = st.columns(2)
with check_col1:
    if st.button("Run Checks"):
        check_resp = post_data("alerts/checks", {})
        if check_resp.get("status") == "success":
            metrics = check_resp.get("metrics", {})
            st.session_state.last_check_metrics = metrics
            new_events = metrics.get("new_events", 0)
            total_events = metrics.get("total_events", 0)
            st.metric("New Alerts Fired", new_events)
            st.metric("Total Alert Events", total_events)
            events = check_resp.get("data", [])
            if events:
                st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
            st.success(check_resp.get("message", "Done"))
        else:
            st.error(f"{check_resp.get('error_code', 'error')}: {check_resp.get('message', 'Unknown error')}")

with check_col2:
    if st.button("Run Checks Again"):
        check_resp = post_data("alerts/checks", {})
        if check_resp.get("status") == "success":
            metrics = check_resp.get("metrics", {})
            new_events = metrics.get("new_events", 0)
            total_events = metrics.get("total_events", 0)
            if new_events == 0:
                st.info("No repeat: Conditions true do not re-fire")
            st.metric("New Alerts Fired", new_events)
            st.metric("Total Alert Events", total_events)
            events = check_resp.get("data", [])
            if events:
                st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
            st.success(check_resp.get("message", "Done"))
        else:
            st.error(f"{check_resp.get('error_code', 'error')}: {check_resp.get('message', 'Unknown error')}")
