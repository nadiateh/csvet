import random
from datetime import date, timedelta
import csv
from pathlib import Path

random.seed(28)

FIRST_NAMES = ["Juan", "Maria", "Jose", "Ana"]
LAST_NAMES = ["Dela Cruz", "Santos", "Reyes", "Garcia"]
CITY_VARIANTS = {
    "Quezon City": ["Quezon City", "quezon city", "QC", "Q.C", "Quezon City "],
    "Makati": ["Makati", "MAKATI", "Makati City", "makati "],
    "Pasig": ["Pasig", "pasig city", "Pasig City", 'PASIG'],
    "Cebu City": ["Cebu City", "cebu", "Cebu city", "CEBU CITY"],
}
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y","%d-%b-%Y", "%B %d, %Y", "%Y.%m.%d"]



def messy_name(name):
    style = random.choice(["as_is", "upper", "lower", "spaces"])
    if style == "upper":
        return name.upper()
    if style == "lower":
        return name.lower()
    if style == "spaces":
        return " " + name.replace(" ", "  ") + " "
    return name

def make_row(i):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    signup = date(2022, 1, 1) + timedelta(days=random.randint(0, 1460))
    city = random.choice(list(CITY_VARIANTS))

    clean = {
        "customer_id": i,
        "full_name": f"{first} {last}",
        "signup_date": signup.isoformat(),
        "city": city,
    }

    messy = {
        "customer_id": i,
        "full_name": messy_name(clean["full_name"]),
        "signup_date": signup.strftime(random.choice(DATE_FORMATS)),
        "city": random.choice(CITY_VARIANTS[city]),
    }
    return clean, messy

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

clean_rows = []
messy_rows = []
for i in range(1, 301):
    clean, messy = make_row(i)
    clean_rows.append(clean)
    messy_rows.append(messy)

write_csv(Path("data/raw/customers_messy.csv"), messy_rows)
write_csv(Path("data/truth/customers_truth.csv"), clean_rows)
print("Wrote", len(messy_rows), "rows")