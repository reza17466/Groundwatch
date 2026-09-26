import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from fpdf import FPDF
import io

# ==================== Page Configuration ====================
st.set_page_config(page_title="GroundWatch", page_icon="💧", layout="wide")

# ==================== Sidebar Navigation ====================
st.sidebar.title("💧 GroundWatch")
st.sidebar.caption("Intelligent Groundwater Monitoring")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Precipitation (DMI)", "Groundwater (GEUS)", "Forecast & Alerts", "Reports"]
)

st.sidebar.divider()
st.sidebar.caption("MVP v2.0 — Reza Chash")

# ==================== Helper Functions ====================

@st.cache_data(ttl=3600)
def fetch_dmi_precipitation(days=30):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    datetime_range = f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    url = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"
    params = {
        "stationId": "06186",
        "parameterId": "precip_past1h",
        "datetime": datetime_range,
        "limit": 1000,
    }
    try:
        response = requests.get(url, params=params, timeout=20)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if features:
                records = []
                for f in features:
                    props = f.get("properties", {})
                    records.append({
                        "timestamp": props.get("observed"),
                        "precipitation_mm": props.get("value"),
                        "station_id": props.get("stationId"),
                    })
                df = pd.DataFrame(records)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp").reset_index(drop=True)
                return df, "real"
    except Exception:
        pass
    # Fallback
    dates = pd.date_range(
        end=datetime.utcnow().replace(minute=0, second=0, microsecond=0),
        periods=days * 24,
        freq="h",
    )
    rng = np.random.default_rng(42)
    precip = rng.exponential(0.3, len(dates))
    precip[precip < 0.1] = 0.0
    df = pd.DataFrame({
        "timestamp": dates,
        "precipitation_mm": np.round(precip, 2),
        "station_id": "SAMPLE-DATA",
    })
    return df, "simulated"

@st.cache_data(ttl=7200)
def fetch_geus_groundwater():
    wfs_url = "http://arcims.minn.dk/wfsconnector/com.esri.wfs.Esrimap"
    params = {
        "SERVICE": "WFS",
        "VERSION": "1.0.0",
        "REQUEST": "GetFeature",
        "TYPENAME": "JUPITER_BORINGER",
        "MAXFEATURES": "100",
        "OUTPUTFORMAT": "json",
    }
    try:
        response = requests.get(wfs_url, params=params, timeout=20)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if features:
                records = []
                for f in features:
                    props = f.get("properties", {})
                    geom = f.get("geometry", {})
                    coords = geom.get("coordinates", [None, None])
                    records.append({
                        "dgunr": props.get("DGUnr"),
                        "municipality": props.get("Kommune"),
                        "drilling_depth": props.get("Boredybde"),
                        "terrain_elevation": props.get("Terrænkote"),
                        "lat": coords[1] if len(coords) > 1 else None,
                        "lon": coords[0] if len(coords) > 0 else None,
                    })
                df = pd.DataFrame(records)
                return df, "real"
    except Exception:
        pass
    # Fallback
    rng = np.random.default_rng(42)
    municipalities = ["Lemvig", "Ringkøbing-Skjern", "Holstebro", "Struer", "Aarhus"]
    df = pd.DataFrame({
        "dgunr": [f"43.{i}" for i in range(1, 101)],
        "municipality": rng.choice(municipalities, 100),
        "drilling_depth": rng.uniform(5, 150, 100).round(1),
        "terrain_elevation": rng.uniform(0, 50, 100).round(1),
        "lat": rng.uniform(55.5, 57.0, 100).round(4),
        "lon": rng.uniform(8.0, 10.5, 100).round(4),
    })
    return df, "simulated"

# ==================== Page: Dashboard ====================
if page == "Dashboard":
    st.title("💧 GroundWatch Dashboard")
    st.subheader("Real-time Overview of Groundwater Monitoring")
    
    # Simulated summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monitoring Points", "124")
    col2.metric("Active Alerts", "3", delta="+1 since yesterday")
    col3.metric("Avg. Water Level (m)", "2.4")
    col4.metric("Data Sources", "DMI, GEUS, Sensors")
    
    st.divider()
    
    # Map with simulated status
    st.subheader("🗺️ Monitoring Points Status")
    rng = np.random.default_rng(42)
    map_data = pd.DataFrame({
        "lat": rng.uniform(55.5, 57.0, 20),
        "lon": rng.uniform(8.0, 10.5, 20),
        "status": rng.choice(["Normal", "Warning", "Critical"], 20, p=[0.7, 0.2, 0.1])
    })
    # Map colors based on status (Streamlit map doesn't support colors directly, but we can use size or just show)
    st.map(map_data[["lat", "lon"]])
    st.caption("🔴 Critical  🟡 Warning  🟢 Normal (color coding in full version)")
    
    st.divider()
    
    st.subheader("📊 Recent Alerts")
    alerts_df = pd.DataFrame({
        "Time": [datetime.now() - timedelta(hours=i) for i in range(5)],
        "Location": ["Lemvig 43.18", "Ringkøbing 43.27", "Holstebro 43.55", "Struer 43.61", "Aarhus 43.72"],
        "Water Level (m)": [1.2, 1.6, 2.1, 1.9, 2.3],
        "Threshold (m)": [1.5, 1.8, 2.5, 2.0, 2.5],
        "Status": ["Critical", "Warning", "Normal", "Warning", "Normal"]
    })
    st.dataframe(alerts_df, use_container_width=True)

# ==================== Page: Precipitation ====================
elif page == "Precipitation (DMI)":
    st.title("🌧️ Precipitation Data (DMI)")
    st.caption("Copenhagen Station — Last 30 Days")
    
    if st.button("Fetch Precipitation Data", type="primary"):
        with st.spinner("Connecting to DMI API..."):
            df_precip, status = fetch_dmi_precipitation(days=30)
        
        if status == "real":
            st.success(f"✅ {len(df_precip)} real records fetched from DMI")
        else:
            st.warning("⚠️ API unavailable — showing simulated data")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Records", len(df_precip))
        col2.metric("Total Precipitation (mm)", round(df_precip["precipitation_mm"].sum(), 1))
        col3.metric("Average (mm/h)", round(df_precip["precipitation_mm"].mean(), 2))
        
        st.subheader("📈 Precipitation Chart")
        st.line_chart(df_precip.set_index("timestamp")["precipitation_mm"])
        
        with st.expander("📄 Raw Data"):
            st.dataframe(df_precip.tail(50))

# ==================== Page: Groundwater ====================
elif page == "Groundwater (GEUS)":
    st.title("🌊 Groundwater Data (GEUS)")
    st.caption("Direct connection to GEUS WFS service (no proxy)")
    
    if st.button("Fetch GEUS Data", type="primary"):
        with st.spinner("Connecting to WFS service..."):
            df_gw, status = fetch_geus_groundwater()
        
        if status == "real":
            st.success(f"✅ {len(df_gw)} real boreholes fetched from GEUS")
        else:
            st.warning("⚠️ WFS service unavailable — showing simulated data")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Boreholes", len(df_gw))
        if "drilling_depth" in df_gw.columns:
            col2.metric("Avg. Drilling Depth (m)", round(df_gw["drilling_depth"].mean(), 1))
        if "terrain_elevation" in df_gw.columns:
            col3.metric("Avg. Terrain Elevation (m)", round(df_gw["terrain_elevation"].mean(), 1))
        
        if "lat" in df_gw.columns and "lon" in df_gw.columns:
            st.subheader("🗺️ Borehole Map")
            st.map(df_gw[["lat", "lon"]].dropna())
        
        if "drilling_depth" in df_gw.columns:
            st.subheader("📈 Drilling Depth Distribution")
            st.bar_chart(df_gw["drilling_depth"].value_counts().sort_index().head(30))
        
        with st.expander("📄 Raw Borehole Data"):
            st.dataframe(df_gw.head(100))

# ==================== Page: Forecast & Alerts ====================
elif page == "Forecast & Alerts":
    st.title("🔮 Forecast & Early Warning")
    
    st.subheader("⚙️ Alert Settings")
    threshold = st.slider("Water Level Alert Threshold (meters below ground)", 0.5, 10.0, 2.0, 0.5)
    
    st.subheader("7-Day Forecast")
    st.info("ℹ️ This section uses simulated data until the AI model is trained.")
    
    rng = np.random.default_rng(42)
    days = 30
    historical = rng.uniform(1.5, 3.0, days) + np.linspace(0, 0.5, days)
    forecast_days = 7
    forecast = historical[-1] + np.cumsum(rng.normal(0.05, 0.1, forecast_days))
    
    all_dates = pd.date_range(end=datetime.utcnow(), periods=days + forecast_days, freq="D")
    all_values = np.concatenate([historical, forecast])
    
    df_forecast = pd.DataFrame({"date": all_dates, "water_level_m": all_values})
    st.line_chart(df_forecast.set_index("date")["water_level_m"])
    
    st.subheader("🚨 Alert Status")
    if forecast[-1] > threshold:
        st.error(f"⚠️ Alert: Forecasted water level ({forecast[-1]:.2f} m) has exceeded the threshold ({threshold} m)!")
    else:
        st.success(f"✅ Normal: Forecasted water level ({forecast[-1]:.2f} m) is below the alert threshold ({threshold} m).")
    
    st.subheader("📊 Forecast Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Level (m)", round(historical[-1], 2))
    col2.metric("7-Day Forecast (m)", round(forecast[-1], 2))
    col3.metric("Change (m)", round(forecast[-1] - historical[-1], 2))

# ==================== Page: Reports ====================
elif page == "Reports":
    st.title("📄 Compliance Reports")
    st.caption("Generate a PDF report for municipalities and environmental authorities.")
    
    st.markdown("""
    This report includes:
    - Current groundwater levels at monitored points
    - Forecasted levels for the next 7 days
    - Alert status and threshold exceedances
    - Data sources and methodology
    """)
    
    if st.button("Generate PDF Report", type="primary"):
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(200, 10, txt="GroundWatch - Groundwater Monitoring Report", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(5)
        pdf.multi_cell(0, 10, txt="This report summarizes the current groundwater levels and forecasted conditions for monitored locations in Denmark.")
        pdf.ln(5)
        pdf.cell(200, 10, txt="Summary of Monitoring Points:", ln=True)
        pdf.cell(200, 10, txt="- Total Points: 124", ln=True)
        pdf.cell(200, 10, txt="- Active Alerts: 3", ln=True)
        pdf.cell(200, 10, txt="- Average Water Level: 2.4 m", ln=True)
        pdf.ln(5)
        pdf.cell(200, 10, txt="Data Sources: DMI (precipitation), GEUS (groundwater), IoT sensors", ln=True)
        pdf.ln(10)
        pdf.cell(200, 10, txt="Prepared by GroundWatch", ln=True)
        
        # Output to bytes
        pdf_output = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_output,
            file_name="groundwatch_report.pdf",
            mime="application/pdf"
        )
        st.success("✅ Report generated successfully!")

st.divider()
st.caption("GroundWatch — MVP v2.0 — Reza Chash")
