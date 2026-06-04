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

### 2. Purchase Request
Source: `../carmen/docs/purchase-request-management/`

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create PR (blank — header + items) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PR_VAL_001–015](/en/inventory/purchase-request/02-business-rules) |
| 2 | Create PR from template | ✅ | ✅ | ✅ | ✅ Done | [UF — Requestor §2](/en/inventory/purchase-request/03-user-flow-requestor) |
| 3 | Add / edit line items (qty, UoM, price, FOC, discount, tax) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PR_VAL_007–013](/en/inventory/purchase-request/02-business-rules) |
| 4 | Submit PR (draft → in_progress, budget soft-commit) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_002](/en/inventory/purchase-request/02-business-rules) |
| 5 | Budget availability check at submit | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PR_VAL_015](/en/inventory/purchase-request/02-business-rules) |
| 6 | Multi-stage approval routing (Department Head → Budget Controller → Finance) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PR_AUTH_001–005](/en/inventory/purchase-request/02-business-rules) |
| 7 | Approve at intermediate stage | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_004](/en/inventory/purchase-request/02-business-rules) |
| 8 | Final-stage approve (in_progress → approved) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_005](/en/inventory/purchase-request/02-business-rules) |
| 9 | Reject PR (header-level, terminates chain, releases soft-commit) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_006](/en/inventory/purchase-request/02-business-rules) |
| 10 | Send-back / return PR to requestor | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_003](/en/inventory/purchase-request/02-business-rules) |
| 11 | Split-reject (accept some lines, reject others) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PR_AUTH_003](/en/inventory/purchase-request/02-business-rules) |
| 12 | Approve with quantity adjustment (approved_qty < requested_qty) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PR_VAL_013](/en/inventory/purchase-request/02-business-rules) |
| 13 | Delegate approval authority | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 PR_AUTH_006](/en/inventory/purchase-request/02-business-rules) |
| 14 | Threshold-based escalation to Procurement Manager | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PR_AUTH_005](/en/inventory/purchase-request/02-business-rules) |
| 15 | Cancel / void draft PR (requestor-initiated before submit) | ✅ | ✅ | ✅ | ✅ Done | [UF — Requestor §3](/en/inventory/purchase-request/03-user-flow-requestor) |
| 16 | Admin void (Finance / sys-admin, any post-submit stage) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PR_AUTH_007](/en/inventory/purchase-request/02-business-rules) |
| 17 | Resubmit / amend after send-back | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_003](/en/inventory/purchase-request/02-business-rules) |
| 18 | Convert PR → PO (full conversion) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_007](/en/inventory/purchase-request/02-business-rules) |
| 19 | Convert PR → PO (partial conversion) | ✅ | ✅ | ✅ | ✅ Done | [UF — Purchaser §3](/en/inventory/purchase-request/03-user-flow-purchaser) |
| 20 | Multi-PR consolidation into one PO (same vendor + currency) | 🟡 | ✅ | ✅ | 🟡 Partial | [BR §6 cross-module rules](/en/inventory/purchase-request/02-business-rules) |
| 21 | Vendor allocation / Allocate Vendor dialog | ✅ | ✅ | ✅ | ✅ Done | [UF — Purchaser §2](/en/inventory/purchase-request/03-user-flow-purchaser) |
| 22 | Pricelist deviation check at conversion | 🟡 | ✅ | ✅ | 🟡 Partial | [UF — Purchaser §3](/en/inventory/purchase-request/03-user-flow-purchaser) |
| 23 | Financial calculations (subtotal / discount / tax / base-currency roll-up) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 PR_CALC_001–008](/en/inventory/purchase-request/02-business-rules) |
| 24 | Multi-currency / FX rate snapshot | ✅ | ✅ | ✅ | ✅ Done | [BR §3 PR_CALC_006](/en/inventory/purchase-request/02-business-rules) |
| 25 | Status lifecycle (draft → in_progress → approved → completed / voided) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_001–007](/en/inventory/purchase-request/02-business-rules) |

## Table B — Config / reference modules

_Reference/admin modules. One `###` section per module, added by Tasks 13–18._

## Maintenance notes

- Living doc — update by hand when wiki pages are added/expanded.
- Bump the `(as of …)` date in the Summary heading whenever rows change.
- Re-run Task 19's count when any row status changes.
