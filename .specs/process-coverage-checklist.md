# Carmen Inventory — Process Coverage Checklist

Internal tracker (not a published Wiki.js page). Enumerates every Carmen Inventory
process by module — sourced from `../carmen/docs/` — and records whether the wiki
documents it. Answers: "is the Inventory documentation project finished?".

How to read: each row is a sub-process. **BR/UF/TS** = covered in the module's
`02-business-rules` / `03-user-flow*` / `04-test-scenarios*` page(s).
Symbols: ✅ complete · 🟡 partial/stub · ⬜ missing. See "How status is judged".

## Summary (as of 2026-06-04)

| Module | Sub-processes | Done | Partial | Not yet | % complete |
|--------|--------------:|-----:|--------:|--------:|-----------:|
| Good Receive Note | 18 | 12 | 6 | 0 | 67% |
| Purchase Request | 25 | 22 | 3 | 0 | 88% |
| Purchase Order | 24 | 23 | 1 | 0 | 96% |
| Store Requisition | 25 | 21 | 4 | 0 | 84% |
| Inventory Adjustment | 16 | 12 | 4 | 0 | 75% |
| Costing | 13 | 10 | 3 | 0 | 77% |
| Inventory | 35 | 32 | 3 | 0 | 91% |
| Product | 12 | 11 | 1 | 0 | 92% |
| Recipe | 20 | 16 | 4 | 0 | 80% |
| Vendor Pricelist | 14 | 12 | 2 | 0 | 86% |
| Physical Count | 14 | 0 | 14 | 0 | 0% |
| Spot Check | 13 | 0 | 13 | 0 | 0% |
| Master Data | 14 | 14 | 0 | 0 | 100% |
| System Config | 10 | 10 | 0 | 0 | 100% |
| Dashboard | 9 | 9 | 0 | 0 | 100% |
| Access Control | 6 | 6 | 0 | 0 | 100% |
| Reporting & Audit | 8 | 8 | 0 | 0 | 100% |
| Templates | 2 | 2 | 0 | 0 | 100% |
| **Project total** | 278 | 220 | 58 | 0 | 79% |

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

### 10. Vendor Pricelist
Source: `../carmen/docs/vendor-pricelist-management/`

> **Note:** The module covers a 6-phase price-collection lifecycle — template setup, campaign/RFQ, vendor invitation, vendor portal submission, validation/quality scoring, and pricelist approval — plus downstream price-assignment on PR/PO and GRN variance checking. BR coverage is in `02-business-rules.md` (rule families `VPL_VAL_*` / `VPL_CALC_*` / `VPL_AUTH_*` / `VPL_POST_*` / `VPL_XMOD_*`, ~81 rules). UF is the `03-user-flow.md` lifecycle overview plus four per-persona files (Purchaser, Vendor, Finance, Audit/Config). TS is the `04-test-scenarios.md` cross-persona overview plus four per-persona scenario files — all with Pre-condition / Steps / Expected format. Vendor-master CRUD (Phase 1 in source) is referenced only obliquely in the wiki (VPL_XMOD_007, VPL_AUTH_002); no dedicated page or scenario exists for it.

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Vendor master CRUD — create/edit/deactivate/soft-delete vendor profiles, category assignments, status monitoring, in-use guards on inactive vendor | 🟡 | 🟡 | ⬜ | 🟡 Partial | [BR §4 VPL_AUTH_002; §6 VPL_XMOD_007](/en/inventory/vendor-pricelist/02-business-rules) |
| 2 | Price-collection template create / edit / activate — name uniqueness, product selection (category/subcategory/item-group), MOQ-tier structure, validity-period / reminder schedule, activate/inactivate/re-activate lifecycle (`VPL_VAL_001–007`, `VPL_POST_001–004`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§5.1](/en/inventory/vendor-pricelist/02-business-rules) |
| 3 | Campaign (RFQ) create / launch / pause / cancel — date-window validation, vendor invitation rows, email-template validation, campaign lifecycle states (`VPL_VAL_008–013`, `VPL_POST_005–009`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§5.2; UF §2.2; request-price-list.md](/en/inventory/vendor-pricelist/02-business-rules) |
| 4 | Vendor invitation & secure token dispatch — cryptographic token generation, per-vendor unique link, email delivery, invitation lifecycle (pending → in-progress → submitted → approved/expired) (`VPL_VAL_011–013`, `VPL_AUTH_007`, `VPL_POST_010–014`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4,§5.3; UF §2.3; TS-Vendor HP-01](/en/inventory/vendor-pricelist/02-business-rules) |
| 5 | Vendor portal price submission — online entry, single-page interface, multi-MOQ-tier inline expansion, auto-save, draft/resume, submission (`VPL_VAL_018–023`, `VPL_POST_015–016`, `VPL_AUTH_008`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2,§5.4; TS-Vendor HP-01..06](/en/inventory/vendor-pricelist/04-test-scenarios-vendor) |
| 6 | Excel template download / upload and email submission method — Excel parse/validate, portal upload, email-to-staff upload path (`submission_method = email / portal`), error reporting (`VPL_AUTH_003`, `VPL_VAL_017`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 VPL_AUTH_003; TS-Purchaser HP-06; TS-Vendor HP-04,09](/en/inventory/vendor-pricelist/04-test-scenarios-purchaser) |
| 7 | Multi-currency pricing — vendor chooses submission currency, per-currency storage (no FX mutation), cross-currency comparison via tenant FX rate at report date, Finance Manager co-signoff for multi-currency activation (`VPL_CALC_005`, `VPL_AUTH_008–010`) | ✅ | ✅ | ✅ | ✅ Done | [BR §3 VPL_CALC_005; §4 VPL_AUTH_008-010; TS-Finance HP-01; X-VPL-03](/en/inventory/vendor-pricelist/02-business-rules) |
| 8 | Price validity periods — effective-from / effective-to validation, auto-expire cron (`active → expired`), re-activate within window, validity countdown display (`VPL_VAL_016`, `VPL_CALC_007`, `VPL_POST_020–021`) | ✅ | ✅ | ✅ | ✅ Done | [BR §2 VPL_VAL_016; §5.4 VPL_POST_021; TS-Purchaser VAL-09; EDGE-04; X-VPL-08](/en/inventory/vendor-pricelist/02-business-rules) |
| 9 | Pricelist approval workflow — review queue, approve (below/above high-value threshold), reject with reason + resubmit, multi-currency co-signoff, segregation of duties gate (`VPL_AUTH_004–006`, `VPL_AUTH_010,014`, `VPL_POST_017–018`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4,§5.4; TS-Purchaser HP-03,05,08; PERM-03..09; X-VPL-02,03,04](/en/inventory/vendor-pricelist/04-test-scenarios-purchaser) |
| 10 | Price comparison / selection on PR — preferred-vendor flag management (one-per-cell invariant), price-assignment engine (business-rules engine, confidence scoring, fallback hierarchy), PR-line default from active pricelist (`VPL_XMOD_001–002`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 VPL_XMOD_001-002; TS-Purchaser HP-04; X-VPL-01](/en/inventory/vendor-pricelist/02-business-rules) |
| 11 | GRN price-variance check — unit-price comparison on GRN posting, variance tolerance gate, variance categorisation (within-tolerance / vendor-over-bill / pricelist-out-of-date / FX-only), downstream AP / Finance action (`VPL_XMOD_005`) | ✅ | ✅ | ✅ | ✅ Done | [BR §6 VPL_XMOD_005; TS-Finance HP-02..06; X-VPL-06](/en/inventory/vendor-pricelist/04-test-scenarios-finance) |
| 12 | Data validation & quality scoring — real-time field-level validation, MOQ-tier non-increasing rule, completeness checks, quality-score computation and threshold routing to Manager (`VPL_CALC_006`, `VPL_VAL_018–025`, `VPL_XMOD_009`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2–§3 VPL_CALC_006; §6 VPL_XMOD_009; TS X-VPL-09; TS-Purchaser HP-03](/en/inventory/vendor-pricelist/02-business-rules) |
| 13 | Portal token policy / session security — token expiry, IP-allowlist enforcement, concurrent-session limits, token revocation by Sysadmin/Manager, suspicious-activity detection (`VPL_AUTH_007`, `VPL_AUTH_012`, `VPL_AUTH_015`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4 VPL_AUTH_007,012,015; TS-Vendor VAL-01..03; EDGE-04; TS-AuditConfig HP-08; X-VPL-07](/en/inventory/vendor-pricelist/04-test-scenarios-audit-config) |
| 14 | Audit trail & RBAC — activity-log writes on every status transition and comment, full chain traceability (template → campaign → invitation → pricelist → PR/PO/GRN), read-only Auditor surface, Sysadmin configuration-change audit log, data-export approval flow (`VPL_AUTH_001–015`, `VPL_POST_001–022`) | ✅ | ✅ | ✅ | ✅ Done | [BR §4; TS-AuditConfig HP-01..10; PERM-01..08](/en/inventory/vendor-pricelist/04-test-scenarios-audit-config) |

### 11. Physical Count
Source: `../carmen/docs/app/inventory-management/physical-count/` , `../carmen/docs/app/inventory-management/physical-count-management/` , `../carmen/docs/documents/pc/`

> **Note:** The source has two parallel spec folders — `physical-count/` (simpler, single-wizard model) and `physical-count-management/` (richer lifecycle: 8 statuses, mobile-first counting UI, unit calculator, blind-count mode, notes/evidence sheet). The wiki documents the data-model-aligned version (three-tier: `tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`; 3 statuses per level). BR coverage is in `02-business-rules.md` (`PHC_VAL_*` / `PHC_CALC_*` / `PHC_AUTH_*` / `PHC_POST_*` / `PHC_XMOD_*`, ~28 rules + lifecycle discrepancy callouts). UF is the `03-user-flow.md` overview + three per-persona files (Count Lead, Counter, Audit/Config). TS overview (`04-test-scenarios.md`) has 20 cross-persona scenarios with Pre-condition + Expected, and per-persona files add ~30 scenarios each, but **none of the scenario tables include a Steps column** — the rubric requires Pre-condition/Steps/Expected for ✅; all TS cells are therefore 🟡.

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Create count period header — Count Lead opens `tb_physical_count_period` for an open fiscal period; validates `tb_period` is open (`PHC_VAL_001`); period enters `draft` status | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 PHC_VAL_001](/en/inventory/physical-count/02-business-rules) · [UF §2.1](/en/inventory/physical-count/03-user-flow) · [TS-CL CL-F-01](/en/inventory/physical-count/04-test-scenarios-count-lead) |
| 2 | Generate count sheet / snapshot stock — Count Lead creates `tb_physical_count` for `(period, location)`, capturing `on_hand_qty` snapshot per line; validates location type (`PHC_VAL_002`–`PHC_VAL_003`); document enters `pending` | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 PHC_VAL_002–003](/en/inventory/physical-count/02-business-rules) · [UF-CL §3](/en/inventory/physical-count/03-user-flow-count-lead) · [TS-CL CL-F-02,03](/en/inventory/physical-count/04-test-scenarios-count-lead) |
| 3 | Frozen vs live mode selection — `physical_count_type = yes` (frozen) locks inventory writes at location during count (`PHC_VAL_006`); `no` (live) allows parallel GRN/SR; mode immutable once `in_progress` (`PHC_VAL_002`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 PHC_VAL_002,006; §5.1](/en/inventory/physical-count/02-business-rules) · [UF-CL §4](/en/inventory/physical-count/03-user-flow-count-lead) · [TS cross-persona #5,6](/en/inventory/physical-count/04-test-scenarios) |
| 4 | Counter assignment — Count Lead assigns counters to zones; zone-grant scopes counter to `(location, zone)` lines; scope-bound visibility enforced (`PHC_AUTH_004`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 PHC_AUTH_004](/en/inventory/physical-count/02-business-rules) · [UF-CL §3](/en/inventory/physical-count/03-user-flow-count-lead) · [TS-CL CL-F-04; TS-C C-R-01,C-R-04](/en/inventory/physical-count/04-test-scenarios-count-lead) |
| 5 | Count entry (counter) — Counter enters `actual_qty` on own-zone lines; first entry auto-transitions document to `in_progress`; stamps `start_counting_at` / `start_counting_by_id`; `actual_qty ≥ 0` enforced (`PHC_VAL_005`); progress tracked (`PHC_CALC_004`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 PHC_VAL_004–005; §3 PHC_CALC_004](/en/inventory/physical-count/02-business-rules) · [UF-Counter §3](/en/inventory/physical-count/03-user-flow-counter) · [TS-C C-F-01..09](/en/inventory/physical-count/04-test-scenarios-counter) |
| 6 | Variance calculation — `diff_qty = actual_qty − on_hand_qty` per line (`PHC_CALC_001`); `variance_% = diff_qty / on_hand_qty × 100` (`PHC_CALC_002`); `variance_value = diff_qty × cost_per_unit` per costing-method (`PHC_CALC_003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §3 PHC_CALC_001–003](/en/inventory/physical-count/02-business-rules) · [UF §2.3](/en/inventory/physical-count/03-user-flow) · [TS cross-persona #7,8,9](/en/inventory/physical-count/04-test-scenarios) |
| 7 | Recount escalation — variance breach per tolerance threshold (`PHC_VAL_007`) blocks submit; Count Lead flags line for recount by a **different** counter; recount-and-reconcile or override required before submit | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 PHC_VAL_007](/en/inventory/physical-count/02-business-rules) · [UF-CL §3](/en/inventory/physical-count/03-user-flow-count-lead) · [TS cross-persona #3,4; TS-C C-E-01](/en/inventory/physical-count/04-test-scenarios) |
| 8 | Override / accept variance — Count Lead countersignature clears recount flag and accepts residual variance; comment-thread carries justification stamped with `created_by_id` (`PHC_AUTH_001`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 PHC_AUTH_001](/en/inventory/physical-count/02-business-rules) · [UF-CL §3](/en/inventory/physical-count/03-user-flow-count-lead) · [TS-CL CL-F-07](/en/inventory/physical-count/04-test-scenarios-count-lead) |
| 9 | Count submission — Count Lead submits when all lines counted (`product_counted == product_total`, `PHC_VAL_004`) and no open recount flags; document transitions `in_progress → completed`; fires variance rollup (`PHC_POST_001`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 PHC_VAL_004; §5 PHC_POST_001](/en/inventory/physical-count/02-business-rules) · [UF §2.2](/en/inventory/physical-count/03-user-flow) · [TS-CL CL-F-08; cross-persona #1](/en/inventory/physical-count/04-test-scenarios-count-lead) |
| 10 | Variance rollup / post adjustment — completed count fans out overage lines → `tb_stock_in` (reason `COUNT_OVERAGE`) and shortage lines → `tb_stock_out` (reason `COUNT_SHORTAGE`); each rollup carries `info.countId` back-reference (`PHC_POST_001`–`PHC_POST_003`); zero-diff lines produce no rollup | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 PHC_POST_001–003](/en/inventory/physical-count/02-business-rules) · [UF §2.3](/en/inventory/physical-count/03-user-flow) · [TS cross-persona #9; TS-CL CL-C-03](/en/inventory/physical-count/04-test-scenarios) |
| 11 | Approve & post adjustment — Approver / Finance reviews rollup `tb_stock_in` / `tb_stock_out` via inventory-adjustment approval queue; approves (writes `tb_inventory_transaction`) or rejects back to Count Lead; SoD enforced (approver ≠ count submitter) (`PHC_AUTH_003`, `PHC_POST_003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 PHC_AUTH_003; §5 PHC_POST_003](/en/inventory/physical-count/02-business-rules) · [UF-Audit §3](/en/inventory/physical-count/03-user-flow-audit-config) · [TS-AC AC-F-02,03; AC-R-04](/en/inventory/physical-count/04-test-scenarios-audit-config) |
| 12 | Period-close gate — `tb_physical_count_period.status` auto-transitions `counting → completed` when all child counts reach `completed`; period close (Stage 3) blocked until rollup adjustments are `completed` in inventory-adjustment (`PHC_VAL_001`, `BR-PE-005`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5.1 discrepancy callout](/en/inventory/physical-count/02-business-rules) · [UF §2.1](/en/inventory/physical-count/03-user-flow) · [TS cross-persona #18; TS-AC AC-C-04](/en/inventory/physical-count/04-test-scenarios) |
| 13 | Audit trail & full-chain inspection — Auditor reads count sheet → recount records → approvals → posted adjustments → `tb_inventory_transaction` with no gaps; all status changes and comment threads carry `created_by_id` / `counted_by_id` stamps (`PHC_AUTH_003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 PHC_AUTH_003](/en/inventory/physical-count/02-business-rules) · [UF-Audit §3](/en/inventory/physical-count/03-user-flow-audit-config) · [TS-AC AC-F-04,05; AC-C-03; cross-persona #17](/en/inventory/physical-count/04-test-scenarios-audit-config) |
| 14 | Sysadmin configuration — configure variance tolerance threshold (`PHC_VAL_007`), default `enum_physical_count_costing_method` (`standard` / `last` / `average` / `last_receiving`), reason-code mapping (`COUNT_OVERAGE` / `COUNT_SHORTAGE` → GL account) (`PHC_AUTH_003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 PHC_AUTH_003; §3 PHC_CALC_003](/en/inventory/physical-count/02-business-rules) · [UF-Audit §3 Sysadmin](/en/inventory/physical-count/03-user-flow-audit-config) · [TS-AC AC-F-06,07,08](/en/inventory/physical-count/04-test-scenarios-audit-config) |

### 12. Spot Check
Source: `../carmen/docs/inventory-management/period-end-process.md` (passing reference only — no dedicated SPC docs folder exists); rule authority is the wiki's own `02-business-rules.md` (`SPC_VAL_*` / `SPC_CALC_*` / `SPC_AUTH_*` / `SPC_POST_*` / `SPC_XMOD_*`, ~30 rules).

> **Note:** No carmen/docs source folder for spot-check exists; the BRD is captured via `tx-10-spot-check.md` (referenced in `02-business-rules.md` § 5.1). The wiki documents a flat two-tier tree (`tb_spot_check` → `tb_spot_check_detail`; no period parent). BR coverage is `02-business-rules.md` (~30 rules + 4 schema-vs-BRD discrepancy callouts). UF is the `03-user-flow.md` overview + three per-persona files (Inventory Controller, Counter, Audit / Config). TS covers `04-test-scenarios.md` (20 cross-persona rows) + three per-persona files (~78 scenarios total), but **none of the TS tables include a Steps column** — per the rubric, all TS cells are therefore 🟡. No E2E Playwright spec exists.

| # | Sub-process | BR | UF | TS | Status | Doc link |
|---|-------------|----|----|----|--------|----------|
| 1 | Spot-check creation — Inventory Controller opens `tb_spot_check` for an inventory- or consignment-type location; direct-cost locations rejected (`SPC_VAL_001`); `method` and `size` validated (`SPC_VAL_002`); `on_hand_qty` snapshot captured per detail line; document enters `pending` | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 SPC_VAL_001–002](/en/inventory/spot-check/02-business-rules) · [UF-IC §3](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS-IC IC-F-01; IC-V-01,02](/en/inventory/spot-check/04-test-scenarios-inventory-controller) |
| 2 | Item selection — random sampling (`method = random`, system picks `size` distinct products), high-value sampling (`method = high_value`, top-`size` by value/velocity), or manual selection (Inventory Controller adds specific product lines explicitly) (`SPC_VAL_002`–`SPC_VAL_003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 SPC_VAL_002–003](/en/inventory/spot-check/02-business-rules) · [UF-IC §3](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS-IC IC-F-01,02,03; cross-persona #2,3](/en/inventory/spot-check/04-test-scenarios) |
| 3 | Counter assignment — Inventory Controller assigns Counter(s) to the spot check; Counter visibility bounded by `tb_user_location` location-grant (`SPC_AUTH_004`); Inventory Controller can re-assign mid-check | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 SPC_AUTH_001,004](/en/inventory/spot-check/02-business-rules) · [UF-IC §3](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS-IC IC-F-04; C-R-01,04; IC-C-01](/en/inventory/spot-check/04-test-scenarios-inventory-controller) |
| 4 | Count entry (Counter) — Counter enters `actual_qty` per assigned line; first entry auto-transitions document to `in_progress`; `actual_qty ≥ 0` enforced (`SPC_VAL_005`); `counted_at` / `counted_by_id` stamped; Counter may flag damaged / unlabelled items via `tb_spot_check_detail_comment` | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 SPC_VAL_004–005; §4 SPC_AUTH_002](/en/inventory/spot-check/02-business-rules) · [UF-Counter §3](/en/inventory/spot-check/03-user-flow-counter) · [TS-Counter C-F-01..10; C-V-01,02](/en/inventory/spot-check/04-test-scenarios-counter) |
| 5 | Variance calculation — `diff_qty = actual_qty − on_hand_qty` per line (`SPC_CALC_001`); `variance_% = diff_qty / on_hand_qty × 100` (`SPC_CALC_002`); `variance_value = diff_qty × cost_per_unit` (`SPC_CALC_003`); zero-diff lines produce no rollup | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §3 SPC_CALC_001–003](/en/inventory/spot-check/02-business-rules) · [UF §2.2](/en/inventory/spot-check/03-user-flow) · [TS cross-persona #6,7,8](/en/inventory/spot-check/04-test-scenarios) |
| 6 | Recount escalation — variance breach per tolerance threshold (`SPC_VAL_006`) blocks submit; Inventory Controller flags line for recount (ideally by a different Counter); document stays `in_progress` until recount flags are resolved | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 SPC_VAL_006](/en/inventory/spot-check/02-business-rules) · [UF-IC §3,§4 decision points](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS-IC IC-F-06; cross-persona #4,5,6](/en/inventory/spot-check/04-test-scenarios) |
| 7 | Override / accept variance — Inventory Controller countersignature clears recount flag and accepts residual variance; justification comment stamped with `created_by_id` (`SPC_AUTH_001`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 SPC_AUTH_001](/en/inventory/spot-check/02-business-rules) · [UF-IC §3](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS-IC IC-F-07; cross-persona #5](/en/inventory/spot-check/04-test-scenarios-inventory-controller) |
| 8 | Submit & variance rollup — Inventory Controller submits when all lines have `actual_qty` (`SPC_VAL_004`) and no open recount flags; `doc_status = in_progress → completed`; overage lines fan out to `tb_stock_in` (reason `SPOT_CHECK_OVERAGE`), shortage to `tb_stock_out` (`SPOT_CHECK_SHORTAGE`); each rollup carries `info.spotCheckId` (`SPC_POST_001`–`SPC_POST_002`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 SPC_POST_001–002](/en/inventory/spot-check/02-business-rules) · [UF §2.1 / §2.2](/en/inventory/spot-check/03-user-flow) · [TS-IC IC-F-08; cross-persona #1,8](/en/inventory/spot-check/04-test-scenarios-inventory-controller) |
| 9 | Rollup adjustment approval — Inventory Controller routes rollup `tb_stock_in` / `tb_stock_out` to Approver / Finance via [inventory-adjustment](/en/inventory/inventory-adjustment); SoD enforced (approver ≠ spot-check submitter); approval writes `tb_inventory_transaction` (`SPC_POST_003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5 SPC_POST_003](/en/inventory/spot-check/02-business-rules) · [UF-IC §5 exit/handoff](/en/inventory/spot-check/03-user-flow-inventory-controller) · [TS-AC AC-R-04; cross-persona #1,14,15](/en/inventory/spot-check/04-test-scenarios-audit-config) |
| 10 | Void / cancel — `pending` or `in_progress` spot check can be voided by Inventory Controller (`SPC_VAL_008`); `completed` spot check cannot be voided — correction requires a fresh spot check or manual `tb_stock_in` / `tb_stock_out` (`SPC_POST_004`); no rollup triggered on void | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2 SPC_VAL_007–008; §5 SPC_POST_004](/en/inventory/spot-check/02-business-rules) · [UF §2.1 void branch](/en/inventory/spot-check/03-user-flow) · [TS-IC IC-F-10,11; IC-V-07; cross-persona #18; AC-E-05](/en/inventory/spot-check/04-test-scenarios-inventory-controller) |
| 11 | Period-close gate — all `tb_spot_check` documents must be `completed` (or `void`) before End Period Close Stage 2 passes (BR-PE-006 on the period-end side); `void` cancels do **not** satisfy the gate; no `tb_spot_check_period` parent exists (flat structure, no period-level rollup) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §5.1 SPC_POST_001 / BR-PE-006 callout](/en/inventory/spot-check/02-business-rules) · [UF §2 completed note](/en/inventory/spot-check/03-user-flow) · [TS cross-persona #13](/en/inventory/spot-check/04-test-scenarios) |
| 12 | Audit trail & full-chain inspection — Auditor reads spot-check sheet → recount records → approvals → posted adjustments → `tb_inventory_transaction` with no gaps; SoD verified (submitter ≠ approver); `counted_by_id` / `created_by_id` stamps on every line and comment (`SPC_AUTH_003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 SPC_AUTH_003](/en/inventory/spot-check/02-business-rules) · [UF-Audit §3](/en/inventory/spot-check/03-user-flow-audit-config) · [TS-AC AC-F-02,03; AC-C-03; cross-persona #15](/en/inventory/spot-check/04-test-scenarios-audit-config) |
| 13 | Sysadmin configuration — configure variance tolerance threshold (`SPC_VAL_006`), default sample `size`, default `method` (`enum_spot_check_method`), and reason-code mapping (`SPOT_CHECK_OVERAGE` / `SPOT_CHECK_SHORTAGE` → GL account) (`SPC_AUTH_003`) | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §4 SPC_AUTH_003; §2 SPC_VAL_006](/en/inventory/spot-check/02-business-rules) · [UF-Audit §3 Sysadmin](/en/inventory/spot-check/03-user-flow-audit-config) · [TS-AC AC-F-04,05,06,07](/en/inventory/spot-check/04-test-scenarios-audit-config) |

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
| 9 | Extra Cost Type | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/extra-cost-type) |
| 10 | Location | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/location) |
| 11 | Tax Profile | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/tax-profile) |
| 12 | Unit | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/unit) |
| 13 | Vendor | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/vendor) |
| 14 | Vendor Business Type (`tb_vendor_business_type`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/master-data/vendor-business-type) |

### 14. System Config
Source: `../carmen/docs/settings/` , `../carmen/docs/app/system-administration/`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | Application Config | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/application-config) |
| 2 | Email Configuration | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/config-email) |
| 3 | Dimension | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/dimension) |
| 4 | Document Management | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/document) |
| 5 | Menu | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/menu) |
| 6 | Period | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/period) |
| 7 | Query Dataset (SQL Workbench) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/query-dataset) |
| 8 | Running Code | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/running-code) |
| 9 | Workflow | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/workflow) |
| 10 | Dashboard Dataset (`tb_widget_workspace`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/system-config/dashboard-dataset) |

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
| 7 | Widget workspace dashboard (current `/dashboard` route — drag-and-drop `tb_widget_workspace` tiles, add/remove/reorder KPI/pie/bar widgets from Dataset catalogue) | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/widget-workspace) |
| 8 | My Pending widget (PR / PO / SR pending-count tiles for the signed-in user — `dashboard-my-pending.tsx`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/my-pending) |
| 9 | My Approval widget (approval task queue by doc type across PR / PO / SR — `dashboard-my-approval.tsx`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/dashboard/my-approval) |

### 16. Access Control
Source: `../carmen/docs/security/` , `../carmen/docs/app/system-administration/permission-management/` , `../carmen/docs/app/system-administration/user-management/` , `../carmen/docs/prisma-schema/schema.prisma`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | User (`tb_user`, `tb_user_profile`, `tb_user_login_session`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/user) |
| 2 | Application Role (`tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/application-role) |
| 3 | Permission (`tb_permission`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/permission) |
| 4 | Business Unit User (`tb_user_tb_business_unit`, `tb_temp_bu_user`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/business-unit-user) |
| 5 | User Location (`tb_user_location`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/user-location) |
| 6 | Department User (`tb_department_user` — user ↔ department pivot with `is_hod` HOD flag; exists in `schema.prisma` and referenced in `DD-permission-management.md` / `DD-user-management.md`) | ✅ | ✅ | ✅ Done | [link](/en/inventory/access-control/department-user) |

### 17. Reporting & Audit
Source: `../carmen/docs/reports/` , `../carmen/docs/app/system-administration/notification-preferences/` , `../carmen/docs/app/system-administration/monitoring/`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | Activity (`tb_activity`, `enum_activity_action`) — tenant-wide append-only audit log | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/activity) |
| 2 | Attachment (`tb_attachment`) — S3-backed binary metadata, polymorphic linkage | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/attachment) |
| 3 | Report History (`tb_report_job`) — append-only execution log for every report run | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/history) |
| 4 | Notification (`tb_notification`, `tb_message_format`, `tb_news`) — inbound message pipe, templates, platform bulletins | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/notification) |
| 5 | Report (`tb_report_job`, `tb_report_schedule`, `tb_report_template`, `tb_print_template_mapping`) — full report generation pipeline | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/report) |
| 6 | Report Schedule (`tb_report_schedule`) — cron-driven recurring report runs | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/schedule) |
| 7 | User Activity (`tb_user_login_session` + `tb_activity` projection) — actor-centric forensic login/logout timeline | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/user-activity) |
| 8 | Widget (`tb_widget_dashboard`, `tb_widget_default_layout`, `tb_widget_workspace`) — dashboard tiles, seed layouts, saved queries | ✅ | ✅ | ✅ Done | [link](/en/inventory/reporting-audit/widget) |

### 18. Templates
Source: `../carmen/docs/app/vendor-management/pricelist-templates/` , `../carmen/docs/purchase-request-management/`

| # | Page / entity | Page exists? | Content complete? | Status | Link |
|---|---------------|--------------|-------------------|--------|------|
| 1 | Price List Template (`tb_pricelist_template`) — RFQ-round scaffold: currency, validity, reminder schedule, escalation | ✅ | ✅ | ✅ Done | [link](/en/inventory/templates/price-list) |
| 2 | Purchase Request Template (`tb_purchase_request_template` + detail + comment) — reusable PR line-bundle cloned into new PRs | ✅ | ✅ | ✅ Done | [link](/en/inventory/templates/purchase-request) |

## Maintenance notes

- Living doc — update by hand when wiki pages are added/expanded.
- Bump the `(as of …)` date in the Summary heading whenever rows change.
- Re-run Task 19's count when any row status changes.
