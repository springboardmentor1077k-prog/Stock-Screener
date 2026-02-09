import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Stock Explorer", layout="wide")

# =====================================================
# SESSION STATE
# =====================================================
if "token" not in st.session_state:
    st.session_state.token = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "portfolio_id" not in st.session_state:
    st.session_state.portfolio_id = None
if "screener_results" not in st.session_state:
    st.session_state.screener_results = []


def headers():
    return {"token": st.session_state.token}


# =====================================================
# LOGIN / REGISTER
# =====================================================
def login_page():
    st.title("AI Stock Explorer")
    st.caption("Search stocks using natural language")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            r = requests.post(
                f"{API_URL}/login",
                json={"username": username, "password": password}
            )
            if r.status_code == 200:
                st.session_state.token = r.json()["token"]
                st.session_state.page = "screener"
                st.success("Login successful")
            else:
                st.error("Invalid credentials")

    with tab2:
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        if st.button("Register"):
            r = requests.post(
                f"{API_URL}/register",
                json={"username": username, "password": password}
            )
            if r.status_code == 200:
                st.success("Registered successfully. Please login.")
            else:
                st.error("Registration failed")


# =====================================================
# MAIN APP
# =====================================================
def screener_page():
    st.title("AI Stock Screener")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state.page = "login"
        return

    # -------------------------------------------------
    # SCREENER
    # -------------------------------------------------
    st.subheader("Stock Screener")

    query = st.text_input(
        "Enter stock query",
        placeholder="pe below 20 and sector equals IT"
    )

    if st.button("Search"):
        r = requests.post(
            f"{API_URL}/screen",
            headers=headers(),
            json={"query": query}
        )
        if r.status_code == 200:
            st.session_state.screener_results = r.json()["data"]
        else:
            st.error(r.text)

    if st.session_state.screener_results:
        df = pd.DataFrame(st.session_state.screener_results)
        st.dataframe(df, use_container_width=True)

    st.divider()

    # -------------------------------------------------
    # PORTFOLIO CONTROLS
    # -------------------------------------------------
    st.header("Portfolio")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Create Portfolio"):
            r = requests.post(
                f"{API_URL}/portfolio/create",
                headers=headers()
            )
            if r.status_code == 200:
                st.session_state.portfolio_id = r.json()["portfolio_id"]
                st.success(f"Portfolio created (ID {st.session_state.portfolio_id})")

    with col2:
        pid = st.number_input("Load Portfolio ID", min_value=1, step=1)
        if st.button("Load Portfolio"):
            st.session_state.portfolio_id = pid

    if not st.session_state.portfolio_id:
        st.info("Create or load a portfolio to continue.")
        return

    # -------------------------------------------------
    # ADD STOCK TO PORTFOLIO (EXPLICIT & STABLE)
    # -------------------------------------------------
    st.subheader("Add Stock to Portfolio")

    with st.form("add_stock_form"):
        stock_id = st.number_input("Stock ID (1–25)", min_value=1, max_value=25)
        quantity = st.number_input("Quantity", min_value=1)
        buy_price = st.number_input("Buy Price (₹)", min_value=1.0)

        submitted = st.form_submit_button("Add Stock")

        if submitted:
            r = requests.post(
                f"{API_URL}/portfolio/add",
                headers=headers(),
                json={
                    "portfolio_id": st.session_state.portfolio_id,
                    "stock_id": stock_id,
                    "quantity": quantity,
                    "buy_price": buy_price
                }
            )
            if r.status_code == 200:
                st.success("Stock added to portfolio")
            else:
                st.error("Failed to add stock")

    st.divider()

    # -------------------------------------------------
    # VIEW PORTFOLIO
    # -------------------------------------------------
    st.subheader("My Holdings")

    r = requests.get(
        f"{API_URL}/portfolio/{st.session_state.portfolio_id}",
        headers=headers()
    )

    holdings = r.json() if r.status_code == 200 else []

    if holdings:
        holdings_df = pd.DataFrame([
            {
                "Holding ID": h["holding_id"],
                "Symbol": h["symbol"],
                "Company": h["company"],
                "Quantity": h["quantity"],
                "Buy Price": h["buy_price"],
                "Buy Time": h["buy_time"]
            }
            for h in holdings
        ])
        st.dataframe(holdings_df, use_container_width=True)

        sell_id = st.number_input("Holding ID to Sell", min_value=1, step=1)
        if st.button("Sell Holding"):
            r = requests.delete(
                f"{API_URL}/portfolio/sell/{sell_id}",
                headers=headers()
            )
            if r.status_code == 200:
                st.success("Stock sold")
    else:
        st.info("No stocks in portfolio")

    # -------------------------------------------------
    # POSITION SUMMARY
    # -------------------------------------------------
    st.subheader("Position Summary (If You Sell Now)")

    if holdings:
        summary_rows = []
        for h in holdings:
            invested = h["buy_price"] * h["quantity"]
            current_value = h["current_price"] * h["quantity"]
            pnl = round(current_value - invested, 2)

            summary_rows.append({
                "Symbol": h["symbol"],
                "Buy Price": h["buy_price"],
                "Current Price": h["current_price"],
                "Quantity": h["quantity"],
                "Invested Amount": invested,
                "Current Value": current_value,
                "Profit / Loss": pnl,
                "Summary": "Profit" if pnl >= 0 else "Loss"
            })

        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    # -------------------------------------------------
    # MARKET SIMULATION
    # -------------------------------------------------
    st.subheader("Market Simulation")

    if st.button("Simulate Market Prices"):
        requests.post(
            f"{API_URL}/simulate",
            headers=headers()
        )
        st.success("Market prices updated")

    st.divider()

    # -------------------------------------------------
    # ALERTS
    # -------------------------------------------------
    st.header("Alerts")

    alert_query = st.text_input("Create alert query")
    if st.button("Create Alert"):
        r = requests.post(
            f"{API_URL}/alerts/create",
            headers=headers(),
            json={"query": alert_query}
        )
        if r.status_code == 200:
            st.success("Alert created")

    if st.button("Check Alerts"):
        r = requests.get(
            f"{API_URL}/alerts/check",
            headers=headers()
        )
        if r.status_code == 200:
            alerts = r.json()["triggered_alerts"]
            if alerts:
                st.dataframe(pd.DataFrame(alerts), use_container_width=True)
            else:
                st.info("No new alerts")


# =====================================================
# ROUTER
# =====================================================
if st.session_state.page == "login":
    login_page()
else:
    screener_page()
