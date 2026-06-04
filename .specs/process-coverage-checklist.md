# Carmen Inventory — Process Coverage Checklist

Internal tracker (not a published Wiki.js page). Enumerates every Carmen Inventory
process by module — sourced from `../carmen/docs/` — and records whether the wiki
documents it. Answers: "is the Inventory documentation project finished?".

How to read: each row is a sub-process. **BR/UF/TS** = covered in the module's
`02-business-rules` / `03-user-flow*` / `04-test-scenarios*` page(s).
Symbols: ✅ complete · 🟡 partial/stub · ⬜ missing. See "How status is judged".

## Summary (as of 2026-06-04)

_Filled in Task 19 after all modules are audited._

| Module | Sub-processes | Done | Partial | Not yet | % complete |
|--------|--------------:|-----:|--------:|--------:|-----------:|
| _pending_ | | | | | |
| **Project total** | | | | | |

## How status is judged

- **BR / UF / TS cell:** `✅` usable section exists · `🟡` mentioned but incomplete/stub · `⬜` not found.
- **Page exists? / Content complete? (Table B):** same symbols for "file present" / "non-stub content".
- **Overall row Status:** `✅ Done` all coverage cells ✅ · `🟡 Partial` some but not all ✅ · `⬜ Not yet` all cells ⬜.

## Source mapping

| Wiki module | carmen/docs source folder |
|-------------|---------------------------|
| good-receive-note | good-recive-note-managment/ |
| purchase-request | purchase-request-management/ |
| purchase-order | purchase-order-management/ |
| store-requisition | store-requisitions/ |
| inventory-adjustment | inventory-adjustment/ |
| costing | costing/ |
| inventory | inventory-management/ |
| product | product-management/ |
| recipe | recipe/ , recipe-module/ |
| vendor-pricelist | vendor-pricelist-management/ |
| physical-count | inventory-management/ , use-cases/ , features/ |
| spot-check | inventory-management/ , use-cases/ , features/ |
| master-data | settings/ , prisma-schema/ |
| system-config | settings/ , prisma-schema/ |
| dashboard | features/ , pages/ |
| access-control | security/ , settings/ |
| reporting-audit | reports/ , features/ |
| templates | templates/ |

## Table A — Process modules

_Modules with the standard 01–04 page set. One `###` section per module, added by Tasks 1–12._

### 1. Good Receive Note
Source: `../carmen/docs/good-recive-note-managment/`

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Receive against PO | ✅ | ✅ | ✅ | ✅ Done | [BR §2, §5, §6](/en/inventory/good-receive-note/02-business-rules) |
| 2 | Direct / manual GRN (no PO) | ✅ | ✅ | ✅ | ✅ Done | [UF — Receiver](/en/inventory/good-receive-note/03-user-flow-receiver) |
| 3 | Partial receipt | ✅ | ✅ | ✅ | ✅ Done | [BR §2 GRN_VAL_009](/en/inventory/good-receive-note/02-business-rules) |
| 4 | Over-receipt (with/without tolerance) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 GRN_VAL_009](/en/inventory/good-receive-note/02-business-rules) |
| 5 | FOC (free-of-charge) items | ✅ | 🟡 | 🟡 | 🟡 Partial | [BR §3 GRN_CALC_001/012](/en/inventory/good-receive-note/02-business-rules) |
| 6 | Extra-cost allocation (manual / by_value / by_qty) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 GRN_CALC_009–011](/en/inventory/good-receive-note/02-business-rules) |
| 7 | Tax handling (inclusive vs exclusive pricing) | ✅ | 🟡 | 🟡 | 🟡 Partial | [BR §3 GRN_CALC_003/004](/en/inventory/good-receive-note/02-business-rules) |
| 8 | Returns / credit note (post-commit correction) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 GRN_POST_009/010](/en/inventory/good-receive-note/02-business-rules) |
| 9 | Posting to inventory on commit | ✅ | ✅ | ✅ | ✅ Done | [BR §5 GRN_POST_003/004](/en/inventory/good-receive-note/02-business-rules) |
| 10 | Status lifecycle (draft → saved → committed → voided) | ✅ | ✅ | ✅ | ✅ Done | [UF — lifecycle](/en/inventory/good-receive-note/03-user-flow) |
| 11 | Multi-PO consolidation into one GRN | ✅ | ✅ | ✅ | ✅ Done | [BR §6 GRN_XMOD_002](/en/inventory/good-receive-note/02-business-rules) |
| 12 | Batch commit | ✅ | ✅ | ✅ | ✅ Done | [BR §4 GRN_AUTH_006](/en/inventory/good-receive-note/02-business-rules) |
| 13 | Lot number / expiry date assignment | ✅ | ✅ | ✅ | ✅ Done | [BR §2 GRN_VAL_012](/en/inventory/good-receive-note/02-business-rules) |
| 14 | Consignment receipt | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §5 GRN_POST_004](/en/inventory/good-receive-note/02-business-rules) |
| 15 | Non-inventory / expense item receipt | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §6 GRN_XMOD_004](/en/inventory/good-receive-note/02-business-rules) |
| 16 | Three-way match (PO ↔ GRN ↔ invoice) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 GRN_POST_007–009](/en/inventory/good-receive-note/02-business-rules) |
| 17 | Vendor cancellation of PO line items (BR-02) | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §6 GRN_XMOD_003](/en/inventory/good-receive-note/02-business-rules) |
| 18 | Multi-currency / FX handling | ✅ | ✅ | ✅ | ✅ Done | [BR §3 GRN_CALC_008](/en/inventory/good-receive-note/02-business-rules) |

## Table B — Config / reference modules

_Reference/admin modules. One `###` section per module, added by Tasks 13–18._

## Maintenance notes

- Living doc — update by hand when wiki pages are added/expanded.
- Bump the `(as of …)` date in the Summary heading whenever rows change.
- Re-run Task 19's count when any row status changes.
