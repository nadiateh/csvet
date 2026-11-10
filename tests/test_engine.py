import pandas as pd
import pytest

from csvet.engine import apply_rules
from csvet.rules import MapValues, NormalizeText, ParseDates, ToNumber

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%B %d, %Y", "%Y.%m.%d"]


def make_df():
    return pd.DataFrame({"city": [" quezon  city ", "QC", "Makati"]})


def title_rule():
    return NormalizeText(type="normalize_text", column="city", case="title", reason="x")


def test_normalize_text_trims_spaces_and_fixes_case():
    cleaned, _ = apply_rules(make_df(), [title_rule()])
    assert cleaned["city"].tolist() == ["Quezon City", "Qc", "Makati"]


def test_map_values_replaces_only_listed_values():
    rule = MapValues(type="map_values", column="city", mapping={"QC": "Quezon City"}, reason="x")
    cleaned, _ = apply_rules(make_df(), [rule])
    assert cleaned["city"].tolist() == [" quezon  city ", "Quezon City", "Makati"]


def test_original_dataframe_is_not_changed():
    df = make_df()
    apply_rules(df, [title_rule()])
    assert df["city"].tolist() == [" quezon  city ", "QC", "Makati"]


def test_every_change_is_logged_with_before_and_after():
    _, changes = apply_rules(make_df(), [title_rule()])
    assert len(changes) == 2
    assert changes[0]["before"] == " quezon  city "
    assert changes[0]["after"] == "Quezon City"
    assert changes[0]["rule_number"] == 1


def test_unchanged_values_are_not_logged():
    _, changes = apply_rules(make_df(), [title_rule()])
    assert all(c["before"] != "Makati" for c in changes)


def test_rules_run_in_order():
    rules = [
        title_rule(),
        MapValues(type="map_values", column="city", mapping={"Qc": "Quezon City"}, reason="x"),
    ]
    cleaned, _ = apply_rules(make_df(), rules)
    assert cleaned["city"].tolist() == ["Quezon City", "Quezon City", "Makati"]


def test_unknown_column_is_rejected():
    rule = NormalizeText(type="normalize_text", column="nope", case="title", reason="x")
    with pytest.raises(ValueError):
        apply_rules(make_df(), [rule])


# ---------- dates and numbers ----------


def run_one(rule, values):
    df = pd.DataFrame({"x": values})
    cleaned, changes = apply_rules(df, [rule])
    return cleaned["x"].tolist(), changes


def date_rule(formats=DATE_FORMATS):
    return ParseDates(type="parse_dates", column="x", input_formats=formats, reason="x")


def number_rule(decimals=2):
    return ToNumber(type="to_number", column="x", decimals=decimals, reason="x")


def test_parse_dates_handles_every_format():
    values = ["2023-07-18", "07/18/2023", "18-Jul-2023", "July 18, 2023", "2023.07.18"]
    result, _ = run_one(date_rule(), values)
    assert result == ["2023-07-18"] * 5


def test_parse_dates_leaves_ambiguous_dates_alone():
    formats = ["%m/%d/%Y", "%d/%m/%Y"]
    result, _ = run_one(date_rule(formats), ["03/04/2025", "25/04/2025"])
    assert result == ["03/04/2025", "2025-04-25"]


def test_parse_dates_leaves_unreadable_values_alone():
    result, _ = run_one(date_rule(), ["not a date"])
    assert result == ["not a date"]


def test_missing_values_become_blank():
    result, _ = run_one(date_rule(), ["N/A", "-", ""])
    assert result == ["", "", ""]
    result, _ = run_one(number_rule(), ["N/A", "unknown"])
    assert result == ["", ""]


def test_to_number_strips_symbols_and_uses_two_decimals():
    result, _ = run_one(number_rule(), ["₱1,338.60", "PHP 566.99", " 2,481.04", "1200"])
    assert result == ["1338.60", "566.99", "2481.04", "1200.00"]


def test_to_number_can_use_whole_numbers():
    result, _ = run_one(number_rule(decimals=0), ["45", "-5", "N/A"])
    assert result == ["45", "-5", ""]


def test_to_number_leaves_text_alone():
    result, _ = run_one(number_rule(), ["Makati"])
    assert result == ["Makati"]


def test_running_the_same_rules_twice_changes_nothing_the_second_time():
    df = pd.DataFrame({"x": ["07/18/2023", "N/A", "March 07, 2022"]})
    rules = [date_rule()]
    once, _ = apply_rules(df, rules)
    twice, changes = apply_rules(once, rules)
    assert once["x"].tolist() == twice["x"].tolist()
    assert changes == []