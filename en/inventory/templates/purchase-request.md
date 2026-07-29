---
title: Purchase Request Template
description: Reusable PR scaffold — frequently-purchased line bundles saved as templates so a Requestor can pre-fill a new PR with one click.
published: true
date: 2026-07-29T04:21:35.000Z
tags: templates, purchase-request, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Purchase Request Template

> **At a Glance**
> **Owner:** Procurement Manager / Product Admin &nbsp;·&nbsp; **Table:** `tb_purchase_request_template` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** none (config artefact) &nbsp;·&nbsp; **Used by:** [purchase-request](/en/inventory/purchase-request) **Create PR from Template** &nbsp;·&nbsp; Reusable line-bundle scaffold whose fields pre-fill a new PR draft on demand.

![Purchase Request Template screen](/screenshots/templates/purchase-request.png)

![Purchase Request Template detail screen](/screenshots/templates/purchase-request-detail.png)

> **Implementation status (verified 2026-07-29):** "Create PR from Template" is a **client-side pre-fill**, not a backend clone endpoint. Selecting a template navigates to `/procurement/purchase-request/new?template_id=<id>`; the new-PR screen fetches the full template list, finds the matching one in the browser, and pre-fills the standard new-PR form (`getDefaultValues(purchaseRequest, template)` in `pr-form-schema.ts`). Nothing is written until the user submits the PR normally, and the resulting `tb_purchase_request` carries **no reference back to the template** — there is no `created_from_template_id` (or equivalent) column anywhere in the schema. Template deletion (`purchase-request-template.service.ts` → `delete()`) is an unconditional **hard delete** with no usage guard, and the create/edit line-item grid exposes only location, product, unit, quantity, and currency — no tax, discount, FOC quantity, or dimension fields, even though the underlying table supports them.

## 1. What & Who

A **Purchase Request Template** is a reusable scaffold capturing the line bundle a Requestor would otherwise re-enter on every recurring PR: standard products, default locations, default quantities, currency, and the workflow under which the eventual PR will route. **Create PR from Template** pre-fills a brand-new PR's form fields from the template's header and detail rows — a plain client-side merge, not a dedicated backend operation. The template itself is untouched; the new PR is independent, editable before submission, and — once created — has no persisted link back to the template it was pre-filled from.

**Maintained by** Procurement Manager / Product Admin &nbsp;·&nbsp; **Used by** Requestors (read-only access to picker) &nbsp;·&nbsp; **Posts nothing** — seed-only config artefact, no GL / AP / inventory effect.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create PR from template | PR → **New** → **From Template** picker | Navigates to `/procurement/purchase-request/new?template_id=<id>`; the new-PR form pre-fills its `workflow_id` and item rows from the template — a client-side merge, not a server-side clone |
| Edit template lines | Templates → Purchase Request → **Edit** | Edits do NOT retroactively affect PRs already created from this template (there is no link between them to propagate through) |
| Disable a seasonal line | Detail row → toggle `is_active = false` (API only) | The row-level `is_active` column exists on `tb_purchase_request_template_detail`, but the current item grid has no toggle for it — reachable only via a direct API call |
| Retire a template | Header → toggle **Active** switch off | Removes it from the "From Template" picker (`GET` list still returns it if `is_active` isn't filtered, but the picker UI hides inactive rows); has no effect on PRs already created |
| Delete a template | Header → **Delete** | Unconditional hard delete (`tx.tb_purchase_request_template.delete()`) — no check for prior usage, no confirmation of impact beyond the delete dialog |
| Add comments | Template → Comments | Stored in `tb_purchase_request_template_comment` |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| Duplicate name silently rejected with a raw database error | `@@unique([name, workflow_id, deleted_at])` is enforced only at the DB layer — neither `create()` nor `update()` in `purchase-request-template.service.ts` checks for a duplicate name first | The generic `@TryCatch` decorator catches the Prisma constraint violation and returns its raw message, not a friendly "name already exists" copy — pick a different name or workflow |
| "Required" on Workflow / Name / Location / Delivery Point / Product / Unit | Zod schema `createPrtSchema` (frontend) requires these on every line before submit | Fill the highlighted field |
| Item removed silently instead of a save-time check | There is **no** minimum-row rule — `purchase_request_template_detail.add` is optional in the DTO, and the service never checks item count | A template with zero lines saves successfully; it just clones nothing into the new PR |
| Delete succeeds even though PRs were created from this template before | No usage guard exists in `delete()` | If this matters operationally, confirm with the requester before deleting a template someone still relies on |

## 4. Edge Cases

- **Client-side pre-fill, not a clone endpoint.** `PrSelectTemplate` only navigates with `?template_id=`; `new-purchase-request-content.tsx` re-fetches the full template list and finds the match in-browser; `pr-form-schema.ts`'s `getDefaultValues(purchaseRequest, template)` maps template detail rows onto the new PR's item array. The new PR is created through the exact same submit path as a from-scratch PR — there is no special "instantiate from template" backend call.
- **No workflow on template itself.** Template has no `workflow_current_stage`, no `user_action`, no `doc_status`. Edits go live immediately on save — intentional, since templates are configuration, not transactional.
- **Currency copies verbatim; the exchange rate does not.** `currency_id` is copied from the template line, but `getDefaultValues` hardcodes `exchange_rate: 1` and drops `currency_code`/`exchange_rate_date` entirely for template-sourced lines — it is **not** re-resolved against current FX data. Whatever currency the template line carried, the new PR's exchange rate starts at `1` regardless, until a normal PR-form recalculation (out of this module's scope) corrects it.
- **No persisted link, by omission not by design guard.** `tb_purchase_request` has no `created_from_template_id` or equivalent column — a template-sourced PR is indistinguishable from a from-scratch PR once created. Editing a template after a PR was pre-filled from it has no effect on that PR, simply because nothing connects them.
- **No delete guard.** Hard delete has no usage check of any kind, in code or in the confirm dialog copy.
- **Row-level `is_active` exists but is UI-orphaned.** The column is real on `tb_purchase_request_template_detail` and defaults to `true`, but no control in `prt-item-fields.tsx`/`prt-item-table.tsx` reads or writes it — every line saved through the UI is `is_active = true`.
- **Tax, discount, FOC quantity, and dimension are schema/DTO-only.** `PurchaseRequestTemplateDetailCreateSchema` accepts `tax_profile_id`, `tax_rate`, `discount_rate`, `foc_qty`, `dimension`, etc., and `create()`/`update()` persist whatever is sent — but the item grid (`prt-item-table.tsx`) renders only Location, Product, Qty/Unit, Currency, and Delivery Point columns. Every line created through the app has zero tax, zero discount, zero FOC quantity, and an empty `dimension`; those other fields are reachable only via a direct API call.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_purchase_request_template`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Template name (unique with workflow). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `workflow_id` | `String? @db.Uuid` | Yes | FK to `tb_workflow`. Copied into a pre-filled PR's `workflow_id` when the template is selected. |
| `workflow_name` | `String? @db.VarChar` | Yes | Denormalised snapshot of the workflow name. |
| `is_active` | `Boolean? @default(true)` | Yes | Lifecycle flag. `true` = selectable in picker; `false` = retired. |
| `note`, `info`, `dimension` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, workflow_id, deleted_at])` map `PRT1_name_workflow_id_u` — same name may exist under different workflows; `@@index([workflow_id])`; `@@index([name])`. FK to `tb_workflow` `onDelete: NoAction`. This constraint is DB-only: neither `create()` nor `update()` pre-checks it, so a collision surfaces as a raw Prisma error, not an app-level message.

No `status` enum on the template — lifecycle is the single boolean `is_active` plus `deleted_at`. There is no "draft" state: `StatusSwitch` in `prt-general-fields.tsx` renders `is_active` as a plain two-way toggle, and a new template defaults to `is_active = true` (`EMPTY_FORM` in `prt-form-schema.ts`) — the picker's `STATUS_OPTIONS` filter is likewise binary (`is_active|bool:true` / `is_active|bool:false`). No code anywhere derives a third state from "used at least once."

### 5.2 `tb_purchase_request_template_detail`

One row per template line.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `purchase_request_template_id` | mixed | No / Yes | PK + parent FK. |
| `location_id`, `location_*`, `delivery_point_*` | mixed | Yes | Default destination snapshot. |
| `product_id`, `product_*` | mixed | No / Yes | Product snapshot. |
| `inventory_unit_id`, `inventory_unit_name` | mixed | Yes | Inventory unit snapshot. |
| `description`, `comment` | `String? @db.VarChar` | Yes | Free text. |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | `currency_id` is the only one of the four the item grid (`prt-item-table.tsx`) actually exposes; `getDefaultValues` copies `currency_id` verbatim into a pre-filled PR but hardcodes `exchange_rate: 1` and drops `currency_code`/`exchange_rate_date` — the rate is **not** re-resolved. |
| `requested_qty`, `requested_unit_*`, `requested_unit_conversion_factor`, `requested_base_qty` | `Decimal(20,5)` / mixed | Yes | Default requested qty (user + base unit) — the one quantity field the UI exposes. |
| `foc_qty`, `foc_unit_*`, `foc_unit_conversion_factor`, `foc_base_qty` | `Decimal(20,5)` / mixed | Yes | Free-of-charge quantity — accepted by the create/update DTO but not rendered anywhere in `prt-item-table.tsx`; always `0`/`null` on lines saved through the app. |
| `tax_*`, `is_tax_adjustment` | mixed | Yes | Tax snapshot — same as `foc_*`: schema/DTO-only, no grid column. |
| `discount_*`, `is_discount_adjustment` | mixed | Yes | Discount snapshot — same as `foc_*`: schema/DTO-only, no grid column. |
| `is_active` | `Boolean? @default(true)` | Yes | Per-line flag, defaults `true`. No control in the item grid reads or writes it, and `getDefaultValues`'s template branch maps every detail row into the pre-filled PR unconditionally — the field is not currently read anywhere on the pre-fill path. |
| `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. `dimension` participates in the unique constraint below but has no form field — every line saves with `dimension = []`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([purchase_request_template_id, product_id, location_id, dimension, deleted_at])` map `PRT1_purchase_request_template_product_location_dimension_u`; `@@index([purchase_request_template_id, product_id, location_id])`; `@@index([purchase_request_template_id])`. FKs to `tb_currency`, `tb_unit` (twice — requested_unit and foc_unit), `tb_location`, `tb_product`, `tb_purchase_request_template`, `tb_tax_profile` — all `onDelete: NoAction`.

The commented block (vendor_id, approved_*, foc_*) in the schema indicates the template intentionally **omits** vendor allocation and approved quantities — those resolve at PR creation time.

### 5.3 `tb_purchase_request_template_comment`

Comments on the template itself, following the canonical comment shape.

## 6. Workflow / Business Rules

Template **does NOT** participate in the workflow engine. Lifecycle is a single boolean:

- **`is_active = true`** (default on create) — surfaced in the "From Template" picker; still editable, and edits have no effect on PRs already pre-filled from it (there is no link to propagate through).
- **`is_active = false`** — hidden from the picker; the template row still exists and can be reactivated.
- **Deletion is separate from both.** `delete()` hard-removes the header and its detail rows in one transaction, regardless of `is_active` or prior usage.

`deleted_at` exists as a standard audit column but the service's `delete()` performs a real `DELETE`, not a soft-delete write to it — no code path in this module sets `deleted_at` without also physically removing the row.

**Authorization:** Templates maintained by Procurement Manager / Product Admin. Requestors can use but cannot edit (role-enforced by the route, not verified at the DTO level in this pass). **Validation on save:** none beyond per-field `required` checks in the frontend Zod schema (`createPrtSchema`) — no server-side uniqueness check, no minimum-row rule.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) — sole consumer. **Create PR from Template** pre-fills a new PR's `workflow_id` and item rows from the template, client-side, before the normal PR-create submit.
- [purchase-request/03-user-flow-requestor](/en/inventory/purchase-request/03-user-flow-requestor) — REQ-HP-06 happy-path scenario uses this flow.
- [system-config/workflow](/en/inventory/system-config/workflow) — the `workflow_id` is the workflow the pre-filled PR enters at submit.
- [product](/en/inventory/product), [master-data/location](/en/inventory/master-data/location), [master-data/currency](/en/inventory/master-data/currency) — the fields the item grid actually resolves against; [master-data/tax-profile](/en/inventory/master-data/tax-profile) is schema-linked but not reachable from this module's UI.
- [templates/price-list](/en/inventory/templates/price-list) — sibling template under the [templates](/en/inventory/templates) umbrella; a genuinely different design (soft-delete, live `status` enum, no linkage-back parity — see that page).

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template` (lines 2635-2664), `tb_purchase_request_template_detail` (lines 2701-2797), `tb_purchase_request_template_comment` (lines 2666-2699).
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-request-template/purchase-request-template.service.ts` (direct Prisma access — `create`/`update`/`delete`/`findAll`/`findOne`); DTOs in `dto/purchase-requesr-template.dto.ts` and `dto/update-purchase-request-template.dto.ts`.
- **Frontend route:** `../carmen-inventory-frontend-react/routes/procurement/purchase-request-template/`; pre-fill consumer at `../carmen-inventory-frontend-react/routes/procurement/purchase-request/new-purchase-request-content.tsx` and `pr-form-schema.ts`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/procurement/purchase-request-template/`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts` — note several of its `describe` blocks ("Clone", "Set as Default") assert against UI affordances (`cloneButton()`, a default-template concept) that do not exist in current frontend or schema code; those tests either soft-skip (`.catch(() => {})`, `count() === 0` guards) or describe aspirational behavior, not confirmed implementation.
