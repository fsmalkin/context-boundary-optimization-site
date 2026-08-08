---
layout: default
title: Context-Boundary Optimization
description: Services computing, per task and at runtime, the information architecture an agent needs to act well.
---

# Context-Boundary Optimization

**When a person uses a software service, the interface is an information
architecture.** It surfaces the relevant actions at each step, confirms the
risky ones, and records what happened. An autonomous agent calling the same
service through its API inherits none of that — only functions and types.

This project develops **context-boundary optimization**: the service computing,
per task and at runtime, the information architecture an agent needs. The
governing object is a **context contract**; its mechanism is a **fisheye view**
keyed to the current task rather than a static document.

<img src="figures/fig1-boundary.png" alt="The boundary between a service and an agent: the service holds capabilities, obligations and record requirements; the agent receives only functions and types." style="max-width:100%">

## The argument in three parts

| | Question it answers | |
| --- | --- | --- |
| **A · Technical** | What is a context contract, and does one improve agent reliability? | [read →](papers/technical-paper.md) · [PDF](papers/context-boundary-optimization.pdf) |
| **B · Economic** | Who should compute the boundary, and why the provider? | [read →](papers/economic-paper.md) · [PDF](papers/computing-the-context-boundary.pdf) |
| **3 · Implementation** | How does a service team actually build one? | [browse →](library/) |

Paper A defines the framework and reports live experiments. Paper B makes the
transaction-cost case for provider-side computation and enforcement. Part 3
turns the framework into a small dependency-free library and a worked example,
so the papers describe something runnable rather than only a design.

## The idea, concretely

A service exposes forty API functions. An agent asked to *"refund the duplicate
charge on invoice 4471"* needs perhaps four of them, one obligation (a refund
over $500 requires supervisor approval), and one record format. Today it
receives all forty and a prompt hoping it infers the rest.

**A context contract makes that inference unnecessary.** The service computes a
task-scoped view, states the obligations that apply, and specifies the record it
expects back — then enforces the obligations deterministically rather than
trusting the model to remember them.

<img src="figures/fig2-fisheye.png" alt="A fisheye view: the task-relevant region of a capability catalog is expanded in detail while distant capabilities are compressed." style="max-width:100%">

## The reference implementation

`context_contract` gives each construct in the papers a small Python object with
no dependencies.

```python
from context_contract import ContextContract, focused_view, Gate

contract = ContextContract.load("contract.json")
view     = focused_view(catalog, task, contract, k=4)   # the fisheye selection
verdict  = Gate(contract).check(action)                 # deterministic enforcement
```

Three ways to use it — an advisor agent that designs a contract for your
service, a CLI (`python -m context_contract advise | scaffold | check`), and a
[worked billing-service example](library/examples/billing-service/) carrying one
action the gate approves and one it rejects.

[**Browse the library →**](library/)

## Interactive

Three tools built while running the experiments, kept because they show the
mechanism better than prose does.

- [**Trace browser**](demos/trace-browser.html) — step through what an agent
  actually did, turn by turn
- [**Adjudication view**](demos/adjudication.html) — how a run was scored, and
  where scorers disagreed
- [**Plain-English results**](demos/plain-english-results.html) — the findings
  without the statistics

## Figures

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem">
  <img src="figures/fig3-runtime-flow.png" alt="Runtime flow: task arrives, contract computes the view, agent acts, gate checks, trace is recorded." style="max-width:100%">
  <img src="figures/fig4-amortization.png" alt="Amortization: the cost of computing a boundary is paid once by the provider and reused across every agent." style="max-width:100%">
  <img src="figures/fig5-enforcement.png" alt="Enforcement: obligations checked deterministically at the gate rather than requested in a prompt." style="max-width:100%">
  <img src="figures/fig6-spectrum.png" alt="A spectrum from raw API access to fully computed boundaries, with cost and capability on each axis." style="max-width:100%">
</div>

## Status

**Both papers are working drafts.** The framework, the library and the worked
example are complete and runnable; the empirical claims are still being
strengthened, and the drafts are tagged accordingly. This site publishes the
work as it stands rather than waiting for a finished version.

Licensed MIT (code) and CC-BY (papers) — see [LICENSE](LICENSE).
