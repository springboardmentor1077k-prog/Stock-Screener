import streamlit as st
import requests
import pandas as pd
import time
import json

# MUST BE FIRST
st.set_page_config(
    page_title="AI Stock Screener",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ---------- CONFIG ----------
API_URL = "http://localhost:8000/api/v1"

# ---------- MODERN STYLES ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Modern Dark Background */
    .stApp {
        background: radial-gradient(circle at top left, #1e1e2f, #0f0f13);
        background-color: #0f0f13;
    }

    /* Glassmorphism Card Style */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }

    /* Custom Inputs */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 8px !important;
        height: 45px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        transition: transform 0.2s;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: scale(1.02);
        background: rgba(255, 255, 255, 0.05);
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        background: transparent;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 10px 20px;
        color: #94a3b8;
        border: none;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(79, 70, 229, 0.2);
        color: #818cf8;
        font-weight: bold;
    }

    /* Headers */
    h1, h2, h3 {
        color: white;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .gradient-text {
        background: linear-gradient(to right, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 15, 19, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "token" not in st.session_state:
    st.session_state.token = None

# ---------- API FUNCTIONS ----------
def login(email, password):
    try:
        response = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": password})
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Invalid credentials")
            return None
    except Exception as e:
        st.error(f"🔌 Connection error: {e}")
        return None

def signup(email, password):
    try:
        response = requests.post(f"{API_URL}/auth/signup", json={"email": email, "password": password})
        if response.status_code == 200:
            st.success("✨ Account created! Please log in.")
            return True
        else:
            st.error(f"Error: {response.text}")
            return False
    except Exception as e:
        st.error(f"🔌 Connection error: {e}")
        return False

def get_screener_results(query, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Parse the query
    parse_response = requests.post(f"{API_URL}/screener/parse", json={"query_text": query}, headers=headers)
    if parse_response.status_code != 200:
        st.error(f"Failed to parse query: {parse_response.text}")
        return [], None
    
    structured_query = parse_response.json()
    
    # Execute search
    search_response = requests.post(f"{API_URL}/screener/search", json=structured_query, headers=headers)
    if search_response.status_code == 200:
        return search_response.json(), structured_query
    else:
        st.error(f"Search failed: {search_response.text}")
        return [], None

def add_to_portfolio(stock_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/portfolio/", json={"stock_id": stock_id}, headers=headers)
    if response.status_code == 200:
        st.success("✅ Added to portfolio!")
    else:
        st.warning(f"Failed to add. {response.text}")

def get_portfolio(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/portfolio/", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch portfolio: {response.text}")
        return []

def get_history(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/screener/history", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# ---------- UI COMPONENTS ----------
def render_header():
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 3rem; margin-bottom: 0;">⚡ <span class="gradient-text">Stock</span>Screener</h1>
            <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 0.5rem;">
                Professional AI-Powered Market Analytics
            </p>
        </div>
    """, unsafe_allow_html=True)

def login_form():
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        email = st.text_input("Email", key="login_email", placeholder="admin@example.com")
        password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Login", key="login_btn"):
            with st.spinner("Authenticating..."):
                token_data = login(email, password)
                if token_data:
                    st.session_state.token = token_data['access_token']
                    st.success("Successfully logged in!")
                    time.sleep(0.5)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def signup_form():
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        email = st.text_input("Email", key="signup_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="signup_password", placeholder="Choose a strong password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Sign Up", key="signup_btn"):
            with st.spinner("Creating account..."):
                signup(email, password)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------- MAIN APP ----------

def main():
    if not st.session_state.token:
        # LOGIN/SIGNUP PAGE
        render_header()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            tab1, tab2 = st.tabs(["🔐 Login", "🆕 Sign Up"])
            with tab1:
                login_form()
            with tab2:
                signup_form()
    
    else:
        # Sidebar Navigation
        with st.sidebar:
            st.markdown("### 🎯 Navigation")
            nav_choice = st.radio("", ["📊 Dashboard", "🔍 Screener", "💼 Portfolio", "📜 History"], label_visibility="collapsed")
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.token = None
                st.rerun()

        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        render_header()

        if nav_choice == "📊 Dashboard":
            st.markdown("### 📊 Market Overview")
            try:
                res = requests.get(f"{API_URL}/screener/stocks-with-fundamentals", headers=headers)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    df = pd.DataFrame(data)

                    if not df.empty:
                        # METRICS ROW
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("Total Stocks Seeded", len(df))
                        with m2:
                            pe_avg = df["pe_ratio"].mean()
                            st.metric("Avg PE Ratio", f"{pe_avg:.2f}" if not pd.isna(pe_avg) else "N/A")
                        with m3:
                            mc_avg = df["market_cap"].mean()
                            st.metric("Avg Market Cap", f"₹{mc_avg / 1e12:.1f}T" if not pd.isna(mc_avg) else "N/A")
                        with m4:
                            st.metric("Active Sectors", df['sector'].nunique())

                        st.markdown("<br>", unsafe_allow_html=True)

                        # Top Companies Table
                        st.markdown("#### 🏆 Top Companies")
                        top_df = df.sort_values(by="market_cap", ascending=False).head(10)
                        st.dataframe(
                            top_df, 
                            use_container_width=True,
                            column_config={
                                "company_name": st.column_config.TextColumn("Company"),
                                "pe_ratio": st.column_config.NumberColumn("PE Ratio", format="%.2f"),
                                "market_cap": st.column_config.NumberColumn("Market Cap", format="₹%.2f"),
                                "current_price": st.column_config.NumberColumn("Price", format="₹%.2f"),
                            }
                        )
                    else:
                        st.info("No stock data available. Go to the Screener to fetch data!")
                else:
                    st.error(f"Error fetching data: {res.status_code}")
            except Exception as e:
                st.error(f"Application Error: {e}")

        elif nav_choice == "🔍 Screener":
            st.markdown("### 🔍 AI-Powered Screener")
            st.markdown("""
                Ask anything in natural language. The system will parse your request into a logic-based query 
                and fetch real-time data if needed.
            """)
            
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            query = st.text_input("Enter your query", placeholder="e.g., Price of RELIANCE OR PE below 30 and ROE above 15", label_visibility="collapsed")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                run_btn = st.button("🚀 Execute AI Query", use_container_width=True)
            with c2:
                show_logic = st.checkbox("Show Parsing Logic (DSL)", value=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if "screener_results" not in st.session_state:
                st.session_state.screener_results = None
            if "screener_query_dsl" not in st.session_state:
                st.session_state.screener_query_dsl = None

            if run_btn and query:
                with st.spinner("🤖 AI is thinking and fetching data..."):
                    results, structured_query = get_screener_results(query, st.session_state.token)
                    st.session_state.screener_results = results
                    st.session_state.screener_query_dsl = structured_query
            
            # Display Results from Session State
            if st.session_state.screener_results is not None:
                results = st.session_state.screener_results
                structured_query = st.session_state.screener_query_dsl

                if show_logic and structured_query:
                    with st.expander("🛠️ How I understood your query", expanded=True):
                        st.markdown(f"**Action:** `{structured_query.get('action', 'N/A')}`")
                        if structured_query.get('conditions'):
                            st.markdown("**Conditions Found:**")
                            for cond in structured_query['conditions']:
                                st.code(f"{cond['field']} {cond['operator']} {cond['value']}")
                        if structured_query.get('target_symbol'):
                            st.markdown(f"**Target:** `{structured_query['target_symbol']}`")
                        st.json(structured_query)
                
                if results:
                    st.success(f"✅ Found {len(results)} matches")
                    
                    # Create a clean DataFrame for the results
                    result_data = []
                    for stock in results:
                        fund = stock.get('fundamentals') or {}
                        result_data.append({
                            "Symbol": stock['symbol'],
                            "Company": stock['company_name'],
                            "Sector": stock['sector'],
                            "Price": fund.get('current_price'),
                            "PE Ratio": fund.get('pe_ratio'),
                            "Market Cap (₹)": fund.get('market_cap'),
                            "Div Yield (%)": fund.get('div_yield'),
                            "id": stock['id']
                        })
                    
                    res_df = pd.DataFrame(result_data)
                    
                    # Display as a rich table
                    st.dataframe(
                        res_df,
                        use_container_width=True,
                        column_config={
                            "Price": st.column_config.NumberColumn(format="₹%.2f"),
                            "Market Cap (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                            "PE Ratio": st.column_config.NumberColumn(format="%.2f"),
                            "Div Yield (%)": st.column_config.NumberColumn(format="%.2f"),
                        }
                    )
                    
                    # Add to Portfolio Quick Action
                    st.markdown("#### 🎯 Quick Actions")
                    for stock in results:
                        with st.container():
                            col_a, col_b = st.columns([4, 1])
                            with col_a:
                                st.write(f"Add **{stock['symbol']}** ({stock['company_name']}) to your portfolio?")
                            with col_b:
                                if st.button("➕ Add", key=f"add_{stock['id']}"):
                                    add_to_portfolio(stock['id'], st.session_state.token)
                else:
                    st.info("No matching stocks found. Try searching for a specific stock like 'Price of TCS' to add it to the database.")

        elif nav_choice == "💼 Portfolio":
            st.markdown("### 💼 My Portfolio")
            items = get_portfolio(st.session_state.token)
            if items:
                total_value = sum(item['quantity'] * item['avg_price'] for item in items)
                m1, m2 = st.columns(2)
                with m1: st.metric("Holdings", len(items))
                with m2: st.metric("Total Value", f"₹{total_value:,.2f}")
                
                for item in items:
                    stock = item['stock']
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    with c1:
                        st.markdown(f"#### {stock['symbol']}")
                        st.caption(stock['company_name'])
                    with c2: st.metric("Qty", item['quantity'])
                    with c3: st.metric("Avg Cost", f"₹{item['avg_price']:,.2f}")
                    with c4:
                        st.metric("Value", f"₹{item['quantity'] * item['avg_price']:,.2f}")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Your portfolio is empty. Use the Screener to find and add stocks!")

        elif nav_choice == "📜 History":
            st.markdown("### 📜 AI Query History")
            history = get_history(st.session_state.token)
            if history:
                for entry in history:
                    with st.expander(f"🔍 {entry['raw_query_text']}"):
                        st.write(f"**Action:** {entry['action']}")
                        st.markdown("**Parsed Parsing Logic:**")
                        st.json(entry.get('parsed_dsl', {}))
                        st.caption(f"Time: {entry.get('timestamp', 'N/A')}")
            else:
                st.info("No history found. Try asking the AI a question in the Screener!")

if __name__ == '__main__':
    main()
