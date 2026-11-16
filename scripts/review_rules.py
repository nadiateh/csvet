import json
import sys
from pathlib import Path

from csvet.evaluate import evaluate, format_report
from csvet.profiler import load_raw_csv
from csvet.review import review_rules
from csvet.rules import RuleSet

proposed_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/output/proposed_rules.json")
out_dir = Path("data/output")

raw = load_raw_csv("data/raw/customers_messy.csv")
proposed = RuleSet.model_validate_json(proposed_path.read_text(encoding="utf-8"))
print(f"Reviewing {len(proposed.rules)} proposed rules from {proposed_path}")

approved, decisions, _ = review_rules(raw, proposed.rules, ask=input)

approved_path = out_dir / "approved_rules.json"
approved_path.write_text(RuleSet(rules=approved).model_dump_json(indent=2), encoding="utf-8")
decisions_path = out_dir / "review_decisions.json"
decisions_path.write_text(json.dumps(decisions, indent=2), encoding="utf-8")

print()
print(f"Approved {len(approved)} of {len(proposed.rules)} rules.")
print("Saved:", approved_path)
print("Saved:", decisions_path)

if approved:
    truth = load_raw_csv("data/truth/customers_truth.csv")
    print()
    print(format_report(evaluate(raw, truth, approved)))