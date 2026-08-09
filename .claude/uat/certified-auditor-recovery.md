# Task-local certified-auditor recovery

## Instrument failure

The shared certified launcher correctly ran a cold, stripped-home Playwright
actor, but its audit produced a false failure at the evidence-to-verdict seam:

- its AST grammar rejected the executor's safe `text(r)` and text-only result
  forwarders even though every call remained one direct static Playwright MCP
  invocation
- its flat text scan treated public browser output containing `DESIGN.md`,
  `../`, and Playwright artifact references as evidence of host-file access

The shared certificate remains failed and its functional debrief remains
discarded. The task-local recovery changes the auditor, not that verdict.

## Corrected seam

The copied launcher preserves the shared stripped `CODEX_HOME`, fresh Codex
thread, subscription authentication, Playwright-only MCP configuration,
network target, scratch directory, lane lock, heartbeat, prompt logging, and
transcript capture. Its task-local auditor:

1. parses each executor call with pinned Acorn 8.17.0
2. permits only read-only tool discovery or one direct non-computed
   `mcp__playwright__*` call with static data
3. rejects file upload, install, unsafe code, shell tools, aliases, computed
   calls, appended statements, and arbitrary output handling
4. correlates every allowed Playwright executor with the matching MCP tool
   name, exact static invocation arguments, MCP result, and executor output
5. exempts only those correlated browser-output records from host-path and
   internal-vocabulary scans
6. applies the full deny scan to agent reasoning, messages, tool arguments,
   discovery output, unbound records, and mismatched results
7. requires one executor output per call and rejects duplicate call-ID output
8. accepts the executor's bounded truncation only when its retained prefix and
   suffix are exact projections of the matched MCP result

Each resulting certificate binds the task-local launcher, shared base launcher,
shared certified-probe adapter, heartbeat module, lane-lock module, Acorn
version, AST validator, and transcript auditor by SHA-256.

## Controls

The first independent review found a P1 provenance bypass: the initial recovery
exempted Playwright event arguments and every output carrying an allowed call
ID without checking exact result content or enforcing single use. Three
generator tests produced false greens for an injected event argument, a
mismatched output, and a duplicate output. That instrument version is rejected.

The first recovery review then found a second P1: the preamble and whole-result
blocks accepted extra properties, so a path hidden beside valid forwarded text
could bypass the payload-level scan. That instrument version is also rejected.
The closed-shape review found a third P1 cluster: event and invocation envelopes
accepted extra properties, alternate outer record types were ignored, and a
`browser_evaluate` result could assert a target `Page URL` without observing
that page. That instrument version is rejected as well. The repair now requires
closed transcript, event, invocation, result, content, executor-call,
executor-output, preamble, and forwarded-block shapes. Unknown outer record
types, duplicate MCP event IDs, and orphan or duplicate executor outputs fail.
Target observation requires a real `browser_navigate` result at the declared
HTTPS origin.

`node .claude/uat/certified-gate/audit-js/audit-controls.mjs` now passes eight
validator controls and thirty-four transcript/provenance controls. The positive
control includes target output with `DESIGN.md`, `../`, and a displayed drive
path. Negative controls fail on the same path in an assistant message, a shell
call, computed tool lookup, appended code, forbidden file transfer, mismatched
Playwright result, unbound result, a non-Playwright MCP result, a host path in a
browser tool argument, injected event arguments, mismatched or duplicate
same-call output, result/content/preamble/block metadata, malformed preamble
text, unknown agent record forms, orphan output, cross-transcript correlation,
an absent or off-target page observation, alternate outer record types,
event/invocation/output envelope extensions, a fabricated `Page URL` returned
by `browser_evaluate`, and a spoofed truncation. A positive truncation control
proves that exact target-result prefixes and suffixes remain admissible. The
runtime auditor binds the observed page origin to the declared HTTPS target and
requires that observation to come from `browser_navigate`.

The corrected auditor also re-read the prior failed run's exact transcript and
returned: 174 lines, 133 agent-originated records, 29 validated Playwright
calls, 58 correlated browser-output records, zero evidence hits. This proves
the original certificate's two reported classes were audit false alarms; it
does not restore that run's discarded functional verdict.

The repaired task-local instrument requires a new independent affected-scope
review before one blind actor invocation may begin.
