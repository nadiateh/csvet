import json
from pathlib import Path

from csvet.engine import apply_rules
from csvet.privacy import mask_profile
from csvet.profiler import load_raw_csv, profile_dataframe
from csvet.proposer import build_messages, propose_rules

CSV_PATH = Path("data/raw/customers_messy.csv")

# A pretend LLM: it answers wrongly first, then correctly.
BAD_REPLY = json.dumps({"rules": [
    {"type": "delete_rows", "column": "age", "reason": "Remove rows with bad ages"},
]})
GOOD_REPLY = json.dumps({"rules": [
    {"type": "normalize_text", "column": "city", "case": "title",
     "reason": "City names have mixed casing and extra spaces"},
    {"type": "map_values", "column": "city",
     "mapping": {"Qc": "Quezon City", "Q.C": "Quezon City", "Makati City": "Makati",
                 "Pasig City": "Pasig", "Cebu": "Cebu City"},
     "reason": "Short forms and extra words refer to the same four cities"},
    {"type": "parse_dates", "column": "signup_date",
     "input_formats": ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%B %d, %Y", "%Y.%m.%d"],
     "reason": "Five different date formats"},
    {"type": "to_number", "column": "monthly_spend", "decimals": 2,
     "reason": "Mixed peso signs, PHP prefixes and commas"},
    {"type": "flag_range", "column": "monthly_spend", "min_value": 0, "max_value": 10000,
     "reason": "A few values are far above the median"},
]})


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)

    def __call__(self, messages):
        print(f"[fake LLM] asked with {len(messages)} messages")
        if len(messages) > 2:
            print("[fake LLM] the last message it received was:")
            print(messages[-1]["content"])
        return self.replies.pop(0)


raw = load_raw_csv(CSV_PATH)
llm_profile = mask_profile(profile_dataframe(raw))

messages = build_messages(llm_profile)
prompt_text = messages[0]["content"] + "\n\n" + messages[1]["content"]
out_dir = Path("data/output")
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "prompt.txt").write_text(prompt_text, encoding="utf-8")

print(f"CSV file size: {CSV_PATH.stat().st_size:,} bytes ({len(raw)} rows)")
print(f"Prompt size:   {len(prompt_text):,} characters (about {len(prompt_text) // 4:,} tokens)")
print("Full prompt saved to", out_dir / "prompt.txt")
print()

rule_set, attempts = propose_rules(llm_profile, FakeLLM([BAD_REPLY, GOOD_REPLY]))
print()
print(f"Accepted on attempt {attempts}. Proposed rules:")
for number, rule in enumerate(rule_set.rules, start=1):
    print(f"  {number}. {rule.type:<15} {rule.column:<14} {rule.reason}")

cleaned, log = apply_rules(raw, rule_set.rules)
changed = sum(1 for e in log if e["action"] == "changed")
flagged = sum(1 for e in log if e["action"] == "flagged")
print()
print(f"Applying them: {changed} values changed, {flagged} flagged for review")