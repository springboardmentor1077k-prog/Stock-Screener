import streamlit as st
import requests
import pandas as pd

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Stock Explorer", layout="centered")
st.title("AI Stock Explorer")

# -------------------------
# SESSION STATE
# -------------------------
if "token" not in st.session_state:
    st.session_state.token = None

# -------------------------
# AUTH SECTION
# -------------------------
if st.session_state.token is None:
    st.subheader("Login / Register")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Register"):
            try:
                res = requests.post(
                    f"{API}/register",
                    json={"username": username, "password": password},
                    timeout=5
                )
                if res.status_code == 200:
                    st.success("Registered successfully. Please login.")
                else:
                    st.error("Registration failed.")
            except requests.exceptions.RequestException:
                st.error("Backend not reachable.")

    with col2:
        if st.button("Login"):
            try:
                res = requests.post(
                    f"{API}/login",
                    json={"username": username, "password": password},
                    timeout=5
                )
                if res.status_code == 200:
                    st.session_state.token = res.json()["token"]
                    st.success("Login successful.")
                else:
                    st.error("Invalid credentials.")
            except requests.exceptions.RequestException:
                st.error("Backend not reachable.")

# -------------------------
# MAIN APP (AFTER LOGIN)
# -------------------------
else:
    headers = {"token": st.session_state.token}

    if st.button("Logout"):
        st.session_state.token = None
        st.info("Logged out.")
        st.stop()

    # -------------------------
    # STOCK SCREENER
    # -------------------------
    st.subheader("Stock Screener")

    query = st.text_input(
        "Enter your stock query",
        placeholder="Example: pe below 20 and sector equals IT"
    )

    if st.button("Search"):
        try:
            res = requests.post(
                f"{API}/screen",
                json={"query": query},
                headers=headers,
                timeout=10
            )

            if res.status_code == 200:
                data = res.json().get("data", [])
                if data:
                    st.dataframe(pd.DataFrame(data), use_container_width=True)
                else:
                    st.info("No matching stocks found.")
            else:
                st.error("Query failed. Check backend logs.")

        except requests.exceptions.RequestException:
            st.error("Backend not reachable.")

    # -------------------------
    # PORTFOLIO
    # -------------------------
    st.subheader("Portfolio")

    if st.button("Create Portfolio"):
        try:
            res = requests.post(f"{API}/portfolio/create", headers=headers)
            if res.status_code == 200:
                st.success(f"Portfolio created. ID: {res.json()['portfolio_id']}")
            else:
                st.error("Failed to create portfolio.")
        except requests.exceptions.RequestException:
            st.error("Backend not reachable.")

    portfolio_id = st.number_input("Portfolio ID", min_value=1, step=1)
    stock_id = st.number_input("Stock ID (1–25)", min_value=1, max_value=25, step=1)
    quantity = st.number_input("Quantity", min_value=1, step=1)
    buy_price = st.number_input("Buy Price", min_value=0.0, step=0.01)

    if st.button("Add to Portfolio"):
        try:
            res = requests.post(
                f"{API}/portfolio/add",
                json={
                    "portfolio_id": portfolio_id,
                    "stock_id": stock_id,
                    "quantity": quantity,
                    "buy_price": buy_price
                },
                headers=headers
            )
            if res.status_code == 200:
                st.success("Stock added to portfolio.")
            else:
                st.error("Failed to add stock.")
        except requests.exceptions.RequestException:
            st.error("Backend not reachable.")

    if st.button("View Portfolio"):
        try:
            res = requests.get(
                f"{API}/portfolio/view/{portfolio_id}",
                headers=headers
            )
            if res.status_code == 200:
                holdings = res.json().get("holdings", [])
                if holdings:
                    st.dataframe(pd.DataFrame(holdings), use_container_width=True)
                else:
                    st.info("No holdings found.")
            else:
                st.error("Failed to fetch portfolio.")
        except requests.exceptions.RequestException:
            st.error("Backend not reachable.")

    # -------------------------
    # MARKET SIMULATION
    # -------------------------
    st.subheader("Market Simulation")

    if st.button("Simulate Market Price Change"):
        try:
            res = requests.post(
                f"{API}/market/simulate",
                headers=headers
            )
            if res.status_code == 200:
                st.success("Market prices updated. Refresh portfolio to see changes.")
            else:
                st.error("Market simulation failed.")
        except requests.exceptions.RequestException:
            st.error("Backend not reachable.")
