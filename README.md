# Accessibility Auditor

[![CI](https://github.com/anusanu162-sudo/accessibility-auditor/actions/workflows/ci.yml/badge.svg)](https://github.com/anusanu162-sudo/accessibility-auditor/actions/workflows/ci.yml)

A command-line tool and web app that scans a page for accessibility problems (WCAG),
scores it out of 100, and exports a report you can hand to a developer.

It loads the page in a real browser (so JavaScript-rendered content is checked), runs
[axe-core](https://github.com/dequelabs/axe-core) against it, and turns the results
into a plain-English report.

## What it checks

Every rule that axe-core ships, including:

- Images without `alt` text
- Text with too little colour contrast
- Form inputs with no label
- Buttons and links with no accessible name
- Incorrect heading order
- Invalid or misused ARIA attributes
- Scrollable regions that cannot be reached by keyboard
- Missing page language and frames without titles

Rules are grouped by impact: **critical**, **serious**, **moderate**, **minor**.

## Why this exists

Most accessibility failures are cheap to fix but invisible to the person who built the
page. Automated checkers find a large share of the common ones in seconds. This project
wraps a good engine (axe-core) in a usable workflow: scan, read, share, fix.

## Honest limitations

- **Automated testing catches roughly 30–50% of real accessibility problems.** It cannot
  tell you whether the alt text makes sense, whether the tab order is logical, or whether
  a screen reader announces things sensibly. Always test manually with a keyboard and a
  screen reader.
- **The score is a heuristic, not a compliance certificate.** It is a weighted count of
  failed rules designed to make progress visible. A high score is not proof that a page
  is WCAG-compliant; a low score is a strong sign of real barriers.
- **Only the loaded state is checked.** Content behind a login, a click, or an infinite
  scroll is not reached.
- **No screenshots yet.** The reports describe elements by CSS selector and HTML snippet.

## Install

Requires Python 3.10+ and a Chrome or Edge install (or Playwright's own Chromium).

```bash
git clone https://github.com/anusanu162-sudo/accessibility-auditor.git
cd accessibility-auditor

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

No Chrome or Edge? Install Playwright's Chromium and pass `--browser ""`:

```bash
playwright install chromium
python -m a11y_auditor.cli https://example.com --browser ""
```

## See a real report

[docs/sample-report.html](docs/sample-report.html) is the output of scanning
[examples/bad-page.html](examples/bad-page.html) (served on localhost for the sample) — a
small page with deliberate accessibility mistakes. Open it in a browser; use
**Print → Save as PDF** if you want a PDF. The Markdown version is
[docs/sample-report.md](docs/sample-report.md).

## Use it from the command line

```bash
python -m a11y_auditor.cli https://example.com
```

Output:

```
Bed & Breakfast - demo page with accessibility problems
  score 47/100 (grade F)
  9 rules failed, 18 elements affected
  critical 2 | serious 3 | moderate 4 | minor 0

  1. [critical] button-name - Buttons must have discernible text (1 element(s))
       button
  2. [serious] color-contrast - Elements must meet minimum color contrast ratio thresholds (1 element(s))
       .faint
  ...
```

Reports are written to `reports/` as Markdown, printable HTML, and JSON.

After `pip install -e .` the same command is available as `a11y-auditor`:

```bash
a11y-auditor https://example.com
```

Useful options:

```bash
python -m a11y_auditor.cli https://example.com --out my-report
python -m a11y_auditor.cli https://example.com --format md
python -m a11y_auditor.cli https://example.com --fail-under 90   # exit code 1 below 90
python -m a11y_auditor.cli https://example.com --browser ""      # bundled Chromium
```

`--fail-under` makes it usable as a CI gate.

## Use the web app

```bash
streamlit run app.py
```

Opens on `http://localhost:8501`. Enter a URL, scan, filter by severity, and download
the report.

## How the score works

Each failed rule costs points by impact:

| Impact | Points per rule | Most it can cost |
| --- | --- | --- |
| Critical | 10 | 50 |
| Serious | 6 | 30 |
| Moderate | 3 | 15 |
| Minor | 1 | 5 |

Points are multiplied by the number of affected elements **up to 3 per rule**, so one
rule affecting 200 images does not drown out everything else. The score is
`max(0, 100 − total deduction)`.

The "most it can cost" column is a cap per severity. Without it, seven different
serious rules would drive almost any real page to zero, which hides the difference
between "bad" and "catastrophic". The caps add up to 100, so 0 is still reachable.
This is a judgement call, not a WCAG standard — read it as a progress indicator, not a
compliance verdict.

Then: **A** ≥ 90, **B** ≥ 80, **C** ≥ 70, **D** ≥ 60, **F** below 60.

## Project layout

```
accessibility-auditor/
├── a11y_auditor/
│   ├── auditor.py       # Playwright + axe-core scan
│   ├── cli.py           # command-line interface
│   ├── models.py        # AuditResult, Violation, Node
│   ├── report.py        # Markdown / HTML / JSON rendering
│   ├── scoring.py       # score, grade, verdict
│   └── vendor/
│       └── axe.min.js   # axe-core 4.14.0, vendored
├── tests/
│   ├── test_scoring.py
│   ├── test_report.py
│   └── test_cli.py
├── examples/
│   └── bad-page.html    # page with deliberate mistakes, for demos
├── docs/
│   ├── sample-report.html
│   └── sample-report.md
├── app.py               # Streamlit UI
├── pyproject.toml
└── requirements.txt
```

The tests use synthetic results only — no network, no browser required.

## Development

```bash
pytest
```

## Credits

- [axe-core](https://github.com/dequelabs/axe-core) by Deque Systems — the accessibility
  engine, licensed under MPL-2.0. A copy is vendored in `a11y_auditor/vendor/axe.min.js`.
- [Playwright](https://playwright.dev/) — browser automation.

## License

MIT. See [LICENSE](LICENSE). axe-core keeps its own MPL-2.0 license.
