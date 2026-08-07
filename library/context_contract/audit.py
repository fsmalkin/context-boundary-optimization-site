"""Structured audit traces for context-boundary runs."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Mapping


@dataclass(slots=True)
class AuditStep:
    """One traceable runtime step."""

    action: dict[str, Any]
    context_used: list[str] = field(default_factory=list)
    obligations_checked: list[str] = field(default_factory=list)
    decision: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable step."""

        return {
            "action": dict(self.action),
            "context_used": list(self.context_used),
            "obligations_checked": list(self.obligations_checked),
            "decision": dict(self.decision),
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AuditStep":
        """Build a step from a mapping."""

        return cls(
            action=dict(value.get("action", {}) or {}),
            context_used=[str(item) for item in value.get("context_used", [])],
            obligations_checked=[str(item) for item in value.get("obligations_checked", [])],
            decision=dict(value.get("decision", {}) or {}),
            evidence=dict(value.get("evidence", {}) or {}),
        )


@dataclass(slots=True)
class AuditTrace:
    """Append-only trace of actions, obligations, decisions, and evidence."""

    steps: list[AuditStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def append(
        self,
        *,
        action: Mapping[str, Any],
        context_used: list[str] | None = None,
        obligations_checked: list[str] | None = None,
        decision: Mapping[str, Any] | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> AuditStep:
        """Append a structured step and return it."""

        step = AuditStep(
            action=dict(action),
            context_used=list(context_used or []),
            obligations_checked=list(obligations_checked or []),
            decision=dict(decision or {}),
            evidence=dict(evidence or {}),
        )
        self.steps.append(step)
        return step

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable trace."""

        return {
            "metadata": dict(self.metadata),
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AuditTrace":
        """Build a trace from a mapping."""

        return cls(
            steps=[AuditStep.from_dict(item) for item in value.get("steps", [])],
            metadata=dict(value.get("metadata", {}) or {}),
        )

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the trace to stable JSON text."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, value: str) -> "AuditTrace":
        """Deserialize a trace from JSON text."""

        return cls.from_dict(json.loads(value))
