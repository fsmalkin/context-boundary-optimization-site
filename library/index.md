---
layout: default
title: Reference implementation
---

# `context_contract`

A dependency-free Python library giving each construct in the papers a small
object. [← back](../)

## Modules

| Module | What it holds |
| --- | --- |
| [`contract.py`](context_contract/contract.py) | `ContextContract` / `ObligationSpec` — the seven boundary dimensions as a declarative schema |
| [`view.py`](context_contract/view.py) | `focused_view(catalog, task, contract, k)` — the fisheye selection computing the task-scoped view |
| [`gate.py`](context_contract/gate.py) | `Gate(contract).check(action)` — deterministic enforcement, policy in the contract rather than in a prompt |
| [`audit.py`](context_contract/audit.py) | `AuditTrace` — the output record the agent must return |
| [`rubric.py`](context_contract/rubric.py) | `score_trace` — scoring a trace against the rubric |
| [`cli.py`](context_contract/cli.py) | `python -m context_contract advise \| scaffold \| check` |

## Worked example

[`examples/billing-service/`](examples/billing-service/) carries the billing
service from Paper A end to end:

- [`contract.json`](examples/billing-service/contract.json) — the contract itself
- [`action-approved.json`](examples/billing-service/action-approved.json) — an action the gate approves
- [`action-missing-approval.json`](examples/billing-service/action-missing-approval.json) — one it rejects, and why
- [`scaffold.py`](examples/billing-service/scaffold.py) — the generated `handle_task()` integration

## Tests

Ten test modules covering the contract, view, gate, audit, rubric, CLI, and the
tau2-bench harness. [Browse `tests/`](tests/).
