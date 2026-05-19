# Data Model: Comment Tables Extraction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract `tb_*_comment` / `tb_*_detail_comment` table descriptions from the inventory book's per-module `01-data-model.md` into a sibling `01a-data-model-comments.md`, in both EN and TH locales, for the 6 inventory modules that currently embed those sections.

**Architecture:** Per-module migration in alphabetical order. Each module produces one new file per locale, edits the source `01-data-model.md` to remove the moved sections and renumber surviving ones, and updates the module landing page (`<module>.md`) to surface the new sub-page in its `## 7. Pages in This Module` list. EN and TH are migrated together within a single task to keep the locales aligned; one task = one module = one commit.

**Tech Stack:** Markdown (Wiki.js-rendered), YAML frontmatter, Bash for grep-based verification. No code, no test suite, no build pipeline — the wiki repo is content-only. Verification is performed via `grep` against established invariants.

**Reference docs:**
- Design: `.specs/2026-05-20-data-model-comments-extraction-design.md`
- Wiki conventions: `CLAUDE.md` (frontmatter, numbered-section hierarchy, comparison-table style)

---

## Pre-Flight Checks

Before starting Task 1, confirm the working state.

- [ ] **Step P1: Verify clean working tree**

Run: `git -C /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki status --short`
Expected: empty output (no uncommitted changes).
If not clean: stop and ask the user how to proceed. Do not commit existing uncommitted work as part of this plan.

- [ ] **Step P2: Verify the source files exist**

Run:
```bash
ls /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/en/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}/01-data-model.md
ls /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/th/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}/01-data-model.md
```
Expected: 12 file paths listed, no errors.

- [ ] **Step P3: Verify the expected H3 count is 15 per locale**

Run:
```bash
grep -rcE "^### [0-9]+\.[0-9]+ tb_[a-z_]+_comment" /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/en/inventory/*/01-data-model.md | grep -v ':0$'
```
Expected output (order may vary):
```
…/good-receive-note/01-data-model.md:2
…/inventory-adjustment/01-data-model.md:3
…/purchase-order/01-data-model.md:2
…/purchase-request/01-data-model.md:2
…/store-requisition/01-data-model.md:2
…/vendor-pricelist/01-data-model.md:4
```
Total = 15. Run the same command against `th/inventory/...` — expect identical counts.
If counts differ from the spec, stop and reconcile before proceeding.

---

## Migration Pattern (applies to every module task)

Every per-module task (Tasks 1–6) follows the same nine-step recipe. The recipe is described once here; each task lists only the per-module specifics (module name, H3 headings to move, surviving-section renumber map, module-tag, page-title text).

### Step pattern per module

**Step M1: Read EN `01-data-model.md` end-to-end**

Use the Read tool on `en/inventory/<module>/01-data-model.md` from line 1 to EOF. The goal is to identify, for each `*_comment` H3 heading listed in the task: the exact heading line, the body that follows (paragraph + field table + `**Constraints:**` block + any back-relation line), and the line where the next `### 2.X` heading or `## 3.` heading begins. Record the line range each H3 block occupies. The block ends one line before the next H3 / H2 starts (i.e. trim a trailing blank line if present).

**Step M2: Create EN `01a-data-model-comments.md`**

Use the Write tool on `en/inventory/<module>/01a-data-model-comments.md`. The file MUST follow this exact template (substituting `<…>` placeholders from the task spec):

```markdown
---
title: <Page Title> — Data Model: Comment Tables
description: Document-level and line-level comment / attachment tables for the <module-display-name> module — message text, attachments JSON, and the user/system comment-type enum.
published: true
date: 2026-05-20T00:00:00.000Z
tags: <module-tag>, data-model, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# <Page Title> — Data Model: Comment Tables

## 1. At a Glance

The <module-display-name> module persists user-authored and system-generated notes plus file attachments on dedicated `*_comment` tables, separate from the lifecycle-bearing header / detail tables documented in [01 — Data Model](/en/inventory/<module>/01-data-model). Every comment row carries a free-text `message`, an `attachments` JSON array of S3-token records (`{originalName, fileToken, contentType}`), and a `type` discriminator (`enum_comment_type`) that distinguishes user-authored entries from system-generated transition notes. Document-level comment tables anchor to the document header; detail-level comment tables anchor to a specific line, enabling per-line evidence (e.g. "photo of damage on this specific item").

## 2. Shared Shape

Every `*_comment` row in this module follows the same column layout:

```
id                  uuid / PK
<parent>_id         uuid / FK to header or detail row
message             text (free-form, nullable)
attachments         json — array of `{originalName, fileToken, contentType}` (nullable)
type                enum_comment_type — `user` (default) | `system`
created_at          timestamp
created_by_id       uuid / FK to tb_user
updated_at          timestamp
updated_by_id       uuid / FK to tb_user
```

The same shape applies to header-level comments and detail-level comments; only the parent FK differs.

## 3. Tables

<verbatim H3 blocks from `01-data-model.md`, in original order, renumbered from `### 2.X …` to `### 3.Y …` where Y starts at 1 and increments for each preserved H3. Each H3 block carries its original paragraph + field table + Constraints line + back-relation line, unchanged. Combined-heading H3s like `### 2.8 tb_stock_out_comment, tb_stock_out_detail_comment` are preserved as a single combined H3 — DO NOT split them.>

## 4. Cross-References

- Sibling: [01 — Data Model](/en/inventory/<module>/01-data-model) — header and detail tables, enum definitions, ERD, the divergence-from-design table.
- Sibling: [02 — Business Rules](/en/inventory/<module>/02-business-rules) — validation rules that consume `*_comment.attachments` (see task-specific cross-reference below).
- Upstream: [<module-display-name> Module Overview](/en/inventory/<module>) — module landing page.
```

Replace placeholders per task spec. The H3 blocks moved into `## 3. Tables` MUST be the verbatim text from `01-data-model.md` with only the `### 2.X` numeric prefix updated to `### 3.Y`. Do not edit, rewrite, or trim the field tables / Constraints lines / back-relation lines.

**Step M3: Edit EN `01-data-model.md` — remove H3 blocks**

For each H3 heading listed in the task, use the Edit tool to delete the full H3 block (heading + body, ending at the blank line before the next H3 / H2). Process H3s in **reverse order within the file** (highest section number first) so line-range shifts from earlier deletions don't invalidate later deletions.

**Step M4: Edit EN `01-data-model.md` — insert stub at first removed H3 position**

Use the Edit tool to insert this paragraph at the position where the first (lowest-numbered) removed H3 used to begin:

```
Comment / attachment tables for this module are documented separately — see [01a — Data Model: Comment Tables](/en/inventory/<module>/01a-data-model-comments).
```

The paragraph stands alone — no heading. A blank line precedes and follows it.

**Step M5: Edit EN `01-data-model.md` — renumber surviving 2.X sub-sections**

For each surviving `### 2.X …` heading whose number needs to change (per the task's renumber map), use the Edit tool to change only the numeric prefix. Also update any in-page prose that cites the old number (search the file for `§2.X` or "section 2.X" patterns and update). The renumber map for each module is specified in the task block.

**Step M6: Edit EN `01-data-model.md` — bump frontmatter `date`**

Use the Edit tool to set the `date:` field in the YAML frontmatter to `2026-05-20T00:00:00.000Z`. Do NOT change `dateCreated`.

**Step M7: Edit EN `<module>.md` landing page**

Use the Edit tool on `en/inventory/<module>.md`. Locate the `## 7. Pages in This Module` section's bullet list. Find the bullet that links to `01 — Data Model`. Insert a new bullet immediately after it:

```
- [01a — Data Model: Comment Tables](/en/inventory/<module>/01a-data-model-comments) — Document-level and line-level comment / attachment tables and the `enum_comment_type` user/system tagging.
```

Bump the landing page's frontmatter `date:` to `2026-05-20T00:00:00.000Z`. `dateCreated` unchanged.

**Step M8: Repeat Steps M1–M7 for the TH locale**

Same nine-step recipe applied to `th/inventory/<module>/...` files. URLs inside cross-reference links use the `/th/...` prefix; table names, field names, enum names, and code-fence content stay in English; narrative prose is translated from EN to TH. The TH `<module>.md` landing page already mirrors the EN one — apply the same bullet-insertion and `date` bump.

For the bullet in TH landing page's §7, use the Thai translation of the EN bullet text:

```
- [01a — โมเดลข้อมูล: ตารางคอมเมนต์](/th/inventory/<module>/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด พร้อมการแยก user/system ผ่าน `enum_comment_type`
```

For the §1 "At a Glance" and §2 "Shared Shape" prose in the TH `01a-data-model-comments.md`, translate the EN text into Thai. Keep the column-layout code-fence block in English (column names are schema identifiers, not narrative).

For the stub paragraph inserted into TH `01-data-model.md`:

```
ตารางคอมเมนต์ / ไฟล์แนบของโมดูลนี้ถูกแยกไปอีกหน้า — ดู [01a — โมเดลข้อมูล: ตารางคอมเมนต์](/th/inventory/<module>/01a-data-model-comments)
```

**Step M9: Verify the module migration**

Run:
```bash
grep -cE "^### [0-9]+\.[0-9]+ tb_[a-z_]+_comment" /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/<module>/01-data-model.md
```
Expected: each line ends with `:0`.

Run:
```bash
grep -cE "^### [0-9]+\.[0-9]+ tb_[a-z_]+_comment" /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/<module>/01a-data-model-comments.md
```
Expected: each line ends with the per-module count from the task (2, 3, 2, 2, 2, or 4).

Run:
```bash
grep -c "01a-data-model-comments" /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/<module>.md
```
Expected: each line ends with `:1` (one bullet link).

Run:
```bash
grep -c "01a-data-model-comments" /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/<module>/01-data-model.md
```
Expected: each line ends with `:1` (one stub link).

If any check fails, stop and diagnose before committing.

**Step M10: Commit the module's changes**

```bash
git -C /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki add \
  en/inventory/<module>/01-data-model.md \
  en/inventory/<module>/01a-data-model-comments.md \
  en/inventory/<module>.md \
  th/inventory/<module>/01-data-model.md \
  th/inventory/<module>/01a-data-model-comments.md \
  th/inventory/<module>.md
git -C /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki commit -m "$(cat <<'EOF'
docs(inventory/<module>): extract comment tables to 01a sub-page

Move tb_*_comment / tb_*_detail_comment H3 sections from 01-data-model.md
into a new sibling 01a-data-model-comments.md. Renumber surviving 2.X
sub-sections, insert a stub link at the first removed-H3 position, and
add the new sub-page to the module landing page's §7 list. Mirrored in
both EN and TH locales.
EOF
)"
```

---

## Task 1: good-receive-note

**Files:**
- Create: `en/inventory/good-receive-note/01a-data-model-comments.md`
- Create: `th/inventory/good-receive-note/01a-data-model-comments.md`
- Modify: `en/inventory/good-receive-note/01-data-model.md`
- Modify: `th/inventory/good-receive-note/01-data-model.md`
- Modify: `en/inventory/good-receive-note.md`
- Modify: `th/inventory/good-receive-note.md`

**Per-module placeholders:**
- `<module>` = `good-receive-note`
- `<module-display-name>` = `Goods Receive Note` (EN) / `ใบรับสินค้า` (TH narrative)
- `<Page Title>` (EN) = `Goods Receive Note` ; (TH) = `ใบรับสินค้า`
- `<module-tag>` = `goods-receive-note` (match the existing tag on `en/inventory/good-receive-note/01-data-model.md` — confirm via Read in Step M1)

**H3 headings to move (in source-file order):**
1. `### 2.2 tb_good_received_note_comment`
2. `### 2.4 tb_good_received_note_detail_comment`

**Renumber map for surviving 2.X (EN; TH mirrors):**

| Before | After |
|--------|-------|
| `### 2.1 tb_good_received_note` (header table) | `### 2.1` (unchanged) |
| ~~`### 2.2 tb_good_received_note_comment`~~ | (moved to 01a §3.1) |
| `### 2.3 tb_good_received_note_detail` | `### 2.2` |
| ~~`### 2.4 tb_good_received_note_detail_comment`~~ | (moved to 01a §3.2) |
| `### 2.5 …` (and any further 2.X) | `### 2.3 …` and onwards |

**Renumber-map confirmation step (do this during Step M1):** the renumber map above assumes the canonical 2.X order. Confirm against the actual file in Read; if the file has additional 2.X sections beyond 2.5, extend the map by shifting each subsequent number down by two (since two H3s are removed).

**01a §3 sub-section numbering:**
- §3.1: body of original 2.2
- §3.2: body of original 2.4

**Step M2 — EN At a Glance cross-reference target:** §2 cross-reference bullet ("Sibling: [02 — Business Rules]…") should mention any GRN-specific rule that consumes `*_comment.attachments`. If no such rule exists, simplify the bullet to: "Sibling: [02 — Business Rules](/en/inventory/good-receive-note/02-business-rules) — validation rules for the GRN lifecycle."

**Per-module verification expected counts (Step M9):**
- `01-data-model.md` H3 count: `0` (each locale)
- `01a-data-model-comments.md` H3 count: `2` (each locale)
- `<module>.md` bullet count: `1` (each locale)
- `01-data-model.md` stub count: `1` (each locale)

Execute steps M1–M10 per the recipe above using these placeholders. Commit with the message template substituted for `good-receive-note`.

---

## Task 2: inventory-adjustment

**Files:**
- Create: `en/inventory/inventory-adjustment/01a-data-model-comments.md`
- Create: `th/inventory/inventory-adjustment/01a-data-model-comments.md`
- Modify: `en/inventory/inventory-adjustment/01-data-model.md`
- Modify: `th/inventory/inventory-adjustment/01-data-model.md`
- Modify: `en/inventory/inventory-adjustment.md`
- Modify: `th/inventory/inventory-adjustment.md`

**Per-module placeholders:**
- `<module>` = `inventory-adjustment`
- `<module-display-name>` = `Inventory Adjustment` (EN) / `การปรับปรุงสต๊อก` (TH narrative)
- `<Page Title>` (EN) = `Inventory Adjustment` ; (TH) = `การปรับปรุงสต๊อก`
- `<module-tag>` = confirm via Read on `en/inventory/inventory-adjustment/01-data-model.md` frontmatter (Step M1)

**H3 headings to move (in source-file order):**
1. `### 2.4 tb_stock_in_comment`
2. `### 2.5 tb_stock_in_detail_comment`
3. `### 2.8 tb_stock_out_comment, tb_stock_out_detail_comment` — **DO NOT split this combined heading**; preserve it as a single H3 in 01a §3.3.

**Renumber map for surviving 2.X (EN; TH mirrors):**

| Before | After |
|--------|-------|
| `### 2.1 tb_adjustment_type` | `### 2.1` (unchanged) |
| `### 2.2 tb_stock_in` | `### 2.2` (unchanged) |
| `### 2.3 tb_stock_in_detail` | `### 2.3` (unchanged) |
| ~~`### 2.4 tb_stock_in_comment`~~ | (moved to 01a §3.1) |
| ~~`### 2.5 tb_stock_in_detail_comment`~~ | (moved to 01a §3.2) |
| `### 2.6 tb_stock_out` | `### 2.4` |
| `### 2.7 tb_stock_out_detail` | `### 2.5` |
| ~~`### 2.8 tb_stock_out_comment, tb_stock_out_detail_comment`~~ | (moved to 01a §3.3) |

**In-page reference updates (Step M5):**
- The ERD ASCII diagram (around line 269–282 in EN per spec) references comment tables by name (e.g. `tb_stock_in_detail_comment`, `tb_stock_out_comment`). Names are retained; no edit needed inside the ERD.
- The `**Constraints:**` lines on 2.2 (now 2.2), 2.3 (now 2.3), 2.6→2.4, 2.7→2.5 reference back-relations to comment tables by name. Names are retained.
- Section "Enums in scope" mentions `enum_comment_type` listing `tb_stock_in_comment.type / tb_stock_in_detail_comment.type / tb_stock_out_comment.type / tb_stock_out_detail_comment.type` — leave this entry in `01-data-model.md` unchanged (the enum is module-wide).
- Scan for any "§2.4", "§2.5", "§2.6", "§2.7", "§2.8" cite-style references in prose and update to the new numbers (2.4→removed, 2.5→removed, 2.6→2.4, 2.7→2.5, 2.8→removed).

**Step M2 — EN At a Glance cross-reference target:** §2 cross-reference bullet should specifically call out `ADJ_VAL_010` ("at least one comment row with non-empty `attachments` when the adjustment-type's `info.requiresDocument = true`"):

```
- Sibling: [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) — `ADJ_VAL_010` consumes `tb_stock_in_comment.attachments` / `tb_stock_out_comment.attachments` to enforce the supporting-document requirement.
```

**01a §3 sub-section numbering:**
- §3.1: body of original 2.4 (`tb_stock_in_comment`)
- §3.2: body of original 2.5 (`tb_stock_in_detail_comment`)
- §3.3: body of original 2.8 (combined `tb_stock_out_comment, tb_stock_out_detail_comment`)

**Per-module verification expected counts (Step M9):**
- `01-data-model.md` H3 count: `0` (each locale)
- `01a-data-model-comments.md` H3 count: `3` (each locale)
- `<module>.md` bullet count: `1` (each locale)
- `01-data-model.md` stub count: `1` (each locale)

Execute steps M1–M10 with the message template substituted for `inventory-adjustment`.

---

## Task 3: purchase-order

**Files:**
- Create: `en/inventory/purchase-order/01a-data-model-comments.md`
- Create: `th/inventory/purchase-order/01a-data-model-comments.md`
- Modify: `en/inventory/purchase-order/01-data-model.md`
- Modify: `th/inventory/purchase-order/01-data-model.md`
- Modify: `en/inventory/purchase-order.md`
- Modify: `th/inventory/purchase-order.md`

**Per-module placeholders:**
- `<module>` = `purchase-order`
- `<module-display-name>` = `Purchase Order` (EN) / `ใบสั่งซื้อ` (TH narrative)
- `<Page Title>` (EN) = `Purchase Order` ; (TH) = `ใบสั่งซื้อ`
- `<module-tag>` = confirm via Read on `en/inventory/purchase-order/01-data-model.md` frontmatter (Step M1)

**H3 headings to move (in source-file order):**
1. `### 2.2 tb_purchase_order_comment`
2. `### 2.4 tb_purchase_order_detail_comment`

**Renumber map for surviving 2.X (EN; TH mirrors):**

| Before | After |
|--------|-------|
| `### 2.1 tb_purchase_order` | `### 2.1` (unchanged) |
| ~~`### 2.2 tb_purchase_order_comment`~~ | (moved to 01a §3.1) |
| `### 2.3 tb_purchase_order_detail` | `### 2.2` |
| ~~`### 2.4 tb_purchase_order_detail_comment`~~ | (moved to 01a §3.2) |
| `### 2.5 …` and onwards | `### 2.3 …` and onwards (shift down by 2) |

**Renumber-map confirmation step (do this during Step M1):** confirm the exact list of 2.X sections beyond 2.4. The renumber map above assumes 2.X numbering is contiguous up to wherever `## 3. Enums` begins. Adjust map if file structure differs.

**In-page reference updates (Step M5):**
- Other modules' files reference `tb_purchase_order_comment` and `tb_purchase_order_detail_comment` by name (e.g. `03-user-flow-procurement-manager.md`, `03-user-flow-audit-config.md`, `04-test-scenarios-receiver.md`). Names are retained; no edit to those files is required.
- Scan `01-data-model.md` for "§2.X" cite-style references and update per the renumber map.

**Step M2 — EN At a Glance cross-reference target:** §2 cross-reference bullet:

```
- Sibling: [02 — Business Rules](/en/inventory/purchase-order/02-business-rules) — `PO_POST_005` (return-to-buyer reason text), `PO_POST_009` (three-way-match exception comments), `PO_POST_010` (void reason text), `PO_POST_011` (close-early reason text), and `PO_AUTH_011` (workflow-stage approval comments) all persist to `tb_purchase_order_comment`.
```

**01a §3 sub-section numbering:**
- §3.1: body of original 2.2
- §3.2: body of original 2.4

**Per-module verification expected counts (Step M9):**
- `01-data-model.md` H3 count: `0` (each locale)
- `01a-data-model-comments.md` H3 count: `2` (each locale)
- `<module>.md` bullet count: `1` (each locale)
- `01-data-model.md` stub count: `1` (each locale)

Execute steps M1–M10 with the message template substituted for `purchase-order`.

---

## Task 4: purchase-request

**Files:**
- Create: `en/inventory/purchase-request/01a-data-model-comments.md`
- Create: `th/inventory/purchase-request/01a-data-model-comments.md`
- Modify: `en/inventory/purchase-request/01-data-model.md`
- Modify: `th/inventory/purchase-request/01-data-model.md`
- Modify: `en/inventory/purchase-request.md`
- Modify: `th/inventory/purchase-request.md`

**Per-module placeholders:**
- `<module>` = `purchase-request`
- `<module-display-name>` = `Purchase Request` (EN) / `ใบขอซื้อ` (TH narrative)
- `<Page Title>` (EN) = `Purchase Request` ; (TH) = `ใบขอซื้อ`
- `<module-tag>` = confirm via Read on `en/inventory/purchase-request/01-data-model.md` frontmatter (Step M1)

**H3 headings to move (in source-file order):**
1. `### 2.3 tb_purchase_request_comment`
2. `### 2.4 tb_purchase_request_detail_comment`

**Renumber map for surviving 2.X (EN; TH mirrors):**

| Before | After |
|--------|-------|
| `### 2.1 tb_purchase_request` | `### 2.1` (unchanged) |
| `### 2.2 tb_purchase_request_detail` | `### 2.2` (unchanged) |
| ~~`### 2.3 tb_purchase_request_comment`~~ | (moved to 01a §3.1) |
| ~~`### 2.4 tb_purchase_request_detail_comment`~~ | (moved to 01a §3.2) |
| `### 2.5 …` and onwards | `### 2.3 …` and onwards (shift down by 2) |

**Renumber-map confirmation step (do this during Step M1):** confirm the exact list of 2.X sections beyond 2.4.

**Step M2 — EN At a Glance cross-reference target:** §2 cross-reference bullet:

```
- Sibling: [02 — Business Rules](/en/inventory/purchase-request/02-business-rules) — validation rules and workflow-stage comment behaviors that persist to `tb_purchase_request_comment` / `tb_purchase_request_detail_comment`.
```

**01a §3 sub-section numbering:**
- §3.1: body of original 2.3
- §3.2: body of original 2.4

**Per-module verification expected counts (Step M9):**
- `01-data-model.md` H3 count: `0` (each locale)
- `01a-data-model-comments.md` H3 count: `2` (each locale)
- `<module>.md` bullet count: `1` (each locale)
- `01-data-model.md` stub count: `1` (each locale)

Execute steps M1–M10 with the message template substituted for `purchase-request`.

---

## Task 5: store-requisition

**Files:**
- Create: `en/inventory/store-requisition/01a-data-model-comments.md`
- Create: `th/inventory/store-requisition/01a-data-model-comments.md`
- Modify: `en/inventory/store-requisition/01-data-model.md`
- Modify: `th/inventory/store-requisition/01-data-model.md`
- Modify: `en/inventory/store-requisition.md`
- Modify: `th/inventory/store-requisition.md`

**Per-module placeholders:**
- `<module>` = `store-requisition`
- `<module-display-name>` = `Store Requisition` (EN) / `ใบเบิกของจากสโตร์` (TH narrative)
- `<Page Title>` (EN) = `Store Requisition` ; (TH) = `ใบเบิกของจากสโตร์`
- `<module-tag>` = confirm via Read on `en/inventory/store-requisition/01-data-model.md` frontmatter (Step M1)

**H3 headings to move (in source-file order):**
1. `### 2.2 tb_store_requisition_comment`
2. `### 2.4 tb_store_requisition_detail_comment`

**Renumber map for surviving 2.X (EN; TH mirrors):**

| Before | After |
|--------|-------|
| `### 2.1 tb_store_requisition` | `### 2.1` (unchanged) |
| ~~`### 2.2 tb_store_requisition_comment`~~ | (moved to 01a §3.1) |
| `### 2.3 tb_store_requisition_detail` | `### 2.2` |
| ~~`### 2.4 tb_store_requisition_detail_comment`~~ | (moved to 01a §3.2) |
| `### 2.5 …` and onwards | `### 2.3 …` and onwards (shift down by 2) |

**Step M2 — EN At a Glance cross-reference target:** §2 cross-reference bullet:

```
- Sibling: [02 — Business Rules](/en/inventory/store-requisition/02-business-rules) — validation rules and workflow-stage comment behaviors that persist to `tb_store_requisition_comment` / `tb_store_requisition_detail_comment`.
```

**01a §3 sub-section numbering:**
- §3.1: body of original 2.2
- §3.2: body of original 2.4

**Per-module verification expected counts (Step M9):**
- `01-data-model.md` H3 count: `0` (each locale)
- `01a-data-model-comments.md` H3 count: `2` (each locale)
- `<module>.md` bullet count: `1` (each locale)
- `01-data-model.md` stub count: `1` (each locale)

Execute steps M1–M10 with the message template substituted for `store-requisition`.

---

## Task 6: vendor-pricelist

This is the largest module — four H3s, two of which are combined headings covering two tables each.

**Files:**
- Create: `en/inventory/vendor-pricelist/01a-data-model-comments.md`
- Create: `th/inventory/vendor-pricelist/01a-data-model-comments.md`
- Modify: `en/inventory/vendor-pricelist/01-data-model.md`
- Modify: `th/inventory/vendor-pricelist/01-data-model.md`
- Modify: `en/inventory/vendor-pricelist.md`
- Modify: `th/inventory/vendor-pricelist.md`

**Per-module placeholders:**
- `<module>` = `vendor-pricelist`
- `<module-display-name>` = `Vendor Price List` (EN) / `ราคาสินค้าจากผู้ขาย` (TH narrative)
- `<Page Title>` (EN) = `Vendor Price List` ; (TH) = `ราคาสินค้าจากผู้ขาย`
- `<module-tag>` = confirm via Read on `en/inventory/vendor-pricelist/01-data-model.md` frontmatter (Step M1)

**H3 headings to move (in source-file order):**
1. `### 2.3 tb_pricelist_template_comment`
2. `### 2.4 tb_pricelist_template_detail_comment`
3. `### 2.7 tb_request_for_pricing_comment / tb_request_for_pricing_detail_comment` — **DO NOT split**; preserve as single combined H3 in 01a §3.3.
4. `### 2.10 tb_pricelist_comment / tb_pricelist_detail_comment` — **DO NOT split**; preserve as single combined H3 in 01a §3.4.

**Renumber map for surviving 2.X (EN; TH mirrors):**

The vendor-pricelist `01-data-model.md` documents ten tables across three sub-entity families (pricelist template, request-for-pricing, pricelist). Confirm the exact 2.X ordering during Step M1 by reading the file. The expected map is:

| Before | After |
|--------|-------|
| `### 2.1 tb_pricelist_template` | `### 2.1` (unchanged) |
| `### 2.2 tb_pricelist_template_detail` | `### 2.2` (unchanged) |
| ~~`### 2.3 tb_pricelist_template_comment`~~ | (moved to 01a §3.1) |
| ~~`### 2.4 tb_pricelist_template_detail_comment`~~ | (moved to 01a §3.2) |
| `### 2.5 tb_request_for_pricing` | `### 2.3` |
| `### 2.6 tb_request_for_pricing_detail` | `### 2.4` |
| ~~`### 2.7 tb_request_for_pricing_comment / tb_request_for_pricing_detail_comment`~~ | (moved to 01a §3.3) |
| `### 2.8 tb_pricelist` | `### 2.5` |
| `### 2.9 tb_pricelist_detail` | `### 2.6` |
| ~~`### 2.10 tb_pricelist_comment / tb_pricelist_detail_comment`~~ | (moved to 01a §3.4) |

**Renumber-map confirmation step (do this during Step M1):** the map above assumes contiguous 2.1–2.10 numbering. If the file uses a different layout (e.g. tables under separate H2s per sub-entity family), adjust the map. Re-verify by listing all `### 2.X` headings in the file and comparing to the map.

**In-page reference updates (Step M5):**
- The module overview `en/inventory/vendor-pricelist.md` references the ten tenant-schema models including all four comment-table groups by name. Names are retained.
- Scan `01-data-model.md` for "§2.X" cite-style references and update per the renumber map.

**Step M2 — EN At a Glance cross-reference target:** §2 cross-reference bullet:

```
- Sibling: [02 — Business Rules](/en/inventory/vendor-pricelist/02-business-rules) — validation rules and workflow-stage comment behaviors across the pricelist template, request-for-pricing, and pricelist sub-entity families, all of which persist to their respective `*_comment` / `*_detail_comment` tables.
```

**01a §3 sub-section numbering:**
- §3.1: body of original 2.3 (`tb_pricelist_template_comment`)
- §3.2: body of original 2.4 (`tb_pricelist_template_detail_comment`)
- §3.3: body of original 2.7 (combined `tb_request_for_pricing_comment / tb_request_for_pricing_detail_comment`)
- §3.4: body of original 2.10 (combined `tb_pricelist_comment / tb_pricelist_detail_comment`)

**Per-module verification expected counts (Step M9):**
- `01-data-model.md` H3 count: `0` (each locale)
- `01a-data-model-comments.md` H3 count: `4` (each locale)
- `<module>.md` bullet count: `1` (each locale)
- `01-data-model.md` stub count: `1` (each locale)

Execute steps M1–M10 with the message template substituted for `vendor-pricelist`.

---

## Task 7: Final Verification

After all six per-module commits land.

- [ ] **Step 7.1: Source files have no remaining comment H3s**

Run:
```bash
grep -rcE "^### [0-9]+\.[0-9]+ tb_[a-z_]+_comment" \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/en/inventory/*/01-data-model.md \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/th/inventory/*/01-data-model.md
```
Expected: every line ends with `:0`.

- [ ] **Step 7.2: All migrated H3s present in 01a files**

Run:
```bash
grep -rcE "^### [0-9]+\.[0-9]+ tb_[a-z_]+_comment" \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/en/inventory/*/01a-data-model-comments.md \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/th/inventory/*/01a-data-model-comments.md
```
Expected:
```
…/good-receive-note/01a-data-model-comments.md:2
…/inventory-adjustment/01a-data-model-comments.md:3
…/purchase-order/01a-data-model-comments.md:2
…/purchase-request/01a-data-model-comments.md:2
…/store-requisition/01a-data-model-comments.md:2
…/vendor-pricelist/01a-data-model-comments.md:4
```
…for both EN and TH (12 lines total, summing to 30).

- [ ] **Step 7.3: Every edited 01-data-model.md has exactly one stub link**

Run:
```bash
grep -rc "01a-data-model-comments" \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/en/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}/01-data-model.md \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/th/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}/01-data-model.md
```
Expected: every line ends with `:1`.

- [ ] **Step 7.4: Every module landing page has exactly one new bullet**

Run:
```bash
grep -rc "01a-data-model-comments" \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/en/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}.md \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/th/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}.md
```
Expected: every line ends with `:1`.

- [ ] **Step 7.5: dateCreated unchanged on every edited file**

Run:
```bash
grep -h "^dateCreated:" \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}/01-data-model.md \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}.md
```
Expected: 24 `dateCreated:` lines, none should read `2026-05-20T00:00:00.000Z` (each should preserve the original creation timestamp from before this migration).

- [ ] **Step 7.6: date bumped to 2026-05-20 on every edited file**

Run:
```bash
grep -h "^date:" \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}/01-data-model.md \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}/01a-data-model-comments.md \
  /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/{en,th}/inventory/{good-receive-note,inventory-adjustment,purchase-order,purchase-request,store-requisition,vendor-pricelist}.md
```
Expected: 36 `date:` lines, every one reading `date: 2026-05-20T00:00:00.000Z`.

- [ ] **Step 7.7: Wiki.js visual smoke check (manual, optional)**

If the dev Wiki.js instance at `http://dev.blueledgers.com:3987/` is reachable, open one EN and one TH `01a-data-model-comments` page in the browser to confirm:
- Frontmatter renders as a page (title, tags appear in the side panel).
- §1 / §2 / §3 / §4 headings render correctly.
- Field tables render correctly (no broken Markdown table syntax).
- The cross-reference link from the stub in `01-data-model.md` actually navigates to `01a-data-model-comments`.

If the dev instance is not reachable, skip this step.

---

## Self-Review Notes

(These notes were written by the plan author for the executor's reference — not steps to execute.)

**Spec coverage:** Every requirement in `.specs/2026-05-20-data-model-comments-extraction-design.md` §1–§9 is covered by a task or step in this plan. Specifically:
- Spec §2.1 (modules in scope) → Tasks 1–6 each cover one module.
- Spec §2.2 (files affected) → each task's "Files" block enumerates the same 6 files per module.
- Spec §3.1–§3.3 (new file naming, frontmatter, structure) → Step M2 template applies uniformly.
- Spec §4 (edits to 01-data-model.md) → Steps M3, M4, M5, M6.
- Spec §5 (TH mirror) → Step M8 within each task.
- Spec §6 (module landing page updates) → Step M7 (+ TH equivalent in M8).
- Spec §7 (implementation order) → Tasks 1–6 are alphabetical per the spec.
- Spec §8 (verification commands) → Task 7 (final verification) replays them, and each module's Step M9 runs per-module verification.

**Placeholder scan:** The plan uses `<module>`, `<module-display-name>`, `<Page Title>`, `<module-tag>` as **named substitution placeholders** that are filled in per task — these are intentional, not "TBD"s. Each task spec block supplies the values. There are no "TODO" / "fill in later" placeholders; the migration recipe is fully described in the M1–M10 pattern.

**Type consistency:** New-page section numbering (`## 1. At a Glance` / `## 2. Shared Shape` / `## 3. Tables` / `## 4. Cross-References`) is consistent across all task descriptions. Frontmatter field names (`title`, `description`, `published`, `date`, `tags`, `editor`, `dateCreated`) and target value `2026-05-20T00:00:00.000Z` are consistent. The H3 prefix `### 3.Y` for moved sections is used everywhere.
