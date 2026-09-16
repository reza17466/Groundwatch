import streamlit as st
from src.data_fetch import fetch_dmi_precipitation

st.set_page_config(page_title="GroundWatch", page_icon="💧", layout="wide")

st.title("💧 GroundWatch")
st.subheader("پلتفرم پایش و پیش‌بینی سطح آب زیرزمینی")

st.markdown("""
نسخه MVP — در حال توسعه
""")

st.divider()

# تست دریافت داده
st.header("🧪 تست دریافت داده از DMI")

if st.button("دریافت داده ۳۰ روز گذشته"):
    with st.spinner("در حال دریافت داده از DMI..."):
        df = fetch_dmi_precipitation(days=30)
    
    if df.empty:
        st.error("داده‌ای دریافت نشد. ممکن است API نیاز به تنظیم داشته باشد.")
    else:
        st.success(f"✅ {len(df)} رکورد دریافت شد")
        st.dataframe(df.head(20))
        st.line_chart(df.set_index("timestamp")["precipitation_mm"])

st.divider()
st.caption("GroundWatch — MVP v0.1 — Reza Chash")
