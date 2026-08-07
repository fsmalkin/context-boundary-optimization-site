"""Declarative context-boundary contracts.

The experiment runners encoded context obligations directly in prompts and
task dictionaries. This module gives those obligations a small reusable schema:
one service author declares one :class:`ContextContract` with the seven paper
axes as first-class fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping


AXES = (
    "required_context",
    "authority",
    "provenance",
    "memory",
    "privacy",
    "uncertainty",
    "output_audit",
)


@dataclass(slots=True)
class ObligationSpec:
    """Declarative requirements and promises for one boundary axis.

    ``preconditions`` maps operation names to tokens the gate can check. Use
    ``"*"`` for global preconditions that apply to every action.
    """

    requires: list[str] = field(default_factory=list)
    promises: list[str] = field(default_factory=list)
    preconditions: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "requires": list(self.requires),
            "promises": list(self.promises),
            "preconditions": {
                str(operation): list(tokens)
                for operation, tokens in self.preconditions.items()
            },
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any] | "ObligationSpec" | None) -> "ObligationSpec":
        """Build an obligation spec from a mapping or return an existing spec."""

        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        preconditions = value.get("preconditions", {})
        if not isinstance(preconditions, Mapping):
            raise TypeError("preconditions must be a mapping of operation to tokens")
        return cls(
            requires=[str(item) for item in value.get("requires", [])],
            promises=[str(item) for item in value.get("promises", [])],
            preconditions={
                str(operation): [str(token) for token in tokens]
                for operation, tokens in preconditions.items()
            },
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(slots=True)
class ContextContract:
    """Service-level contract for the seven context-boundary obligations."""

    name: str = "context-contract"
    version: str = "1.0"
    required_context: ObligationSpec = field(default_factory=ObligationSpec)
    authority: ObligationSpec = field(default_factory=ObligationSpec)
    provenance: ObligationSpec = field(default_factory=ObligationSpec)
    memory: ObligationSpec = field(default_factory=ObligationSpec)
    privacy: ObligationSpec = field(default_factory=ObligationSpec)
    uncertainty: ObligationSpec = field(default_factory=ObligationSpec)
    output_audit: ObligationSpec = field(default_factory=ObligationSpec)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable contract dictionary."""

        return {
            "name": self.name,
            "version": self.version,
            **{axis: getattr(self, axis).to_dict() for axis in AXES},
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ContextContract":
        """Build a contract from ``to_dict`` output or a compatible mapping."""

        return cls(
            name=str(value.get("name", "context-contract")),
            version=str(value.get("version", "1.0")),
            required_context=ObligationSpec.from_dict(value.get("required_context")),
            authority=ObligationSpec.from_dict(value.get("authority")),
            provenance=ObligationSpec.from_dict(value.get("provenance")),
            memory=ObligationSpec.from_dict(value.get("memory")),
            privacy=ObligationSpec.from_dict(value.get("privacy")),
            uncertainty=ObligationSpec.from_dict(value.get("uncertainty")),
            output_audit=ObligationSpec.from_dict(value.get("output_audit")),
            metadata=dict(value.get("metadata", {})),
        )

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the contract to stable JSON text."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, value: str) -> "ContextContract":
        """Deserialize a contract from JSON text."""

        return cls.from_dict(json.loads(value))

    def write_json(self, path: str | Path) -> None:
        """Write stable JSON to ``path``."""

        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "ContextContract":
        """Read a contract from ``path``."""

        return cls.from_json(Path(path).read_text(encoding="utf-8"))
