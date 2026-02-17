import streamlit as st
import pandas as pd
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="StockSense AI", layout="wide")

# ==========================================================
# SESSION STATE
# ==========================================================
if "token" not in st.session_state:
    st.session_state.token = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==========================================================
# AUTH SECTION
# ==========================================================
if not st.session_state.logged_in:

    st.title("🔐 StockSense AI")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # ---------------- LOGIN ----------------
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            response = requests.post(
                f"{API_BASE}/login",
                data={
                    "username": username,
                    "password": password
                }
            )

            if response.status_code == 200:
                st.session_state.token = response.json()["access_token"]
                st.session_state.logged_in = True
                st.success("Login successful ✅")
                st.rerun()
            else:
                st.error("Invalid credentials ❌")

    # ---------------- REGISTER ----------------
    with tab2:
        new_username = st.text_input("New Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("New Password", type="password")

        if st.button("Register"):

            response = requests.post(
                f"{API_BASE}/register",
                json={
                    "username": new_username,
                    "email": new_email,
                    "password": new_password
                }
            )

            if response.status_code == 200:
                st.success("User registered successfully ✅")
            else:
                st.error("Registration failed ❌")

    st.stop()

# ==========================================================
# AFTER LOGIN
# ==========================================================
headers = {
    "Authorization": f"Bearer {st.session_state.token}"
}

# Sidebar
st.sidebar.title("📊 StockSense AI")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.token = None
    st.rerun()

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Screener", "Portfolio", "Alert Center"]
)

# ==========================================================
# DASHBOARD
# ==========================================================
if page == "Dashboard":

    st.title("📊 StockSense AI Dashboard")

    st.markdown("### Welcome to the Intelligent Investment Platform 🚀")

    # -----------------------------------------
    # 🔹 Top KPI Cards
    # -----------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Portfolio Value", "₹ 1,42,520", "+2.4%")
    col2.metric("Total Profit", "₹ 12,450", "+5.1%")
    col3.metric("Active Alerts", "3")
    col4.metric("Risk Score", "Moderate")

    st.divider()

    # -----------------------------------------
    # 🔹 Market Overview
    # -----------------------------------------
    st.subheader("📈 Market Overview")

    import plotly.express as px
    import pandas as pd

    market_data = pd.DataFrame({
        "Index": ["NIFTY 50", "SENSEX", "BANK NIFTY", "MIDCAP"],
        "Change (%)": [1.2, 0.8, -0.4, 1.9]
    })

    fig = px.bar(
        market_data,
        x="Index",
        y="Change (%)",
        color="Change (%)",
        text="Change (%)",
        title="Today's Market Movement"
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # -----------------------------------------
    # 🔹 Quick Actions Section
    # -----------------------------------------
    st.subheader("⚡ Quick Actions")

    colA, colB, colC = st.columns(3)

    if colA.button("🔎 Run Screener"):
        st.success("Navigate to Screener from Sidebar")

    if colB.button("🚨 Create Alert"):
        st.success("Navigate to Alert Center")

    if colC.button("📂 View Portfolio"):
        st.success("Navigate to Portfolio")


# ==========================================================
# SCREENER
# ==========================================================
elif page == "Screener":

    st.title("🔎 AI Stock Screener")

    query = st.text_input("Enter Query (Example: pe_ratio < 25)")

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
            st.success(f"Found {data['count']} matching stocks")
            df = pd.DataFrame(data["results"])
            st.dataframe(df, width="stretch")

elif page == "Portfolio":

    import plotly.express as px
    import plotly.graph_objects as go

    st.title("📂 My Portfolio")

    # --------------------------------------------------
    # 🔹 Hardcoded Portfolio Data (Demo Purpose)
    # --------------------------------------------------
    portfolio_data = [
        {
            "symbol": "INFY",
            "company_name": "Infosys",
            "quantity": 10,
            "cost_price": 1400,
            "current_price": 1550,
            "target_price": 1700
        },
        {
            "symbol": "TCS",
            "company_name": "Tata Consultancy Services",
            "quantity": 5,
            "cost_price": 3200,
            "current_price": 3500,
            "target_price": 3800
        },
        {
            "symbol": "RELIANCE",
            "company_name": "Reliance Industries",
            "quantity": 8,
            "cost_price": 2500,
            "current_price": 2650,
            "target_price": 2900
        }
    ]

    df = pd.DataFrame(portfolio_data)

    # --------------------------------------------------
    # 🔹 Calculations
    # --------------------------------------------------
    df["investment"] = df["quantity"] * df["cost_price"]
    df["current_value"] = df["quantity"] * df["current_price"]
    df["profit_loss"] = df["current_value"] - df["investment"]

    df["upside_percent"] = (
        (df["target_price"] - df["cost_price"]) / df["cost_price"]
    ) * 100

    total_investment = df["investment"].sum()
    total_current_value = df["current_value"].sum()
    total_profit = df["profit_loss"].sum()

    # --------------------------------------------------
    # 🔹 Top Metrics
    # --------------------------------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Investment", f"₹ {total_investment:,.0f}")
    col2.metric("Current Value", f"₹ {total_current_value:,.0f}")
    col3.metric(
        "Total Profit / Loss",
        f"₹ {total_profit:,.0f}",
        delta=f"{(total_profit/total_investment)*100:.2f}%"
    )

    st.divider()

    # --------------------------------------------------
    # 🔹 Holdings Table
    # --------------------------------------------------
    st.subheader("📊 Holdings")

    st.dataframe(
        df[[
            "company_name",
            "symbol",
            "quantity",
            "cost_price",
            "current_price",
            "target_price",
            "profit_loss",
            "upside_percent"
        ]],
        width="stretch"
    )

    st.divider()

    # --------------------------------------------------
    # 🔹 Portfolio Allocation Pie Chart
    # --------------------------------------------------
    st.subheader("📈 Portfolio Allocation")

    fig1 = px.pie(
        df,
        names="symbol",
        values="current_value",
        title="Allocation by Current Value",
        hole=0.4
    )

    fig1.update_layout(template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

    # --------------------------------------------------
    # 🔹 Investment vs Current Value (Bar Chart)
    # --------------------------------------------------
    st.subheader("💰 Investment vs Current Value")

    bar_df = pd.DataFrame({
        "Category": ["Investment", "Current Value"],
        "Amount": [total_investment, total_current_value]
    })

    fig2 = px.bar(
        bar_df,
        x="Category",
        y="Amount",
        text="Amount",
        title="Investment vs Current Value",
        color="Category"
    )

    fig2.update_traces(textposition="outside")
    fig2.update_layout(template="plotly_dark")

    st.plotly_chart(fig2, use_container_width=True)

    # --------------------------------------------------
    # 🔹 Individual Stock Performance
    # --------------------------------------------------
    st.subheader("📉 Individual Stock Profit/Loss")

    fig3 = px.bar(
        df,
        x="symbol",
        y="profit_loss",
        text="profit_loss",
        color="profit_loss",
        title="Profit / Loss by Stock"
    )

    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)

    st.success("Portfolio loaded successfully ✅")


# ==========================================================
# ALERT CENTER
# ==========================================================
elif page == "Alert Center":

    st.title("🚨 Alert Center")

    # ---------------- CREATE ALERT ----------------
    st.subheader("Create Alert")

    portfolio_id = st.number_input("Portfolio ID", min_value=1)
    operation = st.selectbox("Operation", [">", "<", "="])
    metric = st.selectbox("Metric", ["upside_percent"])
    threshold = st.number_input("Threshold", step=1.0)

    if st.button("Create Alert"):

        response = requests.post(
            f"{API_BASE}/alerts",
            json={
                "portfolio_id": portfolio_id,
                "operation": operation,
                "metric": metric,
                "threshold": threshold
            },
            headers=headers
        )

        if response.status_code == 200:
            st.success("Alert created successfully ✅")
        else:
            st.error("Failed to create alert ❌")

    
    # ---------------- SHOW ALERT EVENTS ----------------
    st.subheader("Alert Events")

    if st.button("Show Alert Events"):

        response = requests.get(
            f"{API_BASE}/alert-events",
            headers=headers
        )

        data = response.json()

        if "error" in data:
            st.error(data["error"])
        elif data.get("events"):
            df = pd.DataFrame(data["events"])
            st.dataframe(df, width="stretch")
        else:
            st.warning("No events found.")
