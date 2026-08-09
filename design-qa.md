# Design QA: Research Field Guide

- Source visual truth: `C:\Users\Fred\.codex\generated_images\019fe30f-d649-7f31-bf96-f6f6fda5e74b\exec-3b10c2b7-8c00-4e91-9473-08bb69096708.png`
- Owner refinement: keep the plain-paper and hand-sketched direction; remove ruled-paper cues and cursive or script typography; introduce CBO for nontechnical product managers before the deep dives.
- Browser-rendered implementation: `.claude/design-qa/pm-home-mobile.png`
- Desktop adaptation: `.claude/design-qa/pm-home-desktop.png`
- Same-input comparison: `.claude/design-qa/pm-home-comparison.png`
- Figure-family contact sheet: `.claude/design-qa/figures-contact-sheet.png`
- Route: `http://127.0.0.1:48168/context-boundary-optimization-site/`
- State: anonymous, light theme, page top, all above-the-fold images loaded
- CSS viewport: `390 x 844`
- Device scale factor: `1`
- Source pixels: `853 x 1844`, normalized to `390 x 844`
- Implementation pixels: `390 x 844`
- Desktop evidence: `1280 x 720` CSS viewport and pixels
- Comparison pixels: `800 x 894`
- Mobile SHA-256: `073AAF9709CDDC5CF7132F884BA88D9076143960D72AB10CF8F06AF1A30A82CB`
- Desktop SHA-256: `7554B10479B359D17F17DD59EC1FE1BBAC41EFE8B49BC6FA7C3FC93F3F531B34`
- Comparison SHA-256: `584B56D1C1E1ADF872A7E93039D317B20A96BE690762244D0051DBD00E222C61`
- Figure-family contact sheet SHA-256: `F7D782A39A7926F80B97B7BF77538681F0545C2C46BDF8B32184BA70B489E0E6`

The flow under test is: homepage opens -> a product manager understands the API-to-agent context gap -> the reader chooses Research, Implementation, or Evidence -> the matching existing deep-dive page opens.

## Findings

- All blocking and moderate visual mismatches are resolved.
- [P3] The implementation omits the mock's decorative paper clips and chevron glyphs. Each index card remains a clear, keyboard-focusable link with a 96-pixel touch surface. The card treatment preserves the navigation hierarchy without substituting CSS or text drawings for real assets.
- [P3] The working-drafts stamp appears near the title rather than at the bottom of the opening frame. This keeps a live research-status boundary visible before navigation and preserves the selected visual language.
- [P3] The homepage uses a product-manager headline in place of the mock's research title. Context-Boundary Optimization appears in the first explanatory sentence, while the title carries the owner-requested comprehension job.

## Required Fidelity Surfaces

- Fonts and typography: every HTML heading and display string uses the printed `Trebuchet MS`, `Aptos`, `Segoe UI`, sans-serif stack. The rendered `h1` and lede expose that computed stack at `390 x 844`. No CSS source or built CSS contains a cursive or script fallback. The workflow's short raster labels remain hand-printed and legible.
- Spacing and layout rhythm: the CBO mark, product-manager headline, explanation, and cropped workflow establish the opening mobile sequence. The first problem heading enters the same frame. Cards retain the selected ink borders and slight rotations, with shadows farther down the page. Desktop expands the same hierarchy without horizontal overflow.
- Colors and visual tokens: warm plain paper, navy ink, muted teal, sage, orange, and pale blue preserve the selected direction. The shell has `background-image: none`; the notebook margin rule and ruled texture are absent.
- Image quality and asset fidelity: the workflow, books, toolbox, CBO mark, and research figures are real raster assets. The workflow is cropped to its printed inner panel, which supplies the final visible bounds. Browser readback found natural widths for all six homepage images after lazy-load traversal. Source inspection identifies each custom visible asset as a raster file.
- Copy and content: the homepage first states the product outcome, then explains the familiar API context gap and defines the context contract. Research, Implementation, and Evidence route depth to the existing papers, library, and demos. Working-draft status and every underlying paper, code, demo, PDF, figure, and license route remain available.

## Full-View Comparison Evidence

`.claude/design-qa/pm-home-comparison.png` places the selected direction and the owner-directed refinement together at the same `390 x 844` viewport. The comparison verifies that the paper palette, ink outlines, workflow, and sketch family remain recognizable while the ruled background, script title, and research-first opening are replaced.

## Focused Region Evidence

At `800 x 894`, the comparison keeps the product headline, explanation, workflow labels, CBO mark, first PM-oriented section, colors, and borders legible at one-to-one implementation pixels. `.claude/design-qa/pm-home-desktop.png` separately verifies the responsive header and desktop hero proportions.

## Comparison History

1. Initial comparison: blocked by a P1 opening-frame mismatch. The centered three-line title pushed the cards below the mobile fold while the enlarged workflow consumed too much height. Fix: restore the selected left-aligned two-line title and scale the workflow to its measured slot. Compact the cards to the selected field-guide density.
2. Second comparison: blocked by a P2 content-and-asset mismatch. The card art mapped to the wrong destinations; Papers also lacked the technical/economic structure. Fix: add the two-row Papers preview. Place the book asset with Build and the toolbox with Explore.
3. Third comparison: blocked by a P2 asset-fidelity and accessibility mismatch. The CBO mark was a styled text badge, the ruled paper used CSS-generated lines, and mobile navigation targets were below 44 pixels. Fix: extract the exact selected CBO mark as a transparent raster, use the generated paper texture asset directly, and raise the navigation targets to 44 pixels.
4. Final comparison: passed. The post-fix evidence is `.claude/design-qa/design-qa-comparison.png`; all P0-P2 findings are resolved.
5. Owner refinement: Fred kept the overall direction and removed the ruled-paper and cursive treatments. The shell now uses a flat warm-paper surface, the old notebook margin rule is absent, HTML display copy uses a printed sans-serif stack, and the workflow crops out its ruled surround.
6. PM-first UAT repair: the academic definition no longer leads the page. The first mobile flow now states the product outcome, explains the API context gap, defines the context contract in plain language, and sends technical depth to existing navigation. The affected-scope comparison and browser checks pass.

## Post-review responsive correction

Independent review found that the paper shell could conceal overflow from long Build-page tables at mobile width. The narrow-screen table layout now keeps table semantics while wrapping long cell content inside the available columns. At `390 x 844`, both the worked billing example and library tests page have zero overflowing cells and zero page-level horizontal overflow. Evidence and exact screenshots are recorded in `.claude/design-qa/table-fix-mobile.md`.

## Primary Interactions Tested

- `Research` opens `/papers/` and exposes the `Papers` heading.
- `Implementation` opens `/library/` and exposes the `context_contract` heading.
- `Evidence` opens `/demos/` and exposes the `Interactive` heading.
- The trace browser was opened through the demos route and exposed its real trace controls.
- Browser console warnings and errors: none.
- Mobile horizontal overflow: none; all element rectangles remain within the `390`-pixel viewport and document width is `375` pixels after the browser scrollbar.
- Desktop horizontal overflow: none; all element rectangles remain within the `1280`-pixel viewport and document width is `1265` pixels after the browser scrollbar.
- Missing image alternatives, unnamed links, duplicate IDs, heading skips, broken images, and missing local anchors: none.

## Carrier and deletion evidence

| Visible string | Job | Existing carrier | Verdict |
| --- | --- | --- | --- |
| `Working drafts` | Preserves the research-status boundary before action | No visual control carries research maturity | Keep |
| `Give AI agents the right context for each task` | States the product outcome for the target reader | The workflow shows sequence without naming the outcome | Keep |
| Hero explanation | Defines CBO as a service-prepared operating brief | The workflow carries sequence; prose carries service ownership and rule semantics | Keep |
| `For product teams` | Names the intended reader at the problem transition | No other local carrier states the audience | Keep |
| Research, Implementation, Evidence | Provides three existing deep-dive actions | The links are the action carriers | Keep |
| `A concrete example` | Repeated the refund heading's visible job | `A refund task should begin with a focused brief` | Cut |
| `Choose your depth` | Repeated the deep-dive heading and navigation | `Open the deep dive that matches your job` plus the three links | Cut |

The strong-drafting checker passed. The manual reading pass found no corrective negation, em dash, summary beat, or unsupported effect claim in the new homepage copy. `impeccable` is unavailable on this host, so no result is claimed for that separate visual-craft instrument.

## Implementation Checklist

- [x] Match the selected mobile hierarchy and art direction.
- [x] Use real raster assets for the visible custom art.
- [x] Keep all primary navigation functional and keyboard-focusable.
- [x] Preserve real research, code, demo, PDF, figure, and license routes.
- [x] Verify mobile and desktop browser rendering.
- [x] Exclude QA evidence and the removed comparison route from publication.

final result: passed
