# Design QA: Research Field Guide

- Source visual truth: `C:\Users\Fred\.codex\generated_images\019fe30f-d649-7f31-bf96-f6f6fda5e74b\exec-3b10c2b7-8c00-4e91-9473-08bb69096708.png`
- Browser-rendered implementation: `.claude/design-qa/design-qa-mobile.png`
- Desktop adaptation: `.claude/design-qa/design-qa-desktop.png`
- Same-input comparison: `.claude/design-qa/design-qa-comparison.png`
- Figure-family contact sheet: `.claude/design-qa/figures-contact-sheet.png`
- Route: `http://127.0.0.1:48166/context-boundary-optimization-site/`
- State: anonymous, light theme, page top, all above-the-fold images loaded
- CSS viewport: `390 x 844`
- Device scale factor: `1`
- Source pixels: `853 x 1844`, normalized to `390 x 844`
- Implementation pixels: `390 x 844`
- Desktop evidence: `1280 x 720` CSS viewport, captured at `2022 x 1138` host pixels
- Comparison pixels: `800 x 894`
- Comparison SHA-256: `B40760533E9F3B44995DFD861D990C78E0A6C19FB4EC36363988F1A03ACA5828`
- Figure-family contact sheet SHA-256: `F7D782A39A7926F80B97B7BF77538681F0545C2C46BDF8B32184BA70B489E0E6`

The in-app browser exposed a `617 x 1334` host-pixel backing surface for the `390 x 844` CSS frame after desktop breakpoint testing. The final mobile image uses the first exact CSS viewport tile and is normalized to `390 x 844`; no design region is cropped.

## Findings

- All blocking and moderate visual mismatches are resolved.
- [P3] The implementation omits the mock's decorative paper clips and chevron glyphs. Each index card remains a clear, keyboard-focusable link with a 96-pixel touch surface. The card treatment preserves the navigation hierarchy without substituting CSS or text drawings for real assets.
- [P3] The working-drafts stamp appears near the title rather than at the bottom of the opening frame. This keeps a live research-status boundary visible before navigation and preserves the selected visual language.

## Required Fidelity Surfaces

- Fonts and typography: the marker stack matches the informal navy handwritten hierarchy, preserves the selected two-line title at `390 px`, and keeps the research description readable without truncation. Small navigation and stamp text use a high-contrast system UI face.
- Spacing and layout rhythm: the CBO mark, title, workflow, and all three field-guide cards fit inside the opening mobile frame. Card spacing, ink borders, slight rotations, and shadows retain the index-card rhythm. The desktop adaptation expands the same hierarchy without horizontal overflow.
- Colors and visual tokens: cream paper, navy ink, muted teal, sage, orange, and pale blue match the selected direction. Text and controls retain strong contrast against the paper surface.
- Image quality and asset fidelity: the paper texture, workflow, books, toolbox, CBO mark, and research figures are real raster assets. The opening assets are lossily compressed WebP derivatives inspected after conversion; labels and ink edges remain sharp at their rendered sizes. No inline SVG, emoji, placeholder, or CSS-drawn substitute is present.
- Copy and content: the selected title and project description are preserved. Papers, Build, and Explore remain the three primary destinations. Working-draft status and the real paper, library, demo, PDF, figure, and license routes remain explicit.

## Full-View Comparison Evidence

`.claude/design-qa/design-qa-comparison.png` places the selected direction and final browser capture together at the same `390 x 844` viewport. The comparison verifies hierarchy, opening-frame density, ruled-paper treatment, title wrapping, workflow scale, card sequence, palette, and image placement.

## Focused Region Evidence

No additional crop was needed. At `800 x 894`, the same-input comparison keeps the title, description, workflow labels, card labels, CBO mark, borders, and shadows legible at one-to-one implementation pixels. `.claude/design-qa/design-qa-desktop.png` separately verifies the responsive header and desktop hero proportions.

## Comparison History

1. Initial comparison: blocked by a P1 opening-frame mismatch. The centered three-line title pushed the cards below the mobile fold while the enlarged workflow consumed too much height. Fix: restore the selected left-aligned two-line title and scale the workflow to its measured slot. Compact the cards to the selected field-guide density.
2. Second comparison: blocked by a P2 content-and-asset mismatch. The card art mapped to the wrong destinations; Papers also lacked the technical/economic structure. Fix: add the two-row Papers preview. Place the book asset with Build and the toolbox with Explore.
3. Third comparison: blocked by a P2 asset-fidelity and accessibility mismatch. The CBO mark was a styled text badge, the ruled paper used CSS-generated lines, and mobile navigation targets were below 44 pixels. Fix: extract the exact selected CBO mark as a transparent raster, use the generated paper texture asset directly, and raise the navigation targets to 44 pixels.
4. Final comparison: passed. The post-fix evidence is `.claude/design-qa/design-qa-comparison.png`; all P0-P2 findings are resolved.

## Primary Interactions Tested

- `Papers` scrolls to `#papers` and exposes the `Read the research` heading.
- `Build` opens `/library/` and exposes the `context_contract` heading.
- `Explore` opens `/demos/` and exposes the `Interactive` heading.
- The trace browser was opened through the demos route and exposed its real trace controls.
- Browser console warnings and errors: none.
- Mobile horizontal overflow: none (`scrollWidth = innerWidth = 390`).
- Missing image alternatives, unnamed links, duplicate IDs, heading skips, broken images, and missing local anchors: none.

## Implementation Checklist

- [x] Match the selected mobile hierarchy and art direction.
- [x] Use real raster assets for the visible custom art.
- [x] Keep all primary navigation functional and keyboard-focusable.
- [x] Preserve real research, code, demo, PDF, figure, and license routes.
- [x] Verify mobile and desktop browser rendering.
- [x] Exclude QA evidence and the removed comparison route from publication.

## Follow-up Polish

- Optional: generate dedicated paper-clip and chevron assets in a later admitted visual-polish slice if Fred wants the decorative details reproduced exactly.

final result: passed
