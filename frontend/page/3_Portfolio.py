import streamlit as st
import pandas as pd

st.title("📂 My Portfolio")

portfolio = pd.DataFrame([
    {"symbol": "INFY", "quantity": 50, "cost_price": 1400},
    {"symbol": "TCS", "quantity": 30, "cost_price": 3200}
])

portfolio["current_price"] = portfolio["cost_price"] * 1.15
portfolio["total_value"] = portfolio["quantity"] * portfolio["current_price"]
portfolio["profit_loss"] = (
    (portfolio["current_price"] - portfolio["cost_price"])
    * portfolio["quantity"]
)

st.dataframe(portfolio, width="stretch")

st.metric("Total Value", f"${portfolio['total_value'].sum():,.2f}")
