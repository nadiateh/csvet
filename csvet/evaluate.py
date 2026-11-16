from csvet.engine import apply_rules


def column_scores(messy, cleaned, truth):
    scores = {}
    for column in truth.columns:
        if column not in cleaned.columns:
            continue
        was_right = messy[column] == truth[column]
        is_right = cleaned[column] == truth[column]
        scores[column] = {
            "before": int(was_right.sum()),
            "after": int(is_right.sum()),
            "broken": int((was_right & ~is_right).sum()),
        }
    return scores


def expected_flags(truth):
    expected = set()
    if "expected_flags" not in truth.columns:
        return expected
    for row, text in truth["expected_flags"].items():
        for item in text.split(";"):
            if item:
                expected.add((row, item.split(":")[0]))
    return expected


def found_flags(log):
    return {(entry["row"], entry["column"]) for entry in log if entry["action"] == "flagged"}


def flag_report(log, truth):
    expected = expected_flags(truth)
    found = found_flags(log)
    return {
        "expected": len(expected),
        "raised": len(found),
        "correct": len(expected & found),
        "missed": len(expected - found),
        "false_alarms": len(found - expected),
    }


def evaluate(messy, truth, rules):
    cleaned, log = apply_rules(messy, rules)
    scores = column_scores(messy, cleaned, truth)
    cells = len(truth) * len(scores)
    return {
        "scores": scores,
        "cells": cells,
        "accuracy_before": sum(s["before"] for s in scores.values()) / cells,
        "accuracy_after": sum(s["after"] for s in scores.values()) / cells,
        "broken": sum(s["broken"] for s in scores.values()),
        "flags": flag_report(log, truth),
        "changed": sum(1 for e in log if e["action"] == "changed"),
        "flagged": sum(1 for e in log if e["action"] == "flagged"),
    }


def format_report(result):
    lines = [f"{'column':<15}{'before':>8}{'after':>8}{'broken':>8}"]
    for column, score in result["scores"].items():
        lines.append(
            f"{column:<15}{score['before']:>8}{score['after']:>8}{score['broken']:>8}"
        )
    flags = result["flags"]
    lines += [
        "",
        f"Accuracy: {result['accuracy_before']:.1%} -> {result['accuracy_after']:.1%} "
        f"({result['cells']:,} cells)",
        f"Correct values the rules made WORSE: {result['broken']}",
        f"Flags: expected {flags['expected']}, raised {flags['raised']} "
        f"(correct {flags['correct']}, missed {flags['missed']}, "
        f"false alarms {flags['false_alarms']})",
        f"Values changed: {result['changed']}   Flagged for review: {result['flagged']}",
    ]
    return "\n".join(lines)