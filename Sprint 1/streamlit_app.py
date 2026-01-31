import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

# ---------------- CONFIG ----------------
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI Stock Screener",
    page_icon="📊",
    layout="wide"
)

# ---------------- DARK UI CSS ----------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: #fafafa;
}
.card {
    background-color: #111827;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 16px;
}
.ai-box {
    background: linear-gradient(135deg, #1f2937, #020617);
    padding: 18px;
    border-radius: 14px;
    border-left: 4px solid #22c55e;
    font-size: 16px;
}
.dsl-box {
    background-color: #020617;
    padding: 14px;
    border-radius: 12px;
    font-family: monospace;
    color: #38bdf8;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "token" not in st.session_state:
    st.session_state.token = None

# ---------------- LOGIN ----------------
st.title("📊 AI Stock Screener")

if not st.session_state.token:
    st.subheader("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = requests.post(
            f"{API_URL}/login",
            data={"username": email, "password": password}
        )
        if res.status_code == 200:
            st.session_state.token = res.json()["access_token"]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ---------------- TOP BAR ----------------
top_col1, top_col2 = st.columns([6, 1])

with top_col2:
    if st.button("🚪 Logout"):
        st.session_state.token = None
        st.rerun()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# ---------------- QUERY INPUT ----------------
st.subheader("🔎 Type your query here")

query = st.text_input(
    "Ask like:",
    placeholder="Technology stocks with PE ratio less than 20"
)

# ---------------- RUN QUERY ----------------
if st.button("Run Query") and query:
    with st.spinner("Running intelligent screening..."):
        res = requests.post(
            f"{API_URL}/nl-query",
            headers=headers,
            json={"query": query}
        )

    if res.status_code != 200:
        st.error(res.json()["detail"])
        st.stop()

    data = res.json()
    results = data["results"]
    dsl = data["dsl"]

    # ---------------- DSL PREVIEW ----------------
    st.markdown("### 🧩 Generated DSL")
    st.markdown(
        f"<div class='dsl-box'>{json.dumps(dsl, indent=2)}</div>",
        unsafe_allow_html=True
    )

    if not results:
        st.warning("No matching results found.")
        st.stop()

    df = pd.DataFrame(results)

    # ---------------- METRICS ----------------
    st.markdown("### 📈 Summary")
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Stocks Found", len(df))
    m2.metric("Avg PE", round(df["pe_ratio"].mean(), 2))
    m3.metric("Avg PEG", round(df["peg_ratio"].mean(), 2))
    m4.metric("Avg Dividend", round(df["dividend_yield"].mean(), 2))

    # ---------------- TABLE ----------------
    st.markdown("### 📋 Stock Results")

    def highlight_pe(val):
        if pd.isna(val):
            return ""
        if val <= 15:
            return "background-color: #14532d; color: white"
        elif val <= 25:
            return "background-color: #064e3b; color: white"
        else:
            return "background-color: #7f1d1d; color: white"

    styled_df = (
        df.style
        .applymap(highlight_pe, subset=["pe_ratio"])
        .format({
            "pe_ratio": "{:.2f}",
            "peg_ratio": "{:.2f}",
            "dividend_yield": "{:.2f}"
        })
    )

    st.dataframe(styled_df, use_container_width=True)

    # ---------------- CHARTS ----------------
    st.markdown("### 📊 Visual Insights")

    c1, c2 = st.columns(2)

    with c1:
        fig_sector = px.pie(
            df,
            names="sector",
            hole=0.5,
            title="Sector Split"
        )
        st.plotly_chart(fig_sector, use_container_width=True)

    with c2:
        fig_pe = px.histogram(
            df,
            x="pe_ratio",
            nbins=20,
            title="PE Ratio Distribution"
        )
        st.plotly_chart(fig_pe, use_container_width=True)

    # ---------------- AI INSIGHTS ----------------
    #-st.markdown("### 🧠 AI Insights")

    explain_payload = {
        "sector_summary": df["sector"].value_counts().to_dict(),
        "avg_pe": float(df["pe_ratio"].mean()),
        "avg_peg": float(df["peg_ratio"].mean()),
        "avg_dividend": float(df["dividend_yield"].mean())
    }

    with st.spinner("Thinking like an analyst..."):
        exp = requests.post(
            f"{API_URL}/explain-results",
            headers=headers,
            json=explain_payload
        )

    if exp.status_code == 200:
        st.markdown(
            f"<div class='ai-box'>{exp.json()['explanation']}</div>",
            unsafe_allow_html=True
        )

# ---------------- QUERY HISTORY ----------------
st.divider()
st.markdown("### 🕘 Query History")

hist = requests.get(
    f"{API_URL}/query-history",
    headers=headers
)

if hist.status_code == 200:
    history = hist.json()["history"]

    if history:
        for h in history:
            with st.expander(f"🔍 {h['nl_query']}"):
                st.code(json.dumps(h["dsl"], indent=2), language="json")
    else:
        st.info("No query history yet.") 