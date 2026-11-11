"""Render an AuditResult as Markdown, HTML or plain data."""

from __future__ import annotations

import html
import json
from typing import Any

from .models import AuditResult
from .scoring import compute_score, count_by_impact, verdict

IMPACT_ORDER = ["critical", "serious", "moderate", "minor"]

IMPACT_LABELS = {
    "critical": "Critical",
    "serious": "Serious",
    "moderate": "Moderate",
    "minor": "Minor",
}


def _sorted_violations(result: AuditResult):
    def key(v):
        try:
            return IMPACT_ORDER.index(v.impact)
        except ValueError:
            return len(IMPACT_ORDER)

    return sorted(result.violations, key=lambda v: (key(v), -len(v.nodes), v.id))


def _wcag_tags(tags: list[str]) -> list[str]:
    return [t for t in tags if t.startswith("wcag") or t.startswith("best-practice")]


def _clip(text: str, limit: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def to_dict(result: AuditResult) -> dict[str, Any]:
    """Machine-readable report, ready for JSON."""
    score, grade = compute_score(result.violations)
    return {
        "url": result.url,
        "title": result.title,
        "scanned_at": result.scanned_at,
        "duration_ms": result.duration_ms,
        "score": score,
        "grade": grade,
        "verdict": verdict(score),
        "rules_failed": result.rule_count,
        "elements_affected": result.issue_count,
        "rules_passed": result.pass_count,
        "needs_review": result.incomplete_count,
        "by_impact": count_by_impact(result.violations),
        "violations": [
            {
                "id": v.id,
                "impact": v.impact,
                "help": v.help,
                "description": v.description,
                "help_url": v.help_url,
                "tags": v.tags,
                "element_count": len(v.nodes),
                "elements": [
                    {"selector": n.selector, "html": n.html, "note": n.summary}
                    for n in v.nodes
                ],
            }
            for v in _sorted_violations(result)
        ],
    }


def to_markdown(result: AuditResult) -> str:
    """A readable report for GitHub issues, pull requests or a README."""
    data = to_dict(result)
    lines: list[str] = []

    lines.append(f"# Accessibility report: {data['title'] or data['url']}")
    lines.append("")
    lines.append(f"- **URL:** {data['url']}")
    lines.append(f"- **Scanned:** {data['scanned_at']} ({data['duration_ms']} ms)")
    lines.append(f"- **Score:** {data['score']}/100 (grade {data['grade']})")
    lines.append(f"- **Verdict:** {data['verdict']}")
    lines.append(
        f"- **Rules failed:** {data['rules_failed']}  |  "
        f"**Elements affected:** {data['elements_affected']}  |  "
        f"**Rules passed:** {data['rules_passed']}"
    )
    lines.append("")

    lines.append("## Issues by severity")
    lines.append("")
    lines.append("| Severity | Failed rules |")
    lines.append("| --- | --- |")
    for impact in IMPACT_ORDER:
        lines.append(f"| {IMPACT_LABELS[impact]} | {data['by_impact'][impact]} |")
    lines.append("")

    if not data["violations"]:
        lines.append("No automated accessibility violations were found.")
        return "\n".join(lines)

    lines.append("## Violations")
    lines.append("")

    for index, item in enumerate(data["violations"], start=1):
        lines.append(
            f"### {index}. [{IMPACT_LABELS.get(item['impact'], item['impact'])}] "
            f"`{item['id']}` - {item['help']}"
        )
        lines.append("")
        lines.append(item["description"])
        lines.append("")
        lines.append(f"- Rule reference: {item['help_url']}")
        if item["tags"]:
            lines.append(f"- Tags: {', '.join(_wcag_tags(item['tags']) or item['tags'])}")
        lines.append(f"- Affected elements: {item['element_count']}")
        lines.append("")

        for node in item["elements"]:
            lines.append(f"  - `{node['selector']}`")
            lines.append(f"    ```html\n    {_clip(node['html'])}\n    ```")
            if node["note"]:
                lines.append(f"    {_clip(node['note'], 300)}")
            lines.append("")

    lines.append("---")
    lines.append(
        "Automated checks catch roughly a third to a half of real accessibility "
        "problems. Always test with a keyboard and a screen reader."
    )
    return "\n".join(lines)


def to_html(result: AuditResult) -> str:
    """A standalone, printable HTML report (open it and print to PDF)."""
    data = to_dict(result)
    score = data["score"]
    grade = data["grade"]
    if score >= 90:
        score_color = "#2e7d32"
    elif score >= 70:
        score_color = "#c77800"
    else:
        score_color = "#c0392b"

    rows = []
    for impact in IMPACT_ORDER:
        count = data["by_impact"][impact]
        rows.append(
            f'<tr><td><span class="pill {impact}">{IMPACT_LABELS[impact]}</span></td>'
            f"<td>{count}</td></tr>"
        )

    blocks = []
    for index, item in enumerate(data["violations"], start=1):
        elements = []
        for node in item["elements"]:
            note = (
                f'<p class="note">{html.escape(_clip(node["note"], 300))}</p>'
                if node["note"]
                else ""
            )
            elements.append(
                '<li>'
                f'<code class="sel">{html.escape(node["selector"])}</code>'
                f'<pre>{html.escape(_clip(node["html"]))}</pre>'
                f"{note}"
                "</li>"
            )

        blocks.append(
            f"""
        <section class="rule">
          <h3>
            <span class="pill {item['impact']}">{IMPACT_LABELS.get(item['impact'], item['impact'])}</span>
            <span class="rule-id">{index}. {html.escape(item['id'])}</span> &mdash; {html.escape(item['help'])}
          </h3>
          <p>{html.escape(item['description'])}</p>
          <p class="meta">
            {item['element_count']} affected element(s) &middot;
            <a href="{html.escape(item['help_url'])}">rule documentation</a>
            &middot; tags: {html.escape(', '.join(_wcag_tags(item['tags']) or item['tags']))}
          </p>
          <ul class="elements">{''.join(elements)}</ul>
        </section>"""
        )

    if not blocks:
        blocks.append('<p class="empty">No automated accessibility violations were found.</p>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Accessibility report &mdash; {html.escape(data['title'] or data['url'])}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: "Segoe UI", Calibri, Arial, sans-serif; color: #1f2430;
         max-width: 900px; margin: 32px auto; padding: 0 18px; line-height: 1.55; }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  h2 {{ font-size: 17px; margin-top: 28px; border-bottom: 1px solid #dde4ee; padding-bottom: 6px; }}
  h3 {{ font-size: 14px; margin: 18px 0 6px; }}
  .url {{ color: #5b6475; font-size: 13px; word-break: break-all; }}
  .summary {{ display: flex; gap: 14px; margin: 18px 0 8px; flex-wrap: wrap; }}
  .card {{ border: 1px solid #dde4ee; border-radius: 8px; padding: 12px 16px; min-width: 120px; }}
  .card .n {{ font-size: 24px; font-weight: 700; display: block; }}
  .card .l {{ font-size: 11px; text-transform: uppercase; letter-spacing: .6pt; color: #6b7484; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin: 8px 0 0; }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid #e6ebf2; }}
  th {{ background: #f3f6fa; }}
  .pill {{ display: inline-block; font-size: 10px; text-transform: uppercase; letter-spacing: .6pt;
           padding: 2px 7px; border-radius: 10px; color: #fff; vertical-align: middle; }}
  .pill.critical {{ background: #8e1b1b; }}
  .pill.serious  {{ background: #c0392b; }}
  .pill.moderate {{ background: #c77800; }}
  .pill.minor    {{ background: #5b6475; }}
  .rule {{ border: 1px solid #e6ebf2; border-radius: 8px; padding: 10px 16px; margin: 12px 0;
           page-break-inside: avoid; }}
  .rule-id {{ font-family: Consolas, monospace; font-size: 13px; }}
  .meta, .note {{ font-size: 12px; color: #5b6475; }}
  code.sel {{ font-family: Consolas, monospace; font-size: 12px; background: #f1f3f7;
              padding: 1px 5px; border-radius: 3px; }}
  pre {{ background: #f7f9fc; border: 1px solid #e6ebf2; border-radius: 5px; padding: 7px 9px;
         font-size: 11px; white-space: pre-wrap; word-break: break-all; margin: 5px 0; }}
  ul.elements {{ font-size: 13px; }}
  ul.elements li {{ margin-bottom: 10px; }}
  .empty {{ padding: 10px 0; }}
  footer {{ margin-top: 30px; font-size: 12px; color: #6b7484; border-top: 1px solid #dde4ee;
            padding-top: 10px; }}
  @media print {{ body {{ margin: 0; max-width: none; }} }}
</style>
</head>
<body>
  <h1>Accessibility report</h1>
  <p class="url">{html.escape(data['url'])}</p>
  <p class="url">{html.escape(data['title'] or '')} &middot; scanned {html.escape(data['scanned_at'])}</p>

  <div class="summary">
    <div class="card"><span class="n" style="color:{score_color}">{score}</span>
      <span class="l">Score / 100</span></div>
    <div class="card"><span class="n" style="color:{score_color}">{grade}</span>
      <span class="l">Grade</span></div>
    <div class="card"><span class="n">{data['rules_failed']}</span>
      <span class="l">Rules failed</span></div>
    <div class="card"><span class="n">{data['elements_affected']}</span>
      <span class="l">Elements affected</span></div>
    <div class="card"><span class="n">{data['rules_passed']}</span>
      <span class="l">Rules passed</span></div>
  </div>
  <p>{html.escape(data['verdict'])}</p>

  <h2>Issues by severity</h2>
  <table>
    <tr><th>Severity</th><th>Failed rules</th></tr>
    {''.join(rows)}
  </table>

  <h2>Violations</h2>
  {''.join(blocks)}

  <footer>
    Generated by accessibility-auditor using axe-core {html.escape('4.14.0')}.
    Automated checks catch only part of real accessibility problems &mdash;
    always test with a keyboard and a screen reader.
  </footer>
</body>
</html>
"""


def to_json(result: AuditResult) -> str:
    return json.dumps(to_dict(result), indent=2, ensure_ascii=False)
