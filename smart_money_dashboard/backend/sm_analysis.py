from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np


def load_ohlcv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # core columns must exist
    required_cols = ["timestamp", "open", "high", "low", "close"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in CSV: {missing}")

    # if volume is missing, create dummy zero volume
    if "volume" not in df.columns:
        df["volume"] = 0

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df.drop_duplicates(subset=["timestamp"])
    return df


def detect_swings(df: pd.DataFrame, window: int = 2) -> pd.DataFrame:
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)
    swing_high = np.zeros(n, dtype=bool)
    swing_low = np.zeros(n, dtype=bool)

    for i in range(window, n - window):
        local_highs = highs[i - window:i + window + 1]
        if highs[i] == local_highs.max():
            swing_high[i] = True

        local_lows = lows[i - window:i + window + 1]
        if lows[i] == local_lows.min():
            swing_low[i] = True

    df = df.copy()
    df["swing_high"] = swing_high
    df["swing_low"] = swing_low
    return df


def detect_structure(df: pd.DataFrame, buffer_factor: float = 0.0002) -> Dict[str, Any]:
    last_swing_high = None
    last_swing_low = None
    bos_events: List[Dict[str, Any]] = []
    structure_points: List[Dict[str, Any]] = []
    trend = "range"

    for i, row in df.iterrows():
        if row.get("swing_high"):
            last_swing_high = (i, row["high"])
            structure_points.append({
                "index": int(i),
                "type": "swing_high",
                "price": float(row["high"]),
                "timestamp": pd.Timestamp(row["timestamp"]).isoformat()
            })

        if row.get("swing_low"):
            last_swing_low = (i, row["low"])
            structure_points.append({
                "index": int(i),
                "type": "swing_low",
                "price": float(row["low"]),
                "timestamp": pd.Timestamp(row["timestamp"]).isoformat()
            })

        close_price = row["close"]
        price_buffer = close_price * buffer_factor

        if last_swing_high is not None and close_price > last_swing_high[1] + price_buffer:
            bos_events.append({
                "index": int(i),
                "type": "bullish_bos",
                "reference_index": int(last_swing_high[0]),
                "reference_price": float(last_swing_high[1]),
                "price": float(close_price),
                "timestamp": pd.Timestamp(row["timestamp"]).isoformat()
            })
            trend = "uptrend"

        if last_swing_low is not None and close_price < last_swing_low[1] - price_buffer:
            bos_events.append({
                "index": int(i),
                "type": "bearish_bos",
                "reference_index": int(last_swing_low[0]),
                "reference_price": float(last_swing_low[1]),
                "price": float(close_price),
                "timestamp": pd.Timestamp(row["timestamp"]).isoformat()
            })
            trend = "downtrend"

    choch_events: List[Dict[str, Any]] = []
    last_bos_type = None
    for event in bos_events:
        if last_bos_type is None:
            last_bos_type = event["type"]
            continue

        if "bullish" in last_bos_type and "bearish" in event["type"]:
            choch_events.append({**event, "type": "bearish_choch"})
        if "bearish" in last_bos_type and "bullish" in event["type"]:
            choch_events.append({**event, "type": "bullish_choch"})

        last_bos_type = event["type"]

    if bos_events:
        last_bos = bos_events[-1]
        if "bullish" in last_bos["type"]:
            trend = "uptrend"
        elif "bearish" in last_bos["type"]:
            trend = "downtrend"
    else:
        trend = "range"

    return {
        "trend": trend,
        "bos_events": bos_events,
        "choch_events": choch_events,
        "structure_points": structure_points
    }


def map_liquidity(df: pd.DataFrame, tolerance_factor: float = 0.0002) -> List[Dict[str, Any]]:
    highs = df["high"].values
    lows = df["low"].values
    timestamps = df["timestamp"].values
    liquidity_levels: List[Dict[str, Any]] = []

    n = len(df)
    for i in range(1, n):
        price_h = highs[i]
        tol_h = price_h * tolerance_factor
        if abs(highs[i] - highs[i - 1]) <= tol_h:
            liquidity_levels.append({
                "type": "EQH",
                "price": float(price_h),
                "index_a": int(i - 1),
                "index_b": int(i),
                "timestamp_a": pd.Timestamp(timestamps[i - 1]).isoformat(),
                "timestamp_b": pd.Timestamp(timestamps[i]).isoformat()
            })

        price_l = lows[i]
        tol_l = price_l * tolerance_factor
        if abs(lows[i] - lows[i - 1]) <= tol_l:
            liquidity_levels.append({
                "type": "EQL",
                "price": float(price_l),
                "index_a": int(i - 1),
                "index_b": int(i),
                "timestamp_a": pd.Timestamp(timestamps[i - 1]).isoformat(),
                "timestamp_b": pd.Timestamp(timestamps[i]).isoformat()
            })

    return liquidity_levels


def find_fvgs(df: pd.DataFrame, min_gap: float = 2.5) -> List[Dict[str, Any]]:
    """
    Detect fair value gaps and filter out tiny micro gaps.
    min_gap is the minimum gap size in price units.
    For gold on 15 minute candles, values around 2 to 3 are reasonable.
    """
    highs = df["high"].values
    lows = df["low"].values
    timestamps = df["timestamp"].values
    fvgs: List[Dict[str, Any]] = []

    n = len(df)
    for i in range(0, n - 2):

        # bullish FVG: candle C low is above candle A high
        if lows[i + 2] > highs[i]:
            gap_low = float(highs[i])
            gap_high = float(lows[i + 2])
            gap_size = gap_high - gap_low
            if gap_size >= min_gap:
                center = (gap_high + gap_low) / 2.0
                fvgs.append({
                    "type": "bullish",
                    "index_a": int(i),
                    "index_c": int(i + 2),
                    "gap_low": gap_low,
                    "gap_high": gap_high,
                    "center": center,
                    "timestamp_a": pd.Timestamp(timestamps[i]).isoformat(),
                    "timestamp_c": pd.Timestamp(timestamps[i + 2]).isoformat()
                })

        # bearish FVG: candle C high is below candle A low
        if highs[i + 2] < lows[i]:
            gap_high = float(lows[i])
            gap_low = float(highs[i + 2])
            gap_size = gap_high - gap_low
            if gap_size >= min_gap:
                center = (gap_high + gap_low) / 2.0
                fvgs.append({
                    "type": "bearish",
                    "index_a": int(i),
                    "index_c": int(i + 2),
                    "gap_low": gap_low,
                    "gap_high": gap_high,
                    "center": center,
                    "timestamp_a": pd.Timestamp(timestamps[i]).isoformat(),
                    "timestamp_c": pd.Timestamp(timestamps[i + 2]).isoformat()
                })

    return fvgs


def compute_major_swing(df: pd.DataFrame) -> Tuple[float, float]:
    recent = df.tail(200)
    swing_low = recent["low"].min()
    swing_high = recent["high"].max()
    return float(swing_low), float(swing_high)


def compute_premium_discount(df: pd.DataFrame) -> Dict[str, Any]:
    swing_low, swing_high = compute_major_swing(df)
    current_price = float(df["close"].iloc[-1])
    mid = (swing_high + swing_low) / 2.0
    if swing_high == swing_low:
        fraction = 0.5
    else:
        fraction = (current_price - swing_low) / (swing_high - swing_low)
    fraction = max(0.0, min(1.0, fraction))
    zone = "equilibrium"
    if current_price < mid:
        zone = "discount"
    if current_price > mid:
        zone = "premium"
    return {
        "swing_low": swing_low,
        "swing_high": swing_high,
        "mid": mid,
        "current_price": current_price,
        "zone": zone,
        "discount_fraction": fraction
    }


def detect_displacement(df: pd.DataFrame, threshold: float = 0.75) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    for i, row in df.iterrows():
        body_size = abs(row["close"] - row["open"])
        range_size = row["high"] - row["low"]
        if range_size <= 0:
            continue
        ratio = body_size / range_size
        if ratio > threshold:
            direction = "bullish" if row["close"] > row["open"] else "bearish"
            flags.append({
                "index": int(i),
                "ratio": float(ratio),
                "direction": direction,
                "timestamp": pd.Timestamp(row["timestamp"]).isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"])
            })
    return flags


def generate_bias(structure_info: Dict[str, Any],
                  premium_discount: Dict[str, Any],
                  liquidity: List[Dict[str, Any]],
                  fvgs: List[Dict[str, Any]],
                  displacement_flags: List[Dict[str, Any]]) -> Dict[str, Any]:

    trend = structure_info.get("trend", "range")
    zone = premium_discount.get("zone", "equilibrium")
    last_displacement = displacement_flags[-1] if displacement_flags else None

    score = 0.0
    explanation_parts: List[str] = []

    if trend == "uptrend":
        score += 1.0
        explanation_parts.append("Last BOS suggests an uptrend")
    elif trend == "downtrend":
        score -= 1.0
        explanation_parts.append("Last BOS suggests a downtrend")

    if zone == "discount":
        score += 0.7
        explanation_parts.append("Price trades in discount")
    elif zone == "premium":
        score -= 0.7
        explanation_parts.append("Price trades in premium")

    if liquidity:
        if trend == "uptrend":
            score += 0.3
            explanation_parts.append("Liquidity likely resting above recent highs")
        elif trend == "downtrend":
            score -= 0.3
            explanation_parts.append("Liquidity likely resting below recent lows")

    if fvgs:
        last_fvg = fvgs[-1]
        if last_fvg["type"] == "bullish":
            score += 0.3
            explanation_parts.append("Recent bullish FVG")
        else:
            score -= 0.3
            explanation_parts.append("Recent bearish FVG")

    if last_displacement:
        if last_displacement["direction"] == "bullish":
            score += 0.5
            explanation_parts.append("Recent bullish displacement candle")
        else:
            score -= 0.5
            explanation_parts.append("Recent bearish displacement candle")

    if score > 0.8:
        bias = "strong_bullish"
    elif score > 0.2:
        bias = "bullish"
    elif score < -0.8:
        bias = "strong_bearish"
    elif score < -0.2:
        bias = "bearish"
    else:
        bias = "neutral"

    return {
        "bias": bias,
        "score": score,
        "explanation": explanation_parts
    }


def build_ohlcv_payload(df: pd.DataFrame, limit: int = 300) -> list:
    recent = df.tail(limit)
    out: List[Dict[str, Any]] = []
    for _, row in recent.iterrows():
        out.append({
            "time": pd.Timestamp(row["timestamp"]).isoformat(),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row.get("volume", 0))
        })
    return out


def generate_trade_setups(structure_info: Dict[str, Any],
                          premium_discount: Dict[str, Any],
                          liquidity: List[Dict[str, Any]],
                          fvgs: List[Dict[str, Any]],
                          current_price: float,
                          max_setups: int = 3) -> List[Dict[str, Any]]:
    """
    Build simple rule based trade ideas from the existing smart money context.
    Two base models:
      long: uptrend, discount, bullish FVG
      short: downtrend, premium, bearish FVG
    """

    trend = structure_info.get("trend", "range")
    zone = premium_discount.get("zone", "equilibrium")

    setups: List[Dict[str, Any]] = []

    if not fvgs:
        return setups

    def nearest_liquidity(direction: str) -> Optional[float]:
        if not liquidity:
            return None
        if direction == "up":
            higher = [l["price"] for l in liquidity if l["price"] > current_price]
            return min(higher) if higher else None
        else:
            lower = [l["price"] for l in liquidity if l["price"] < current_price]
            return max(lower) if lower else None

    # walk through recent fvgs from newest backwards
    for fvg in reversed(fvgs[-10:]):
        mid = (fvg["gap_high"] + fvg["gap_low"]) / 2.0
        direction: Optional[str] = None
        rationale: List[str] = []
        entry = mid
        stop: float
        tp1: float
        tp2: float

        # bullish model
        if trend == "uptrend" and zone == "discount" and fvg["type"] == "bullish":
            direction = "long"
            stop = fvg["gap_low"]
            risk = entry - stop
            if risk <= 0:
                continue
            liq_target = nearest_liquidity("up")
            if liq_target is None:
                liq_target = entry + 2 * risk
            tp1 = liq_target
            tp2 = entry + 2 * risk
            rationale.extend([
                "Uptrend structure (bullish BOS)",
                "Price trades in discount",
                "Recent bullish FVG below or near price"
            ])

        # bearish model
        elif trend == "downtrend" and zone == "premium" and fvg["type"] == "bearish":
            direction = "short"
            stop = fvg["gap_high"]
            risk = stop - entry
            if risk <= 0:
                continue
            liq_target = nearest_liquidity("down")
            if liq_target is None:
                liq_target = entry - 2 * risk
            tp1 = liq_target
            tp2 = entry - 2 * risk
            rationale.extend([
                "Downtrend structure (bearish BOS)",
                "Price trades in premium",
                "Recent bearish FVG above or near price"
            ])
        else:
            continue

        rr1 = (tp1 - entry) / risk if direction == "long" else (entry - tp1) / risk
        rr2 = (tp2 - entry) / risk if direction == "long" else (entry - tp2) / risk

        setups.append({
            "direction": direction,
            "entry": entry,
            "stop": stop,
            "tp1": tp1,
            "tp2": tp2,
            "risk_per_unit": risk,
            "rr_tp1": rr1,
            "rr_tp2": rr2,
            "fvg_type": fvg["type"],
            "fvg_gap_low": fvg["gap_low"],
            "fvg_gap_high": fvg["gap_high"],
            "timestamp_a": fvg["timestamp_a"],
            "timestamp_c": fvg["timestamp_c"],
            "rationale": rationale,
        })

        if len(setups) >= max_setups:
            break

    return setups


def analyze(csv_path: str) -> Dict[str, Any]:
    df = load_ohlcv(csv_path)
    df = detect_swings(df, window=2)
    structure_info = detect_structure(df)
    liquidity = map_liquidity(df)
    fvgs = find_fvgs(df, min_gap=5)
    premium_discount = compute_premium_discount(df)
    displacement_flags = detect_displacement(df)
    bias_info = generate_bias(structure_info, premium_discount, liquidity, fvgs, displacement_flags)
    ohlcv_payload = build_ohlcv_payload(df)

    current_price = float(df["close"].iloc[-1])
    trade_setups = generate_trade_setups(
        structure_info,
        premium_discount,
        liquidity,
        fvgs,
        current_price,
    )

    return {
        "bias": bias_info["bias"],
        "bias_score": bias_info["score"],
        "bias_explanation": bias_info["explanation"],
        "premium_discount": premium_discount["zone"],
        "discount_fraction": premium_discount["discount_fraction"],
        "major_swing": {
            "swing_low": premium_discount["swing_low"],
            "swing_high": premium_discount["swing_high"],
            "mid": premium_discount["mid"]
        },
        "liquidity_levels": liquidity,
        "fair_value_gaps": fvgs,
        "structure_points": structure_info["structure_points"],
        "bos_events": structure_info["bos_events"],
        "choch_events": structure_info["choch_events"],
        "fvg_count": len(fvgs),
        "displacement_flags": displacement_flags,
        "ohlcv": ohlcv_payload,
        "trade_setups": trade_setups,
    }
