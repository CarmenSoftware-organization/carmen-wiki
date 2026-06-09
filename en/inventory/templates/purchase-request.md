---
title: Purchase Request Template
description: Reusable PR scaffold — frequently-purchased line bundles saved as templates so a Requestor can instantiate a PR with one click.
published: true
date: 2026-06-09T16:28:56.000Z
tags: templates, purchase-request, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Purchase Request Template

> **At a Glance**
> **Owner:** Procurement Manager / Product Admin &nbsp;·&nbsp; **Table:** `tb_purchase_request_template` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** none (config artefact) &nbsp;·&nbsp; **Used by:** [purchase-request](/en/inventory/purchase-request) **Create PR from Template** &nbsp;·&nbsp; Reusable line-bundle scaffold cloned into a new PR on demand.

![Purchase Request Template screen](/screenshots/templates/purchase-request.png)

![Purchase Request Template detail screen](/screenshots/templates/purchase-request-detail.png)

## 1. What & Who

A **Purchase Request Template** is a reusable scaffold capturing the line bundle a Requestor would otherwise re-enter on every recurring PR: standard products, default locations, default quantities, currency, tax / discount snapshots, and the workflow under which the eventual PR will route. **Create PR from Template** deep-clones the header and detail rows into a brand-new `tb_purchase_request` at `pr_status = draft`. The template itself is untouched; the new PR is independent and editable before submission.

**Maintained by** Procurement Manager / Product Admin &nbsp;·&nbsp; **Used by** Requestors (read-only access to picker) &nbsp;·&nbsp; **Posts nothing** — seed-only config artefact, no GL / AP / inventory effect.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create PR from template | PR → **New** → **From Template** picker | Deep-clones header + `is_active = true` detail rows into a fresh PR |
| Edit template lines | Templates → Purchase Request → **Edit** | Edits do NOT propagate to PRs already cloned from this template |
| Disable a seasonal line | Detail row → toggle `is_active = false` | Line stays in template but is skipped at clone time |
| Retire a template | Header → toggle `is_active = false` | Removes it from the picker; historical PRs still reference `created_from_template_id` |
| Hard-delete unused template | Header → **Delete** | Only allowed if never instantiated — otherwise flip `is_active` |
| Add comments | Template → Comments | Stored in `tb_purchase_request_template_comment` |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name must be unique within workflow" | Another non-deleted template has the same `(name, workflow_id)` | Pick a different name or workflow |
| "At least one active detail row required" | All lines have `is_active = false` | Enable at least one line before publishing |
| "Hard-delete blocked — template in use" | A PR was previously cloned from this template | Set `is_active = false` instead |
| "Rate not in history" (on clone) | No `tb_exchange_rate` row on the cloned PR's `pr_date` | Add a rate (see [master-data/exchange-rate](/en/inventory/master-data/exchange-rate)) then retry clone |
| "Product / location reference inactive" | Master record soft-deleted after template was authored | Edit the line to swap in an active reference |
| Cloned PR has wrong currency | Currency code is copied verbatim; only the rate re-resolves | Edit the cloned PR header; currency cannot change on the template post-clone |

## 4. Edge Cases

- **Deep-copy clone semantics.** Clone inserts a fresh `tb_purchase_request` (new `pr_no`, `pr_status = draft`, current user as creator) and one `tb_purchase_request_detail` per `is_active = true` template line. Quantities, units, tax / discount snapshots, dimensions copied **verbatim**. Inactive lines are skipped.
- **No workflow on template itself.** Template has no `workflow_current_stage`, no `user_action`, no `doc_status`. Edits go live immediately on save — intentional, since templates are configuration, not transactional.
- **Currency / FX resolution at clone.** Currency code copied verbatim; `exchange_rate` and `exchange_rate_date` are **re-resolved** at clone time against [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) using the new PR's `pr_date` — prevents stale FX.
- **Seed-only persistence.** Template rows are never FK-referenced by transactional documents — the PR records a copy, not a reference. Editing a template after a PR has been cloned does **NOT** retroactively change that PR.
- **Hard-delete guard.** Once a PR has been cloned from the template, hard-delete is blocked; soft retirement only.
- **Per-line `is_active`.** A line can be temporarily disabled without removing it — useful for seasonal SKUs.
- **Dimension awareness.** `dimension` JSON participates in the per-line unique key, so a single product can appear twice in a template under different dimension values (e.g. different cost centres).

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_purchase_request_template`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Template name (unique with workflow). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `workflow_id` | `String? @db.Uuid` | Yes | FK to `tb_workflow`. The workflow assigned to PRs cloned from this template. |
| `workflow_name` | `String? @db.VarChar` | Yes | Denormalised snapshot of the workflow name. |
| `is_active` | `Boolean? @default(true)` | Yes | Lifecycle flag. `true` = selectable in picker; `false` = retired. |
| `note`, `info`, `dimension` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, workflow_id, deleted_at])` map `PRT1_name_workflow_id_u` — same name may exist under different workflows; `@@index([workflow_id])`; `@@index([name])`. FK to `tb_workflow` `onDelete: NoAction`.

No `status` enum on the template — lifecycle is the boolean `is_active` plus `deleted_at`. See Section 6 for how the three logical states (draft / active / inactive) map.

### 5.2 `tb_purchase_request_template_detail`

One row per template line.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `purchase_request_template_id` | mixed | No / Yes | PK + parent FK. |
| `location_id`, `location_*`, `delivery_point_*` | mixed | Yes | Default destination snapshot. |
| `product_id`, `product_*` | mixed | No / Yes | Product snapshot. |
| `inventory_unit_id`, `inventory_unit_name` | mixed | Yes | Inventory unit snapshot. |
| `description`, `comment` | `String? @db.VarChar` | Yes | Free text. |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | Currency snapshot — resolved at clone, not on template edit. |
| `requested_qty`, `requested_unit_*`, `requested_unit_conversion_factor`, `requested_base_qty` | `Decimal(20,5)` / mixed | Yes | Default requested qty (user + base unit). |
| `foc_qty`, `foc_unit_*`, `foc_unit_conversion_factor`, `foc_base_qty` | `Decimal(20,5)` / mixed | Yes | Default free-of-charge quantity. |
| `tax_*`, `is_tax_adjustment` | mixed | Yes | Tax snapshot. |
| `discount_*`, `is_discount_adjustment` | mixed | Yes | Discount snapshot. |
| `is_active` | `Boolean? @default(true)` | Yes | Per-line flag — inactive lines skipped at clone. |
| `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([purchase_request_template_id, product_id, location_id, dimension, deleted_at])` map `PRT1_purchase_request_template_product_location_dimension_u`; `@@index([purchase_request_template_id, product_id, location_id])`; `@@index([purchase_request_template_id])`. FKs to `tb_currency`, `tb_unit` (twice — requested_unit and foc_unit), `tb_location`, `tb_product`, `tb_purchase_request_template`, `tb_tax_profile` — all `onDelete: NoAction`.

The commented block (vendor_id, approved_*, foc_*) in the schema indicates the template intentionally **omits** vendor allocation and approved quantities — those resolve at PR creation time.

### 5.3 `tb_purchase_request_template_comment`

Comments on the template itself, following the canonical comment shape.

## 6. Workflow / Business Rules

Template **does NOT** participate in the workflow engine. Three logical states derive from `is_active` and `deleted_at`:

- **`draft`** (`is_active = false`, `deleted_at IS NULL`, no usage yet) — editable, not in picker. Allows private assembly before publishing.
- **`active`** (`is_active = true`, `deleted_at IS NULL`) — surfaced in picker; still editable, but edits do NOT propagate to already-cloned PRs.
- **`inactive`** (`is_active = false`, `deleted_at IS NULL`, used at least once) — retired from picker; remains readable on historical PRs.

`deleted_at` is the soft-delete sentinel — used only when never instantiated.

**Authorization:** Templates maintained by Procurement Manager / Product Admin. Requestors can use but cannot edit (role-enforced). **Validation on save:** name unique within `workflow_id`; ≥ 1 detail row with `is_active = true` required to enable the picker entry.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) — sole consumer. **Create PR from Template** clones header + detail into a new `tb_purchase_request` + `tb_purchase_request_detail` at `pr_status = draft`.
- [purchase-request/03-user-flow-requestor](/en/inventory/purchase-request/03-user-flow-requestor) — REQ-HP-06 happy-path scenario uses this flow.
- [system-config/workflow](/en/inventory/system-config/workflow) — the `workflow_id` is the workflow the cloned PR enters at submit.
- [product](/en/inventory/product), [master-data/location](/en/inventory/master-data/location), [master-data/currency](/en/inventory/master-data/currency), [master-data/tax-profile](/en/inventory/master-data/tax-profile) — every line snapshots from these at template-edit time; clone re-resolves currency/rate but leaves other refs as-is.
- [templates/price-list](/en/inventory/templates/price-list) — sibling template under the [templates](/en/inventory/templates) umbrella.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template` (lines 2402-2430), `tb_purchase_request_template_detail` (lines 2466-2562), `tb_purchase_request_template_comment` (lines 2432-2464).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/procurement/purchase-request-template/`.
- **Carmen docs:** `../carmen/docs/purchase-request-management/purchase-request-template-ba.md`; `../carmen/docs/purchase-request-management/PR-User-Experience.md` (template-based creation flow).
