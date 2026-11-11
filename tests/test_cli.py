"""Tests for report file naming (no browser, no network)."""

from __future__ import annotations

from pathlib import Path

from a11y_auditor.cli import _slug, main, report_paths


def test_slug_keeps_dots_inside_host_name():
    assert _slug("https://www.w3.org/WAI/demos/bad/") == "www.w3.org-WAI-demos-bad"


def test_slug_strips_scheme_and_trailing_slash():
    assert _slug("https://example.com/") == "example.com"
    assert _slug("http://example.com/a/b/") == "example.com-a-b"


def test_file_url_uses_the_file_stem():
    assert _slug("file:///C:/work/my%20page.html") == "my-page"


def test_report_paths_do_not_eat_dots_in_the_slug(tmp_path: Path):
    # Regression test: Path.with_suffix(".md") once turned this into "www.w3.md".
    paths = report_paths(tmp_path, "https://www.w3.org/WAI/demos/bad/", ["md", "html", "json"])
    assert [p.name for p in paths] == [
        "www.w3.org-WAI-demos-bad.md",
        "www.w3.org-WAI-demos-bad.html",
        "www.w3.org-WAI-demos-bad.json",
    ]


def test_slug_is_length_limited():
    long_url = "https://example.com/" + "a" * 300
    assert len(_slug(long_url)) <= 80


def test_slug_never_empty():
    assert _slug("https://") == "report"


def test_unknown_format_fails_before_any_scan(capsys):
    # No browser is launched because the format is checked first.
    assert main(["https://example.com", "--format", "docx"]) == 2
    assert "Unknown format" in capsys.readouterr().err


def test_empty_format_fails_before_any_scan(capsys):
    assert main(["https://example.com", "--format", ","]) == 2
    assert "No formats selected" in capsys.readouterr().err
