import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Stock Explorer",
    layout="centered"
)

# -------------------------
# Session State Init
# -------------------------
if "token" not in st.session_state:
    st.session_state.token = None

if "page" not in st.session_state:
    st.session_state.page = "login"


# -------------------------
# Custom Styling
# -------------------------
st.markdown("""
<style>
.main-title {
    font-size: 40px;
    font-weight: 700;
    color: #1f3c88;
    text-align: center;
}
.tagline {
    font-size: 16px;
    color: #555;
    text-align: center;
    margin-bottom: 30px;
}
.section-title {
    font-size: 24px;
    font-weight: 600;
    color: #1f3c88;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# LOGIN PAGE
# -------------------------
def login_page():
    st.markdown('<div class="main-title">AI Stock Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Search stocks using simple English queries</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    # -------- LOGIN --------
    with tab1:
        st.markdown('<div class="section-title">Login</div>', unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            payload = {"username": username, "password": password}

            try:
                res = requests.post(f"{API_URL}/login", json=payload, timeout=5)

                if res.status_code == 200:
                    st.session_state.token = res.json()["token"]
                    st.session_state.page = "screener"
                    st.success("✅ Login successful")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Login failed"))

            except requests.exceptions.ConnectionError:
                st.error("❌ Backend server is not running.")
            except requests.exceptions.Timeout:
                st.error("❌ Backend request timed out.")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")

    # -------- REGISTER --------
    with tab2:
        st.markdown('<div class="section-title">Register</div>', unsafe_allow_html=True)
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Register"):
            payload = {"username": new_user, "password": new_pass}

            try:
                res = requests.post(f"{API_URL}/register", json=payload, timeout=5)

                if res.status_code == 200:
                    st.success("🎉 Registration successful. Please login.")
                else:
                    st.error(res.json().get("detail", "Registration failed"))

            except requests.exceptions.ConnectionError:
                st.error("❌ Backend server is not running.")
            except requests.exceptions.Timeout:
                st.error("❌ Backend request timed out.")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")


# -------------------------
# SCREENER PAGE
# -------------------------
def screener_page():
    st.markdown('<div class="main-title">AI Stock Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Search stocks using simple English queries</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.page = "login"
            st.rerun()

    st.markdown('<div class="section-title">Stock Screener</div>', unsafe_allow_html=True)

    query = st.text_input(
        "Enter your stock query",
        placeholder="Example: show IT stocks below 20 pe"
    )

    if st.button("Search"):
        if not query:
            st.warning("Please enter a query")
            return

        headers = {"token": st.session_state.token}
        payload = {"query": query}

        try:
            res = requests.post(
                f"{API_URL}/screen",
                json=payload,
                headers=headers,
                timeout=10
            )

            if res.status_code == 200:
                result = res.json()
                count = result["count"]
                data = result["data"]

                st.success(f"✅ Total matching stocks: {count}")

                if count > 0:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No matching results found.")

            else:
                error_msg = res.json().get("detail", "Invalid query")
                st.error(f"❌ {error_msg}")

        except requests.exceptions.ConnectionError:
            st.error("❌ Backend server is not running.")
        except requests.exceptions.Timeout:
            st.error("❌ Backend request timed out.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")


# -------------------------
# ROUTING
# -------------------------
if st.session_state.page == "login":
    login_page()
else:
    screener_page()
