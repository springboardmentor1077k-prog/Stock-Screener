import streamlit as st
import pandas as pd
import sqlite3
from ai_backend import AIBackend
from database import init_db
import os

# Page Configuration
st.set_page_config(
    page_title="Scenario 1: Valid Query",
    page_icon="✅",
    layout="wide"
)

# Initialize Database if needed
if not os.path.exists("stocks.db"):
    init_db()

# Initialize AI Backend
if 'backend' not in st.session_state:
    st.session_state.backend = AIBackend()

DB_NAME = "stocks.db"

def execute_sql(sql):
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except Exception as e:
        return str(e)

st.title("Scenario 1: Valid Query with Results")
st.markdown("""
**Goal:** Demonstrate the successful translation of a natural language query into SQL and the retrieval of matching records.
""")

# Input query
query_input = st.text_area("Enter your query (one per line):", placeholder="e.g. Show IT sector stocks with PE ratio less than 20")

if st.button("Execute Query") or query_input:
    if not query_input.strip():
        st.warning("Please enter a query.")
    else:
        queries = [q.strip() for q in query_input.split('\n') if q.strip()]
        
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

                # Step 3: Execute SQL
                st.markdown(f"### {i}.2 Database Results")
                result = execute_sql(response["generated_sql"])

                if isinstance(result, pd.DataFrame):
                    if not result.empty:
                        st.write(f"**Total Rows:** {len(result)}")
                        st.dataframe(result)
                        st.metric(f"Records Found (Query {i})", len(result))
                    else:
                        st.warning(f"No matching records found for Query {i}.")
                else:
                    st.error(f"SQL Execution Error: {result}")
            else:
                st.error("Unexpected invalid response for this scenario.")
