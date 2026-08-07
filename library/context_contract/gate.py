"""Deterministic context-boundary enforcement.

This module generalizes the provider-gate logic from
``scripts/tau2_enforcement.py``. The experiment script had domain-specific
policy checks; this library keeps the mechanism and moves policy into
declarative contract preconditions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .contract import AXES, ContextContract, ObligationSpec


@dataclass(slots=True)
class ProposedAction:
    """A tool call emitted by an agent or application."""

    operation: str
    arguments: dict[str, Any] = field(default_factory=dict)
    approval_state: str = "not_required"
    context: dict[str, Any] = field(default_factory=dict)
    source_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProposedAction":
        """Build an action from common tool-call dictionary shapes."""

        operation = str(value.get("operation", value.get("name", "")))
        if not operation:
            raise ValueError("proposed action requires an operation or name")
        return cls(
            operation=operation,
            arguments=dict(value.get("arguments", {}) or {}),
            approval_state=str(value.get("approval_state", "not_required")),
            context=dict(value.get("context", {}) or {}),
            source_ids=[str(item) for item in value.get("source_ids", [])],
            metadata=dict(value.get("metadata", {}) or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable action."""

        return {
            "operation": self.operation,
            "arguments": dict(self.arguments),
            "approval_state": self.approval_state,
            "context": dict(self.context),
            "source_ids": list(self.source_ids),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class GateDecision:
    """Machine-readable gate result."""

    accepted: bool
    reason: str
    action: str
    checked: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable gate result."""

        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "action": self.action,
            "checked": list(self.checked),
            "missing": list(self.missing),
            "evidence": dict(self.evidence),
        }


class Gate:
    """Evaluate proposed actions against a :class:`ContextContract`."""

    def __init__(self, contract: ContextContract):
        self.contract = contract

    def check(
        self,
        action: ProposedAction | Mapping[str, Any],
        *,
        state: Mapping[str, Any] | None = None,
    ) -> GateDecision:
        """Accept or reject an action using declarative preconditions.

        Supported precondition tokens:
        ``approval`` or ``approval_state=approved``;
        ``state:key``; ``context:key``; ``argument:key``; ``source_ids``;
        and bare keys, which are resolved against state, context, arguments,
        metadata, then action attributes.
        """

        proposed = action if isinstance(action, ProposedAction) else ProposedAction.from_mapping(action)
        runtime_state = dict(state or {})
        tokens = self._preconditions_for(proposed.operation)
        missing = [
            token
            for token in tokens
            if not precondition_met(token, proposed, runtime_state)
        ]
        if missing:
            return GateDecision(
                accepted=False,
                reason="missing_preconditions",
                action=proposed.operation,
                checked=tokens,
                missing=missing,
                evidence={"state_keys": sorted(runtime_state), "action": proposed.to_dict()},
            )
        return GateDecision(
            accepted=True,
            reason="accepted",
            action=proposed.operation,
            checked=tokens,
            missing=[],
            evidence={"state_keys": sorted(runtime_state), "action": proposed.to_dict()},
        )

    def _preconditions_for(self, operation: str) -> list[str]:
        tokens: list[str] = []
        for axis_name in AXES:
            axis: ObligationSpec = getattr(self.contract, axis_name)
            tokens.extend(axis.preconditions.get("*", []))
            tokens.extend(axis.preconditions.get(operation, []))
        return dedupe(tokens)


def precondition_met(token: str, action: ProposedAction, state: Mapping[str, Any]) -> bool:
    """Return whether one declarative precondition token is satisfied."""

    token = str(token).strip()
    if not token:
        return True
    if token == "approval":
        return action.approval_state == "approved"
    if token.startswith("approval_state="):
        return action.approval_state == token.split("=", 1)[1]
    if token == "source_ids":
        return bool(action.source_ids)
    if ":" in token:
        namespace, key = token.split(":", 1)
        return bool(value_for_namespace(namespace, key, action, state))
    return bool(
        state.get(token)
        or action.context.get(token)
        or action.arguments.get(token)
        or action.metadata.get(token)
        or getattr(action, token, None)
    )


def value_for_namespace(
    namespace: str,
    key: str,
    action: ProposedAction,
    state: Mapping[str, Any],
) -> Any:
    """Resolve a namespaced precondition token."""

    if namespace == "state":
        return state.get(key)
    if namespace == "context":
        return action.context.get(key)
    if namespace == "argument":
        return action.arguments.get(key)
    if namespace == "metadata":
        return action.metadata.get(key)
    if namespace == "action":
        return getattr(action, key, None)
    raise ValueError(f"unknown precondition namespace: {namespace}")


def dedupe(values: list[str]) -> list[str]:
    """Return values in first-seen order without duplicates."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result
