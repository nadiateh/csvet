import json
import sys
from pathlib import Path

import pandas as pd

from csvet.engine import apply_rules
from csvet.evaluate import evaluate, format_report
from csvet.profiler import load_raw_csv
from csvet.reuse import find_unseen, missing_columns
from csvet.rules import RuleSet

if len(sys.argv) < 2:
    sys.exit("Usage: python -m scripts.clean_with_rules data/raw/<new_file>.csv [rules.json]")

raw_path = Path(sys.argv[1])
rules_path = Path(sys.argv[2] if len(sys.argv) > 2 else "data/output/approved_rules.json")
known_path = Path("data/output/known_values.json")
out_dir = Path("data/output")

raw = load_raw_csv(raw_path)
rules = RuleSet.model_validate_json(rules_path.read_text(encoding="utf-8")).rules
print(f"Loaded {len(raw)} rows from {raw_path}")
print(f"Applying {len(rules)} saved rules from {rules_path} (no AI call)")

missing = missing_columns(rules, raw)
if missing:
    sys.exit(f"This file has no column named {missing}. Nothing was changed.")

cleaned, log = apply_rules(raw, rules)

stem = raw_path.stem
cleaned_path = out_dir / f"{stem}_cleaned.csv"
log_path = out_dir / f"{stem}_change_log.csv"
cleaned.to_csv(cleaned_path, index=False)
pd.DataFrame(log).to_csv(log_path, index=False)

changed = sum(1 for e in log if e["action"] == "changed")
flagged = sum(1 for e in log if e["action"] == "flagged")
print()
print(f"Changed {changed} values, flagged {flagged} for a human to look at.")
print("Saved:", cleaned_path)
print("Saved:", log_path)

print()
if known_path.exists():
    known = json.loads(known_path.read_text(encoding="utf-8"))
    unseen = find_unseen(cleaned, known)
    if unseen:
        print("WARNING: values the reviewed rules have never seen (they may be wrong):")
        for column, values in unseen.items():
            for value, count in values.items():
                print(f"  {column}: {value!r}  ({count}x)")
        print("Check these by hand, or run the review step again to add a rule.")
    else:
        print("No unfamiliar values: every label was seen when the rules were reviewed.")
else:
    print("No known_values.json found, so the unfamiliar-value check was skipped.")

truth_path = Path("data/truth") / raw_path.name.replace("messy", "truth")
if truth_path.exists():
    truth = load_raw_csv(truth_path)
    print()
    print("Answer key found, so we can measure it:")
    print(format_report(evaluate(raw, truth, rules)))