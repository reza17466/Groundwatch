import streamlit as st
import pandas as pd
from src.data_fetch import fetch_dmi_precipitation

st.set_page_config(page_title="GroundWatch", page_icon="💧", layout="wide")

st.title("💧 GroundWatch")
st.subheader("پلتفرم پایش و پیش‌بینی سطح آب زیرزمینی")
st.caption("نسخه MVP — در حال توسعه")

st.divider()

st.header("🌧️ داده بارش کپنهاگ")

if st.button("دریافت داده ۳۰ روز گذشته", type="primary"):
    with st.spinner("در حال دریافت داده..."):
        df = fetch_dmi_precipitation(days=30)

    if df.empty:
        st.error("داده‌ای دریافت نشد.")
    else:
        source = df["station_id"].iloc[0]
        if source == "SAMPLE-DATA":
            st.warning("⚠️ داده شبیه‌سازی‌شده (API واقعی در دسترس نیست)")
        else:
            st.success(f"✅ داده واقعی DMI — {len(df)} رکورد")

        col1, col2, col3 = st.columns(3)
        col1.metric("تعداد رکورد", len(df))
        col2.metric("مجموع بارش (mm)", round(df["precipitation_mm"].sum(), 1))
        col3.metric("میانگین (mm/h)", round(df["precipitation_mm"].mean(), 2))

        st.subheader("📈 نمودار بارش")
        chart_data = df.set_index("timestamp")["precipitation_mm"]
        st.line_chart(chart_data)

        with st.expander("📄 مشاهده داده خام"):
            st.dataframe(df.tail(50))

st.divider()
st.caption("GroundWatch — MVP v0.1 — Reza Chash")
