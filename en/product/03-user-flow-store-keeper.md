---
title: Product — User Flow — Store Keeper
description: Store Keeper's flow within the product module — read-only barcode-driven lookup, location policy reference, and feedback paths.
published: true
date: 2026-05-15T15:30:00.000Z
tags: product, user-flow, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# Product — User Flow — Store Keeper

## 1. Role in This Module

The **Store Keeper** persona is a **read-only consumer** of the product catalogue, operating at the **floor / location level** during receiving, picking, transfers, and counts. Within the product module their authority is **lookup only**: they scan barcodes (`tb_product.barcode`) for fast identification on mobile devices, view product detail (handling instructions from `tb_product.info` JSON, shelf life, storage requirements, perishable flags), reference per-location stock policy (`tb_product_location.min_qty / max_qty / par_qty / re_order_qty`) for context during counts and replenishment, and post comments (`tb_product_comment`) for barcode mismatches and operational issues. They do **not** create products, do **not** edit any master-data field, do **not** edit per-location stock policy (Inventory Controller role per [[inventory/02-business-rules]] `INV_AUTH_004`), do **not** edit unit conversions, and do **not** participate in product lifecycle transitions. Their transactional activity (receiving GRN, stock-in / stock-out, running physical / spot counts) lives in the [[good-receive-note]], [[inventory]], [[physical-count]], and [[spot-check]] persona files — this page covers only the **product-catalogue lookup** surface they touch in support of that work.

## 2. Entry Point and Primary Flow

**Entry points:** Three primary paths into the Store Keeper's interaction with the product module, all read-only and most via mobile.

- **Barcode scan (mobile)** — the dominant flow during receiving, picking, counting. The Store Keeper scans the product label; the mobile app resolves the scanned identifier against `tb_product.barcode` and surfaces the resolved product to the transactional flow.
- **Product detail (mobile or desktop)** — direct browse to a product to view handling instructions, shelf life, classification, or to verify the per-location stock policy. Used during count execution or when triaging a receiving issue.
- **Per-location policy reference** — viewing `tb_product_location` for a product at a specific location, to compare on-hand against par / min / max during a count or replenishment check.

**Primary flow (barcode scan during receiving, 5 steps — the dominant pattern):**

1. **Open the receiving flow on mobile.** From within [[good-receive-note]]'s Receiver flow, the Store Keeper is at the GRN line entry screen. They tap the scan button.
2. **Scan the barcode.** The mobile camera reads the product label (UPC / EAN / CODE128 per `PRD_VAL_005`); the app posts the scanned value to the lookup endpoint. The endpoint queries `tb_product.barcode = <scanned>` filtered to active products (`product_status_type = active`, `is_active = true`, `deleted_at IS NULL`). If exactly one match is found, the resolved product is returned with id, code, name, base unit, classification path, and handling notes.
3. **Confirm the resolved product.** The mobile app shows the resolved product card with the photo (if any), code, name, local name, and the next-action choice ("Add to this GRN line", "View details", "Wrong product"). The Store Keeper confirms or pivots — if the resolved product matches the physical item in hand, they add to the line; if it doesn't, they pivot to the manual-search or barcode-mismatch path.
4. **Reference handling / location context (optional).** Before adding to the line, the Store Keeper may tap "View details" to see:
   - **Handling notes** from `tb_product.info` JSON — storage temperature, shelf life, fragile / hazardous flags, allergens.
   - **Per-location stock policy** at the receiving location — `tb_product_location.min_qty / max_qty / par_qty` for context (is this receipt above max? below min?).
   - **Standard cost** (`tb_product.standard_cost`) for high-value items as a sanity-check against the GRN line's unit cost.
   - **Vendor mapping** (`tb_product_tb_vendor`) — does the receiving vendor match the configured vendor for this product?
5. **Add to GRN line.** The GRN line is populated with `product_id`, base unit, and the picked order-unit (from `tb_unit_conversion`). The Store Keeper enters qty (in order-unit) and the line is saved. The product master is unchanged.

The **count / spot-check** flow is a parallel pattern:

- Scan barcode to identify the product on the shelf.
- Reference `tb_product_location.par_qty` for the count location — does the counted qty match par? Below par? Above par?
- Reference handling notes — is the product perishable (expiry-date required on the count line per `INV_VAL_006` extension)?
- Add the count line; the product is read, not edited.

The **stock-in / stock-out** flow (manual adjustments per [[inventory/03-user-flow-store-keeper.md]]):

- For non-barcode workflows (e.g. a found-stock entry with no label), the Store Keeper searches by code or name in the manual picker. Same scope rules apply (`active` + `is_active = true` + non-deleted).
- For perishable products, the form prompts for expiry date (required per `INV_VAL_006`); the perishable flag comes from `tb_product.info` JSON (or by category convention).

The **comment / feedback** flow:

- **Barcode mismatch.** When a scanned barcode resolves to the wrong product (the physical label says "Spring Water 1L" but the resolved product is "Spring Water 500ml"), the Store Keeper posts a comment on the resolved product with the scanned barcode and a photo of the physical label per [03-user-flow.md](./03-user-flow.md) Section 4. The Product Administrator updates `tb_product.barcode` (or the SKU mapping) and replies. The Store Keeper rescans to confirm.
- **Unresolved barcode.** When a scan returns no match (`PRD_VAL_005` would block adding the barcode if it conflicted; here the issue is the barcode is simply not in the catalogue), the Store Keeper either uses the manual search to find the product by code/name and post a comment requesting the Product Administrator add the barcode mapping, or the Product Administrator creates a new product entirely if it's a new SKU.
- **Handling-note correction.** If the storage / shelf-life instructions in `tb_product.info` are wrong (e.g. the bag says "Refrigerate at 4°C" but the master says "Ambient"), the Store Keeper posts a comment so the Product Administrator can update the JSON. Critical safety-related corrections (allergen omission, hazard flag missing) are escalated out-of-band in addition to the comment.
- **Location-policy adjustment.** When the configured `min_qty` / `max_qty` / `par_qty` feels wrong for a location (constant stock-outs at the min, or constant overstock above max), the Store Keeper posts feedback on `tb_product_location` (via the product detail's location tab). The handoff is to **Inventory Controller** (not Product Administrator), per `INV_AUTH_004`.

## 3. Decision Branches

- **Scan resolves to one product — confirm or pivot.** Single resolved match is the happy path; the Store Keeper confirms or, if the physical item doesn't match, taps "Wrong product" to enter the barcode-mismatch comment flow.
- **Scan resolves to multiple products (rare).** Per `PRD_VAL_005` barcode uniqueness is application-enforced, so true duplicates should not exist in live state. If the lookup returns multiple matches (typically because one product is soft-deleted but the application's barcode index includes it), the app shows a picker; the Store Keeper selects the active one. This case typically indicates an underlying data quality issue — the Store Keeper posts a comment so the Product Administrator can clean up.
- **Scan resolves to no product — manual fallback.** No match: switch to manual search by code or name. If the product genuinely doesn't exist, post a new-product request comment and route the work back to the floor supervisor or hold the receiving line.
- **Inactive product encountered (rare).** The barcode-lookup endpoint filters to active products by default. If the Store Keeper toggles the inactive filter (rare on mobile — typically a desktop feature), they may see inactive products in detail view but cannot add them to a new transactional line per `PRD_XMOD_001`. The picker rejects.
- **Reference standard cost vs assume vendor-quoted cost on GRN.** The Store Keeper's role on a GRN is to confirm receipt; they're not setting the unit cost (the GRN line carries it from PO / pricelist). However, when the GRN line cost diverges materially from `standard_cost`, the Store Keeper flags it on the GRN's comment thread so the Receiver / Inventory Manager can investigate before commit. This is a [[good-receive-note]] concern but the data is read from the product master.
- **Use barcode for picking (SR) vs use code for finding.** During SR dispatch (issuing stock to an outlet), the Store Keeper typically scans the barcode to confirm they're picking the right product from the bin. During SR composition (the outlet manager raising the request), code-based search is more common. The product master surface is the same; the entry path differs.
- **Per-location policy as a soft signal, not a hard gate.** `min_qty` / `max_qty` / `par_qty` are advisory — they trigger alerts and replenishment suggestions but don't block transactions. A receipt that pushes on-hand above `max_qty` will succeed; the system flags it for review but doesn't reject. The Store Keeper uses these values as context for count investigations (a count that's far from par may indicate an issue worth investigating) rather than as transactional gates.
- **Comment vs activity-log entry.** Comments (`tb_product_comment`) are user-driven, free-text discussion. Activity log is system-driven (status transitions, field changes). The Store Keeper posts in comments; system events post in activity log. Both are queryable but serve different purposes.

## 4. Exit Point / Handoffs

The Store Keeper's interaction with the product master ends at one of these boundaries:

- **Barcode resolved, line populated, work continues in the source module.** The product master was read; the GRN / count / SR / stock-in / stock-out line is populated with `product_id`. The product master is unchanged; the Store Keeper's transactional work proceeds in the source module per its persona file.
- **Comment posted for barcode mismatch.** The barcode-mismatch comment is logged on the affected product; the Product Administrator picks it up from the comments queue per [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) Section 4. The Store Keeper may need to defer the GRN line / count line until the master is updated and the rescan succeeds (or use manual search to proceed with the work and post the comment for later master-data clean-up).
- **Comment posted for unresolved barcode / new-product request.** Same as above; the work pauses or proceeds via manual search depending on the urgency.
- **Per-location policy feedback routed to Inventory Controller.** Min / max / par / reorder feedback is logged via comment on the product's location tab; the **Inventory Controller** picks it up (not Product Administrator). The Store Keeper's involvement on the policy concern ends; the Inventory Controller may engage them for context during the review per [[inventory/03-user-flow-inventory-controller.md]].
- **Handling-note correction posted.** Comment on the product with the proposed correction (storage temp, shelf life, allergen flag) is logged; the Product Administrator updates `tb_product.info` JSON per their flow.
- **Lookup session ends without state change.** When the Store Keeper used the catalogue purely for reference (e.g. checking handling instructions before opening a perishables shipment), the session ends with no master change and no transactional posting.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the canonical product-record state machine (Section 2 — the Store Keeper is a consumer of the `active` state) and the cross-persona handoff table (Section 4 — Store Keeper → Product Administrator on barcode mismatch / handling-note correction, Store Keeper → Inventory Controller on per-location policy feedback).
- Sibling: [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) — upstream persona that creates / maintains the catalogue the Store Keeper reads; barcode-mismatch and handling-note corrections route to this persona.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — parallel read-only consumer persona at the procurement layer.
- Sibling: [01-data-model.md](./01-data-model.md) — the `tb_product` shape (especially `barcode`, `info` JSON, `inventory_unit_id` referenced in step 4 of the primary flow), `tb_product_location` for per-location policy (step 4 detail), `enum_product_status_type` (the active filter on the barcode-lookup endpoint).
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation rule `PRD_VAL_005` (barcode uniqueness — application-enforced), calculation rule `PRD_CALC_001` (classification path), authorization rules `PRD_AUTH_007` (Store Keeper read with barcode lookup) and `PRD_AUTH_008` (Store Keeper read of per-location policy — but not edit); cross-module rule `PRD_XMOD_001` (inactive product rejected on new line) referenced in the decision branch.
- Related: [[good-receive-note]] — primary module for the dominant barcode-scan flow (step 1 entry); product master is consumed at line entry. The product's deviation tolerances (`PRD_CALC_003`) gate the GRN line's variance approval.
- Related: [[inventory]] — `tb_product_location` is read here; the **edit** authority belongs to the Inventory Controller per [[inventory/02-business-rules]] `INV_AUTH_004`. Per-location policy feedback routes to that persona.
- Related: [[physical-count]] / [[spot-check]] — count execution uses barcode scan and per-location policy reference per Section 2 (count / spot-check flow).
- Related: [[store-requisition]] — SR dispatch / picking uses barcode scan for bin-pick confirmation; product master is consumed at the pick step.
- Related: [[inventory-adjustment]] — stock-in / stock-out for manual adjustments; perishable flag from `tb_product.info` is referenced at line save per the per-product expiry rule.
