import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Stock Explorer",
    layout="centered"
)

# -------------------------
# SESSION STATE
# -------------------------
if "token" not in st.session_state:
    st.session_state.token = None

if "page" not in st.session_state:
    st.session_state.page = "login"

# -------------------------
# LOGIN / REGISTER PAGE
# -------------------------
def login_page():
    st.title("AI Stock Explorer")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            res = requests.post(
                f"{API_URL}/login",
                json={"username": username, "password": password}
            )
            if res.status_code == 200:
                st.session_state.token = res.json()["token"]
                st.session_state.page = "screener"
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")

        if st.button("Register"):
            res = requests.post(
                f"{API_URL}/register",
                json={"username": username, "password": password}
            )
            if res.status_code == 200:
                st.success("Registered successfully")
            else:
                st.error("Registration failed")

# -------------------------
# SCREENER + ALERTS PAGE
# -------------------------
def screener_page():
    st.title("AI Stock Explorer")

    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.page = "login"
        st.rerun()

    query = st.text_input(
        "Enter your stock query",
        placeholder="Example: pe below 20 and sector equals IT"
    )

    headers = {"token": st.session_state.token}

    # -------------------------
    # SEARCH
    # -------------------------
    if st.button("Search"):
        res = requests.post(
            f"{API_URL}/screen",
            json={"query": query},
            headers=headers
        )

        if res.status_code == 200:
            data = res.json()["data"]
            if len(data) == 0:
                st.info("No matching stocks found")
            else:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
        else:
            st.error(res.json().get("detail", "Query failed"))

    # -------------------------
    # CREATE ALERT
    # -------------------------
    if st.button("Create Alert"):
        res = requests.post(
            f"{API_URL}/alerts/create",
            json={"query": query},
            headers=headers
        )

        if res.status_code == 200:
            st.success("Alert created")
        else:
            st.error(res.json().get("detail", "Failed to create alert"))

    # -------------------------
    # CHECK ALERTS
    # -------------------------
    if st.button("Check Alerts"):
        res = requests.get(
            f"{API_URL}/alerts/evaluate",
            headers=headers
        )

        if res.status_code == 200:
            result = res.json()
            alerts = result.get("triggered_alerts", [])

            if len(alerts) == 0:
                st.info("No new alerts")
            else:
                # IMPORTANT: backend returns 'symbol', NOT 'stock'
                df = pd.DataFrame(alerts)
                st.dataframe(df, use_container_width=True)
        else:
            st.error("Failed to fetch alerts")

# -------------------------
# ROUTING
# -------------------------
if st.session_state.page == "login":
    login_page()
else:
    screener_page()
