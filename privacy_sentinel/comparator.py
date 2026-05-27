"""Simple comparator for privacy labels."""
from typing import Dict, Any


def normalize_list_field(value: Any):
    if value is None:
        return set()
    if isinstance(value, str):
        parts = [p.strip().lower() for p in value.split(",") if p.strip()]
        return set(parts)
    if isinstance(value, (list, tuple, set)):
        return set([str(p).strip().lower() for p in value if str(p).strip()])
    return set()


def compare_labels(label_a: Dict, label_b: Dict) -> Dict:
    """Compare two labels (dict-like) and return a small report.

    Expected keys: 'data_categories', 'data_types' (either lists or comma-separated strings).
    """
    a_cats = normalize_list_field(label_a.get("data_categories"))
    b_cats = normalize_list_field(label_b.get("data_categories"))
    a_types = normalize_list_field(label_a.get("data_types"))
    b_types = normalize_list_field(label_b.get("data_types"))

    cat_overlap = a_cats & b_cats
    type_overlap = a_types & b_types

    cat_union = a_cats | b_cats
    type_union = a_types | b_types

    cat_consistency = (len(cat_overlap) / len(cat_union)) if cat_union else 1.0
    type_consistency = (len(type_overlap) / len(type_union)) if type_union else 1.0

    return {
        "categories": {
            "a": sorted(a_cats),
            "b": sorted(b_cats),
            "overlap": sorted(cat_overlap),
            "consistency": cat_consistency,
        },
        "types": {
            "a": sorted(a_types),
            "b": sorted(b_types),
            "overlap": sorted(type_overlap),
            "consistency": type_consistency,
        },
        "overall_consistency": (cat_consistency + type_consistency) / 2.0,
    }


if __name__ == "__main__":
    a = {"data_categories": "analytics, diagnostics", "data_types": "location, identifiers"}
    b = {"data_categories": "analytics", "data_types": "identifiers, contacts"}
    print(compare_labels(a, b))
