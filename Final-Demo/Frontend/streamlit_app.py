import streamlit as st
import requests
import pandas as pd
import json
import time

# ---------------- CONFIG ----------------
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="ProTrade AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- COMPLIANCE TEXTS ---
DISCLAIMERS = {
    "global_banner": "🚧 **EDUCATIONAL PROTOTYPE:** This platform is for academic purposes only. Do not trade real money based on these results.",
    "global_footer": "© 2026 AI Screener Project. Data provided for educational use. Not investment advice.",
    "screener_results": "📉 **Data Accuracy Notice:** AI-generated results. Not a recommendation to buy.",
    "analyst_risk": "🎯 **Analyst Disclaimer:** Targets are subjective opinions. Never invest solely based on them.",
    "alerts_trigger": "🔔 **Alert Reliability:** Execution delays may occur."
}

# ---------------- CSS STYLES ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1639322537228-f710d846310a?auto=format&fit=crop&q=80&w=2000');
        background-size: cover;
        background-position: center center;
        background-attachment: fixed;
        background-blend-mode: overlay;
        background-color: rgba(15, 23, 42, 0.92);
    }
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }
    /* NAVBAR */
    .navbar {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px 25px;
        border-radius: 12px;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .navbar-brand {
        font-size: 26px;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    /* CARDS */
    .metric-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.8));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        transition: transform 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-5px); }
    
    /* BUTTONS */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        border: none;
        color: white;
        padding: 12px 28px;
        border-radius: 8px;
        font-weight: 600;
    }
    div.stButton > button:hover { transform: scale(1.02); }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "token" not in st.session_state:
    st.session_state.token = None
if "results" not in st.session_state:
    st.session_state.results = []
if "notified_events" not in st.session_state:
    st.session_state.notified_events = set() # Track shown alerts

# ---------------- HELPER: NOTIFICATION POLL ----------------
def check_notifications():
    """Poll backend for new alert triggers"""
    if not st.session_state.token: return
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        res = requests.get(f"{API_URL}/notifications", headers=headers)
        if res.status_code == 200:
            events = res.json()
            for e in events:
                event_id = e['event_id']
                if event_id not in st.session_state.notified_events:
                    # SHOW TOAST
                    msg = f"🚨 {e['ticker']} hit {e['metric']} {e['operator']} {e['threshold']}! Value: {e['triggered_value']}"
                    st.toast(msg, icon="🔔")
                    st.session_state.notified_events.add(event_id)
    except: pass

# ---------------- NAVBAR ----------------
def render_navbar():
    redis_status = "Checking..."
    try:
        health = requests.get(f"{API_URL}/health", timeout=0.5).json()
        if health["status"] == "ok":
            redis_txt = "⚡ Redis Active" if health.get("redis") == "connected" else "🐢 DB Mode"
            redis_status = f"🟢 Online | {redis_txt}"
    except:
        redis_status = "🔴 Offline"

    st.markdown(f"""
        <div class="navbar">
            <div class="navbar-brand">⚡ ProTrade AI</div>
            <div class="status-badge" style="color:#34d399; font-size:12px;">{redis_status}</div>
        </div>
    """, unsafe_allow_html=True)
    st.warning(DISCLAIMERS["global_banner"], icon="⚠️")

render_navbar()

# ---------------- LOGIN SCREEN ----------------
if not st.session_state.token:
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <h1 style='font-size: 56px; line-height: 1.1;'>
                Market Intelligence,<br><span style='color: #3b82f6;'>Simplified.</span>
            </h1>
            <p style='font-size: 18px; color: #94a3b8; margin-top: 20px;'>
                Use natural language to screen stocks, analyze trends, and manage your portfolio with AI.
            </p>
        """, unsafe_allow_html=True)
        st.info("💡 **Try:** *'Undervalued Tech stocks with High Growth'*")

    with c2:
        st.markdown("""<div class="metric-card" style='max-width: 400px; margin: auto;'>
            <h3 style='text-align: center;'>Welcome Back</h3>""", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["Login", "Register"])
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True):
                    try:
                        res = requests.post(f"{API_URL}/login", data={"username": email, "password": password})
                        if res.status_code == 200:
                            st.session_state.token = res.json()["access_token"]
                            st.rerun()
                        else:
                            st.error(res.json().get("message", "Login Failed"))
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        with tab_signup:
            with st.form("signup_form"):
                n_email = st.text_input("New Email")
                n_pass = st.text_input("New Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    try:
                        res = requests.post(f"{API_URL}/signup", json={"email": n_email, "password": n_pass})
                        if res.status_code == 200:
                            st.success("✅ Account created! Please log in.")
                        else:
                            st.error(res.json().get("message", "Signup Failed"))
                    except: st.error("Error")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ---------------- AUTH DASHBOARD ----------------
headers = {"Authorization": f"Bearer {st.session_state.token}"}

# POLL FOR ALERTS ON EVERY RELOAD
check_notifications()

with st.sidebar:
    st.markdown("### 👤 User Profile")
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.token = None
        st.rerun()
    st.markdown("---")
    st.caption(f"Connected to {API_URL}")

t_dash, t_screen, t_port, t_alert, t_ai = st.tabs([
    "🏠 Dashboard", "🔍 Screener", "💼 Portfolio", "🔔 Alerts", "🧠 AI Analysis"
])

# --- TAB 1: DASHBOARD ---
with t_dash:
    st.markdown("<h2>📊 Market Overview</h2>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("S&P 500", "4,783.45", "1.2%")
    with m2: st.metric("Nasdaq", "15,120.30", "0.8%")
    with m3: st.metric("Portfolio", "$12,450", "-0.5%")
    with m4: st.metric("Active Alerts", "3", "Running")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # RECENT ALERTS SECTION
    st.markdown("### 🕒 Recent Alerts Activity")
    try:
        notifs = requests.get(f"{API_URL}/notifications", headers=headers).json()
        if notifs:
            for n in notifs:
                st.info(f"⏰ {n['triggered_at'][:19]} | **{n['ticker']}** hit {n['metric']} {n['operator']} {n['threshold']} (Value: {n['triggered_value']})")
        else:
            st.caption("No recent alerts triggered.")
    except: st.caption("Could not load alerts.")

# --- TAB 2: SCREENER ---
with t_screen:
    st.markdown("<h2>🔍 AI Stock Screener</h2>", unsafe_allow_html=True)
    c_search, c_btn = st.columns([4, 1])
    with c_search: query = st.text_input("Search", placeholder="e.g. 'Undervalued Tech stocks'", label_visibility="collapsed")
    with c_btn: search = st.button("Run Scan 🚀", use_container_width=True)

    if search and query:
        with st.spinner("Analyzing..."):
            try:
                res = requests.post(f"{API_URL}/screen", headers=headers, json={"query": query})
                if res.status_code == 200:
                    st.session_state.results = res.json()["results"]
                    st.success(f"Found {len(st.session_state.results)} matches")
                else: st.error(res.json().get("message", "Error"))
            except Exception as e: st.error(f"Error: {e}")

    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        cols = ["ticker", "company_name", "sector", "pe_ratio", "dividend_yield", "current_price", "analyst_rating"]
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True)
    else:
        st.caption("Use the search bar above.")

# --- TAB 3: PORTFOLIO ---
with t_port:
    st.markdown("<h2>💼 My Portfolio</h2>", unsafe_allow_html=True)
    if st.button("Refresh"): st.rerun()
    try:
        data = requests.get(f"{API_URL}/portfolio", headers=headers).json()
        if data["holdings"]:
            st.metric("Total P/L", f"${data['total_profit_loss']:,.2f}")
            st.dataframe(pd.DataFrame(data["holdings"]), use_container_width=True)
        else: st.info("Portfolio empty.")
    except: st.error("Load failed.")

# --- TAB 4: ALERTS ---
with t_alert:
    st.markdown("<h2>🔔 Active Alerts</h2>", unsafe_allow_html=True)
    with st.form("new_alert"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: m = st.selectbox("Metric", ["price", "pe_ratio", "dividend_yield"])
        with c2: o = st.selectbox("Operator", ["<", ">"])
        with c3: v = st.number_input("Threshold", value=100.0)
        with c4: 
            st.write("")
            st.write("")
            s = st.form_submit_button("Create")
        if s:
            r = requests.post(f"{API_URL}/alerts", headers=headers, json={"metric": m, "operator": o, "threshold": v})
            if r.status_code == 200: st.success("Created!")
            else: st.error("Failed")
    
    st.markdown("### Your Active Rules")
    try:
        al = requests.get(f"{API_URL}/alerts", headers=headers).json()
        if al["alerts"]:
            st.dataframe(pd.DataFrame(al["alerts"]), use_container_width=True)
    except: pass

# --- TAB 5: AI ANALYSIS ---

with t_ai:

    st.markdown("<h2>🧠 AI Market Analysis</h2>", unsafe_allow_html=True)

   

    if st.session_state.results:

        col_ai_img, col_ai_btn = st.columns([1, 4])

       

        with col_ai_img:

            st.image("https://cdn-icons-png.flaticon.com/512/2040/2040946.png", width=100)

           

        with col_ai_btn:

             st.markdown("### Generate Intelligence Report")

             if st.button("Generate Report on Screened Stocks"):

               

                # --- NEW: Prepare Data Payload ---

                # We convert the entire results DataFrame to a list of dictionaries

                # This sends the actual Tickers, PEs, and Sectors to the backend

                stocks_payload = st.session_state.results

               

                with st.spinner("AI is analyzing market trends..."):

                    try:

                        # Send the full list of stocks

                        response = requests.post(

                            f"{API_URL}/explain-results",

                            headers=headers,

                            json={"stocks": stocks_payload}

                        )

                       

                        if response.status_code == 200:

                            expl = response.json()["explanation"]

                            st.markdown(f"""

                                <div class="metric-card">

                                    {expl}

                                </div>

                            """, unsafe_allow_html=True)

                        else:

                            st.error(f"Analysis Error: {response.text}")

                           

                    except Exception as e:

                        st.error(f"AI Analysis Failed: {e}")

    else:

        st.warning("Please run a screener search (Tab 2) first to analyze the results.")

st.markdown("---")
st.caption(DISCLAIMERS["global_footer"])
