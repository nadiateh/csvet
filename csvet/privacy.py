import copy
import re

SENSITIVE_NAME_WORDS =["name", "email", "phone", "mobile", "address", "contact"]
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")

def is_sensitive_column(column_name, sample_values):
    lower = column_name.lower()
    if any(word in lower for word in SENSITIVE_NAME_WORDS):
        return True

    if not sample_values:
        return False

    email_hits = sum(1 for v in sample_values if EMAIL_PATTERN.search(v))
    return email_hits >= 0.5 * len(sample_values)

def mask_profile(profile):
    masked = copy.deepcopy(profile)
    for name, column in masked["columns"].items():
        values = [item["value"] for item in column["top_values"]]
        if is_sensitive_column(name, values):
            column["top_values"] = []
            column["masked"] = True
        else:
            column["masked"] = False
    return masked
