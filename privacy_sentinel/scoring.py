from typing import Dict

GENERIC_TERMS = {"data", "information", "personal data", "info", "other"}


def completeness_score(label: Dict) -> float:
    fields = ["data_categories", "data_types", "tracking_disclosed", "shares_data", "data_deletion_option"]
    present = sum(1 for f in fields if label.get(f))
    return present / len(fields)


def specificity_score(label: Dict) -> float:
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
    return float(comp_report.get("overall_consistency", 0.0))


def risk_flag(overall: float, high_threshold: float = 0.5, medium_threshold: float = 0.7) -> str:
    if overall < high_threshold:
        return "High"
    if overall < medium_threshold:
        return "Medium"
    return "Low"


def calculate_scores(label_a: Dict, label_b: Dict, comp_report: Dict,
                     high_threshold: float = 0.5, medium_threshold: float = 0.7) -> Dict:
    completeness = (completeness_score(label_a) + completeness_score(label_b)) / 2.0
    specificity = (specificity_score(label_a) + specificity_score(label_b)) / 2.0
    consistency = consistency_score(comp_report)

    overall = (0.4 * completeness) + (0.3 * specificity) + (0.3 * consistency)
    flag = risk_flag(overall, high_threshold, medium_threshold)

    return {
        "completeness": round(completeness, 3),
        "specificity": round(specificity, 3),
        "consistency": round(consistency, 3),
        "overall": round(overall, 3),
        "risk_flag": flag,
    }


if __name__ == "__main__":
    from privacy_sentinel.comparator import compare_labels
    a = {"data_categories": "analytics, diagnostics", "data_types": "data, identifiers",
         "tracking_disclosed": "Yes", "shares_data": "Yes", "data_deletion_option": "No"}
    b = {"data_categories": "analytics", "data_types": "identifiers, contacts",
         "tracking_disclosed": "Yes", "shares_data": "No", "data_deletion_option": "No"}
    comp = compare_labels(a, b)
    print(calculate_scores(a, b, comp))
