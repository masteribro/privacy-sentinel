"""Minimal Streamlit app for Privacy Sentinel."""
import streamlit as st
import sqlite3
from privacy_sentinel import db_setup
from privacy_sentinel.comparator import compare_labels
from privacy_sentinel.scoring import calculate_scores


DB_PATH = "data/privacy_sentinel.db"


def get_conn():
    db_setup.init_db(DB_PATH)
    return sqlite3.connect(DB_PATH)


def main():
    st.title("Privacy Sentinel — Minimal")

    st.write("Upload two label JSON snippets or paste simple comma-separated fields to compare.")

    with st.form("compare"):
        a_cats = st.text_input("Label A - data_categories (comma separated)")
        a_types = st.text_input("Label A - data_types (comma separated)")
        b_cats = st.text_input("Label B - data_categories (comma separated)")
        b_types = st.text_input("Label B - data_types (comma separated)")
        submitted = st.form_submit_button("Compare")

    if submitted:
        label_a = {"data_categories": a_cats, "data_types": a_types}
        label_b = {"data_categories": b_cats, "data_types": b_types}
        comp = compare_labels(label_a, label_b)
        scores = calculate_scores(label_a, label_b, comp)

        st.subheader("Comparison Report")
        st.json(comp)

        st.subheader("Scores")
        st.json(scores)


if __name__ == "__main__":
    main()
