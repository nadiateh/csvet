from csvet.privacy import is_sensitive_column, mask_profile

def test_detects_sensitive_column_by_name():
    assert is_sensitive_column("full_name", [])
    assert is_sensitive_column("Customer Email", [])
    assert not is_sensitive_column("city", ["Makati", "QC"])


def test_detects_emails_by_value():
    assert is_sensitive_column("info", ["juan@example.com", "ana@example.org"])
    assert not is_sensitive_column("info", ["Basic", "Premium"])


def test_mask_profile_hides_values_and_keeps_original():
    profile = {
        "row_count": 2,
        "columns": {
            "full_name": {"top_values": [{"value": "Juan Santos", "count": 2}]},
            "city": {"top_values": [{"value": "QC", "count": 2}]},
        },
    }
    masked = mask_profile(profile)

    assert masked["columns"]["full_name"]["top_values"] == []
    assert masked["columns"]["full_name"]["masked"] is True
    assert masked["columns"]["city"]["top_values"][0]["value"] == "QC"
    assert profile["columns"]["full_name"]["top_values"] != []