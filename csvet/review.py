import json
from collections import Counter

from pydantic import ValidationError

from csvet.engine import apply_rule
from csvet.proposer import describe_error

LOCKED_FIELDS = ("type", "column")


def preview_rule(df, rule, rule_number, limit=5):
    log = apply_rule(df.copy(), rule, rule_number)
    groups = Counter((e["action"], e["before"], e["after"], e["note"]) for e in log)
    examples = [
        {"action": action, "before": before, "after": after, "note": note, "count": count}
        for (action, before, after, note), count in groups.most_common(limit)
    ]
    return {
        "changed": sum(1 for e in log if e["action"] == "changed"),
        "flagged": sum(1 for e in log if e["action"] == "flagged"),
        "examples": examples,
    }


def edit_rule(rule, field, json_text):
    data = rule.model_dump()
    if field in LOCKED_FIELDS or field not in data:
        editable = ", ".join(name for name in data if name not in LOCKED_FIELDS)
        raise ValueError(f"You can only change: {editable}")
    try:
        data[field] = json.loads(json_text)
    except json.JSONDecodeError:
        raise ValueError('The new value must be JSON, for example 1, "title" or ["%Y-%m-%d"].')
    try:
        return type(rule).model_validate(data)
    except ValidationError as error:
        raise ValueError(describe_error(error))


def show_rule(rule, number, total, preview, show):
    settings = {
        name: value
        for name, value in rule.model_dump().items()
        if name not in ("type", "column", "reason")
    }
    settings_text = json.dumps(settings, ensure_ascii=False)
    if len(settings_text) > 300:
        settings_text = settings_text[:300] + "..."

    show("")
    show(f"Rule {number} of {total}: {rule.type} on {rule.column}")
    show(f"  Why:      {rule.reason}")
    show(f"  Settings: {settings_text}")
    show(f"  On the data so far it would change {preview['changed']} values "
         f"and flag {preview['flagged']}.")
    for example in preview["examples"]:
        if example["action"] == "flagged":
            show(f"    {example['before']!r}  FLAGGED: {example['note']}  ({example['count']}x)")
        else:
            show(f"    {example['before']!r} -> {example['after']!r}  ({example['count']}x)")


def review_rules(raw, rules, ask, show=print):
    current = raw.copy()
    approved = []
    decisions = []

    for number, rule in enumerate(rules, start=1):
        edited = False
        while True:
            show_rule(rule, number, len(rules), preview_rule(current, rule, number), show)
            answer = ask("[a]pprove, [r]eject or [e]dit? ").strip().lower()

            if answer == "a":
                apply_rule(current, rule, number)
                approved.append(rule)
                decision = "approved"
                break
            if answer == "r":
                decision = "rejected"
                break
            if answer == "e":
                field = ask("Which setting? ").strip()
                value = ask("New value (JSON): ")
                try:
                    rule = edit_rule(rule, field, value)
                    edited = True
                except ValueError as error:
                    show(f"Could not change it: {error}")
                continue
            show("Please type a, r or e.")

        decisions.append({
            "rule_number": number,
            "type": rule.type,
            "column": rule.column,
            "decision": decision,
            "edited": edited,
        })

    return approved, decisions, current