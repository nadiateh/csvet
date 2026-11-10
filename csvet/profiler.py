import pandas as pd
import re
from collections import Counter
import json
from pathlib import Path
import math

from csvet.privacy import mask_profile

NULL_TOKENS = {"", "na", "n/a", "null", "none", "nan", "-", "?", "unknown"}
MAX_CATEGORY_VAULES = 30

def load_raw_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")

def is_null_like(value):
    return value.strip().lower() in NULL_TOKENS

def value_shape(value):
    shape = re.sub(r"[0-9]", "9", value)
    shape = re.sub(r"[a-z]", "a", shape)
    shape = re.sub(r"[A-Z]", "A", shape)
    shape = re.sub(r"a+", "a", shape)
    shape = re.sub(r"A+", "A", shape)
    return shape

def counts_to_list(counter, n, key):
    return [{key: item, "count": count} for item, count in counter.most_common(n)]

def to_number(value):
    cleaned = re.sub(r"(?i)php|[₱$, \s]", "", value)
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if math.isfinite(number):
        return number
    return None

def numeric_stats(filled):
    numbers = [n for n in (to_number(v) for v in filled) if n is not None]
    if not numbers or len(numbers) < 0.8 * len(filled):
        return None

    s = pd.Series(numbers)
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr

    return {
        "min": float(s.min()),
        "max": float(s.max()),
        "median": float(s.median()),
        "outlier_low": round(float(low), 2),
        "outlier_high": round(float(high), 2),
        "outlier_count": int(((s < low) | (s > high)).sum()),
    }

def profile_column(series):
    values = series.tolist()
    filled = [v for v in values if not is_null_like(v)]
    value_counts = Counter(filled)

    if len(value_counts) <= MAX_CATEGORY_VAULES:
        how_many = len(value_counts)
    else:
        how_many = 10

    return {
        "null_count": len(values) - len(filled),
        "null_tokens_seen": sorted({v for v in values if is_null_like(v)}),
        "unique_count": len(value_counts),
        "top_values": counts_to_list(value_counts, how_many, "value"),
        "top_shapes": counts_to_list(Counter(value_shape(v) for v in filled), 5, "shape"),
        "whitespace_issues": sum(1 for v in filled if v != v.strip() or "  " in v),
        "numeric": numeric_stats(filled),
    }

def profile_dataframe(df):
    return {
        "row_count": len(df),
        "columns": {name: profile_column(df[name]) for name in df.columns},
    }

if __name__ == "__main__":

    df = load_raw_csv("data/raw/customers_messy.csv")
    profile = profile_dataframe(df)
    llm_profile = mask_profile(profile)

    out_dir = Path("data/output")
    out_dir.parent.mkdir(parents=True, exist_ok=True)

    full_path = out_dir / "customers_messy.profile.json"
    llm_path = out_dir / "customers_messy.llim_profile.json"
    full_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    llm_path.write_text(json.dumps(llm_profile, indent=2, ensure_ascii=False), encoding="utf-8")

    print("FUll profile (stays on your computer) ->", full_path)
    print("Masked profile (safe to send to LLM)  ->", llm_path)
