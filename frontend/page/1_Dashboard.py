import streamlit as st

st.title("📊 StockSense AI Dashboard")

st.success("Welcome to StockSense AI 🚀")

col1, col2, col3 = st.columns(3)

col1.metric("Portfolio Value", "$142,000", "+3.5%")
col2.metric("Total P/L", "+$12,500", "+5.2%")
col3.metric("Active Alerts", "4")
