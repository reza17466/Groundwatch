"""
دریافت داده از منابع باز دانمارک
- DMI: داده‌های هواشناسی (بارش)
- اگر API جواب نداد، داده نمونه تولید می‌شود (برای توسعه)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

COPENHAGEN_STATION_ID = "06186"


def generate_sample_data(days: int = 30) -> pd.DataFrame:
    """تولید داده نمونه واقع‌گرایانه بارش برای توسعه."""
    dates = pd.date_range(end=datetime.utcnow(), periods=days * 24, freq="h")
    np.random.seed(42)
    precip = np.random.exponential(0.3, len(dates))
    precip[precip < 0.1] = 0
    return pd.DataFrame({
        "timestamp": dates,
        "precipitation_mm": precip.round(2),
        "station_id": "SAMPLE",
        "parameter_id": "precip_past1h",
    })


def fetch_dmi_precipitation(station_id: str = COPENHAGEN_STATION_ID, days: int = 30) -> pd.DataFrame:
    """
    دریافت داده بارش از DMI Frie Data API v2.
    اگر API جواب نداد، داده نمونه برمی‌گرداند.
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

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if features:
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
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp").reset_index(drop=True)
                print(f"✅ داده واقعی DMI دریافت شد: {len(df)} رکورد")
                return df
    except Exception as e:
        print(f"⚠️ خطا در API: {e}")

    # اگر API کار نکرد، داده نمونه
    print("⚠️ API در دسترس نیست — استفاده از داده نمونه")
    return generate_sample_data(days)


def save_to_csv(df: pd.DataFrame, filename: str) -> None:
    if df.empty:
        return
    path = DATA_DIR / filename
    df.to_csv(path, index=False)
    print(f"✅ داده ذخیره شد: {path}")
