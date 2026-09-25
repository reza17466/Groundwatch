import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="GroundWatch", page_icon="💧", layout="wide")

st.title("💧 GroundWatch")
st.subheader("پلتفرم پایش و پیش‌بینی سطح آب زیرزمینی")
st.caption("نسخه MVP — در حال توسعه")

st.divider()

# ==================== توابع کمکی ====================

def generate_sample_precip_data(days=30):
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

def generate_sample_groundwater_data(n=100):
    rng = np.random.default_rng(42)
    communes = ["Lemvig", "Ringkøbing-Skjern", "Holstebro", "Struer", "Aarhus"]
    return pd.DataFrame({
        "dgunr": [f"43.{i}" for i in range(1, n + 1)],
        "kommune": rng.choice(communes, n),
        "boredybde": rng.uniform(5, 150, n).round(1),
        "terrænkote": rng.uniform(0, 50, n).round(1),
        "lat": rng.uniform(55.5, 57.0, n).round(4),
        "lon": rng.uniform(8.0, 10.5, n).round(4),
        "water_level_m": rng.uniform(0.5, 5.0, n).round(2),
    })

# ==================== تب‌ها ====================

tab1, tab2, tab3 = st.tabs(["🌧️ بارش", "🌊 آب زیرزمینی", "🔮 پیش‌بینی و هشدار"])

# ---------- تب ۱: بارش ----------
with tab1:
    st.header("داده بارش — ۳۰ روز گذشته")
    
    uploaded_precip = st.file_uploader(
        "آپلود فایل CSV بارش (اختیاری)", type=["csv"], key="precip_upload"
    )
    
    if st.button("نمایش داده بارش", type="primary", key="precip_btn"):
        if uploaded_precip is not None:
            try:
                df = pd.read_csv(uploaded_precip)
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                st.success(f"✅ {len(df)} رکورد از فایل آپلود شده")
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")
                df = generate_sample_precip_data(30)
                st.warning("⚠️ داده شبیه‌سازی‌شده استفاده شد")
        else:
            df = generate_sample_precip_data(30)
            st.info("ℹ️ داده شبیه‌سازی‌شده — برای داده واقعی، CSV آپلود کنید")
        
        if not df.empty and "precipitation_mm" in df.columns:
            col1, col2, col3 = st.columns(3)
            col1.metric("تعداد رکورد", len(df))
            col2.metric("مجموع بارش (mm)", round(df["precipitation_mm"].sum(), 1))
            col3.metric("میانگین (mm/h)", round(df["precipitation_mm"].mean(), 2))
            
            st.subheader("📈 نمودار بارش")
            if "timestamp" in df.columns:
                st.line_chart(df.set_index("timestamp")["precipitation_mm"])
            else:
                st.line_chart(df["precipitation_mm"])
            
            with st.expander("📄 داده خام"):
                st.dataframe(df.tail(50))

# ---------- تب ۲: آب زیرزمینی ----------
with tab2:
    st.header("داده سطح آب زیرزمینی — GEUS دانمارک")
    
    uploaded_gw = st.file_uploader(
        "آپلود فایل CSV آب زیرزمینی (اختیاری)", type=["csv"], key="gw_upload"
    )
    
    if st.button("نمایش داده آب زیرزمینی", type="primary", key="gw_btn"):
        if uploaded_gw is not None:
            try:
                df_gw = pd.read_csv(uploaded_gw)
                st.success(f"✅ {len(df_gw)} رکورد از فایل آپلود شده")
                source = "uploaded"
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")
                df_gw = generate_sample_groundwater_data()
                source = "sample"
        else:
            df_gw = generate_sample_groundwater_data()
            source = "sample"
        
        if source == "sample":
            st.info("ℹ️ داده شبیه‌سازی‌شده — برای داده واقعی، CSV آپلود کنید")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("تعداد چاه", len(df_gw))
        if "boredybde" in df_gw.columns:
            col2.metric("میانگین عمق (m)", round(df_gw["boredybde"].mean(), 1))
        if "terrænkote" in df_gw.columns:
            col3.metric("میانگین ارتفاع (m)", round(df_gw["terrænkote"].mean(), 1))
        
        # نقشه
        if "lat" in df_gw.columns and "lon" in df_gw.columns:
            st.subheader("🗺️ نقشه چاه‌ها")
            st.map(df_gw[["lat", "lon"]].dropna())
        
        # نمودار
        if "boredybde" in df_gw.columns:
            st.subheader("📈 توزیع عمق چاه‌ها")
            st.bar_chart(df_gw["boredybde"].value_counts().sort_index().head(30))
        
        with st.expander("📄 داده خام چاه‌ها"):
            st.dataframe(df_gw.head(100))

# ---------- تب ۳: پیش‌بینی و هشدار ----------
with tab3:
    st.header("پیش‌بینی و هشدار زودهنگام")
    
    st.subheader("⚙️ تنظیمات هشدار")
    threshold = st.slider(
        "حد هشدار سطح آب (متر زیر زمین)", 0.5, 10.0, 2.0, 0.5
    )
    
    st.subheader("🔮 پیش‌بینی ۷ روزه")
    
    rng = np.random.default_rng(42)
    days = 30
    historical = rng.uniform(1.5, 3.0, days)
    trend = np.linspace(0, 0.5, days)
    historical = historical + trend
    
    forecast_days = 7
    last_value = historical[-1]
    forecast = last_value + np.cumsum(rng.normal(0.05, 0.1, forecast_days))
    
    all_dates = pd.date_range(end=datetime.utcnow(), periods=days + forecast_days, freq="D")
    all_values = np.concatenate([historical, forecast])
    
    df_forecast = pd.DataFrame({
        "date": all_dates,
        "water_level_m": all_values,
    })
    
    st.line_chart(df_forecast.set_index("date")["water_level_m"])
    
    st.subheader("🚨 وضعیت هشدار")
    if forecast[-1] > threshold:
        st.error(
            f"⚠️ هشدار: سطح آب زیرزمینی پیش‌بینی‌شده "
            f"({forecast[-1]:.2f} m) از حد مجاز ({threshold} m) عبور کرده است!"
        )
    else:
        st.success(
            f"✅ وضعیت عادی: سطح آب پیش‌بینی‌شده "
            f"({forecast[-1]:.2f} m) زیر حد هشدار ({threshold} m) است."
        )
    
    st.subheader("📊 خلاصه پیش‌بینی")
    col1, col2, col3 = st.columns(3)
    col1.metric("سطح فعلی (m)", round(historical[-1], 2))
    col2.metric("پیش‌بینی ۷ روزه (m)", round(forecast[-1], 2))
    col3.metric("تغییر (m)", round(forecast[-1] - historical[-1], 2))

st.divider()
st.caption("GroundWatch — MVP v0.2 — Reza Chash")
