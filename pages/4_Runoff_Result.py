import streamlit as st
import pandas as pd
import io
from datetime import datetime
import matplotlib.pyplot as plt
import base64

st.set_page_config(page_title="Runoff Results", page_icon="📉", layout="wide")
st.title("📉 Runoff Results")

st.write("""
Upload a CSV of rainfall time series (two columns): **time** and **rain_mm**.
- **time**: ISO timestamps (e.g. 2025-11-07 09:00) or any parseable datetime.
- **rain_mm**: rainfall depth during the interval in millimetres.
If your file has only rainfall depths, upload a single-column CSV and set the interval length below.
""")

uploaded = st.file_uploader("Upload rainfall CSV", type=["csv"])

col1, col2 = st.columns([1,1])
with col1:
    area_km2 = st.number_input("Catchment area (km²)", min_value=0.0001, value=1.0, format="%.4f")
    interval_min = st.number_input("If no timestamps, interval length (minutes)", min_value=1, value=60)
    cn_value = st.number_input("Curve Number (CN) for SCS method", min_value=1.0, max_value=100.0, value=75.0)
with col2:
    runoff_unit = st.selectbox("Runoff output unit", ["mm depth", "m³ (volume)"])
    download_name = st.text_input("Download filename (without extension)", value="runoff_results")

def compute_scs(P_mm, CN):
    # P_mm: rainfall depth in mm for the interval
    if CN == 0:
        return 0.0
    S = (25400.0 / CN) - 254.0  # mm
    Ia = 0.2 * S
    if P_mm <= Ia:
        return 0.0
    Q = ((P_mm - Ia) ** 2) / (P_mm + 0.8 * S)
    return Q

def compute_stranger_discharge(intensity_mm_per_hr, area_km2):
    # Q (m3/s) = 0.278 * i (mm/hr) * A (km2)
    return 0.278 * intensity_mm_per_hr * area_km2

def df_from_upload(f):
    try:
        df = pd.read_csv(f)
        # Try to find column names
        cols = [c.lower() for c in df.columns]
        if "rain_mm" in cols:
            col_rain = df.columns[cols.index("rain_mm")]
        elif "rain" in cols:
            col_rain = df.columns[cols.index("rain")]
        else:
            # assume first column is rain
            col_rain = df.columns[0]
        if "time" in cols or "timestamp" in cols or "date" in cols:
            for cand in ["time","timestamp","date"]:
                if cand in cols:
                    col_time = df.columns[cols.index(cand)]
                    break
            df["time"] = pd.to_datetime(df[col_time])
        else:
            df["time"] = None
        df["rain_mm"] = pd.to_numeric(df[col_rain], errors="coerce").fillna(0.0)
        return df[["time","rain_mm"]]
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        return None

if uploaded is not None:
    df = df_from_upload(uploaded)
    if df is None:
        st.stop()

    # If time is None, generate times using interval
    if df["time"].isnull().all():
        start = datetime.now()
        times = [start + pd.Timedelta(minutes=interval_min*i) for i in range(len(df))]
        df["time"] = times

    # compute delta hours between samples (assume constant)
    df = df.sort_values("time").reset_index(drop=True)
    if len(df) >= 2:
        delta = (df.loc[1,"time"] - df.loc[0,"time"]).total_seconds() / 3600.0
        if delta <= 0:
            delta = interval_min / 60.0
    else:
        delta = interval_min / 60.0

    # Compute intensity mm/hr for each interval (rain_mm / delta_hours)
    df["intensity_mm_per_hr"] = df["rain_mm"] / delta

    # Compute SCS runoff depth (mm) per interval
    df["scs_runoff_mm"] = df["rain_mm"].apply(lambda p: compute_scs(p, cn_value))

    # Convert runoff depth to volume m3: depth(mm)/1000 * area_m2
    area_m2 = area_km2 * 1e6
    df["scs_runoff_m3"] = df["scs_runoff_mm"] / 1000.0 * area_m2

    # Compute Stranger discharge (m3/s) per interval using intensity
    df["stranger_Q_m3s"] = df["intensity_mm_per_hr"].apply(lambda i: compute_stranger_discharge(i, area_km2))

    # For comparability, compute Stranger volume over the interval: Q (m3/s) * seconds in interval
    seconds = delta * 3600.0
    df["stranger_volume_m3"] = df["stranger_Q_m3s"] * seconds

    # Show summary metrics
    st.subheader("Summary")
    total_rain = df["rain_mm"].sum()
    total_scs_runoff_mm = df["scs_runoff_mm"].sum()
    total_scs_volume = df["scs_runoff_m3"].sum()
    total_stranger_volume = df["stranger_volume_m3"].sum()

    st.write(f"- Total rainfall: **{total_rain:.2f} mm**")
    st.write(f"- Total SCS runoff: **{total_scs_runoff_mm:.2f} mm** ({total_scs_volume:,.0f} m³)")
    st.write(f"- Total Stranger estimated volume: **{total_stranger_volume:,.0f} m³**")

    # Tabs for separate views
    tab1, tab2 = st.tabs(["SCS Curve Number (CN) Method", "Stranger's Method"])

    with tab1:
        st.subheader("SCS Runoff Hydrograph")
        fig, ax = plt.subplots(figsize=(10,3))
        ax.plot(df["time"], df["scs_runoff_mm"])
        ax.set_ylabel("Runoff (mm)")
        ax.set_xlabel("Time")
        ax.grid(True)
        st.pyplot(fig)

        st.subheader("SCS Runoff Table")
        st.dataframe(df[["time","rain_mm","scs_runoff_mm","scs_runoff_m3"]])

    with tab2:
        st.subheader("Stranger's Discharge Hydrograph (Q in m³/s)")
        fig2, ax2 = plt.subplots(figsize=(10,3))
        ax2.plot(df["time"], df["stranger_Q_m3s"])
        ax2.set_ylabel("Discharge (m³/s)")
        ax2.set_xlabel("Time")
        ax2.grid(True)
        st.pyplot(fig2)

        st.subheader("Stranger's Results Table")
        st.dataframe(df[["time","rain_mm","intensity_mm_per_hr","stranger_Q_m3s","stranger_volume_m3"]])

    # Prepare downloadable CSV with results
    out = df.copy()
    out["time"] = out["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    csv_bytes = out.to_csv(index=False).encode("utf-8")
    b64 = base64.b64encode(csv_bytes).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{download_name}.csv">⬇️ Download results as CSV</a>'
    st.markdown(href, unsafe_allow_html=True)

else:
    st.info("Upload a rainfall CSV to compute runoff using both methods.")
