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

## Table B — Config / reference modules

_Reference/admin modules. One `###` section per module, added by Tasks 13–18._

## Maintenance notes

- Living doc — update by hand when wiki pages are added/expanded.
- Bump the `(as of …)` date in the Summary heading whenever rows change.
- Re-run Task 19's count when any row status changes.
