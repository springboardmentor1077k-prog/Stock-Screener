import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

# ---------------- CONFIG ----------------
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="ProTrade AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- STYLING (Fast CSS) ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0e1117; 
        color: #e0e0e0;
    }

    /* Fast Button Styling */
    div.stButton > button {
        background: #2563eb;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
        transition: background 0.2s;
    }
    div.stButton > button:hover {
        background: #1d4ed8;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "token" not in st.session_state:
    st.session_state.token = None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚡ ProTrade AI")
    st.caption("High-Performance Screener")
    
    if st.session_state.token:
        st.success("🟢 System Online")
        if st.button("🚪 Logout"):
            st.session_state.token = None
            st.rerun()
    else:
        st.warning("🔴 System Offline")

# ---------------- LOGIN SCREEN ----------------
if not st.session_state.token:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("### 🔐 Secure Access")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                try:
                    # Added Timeout to prevent hanging
                    res = requests.post(f"{API_URL}/login", data={"username": email, "password": password}, timeout=5)
                    if res.status_code == 200:
                        st.session_state.token = res.json()["access_token"]
                        st.rerun()
                    else:
                        st.error("Access Denied.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to Backend. Is 'main.py' running?")
                except Exception as e:
                    st.error(f"Error: {e}")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# ---------------- MAIN UI ----------------
st.markdown("## 🔎 Market Scanner")

c1, c2 = st.columns([4, 1])
with c1:
    query = st.text_input(
        "Query",
        placeholder="e.g., Tech stocks with PE < 30 OR Energy stocks with Dividend > 3",
        label_visibility="collapsed"
    )
with c2:
    search_btn = st.button("🚀 Scan Market", type="primary", use_container_width=True)

# ---------------- LOGIC ----------------
if search_btn and query:
    # Use Standard Spinner (Instant, no download required)
    with st.spinner("⚡ Scanning Market Data..."):
        try:
            # 10 Second Timeout to ensure it doesn't hang forever
            res = requests.post(f"{API_URL}/nl-query", headers=headers, json={"query": query}, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                st.session_state.results = data["results"]
                st.session_state.dsl = data["dsl"]
            else:
                st.error(f"Server Error: {res.text}")
                
        except requests.exceptions.ReadTimeout:
            st.error("⏱️ Request Timed Out. The backend is taking too long.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection Refused. Make sure 'main.py' is running.")
        except Exception as e:
            st.error(f"Unexpected Error: {e}")

# Display Results
if "results" in st.session_state and st.session_state.results:
    results = st.session_state.results
    df = pd.DataFrame(results)
    
    # METRICS
    st.markdown("###")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matches", len(df))
    m2.metric("Avg PE", f"{df['pe_ratio'].mean():.2f}")
    
    upside = "N/A"
    if "analyst_upside" in df and not df["analyst_upside"].dropna().empty:
        upside = f"{df['analyst_upside'].mean():.1f}%"
    m3.metric("Avg Upside", upside)
    m4.metric("Avg Div Yield", f"{df['dividend_yield'].mean():.2f}%")

    # TABS
    t1, t2, t3, t4, t5 = st.tabs([
        "📋 Results", 
        "🎯 Targets", 
        "📊 Visuals", 
        "🧠 AI Insight", 
        "🔧 Logic"
    ])

    # TAB 1: FUNDAMENTALS (Removed Logo Column for Speed)
    with t1:
        st.caption("Fundamental Data")
        fund_cols = ["ticker", "company_name", "sector", "pe_ratio", "dividend_yield", "debt_to_equity"]
        fund_cols = [c for c in fund_cols if c in df.columns]

        st.dataframe(
            df[fund_cols],
            column_config={
                "pe_ratio": st.column_config.NumberColumn("PE Ratio", format="%.2f"),
                "dividend_yield": st.column_config.NumberColumn("Div Yield", format="%.2f%%"),
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )

    # TAB 2: ANALYST TARGETS
    with t2:
        st.caption("Analyst Forecasts")
        target_cols = ["ticker", "current_price", "avg_target", "analyst_rating", "analyst_upside"]
        
        if "analyst_rating" in df.columns:
            st.dataframe(
                df[target_cols],
                column_config={
                    "current_price": st.column_config.NumberColumn("Current", format="$%.2f"),
                    "avg_target": st.column_config.NumberColumn("Target", format="$%.2f"),
                    "analyst_upside": st.column_config.ProgressColumn("Upside", format="%.1f%%", min_value=-20, max_value=50),
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("No analyst data found.")

    # TAB 3: CHARTS
    with t3:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(df, names="sector", title="Sector Split", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if "analyst_upside" in df.columns:
                fig = px.bar(df, x="ticker", y="analyst_upside", title="Upside Potential")
                st.plotly_chart(fig, use_container_width=True)

    # TAB 4: AI INSIGHTS
    with t4:
        if st.button("Generate AI Report"):
            with st.spinner("Generating..."):
                try:
                    payload = {
                        "sector_summary": df["sector"].value_counts().to_dict(),
                        "avg_pe": float(df["pe_ratio"].mean()),
                        "avg_peg": 0.0,
                        "avg_dividend": float(df["dividend_yield"].mean())
                    }
                    exp = requests.post(f"{API_URL}/explain-results", headers=headers, json=payload, timeout=8)
                    if exp.status_code == 200:
                        st.success("Analysis Complete")
                        st.markdown(exp.json()['explanation'])
                    else:
                        st.error("AI Service Error")
                except Exception as e:
                    st.error(f"AI Timeout: {e}")

    # TAB 5: DEBUG LOGIC
    with t5:
        st.json(st.session_state.dsl)