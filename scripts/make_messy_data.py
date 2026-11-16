import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 28
TAG = sys.argv[2] if len(sys.argv) > 2 else ""
random.seed(SEED)

ROWS = 300
SUFFIX = f"_{TAG}" if TAG else ""
OUT_MESSY = Path(f"data/raw/customers{SUFFIX}_messy.csv")
OUT_TRUTH = Path(f"data/truth/customers{SUFFIX}_truth.csv")

FIRST_NAMES = ["Juan", "Maria", "Jose", "Ana"]
LAST_NAMES = ["Dela Cruz", "Santos", "Reyes", "Garcia"]
CITY_VARIANTS = {
    "Quezon City": ["Quezon City", "quezon city", "QC", "Q.C", "Quezon City "],
    "Makati": ["Makati", "MAKATI", "Makati City", "makati "],
    "Pasig": ["Pasig", "pasig city", "Pasig City", "PASIG"],
    "Cebu City": ["Cebu City", "cebu", "Cebu city", "CEBU CITY"],
}
if TAG:  # a second file contains spellings the first one never had
    CITY_VARIANTS["Quezon City"].append("Q City")
    CITY_VARIANTS["Makati"].append("Makati, PH")

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%B %d, %Y", "%Y.%m.%d"]


def messy_name(name):
    style = random.choice(["as_is", "upper", "lower", "spaces"])
    if style == "upper":
        return name.upper()
    if style == "lower":
        return name.lower()
    if style == "spaces":
        return " " + name.replace(" ", "  ") + " "
    return name


def messy_money(amount):
    return random.choice([
        f"{amount:.2f}",
        f"₱{amount:,.2f}",
        f"PHP {amount:.2f}",
        f" {amount:,.2f}",
    ])


def make_row(i):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    signup = date(2022, 1, 1) + timedelta(days=random.randint(0, 1460))
    city = random.choice(list(CITY_VARIANTS))
    spend = round(random.uniform(199, 2999), 2)
    age = random.randint(18, 70)
    flags = []

    clean = {
        "customer_id": i,
        "full_name": f"{first} {last}",
        "signup_date": signup.isoformat(),
        "city": city,
        "monthly_spend": f"{spend:.2f}",
        "age": str(age),
    }
    messy = {
        "customer_id": i,
        "full_name": messy_name(clean["full_name"]),
        "signup_date": signup.strftime(random.choice(DATE_FORMATS)),
        "city": random.choice(CITY_VARIANTS[city]),
        "monthly_spend": messy_money(spend),
        "age": str(age),
    }

    roll = random.random()
    if roll < 0.05:
        messy["monthly_spend"] = random.choice(["", "N/A", "-"])
        clean["monthly_spend"] = ""
    elif roll < 0.07:
        wrong = f"{spend * 1000:.2f}"
        messy["monthly_spend"] = wrong
        clean["monthly_spend"] = wrong
        flags.append("monthly_spend:outlier")

    roll = random.random()
    if roll < 0.05:
        messy["age"] = random.choice(["", "N/A", "unknown"])
        clean["age"] = ""
    elif roll < 0.07:
        bad = random.choice(["-5", "230", "0"])
        messy["age"] = bad
        clean["age"] = bad
        flags.append("age:invalid")
    clean["expected_flags"] = ";".join(flags)

    return clean, messy


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    clean_rows = []
    messy_rows = []
    for i in range(1, ROWS + 1):
        clean, messy = make_row(i)
        clean_rows.append(clean)
        messy_rows.append(messy)

    write_csv(OUT_MESSY, messy_rows)
    write_csv(OUT_TRUTH, clean_rows)
    print(f"Wrote {len(messy_rows)} rows -> {OUT_MESSY}")
    print(f"Wrote answer key -> {OUT_TRUTH}")


if __name__ == "__main__":
    main()