---
layout: default
title: Tests
---

# Tests

Ten modules covering every construct in the papers. [← library](../)

| Module | Covers |
| --- | --- |
| [`test_contract.py`](test_contract.py) | Contract loading, the seven boundary dimensions, obligation specs |
| [`test_view.py`](test_view.py) | The fisheye selection — that the task-scoped view contains what the task needs and omits what it does not |
| [`test_gate.py`](test_gate.py) | Deterministic enforcement, including the rejection path and its reason |
| [`test_audit.py`](test_audit.py) | The trace record the agent must return |
| [`test_rubric.py`](test_rubric.py) | Scoring a trace |
| [`test_cli.py`](test_cli.py) | `advise`, `scaffold` and `check` end to end |
| [`test_legacy_profiles.py`](test_legacy_profiles.py) | Backwards compatibility with earlier contract shapes |
| [`test_phase5_harness.py`](test_phase5_harness.py) · [`test_phase5_analyzer.py`](test_phase5_analyzer.py) | The experiment harness and its analysis |
| [`test_tau2_phase1_harness.py`](test_tau2_phase1_harness.py) | Integration with the public tau2-bench benchmark |

```bash
python -m pytest library/tests
```
