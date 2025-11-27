import requests
import pandas as pd

API_KEY = "09b66b708922401fb2c8e85cbca68b80"

SYMBOL = "XAU/USD"
INTERVAL = "15min"
START_DATE = "2025-11-01 00:00:00"
END_DATE   = "2025-11-27 23:59:59"
OUT_FILE   = "XAUUSD_15m_2025-11-01_2025-11-27.csv"

def main():
    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "apikey": API_KEY,
        "outputsize": 5000,
        "format": "JSON"
    }

    print("Requesting data from Twelve Data...")
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    if "values" not in data:
        raise SystemExit(f"API error: {data}")

    values = data["values"]
    df = pd.DataFrame(values)

    # required columns except volume
    required = ["datetime", "open", "high", "low", "close"]
    for col in required:
        if col not in df.columns:
            raise SystemExit(f"Missing column: {col}")

    # if volume missing, create it
    if "volume" not in df.columns:
        df["volume"] = 0

    df = df.rename(columns={"datetime": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df = df.sort_values("timestamp").reset_index(drop=True)

    df.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(df)} rows to {OUT_FILE}")

if __name__ == "__main__":
    main()
