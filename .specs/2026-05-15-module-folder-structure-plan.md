# Module Folder Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 12 module folders under the carmen-wiki repo root, each with an `index.md` landing page, and relocate the existing `inventory/calculation-methods.md` to `costing/`.

**Architecture:** Each top-level folder represents one inventory ERP module. Each `index.md` is a Wiki.js-compatible Markdown file with required frontmatter and a fixed section structure (Overview, Business Context, Key Concepts, Roles, Related Modules, Reference Sources, Pages). 10 of the 12 modules synthesize their content from corresponding folders in `../carmen/docs/`; `stock-take` and `spot-check` use skeleton content with TODO callouts because no carmen/docs source exists.

**Tech Stack:** Markdown only. No build tooling. Verification uses `python3` (stdlib `yaml` via PyYAML or fallback to manual frontmatter inspection) and `git`.

**Reference spec:** `.specs/2026-05-15-module-folder-structure-design.md`

---

## File Structure

**Modified files:**
- `inventory/calculation-methods.md` → moved (via `git mv`) to `costing/calculation-methods.md`; `date` frontmatter field updated to `2026-05-15T07:48:00.000Z`. `dateCreated` unchanged.

**Created files (12 × `index.md`):**
- `inventory/index.md`
- `costing/index.md`
- `inventory-adjustment/index.md`
- `good-receive-note/index.md`
- `store-requisition/index.md`
- `stock-take/index.md`
- `spot-check/index.md`
- `purchase-request/index.md`
- `purchase-order/index.md`
- `vendor-pricelist/index.md`
- `product/index.md`
- `recipe/index.md`

Each `index.md` follows the **Common Template** below.

---

## Common Template

Every `index.md` uses exactly this skeleton. Per-module substitutions are listed in each task.

```markdown
---
title: <MODULE_TITLE>
description: <MODULE_DESCRIPTION>
published: true
date: 2026-05-15T07:48:00.000Z
tags: <MODULE_SLUG>, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# <MODULE_TITLE>

## 1. Overview

<2-3 paragraphs synthesized from the listed source files. State what the module
does, what document(s) or entity it manages, and its role in the inventory ERP.>

## 2. Business Context

<Why this module exists. The business problem it solves. Where it sits in the
hospitality supply chain flow (e.g. "GRN is the receiving step between PO and
inventory, where physical goods become recorded stock").>

## 3. Key Concepts

- **<Term>**: <definition>
- **<Term>**: <definition>

<Glossary specific to this module — document types, status enums, costing methods,
party roles, etc. Aim for 4-8 entries.>

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| <role> | <what they do in this module> |

<Aim for 2-5 rows. Roles common across modules: Store Keeper, Inventory Controller,
Purchaser, Approver, Finance, Auditor. Module-specific roles also welcome.>

## 5. Related Modules

- [[<other-module-slug>]] — <how they connect>

<Forward-references are OK. Cross-link section uses Wiki.js `[[slug]]` syntax.
List per-module cross-links are specified in each task.>

## 6. Reference Sources

- Concepts: `../carmen/docs/<source-folder>/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

<Bullet list of links to sub-pages within this folder, or "No sub-pages yet."
For `costing/`, the relocated `calculation-methods.md` goes here.>
```

---

## Verification Helper

A frontmatter sanity check used in every module task. It is written once in Task 1 and reused. The script uses only the Python stdlib — no PyYAML dependency — and validates frontmatter delimiters plus required field presence with simple regex (sufficient for the fixed template; full YAML validation is not needed).

The script is saved to `.specs/verify_frontmatter.py` and invoked as:
```bash
python3 .specs/verify_frontmatter.py <path>
```

---

## Task 1: Write the verifier script and relocate calculation-methods.md

**Files:**
- Create: `.specs/verify_frontmatter.py`
- Move: `inventory/calculation-methods.md` → `costing/calculation-methods.md`
- Modify: frontmatter `date` field in the moved file

- [ ] **Step 1: Write the frontmatter verifier**

Create `.specs/verify_frontmatter.py` with this exact content:

```python
#!/usr/bin/env python3
"""Sanity-check Wiki.js frontmatter for carmen-wiki pages."""
import re
import sys
from pathlib import Path

REQUIRED_KEYS = ["title", "description", "published", "date", "tags", "editor", "dateCreated"]

def main(path_arg: str) -> int:
    p = Path(path_arg)
    text = p.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        print(f"FAIL: {p} — no frontmatter delimiters")
        return 1
    block = m.group(1)
    missing = [k for k in REQUIRED_KEYS if not re.search(rf"^{k}\s*:", block, re.MULTILINE)]
    if missing:
        print(f"FAIL: {p} — missing keys: {missing}")
        return 1
    title_match = re.search(r"^title\s*:\s*(.+?)\s*$", block, re.MULTILINE)
    title = title_match.group(1) if title_match else "?"
    if not re.search(r"^published\s*:\s*true\s*$", block, re.MULTILINE):
        print(f"FAIL: {p} — published must be true")
        return 1
    if not re.search(r"^editor\s*:\s*markdown\s*$", block, re.MULTILINE):
        print(f"FAIL: {p} — editor must be markdown")
        return 1
    print(f"OK: {p} — title={title!r}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```

- [ ] **Step 2: Smoke-test the verifier against the existing file (in its current location)**

Run: `python3 .specs/verify_frontmatter.py inventory/calculation-methods.md`
Expected: `OK: inventory/calculation-methods.md — title='Inventory Costing Methods: FIFO vs. Weighted Average'`

- [ ] **Step 3: Create the `costing/` directory and move the file**

```bash
mkdir -p costing
git mv inventory/calculation-methods.md costing/calculation-methods.md
```

- [ ] **Step 4: Update the `date` frontmatter field**

Open `costing/calculation-methods.md`. Find:
```yaml
date: 2026-02-16T11:24:32.555Z
```
Replace with:
```yaml
date: 2026-05-15T07:48:00.000Z
```
Leave `dateCreated` unchanged.

- [ ] **Step 5: Verify frontmatter still parses after the move and edit**

Run: `python3 .specs/verify_frontmatter.py costing/calculation-methods.md`
Expected: `OK: costing/calculation-methods.md — title='Inventory Costing Methods: FIFO vs. Weighted Average'`

- [ ] **Step 6: Confirm inventory/ is empty**

Run: `ls inventory/`
Expected: empty output (will be repopulated in Task 2).

- [ ] **Step 7: Commit**

```bash
git add .specs/verify_frontmatter.py costing/calculation-methods.md
git commit -m "docs: add frontmatter verifier and relocate calculation-methods

Add .specs/verify_frontmatter.py for sanity-checking Wiki.js
frontmatter across module landing pages.

Relocate calculation-methods.md from inventory/ to costing/ per
.specs/2026-05-15-module-folder-structure-design.md section 2.3 —
the content is a costing topic. Move via git mv to preserve history.
Update date frontmatter to 2026-05-15; dateCreated unchanged."
```

---

## Task 2: Create inventory/index.md

**Files:**
- Create: `inventory/index.md`
- Source: `../carmen/docs/inventory-management/period-end-process.md`, `../carmen/docs/Inventory/inventory-management-prd.md`, `../carmen/docs/Inventory/data-structure-trace.md`, `../carmen/docs/Inventory/location-type-and-financial-treatment.md`, `../carmen/docs/Inventory/stock-in-detail.md`

**Substitutions for the Common Template:**
- `<MODULE_TITLE>`: `Inventory`
- `<MODULE_DESCRIPTION>`: `Stock balances, locations, and the period-end process — the core of the inventory ERP.`
- `<MODULE_SLUG>`: `inventory`

**Section 5 cross-links:**
- `[[costing]]` — costing is calculated against inventory balances; every stock movement updates valuation
- `[[good-receive-note]]` — GRN is the primary upstream source of stock receipts
- `[[store-requisition]]` — store requisitions are the primary downstream consumer
- `[[inventory-adjustment]]` — manual corrections to balances
- `[[stock-take]]` — periodic full count
- `[[spot-check]]` — partial verification counts

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read source files**

```bash
cat ../carmen/docs/inventory-management/period-end-process.md
cat ../carmen/docs/Inventory/inventory-management-prd.md
cat ../carmen/docs/Inventory/data-structure-trace.md
cat ../carmen/docs/Inventory/location-type-and-financial-treatment.md
cat ../carmen/docs/Inventory/stock-in-detail.md
```

- [ ] **Step 2: Write `inventory/index.md`**

Use the Common Template. Fill section 1 (Overview) with 2-3 paragraphs synthesized from the PRD and data-structure docs: stock balance per product-warehouse-location, movement types (IN/OUT/ADJUST/TRANSFER), period-end snapshot. Section 2 (Business Context): role in the hospitality supply chain (food cost control, audit, regulatory). Section 3 (Key Concepts): at minimum — Stock Balance, Location Type, Stock Movement, Period-End Snapshot, Valuation Method (cross-ref costing). Section 4 (Roles): Store Keeper, Inventory Controller, Finance. Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter parses**

Run: `python3 .specs/verify_frontmatter.py inventory/index.md`
Expected: `OK: inventory/index.md — title='Inventory'`

- [ ] **Step 4: Sanity-check that no template placeholder remains**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' inventory/index.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"`
Expected: `OK: no placeholders`

- [ ] **Step 5: Commit**

```bash
git add inventory/index.md
git commit -m "docs(inventory): add module landing page

Module overview synthesized from carmen/docs/inventory-management/ and
carmen/docs/Inventory/. Cross-links to costing, GRN, store-requisition,
inventory-adjustment, stock-take, spot-check."
```

---

## Task 3: Create costing/index.md

**Files:**
- Create: `costing/index.md`
- Source: `../carmen/docs/costing/enhanced-costing-engine.md`
- Existing sibling: `costing/calculation-methods.md` (from Task 1)

**Substitutions:**
- `<MODULE_TITLE>`: `Costing`
- `<MODULE_DESCRIPTION>`: `Inventory valuation methods (FIFO, Weighted Average) and the costing engine that calculates COGS and ending inventory value.`
- `<MODULE_SLUG>`: `costing`

**Section 5 cross-links:**
- `[[inventory]]` — costing operates on inventory movements; every IN/OUT triggers a costing calculation
- `[[good-receive-note]]` — GRN receipts set unit costs (FIFO) or update averages (WAC)
- `[[recipe]]` — recipe consumption uses costed quantities to derive food cost
- `[[inventory-adjustment]]` — adjustments require a cost basis from the costing engine

**Section 7:**
```markdown
- [Inventory Costing Methods: FIFO vs. Weighted Average](./calculation-methods.md) — Analysis and algorithms for the two supported costing methods.
```

- [ ] **Step 1: Read source**

```bash
cat ../carmen/docs/costing/enhanced-costing-engine.md
```

- [ ] **Step 2: Write `costing/index.md`**

Use the Common Template. Section 1: what the costing engine does, when it runs (per-transaction), what it outputs (COGS, valuation). Section 2: regulatory framing (IFRS/GAAP accept both methods), food-cost control framing. Section 3: at minimum — COGS, Ending Inventory Value, FIFO, Weighted Average Cost, Lot/Batch, Cost Basis. Section 4: Finance, Inventory Controller, Auditor. Section 5: cross-links above. Section 7: use the bullet above linking to `./calculation-methods.md`.

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py costing/index.md`
Expected: `OK: costing/index.md — title='Costing'`

- [ ] **Step 4: Verify the sub-page link resolves to an existing file**

Run: `test -f costing/calculation-methods.md && echo OK || echo FAIL`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add costing/index.md
git commit -m "docs(costing): add module landing page

Overview of the costing engine and the two supported methods. Links to
the existing calculation-methods page (relocated in previous commit)."
```

---

## Task 4: Create inventory-adjustment/index.md

**Files:**
- Create: `inventory-adjustment/index.md`
- Source: `../carmen/docs/inventory-adjustment/INV-ADJ-Overview.md`, `../carmen/docs/inventory-adjustment/INV-ADJ-PRD.md`, `../carmen/docs/inventory-adjustment/INV-ADJ-Business-Requirements.md`, `../carmen/docs/inventory-adjustment/INV-ADJ-Business-Logic.md`

**Substitutions:**
- `<MODULE_TITLE>`: `Inventory Adjustment`
- `<MODULE_DESCRIPTION>`: `Manual corrections to stock balances — write-offs, write-ons, reclassifications.`
- `<MODULE_SLUG>`: `inventory-adjustment`

**Section 5 cross-links:**
- `[[inventory]]` — adjustments modify inventory balances directly
- `[[costing]]` — adjustments require a cost basis (entered manually or from costing engine)
- `[[stock-take]]` — count variances become adjustment documents
- `[[spot-check]]` — partial count variances become adjustment documents

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read sources**

```bash
mkdir -p inventory-adjustment
cat ../carmen/docs/inventory-adjustment/INV-ADJ-Overview.md
cat ../carmen/docs/inventory-adjustment/INV-ADJ-PRD.md
cat ../carmen/docs/inventory-adjustment/INV-ADJ-Business-Requirements.md
cat ../carmen/docs/inventory-adjustment/INV-ADJ-Business-Logic.md
```

- [ ] **Step 2: Write `inventory-adjustment/index.md`**

Use the Common Template. Section 1: what an adjustment document is (header + lines), when it's used (damage, theft, expiry, found stock, reclassification). Section 2: audit and financial impact — adjustments are scrutinized because they bypass normal flows. Section 3: at minimum — Adjustment Type (positive/negative), Reason Code, Cost Basis, Approval, Posting. Section 4: Store Keeper (initiates), Inventory Controller (approves), Auditor. Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py inventory-adjustment/index.md`
Expected: `OK: inventory-adjustment/index.md — title='Inventory Adjustment'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' inventory-adjustment/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add inventory-adjustment/index.md
git commit -m "docs(inventory-adjustment): add module landing page

Synthesized from carmen/docs/inventory-adjustment/."
```

---

## Task 5: Create good-receive-note/index.md

**Files:**
- Create: `good-receive-note/index.md`
- Source: `../carmen/docs/good-recive-note-managment/GRN-Overview.md`, `../carmen/docs/good-recive-note-managment/grn-master-prd.md`, `../carmen/docs/good-recive-note-managment/GRN-User-Experience.md`

**Substitutions:**
- `<MODULE_TITLE>`: `Good Receive Note (GRN)`
- `<MODULE_DESCRIPTION>`: `The receiving document that records physical goods received against a purchase order and adds them to inventory.`
- `<MODULE_SLUG>`: `good-receive-note`

**Section 5 cross-links:**
- `[[purchase-order]]` — GRN is created against a PO; matched on receipt
- `[[inventory]]` — receiving a GRN posts a stock IN movement
- `[[costing]]` — GRN unit costs feed FIFO lot records or update Weighted Average
- `[[vendor-pricelist]]` — GRN price variance is checked against the vendor pricelist

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read sources**

```bash
mkdir -p good-receive-note
cat ../carmen/docs/good-recive-note-managment/GRN-Overview.md
cat ../carmen/docs/good-recive-note-managment/grn-master-prd.md
cat ../carmen/docs/good-recive-note-managment/GRN-User-Experience.md
```

- [ ] **Step 2: Write `good-receive-note/index.md`**

Use the Common Template. Section 1: GRN definition, lifecycle (draft → received → posted), three-way match (PO ↔ GRN ↔ vendor invoice). Section 2: control point where physical reality meets the books; food-safety reception checks. Section 3: at minimum — Receiving Lot, Three-Way Match, Partial Receipt, Over/Under Receipt, Receipt Posting, Quality Hold. Section 4: Store Keeper (receives), Purchaser (creates PO upstream), Finance (matches invoice). Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py good-receive-note/index.md`
Expected: `OK: good-receive-note/index.md — title='Good Receive Note (GRN)'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' good-receive-note/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add good-receive-note/index.md
git commit -m "docs(good-receive-note): add module landing page

Synthesized from carmen/docs/good-recive-note-managment/. Folder name
normalized (typos fixed, -managment suffix dropped) per spec."
```

---

## Task 6: Create store-requisition/index.md

**Files:**
- Create: `store-requisition/index.md`
- Source: `../carmen/docs/store-requisitions/SR-Overview.md`, `../carmen/docs/store-requisitions/Store Requisitions.md`, `../carmen/docs/store-requisitions/SR-Technical-Specification.md`

**Substitutions:**
- `<MODULE_TITLE>`: `Store Requisition`
- `<MODULE_DESCRIPTION>`: `Internal request to draw stock from a warehouse or central store to a consuming location (kitchen, bar, outlet).`
- `<MODULE_SLUG>`: `store-requisition`

**Section 5 cross-links:**
- `[[inventory]]` — issuing a requisition posts a stock OUT movement at source and a stock IN movement at destination (or a single OUT for consumption)
- `[[costing]]` — issued quantities are costed at the source location's current cost
- `[[recipe]]` — recipes may auto-generate requisitions for ingredients needed
- `[[good-receive-note]]` — inter-location transfers may use a paired SR + GRN

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read sources**

```bash
mkdir -p store-requisition
cat ../carmen/docs/store-requisitions/SR-Overview.md
cat "../carmen/docs/store-requisitions/Store Requisitions.md"
cat ../carmen/docs/store-requisitions/SR-Technical-Specification.md
```

- [ ] **Step 2: Write `store-requisition/index.md`**

Use the Common Template. Section 1: SR definition (internal stock request), lifecycle (draft → submitted → approved → issued → received). Section 2: control over stock movement between locations; food-cost attribution per outlet. Section 3: at minimum — Source Location, Destination Location, Approval Workflow, Issued Quantity, Variance, Cost Center. Section 4: Outlet Manager (requests), Store Keeper (issues), Approver. Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py store-requisition/index.md`
Expected: `OK: store-requisition/index.md — title='Store Requisition'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' store-requisition/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add store-requisition/index.md
git commit -m "docs(store-requisition): add module landing page

Synthesized from carmen/docs/store-requisitions/. Folder name normalized
to singular per spec."
```

---

## Task 7: Create stock-take/index.md (no carmen/docs source)

**Files:**
- Create: `stock-take/index.md`
- Source: none in carmen/docs. Inspect frontend and E2E for screen/feature naming only:
  - `../carmen-inventory-frontend-react/routes/` — look for stock-take routes
  - `../carmen-inventory-frontend-e2e/tests/` — look for stock-take scenarios

**Substitutions:**
- `<MODULE_TITLE>`: `Stock Take`
- `<MODULE_DESCRIPTION>`: `Periodic physical count of all inventory at a location to reconcile system balances against reality.`
- `<MODULE_SLUG>`: `stock-take`

**Section 5 cross-links:**
- `[[inventory]]` — stock-take resets balances to counted quantities
- `[[inventory-adjustment]]` — variances between count and book are posted as adjustments
- `[[spot-check]]` — narrower partial count uses the same concept

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Quick inspection of implementation (for naming only)**

```bash
ls ../carmen-inventory-frontend-react/routes 2>/dev/null | grep -i 'stock\|take' || echo "no frontend stock-take route"
ls ../carmen-inventory-frontend-e2e/tests 2>/dev/null | grep -i 'stock\|take' || echo "no e2e stock-take tests"
```

This step gathers naming hints. If nothing is found, that's fine — the page will be a skeleton.

- [ ] **Step 2: Write `stock-take/index.md` as a skeleton**

Use the Common Template. Fill frontmatter normally. For sections 1-3 (Overview, Business Context, Key Concepts), write what is known generically about stock takes (definition, periodicity, sheet → count → recount → variance → posting flow, frozen-stock vs. live-count), and add this callout near the end of section 1:

```markdown
> **TODO:** Source content from `../carmen-inventory-frontend-react/` (UI flow) and `../carmen-inventory-frontend-e2e/` (test scenarios). No carmen/docs source folder exists for this module.
```

Section 4: Inventory Controller (leads), Counter (counts), Approver, Auditor. Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

```bash
mkdir -p stock-take
python3 .specs/verify_frontmatter.py stock-take/index.md
```
Expected: `OK: stock-take/index.md — title='Stock Take'`

- [ ] **Step 4: Placeholder scan (TODO callout is intentional and excluded)**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' stock-take/index.md && echo FAIL || echo OK`
Expected: `OK` (note: the `> **TODO:**` callout is intentional and uses a different pattern — it should remain in place)

- [ ] **Step 5: Commit**

```bash
git add stock-take/index.md
git commit -m "docs(stock-take): add module landing page (skeleton)

No carmen/docs source folder exists for stock-take. Page is a skeleton
with a TODO callout pointing at frontend + E2E for source content per
spec section 2."
```

---

## Task 8: Create spot-check/index.md (no carmen/docs source)

**Files:**
- Create: `spot-check/index.md`
- Source: none in carmen/docs. Inspect frontend and E2E for naming.

**Substitutions:**
- `<MODULE_TITLE>`: `Spot Check`
- `<MODULE_DESCRIPTION>`: `Targeted partial count of selected items or locations — a lighter-weight check than a full stock take.`
- `<MODULE_SLUG>`: `spot-check`

**Section 5 cross-links:**
- `[[inventory]]` — spot check verifies a subset of inventory balances
- `[[inventory-adjustment]]` — variances are posted as adjustments
- `[[stock-take]]` — full count counterpart

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Quick inspection of implementation**

```bash
ls ../carmen-inventory-frontend-react/routes 2>/dev/null | grep -i 'spot\|check' || echo "no frontend spot-check route"
ls ../carmen-inventory-frontend-e2e/tests 2>/dev/null | grep -i 'spot\|check' || echo "no e2e spot-check tests"
```

- [ ] **Step 2: Write `spot-check/index.md` as a skeleton**

Use the Common Template. Sections 1-3 generic: definition (partial vs. full count), trigger (random, risk-based, post-incident), workflow (select items → count → variance → action). Add this callout near the end of section 1:

```markdown
> **TODO:** Source content from `../carmen-inventory-frontend-react/` (UI flow) and `../carmen-inventory-frontend-e2e/` (test scenarios). No carmen/docs source folder exists for this module.
```

Section 4: Inventory Controller, Counter, Auditor. Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

```bash
mkdir -p spot-check
python3 .specs/verify_frontmatter.py spot-check/index.md
```
Expected: `OK: spot-check/index.md — title='Spot Check'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' spot-check/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add spot-check/index.md
git commit -m "docs(spot-check): add module landing page (skeleton)

No carmen/docs source folder exists for spot-check. Page is a skeleton
with a TODO callout per spec section 2."
```

---

## Task 9: Create purchase-request/index.md

**Files:**
- Create: `purchase-request/index.md`
- Source: `../carmen/docs/purchase-request-management/PR-Overview.md`, `../carmen/docs/purchase-request-management/purchase-request-module-prd.md`, `../carmen/docs/purchase-request-management/purchase-request-ba.md`

**Substitutions:**
- `<MODULE_TITLE>`: `Purchase Request`
- `<MODULE_DESCRIPTION>`: `Internal request to procure goods — the upstream demand signal that becomes a purchase order after approval.`
- `<MODULE_SLUG>`: `purchase-request`

**Section 5 cross-links:**
- `[[purchase-order]]` — approved PRs become POs
- `[[product]]` — PR lines reference products from the catalog
- `[[vendor-pricelist]]` — preferred vendors and reference prices come from the pricelist
- `[[inventory]]` — current stock levels often justify a PR

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read sources**

```bash
mkdir -p purchase-request
cat ../carmen/docs/purchase-request-management/PR-Overview.md
cat ../carmen/docs/purchase-request-management/purchase-request-module-prd.md
cat ../carmen/docs/purchase-request-management/purchase-request-ba.md
```

- [ ] **Step 2: Write `purchase-request/index.md`**

Use the Common Template. Section 1: PR definition, lifecycle (draft → submitted → approved → converted to PO / rejected), multi-level approval workflow. Section 2: spending control before commitment to a vendor; budget enforcement. Section 3: at minimum — Approval Level, Budget Check, Preferred Vendor, Conversion to PO, Cancellation. Section 4: Requester (creates), Approver (multiple levels), Purchaser (converts to PO). Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py purchase-request/index.md`
Expected: `OK: purchase-request/index.md — title='Purchase Request'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' purchase-request/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add purchase-request/index.md
git commit -m "docs(purchase-request): add module landing page

Synthesized from carmen/docs/purchase-request-management/."
```

---

## Task 10: Create purchase-order/index.md

**Files:**
- Create: `purchase-order/index.md`
- Source: `../carmen/docs/purchase-order-management/purchase-order-module.md`

**Substitutions:**
- `<MODULE_TITLE>`: `Purchase Order`
- `<MODULE_DESCRIPTION>`: `Formal commitment to a vendor to purchase goods at agreed prices, quantities, and delivery terms.`
- `<MODULE_SLUG>`: `purchase-order`

**Section 5 cross-links:**
- `[[purchase-request]]` — POs are generated from approved PRs
- `[[good-receive-note]]` — GRN is created against a PO on receipt
- `[[vendor-pricelist]]` — PO prices are validated against vendor pricelists
- `[[product]]` — PO lines reference products from the catalog

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read source**

```bash
mkdir -p purchase-order
cat ../carmen/docs/purchase-order-management/purchase-order-module.md
```

- [ ] **Step 2: Write `purchase-order/index.md`**

Use the Common Template. Section 1: PO definition, lifecycle (draft → sent → confirmed → partially received → fully received → closed), amendments, cancellation. Section 2: legal commitment to vendor; AP impact at invoice; controls over rogue spending. Section 3: at minimum — PO Header, PO Line, Delivery Terms, Payment Terms, Amendment, Open vs. Closed PO, Three-Way Match. Section 4: Purchaser, Vendor, Receiver (downstream Store Keeper), Finance. Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py purchase-order/index.md`
Expected: `OK: purchase-order/index.md — title='Purchase Order'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' purchase-order/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add purchase-order/index.md
git commit -m "docs(purchase-order): add module landing page

Synthesized from carmen/docs/purchase-order-management/."
```

---

## Task 11: Create vendor-pricelist/index.md

**Files:**
- Create: `vendor-pricelist/index.md`
- Source: `../carmen/docs/vendor-pricelist-management/requirements.md`, `../carmen/docs/vendor-pricelist-management/design.md`, `../carmen/docs/vendor-pricelist-management/price-assignment-workflow-documentation.md`

**Substitutions:**
- `<MODULE_TITLE>`: `Vendor Pricelist`
- `<MODULE_DESCRIPTION>`: `Vendor catalogs of products with agreed prices, units, and validity periods — the reference for PR/PO pricing.`
- `<MODULE_SLUG>`: `vendor-pricelist`

**Section 5 cross-links:**
- `[[product]]` — pricelist entries reference products
- `[[purchase-request]]` — PRs default to preferred vendor pricelists
- `[[purchase-order]]` — POs validate prices against the active pricelist
- `[[good-receive-note]]` — GRN price variance is calculated against pricelist

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read sources**

```bash
mkdir -p vendor-pricelist
cat ../carmen/docs/vendor-pricelist-management/requirements.md
cat ../carmen/docs/vendor-pricelist-management/design.md
cat ../carmen/docs/vendor-pricelist-management/price-assignment-workflow-documentation.md
```

- [ ] **Step 2: Write `vendor-pricelist/index.md`**

Use the Common Template. Section 1: pricelist structure (vendor × product × unit × validity), assignment of preferred vendor per product, multi-currency. Section 2: enforces negotiated rates; basis for variance reporting. Section 3: at minimum — Pricelist Header, Pricelist Line, Validity Period, Preferred Vendor, Price Variance, Unit Conversion. Section 4: Purchaser (negotiates and uploads), Vendor (provides), Finance (audits variance). Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py vendor-pricelist/index.md`
Expected: `OK: vendor-pricelist/index.md — title='Vendor Pricelist'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' vendor-pricelist/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add vendor-pricelist/index.md
git commit -m "docs(vendor-pricelist): add module landing page

Synthesized from carmen/docs/vendor-pricelist-management/."
```

---

## Task 12: Create product/index.md

**Files:**
- Create: `product/index.md`
- Source: `../carmen/docs/product-management/PROD-Overview.md`, `../carmen/docs/product-management/PROD-PRD.md`, `../carmen/docs/product-management/product-master-prd.md`, `../carmen/docs/product-management/PROD-Business-Requirements.md`

**Substitutions:**
- `<MODULE_TITLE>`: `Product`
- `<MODULE_DESCRIPTION>`: `Product master data — categories, units of measure, locations, and import/export — the catalog every inventory document references.`
- `<MODULE_SLUG>`: `product`

**Section 5 cross-links:**
- `[[inventory]]` — every inventory balance is keyed by product
- `[[vendor-pricelist]]` — pricelists reference products
- `[[purchase-request]]` — PR lines reference products
- `[[purchase-order]]` — PO lines reference products
- `[[recipe]]` — recipes reference products as ingredients

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read sources**

```bash
mkdir -p product
cat ../carmen/docs/product-management/PROD-Overview.md
cat ../carmen/docs/product-management/PROD-PRD.md
cat ../carmen/docs/product-management/product-master-prd.md
cat ../carmen/docs/product-management/PROD-Business-Requirements.md
```

- [ ] **Step 2: Write `product/index.md`**

Use the Common Template. Section 1: product master structure (categories, sub-categories, attributes), base unit and conversion factors, multi-location enablement, import/export. Section 2: foundation for every other module — bad product master corrupts everything downstream. Section 3: at minimum — Product Category, Base Unit, Conversion Factor, Location Mapping, Active/Inactive, Barcode, Allergen. Section 4: Product Administrator, Purchaser, Store Keeper (lookups). Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py product/index.md`
Expected: `OK: product/index.md — title='Product'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' product/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add product/index.md
git commit -m "docs(product): add module landing page

Synthesized from carmen/docs/product-management/."
```

---

## Task 13: Create recipe/index.md

**Files:**
- Create: `recipe/index.md`
- Source: `../carmen/docs/recipe-module/RECIPE-Overview.md`, `../carmen/docs/recipe-module/RECIPE-PRD.md`, `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md`, `../carmen/docs/recipe/recipe-management.md`

**Substitutions:**
- `<MODULE_TITLE>`: `Recipe`
- `<MODULE_DESCRIPTION>`: `Recipes (ingredient lists with yields) — the bridge between menu items and inventory consumption.`
- `<MODULE_SLUG>`: `recipe`

**Section 5 cross-links:**
- `[[product]]` — recipe ingredients reference products
- `[[inventory]]` — recipe usage drives inventory OUT movements (theoretical consumption)
- `[[costing]]` — recipe cost is the sum of costed ingredient quantities
- `[[store-requisition]]` — recipes may auto-generate requisitions

**Section 7:** "No sub-pages yet."

- [ ] **Step 1: Read sources**

```bash
mkdir -p recipe
cat ../carmen/docs/recipe-module/RECIPE-Overview.md
cat ../carmen/docs/recipe-module/RECIPE-PRD.md
cat ../carmen/docs/recipe-module/RECIPE-Business-Requirements.md
cat ../carmen/docs/recipe/recipe-management.md
```

- [ ] **Step 2: Write `recipe/index.md`**

Use the Common Template. Section 1: recipe structure (header + ingredient lines + yield), sub-recipes (recipe-as-ingredient), recipe vs. menu item, version history. Section 2: food cost engineering, theoretical vs. actual variance analysis. Section 3: at minimum — Yield, Ingredient, Sub-Recipe, Recipe Cost, Theoretical Consumption, Actual Consumption, Variance, Menu Item Linkage. Section 4: Chef (creates and revises), Cost Controller (reviews cost), Outlet Manager (orders from). Section 5: cross-links above. Section 7: "No sub-pages yet."

- [ ] **Step 3: Verify frontmatter**

Run: `python3 .specs/verify_frontmatter.py recipe/index.md`
Expected: `OK: recipe/index.md — title='Recipe'`

- [ ] **Step 4: Placeholder scan**

Run: `grep -n '<MODULE_\|<Term>\|<role>\|<other-module' recipe/index.md && echo FAIL || echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add recipe/index.md
git commit -m "docs(recipe): add module landing page

Consolidated from carmen/docs/recipe-module/ (PRD, requirements) and
carmen/docs/recipe/ (UI specs) per spec section 2.2."
```

---

## Task 14: Final verification and push

**Files:** none — verification only.

- [ ] **Step 1: Verify all 12 index.md files exist**

```bash
for d in inventory costing inventory-adjustment good-receive-note store-requisition stock-take spot-check purchase-request purchase-order vendor-pricelist product recipe; do
  test -f "$d/index.md" && echo "OK: $d/index.md" || echo "FAIL: $d/index.md missing"
done
```
Expected: 12 lines of `OK:`.

- [ ] **Step 2: Verify all frontmatters parse**

```bash
for d in inventory costing inventory-adjustment good-receive-note store-requisition stock-take spot-check purchase-request purchase-order vendor-pricelist product recipe; do
  python3 .specs/verify_frontmatter.py "$d/index.md"
done
```
Expected: 12 lines of `OK: ... title='...'`.

- [ ] **Step 3: Verify the relocated calculation-methods.md still parses**

```bash
python3 .specs/verify_frontmatter.py costing/calculation-methods.md
```
Expected: `OK: costing/calculation-methods.md — title='Inventory Costing Methods: FIFO vs. Weighted Average'`

- [ ] **Step 4: Verify inventory/ is no longer the home of calculation-methods.md**

```bash
test ! -f inventory/calculation-methods.md && echo "OK: moved" || echo "FAIL: still present in inventory/"
```
Expected: `OK: moved`

- [ ] **Step 5: Verify no template placeholders remain anywhere**

```bash
grep -rn --include='*.md' '<MODULE_\|<Term>\|<role>\|<other-module' . && echo "FAIL: placeholders found" || echo "OK: no placeholders"
```
Expected: `OK: no placeholders`

- [ ] **Step 6: Check git log shows the expected commits**

```bash
git log --oneline -20
```
Expected: at least 13 commits from this work (1 relocation + 12 module index.md + possibly the verifier helper commit).

- [ ] **Step 7: Push to origin**

```bash
git push origin main
```
Expected: push succeeds.
