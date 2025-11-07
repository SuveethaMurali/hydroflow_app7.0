import streamlit as st

st.set_page_config(page_title="Method Selection", page_icon="🧮")

st.title("📘 Method Selection")
st.write("Choose a method for runoff estimation:")

method = st.radio("Select a method:", ["SCS Curve Number (CN) Method", "Stranger’s Method"])

if st.button("➡️ Proceed"):
    if method == "SCS Curve Number (CN) Method":
        st.switch_page("pages/2_SCN_Method.py")
    else:
        st.switch_page("pages/3_Strangers_Method.py")

if st.button("⬅️ Back to Home"):
    st.switch_page("Home.py")
