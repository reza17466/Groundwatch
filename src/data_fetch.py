"""
دریافت داده از منابع باز دانمارک
- DMI: داده‌های هواشناسی (بارش، دما)
- GEUS: داده‌های سطح آب زیرزمینی (در نسخه بعدی)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# شناسه ایستگاه هواشناسی کپنهاگ
COPENHAGEN_STATION_ID = "06186"


def fetch_dmi_precipitation(station_id: str = COPENHAGEN_STATION_ID, days: int = 30) -> pd.DataFrame:
    """
    دریافت داده بارش از DMI Frie Data API v2.
    از دسامبر ۲۰۲۵ نیازی به API Key نیست.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    datetime_range = (
        f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/"
        f"{end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )

    # ✅ آدرس صحیح و جدید (بدون احراز هویت)
    url = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"
    params = {
        "stationId": station_id,
        "parameterId": "precip_past1h",
        "datetime": datetime_range,
        "limit": 1000,
    }

    print(f"🔍 درخواست به: {url}")
    print(f"📋 پارامترها: {params}")

    try:
        response = requests.get(url, params=params, timeout=60)
        print(f"📡 وضعیت پاسخ: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ خطای HTTP: {response.status_code}")
            print(f"📄 متن پاسخ: {response.text[:500]}")
            return pd.DataFrame()

        data = response.json()
        features = data.get("features", [])
        print(f"✅ تعداد رکورد دریافت‌شده: {len(features)}")

        if not features:
            print("⚠️ پاسخ خالی است. ممکن است پارامترها اشتباه باشند.")
            return pd.DataFrame()

        records = []
        for feature in features:
            props = feature.get("properties", {})
            records.append({
                "timestamp": props.get("observed"),
                "precipitation_mm": props.get("value"),
                "station_id": props.get("stationId"),
                "parameter_id": props.get("parameterId"),
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
            print(f"📊 تعداد رکورد نهایی: {len(df)}")

        return df

    except requests.exceptions.Timeout:
        print("❌ خطا: درخواست به DMI timeout شد (۶۰ ثانیه).")
        return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        print("❌ خطا: اتصال به DMI برقرار نشد.")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {type(e).__name__}: {e}")
        return pd.DataFrame()


def save_to_csv(df: pd.DataFrame, filename: str) -> None:
    """ذخیره DataFrame در فایل CSV"""
    if df.empty:
        print("داده‌ای برای ذخیره وجود ندارد.")
        return

    path = DATA_DIR / filename
    df.to_csv(path, index=False)
    print(f"✅ داده در {path} ذخیره شد ({len(df)} رکورد)")


if __name__ == "__main__":
    print("🌧️ دریافت داده بارش از DMI...")
    df = fetch_dmi_precipitation(days=30)

    if not df.empty:
        print(df.head())
        print(f"\nتعداد رکورد: {len(df)}")
        save_to_csv(df, "dmi_precipitation.csv")
    else:
        print("⚠️ داده‌ای دریافت نشد. متن خطاهای بالا را بررسی کن.")
