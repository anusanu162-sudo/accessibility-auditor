"""Streamlit web app for the accessibility auditor.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from a11y_auditor import AuditError, compute_score, count_by_impact, run_audit, to_html, to_json, to_markdown, verdict

IMPACT_ORDER = ["critical", "serious", "moderate", "minor"]
IMPACT_LABELS = {
    "critical": "Critical",
    "serious": "Serious",
    "moderate": "Moderate",
    "minor": "Minor",
}

st.set_page_config(page_title="Accessibility Auditor", page_icon="♿", layout="wide")

st.title("Accessibility Auditor")
st.caption(
    "Scan any public web page for WCAG accessibility problems, get a score, "
    "and download a report. Powered by axe-core running in a real browser."
)

with st.sidebar:
    st.header("Scan settings")
    browser = st.selectbox(
        "Browser",
        ["chrome", "msedge", ""],
        index=0,
        help="Installed browser to drive. Choose the blank option to use Playwright's "
        "bundled Chromium, which needs `playwright install chromium`.",
    )
    timeout = st.number_input(
        "Page load timeout (seconds)", min_value=5, max_value=120, value=30, step=5
    )
    wait = st.number_input(
        "Extra wait after load (ms)",
        min_value=0,
        max_value=10_000,
        value=1_200,
        step=200,
        help="Gives late JavaScript, lazy images and fonts time to appear.",
    )
    max_nodes = st.number_input(
        "Max elements shown per rule", min_value=1, max_value=20, value=5, step=1
    )
    st.divider()
    st.caption(
        "Automated checks catch only part of real accessibility problems. "
        "Always test with a keyboard and a screen reader too."
    )

url = st.text_input(
    "Page URL",
    value="https://www.w3.org/WAI/demos/bad/",
    help="Include the scheme, e.g. https://example.com",
)

scan = st.button("Scan page", type="primary")


def _run(url_value: str):
    with st.spinner("Loading the page and running axe-core…"):
        result = run_audit(
            url_value,
            browser_channel=browser,
            timeout_ms=int(timeout) * 1000,
            extra_wait_ms=int(wait),
            max_nodes=int(max_nodes),
        )
    st.session_state["result"] = result


if scan:
    if not url.strip():
        st.warning("Enter a URL first.")
    elif not url.strip().lower().startswith(("http://", "https://")):
        st.warning("The URL must start with http:// or https://")
    else:
        try:
            _run(url.strip())
        except AuditError as exc:
            st.session_state.pop("result", None)
            st.error(f"Could not scan that page: {exc}")

result = st.session_state.get("result")

if result is not None:
    score, grade = compute_score(result.violations)
    counts = count_by_impact(result.violations)

    st.divider()
    st.subheader(result.title or result.url)
    st.caption(f"{result.url} — scanned {result.scanned_at} in {result.duration_ms} ms")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Score", f"{score}/100")
    c2.metric("Grade", grade)
    c3.metric("Rules failed", result.rule_count)
    c4.metric("Elements affected", result.issue_count)
    c5.metric("Rules passed", result.pass_count)

    if score >= 90:
        st.success(verdict(score))
    elif score >= 70:
        st.warning(verdict(score))
    else:
        st.error(verdict(score))

    st.markdown("**Issues by severity**")
    cols = st.columns(4)
    for col, impact in zip(cols, IMPACT_ORDER):
        col.metric(IMPACT_LABELS[impact], counts[impact])

    st.divider()

    left, right = st.columns([3, 1])
    with left:
        st.subheader("Violations")
    with right:
        selected = st.multiselect(
            "Filter by severity",
            IMPACT_ORDER,
            default=IMPACT_ORDER,
            format_func=lambda x: IMPACT_LABELS[x],
            label_visibility="collapsed",
        )

    shown = [v for v in result.violations if v.impact in selected]
    shown.sort(key=lambda v: (IMPACT_ORDER.index(v.impact) if v.impact in IMPACT_ORDER else 9, -len(v.nodes)))

    if not result.violations:
        st.success("No automated accessibility violations were found on this page.")
    elif not shown:
        st.info("No violations at the selected severities.")
    else:
        for violation in shown:
            label = (
                f"[{IMPACT_LABELS.get(violation.impact, violation.impact)}] "
                f"{violation.id} — {violation.help} ({len(violation.nodes)} element(s))"
            )
            with st.expander(label):
                st.markdown(violation.description)
                st.caption(f"Rule reference: {violation.help_url}")
                if violation.tags:
                    st.caption("Tags: " + ", ".join(violation.tags))
                for index, node in enumerate(violation.nodes, start=1):
                    st.markdown(f"**{index}. `{node.selector}`**")
                    st.code(node.html, language="html")
                    if node.summary:
                        st.caption(node.summary)

    st.divider()
    st.subheader("Download report")
    d1, d2, d3 = st.columns(3)
    base = "accessibility-report"
    d1.download_button(
        "Markdown",
        data=to_markdown(result),
        file_name=f"{base}.md",
        mime="text/markdown",
    )
    d2.download_button(
        "HTML (printable)",
        data=to_html(result),
        file_name=f"{base}.html",
        mime="text/html",
    )
    d3.download_button(
        "JSON",
        data=to_json(result),
        file_name=f"{base}.json",
        mime="application/json",
    )
    st.caption("Open the HTML file in a browser and print it to PDF if you need a PDF.")
else:
    st.info("Enter a URL above and press **Scan page** to begin.")
