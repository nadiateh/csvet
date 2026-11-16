from collections import Counter

from csvet.privacy import is_sensitive_column
from csvet.profiler import MAX_CATEGORY_VALUES, is_null_like
from csvet.rules import MapValues, NormalizeText

# Only these rules work on labels, so only these columns can contain "new labels".
LABEL_RULES = (NormalizeText, MapValues)


def missing_columns(rules, df):
    """Columns the rules need that the new file does not have, in order."""
    needed = dict.fromkeys(rule.column for rule in rules)
    return [column for column in needed if column not in df.columns]


def learn_known_values(cleaned, rules):
    """The cleaned labels the reviewer actually saw, for each small label column."""
    known = {}
    for column in dict.fromkeys(r.column for r in rules if isinstance(r, LABEL_RULES)):
        values = sorted({v for v in cleaned[column] if not is_null_like(v)})
        if len(values) > MAX_CATEGORY_VALUES:
            continue  # too many different values to be labels (probably free text)
        if is_sensitive_column(column, values):
            continue  # never store personal data
        known[column] = values
    return known


def find_unseen(cleaned, known):
    """Cleaned values that were not in the file the rules were reviewed on."""
    unseen = {}
    for column, values in known.items():
        if column not in cleaned.columns:
            continue
        allowed = set(values)
        counts = Counter(
            v for v in cleaned[column] if not is_null_like(v) and v not in allowed
        )
        if counts:
            unseen[column] = dict(counts.most_common())
    return unseen