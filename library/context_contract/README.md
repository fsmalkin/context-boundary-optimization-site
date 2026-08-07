# context_contract

`context_contract` is the reference implementation for the Context-Boundary
Optimization framework. It packages the reusable mechanisms that first appeared
in the experiment harnesses:

- `contract.py` defines the seven-axis contract schema.
- `view.py` consolidates focused catalog selection from `scripts/run_live_experiment.py`.
- `gate.py` generalizes deterministic provider gates from `scripts/tau2_enforcement.py`.
- `audit.py` records the trace that makes a run inspectable.
- `rubric.py` implements deterministic scoring and exposes a hook for external judgment.

The library has no network path and no LLM dependency.

## Public API

- `ContextContract.to_dict()`, `ContextContract.from_dict(data)`
- `ContextContract.to_json()`, `ContextContract.from_json(text)`
- `focused_view(catalog, task, contract, k=5, scorer=None)`
- `Gate(contract).check(action, state=None)`
- `AuditTrace.append(action=..., context_used=..., obligations_checked=..., decision=..., evidence=...)`
- `score_trace(trace, contract, gate=None, external_scorer=None)`

## CLI

- `python -m context_contract scaffold contract.json --out scaffold.py`
- `python -m context_contract advise service.json`
- `python -m context_contract check contract.json action.json`

`advise` is a heuristic first pass. It applies transparent keyword rules and
labels the output as a starting point for human review or the advisor skill.

## Example

```python
from context_contract import AuditTrace, ContextContract, Gate, ObligationSpec, focused_view, score_trace

contract = ContextContract(
    name="billing-service",
    authority=ObligationSpec(
        preconditions={"send_invoice": ["approval_state=approved", "argument:customer_id"]},
    ),
    output_audit=ObligationSpec(promises=["record actions, decisions, and evidence"]),
)
catalog = [
    {"name": "send_invoice", "description": "Send an approved invoice to a customer", "importance": 1},
    {"name": "delete_account", "description": "Remove a customer account"},
    {"name": "search_docs", "description": "Search public documentation"},
]
task = {"title": "send approved invoice", "required_tools": ["send_invoice"]}

view = focused_view(catalog, task, contract, k=1)[0]
gate = Gate(contract)
action = {"operation": "send_invoice", "arguments": {"customer_id": "cus_123"}, "approval_state": "approved"}
decision = gate.check(action)

trace = AuditTrace(metadata={"task": task["title"]})
trace.append(
    action=action,
    context_used=[view["name"]],
    obligations_checked=decision.checked,
    decision=decision.to_dict(),
    evidence={"approval_record": "ticket-42"},
)
score = score_trace(trace, contract)
print(decision.accepted, view["name"], score.to_dict()["auditability_score"])
```
