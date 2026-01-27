import streamlit as st
import pandas as pd
from ai_backend import AIBackend
import os

# Page Configuration
st.set_page_config(
    page_title="Scenario 3: Invalid Query",
    page_icon="🚫",
    layout="wide"
)

# Initialize AI Backend
if 'backend' not in st.session_state:
    st.session_state.backend = AIBackend()

st.title("Scenario 3: Invalid / Unsupported Query")
st.markdown("""
**Goal:** Demonstrate the safety layer that intercepts unsupported intents (e.g., predictions, advice) and prevents SQL generation.
""")

# Input query
query_input = st.text_area("Enter your query (one per line):", placeholder="e.g. Predict next quarter performance for Apple")

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
            if not response["is_valid"]:
                st.success(f"Security Layer Active: Query {i} Rejected")
                
                st.markdown("### Analysis Result")
                st.error(f"Error: {response['error_message']}")
                st.markdown(f"**Reason:** {response['reason']}")
                
                st.markdown("---")
                st.info("No SQL was generated. No database connection was attempted.")
            else:
                st.error(f"Unexpectedly validated an invalid query for Query {i}!")
