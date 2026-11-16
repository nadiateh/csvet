import pandas as pd

from csvet.evaluate import (
    column_scores,
    evaluate,
    expected_flags,
    flag_report,
    format_report,
)
from csvet.rules import NormalizeText, ToNumber


def make_frames():
    messy = pd.DataFrame({"id": ["1", "2", "3"], "city": ["qc", " Makati", "Pasig"]})
    truth = pd.DataFrame({
        "id": ["1", "2", "3"],
        "city": ["QC", "Makati", "Pasig"],
        "expected_flags": ["", "city:invalid", ""],
    })
    return messy, truth


def test_column_scores_count_before_after_and_broken():
    messy, truth = make_frames()
    cleaned = pd.DataFrame({"id": ["1.00", "2", "3"], "city": ["QC", "Makati", "pasig"]})
    scores = column_scores(messy, cleaned, truth)
    assert scores["id"] == {"before": 3, "after": 2, "broken": 1}
    assert scores["city"] == {"before": 1, "after": 2, "broken": 1}
    assert "expected_flags" not in scores


def test_expected_flags_reads_the_answer_key():
    _, truth = make_frames()
    assert expected_flags(truth) == {(1, "city")}


def test_expected_flags_is_empty_without_the_column():
    assert expected_flags(pd.DataFrame({"a": ["1"]})) == set()


def test_flag_report_counts_correct_missed_and_false_alarms():
    _, truth = make_frames()
    log = [
        {"action": "flagged", "row": 1, "column": "city"},
        {"action": "flagged", "row": 2, "column": "city"},
        {"action": "changed", "row": 0, "column": "city"},
    ]
    report = flag_report(log, truth)
    assert report == {"expected": 1, "raised": 2, "correct": 1, "missed": 0, "false_alarms": 1}


def test_evaluate_shows_an_improvement():
    messy, truth = make_frames()
    rule = NormalizeText(type="normalize_text", column="city", case="keep", reason="x")
    result = evaluate(messy, truth, [rule])
    assert result["accuracy_after"] > result["accuracy_before"]
    assert result["broken"] == 0


def test_evaluate_catches_a_rule_that_damages_good_data():
    messy, truth = make_frames()
    rule = ToNumber(type="to_number", column="id", decimals=2, reason="x")
    result = evaluate(messy, truth, [rule])
    assert result["scores"]["id"]["broken"] == 3
    assert result["broken"] == 3


def test_format_report_has_the_key_lines():
    messy, truth = make_frames()
    rule = ToNumber(type="to_number", column="id", decimals=2, reason="x")
    text = format_report(evaluate(messy, truth, [rule]))
    assert "Accuracy:" in text
    assert "made WORSE: 3" in text
    assert "Flags:" in text