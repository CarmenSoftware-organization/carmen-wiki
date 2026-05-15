# Design: Module Folder Structure with index.md Landing Pages

**Date:** 2026-05-15
**Status:** Approved (user)
**Scope:** carmen-wiki repository structure

This spec is a meta document for the wiki repo — it lives in `.specs/` and is not Wiki.js content. It defines the top-level folder layout for the inventory ERP user manual and the template for each module's landing page (`index.md`).

---

## 1. Goal

Establish a top-level folder per inventory ERP module, with a landing page (`index.md`) that orients developers and testers before they drill into sub-pages. The set of folders mirrors the functional modules in `../carmen/docs/`, normalized for naming consistency, plus two modules (`stock-take`, `spot-check`) that exist in the product but lack a source folder in carmen/docs.

## 2. Folder List (12 modules)

| # | Wiki folder | Source in `../carmen/docs/` |
|---|-------------|-----------------------------|
| 1 | `inventory/` | `inventory-management/` + `Inventory/` (merged) |
| 2 | `costing/` | `costing/` |
| 3 | `inventory-adjustment/` | `inventory-adjustment/` |
| 4 | `good-receive-note/` | `good-recive-note-managment/` (typos fixed) |
| 5 | `store-requisition/` | `store-requisitions/` (singular) |
| 6 | `stock-take/` | — (no source; draft from frontend + E2E) |
| 7 | `spot-check/` | — (no source; draft from frontend + E2E) |
| 8 | `purchase-request/` | `purchase-request-management/` |
| 9 | `purchase-order/` | `purchase-order-management/` |
| 10 | `vendor-pricelist/` | `vendor-pricelist-management/` |
| 11 | `product/` | `product-management/` |
| 12 | `recipe/` | `recipe/` + `recipe-module/` (merged) |

### 2.1 Naming rules

- **Fix typos** found in carmen/docs (`recive` → `receive`, `managment` → `management`).
- **Drop the `-management` / `-managment` suffix** — the folder name is the entity, not a phrase about managing it (`purchase-order`, not `purchase-order-management`).
- **Prefer singular nouns** for document-type modules (`store-requisition`, not `store-requisitions`).
- **kebab-case**, lowercase, ASCII only.

### 2.2 Merge decisions

- `inventory-management/` + `Inventory/` in carmen/docs both describe the inventory module from different angles (process vs. data structure). The wiki consolidates them into one `inventory/` folder; both serve as concept sources.
- `recipe/` + `recipe-module/` in carmen/docs split UI/page specs from API/PRD content. The wiki consolidates into one `recipe/` folder; both serve as concept sources.

### 2.3 Existing file relocation

- `inventory/calculation-methods.md` (current location) covers FIFO vs. Weighted Average — semantically a **costing** topic, not an **inventory** overview topic.
- **Action:** move to `costing/calculation-methods.md` via `git mv`. Update its frontmatter `date` to 2026-05-15 (it was last edited today anyway). Leave `dateCreated` unchanged.
- The new `inventory/index.md` will be a fresh module overview, not a continuation of the costing content.

## 3. `index.md` Template

Every module folder gets an `index.md` with this structure. Wiki.js serves it as the folder's landing page (`/<module>/` URL).

```markdown
---
title: <Module Name>
description: <One-line summary for Wiki.js search/preview>
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp — same as date on creation>
---

# <Module Name>

## 1. Overview
<2-3 paragraphs: what this module does and its role in inventory ERP.
Synthesize from the source folder(s) in carmen/docs.>

## 2. Business Context
<Why this module exists, what business problem it solves, and where it sits
in the hospitality supply chain flow.>

## 3. Key Concepts
- **<Concept>**: <definition>
- **<Concept>**: <definition>
<Glossary of terms specific to this module — document types, status enums,
costing methods, etc.>

## 4. Roles and Personas
| Role | Responsibility |
|------|----------------|
| <role> | <what they do in this module> |

## 5. Related Modules
- [[<other-module>]] — <how they connect>
<Upstream/downstream relationships, e.g. GRN consumes PO, feeds inventory,
triggers costing.>

## 6. Reference Sources
- Concepts: `../carmen/docs/<source-folder>/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module
<Table of contents linking to sub-pages within this folder. Start with
"No sub-pages yet" if the folder has only index.md.>
```

### 3.1 Template notes

- **Section 6** is boilerplate — same across all 12 modules. Paths are relative to the carmen-wiki repo root for documentation purposes; readers consult them on their local machine.
- **Section 7** starts as a stub for most modules. The existing `costing/calculation-methods.md` (after the move) gets listed in `costing/`'s section 7.
- For `stock-take/` and `spot-check/`, sections 1-3 are written as skeletons with a visible `> TODO: source from frontend and E2E tests` callout where carmen/docs content would normally feed in.
- Frontmatter `date` and `dateCreated` are set to the creation time for new files (2026-05-15T... for this rollout).

## 4. Out of Scope

- Sub-pages inside each module folder — only `index.md` is created in this work.
- File-level topics that exist as standalone `.md` files in carmen/docs (`consumption-tracking-enhancement-documentation.md`, `fractional-inventory-system.md`, `workflow-permissions-system.md`) — these are not top-level modules. Likely homes in later work: consumption-tracking under `recipe/` (consumption is recipe-driven), fractional-inventory under `inventory/`, workflow-permissions as a cross-cutting page (not part of this spec).
- Wiki.js navigation/sidebar configuration — handled separately by Wiki.js admin.
- Content migration from carmen/docs into sub-pages — separate effort, one module at a time.

## 5. Implementation Notes

Concrete steps for the implementation plan (handed off to writing-plans):

1. `git mv inventory/calculation-methods.md costing/calculation-methods.md` and update its `date` frontmatter field.
2. Create the 12 folders (some are new, `inventory/` and `costing/` already exist).
3. For each folder, create `index.md` from the template. For 10 of them, synthesize sections 1-3 by reading the corresponding `../carmen/docs/` source folder(s). For `stock-take/` and `spot-check/`, write skeleton with TODO callouts.
4. Cross-link section 5 ("Related Modules") across pages — these are forward references at first; some `[[name]]` links resolve to siblings created in the same batch.
5. Commit in logical groups (e.g. one commit per module, or one commit for the move + one commit per group of related modules).

## 6. Open Questions

None at design time. All clarifying questions were resolved during brainstorming.
