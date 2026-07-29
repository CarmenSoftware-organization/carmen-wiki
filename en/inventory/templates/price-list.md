---
title: Price List Template
description: Reusable RFQ / pricelist scaffold defining currency, validity, vendor instructions, and a per-product MOQ list — the source template Request for Pricing rounds are issued from.
published: true
date: 2026-07-29T04:41:24.000Z
tags: templates, price-list, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Price List Template

> **At a Glance**
> **Owner:** Product Admin / Procurement Lead &nbsp;·&nbsp; **Table:** `tb_pricelist_template` (+ detail, comments) &nbsp;·&nbsp; **Used by:** [vendor-pricelist](/en/inventory/vendor-pricelist) — Request for Pricing rounds carry a live `pricelist_template_id` FK &nbsp;·&nbsp; The shape of a pricelist round — currency, validity, vendor instructions, and a product/MOQ list.

![Price List Template screen](/screenshots/templates/price-list.png)

![Price List Template detail screen](/screenshots/templates/price-list-detail.png)

> **Implementation status (verified 2026-07-29):** the create/edit form (`plt-form.tsx`) exposes exactly six things — Name, Currency, Validity period, Description, Status, Vendor instructions — plus a **Products** section (per-product MOQ tiers) the previous version of this page didn't document at all. `reminder_days`, `send_reminders`, and `escalation_after_days` are real columns on `tb_pricelist_template` and the backend `update()` will happily persist them if posted directly to the API, but **no UI field sets them, no server-side validation checks them, and no background job (`micro-cronjobs`, repo-wide search) reads them** — they are inert. Clone was explicitly removed: `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` has a dedicated "Pricelist Template — Clone (removed)" suite asserting no clone affordance exists in the list, detail, or edit view, for any role. Delete (`price-list-template.service.ts` → `remove()`) is an unconditional **soft delete** (`status = inactive` + `deleted_at`) with no usage guard — there is no separate hard-delete path to be blocked.

## 1. What & Who

A pricelist template is the **shape of a pricelist round**: which currency the quote is in, how many days the resulting pricelist stays valid, the instructions rendered to the vendor, and the list of products (each with one or more MOQ tiers — a unit + quantity + note) that any vendor receiving this template will be asked to price. The buyer picks the template when starting a Request for Pricing (RFQ) round; `tb_request_for_pricing.pricelist_template_id` is a real, persisted FK — unlike the PR template (see [templates/purchase-request](/en/inventory/templates/purchase-request)), a pricelist template stays linked to every RFQ round issued from it, not just copied-and-forgotten.

Templates speed up recurring procurement cycles — instead of re-entering the same product/MOQ list and vendor instructions, the buyer reuses (for example) a "Fresh Produce Template" with its currency, validity, and product list already in place.

**Maintained by** Product Admin or the procurement lead. **Read by** the RFQ creation flow (`tb_request_for_pricing.pricelist_template_id`).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a template | Vendor Management → Price List Templates → **Add Template** | Name, currency, and validity period are the only required header fields |
| Add products | Template edit → product tree → check a product | Adds an empty MOQ row (unit + qty); use **Add tier** for a second MOQ break on the same product |
| Remove a product / tier | Product row → **Remove tier**, or uncheck in the tree → confirm | Removing the last tier of a product removes the product; removing the last product returns the section to "No products yet" |
| Activate / deactivate | Template edit → Status select (`draft`/`active`/`inactive`) → **Save** | There is no separate quick-toggle — status changes go through the same full edit-and-save as every other field. The backend also exposes a bare `PATCH :id/status`, but nothing in the frontend calls it. |
| Change vendor instructions | Template edit → **Instructions to vendor** textarea | Rendered to the vendor when this template is issued as an RFQ |
| Delete a template | Template detail (edit mode) → **Delete** | Always succeeds, always soft-deletes (see status below) — regardless of whether any RFQ round references this template |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Price list template name already exists" (409) | Case-insensitive duplicate among non-deleted templates | Pick a different name — this check is real, run on both `create()` and `update()` |
| Product row rejected on save | `product_id` and `unit_id` are both required per detail row (`plt-form-schema.ts`) | Pick a product and unit, or remove the empty row, before saving |
| Validity period won't go below 1 | The stepper's `<input type="number" min={1}>` is a native HTML constraint, not a custom business-rule message | There is no server-side minimum either way — the block is purely client-side |
| "Currency not found" | `currency_id` doesn't resolve to an existing row | Pick a valid currency — this only checks existence, **not** whether the currency is active |

Claims **not** backed by any code found in this pass, previously documented as if enforced: a rejected/sorted `reminder_days` array, an "inactive currency" check, a non-negative `escalation_after_days` rule, and a delete block for templates with issued RFQ rounds. None of these exist in `createPriceListTemplateCreateValidation`/`createPriceListTemplateUpdateValidation` (`price-list-template.dto.ts`) or in `price-list-template.service.ts`.

## 4. Edge Cases

- **Products are the template's real payload, and were previously undocumented.** Each `tb_pricelist_template_detail` row is one product; `order_unit_obj` (JSONB) holds an array of MOQ tiers (`{unit_id, unit_name, qty, note}`). The form flattens tiers into a checkbox-tree-driven list — checking a product adds one empty tier row, **Add tier** appends another for the same product with an auto-incremented default qty, and removing a product removes every tier row for it in one confirm.
- **Currency change on an existing template** only matters going forward — `tb_request_for_pricing` denormalizes nothing from the template beyond the FK, so this page cannot confirm from the frontend alone whether an in-flight RFQ re-reads the template's current currency or not; treat as unconfirmed.
- **`reminder_days` / `send_reminders` / `escalation_after_days` are dead weight through the UI.** They're real columns, accepted by `create()`/`update()` if posted directly (confirmed by reading `price-list-template.service.ts`), but the create/edit form has no field for any of them, and no background job reads them — a `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` test's own step-by-step description (`TC-PT-030001`) still narrates "toggle send-reminders switch… select 14 and 7 day reminder checkboxes… enter escalation days," but the test body it's attached to only fills the Name field and saves — the annotation is stale/aspirational relative to the code it's supposed to describe.
- **Clone is confirmed removed, not merely undocumented.** `160-pl-template.spec.ts`'s "Pricelist Template — Clone (removed)" suite explicitly asserts `cloneButton()`/`cloneMenuItem()` have zero matches in the list, the detail view, and edit mode, for every role tested.
- **Delete is soft, unconditional, and immediate — but the detail-row soft-delete is incomplete.** `remove()` sets `status = inactive`, `deleted_at`, and `deleted_by_id` on the **header** row, but the detail-row `updateMany` (`price-list-template.service.ts:741-746`) sets **only `deleted_by_id`** — `deleted_at` is never written on `tb_pricelist_template_detail`. A query filtering detail rows on `deleted_at IS NULL` would not detect a deleted template's lines at all; only the header's `deleted_at`/`status` reliably signal deletion. There is no distinct hard-delete action anywhere, and no check for whether an RFQ round (`tb_request_for_pricing.pricelist_template_id`) still points at this template.
- **Status is a real 3-value enum** (`draft`/`active`/`inactive`, DB default `draft`) edited through an ordinary `<Select>` in the same form as every other field — no distinct workflow, no gate tied to product-list completeness.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_pricelist_template`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Template name. |
| `status` | `enum_pricelist_template_status` | No | `draft` (default), `active`, `inactive`. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `vendor_instructions` | `String? @db.Text` | Yes | Rendered to vendor on RFQ send. |
| `currency_id` | `String? @db.Uuid` | Yes | FK to `tb_currency`. |
| `currency_code` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `validity_period` | `Int?` | Yes | Days the resulting pricelist stays valid after issuance. |
| `send_reminders` | `Boolean?` | Yes | Master switch (default `true`). |
| `reminder_days` | `Json? @db.JsonB` | Yes | Array of days-before-deadline (e.g. `[14, 7, 3, 1]`). |
| `escalation_after_days` | `Int? @db.Integer` | Yes | Days after deadline to escalate (default `0`). |
| `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** Primary key on `id`. `@@unique([name, deleted_at], map: "pricelist_template_name_deletedat_u")` — this is a real DB-level constraint, not application-only. FK on `currency_id` `onDelete: NoAction`. Reverse relations to `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, and `tb_request_for_pricing`.

**`enum_pricelist_template_status`:** `draft` (default), `active`, `inactive`.

### 5.2 `tb_pricelist_template_detail`

One row per product on the template; MOQ tiers for that product are packed into a single JSONB column rather than one row per tier.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `pricelist_template_id` | mixed | No | PK + parent FK. |
| `sequence_no` | `Int? @default(1)` | Yes | Display order. |
| `product_id`, `product_code`, `product_name`, `product_local_name`, `product_sku` | mixed | No / Yes | Product snapshot, enriched server-side from `tb_product` on save. |
| `inventory_unit_id`, `inventory_unit_name` | mixed | Yes | Product's inventory unit, enriched server-side. |
| `order_unit_obj` | `Json? @db.JsonB` | Yes | The MOQ tier array — `[{unit_id, unit_name, qty, note}, …]`. The form's "Add tier" button appends entries here; there's no separate tier table. |
| `comment` | `String? @db.VarChar` | Yes | Free text. |
| `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([pricelist_template_id, product_id, deleted_at])` — one detail row per product per template (all of a product's MOQ tiers live inside that single row's `order_unit_obj`, not as separate rows).

### 5.3 `tb_pricelist_template_comment`

Comments on the template itself, following the canonical comment shape. No frontend surface for these was checked in this pass.

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted — enforced **both** at the DB level (`@@unique([name, deleted_at])`) and redundantly re-checked in application code (`create()` does an explicit `findFirst` before insert; `update()`'s Zod `superRefine` does another `findFirst`).
- **No deletion guard of any kind.** `remove()` always succeeds and always soft-deletes — `status = inactive` + `deleted_at` on the **header** only; every detail row gets `deleted_by_id` but **not** `deleted_at` (see the Edge Cases note above) — there is no hard-delete path to be blocked, and no check for RFQ rounds still referencing the template.
- **Validation actually enforced:** `name` uniqueness (above); `currency_id` must reference an *existing* currency (existence only, not `is_active`); each product detail's `product_id` must exist and each MOQ tier's `unit_id` must exist. **Not enforced anywhere in code:** `validity_period` non-negativity (only a client-side native `min=1` on the stepper input), `escalation_after_days` non-negativity, `reminder_days` sort order or positivity.
- **Status is not a workflow.** `draft`/`active`/`inactive` is edited through the same `<Select>` as every other header field in the standard edit-and-save flow. The backend additionally exposes `updateStatus()` (`PATCH :id/status`, a bare unconditional write with no validation), but no frontend code calls it.
- **Reminders/escalation are unread.** `send_reminders`, `reminder_days`, `escalation_after_days` are accepted and persisted by `create()`/`update()` if present in the request body, but nothing in this repo or in `micro-cronjobs` (a repo-wide, case-insensitive search for "reminder"/"escalat" returned no matches there) reads them back out.
- **Currency change.** Nothing observed from the frontend/backend in this pass reads the template's currency after an RFQ round is issued — whether an in-flight round would see a later currency change is unconfirmed, not "new rounds only" as previously asserted.

## 7. Cross-References

- [vendor-pricelist](/en/inventory/vendor-pricelist) — RFQ rounds (`tb_request_for_pricing`) carry a persisted `pricelist_template_id` FK, and the external vendor portal auto-creates a draft `tb_pricelist` per invited vendor from the RFQ; see that module's own pages for the RFQ/portal mechanics (out of scope here).
- [master-data/currency](/en/inventory/master-data/currency) — `currency_id` resolution (existence-only check).
- [templates/purchase-request](/en/inventory/templates/purchase-request) — sibling template with materially different mechanics: hard delete vs. this template's soft delete, and no persisted consumer-side link vs. this template's live FK from `tb_request_for_pricing`.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `enum_pricelist_template_status` + `tb_pricelist_template` (lines 4222-4268), `tb_pricelist_template_comment` (lines 4270-4303), `tb_pricelist_template_detail` (lines 4305 onward).
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/price-list-template/price-list-template.service.ts` (direct Prisma access — this is the real data layer; the `backend-gateway` `pricelist-templates.service.ts` is a thin TCP proxy in front of it); DTOs and validation factories in `dto/price-list-template.dto.ts`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/vendor-management/price-list-template/` (`plt-form.tsx`, `plt-form-schema.ts`, `plt-form-products-section.tsx` for the MOQ UI).
- **E2E:** `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` — see the "Clone (removed)" suite and note `TC-PT-030001`'s step annotation describes UI controls (multi-MOQ switch, lead-time switch, max-items field, reminder checkboxes, escalation days) that the test body never interacts with and that don't exist in `plt-form.tsx`.
