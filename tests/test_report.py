"""Tests for report rendering: JSON shape, Markdown text, HTML safety."""

from __future__ import annotations

import json

from a11y_auditor.models import AuditResult, Node, Violation
from a11y_auditor.report import to_dict, to_html, to_json, to_markdown


def sample_result() -> AuditResult:
    return AuditResult(
        url="https://example.com/",
        title="Example <Page>",
        scanned_at="2026-01-01 00:00 UTC",
        duration_ms=1234,
        pass_count=20,
        incomplete_count=2,
        violations=[
            Violation(
                id="image-alt",
                impact="critical",
                help="Images must have alternate text",
                description="Ensure <img> elements have alternate text.",
                help_url="https://dequeuniversity.com/rules/axe/4.14/image-alt",
                tags=["wcag2a", "wcag111"],
                nodes=[
                    Node(target=["img.hero"], html='<img src="a.png">', summary="Add alt text"),
                    Node(target=["img.logo"], html='<img src="b.png">'),
                ],
            ),
            Violation(
                id="color-contrast",
                impact="serious",
                help="Elements must meet minimum color contrast",
                description="Text needs enough contrast.",
                help_url="https://dequeuniversity.com/rules/axe/4.14/color-contrast",
                tags=["wcag2aa", "wcag143"],
                nodes=[Node(target=["p.lead"], html='<p class="lead">Hi</p>')],
            ),
        ],
    )


def test_to_dict_has_expected_top_level_keys():
    data = to_dict(sample_result())
    for key in (
        "url",
        "title",
        "scanned_at",
        "score",
        "grade",
        "verdict",
        "rules_failed",
        "elements_affected",
        "rules_passed",
        "by_impact",
        "violations",
    ):
        assert key in data


def test_to_dict_counts_match_the_data():
    data = to_dict(sample_result())
    assert data["rules_failed"] == 2
    assert data["elements_affected"] == 3
    assert data["rules_passed"] == 20
    assert data["by_impact"]["critical"] == 1
    assert data["by_impact"]["serious"] == 1


def test_to_dict_sorts_worst_impact_first():
    data = to_dict(sample_result())
    assert [v["impact"] for v in data["violations"]] == ["critical", "serious"]


def test_clean_page_scores_100_in_report():
    result = sample_result()
    result.violations = []
    data = to_dict(result)
    assert data["score"] == 100
    assert data["grade"] == "A"


def test_json_round_trips():
    parsed = json.loads(to_json(sample_result()))
    assert parsed["url"] == "https://example.com/"
    assert parsed["violations"][0]["id"] == "image-alt"


def test_markdown_contains_key_lines():
    md = to_markdown(sample_result())
    assert "# Accessibility report" in md
    assert "https://example.com/" in md
    assert "image-alt" in md
    assert "color-contrast" in md
    assert "img.hero" in md


def test_markdown_handles_no_violations():
    result = sample_result()
    result.violations = []
    md = to_markdown(result)
    assert "No automated accessibility violations were found." in md


def test_html_escapes_page_content():
    html_out = to_html(sample_result())
    # The page title contains angle brackets and must not be injected as a tag.
    assert "Example &lt;Page&gt;" in html_out
    assert "Example <Page>" not in html_out


def test_html_is_standalone_document():
    html_out = to_html(sample_result())
    assert html_out.lstrip().startswith("<!DOCTYPE html>")
    assert "<style>" in html_out
    assert html_out.rstrip().endswith("</html>")
