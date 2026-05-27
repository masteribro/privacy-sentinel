from privacy_sentinel.comparator import compare_labels


def test_compare_simple_overlap():
    a = {"data_categories": "analytics, diagnostics", "data_types": "location, identifiers"}
    b = {"data_categories": "analytics", "data_types": "identifiers, contacts"}
    r = compare_labels(a, b)
    assert r["categories"]["consistency"] == 0.5
    assert 0 <= r["overall_consistency"] <= 1.0
