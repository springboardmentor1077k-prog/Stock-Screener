import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Stock Explorer", layout="wide")

# =====================================================
# STYLE
# =====================================================
st.markdown("""
<style>
.block-container { padding-top:1rem; }

.fintech-header {
    background:linear-gradient(90deg,#0f1c2e,#1f3b73);
    color:#ffffff;
    padding:14px 18px;
    border-radius:10px;
    margin-bottom:14px;
    font-size:26px;
    font-weight:700;
}

.fintech-card {
    background:#111827;
    padding:16px;
    border-radius:10px;
    margin-bottom:14px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown(
    '<div class="fintech-header">📊 AI Stock Explorer</div>',
    unsafe_allow_html=True
)

st.info(
    "📘 Algorithm-based screening and portfolio simulation for educational exploration."
)

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
# LOGIN PAGE
# =====================================================
def login_page():

    st.subheader("Access Portal")

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
                st.rerun()
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

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state.page = "login"
        st.rerun()

    # -------------------------------------------------
    # SCREENER
    # -------------------------------------------------
    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)

    st.subheader("📊 Stock Screener")

    query = st.text_input("Enter stock query")

    if st.button("Search"):
        r = requests.post(
            f"{API_URL}/screen",
            headers=headers(),
            json={"query": query}
        )
        if r.status_code == 200:
            data = r.json()
            st.session_state.screener_results = data["data"]
            st.success(f"{data['count']} results fetched")

    if st.session_state.screener_results:
        df = pd.DataFrame(st.session_state.screener_results)
        st.dataframe(df, use_container_width=True)

        st.markdown("""
        <div style="background-color:#2b0b0b;border-left:5px solid #ff4b4b;
        padding:10px;border-radius:6px;">
        ⚠️ Screening results are generated from rule-based matching and
        presented for informational exploration.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------
    # PORTFOLIO SECTION
    # -------------------------------------------------
    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)

    st.header("💼 Portfolio")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Create Portfolio"):
            r = requests.post(
                f"{API_URL}/portfolio/create",
                headers=headers()
            )
            if r.status_code == 200:
                st.session_state.portfolio_id = r.json()["portfolio_id"]

    with col2:
        pid = st.number_input("Load Portfolio ID", min_value=1, step=1)
        if st.button("Load Portfolio"):
            st.session_state.portfolio_id = pid

    if not st.session_state.portfolio_id:
        st.info("Create or load a portfolio to continue.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # -------------------------------------------------
    # ADD STOCK
    # -------------------------------------------------
    st.subheader("Add Stock to Portfolio")

    with st.form("add_stock_form"):
        stock_id = st.number_input("Stock ID", min_value=1)
        quantity = st.number_input("Quantity", min_value=1)
        buy_price = st.number_input("Buy Price", min_value=1.0)
        submitted = st.form_submit_button("Add Stock")

        if submitted:
            requests.post(
                f"{API_URL}/portfolio/add",
                headers=headers(),
                json={
                    "portfolio_id": st.session_state.portfolio_id,
                    "stock_id": stock_id,
                    "quantity": quantity,
                    "buy_price": buy_price
                }
            )

    # -------------------------------------------------
    # VIEW PORTFOLIO (RESTORED)
    # -------------------------------------------------
    st.subheader("📄 View Portfolio")

    r = requests.get(
        f"{API_URL}/portfolio/{st.session_state.portfolio_id}",
        headers=headers()
    )

    holdings = r.json() if r.status_code == 200 else []

    if holdings:
        holdings_df = pd.DataFrame(holdings)
        st.dataframe(holdings_df, use_container_width=True)

        sell_id = st.number_input("Holding ID to Sell", min_value=1)
        if st.button("Sell Holding"):
            requests.delete(
                f"{API_URL}/portfolio/sell/{sell_id}",
                headers=headers()
            )

    # -------------------------------------------------
    # POSITION SUMMARY (RESTORED)
    # -------------------------------------------------
    st.subheader("📊 Position Summary")

    if holdings:
        summary_rows = []
        for h in holdings:
            invested = h["buy_price"] * h["quantity"]
            current_value = h["current_price"] * h["quantity"]
            pnl = round(current_value - invested, 2)

            summary_rows.append({
                "Symbol": h["symbol"],
                "Invested": invested,
                "Current Value": current_value,
                "PnL": pnl
            })

        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------
    # MARKET SIMULATION
    # -------------------------------------------------
    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)

    st.subheader("📈 Market Simulation")

    if st.button("Simulate Market Prices"):
        requests.post(
            f"{API_URL}/simulate",
            headers=headers()
        )
        st.success("Market prices updated")

    st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------
    # ALERTS
    # -------------------------------------------------
    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)

    st.header("🔔 Alerts")

    alert_query = st.text_input("Create alert query")

    if st.button("Create Alert"):
        requests.post(
            f"{API_URL}/alerts/create",
            headers=headers(),
            json={"query": alert_query}
        )

    if st.button("Check Alerts"):
        r = requests.get(
            f"{API_URL}/alerts/check",
            headers=headers()
        )
        if r.status_code == 200:
            alerts = r.json()["triggered_alerts"]
            if alerts:
                st.dataframe(pd.DataFrame(alerts), use_container_width=True)

    st.markdown("""
    <div style="background-color:#2b0b0b;border-left:5px solid #ff4b4b;
    padding:10px;border-radius:6px;">
    🔔 Alerts notify when selected conditions match market data.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# ROUTER
# =====================================================
if st.session_state.page == "login":
    login_page()
else:
    screener_page()

# =====================================================
# FOOTER
# =====================================================
st.markdown("""
<hr>
<div style='font-size:12px;color:gray;text-align:center;'>
Educational platform demonstrating stock screening, portfolio tracking and alerts.
</div>
""", unsafe_allow_html=True)
