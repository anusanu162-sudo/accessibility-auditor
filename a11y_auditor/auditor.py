"""Run an accessibility audit on a URL using Playwright + axe-core.

axe-core is Mozilla's open-source accessibility testing engine. We load the page
in a real browser (so JavaScript-rendered content is included), inject axe, and
collect the rules the page fails.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from .models import AuditResult, Node, Violation

AXE_PATH = Path(__file__).resolve().parent / "vendor" / "axe.min.js"

# Pages that load successfully but contain no real content, because the site put a
# bot check in front of it. Reporting "1 violation" on these would be misleading.
BLOCKED_PAGE_TITLES = {
    "just a moment...",
    "attention required! | cloudflare",
    "access denied",
    "robot check",
    "are you a robot?",
}

# Runs inside the page. Kept small: it maps axe's large output down to the
# handful of fields we actually need, so nothing big crosses the process boundary.
AXE_RUN_JS = """
async (maxNodes) => {
  const results = await axe.run(document, {
    reporter: 'v2',
    resultTypes: ['violations', 'passes', 'incomplete', 'inapplicable']
  });

  return {
    violations: results.violations.map(v => ({
      id: v.id,
      impact: v.impact || 'minor',
      help: v.help,
      description: v.description,
      helpUrl: v.helpUrl,
      tags: v.tags || [],
      nodes: v.nodes.slice(0, maxNodes).map(n => ({
        target: n.target || [],
        html: n.html || '',
        summary: (n.failureSummary || '').slice(0, 400)
      }))
    })),
    passCount: results.passes.length,
    incompleteCount: results.incomplete.length
  };
}
"""


class AuditError(RuntimeError):
    """Raised when a page cannot be scanned."""


def _launch_browser(playwright, browser_channel: str):
    """Try the requested browser channel, then fall back to Playwright's own."""
    attempts = [{"channel": browser_channel}] if browser_channel else []
    attempts.append({})

    last_error: Exception | None = None
    for options in attempts:
        try:
            return playwright.chromium.launch(headless=True, **options)
        except PlaywrightError as exc:  # channel missing, browser not installed
            last_error = exc

    raise AuditError(
        "Could not start a browser. Install one with:\n"
        "    playwright install chromium\n"
        f"Last error: {last_error}"
    )


def _inject_axe(page) -> None:
    """Load axe into the page, working around strict Content-Security-Policy."""
    try:
        page.add_script_tag(path=str(AXE_PATH))
        if page.evaluate("() => typeof axe !== 'undefined'"):
            return
    except PlaywrightError:
        pass  # a <script> tag can be blocked by CSP; fall through to eval

    source = AXE_PATH.read_text(encoding="utf-8")
    page.evaluate(source)
    if not page.evaluate("() => typeof axe !== 'undefined'"):
        raise AuditError("Could not load the axe-core engine into the page.")


def run_audit(
    url: str,
    *,
    browser_channel: str = "chrome",
    timeout_ms: int = 30_000,
    wait_until: str = "load",
    extra_wait_ms: int = 1_200,
    max_nodes: int = 10,
) -> AuditResult:
    """Scan one URL and return the violations found.

    Args:
        url: Page to scan. Must include the scheme, e.g. https://example.com
        browser_channel: Installed browser to drive ("chrome", "msedge"),
            or "" to use Playwright's bundled Chromium.
        timeout_ms: Navigation timeout.
        wait_until: Playwright load state ("load", "domcontentloaded", "networkidle").
        extra_wait_ms: Extra settle time for late JavaScript (lazy content, fonts).
        max_nodes: Maximum affected elements kept per rule.
    """
    if not AXE_PATH.exists():
        raise AuditError(f"axe-core not found at {AXE_PATH}")

    started = time.perf_counter()
    scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with sync_playwright() as playwright:
        browser = _launch_browser(playwright, browser_channel)
        try:
            context = browser.new_context(
                viewport={"width": 1366, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 "
                    "a11y-auditor/1.0"
                ),
            )
            page = context.new_page()
            page.set_default_timeout(timeout_ms)

            try:
                page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            except PlaywrightError as exc:
                raise AuditError(f"Could not load {url}: {exc}") from exc

            if extra_wait_ms:
                page.wait_for_timeout(extra_wait_ms)

            title = page.title()
            if title.strip().lower() in BLOCKED_PAGE_TITLES:
                raise AuditError(
                    f"{url} showed a bot-protection page instead of the real content "
                    f"(title: {title!r}). Nothing useful can be checked. Try again later "
                    "or scan a page that does not block automated browsers."
                )

            _inject_axe(page)

            try:
                raw = page.evaluate(AXE_RUN_JS, max_nodes)
            except PlaywrightError as exc:
                raise AuditError(f"axe-core failed to run: {exc}") from exc

            violations = [
                Violation(
                    id=item["id"],
                    impact=item["impact"],
                    help=item["help"],
                    description=item["description"],
                    help_url=item["helpUrl"],
                    tags=item.get("tags", []),
                    nodes=[
                        Node(
                            target=node.get("target", []),
                            html=node.get("html", ""),
                            summary=node.get("summary"),
                        )
                        for node in item.get("nodes", [])
                    ],
                )
                for item in raw.get("violations", [])
            ]
        finally:
            browser.close()

    duration_ms = int((time.perf_counter() - started) * 1000)

    return AuditResult(
        url=url,
        title=title,
        scanned_at=scanned_at,
        duration_ms=duration_ms,
        violations=violations,
        pass_count=raw.get("passCount", 0),
        incomplete_count=raw.get("incompleteCount", 0),
    )
