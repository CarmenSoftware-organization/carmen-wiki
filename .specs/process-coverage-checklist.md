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
| 11 | Final approval + transmit PO to vendor (in_progress → sent, auto-transmit) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PO_POST_004](/en/inventory/purchase-order/02-business-rules) |
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
| 24 | Status lifecycle (draft → in_progress → sent → partial → completed / closed / voided) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 + §5.1 status mapping](/en/inventory/purchase-order/02-business-rules) |

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
| 18 | Stock replenishment trigger (cron auto-generates SR draft; Inventory Controller reviews) | 🟡 | ✅ | ⬜ | 🟡 Partial | [stock-replenishment.md](/en/inventory/store-requisition/stock-replenishment) |
| 19 | Cancel SR (requester withdrawal / all-lines-rejected automatic, `SR_POST_009`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_009](/en/inventory/store-requisition/02-business-rules) |
| 20 | Void SR (admin — Inventory Controller / Sysadmin, pre-commit only, `SR_POST_010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 SR_POST_010](/en/inventory/store-requisition/02-business-rules) |
| 21 | Segregation of duties (Requester ≠ Approver `SR_AUTH_011`; Approver ≠ Fulfiller `SR_AUTH_012`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 SR_AUTH_011–012](/en/inventory/store-requisition/02-business-rules) |
| 22 | Closed-period commit block (`SR_VAL_014`; Finance reopen or admin void) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 SR_VAL_014](/en/inventory/store-requisition/02-business-rules) |
| 23 | Journal entry generation and GL posting (Dr/Cr per `sr_type` and cost-centre dimension) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 SR_POST_007](/en/inventory/store-requisition/02-business-rules) |
| 24 | Source costing-method feed (FIFO / moving-average cost-per-unit at issue, `SR_CALC_004`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §3 SR_CALC_004](/en/inventory/store-requisition/02-business-rules) |
| 25 | Status lifecycle (`draft → in_progress → completed / cancelled / voided` + §5.1 UI-vs-BRD mapping) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 + §5.1](/en/inventory/store-requisition/02-business-rules) |

### 5. Inventory Adjustment
Source: `../carmen/docs/inventory-adjustment/`

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create adjustment document — `tb_stock_in` (IN) or `tb_stock_out` (OUT) at `draft` (auto-number, location, department, description) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 ADJ_VAL_001–005](/en/inventory/inventory-adjustment/02-business-rules) |
| 2 | Reason-code selection and direction validation (reason `type` must match document direction; `ADJ_VAL_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 ADJ_VAL_002](/en/inventory/inventory-adjustment/02-business-rules) |
| 3 | Lot-level entry — existing lot on stock-in or stock-out; new-lot creation on stock-in (`ADJ_VAL_009`, `ADJ_AUTH_003`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 ADJ_VAL_009 / §4 ADJ_AUTH_003](/en/inventory/inventory-adjustment/02-business-rules) |
| 4 | Submit auto-approve (below-threshold existing-lot → `draft → completed` fast path, `ADJ_POST_001` / `ADJ_AUTH_002`) | ✅ | ✅ | ✅ | ✅ Done | [UF §2.2](/en/inventory/inventory-adjustment/03-user-flow) |
| 5 | Threshold-based approval routing (Store Keeper → Inventory Controller → Finance, `ADJ_AUTH_004` / `ADJ_AUTH_005`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 ADJ_AUTH_004–005](/en/inventory/inventory-adjustment/02-business-rules) |
| 6 | Wastage / write-off categorisation and GL-account mapping per reason code (`ADJ_XMOD_007`; wastage-reporting variant) | ✅ | ✅ | 🟡 | 🟡 Partial | [wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting) |
| 7 | Posting — inventory transaction + FIFO or weighted-average cost-layer write (`ADJ_POST_002`, `ADJ_CALC_005`–`007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 ADJ_POST_002](/en/inventory/inventory-adjustment/02-business-rules) |
| 8 | GL journal entry generation (Dr/Cr per reason-code `info.glAccount` and `dimension.department`, `ADJ_XMOD_007`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §6 ADJ_XMOD_007](/en/inventory/inventory-adjustment/02-business-rules) |
| 9 | Physical-count / spot-check variance rollup — auto-create and auto-post `tb_stock_in` / `tb_stock_out` (`ADJ_POST_006`, `ADJ_XMOD_002/003`) | ✅ | ✅ | ✅ | ✅ Done | [TS cross-persona #5–6](/en/inventory/inventory-adjustment/04-test-scenarios) |
| 10 | Void via compensating reversal (post-fact correction — two-step, `ADJ_POST_004`; original transaction not edited) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 ADJ_POST_004](/en/inventory/inventory-adjustment/02-business-rules) |
| 11 | Cancel pre-post (`draft / in_progress → cancelled`, `ADJ_POST_003`; no inventory effect; terminal) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 ADJ_POST_003](/en/inventory/inventory-adjustment/02-business-rules) |
| 12 | Segregation of duties (adjuster ≠ originating receiver above SoD threshold, `ADJ_AUTH_010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 ADJ_AUTH_010](/en/inventory/inventory-adjustment/02-business-rules) |
| 13 | Period-containment gate (closed / locked period rejection, `ADJ_VAL_011` / `INV_VAL_008`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 ADJ_VAL_011](/en/inventory/inventory-adjustment/02-business-rules) |
| 14 | Consignment-location adjustment (memo-only inbound; COGS + AP deferred to consumption, `ADJ_POST_008`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 ADJ_POST_008](/en/inventory/inventory-adjustment/02-business-rules) |
| 15 | Reason-code / adjustment-type configuration (Sysadmin CRUD, GL mapping, `requiresDocument` / `requiresQualityCheck` flags, thresholds, `ADJ_AUTH_008`) | ✅ | ✅ | ✅ | ✅ Done | [TS Audit/Config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config) |
| 16 | Status lifecycle (`draft → in_progress → completed → cancelled / voided` + §5.1 live-UI vs BRD mapping) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 + §5.1](/en/inventory/inventory-adjustment/02-business-rules) |

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
| 7 | Count-variance valuation by configured method (`enum_physical_count_costing_method`: `standard` / `last` / `average` / `last_receiving`) — cost resolved at count-rollup post time (`COST_CALC_008`, `COST_POST_009`; `COST_VAL_007`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #4; BR §3 COST_CALC_008](/en/inventory/costing/04-test-scenarios) |
| 8 | Period close — `tb_period_snapshot` rows written with `closing_qty / closing_cost_per_unit / closing_total_cost`; cost locked for the period (`COST_CALC_006`, `COST_POST_007`; `COST_VAL_008`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #5–6; FIN-HP-04–05](/en/inventory/costing/04-test-scenarios) |
| 9 | Period open — rollforward carries per-lot `cost_per_unit` (FIFO `lot_seq_no` preserved) or single WA anchor row into next period (`COST_CALC_007`, `COST_POST_008`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #5–6; FIN-HP-04–05](/en/inventory/costing/04-test-scenarios) |
| 10 | Costing method configuration — BU-level FIFO↔WA; blocked on non-zero on-hand (`COST_VAL_009`); change after drain happy path (`COST_AUTH_001`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #7–8; FIN-HP-09](/en/inventory/costing/04-test-scenarios) |
| 11 | Standard-cost management — `tb_product.standard_cost` update; prospective only, no cost-layer effect (`COST_CALC_009`, `COST_POST_010`; `COST_AUTH_003`) | ✅ | ✅ | ✅ | ✅ Done | [cross-persona TS #9; FIN-HP-08](/en/inventory/costing/04-test-scenarios) |
| 12 | Direct-cost location receipt — engine skipped, no cost-layer row written; GL expensed at receipt (`COST_VAL_011`, `COST_POST_005`) | ✅ | 🟡 | ✅ | 🟡 Partial | [cross-persona TS #17; BR §5 COST_POST_005](/en/inventory/costing/04-test-scenarios) |
| 13 | Consignment location receipt — memo cost-layer row flagged; AP and Inventory journal deferred to consumption (`COST_VAL_012`, `COST_POST_006`) | ✅ | 🟡 | ✅ | 🟡 Partial | [cross-persona TS #18; BR §5 COST_POST_006](/en/inventory/costing/04-test-scenarios) |

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
| 28 | Period close blocked by prerequisite hold (in-flight documents / missing Controller sign-off) | ✅ | ✅ | ✅ | ✅ Done | [period-end.md §3; FIN-HP-05; FIN-VAL-03–04; cross-persona TS #6](/en/inventory/inventory/period-end) |
| 29 | Lot-recall chain-of-custody trace (backward GRN + forward consumption — Auditor read-only) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_009; AUD-HP-02; cross-persona TS #13](/en/inventory/inventory/04-test-scenarios-audit-config) |
| 30 | Period-snapshot reconciliation audit query (Auditor verifies ledger sum vs snapshot delta) | ✅ | ✅ | ✅ | ✅ Done | [AUD-HP-03; transaction.md §2](/en/inventory/inventory/04-test-scenarios-audit-config) |
| 31 | Location-type change blocked by non-zero on-hand (`INV_AUTH_008` drain requirement) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 INV_AUTH_008; AUD-VAL-01; cross-persona TS #16](/en/inventory/inventory/04-test-scenarios-audit-config) |
| 32 | Costing-method change blocked by non-zero on-hand (`INV_XMOD_009`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 INV_XMOD_009; AUD-HP-06; AUD-VAL-02](/en/inventory/inventory/04-test-scenarios-audit-config) |
| 33 | Concurrent inbound posts to same lot — append-only, no race condition (`INV_CALC_004`, `INV_CALC_007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 INV_CALC_004; cross-persona TS #9; SK-EDGE-03](/en/inventory/inventory/04-test-scenarios-store-keeper) |
| 34 | Multi-source channel convergence — all modules post via same `tb_inventory_transaction` API (`INV_XMOD_010`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §6 INV_XMOD_010; transaction.md §6](/en/inventory/inventory/transaction) |
| 35 | Inventory transaction log query / audit trail (read-only ledger view, balance derivation check) | ✅ | ✅ | ✅ | ✅ Done | [transaction.md §2–4; AUD-HP-01](/en/inventory/inventory/transaction) |

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
| 6 | Product–location assignment — enable product at location, set min / max / par / reorder policy (`PRD_VAL_012`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PRD_VAL_012; PA-HP-03; PA-VAL-10](/en/inventory/product/02-business-rules) |
| 7 | Vendor mapping — product–vendor join, vendor-product-code cross-reference (`PRD_VAL_013`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 PRD_VAL_013; PA-HP-04; PA-VAL-11](/en/inventory/product/02-business-rules) |
| 8 | Barcode / SKU management — assign barcode, uniqueness guard, barcode-scan lookup by Store Keeper, mismatch comment flow | ✅ | ✅ | ✅ | ✅ Done | [TS — Store Keeper](/en/inventory/product/04-test-scenarios-store-keeper) |
| 9 | Bulk import / export — dry-run preview, partial-success mode, strict-commit, row-level error report (`PRD_LIFE_006/007`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5 PRD_LIFE_006/007; PA-HP-07/08; cross-persona TS #2/3](/en/inventory/product/02-business-rules) |
| 10 | Tax-profile and deviation-tolerance inheritance cascade — item-group → sub-category → category fallback (`PRD_CALC_002/003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §3 PRD_CALC_002/003; UF product-admin §2 step 5; PA-EDGE-02/03](/en/inventory/product/02-business-rules) |
| 11 | Standard-cost management and SoD approval gate — edit, above-threshold routing to Cost Controller / Finance, activity-log record (`PRD_AUTH_012`, `PRD_CALC_008`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 PRD_AUTH_012; UF product-admin §3; PA-HP-09; cross-persona TS #4](/en/inventory/product/02-business-rules) |
| 12 | Audit trail / activity log — every product-master change logged (create, edit, status transition, soft-delete, restore, comment threads) (`PRD_XMOD_011`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 PRD_XMOD_011; cross-persona TS #15; PA-PERM-08/10](/en/inventory/product/04-test-scenarios) |

### 9. Recipe
Source: `../carmen/docs/recipe/` , `../carmen/docs/recipe-module/`

> **Note:** Recipe is a costed formula document (not a workflow document) — three-state lifecycle (`DRAFT → PUBLISHED → ARCHIVED`), RBAC-gated, with `tb_recipe_version` snapshots and `tb_recipe_pricing_history` as the audit trail. BR coverage is via `02-business-rules.md` rule families `REC_VAL_*` / `REC_CALC_*` / `REC_AUTH_*` / `REC_POST_*` / `REC_XMOD_*`. UF coverage is across `03-user-flow.md` (lifecycle state table + persona index) and five per-persona flow pages. TS coverage is across `04-test-scenarios.md` (14 cross-persona scenarios) and five per-persona scenario pages (`chef`, `cost-controller`, `outlet-manager`, `procurement-fb-ops`, `audit-config`). Four support-master pages exist: `category.md`, `cuisine.md`, `equipment.md`, `equipment-category.md`.

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create recipe (`DRAFT`) — required-field validation, code assignment, category/cuisine selection, yield & time, category default-cost inheritance (`REC_VAL_001–008`, `REC_AUTH_001`, `REC_POST_001`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2–§5](/en/inventory/recipe/02-business-rules) |
| 2 | Ingredient line management — add product or sub-recipe lines, qty/unit/wastage, cost-per-unit, UoM conversion, discriminator integrity, cycle detection (`REC_VAL_009–014`, `REC_CALC_001–002`, `REC_AUTH_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2–§3](/en/inventory/recipe/02-business-rules) |
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
| 13 | Preparation steps — add sequential steps (title, description, equipment, temperature, duration, images), reorder, at-publish completeness gate (`REC_VAL_016`, `REC_POST_002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§5; CHEF-HP-02; CHEF-VAL-13](/en/inventory/recipe/02-business-rules) |
| 14 | Versioning and pricing-history audit trail — `tb_recipe_version` full snapshot on every `PUBLISHED` edit; `tb_recipe_pricing_history` on cost/price change; rollback via snapshot re-apply; auditor read-only access (`REC_XMOD_009`, `REC_AUTH_013`) | ✅ | ✅ | ✅ | ✅ Done | [BR §5–§6; CC-EDGE-07/08; AC-HP-06/07; cross-persona TS #11](/en/inventory/recipe/02-business-rules) |
| 15 | RBAC and permission gates — per-role, per-category permission scoping (chef, cost controller, outlet manager, procurement, audit/config); category-scoped chefs; soft-delete authority (`REC_AUTH_001–014`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4; CHEF-PERM-01–07; CC-PERM-01–07; AC-PERM-01–09](/en/inventory/recipe/02-business-rules) |
| 16 | Recipe category master CRUD — hierarchical tree (self-FK `parent_id`), default cost settings seed onto new recipes, reparenting with cycle guard, delete guards, inactive flag | ✅ | 🟡 | 🟡 | 🟡 Partial | [category.md](/en/inventory/recipe/category) |
| 17 | Cuisine master CRUD — flat catalogue with `enum_cuisine_region` anchor, unique-name guard, delete guard, retire/inactive flow | ✅ | 🟡 | 🟡 | 🟡 Partial | [cuisine.md](/en/inventory/recipe/cuisine) |
| 18 | Equipment master CRUD — code + name, category FK, specs, maintenance schedule + dates, station assignment, qty counters, delete guard | ✅ | 🟡 | 🟡 | 🟡 Partial | [equipment.md](/en/inventory/recipe/equipment) |
| 19 | Equipment category master CRUD — flat functional grouping (Preparation, Cooking, Holding, …), name-unique guard, delete guard (app-layer; FK `NoAction`), rename fan-out to denormalised `category_name` | ✅ | 🟡 | 🟡 | 🟡 Partial | [equipment-category.md](/en/inventory/recipe/equipment-category) |
| 20 | Clone recipe — copy header/ingredients/steps/variants into new `DRAFT`, clear `published_at`/`archived_at`, assign new code/name, fresh version chain on first publish | ✅ | ✅ | ✅ | ✅ Done | [CHEF-HP-07; CHEF-EDGE-06](/en/inventory/recipe/04-test-scenarios-chef) |

## Table B — Config / reference modules

_Reference/admin modules. One `###` section per module, added by Tasks 13–18._

## Maintenance notes

- Living doc — update by hand when wiki pages are added/expanded.
- Bump the `(as of …)` date in the Summary heading whenever rows change.
- Re-run Task 19's count when any row status changes.
