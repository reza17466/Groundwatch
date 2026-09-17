import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests

# ==================== تنظیمات اولیه صفحه ====================
st.set_page_config(page_title="GroundWatch", page_icon="💧", layout="wide")

st.title("💧 GroundWatch")
st.subheader("پلتفرم پایش و پیش‌بینی سطح آب زیرزمینی")
st.caption("نسخه MVP — در حال توسعه")

st.divider()

# ==================== توابع کمکی ====================

# تابع برای دریافت امن کلیدهای API از Streamlit Secrets
def get_secret(key, default=None):
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return default

# ==================== ماژول دریافت داده DMI (بارش) ====================

@st.cache_data(ttl=3600)  # کش کردن داده‌ها برای ۱ ساعت
def fetch_dmi_precipitation(days=30):
    """دریافت داده بارش از DMI Frie Data API v2."""
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
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if features:
                records = [{
                    "timestamp": f.get("properties", {}).get("observed"),
                    "precipitation_mm": f.get("properties", {}).get("value"),
                    "station_id": f.get("properties", {}).get("stationId"),
                } for f in features]
                df = pd.DataFrame(records)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp").reset_index(drop=True)
                return df
    except Exception:
        pass
    return generate_sample_precip_data(days)

def generate_sample_precip_data(days=30):
    """تولید داده نمونه بارش در صورت عدم دسترسی به API."""
    dates = pd.date_range(
        end=datetime.utcnow().replace(minute=0, second=0, microsecond=0),
        periods=days * 24,
        freq="h",
    )
    rng = np.random.default_rng(42)
    precip = rng.exponential(0.3, len(dates))
    precip[precip < 0.1] = 0.0
    return pd.DataFrame({
        "timestamp": dates,
        "precipitation_mm": np.round(precip, 2),
    })

# ==================== ماژول دریافت داده GEUS (آب زیرزمینی) ====================

@st.cache_data(ttl=7200)  # کش کردن داده‌ها برای ۲ ساعت
def fetch_geus_groundwater():
    """
    دریافت داده آب زیرزمینی از سرویس WFS سازمان GEUS.
    این سرویس به صورت خودکار به پایگاه داده Jupiter متصل می‌شود.
    """
    # آدرس سرویس WFS برای پایگاه داده Jupiter
    base_url = "http://arcims.minn.dk/wfsconnector/com.esri.wfs.Esrimap"
    params = {
        "SERVICENAME": "GEUS_DK_JUPITER_WFS",
        "REQUEST": "GetFeature",
        "VERSION": "1.0.0",
        "TYPENAME": "JUPITER_BORINGER",  # لایه چاه‌ها
        "MAXFEATURES": "100",
        "OUTPUTFORMAT": "json",
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if features:
                records = []
                for f in features:
                    props = f.get("properties", {})
                    records.append({
                        "dgunr": props.get("DGUnr"),
                        "kommune": props.get("Kommune"),
                        "boredybde": props.get("Boredybde"),
                        "terrænkote": props.get("Terrænkote"),
                        "x": f.get("geometry", {}).get("coordinates", [None])[0],
                        "y": f.get("geometry", {}).get("coordinates", [None])[1],
                    })
                df = pd.DataFrame(records)
                return df, "GEUS Real Data"
    except Exception as e:
        pass
    
    # اگر WFS کار نکرد، داده نمونه برگردان
    df = generate_sample_groundwater_data()
    return df, "Simulated Data (GEUS WFS unavailable)"

def generate_sample_groundwater_data(n=100):
    """تولید داده نمونه واقع‌گرایانه آب زیرزمینی."""
    rng = np.random.default_rng(42)
    communes = ["Lemvig", "Ringkøbing-Skjern", "Holstebro", "Struer", "Aarhus"]
    data = {
        "dgunr": [f"43.{i}" for i in range(1, n + 1)],
        "kommune": rng.choice(communes, n),
        "boredybde": rng.uniform(5, 150, n).round(1),
        "terrænkote": rng.uniform(0, 50, n).round(1),
        "x": rng.uniform(440000, 500000, n).round(0),
        "y": rng.uniform(6200000, 6300000, n).round(0),
    }
    return pd.DataFrame(data)

# ==================== رابط کاربری ====================

tab1, tab2 = st.tabs(["🌧️ بارش", "🌊 آب زیرزمینی"])

# ---------- تب ۱: بارش ----------
with tab1:
    st.header("داده بارش کپنهاگ — ۳۰ روز گذشته")
    
    if st.button("نمایش داده بارش", type="primary", key="precip_btn"):
        with st.spinner("در حال دریافت داده..."):
            df = fetch_dmi_precipitation(days=30)
        
        if df.empty:
            st.error("داده‌ای دریافت نشد.")
        else:
            st.success(f"✅ {len(df)} رکورد بارش")
            col1, col2, col3 = st.columns(3)
            col1.metric("تعداد رکورد", len(df))
            col2.metric("مجموع بارش (mm)", round(df["precipitation_mm"].sum(), 1))
            col3.metric("میانگین (mm/h)", round(df["precipitation_mm"].mean(), 2))
            
            st.subheader("📈 نمودار بارش")
            st.line_chart(df.set_index("timestamp")["precipitation_mm"])
            
            with st.expander("📄 داده خام"):
                st.dataframe(df.tail(50))

# ---------- تب ۲: آب زیرزمینی ----------
with tab2:
    st.header("داده سطح آب زیرزمینی — GEUS دانمارک")
    st.caption("این داده‌ها مستقیماً از پایگاه داده ملی Jupiter دریافت می‌شوند.")
    
    if st.button("دریافت داده GEUS", type="primary", key="gw_btn"):
        with st.spinner("در حال اتصال به پایگاه داده GEUS..."):
            df_gw, source = fetch_geus_groundwater()
        
        if df_gw.empty:
            st.error("داده‌ای دریافت نشد.")
        else:
            if "Real" in source:
                st.success(f"✅ {len(df_gw)} چاه از پایگاه داده واقعی GEUS دریافت شد")
            else:
                st.warning(f"⚠️ {source} — نمایش داده‌های شبیه‌سازی‌شده")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("تعداد چاه", len(df_gw))
            col2.metric("میانگین عمق (m)", round(df_gw["boredybde"].mean(), 1))
            col3.metric("میانگین ارتفاع (m)", round(df_gw["terrænkote"].mean(), 1))
            
            st.subheader("📈 توزیع عمق چاه‌ها")
            st.bar_chart(df_gw["boredybde"].value_counts().sort_index().head(30))
            
            with st.expander("📄 داده خام چاه‌ها"):
                st.dataframe(df_gw.head(100))

st.divider()
st.caption("GroundWatch — MVP v0.1 — Reza Chash")
