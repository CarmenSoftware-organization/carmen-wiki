---
title: Product — User Flow — Purchaser
description: Purchaser's flow within the product module — read-only lookup, reference, and feedback paths.
published: true
date: 2026-05-15T15:30:00.000Z
tags: product, user-flow, purchaser, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# Product — User Flow — Purchaser

## 1. Role in This Module

The **Purchaser** persona is a **read-only consumer** of the product catalogue. Within the product module their authority is **lookup only**: they search and filter the live catalogue, view product detail (including standard cost, last-receiving cost per `PRD_CALC_008`, unit conversions, vendor mapping, classification, tax profile), reference the order-unit conversion factors when composing PR / PO lines, and post comments (`tb_product_comment`) on products they find stale or incorrect or to request a new product to be created. They do **not** create products, do **not** edit any master-data field, do **not** edit unit conversions or classification, do **not** approve standard-cost changes (Cost Controller / Finance role), do **not** edit per-location stock policy (Inventory Controller role), and do **not** participate in product lifecycle transitions. Their inventory-side activity (composing PRs and POs) is fully transactional and lives in the [[purchase-request]] and [[purchase-order]] persona files — this page covers only the **product-catalogue lookup** surface they touch in support of that work.

## 2. Entry Point and Primary Flow

**Entry points:** Two primary paths into the Purchaser's interaction with the product module — one direct (browsing the catalogue) and one indirect (the product picker on a PR / PO line).

- **Product Management → Products (list / search)** — direct browse / search. Used when researching catalogue completeness ahead of a planned procurement run, checking the standard cost of a basket of items, or verifying vendor mappings before opening a PR.
- **PR / PO line product picker** — indirect, embedded inside the PR / PO composition flow. The picker filters by `product_status_type = active`, `is_active = true`, and `deleted_at IS NULL` per `PRD_AUTH_009`. Pickers may be further scoped by vendor (when composing a PO against a specific vendor, the picker filters to products with a `tb_product_tb_vendor` mapping to that vendor).

**Primary flow (look up a product to add to a PR line, 6 steps — the dominant pattern):**

1. **Open the PR line picker.** From within [[purchase-request]]'s line entry, click the product field to open the picker. The picker shows the active catalogue with columns for code, name, base unit, standard cost, last-receiving cost (derived per `PRD_CALC_008`), and vendor count (number of mapped vendors).
2. **Search / filter.** Type code, name, local name, barcode, or SKU. Search is full-text per `TR-SEARCH-*` (carmen/docs PRD § 5.5). Filter by category / sub-category / item-group (classification dropdown), by vendor (the vendor scope), or by other attributes surfaced via `tb_product.info` JSON keys. Filtering is read-only — the Purchaser cannot save filters into the master, only into their personal saved-view (frontend-only feature).
3. **Inspect the product detail (optional).** Click through to the full product detail view for deeper context: classification path (`PRD_CALC_001`), inherited tax profile (`PRD_CALC_002`), deviation tolerances (`PRD_CALC_003`), all defined unit conversions (`tb_unit_conversion` rows), vendor mapping (`tb_product_tb_vendor` rows with `vendor_product_code` cross-reference), per-location stock policy (`tb_product_location` rows — informational; the Purchaser doesn't edit), and the latest purchase history (last few GRN receipts with date / vendor / unit cost). The Latest Purchase tab is the Purchaser's go-to for price benchmarking.
4. **Select the product.** Choose the row in the picker; the PR / PO line is populated with `product_id`, `inventory_unit_id` (the product's base unit), and the **default order-unit** (the `tb_unit_conversion` row with `is_default = true`, `unit_type = order_unit`). The Purchaser may override the order-unit by picking another configured conversion (e.g. switch from `CASE` to `EACH` for a smaller order); per `PRD_XMOD_006`, a unit not defined in `tb_unit_conversion` for the product cannot be used (the picker only shows defined conversions).
5. **Enter qty and unit-price.** Qty in the chosen order-unit, unit-price (typically pre-populated from the latest `tb_pricelist_detail` or last GRN cost). The system computes the base-unit qty per `PRD_CALC_005` (`order_unit_qty × conversion_factor = base_unit_qty`) for downstream inventory and costing. The price-deviation tolerance (`PRD_CALC_003` → effective `price_deviation_limit`) is read at this point; a unit-price outside tolerance flags for above-threshold approval per `PR_VAL_*`.
6. **Save the line.** The PR / PO line is added; the Purchaser's interaction with the product master ends. The product itself is unchanged (read-only).

The **comment** flow is the secondary path:

- **Stale or missing catalogue feedback.** When the Purchaser encounters a product whose data is wrong (incorrect base unit, missing vendor mapping, standard cost out of date, missing conversion factor for a unit they need), or when a product they expect to find doesn't exist in the catalogue, they post a comment on the relevant product (`tb_product_comment.message`). Attachments can include screenshots of vendor quotes or supplier catalog pages. For a missing product, the comment is posted on the closest existing product or via a separate "new product request" channel; the Product Administrator picks it up from the comments queue per [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) Section 2.
- **Pricing escalation.** If a vendor quote diverges materially from the recorded standard cost (`tb_product.standard_cost`) and would breach the deviation tolerance, the Purchaser flags it via comment so the Product Administrator (with Cost Controller sign-off per `PRD_AUTH_012`) can update the standard cost. The Purchaser does **not** edit `standard_cost` directly.

The **catalogue-browse** flow (entry point 1) follows the same shape but is used outside the context of a specific PR / PO — typically for procurement-planning research or for verifying catalogue completeness before a quarterly menu refresh.

## 3. Decision Branches

- **Picker filter — include inactive products?** By default the picker shows `product_status_type = active`. The Purchaser may toggle a "show inactive" filter to find historical products (e.g. researching what was used last year before the seasonal SKU was deactivated). Selecting an inactive product for a **new** line is rejected per `PRD_XMOD_001` — the picker greys out inactive rows when the toggle is on, and direct API submission of an inactive `product_id` is rejected at the source-module's line save. This filter is read-only — toggling it doesn't change the master.
- **Choose order-unit on the line.** The picker shows the default order-unit (`is_default = true`) but allows switching to any other configured order-unit conversion. If the unit the Purchaser needs is not configured, the only paths are: (a) post a comment requesting the Product Administrator add the conversion, then wait, or (b) use a different configured unit and adjust the qty manually (less reliable — system calculations may be off). The first path is strongly preferred.
- **Standard cost vs last-receiving cost.** The product detail surfaces both:
  - `standard_cost` is the Product-Administrator-managed reference; updated on a cadence (monthly / quarterly per Cost Controller's process).
  - **Last-receiving cost** (derived per `PRD_CALC_008`) is the most recent actual unit cost from a GRN — "what we last actually paid".
  
  The Purchaser uses both: standard cost is the budget reference (compare vendor quote against standard, flag deviation); last-receiving cost is the market reference (compare current quote against the most recent actual purchase). A vendor quote materially above standard but in line with the last receiving is "market drift" — flag for standard-cost refresh. A vendor quote above both is "vendor anomaly" — investigate the vendor.
- **Vendor scope filter on PO.** When composing a PO against a specific vendor, the picker scopes to products with a `tb_product_tb_vendor` mapping to that vendor (per `PRD_AUTH_006`). If the product the Purchaser wants to add is not mapped to the vendor, the line cannot be saved against that PO — either change the vendor on the PO, or post a comment requesting the Product Administrator add the vendor mapping. (For mixed-vendor PRs that explode into multiple POs, this filter applies per the chosen-vendor selection on PO creation.)
- **Comment vs out-of-band escalation.** For routine catalogue feedback (stale price, missing conversion, barcode mismatch), the comment thread is the standard channel. For urgent issues (a critical SKU missing during a menu launch, vendor mapping wrong on a same-day PO), the Purchaser may escalate via direct channel (chat, email) and post the comment as the audit-trail anchor. The catalogue UI does not have a separate "urgent" comment type.
- **Search by barcode vs by code.** For routine SKU lookup, search by code (most products carry the same code internally as in vendor catalogs). For receiving-driven research (Purchaser cross-checks a GRN line's product), search by barcode (`tb_product.barcode`) matches the scanned identifier.

## 4. Exit Point / Handoffs

The Purchaser's interaction with the product master ends at one of these boundaries:

- **PR / PO line saved.** The picker resolved a `product_id`; the line is populated and saved on the PR / PO. The product master is unchanged. The Purchaser's involvement on the catalogue side is done; their work continues in [[purchase-request]] / [[purchase-order]] as the document's owner.
- **Comment posted, awaiting Product Administrator.** Stale-catalogue feedback or new-product request is logged as a comment on the relevant product (or the closest existing product). The Product Administrator picks it up from the comments queue per [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) Section 4 ("Inbound comment resolved"). The Purchaser may receive a notification when the comment is resolved (depending on tenant configuration); if blocked on the resolution, the Purchaser may need to defer the PR / PO line until the master is updated.
- **Pricing escalation routed.** A vendor quote breaching standard-cost deviation tolerance triggers a comment / escalation flow; resolution is on the Product Administrator + Cost Controller / Finance side per `PRD_AUTH_012`. The Purchaser holds the PR / PO line at draft pending the standard-cost refresh, or proceeds with the line and accepts the deviation flag on the document workflow.
- **Picker closed without selection.** When the Purchaser couldn't find what they needed (missing product, missing vendor mapping, missing conversion), the picker is closed and a comment / new-product request is posted. The PR / PO line stays at draft.
- **Browse-only research session ends.** When the catalogue browse was for planning research (not tied to a specific PR / PO), the Purchaser's session ends without action — knowledge gained informs subsequent procurement work but no state change is committed.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the canonical product-record state machine (Section 2 — the Purchaser is a consumer of the `active` state) and the cross-persona handoff table (Section 4 — Purchaser → Product Administrator comment / new-product-request route).
- Sibling: [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) — upstream persona that creates / maintains the catalogue the Purchaser reads. The comment-resolution handoff lives there.
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — parallel read-only consumer persona at the operational floor.
- Sibling: [01-data-model.md](./01-data-model.md) — the `tb_product` shape the picker surfaces (steps 1–2 of the primary flow), `tb_unit_conversion` with `unit_type = order_unit` (step 4–5), `tb_product_tb_vendor` for vendor scope (step 2 vendor filter and decision branch on PO scope), `enum_product_status_type` (the active filter).
- Sibling: [02-business-rules.md](./02-business-rules.md) — calculation rules `PRD_CALC_001` (classification path), `PRD_CALC_002` (tax-profile inheritance), `PRD_CALC_005` (conversion factor), `PRD_CALC_008` (last-receiving cost — derived) referenced in steps 3 and 5; authorization rules `PRD_AUTH_005` (Purchaser read-only authority), `PRD_AUTH_006` (vendor-mapping read), `PRD_AUTH_009` (picker default filter); cross-module rule `PRD_XMOD_001` (inactive product rejected on new line) referenced in the decision branch.
- Related: [[purchase-request]] / [[purchase-order]] — primary modules the Purchaser owns; product picker is embedded in the line entry. The product's deviation tolerances (`PRD_CALC_003`) gate above-threshold approval on these documents.
- Related: [[vendor-pricelist]] — pricelists reference products; the Purchaser reads them in support of PR / PO line pricing.
- Related: [[good-receive-note]] — the GRN's actual receiving cost feeds back into `tb_inventory_transaction_cost_layer.cost_per_unit` which is what `PRD_CALC_008` (last-receiving cost) surfaces back to the Purchaser. The data flow is round-trip but the Purchaser is a read-side participant only.
