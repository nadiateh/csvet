import pandas as pd
import re
from collections import Counter
import json
from pathlib import Path

NULL_TOKENS = {"", "na", "n/a", "null", "none", "nan", "-", "?", "unknown"}

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

def profile_column(series):
    values = series.tolist()
    filled = [v for v in values if not is_null_like(v)]
    return {
        "null_count": len(values) - len(filled),
        "null_tokens_seen": sorted({v for v in values if is_null_like(v)}),
        "unique_count": len(set(filled)),
        "top_values": Counter(filled).most_common(10),
        "top_shapes": Counter(value_shape(v) for v in filled).most_common(5),
        "whitespace_issues": sum(1 for v in filled if v != v.strip() or "  " in v),
    }

def profile_dataframe(df):
    return {
        "row_count": len(df),
        "columns": {name: profile_column(df[name]) for name in df.columns},
    }

if __name__ == "__main__":

    df = load_raw_csv("data/raw/customers_messy.csv")
    profile = profile_dataframe(df)

    out_path = Path("data/output/customers_messy.profile.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Saved ->", out_path)
