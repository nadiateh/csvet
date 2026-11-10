
from pydantic import ValidationError

from csvet.rules import RuleSet

proposal = {
    "rules": [
        {"type": "normalize_text", "column": "city", "case": "title",
         "reason": "Fix spacing and casing first"},
        {"type": "map_values", "column": "city",
         "mapping": {"Qc": "Quezon City", "Q.C": "Quezon City"},
         "reason": "Short forms of Quezon City"},
        {"type": "parse_dates", "column": "signup_date",
         "input_formats": ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%B %d, %Y", "%Y.%m.%d"],
         "reason": "Five date formats found"},
        {"type": "to_number", "column": "monthly_spend",
         "reason": "Remove peso signs, PHP and commas"},
        {"type": "flag_range", "column": "age", "min_value": 0, "max_value": 120,
         "reason": "Ages outside 0-120 are impossible"},
    ]
}

rule_set = RuleSet.model_validate(proposal)
for rule in rule_set.rules:
    print(type(rule).__name__, "->", rule.column)
print()

bad = {"rules": [{"type": "flag_range", "column": "age", "reason": "no limits given"}]}
try:
    RuleSet.model_validate(bad)
except ValidationError as error:
    print("REJECTED:")
    print(error)
