import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.title("Dummy Auth Flow Demo")

# -----------------------------
# Session state
# -----------------------------
if "token" not in st.session_state:
    st.session_state.token = None

# -----------------------------
# LOGIN UI
# -----------------------------
st.subheader("Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    response = requests.post(
        f"{API_BASE}/login",
        json={"email": email, "password": password}
    )

    if response.status_code == 200:
        st.session_state.token = response.json()["token"]
        st.success("Login successful")
    else:
        st.error("Invalid credentials")

# -----------------------------
# PROTECTED API CALL
# -----------------------------
st.subheader("Portfolio (Protected API)")

if st.session_state.token:
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    if st.button("Fetch Portfolio"):
        response = requests.get(
            f"{API_BASE}/portfolio",
            headers=headers
        )

        if response.status_code == 200:
            st.json(response.json())
        else:
            st.error("Unauthorized access")
else:
    st.info("Please login first")
