import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from io import StringIO

st.set_page_config(page_title="GroundWatch", page_icon="💧", layout="wide")

st.title("💧 GroundWatch")
st.subheader("پلتفرم پایش و پیش‌بینی سطح آب زیرزمینی")
st.caption("نسخه MVP — در حال توسعه")

st.divider()

# ==================== توابع کمکی ====================

@st.cache_data(ttl=3600)
def fetch_geus_water_level_data():
    """
    دریافت داده‌های واقعی سطح آب زیرزمینی از سرویس WFS سازمان GEUS.
    """
    # سرویس WFS برای لایه اندازه‌گیری سطح آب (jupiter_pejlinger)
    wfs_url = "https://data.geus.dk/geusmap/ows/25832.jsp"
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAME": "jupiter_pejlinger",
        "OUTPUTFORMAT": "application/json",
        "COUNT": "2000",  # محدود کردن تعداد رکوردها برای سرعت
    }

    try:
        response = requests.get(wfs_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        if not features:
            return pd.DataFrame(), "empty"

        records = []
        for f in features:
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [None, None])

            records.append({
                "dgunr": props.get("dgunr"),
                "dato": props.get("dato"),
                "vandstand": props.get("kote"),  # سطح آب بر حسب متر
                "magasin": props.get("magasin"),
                "lon": coords[0] if len(coords) > 0 else None,
                "lat": coords[1] if len(coords) > 1 else None,
            })

        df = pd.DataFrame(records)

        if not df.empty and "dato" in df.columns:
            df["dato"] = pd.to_datetime(df["dato"], errors="coerce")
            df = df.dropna(subset=["dato"]).sort_values("dato", ascending=False)

        return df, "real"

    except Exception as e:
        return pd.DataFrame(), f"error: {str(e)}"


def generate_sample_groundwater_data(n=100):
    """تولید داده نمونه در صورت عدم دسترسی به سرویس GEUS."""
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
    st.info("ℹ️ این بخش هنوز به داده واقعی متصل نشده و از داده نمونه استفاده می‌کند.")

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

    if st.button("نمایش داده بارش", type="primary", key="precip_btn"):
        df = generate_sample_precip_data(30)
        col1, col2, col3 = st.columns(3)
        col1.metric("تعداد رکورد", len(df))
        col2.metric("مجموع بارش (mm)", round(df["precipitation_mm"].sum(), 1))
        col3.metric("میانگین (mm/h)", round(df["precipitation_mm"].mean(), 2))
        st.line_chart(df.set_index("timestamp")["precipitation_mm"])
        with st.expander("📄 داده خام"):
            st.dataframe(df.tail(50))

# ---------- تب ۲: آب زیرزمینی ----------
with tab2:
    st.header("داده سطح آب زیرزمینی — GEUS دانمارک")

    if st.button("دریافت داده واقعی از GEUS", type="primary", key="gw_btn"):
        with st.spinner("در حال اتصال به سرویس WFS سازمان GEUS..."):
            df_gw, status = fetch_geus_water_level_data()

        if status == "real" and not df_gw.empty:
            st.success(f"✅ {len(df_gw)} رکورد واقعی سطح آب از GEUS دریافت شد")

            col1, col2, col3 = st.columns(3)
            col1.metric("تعداد اندازه‌گیری", len(df_gw))
            if "vandstand" in df_gw.columns:
                col2.metric("میانگین سطح آب (m)", round(df_gw["vandstand"].mean(), 2))
                col3.metric("حداکثر سطح آب (m)", round(df_gw["vandstand"].max(), 2))

            # نقشه
            if "lat" in df_gw.columns and "lon" in df_gw.columns:
                map_data = df_gw[["lat", "lon"]].dropna()
                if not map_data.empty:
                    st.subheader("🗺️ نقشه نقاط اندازه‌گیری")
                    st.map(map_data)

            # نمودار سری زمانی
            if "dato" in df_gw.columns and "vandstand" in df_gw.columns:
                st.subheader("📈 روند سطح آب در زمان")
                chart_df = df_gw[["dato", "vandstand"]].dropna().set_index("dato")
                st.line_chart(chart_df["vandstand"])

            # توزیع سطح آب
            if "vandstand" in df_gw.columns:
                st.subheader("📊 توزیع سطح آب")
                st.bar_chart(df_gw["vandstand"].value_counts().sort_index().head(30))

            with st.expander("📄 داده خام"):
                st.dataframe(df_gw.head(100))

        else:
            st.warning(f"⚠️ سرویس GEUS در دسترس نیست ({status}) — نمایش داده نمونه")
            df_gw = generate_sample_groundwater_data()
            col1, col2, col3 = st.columns(3)
            col1.metric("تعداد چاه (نمونه)", len(df_gw))
            col2.metric("میانگین عمق (m)", round(df_gw["boredybde"].mean(), 1))
            col3.metric("میانگین ارتفاع (m)", round(df_gw["terrænkote"].mean(), 1))
            st.map(df_gw[["lat", "lon"]].dropna())
            with st.expander("📄 داده خام"):
                st.dataframe(df_gw.head(100))

# ---------- تب ۳: پیش‌بینی و هشدار ----------
with tab3:
    st.header("پیش‌بینی و هشدار زودهنگام")

    st.subheader("⚙️ تنظیمات هشدار")
    threshold = st.slider("حد هشدار سطح آب (متر زیر زمین)", 0.5, 10.0, 2.0, 0.5)

    st.subheader("🔮 پیش‌بینی ۷ روزه")
    st.info("ℹ️ این بخش هنوز به مدل پیش‌بینی واقعی متصل نشده است.")

    rng = np.random.default_rng(42)
    days = 30
    historical = rng.uniform(1.5, 3.0, days) + np.linspace(0, 0.5, days)
    forecast_days = 7
    forecast = historical[-1] + np.cumsum(rng.normal(0.05, 0.1, forecast_days))

    all_dates = pd.date_range(end=datetime.utcnow(), periods=days + forecast_days, freq="D")
    all_values = np.concatenate([historical, forecast])

    df_forecast = pd.DataFrame({"date": all_dates, "water_level_m": all_values})
    st.line_chart(df_forecast.set_index("date")["water_level_m"])

    st.subheader("🚨 وضعیت هشدار")
    if forecast[-1] > threshold:
        st.error(f"⚠️ هشدار: سطح آب پیش‌بینی‌شده ({forecast[-1]:.2f} m) از حد مجاز ({threshold} m) عبور کرده است!")
    else:
        st.success(f"✅ وضعیت عادی: سطح آب پیش‌بینی‌شده ({forecast[-1]:.2f} m) زیر حد هشدار ({threshold} m) است.")

    col1, col2, col3 = st.columns(3)
    col1.metric("سطح فعلی (m)", round(historical[-1], 2))
    col2.metric("پیش‌بینی ۷ روزه (m)", round(forecast[-1], 2))
    col3.metric("تغییر (m)", round(forecast[-1] - historical[-1], 2))

st.divider()
st.caption("GroundWatch — MVP v0.3 — Reza Chash")
