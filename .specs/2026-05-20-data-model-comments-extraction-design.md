# Data Model: Comment Tables Extraction — Design

**Date:** 2026-05-20
**Status:** Approved (verbal, in-conversation)
**Scope:** Carmen Inventory book — 6 modules, both locales (EN, TH)

## 1. Purpose

Extract the `*_comment` / `*_detail_comment` table descriptions currently embedded as H3 sub-sections inside each module's `01-data-model.md` into a sibling file `01a-data-model-comments.md`. Comment / attachment tables in the inventory tenant schema share a near-identical shape (header + free-text message + `attachments` JSON array + `enum_comment_type`) and are conceptually a separate concern from the transactional header / detail tables that own the workflow lifecycle. Grouping them on their own page keeps `01-data-model.md` focused on the lifecycle-bearing entities and gives reviewers a single place to verify the comment-table pattern.

## 2. Scope

### 2.1 Modules in scope

Six inventory modules have one or more comment-table H3 sections in `01-data-model.md`. Counts of H3 sections (matched by `^### [0-9]+\.[0-9]+ tb_[a-z_]+_comment` in EN; TH mirrors EN 1:1):

| Module | H3 headings to move |
|--------|---------------------|
| `good-receive-note` | `### 2.2 tb_good_received_note_comment`, `### 2.4 tb_good_received_note_detail_comment` |
| `inventory-adjustment` | `### 2.4 tb_stock_in_comment`, `### 2.5 tb_stock_in_detail_comment`, `### 2.8 tb_stock_out_comment, tb_stock_out_detail_comment` |
| `purchase-order` | `### 2.2 tb_purchase_order_comment`, `### 2.4 tb_purchase_order_detail_comment` |
| `purchase-request` | `### 2.3 tb_purchase_request_comment`, `### 2.4 tb_purchase_request_detail_comment` |
| `store-requisition` | `### 2.2 tb_store_requisition_comment`, `### 2.4 tb_store_requisition_detail_comment` |
| `vendor-pricelist` | `### 2.3 tb_pricelist_template_comment`, `### 2.4 tb_pricelist_template_detail_comment`, `### 2.7 tb_request_for_pricing_comment / tb_request_for_pricing_detail_comment`, `### 2.10 tb_pricelist_comment / tb_pricelist_detail_comment` |

### 2.2 Files affected

- **Source files edited (12 total — 6 EN + 6 TH):** `en/inventory/<module>/01-data-model.md` and `th/inventory/<module>/01-data-model.md` for the six modules above.
- **New files created (12 total):** `en/inventory/<module>/01a-data-model-comments.md` and `th/inventory/<module>/01a-data-model-comments.md` for the six modules above.
- **Module landing pages updated (12 total):** `en/inventory/<module>.md` and `th/inventory/<module>.md` for the six modules above — `## 7. Pages in This Module` gets a new bullet pointing at `01a-data-model-comments`.

### 2.3 Out of scope

- Modules without `*_comment` H3s in `01-data-model.md` (`costing`, `inventory`, `physical-count`, `product`, `recipe`, `spot-check`). Their data-model pages are untouched.
- The Carmen Platform book (`en/platform/`, `th/platform/`). No platform module embeds inventory-style comment tables.
- Cross-references from `02-business-rules.md`, `03-user-flow-*.md`, `04-test-scenarios-*.md` that mention comment-table names in prose. These mention the table name without anchor links (verified — no occurrence of `01-data-model#…_comment` across the wiki) and remain valid because the table name is still referenced — only the page that documents it has moved.

## 3. New File: `01a-data-model-comments.md`

### 3.1 Naming rationale

- `01a` prefix sorts immediately after `01-data-model.md` in any file listing — keeping the data-model reference visually grouped.
- The `a` suffix (versus `01b`, `02`) marks it as an *appendix to 01*, not a new step in the numbered backbone (which is `01 data model → 02 business rules → 03 user flow → 04 test scenarios`). The numbered backbone applies to every module; comment tables only exist in 6 of the 14 inventory modules.
- Avoids competing with the existing non-numbered supplemental file convention (`credit-note.md`, `wastage-reporting.md`, `request-price-list.md`), which is reserved for narrative companion pages, not reference appendices.

### 3.2 Wiki.js frontmatter

```yaml
---
title: <Module Title> — Data Model: Comment Tables
description: Document-level and line-level comment / attachment tables for the <module> module — message text, attachments JSON, and the user/system comment-type enum.
published: true
date: 2026-05-20T00:00:00.000Z
tags: <module-tag>, data-model, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---
```

Per-module specifics:
- `<Module Title>` matches the existing module landing-page title (e.g. "Inventory Adjustment", "Purchase Order", "Vendor Price List").
- `<module-tag>` matches the existing tag set on `01-data-model.md` of the same module (the new file inherits the module's tagging convention).

### 3.3 Page structure

Identical structure across all six modules so cross-module reading is predictable:

```markdown
## 1. At a Glance

One short paragraph describing what this page covers: the comment / attachment tables for the <module> module, the shared shape they follow, and the role of `enum_comment_type`. Cross-reference back to `01-data-model.md` for the lifecycle-bearing tables.

## 2. Shared Shape

Bullet list of the columns that every `*_comment` row in this module carries (id, parent FK, message text, attachments JSON array of `{originalName, fileToken, contentType}`, `type` enum, audit columns). One small fenced pseudo-code block showing the canonical column layout.

## 3. Tables

### 3.1 <first comment table>

Verbatim move of the H3 body from `01-data-model.md`, renumbered from `2.X` to `3.X`. The narrative paragraph, the field table, the `**Constraints:**` line, and any back-relation list are preserved exactly.

### 3.2 <second comment table>
…and so on for each comment table in the module.

## 4. Cross-References

- Sibling: `[01 — Data Model](/<locale>/inventory/<module>/01-data-model)` — header and detail tables, enum definitions, ERD, the divergence-from-design table.
- Sibling: `[02 — Business Rules](/<locale>/inventory/<module>/02-business-rules)` — validation rules that consume `tb_*_comment.attachments` (e.g. ADJ_VAL_010 for inventory-adjustment).
- Upstream: any module-specific user flow that documents attaching evidence to a comment row (e.g. `03-user-flow-store-keeper` for inventory-adjustment).
```

The H3 bodies are **verbatim moves**, not rewrites — preserving every field-table row, every constraint line, every back-relation list. This keeps the migration mechanical and avoids accidental content drift.

## 4. Edits to `01-data-model.md`

### 4.1 Remove the H3 sections

Delete each `### 2.X tb_*_comment …` heading and its full body (paragraph, field table, constraints, back-relations) from `01-data-model.md`.

### 4.2 Replace with a stub at the position of the first removed H3

At the position where the first removed H3 used to sit, insert a single short paragraph (no heading):

> Comment / attachment tables for this module are documented separately — see [01a — Data Model: Comment Tables](/<locale>/inventory/<module>/01a-data-model-comments).

This is the only insertion. Subsequent removed H3s leave no stub — the cross-reference at the first position covers all of them. The bullet list in `## 7. Pages in This Module` on the module landing page (see §6) is the canonical entry point; the stub inside `01-data-model.md` is a contextual pointer for readers already inside the data-model page.

### 4.3 Renumber surviving 2.X sub-sections

After removing the comment H3s, renumber the remaining `### 2.X` sub-sections in order so numbering is contiguous. Example for `inventory-adjustment`:

| Before | After |
|--------|-------|
| `### 2.1 tb_adjustment_type` | `### 2.1 tb_adjustment_type` |
| `### 2.2 tb_stock_in` | `### 2.2 tb_stock_in` |
| `### 2.3 tb_stock_in_detail` | `### 2.3 tb_stock_in_detail` |
| ~~`### 2.4 tb_stock_in_comment`~~ | (moved) |
| ~~`### 2.5 tb_stock_in_detail_comment`~~ | (moved) |
| `### 2.6 tb_stock_out` | `### 2.4 tb_stock_out` |
| `### 2.7 tb_stock_out_detail` | `### 2.5 tb_stock_out_detail` |
| ~~`### 2.8 tb_stock_out_comment, tb_stock_out_detail_comment`~~ | (moved) |

Any in-page prose that references the old number (e.g. "as defined in §2.5") gets the corresponding new number. ERD ASCII diagrams and `**Constraints:**` back-relation lists still reference comment tables by name — those references stay because they name the table, not the section.

### 4.4 Frontmatter `date` bump

Update `date:` in the frontmatter of each edited `01-data-model.md` to `2026-05-20T00:00:00.000Z`. Do **not** touch `dateCreated`.

### 4.5 Section-3 / "Enums in scope" sub-section

Where the module-wide `enum_comment_type` is listed (e.g. inventory-adjustment §3.X "Enums in scope"), the entry stays in `01-data-model.md` — the enum is used by comment tables but is part of the module-wide enum catalogue. The new comments page references it via the cross-link.

## 5. TH Locale Mirror

Each EN edit has a 1:1 TH counterpart:

- Every TH `01-data-model.md` has the same `### 2.X tb_*_comment` heading set as its EN twin (verified by parallel grep). The same removals, renumbers, and stub insertion apply to TH.
- Each new TH `01a-data-model-comments.md` is a Thai translation of the EN page, structured identically (`## 1. At a Glance` / `## 2. Shared Shape` / `## 3. Tables` / `## 4. Cross-References`). The table names, field names, enum names, and any code-fence content remain in English — only narrative prose is translated.
- The cross-references in §4 of the TH page use the `/th/inventory/<module>/...` path prefix; otherwise URLs are identical.
- Frontmatter `title` and `description` are translated; `tags` is the same.

## 6. Module Landing Page Updates

Each `en/inventory/<module>.md` (and TH twin) has a `## 7. Pages in This Module` bullet list. Add a new bullet immediately after the `01 — Data Model` entry:

```markdown
- [01 — Data Model](/<locale>/inventory/<module>/01-data-model) — Entities, fields, relationships, and enums (Prisma-derived).
- [01a — Data Model: Comment Tables](/<locale>/inventory/<module>/01a-data-model-comments) — Document-level and line-level comment / attachment tables and the `enum_comment_type` user/system tagging.
- [02 — Business Rules](/<locale>/inventory/<module>/02-business-rules) — …
```

Bump `date:` in the landing page frontmatter to `2026-05-20T00:00:00.000Z`. `dateCreated` unchanged.

## 7. Implementation Order

Per-module, edit in this order to avoid leaving the repo in a half-migrated state mid-module:

1. Create new EN `01a-data-model-comments.md` (verbatim move from EN `01-data-model.md`, restructured under `## 3. Tables`).
2. Edit EN `01-data-model.md` — remove H3s, insert stub, renumber, bump `date`.
3. Update EN `<module>.md` — add bullet, bump `date`.
4. Repeat steps 1–3 for the TH locale of the same module.
5. Move to the next module.

Six modules × two locales = 12 module-locale batches; each batch touches three files (1 new `01a-data-model-comments.md`, 1 edited `01-data-model.md`, 1 edited `<module>.md`) = 36 file modifications total. Process modules in this order (alphabetical within the inventory book):

1. `good-receive-note`
2. `inventory-adjustment`
3. `purchase-order`
4. `purchase-request`
5. `store-requisition`
6. `vendor-pricelist`

## 8. Verification

After all 24 batches:

- `grep -rE "^### [0-9]+\\.[0-9]+ tb_[a-z_]+_comment" en/inventory/*/01-data-model.md th/inventory/*/01-data-model.md` returns no matches.
- `grep -rE "^### [0-9]+\\.[0-9]+ tb_[a-z_]+_comment" en/inventory/*/01a-data-model-comments.md th/inventory/*/01a-data-model-comments.md` returns the full migrated set (15 H3 lines per locale = 30 total: good-receive-note 2, inventory-adjustment 3, purchase-order 2, purchase-request 2, store-requisition 2, vendor-pricelist 4).
- Every edited `01-data-model.md` contains exactly one stub paragraph linking to `01a-data-model-comments`.
- Every `<module>.md` for the six modules contains the new `01a` bullet in §7.
- Frontmatter `date:` bumped to `2026-05-20T00:00:00.000Z` on every edited file. `dateCreated:` unchanged on every edited file.
- No stray references to old section numbers (e.g. "see §2.5") survive in any edited `01-data-model.md`.

## 9. Out-of-Scope Follow-Ups (Deferred)

- Consider applying the same extraction pattern to future inventory modules whose `01-data-model.md` grows comment-table sub-sections — adopt `01a-data-model-comments.md` as the canonical location.
- Consider whether the Carmen Platform book needs a parallel pattern if platform admin modules ever introduce comment / attachment tables. (Currently none do.)
- Wiki.js navigation tree may auto-pick up the new pages on next git-sync; no manual config change is required.
