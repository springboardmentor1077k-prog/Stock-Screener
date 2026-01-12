import streamlit as st
import requests
import pandas as pd
st.markdown("""
<style>
/* Remove white background blocks */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #ffffff;
}

section[data-testid="stSidebar"],
div[data-testid="stVerticalBlock"] {
    background-color: transparent !important;
}

/* Remove white cards */
div[data-testid="stMetric"] {
    background-color: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 10px;
}

/* Inputs styling */
input, textarea {
    background-color: rgba(255,255,255,0.08) !important;
    color: white !important;
}

/* Dataframe background */
[data-testid="stDataFrame"] {
    background-color: rgba(255,255,255,0.03);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)



API_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="AI Stock Screener",
    layout="wide",
    page_icon="📊"
)

# ---------- SESSION ----------
if "token" not in st.session_state:
    st.session_state.token = None

st.markdown("""
<h1 style='text-align:center;'>📊 AI-Powered Stock Screener</h1>
<p style='text-align:center; color:#475569;'>
Secure • Data-Driven • Real-Time Market Insights
</p>
""", unsafe_allow_html=True)


# ---------- AUTH TABS ----------
tab1, tab2 = st.tabs(["🔐 Login", "🆕 Sign Up"])

# ================= SIGN UP =================
with tab2:
    st.subheader("Create New Account")

    signup_email = st.text_input("Email", key="signup_email")
    signup_password = st.text_input(
        "Password", type="password", key="signup_password"
    )

    if st.button("Sign Up"):
        res = requests.post(
            f"{API_URL}/signup",
            params={
                "email": signup_email,
                "password": signup_password
            }
        )

        if res.status_code == 200:
            st.success("Account created successfully. Please login.")
        else:
            st.error(res.json().get("detail", "Signup failed"))

# ================= LOGIN =================
with tab1:
    st.subheader("Login")

    login_email = st.text_input("Email", key="login_email")
    login_password = st.text_input(
        "Password", type="password", key="login_password"
    )

    if st.button("Login"):
        res = requests.post(
            f"{API_URL}/login",
            data={
                "username": login_email,
                "password": login_password
            }
        )

        if res.status_code == 200:
            st.session_state.token = res.json()["access_token"]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials. New users must Sign Up first.")

# ================= DASHBOARD =================
if st.session_state.token:
    st.divider()

    st.subheader("🔐 Access Token")
    st.code(st.session_state.token)

    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    # ---------- FETCH STOCKS + FUNDAMENTALS ----------
    res = requests.get(
        f"{API_URL}/stocks-with-fundamentals",
        headers=headers
    )

    if res.status_code == 200:
        data = res.json()["data"]
        df = pd.DataFrame(data)

        if not df.empty:
            st.subheader("📈 Stock Fundamentals Screener")

            # -------- Filters --------
            col1, col2 = st.columns(2)

            with col1:
                sector_filter = st.selectbox(
                    "Filter by Sector",
                    ["All"] + sorted(df["sector"].dropna().unique())
                )

            with col2:
                max_pe = st.slider(
                    "Max PE Ratio",
                    min_value=0.0,
                    max_value=float(df["pe_ratio"].max()),
                    value=float(df["pe_ratio"].max())
                )

            if sector_filter != "All":
                df = df[df["sector"] == sector_filter]

            df = df[df["pe_ratio"] <= max_pe]

            m1, m2, m3 = st.columns(3)

            with m1:
                st.metric("📌 Total Stocks", len(df))

            with m2:
                st.metric("📉 Avg PE Ratio", round(df["pe_ratio"].mean(), 2))

            with m3:
                st.metric("📈 Avg PEG Ratio", round(df["peg_ratio"].mean(), 2))


            st.divider()

            # -------- Data Table --------
            st.dataframe(
                df.rename(columns={
                    "stock_id": "Symbol",
                    "company_name": "Company",
                    "sector": "Sector",
                    "pe_ratio": "PE Ratio",
                    "peg_ratio": "PEG Ratio"
                }),
                use_container_width=True
            )

        else:
            st.info("No stock fundamentals available")

    else:
        st.error("Unauthorized or server error")

    # ---------- LOGOUT ----------
    if st.button("Logout"):
        st.session_state.token = None
        st.rerun()
