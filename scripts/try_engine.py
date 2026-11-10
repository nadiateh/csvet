from collections import Counter

from csvet.engine import apply_rules
from csvet.profiler import load_raw_csv
from csvet.rules import MapValues, NormalizeText

messy = load_raw_csv("data/raw/customers_messy.csv")
truth = load_raw_csv("data/truth/customers_truth.csv")

rules = [
    NormalizeText(type="normalize_text", column="city", case="title", reason="Fix spacing and casing"),
    MapValues(
        type="map_values",
        column="city",
        mapping={"Qc": "Quezon City", "Q.C": "Quezon City"},
        reason="SHort forms of Quezon City",
    ),
]

cleaned, changes = apply_rules(messy, rules)

print("Change made:", len(changes))
print("Changes per rule:", dict(Counter(c["rule_number"] for c in changes)))
print()

for change in changes[:5]:
    print(f"row {change['row']}: {change['before']!r} -> {change['after']!r}")
print()

before_ok = (messy["city"] == truth["city"]).sum()
after_ok = (cleaned["city"] == truth["city"]).sum()
print(f"City matches the answer key: before {before_ok}/{len(messy)}, after {after_ok}/{len(messy)}")
print("Cities still wrong:", dict(Counter(cleaned["city"][cleaned["city"] != truth["city"]])))
