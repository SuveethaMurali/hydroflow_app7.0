import streamlit as st

st.set_page_config(page_title="Stranger’s Method", page_icon="📈")
st.title("📊 Stranger’s Method")

st.write("""
The **Stranger’s Method** estimates runoff by analyzing rainfall intensity 
and catchment characteristics.
""")

rain_intensity = st.number_input("Enter Rainfall Intensity (mm/hr):", min_value=0.0)
area = st.number_input("Enter Catchment Area (km²):", min_value=0.0)
if st.button("Compute Discharge"):
    discharge = 0.278 * rain_intensity * area
    st.success(f"Estimated Peak Discharge: {discharge:.2f} m³/s")

if st.button("⬅️ Back to Method Selection"):
    st.switch_page("pages/1_Method_Selection.py")
