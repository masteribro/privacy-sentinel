from privacy_sentinel.scoring import calculate_scores
from privacy_sentinel.comparator import compare_labels


def test_scoring_basic():
    a = {"data_categories": "analytics", "data_types": "identifiers"}
    b = {"data_categories": "analytics", "data_types": "identifiers"}
    comp = compare_labels(a, b)
    scores = calculate_scores(a, b, comp)
    assert scores["overall"] >= 0
    assert 0 <= scores["completeness"] <= 1
