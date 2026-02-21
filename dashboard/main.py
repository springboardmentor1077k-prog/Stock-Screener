import streamlit as st
from services import http
from views import market_explorer, holdings, signals
import os
import base64


st.set_page_config(page_title="QuantDash", layout="wide")

# Build base64 data URL for background image using safe absolute path resolution
_bg_path = os.path.join(os.path.dirname(__file__), "assets", "background.jpeg")
_bg_data_url = ""
if os.path.exists(_bg_path):
    with open(_bg_path, "rb") as _f:
        _bg_b64 = base64.b64encode(_f.read()).decode("utf-8")
    _bg_data_url = "data:image/jpeg;base64," + _bg_b64
_bg_fragment = f", url('{_bg_data_url}')" if _bg_data_url else ""

css = """
<style>
:root {
  --qd-accent: #00897b;
  --qd-amber: #ffb300;
}
.stApp header { background: linear-gradient(90deg, var(--qd-accent), var(--qd-amber)); height: 4px; }
/* Full-page background on .stApp with dark overlay; image injected as base64 */
.stApp {
  background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)) REPLACE_BG;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  background-repeat: no-repeat;
}
div.stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid rgba(255,255,255,0.12); }
div.stTabs [data-baseweb="tab"] { background: transparent !important; border-radius: 0 !important; margin-right: 18px; padding: 6px 0; }
div.stTabs [data-baseweb="tab"] p { margin: 0; padding: 0 6px; color: #ffffff !important; font-weight: 700; letter-spacing: .2px; }
div.stTabs [aria-selected="true"] { border-bottom: 2px solid var(--qd-accent) !important; }
.qd-banner { background: rgba(255,255,255,0.06); padding: 10px 14px; border-left: 4px solid var(--qd-amber); border-radius: 6px; color: #ffffff !important; }
.qd-success { background: #e8f5e9; border-left-color: #2e7d32; }
/* Force Streamlit alert text to white for contrast on dark theme */
.stAlert, .stAlert p, .stAlert div, .stAlert span { color: #ffffff !important; }
/* Success/info/Warning backgrounds remain; only text forced to white */
/* Optional: thin row separators for custom lists */
hr.qd-row-sep { border: 0; height: 1px; background: rgba(255,255,255,0.12); margin: 6px 0 10px; }
</style>
"""
st.markdown(css.replace("REPLACE_BG", _bg_fragment), unsafe_allow_html=True)

for k in ["explorer_result", "holdings_data", "alerts_list", "last_alert_run", "auth"]:
    if k not in st.session_state:
        st.session_state[k] = None
if st.session_state.get("auth") and isinstance(st.session_state["auth"], dict) and st.session_state["auth"].get("token"):
    http.set_token(st.session_state["auth"]["token"])

if not st.session_state.get("auth"):
    st.markdown('<h1 style="color:#ffffff;margin:0 0 4px 0;">AI STOCKLens Screener</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#ffffff;margin-top:0;">Access</h3>', unsafe_allow_html=True)
    st.markdown('<div class="qd-banner">Register a new account, then log in</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Register")
        with st.form("register_form", clear_on_submit=False):
            reg_email = st.text_input("Email", key="reg_email")
            reg_pw = st.text_input("Password", type="password", key="reg_pw")
            reg_pw2 = st.text_input("Confirm Password", type="password", key="reg_pw2")
            reg_submit = st.form_submit_button("Create Account")
        if reg_submit:
            if reg_pw != reg_pw2:
                st.warning("Passwords do not match")
            else:
                try:
                    http.post("/register", {"email": reg_email, "password": reg_pw})
                    st.success("Registration successful. Please log in.")
                except http.NetworkError as e:
                    st.warning(str(e))
    with c2:
        st.subheader("Login")
        with st.form("login_form", clear_on_submit=True):
            login_email = st.text_input("Login Email", key="login_email")
            login_pw = st.text_input("Login Password", type="password", key="login_pw")
            login_submit = st.form_submit_button("Sign In")
        if login_submit:
            try:
                items, _ = http.post("/login", {"email": login_email, "password": login_pw})
                info = items[0] if items else {}
                st.session_state["auth"] = {"email": info.get("email"), "user_id": info.get("user_id"), "token": info.get("token")}
                http.set_token(info.get("token"))
                st.rerun()
            except http.NetworkError as e:
                st.warning(str(e))
else:
    top = st.columns([6, 1])
    with top[1]:
        if st.button("Log out"):
            st.session_state["auth"] = None
            st.session_state["explorer_result"] = None
            st.session_state["holdings_data"] = None
            st.session_state["alerts_list"] = None
            st.session_state["last_alert_run"] = None
            http.set_token(None)
            st.rerun()
    st.markdown('<h1 style="color:#ffffff;margin:0 0 4px 0;">AI STOCKLens Screener</h1>', unsafe_allow_html=True)
    tabs = st.tabs(["Market Explorer", "Holdings", "Signals"])
    with tabs[0]:
        market_explorer.render()
    with tabs[1]:
        holdings.render()
    with tabs[2]:
        signals.render()
