from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAIError

from csvet.engine import apply_rules
from csvet.llm import make_openai_caller
from csvet.privacy import mask_profile
from csvet.profiler import load_raw_csv, profile_dataframe
from csvet.proposer import build_messages, propose_rules

CSV_PATH = Path("data/raw/customers_messy.csv")
OUT_DIR = Path("data/output")

load_dotenv()
try:
    call_llm = make_openai_caller()
except RuntimeError as error:
    raise SystemExit(f"Setup problem: {error}")

raw = load_raw_csv(CSV_PATH)
llm_profile = mask_profile(profile_dataframe(raw))

messages = build_messages(llm_profile)
prompt_text = messages[0]["content"] + "\n\n" + messages[1]["content"]
OUT_DIR.mkdir(parents=True, exist_ok=True)
prompt_path = OUT_DIR / "prompt.txt"
prompt_path.write_text(prompt_text, encoding="utf-8")

hidden = [name for name, column in llm_profile["columns"].items() if column["masked"]]
print(f"Columns whose values are hidden: {', '.join(hidden) or 'none'}")
print(f"The prompt is about {len(prompt_text) // 4:,} tokens. Full text: {prompt_path}")
print("Open that file to see exactly what will be sent.")
if input("Send it to OpenAI? (y/n) ").strip().lower() != "y":
    print("Cancelled. Nothing was sent.")
    raise SystemExit

try:
    rule_set, attempts = propose_rules(llm_profile, call_llm)
except (OpenAIError, ValueError) as error:
    raise SystemExit(f"The request failed ({type(error).__name__}): {error}")

print()
print(f"Accepted on attempt {attempts}. The LLM proposed {len(rule_set.rules)} rules:")
for number, rule in enumerate(rule_set.rules, start=1):
    print(f"  {number}. {rule.type:<15} {rule.column:<14} {rule.reason}")

rules_path = OUT_DIR / "proposed_rules.json"
rules_path.write_text(rule_set.model_dump_json(indent=2), encoding="utf-8")
print("Saved rules to", rules_path)

cleaned, log = apply_rules(raw, rule_set.rules)
changed = sum(1 for e in log if e["action"] == "changed")
flagged = [e for e in log if e["action"] == "flagged"]
print()
print(f"Applying them: {changed} values changed, {len(flagged)} flagged for review")
for entry in flagged[:5]:
    print(f"  row {entry['row']}, {entry['column']}: {entry['before']!r} -> {entry['note']}")