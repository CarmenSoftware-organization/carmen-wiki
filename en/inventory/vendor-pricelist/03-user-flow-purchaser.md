---
title: Vendor Pricelist — User Flow — Purchaser
description: Purchaser's flow within the vendor-pricelist module — four independent CRUD screens (Vendor, Price List, Price List Template, Request for Pricing), no unified workspace, no workflow engine.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, purchaser, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow — Purchaser

> **At a Glance**
> **Persona:** Purchaser &nbsp;·&nbsp; **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist) &nbsp;·&nbsp; **Screens:** Vendor, Price List, Price List Template, Request for Pricing — four separate top-level pages under Vendor Management, plus a `/vendor-management` KPI dashboard
> **Verified 2026-07-16:** no Manager-only high-value gate, no Finance co-signoff, no preferred-vendor "matrix," no reminders/campaign-pause/cancel actions — none of these have matching code.

## 1. Role in This Module

The **Purchaser** is the only internal persona with a write surface in this module. The previous version of this page consolidated "Purchaser / Purchasing Staff" and "Purchasing Manager" into one file on the theory that the Manager held an elevated, threshold-gated approval authority over the same screens. That threshold does not exist — there is no distinct approve/reject endpoint on Price List or Price List Template at all, so there is nothing for a Manager tier to gate. This file therefore documents a single Purchaser role covering all four screens: **Vendor** (master data — contacts, addresses, business type, certificates), **Price List** (the vendor's quoted prices), **Price List Template** (what a future RFQ will ask vendors to quote), and **Request for Pricing** (an outbound RFQ naming a template + vendor cohort).

## 2. Entry Point and Primary Flow

**Entry point:** Sidebar → **Vendor Management**. This lands on a KPI dashboard (`/vendor-management`) with widget tiles for active-vendor count, active-pricelist count, pricelists expiring soon, and RFQs upcoming/issued — not a unified tabbed workspace. Each of the four sub-screens (Vendor, Price List, Price List Template, Request Price List) is its own top-level list/detail/new route reached from the sidebar.

**Primary flow — building coverage for a new product line:**

1. **Maintain the vendor.** Sidebar → **Vendor** → **New** (or edit an existing vendor). Fill code, name, business type, address(es), contact(s), and any free-form info rows. Save.
2. **Build a Price List Template** (optional — only needed if pricing will be collected via an RFQ rather than entered directly). Sidebar → **Price List Template** → **New**. Fill `name`, `vendor_instructions`, default `currency_id`, `validity_period` (days), `reminder_days`, and vendor-facing instructions. Add products via the **Products** section — each product gets a default order unit and one or more MOQ-tier definitions stored as JSON (`order_unit_obj`). Save; optionally flip `status` to `active` via the template's status control (`PATCH :id/status` — a bare status write with no gate of any kind, so this step has no effect beyond the field value itself).
3. **Create a Request for Pricing** to solicit quotes. Sidebar → **Request Price List** → **New**. Pick a template, set `name`/`start_date`/`end_date`/`custom_message`, and add vendor rows (vendor + contact person/phone/email). Click Save — this single call both creates the RFQ header and, for every vendor row, generates a unique `pricelist_url_token` and signs a JWT the token maps to. There is no separate "launch" step.
4. **The vendor opens the portal.** Each vendor row's token forms the link `/pl/:url_token`. Visiting it calls the one real portal endpoint, which auto-creates a zero-priced draft `tb_pricelist` from the template (or returns the existing one) — see [03-user-flow-vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor) for the confirmed gap in what happens next.
5. **Edit and activate the pricelist directly.** Because the portal's own Save/Submit calls do not reach a working backend route today, the practical path to a usable pricelist is for the Purchaser to open the auto-created draft on the **Price List** screen directly, fill in real prices per product/MOQ tier, and set `status = active` from the edit form. Alternatively, skip the RFQ entirely: Sidebar → **Price List** → **New**, pick the vendor and currency, add detail rows, and save at `status = active` directly — this is the more common path for pricing that was negotiated by phone/email rather than solicited through a formal RFQ.
6. **Mark the preferred row, if more than one vendor quotes the same product.** On a pricelist's own **Products** grid, the `is_preferred` checkbox (Crown icon in view mode) is a per-row flag, set independently on each vendor's own pricelist. There is no cross-vendor comparison screen — the effect of the flag is visible only through the `price-compare` endpoint (`is_preferred desc, price asc`), which downstream PR/PO pricing consumes.

## 3. Decision Branches

- **Bulk-loading a vendor's price sheet.** The Price List screen supports CSV import (grouped upsert keyed on `pricelist_no`, with per-row product/unit/vendor/currency validation) and an Excel-style upload/download, in addition to manual row entry — useful when a vendor sends a spreadsheet rather than using the portal.
- **Correcting an active pricelist.** There is no immutability guard on `active` pricelists — the Purchaser can edit detail rows on an active pricelist directly; there is no requirement to inactivate first, unlike the design document's original (unimplemented) "open a new pricelist" rule.
- **A vendor cannot use the portal at all.** Set the pricelist's `submission_method = manual` or `email` directly on the Price List form and enter the prices the Purchaser received by phone or email — there is no dedicated "upload on vendor's behalf" screen distinct from the ordinary create/edit form.
- **Deciding which vendor is preferred for a product.** Toggle `is_preferred` on the winning vendor's own pricelist row. Nothing enforces "exactly one preferred row per product" automatically — a Purchaser could leave two vendors both marked preferred, in which case `price-compare`'s sort (`is_preferred desc, price asc`) picks whichever has the lower price as `selected`.

## 4. Exit Point / Handoffs

- **Price list active.** Once `tb_pricelist.status = active`, it is queryable by [purchase-request](/en/inventory/purchase-request) / [purchase-order](/en/inventory/purchase-order) / [good-receive-note](/en/inventory/good-receive-note) pricing logic via `price-compare` and the active-pricelist lookup endpoints. No further Purchaser action is required.
- **RFQ vendor never responds.** There is no auto-expiry, no reminder, and no "campaign closed" state — the RFQ row and its unresolved invitation rows simply remain in the list, distinguishable only by `has_submitted = false`.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — real status fields and the confirmed cross-persona handoff table.
- Business rules: [02-business-rules.md](./02-business-rules.md) — confirmed-vs-design-target status per rule.
- Data model: [01-data-model.md](./01-data-model.md) — entities, the multi-MOQ-per-product unique key on `tb_pricelist_detail`.
- Sibling: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — the external counterparty whose portal visit produces the draft this file's Step 5 edits.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) / [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — correction pages; neither persona exists distinctly in this module.
- Cross-link: [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [product](/en/inventory/product).
- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/`.
