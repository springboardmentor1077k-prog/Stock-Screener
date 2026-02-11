import streamlit as st
import pandas as pd
import sqlite3
from ai_backend import AIBackend
from database import init_db, DB_NAME
import os

# Page Configuration
st.set_page_config(
    page_title="AI-Powered SQL Demo",
    page_icon="🤖",
    layout="wide"
)

# Initialize AI Backend
if 'backend' not in st.session_state:
    st.session_state.backend = AIBackend()

# Initialize Database if needed
if not os.path.exists(DB_NAME):
    init_db()

def execute_sql(sql):
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except Exception as e:
        return str(e)

# Sidebar
with st.sidebar:
    st.title("Control Panel")
    if st.button("Reset Database"):
        init_db()
        st.success("Database reset to initial state!")
    
    st.markdown("---")
    st.info("Disclaimer: Informational use only. No investment advice.")

# Main Interface
st.title("🤖 Natural Language to SQL Query Engine + Analyst Data")
st.markdown("""
This system demonstrates a secure AI pipeline that converts natural language into SQL 
to query a structured stock database and enriches it with Analyst Data.
""")
st.info("Global Disclaimer: This platform provides informational market data only and does not offer investment advice.")

# Input
queries_input = st.text_area("Enter your queries (one per line):", placeholder="e.g.,\nShow IT sector stocks", height=150)

if st.button("Execute Queries") or queries_input:
    if not queries_input.strip():
        st.warning("Please enter at least one query.")
    else:
        queries = [q.strip() for q in queries_input.split('\n') if q.strip()]
        
        for i, query in enumerate(queries, 1):
            st.markdown("---")
            st.markdown(f"## Query {i}: {query}")
            
            # Step 1: AI Processing
            with st.spinner(f"AI is analyzing query {i}..."):
                response = st.session_state.backend.process_query(query)

            # Step 2: Handle Response
            if response["is_valid"]:
                st.success(f"Query {i} Validated Successfully")
                
                # Display Generated SQL
                st.markdown(f"### {i}.1 Generated SQL")
                st.code(response["generated_sql"], language="sql")
                st.caption("Explanation provided for transparency. Non-advisory, informational only.")

                # Step 3: Execute SQL
                st.markdown(f"### {i}.2 Database Results (Joined with Analyst Data)")
                
                # Execute SQL to get screener results
                screener_df = execute_sql(response["generated_sql"])
                
                if isinstance(screener_df, pd.DataFrame):
                    if screener_df.empty:
                         st.warning("No matching records found.")
                    else:
                        # Join with Analyst Data
                        try:
                            conn = sqlite3.connect(DB_NAME)
                            analyst_df = pd.read_sql_query("SELECT * FROM analyst_ratings", conn)
                            conn.close()
                            
                            # Perform Left Join
                            merged_df = pd.merge(screener_df, analyst_df, on='symbol', how='left')
                            
                            # Calculate Upside %
                            merged_df['upside_percent'] = ((merged_df['target_price'] - merged_df['price']) / merged_df['price']) * 100
                            
                            # Format columns for display
                            display_df = merged_df.copy()
                            display_df['upside_percent'] = display_df['upside_percent'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
                            
                            # Define strict column order as requested
                            # Symbol is required for context
                            desired_cols = ['symbol', 'price', 'target_price', 'upside_percent', 'recommendation', 'disclaimer']
                            
                            # Filter to exist columns only
                            final_cols = [c for c in desired_cols if c in display_df.columns]
                            
                            # Rename for clearer UI if desired, or keep as is. 
                            # User asked for "cp", "tp". Let's use nice headers.
                            column_config = {
                                "price": "Current Price",
                                "target_price": "Target Price",
                                "upside_percent": "Upside %",
                                "recommendation": "Recommendation",
                                "disclaimer": "Disclaimer"
                            }
                            
                            st.dataframe(display_df[final_cols], column_config=column_config)
                            st.caption("Analyst targets are third-party opinions. Not advice. May be inaccurate or outdated.")
                            
                            # Show raw JSON response as requested
                            st.markdown("### {i}.3 JSON Response")
                            json_records = display_df[final_cols].to_dict(orient='records')
                            st.json(json_records)
                            
                        except Exception:
                             st.error("System error. Please try again later.")
                             st.dataframe(screener_df) # Fallback
                else:
                    st.error("System error. Please try again later.")

            else:
                st.error("Query rejected by compliance")

# Footer
st.markdown("---")
st.caption("Demo Project | AI Backend Assistant")
