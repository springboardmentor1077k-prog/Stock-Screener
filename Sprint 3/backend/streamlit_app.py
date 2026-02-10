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

# ---------------- 1. CUSTOM CSS (THE "REAL WEBSITE" LOOK) ----------------
st.markdown("""
<style>
    /* IMPORT GOOGLE FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* GLOBAL STYLES */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0f172a; /* Dark Navy Background */
        color: #f8fafc;
    }

    /* REMOVE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* CUSTOM NAVBAR */
    .navbar {
        padding: 15px 20px;
        background: #1e293b;
        border-bottom: 1px solid #334155;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .navbar-title {
        font-size: 24px;
        font-weight: 700;
        color: #38bdf8; /* Light Blue */
        margin-right: auto;
    }
    .navbar-status {
        font-size: 14px;
        color: #94a3b8;
        background: #0f172a;
        padding: 5px 12px;
        border-radius: 20px;
        border: 1px solid #334155;
    }

    /* CARD STYLING FOR METRICS */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #38bdf8;
    }

    /* BUTTON STYLING */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.5);
    }

    /* DISCLAIMER BOX */
    .disclaimer-box {
        background-color: #1e293b; 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 25px; 
        border-left: 4px solid #f59e0b;
        font-size: 0.9em;
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "token" not in st.session_state:
    st.session_state.token = None

# ---------------- 2. TOP NAVIGATION BAR ----------------
def render_navbar():
    # Simple Health Check for the Status Badge
    status_color = "🔴 Offline"
    try:
        if requests.get(f"{API_URL}/health", timeout=1).status_code == 200:
            status_color = "🟢 System Online"
    except:
        pass

    st.markdown(f"""
        <div class="navbar">
            <div class="navbar-title">⚡ ProTrade AI</div>
            <div class="navbar-status">{status_color}</div>
        </div>
    """, unsafe_allow_html=True)

render_navbar()

# ---------------- 3. LANDING PAGE (IF NOT LOGGED IN) ----------------
if not st.session_state.token:
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("Intelligent Market Screening.")
        st.markdown("""
            <h3 style='color: #94a3b8; font-weight: 400;'>
            Stop searching manually. Use AI to filter stocks by valuation, growth, and sector trends in seconds.
            </h3>
            <br>
        """, unsafe_allow_html=True)
        
        st.info("💡 **Try Queries Like:**\n- *'Tech stocks with PE < 25 and PEG < 1.5'*\n- *'Healthcare stocks with Dividend > 3%'*")

    with c2:
        st.markdown("""
            <div style='background: #1e293b; padding: 30px; border-radius: 15px; border: 1px solid #334155; margin-top: 20px;'>
                <h3 style='text-align: center;'>Get Started</h3>
        """, unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["Login", "Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                
                if submitted:
                    try:
                        res = requests.post(f"{API_URL}/login", data={"username": email, "password": password}, timeout=5)
                        if res.status_code == 200:
                            st.session_state.token = res.json()["access_token"]
                            st.rerun()
                        else:
                            st.error("❌ Invalid Credentials")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("New Email")
                new_password = st.text_input("New Password", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                signup_submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if signup_submitted:
                    try:
                        res = requests.post(f"{API_URL}/signup", json={"email": new_email, "password": new_password}, timeout=5)
                        if res.status_code == 200:
                            st.success("✅ Account created! Please log in.")
                        else:
                            st.error(f"Error: {res.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ---------------- 4. AUTHENTICATED DASHBOARD ----------------

# --- SIDEBAR MENU ---
with st.sidebar:
    st.markdown("### 👤 User Menu")
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.token = None
        st.rerun()
        
    st.markdown("---")
    st.caption("Database Tools")
    if st.button("📊 DB Stats", use_container_width=True):
        try:
            check = requests.post(
                f"{API_URL}/nl-query", 
                headers={"Authorization": f"Bearer {st.session_state.token}"}, 
                json={"query": "stocks"}, 
                timeout=5
            )
            count = len(check.json().get("results", []))
            st.info(f"Tracking {count} stocks")
        except:
            st.error("Connection Failed")

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# --- MAIN SCREENER INTERFACE ---

# Disclaimer
st.markdown("""
    <div class="disclaimer-box">
        <strong>⚠️ Disclaimer:</strong> Results are for informational purposes only. Always verify data independently.
    </div>
""", unsafe_allow_html=True)

# Query Box
c1, c2 = st.columns([5, 1])
with c1:
    query = st.text_input("Ask the Market", placeholder="e.g. Undervalued Tech stocks with strong growth...", label_visibility="collapsed")
with c2:
    search_btn = st.button("Run Scan 🚀", type="primary", use_container_width=True)

# Logic Execution
if search_btn and query:
    with st.spinner("⚡ analyzing market data..."):
        try:
            res = requests.post(f"{API_URL}/nl-query", headers=headers, json={"query": query}, timeout=30)
            if res.status_code == 200:
                data = res.json()
                st.session_state.results = data["results"]
                st.session_state.dsl = data["dsl"]
            else:
                st.error(f"Error {res.status_code}: {res.text}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

# Results Dashboard
if "results" in st.session_state:
    results = st.session_state.results
    
    # Process Data
    df = pd.DataFrame(results) if results else pd.DataFrame()
    
    # If empty, fill expected cols for structure
    expected_cols = ["ticker", "pe_ratio", "dividend_yield", "sector", "analyst_upside", "current_price"]
    for c in expected_cols:
        if c not in df.columns: df[c] = None

    if not df.empty:
        st.markdown(f"### ✅ Found {len(df)} Matches")
    
    # TABS LAYOUT
    t1, t2, t3, t4, t5, t6 = st.tabs(["📋 Table", "🎯 Targets", "💼 Portfolio", "🔔 Alerts", "📊 Charts", "🧠 AI Report"])

    # TAB 1: RESULTS (or TABLE)
    with t1:
        if not df.empty:
            # 1. ADD "peg_ratio" TO THIS LIST
            cols = ["ticker", "company_name", "sector", "pe_ratio", "peg_ratio", "dividend_yield", "debt_to_equity"]
            
            # 2. Filter to ensure columns exist in data
            final_cols = [c for c in cols if c in df.columns]
            
            # 3. Configure formatting (optional but looks better)
            st.dataframe(
                df[final_cols], 
                column_config={
                    "pe_ratio": st.column_config.NumberColumn("PE Ratio", format="%.2f"),
                    "peg_ratio": st.column_config.NumberColumn("PEG Ratio", format="%.2f"), # <--- Add Format
                    "dividend_yield": st.column_config.NumberColumn("Div Yield", format="%.2f%%"),
                },
                hide_index=True, 
                use_container_width=True, 
                height=450
            )
        else:
            st.warning("No matches found.")

    with t2:
        if not df.empty and 'avg_target' in df.columns:
            st.dataframe(
                df[["ticker", "current_price", "avg_target", "analyst_rating", "analyst_upside"]],
                column_config={
                    "analyst_upside": st.column_config.ProgressColumn("Upside", format="%.1f%%", min_value=-20, max_value=50)
                },
                hide_index=True, use_container_width=True
            )
        else:
            st.info("No analyst data available.")

    # TAB 3: PORTFOLIO
    with t3:
        try:
            # 1. Fetch Data
            p_data = requests.get(f"{API_URL}/portfolio", headers=headers).json()
            
            # 2. Summary Metrics
            if p_data["holdings"]:
                # Create 3 nice columns for high-level stats
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Investment", f"${(p_data['total_value'] - p_data['total_profit_loss']):,.2f}")
                m2.metric("Current Value", f"${p_data['total_value']:,.2f}")
                m3.metric("Total P/L", f"${p_data['total_profit_loss']:,.2f}", 
                          delta_color="normal" if p_data['total_profit_loss'] >= 0 else "inverse")

                # 3. Clean & Format the Table
                p_df = pd.DataFrame(p_data["holdings"])

                # Select ONLY columns we want to see (Hide portfolio_id)
                display_cols = [
                    "ticker", "company_name", "sector", "quantity", 
                    "buy_price", "current_price", "current_value", 
                    "profit_loss", "profit_loss_pct"
                ]
                
                # Configure formatting (Money, %, Colors)
                st.dataframe(
                    p_df[display_cols],
                    column_config={
                        "ticker": "Symbol",
                        "company_name": "Company",
                        "sector": "Sector",
                        "quantity": "Qty",
                        "buy_price": st.column_config.NumberColumn("Avg Buy", format="$%.2f"),
                        "current_price": st.column_config.NumberColumn("Current Price", format="$%.2f"),
                        "current_value": st.column_config.NumberColumn("Value", format="$%.2f"),
                        "profit_loss": st.column_config.NumberColumn(
                            "P/L ($)", 
                            format="$%.2f",
                        ),
                        "profit_loss_pct": st.column_config.NumberColumn(
                            "P/L (%)", 
                            format="%.2f%%",
                        ),
                    },
                    hide_index=True, 
                    use_container_width=True
                )
            else:
                st.info("Your portfolio is empty.")
                
        except Exception as e:
            st.error(f"Could not load portfolio: {e}")
    with t4: # ALERTS TAB
        with st.form("new_alert"):
            ac1, ac2, ac3, ac4 = st.columns([2,1,1,1])
            with ac1: metric = st.selectbox("Metric", ["pe_ratio", "price", "dividend_yield"])
            with ac2: op = st.selectbox("Op", ["<", ">"])
            with ac3: val = st.number_input("Value", value=20.0)
            with ac4: 
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Set Alert"):
                    requests.post(f"{API_URL}/alerts", headers=headers, json={"metric": metric, "operator": op, "threshold": val})
                    st.success("Set!")
                    
        if st.button("Run Alert Check"):
             check = requests.post(f"{API_URL}/alerts/check", headers=headers).json()
             if check.get("new_events_triggered") > 0:
                 st.toast(f"🚨 {check['new_events_triggered']} Alerts Triggered!", icon="🔥")
                 st.rerun()
             else:
                 st.success("No new triggers.")

        # Show History
        data = requests.get(f"{API_URL}/alerts", headers=headers).json()
        if data.get("events"):
            st.dataframe(pd.DataFrame(data["events"]), hide_index=True, use_container_width=True)

    with t5:
        if not df.empty:
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.pie(df, names="sector", title="Sector Distribution", hole=0.5), use_container_width=True)
            if "analyst_upside" in df.columns:
                c2.plotly_chart(px.bar(df, x="ticker", y="analyst_upside", title="Analyst Upside Potential"), use_container_width=True)

    with t6:
        if st.button("Generate AI Analysis"):
            with st.spinner("Consulting AI..."):
                payload = {
                    "sector_summary": df["sector"].value_counts().to_dict() if not df.empty else {},
                    "avg_pe": float(df["pe_ratio"].mean()) if not df.empty else 0,
                    "avg_peg": 0, "avg_dividend": float(df["dividend_yield"].mean()) if not df.empty else 0
                }
                explanation = requests.post(f"{API_URL}/explain-results", headers=headers, json=payload).json()["explanation"]
                st.markdown(explanation)
