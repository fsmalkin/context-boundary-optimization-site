# CBO sales landing mock validation

Date: 2026-08-09
Stage: full-loop-mock-first R&D, uncertified
Live homepage: unchanged at `main@995572c1c453fe030ae53e0ab6eb2990b66ce158`

## Candidate

The candidate contains one mock board, three responsive directions, one shared
style sheet, research synthesis, a frame-blind copy pass, and rendered evidence.
It edits no live route. It reuses the selected CBO marks and hand-sketched raster
illustrations. Image generation, Gemini, Filevine, and other drafting-provider
operations remain held.

| Artifact | SHA-256 | Evidence size |
| --- | --- | --- |
| `mocks/open-source-product/index.html` | `FD9CE9E8E6F745999203DB7204F8E399CBD48EF13975831A158BA98824D0B843` | source |
| `mocks/open-source-product/direction-1.html` | `0B7F4934E45E85F39850CEF9632AC3CB11DA2B8B83740DFA06F633D0C520E924` | source |
| `mocks/open-source-product/direction-2.html` | `2176F9E8EA7701482FE95F09C0CEF95AC827CD939D80EA2D6F4600AA09A37D33` | source |
| `mocks/open-source-product/direction-3.html` | `2BA92D52A0E78F2FC26301CBC7ABA2934E160CC1CCBAD5ECDACB5B6EB6BB996D` | source |
| `mocks/open-source-product/mock.css` | `150BFC7B07F226556F9363CF0C0DF88E36A197157EC80A65AABD5B87A7487CD5` | source |
| Problem-first mobile viewport | `F095F6BB204268926F60C66169E0A2B4D874EF23FED0853AFCFA074C2A8FAF6A` | 375 x 812 |
| Problem-first desktop viewport | `D12280FE83A0A906B93C7522586D8BF7FB93903EB49602E813A7998E78EFC386` | 1265 x 712 |
| Mechanism-first mobile viewport | `5BB153DF1697824D619077EB4A98519CDF8F450A0E20056DEAAC1D0A63D18D5F` | 375 x 812 |
| Mechanism-first desktop viewport | `3BCA5B5CA5C0BFF17B6B1EE6B22D00DF0C94A118513ABBC62D0E38F03744DD4C` | 1265 x 712 |
| Adoption-first mobile viewport | `9298A22BB2CA8B7299D18285CA8BBF13E2C499162C62FEB269771C65DF15FD80` | 375 x 812 |
| Adoption-first desktop viewport | `04697CC1CBB9FD9610BBAEAB2660F3AC279788844B2D971EA7D540BAE4EDE236` | 1265 x 712 |
| Mobile first-screen comparison | `53916E14E50303B2E322CCDC7175503AA514ADED7CEC51A458A38045FBDBFB6C` | 1585 x 854 |

The configured test viewports were 390 x 844 and 1280 x 720. The captured
content areas were 375 x 812 and 1265 x 712 after browser chrome. Each document
reported matching client and scroll widths.

## Evidence recovery

Independent review of `a350aa9c590ea02dfcf89240df772be8d8bdd041`
failed the screenshot instrument. The browser's `fullPage` capture returned a
blank two-color canvas even though the same loaded page produced a valid normal
viewport capture. A direct generator control reproduced the 10,608-byte blank
result. The earlier check verified dimensions, hashes, DOM state, and image
readiness, while the side-by-side board used a separate valid first-screen
capture. None of those checks proved that the full-page files contained page
content.

The remediation replaces the blank files with normal mobile and desktop
viewport captures and removes the redundant fold aliases. The focused
`check_sales_landing_captures.py` control now requires readable dark pixels,
nontrivial image entropy, at least 1,000 colors, expected dimensions, and a
unique capture per direction. The discarded canvases had a zero dark-pixel
ratio, entropy below 1.9, and no more than 106 colors. Every corrected capture
passes with a dark-pixel ratio above 0.06 and entropy above 5.0.

The same remediation changes Direction 3 to "Give each agent the service
context for its task" and replaces the board's flow-content `span` wrappers
with `div` elements. Those edits resolve the two remaining review findings
without changing a live route.

## Rendered checks

- All three mobile viewport renders reported
  `clientWidth == scrollWidth == 375`.
- All three desktop viewport renders reported
  `clientWidth == scrollWidth == 1265`.
- Every referenced image completed with positive natural dimensions.
- The hero copy precedes the hero illustration on all three mobile directions.
- The configured mobile and desktop runs produced zero warning or error logs.
- Each direction contains one H1, one main landmark, labeled primary navigation,
  unique IDs, complete image alternatives, non-empty links, and valid on-page
  fragments.
- Primary navigation uses Why CBO, How it works, Build, Research, and GitHub.
  Evidence appears only through the supporting credibility band.
- Every direction uses `Open the billing example` as its primary action.
- The corrected side-by-side inspection confirms warm plain paper, printed type,
  existing raster sketches, mobile-first hierarchy, and no ruled page surface
  or cursive text.

## Deterministic gates

- `npx impeccable detect mocks/open-source-product`: exit 0.
- `check_sales_landing_captures.py`: exit 0 across the three mobile captures,
  three desktop captures, and the comparison board.
- Strong Drafting Style hard checks across mock source and design evidence:
  exit 0, with two review-only exhaustive-list candidates retained.
- `git diff --check`: exit 0.
- Sprint preflight with admission and exclusive writer binding: exit 0 at scope
  SHA-256 `6EF253BB76E1789959527AF1644B82321DA2DA68608A800667E83A680EA84C0F`.
- Source-server HTTP checks: the board, three variants, CSS, homepage, library,
  billing example, papers index, demos, license, and reused assets returned 200.
  The source-only Python server lacks Jekyll output for the two rendered paper
  routes. Their current GitHub Pages URLs independently returned 200, which is
  the relevant publication behavior for those relative links.

## Reader and claim checks

The baseline and per-direction blind evidence lives in
`sales-landing-research.md`. Each final direction passed category recognition,
API/MCP/CBO differentiation, relevance, and primary-action comprehension.
Direction 1 is the recommendation because it opens with the requested layer
distinction and routes directly to the working example.

The forty-operation to four-action billing scenario is explicitly illustrative.
The linked billing-service reference example demonstrates the contract, gate,
and receipt structure in its existing service scenario. The mocks make no
production-readiness, interoperability, reliability, cost, or completed-
validation claim.
