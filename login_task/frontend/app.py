import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.title("Simple Login")

if "token" not in st.session_state:
    st.session_state.token = None

if st.session_state.token is None:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        r = requests.post(
            f"{BACKEND_URL}/login",
            json={"username": username, "password": password}
        )

        if r.status_code == 200:
            st.session_state.token = r.json()["access_token"]
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Wrong credentials")

else:
    st.success("Logged in already")

    if st.button("Call Protected API"):
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        r = requests.get(f"{BACKEND_URL}/protected", headers=headers)

        st.write(r.json())

    if st.button("Logout"):
        st.session_state.token = None
        st.rerun()
