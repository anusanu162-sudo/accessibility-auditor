"""Turn a list of violations into a single score and letter grade."""

from __future__ import annotations

from .models import Violation

# How many points each failed rule costs.
IMPACT_WEIGHTS: dict[str, int] = {
    "critical": 10,
    "serious": 6,
    "moderate": 3,
    "minor": 1,
}

# A rule that affects 40 images should not cost 40 times as much as one image.
# We stop counting after this many affected elements per rule.
MAX_ELEMENTS_COUNTED = 3

# Even a page with 30 critical rules should not automatically score zero: that
# hides how much else the page gets right. Each severity can only take away so
# much. The four caps add up to 100, so 0 is still possible.
SEVERITY_CAPS: dict[str, int] = {
    "critical": 50,
    "serious": 30,
    "moderate": 15,
    "minor": 5,
}

GRADE_BANDS: list[tuple[int, str]] = [
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
]


def grade_for(score: int) -> str:
    """Map a 0-100 score to a letter grade."""
    for threshold, grade in GRADE_BANDS:
        if score >= threshold:
            return grade
    return "F"


def compute_score(violations: list[Violation]) -> tuple[int, str]:
    """Return (score, grade) for a page.

    Each failed rule costs points based on its impact. The cost grows with the
    number of affected elements, but only up to MAX_ELEMENTS_COUNTED, so one
    widespread rule cannot drive the whole score to zero by itself. Each severity
    level is also capped (SEVERITY_CAPS) so one crowded category cannot hide
    everything the page gets right.
    """
    totals = {level: 0 for level in IMPACT_WEIGHTS}
    for violation in violations:
        level = violation.impact if violation.impact in IMPACT_WEIGHTS else "moderate"
        counted = min(max(len(violation.nodes), 1), MAX_ELEMENTS_COUNTED)
        totals[level] += IMPACT_WEIGHTS[level] * counted

    deduction = sum(min(totals[level], SEVERITY_CAPS[level]) for level in totals)

    score = max(0, 100 - deduction)
    return score, grade_for(score)


def count_by_impact(violations: list[Violation]) -> dict[str, int]:
    """Count failed rules per impact level, always returning all four keys."""
    counts = {level: 0 for level in IMPACT_WEIGHTS}
    for violation in violations:
        if violation.impact in counts:
            counts[violation.impact] += 1
        else:
            counts["moderate"] += 1
    return counts


def verdict(score: int) -> str:
    """A one-line human summary of the score."""
    if score >= 90:
        return "Good - only minor problems found."
    if score >= 80:
        return "Fair - several issues should be fixed."
    if score >= 70:
        return "Needs work - real barriers for some users."
    if score >= 60:
        return "Poor - many users will struggle."
    return "Failing - serious barriers across the page."
