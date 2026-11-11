"""Command-line interface: scan a URL and write a report.

Examples:
    python -m a11y_auditor.cli https://example.com
    python -m a11y_auditor.cli https://example.com --out reports --fail-under 90
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from .auditor import AuditError, run_audit
from .report import to_html, to_json, to_markdown
from .scoring import compute_score, count_by_impact

SLUG_MAX = 80


def _slug(url: str) -> str:
    """Turn a URL into a safe file name like example-com-home."""
    parsed = urlparse(url)
    if parsed.scheme == "file":
        name = Path(unquote(parsed.path)).stem
        if name:
            return "-".join(name.split())[:SLUG_MAX] or "report"

    cleaned = url.split("://", 1)[-1]
    for ch in ":/?#[]@!$&'()*+,;=%~":
        cleaned = cleaned.replace(ch, "-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    cleaned = cleaned.strip("-.")[:SLUG_MAX]
    return cleaned.rstrip("-.!") or "report"


def report_paths(out_dir: Path, url: str, formats: list[str]) -> list[Path]:
    """Where each report format will be written."""
    # Build names by hand: Path.with_suffix() would eat a dot inside the slug,
    # turning "www.w3.org-WAI-demos-bad" into "www.w3.md".
    return [out_dir / f"{_slug(url)}.{fmt}" for fmt in formats]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="a11y-auditor",
        description="Check a web page for accessibility problems and write a report.",
    )
    parser.add_argument("url", help="Page to scan, including https://")
    parser.add_argument(
        "-o",
        "--out",
        default="reports",
        help="Folder for the report files (default: reports)",
    )
    parser.add_argument(
        "--format",
        default="md,html,json",
        help="Comma-separated formats to write: md, html, json (default: all three)",
    )
    parser.add_argument(
        "--browser",
        default="chrome",
        help='Browser channel to drive: "chrome", "msedge", or "" for bundled Chromium',
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30_000,
        help="Page load timeout in milliseconds (default: 30000)",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=1_200,
        help="Extra settle time in milliseconds after load (default: 1200)",
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=None,
        metavar="SCORE",
        help="Exit with code 1 if the score is below SCORE (useful in CI)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the summary line, not the full violation list",
    )
    return parser


def format_summary(url: str, title: str, score: int, grade: str, result) -> str:
    counts = count_by_impact(result.violations)
    return (
        f"{title or url}\n"
        f"  score {score}/100 (grade {grade})\n"
        f"  {result.rule_count} rules failed, {result.issue_count} elements affected\n"
        f"  critical {counts['critical']} | serious {counts['serious']} | "
        f"moderate {counts['moderate']} | minor {counts['minor']}"
    )


def format_violations(result) -> str:
    lines = []
    for index, violation in enumerate(result.violations, start=1):
        lines.append(
            f"  {index}. [{violation.impact}] {violation.id} - {violation.help} "
            f"({len(violation.nodes)} element(s))"
        )
        for node in violation.nodes[:3]:
            lines.append(f"       {node.selector}")
        if len(violation.nodes) > 3:
            lines.append(f"       ... and {len(violation.nodes) - 3} more")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    writers = {"md": (to_markdown, "md"), "html": (to_html, "html"), "json": (to_json, "json")}
    if not formats:
        print("No formats selected. Use --format md, html, json.", file=sys.stderr)
        return 2
    unknown = [f for f in formats if f not in writers]
    if unknown:
        print(f"Unknown format(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    try:
        result = run_audit(
            args.url,
            browser_channel=args.browser,
            timeout_ms=args.timeout,
            extra_wait_ms=args.wait,
        )
    except AuditError as exc:
        print(f"Audit failed: {exc}", file=sys.stderr)
        return 2

    score, grade = compute_score(result.violations)
    print(format_summary(args.url, result.title, score, grade, result))

    if not args.quiet and result.violations:
        print()
        print(format_violations(result))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = report_paths(out_dir, args.url, formats)
    written = []
    for fmt, path in zip(formats, paths):
        writer, _ = writers[fmt]
        path.write_text(writer(result), encoding="utf-8")
        written.append(path)

    print()
    print("Reports written:")
    for path in written:
        print(f"  {path}")

    if args.fail_under is not None and score < args.fail_under:
        print(
            f"\nScore {score} is below --fail-under {args.fail_under}.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
