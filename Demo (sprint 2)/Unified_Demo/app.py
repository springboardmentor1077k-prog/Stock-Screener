import streamlit as st
import pandas as pd
import sqlite3
from ai_backend import AIBackend
from database import init_db
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

# Database Helper
DB_NAME = "stocks.db"

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
    st.markdown("### Demo Scenarios")
    st.info("1. Valid Query: 'Show IT sector stocks with PE ratio less than 20'")
    st.info("2. No Results: 'Find stocks priced above 5000'")
    st.info("3. Invalid: 'Predict next quarter performance'")

# Main Interface
st.title("🤖 Natural Language to SQL Query Engine")
st.markdown("""
This system demonstrates a secure AI pipeline that converts natural language into SQL 
to query a structured stock database.
""")

# Input
queries_input = st.text_area("Enter your queries (one per line):", placeholder="e.g.,\nShow IT sector stocks with PE ratio less than 20\nFind stocks priced above 5000", height=150)

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
                st.caption(response["explanation"])

                # Step 3: Execute SQL (Simulated Backend Execution)
                st.markdown(f"### {i}.2 Database Results")
                result = execute_sql(response["generated_sql"])

                if isinstance(result, pd.DataFrame):
                    if not result.empty:
                        st.dataframe(result)
                        st.metric(f"Records Found (Query {i})", len(result))
                    else:
                        st.warning(f"No matching records found for Query {i}.")
                        st.metric(f"Records Found (Query {i})", 0)
                else:
                    st.error(f"SQL Execution Error: {result}")

            else:
                st.error(f"Query {i} Rejected by Safety Layer")
                st.markdown(f"**Reason:** {response['reason']}")
                st.markdown(f"**Error:** {response['error_message']}")

# Footer
st.markdown("---")
st.caption("Demo Project | AI Backend Assistant")
