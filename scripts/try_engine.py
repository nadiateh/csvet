from csvet.engine import apply_rules
from csvet.profiler import load_raw_csv
from csvet.rules import MapValues, NormalizeText, ParseDates, ToNumber

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%B %d, %Y", "%Y.%m.%d"]

rules = [
    NormalizeText(type="normalize_text", column="full_name", case="title",
                  reason="Fix spacing and casing in names"),
    NormalizeText(type="normalize_text", column="city", case="title",
                  reason="Fix spacing and casing"),
    MapValues(
        type="map_values",
        column="city",
        mapping={
            "Qc": "Quezon City",
            "Q.C": "Quezon City",
            "Makati City": "Makati",
            "Pasig City": "Pasig",
            "Cebu": "Cebu City",
        },
        reason="Short forms and extra words",
    ),
    ParseDates(type="parse_dates", column="signup_date", input_formats=DATE_FORMATS,
               reason="Five date formats found"),
    ToNumber(type="to_number", column="monthly_spend", decimals=2,
             reason="Remove peso signs, PHP and commas"),
    ToNumber(type="to_number", column="age", decimals=0,
             reason="Ages are whole numbers"),
]


def print_scoreboard(cleaned, truth):
    print(f"{'column':<15}{'before':>8}{'after':>8}")
    for column in truth.columns:
        if column not in cleaned.columns:
            continue
        before = (messy[column] == truth[column]).sum()
        after = (cleaned[column] == truth[column]).sum()
        print(f"{column:<15}{before:>8}{after:>8}   (out of {len(truth)})")


messy = load_raw_csv("data/raw/customers_messy.csv")
truth = load_raw_csv("data/truth/customers_truth.csv")

cleaned, changes = apply_rules(messy, rules)
print("Changes made:", len(changes))
print()
print_scoreboard(cleaned, truth)