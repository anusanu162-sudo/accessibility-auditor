"""Data structures for an accessibility audit."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    """One element on the page that breaks a rule."""

    target: list[str]
    html: str
    summary: str | None = None

    @property
    def selector(self) -> str:
        return " ".join(self.target) if self.target else "(unknown)"


@dataclass
class Violation:
    """One accessibility rule that the page failed, with every element it affects."""

    id: str
    impact: str
    help: str
    description: str
    help_url: str
    tags: list[str] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)


@dataclass
class AuditResult:
    """Everything we know about one scanned page."""

    url: str
    title: str
    scanned_at: str
    duration_ms: int
    violations: list[Violation] = field(default_factory=list)
    pass_count: int = 0
    incomplete_count: int = 0

    @property
    def rule_count(self) -> int:
        """How many different rules failed."""
        return len(self.violations)

    @property
    def issue_count(self) -> int:
        """How many individual elements are affected, across all rules."""
        return sum(len(v.nodes) for v in self.violations)
