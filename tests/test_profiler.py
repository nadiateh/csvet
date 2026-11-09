import pandas as pd 
from csvet.profiler import (
    is_null_like,
    numeric_stats,
    profile_column,
    to_number,
    value_shape,
)

def test_is_null_like_catches_common_tokens():
    assert is_null_like("")
    assert is_null_like(" N/A ")
    assert is_null_like("unknown")
    assert not is_null_like("Makati")


def test_value_shape_tells_date_formats_apart():
    assert value_shape("2023-07-18") == "9999-99-99"
    assert value_shape("07/18/2023") == "99/99/9999"


def test_value_shape_ignores_name_length():
    assert value_shape("Juan Santos") == value_shape("Maria Garcia")


def test_to_number_handles_peso_formats():
    assert to_number("₱1,338.60") == 1338.6
    assert to_number("PHP 566.99") == 566.99
    assert to_number(" 2,481.04 ") == 2481.04
    assert to_number("Makati") is None
    assert to_number("inf") is None


def test_numeric_stats_skips_text_columns():
    assert numeric_stats(["Makati", "Pasig", "QC"]) is None


def test_profile_column_counts_nulls_and_outliers():
    s = pd.Series(["10", "12", "11", "", "N/A", "9000"])
    p = profile_column(s)
    assert p["null_count"] == 2
    assert p["numeric"]["outlier_count"] == 1