import streamlit as st
from services import http
import pandas as pd


def render():
    st.markdown('<h2 style="color:#ffffff;margin-top:0;">Holdings</h2>', unsafe_allow_html=True)
    st.info("Favorites are user-selected and do not represent investment recommendations.")
    with st.form("add_favorite_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 3, 1])
        with c1:
            symbol = st.text_input("Symbol").upper()
        with c2:
            label = st.text_input("Custom Name")
        with c3:
            add = st.form_submit_button("Add")
    if add:
        try:
            http.post("/favorites", {"symbol": symbol, "label": label})
            st.success("Added to favorites")
        except http.NetworkError as e:
            st.warning(str(e))
    try:
        items, _ = http.get("/favorites")
    except http.NetworkError as e:
        st.warning(str(e))
        items = []
    if items:
        st.markdown(" ")
        # header with bottom border
        h1, h2, h3, h4, h5 = st.columns([2, 3, 3, 2, 1])
        h1.markdown("**symbol**")
        h2.markdown("**custom_name**")
        h3.markdown("**sector**")
        h4.markdown("**price**")
        h5.markdown("**Delete**")
        st.markdown('<hr class="qd-row-sep" />', unsafe_allow_html=True)
        # rows with separators and padding
        for it in items:
            c1, c2, c3, c4, c5 = st.columns([2, 3, 3, 2, 1])
            c1.markdown(f"{it.get('symbol','')}")
            c2.markdown(f"{it.get('label','')}")
            c3.markdown(f"{it.get('sector','')}")
            c4.markdown(f"{it.get('price','')}")
            if c5.button("✖", key=f"del_{it['favorite_id']}"):
                try:
                    http.post("/favorites/remove", {"favorite_id": it["favorite_id"]})
                    st.rerun()
                except http.NetworkError as e:
                    st.warning(str(e))
            st.markdown('<hr class="qd-row-sep" />', unsafe_allow_html=True)
    else:
        st.markdown('<div class="qd-banner">No favorites yet</div>', unsafe_allow_html=True)
