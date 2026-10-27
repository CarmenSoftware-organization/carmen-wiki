# Carmen Inventory — Process Coverage Checklist

Internal tracker (not a published Wiki.js page). Enumerates every Carmen Inventory
process by module — sourced from `../carmen/docs/` — and records whether the wiki
documents it. Answers: "is the Inventory documentation project finished?".
The Platform book has its own sibling tracker: `.specs/platform-coverage-checklist.md`.

How to read: each row is a sub-process. **BR/UF/TS** = covered in the module's
`02-business-rules` / `03-user-flow*` / `04-test-scenarios*` page(s).
Symbols: ✅ complete · 🟡 partial/stub · ⬜ missing. See "How status is judged".

Source HEADs for the 2026-10-27 re-sync: carmen-turborepo-backend `c9d788829`, carmen-frontend `391062b5`, bruno `5c98670`, e2e `d795a25`; baseline = the 2026-09-22 HEADs.

Source HEADs for the 2026-09-22 re-sync (history): backend-v2 `ef4d6f08f`, frontend-react `0713cbc9`, bruno `7f96637`, e2e `809d8e3`; baseline wiki `21fa189` (2026-07-29).

## Summary (as of 2026-10-27 — EN re-sync; TH deferred)

| Module | Sub-processes | Done | Partial | Not yet | % complete |
|--------|--------------:|-----:|--------:|--------:|-----------:|
| Good Receive Note | 28 | 21 | 7 | 0 | 75% |
| Purchase Request | 34 | 25 | 9 | 0 | 74% |
| Purchase Order | 36 | 32 | 4 | 0 | 89% |
| Store Requisition | 29 | 24 | 5 | 0 | 83% |
| Inventory Adjustment | 19 | 13 | 6 | 0 | 68% |
| Costing | 20 | 15 | 5 | 0 | 75% |
| Inventory | 40 | 34 | 6 | 0 | 85% |
| Product | 13 | 12 | 1 | 0 | 92% |
| Recipe | 24 | 20 | 4 | 0 | 83% |
| Vendor Pricelist | 26 | 22 | 4 | 0 | 85% |
| Physical Count | 14 | 14 | 0 | 0 | 100% |
| Spot Check | 14 | 13 | 1 | 0 | 93% |
| Master Data | 20 | 19 | 1 | 0 | 95% |
| System Config | 19 | 19 | 0 | 0 | 100% |
| Dashboard | 12 | 12 | 0 | 0 | 100% |
| Access Control | 11 | 10 | 1 | 0 | 91% |
| Reporting & Audit | 13 | 13 | 0 | 0 | 100% |
| Templates | 4 | 4 | 0 | 0 | 100% |
| General Ledger | 5 | 4 | 0 | 1 | 80% |
| **Project total** | 381 | 326 | 54 | 1 | 86% |

Arithmetic (2026-10-27): Done = 21 + 25 + 32 + 24 + 13 + 15 + 34 + 12 + 20 + 22 + 14 + 13 + 19 + 19 + 12 + 10 + 13 + 4 + 4 = **326**; Partial = 7 + 9 + 4 + 5 + 6 + 5 + 6 + 1 + 4 + 4 + 0 + 1 + 1 + 0 + 0 + 1 + 0 + 0 + 0 = **54**; Not yet = 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 1 = **1**; total = 326 + 54 + 1 = **381**; 326 / 381 = **86%** (previous: 313 sub-processes, 255 / 56 / 2, 81% as of 2026-09-22; before that 279, 221 / 58 / 0, 79% as of 2026-06-09).

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
| general-ledger | (none in carmen/docs — backend-v2 `gl` module, Bruno `gl/*`, micro-cronjobs) |

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
| 5 | FOC (free-of-charge) items — FOC-only document now writes a movement and advances the PO FOC counter (fixed 2026-10-24; re-verified 2026-10-27) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 GRN_CALC_001/012; cross-persona TS #5, #12](/en/inventory/good-receive-note/02-business-rules) |
| 6 | Extra-cost allocation (manual / by_value / by_qty — live; written to `cost_layer.extra_cost_amount`; re-verified 2026-09-22) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 GRN_CALC_009–011](/en/inventory/good-receive-note/02-business-rules) |
| 7 | Tax handling (inclusive vs exclusive pricing) | ✅ | 🟡 | 🟡 | 🟡 Partial | [BR §3 GRN_CALC_003/004](/en/inventory/good-receive-note/02-business-rules) |
| 8 | Returns / credit note (post-commit correction) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 GRN_POST_009/010](/en/inventory/good-receive-note/02-business-rules) |
| 9 | Posting to inventory on commit — timing re-verified 2026-09-22: commit posts; average-costing BUs re-average at save | ✅ | ✅ | ✅ | ✅ Done | [BR §5 GRN_POST_003/004](/en/inventory/good-receive-note/02-business-rules) |
| 10 | Status lifecycle (draft → saved → committed → voided; reject path) — save / commit / void / reject re-verified 2026-09-22 | ✅ | ✅ | ✅ | ✅ Done | [UF — lifecycle](/en/inventory/good-receive-note/03-user-flow) |
| 11 | Multi-PO consolidation into one GRN | ✅ | ✅ | ✅ | ✅ Done | [BR §6 GRN_XMOD_002](/en/inventory/good-receive-note/02-business-rules) |
| 12 | Batch commit | ✅ | ✅ | ✅ | ✅ Done | [BR §4 GRN_AUTH_006](/en/inventory/good-receive-note/02-business-rules) |
| 13 | Lot number / expiry date assignment | ✅ | ✅ | ✅ | ✅ Done | [BR §2 GRN_VAL_012](/en/inventory/good-receive-note/02-business-rules) |
| 14 | Consignment receipt | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §5 GRN_POST_004](/en/inventory/good-receive-note/02-business-rules) |
| 15 | Non-inventory / expense item receipt | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §6 GRN_XMOD_004](/en/inventory/good-receive-note/02-business-rules) |
| 16 | Three-way match (PO ↔ GRN ↔ invoice) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 GRN_POST_007–009](/en/inventory/good-receive-note/02-business-rules) |
| 17 | Vendor cancellation of PO line items (BR-02) | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §6 GRN_XMOD_003](/en/inventory/good-receive-note/02-business-rules) |
| 18 | Multi-currency / FX handling | ✅ | ✅ | ✅ | ✅ Done | [BR §3 GRN_CALC_008](/en/inventory/good-receive-note/02-business-rules) |
| 19 | `POST …/verify` dry-run (pre-commit validation without side effects) | ✅ | ✅ | ✅ | ✅ Done | [BR §2](/en/inventory/good-receive-note/02-business-rules) |
| 20 | `GET …/stock-movements` (per-GRN ledger movements view) | ✅ | ✅ | ✅ | ✅ Done | [UF](/en/inventory/good-receive-note/03-user-flow) |
| 21 | `GET …/ref` reference documents (linked PO / CN lookup) | ✅ | ✅ | ✅ | ✅ Done | [UF](/en/inventory/good-receive-note/03-user-flow) |
| 22 | Draft save without full validation + out-of-period document-date prompt | ✅ | ✅ | ✅ | ✅ Done | [BR §2 / UF](/en/inventory/good-receive-note/03-user-flow) |
| 23 | Edit a `saved` GRN — allowed fields, stock lock (lot drawn by another document / live credit note / locked movement), content rules re-run (`GRN_VAL_021`–`023`; 2026-10-24) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 GRN_VAL_021–023; cross-persona TS #9](/en/inventory/good-receive-note/02-business-rules) |
| 24 | Committed GRN is header-only and frozen once an AP invoice takes a line (`GRN_VAL_024`, `GRN_COMMITTED_HEADER_ONLY`, `GRN_AP_LINKED_NOT_EDITABLE`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 GRN_VAL_024; cross-persona TS #11; FIN-AP-03](/en/inventory/good-receive-note/02-business-rules) |
| 25 | FIFO receipt-order guard — receipt date not earlier than the latest receipt of the product at the location in the period (`GRN_VAL_020`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 GRN_VAL_020; cross-persona TS #10](/en/inventory/good-receive-note/02-business-rules) |
| 26 | `commit_date` stamp on commit / approve (`updateGrnStatus`; 2026-10-16) — no TS scenario | ✅ | ✅ | ⬜ | 🟡 Partial | [data model](/en/inventory/good-receive-note/01-data-model) |
| 27 | PO picker `can_use` — From-PO wizard offers only receivable POs (`po_status ∈ approved / sent_or_print / partial`) — no BR rule, no TS scenario | ⬜ | ✅ | ⬜ | 🟡 Partial | [UF — Receiver](/en/inventory/good-receive-note/03-user-flow-receiver) |
| 28 | GRN → AP invoice cross-link — AP invoice built from committed GRN lines (`grn-candidates`, `matched_qty`), GRN edit lock it causes | ✅ | ✅ | ✅ | ✅ Done | [ap-invoice-from-grn](/en/inventory/general-ledger/ap-invoice-from-grn) |

### 2. Purchase Request
Source: `../carmen/docs/purchase-request-management/`

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create PR (blank — header + items) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PR_VAL_001–015](/en/inventory/purchase-request/02-business-rules) |
| 2 | Create PR from template | ✅ | ✅ | ✅ | ✅ Done | [UF — Requestor §2](/en/inventory/purchase-request/03-user-flow-requestor) |
| 3 | Add / edit line items (qty, UoM, price, FOC, discount, tax) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PR_VAL_007–013](/en/inventory/purchase-request/02-business-rules) |
| 4 | Submit PR (draft → in_progress; submit validation re-verified 2026-09-22 — budget soft-commit has no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_002](/en/inventory/purchase-request/02-business-rules) |
| 5 | Budget availability check at submit (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PR_VAL_015](/en/inventory/purchase-request/02-business-rules) |
| 6 | Multi-stage approval routing (Department Head → Budget Controller → Finance) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PR_AUTH_001–005](/en/inventory/purchase-request/02-business-rules) |
| 7 | Approve at intermediate stage | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_004](/en/inventory/purchase-request/02-business-rules) |
| 8 | Final-stage approve (in_progress → approved) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_005](/en/inventory/purchase-request/02-business-rules) |
| 9 | Reject PR (header-level, terminates chain, releases soft-commit) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_006](/en/inventory/purchase-request/02-business-rules) |
| 10 | Send-back / return PR to requestor | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_003](/en/inventory/purchase-request/02-business-rules) |
| 11 | Split-reject (accept some lines, reject others) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PR_AUTH_003](/en/inventory/purchase-request/02-business-rules) |
| 12 | Approve with quantity adjustment (approved_qty < requested_qty) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PR_VAL_013](/en/inventory/purchase-request/02-business-rules) |
| 13 | Delegate approval authority | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 PR_AUTH_006](/en/inventory/purchase-request/02-business-rules) |
| 14 | Threshold-based escalation to Procurement Manager | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PR_AUTH_005](/en/inventory/purchase-request/02-business-rules) |
| 15 | Cancel / void / delete draft PR (requestor-initiated before submit; delete re-verified 2026-09-22) | ✅ | ✅ | ✅ | ✅ Done | [UF — Requestor §3](/en/inventory/purchase-request/03-user-flow-requestor) |
| 16 | Admin void (Finance / sys-admin, any post-submit stage) (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PR_AUTH_007](/en/inventory/purchase-request/02-business-rules) |
| 17 | Resubmit / amend after send-back | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_003](/en/inventory/purchase-request/02-business-rules) |
| 18 | Convert PR → PO (full conversion) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_007](/en/inventory/purchase-request/02-business-rules) |
| 19 | Convert PR → PO (partial conversion) | ✅ | ✅ | ✅ | ✅ Done | [UF — Purchaser §3](/en/inventory/purchase-request/03-user-flow-purchaser) |
| 20 | Multi-PR consolidation into one PO (same vendor + currency) | 🟡 | ✅ | ✅ | 🟡 Partial | [BR §6 cross-module rules](/en/inventory/purchase-request/02-business-rules) |
| 21 | Vendor allocation / Allocate Vendor dialog | ✅ | ✅ | ✅ | ✅ Done | [UF — Purchaser §2](/en/inventory/purchase-request/03-user-flow-purchaser) |
| 22 | Pricelist deviation check at conversion | 🟡 | ✅ | ✅ | 🟡 Partial | [UF — Purchaser §3](/en/inventory/purchase-request/03-user-flow-purchaser) |
| 23 | Financial calculations (subtotal / discount / tax / base-currency roll-up) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 PR_CALC_001–008](/en/inventory/purchase-request/02-business-rules) |
| 24 | Multi-currency / FX rate snapshot | ✅ | ✅ | ✅ | ✅ Done | [BR §3 PR_CALC_006](/en/inventory/purchase-request/02-business-rules) |
| 25 | Status lifecycle (draft → in_progress → approved → completed / voided) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PR_POST_001–007](/en/inventory/purchase-request/02-business-rules) |
| 26 | Pre-flight verify endpoint (dry-run validation before submit) | ✅ | ✅ | ✅ | ✅ Done | [BR §2](/en/inventory/purchase-request/02-business-rules) |
| 27 | My Approval queue — unified `GET /api/my-pending` backed by view `sys_v_my_pending` | ✅ | ✅ | ✅ | ✅ Done | [my-approval](/en/inventory/purchase-request/my-approval) |
| 28 | Stage-hidden prices — a workflow stage can hide `price_per_unit` / `total_price` from its actors (`PR_AUTH_011`, `hidden_fields`; 2026-10) — no TS scenario | ✅ | ✅ | ⬜ | 🟡 Partial | [BR §4 PR_AUTH_011](/en/inventory/purchase-request/02-business-rules) |
| 29 | Stage action switches — approve / reject / send back switched off per stage (`PR_AUTH_010`; 2026-10) — no TS scenario | ✅ | ✅ | ⬜ | 🟡 Partial | [BR §4 PR_AUTH_010](/en/inventory/purchase-request/02-business-rules) |
| 30 | Row visibility — `view` / `view_department` / `view_all` scope on list and detail, participant read on detail (`PR_AUTH_009`) — UF mention only, no TS scenario | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §4 PR_AUTH_009](/en/inventory/purchase-request/02-business-rules) |
| 31 | Ask AI menu on the item grid (providers + prompt from the BU `ask_ai` config; price omitted when the stage hides it) — described on the module page and System Config only; no BR rule, no TS | ⬜ | 🟡 | ⬜ | 🟡 Partial | [purchase-request](/en/inventory/purchase-request) · [system-config/ask-ai](/en/inventory/system-config/ask-ai) |
| 32 | MCP read tools `get_purchase_requests` / `get_purchase_request` (scope `read:procurement`, same row visibility) — one table row on the module page only | 🟡 | ⬜ | ⬜ | 🟡 Partial | [purchase-request](/en/inventory/purchase-request) |
| 33 | Comment attachment policy — per-BU allowed types / size (`attachment.allowed_types`, `attachment.max_size_mb`), delta edit — data-model page + UF line; no BR rule, no TS | 🟡 | ✅ | ⬜ | 🟡 Partial | [01a §4](/en/inventory/purchase-request/01a-data-model-comments) |
| 34 | My Approval — Sent-back filter chip and per-stage hidden amounts (`hidden_fields`) | ✅ | ✅ | ✅ | ✅ Done | [my-approval](/en/inventory/purchase-request/my-approval) |

### 3. Purchase Order
Source: `../carmen/docs/purchase-order-management/`

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create PO — manual blank (no PR linkage) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PO_AUTH_001](/en/inventory/purchase-order/02-business-rules) |
| 2 | Create PO from PR (vendor+currency grouping, bridge table written) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 PO_XMOD_001–002](/en/inventory/purchase-order/02-business-rules) |
| 3 | Multi-PR consolidation into one PO (same vendor + currency) | ✅ | ✅ | ✅ | ✅ Done | [UF — Purchaser §2](/en/inventory/purchase-order/03-user-flow-purchaser) |
| 4 | Partial PR conversion (selected lines / qty only) | ✅ | ✅ | ✅ | ✅ Done | [UF — Purchaser §3](/en/inventory/purchase-order/03-user-flow-purchaser) |
| 5 | Financial calculations (subtotal / discount / FOC / tax / base-currency roll-up) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 PO_CALC_001–012](/en/inventory/purchase-order/02-business-rules) |
| 6 | Multi-currency / FX rate snapshot | ✅ | ✅ | ✅ | ✅ Done | [BR §3 PO_CALC_006](/en/inventory/purchase-order/02-business-rules) |
| 7 | Submit PO for approval (draft → in_progress) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_002](/en/inventory/purchase-order/02-business-rules) |
| 8 | High-value approval gate (in_progress, FC Procurement Manager) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PO_AUTH_004](/en/inventory/purchase-order/02-business-rules) |
| 9 | Send-back / return to buyer during approval (in_progress → draft) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_005](/en/inventory/purchase-order/02-business-rules) |
| 10 | Reject PO at approval stage (in_progress → voided) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_010](/en/inventory/purchase-order/02-business-rules) |
| 11 | Final approval (lands on `approved`) + send to vendor (`send-email` / `mark-sent` → status `sent_or_print`) — re-verified 2026-09-22 | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_004](/en/inventory/purchase-order/02-business-rules) |
| 12 | Vendor acknowledgement (recorded by Purchaser as comment — no status change) | ✅ | ✅ | ✅ | ✅ Done | [UF — Vendor §2](/en/inventory/purchase-order/03-user-flow-vendor) |
| 13 | Pricelist price snapshot and deviation check at PR-to-PO conversion | ✅ | ✅ | ✅ | ✅ Done | [BR §6 PO_XMOD_005–006](/en/inventory/purchase-order/02-business-rules) |
| 14 | Post-sent amendment (cancelled_qty + per-line note only — PO_VAL_016) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PO_VAL_016](/en/inventory/purchase-order/02-business-rules) |
| 15 | Partial receipt via GRN (sent → partial, line received_qty update) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_006](/en/inventory/purchase-order/02-business-rules) |
| 16 | Full receipt via GRN (sent/partial → completed) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_007](/en/inventory/purchase-order/02-business-rules) |
| 17 | Early-close partial PO (partial → closed, remainder written to cancelled_qty) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_011](/en/inventory/purchase-order/02-business-rules) |
| 18 | Void PO from any non-terminal state (Manager override, PO_AUTH_007) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PO_AUTH_007](/en/inventory/purchase-order/02-business-rules) |
| 19 | Soft-delete draft PO (Manager-only, PO_AUTH_005) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PO_AUTH_005](/en/inventory/purchase-order/02-business-rules) |
| 20 | Three-way match (PO ↔ GRN ↔ invoice) success → AP liability posted | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_008](/en/inventory/purchase-order/02-business-rules) |
| 21 | Three-way match failure (qty / price discrepancy → invoice held in dispute) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_009](/en/inventory/purchase-order/02-business-rules) |
| 22 | Credit note (post-receipt quantity return or amount discount against GRN) | 🟡 | 🟡 | ⬜ | 🟡 Partial | [credit-note.md](/en/inventory/purchase-order/credit-note) |
| 23 | Segregation of duties (PO buyer ≠ GRN poster, PO_AUTH_010) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PO_AUTH_010](/en/inventory/purchase-order/02-business-rules) |
| 24 | Status lifecycle (draft → in_progress → sent → partial → completed / closed / voided; opt-in E2E `404-po-doc-flow`, 5 cases, 2026-10-27) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 + §5.1 status mapping](/en/inventory/purchase-order/02-business-rules) |
| 25 | Verify dry-run endpoint (pre-submit validation without side effects) | ✅ | ✅ | ✅ | ✅ Done | [BR §2](/en/inventory/purchase-order/02-business-rules) |
| 26 | Swipe approve (mobile-style approve gesture on the approval list) | ✅ | ✅ | ✅ | ✅ Done | [BR §4](/en/inventory/purchase-order/02-business-rules) |
| 27 | Credit note approval workflow — none: `draft → completed` on submit (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [credit-note.md](/en/inventory/purchase-order/credit-note) |
| 28 | Credit note void — no void route (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [credit-note.md](/en/inventory/purchase-order/credit-note) |
| 29 | Credit note stock-movement tab (ledger rows written by the CN) | ✅ | ✅ | ✅ | ✅ Done | [credit-note.md](/en/inventory/purchase-order/credit-note) |
| 30 | Stage-hidden prices (`PO_AUTH_013`: stage `hide_fields`, masked on list and detail; 2026-10) — no TS scenario | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §4 PO_AUTH_013](/en/inventory/purchase-order/02-business-rules) |
| 31 | Stage action switches (`PO_AUTH_014`: `WORKFLOW_STAGE_ACTION_DISABLED` 422 on approve / reject / send back) — no TS scenario | ✅ | 🟡 | ⬜ | 🟡 Partial | [BR §4 PO_AUTH_014](/en/inventory/purchase-order/02-business-rules) |
| 32 | PO list layout — PO type under the number, send-back badge with lazy reasons — module page only, no BR / TS | ⬜ | 🟡 | ⬜ | 🟡 Partial | [purchase-order](/en/inventory/purchase-order) |
| 33 | Credit note period gate — `cn_date` must be in the current inventory period at create and at submit (`CREDIT_NOTE_DATE_NOT_CURRENT_PERIOD`, `CREDIT_NOTE_NO_OPEN_PERIOD`) | ✅ | ✅ | ✅ | ✅ Done | [credit-note.md §3](/en/inventory/purchase-order/credit-note) |
| 34 | Credit note stock-cover check — `quantity_return` must be covered by on-hand on the CN date (`CREDIT_NOTE_INSUFFICIENT_STOCK`; direct-type locations book a cost variance instead) | ✅ | ✅ | ✅ | ✅ Done | [credit-note.md §3, §4](/en/inventory/purchase-order/credit-note) |
| 35 | Credit note draft-only edit / delete (`CREDIT_NOTE_ONLY_DRAFT_EDITABLE`, `CREDIT_NOTE_ONLY_DRAFT_DELETABLE`) | ✅ | ✅ | ✅ | ✅ Done | [credit-note.md §2, §3](/en/inventory/purchase-order/credit-note) |
| 36 | Credit note server-derived `return_base_qty` and `base_*` amounts (`calcCreditNoteBaseAmounts`; client values replaced); E2E `603-cn-doc-flow` | ✅ | ✅ | ✅ | ✅ Done | [credit-note.md §4, §5](/en/inventory/purchase-order/credit-note) |

### 4. Store Requisition
Source: `../carmen/docs/store-requisitions/`

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create SR — manual blank (header + lines, `sr_type` pick, location pair) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SR_AUTH_001–002](/en/inventory/store-requisition/02-business-rules) |
| 2 | Auto-create SR from recipe demand (`info.recipe_id` back-reference) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §6 SR_XMOD_006](/en/inventory/store-requisition/02-business-rules) |
| 3 | Submit SR (`draft → in_progress`, source-availability check SR_VAL_009) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SR_AUTH_003](/en/inventory/store-requisition/02-business-rules) |
| 4 | Multi-stage approval routing (workflow stage advance, per-line `user_action.execute`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 SR_XMOD_008](/en/inventory/store-requisition/02-business-rules) |
| 5 | Approve SR lines in full (`approved_qty = requested_qty`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SR_AUTH_005](/en/inventory/store-requisition/02-business-rules) |
| 6 | Trim `approved_qty` below `requested_qty` (partial-approval per line) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SR_VAL_010](/en/inventory/store-requisition/02-business-rules) |
| 7 | Reject SR lines (mandatory `reject_message`, SR_VAL_010 second clause) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_004](/en/inventory/store-requisition/02-business-rules) |
| 8 | Send back for correction (Approver → Requester stage, `review_message`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_004](/en/inventory/store-requisition/02-business-rules) |
| 9 | Split-reject (mixed per-line outcomes — some approved, some rejected, SR_AUTH_006) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SR_AUTH_006](/en/inventory/store-requisition/02-business-rules) |
| 10 | Approval delegation (deputy acts via `tb_workflow` config) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 SR_XMOD_008](/en/inventory/store-requisition/02-business-rules) |
| 11 | Fulfil / issue stock — `sr_type = issue` (OUT at source, expense Dr at cost-centre) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_006–007](/en/inventory/store-requisition/02-business-rules) |
| 12 | Fulfil / stock transfer — `sr_type = transfer` (paired OUT + IN, destination on-hand increment) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_006–007](/en/inventory/store-requisition/02-business-rules) |
| 13 | Partial fulfilment — at-issue stock-out short-fulfilment (`SR_VAL_013`, `SR_POST_012`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_012](/en/inventory/store-requisition/02-business-rules) |
| 14 | Lot-controlled item pick (multi-lot selection, `SR_VAL_012`, `SR_XMOD_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 SR_XMOD_002](/en/inventory/store-requisition/02-business-rules) |
| 15 | Commit SR (`in_progress → completed` — the single posting event, inventory tx + GL) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_005](/en/inventory/store-requisition/02-business-rules) |
| 16 | Receiver acknowledgement (post-commit, no `doc_status` change, `SR_POST_013`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SR_AUTH_008](/en/inventory/store-requisition/02-business-rules) |
| 17 | Receiver discrepancy flag (post-commit; resolution via inventory-adjustment) | ✅ | ✅ | ✅ | ✅ Done | [TS — Receiver](/en/inventory/store-requisition/04-test-scenarios-receiver) |
| 18 | Stock replenishment (on-hand scoped to the active period since 2026-10-27; real API — Inventory Controller reviews generated SR draft; auto-generating cron still absent, re-verified 2026-09-22) | ✅ | ✅ | ✅ | ✅ Done | [stock-replenishment.md](/en/inventory/store-requisition/stock-replenishment) |
| 19 | Cancel SR (requester withdrawal / all-lines-rejected automatic, `SR_POST_009`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_009](/en/inventory/store-requisition/02-business-rules) |
| 20 | Void SR (admin — Inventory Controller / Sysadmin, pre-commit only, `SR_POST_010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_010](/en/inventory/store-requisition/02-business-rules) |
| 21 | Segregation of duties (Requester ≠ Approver `SR_AUTH_011`; Approver ≠ Fulfiller `SR_AUTH_012`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SR_AUTH_011–012](/en/inventory/store-requisition/02-business-rules) |
| 22 | Active-period date gate on submit and issue (`SR_VAL_014`; reference is the **active** period = oldest `open` / `locked`, reworked 2026-10-27; `sr-date.helper`; Finance reopen or admin void) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SR_VAL_014](/en/inventory/store-requisition/02-business-rules) |
| 23 | Journal entry generation and GL posting (Dr/Cr per `sr_type` and cost-centre dimension) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 SR_POST_007](/en/inventory/store-requisition/02-business-rules) |
| 24 | Source costing-method feed (FIFO / moving-average cost-per-unit at issue, `SR_CALC_004`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §3 SR_CALC_004](/en/inventory/store-requisition/02-business-rules) |
| 25 | Status lifecycle (`draft → in_progress → completed / cancelled / voided` + §5.1 UI-vs-BRD mapping) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 + §5.1](/en/inventory/store-requisition/02-business-rules) |
| 26 | Three-quantity invariant `0 ≤ issued_qty ≤ approved_qty ≤ requested_qty` (`SR_CALC_001` / `SR_VAL_008`) — not enforced (design) (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SR_VAL_008; §3 SR_CALC_001](/en/inventory/store-requisition/02-business-rules) |
| 27 | Stage action switches (`SR_AUTH_015`: approve / reject / send back switched off per stage; footer hides the button) — no TS scenario | ✅ | ✅ | ⬜ | 🟡 Partial | [BR §4 SR_AUTH_015](/en/inventory/store-requisition/02-business-rules) |
| 28 | Issue-stage guards — `issued_qty ≤ approved_qty` (`SR_VAL_008`), nothing-issued refusal (`SR_VAL_011`), pre-write source-stock check and posting in the completion transaction (`SR_VAL_013`; pre-write finding closed 2026-10-27) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SR_VAL_008/011/013; TS-Fulfiller FUL-VAL-01/03/05](/en/inventory/store-requisition/02-business-rules) |
| 29 | Comment attachment policy — per-BU allowed types / size on SR comments — data-model page only; no BR rule, no TS | 🟡 | 🟡 | ⬜ | 🟡 Partial | [01a §3a](/en/inventory/store-requisition/01a-data-model-comments) |

### 5. Inventory Adjustment
Source: `../carmen/docs/inventory-adjustment/`

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create adjustment document — `tb_stock_in` (IN) or `tb_stock_out` (OUT) at `draft` (auto-number, location, department, description) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 ADJ_VAL_001–005](/en/inventory/inventory-adjustment/02-business-rules) |
| 2 | Reason-code selection and direction validation (reason `type` must match document direction; `ADJ_VAL_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 ADJ_VAL_002](/en/inventory/inventory-adjustment/02-business-rules) |
| 3 | Lot-level entry — existing lot on stock-in or stock-out; new-lot creation on stock-in (`ADJ_VAL_009`, `ADJ_AUTH_003`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 ADJ_VAL_009 / §4 ADJ_AUTH_003](/en/inventory/inventory-adjustment/02-business-rules) |
| 4 | Submit auto-approve (below-threshold existing-lot → `draft → completed` fast path, `ADJ_POST_001` / `ADJ_AUTH_002`) | ✅ | ✅ | ✅ | ✅ Done | [UF §2.2](/en/inventory/inventory-adjustment/03-user-flow) |
| 5 | Threshold-based approval routing (Store Keeper → Inventory Controller → Finance, `ADJ_AUTH_004` / `ADJ_AUTH_005`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 ADJ_AUTH_004–005](/en/inventory/inventory-adjustment/02-business-rules) |
| 6 | Wastage / write-off categorisation and GL-account mapping per reason code (`ADJ_XMOD_007`; wastage-reporting variant — real API, re-verified 2026-09-22; write-off `so_date` must lie in the **active** period since 2026-10-27) | ✅ | ✅ | ✅ | ✅ Done | [wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting) |
| 7 | Posting — inventory transaction + FIFO or weighted-average cost-layer write (`ADJ_POST_002`, `ADJ_CALC_005`–`007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 ADJ_POST_002](/en/inventory/inventory-adjustment/02-business-rules) |
| 8 | GL journal entry generation (Dr/Cr per reason-code `info.glAccount` and `dimension.department`, `ADJ_XMOD_007`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §6 ADJ_XMOD_007](/en/inventory/inventory-adjustment/02-business-rules) |
| 9 | Physical-count / spot-check variance rollup — auto-create and auto-post `tb_stock_in` / `tb_stock_out` (`ADJ_POST_006`, `ADJ_XMOD_002/003`) | ✅ | ✅ | ✅ | ✅ Done | [TS cross-persona #5–6](/en/inventory/inventory-adjustment/04-test-scenarios) |
| 10 | Void via compensating reversal (post-fact correction — two-step, `ADJ_POST_004`; original transaction not edited) — void real in UI (draft → save → commit → void), re-verified 2026-09-22 | ✅ | ✅ | ✅ | ✅ Done | [BR §5 ADJ_POST_004](/en/inventory/inventory-adjustment/02-business-rules) |
| 11 | Cancel pre-post (`draft / in_progress → cancelled`, `ADJ_POST_003`; no inventory effect; terminal) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 ADJ_POST_003](/en/inventory/inventory-adjustment/02-business-rules) |
| 12 | Segregation of duties (adjuster ≠ originating receiver above SoD threshold, `ADJ_AUTH_010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 ADJ_AUTH_010](/en/inventory/inventory-adjustment/02-business-rules) |
| 13 | Period-containment gate (closed / locked period rejection, `ADJ_VAL_011` / `INV_VAL_008`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 ADJ_VAL_011](/en/inventory/inventory-adjustment/02-business-rules) |
| 14 | Consignment-location adjustment (memo-only inbound; COGS + AP deferred to consumption, `ADJ_POST_008`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 ADJ_POST_008](/en/inventory/inventory-adjustment/02-business-rules) |
| 15 | Reason-code / adjustment-type configuration (Sysadmin CRUD, GL mapping, `requiresDocument` / `requiresQualityCheck` flags, thresholds, `ADJ_AUTH_008`) | ✅ | ✅ | ✅ | ✅ Done | [TS Audit/Config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config) |
| 16 | Status lifecycle (`draft → in_progress → completed → cancelled / voided` + §5.1 live-UI vs BRD mapping) — draft → save → commit → void re-verified 2026-09-22 | ✅ | ✅ | ✅ | ✅ Done | [BR §5 + §5.1](/en/inventory/inventory-adjustment/02-business-rules) |
| 17 | Dated stock-out availability pre-check — requested qty ≤ drawable qty as of `so_date` in the active period (`ADJ_VAL_010`, `getDrawableQtyAsOf`) — E2E gap noted, no dedicated TS scenario | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 ADJ_VAL_010](/en/inventory/inventory-adjustment/02-business-rules) |
| 18 | FIFO receipt-order guard on stock-in — date earlier than the latest posted receipt refused (`STOCK_IN_DATE_BEFORE_LATEST_RECEIPT`, `ADJ_VAL_003`) — no TS scenario (gap noted) | ✅ | 🟡 | 🟡 | 🟡 Partial | [BR §2 ADJ_VAL_003](/en/inventory/inventory-adjustment/02-business-rules) |
| 19 | Void guard for a `SALE` stock-out created by Sales Consumption (`STOCK_OUT_VOID_VIA_SALES_CONSUMPTION`, `ADJ_VAL_012`) — void the Sales Consumption instead; no TS scenario | ✅ | ✅ | ⬜ | 🟡 Partial | [BR §2 ADJ_VAL_012](/en/inventory/inventory-adjustment/02-business-rules) · [recipe/sales-consumption §7](/en/inventory/recipe/sales-consumption) |

### 6. Costing
Source: `../carmen/docs/costing/` · Wiki: `en/inventory/costing/`

> **Note:** Costing is an engine/concept module — it has no document lifecycle of its own. Every sub-process is triggered by an upstream inventory transaction post or a period-end run. BR coverage is via `02-business-rules.md` rule families `COST_VAL_*` / `COST_CALC_*` / `COST_AUTH_*` / `COST_POST_*` / `COST_XMOD_*`. UF coverage is across the three role-specific flow pages (Finance, Controller, Auditor). TS coverage is across `04-test-scenarios.md` (cross-persona) and the three role-specific scenario pages.

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | FIFO inbound — new lot creation (`lot_no`, `lot_index`, `lot_seq_no` assignment) on every inbound at a FIFO business unit (`COST_CALC_004`, `COST_POST_001`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 COST_CALC_004](/en/inventory/costing/02-business-rules) |
| 2 | FIFO outbound — oldest-lot-first cost pick; single or multi-lot spanning consumption (`COST_CALC_001`, `COST_POST_002`; `COST_VAL_002` guards no-layer case) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #1; IC-HP-01](/en/inventory/costing/04-test-scenarios) |
| 3 | Weighted Average inbound — running average recompute on every inbound (`COST_CALC_003`, `COST_POST_001`; `COST_VAL_005` guards inputs) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #2; calc-methods §3](/en/inventory/costing/calculation-methods) |
| 4 | Weighted Average outbound — cost pick at current running average; average not updated on issue (`COST_CALC_002`, `COST_POST_002`; `COST_VAL_003` guards no-average case) | ✅ | ✅ | ✅ | ✅ Done | [IC-HP-02; BR §3 COST_CALC_002](/en/inventory/costing/04-test-scenarios-inventory-controller) |
| 5 | Credit-note-amount revaluation — post-receipt lot cost rebase via `diff_amount`; downstream FIFO picks revalued cost; already-consumed portions not retroactively adjusted (`COST_CALC_005`, `COST_POST_003`; `COST_VAL_006`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #3; FIN-HP-01](/en/inventory/costing/04-test-scenarios) |
| 6 | Credit-note-quantity reversal — outbound bound to originating GRN lot at that lot's `cost_per_unit` (not a free FIFO pick) (`COST_POST_004`) | ✅ | 🟡 | 🟡 | 🟡 Partial | [BR §5 COST_POST_004](/en/inventory/costing/02-business-rules) |
| 7 | Count-variance valuation — overage priced by the BU `si.cost-from` setting (`standard` / `last_cost` / `last_receiving` / `average`; old `enum_physical_count_costing_method` no longer read), shortage at posted lot / average cost (re-verified 2026-10-27) (`COST_CALC_008`, `COST_POST_009`; `COST_VAL_007`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #4; BR §3 COST_CALC_008](/en/inventory/costing/04-test-scenarios) |
| 8 | Period close — `tb_period_snapshot` rows written with `closing_qty / closing_cost_per_unit / closing_total_cost`; cost locked for the period (`COST_CALC_006`, `COST_POST_007`; `COST_VAL_008`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #5–6; FIN-HP-04–05](/en/inventory/costing/04-test-scenarios) |
| 9 | Period open — rollforward carries per-lot `cost_per_unit` (FIFO `lot_seq_no` preserved) or single WA anchor row into next period (`COST_CALC_007`, `COST_POST_008`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #5–6; FIN-HP-04–05](/en/inventory/costing/04-test-scenarios) |
| 10 | Costing method configuration — BU-level FIFO↔WA; blocked on non-zero on-hand (`COST_VAL_009`); change after drain happy path (`COST_AUTH_001`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #7–8; FIN-HP-09](/en/inventory/costing/04-test-scenarios) |
| 11 | Standard-cost management — `tb_product.standard_cost` update; prospective only, no cost-layer effect (`COST_CALC_009`, `COST_POST_010`; `COST_AUTH_003`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #9; FIN-HP-08](/en/inventory/costing/04-test-scenarios) |
| 12 | Direct-cost location receipt — engine skipped, no cost-layer row written; GL expensed at receipt (`COST_VAL_011`, `COST_POST_005`) | ✅ | 🟡 | ✅ | 🟡 Partial | [cross-persona TS #17; BR §5 COST_POST_005](/en/inventory/costing/04-test-scenarios) |
| 13 | Consignment location receipt — memo cost-layer row flagged; AP and Inventory journal deferred to consumption (`COST_VAL_012`, `COST_POST_006`) | ✅ | 🟡 | ✅ | 🟡 Partial | [cross-persona TS #18; BR §5 COST_POST_006](/en/inventory/costing/04-test-scenarios) |
| 14 | Extra-cost allocation into landed cost — `by_qty` / `by_value` / `manual`, `cost_layer.extra_cost_amount` (`COST_CALC_011`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 COST_CALC_011](/en/inventory/costing/02-business-rules) |
| 15 | GL posting from the costing engine — Not applicable: GL module exists (2026-09) but is unwired to inventory (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [calculation-methods](/en/inventory/costing/calculation-methods) · [gl-posting](/en/inventory/general-ledger/gl-posting) |
| 16 | Cost read endpoints — last cost, last receiving by unit, on-hand / on-order with `last_price` | ✅ | ✅ | ✅ | ✅ Done | [BR §3](/en/inventory/costing/02-business-rules) |
| 17 | `average_per_location` method — per-(product, location) moving average on inbound / outbound post and at period close (`processAveragePerLocationClose`; 2026-09-28) | ✅ | ✅ | ✅ | ✅ Done | [BR `COST_VAL_001`; cross-persona TS #15](/en/inventory/costing/02-business-rules) |
| 18 | FIFO draws lots in commit order (transaction clock), not document date; lot number never reused after a void | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #16, #17](/en/inventory/costing/04-test-scenarios) |
| 19 | Average stamped on the active period's layers only (not prior periods) — TS scenarios assert the stamp only for close | ✅ | ✅ | 🟡 | 🟡 Partial | [BR header note](/en/inventory/costing/02-business-rules) · [UF](/en/inventory/costing/03-user-flow) |
| 20 | Stock-in default-cost endpoint (`…/location/:location_id/stock-in`, `si.cost-from`) and cost-estimate `at_date` — module page only, no BR rule or TS | 🟡 | 🟡 | ⬜ | 🟡 Partial | [costing](/en/inventory/costing) |

### 7. Inventory
Source: `../carmen/docs/inventory-management/`

> **Note:** Inventory is the stock-ledger / on-hand engine module — it has no document lifecycle of its own. Every sub-process is either a movement posted via an upstream source module (GRN, SR, adjustment, count, credit note) or a period-level lifecycle action. BR coverage is via `02-business-rules.md` rule families `INV_VAL_*` / `INV_CALC_*` / `INV_AUTH_*` / `INV_POST_*` / `INV_XMOD_*`. UF coverage is across the four role-specific flow pages (Store Keeper, Inventory Controller, Finance, Audit/Config) plus the overview `03-user-flow.md`. TS coverage is across `04-test-scenarios.md` (cross-persona scenarios) and the four role-specific scenario pages. Two non-`02-business-rules` reference pages exist: `transaction.md` (ledger view / edge-cases) and `period-end.md` (close ceremony).

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Inbound post to inventory-type location — cost-layer insert (`INV_POST_001`; GRN / transfer-in / adjustment-in) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_001](/en/inventory/inventory/02-business-rules) |
| 2 | Outbound post from inventory-type location — FIFO / WA cost pick (`INV_POST_002`; issue / transfer-out / adjustment-out) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_002; cross-persona TS #7](/en/inventory/inventory/04-test-scenarios) |
| 3 | Derived on-hand calculation (no `tb_stock_balance` row — `INV_CALC_004` sum from cost-layer since last snapshot) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 INV_CALC_004; SK-HP-01](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 4 | FIFO outbound spanning multiple lots (oldest-lot-first, `INV_CALC_005`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 INV_CALC_005; cross-persona TS #7](/en/inventory/inventory/04-test-scenarios) |
| 5 | Weighted-average inbound recompute (`INV_CALC_007` new average on every inbound) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 INV_CALC_007; cross-persona TS #8](/en/inventory/inventory/04-test-scenarios) |
| 6 | No-negative-balance guard (`INV_VAL_005`) — reject outbound exceeding on-hand | ✅ | ✅ | ✅ | ✅ Done | [BR §2 INV_VAL_005; cross-persona TS #10; SK-VAL-04](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 7 | Lot identity validation — new-lot uniqueness / existing-lot availability (`INV_VAL_006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 INV_VAL_006; SK-VAL-05](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 8 | Period-lock guard — reject post into closed / locked period (`INV_VAL_008`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 INV_VAL_008; cross-persona TS #11; SK-VAL-07](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 9 | Direct-cost location receipt — no cost-layer row, immediate expense GL (`INV_POST_003`, `INV_VAL_009`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 §5 INV_POST_003; cross-persona TS #14](/en/inventory/inventory/04-test-scenarios) |
| 10 | Consignment location receipt (memo cost-layer, no AP / Inventory debit at receipt — `INV_POST_004`, `INV_VAL_010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_004; cross-persona TS #15](/en/inventory/inventory/04-test-scenarios) |
| 11 | Consignment consumption (simultaneous COGS + AP post at issue — `INV_POST_005`) | ✅ | 🟡 | 🟡 | 🟡 Partial | [BR §5 INV_POST_005](/en/inventory/inventory/02-business-rules) |
| 12 | Inter-location transfer (paired transfer-out + transfer-in cost-layer rows — `INV_POST_006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_006; cross-persona TS #1 / #7](/en/inventory/inventory/04-test-scenarios) |
| 13 | Credit-note amount adjustment — lot cost rebase, `diff_amount` (`INV_POST_007`, `INV_CALC_011`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_007; cross-persona TS #12](/en/inventory/inventory/04-test-scenarios) |
| 14 | Credit-note quantity reversal — outbound from originating GRN lot (`INV_POST_008`) | ✅ | 🟡 | 🟡 | 🟡 Partial | [BR §5 INV_POST_008](/en/inventory/inventory/02-business-rules) |
| 15 | Compensating reversal — new opposite-sign transaction; original marked `deleted_at` (`INV_POST_012`, `INV_VAL_013`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_012; SK-PERM-03; IC-PERM-06](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 16 | Below-threshold stock-in / stock-out auto-approve (Store Keeper auto-post path — `INV_AUTH_001`, `INV_AUTH_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_001–002; SK-HP-01–02; cross-persona TS #1](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 17 | Above-threshold approval routing: Store Keeper → Inventory Controller (`INV_AUTH_003`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_003; IC-HP-01; cross-persona TS #2](/en/inventory/inventory/04-test-scenarios-inventory-controller) |
| 18 | Above-Finance-threshold routing: Inventory Controller → Finance (`INV_AUTH_005`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_005; FIN-HP-01; cross-persona TS #3](/en/inventory/inventory/04-test-scenarios-finance) |
| 19 | New-lot stock-in always routes for Controller approval (regardless of cost — new-lot rule) | ✅ | ✅ | ✅ | ✅ Done | [SK-HP-03; IC-HP-03](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 20 | Segregation of duties — write-off of a lot by the user who received it (`INV_AUTH_010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_010; SK-PERM-06](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 21 | Stock-policy maintenance (min / max / par / reorder on `tb_product_location` — `INV_AUTH_004`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_004; IC-HP-06; IC-VAL-05](/en/inventory/inventory/04-test-scenarios-inventory-controller) |
| 22 | Count-variance rollup post (physical / spot count variance → auto-staged stock-in / stock-out — `INV_XMOD_003/004`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 INV_XMOD_003–004; IC-HP-04; cross-persona TS #4](/en/inventory/inventory/04-test-scenarios-inventory-controller) |
| 23 | Inventory-to-GL reconciliation (sub-ledger sum vs GL Inventory control account — `INV_XMOD_008`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 INV_XMOD_008; FIN-HP-02–03; FIN-VAL-02](/en/inventory/inventory/04-test-scenarios-finance) |
| 24 | Period close (snapshot write, cost-layer close rows, `tb_period.status open → closed` — `INV_POST_009`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_009; FIN-HP-04; cross-persona TS #5](/en/inventory/inventory/04-test-scenarios-finance) |
| 25 | Period open / rollforward (next-period opening rows, FIFO `lot_seq_no` preserved — `INV_POST_010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_010; FIN-HP-04; period-end.md §6](/en/inventory/inventory/period-end) |
| 26 | Period lock (`closed → locked` — terminal; Finance Manager only — `INV_POST_011`, `INV_AUTH_006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 INV_POST_011; FIN-HP-06; IC-PERM-05](/en/inventory/inventory/04-test-scenarios-finance) |
| 27 | Period re-open within audit window (exceptional — audit-logged, Finance Manager only — `INV_AUTH_006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_006; FIN-HP-07; cross-persona TS #17](/en/inventory/inventory/04-test-scenarios-finance) |
| 28 | Period close blocked by prerequisite hold (start-counting gate `listStartCountingBlockers`; PR/PO no longer gate; period resolved from document date — re-verified 2026-09-22; opt-in E2E period-close specs 910–924) | ✅ | ✅ | ✅ | ✅ Done | [period-end.md §3; FIN-HP-05; FIN-VAL-03–04; cross-persona TS #6](/en/inventory/inventory/period-end) |
| 29 | Lot-recall chain-of-custody trace (backward GRN + forward consumption — Auditor read-only) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_009; AUD-HP-02; cross-persona TS #13](/en/inventory/inventory/04-test-scenarios-audit-config) |
| 30 | Period-snapshot reconciliation audit query (Auditor verifies ledger sum vs snapshot delta) | ✅ | ✅ | ✅ | ✅ Done | [AUD-HP-03; transaction.md §2](/en/inventory/inventory/04-test-scenarios-audit-config) |
| 31 | Location-type change blocked by non-zero on-hand (`INV_AUTH_008` drain requirement) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_008; AUD-VAL-01; cross-persona TS #16](/en/inventory/inventory/04-test-scenarios-audit-config) |
| 32 | Costing-method change blocked by non-zero on-hand (`INV_XMOD_009`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 INV_XMOD_009; AUD-HP-06; AUD-VAL-02](/en/inventory/inventory/04-test-scenarios-audit-config) |
| 33 | Concurrent inbound posts to same lot — append-only, no race condition (`INV_CALC_004`, `INV_CALC_007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 INV_CALC_004; cross-persona TS #9; SK-EDGE-03](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 34 | Multi-source channel convergence — all modules post via same `tb_inventory_transaction` API (`INV_XMOD_010`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §6 INV_XMOD_010; transaction.md §6](/en/inventory/inventory/transaction) |
| 35 | Inventory transaction log query / audit trail (read-only ledger view, balance derivation check) | ✅ | ✅ | ✅ | ✅ Done | [transaction.md §2–4; AUD-HP-01](/en/inventory/inventory/transaction) |
| 36 | Start counting round — `POST /period-ends/start-counting` (idempotent; opens `tb_physical_count_period`) | ✅ | ✅ | ✅ | ✅ Done | [period-end.md](/en/inventory/inventory/period-end) |
| 37 | Physical-count submit posts to the ledger — EOP-IN / EOP-OUT stock documents created `completed`, each line posted via `executeAdjustmentIn/Out` into the counted period (reverses the 2026-09-22 "never posts" gap; re-verified 2026-10-27) | ✅ | ✅ | ✅ | ✅ Done | [PC BR §5 PHC_POST_003](/en/inventory/physical-count/02-business-rules) · [cross-persona TS #2](/en/inventory/physical-count/04-test-scenarios) |
| 38 | Held receipts on average-costed BUs — GRNs / stock-ins dated in the next period are held and posted at the close — no TS scenario (gap noted) | 🟡 | ✅ | 🟡 | 🟡 Partial | [period-end.md](/en/inventory/inventory/period-end) |
| 39 | `average_per_location` period close (`processAveragePerLocationClose`, no restatement) — covered in period-end only; no TS scenario | ✅ | ✅ | ⬜ | 🟡 Partial | [period-end.md](/en/inventory/inventory/period-end) |
| 40 | Active-period rule — oldest `open` / `locked` period scopes on-hand, stock-out dating and stamping (`INV_VAL_008`, `buildOnHandPeriodWhere`); no dedicated TS scenario on the Inventory pages | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 INV_VAL_008](/en/inventory/inventory/02-business-rules) |

### 8. Product
Source: `../carmen/docs/product-management/`

> **Note:** Product is master-data — there is no document `doc_status` workflow, no posting event, and no period lock. The sub-processes below cover the CRUD + lifecycle surface owned by the Product Administrator, plus the read-side lookup / scan surface owned by Purchaser and Store Keeper. BR coverage is via `02-business-rules.md` rule families `PRD_VAL_*` / `PRD_CALC_*` / `PRD_AUTH_*` / `PRD_LIFE_*` / `PRD_XMOD_*`. UF coverage is across `03-user-flow.md` (lifecycle + persona index) and the three role-specific flow pages. TS coverage is across `04-test-scenarios.md` (cross-persona scenarios) and the three role-specific scenario pages (`product-admin`, `purchaser`, `store-keeper`). One additional reference page exists: `category.md` (taxonomy CRUD, attribute inheritance, edge-case matrix).

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create / edit product — single form (code, name, classification, base unit, flags, cost, deviation tolerances) | ✅ | ✅ | ✅ | ✅ Done | [BR §2–§3 PRD_VAL_001–007; PA-HP-01](/en/inventory/product/02-business-rules) |
| 2 | Product categorisation — 3-level hierarchy CRUD (category → sub-category → item-group, codes, cascade-default preview, delete guards) | ✅ | ✅ | ✅ | ✅ Done | [category.md](/en/inventory/product/category) |
| 3 | Unit management — create / edit units, in-use deletion guard (`PRD_VAL_017`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PRD_VAL_017; PA-HP-06; PA-VAL-15](/en/inventory/product/02-business-rules) |
| 4 | Unit conversions — define order-unit / ingredient-unit factors, bidirectional consistency, multi-hop resolution (`PRD_VAL_010/011`, `PRD_CALC_005/006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2–§3 PRD_VAL_010/011; PA-HP-02; PA-VAL-08/09; PA-EDGE-04/05](/en/inventory/product/02-business-rules) |
| 5 | Product lifecycle / status — active → inactive → discontinued → soft-delete → restore, with in-use guards (`PRD_LIFE_001–010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PRD_LIFE_*; UF §2 state table; PA-LIFE-01–13](/en/inventory/product/02-business-rules) |
| 6 | Product–location assignment — enable product at location, shelf assignment, set min / max / par / reorder policy (`PRD_VAL_012`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PRD_VAL_012; PA-HP-03; PA-VAL-10](/en/inventory/product/02-business-rules) |
| 7 | Vendor mapping — product–vendor join, vendor-product-code cross-reference (`PRD_VAL_013`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PRD_VAL_013; PA-HP-04; PA-VAL-11](/en/inventory/product/02-business-rules) |
| 8 | Barcode / SKU management — assign barcode, uniqueness guard, barcode-scan lookup by Store Keeper, mismatch comment flow | ✅ | ✅ | ✅ | ✅ Done | [TS — Store Keeper](/en/inventory/product/04-test-scenarios-store-keeper) |
| 9 | Bulk import / export — Not applicable: no importer exists (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PRD_LIFE_006/007; PA-HP-07/08; cross-persona TS #2/3](/en/inventory/product/02-business-rules) |
| 10 | Tax-profile and deviation-tolerance inheritance cascade — item-group → sub-category → category fallback (`PRD_CALC_002/003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §3 PRD_CALC_002/003; UF product-admin §2 step 5; PA-EDGE-02/03](/en/inventory/product/02-business-rules) |
| 11 | Standard-cost management and SoD approval gate — edit, above-threshold routing to Cost Controller / Finance, activity-log record (`PRD_AUTH_012`, `PRD_CALC_008`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PRD_AUTH_012; UF product-admin §3; PA-HP-09; cross-persona TS #4](/en/inventory/product/02-business-rules) |
| 12 | Audit trail / activity log — every product-master change logged (create, edit, status transition, soft-delete, restore, comment threads) (`PRD_XMOD_011`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 PRD_XMOD_011; cross-persona TS #15; PA-PERM-08/10](/en/inventory/product/04-test-scenarios) |
| 13 | Product category tree — overwrite-to-descendants confirm dialog, Inventory / Direct GL account defaults (inherit from level above), Product Category Report print / export | ✅ | ✅ | ✅ | ✅ Done | [category.md](/en/inventory/product/category) |

### 9. Recipe
Source: `../carmen/docs/recipe/` , `../carmen/docs/recipe-module/`

> **Note:** Recipe is a costed formula document (not a workflow document) — three-state lifecycle (`DRAFT → PUBLISHED → ARCHIVED`), RBAC-gated, with `tb_recipe_version` snapshots and `tb_recipe_pricing_history` as the audit trail. BR coverage is via `02-business-rules.md` rule families `REC_VAL_*` / `REC_CALC_*` / `REC_AUTH_*` / `REC_POST_*` / `REC_XMOD_*`. UF coverage is across `03-user-flow.md` (lifecycle state table + persona index) and five per-persona flow pages. TS coverage is across `04-test-scenarios.md` (14 cross-persona scenarios) and five per-persona scenario pages (`chef`, `cost-controller`, `outlet-manager`, `procurement-fb-ops`, `audit-config`). Four support-master pages exist: `category.md`, `cuisine.md`, `equipment.md`, `equipment-category.md`.

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create recipe (`DRAFT`) — required-field validation, code assignment, category/cuisine selection, yield & time, category defaults (partially applied: seed the target food-cost %) (`REC_VAL_001–008`, `REC_AUTH_001`, `REC_POST_001`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2–§5](/en/inventory/recipe/02-business-rules) |
| 2 | Ingredient line management — persisted via `PUT …/recipes/:id/ingredients` (2026-10), add product or sub-recipe lines, qty/unit/wastage, cost-per-unit, UoM conversion, discriminator integrity, cycle detection (`REC_VAL_009–014`, `REC_CALC_001–002`, `REC_AUTH_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2–§3](/en/inventory/recipe/02-business-rules) |
| 3 | Recipe costing roll-up — ingredient net cost → total ingredient cost → labor / overhead → cost per portion → suggested price → food-cost % → gross margin (`REC_CALC_001–015`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3](/en/inventory/recipe/02-business-rules) |
| 4 | Sub-recipe nesting — use a `PUBLISHED` recipe as ingredient, cost sourced from sub-recipe `cost_per_portion`, back-relation tracking, cycle guard (`REC_VAL_010–011`, `REC_CALC_011`, `REC_POST_006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2–§5; CHEF-HP-08; cross-persona TS #3,#12](/en/inventory/recipe/02-business-rules) |
| 5 | Publish recipe (`DRAFT → PUBLISHED`) — completeness gate (≥1 ingredient, ≥1 step, valid cost rollup, selling price > cost), optional Cost Controller co-approval for off-target margins, `tb_recipe_version` v1 + pricing-history snapshot (`REC_VAL_015–018`, `REC_AUTH_003/007`, `REC_POST_003`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§4,§5; CHEF-HP-03; cross-persona TS #1,#2](/en/inventory/recipe/02-business-rules) |
| 6 | Edit `PUBLISHED` recipe — in-place with versioning (new `tb_recipe_version` row) or un-publish round-trip; sub-recipe cost cascade fan-out to parent recipes; pricing-history row on cost/price change (`REC_AUTH_002/005`, `REC_POST_004/005/006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4–§5; CHEF-HP-04/05; cross-persona TS #4,#7,#8](/en/inventory/recipe/02-business-rules) |
| 7 | Yield variants — define alternate portions (e.g. Double Burger) with `conversion_rate`, stepped-quantity ingredient scoping, per-variant cost/price/margin, variant scaling rules (`REC_CALC_012`, `REC_VAL_007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2–§3; CHEF-HP-02; CHEF-EDGE-04/07; CC-EDGE-06](/en/inventory/recipe/02-business-rules) |
| 8 | Cost-only edit by Cost Controller — update `target_food_cost_percentage`, `selling_price`, `labor_cost_percentage`, `overhead_percentage`; recompute pricing rollup; write `tb_recipe_pricing_history` row (`REC_AUTH_006`, `REC_POST_010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4–§5; CC-HP-01/06](/en/inventory/recipe/02-business-rules) |
| 9 | Cost drift detection and cascade — ingredient cost change propagates through sub-recipe chain to parent recipes; costing-module event triggers re-cost; drift-tolerance flag surfaces out-of-range recipes (`REC_CALC_011`, `REC_XMOD_005–006`, `REC_POST_006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3,§5–§6; CC-HP-03; CC-EDGE-01/02; cross-persona TS #3,#13](/en/inventory/recipe/02-business-rules) |
| 10 | Archive recipe (`PUBLISHED → ARCHIVED`) — terminal state, final `tb_recipe_version` row, sever menu-item linkages, historical inventory ledger preserved; clone path to revive (`REC_AUTH_004`, `REC_POST_007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4–§5; CHEF-HP-06; cross-persona TS #9](/en/inventory/recipe/02-business-rules) |
| 11 | Theoretical consumption fan-out — `PUBLISHED` recipe drives theoretical OUT movements per ingredient on POS menu sale; sub-recipes recurse to leaf products; formula source for food-cost variance (`REC_CALC_014`, `REC_XMOD_003–004`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5–§6; cross-persona TS #1,#12](/en/inventory/recipe/02-business-rules) |
| 12 | Recipe-driven SR auto-create — recipe module computes ingredient demand × cover count and posts SR `draft` at outlet with `info.recipe_id` back-reference (`REC_XMOD_007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6; UF §4 cross-persona handoffs; cross-persona TS #6](/en/inventory/recipe/02-business-rules) |
| 13 | Preparation steps — editable in the form (add / edit / delete / reorder; UI since 2026-10), sequential steps (title, description, equipment, temperature, duration, images), reorder, at-publish completeness gate (`REC_VAL_016`, `REC_POST_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§5; CHEF-HP-02; CHEF-VAL-13](/en/inventory/recipe/02-business-rules) |
| 14 | Versioning and pricing-history audit trail — `tb_recipe_version` full snapshot on every `PUBLISHED` edit; `tb_recipe_pricing_history` on cost/price change; rollback via snapshot re-apply; auditor read-only access (`REC_XMOD_009`, `REC_AUTH_013`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5–§6; CC-EDGE-07/08; AC-HP-06/07; cross-persona TS #11](/en/inventory/recipe/02-business-rules) |
| 15 | RBAC and permission gates — per-role, per-category permission scoping (chef, cost controller, outlet manager, procurement, audit/config); category-scoped chefs; soft-delete authority (`REC_AUTH_001–014`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4; CHEF-PERM-01–07; CC-PERM-01–07; AC-PERM-01–09](/en/inventory/recipe/02-business-rules) |
| 16 | Recipe category master CRUD — hierarchical tree (self-FK `parent_id`), default cost settings seed onto new recipes, reparenting with cycle guard, delete guards, inactive flag — e2e-covered screen (2026-09-22) | ✅ | ✅ | ✅ | ✅ Done | [category.md](/en/inventory/recipe/category) |
| 17 | Cuisine master CRUD — flat catalogue with `enum_cuisine_region` anchor, unique-name guard, delete guard, retire/inactive flow — e2e-covered screen (2026-09-22) | ✅ | ✅ | ✅ | ✅ Done | [cuisine.md](/en/inventory/recipe/cuisine) |
| 18 | Equipment master CRUD — code + name, category FK, specs, maintenance schedule + dates, station assignment, qty counters, delete guard | ✅ | 🟡 | 🟡 | 🟡 Partial | [equipment.md](/en/inventory/recipe/equipment) |
| 19 | Equipment category master CRUD — flat functional grouping (Preparation, Cooking, Holding, …), name-unique guard, delete guard (app-layer; FK `NoAction`), rename fan-out to denormalised `category_name` | ✅ | 🟡 | 🟡 | 🟡 Partial | [equipment-category.md](/en/inventory/recipe/equipment-category) |
| 20 | Clone recipe — copy header/ingredients/steps/variants into new `DRAFT`, clear `published_at`/`archived_at`, assign new code/name, fresh version chain on first publish | ✅ | ✅ | ✅ | ✅ Done | [CHEF-HP-07; CHEF-EDGE-06](/en/inventory/recipe/04-test-scenarios-chef) |
| 21 | Import POS — upload / scheduled Simphony pull, brand file formats, what an import writes, edge cases | ✅ | ✅ | ✅ | ✅ Done | [import-pos](/en/inventory/recipe/import-pos) |
| 22 | Sales Consumption — list / calendar, line resolution, recipe explosion, verify on-hand, post, void, daily sync, mapping | ✅ | ✅ | ✅ | ✅ Done | [sales-consumption](/en/inventory/recipe/sales-consumption) |
| 23 | Cook mode — read-only tablet view at `/operation-plan/recipe/:id` (steps, ingredient checklist, wake-lock) — module + UF overview notes only; no TS scenario | 🟡 | 🟡 | ⬜ | 🟡 Partial | [recipe](/en/inventory/recipe) |
| 24 | Recipe comments with attachments (`tb_recipe_comment`, `recipe-comments`; 2026-10) — data-model + module page only; no BR rule or TS | 🟡 | 🟡 | ⬜ | 🟡 Partial | [01-data-model §2.11](/en/inventory/recipe/01-data-model) |

### 10. Vendor Pricelist
Source: `../carmen/docs/vendor-pricelist-management/`

> **Note:** The module covers a 6-phase price-collection lifecycle — template setup, campaign/RFQ, vendor invitation, vendor portal submission, validation/quality scoring, and pricelist approval — plus downstream price-assignment on PR/PO and GRN variance checking. BR coverage is in `02-business-rules.md` (rule families `VPL_VAL_*` / `VPL_CALC_*` / `VPL_AUTH_*` / `VPL_POST_*` / `VPL_XMOD_*`, ~81 rules). UF is the `03-user-flow.md` lifecycle overview plus four per-persona files (Purchaser, Vendor, Finance, Audit/Config). TS is the `04-test-scenarios.md` cross-persona overview plus four per-persona scenario files — all with Pre-condition / Steps / Expected format. Vendor-master CRUD (Phase 1 in source) is referenced only obliquely in the wiki (VPL_XMOD_007, VPL_AUTH_002); no dedicated page or scenario exists for it.

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Vendor master CRUD — create/edit/deactivate/soft-delete vendor profiles, category assignments, status monitoring, in-use guards on inactive vendor | 🟡 | 🟡 | ⬜ | 🟡 Partial | [BR §4 VPL_AUTH_002; §6 VPL_XMOD_007](/en/inventory/vendor-pricelist/02-business-rules) |
| 2 | Price-collection template create / edit / activate — name uniqueness, product selection (category/subcategory/item-group), MOQ-tier structure, validity-period / reminder schedule, activate/inactivate/re-activate lifecycle (`VPL_VAL_001–007`, `VPL_POST_001–004`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§5.1](/en/inventory/vendor-pricelist/02-business-rules) |
| 3 | Campaign (RFQ) create / launch / pause / cancel — date-window validation, vendor invitation rows, email-template validation, campaign lifecycle states (`VPL_VAL_008–013`, `VPL_POST_005–009`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§5.2; UF §2.2; request-price-list.md](/en/inventory/vendor-pricelist/02-business-rules) |
| 4 | Vendor invitation & secure token dispatch — cryptographic token generation, per-vendor unique link, email delivery, invitation lifecycle (pending → in-progress → submitted → approved/expired) (`VPL_VAL_011–013`, `VPL_AUTH_007`, `VPL_POST_010–014`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4,§5.3; UF §2.3; TS-Vendor HP-01](/en/inventory/vendor-pricelist/02-business-rules) |
| 5 | Vendor portal price submission — save / submit via `pricelist-external` controller + `UrlTokenGuard`; multi-MOQ-tier inline expansion, auto-save, draft/resume (`VPL_VAL_018–023`, `VPL_POST_015–016`, `VPL_AUTH_008`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§5.4; TS-Vendor HP-01..06](/en/inventory/vendor-pricelist/04-test-scenarios-vendor) |
| 6 | Excel template download / upload and email submission method — Excel parse/validate, portal upload, email-to-staff upload path (`submission_method = email / portal`), error reporting (`VPL_AUTH_003`, `VPL_VAL_017`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 VPL_AUTH_003; TS-Purchaser HP-06; TS-Vendor HP-04,09](/en/inventory/vendor-pricelist/04-test-scenarios-purchaser) |
| 7 | Multi-currency pricing — vendor chooses submission currency, per-currency storage (no FX mutation), cross-currency comparison via tenant FX rate at report date, Finance Manager co-signoff for multi-currency activation (`VPL_CALC_005`, `VPL_AUTH_008–010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 VPL_CALC_005; §4 VPL_AUTH_008-010; TS-Finance HP-01; X-VPL-03](/en/inventory/vendor-pricelist/02-business-rules) |
| 8 | Price validity periods — effective-from / effective-to validation, auto-expire cron (`active → expired`), re-activate within window, validity countdown display (`VPL_VAL_016`, `VPL_CALC_007`, `VPL_POST_020–021`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 VPL_VAL_016; §5.4 VPL_POST_021; TS-Purchaser VAL-09; EDGE-04; X-VPL-08](/en/inventory/vendor-pricelist/02-business-rules) |
| 9 | Pricelist approval workflow — review queue, approve (below/above high-value threshold), reject with reason + resubmit, multi-currency co-signoff, segregation of duties gate (`VPL_AUTH_004–006`, `VPL_AUTH_010,014`, `VPL_POST_017–018`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4,§5.4; TS-Purchaser HP-03,05,08; PERM-03..09; X-VPL-02,03,04](/en/inventory/vendor-pricelist/04-test-scenarios-purchaser) |
| 10 | Price comparison / selection on PR — preferred-vendor flag management (one-per-cell invariant), price-assignment engine (business-rules engine, confidence scoring, fallback hierarchy), PR-line default from active pricelist (`VPL_XMOD_001–002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 VPL_XMOD_001-002; TS-Purchaser HP-04; X-VPL-01](/en/inventory/vendor-pricelist/02-business-rules) |
| 11 | GRN price-variance check — unit-price comparison on GRN posting, variance tolerance gate, variance categorisation (within-tolerance / vendor-over-bill / pricelist-out-of-date / FX-only), downstream AP / Finance action (`VPL_XMOD_005`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 VPL_XMOD_005; TS-Finance HP-02..06; X-VPL-06](/en/inventory/vendor-pricelist/04-test-scenarios-finance) |
| 12 | Data validation & quality scoring — real-time field-level validation, MOQ-tier non-increasing rule, completeness checks, quality-score computation and threshold routing to Manager (`VPL_CALC_006`, `VPL_VAL_018–025`, `VPL_XMOD_009`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2–§3 VPL_CALC_006; §6 VPL_XMOD_009; TS X-VPL-09; TS-Purchaser HP-03](/en/inventory/vendor-pricelist/02-business-rules) |
| 13 | Portal token policy / session security — token expiry, IP-allowlist enforcement, concurrent-session limits, token revocation by Sysadmin/Manager, suspicious-activity detection (`VPL_AUTH_007`, `VPL_AUTH_012`, `VPL_AUTH_015`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 VPL_AUTH_007,012,015; TS-Vendor VAL-01..03; EDGE-04; TS-AuditConfig HP-08; X-VPL-07](/en/inventory/vendor-pricelist/04-test-scenarios-audit-config) |
| 14 | Audit trail & RBAC — activity-log writes on every status transition and comment, full chain traceability (template → campaign → invitation → pricelist → PR/PO/GRN), read-only Auditor surface, Sysadmin configuration-change audit log, data-export approval flow (`VPL_AUTH_001–015`, `VPL_POST_001–022`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4; TS-AuditConfig HP-01..10; PERM-01..08](/en/inventory/vendor-pricelist/04-test-scenarios-audit-config) |
| 15 | RFQ send-email (dispatch campaign invitation mail) | ✅ | ✅ | ✅ | ✅ Done | [request-price-list](/en/inventory/vendor-pricelist/request-price-list) |
| 16 | Vendor `tax_no` / `branch_no` / `rating` / default AP account fields (vendor form since 2026-10; `VPL_VAL_026`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2; TS-Purchaser HP-12](/en/inventory/vendor-pricelist/02-business-rules) |
| 17 | Vendor certification screen | ✅ | ✅ | ✅ | ✅ Done | [UF — Vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor) |
| 18 | Price list void / restore — reversible `voided` status with reason, read-only meanwhile | ✅ | ✅ | ✅ | ✅ Done | [TS-Purchaser HP-13; UF](/en/inventory/vendor-pricelist/04-test-scenarios-purchaser) |
| 19 | Admin-only permanent delete of a price list, blocked when a PR line, credit note or RFQ line references it | ✅ | ✅ | ✅ | ✅ Done | [TS-Purchaser VAL-12/13; EDGE-08](/en/inventory/vendor-pricelist/04-test-scenarios-purchaser) |
| 20 | Price List screen validity tabs — Current / Expired / All | ✅ | ✅ | ✅ | ✅ Done | [TS-Purchaser HP-14; UF](/en/inventory/vendor-pricelist/03-user-flow) |
| 21 | Portal price entry before tax — add-VAT only, read-only Tax Rate, computed Total (`VPL_VAL_021`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 VPL_VAL_021; TS-Vendor HP-09](/en/inventory/vendor-pricelist/04-test-scenarios-vendor) |
| 22 | Vendor comments + attachments sheet and Print (Vendor Detail Report) — UF / master-data page only; E2E gap noted, no TS scenario | 🟡 | ✅ | ⬜ | 🟡 Partial | [UF — Purchaser §2](/en/inventory/vendor-pricelist/03-user-flow-purchaser) · [master-data/vendor](/en/inventory/master-data/vendor) |
| 23 | Certification list shows holder counts per certificate (valid / expiring / expired) — one sentence on the module page; no BR / UF / TS detail | ⬜ | 🟡 | ⬜ | 🟡 Partial | [vendor-pricelist](/en/inventory/vendor-pricelist) |
| 24 | RFQ list Responses column (`submitted / invited`) and Upcoming / Open / Closed window badge | ✅ | ✅ | ✅ | ✅ Done | [request-price-list](/en/inventory/vendor-pricelist/request-price-list) |
| 25 | `price-compare` suggestions (`suggests`) for quantities below the cheapest MOQ tier | ✅ | ✅ | ✅ | ✅ Done | [BR §3 VPL_CALC_004; TS-Purchaser EDGE-09](/en/inventory/vendor-pricelist/02-business-rules) |
| 26 | Vendor Management dashboard — 10 system tiles from Backstage widget templates + shared BU widget section | ✅ | ✅ | ✅ | ✅ Done | [vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard) |

### 11. Physical Count
Source: `../carmen/docs/app/inventory-management/physical-count/` , `../carmen/docs/app/inventory-management/physical-count-management/` , `../carmen/docs/documents/pc/`

> **Note (re-judged 2026-10-27 against the re-synced pages):** the wiki documents the live code — three-tier `tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`, one permission key (`inventory_management.physical_count`), one undifferentiated role split across the list and entry / review screens. BR coverage is `02-business-rules.md` (`PHC_VAL_*` / `PHC_CALC_*` / `PHC_AUTH_*` / `PHC_POST_*` / `PHC_XMOD_*`, rewritten from code; § 5.1 lists divergences from the planning document). Rows 3, 4, 7, 8, 11, 13 and 14 describe capabilities the pages document as **absent** (frozen / live lock, counter zones, recount, override, approval, auditor, sysadmin config); per this file's convention they are ✅ Done with the "(documented as not implemented — no code path)" suffix, and their TS ✅ rests on the correction pages `04-test-scenarios-audit-config.md` / `03-user-flow-audit-config.md`. TS ✅ on the real rows rests on the cross-persona § 4 table in `04-test-scenarios.md` (has a Steps column); the per-screen tables only carry Pre-condition / Expected. The 2026-09-22 rule that "none of the TS tables include Steps, so all TS cells are 🟡" no longer holds. Submit now posts to the ledger (2026-10); no `physical-count` Playwright spec exists, but the opt-in period-close specs 921 / 922 exercise it.

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Open the count round — **Start Period Close** (`POST /period-ends/start-counting`) moves `tb_physical_count_period` `draft → counting`; the list auto-provisions the period row; creating a count while the period is not `counting` is refused (`PHC_VAL_001`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PHC_VAL_001](/en/inventory/physical-count/02-business-rules) · [UF §2](/en/inventory/physical-count/03-user-flow) · [TS-List L-F-01, L-V-01](/en/inventory/physical-count/04-test-scenarios-count-lead) |
| 2 | Start / resume the count sheet for `(period, location)` — product pool = assigned ∪ stocked products, idempotent re-create (`PHC_VAL_002`–`003`); `on_hand_qty` read from the counted period's cost layers (`PHC_CALC_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PHC_VAL_002–003; §3 PHC_CALC_002](/en/inventory/physical-count/02-business-rules) · [UF-List §3](/en/inventory/physical-count/03-user-flow-count-lead) · [TS cross-persona #1–#4; L-F-02, L-F-03, L-E-02](/en/inventory/physical-count/04-test-scenarios) |
| 3 | Required vs optional locations — `physical_count_type` decides which locations gate period close; frozen / live mode and a location transaction lock **do not exist** (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §5.1 transaction-lock row; §6 PHC_XMOD_003](/en/inventory/physical-count/02-business-rules) · [UF §2](/en/inventory/physical-count/03-user-flow) · [TS cross-persona #7, #8; L-F-06](/en/inventory/physical-count/04-test-scenarios) |
| 4 | Counter assignment / zones — **not implemented**: any holder of `inventory_management.physical_count` can count any location (`PHC_AUTH_002`) (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PHC_AUTH_002](/en/inventory/physical-count/02-business-rules) · [UF-Counter](/en/inventory/physical-count/03-user-flow-counter) · [TS-Counter E-R-01](/en/inventory/physical-count/04-test-scenarios-counter) |
| 5 | Line entry — `actual_qty` per line, Save stamps `counted_at` / `counted_by_id`, notes + photo, calculator, import / export, Refresh adds newly stocked products (`PHC_VAL_004`–`005`, `PHC_CALC_003`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PHC_VAL_004–005; §3 PHC_CALC_003](/en/inventory/physical-count/02-business-rules) · [UF-Counter §3](/en/inventory/physical-count/03-user-flow-counter) · [TS-Counter E-F-01..07; cross-persona #3, #4, #6](/en/inventory/physical-count/04-test-scenarios-counter) |
| 6 | Variance — `diff_qty = actual_qty − on_hand_qty` (`PHC_CALC_001`) with on-hand recomputed at Submit for Review; review screen shows match / overage / shortage counts (no variance % or monetary variance) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 PHC_CALC_001–002](/en/inventory/physical-count/02-business-rules) · [UF-Counter](/en/inventory/physical-count/03-user-flow-counter) · [TS-Counter E-F-08, E-F-09; cross-persona #1, #2](/en/inventory/physical-count/04-test-scenarios-counter) |
| 7 | Recount escalation / variance tolerance threshold — **not implemented** (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 "Not found in code" note; §5.1](/en/inventory/physical-count/02-business-rules) · [UF §2](/en/inventory/physical-count/03-user-flow) · [TS-AC correction page](/en/inventory/physical-count/04-test-scenarios-audit-config) |
| 8 | Override / countersign of variance by a second person — **not implemented**: the user who counts also reviews and submits (`PHC_AUTH_003`) (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PHC_AUTH_003](/en/inventory/physical-count/02-business-rules) · [UF-Audit correction](/en/inventory/physical-count/03-user-flow-audit-config) · [TS-AC correction page](/en/inventory/physical-count/04-test-scenarios-audit-config) |
| 9 | Final Submit — every line counted (`PHC_VAL_004`), not already `completed` (`PHC_VAL_006`), current `doc_version` (`PHC_VAL_007`); `in_progress → completed` | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PHC_VAL_004, 006, 007](/en/inventory/physical-count/02-business-rules) · [UF §2](/en/inventory/physical-count/03-user-flow) · [TS-Counter V-01..V-03; cross-persona #5, #6](/en/inventory/physical-count/04-test-scenarios-counter) |
| 10 | Variance rollup + ledger posting — one `eop_in` stock-in (overage) and one `eop_out` stock-out (shortage), created `completed`, each line posted via `executeAdjustmentIn/Out` into the counted period; overage priced by BU `si.cost-from`, shortage at posted cost; all-or-nothing on a shortfall; no back-reference to the count (`PHC_POST_001`–`003`, `PHC_CALC_004`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PHC_POST_001–003](/en/inventory/physical-count/02-business-rules) · [UF-Counter](/en/inventory/physical-count/03-user-flow-counter) · [TS cross-persona #2; TS-Counter E-F-10, E-E-05, E-E-06](/en/inventory/physical-count/04-test-scenarios) |
| 11 | Approval of the rollup adjustment — **not implemented**: the documents are created `completed` and posted immediately (`PHC_POST_001`, `PHC_AUTH_003`) (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PHC_AUTH_003; §5 PHC_POST_001](/en/inventory/physical-count/02-business-rules) · [UF-Audit correction](/en/inventory/physical-count/03-user-flow-audit-config) · [TS-AC correction page](/en/inventory/physical-count/04-test-scenarios-audit-config) |
| 12 | Period-close gate — `validatePhysicalCount` blocks close until every required location has a `completed` count (`PHC_XMOD_003`); the planning-doc `FINALIZED` / GL step does not exist (§5.1) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 PHC_XMOD_003; §5.1](/en/inventory/physical-count/02-business-rules) · [UF-List §4](/en/inventory/physical-count/03-user-flow-count-lead) · [TS cross-persona #7, #8](/en/inventory/physical-count/04-test-scenarios) |
| 13 | Audit trail / full-chain inspection — **no dedicated Auditor surface**; correction after completion needs a fresh adjustment (`PHC_POST_004`) (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PHC_AUTH_003; §5 PHC_POST_004](/en/inventory/physical-count/02-business-rules) · [UF-Audit correction](/en/inventory/physical-count/03-user-flow-audit-config) · [TS-AC correction page](/en/inventory/physical-count/04-test-scenarios-audit-config) |
| 14 | Sysadmin configuration — **none per module**: no tolerance or reason-code mapping; overage priced by BU `si.cost-from`, and active `eop_in` / `eop_out` adjustment types are a prerequisite (`PHC_POST_002`) (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4; §5 PHC_POST_002](/en/inventory/physical-count/02-business-rules) · [UF-Audit correction](/en/inventory/physical-count/03-user-flow-audit-config) · [TS-AC correction page](/en/inventory/physical-count/04-test-scenarios-audit-config) |

### 12. Spot Check
Source: `../carmen/docs/inventory-management/period-end-process.md` (passing reference only — no dedicated SPC docs folder exists); rule authority is the wiki's own `02-business-rules.md` (`SPC_VAL_*` / `SPC_CALC_*` / `SPC_AUTH_*` / `SPC_POST_*` / `SPC_XMOD_*`, ~30 rules).

> **Note (re-judged 2026-10-27 against the re-synced pages):** the wiki documents the live code — a flat `tb_spot_check` → `tb_spot_check_detail` tree, one permission key (`inventory_management.spot_check`), no persona hand-off. BR coverage is `02-business-rules.md` (`SPC_VAL_*` / `SPC_CALC_*` / `SPC_AUTH_*` / `SPC_POST_*` / `SPC_XMOD_*`; § 5.1 compares against the planning document). Rows 3, 6, 7, 9 (approval half), 12 and 13 describe capabilities the pages document as **absent**; per this file's convention they are ✅ Done with the "(documented as not implemented — no code path)" suffix, their TS ✅ resting on the correction pages. Row 8 is Done because the pages document precisely that the final submit has **no rollup** — a spot check writes nothing to the ledger. TS ✅ on the real rows rests on the cross-persona § 4 table in `04-test-scenarios.md` (has a Steps column); the per-screen tables only carry Pre-condition / Expected. Row 11 stays 🟡: nothing in the TS pages asserts that spot check is not a period-end gate. No `spot-check` Playwright spec exists (manual catalog `760-spot-check.md`, 44 cases).

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create a spot check — pick a listed location (inventory / consignment, active, counted-flag filter), method and size; header `pending` with `on_hand_qty` seeded per line (`SPC_VAL_001`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SPC_VAL_001](/en/inventory/spot-check/02-business-rules) · [UF-IC §3](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS-IC L-F-06; cross-persona #1, #4, #10](/en/inventory/spot-check/04-test-scenarios) |
| 2 | Item selection — random, high-value (`on_hand_qty × max cost`, active-period window) or manual product pick; empty pool and out-of-pool products rejected (`SPC_VAL_002`–`004`, `SPC_CALC_004`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SPC_VAL_002–004; §3 SPC_CALC_004](/en/inventory/spot-check/02-business-rules) · [UF-IC §3](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS cross-persona #2, #3, #4, #10, #11](/en/inventory/spot-check/04-test-scenarios) |
| 3 | Counter assignment — **not implemented**: any holder of `inventory_management.spot_check` counts any spot check (`SPC_AUTH_002`) (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SPC_AUTH_002](/en/inventory/spot-check/02-business-rules) · [UF-Counter](/en/inventory/spot-check/03-user-flow-counter) · [TS-IC L-R-01](/en/inventory/spot-check/04-test-scenarios-inventory-controller) |
| 4 | Count entry and Save For Resume — `actual_qty` per line, first Save moves `pending → in_progress`, `counted_at` / `counted_by_id` stamped, notes, import / export (`SPC_VAL_007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SPC_VAL_007](/en/inventory/spot-check/02-business-rules) · [UF-Counter §3](/en/inventory/spot-check/03-user-flow-counter) · [TS-Counter E-F-06; cross-persona #5, #6](/en/inventory/spot-check/04-test-scenarios) |
| 5 | Variance — `diff_qty = actual_qty − on_hand_qty` (`SPC_CALC_001`), on-hand refreshed at Submit for Review from the active period (`SPC_CALC_002`), review summary counts (`SPC_CALC_003`); no monetary variance exists | ✅ | ✅ | ✅ | ✅ Done | [BR §3 SPC_CALC_001–003](/en/inventory/spot-check/02-business-rules) · [UF §2](/en/inventory/spot-check/03-user-flow) · [TS-Counter E-F-07; cross-persona #2, #6](/en/inventory/spot-check/04-test-scenarios) |
| 6 | Recount escalation / variance tolerance — **not implemented** (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 "Not found in code" note](/en/inventory/spot-check/02-business-rules) · [UF-Audit correction](/en/inventory/spot-check/03-user-flow-audit-config) · [TS-AC correction page](/en/inventory/spot-check/04-test-scenarios-audit-config) |
| 7 | Override / countersign of variance — **not implemented** (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SPC_AUTH_003](/en/inventory/spot-check/02-business-rules) · [UF-Audit correction](/en/inventory/spot-check/03-user-flow-audit-config) · [TS-AC correction page](/en/inventory/spot-check/04-test-scenarios-audit-config) |
| 8 | Final Submit — `doc_status → completed`, `end_date` stamped, **no completeness check** at the API (`SPC_VAL_008`); **no rollup, no stock-in / stock-out, no ledger write** (`SPC_POST_001`–`002`) (rollup documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SPC_VAL_008; §5 SPC_POST_001–002](/en/inventory/spot-check/02-business-rules) · [UF §2](/en/inventory/spot-check/03-user-flow) · [TS-Counter E-F-09; cross-persona #1, #2, #6, #12](/en/inventory/spot-check/04-test-scenarios) |
| 9 | Correcting a confirmed variance — only by a separately created inventory-adjustment document, no link back (`SPC_POST_003`, `SPC_XMOD_001`); rollup approval workflow **not implemented** (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SPC_POST_003; §6 SPC_XMOD_001](/en/inventory/spot-check/02-business-rules) · [UF-IC §5](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS cross-persona #12](/en/inventory/spot-check/04-test-scenarios) |
| 10 | Reset (void) — `pending` / `in_progress` → `void`, detail rows kept; blocked once `void` or `completed` (`SPC_VAL_006`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SPC_VAL_006](/en/inventory/spot-check/02-business-rules) · [UF §2](/en/inventory/spot-check/03-user-flow) · [TS-IC L-F-12, L-V-06; cross-persona #7](/en/inventory/spot-check/04-test-scenarios) |
| 11 | Period-close gate — **spot check is not a period-end gate** (`period-end.validate.ts` has no spot reference; planning-doc claim is 🔴 in § 5.1, `SPC_XMOD_003`) — absence documented in BR + UF; no TS scenario asserts it | ✅ | ✅ | ⬜ | 🟡 Partial | [BR §5.1; §6 SPC_XMOD_003](/en/inventory/spot-check/02-business-rules) · [UF-IC §3](/en/inventory/spot-check/03-user-flow-inventory-controller) |
| 12 | Audit trail / full-chain inspection — **no dedicated Auditor surface** (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SPC_AUTH_003](/en/inventory/spot-check/02-business-rules) · [UF-Audit correction](/en/inventory/spot-check/03-user-flow-audit-config) · [TS-AC correction page](/en/inventory/spot-check/04-test-scenarios-audit-config) |
| 13 | Sysadmin configuration — **none**: no tolerance, default size / method or reason-code mapping exists (documented as not implemented — no code path) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SPC_AUTH_003](/en/inventory/spot-check/02-business-rules) · [UF-Audit correction](/en/inventory/spot-check/03-user-flow-audit-config) · [TS-AC correction page](/en/inventory/spot-check/04-test-scenarios-audit-config) |
| 14 | History view — own route `/inventory-management/spot-check/history`, server-side filter / search / sort / paging; reopening a `completed` check re-runs `reviewItems()` unguarded (`SPC_POST_004`, confirmed code gap) | ✅ | ✅ | ✅ | ✅ Done | [UF-IC §3](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS-IC L-F-02; cross-persona #8](/en/inventory/spot-check/04-test-scenarios-inventory-controller) · [BR §5 SPC_POST_004](/en/inventory/spot-check/02-business-rules) |

## Table B — Config / reference modules

_Reference/admin modules. One `###` section per module, added by Tasks 13–18._

### 13. Master Data
Source: `../carmen/docs/settings/` , `../carmen/docs/prisma-schema/`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | Adjustment Type | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/adjustment-type) |
| 2 | Business Unit | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/business-unit) |
| 3 | Credit Note Reason | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/credit-note-reason) |
| 4 | Credit Term | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/credit-term) |
| 5 | Currency | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/currency) |
| 6 | Delivery Point | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/delivery-point) |
| 7 | Department | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/department) |
| 8 | Exchange Rate | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/exchange-rate) |
| 9 | Extra Cost Type (allocation `by_qty` / `by_value` / `manual`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/extra-cost-type) |
| 10 | Location | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/location) |
| 11 | Tax Profile | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/tax-profile) |
| 12 | Unit | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/unit) |
| 13 | Vendor | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/vendor) |
| 14 | Vendor Business Type (`tb_vendor_business_type`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/vendor-business-type) |
| 15 | Shelf | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/shelf) |
| 16 | Chart of Accounts (create form sends `category` / `nature` / `type`; `department_required` / `allowed_dimensions` toggles are not persisted — documented gap) | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/chart-of-accounts) |
| 17 | Cost Center (list screens, optional group, Carmen GL department import, in-use delete guard) | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/cost-center) |
| 18 | Chart of Account Mapping (list, override, batch, review, generate, resolve, status filters) | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/chart-of-account-mapping) |
| 19 | Tax Profile WHT classification (`tax_type`, `wht_pnd_form`, `wht_income_type`, GL account) — API only, the dialog sends none of the fields | ✅ | 🟡 | 🟡 Partial | [link](/en/inventory/master-data/tar-profile) |
| 20 | Location default cost center (`cost_center_id`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/location) |

### 14. System Config
Source: `../carmen/docs/settings/` , `../carmen/docs/app/system-administration/`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | Application Config | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/application-config) |
| 2 | Email Configuration | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/config-email) |
| 3 | Dimension | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/dimension) |
| 4 | Document Management | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/document) |
| 5 | Menu | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/menu) |
| 6 | Inventory Period | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/period) |
| 7 | Query Dataset (SQL Workbench) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/query-dataset) |
| 8 | Running Code | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/running-code) |
| 9 | Workflow | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/workflow) |
| 10 | Dashboard Dataset (code-registered in **micro-data** Go service; no tenant table — gateway proxies `/api/dashboard/datasets`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/dashboard-dataset) |
| 11 | Document Version — optimistic-concurrency `doc_version` guard (409 Conflict on stale save); cross-cutting across ~20 transactional/config entities | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/doc-version) |
| 12 | Email Profile | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/config-email) |
| 13 | Email Template | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/config-email) |
| 14 | Interface screen (BU API key lifecycle, `api/ext/v1` auth + `ap-invoices` / `gl-journals` endpoints, POS summary) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/interface) |
| 15 | Notification Template (app-only) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/notification-template) |
| 16 | Ask AI (per-BU provider toggles, prompt override, consumption by the PR Ask AI menu) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/ask-ai) |
| 17 | Workflow authoring surface (Insights tab, stage rail, duplicate, seeded notification templates, per-stage action switches) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/workflow) |
| 18 | Email profile sign-in methods (password / OAuth, Hotmail device-code connect, test) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/config-email) |
| 19 | Activity Log screen (`tb_activity` grid, 25 actions, multi-actor comma-separated filter, XLSX export, print) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/activity-log) |

### 15. Dashboard
Source: `../carmen/docs/features/` , `../carmen/docs/pages/`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | Main dashboard (cross-module KPI overview) | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/main) |
| 2 | GRN dashboard | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/grn) |
| 3 | Inventory dashboard | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/inventory) |
| 4 | PO dashboard | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/po) |
| 5 | PR dashboard | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/pr) |
| 6 | SR dashboard | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/sr) |
| 7 | Widget workspace dashboard (current `/dashboard` route — drag-and-drop `tb_widget_workspace` tiles, add/remove/reorder KPI/pie/bar widgets from Dataset catalogue) — display / render switch / lazy load via micro-data (2026-09-22) | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/widget-workspace) |
| 8 | My Pending widget (PR / PO / SR pending-count tiles for the signed-in user — `dashboard-my-pending.tsx`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/my-pending) |
| 9 | My Approval widget (approval task queue by doc type across PR / PO / SR — `dashboard-my-approval.tsx`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/my-approval) |
| 10 | BU widget section on `/dashboard` and every module dashboard + platform deploy (`skip_customized` / `overwrite`) — BU widgets now have a UI | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/widget) |
| 11 | Bilingual widget titles (`title_i18n`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/widget) |
| 12 | `inventory.slow-moving` table dataset with cell links | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/widget) |

### 16. Access Control
Source: `../carmen/docs/security/` , `../carmen/docs/app/system-administration/permission-management/` , `../carmen/docs/app/system-administration/user-management/` , `../carmen/docs/prisma-schema/schema.prisma`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | User (`tb_user`, `tb_user_profile`, `tb_user_login_session`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/user) |
| 2 | Application Role (`tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/application-role) |
| 3 | Permission (`tb_permission`) — incl. comment + approval-workflow App IDs for PR/PO/SR (`*Comment.*`, `storeRequisition.{approve,reject,review,save}`, `my-approve.findAll`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/permission) |
| 4 | Business Unit User (`tb_user_tb_business_unit`, `tb_temp_bu_user`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/business-unit-user) |
| 5 | User Location (`tb_user_location`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/user-location) |
| 6 | Department User (`tb_department_user` — user ↔ department pivot with `is_hod` HOD flag; exists in `schema.prisma` and referenced in `DD-permission-management.md` / `DD-user-management.md`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/department-user) |
| 7 | User access PATCH (single-request update of a user's access) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/user) |
| 8 | User × role matrix | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/user) |
| 9 | Invitations flow | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/user) |
| 10 | Role / permission controllers carry no `AppIdGuard` and no `@Permission` (KeycloakGuard only; RBAC decorators now on 88 routes elsewhere) — open code gap | ✅ | 🟡 | 🟡 Partial | [link](/en/inventory/access-control/permission) |
| 11 | Google sign-in on the login and invitation pages (`/api/auth/google/*`, app-status codes) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/user) |

### 17. Reporting & Audit
Source: `../carmen/docs/reports/` , `../carmen/docs/app/system-administration/notification-preferences/` , `../carmen/docs/app/system-administration/monitoring/`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | Activity (`tb_activity`, `enum_activity_action`) — tenant-wide append-only audit log | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/activity) |
| 2 | Attachment (`tb_attachment`) — S3-backed binary metadata, polymorphic linkage; presigned-URL re-resolution on read + comment-attachment DTO | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/attachment) |
| 3 | Report History (`tb_report_job`) — append-only execution log for every report run | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/history) |
| 4 | Notification (`tb_notification`, `tb_message_format`, `tb_news`) — inbound message pipe, templates, platform bulletins — NotifyInput redesign (2026-09-22) | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/notification) |
| 5 | Report (`tb_report_job`, `tb_report_schedule`, `tb_report_template`, `tb_print_template_mapping`) — full report generation pipeline; micro-data/micro-report split (dataset resolve vs render) — print-form default + PDF export (2026-09-22) | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/report) |
| 6 | Report Schedule (`tb_report_schedule`) — cron-driven recurring report runs | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/schedule) |
| 7 | User Activity (`tb_user_login_session` + `tb_activity` projection) — actor-centric forensic login/logout timeline | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/user-activity) |
| 8 | Widget (`tb_widget_dashboard`, `tb_widget_default_layout`, `tb_widget_workspace`) — dashboard tiles, seed layouts, saved queries; CRUD hosted in **micro-data** (gateway-proxied); BU widgets now have a UI, module and deploy state (2026-10) | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/widget) |
| 9 | Per-record Activity sheet (document-level audit drawer) | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/activity) |
| 10 | Report Export data (CSV via Export XML, `POST /reports/export`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/report) |
| 11 | Report template availability — `allow_run` / `allow_export` switches, `actionable=true` listing | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/report) |
| 12 | Activity price masking — PR / PO price fields hidden in activity rows for callers who may not see prices | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/activity) |
| 13 | Notification `/ws` socket authentication (`{ type: "auth", token }` within 5 s) | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/notification) |

### 18. Templates
Source: `../carmen/docs/app/vendor-management/pricelist-templates/` , `../carmen/docs/purchase-request-management/`

> **Note (2026-09-22):** the notification template lives in System Config (#15 Notification Template), not here.

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | Price List Template (`tb_pricelist_template`) — RFQ-round scaffold: currency, validity, reminder schedule, escalation | ✅ | ✅ | ✅ Done | [link](/en/inventory/templates/price-list) |
| 2 | Purchase Request Template (`tb_purchase_request_template` + detail + comment) — reusable PR line-bundle cloned into new PRs | ✅ | ✅ | ✅ Done | [link](/en/inventory/templates/purchase-request) |
| 3 | PR template line delete (form posts `delete: [{ id }]`; before `48edc588` the line was silently kept) | ✅ | ✅ | ✅ Done | [link](/en/inventory/templates/purchase-request) |
| 4 | Price-list template name check — case-insensitive, `409`, service-side only | ✅ | ✅ | ✅ Done | [link](/en/inventory/templates/price-list) |

### 19. General Ledger
Source: `../carmen-turborepo-backend-v2/` GL module (backend + Bruno + cron only, no UI) · Wiki: `en/inventory/general-ledger.md`, `en/inventory/general-ledger/gl-posting.md`

> **Scope note (owner decision 2026-09-22):** the wiki documents the General Ledger only at its seam with inventory. Row 1 is the seam and is Done because the page proves no inventory-to-GL posting exists. Row 2 (GL master, budgets, JV templates, GL reports) is **⬜ Not yet — out of scope by owner decision 2026-09-22**; it is listed so the gap is explicit and must not be read as 🟡 Partial.

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | GL posting from inventory (scoped: page proves none exists — nothing in inventory posts to the ledger as of backend `c9d788829`, 2026-10-27; the ledger is reached one step later by an AP invoice — rows 3–5) | ✅ | ✅ | ✅ Done | [gl-posting](/en/inventory/general-ledger/gl-posting) |
| 2 | GL master / budget / JV template / reports — out of scope by owner decision 2026-09-22 | ⬜ | ⬜ | ⬜ Not yet | [landing §1.1](/en/inventory/general-ledger) |
| 3 | AP invoice from GRN (`grn-candidates`, `from-grn`, `matched_qty`; posts Dr inventory / Dr input VAT / Cr AP on approval; GRN edit lock) | ✅ | ✅ | ✅ Done | [ap-invoice-from-grn](/en/inventory/general-ledger/ap-invoice-from-grn) |
| 4 | Subledger posting facade (reversal voucher on void, `GL_JV_IMMUTABLE`) | ✅ | ✅ | ✅ Done | [gl-posting](/en/inventory/general-ledger/gl-posting) |
| 5 | External read export `api/ext/v1/ap-invoices` (GRN, CN) and `gl-journals` (SR, SI, SO) | ✅ | ✅ | ✅ Done | [ap-invoice-from-grn §6](/en/inventory/general-ledger/ap-invoice-from-grn) |

## Maintenance notes

- Living doc — update by hand when wiki pages are added/expanded.
- Bump the `(as of …)` date in the Summary heading whenever rows change.
- 2026-06-09 backend/platform/micro-data docs sync: added System Config #11 Document Version (`doc_version` optimistic concurrency); enriched Access Control #3 Permission (comment + approval-workflow App IDs), Reporting & Audit #2/#5/#8 (attachment presigned-URL/DTO, micro-data↔micro-report split, widget CRUD in micro-data), System Config #10 Dashboard Dataset (micro-data backing). Process-module BR/UF/TS rows unchanged — these are reference/Table-B entities, all already ✅.
- 2026-09-22 EN re-sync (backend-v2 `ef4d6f08f`, frontend `0713cbc9`, bruno `7f96637`, e2e `809d8e3`): statuses re-judged against code; rows added for verify dry-runs, stock-movement / ref views, My Approval, CN tabs, cost read endpoints, start-counting, vendor portal / RFQ, Shelf / Chart of Accounts / Cost Center, Email Profile / Template / Interface / Notification Template, access PATCH / role matrix / invitations, Activity sheet; new §19 General Ledger (seam only — out of scope by owner decision). Rows whose behaviour has no code path are marked Done with a "(documented as not implemented — no code path)" suffix — the wiki documents the absence. Details: `.specs/resync-inventory-2026-09-22-progress.md` and `.specs/carmen-docs-drift-2026-09-22.md`. TH deferred.
- 2026-10-27 EN re-sync (backend `c9d788829`, frontend `391062b5`, bruno `5c98670`, e2e `d795a25`; baseline = the 2026-09-22 HEADs): +68 rows (313 → 381), 255 → 326 Done, 56 → 54 Partial, 2 → 1 Not yet. Physical Count and Spot Check re-judged row by row against the re-synced pages: all 14 PC rows and 13 of 14 SC rows are now ✅ — the rows were rewritten to the live mechanics (stale rule IDs, recount / approval / auditor / config rows now carry the "(documented as not implemented — no code path)" suffix); PC submit now posts to the ledger (Inventory #37 flipped to Done), SC submit still writes nothing. New pages: recipe/sales-consumption, recipe/import-pos, master-data/chart-of-account-mapping, system-config/ask-ai, system-config/interface (replaces the old "Not yet" row), general-ledger/ap-invoice-from-grn. **Rule applied to new rows:** ✅ Done only when BR, UF and TS all have a section; cross-cutting 2026-10 features that exist in BR / UF but have no scenario in `04-test-scenarios*` (PR / PO / SR stage-hidden prices and stage action switches, row visibility, comment attachment policy, `commit_date`, Inventory held-receipt / active-period rules, etc.) are 🟡 Partial with the reason in the row — closing them needs TS scenarios, not new pages. E2E-only items (PO `404-po-doc-flow`, period-close specs 910–924) were folded into existing rows (PO #24, Inventory #28), not added as rows. Not added: System Config `company-profile` page exists but has no row (pre-existing gap). Existing rows text-updated: GRN #5 (FOC-only, now Done), SR #18 / #22, ADJ #6, Costing #7, Recipe #1 / #2 / #13, VPL #16, MD #16 / #17 (Cost Center now Done), SysConfig #14 (Interface now Done), AC #10, RA #8, GL #1. Details: this entry plus the per-module sections above. TH deferred.
- Re-run Task 19's count when any row status changes.
