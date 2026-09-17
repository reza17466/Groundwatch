"""
دریافت داده از منابع باز دانمارک
- تلاش برای API واقعی DMI
- در صورت شکست، داده شبیه‌سازی‌شده واقع‌گرایانه
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
    """تولید داده نمونه واقع‌گرایانه بارش."""
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
        "station_id": "SAMPLE-DATA",
        "parameter_id": "precip_past1h",
    })


def fetch_dmi_precipitation(station_id: str = COPENHAGEN_STATION_ID, days: int = 30) -> pd.DataFrame:
    """تلاش برای دریافت داده واقعی، در غیر این صورت داده نمونه."""
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
        response = requests.get(url, params=params, timeout=15)
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
                return df
    except Exception:
        pass

    # Fallback: داده نمونه
    return generate_sample_data(days)


def save_to_csv(df: pd.DataFrame, filename: str) -> None:
    if df.empty:
        return
    path = DATA_DIR / filename
    df.to_csv(path, index=False)
