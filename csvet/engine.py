from encodings.idna import ToUnicode
from datetime import datetime

from csvet.profiler import is_null_like, to_number
from csvet.rules import MapValues, NormalizeText, ParseDates, ToNumber

def parse_date(value, formats):
    found = set()
    for fmt in formats:
        try:
            found.add(datetime.strptime(value.strip(), fmt).date())
        except ValueError:
            pass
    if len(found) == 1:
        return found.pop().isoformat()
    return None

def new_value(rule, value):
    if isinstance(rule, NormalizeText):
        cleaned = " ".join(value.split())
        if rule.case == "title":
            return cleaned.title()
        if rule.case == "upper":
            return cleaned.upper()
        if rule.case == "lower":
            return cleaned.lower()
        return cleaned

    if isinstance(rule, MapValues):
        return rule.mapping.get(value, value)

    if isinstance(rule, ParseDates):
        if is_null_like(value):
            return ""
        parsed = parse_date(value, rule.input_formats)
        if parsed is None:
            return value
        return parsed

    if isinstance(rule, ToNumber):
        if is_null_like(value):
            return ""
        number = to_number(value)
        if number is None:
            return value
        return f"{number:.{rule.decimals}f}"

    raise ValueError(f"No code yet for rule type: {rule.type}")

def apply_rule(df, rule, rule_number):
    if rule.column not in df.columns:
        raise ValueError(f"Rule {rule_number} uses a column that does not exist: {rule.column}")

    changes =[]
    for row, before, in df[rule.column].items():
        after = new_value(rule, before)
        if after != before:
            df.at[row, rule.column] = after
            changes.append({
                "rule_number": rule_number,
                "rule_type": rule.type,
                "row": row,
                "column": rule.column,
                "before": before, 
                "after": after,
            })
    return changes

def apply_rules(df, rules):
    cleaned = df.copy()
    all_changes = []
    for number, rule in enumerate(rules, start=1):
        all_changes.extend(apply_rule(cleaned, rule, number))
    return cleaned, all_changes