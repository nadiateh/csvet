import pandas as pd

from csvet.reuse import find_unseen, learn_known_values, missing_columns
from csvet.rules import FlagRange, MapValues, NormalizeText


def title_city():
    return NormalizeText(type="normalize_text", column="city", case="title", reason="x")


def names_rule():
    return NormalizeText(type="normalize_text", column="full_name", case="title", reason="x")


def age_rule():
    return FlagRange(type="flag_range", column="age", min_value=1, max_value=120, reason="x")


# ---------- missing_columns ----------


def test_missing_columns_lists_what_the_new_file_lacks():
    df = pd.DataFrame({"city": ["Pasig"]})
    assert missing_columns([title_city(), age_rule(), age_rule()], df) == ["age"]


def test_missing_columns_is_empty_when_everything_is_there():
    df = pd.DataFrame({"city": ["Pasig"], "age": ["30"]})
    assert missing_columns([title_city(), age_rule()], df) == []


# ---------- learn_known_values ----------


def test_learn_known_values_keeps_sorted_distinct_labels_without_blanks():
    cleaned = pd.DataFrame({"city": ["Pasig", "Makati", "Pasig", ""]})
    assert learn_known_values(cleaned, [title_city()]) == {"city": ["Makati", "Pasig"]}


def test_learn_known_values_ignores_columns_without_label_rules():
    cleaned = pd.DataFrame({"city": ["Pasig"], "age": ["30"]})
    assert "age" not in learn_known_values(cleaned, [title_city(), age_rule()])


def test_learn_known_values_never_stores_sensitive_columns():
    cleaned = pd.DataFrame({"full_name": ["Ana Reyes"]})
    assert learn_known_values(cleaned, [names_rule()]) == {}


def test_learn_known_values_skips_columns_with_too_many_values():
    cleaned = pd.DataFrame({"city": [f"Town {i}" for i in range(31)]})
    assert learn_known_values(cleaned, [title_city()]) == {}


def test_learn_known_values_counts_map_values_columns_too():
    rule = MapValues(type="map_values", column="plan", mapping={"Prem": "Premium"}, reason="x")
    cleaned = pd.DataFrame({"plan": ["Premium", "Basic"]})
    assert learn_known_values(cleaned, [rule]) == {"plan": ["Basic", "Premium"]}


# ---------- find_unseen ----------


def test_find_unseen_reports_new_values_with_counts():
    known = {"city": ["Makati", "Pasig"]}
    cleaned = pd.DataFrame({"city": ["Pasig", "Q City", "Q City", "Makati"]})
    assert find_unseen(cleaned, known) == {"city": {"Q City": 2}}


def test_find_unseen_is_empty_when_everything_was_seen():
    known = {"city": ["Makati", "Pasig"]}
    cleaned = pd.DataFrame({"city": ["Pasig", "Makati", ""]})
    assert find_unseen(cleaned, known) == {}


def test_find_unseen_ignores_known_columns_missing_from_the_file():
    assert find_unseen(pd.DataFrame({"age": ["30"]}), {"city": ["Pasig"]}) == {}