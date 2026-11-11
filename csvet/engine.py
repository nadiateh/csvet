from datetime import datetime

from csvet.profiler import is_null_like, to_number
from csvet.rules import FlagRange, MapValues, NormalizeText, ParseDates, ToNumber


def show(number):
    return f"{number:,.2f}".rstrip("0").rstrip(".")


def parse_date(value, formats):
    found = set()
    for fmt in formats:
        try:
            found.add(datetime.strptime(value.strip(), fmt).date())
        except ValueError:
            pass
    if len(found) == 1:
        return found.pop().isoformat(), None
    if len(found) == 0:
        return None, "no listed date format matches this value"
    options = " or ".join(d.isoformat() for d in sorted(found))
    return None, f"ambiguous date, could be {options}"


def new_value(rule, value):
    """Return (new_value, note). A note means: leave it and flag it for a human."""
    if isinstance(rule, NormalizeText):
        cleaned = " ".join(value.split())
        if rule.case == "title":
            cleaned = cleaned.title()
        elif rule.case == "upper":
            cleaned = cleaned.upper()
        elif rule.case == "lower":
            cleaned = cleaned.lower()
        return cleaned, None

    if isinstance(rule, MapValues):
        return rule.mapping.get(value, value), None

    if isinstance(rule, ParseDates):
        if is_null_like(value):
            return "", None
        parsed, note = parse_date(value, rule.input_formats)
        if parsed is None:
            return value, note
        return parsed, None

    if isinstance(rule, ToNumber):
        if is_null_like(value):
            return "", None
        number = to_number(value)
        if number is None:
            return value, "not a number"
        return f"{number:.{rule.decimals}f}", None

    if isinstance(rule, FlagRange):
        if is_null_like(value):
            return value, None
        number = to_number(value)
        if number is None:
            return value, "not a number"
        if rule.min_value is not None and number < rule.min_value:
            return value, f"{show(number)} is below the minimum {show(rule.min_value)}"
        if rule.max_value is not None and number > rule.max_value:
            return value, f"{show(number)} is above the maximum {show(rule.max_value)}"
        return value, None

    raise ValueError(f"No code for rule type: {rule.type}")


def apply_rule(df, rule, rule_number):
    if rule.column not in df.columns:
        raise ValueError(f"Rule {rule_number} uses a column that does not exist: {rule.column}")

    log = []
    for row, before in df[rule.column].items():
        after, note = new_value(rule, before)

        if note:
            action = "flagged"
        elif after != before:
            action = "changed"
            df.at[row, rule.column] = after
        else:
            continue

        log.append({
            "rule_number": rule_number,
            "rule_type": rule.type,
            "row": row,
            "column": rule.column,
            "action": action,
            "before": before,
            "after": after,
            "note": note or "",
        })
    return log


def apply_rules(df, rules):
    cleaned = df.copy()
    full_log = []
    for number, rule in enumerate(rules, start=1):
        full_log.extend(apply_rule(cleaned, rule, number))
    return cleaned, full_log