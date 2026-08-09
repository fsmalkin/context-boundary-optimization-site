# Mobile table-fix verification

- Browser: selected Codex in-app browser
- CSS viewport: 390 x 844
- Device scale factor: 1
- Build: official GitHub Pages gem / Jekyll 3.10.0 production-equivalent local build

## Worked billing example

- Route: `/context-boundary-optimization-site/library/examples/billing-service/`
- Screenshot: `table-fix-billing-mobile.png`
- SHA-256: `A02F9D1914178028CB8752C65AF5CC79341D2130CC4FEE9950B98EB1D8735B23`
- Page width: `390`; table client/scroll widths: `329 / 328`
- Computed table layout: `fixed`
- Cells whose scroll width exceeded client width: `0`

## Library tests

- Route: `/context-boundary-optimization-site/library/tests/`
- Screenshot: `table-fix-tests-mobile.png`
- SHA-256: `C68F17DC1A9CE85BAA2C3B8BF2C08D9675A3B87024482466A30AE66A7D156BDF`
- Page width: `390`; table client/scroll widths: `329 / 328`
- Computed table layout: `fixed`
- Cells whose scroll width exceeded client width: `0`

Both pages retained table semantics (`display: table`), wrapped long cell content inside the available columns, and produced no page-level horizontal overflow. The probe was connected to each intended route through its distinct title, table row count, and visible screenshot. A cell or table overflow would change the measured deltas and fail this receipt.
