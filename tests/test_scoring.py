"""Tests for scoring: weights, caps, grades, verdicts."""

from __future__ import annotations

from a11y_auditor.models import Node, Violation
from a11y_auditor.scoring import (
    IMPACT_WEIGHTS,
    MAX_ELEMENTS_COUNTED,
    SEVERITY_CAPS,
    compute_score,
    count_by_impact,
    grade_for,
    verdict,
)


def make_violation(impact: str, nodes: int = 1, rule_id: str = "rule") -> Violation:
    return Violation(
        id=rule_id,
        impact=impact,
        help="help text",
        description="description",
        help_url="https://example.com/rule",
        nodes=[Node(target=[f"elem-{i}"], html="<div></div>") for i in range(nodes)],
    )


def test_perfect_page_scores_100():
    score, grade = compute_score([])
    assert score == 100
    assert grade == "A"


def test_single_critical_costs_ten():
    score, _ = compute_score([make_violation("critical", nodes=1)])
    assert score == 90


def test_single_serious_costs_six():
    score, _ = compute_score([make_violation("serious", nodes=1)])
    assert score == 100 - IMPACT_WEIGHTS["serious"]


def test_element_count_multiplies_until_cap():
    one = compute_score([make_violation("serious", nodes=1)])[0]
    three = compute_score([make_violation("serious", nodes=MAX_ELEMENTS_COUNTED)])[0]
    many = compute_score([make_violation("serious", nodes=MAX_ELEMENTS_COUNTED * 10)])[0]

    assert three < one
    assert many == three, "the per-rule cap must stop one rule from dominating"


def test_severity_cap_stops_one_category_hiding_the_whole_page():
    violations = [make_violation("critical", nodes=3, rule_id=f"r{i}") for i in range(20)]
    score, grade = compute_score(violations)
    # The critical bucket can only take 50 points, so the floor is not reached.
    assert score == 100 - SEVERITY_CAPS["critical"]
    assert grade == "F"


def test_all_categories_maxed_scores_zero():
    violations = []
    for impact in ("critical", "serious", "moderate", "minor"):
        violations += [
            make_violation(impact, nodes=MAX_ELEMENTS_COUNTED, rule_id=f"{impact}{i}")
            for i in range(10)
        ]
    score, grade = compute_score(violations)
    assert score == 0
    assert grade == "F"


def test_per_severity_caps_add_up_to_a_hundred():
    assert sum(SEVERITY_CAPS.values()) == 100



def test_unknown_impact_falls_back_to_moderate():
    score, _ = compute_score([make_violation("weird", nodes=1)])
    assert score == 100 - IMPACT_WEIGHTS["moderate"]


def test_grade_bands():
    assert grade_for(100) == "A"
    assert grade_for(90) == "A"
    assert grade_for(89) == "B"
    assert grade_for(80) == "B"
    assert grade_for(79) == "C"
    assert grade_for(70) == "C"
    assert grade_for(69) == "D"
    assert grade_for(60) == "D"
    assert grade_for(59) == "F"
    assert grade_for(0) == "F"


def test_count_by_impact_counts_rules_not_elements():
    violations = [
        make_violation("critical", nodes=5),
        make_violation("critical", nodes=2),
        make_violation("minor", nodes=1),
    ]
    counts = count_by_impact(violations)
    assert counts == {"critical": 2, "serious": 0, "moderate": 0, "minor": 1}


def test_count_by_impact_always_has_all_keys():
    counts = count_by_impact([])
    assert set(counts) == {"critical", "serious", "moderate", "minor"}
    assert all(v == 0 for v in counts.values())


def test_verdict_is_non_empty_for_every_band():
    for score in (100, 85, 75, 65, 30):
        assert verdict(score)
