"""Simple scoring engine for Privacy Sentinel."""
from typing import Dict


GENERIC_TERMS = {"data", "information", "personal data", "info", "other"}


def completeness_score(label: Dict) -> float:
    # simple completeness: proportion of expected fields present
    fields = ["data_categories", "data_types"]
    present = sum(1 for f in fields if label.get(f))
    return present / len(fields)


def specificity_score(label: Dict) -> float:
    # penalise generic terms in data_types
    types = label.get("data_types") or ""
    if isinstance(types, (list, tuple, set)):
        items = [t.strip().lower() for t in types]
    else:
        items = [t.strip().lower() for t in str(types).split(",") if t.strip()]
    if not items:
        return 0.0
    generic = sum(1 for it in items if it in GENERIC_TERMS)
    return max(0.0, 1.0 - (generic / len(items)))


def consistency_score(comp_report: Dict) -> float:
    # use the overall_consistency from comparator
    return float(comp_report.get("overall_consistency", 0.0))


def calculate_scores(label_a: Dict, label_b: Dict, comp_report: Dict) -> Dict:
    c_a = completeness_score(label_a)
    c_b = completeness_score(label_b)
    completeness = (c_a + c_b) / 2.0

    s_a = specificity_score(label_a)
    s_b = specificity_score(label_b)
    specificity = (s_a + s_b) / 2.0

    consistency = consistency_score(comp_report)

    overall = (0.4 * completeness) + (0.3 * specificity) + (0.3 * consistency)

    return {
        "completeness": completeness,
        "specificity": specificity,
        "consistency": consistency,
        "overall": overall,
    }


if __name__ == "__main__":
    from privacy_sentinel.comparator import compare_labels

    a = {"data_categories": "analytics, diagnostics", "data_types": "data, identifiers"}
    b = {"data_categories": "analytics", "data_types": "identifiers, contacts"}
    comp = compare_labels(a, b)
    print(calculate_scores(a, b, comp))
