---
layout: default
title: Worked example — billing service
---

# Worked example: a billing service

The service from Paper A, carried end to end. [← library](../../)

A refund over $500 requires supervisor approval. That obligation lives in the
contract, and the gate enforces it — the agent is not asked to remember it.

| File | What it shows |
| --- | --- |
| [`contract.json`](contract.json) | The context contract: capabilities, obligations, and the record the agent must return |
| [`service.json`](service.json) | The service's full capability catalog, before any task-scoped narrowing |
| [`action-approved.json`](action-approved.json) | An action the gate approves — the approval is present |
| [`action-missing-approval.json`](action-missing-approval.json) | The same action without it. The gate rejects, and says which obligation failed |
| [`scaffold.py`](scaffold.py) | The generated `handle_task()` integration |
| [`test_example.py`](test_example.py) | Both cases as tests |

Run it:

```bash
python -m context_contract check \
  --contract contract.json \
  --action action-missing-approval.json
```
