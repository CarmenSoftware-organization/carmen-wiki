---
title: Vendor Pricelist — Test Scenarios — Purchaser
description: Purchaser's test cases (happy path, validation, edge cases) for vendor-pricelist, grounded in the five real CRUD screens.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: vendor-pricelist, test-scenarios, purchaser, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Test Scenarios — Purchaser

> **At a Glance**
> **Persona:** Purchaser &nbsp;·&nbsp; **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist)
> **Executable coverage (2026-09-22):** `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts` (31) + `docs/test-cases/gaps/150-vendor-gap.md` (54); `tests/159-pl.spec.ts` (28) + `gaps/159-pl-gap.md` (65); `tests/160-pl-template.spec.ts` (33) + `gaps/160-pl-template-gap.md` (58); `tests/043-certification.spec.ts` (6) + `gaps/043-certification-gap.md` (29); no spec for Request for Pricing.
> **Verified 2026-07-16, re-checked 2026-09-22:** no Manager-elevation tier, no high-value threshold, no quality-score gate — none of these have matching code. New rows below cover Send email, `submitted`, certification, and the vendor tax/rating columns.

This page captures the test scenarios the Purchaser drives across the module's five screens. There is no distinct Manager tier — every scenario below is reachable by any user holding the relevant screen's edit permission.

## 1. Happy Path

| # | Scenario | Steps | Expected |
| - | -------- | ----- | -------- |
| VPL-PUR-HP-01 | Create a vendor with code + name + business type | Sidebar → **Vendor** → **New**. Fill code, name, pick a business type. Save. | Vendor row created; found in list by name. Matches `TC-VEN-030003`. |
| VPL-PUR-HP-02 | Create a Price List Template with product + MOQ tiers | Sidebar → **Price List Template** → **New**. Fill name, default currency, validity period. Add a product with a default order unit + MOQ tiers. Save. | `tb_pricelist_template` + one `tb_pricelist_template_detail` row created at `status = draft`. Matches `160-pl-template.spec.ts`. |
| VPL-PUR-HP-03 | Flip a template's status via the dedicated status endpoint | Open the saved template. Change `status` to `active`. | `PATCH :id/status` fires; `status = active`. No validation runs (no "≥1 product" gate) — confirmed via `pricelist-templates.service.ts`'s `updateStatus()`. |
| VPL-PUR-HP-04 | Create a Request for Pricing naming a template + two vendors | Sidebar → **Request Price List** → **New**. Pick the template. Add vendor rows for `V1` + `V2`. Save. | `tb_request_for_pricing` row + two `tb_request_for_pricing_detail` rows created in the same call, each with a fresh `pricelist_url_token`. No separate "launch" action exists. |
| VPL-PUR-HP-05 | Email the RFQ link, vendor submits, Purchaser activates | 1. On the saved RFQ, vendor row `V1` → **Send email** → pick email profile, confirm `to`, subject/body (link inserted) → send. 2. `V1` opens `/pl/:url_token`, prices, **Submit**. 3. Purchaser opens the now-`submitted` pricelist on **Price List**, reviews, sets `status = active`. | `POST …/request-for-pricings/:id/send-email` → `email_sent` activity; RFQ row shows `has_submitted = true` and `pricelist.status = submitted`; after step 3 `price-compare` for the covered product/currency/date returns this row. |
| VPL-PUR-HP-10 | Set a pricelist `submitted` manually with unpriced rows — **added 2026-09-22** | Open a `draft` pricelist with three rows, one at `price = 0`; set `status = submitted`; Save. | `submitted_at` stamped; the zero-priced row is deleted (`removeUnpricedDetails`), the two priced rows remain (`VPL_VAL_023`). |
| VPL-PUR-HP-11 | Maintain the Certification master and attach a certificate to a vendor — **added 2026-09-22** | Sidebar → **Certification** → **New** (`code`, `name`, `description`, active) → Save. Then Vendor → edit → Certificates section → add row picking that certification, `certificate_no`, issued/expiry dates, attachment → Save. | `tb_certificate` row created (`POST /api/config/{bu}/vendor-master-certificates`); `tb_vendor_certificate` row created via `POST …/vendor-certificates/vendor/:vendor_id`; both visible on reload. Matches `043-certification.spec.ts`. |
| VPL-PUR-HP-12 | Set vendor `tax_no` / `branch_no` / `rating` via API — **added 2026-09-22** | `PUT /api/config/{bu}/vendors/:id` with `tax_no = "0105551234567"`, `branch_no = "00000"`, `rating = 4`. | Stored and returned by `GET …/vendors/:id`; the React form shows `tax_profile` but has no inputs for these three fields, so they are API/Bruno-only today. |
| VPL-PUR-HP-06 | Create a Price List directly, without an RFQ | Sidebar → **Price List** → **New**. Pick vendor + currency, set validity dates, add detail rows, save at `status = active`. | Pricelist created directly; matches `TC-PL-020001`. This is the practical path when a vendor won't be using the (currently broken) portal. |
| VPL-PUR-HP-07 | Toggle `is_preferred` on a pricelist's own row | Open an active pricelist → **Products** grid → toggle the Crown checkbox on one row. Save. | `tb_pricelist_detail.is_preferred = true` on that row. No cross-vendor screen involved — this is a per-row field on this pricelist alone. |
| VPL-PUR-HP-08 | Bulk-load a vendor's price sheet via CSV | Price List → Import CSV with `pricelist_no`/`vendor_id`/`currency_id`/product rows. | Grouped upsert by `pricelist_no`: new pricelists created, existing ones updated with a full detail-row replace. Matches `PriceListService.importCsv()`. |
| VPL-PUR-HP-09 | Edit an active pricelist's detail row directly | Open an active pricelist → edit a row's price → Save. | Saved with no immutability guard — confirmed no status-based branch blocks this in `update()`. |

## 2. Permission / Authorization

| # | Scenario | Expected |
| - | -------- | -------- |
| VPL-PUR-PERM-01 | Purchaser without the module's view/edit permission attempts any of the four screens | Denied per the generic module-level permission gate — no finer-grained (create-vs-approve) split exists to test. |
| VPL-PUR-PERM-02 *(removed)* | High-value / multi-currency approval gate | **Removed — not implemented.** There is no distinct approve endpoint and no `threshold` anywhere in this module's code. |
| VPL-PUR-PERM-03 *(removed)* | Token-revocation permission | **Removed — not implemented.** No revoke action exists. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error | Confirmed? |
| - | -------- | ------- | -------------- | ---------- |
| VPL-PUR-VAL-01 | Create a template with a duplicate name | Reuse an existing non-deleted `tb_pricelist_template.name` | Rejected via `pricelist_template_name_deletedat_u` DB constraint | **Confirmed** |
| VPL-PUR-VAL-02 | Create a pricelist with `effective_from_date` in the past | Set a back-dated `effective_from_date` | Rejected — `PRICE_LIST_FROM_IN_PAST` | **Confirmed** |
| VPL-PUR-VAL-03 | Create a pricelist with `effective_from_date > effective_to_date` | Reversed dates | Rejected — `PRICE_LIST_FROM_AFTER_TO` | **Confirmed** |
| VPL-PUR-VAL-04 | Create an RFQ with `start_date > end_date` | Reversed dates | Rejected — `RFP_INVALID_DATE_RANGE` | **Confirmed** |
| VPL-PUR-VAL-05 | Add the same vendor twice to one RFQ | Second `vendors.add` row with the same `vendor_id` | Rejected via `request_for_pricing_detail_request_for_pricing_id_vendor_id_u` | **Confirmed** |
| VPL-PUR-VAL-06 | Activate a template with zero product rows | Template has no `tb_pricelist_template_detail` rows; flip `status` to `active` | **Not rejected** — `updateStatus()` performs no such check; this is a confirmed gap versus the previous draft's `VPL_VAL_002` claim. | **Confirmed gap** |
| VPL-PUR-VAL-07 | Save a pricelist row with descending MOQ-tier pricing (higher MOQ at a higher price) | Tier 1 `qty 1 @ ฿10`, Tier 2 `qty 50 @ ฿12` | **Not rejected** — no non-increasing check exists anywhere in this module's code; a confirmed gap versus the previous draft's `VPL_VAL_020` claim. | **Confirmed gap** |
| VPL-PUR-VAL-08 | Edit a doc-version-stale row (optimistic concurrency) | Two sessions load the same pricelist; the second saves with a stale `doc_version` | Rejected — `update()` scopes the `where` clause on `{id, doc_version}`, so a stale write matches zero rows | **Confirmed** |
| VPL-PUR-VAL-09 | Vendor `rating` outside 1–5 — **added 2026-09-22** | `PUT …/vendors/:id` with `rating = 6` (or `0`) | Rejected — Zod `int().min(1).max(5)` (400); a direct DB write is stopped by `vendor_rating_chk` | **Confirmed** |
| VPL-PUR-VAL-10 | Send email without a recipient — **added 2026-09-22** | Send-email dialog with `to` cleared | Rejected by the API — `to` requires at least one address (`RequestForPricingSendEmailSwaggerDto`); the dialog itself only disables **Send** while no email profile is selected or a send is in flight (`rfp-send-email-dialog.tsx`), so the error surfaces as a toast | **Confirmed** |
| VPL-PUR-VAL-11 | Create a pricelist without effective dates — **added 2026-09-22** | Leave `effective_from_date` / `effective_to_date` empty on the Price List form | Blocked client-side — both dates are required since `1fca0b7d` (2026-09-11); the API additionally rejects past dates (`VPL_VAL_016`) | **Confirmed** |

## 4. Edge Cases

| # | Scenario | Expected |
| - | -------- | -------- |
| VPL-PUR-EDGE-01 | Concurrent edits on the same pricelist from two sessions | First save wins (matches on `doc_version`); the second's `update()` call affects zero rows, matching the general Carmen `doc_version` optimistic-lock pattern used across every module in this pass. |
| VPL-PUR-EDGE-02 | Multi-MOQ-tier pricing on one product, multiple rows | Accepted — `@@unique([pricelist_id, product_id, unit_id, moq_qty, deleted_at])` permits one row per distinct `moq_qty`. |
| VPL-PUR-EDGE-03 | Soft-delete a pricelist, then create a new one reusing the same `pricelist_no` | Accepted — the unique index includes `deleted_at`. |
| VPL-PUR-EDGE-04 | Two vendors both marked `is_preferred = true` for the same product/currency | Both rows persist independently — nothing enforces "exactly one preferred row"; `price-compare`'s sort (`is_preferred desc, price asc`) picks whichever has the lower price as `selected` when both are preferred. |
| VPL-PUR-EDGE-05 | Vendor visits the portal link twice | First visit creates the draft pricelist; the second visit's `checkPriceList()` call returns the same existing pricelist rather than creating a duplicate (branches on whether `pricelist_id` is already populated on the invitation row). |
| VPL-PUR-EDGE-06 | PO wizard against a pricelist whose products are outside the PO workflow — **added 2026-09-22** | `GET …/pricelists/active/:vendor_id/:delivery_date?workflow_id=` returns the pricelist with `can_use = false` on those lines (header `can_use = true` only if any line is usable); the PO *From Price List* wizard disables them rather than hiding the pricelist (`VPL_CALC_007`). |
| VPL-PUR-EDGE-07 | `price-compare` for a quantity below the cheapest tier's MOQ — **added 2026-09-22** | With `qty = 2` and tiers MOQ 1/5/100, only the MOQ-1 tier qualifies; the response's `selected` row carries `moq_qty = 1` even if the MOQ-100 tier is cheaper (`VPL_CALC_004`). Without `qty` the cheapest tier wins regardless of MOQ. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md).
- User flow: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md).
- Business rules: [02-business-rules.md](./02-business-rules.md) § 2 (confirmed-vs-design-target validation), § 5 (status rules).
- E2E: `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts`, `159-pl.spec.ts`, `160-pl-template.spec.ts`, `043-certification.spec.ts` and their gap reports under `docs/test-cases/gaps/`.
- Cross-link: [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [product](/en/inventory/product).
