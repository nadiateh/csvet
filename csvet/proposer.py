import json

from pydantic import ValidationError

from csvet.rules import RuleSet

SYSTEM_PROMPT = """You are a data-cleaning assistant. You are given a profile of a CSV file: \
statistics and example values for each column. Propose cleaning rules as JSON. \
Never output cleaned data, only rules.

Reply with ONE JSON object and nothing else, in this form:
{"rules": [ ...rules... ]}

Every rule has "type", "column" and "reason" (one short sentence, based on the profile). \
Allowed rule types, and no others:

1. normalize_text: trims spaces, collapses repeated spaces, optionally changes casing.
   {"type": "normalize_text", "column": "...", "case": "title" | "upper" | "lower" | "keep", "reason": "..."}
2. map_values: replaces exact values with a standard value.
   {"type": "map_values", "column": "...", "mapping": {"old": "new"}, "reason": "..."}
3. parse_dates: converts dates to YYYY-MM-DD. "input_formats" are Python strptime codes such as \
"%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%B %d, %Y".
   {"type": "parse_dates", "column": "...", "input_formats": ["..."], "reason": "..."}
4. to_number: removes currency symbols, commas and spaces and writes a plain number. \
"decimals" is the number of decimal places (0 for whole numbers).
   {"type": "to_number", "column": "...", "decimals": 2, "reason": "..."}
5. flag_range: does NOT change values. It flags values outside a range for human review. \
Give "min_value", "max_value" or both.
   {"type": "flag_range", "column": "...", "min_value": 0, "max_value": 120, "reason": "..."}

Important:
- Rules run in the order you list them, and each rule sees the output of the previous one. \
For example, after normalize_text with case "title", the value "QC" has become "Qc", so a \
map_values key must be "Qc".
- Only use column names that appear in the profile.
- Columns with "masked": true have no example values. Do not use map_values on them.
- Only propose a rule when the profile shows a problem it fixes. Leave clean columns alone \
(for example ID columns).
- Never guess missing values and never map values you cannot see in the profile.
- Do not list both day-first and month-first date formats unless the profile shows both are present.
- Use flag_range for impossible values (such as negative ages) and extreme outliers, with limits \
that fit what the column means.
- Put a flag_range rule after any to_number rule for the same column."""


def build_messages(llm_profile):
    profile_text = json.dumps(llm_profile, ensure_ascii=False, separators=(",", ":"))
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Profile of the CSV file:\n" + profile_text},
    ]


def clean_reply(reply):
    text = reply.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def describe_error(error):
    lines = []
    for item in error.errors():
        where = ".".join(str(part) for part in item["loc"]) or "reply"
        lines.append(f"{where}: {item['msg']}")
    return "\n".join(lines)


def check_rules(rule_set, llm_profile):
    columns = llm_profile["columns"]
    problems = []
    for number, rule in enumerate(rule_set.rules, start=1):
        if rule.column not in columns:
            names = ", ".join(columns)
            problems.append(
                f"Rule {number} uses column '{rule.column}', which is not in the profile. "
                f"The columns are: {names}."
            )
        elif rule.type == "map_values" and columns[rule.column].get("masked", False):
            problems.append(
                f"Rule {number} uses map_values on '{rule.column}', which is masked, "
                f"so you cannot know its real values."
            )
    return problems


def propose_rules(llm_profile, call_llm, max_attempts=3):
    messages = build_messages(llm_profile)
    feedback = ""

    for attempt in range(1, max_attempts + 1):
        reply = call_llm(messages)
        try:
            rule_set = RuleSet.model_validate_json(clean_reply(reply))
            problems = check_rules(rule_set, llm_profile)
            if not problems:
                return rule_set, attempt
            feedback = "\n".join(problems)
        except ValidationError as error:
            feedback = describe_error(error)

        messages = messages + [
            {"role": "assistant", "content": reply},
            {
                "role": "user",
                "content": "Your reply was rejected:\n" + feedback
                + "\nReply again with the complete corrected JSON object only.",
            },
        ]

    raise ValueError(f"No valid rules after {max_attempts} attempts. Last problem:\n{feedback}")