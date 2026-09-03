---
title: Dimension
description: Schema-provisioned custom-field system (tb_dimension, tb_dimension_display_in, and a dimension JSONB slot on ~65 tables) with no CRUD screen, no backend service, and no frontend consumer found anywhere in the codebase.
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, dimension, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Dimension

> **At a Glance**
> **Owner:** Nobody today — **no UI or API to create/edit a dimension exists** &nbsp;·&nbsp; **Table:** `tb_dimension` (+ `tb_dimension_display_in`) &nbsp;·&nbsp; **`dimension` JSONB column** provisioned on ~65 tenant tables (transactional + master) but never read or written by any found code path &nbsp;·&nbsp; Design-stage custom-field system — schema exists, nothing implements it.

## Implementation status (verified 2026-07-16)

A repo-wide search (`carmen-inventory-frontend-react`, `carmen-turborepo-backend-v2`) found **no route, component, controller, or service** that creates, edits, lists, or deletes a `tb_dimension` or `tb_dimension_display_in` row:

- **No frontend route.** `/system-admin` has no `dimension` path in `routes/router.tsx`, and no `dimension`-named directory exists under `routes/system-admin/`. The System Admin landing page (`landing-types.ts`) does not list a Dimensions module in any of its five chapters.
- **No backend CRUD.** `tb_dimension` is referenced in exactly one non-schema file: `dimension-comment.service.ts` — and only as a `findFirst` existence check before creating a comment row. There is no `dimension.service.ts`, `dimension.controller.ts`, or Bruno `config/dimension/*` folder (only `config/dimension-comment/*`, a comment thread on rows that must already exist by some other means — direct DB insert or seed data, not observed anywhere).
- **`tb_dimension_display_in` has zero non-schema references at all** — not even the comment feature touches it.
- **The `dimension` JSONB column is real but inert.** 65 tenant tables carry a `dimension Json?` column (confirmed by grep count against the Prisma schema), including `tb_purchase_request`, `tb_workflow`, and most other transactional/master tables — but a search of the Purchase Request module (the module every other "cross-reference" below points at) found zero reads or writes of `.dimension` anywhere in its forms, hooks, or services. The column is schema-provisioned capacity, not a wired-up feature.
- Every hit for the bare word `dimension` inside `carmen-inventory-frontend-react` (outside this dead code path) turns out to be an unrelated physical-dimension field — equipment/product/unit length-width-height — not this custom-field concept.

The rest of this page describes the **design intent** as captured in the schema (kept because the tables and column are real and may be built out later), not a shipped feature. Treat every task/workflow claim below as **unconfirmed / not yet implemented** unless restated otherwise.

## 1. What & Who

Dimensions are a **planned user-extensible custom-field system**, provisioned in the schema but not built out. The intended design: a dimension defines a named tag (`cost_centre`, `project_code`, `gl_account_override`, `event_name`, …) with a typed value space, default value, and a list of *places it should appear* — header of PR, detail of GRN, the vendor master, etc. End-user values would be stored in the `dimension` JSONB column that most transactional/master tables carry — but no code populates or reads that column today.

The two-table split reflects the intended design. `tb_dimension` would be the *definition*. `tb_dimension_display_in` would be the *display matrix* — one row per place the dimension should appear (with per-place override defaults). This is the design for cost-centre tagging on PR headers and IA detail lines without hardcoded columns — **not yet realized in code**.

**Maintained by** nobody currently — there is no admin surface. **Read by** nothing found — no form renders dimension fields; no report performs cost-allocation off this table.

## 2. Common Tasks

No task in this table can be performed today — there is no screen. Kept as the *design intent* implied by the schema shape; do not treat as verified behavior.

| Task (design intent, unbuilt) | Where (does not exist) | Notes |
|---|---|---|
| Define a dimension | ~~System Config → Dimensions → New~~ | No such screen exists |
| Enable a dimension on a place | ~~Dimension edit → display-in matrix~~ | No such screen exists |
| Curate `lookup` allowed values | ~~Dimension edit → `value` editor~~ | No such screen exists |
| Override default per place | ~~Display-in row → `default_value`~~ | No such screen exists |
| Retire a dimension | ~~Set `is_active = false`~~ | Would require a row to exist first — no create path found |
| Audit dimension changes | ~~[reporting-audit/activity](/en/inventory/reporting-audit/activity) log~~ | No service writes dimension changes; nothing to audit |

## 3. Validation & Errors

Unconfirmed — no service layer exists to enforce any of these. Kept as design intent only.

| Symptom (hypothetical) | Cause | Action |
|---|---|---|
| "Key already exists" | Duplicate among non-deleted | Not implemented — no create endpoint |
| "Value not in catalogue" | `lookup` value not in `value` JSON | Not implemented |
| Cannot hard-delete dimension | Documents have non-empty values for the key | Not implemented — no document ever writes a value |
| Field missing from new form | `display_in` row missing or removed | Not applicable — no form renders dimension fields |
| Type mismatch on save | Document value violates `type` | Not implemented |

## 4. Edge Cases

- **Nothing to snapshot.** No document has ever been observed to write a `dimension` JSON value, so the "snapshot semantics" question (do later catalogue edits retro-edit historical documents?) is moot until a writer exists.
- **Comment feature is the one live code path.** `dimension-comment` lets a caller attach a freeform comment to an *existing* `tb_dimension.id` — but nothing in the codebase creates that row, so in practice this endpoint has no reachable target from any UI.
- **Master-record tagging** (vendor / location / currency inheriting dimension defaults) is design language only — no cascade code was found.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_dimension`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `key` | `String @db.VarChar` | No | Programmatic key (e.g. `cost_centre`). Stored verbatim in document `dimension` arrays. |
| `type` | `enum_dimension_type` | No | `string`, `number`, `boolean`, `date`, `datetime`, `json`, `dataset`, `lookup`, `lookup_dataset`. |
| `value` | `Json? @db.JsonB` | Yes | Catalogue / allowed-values list. |
| `description` / `note` | `String?` | Yes | Free text. |
| `default_value` | `Json? @db.JsonB` | Yes | Top-level default. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `info` | `Json? @db.JsonB` | Yes | Free-form metadata. |
| `doc_version` | `Int` | No | Optimistic-concurrency token. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([key, deleted_at])`. Index on `[key]`.

### 5.2 `tb_dimension_display_in`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `dimension_id` | `String @db.Uuid` | No | FK to `tb_dimension.id`. |
| `display_in` | `enum_dimension_display_in` | No | Where the dimension shows up. |
| `default_value` | `Json? @db.JsonB` | Yes | Per-place override. |
| `note` / `info` / `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([dimension_id, display_in, deleted_at])`. Index on `[dimension_id, display_in]`. FK `onDelete: NoAction`.

**`enum_dimension_display_in`:** `currency`, `exchange_rate`, `delivery_point`, `department`, `product_category`, `product_sub_category`, `product_item_group`, `product`, `location`, `vendor`, `pricelist`, `unit`, `purchase_request_header`, `purchase_request_detail`, `purchase_order_header`, `purchase_order_detail`, `goods_received_note_header`, `goods_received_note_detail`, `transfer_header`, `transfer_detail`, `stock_in_header`, `stock_in_detail`, `stock_out_header`, `stock_out_detail`.

## 6. Business Rules

None of the rules below are enforced by any code found — they describe the constraint shape implied by the schema (uniqueness indexes, FK, nullable flags), not verified application behavior.

- **Uniqueness (schema-level only).** `key` unique among non-deleted; each `(dimension_id, display_in)` unique — enforced by the DB index, not by any application-layer check (no service exists to trigger one).
- **Type validation, default cascade, deletion guards, place removal, snapshot semantics** — all design intent carried over from the original spec; **no code implements any of them.**

## 7. Cross-References

The modules below do **not** currently reference dimensions in any way that was found in code — cross-links are kept only because the schema's `dimension` JSONB column is present on their tables. Treat every line as "column exists, unused," not "integration confirmed."

- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order) — `dimension` column present on header/detail tables; zero reads/writes found.
- [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [inventory](/en/inventory/inventory) — same: column present, unused.
- [master-data/vendor](/en/inventory/master-data/vendor), [master-data/location](/en/inventory/master-data/location), [master-data/currency](/en/inventory/master-data/currency), [product](/en/inventory/product) — no dimension-tagging UI or cascade code found on any master record.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dimension` (lines ~4981-5006), `tb_dimension_display_in` (lines ~5045-5065), `enum_dimension_display_in` (line ~164).
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/dimension-comment/dimension-comment.service.ts` — the only non-schema code that touches `tb_dimension` (as a `findFirst` existence check before writing a comment). No `dimension.service.ts` / `dimension.controller.ts` exists.
- **Frontend:** none found. No `dimension` path exists in `../carmen-inventory-frontend-react/routes/router.tsx`, and no `dimension`-named route directory exists under `../carmen-inventory-frontend-react/routes/system-admin/`.
