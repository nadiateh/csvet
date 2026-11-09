import pandas as pd
import re
from collections import Counter

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

df = load_raw_csv("data/raw/customers_messy.csv")

for column in df.columns:
    values = df[column].tolist()
    filled = [v for v in values if not is_null_like(v)]
    shapes = Counter(value_shape(v) for v in filled)

    print(column)
    print(" missing:", len(values) - len(filled))
    print(" shapes:", shapes.most_common(5))
    print()
    