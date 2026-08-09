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

| Artifact | SHA-256 | Rendered size |
| --- | --- | --- |
| `mocks/open-source-product/index.html` | `006D1A6036D80C8A49BE98F4400C35B3B4E24AF6ED5DEDD0A9BC8E4939FA68BB` | source |
| `mocks/open-source-product/direction-1.html` | `0B7F4934E45E85F39850CEF9632AC3CB11DA2B8B83740DFA06F633D0C520E924` | source |
| `mocks/open-source-product/direction-2.html` | `2176F9E8EA7701482FE95F09C0CEF95AC827CD939D80EA2D6F4600AA09A37D33` | source |
| `mocks/open-source-product/direction-3.html` | `D3C684604AADB7D4EC3459149DAC26971FDF990F6A2E0FD70608BA1DBEEE3975` | source |
| `mocks/open-source-product/mock.css` | `150BFC7B07F226556F9363CF0C0DF88E36A197157EC80A65AABD5B87A7487CD5` | source |
| Problem-first mobile | `998EE0A5A8EBAF99370401C448150CC75D175AA97703554AAA01F2C26CD63771` | 375 x 3267 |
| Problem-first desktop | `F9A82F4C8486179F9791C02B0BBEDD0BB8FA20AC8C26F0FA91C33203BE77FA54` | 1265 x 2370 |
| Mechanism-first mobile | `3F5F1E355CDF62ED03D1B87FE45046880C5ACB9166191050BE8D20FB234870B1` | 375 x 3249 |
| Mechanism-first desktop | `0E44148C90C08FB084F361A101E4A53388E31083CBF30D2A0A0D0C54FAB2031E` | 1265 x 2822 |
| Adoption-first mobile | `657556EDE4811193DC2BF09CBD54EF5AD5DAB5AAF60843E7364058874B832568` | 375 x 3481 |
| Adoption-first desktop | `E6A24615713BF0DEC7912793F39D14A3E66BBA5E0DD7BDBE65520B162CA25E57` | 1265 x 2381 |
| Mobile first-screen comparison | `21E6A654966AC76C327E202F54FC30FA516BCD53202A0A186C9A7D6DA79D4D4A` | 1600 x 862 |

The configured test viewports were 390 x 844 and 1280 x 720. The in-app
browser's captured content areas were 375 and 1265 pixels wide after browser
chrome. Each document reported matching client and scroll widths.

## Rendered checks

- All three mobile renders reported `clientWidth == scrollWidth == 375`.
- All three desktop renders reported `clientWidth == scrollWidth == 1265`.
- Every referenced image completed with positive natural dimensions.
- The hero copy precedes the hero illustration on all three mobile directions.
- The configured mobile and desktop runs produced zero warning or error logs.
- Each direction contains one H1, one main landmark, labeled primary navigation,
  unique IDs, complete image alternatives, non-empty links, and valid on-page
  fragments.
- Primary navigation uses Why CBO, How it works, Build, Research, and GitHub.
  Evidence appears only through the supporting credibility band.
- Every direction uses `Open the billing example` as its primary action.
- The final side-by-side inspection confirms warm plain paper, printed type,
  existing raster sketches, mobile-first hierarchy, and no ruled page surface
  or cursive text.

## Deterministic gates

- `npx impeccable detect mocks/open-source-product`: exit 0.
- Strong Drafting Style hard checks across mock source and design evidence:
  exit 0, with two review-only exhaustive-list candidates retained.
- `git diff --check`: exit 0.
- Sprint preflight with admission and exclusive writer binding: exit 0 at scope
  SHA-256 `036F388222053F8ABBE05DA21C0688044862C56478A93DEF57DAEE7FF7EA4C05`.
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
