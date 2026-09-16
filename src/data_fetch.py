"""
دریافت داده از منابع باز دانمارک
- DMI: داده‌های هواشناسی (بارش، دما)
- GEUS: داده‌های سطح آب زیرزمینی (در نسخه بعدی)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


# مسیر ذخیره داده
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def fetch_dmi_precipitation(station_id: str = "06186", days: int = 30) -> pd.DataFrame:
    """
    دریافت داده بارش از DMI Frie Data API (نسخه ۲).
    
    Args:
        station_id: شناسه ایستگاه هواشناسی (پیش‌فرض: 06186 = Copenhagen)
        days: تعداد روزهای گذشته
    
    Returns:
        DataFrame با ستون‌های timestamp و precipitation_mm
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    
    # DMI Frie Data API v2 - Open Data (بدون نیاز به احراز هویت)
    url = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"
    params = {
        "stationId": station_id,
        "parameterId": "precip_past1h",
        "datetime": f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "limit": 1000,
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # استخراج داده‌ها
        records = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            records.append({
                "timestamp": props.get("observed"),
                "precipitation_mm": props.get("value"),
                "station_id": props.get("stationId"),
            })
        
        df = pd.DataFrame(records)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"خطا در دریافت داده DMI: {e}")
        return pd.DataFrame()
    except KeyError as e:
        print(f"خطا در ساختار داده: {e}")
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
        print("⚠️ داده‌ای دریافت نشد. ممکن است API تغییر کرده باشد.")
        print("بررسی کن: https://www.dmi.dk/friedata")
