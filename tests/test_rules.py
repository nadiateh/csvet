import pytest
from pydantic import ValidationError

from csvet.rules import (
    MapValues, 
    NormalizeText,
    FlagRange,
    ParseDates,
    RuleSet,
    ToNumber,
    )


def test_valid_normalize_text_rule_is_accepted():
    rule = NormalizeText.model_validate(
        {"type": "normalize_text", "column": "full_name", "case": "title", "reason": "x"}
    )
    assert rule.case == "title"


def test_case_defaults_to_keep():
    rule = NormalizeText.model_validate(
        {"type": "normalize_text", "column": "city", "reason": "x"}
    )
    assert rule.case == "keep"


def test_unknown_case_is_rejected():
    with pytest.raises(ValidationError):
        NormalizeText.model_validate(
            {"type": "normalize_text", "column": "full_name", "case": "sentence", "reason": "x"}
        )


def test_missing_reason_is_rejected():
    with pytest.raises(ValidationError):
        MapValues.model_validate(
            {"type": "map_values", "column": "city", "mapping": {"QC": "Quezon City"}}
        )


def test_empty_mapping_is_rejected():
    with pytest.raises(ValidationError):
        MapValues.model_validate(
            {"type": "map_values", "column": "city", "mapping": {}, "reason": "x"}
        )

def test_rule_set_picks_the_right_rule_type():
    rule_set = RuleSet.model_validate({
        "rules": [
            {"type": "to_number", "column": "monthly_spend", "reason": "x"},
            {"type": "flag_range", "column": "age", "max_value": 120, "reason": "x"},
        ]
    })
    assert isinstance(rule_set.rules[0], ToNumber)
    assert isinstance(rule_set.rules[1], FlagRange)


def test_unknown_rule_type_is_rejected():
    with pytest.raises(ValidationError):
        RuleSet.model_validate(
            {"rules": [{"type": "delete_rows", "column": "age", "reason": "x"}]}
        )


def test_flag_range_needs_at_least_one_limit():
    with pytest.raises(ValidationError):
        FlagRange.model_validate({"type": "flag_range", "column": "age", "reason": "x"})


def test_flag_range_min_must_not_exceed_max():
    with pytest.raises(ValidationError):
        FlagRange.model_validate(
            {"type": "flag_range", "column": "age", "min_value": 120, "max_value": 0, "reason": "x"}
        )


def test_parse_dates_needs_formats():
    with pytest.raises(ValidationError):
        ParseDates.model_validate(
            {"type": "parse_dates", "column": "signup_date", "input_formats": [], "reason": "x"}
        )

def test_to_number_decimals_defaults_to_two():
    rule = ToNumber.model_validate({"type": "to_number", "column": "x", "reason": "x"})
    assert rule.decimals == 2


def test_to_number_rejects_negative_decimals():
    with pytest.raises(ValidationError):
        ToNumber.model_validate({"type": "to_number", "column": "x", "decimals": -1, "reason": "x"})