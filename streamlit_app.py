import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL")

st.set_page_config(
    page_title="AI Stock Screener",
    page_icon="📊",
    layout="wide"
)

# ---------------- SESSION ----------------
if "token" not in st.session_state:
    st.session_state.token = None

st.title("📊 AI Stock Screener")

# ---------------- AUTH ----------------
if not st.session_state.token:
    st.subheader("Login / Signup")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    # -------- LOGIN --------
    if col1.button("Login"):
        r = requests.post(
            f"{API_URL}/auth/login",
            json={"email": email, "password": password}
        )

        if r.ok:
            st.session_state.token = r.json()["access_token"]
            st.success("Login successful")
            st.rerun()
        else:
            # ✅ SAFE ERROR HANDLING
            try:
                st.error(r.json().get("detail", r.text))
            except Exception:
                st.error(r.text)

    # -------- SIGNUP --------
    if col2.button("Signup"):
        r = requests.post(
            f"{API_URL}/auth/signup",
            json={"email": email, "password": password}
        )

        if r.ok:
            st.success("User created. Please login.")
        else:
            # ✅ SAFE ERROR HANDLING
            try:
                st.error(r.json().get("detail", r.text))
            except Exception:
                st.error(r.text)

# ---------------- DASHBOARD ----------------
else:
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    r = requests.get(f"{API_URL}/stocks", headers=headers)

    if r.ok:
        df = pd.DataFrame(r.json())
        st.subheader("📈 Stocks Overview")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Failed to fetch stock data")

    if st.button("Logout"):
        st.session_state.token = None
        st.rerun()
