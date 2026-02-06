import streamlit as st
import requests
import pandas as pd

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="AI Stock Screener",
    layout="wide",
    page_icon="📊"
)

# ===============================
# HEADER
# ===============================
st.markdown("""
<style>
.big-title {
    font-size: 36px;
    font-weight: 700;
}
.subtitle {
    color: #9ca3af;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">📊 AI Stock Screener</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Natural Language → LLM → DSL → SQL → PostgreSQL</div>',
    unsafe_allow_html=True
)

st.divider()

API_URL = "http://127.0.0.1:8000/screen"

st.subheader("🔍 Ask in plain English")

nl_query = st.text_input(
    "",
    placeholder="e.g. Show me stocks with PE ratio less than 40"
)

run_btn = st.button("🚀 Run Screener", use_container_width=True)

def friendly_error(msg: str) -> str:
    msg = msg.lower()

    if "filters must be a list" in msg or "did not return valid json" in msg:
        return "❌ Your query is not related to stock screening. Please try a finance-related query."

    if "invalid field" in msg or "invalid operator" in msg:
        return "❌ The query contains unsupported conditions."

    if "missing 'query'" in msg:
        return "❌ Please enter a valid query."

    return "❌ Unable to process your request. Please try again."

# ===============================
# EXECUTION
# ===============================
if run_btn:
    if not nl_query.strip():
        st.warning("⚠️ Please enter a stock-related query.")
    else:
        try:
            response = requests.post(API_URL, json={"query": nl_query})

            # -------------------------------
            # ERROR CASE
            # -------------------------------
            if response.status_code != 200:
                backend_msg = response.json().get("detail", "")
                st.error("Error")
                st.warning(friendly_error(backend_msg))

            # -------------------------------
            # SUCCESS CASE
            # -------------------------------
            else:
                results = response.json().get("results", [])

                if not results:
                    st.info("ℹ️ No matching stocks found for the given criteria.")
                else:
                    df = pd.DataFrame(results)
                    df.columns = ["Stock Symbol", "Company Name", "P/E Ratio"]

                    st.success(f"✅ {len(df)} stocks matched")
                    st.dataframe(df, use_container_width=True)

        except requests.exceptions.ConnectionError:
            st.error("❌ Backend server is not running. Please start FastAPI.")
