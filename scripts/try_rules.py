from pydantic import ValidationError

from csvet.rules import MapValues, NormalizeText

good = {
    "type": "map_values",
    "column": "city",
    "mapping": {"QC": "Quezon City", "Q.C": "Quezon City"},
    "reason": "QC and Q.C are short forms of Quezon City",
}
rule = MapValues.model_validate(good)
print("ACCEPTED:", rule)
print()

bad = {
    "type": "normalize_text",
    "column": "full_name",
    "case": "sentence",
    "reason": "Names should look consistent",
}
try:
    NormalizeText.model_validate(bad)
except ValidationError as error:
    print("REJECTED:")
    print(error)