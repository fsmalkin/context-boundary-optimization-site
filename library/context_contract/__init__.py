"""Reference implementation for context-boundary contracts.

The public API keeps the paper framework operational and dependency-light:
declare a contract, compute a focused view, enforce an action, record an audit
trace, and score deterministic rubric signals.
"""

from .audit import AuditStep, AuditTrace
from .contract import AXES, ContextContract, ObligationSpec
from .gate import Gate, GateDecision, ProposedAction
from .rubric import FAILURE_AXES, RUBRIC_AXIS_DEFINITIONS, RubricScore, score_trace
from .view import focused_view

__all__ = [
    "AXES",
    "FAILURE_AXES",
    "RUBRIC_AXIS_DEFINITIONS",
    "AuditStep",
    "AuditTrace",
    "ContextContract",
    "Gate",
    "GateDecision",
    "ObligationSpec",
    "ProposedAction",
    "RubricScore",
    "focused_view",
    "score_trace",
]
