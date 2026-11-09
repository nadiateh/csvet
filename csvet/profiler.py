import pandas as pd

NULL_TOKENS = {"", "na", "n/a", "null", "none", "nan", "-", "?", "unknown"}

def load_raw_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")

def is_null_like(value):
    return value.strip().lower() in NULL_TOKENS

df = load_raw_csv("data/raw/customers_messy.csv")
print(df.head())
print()

for column in df.columns:
    values = df[column].tolist()
    nulls = [v for v in values if is_null_like(v)]
    print(column, "->", len(nulls), "missing")