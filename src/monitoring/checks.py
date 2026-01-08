from __future__ import annotations


def evaluate_thresholds(
    metrics: dict[str, float], thresholds: dict[str, float]
) -> list[tuple[str, float, float]]:
    """
    Compare metrics against threshold requirements.
    Returns a list of (key, value, threshold) that violate the rule.

    Supported threshold semantics (by key name):
      - max_* : metric must be <= threshold (for positive metrics)
                For negative metrics like drawdown, threshold value is also negative,
                and we check if metric is MORE negative (worse).
      - min_* : metric must be >= threshold
    """
    issues: list[tuple[str, float, float]] = []
    for key, th in thresholds.items():
        metric_key = key
        cmp = "eq"
        if key.startswith("max_"):
            metric_key = key[len("max_") :]
            cmp = "le"
        elif key.startswith("min_"):
            metric_key = key[len("min_") :]
            cmp = "ge"

        if metric_key not in metrics:
            # allow non-present keys (e.g., optional metrics)
            continue
        val = metrics[metric_key]
        if cmp == "le":
            # For negative thresholds (e.g., drawdown), "worse" means more negative
            # e.g., -0.30 is worse than -0.15 (threshold), so check val < th
            if th < 0:
                if val < th:
                    issues.append((key, val, th))
            else:
                if val > th:
                    issues.append((key, val, th))
        elif cmp == "ge":
            if val < th:
                issues.append((key, val, th))
        else:
            if val != th:
                issues.append((key, val, th))
    return issues
