"""
Alerts Page - Configure and manage database-wide alerts.

This page allows users to:
- Create alerts that monitor all stocks in the database
- View active alerts from database
- Manage alert settings
"""

import streamlit as st
import pandas as pd
from api_client import APIClient


# Metric options mapping to backend
METRIC_OPTIONS = {
    "PE Ratio": "pe_ratio",
    "PEG Ratio": "peg_ratio",
    "Debt": "debt",
    "Free Cash Flow": "free_cash_flow",
    "Revenue": "revenue",
    "EBITDA": "ebitda",
    "Net Profit": "net_profit",
    "Current Market Price": "current_market_price",
    "Target Price High": "target_price_high",
    "Target Price Low": "target_price_low"
}

OPERATOR_OPTIONS = {
    "Less than (<)": "<",
    "Greater than (>)": ">",
    "Less than or equal (<=)": "<=",
    "Greater than or equal (>=)": ">=",
    "Equal to (=)": "="
}


def render_alerts():
    """Render the alerts configuration page."""
    
    # Initialize API client
    if "api_client" not in st.session_state:
        from api_client import APIClient
        st.session_state.api_client = APIClient()
    
    api_client = st.session_state.api_client
    
    # Hide default Streamlit page nav (we use custom nav above)
    st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.header("📈 AI Stock Screener")
        st.divider()
        st.page_link("pages/_screener.py", label="📊 Screener", icon=None)
        st.page_link("pages/_portfolio.py", label="💼 Portfolio", icon=None)
        st.page_link("pages/_alerts.py", label="🔔 Alerts", icon=None)
    
    # Display user email in top right
    col_title, col_email, col_logout = st.columns([3, 1, 1])
    with col_title:
        st.title("🔔 Alerts")
    with col_email:
        if "email" in st.session_state and st.session_state.email:
            st.markdown(f"<div style='text-align: right; padding-top: 20px;'>👤 {st.session_state.email}</div>", unsafe_allow_html=True)
    with col_logout:
        st.write("")
        st.write("")
        if st.button("🚪 Logout", key="logout_alerts"):
            # Clear session state
            st.session_state.token = None
            st.session_state.email = None
            st.session_state.user_id = None
            st.session_state.authenticated = False
            st.switch_page("app.py")
    
    # Page header
    st.caption("Configure alerts to monitor all stocks in the database")
    st.warning("Disclaimer: This platform is for informational purposes only and is not financial advice.")
    
    # Check authentication
    if "token" not in st.session_state or not st.session_state.token:
        st.error("🔒 Please login first")
        return
    
    # Info about database-wide alerts
    st.info("ℹ️ **Note:** Alerts monitor the entire stock database. If any stock meets the condition, the alert will trigger.")
    
    
    # Load alerts from backend
    success, message, data = api_client.get_alerts(st.session_state.token)
    # ---------------------

    if not success:
        st.error(f"❌ Error loading alerts: {message}")
        return
    
    existing_alerts = data.get("items", data.get("alerts", [])) or []

    # Manual trigger section
    st.divider()
    st.subheader("Trigger Alerts")
    st.caption("Click to evaluate all active alerts now")

    if st.button("🚨 Trigger Alerts Now", use_container_width=True, type="primary"):
        with st.spinner("Evaluating alerts..."):
            success, msg, eval_data = api_client.evaluate_alerts(st.session_state.token)

        if success:
            triggered_alerts = eval_data.get("items", eval_data.get("triggered_alerts", [])) or []
            triggered_rows = []
            for alert in triggered_alerts:
                condition = f"{alert.get('metric')} {alert.get('operator')} {alert.get('threshold')}"
                for stock in alert.get("triggered_stocks", []):
                    triggered_rows.append({
                        "Alert ID": alert.get("alert_id"),
                        "Condition": condition,
                        "Symbol": stock.get("symbol"),
                        "Company": stock.get("company_name"),
                            "Triggered Value": stock.get("triggered_value"),
                        })

            if triggered_rows:
                st.dataframe(
                    pd.DataFrame(triggered_rows),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No records found")
        else:
            st.error(f"❌ {msg}")
    
    # Create alert section
    st.subheader("Create New Alert")
    st.caption("Set up automated alerts across all stocks")
    
    # Use st.form() for grouped inputs
    with st.form("alert_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Metric selection
            metric_label = st.selectbox(
                "Metric to Monitor",
                ["Select metric..."] + list(METRIC_OPTIONS.keys()),
                help="What metric should trigger the alert"
            )
        
        with col2:
            # Operator selection
            operator_label = st.selectbox(
                "Condition",
                ["Select condition..."] + list(OPERATOR_OPTIONS.keys()),
                help="How to compare the metric"
            )
            
            # Threshold value
            threshold = st.number_input(
                "Threshold Value",
                min_value=0.0,
                value=25.0,
                step=0.1,
                help="Value that triggers the alert"
            )
        
        # Submit button
        submitted = st.form_submit_button(
            "✅ Create Alert",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if (metric_label != "Select metric..." and 
                operator_label != "Select condition..."):
                
                # Map labels to backend values
                metric = METRIC_OPTIONS[metric_label]
                operator = OPERATOR_OPTIONS[operator_label]
                
                # Create alert via API
                with st.spinner("Creating alert..."):
                    success, msg, alert_data = api_client.create_alert(
                        portfolio_id=None,
                        metric=metric,
                        operator=operator,
                        threshold=threshold,
                        token=st.session_state.token
                    )
                
                if success:
                    st.success(f"✅ {msg}")
                    # Keep alert state in sync by evaluating immediately after creation.
                    with st.spinner("Evaluating alert once..."):
                        eval_success, eval_msg, eval_data = api_client.evaluate_alerts(st.session_state.token)
                    if eval_success:
                        triggered_count = eval_data.get("triggered_count", 0)
                        if triggered_count > 0:
                            st.info(f"ℹ️ New alert evaluated. {triggered_count} trigger(s) detected.")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("⚠️ Please fill in all fields")
    
    # Display active alerts
    st.divider()
    st.subheader("Active Alerts")
    
    if len(existing_alerts) == 0:
        # Empty state
        st.info("📭 No active alerts. Create one above!")
    else:
        # Status indicator - show count
        st.success(f"✅ {len(existing_alerts)} active alert(s)")
        
        # Convert to DataFrame for display
        display_data = []
        for alert in existing_alerts:
            display_data.append({
                "ID": alert.get('id'),
                "Metric": alert.get('metric', 'N/A'),
                "Condition": f"{alert.get('operator', '?')} {alert.get('threshold', 'N/A')}",
                "Status": alert.get('status', 'unknown'),
                "Active": "Yes" if alert.get('is_active') else "No",
                "Triggers": alert.get('trigger_count', 0),
                "Last Triggered": alert.get('last_triggered') if alert.get('last_triggered') else "Never"
            })
        
        df = pd.DataFrame(display_data)
        
        # Display alerts table
        with st.container():
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        
        # Delete alert section
        st.divider()
        col1, col2 = st.columns([3, 1])
        
        with col1:
            alert_to_delete = st.selectbox(
                "Remove alert",
                ["Select alert..."] + [
                    f"ID {alert.get('id')}: Database - {alert.get('metric', 'N/A')} {alert.get('operator', '?')} {alert.get('threshold', 'N/A')}"
                    for alert in existing_alerts
                    if alert.get("id") is not None
                ]
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                if alert_to_delete and alert_to_delete != "Select alert...":
                    # Extract alert ID
                    alert_id = int(alert_to_delete.split(":")[0].replace("ID ", ""))
                    
                    with st.spinner("Deleting alert..."):
                        success, msg = api_client.delete_alert(alert_id, st.session_state.token)
                    
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


if __name__ == "__main__":
    render_alerts()
