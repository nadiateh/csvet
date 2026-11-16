import json

import pandas as pd
import pytest

from csvet.review import edit_rule, preview_rule, review_rules
from csvet.rules import FlagRange, MapValues, NormalizeText, ParseDates


def title_rule():
    return NormalizeText(type="normalize_text", column="city", case="title", reason="x")


def qc_rule(key="Qc"):
    return MapValues(type="map_values", column="city", mapping={key: "Quezon City"}, reason="x")


def make_df():
    return pd.DataFrame({"city": ["MAKATI", "MAKATI", "Pasig", "QC"]})


def scripted(answers):
    items = iter(answers)
    return lambda prompt: next(items)


def run_review(rules, answers, df=None):
    shown = []
    result = review_rules(
        make_df() if df is None else df, rules, scripted(answers), show=shown.append
    )
    return result, shown


# ---------- preview ----------


def test_preview_counts_and_groups_identical_changes():
    preview = preview_rule(make_df(), title_rule(), 1)
    assert preview["changed"] == 3
    assert preview["flagged"] == 0
    assert preview["examples"][0]["before"] == "MAKATI"
    assert preview["examples"][0]["count"] == 2


def test_preview_does_not_change_the_data():
    df = make_df()
    preview_rule(df, title_rule(), 1)
    assert df["city"].tolist() == ["MAKATI", "MAKATI", "Pasig", "QC"]


def test_preview_reports_flags():
    df = pd.DataFrame({"age": ["25", "230"]})
    rule = FlagRange(type="flag_range", column="age", min_value=1, max_value=120, reason="x")
    preview = preview_rule(df, rule, 1)
    assert preview["flagged"] == 1
    assert preview["examples"][0]["action"] == "flagged"


# ---------- edit ----------


def test_edit_rule_changes_one_setting_and_keeps_the_original():
    rule = FlagRange(type="flag_range", column="age", min_value=0, max_value=120, reason="x")
    edited = edit_rule(rule, "min_value", "1")
    assert edited.min_value == 1
    assert rule.min_value == 0


def test_edit_rule_accepts_lists_and_dictionaries():
    rule = ParseDates(type="parse_dates", column="d", input_formats=["%m/%d/%Y", "%d/%m/%Y"], reason="x")
    edited = edit_rule(rule, "input_formats", '["%m/%d/%Y"]')
    assert edited.input_formats == ["%m/%d/%Y"]
    edited = edit_rule(qc_rule(), "mapping", '{"Qc": "Quezon City", "Q.C": "Quezon City"}')
    assert len(edited.mapping) == 2


def test_edit_rule_refuses_type_and_column():
    with pytest.raises(ValueError, match="only change"):
        edit_rule(title_rule(), "type", '"map_values"')
    with pytest.raises(ValueError, match="only change"):
        edit_rule(title_rule(), "column", '"age"')


def test_edit_rule_refuses_unknown_fields():
    with pytest.raises(ValueError, match="only change"):
        edit_rule(title_rule(), "colour", '"red"')


def test_edit_rule_refuses_text_that_is_not_json():
    with pytest.raises(ValueError, match="JSON"):
        edit_rule(title_rule(), "case", "title")


def test_edit_rule_refuses_values_that_break_the_rule():
    rule = FlagRange(type="flag_range", column="age", min_value=0, max_value=120, reason="x")
    with pytest.raises(ValueError):
        edit_rule(rule, "min_value", "500")
    with pytest.raises(ValueError):
        edit_rule(title_rule(), "case", '"sentence"')


# ---------- review loop ----------


def test_approved_rules_are_kept_and_applied():
    (approved, decisions, current), _ = run_review([title_rule()], ["a"])
    assert approved == [title_rule()]
    assert current["city"].tolist() == ["Makati", "Makati", "Pasig", "Qc"]
    assert decisions[0]["decision"] == "approved"


def test_rejected_rules_are_dropped_and_not_applied():
    (approved, decisions, current), _ = run_review([title_rule()], ["r"])
    assert approved == []
    assert current["city"].tolist() == ["MAKATI", "MAKATI", "Pasig", "QC"]
    assert decisions[0]["decision"] == "rejected"


def test_later_previews_see_the_effect_of_earlier_approvals():
    (approved, _, current), shown = run_review([title_rule(), qc_rule("Qc")], ["a", "a"])
    assert current["city"].tolist() == ["Makati", "Makati", "Pasig", "Quezon City"]
    assert any("would change 1 values" in line for line in shown)


def test_rejecting_an_earlier_rule_changes_what_a_later_rule_can_do():
    _, shown = run_review([title_rule(), qc_rule("Qc")], ["r", "a"])
    assert any("would change 0 values" in line for line in shown)


def test_edit_then_approve_keeps_the_edited_rule():
    rule = FlagRange(type="flag_range", column="age", min_value=0, max_value=120, reason="x")
    df = pd.DataFrame({"age": ["0", "25"]})
    (approved, decisions, _), _ = run_review([rule], ["e", "min_value", "1", "a"], df)
    assert approved[0].min_value == 1
    assert decisions[0]["edited"] is True


def test_a_failed_edit_keeps_the_rule_and_asks_again():
    answers = ["e", "case", "sentence", "e", "case", '"upper"', "a"]
    (approved, _, current), shown = run_review([title_rule()], answers)
    assert approved[0].case == "upper"
    assert any("Could not change it" in line for line in shown)


def test_unknown_answers_ask_again():
    (approved, _, _), shown = run_review([title_rule()], ["maybe", "a"])
    assert len(approved) == 1
    assert any("Please type" in line for line in shown)


def test_decisions_are_recorded_for_every_rule():
    (_, decisions, _), _ = run_review([title_rule(), qc_rule()], ["a", "r"])
    assert [d["decision"] for d in decisions] == ["approved", "rejected"]
    assert decisions[0]["rule_number"] == 1
    assert decisions[1]["type"] == "map_values"
    json.dumps(decisions)