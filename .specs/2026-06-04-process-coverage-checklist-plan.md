# Process Coverage Checklist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and populate `.specs/process-coverage-checklist.md`, an internal living tracker that lists every Carmen Inventory process by module and records wiki documentation coverage, answering "is the project finished?".

**Architecture:** A single plain-markdown file. One scaffold task creates the skeleton; one task per module audits that module (enumerate sub-processes from `../carmen/docs/`, cross-check the wiki, fill the table); a final task computes the roll-up summary. No code, no test suite (this repo has none) — the "test" for each task is a verification grep plus a structural check.

**Tech Stack:** Markdown only. Tools: `find`, `grep`, `ls`, the Read tool, `git`. Source of truth: `../carmen/docs/` (verified present) and the existing wiki pages under `en/inventory/`.

---

## Adaptation note (read first)

This is a **documentation-audit** deliverable, not code. The writing-plans TDD loop is adapted as follows for every module task:

**The Audit Procedure (S1–S5)** — every module task runs these exact steps with module-specific inputs given in the task:

- **S1 — Enumerate (source):** Read the listed `../carmen/docs/<folder>/` files (start with `*Overview*`, `*prd*`, `*process*`, `README`). Write down the discrete **sub-processes / scenarios** the module should support. A sub-process is a distinct business action or branch (e.g. "partial receipt", "over-receipt", "return / credit note"), not a UI field.
- **S2 — Cross-check (wiki):** For each sub-process, grep the module's wiki pages to decide BR/UF/TS coverage. Template commands (replace `<mod>`):
  ```bash
  grep -niE '<keyword>' en/inventory/<mod>/02-business-rules.md
  grep -rniE '<keyword>' en/inventory/<mod>/03-user-flow*.md
  grep -rniE '<keyword>' en/inventory/<mod>/04-test-scenarios*.md
  ```
  Mark each cell `✅` (usable section exists), `🟡` (mentioned but stub/incomplete), `⬜` (not found). See rubric §6 of the design.
- **S3 — Write the section:** Add the module's `###` heading, `Source:` line, and the filled table to the file, in the correct table (A or B). Set the row **Status** from the rubric (✅ all-cells-✅ / 🟡 some / ⬜ none). Fill **Doc link** with an absolute-URL markdown link to the most relevant page or section anchor (e.g. `/en/inventory/good-receive-note/02-business-rules`), `—` if none.
- **S4 — Verify:** Run the verification grep in the task (confirms the section was written and link targets exist). Confirm every row has a Status and the cell symbols are from `{✅,🟡,⬜}` only.
- **S5 — Commit:** One commit per module.

Each task below gives the module-specific inputs (source folder, wiki page glob, sub-process hunting hints) and a tailored verify + commit. The procedure body is identical by design — run S1–S5 above.

**Design reference:** `.specs/2026-06-04-process-coverage-checklist-design.md`. Read §5 (file structure), §6 (rubric), §7 (source mapping) before starting.

---

## File Structure

- **Create:** `.specs/process-coverage-checklist.md` — the entire deliverable (one file, plain markdown, English, no Wiki.js frontmatter).
- **Read-only inputs:** `../carmen/docs/**` (source of "should-exist" processes), `en/inventory/**` (existing wiki pages to grade).
- No other files are created or modified.

---

## Task 0: Scaffold the checklist file

**Files:**
- Create: `.specs/process-coverage-checklist.md`

- [ ] **Step 1: Create the file with the full skeleton**

Write exactly this content (tables empty except headers; summary/source-mapping filled later):

````markdown
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

## Table B — Config / reference modules

_Reference/admin modules. One `###` section per module, added by Tasks 13–18._

## Maintenance notes

- Living doc — update by hand when wiki pages are added/expanded.
- Bump the `(as of …)` date in the Summary heading whenever rows change.
- Re-run Task 19's count when any row status changes.
````

- [ ] **Step 2: Verify the file exists and headings are present**

Run:
```bash
grep -nE '^(#|##) ' .specs/process-coverage-checklist.md
```
Expected: lines for the H1 title, `## Summary`, `## How status is judged`, `## Source mapping`, `## Table A — Process modules`, `## Table B — Config / reference modules`, `## Maintenance notes`.

- [ ] **Step 3: Commit**

```bash
git add .specs/process-coverage-checklist.md
git commit -m "docs(.specs): scaffold process coverage checklist"
```

---

## Table A tasks (process modules)

Each task: run **Audit Procedure S1–S5** with the inputs below. Append the module's `###` section under `## Table A — Process modules`, numbered in order (`### 1.`, `### 2.`, …). Use the row format from design §5.2:

```
| # | Sub-process | BR | UF | TS | Status | Doc link |
```

### Task 1: Audit Good Receive Note

**Files:**
- Modify: `.specs/process-coverage-checklist.md` (append `### 1. Good Receive Note`)

**Inputs:**
- Source: `../carmen/docs/good-recive-note-managment/` — read `GRN-Overview.md`, `grn-master-prd.md`, `grn-create-process-doc.md`, `GRN-User-Flow-Diagram.md`.
- Wiki pages: `en/inventory/good-receive-note/02-business-rules.md`, `03-user-flow*.md`, `04-test-scenarios*.md`.
- Sub-process hints to confirm/expand from source: receive against PO, direct/manual GRN, partial receipt, over-/under-receipt, FOC items, extra costs allocation, tax handling, returns / credit note, posting to inventory, status lifecycle (draft→committed).

- [ ] **Step 1 (S1): Enumerate sub-processes from source** — read the four source files; list the module's sub-processes.
- [ ] **Step 2 (S2): Cross-check wiki coverage** — for each sub-process:
  ```bash
  grep -niE 'partial|over-receipt|credit note|extra cost|foc|posting|return' en/inventory/good-receive-note/02-business-rules.md
  grep -rniE 'partial|over-receipt|credit note|extra cost|foc|posting|return' en/inventory/good-receive-note/03-user-flow*.md en/inventory/good-receive-note/04-test-scenarios*.md
  ```
- [ ] **Step 3 (S3): Write `### 1. Good Receive Note`** section (heading, `Source: ../carmen/docs/good-recive-note-managment/`, filled table).
- [ ] **Step 4 (S4): Verify**
  ```bash
  grep -nA40 '^### 1\. Good Receive Note' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'
  ```
  Expected: a non-zero count equal to (rows × cells filled). Confirm each Doc link path exists: `ls en/inventory/good-receive-note/02-business-rules.md`.
- [ ] **Step 5 (S5): Commit**
  ```bash
  git add .specs/process-coverage-checklist.md
  git commit -m "docs(.specs): coverage audit — good-receive-note"
  ```

### Task 2: Audit Purchase Request

**Inputs:**
- Source: `../carmen/docs/purchase-request-management/` — read `PR-Overview.md`, `purchase-request-module-prd.md`, `purchase-request-ba.md`, `module-map.md`.
- Wiki: `en/inventory/purchase-request/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`.
- Sub-process hints: create PR (blank/from template), add items, budget check, multi-stage approval routing, approve/reject/return, delegate approval (`my-approval`), convert PR→PO, amend/cancel.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'approv|reject|return|template|budget|convert|delegat|cancel|amend' en/inventory/purchase-request/02-business-rules.md en/inventory/purchase-request/03-user-flow*.md en/inventory/purchase-request/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 2. Purchase Request`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 2\. Purchase Request' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** `git commit -am "docs(.specs): coverage audit — purchase-request"` (after `git add`).

### Task 3: Audit Purchase Order

**Inputs:**
- Source: `../carmen/docs/purchase-order-management/` — read `*Overview*`, `*prd*`, `*ba*`, `README.md`.
- Wiki: `en/inventory/purchase-order/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`.
- Sub-process hints: create PO (from PR / blank), send to vendor, vendor acknowledgement, amend PO, partial vs full delivery linkage to GRN, credit note (`credit-note.md`), close/cancel PO.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'vendor|acknowledg|amend|deliver|credit note|close|cancel|from pr' en/inventory/purchase-order/02-business-rules.md en/inventory/purchase-order/03-user-flow*.md en/inventory/purchase-order/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 3. Purchase Order`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 3\. Purchase Order' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — purchase-order`.

### Task 4: Audit Store Requisition

**Inputs:**
- Source: `../carmen/docs/store-requisitions/` — read `*Overview*`, `*prd*`, `*ba*`, `README.md`.
- Wiki: `en/inventory/store-requisition/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`, plus `stock-replenishment.md`.
- Sub-process hints: create SR, approval routing, fulfil/issue stock, partial fulfilment, receive at destination, inter-location transfer, stock replenishment trigger, cancel.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'approv|fulfil|issue|partial|transfer|replenish|receive|cancel' en/inventory/store-requisition/02-business-rules.md en/inventory/store-requisition/03-user-flow*.md en/inventory/store-requisition/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 4. Store Requisition`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 4\. Store Requisition' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — store-requisition`.

### Task 5: Audit Inventory Adjustment

**Inputs:**
- Source: `../carmen/docs/inventory-adjustment/` — read `*Overview*`, `*prd*`, `README.md`.
- Wiki: `en/inventory/inventory-adjustment/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`, plus `wastage-reporting.md`.
- Sub-process hints: increase adjustment, decrease adjustment, adjustment types/reasons, wastage reporting, valuation impact, approval, posting.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'increase|decrease|wastage|reason|adjustment type|valuation|approv|posting' en/inventory/inventory-adjustment/02-business-rules.md en/inventory/inventory-adjustment/03-user-flow*.md en/inventory/inventory-adjustment/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 5. Inventory Adjustment`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 5\. Inventory Adjustment' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — inventory-adjustment`.

### Task 6: Audit Costing

**Inputs:**
- Source: `../carmen/docs/costing/enhanced-costing-engine.md` (+ scan `../carmen/docs/costing/` for others).
- Wiki: `en/inventory/costing/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`, plus `calculation-methods.md`, `01-data-model.md`.
- Sub-process hints: FIFO costing, weighted-average costing, cost on receipt, cost on issue, revaluation, period close cost roll, negative-stock costing edge case.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'fifo|weighted|average|revaluat|on issue|on receipt|negative|period' en/inventory/costing/02-business-rules.md en/inventory/costing/03-user-flow*.md en/inventory/costing/04-test-scenarios*.md en/inventory/costing/calculation-methods.md`
- [ ] **Step 3 (S3):** Write `### 6. Costing`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 6\. Costing' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — costing`.

### Task 7: Audit Inventory (stock ledger)

**Inputs:**
- Source: `../carmen/docs/inventory-management/` — read `*Overview*`, `*prd*`, README, and files referencing transactions/period-end.
- Wiki: `en/inventory/inventory/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`, plus `transaction.md`, `period-end.md`.
- Sub-process hints: stock-in/stock-out transactions, transaction types, on-hand calculation, period-end close, opening/closing balance, stock card/ledger query, multi-location stock.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'transaction|on-hand|period|close|balance|ledger|stock card|location' en/inventory/inventory/02-business-rules.md en/inventory/inventory/03-user-flow*.md en/inventory/inventory/04-test-scenarios*.md en/inventory/inventory/transaction.md en/inventory/inventory/period-end.md`
- [ ] **Step 3 (S3):** Write `### 7. Inventory`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 7\. Inventory' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — inventory`.

### Task 8: Audit Product

**Inputs:**
- Source: `../carmen/docs/product-management/` — read `*Overview*`, `*prd*`, README.
- Wiki: `en/inventory/product/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`, plus `category.md`.
- Sub-process hints: create/edit product, product categories, units & conversions, product status/lifecycle, assign to locations, barcode/SKU, inventory vs non-inventory item.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'category|unit|conversion|status|location|barcode|sku|inventory item' en/inventory/product/02-business-rules.md en/inventory/product/03-user-flow*.md en/inventory/product/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 8. Product`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 8\. Product' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — product`.

### Task 9: Audit Recipe

**Inputs:**
- Source: `../carmen/docs/recipe/` and `../carmen/docs/recipe-module/` — read `*Overview*`, `*prd*`, README.
- Wiki: `en/inventory/recipe/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`, plus `category.md`, `cuisine.md`, `equipment.md`, `equipment-category.md`.
- Sub-process hints: create recipe, ingredients & yields, recipe costing roll-up, sub-recipe nesting, recipe categories/cuisine, equipment assignment, portion/scaling.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'ingredient|yield|cost|sub-recipe|cuisine|equipment|portion|scal' en/inventory/recipe/02-business-rules.md en/inventory/recipe/03-user-flow*.md en/inventory/recipe/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 9. Recipe`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 9\. Recipe' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — recipe`.

### Task 10: Audit Vendor Pricelist

**Inputs:**
- Source: `../carmen/docs/vendor-pricelist-management/` — read `*Overview*`, `*prd*`, README.
- Wiki: `en/inventory/vendor-pricelist/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`, plus `request-price-list.md`.
- Sub-process hints: request price list from vendor, vendor submits prices, price list approval, price validity periods, multi-currency pricing, price comparison/selection on PR/PO, expiry handling.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'request|submit|approv|validity|currency|compar|expir|price' en/inventory/vendor-pricelist/02-business-rules.md en/inventory/vendor-pricelist/03-user-flow*.md en/inventory/vendor-pricelist/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 10. Vendor Pricelist`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 10\. Vendor Pricelist' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — vendor-pricelist`.

### Task 11: Audit Physical Count

**Inputs:**
- Source: `../carmen/docs/inventory-management/` + `../carmen/docs/use-cases/` + `../carmen/docs/features/` — search for "physical count" / "stock take".
  ```bash
  grep -rliE 'physical count|stock[- ]take|stocktake' ../carmen/docs/inventory-management ../carmen/docs/use-cases ../carmen/docs/features
  ```
- Wiki: `en/inventory/physical-count/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`.
- Sub-process hints: create count plan, freeze/snapshot stock, count entry (counter), recount, variance review (count lead), approve & post adjustment, full vs cycle count, audit config.

- [ ] **Step 1 (S1):** Enumerate from source (use the grep above to find files).
- [ ] **Step 2 (S2):** `grep -rniE 'plan|freeze|snapshot|count|recount|variance|approv|post|cycle' en/inventory/physical-count/02-business-rules.md en/inventory/physical-count/03-user-flow*.md en/inventory/physical-count/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 11. Physical Count`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 11\. Physical Count' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — physical-count`.

### Task 12: Audit Spot Check

**Inputs:**
- Source: same folders as Task 11 — search for "spot check".
  ```bash
  grep -rliE 'spot[- ]check' ../carmen/docs/inventory-management ../carmen/docs/use-cases ../carmen/docs/features
  ```
- Wiki: `en/inventory/spot-check/{02-business-rules,03-user-flow*,04-test-scenarios*}.md`.
- Sub-process hints: initiate spot check, random/targeted item selection, count entry, variance vs system, escalation to full count, approve, audit config.

- [ ] **Step 1 (S1):** Enumerate from source.
- [ ] **Step 2 (S2):** `grep -rniE 'random|select|count|variance|escalat|approv|target' en/inventory/spot-check/02-business-rules.md en/inventory/spot-check/03-user-flow*.md en/inventory/spot-check/04-test-scenarios*.md`
- [ ] **Step 3 (S3):** Write `### 12. Spot Check`.
- [ ] **Step 4 (S4):** `grep -nA40 '^### 12\. Spot Check' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — spot-check`.

---

## Table B tasks (config / reference modules)

Each task appends a `###` section under `## Table B — Config / reference modules`, numbered `### 13.`…`### 18.`, using the design §5.3 row format:

```
| # | Page / entity | Page exists? | Content complete? | Status | Link |
```

**Table B audit variant of S1–S2:** S1 = list the entities/topics the module should cover (from source folder + the existing wiki sub-pages); S2 = for each, check (a) does a wiki `.md` page exist (`ls en/inventory/<mod>/<entity>.md`), (b) is its content non-stub (`wc -l` and a quick Read — a page under ~15 content lines or containing "TODO"/"placeholder" is `🟡`/`⬜`). S3–S5 unchanged.

### Task 13: Audit Master Data

**Inputs:**
- Source: `../carmen/docs/settings/`, `../carmen/docs/prisma-schema/`.
- Existing wiki entity pages (rows): adjustment-type, business-unit, credit-note-reason, credit-term, currency, delivery-point, department, exchange-rate, extra-cost-type, location, tax-profile, unit, vendor.
  ```bash
  ls en/inventory/master-data/*.md
  ```
- Gap check: list entities the source/prisma-schema implies that have **no** wiki page → add as `⬜ Not yet` rows.

- [ ] **Step 1 (S1):** List entities from source + `ls` above.
- [ ] **Step 2 (S2):** For each entity: `test -f en/inventory/master-data/<entity>.md && wc -l en/inventory/master-data/<entity>.md`; Read short ones to judge stub vs complete.
- [ ] **Step 3 (S3):** Write `### 13. Master Data` (rows = entities; columns Page exists?/Content complete?/Status/Link).
- [ ] **Step 4 (S4):** `grep -nA30 '^### 13\. Master Data' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero; spot-check one Link path with `ls`.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — master-data`.

### Task 14: Audit System Config

**Inputs:**
- Source: `../carmen/docs/settings/`, `../carmen/docs/prisma-schema/`.
- Existing wiki pages (rows): application-config, config-email, dimension, document, menu, period, query-dataset, running-code, workflow (`ls en/inventory/system-config/*.md`).
- Gap check: config topics in source with no wiki page → `⬜` rows.

- [ ] **Step 1 (S1):** List config topics from source + `ls`.
- [ ] **Step 2 (S2):** Per page: `wc -l` + Read short ones for stub judgement.
- [ ] **Step 3 (S3):** Write `### 14. System Config`.
- [ ] **Step 4 (S4):** `grep -nA30 '^### 14\. System Config' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — system-config`.

### Task 15: Audit Dashboard

**Inputs:**
- Source: `../carmen/docs/features/`, `../carmen/docs/pages/` — search for "dashboard"/"widget".
- Existing wiki pages (rows): main, grn, inventory, po, pr, sr (`ls en/inventory/dashboard/*.md`).
- Gap check: documented dashboards/widgets in source with no wiki page → `⬜`.

- [ ] **Step 1 (S1):** List dashboard views/widgets from source + `ls`.
- [ ] **Step 2 (S2):** Per page: `wc -l` + Read short ones.
- [ ] **Step 3 (S3):** Write `### 15. Dashboard`.
- [ ] **Step 4 (S4):** `grep -nA30 '^### 15\. Dashboard' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — dashboard`.

### Task 16: Audit Access Control

**Inputs:**
- Source: `../carmen/docs/security/`, `../carmen/docs/settings/` — search for roles/permissions.
- Existing wiki pages (rows): application-role, business-unit-user, permission, user-location, user (`ls en/inventory/access-control/*.md`).
- Gap check: access-control concepts in source with no wiki page → `⬜`.

- [ ] **Step 1 (S1):** List concepts from source + `ls`.
- [ ] **Step 2 (S2):** Per page: `wc -l` + Read short ones.
- [ ] **Step 3 (S3):** Write `### 16. Access Control`.
- [ ] **Step 4 (S4):** `grep -nA30 '^### 16\. Access Control' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — access-control`.

### Task 17: Audit Reporting & Audit

**Inputs:**
- Source: `../carmen/docs/reports/`, `../carmen/docs/features/`.
- Existing wiki pages (rows): activity, attachment, history, notification, report, schedule, user-activity, widget (`ls en/inventory/reporting-audit/*.md`).
- Gap check: reporting/audit topics in source with no wiki page → `⬜`.

- [ ] **Step 1 (S1):** List topics from source + `ls`.
- [ ] **Step 2 (S2):** Per page: `wc -l` + Read short ones.
- [ ] **Step 3 (S3):** Write `### 17. Reporting & Audit`.
- [ ] **Step 4 (S4):** `grep -nA30 '^### 17\. Reporting' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — reporting-audit`.

### Task 18: Audit Templates

**Inputs:**
- Source: `../carmen/docs/templates/`.
- Existing wiki pages (rows): price-list, purchase-request (`ls en/inventory/templates/*.md`).
- Gap check: template types in source with no wiki page → `⬜`.

- [ ] **Step 1 (S1):** List template types from source + `ls`.
- [ ] **Step 2 (S2):** Per page: `wc -l` + Read short ones.
- [ ] **Step 3 (S3):** Write `### 18. Templates`.
- [ ] **Step 4 (S4):** `grep -nA30 '^### 18\. Templates' .specs/process-coverage-checklist.md | grep -cE '✅|🟡|⬜'` → non-zero.
- [ ] **Step 5 (S5):** Commit `docs(.specs): coverage audit — templates`.

---

## Task 19: Compute roll-up summary

**Files:**
- Modify: `.specs/process-coverage-checklist.md` (replace the `## Summary` placeholder table).

- [ ] **Step 1: Count rows per module** — for each `### N.` section, count rows and tally Status symbols.
  ```bash
  for n in $(seq 1 18); do
    echo "=== section $n ==="
    awk "/^### $n\\. /{f=1;next} /^### /{f=0} f" .specs/process-coverage-checklist.md \
      | grep -E '^\| *[0-9]' \
      | awk -F'|' '{print $(NF-1)}' | grep -oE '✅ Done|🟡 Partial|⬜ Not yet' | sort | uniq -c
  done
  ```
  (Counts the Status column per data row. Adjust column index if a row's link cell contains pipes — verify by eye.)

- [ ] **Step 2: Fill the Summary table** — one row per module: Sub-processes (total rows), Done (✅), Partial (🟡), Not yet (⬜), and `% complete = round(Done / Sub-processes * 100)`. Add a **Project total** row summing each column; project `% complete = total Done / total Sub-processes`.

- [ ] **Step 3: Bump the date** — ensure the heading reads `## Summary (as of 2026-06-04)` (or the actual run date).

- [ ] **Step 4: Verify totals are internally consistent**
  ```bash
  grep -nE '^\| ' .specs/process-coverage-checklist.md | grep -i 'project total'
  ```
  Confirm: Project total Sub-processes == sum of per-module Sub-processes, and Done+Partial+Not yet == Sub-processes for every row.

- [ ] **Step 5: Commit**
  ```bash
  git add .specs/process-coverage-checklist.md
  git commit -m "docs(.specs): fill process coverage roll-up summary"
  ```

---

## Task 20: Final consistency pass

**Files:**
- Modify: `.specs/process-coverage-checklist.md` (fixes only).

- [ ] **Step 1: Symbol sanity** — only approved symbols appear in cells.
  ```bash
  grep -oE '[^ |]*' .specs/process-coverage-checklist.md | grep -E '🟢|🔴|❌|✔|☑' || echo "OK: no stray symbols"
  ```
  Expected: `OK: no stray symbols`. Fix any non-`{✅,🟡,⬜}` status marks.

- [ ] **Step 2: All 18 sections present**
  ```bash
  grep -cE '^### (1[0-8]|[1-9])\. ' .specs/process-coverage-checklist.md
  ```
  Expected: `18`.

- [ ] **Step 3: Every Status value is valid** — no empty Status cells.
  ```bash
  grep -E '^\| *[0-9]+ \|' .specs/process-coverage-checklist.md | grep -vE '✅ Done|🟡 Partial|⬜ Not yet' || echo "OK: every data row has a status"
  ```
  Expected: `OK: every data row has a status`.

- [ ] **Step 4: Link targets resolve** — extract wiki links and confirm the pages exist.
  ```bash
  grep -oE '\(/en/inventory/[a-z0-9/-]+' .specs/process-coverage-checklist.md | sed 's/^(//' | sort -u | while read u; do
    f="en${u#/en}"; [ -f "$f.md" ] || echo "MISSING PAGE: $u"
  done; echo "link check done"
  ```
  Expected: no `MISSING PAGE` lines (anchors after a page path are fine; this checks the page file).

- [ ] **Step 5: Commit any fixes**
  ```bash
  git add .specs/process-coverage-checklist.md
  git commit -m "docs(.specs): final consistency pass on coverage checklist" || echo "nothing to fix"
  ```

---

## Self-review (plan vs design)

- **Design §3 deliverable (single file, no frontmatter, English):** Task 0 — ✅.
- **Design §4 scope (Table A ~12, Table B ~6):** Tasks 1–12, 13–18 — ✅.
- **Design §5.1 roll-up summary:** Task 19 — ✅.
- **Design §5.2 Table A columns (BR/UF/TS/Status/link):** every Table A task S3 — ✅.
- **Design §5.3 Table B columns (Page exists?/Content complete?/Status/Link):** Table B variant + Tasks 13–18 — ✅.
- **Design §6 rubric:** scaffolded in Task 0, applied in every S3, enforced in Task 20 — ✅.
- **Design §7 source mapping:** Task 0 step 1 — ✅.
- **Design §6 "A=reveal gaps" (source entities with no wiki page):** Table B gap-check in Tasks 13–18; Table A sub-processes come from source first (S1) so missing ones surface as ⬜ rows — ✅.
- **Placeholder scan:** module sub-process lists are intentionally produced by S1 (the audit is the work), not pre-listed — each task gives exact source files + grep, so no work is hand-waved. No "TBD/TODO" steps.
