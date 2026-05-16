---
title: Product — User Flow
description: Product master-data lifecycle and persona-specific flow files.
published: true
date: 2026-05-17T11:00:00.000Z
tags: product, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# Product — User Flow

> **At a Glance**
> **Module:** [[product]] &nbsp;·&nbsp; **Personas:** Product Administrator (CRUD owner) &nbsp;·&nbsp; Purchaser (read-only) &nbsp;·&nbsp; Store Keeper (read-only)
> **Workflow lifecycle:** Master-data — no `doc_status`, no period lock. `(none) → active ↔ inactive → soft-deleted (restore possible)`. `is_active = false` hides from pickers. Every transition is auditable and instantaneous.
> **Drill into per-persona views below for action-level detail**

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `product` module. Product is **master-data**, not transactional — there is no posting event, no journal-entry fan-out, no period boundary that locks the record. The lifecycle a persona walks is the **lifecycle of a catalogue row**: it is created by the Product Administrator (often via import for the initial catalogue load, then individually for new SKUs and menu launches), it stays `active` while in use by procurement and operations, it may be deactivated when retired (subject to in-use guards), and it is soft-deleted when truly retired (subject to harder in-use guards). The three personas the module serves have very different relationships to this lifecycle — the Product Administrator **owns** it, the Purchaser and Store Keeper are **consumers** who look up and read the catalogue during their own document workflows.

Section 2 below describes the **product-record state machine** — the canonical set of legal transitions independent of who acts. Section 3 indexes the three per-persona drill-down files. Section 4 summarises the cross-persona handoffs — which are intentionally light in this module: the Product Administrator's work feeds the consumers but the consumers do not feed back into product-lifecycle transitions (beyond comments / feedback). The handoffs that exist are mostly Purchaser → Product Administrator (flag stale catalogue entry, request new product) and Store Keeper → Product Administrator (flag barcode mismatch, request location-policy adjustment).

Master-data note: because Purchaser and Store Keeper are lookup-only consumers, their persona files are **substantially narrower in scope** than the equivalent transactional-module persona files. There is no draft → submit → approve workflow they drive; there is just search, filter, scan, read, and (where applicable) comment. The Product Administrator's persona file, conversely, is the wide one — it covers the full CRUD surface, the classification chain, units and conversions, location mapping, vendor mapping, lifecycle transitions, and bulk import / export.

## 2. Product Record Lifecycle

A single state machine governs the product record:

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create (UI form or bulk import) | `active` | Product Administrator (`PRD_AUTH_001`, `PRD_AUTH_003` for bulk) | Validation rules `PRD_VAL_001`–`PRD_VAL_016` all pass. Classification (`tb_product_item_group_id`), base unit (`inventory_unit_id`), and code/name are required. Tax-profile and deviation tolerances may be inherited from the classification chain per `PRD_CALC_002`–`PRD_CALC_003`. Writes `tb_product` with `product_status_type = active`, `is_active = true`. Activity log records the create. |
| `active` | edit fields (name, description, classification, units mapping, location policy, vendor mapping, deviation tolerances, standard_cost, tax-profile override, info JSON, certification JSON) | `active` | Product Administrator | Validation rules re-run per the edited fields. `inventory_unit_id` is **immutable** once the product has any inventory history (`PRD_VAL_003`). Classification changes are prospective per `PRD_LIFE_010`. Activity log records each field-level change. |
| `active` | deactivate | `inactive` | Product Administrator (`PRD_AUTH_004`) | Lifecycle guard `PRD_LIFE_002`: no open PR / PO / SR line may reference the product. Soft-block if referenced by a published recipe (override option available with activity-log reason). On override, affected recipes may be auto-flagged for review. Sets `product_status_type = inactive`; `is_active` unchanged. Picker exclusion takes effect immediately. |
| `inactive` | re-activate | `active` | Product Administrator (`PRD_AUTH_004`) | Lifecycle guard `PRD_LIFE_003`: classification chain still valid. Inheritance values recomputed at next read. Recipe-review flags from `PRD_LIFE_002` are cleared. |
| `active | inactive` | hard-disable (`is_active = false`) | `(hidden — not picker-visible anywhere)` | Product Administrator | Lifecycle guard `PRD_LIFE_005`: same as deactivate guards plus the rule that `is_active = false` implies `product_status_type = inactive`. Used for products that should disappear from admin views (e.g. true end-of-life or compliance-mandated removal). |
| `active | inactive` | soft-delete | `soft-deleted` | Product Administrator (`PRD_AUTH_001`) | Hard guards `PRD_LIFE_004`: zero current on-hand (derived) at every location; no non-terminal document line referencing the product (PR / PO / GRN / SR / count / spot-check / credit-note / pricelist / recipe-ingredient); no non-deleted recipe ingredient. Sets `deleted_at`, `deleted_by_id`. The `(code, name)` becomes re-usable. |
| `soft-deleted` | restore | `active` | Product Administrator (exceptional) | Lifecycle guard `PRD_LIFE_009`: the `(code, name)` must still be unique among live products (rejected if a new product has taken the freed code/name in the interim). Clears `deleted_at` / `deleted_by_id`. |

Notes:

- **No workflow `doc_status`.** Unlike the transactional modules, product has no `draft → in_progress → completed` progression. Every save is immediate; every transition is auditable but instantaneous.
- **No period boundary.** Product master is not period-locked. Edits remain possible even when the surrounding accounting period is `closed` or `locked` — only the **transactional** modules respect the period lock.
- **Bulk import is the dominant create path.** For initial catalogue load and for new-property go-lives, the Product Administrator runs import in dry-run mode, reviews the validation report, fixes errors, then runs strict-mode commit. The state machine above applies per-row; passing rows enter `active`, failing rows are reported.
- **Audit log is the conversation surface for lifecycle events.** Every transition records actor / timestamp / reason. The comment table (`tb_product_comment`) holds human discussion (typically inbound feedback from Purchaser / Store Keeper); the activity log holds system events.

## 3. Persona Index

Each persona below has a dedicated drill-down file describing their entry point, primary flow, decision branches, and exit point. Slugs match the persona role; clicking the link opens the per-persona view.

- [Product Administrator](./03-user-flow-product-admin.md) — owns the catalogue. Creates and maintains products, categories, sub-categories, item-groups, units. Configures conversion factors, attributes (via `info` JSON), location mappings (`tb_product_location`), vendor mappings (`tb_product_tb_vendor`). Runs imports / exports. Manages the product lifecycle (activation, deprecation, deletion). The wide persona — most of the module's surface lives in their flow.
- [Purchaser](./03-user-flow-purchaser.md) — looks up products to compose PRs and POs. Read-only consumer. References `standard_cost` and the derived last-receiving-cost (`PRD_CALC_008`) for budget-vs-actual reference; verifies order-unit conversions (`tb_unit_conversion` with `unit_type = order_unit`) and vendor mappings (`tb_product_tb_vendor`) before adding a line to a PR / PO; comments on stale or missing catalogue entries to route back to Product Administrator. Their lifecycle ownership is none — they read.
- [Store Keeper](./03-user-flow-store-keeper.md) — looks up products during receiving, picking, transfers, counts. Read-only consumer. Scans barcodes (`tb_product.barcode`) for fast identification; references per-location stock policy (`tb_product_location.min_qty` / `max_qty` / `par_qty`) and per-product handling notes (storage instructions, shelf life from `tb_product.info` JSON). Their lifecycle ownership is also none — they read and comment.

## 4. Cross-Persona Handoffs

The table below captures the moments where product work moves from one persona's responsibility to another's. Because Purchaser and Store Keeper are read-only, most handoffs are unidirectional — the Product Administrator pushes catalogue state to the consumers, and the consumers occasionally pull updates back via comment / feedback channels.

| From persona | Trigger | To persona | System state at handoff |
| ------------ | ------- | ---------- | ----------------------- |
| Product Administrator | New product created and `active`; classification, units, conversions, location mapping, vendor mapping configured | Purchaser, Store Keeper | `tb_product.product_status_type = active`, `is_active = true`. Picker on every downstream module immediately surfaces the new product. No explicit notification — pickers are read-on-demand. |
| Product Administrator | Product `standard_cost` updated above the tenant SoD threshold | Cost Controller / Finance (via SoD gate `PRD_AUTH_012`) | Activity log records the change. If the workflow requires explicit approval, the change may be staged (application convention) until Cost Controller / Finance acknowledges — for installations without a hard approval workflow, the change is immediate and the audit log is the soft control. |
| Product Administrator | Product deactivated | Purchaser, Store Keeper | Pickers filter the product out of new-document defaults. Existing line items on active documents remain valid. Recipe references (if any) get a recipe-review flag if the deactivation was overridden per `PRD_LIFE_002`. |
| Purchaser | Stale or missing catalogue entry encountered while composing a PR / PO | Product Administrator | Purchaser posts a comment (`tb_product_comment`) on the affected product (or, for a missing product, posts a "new product request" via a comment on the closest existing product or via a separate request channel). Product Administrator picks up the comment, investigates, updates the master or creates the new product, replies on the comment thread. |
| Store Keeper | Barcode mismatch during receiving or count (the scanned barcode resolves to the wrong product, or doesn't resolve at all) | Product Administrator | Store Keeper posts a comment on the affected product with the scanned barcode and the physical product label. Product Administrator validates the report (typically by checking the vendor pricelist or the GRN) and updates `tb_product.barcode`. The Store Keeper rescans to confirm. |
| Store Keeper | Per-location stock policy needs adjustment (min / max / par / reorder feels wrong for a location) | Inventory Controller (per [[inventory/02-business-rules]] `INV_AUTH_004`) | Store Keeper posts a comment on the product or on `tb_product_location` (via the product's location-policy tab). Inventory Controller — **not** Product Administrator — owns replenishment-policy edits, so the routing is to inventory. Product Administrator may participate if a structural change to the location-mapping itself is needed (e.g. adding a new location to the product). |
| Product Administrator | Bulk import job completes | Product Administrator (self — reviews error report) | Import job's `created_by_id` is the Product Administrator; error report is downloadable. No external handoff — the Administrator iterates on the import until successful. |
| System Administrator | RBAC role configuration changed for the product module | All personas | Persona scopes may shift (e.g. an additional approver role added to the SoD threshold per `PRD_AUTH_012`). No transaction state change; new rules apply prospectively. |
| Auditor | Audit query complete | (no downstream action) | Read-only handoff — Auditor consumes product master state, comment history, and activity log without writing back. |

## 5. References

- `../carmen/docs/product-management/PROD-PRD.md` — primary PRD describing the product-management persona set (Product Manager, Category Manager, Inventory Manager, Finance Team, Operations Team, System Administrator, Sustainability Officer). This wiki collapses the carmen/docs persona set into three operational personas (Product Administrator, Purchaser, Store Keeper) matched to the hospitality-ERP user reality — see Section 3.
- `../carmen/docs/product-management/product-master-prd.md` — UI-anchored PRD describing the Product List page, Product Detail page (with tabs for header, attributes, units, conversions, store/location assignment, latest purchase, activity log), and the data model behind each tab. The user-flow narrative in the per-persona files maps directly onto these UI surfaces.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_product_status_type` (two values, `active | inactive`, not three) and the `enum_unit_type` (`order_unit | ingredient_unit`); the classification chain shape (three levels, not five); the divergences against carmen/docs that shape the "no `discontinued` state" framing here.
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation (`PRD_VAL_*`), calculation / inheritance (`PRD_CALC_*`), authorization (`PRD_AUTH_*`), lifecycle (`PRD_LIFE_*`), and cross-module (`PRD_XMOD_*`) rules referenced by every transition in Section 2.
- Related modules: [[inventory]] (consumer of `product_id` on every transaction; in-use guard for product delete), [[costing]] (`PRD_XMOD_003` — `standard_cost` source, FIFO/WA method is on business-unit not product), [[good-receive-note]] (consumer; deviation tolerances gate receiving variance), [[store-requisition]] (consumer; product–location mapping drives par-level sizing), [[purchase-request]] / [[purchase-order]] (consumer; order-unit conversions), [[vendor-pricelist]] (consumer; product–vendor join), [[recipe]] (consumer; product as ingredient — `is_used_in_recipe` filter on picker).
