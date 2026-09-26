import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

# ==================== Page Configuration ====================
st.set_page_config(page_title="GroundWatch", page_icon="💧", layout="wide")

st.title("💧 GroundWatch")
st.subheader("Intelligent Platform for Groundwater Monitoring & Forecasting")
st.caption("MVP Version — Powered by Danish Open Data (DMI, GEUS)")

st.divider()

# ==================== Helper Functions ====================

# -------------------- 1. Fetch Precipitation Data (DMI) --------------------
@st.cache_data(ttl=3600)
def fetch_dmi_precipitation(days=30):
    """Fetch precipitation data from DMI Frie Data API v2."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    datetime_range = f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    url = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"
    params = {
        "stationId": "06186",  # Copenhagen station
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
    
    # Fallback: simulated data if API is unavailable
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

# -------------------- 2. Fetch Groundwater Data (GEUS) --------------------
@st.cache_data(ttl=7200)
def fetch_geus_groundwater():
    """Fetch borehole data from GEUS WFS service."""
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
    
    # Fallback: simulated data
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

# ==================== User Interface ====================

tab1, tab2, tab3 = st.tabs(["🌧️ Precipitation (DMI)", "🌊 Groundwater (GEUS)", "🔮 Forecast & Alerts"])

# ---------- Tab 1: Precipitation ----------
with tab1:
    st.header("Precipitation Data — Copenhagen (Last 30 Days)")
    
    if st.button("Fetch Precipitation Data", type="primary", key="precip_btn"):
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

# ---------- Tab 2: Groundwater ----------
with tab2:
    st.header("Groundwater Level Data — GEUS Denmark")
    st.caption("Direct connection to GEUS WFS service (no proxy)")
    
    if st.button("Fetch GEUS Data", type="primary", key="gw_btn"):
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
        
        # Interactive map
        if "lat" in df_gw.columns and "lon" in df_gw.columns:
            st.subheader("🗺️ Borehole Map")
            st.map(df_gw[["lat", "lon"]].dropna())
        
        # Depth distribution chart
        if "drilling_depth" in df_gw.columns:
            st.subheader("📈 Drilling Depth Distribution")
            st.bar_chart(df_gw["drilling_depth"].value_counts().sort_index().head(30))
        
        with st.expander("📄 Raw Borehole Data"):
            st.dataframe(df_gw.head(100))

# ---------- Tab 3: Forecast & Alerts ----------
with tab3:
    st.header("Forecasting & Early Warning")
    
    st.subheader("⚙️ Alert Settings")
    threshold = st.slider("Water Level Alert Threshold (meters below ground)", 0.5, 10.0, 2.0, 0.5)
    
    st.subheader("🔮 7-Day Forecast")
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

st.divider()
st.caption("GroundWatch — MVP v1.1 — Reza Chash")
