# Process Coverage Checklist — Design

**Date:** 2026-06-04
**Status:** Approved (design phase)
**Author:** brainstorming session

## 1. Purpose

Provide a single internal tracker that answers one question: **"Is the carmen-wiki Inventory documentation project finished?"**

It does this by enumerating every Carmen Inventory **process** (grouped by module) from the source-of-truth repos, then recording — per process — whether the wiki already documents it across the standard page types. The checklist doubles as a process index (table of contents) and a documentation coverage matrix.

This is an **internal tracker for the wiki-writing team**, not a published Wiki.js page.

## 2. Decisions (from brainstorming)

| # | Question | Decision |
|---|----------|----------|
| 1 | Goal | **C** — combined process index + documentation-status matrix |
| 2 | Row granularity | **C** — module as group heading, sub-processes as rows |
| 3 | What status measures | **B+C** — separate columns per standard page type (Business rules / User flow / Test scenarios) **plus** an overall status and a link to the page/section |
| 4 | Location / ownership | **B** — internal tracker, no Wiki.js frontmatter, no Thai translation |
| 5 | Module scope | **C** — all modules, split into two tables (process vs config/reference) |
| 6 | Source of sub-process list | **A** — extract the "should-exist" list from `../carmen/docs/` so real gaps surface, then cross-check against the wiki |
| Approach | How to build/shape it | **Approach 1** — single tracker file, audited module-by-module |

## 3. Deliverable

- **One living markdown file:** `.specs/process-coverage-checklist.md`
- Plain markdown, **no Wiki.js frontmatter**, **English**, **no Thai mirror**.
- Follows the precedent of `.specs/2026-05-17-screenshots-coverage-checklist.md` (an existing internal coverage checklist in `.specs/`).

## 4. Scope — modules

All 18 Inventory-book modules, split into two tables.

**Table A — Process modules (~12)** — modules with the standard `01–04` page set:
purchase-request, purchase-order, good-receive-note, store-requisition, inventory-adjustment, physical-count, spot-check, costing, inventory, product, recipe, vendor-pricelist.

**Table B — Config / reference modules (~6)** — reference/admin modules without the `01–04` set:
master-data, system-config, dashboard, access-control, reporting-audit, templates.

> The Platform book is **out of scope** for this checklist — Inventory only.

## 5. File structure

The file is ordered top-down so a reader sees the headline number first, then the detail.

```
# Carmen Inventory — Process Coverage Checklist

(intro: what this is, how to read it)

## Summary (as of YYYY-MM-DD)        <- roll-up table, §4.1
## How status is judged              <- rubric, §6
## Source mapping                    <- wiki module -> carmen/docs folder, §7

## Table A — Process modules
### 1. <Module>                      <- one ### heading per module
   (per-module source line + sub-process rows)
### 2. <Module>
...

## Table B — Config / reference modules
### 13. <Module>
...

## Maintenance notes
```

### 5.1 Roll-up summary (top of file)

```markdown
## Summary (as of 2026-06-04)

| Module | Sub-processes | Done | Partial | Not yet | % complete |
|--------|--------------:|-----:|--------:|--------:|-----------:|
| Good Receive Note | 8 | 5 | 2 | 1 | 63% |
| Purchase Request  | 6 | 6 | 0 | 0 | 100% |
| ... | ... | ... | ... | ... | ... |
| **Project total** | **N** | **x** | **y** | **z** | **NN%** |
```

`% complete` counts a row as complete only when overall status is ✅ Done.

### 5.2 Table A row format (process modules)

Each module is a `###` heading with a source line, then a table whose rows are sub-processes.

```markdown
### 1. Good Receive Note
Source: ../carmen/docs/good-recive-note-managment/

| # | Sub-process            | BR | UF | TS | Status     | Doc link |
|---|------------------------|----|----|----|------------|----------|
| 1 | Receive against PO     | ✅ | ✅ | ✅ | ✅ Done    | [BR §2.1](/en/inventory/good-receive-note/02-business-rules) |
| 2 | Partial receipt        | ✅ | ✅ | 🟡 | 🟡 Partial | [BR §2.4](/en/inventory/good-receive-note/02-business-rules) |
| 3 | Over-receipt           | 🟡 | ⬜ | ⬜ | 🟡 Partial | — |
| 4 | Return / credit note   | ⬜ | ⬜ | ⬜ | ⬜ Not yet | — |
```

Columns:
- **Sub-process** — a discrete business process within the module, sourced from `carmen/docs`.
- **BR / UF / TS** — is this sub-process covered in the module's `02-business-rules` / `03-user-flow` / `04-test-scenarios` page(s)?
- **Status** — overall roll-up of the row (see rubric).
- **Doc link** — absolute-URL markdown link to the most relevant wiki page or section anchor; `—` when none exists.

### 5.3 Table B row format (config / reference modules)

These modules are reference pages per entity/topic, so columns measure page existence and content completeness instead of BR/UF/TS.

```markdown
### 13. Master Data
Source: ../carmen/docs/settings/ , ../carmen/docs/prisma-schema/

| # | Page / entity | Page exists? | Content complete? | Status     | Link |
|---|---------------|--------------|-------------------|------------|------|
| 1 | Vendor        | ✅           | ✅                | ✅ Done    | [link](/en/inventory/master-data/vendor) |
| 2 | Unit          | ✅           | 🟡                | 🟡 Partial | [link](/en/inventory/master-data/unit) |
| 3 | Tax Profile   | ✅           | ⬜                | 🟡 Partial | [link](/en/inventory/master-data/tax-profile) |
| 4 | <source entity with no wiki page yet> | ⬜ | ⬜ | ⬜ Not yet | — |
```

Columns:
- **Page exists?** — does a wiki `.md` page for this entity exist?
- **Content complete?** — real content vs stub/placeholder.
- **Status / Link** — as in Table A. A source entity with no wiki page is a `⬜ Not yet` row, surfacing the gap.

## 6. Status rubric

Make judgements explicit to avoid drift:

- **BR / UF / TS cell:**
  - `✅` — the page has a usable section covering this sub-process.
  - `🟡` — mentioned but incomplete, or a stub.
  - `⬜` — not found.
- **Page exists? / Content complete? cell (Table B):** same ✅/🟡/⬜ meaning applied to "file present" and "non-stub content".
- **Overall row Status:**
  - `✅ Done` — all coverage cells are ✅.
  - `🟡 Partial` — at least one ✅ or 🟡, but not all ✅.
  - `⬜ Not yet` — all coverage cells are ⬜.

## 7. Source mapping

A small table mapping each wiki module to the `carmen/docs` folder(s) used to enumerate its sub-processes — makes the audit reproducible and records provenance. Verified to exist on this machine:

| Wiki module | carmen/docs source folder |
|-------------|---------------------------|
| good-receive-note | good-recive-note-managment/ |
| purchase-request  | purchase-request-management/ |
| purchase-order    | purchase-order-management/ |
| store-requisition | store-requisitions/ |
| inventory-adjustment | inventory-adjustment/ |
| costing           | costing/ |
| inventory         | inventory-management/ |
| product           | product-management/ |
| recipe            | recipe/ , recipe-module/ |
| vendor-pricelist  | vendor-pricelist-management/ |
| physical-count / spot-check | inventory-management/ (+ use-cases/ , features/) |
| master-data / system-config | settings/ , prisma-schema/ |

(Exact folder set per module is finalized during the audit; missing matches are noted in the row.)

## 8. How it gets built (implementation note)

Per module, module-by-module (Approach 1):
1. Read the mapped `carmen/docs` source to enumerate the sub-processes that **should** exist.
2. Grep the module's wiki pages (`02-business-rules`, `03-user-flow*`, `04-test-scenarios*`, or entity pages) to mark each coverage cell.
3. Fill the Doc link with the best matching page/section.
4. After all modules, compute the roll-up summary and project total.

Building/populating the actual data is the job of the implementation plan, not this design.

## 9. Out of scope (YAGNI)

- No automation/script to regenerate the checklist — manual living doc.
- No Wiki.js page, no Thai mirror, no frontmatter.
- No Platform-book coverage.
- No per-module separate files (rejected Approach 2).
- Section-anchor precision is best-effort; page-level links are acceptable when a stable anchor is unavailable.
