import streamlit as st
import requests
import os
import pandas as pd

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

st.set_page_config(
    page_title="Stock Screener",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global Dark Theme ────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Root & App ── */
    html, body, [data-testid="stApp"] {
        background-color: #0d0f1a !important;
        font-family: 'Inter', sans-serif;
        color: #e2e8f0 !important;
    }
    .stApp { background-color: #0d0f1a !important; }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #111320 !important;
        border-right: 1px solid #1e2235 !important;
        min-width: 220px !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
    [data-testid="stSidebarNav"] { display: none; }

    /* ── Global text ── */
    p, label, .stMarkdown, .stText,
    [data-testid="stMarkdownContainer"] p {
        color: #cbd5e1 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Specific span overrides only where needed */
    .logo-text span, .nav-item span, .nav-title span {
        font-family: 'Inter', sans-serif !important;
    }
    
    h1, h2, h3, h4, h5, h6 { color: #f1f5f9 !important; }

    /* ── Nav items in sidebar ── */
    .nav-title {
        color: #94a3b8 !important;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        padding: 0 0.75rem;
        margin-bottom: 0.5rem;
    }
    .nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.55rem 0.75rem;
        border-radius: 8px;
        margin: 2px 0.5rem;
        cursor: pointer;
        font-size: 0.93rem;
        font-weight: 500;
        color: #94a3b8 !important;
        transition: background 0.18s, color 0.18s;
        text-decoration: none;
    }
    .nav-item:hover { background: #1e2235; color: #e2e8f0 !important; }
    .nav-item.active {
        background: rgba(139,92,246,0.18);
        color: #a78bfa !important;
        font-weight: 600;
    }
    .nav-item .dot {
        width: 8px; height: 8px; border-radius: 50%;
        display: inline-block; flex-shrink: 0;
    }

    /* ── Logout button ── */
    .logout-btn-wrapper .stButton button {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 0.6rem 1rem !important;
        font-size: 0.9rem !important;
        transition: all 0.2s !important;
    }
    .logout-btn-wrapper .stButton button:hover {
        background: linear-gradient(135deg, #6d28d9, #5b21b6) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(124,58,237,0.4) !important;
    }

    /* ── Header (logo) ── */
    .app-header {
        text-align: center;
        padding: 1.8rem 1rem 1.4rem;
        margin-bottom: 1.8rem;
    }
    .app-header .logo-text {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .app-header .logo-text .brand-stock { color: #a78bfa; }
    .app-header .logo-text .brand-screener { color: #f1f5f9; }
    .app-header .logo-bolt { font-size: 2.2rem; margin-right: 4px; }
    .app-header .subtitle {
        color: #7c6fcd !important;
        font-size: 0.95rem;
        margin-top: 0.4rem;
        font-weight: 400;
    }

    /* ── Section titles ── */
    .section-title {
        font-size: 1.55rem;
        font-weight: 700;
        color: #f1f5f9 !important;
        margin-bottom: 0.3rem;
    }

    /* ── Cards / Metrics ── */
    div[data-testid="stMetric"] {
        background: #161826 !important;
        border: 1px solid #1e2235 !important;
        border-radius: 12px !important;
        padding: 1.2rem 1.4rem !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.35) !important;
        border-color: #7c3aed !important;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    div[data-testid="stMetricValue"] > div { color: #f1f5f9 !important; font-weight: 700 !important; }

    /* ── Buttons ── */
    .stButton button {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.65rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s !important;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #6d28d9, #5b21b6) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(109,40,217,0.45) !important;
    }

    /* ── Text inputs ── */
    .stTextInput input, .stTextInput textarea,
    div[data-baseweb="input"] input {
        background: #1a1d2e !important;
        border: 1px solid #2a2f45 !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.75rem !important;
    }
    .stTextInput input:focus, div[data-baseweb="input"] input:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 2px rgba(124,58,237,0.25) !important;
        outline: none !important;
    }
    .stTextInput input::placeholder { color: #475569 !important; }

    /* ── Number input ── */
    div[data-baseweb="input"] {
        background: #1a1d2e !important;
        border-radius: 10px !important;
        border: 1px solid #2a2f45 !important;
    }

    /* ── Selectbox ── */
    div[data-baseweb="select"] > div {
        background: #1a1d2e !important;
        border: 1px solid #2a2f45 !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }
    [data-baseweb="popover"] { background: #1a1d2e !important; }
    [data-baseweb="menu"] { background: #1a1d2e !important; }

    /* ── DataFrames / Tables ── */
    div[data-testid="stDataFrame"],
    div[data-testid="stDataEditor"] {
        border: 1px solid #1e2235 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #161826 !important;
    }

    /* Glide-data-grid: canvas wrapper & scrollers */
    .dvn-scroller,
    .dvn-style,
    [class*="dark-table-wrap"] {
        background: #161826 !important;
        color: #e2e8f0 !important;
    }

    /* Force ALL text inside the dataframe wrapper to be light */
    div[data-testid="stDataFrame"] *,
    div[data-testid="stDataEditor"] * {
        color: #e2e8f0 !important;
    }

    /* Header row */
    div[data-testid="stDataFrame"] [role="columnheader"],
    div[data-testid="stDataEditor"] [role="columnheader"] {
        background: #1e2235 !important;
        color: #a78bfa !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #2a2f45 !important;
    }

    /* Data cells */
    div[data-testid="stDataFrame"] [role="gridcell"],
    div[data-testid="stDataEditor"] [role="gridcell"] {
        background: #161826 !important;
        color: #e2e8f0 !important;
        border-color: #1e2235 !important;
    }

    /* Alternating row highlight */
    div[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"],
    div[data-testid="stDataEditor"] [role="row"]:nth-child(even) [role="gridcell"] {
        background: #1a1d2e !important;
    }

    /* Fix Streamlit's internal --text-color CSS variable for the grid canvas */
    div[data-testid="stDataFrame"] canvas,
    div[data-testid="stDataEditor"] canvas {
        color-scheme: dark !important;
    }

    /* ── Expander ── */
    details[data-testid="stExpander"] {
        background: #161826 !important;
        border: 1px solid #1e2235 !important;
        border-radius: 10px !important;
    }
    details[data-testid="stExpander"] summary {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    /* Hide the default caret icon to prevent overlay with custom emojis */
    details[data-testid="stExpander"] summary svg,
    details[data-testid="stExpander"] summary [data-testid="stIcon"] {
        display: none !important;
    }

    /* ── Divider ── */
    hr { border-color: #1e2235 !important; }

    /* ── Alerts (streamlit) ── */
    div[data-testid="stAlert"] { border-radius: 10px !important; }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: #7c3aed !important; }

    /* ── Checkbox ── */
    [data-testid="stCheckbox"] label { color: #cbd5e1 !important; }

    /* ── Tab styling (auth page) ── */
    .auth-tabs { display: flex; gap: 0; margin-bottom: 1.2rem; border-bottom: 2px solid #1e2235; }
    .auth-tab-btn {
        background: transparent;
        border: none;
        color: #64748b;
        font-size: 0.95rem;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        cursor: pointer;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        transition: all 0.2s;
    }
    .auth-tab-btn.active { color: #e2e8f0; border-bottom-color: #7c3aed; }

    /* ── Login card ── */
    .login-card {
        background: #161826;
        border: 1px solid #1e2235;
        border-radius: 16px;
        padding: 2rem 2.2rem;
        max-width: 500px;
        margin: 0 auto;
    }

    /* ── Disclaimer ── */
    .disclaimer-box {
        background: linear-gradient(to right, #1a1207, #1a0a0a);
        padding: 16px 20px;
        border-radius: 10px;
        border-left: 4px solid #d97706;
        color: #92400e;
        font-size: 0.82em;
        margin-top: 60px;
    }

    /* ── Data Editor ── */
    div[data-testid="stDataEditor"] {
        border: 1px solid #1e2235 !important;
        border-radius: 10px !important;
        background: #161826 !important;
    }

    /* ── Custom HTML table (replaces canvas dataframe) ── */
    .dark-table-wrap {
        overflow-x: auto;
        border-radius: 10px;
        border: 1px solid #1e2235;
        margin-bottom: 1rem;
    }
    .dark-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        background: #161826;
    }
    .dark-table thead tr {
        background: #1e2235;
    }
    .dark-table th {
        color: #a78bfa;
        font-weight: 600;
        padding: 10px 14px;
        text-align: left;
        border-bottom: 1px solid #2a2f45;
        white-space: nowrap;
        letter-spacing: 0.03em;
    }
    .dark-table td {
        color: #e2e8f0;
        padding: 9px 14px;
        border-bottom: 1px solid #1e2235;
        white-space: nowrap;
    }
    .dark-table tbody tr:last-child td { border-bottom: none; }
    .dark-table tbody tr:nth-child(even) { background: #1a1d2e; }
    .dark-table tbody tr:hover { background: #1e2040; }

    /* hide default Streamlit hamburger / footer */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'triggered_notifications' not in st.session_state:
    st.session_state.triggered_notifications = []
if 'active_page' not in st.session_state:
    st.session_state.active_page = "Dashboard"
if 'auth_tab' not in st.session_state:
    st.session_state.auth_tab = "Login"
if 'screener_results' not in st.session_state:
    st.session_state.screener_results = None
if 'screener_query' not in st.session_state:
    st.session_state.screener_query = ""

# ─── HTML Table Renderer (bypasses canvas-based dataframe) ────────────────────
def render_table(df: pd.DataFrame):
    """Render a DataFrame as a styled HTML table — always visible on dark bg."""
    if df is None or df.empty:
        st.info("No data to display.")
        return
    headers = "".join(f"<th>{col}</th>" for col in df.columns)
    rows = ""
    for _, row in df.iterrows():
        cells = "".join(f"<td>{val}</td>" for val in row)
        rows += f"<tr>{cells}</tr>"
    html = f"""
    <div class="dark-table-wrap">
      <table class="dark-table">
        <thead><tr>{headers}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ─── API helpers ───────────────────────────────────────────────────────────────
def login_user(email, password):
    try:
        response = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data['token']
            st.session_state.user_email = data['email']
            return True, "Login successful!"
        else:
            try:
                return False, response.json().get('detail', 'Login failed')
            except:
                return False, f"Login failed with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please make sure the backend is running."
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def signup_user(email, password):
    try:
        response = requests.post(f"{API_URL}/auth/signup", json={"email": email, "password": password})
        if response.status_code == 200:
            return True, "Account created successfully! Please login to continue."
        else:
            try:
                return False, response.json().get('detail', 'Signup failed')
            except:
                return False, f"Signup failed with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please make sure the backend is running."
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def logout_user():
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user_email = None
    st.session_state.active_page = "Dashboard"


def run_screener(query):
    if not query or not query.strip():
        return False, "Please enter a valid search query"
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        with st.spinner("🤖 Analyzing your query and scanning the market..."):
            response = requests.post(f"{API_URL}/ai/screener",
                                     params={"query": query.strip()},
                                     headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, dict):
                return False, "Received invalid data format from server"
            if 'results' not in data:
                return False, "Response missing 'results' key"
            return True, data
        elif response.status_code == 401:
            st.session_state.authenticated = False
            return False, "Session expired. Please login again."
        else:
            try:
                return False, response.json().get('detail', f'Backend error ({response.status_code})')
            except:
                return False, f"Backend error (status {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "Query timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server."
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def check_backend_connection():
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

# ─── Shared header ─────────────────────────────────────────────────────────────
def render_header(subtitle="Professional AI-Powered Market Analytics"):
    st.markdown(f"""
    <div class="app-header">
        <div class="logo-text">
            <span class="logo-bolt">⚡</span>
            <span class="brand-stock">Stock</span><span class="brand-screener">Screener</span>
        </div>
        <p class="subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

# ─── Backend check ─────────────────────────────────────────────────────────────
if not check_backend_connection():
    render_header()
    st.error("⚠️ Backend server is not running!")
    st.info("Please start the FastAPI backend server:")
    st.code("uvicorn backend.api.main:app --host 127.0.0.1 --port 8001 --reload")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
#  AUTH PAGE
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    render_header()

    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_mid:
        # Tab switcher (Login / Sign Up)
        tab_col1, tab_col2, _ = st.columns([1, 1, 2])
        with tab_col1:
            if st.button("🔒 Login",
                         use_container_width=True,
                         key="tab_login",
                         type="primary" if st.session_state.auth_tab == "Login" else "secondary"):
                st.session_state.auth_tab = "Login"
                st.rerun()
        with tab_col2:
            if st.button("🖊 Sign Up",
                         use_container_width=True,
                         key="tab_signup",
                         type="primary" if st.session_state.auth_tab == "Sign Up" else "secondary"):
                st.session_state.auth_tab = "Sign Up"
                st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.session_state.auth_tab == "Login":
            with st.form("login_form"):
                email    = st.text_input("Email",    placeholder="admin@example.com")
                password = st.text_input("Password", placeholder="••••••••", type="password")
                submit   = st.form_submit_button("🚀 Login", use_container_width=True)
                if submit:
                    if email and password:
                        success, message = login_user(email, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter both email and password")
        else:
            with st.form("signup_form"):
                email    = st.text_input("Email",      placeholder="you@example.com",   key="se")
                password = st.text_input("Password",   placeholder="Min 6 characters",  key="sp", type="password")
                submit   = st.form_submit_button("🚀 Create Account", use_container_width=True)
                if submit:
                    if email and password:
                        if len(password) < 6:
                            st.error("Password must be at least 6 characters.")
                        elif '@' not in email:
                            st.error("Please enter a valid email address.")
                        else:
                            success, message = signup_user(email.strip(), password)
                            if success:
                                st.success(message)
                                st.info("You can now switch to the Login tab to access your account.")
                            else:
                                st.error(message)
                    else:
                        st.error("Please fill in all fields.")

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP (authenticated)
# ═══════════════════════════════════════════════════════════════════════════════
else:
    # ── Left Sidebar Navigation ───────────────────────────────────────────────
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="padding: 0.5rem 0.75rem 1.5rem; display:flex; align-items:center; gap:8px;">
            <span style="font-size:1.4rem;">⚡</span>
            <span style="font-size:1.1rem; font-weight:800; color:#a78bfa;">Stock</span><span style="font-size:1.1rem; font-weight:800; color:#f1f5f9;">Screener</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<p class="nav-title">Navigation</p>', unsafe_allow_html=True)

        pages = [
            ("Dashboard",  "📊", "#ef4444"),   # red dot
            ("Screener",   "🔍", "#f97316"),   # orange dot
            ("Portfolio",  "💼", "#22c55e"),   # green dot
            ("Alerts",    "📋", "#eab308"),   # yellow dot
        ]

        for page_name, icon, dot_color in pages:
            is_active = st.session_state.active_page == page_name
            active_cls = "active" if is_active else ""
            # We use a button per nav item for interactivity
            if st.button(
                f"{icon}  {page_name}",
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.active_page = page_name
                st.rerun()

        # ── Notifications Area ──
        note_count = len(st.session_state.triggered_notifications)
        badge_html = f'<span style="background:#ef4444; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; margin-left:8px;">{note_count}</span>' if note_count > 0 else ""
        st.markdown(f'<p class="nav-title" style="margin-top:1.5rem; display:flex; align-items:center;">🔔 Alert Notifications {badge_html}</p>', unsafe_allow_html=True)
        if not st.session_state.triggered_notifications:
            st.info("No recent alerts.")
        else:
            if st.button("🗑️ Clear All", key="clear_notifications", use_container_width=True):
                st.session_state.triggered_notifications = []
                st.rerun()
            
            for note in st.session_state.triggered_notifications[::-1]:
                with st.container(border=True):
                    st.markdown(f"**{note['symbol']}**")
                    st.markdown(f"<small>{note['metric']} {note['operator']} {note['threshold']}</small>", unsafe_allow_html=True)
                    st.markdown(f"<small style='color:#94a3b8;'>Value: {note['value']:.2f}</small>", unsafe_allow_html=True)

        st.markdown("<hr style='margin:1.5rem 0.5rem;border-color:#1e2235;'>", unsafe_allow_html=True)

        # Logout
        st.markdown('<div class="logout-btn-wrapper">', unsafe_allow_html=True)
        if st.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
            logout_user()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Automated Alert Poller (Every 10 seconds) ──────────────────────────
    if hasattr(st, "fragment"):
        @st.fragment(run_every=10)
        def alert_poller_fragment():
            if st.session_state.get('authenticated') and st.session_state.get('token'):
                try:
                    h = {"Authorization": f"Bearer {st.session_state.token}"}
                    # Silent poll
                    res = requests.get(f"{API_URL}/alerts/poll", headers=h)
                    if res.status_code == 200:
                        trig = res.json().get('triggered_alerts', [])
                        for a in trig:
                            # Track unique triggers in this session to avoid double-toasting
                            # Note: the 15-min cooldown is handled by the server, but we still
                            # check locally to be safe.
                            already_shown = any(n.get('alert_id') == a.get('alert_id') for n in st.session_state.triggered_notifications)
                            
                            if not already_shown:
                                st.session_state.triggered_notifications.append(a)
                                st.toast(f"🔔 **{a['symbol']}** Alert: {a['metric']} {a['operator']} {a['threshold']} (Now: {a['value']:.2f})", icon="🔔")
                except:
                    pass
        alert_poller_fragment()
    else:
        # Fallback if fragment is not available (older streamlit)
        # We can't do a smooth 5s check easily without fragment or custom components
        pass

    # ── Page: Dashboard ───────────────────────────────────────────────────────
    if st.session_state.active_page == "Dashboard":
        render_header()

        st.markdown('<p class="section-title">📊 Market Overview</p>', unsafe_allow_html=True)

        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            resp = requests.get(f"{API_URL}/stocks/overview", headers=headers, timeout=10)
            if resp.status_code == 200:
                overview = resp.json()
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Stocks Seeded", overview.get("total_stocks", "—"))
                with col2:
                    avg_pe = overview.get("avg_pe_ratio", 0)
                    st.metric("Avg PE Ratio", f"{avg_pe:.2f}" if avg_pe else "—")
                with col3:
                    avg_mc = overview.get("avg_market_cap", 0)
                    if avg_mc:
                        if avg_mc >= 1e12:
                            mc_str = f"₹{avg_mc/1e12:.1f}T"
                        elif avg_mc >= 1e9:
                            mc_str = f"₹{avg_mc/1e9:.1f}B"
                        else:
                            mc_str = f"₹{avg_mc:,.0f}"
                    else:
                        mc_str = "—"
                    st.metric("Avg Market Cap", mc_str)
                with col4:
                    st.metric("Active Sectors", overview.get("active_sectors", "—"))
            else:
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Total Stocks", "—")
                with c2: st.metric("Avg PE Ratio", "—")
                with c3: st.metric("Avg Market Cap", "—")
                with c4: st.metric("Active Sectors", "—")
        except Exception:
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Stocks", "—")
            with c2: st.metric("Avg PE Ratio", "—")
            with c3: st.metric("Avg Market Cap", "—")
            with c4: st.metric("Active Sectors", "—")

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<p class="section-title">🏆 Top Companies</p>', unsafe_allow_html=True)

        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            resp = requests.get(f"{API_URL}/stocks/top", headers=headers, timeout=10)
            if resp.status_code == 200:
                top_stocks = resp.json()
                if top_stocks:
                    df_top = pd.DataFrame(top_stocks)
                    render_table(df_top)
                else:
                    st.info("No top-company data available.")
            else:
                st.info("Could not load top companies — if this endpoint doesn't exist, please check the backend.")
        except Exception as e:
            st.info(f"Top companies data unavailable — {e}")

    # ── Page: Screener ─────────────────────────────────────────────────────────
    elif st.session_state.active_page == "Screener":
        render_header()

        st.markdown('<p class="section-title">🔍 AI-Powered Screener</p>', unsafe_allow_html=True)
        st.markdown("<p style='color:#94a3b8;margin-bottom:1rem;'>Ask anything in natural language. The system will parse your request into a logic-based query and fetch real-time data if needed.</p>", unsafe_allow_html=True)

        query = st.text_input(
            "Screening query",
            placeholder="e.g., Price of RELIANCE OR PE below 30 and ROE above 15",
            label_visibility="collapsed",
        )

        col_btn, col_chk = st.columns([1, 1])
        with col_btn:
            run_btn = st.button("🚀 Execute AI Query", use_container_width=True)
        with col_chk:
            show_dsl = st.checkbox("Show Parsing Logic (DSL)", value=True)

        if run_btn and query:
            success, result = run_screener(query)
            if success:
                st.session_state.screener_results = result
                st.session_state.screener_query = query
            else:
                st.error(result)
                st.session_state.screener_results = None

        if st.session_state.screener_results:
            result = st.session_state.screener_results
            result_count = len(result['results'])
            st.success(f"Found **{result_count}** stocks matching your criteria for: *{st.session_state.get('screener_query', '')}*")

            if result_count > 0:
                if show_dsl and result.get("dsl"):
                    with st.expander("📐 Parsed DSL Logic"):
                        st.json(result["dsl"])

                    st.subheader(f"Results ({result_count})")
                    df = pd.DataFrame(result["results"])
                    essential_columns = ['symbol', 'company_name', 'current_price', 'pe_ratio', 'market_cap', 'roe', 'debt_equity', 'dividend_yield']
                    available_columns = [c for c in essential_columns if c in df.columns]
                    df_display = df[available_columns] if available_columns else df
                    column_mapping = {
                        'symbol': 'Symbol', 'company_name': 'Company',
                        'pe_ratio': 'P/E', 'market_cap': 'Market Cap',
                        'current_price': 'Price', 'roe': 'ROE (%)',
                        'debt_equity': 'Debt/Equity', 'dividend_yield': 'Div. Yield (%)'
                    }
                    df_display = df_display.rename(columns={k: v for k, v in column_mapping.items() if k in df_display.columns})
                    if 'P/E' in df_display.columns:
                        df_display['P/E'] = df_display['P/E'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) and x > 0 else "N/A")
                    if 'Market Cap' in df_display.columns:
                        df_display['Market Cap'] = df_display['Market Cap'].apply(lambda x: f"₹{x/1e9:.1f}B" if pd.notnull(x) and x > 0 else "N/A")
                    if 'Price' in df_display.columns:
                        df_display['Price'] = df_display['Price'].apply(lambda x: f"₹{x:.2f}" if pd.notnull(x) and x > 0 else "N/A")
                    if 'ROE (%)' in df_display.columns:
                        df_display['ROE (%)'] = df_display['ROE (%)'].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) and x != 0 else "N/A")
                    if 'Debt/Equity' in df_display.columns:
                        df_display['Debt/Equity'] = df_display['Debt/Equity'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) and x != 0 else "N/A")
                    if 'Div. Yield (%)' in df_display.columns:
                        df_display['Div. Yield (%)'] = df_display['Div. Yield (%)'].apply(lambda x: f"{x*100:.2f}%" if pd.notnull(x) and x != 0 else "N/A")
                    render_table(df_display)

                    # ── Selection & Add to Portfolio (Implementation Plan) ────
                    st.markdown("---")
                    st.markdown('<p style="font-weight:600; font-size:1.1rem; color:#f1f5f9;">➕ Add Stocks to Portfolio</p>', unsafe_allow_html=True)
                    
                    # Create labels for multiselect
                    options = [f"{r['symbol']} - {r['company_name']}" for _, r in df.iterrows()]
                    selected_stock_labels = st.multiselect(
                        "Select one or more stocks from above",
                        options=options,
                        placeholder="Search or select stocks..."
                    )

                    if selected_stock_labels:
                        if st.button("📁 Create / Add to Portfolio", use_container_width=True):
                            st.session_state.show_add_to_port_form = True

                        if st.session_state.get('show_add_to_port_form'):
                            with st.expander("Portfolio Details", expanded=True):
                                with st.form("add_to_portfolio_form"):
                                    # Fetch existing portfolios
                                    header_auth = {"Authorization": f"Bearer {st.session_state.token}"}
                                    port_resp = requests.get(f"{API_URL}/portfolio/", headers=header_auth)
                                    portfolios = port_resp.json() if port_resp.status_code == 200 else []
                                    
                                    port_names = ["-- Create New Portfolio --"] + [p['name'] for p in portfolios]
                                    selected_port_name = st.selectbox("Select Portfolio", port_names)
                                    
                                    new_port_name = ""
                                    if selected_port_name == "-- Create New Portfolio --":
                                        new_port_name = st.text_input("New Portfolio Name", placeholder="e.g. My Watchlist")
                                    
                                    person_name = st.text_input("Owner Name", placeholder="e.g. John Doe")
                                    
                                    col_qty, col_prc = st.columns(2)
                                    with col_qty:
                                        qty = st.number_input("Quantity", min_value=0.0, step=1.0, value=1.0)
                                    with col_prc:
                                        # Default price from first selected stock
                                        default_price = 0.0
                                        if selected_stock_labels:
                                            first_sym = selected_stock_labels[0].split(" - ")[0]
                                            s_match = df[df['symbol'] == first_sym]
                                            if not s_match.empty:
                                                default_price = float(s_match.iloc[0].get('current_price', 0))
                                        avg_price = st.number_input("Average Buy Price (₹)", min_value=0.0, step=0.1, value=default_price)

                                    submit_add = st.form_submit_button("🚀 Confirm Addition")
                                    
                                    if submit_add:
                                        target_port_id = None
                                        
                                        if selected_port_name == "-- Create New Portfolio --":
                                            if not new_port_name.strip():
                                                st.error("Please enter a name for the new portfolio")
                                            else:
                                                c_resp = requests.post(f"{API_URL}/portfolio/", 
                                                                    json={"name": new_port_name.strip(), "person_name": person_name.strip()}, 
                                                                    headers=header_auth)
                                                if c_resp.status_code == 200:
                                                    target_port_id = c_resp.json().get('portfolio_id')
                                                else:
                                                    st.error(c_resp.json().get('detail', 'Failed to create portfolio'))
                                        else:
                                            target_port_id = next((p['portfolio_id'] for p in portfolios if p['name'] == selected_port_name), None)

                                        if target_port_id:
                                            success_count = 0
                                            for label in selected_stock_labels:
                                                sym = label.split(" - ")[0]
                                                target_stock = df[df['symbol'] == sym].iloc[0]
                                                
                                                hold_payload = {
                                                    "stock_id": int(target_stock['stock_id']),
                                                    "quantity": float(qty),
                                                    "avg_price": float(avg_price)
                                                }
                                                a_resp = requests.post(f"{API_URL}/portfolio/{target_port_id}/holdings", 
                                                                       json=hold_payload, headers=header_auth)
                                                if a_resp.status_code == 200:
                                                    success_count += 1
                                            
                                            if success_count > 0:
                                                st.success(f"Successfully added {success_count} stock(s) to Active Holdings!")
                                                st.session_state.show_add_to_port_form = False
                                                st.rerun()
                                            else:
                                                st.error("Failed to add stocks to holdings.")

                    if result.get("has_quarterly", False) and result.get("quarterly_data"):
                        st.subheader("📊 Quarterly Financial Data")
                        quarterly_data = result["quarterly_data"]
                        if quarterly_data and isinstance(quarterly_data, dict):
                            symbols_with_data = []
                            for stock_id, quarters in quarterly_data.items():
                                if quarters and isinstance(quarters, list) and len(quarters) > 0:
                                    if 'symbol' in quarters[0]:
                                        symbols_with_data.append(quarters[0]['symbol'])
                            if symbols_with_data:
                                if len(symbols_with_data) <= 5:
                                    tabs = st.tabs(symbols_with_data)
                                    for i, symbol in enumerate(symbols_with_data):
                                        with tabs[i]:
                                            symbol_quarters = None
                                            for stock_id, quarters in quarterly_data.items():
                                                if quarters and len(quarters) > 0 and quarters[0].get('symbol') == symbol:
                                                    symbol_quarters = quarters; break
                                            if symbol_quarters:
                                                try:
                                                    qdf = pd.DataFrame(symbol_quarters)
                                                    req_cols = ['quarter', 'year', 'revenue', 'ebitda', 'net_profit']
                                                    avail = [c for c in req_cols if c in qdf.columns]
                                                    if avail:
                                                        qdf = qdf[avail]
                                                        for col in ['revenue', 'ebitda', 'net_profit']:
                                                            if col in qdf.columns:
                                                                qdf[col] = qdf[col].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) and x != 0 else "N/A")
                                                        qdf = qdf.rename(columns={'quarter':'Quarter','year':'Year','revenue':'Revenue','ebitda':'EBITDA','net_profit':'Net Profit'})
                                                        st.dataframe(qdf, use_container_width=True)
                                                except Exception as e:
                                                    st.error(f"Error: {e}")
                                else:
                                    for stock_id, quarters in quarterly_data.items():
                                        if quarters:
                                            symbol = quarters[0].get('symbol', f'Stock {stock_id}')
                                            with st.expander(f"📈 {symbol}"):
                                                try:
                                                    qdf = pd.DataFrame(quarters)
                                                    req_cols = ['quarter', 'year', 'revenue', 'ebitda', 'net_profit']
                                                    avail = [c for c in req_cols if c in qdf.columns]
                                                    if avail:
                                                        qdf = qdf[avail]
                                                        qdf = qdf.rename(columns={'quarter':'Quarter','year':'Year','revenue':'Revenue','ebitda':'EBITDA','net_profit':'Net Profit'})
                                                        st.dataframe(qdf, use_container_width=True)
                                                except Exception as e:
                                                    st.error(f"Error: {e}")
                else:
                    st.info("No stocks matched your criteria.")
            else:
                st.error(f"❌ {result}")
                if "Session expired" in result:
                    st.rerun()

    # ── Page: Portfolio ────────────────────────────────────────────────────────
    elif st.session_state.active_page == "Portfolio":
        render_header()
        st.markdown('<p class="section-title">💼 Portfolio Management</p>', unsafe_allow_html=True)

        def get_portfolios():
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.get(f"{API_URL}/portfolio/", headers=headers)
                return (True, r.json()) if r.status_code == 200 else (False, "Failed to fetch portfolios")
            except Exception as e:
                return False, f"Error: {e}"

        def get_portfolio_holdings(portfolio_id):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.get(f"{API_URL}/portfolio/{portfolio_id}/holdings", headers=headers)
                return (True, r.json()) if r.status_code == 200 else (False, "Failed to fetch holdings")
            except Exception as e:
                return False, f"Error: {e}"

        def create_portfolio(name):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.post(f"{API_URL}/portfolio/", json={"name": name}, headers=headers)
                return (True, "Portfolio created successfully") if r.status_code == 200 else (False, "Failed to create portfolio")
            except Exception as e:
                return False, f"Error: {e}"

        def get_portfolio_summary():
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.get(f"{API_URL}/portfolio/summary", headers=headers)
                return (True, r.json()) if r.status_code == 200 else (False, "Failed to fetch summary")
            except Exception as e:
                return False, f"Error: {e}"

        success, summary = get_portfolio_summary()
        if success:
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total Portfolios", summary.get('total_portfolios', 0))
            with col2: st.metric("Total Holdings", summary.get('total_holdings', 0))
            with col3:
                invested = summary.get('total_invested', 0)
                st.metric("Total Invested", f"₹{invested:,.2f}" if invested else "₹0.00")
            with col4:
                cv = summary.get('current_value', 0)
                st.metric("Current Value", f"₹{cv:,.2f}" if cv else "₹0.00")
            invested = summary.get('total_invested', 0)
            if invested > 0:
                gl = summary.get('total_gain_loss', 0)
                glp = summary.get('gain_loss_percent', 0)
                if gl != 0:
                    st.metric("Total Gain/Loss", f"₹{gl:+,.2f} ({glp:+.1f}%)", delta=f"{glp:+.1f}%")

        st.divider()
        with st.expander("➕ Create New Portfolio"):
            with st.form("create_portfolio"):
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    portfolio_name = st.text_input("Portfolio Name")
                with p_col2:
                    person_name = st.text_input("Owner/Person Name", placeholder="Optional")
                
                if st.form_submit_button("Create Portfolio"):
                    if portfolio_name.strip():
                        # Updated to handle person_name
                        try:
                            headers = {"Authorization": f"Bearer {st.session_state.token}"}
                            r = requests.post(f"{API_URL}/portfolio/", 
                                            json={"name": portfolio_name.strip(), "person_name": person_name.strip()}, 
                                            headers=headers)
                            if r.status_code == 200:
                                st.success("Portfolio created successfully"); st.rerun()
                            else:
                                st.error(r.json().get('detail', "Failed to create portfolio"))
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.error("Please enter a portfolio name")

        success, portfolios = get_portfolios()
        if success and portfolios:
            st.subheader("Your Portfolios")
            for portfolio in portfolios:
                disp_name = f"📁 {portfolio['name']}"
                if portfolio.get('person_name'):
                    disp_name += f" ({portfolio['person_name']})"
                
                with st.expander(f"{disp_name} — {portfolio['total_holdings']} holdings"):
                    hs, holdings = get_portfolio_holdings(portfolio['portfolio_id'])
                    if hs and holdings:
                        hdf = pd.DataFrame(holdings)
                        disp_cols = ['symbol','company_name','quantity','avg_price','current_price','total_value','gain_loss','gain_loss_percent']
                        avail = [c for c in disp_cols if c in hdf.columns]
                        if avail:
                            hd = hdf[avail].copy()
                            hd = hd.rename(columns={'symbol':'Symbol','company_name':'Company','quantity':'Qty','avg_price':'Avg Price','current_price':'Current Price','total_value':'Total Value','gain_loss':'Gain/Loss','gain_loss_percent':'Gain/Loss %'})
                            for col in ['Avg Price','Current Price']:
                                if col in hd.columns: hd[col] = hd[col].apply(lambda x: f"₹{x:.2f}" if pd.notnull(x) else "N/A")
                            if 'Total Value' in hd.columns: hd['Total Value'] = hd['Total Value'].apply(lambda x: f"₹{x:,.2f}" if pd.notnull(x) else "N/A")
                            if 'Gain/Loss' in hd.columns: hd['Gain/Loss'] = hd['Gain/Loss'].apply(lambda x: f"₹{x:+,.2f}" if pd.notnull(x) else "N/A")
                            if 'Gain/Loss %' in hd.columns: hd['Gain/Loss %'] = hd['Gain/Loss %'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "N/A")
                            render_table(hd)
                        else:
                            st.info("No holdings data available")
                    else:
                        st.info("No active holdings in this portfolio yet.")

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Delete Entire Portfolio", key=f"del_port_{portfolio['portfolio_id']}", type="secondary"):
                        delete_portfolio(portfolio['portfolio_id'])
                        st.rerun()
        else:
            st.info("No portfolios found. Create your first portfolio above!")

    # ── Page: Alerts ─────────────────────────────────────────────────
    elif st.session_state.active_page == "Alerts":
        render_header()
        st.markdown('<p class="section-title">🔔 Price Alert Management</p>', unsafe_allow_html=True)

        def get_alerts():
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.get(f"{API_URL}/alerts/", headers=headers)
                return (True, r.json()) if r.status_code == 200 else (False, "Failed to fetch alerts")
            except Exception as e:
                return False, f"Error: {e}"

        def get_alert_events():
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.get(f"{API_URL}/alerts/events", headers=headers)
                return (True, r.json()) if r.status_code == 200 else (False, "Failed to fetch events")
            except Exception as e:
                return False, f"Error: {e}"

        def get_alert_summary():
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.get(f"{API_URL}/alerts/summary", headers=headers)
                return (True, r.json()) if r.status_code == 200 else (False, "Failed to fetch summary")
            except Exception as e:
                return False, f"Error: {e}"

        def create_alert(stock_id, portfolio_id, metric, operator, threshold):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.post(f"{API_URL}/alerts/", json={"stock_id": stock_id, "portfolio_id": portfolio_id, "metric": metric, "operator": operator, "threshold": threshold}, headers=headers)
                if r.status_code == 200: return True, "Alert created successfully"
                return False, r.json().get('detail', 'Failed to create alert')
            except Exception as e:
                return False, f"Error: {e}"

        def delete_alert(alert_id):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.delete(f"{API_URL}/alerts/{alert_id}", headers=headers)
                return (True, "Alert deleted") if r.status_code == 200 else (False, "Failed to delete")
            except Exception as e:
                return False, f"Error: {e}"

        def toggle_alert(alert_id):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.patch(f"{API_URL}/alerts/{alert_id}/toggle", headers=headers)
                return (True, r.json()) if r.status_code == 200 else (False, "Failed to toggle")
            except Exception as e:
                return False, f"Error: {e}"

        def get_portfolios():
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                r = requests.get(f"{API_URL}/portfolio/", headers=headers)
                return (True, r.json()) if r.status_code == 200 else (False, [])
            except:
                return False, []

        ok_sum, summary = get_alert_summary()
        if ok_sum:
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Alerts", summary.get('total_alerts', 0))
            with c2: st.metric("Active Alerts", summary.get('active_alerts', 0))
            with c3: st.metric("Total Triggers", summary.get('total_triggers', 0))
            with c4: st.metric("Stocks Monitored", summary.get('stocks_monitored', 0))

        st.divider()

        with st.expander("➕ Create New Alert"):
            st.write("Set up alerts to monitor your portfolio stocks")
            with st.form("create_alert"):
                ac1, ac2 = st.columns(2)
                with ac1:
                    stock_symbol = st.text_input("Stock Symbol (e.g., AAPL, TCS)", key="alert_stock")
                    metric = st.selectbox("Metric", ["price","pe_ratio","market_cap","eps","roe","dividend_yield"],
                                          format_func=lambda x: x.replace('_', ' ').title())
                with ac2:
                    operator  = st.selectbox("Operator", [">", "<", ">=", "<=", "="])
                    threshold = st.number_input("Threshold Value", min_value=0.0, step=0.01, format="%.2f")

                port_ok, portfolios = get_portfolios()
                if port_ok and portfolios:
                    port_opts = {p['name']: p['portfolio_id'] for p in portfolios}
                    sel_port_name = st.selectbox("Portfolio", list(port_opts.keys()))
                    sel_port_id   = port_opts[sel_port_name]
                else:
                    st.warning("You need to create a portfolio first.")
                    sel_port_id = None

                if st.form_submit_button("Create Alert"):
                    if stock_symbol.strip() and threshold > 0 and sel_port_id:
                        try:
                            headers = {"Authorization": f"Bearer {st.session_state.token}"}
                            r = requests.get(f"{API_URL}/alerts/stocks/search",
                                             params={"symbol": stock_symbol.upper().strip()},
                                             headers=headers)
                            if r.status_code == 200:
                                stock = r.json()
                                ok, msg = create_alert(stock['stock_id'], sel_port_id, metric, operator, threshold)
                                if ok: st.success(msg); st.rerun()
                                else: st.error(msg)
                            else:
                                st.error(f"Stock symbol '{stock_symbol.upper()}' not found")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.error("Please fill in all fields and select a portfolio")

        ok_al, alerts = get_alerts()
        if ok_al and alerts:
            st.subheader("Your Active Alerts")
            
            # Prepare display data
            display_data = []
            for alert in alerts:
                display_data.append({
                    'ID': alert['alert_id'],
                    'Symbol': alert['symbol'],
                    'Company': alert['company_name'],
                    'Metric': alert['metric'].replace('_', ' ').title(),
                    'Op': alert['operator'],
                    'Threshold': f"{alert['threshold']:,.2f}",
                    'Status': '✅ Active' if alert['is_active'] else '❌ Inactive',
                    'Triggers': alert['times_triggered'],
                    'Last Triggered': pd.to_datetime(alert['last_triggered']).strftime('%Y-%m-%d %H:%M') if pd.notnull(alert['last_triggered']) else "Never"
                })
            
            df_alerts = pd.DataFrame(display_data)
            render_table(df_alerts)

            # Management UI (Multiselect based selection)
            st.markdown('<p style="font-weight:600; margin-top:1rem; color:#f1f5f9;">⚙️ Manage Alerts</p>', unsafe_allow_html=True)
            
            # Create selection labels
            alert_map = {f"#{a['ID']} {a['Symbol']} ({a['Metric']})": a['ID'] for a in display_data}
            selected_labels = st.multiselect("Select alerts to modify", options=list(alert_map.keys()))
            
            if selected_labels:
                selected_ids = [alert_map[label] for label in selected_labels]
                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    if st.button("🗑️ Delete Selected", use_container_width=True):
                        cnt = 0
                        for aid in selected_ids:
                            if delete_alert(aid)[0]: cnt += 1
                        st.success(f"Deleted {cnt} alert(s)"); st.rerun()
                with mc2:
                    if st.button("🔔 Activate Selected", use_container_width=True):
                        cnt = 0
                        for aid in selected_ids:
                            al = next((a for a in alerts if a['alert_id'] == aid), None)
                            if al and not al['is_active'] and toggle_alert(aid)[0]: cnt += 1
                        st.success(f"Activated {cnt}"); st.rerun()
                with mc3:
                    if st.button("🔕 Deactivate Selected", use_container_width=True):
                        cnt = 0
                        for aid in selected_ids:
                            al = next((a for a in alerts if a['alert_id'] == aid), None)
                            if al and al['is_active'] and toggle_alert(aid)[0]: cnt += 1
                        st.success(f"Deactivated {cnt}"); st.rerun()
        else:
            st.info("No alerts found. Create your first alert above!")

        st.divider()
        st.subheader("📊 Recent Alert Triggers")
        ok_ev, events = get_alert_events()
        if ok_ev and events:
            edf = pd.DataFrame(events)
            disp_cols = ['symbol','company_name','metric','operator','threshold','triggered_value','triggered_at']
            avail = [c for c in disp_cols if c in edf.columns]
            if avail:
                ed = edf[avail].copy().rename(columns={'symbol':'Symbol','company_name':'Company','metric':'Metric','operator':'Op','threshold':'Threshold','triggered_value':'Actual Value','triggered_at':'Triggered At'})
                if 'Metric' in ed.columns: ed['Metric'] = ed['Metric'].apply(lambda x: x.replace('_',' ').title() if pd.notnull(x) else "N/A")
                for col in ['Threshold','Actual Value']:
                    if col in ed.columns: ed[col] = ed[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "N/A")
                if 'Triggered At' in ed.columns:
                    ed['Triggered At'] = ed['Triggered At'].apply(lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M') if pd.notnull(x) else "N/A")
                render_table(ed)
        else:
            st.info("No alert triggers yet.")

# ─── Footer disclaimer ─────────────────────────────────────────────────────────
st.markdown('<div class="disclaimer-box">⚠️ <strong>Academic Project Disclaimer:</strong> This application is developed for educational purposes. Data presented here is simulated or retrieved from public sources and should not be used for actual financial decision-making.</div>', unsafe_allow_html=True)
