# Functional UAT remediation

## Gate status

The 2026-08-08 blind actor run completed, but its shared-harness blindness
certificate failed. Its debrief is discarded for gate authority. The source
and primary in-app browser independently reproduced three user-task failures
against the same production-equivalent preview.

## Reproduced findings

1. The paper cards linked to `.md` files without Jekyll front matter. The
   server returned raw `text/markdown`, and the selected paper shell was
   absent.
2. The trace browser measured 584 CSS pixels wide in a 390-pixel viewport and
   had no visible route back to the field guide.
3. The plain-English results said the seven-point lead over the strongest
   runner-up survived correction. The corrected technical paper says only the
   approval-only comparison survived Holm correction and records an
   information-asymmetry limitation.

## Five whys

1. The mobile evidence task failed because primary routes did not preserve the
   selected shell, mobile containment, or corrected statistical meaning.
2. The paper files were treated as downloadable Markdown rather than rendered
   Jekyll pages, and the trace tool retained desktop-width assumptions.
3. The initial redesign preserved existing route implementations without
   traversing their complete mobile user journey.
4. Presentation checks covered the entry page and Build tables, while the
   paper-reading and trace-exploration branches were not connected to the same
   discriminating browser task.
5. No earlier production-equivalent mobile functional gate had followed both
   branches before promotion.

The repair invariant is: every primary route from the field guide renders as
usable HTML or a deliberately standalone tool, fits a 390-pixel viewport
without page-level horizontal scrolling, provides a visible return path, and
states corrected empirical claims consistently.

## Repair and deterministic proof

- Both paper sources now carry rendering-only front matter and explicit `.html`
  permalinks. The official GitHub Pages-equivalent build contains both HTML
  pages and no raw `.md` outputs.
- The trace browser now contains the visible `Research field guide` return link,
  full-width mobile filters, and wrapping containment. The in-app browser
  measured `innerWidth=390`, `documentScrollWidth=375`; filtering, opening a
  20-message trace, returning to the list, and returning to `/#explore` all
  passed.
- The corrected summary now distinguishes the first-place point estimate from
  the single Holm-surviving approval-only comparison.
- Production-equivalent index SHA-256:
  `DC982A7B62E7E23DD54A45D11B678F3718218865F9792A1C8522CD860C550659`.
- Focused library regression: 10 passed. New prose drafting check: passed.

A fresh certified blind run remains required. This note is deterministic
remediation evidence and does not claim functional acceptance.

## Independent-review P1 and repair

The first affected-scope review found a fourth functional defect before the
replacement blind run. Eighteen pairs of telecom rows share the same
60-character display task ID and trial. The browser used `find()` on that
abbreviation, so both rows opened the first source trace and 18 conversations
were unreachable.

The identity repair separates display text from identity. When a cell is first
opened, `trace-identity.js` binds its index rows to source rows by cell-local
position, validates displayed task prefix, trial, reward, and message count,
then assigns a stable identity from the cell, full task ID, and trial. Opening a
row resolves only that bound source position and fails loudly if the source
changes after binding.

The exhaustive connected check reports 648 rows, 18 source cells, 18 collision
groups, and 648 unique stable identities. Every source trace is reached once.
Negative controls reject a row/source order mismatch and a duplicate full-task
identity even when the colliding rows have the same reward and message count.
In the in-app browser, the two previously colliding MCP-style telecom rows both
opened 65-message conversations, the conversation bodies differed, and the
390-pixel viewport retained a 375-pixel document width.
