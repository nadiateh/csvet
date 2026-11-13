import json

import pytest

from csvet.privacy import mask_profile
from csvet.proposer import (
    SYSTEM_PROMPT,
    build_messages,
    check_rules,
    clean_reply,
    propose_rules,
)
from csvet.rules import RuleSet


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, messages):
        self.calls.append(messages)
        return self.replies.pop(0)


def make_profile():
    profile = {
        "row_count": 3,
        "columns": {
            "full_name": {"top_values": [{"value": "Juan Santos", "count": 3}]},
            "city": {"top_values": [{"value": "QC", "count": 2}, {"value": "Makati", "count": 1}]},
        },
    }
    return mask_profile(profile)


GOOD = json.dumps({"rules": [
    {"type": "normalize_text", "column": "city", "case": "title", "reason": "Mixed casing"},
]})
BAD_TYPE = json.dumps({"rules": [{"type": "delete_rows", "column": "city", "reason": "x"}]})
BAD_COLUMN = json.dumps({"rules": [
    {"type": "normalize_text", "column": "town", "case": "title", "reason": "x"},
]})
MAP_MASKED = json.dumps({"rules": [
    {"type": "map_values", "column": "full_name", "mapping": {"juan": "Juan"}, "reason": "x"},
]})


def test_prompt_describes_every_rule_type():
    for name in ["normalize_text", "map_values", "parse_dates", "to_number", "flag_range"]:
        assert name in SYSTEM_PROMPT


def test_messages_contain_the_profile_but_not_masked_values():
    messages = build_messages(make_profile())
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Makati" in messages[1]["content"]
    assert "Juan" not in messages[1]["content"]


def test_clean_reply_removes_code_fences():
    assert clean_reply('```json\n{"rules": []}\n```') == '{"rules": []}'
    assert clean_reply('  {"rules": []}  ') == '{"rules": []}'


def test_valid_first_reply_is_accepted():
    llm = FakeLLM([GOOD])
    rule_set, attempts = propose_rules(make_profile(), llm)
    assert attempts == 1
    assert isinstance(rule_set, RuleSet)
    assert len(llm.calls) == 1


def test_reply_in_code_fences_is_accepted():
    llm = FakeLLM(["```json\n" + GOOD + "\n```"])
    _, attempts = propose_rules(make_profile(), llm)
    assert attempts == 1


def test_bad_rule_type_is_sent_back_and_corrected():
    llm = FakeLLM([BAD_TYPE, GOOD])
    _, attempts = propose_rules(make_profile(), llm)
    assert attempts == 2
    feedback = llm.calls[1][-1]["content"]
    assert "rejected" in feedback
    assert "delete_rows" in feedback
    assert llm.calls[1][-2]["content"] == BAD_TYPE


def test_text_that_is_not_json_is_sent_back():
    llm = FakeLLM(["Sure! Here are some rules.", GOOD])
    _, attempts = propose_rules(make_profile(), llm)
    assert attempts == 2


def test_unknown_column_is_sent_back():
    llm = FakeLLM([BAD_COLUMN, GOOD])
    _, attempts = propose_rules(make_profile(), llm)
    assert attempts == 2
    assert "'town'" in llm.calls[1][-1]["content"]


def test_gives_up_after_max_attempts():
    llm = FakeLLM([BAD_TYPE, BAD_TYPE, BAD_TYPE])
    with pytest.raises(ValueError):
        propose_rules(make_profile(), llm, max_attempts=3)
    assert len(llm.calls) == 3


def test_check_rules_finds_unknown_columns():
    rule_set = RuleSet.model_validate_json(BAD_COLUMN)
    problems = check_rules(rule_set, make_profile())
    assert len(problems) == 1
    assert "town" in problems[0]


def test_check_rules_rejects_map_values_on_masked_columns():
    rule_set = RuleSet.model_validate_json(MAP_MASKED)
    problems = check_rules(rule_set, make_profile())
    assert len(problems) == 1
    assert "masked" in problems[0]


def test_check_rules_accepts_good_rules():
    rule_set = RuleSet.model_validate_json(GOOD)
    assert check_rules(rule_set, make_profile()) == []