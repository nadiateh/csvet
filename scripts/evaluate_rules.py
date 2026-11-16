import sys
from pathlib import Path

from csvet.evaluate import evaluate, format_report
from csvet.profiler import load_raw_csv
from csvet.rules import RuleSet

paths = sys.argv[1:] or ["data/output/proposed_rules.json"]

messy = load_raw_csv("data/raw/customers_messy.csv")
truth = load_raw_csv("data/truth/customers_truth.csv")

results = {}
for path in paths:
    rule_set = RuleSet.model_validate_json(Path(path).read_text(encoding="utf-8"))
    results[path] = evaluate(messy, truth, rule_set.rules)
    print("=" * 62)
    print(path)
    print("=" * 62)
    print(format_report(results[path]))
    print()

if len(results) > 1:
    print("=" * 62)
    print(f"{'rules file':<34}{'accuracy':>9}{'broken':>8}{'missed':>7}{'false':>6}")
    for path, result in results.items():
        flags = result["flags"]
        print(
            f"{Path(path).name:<34}{result['accuracy_after']:>9.1%}"
            f"{result['broken']:>8}{flags['missed']:>7}{flags['false_alarms']:>6}"
        )