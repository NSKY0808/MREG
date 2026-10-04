from decimal import Decimal

from mreg.models.policy import Rule


def satisfies(value: float, rule: Rule) -> bool:
    """Exact comparison of decimal representations, without hidden tolerance."""
    v, threshold = Decimal(str(value)), Decimal(str(rule.threshold))
    if rule.operator == "ge":
        return v >= threshold if rule.inclusive else v > threshold
    return v <= threshold if rule.inclusive else v < threshold


def regression(candidate: float, baseline: float, rule: Rule) -> float:
    b, c = Decimal(str(baseline)), Decimal(str(candidate))
    change = b - c if rule.direction == "higher" else c - b
    if rule.unit == "relative_percent":
        return float(change / abs(b) * 100)
    return float(change * 100 if rule.unit == "percentage_points" else change)
