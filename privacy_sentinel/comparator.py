from typing import Dict, Any


def normalize_list_field(value: Any):
    # turns "Location, Contacts , email" into {"location", "contacts", "email"}
    # so casing/spacing differences between iOS and Android entries don't count as mismatches
    if value is None:
        return set()
    if isinstance(value, str):
        parts = [p.strip().lower() for p in value.split(",") if p.strip()]
        return set(parts)
    if isinstance(value, (list, tuple, set)):
        return set([str(p).strip().lower() for p in value if str(p).strip()])
    return set()


def compare_labels(label_a: Dict, label_b: Dict) -> Dict:
    """Compare two privacy labels and return a structured report.

    Compares data_categories, data_types, and the three boolean disclosure
    fields (tracking_disclosed, shares_data, data_deletion_option).
    Consistency is calculated using Jaccard similarity for list fields.
    """
    a_cats = normalize_list_field(label_a.get("data_categories"))
    b_cats = normalize_list_field(label_b.get("data_categories"))
    a_types = normalize_list_field(label_a.get("data_types"))
    b_types = normalize_list_field(label_b.get("data_types"))

    cat_union = a_cats | b_cats
    type_union = a_types | b_types

    # Jaccard similarity: what they agree on, divided by everything either one mentioned.
    # 1.0 = identical lists, 0.0 = no overlap at all. Falls back to 1.0 if both sides are
    # empty — nothing was declared, so there's nothing to disagree about either.
    cat_consistency = (len(a_cats & b_cats) / len(cat_union)) if cat_union else 1.0
    type_consistency = (len(a_types & b_types) / len(type_union)) if type_union else 1.0

    # the Yes/No fields can't use Jaccard — just check if both platforms gave the same answer

    bool_fields = ["tracking_disclosed", "shares_data", "data_deletion_option"]
    bool_results = {}
    match_count = 0
    present_count = 0
    for field in bool_fields:
        a_val = (label_a.get(field) or "").strip().lower()
        b_val = (label_b.get(field) or "").strip().lower()
        if a_val and b_val:
            present_count += 1
            matched = a_val == b_val
            if matched:
                match_count += 1
            bool_results[field] = {"a": a_val, "b": b_val, "match": matched}
        else:
            bool_results[field] = {"a": a_val or "not stated", "b": b_val or "not stated", "match": None}

    bool_consistency = (match_count / present_count) if present_count else 1.0
    overall_consistency = (cat_consistency + type_consistency + bool_consistency) / 3.0

    return {
        "categories": {
            "a": sorted(a_cats),
            "b": sorted(b_cats),
            "overlap": sorted(a_cats & b_cats),
            "consistency": cat_consistency,
        },
        "types": {
            "a": sorted(a_types),
            "b": sorted(b_types),
            "overlap": sorted(a_types & b_types),
            "consistency": type_consistency,
        },
        "boolean_fields": bool_results,
        "boolean_consistency": bool_consistency,
        "overall_consistency": overall_consistency,
    }


if __name__ == "__main__":
    a = {"data_categories": "analytics, diagnostics", "data_types": "location, identifiers",
         "tracking_disclosed": "Yes", "shares_data": "Yes", "data_deletion_option": "No"}
    b = {"data_categories": "analytics", "data_types": "identifiers, contacts",
         "tracking_disclosed": "Yes", "shares_data": "No", "data_deletion_option": "No"}
    import json
    print(json.dumps(compare_labels(a, b), indent=2))
