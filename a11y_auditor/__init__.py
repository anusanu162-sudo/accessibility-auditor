"""accessibility-auditor: WCAG checks for any web page, powered by axe-core."""

from .auditor import AuditError, run_audit
from .models import AuditResult, Node, Violation
from .report import to_dict, to_html, to_json, to_markdown
from .scoring import compute_score, count_by_impact, grade_for, verdict

__version__ = "1.0.0"

__all__ = [
    "AuditError",
    "AuditResult",
    "Node",
    "Violation",
    "run_audit",
    "compute_score",
    "count_by_impact",
    "grade_for",
    "verdict",
    "to_dict",
    "to_html",
    "to_json",
    "to_markdown",
    "__version__",
]
