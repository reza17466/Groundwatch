import streamlit as st
from src.data_fetch import fetch_dmi_precipitation

st.set_page_config(page_title="GroundWatch", page_icon="💧", layout="wide")

st.title("💧 GroundWatch")
st.subheader("پلتفرم پایش و پیش‌بینی سطح آب زیرزمینی")
st.caption("نسخه MVP — در حال توسعه")

st.divider()

st.header("🌧️ داده بارش کپنهاگ")

if st.button("دریافت داده ۳۰ روز گذشته"):
    with st.spinner("در حال دریافت داده..."):
        df = fetch_dmi_precipitation(days=30)

    if df.empty:
        st.error("داده‌ای دریافت نشد.")
    else:
        st.success(f"✅ {len(df)} رکورد دریافت شد")
        st.dataframe(df.tail(20))

        chart_data = df.set_index("timestamp")["precipitation_mm"]
        st.line_chart(chart_data)

st.divider()
st.caption("GroundWatch — MVP v0.1 — Reza Chash")
