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


def fetch_dmi_precipitation(station_id: str = "06186", days: int = 30) -> pd.DataFrame:
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
            print("⚠️ پاسخ خالی است.")
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
        print("❌ خطا: درخواست به DMI timeout شد.")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ خطا: {type(e).__name__}: {e}")
        return pd.DataFrame()


def save_to_csv(df: pd.DataFrame, filename: str) -> None:
    if df.empty:
        return
    path = DATA_DIR / filename
    df.to_csv(path, index=False)
    print(f"✅ داده ذخیره شد: {path}")


if __name__ == "__main__":
    df = fetch_dmi_precipitation(days=30)
    if not df.empty:
        print(df.head())
        save_to_csv(df, "dmi_precipitation.csv")
