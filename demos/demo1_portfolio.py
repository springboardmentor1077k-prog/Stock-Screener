import os
import sys
import streamlit as st
import pandas as pd

root = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.join(os.path.dirname(root), "Streamlit_Dashboard")
utils_dir = os.path.join(dashboard_dir, "utils")
sys.path.append(utils_dir)
from api import fetch_data

st.set_page_config(page_title="Demo 1: Portfolio", page_icon="💼", layout="wide")
st.header("Demo 1: Portfolio Loading")
with st.spinner("Loading portfolio"):
    response = fetch_data("portfolio")

if response.get("status") == "success":
    data = response.get("data", [])
    if not data:
        st.info("Portfolio is empty")
    else:
        df = pd.DataFrame(data)
        total_value = float((df["current_price"] * df["quantity"]).sum())
        total_profit = float(df["profit_loss"].sum())
        st.metric("Total Portfolio Value", f"${total_value:,.2f}", f"${total_profit:,.2f}")
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
    st.error(f"{response.get('error_code', 'error')}: {response.get('message', 'Unknown error')}")
