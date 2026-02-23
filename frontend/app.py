import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Powered Stock Screener",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
.fintech-header{
    background:linear-gradient(90deg,#0f1c2e,#1f3b73);
    color:white;
    padding:14px;
    border-radius:10px;
    font-size:24px;
    font-weight:600;
    margin-bottom:14px;
}
.landing-title{
    font-size:42px;
    font-weight:700;
    color:#1f3b73;
}
.landing-desc{
    font-size:18px;
    color:#5b7fa3;
}
.footer-card{
    background:linear-gradient(90deg,#0f1c2e,#1f3b73);
    padding:14px;
    border-radius:10px;
    text-align:center;
    font-size:14px;
    color:#ffffff;
    margin-top:40px;
}
</style>
""", unsafe_allow_html=True)

if "token" not in st.session_state:
    st.session_state.token=None
if "page" not in st.session_state:
    st.session_state.page="landing"
if "portfolio_id" not in st.session_state:
    st.session_state.portfolio_id=None
if "screener_results" not in st.session_state:
    st.session_state.screener_results=[]
if "buy_stock" not in st.session_state:
    st.session_state.buy_stock=None
if "buy_price" not in st.session_state:
    st.session_state.buy_price=None

def headers():
    return {"token":st.session_state.token}

if st.session_state.page=="landing":

    col1,col2 = st.columns([1.2,1])

    with col1:
        st.markdown('<div class="landing-title">AI Powered Stock Screener</div>',unsafe_allow_html=True)
        st.markdown(
            '<div class="landing-desc">'
            'Discover stocks using plain English queries, track portfolio performance and receive intelligent market alerts.'
            '</div>',
            unsafe_allow_html=True
        )

        if st.button("Continue to Platform"):
            st.session_state.page="login"
            st.rerun()

    with col2:
        st.image("landing.jpeg", use_container_width=True)

    st.stop()

if not st.session_state.token:

    st.markdown('<div class="fintech-header">🔐 Access Portal</div>',unsafe_allow_html=True)

    tab1,tab2=st.tabs(["Login","Register"])

    with tab1:
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        if st.button("Login"):
            r=requests.post(f"{API_URL}/login",json={"username":u,"password":p})
            if r.status_code==200:
                st.session_state.token=r.json()["token"]
                st.session_state.page="app"
                st.rerun()

    with tab2:
        u=st.text_input("New Username")
        p=st.text_input("New Password",type="password")
        if st.button("Register"):
            requests.post(f"{API_URL}/register",json={"username":u,"password":p})
            st.success("Registered successfully")

    st.stop()

st.sidebar.title("📈 AI Powered Screener")

page=st.sidebar.radio(
    "Navigate",
    ["📊 Screener Engine","💼 View Portfolio","📈 Market Simulation"]
)

st.markdown('<div class="fintech-header">📈 AI Powered Stock Screener</div>',unsafe_allow_html=True)

if page=="📊 Screener Engine":

    query=st.text_input("Enter stock query")

    if st.button("Search"):
        r=requests.post(f"{API_URL}/screen",headers=headers(),json={"query":query})
        if r.status_code==200:
            data=r.json()
            st.session_state.screener_results=data["data"]
            st.success(f"{data['count']} results fetched")

    if st.session_state.screener_results:

        df=pd.DataFrame(st.session_state.screener_results)
        st.dataframe(df,use_container_width=True)

        st.markdown("""
        <div style="background-color:#2b0b0b;border-left:5px solid #ff4b4b;
        padding:10px;border-radius:6px;margin-top:8px;">
        ⚠️ Screening results are generated using analytical filtering conditions and are intended for informational purposes only.
        </div>
        """,unsafe_allow_html=True)

        price_col=None
        for c in df.columns:
            if "price" in c.lower():
                price_col=c

        for i,row in df.iterrows():

            col1,col2=st.columns([6,1])

            with col1:
                st.write(row["symbol"])

            with col2:
                if st.button("BUY",key=f"buy_{i}"):

                    st.session_state.buy_stock=row["stock_id"]
                    st.session_state.buy_price=row[price_col] if price_col else 1

    if st.session_state.buy_stock:

        st.subheader("Add Stock to Portfolio")

        qty=st.number_input("Quantity",min_value=1,value=1)

        if st.button("Confirm Buy"):

            if not st.session_state.portfolio_id:
                r=requests.post(f"{API_URL}/portfolio/create",headers=headers())
                st.session_state.portfolio_id=r.json()["portfolio_id"]

            requests.post(
                f"{API_URL}/portfolio/add",
                headers=headers(),
                json={
                    "portfolio_id":st.session_state.portfolio_id,
                    "stock_id":st.session_state.buy_stock,
                    "quantity":qty,
                    "buy_price":st.session_state.buy_price
                }
            )

            st.success("Added to portfolio")

            st.session_state.buy_stock=None

if page=="💼 View Portfolio":

    if st.session_state.portfolio_id:

        r=requests.get(f"{API_URL}/portfolio/{st.session_state.portfolio_id}",headers=headers())
        holdings=r.json()

        rows=[]
        for h in holdings:

            invested=h["buy_price"]*h["quantity"]
            current=h["current_price"]*h["quantity"]
            pnl=current-invested
            pnl_percent=(pnl/invested)*100 if invested else 0

            rows.append({
                "Symbol":h["symbol"],
                "Qty":h["quantity"],
                "Avg Price":round(h["buy_price"],2),
                "LTP":round(h["current_price"],2),
                "Invested":round(invested,2),
                "Current":round(current,2),
                "PnL":round(pnl,2),
                "PnL %":round(pnl_percent,2)
            })

        df=pd.DataFrame(rows)
        df.index=df.index+1
        st.dataframe(df,use_container_width=True)

        st.markdown("""
        <div style="background-color:#2b0b0b;border-left:5px solid #ff4b4b;
        padding:10px;border-radius:6px;margin-top:8px;">
        ⚠️ Portfolio values are based on simulated market conditions for demonstration purposes.
        </div>
        """,unsafe_allow_html=True)

    st.subheader("🔔 Alerts")

    alert_query=st.text_input("Create alert query")

    if st.button("Create Alert"):
        requests.post(f"{API_URL}/alerts/create",headers=headers(),json={"query":alert_query})
        st.success("Alert created successfully")

    if st.button("Check Alerts"):

        r = requests.get(f"{API_URL}/alerts/check", headers=headers())

        if r.status_code == 200:

            alerts = r.json()["triggered_alerts"]

            if alerts:

                for a in alerts:

                    color = "#22c55e"
                    if a["signal"] == "WATCH":
                        color = "#f59e0b"
                    if a["signal"] == "RISK":
                        color = "#ef4444"

                    col1, col2 = st.columns([1,3])

                    with col2:
                        st.markdown(f"""
                        <div style="
                            background:#0f172a;
                            padding:14px;
                            border-radius:12px;
                            margin-bottom:10px;
                            border-left:6px solid {color};
                        ">
                        <b>{a["signal"]} SIGNAL</b><br>
                        <b>Stock:</b> {a["symbol"]}<br>
                        <b>Price:</b> ₹{a["current_price"]}<br>
                        <b>Reason:</b> {a["reason"]}
                        </div>
                        """, unsafe_allow_html=True)

            else:
                st.info("No alerts triggered yet.")

if page=="📈 Market Simulation":

    if st.button("Simulate Market Prices"):
        requests.post(f"{API_URL}/simulate",headers=headers())
        st.success("Market prices updated")

st.markdown("""
<div class="footer-card">
This platform is provided for educational and demonstration purposes only and does not constitute financial advice.
</div>
""",unsafe_allow_html=True)
