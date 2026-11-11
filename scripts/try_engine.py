from pathlib import Path

import pandas as pd

from csvet.engine import apply_rules
from csvet.profiler import load_raw_csv
from csvet.rules import FlagRange, MapValues, NormalizeText, ParseDates, ToNumber

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%B %d, %Y", "%Y.%m.%d"]

rules = [
    NormalizeText(type="normalize_text", column="full_name", case="title",
                  reason="Fix spacing and casing in names"),
    NormalizeText(type="normalize_text", column="city", case="title",
                  reason="Fix spacing and casing"),
    MapValues(
        type="map_values",
        column="city",
        mapping={
            "Qc": "Quezon City",
            "Q.C": "Quezon City",
            "Makati City": "Makati",
            "Pasig City": "Pasig",
            "Cebu": "Cebu City",
        },
        reason="Short forms and extra words",
    ),
    ParseDates(type="parse_dates", column="signup_date", input_formats=DATE_FORMATS,
               reason="Five date formats found"),
    ToNumber(type="to_number", column="monthly_spend", decimals=2,
             reason="Remove peso signs, PHP and commas"),
    ToNumber(type="to_number", column="age", decimals=0,
             reason="Ages are whole numbers"),
    FlagRange(type="flag_range", column="monthly_spend", min_value=0, max_value=10000,
              reason="Spending above 10,000 is probably a typo"),
    FlagRange(type="flag_range", column="age", min_value=1, max_value=120,
              reason="Customers must be between 1 and 120 years old"),
]


def print_scoreboard(messy, cleaned, truth):
    print(f"{'column':<15}{'before':>8}{'after':>8}")
    for column in truth.columns:
        if column not in cleaned.columns:
            continue
        before = (messy[column] == truth[column]).sum()
        after = (cleaned[column] == truth[column]).sum()
        print(f"{column:<15}{before:>8}{after:>8}   (out of {len(truth)})")


def expected_flags(truth):
    expected = set()
    for row, text in truth["expected_flags"].items():
        for item in text.split(";"):
            if item:
                expected.add((row, item.split(":")[0]))
    return expected


def found_flags(log):
    return {(e["row"], e["column"]) for e in log if e["action"] == "flagged"}


messy = load_raw_csv("data/raw/customers_messy.csv")
truth = load_raw_csv("data/truth/customers_truth.csv")

cleaned, log = apply_rules(messy, rules)

changed = [e for e in log if e["action"] == "changed"]
flagged = [e for e in log if e["action"] == "flagged"]
print(f"Changed: {len(changed)}   Flagged for review: {len(flagged)}")
print()
print_scoreboard(messy, cleaned, truth)

expected = expected_flags(truth)
found = found_flags(log)
print()
print(f"Flags the answer key expects: {len(expected)}")
print(f"Flags CSVet raised:           {len(found)}")
print(f"  correct:      {len(expected & found)}")
print(f"  missed:       {len(expected - found)}")
print(f"  false alarms: {len(found - expected)}")
print()
print("First flags:")
for entry in flagged[:5]:
    print(f"  row {entry['row']}, {entry['column']}: {entry['before']!r} -> {entry['note']}")

out_dir = Path("data/output")
out_dir.mkdir(parents=True, exist_ok=True)
cleaned.to_csv(out_dir / "customers_cleaned.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(log).to_csv(out_dir / "customers_change_log.csv", index=False, encoding="utf-8-sig")
print()
print("Saved cleaned file and change log to", out_dir)