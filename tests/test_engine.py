import pandas as pd
import pytest

from csvet.engine import apply_rules
from csvet.rules import MapValues, NormalizeText

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