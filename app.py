import streamlit as st

# تنظیمات صفحه
st.set_page_config(
    page_title="GroundWatch",
    page_icon="💧",
    layout="wide",
)

# عنوان
st.title("💧 GroundWatch")
st.subheader("پلتفرم پایش و پیش‌بینی سطح آب زیرزمینی")

# توضیح
st.markdown("""
این یک نسخه MVP است. در نسخه‌های بعدی، این داشبورد شامل موارد زیر خواهد بود:

- 🗺️ **نقشه چاه‌ها**: نمایش سطح آب روی نقشه دانمارک
- 📈 **نمودار تاریخی**: روند سطح آب در ۵ سال گذشته
- 🔮 **پیش‌بینی ۷ روزه**: با استفاده از داده‌های بارش و دما
- 🚨 **هشدار خودکار**: وقتی سطح از حد خطر عبور کند
- 📄 **گزارش PDF**: برای ارائه به شهرداری
""")

# بخش داده
st.divider()
st.header("منابع داده")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🌍 GEUS")
    st.caption("داده‌های چاه‌ها و سطح آب زیرزمینی دانمارک")

with col2:
    st.markdown("### ☁️ DMI")
    st.caption("داده‌های هواشناسی و بارش")

with col3:
    st.markdown("### 📡 VandA")
    st.caption("سری‌های زمانی سطح آب")

# فوتر
st.divider()
st.caption("GroundWatch — MVP v0.1 — ساخته‌شده توسط Reza Chash")
