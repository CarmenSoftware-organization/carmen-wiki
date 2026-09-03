---
title: Extra Cost Type
description: Catalogue of GRN landed-cost categories (freight, duty, handling) with per-instance allocation modes (by value, by qty, manual).
published: true
date: 2026-07-15T21:47:09.000Z
tags: master-data, extra-cost-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Extra Cost Type

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Tables:** `tb_extra_cost_type` (catalogue) + `tb_extra_cost` (per-GRN instance) &nbsp;·&nbsp; **Used by:** GRN landed-cost allocation &nbsp;·&nbsp; Categories like Freight / Duty / Handling with `by_value` / `by_qty` / `manual` allocation modes.

![Extra Cost Type screen](/screenshots/master-data/extra-cost-type.png)

## 1. What & Who

**Extra costs** are the freight, duty, handling, and other **landed-cost** components allocated onto received goods so the **unit cost in inventory** reflects the *delivered* cost, not just the invoice line. `tb_extra_cost_type` holds the named categories (`Freight`, `Customs Duty`, `Brokerage`); `tb_extra_cost` is a per-GRN instance with a chosen **allocation mode** (`by_value`, `by_qty`, or `manual`).

`by_value` and `by_qty` are the two allocation-mode labels a user can pick in the current GRN form; `manual` is a third value the enum and schema permit but the picker never offers. **Maintained by** Product Admin (catalogue) and GRN users (instances). **Read by** the costing engine, in principle — see the confirmed gap below.

**Confirmed gap (verified against `grn-extra-cost-fields.tsx` and `good-received-note.service.ts` this pass):** regardless of which allocation mode is picked, every `tb_extra_cost_detail` line has its own plain, manually-typed `amount` input — there is no code anywhere in the GRN service that computes or splits an extra-cost total across lines proportional to value or quantity. The `allocate_extra_cost_type` field is persisted as a classification tag only; it has no computational effect found in this pass. Treat the `by_value` / `by_qty` allocation formulas below as **design intent**, not confirmed live behavior (this mirrors the good-receive-note module's own resync pass, which flagged the identical gap and left it unconfirmed).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a cost type | Configuration → Master Data → Extra Cost Type → **New** | Required: `name` |
| Deactivate a type | Toggle `is_active` | Hidden from new GRNs; historical GRNs unaffected |
| Attach to GRN | GRN edit screen → **Extra Costs** section | Creates a `tb_extra_cost` header (one per GRN) plus one `tb_extra_cost_detail` row per added cost line |
| Pick an allocation-mode label | Same screen → mode dropdown | Only `by_qty` / `by_value` are offered (`by_qty` is the form default); `manual` exists in the schema but is not a picker option |
| Enter a cost-line amount | Same screen → **Add Cost** → `amount` field per row | Always a plain manually-typed number, regardless of which allocation-mode label is selected — no auto-split was found |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already in use" | Duplicate `name` on a non-deleted row | Pick a different name |
| **Unconfirmed** — no delete guard found | `extra_cost_type.service.ts`'s `delete()` is an unconditional soft-delete with no check for existing `tb_extra_cost_detail` references | A prior version of this page asserted "cannot delete — referenced by GRN extra-cost detail" as an enforced error; treat it as **not enforced** until re-verified |
| **Unconfirmed** — no reconciliation or posted-GRN lock found | A prior version of this page asserted "missing allocation amount," "allocated sum doesn't equal parent," and "cannot change allocation on a posted GRN" as enforced errors. A direct read of `good-received-note.service.ts`'s extra-cost create/update paths found no sum-reconciliation check and no extra-cost-specific edit lock — any general edit restriction comes from the parent GRN's own `doc_status`/`isReadOnly` gate (see [good-receive-note](/en/inventory/good-receive-note)), not from anything specific to extra costs | Treat these three messages as unconfirmed until re-verified |

## 4. Edge Cases

- **No allocation math found.** The `amount` on each `tb_extra_cost_detail` row is always user-entered; changing the header's `allocate_extra_cost_type` label does not recalculate any line (confirmed by reading `grn-extra-cost-fields.tsx` — the mode `Select` and the per-row `amount` `Input` are independent form fields with no derived-value wiring between them).
- **`manual` is schema-only.** The Prisma enum and DTOs accept `manual` as a third `allocate_extra_cost_type` value, but the GRN form's dropdown hard-codes only `by_qty` and `by_value` as options — `manual` is unreachable through the UI.
- **Inactive types** stay readable on historical GRNs.
- **Costing impact — unconfirmed.** The intent is for extra costs to flow into the landed unit cost the costing engine consumes; whether any cost-layer-creation code actually reads `tb_extra_cost_detail` amounts was not confirmed in this pass (mirrors the good-receive-note module's own unconfirmed flag on this point).

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_extra_cost_type`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String? @db.VarChar` | Yes | Display name (e.g. `Freight`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `extra_cost_type_name_u`. Index on `name`. Reverse relation to `tb_extra_cost_detail`.

### 5.2 `tb_extra_cost`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String? @db.VarChar` | Yes | Free-text label. |
| `good_received_note_id` | `String? @db.Uuid` | Yes | FK to `tb_good_received_note`. |
| `allocate_extra_cost_type` | `enum_allocate_extra_cost_type?` | Yes | `manual`, `by_value`, or `by_qty`. |
| `description`, `note` | `String?` | Yes | Free text. |
| `info`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `name` (`extra_cost_name_idx`). FK to `tb_good_received_note` `onDelete: NoAction`. Reverse relations to `tb_extra_cost_detail` and `tb_extra_cost_comment`. (`tb_extra_cost_detail` carries the per-line breakdown including the FK to `tb_extra_cost_type`.)

`enum_allocate_extra_cost_type` values: `manual`, `by_value`, `by_qty`.

## 6. Business Rules

- **Uniqueness.** `tb_extra_cost_type.name` unique among non-deleted rows.
- **Deletion guards — unconfirmed.** No reference check was found in `delete()`; soft-delete succeeds unconditionally even with existing `tb_extra_cost_detail` references.
- **Validation — unconfirmed.** No code was found that requires every line to have an amount before posting, or that rejects an unbalanced allocation. Every line already carries a plain, always-editable `amount` field, so there is nothing for such a check to enforce beyond ordinary required-field validation.
- **Allocation invariants — design intent, not confirmed.** No reconciliation code (`by_value` / `by_qty` summing to a parent total) was found in `good-received-note.service.ts`.
- **Lifecycle.** Inactive types readable on historical GRNs; hidden from new GRN pickers.
- **Re-allocation — unconfirmed.** No mode-specific edit lock was found; any restriction on editing extra costs after posting comes from the GRN's own general `doc_status` gate, not from this entity.

## 7. Cross-References

- [good-receive-note](/en/inventory/good-receive-note) — sole consumer. Each GRN has one `tb_extra_cost` header holding multiple `tb_extra_cost_detail` lines, each tagged with an extra-cost type and a manually-entered amount.
- [costing](/en/inventory/costing) — landed unit cost is *intended* to flow from extra-cost allocation; whether any costing code actually reads `tb_extra_cost_detail` amounts is unconfirmed (see Edge Cases).

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_extra_cost_type` (lines ~5204-5227), `tb_extra_cost` (lines ~5068-5092), `enum_allocate_extra_cost_type` (lines ~105-109).
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/extra-cost-type/` (catalogue); `../carmen-inventory-frontend-react/routes/procurement/goods-receive-note/grn-extra-cost-fields.tsx` (GRN instance form).
