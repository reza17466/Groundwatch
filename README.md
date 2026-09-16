# GroundWatch

پلتفرم هشدار زودهنگام و پیش‌بینی سطح آب زیرزمینی با استفاده از داده‌های باز (GEUS, DMI) و سنسورهای محلی.

## مشکل
سطح آب زیرزمینی در دانمارک از سال ۱۹۸۸ بیش از یک متر بالا آمده و به زیرساخت‌ها، ساختمان‌ها و کشاورزی آسیب می‌زند.

## راه‌حل
یک داشبورد SaaS که:
- سطح آب را روی نقشه نمایش می‌دهد
- ۷ روز آینده را پیش‌بینی می‌کند
- وقتی از حد خطر عبور کرد، هشدار می‌دهد
- گزارش PDF برای شهرداری تولید می‌کند

## منابع داده
- GEUS Jupiter
- GEUS Sensornet
- DMI Frie Data
- VandA (Miljøportal)

## پشته فناوری
- Python + Streamlit
- Pandas + Plotly
- Prophet / ARIMA
- n8n برای هشدار

## نحوه اجرا
```bash
pip install -r requirements.txt
streamlit run app.pyw
