import streamlit as st

st.set_page_config(page_title="SCS CN Method", page_icon="💧")
st.title("🌀 SCS Curve Number (CN) Method")

st.write("""
The **SCS CN Method** is used to estimate direct runoff using empirical relationships 
based on land use, soil type, and rainfall depth.
""")

rain = st.number_input("Enter Rainfall (mm):", min_value=0.0)
cn = st.number_input("Enter Curve Number:", min_value=0.0, max_value=100.0)
if st.button("Calculate Runoff"):
    s = (25400 / cn) - 254 if cn != 0 else None
    q = ((rain - 0.2 * s) ** 2) / (rain + 0.8 * s) if (s is not None and rain > 0.2 * s) else 0
    st.success(f"Estimated Runoff: {q:.2f} mm")

if st.button("⬅️ Back to Method Selection"):
    st.switch_page("pages/1_Method_Selection.py")
