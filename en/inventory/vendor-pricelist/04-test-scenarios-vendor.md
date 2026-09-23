---
title: Vendor Pricelist — Test Scenarios — Vendor
description: Vendor's test cases for vendor-pricelist. External party — portal open / save / submit / expiry; Permission section reduced to a single N/A row.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: vendor-pricelist, test-scenarios, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Test Scenarios — Vendor

> **At a Glance**
> **Persona:** Vendor (external — token-authenticated portal only) &nbsp;·&nbsp; **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist)
> **Executable coverage (2026-09-22):** no Playwright spec for the portal; the documentation-only catalog `../carmen-inventory-frontend-e2e/docs/test-cases/1002-external-price-list.md` (42 `TC-EPL-*` cases: load, header, product table, MOQ sub-table, tax-profile / unit pickers, save, Excel import, submit, expired screen) is the closest oracle. This page does not mirror it.
> **Re-synced 2026-09-22:** the 2026-07-16 "Save/Submit confirmed non-functional" finding is obsolete — `PATCH /api/pricelist-external/:url_token` and `POST …/submit` exist; the link expires at the RFQ `end_date`.

This page captures the test scenarios that exercise the **Vendor** persona's interaction with `/pl/:url_token`. Because there is no Carmen login for the vendor, the Permission / Authorization section is a single N/A row.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| VPL-VND-HP-01 | Open the portal link for the first time | RFQ created with vendor `V1` invited (see `VPL-PUR-HP-04`), `end_date` in the future; `V1`'s `pricelist_url_token` known | Vendor opens `/pl/:url_token` | `POST /api/external/api/check-pricelist/:url_token` passes `UrlTokenGuard`; a zero-priced draft `tb_pricelist` (one row per template product × unit/MOQ tier, tax profile pre-filled, `effective_from/to` = RFQ dates) is created and returned; the invitation row's `pricelist_id` / `pricelist_no` are populated; a `create` activity is logged. |
| VPL-VND-HP-02 | Re-open the portal link after a pricelist already exists | Continue from VPL-VND-HP-01 | Vendor opens the same link again | The same call returns the existing pricelist rather than creating a second one. |
| VPL-VND-HP-03 | Pick a tax profile and order unit per line | Continue from HP-01; BU has ≥ 2 tax profiles; a product has ≥ 2 order units | Toggle Edit mode; change the tax profile and unit on one line | Options come from `GET …/check-pricelist/:url_token/tax-profiles` and `…/units` (default unit flagged); the line's `tax_rate` / `tax_amt` recompute client-side. |
| VPL-VND-HP-04 | Save a draft | Continue from HP-03; type prices on two lines | Click **Save** | `PATCH …/pricelist-external/:url_token` with `{ note, pricelist_detail: { update: [...] } }` → 200; the pricelist stays `draft`; reloading the link shows the saved prices; `tb_activity` has a `vendor.pricelist.draft_saved` entry with before/after snapshots. |
| VPL-VND-HP-05 | Add another MOQ tier for a product | Continue from HP-04 | In the MOQ sub-table add a tier (`moq_qty = 50`, lower price); Save | `pricelist_detail.add[]` creates a new `(product, unit, moq_qty)` row; the unique key permits it. |
| VPL-VND-HP-06 | Import prices from Excel | Continue from HP-01; sheet in the portal's download format | **Import** → choose file → confirm | `price-list-external-excel.ts` parses the sheet into the form; rows match on product code + unit + MOQ; unmatched rows are reported in the dialog; nothing is persisted until **Save**. |
| VPL-VND-HP-07 | Submit | Continue from HP-04; one line left at `price = 0` | Click **Submit** → confirm | `POST …/pricelist-external/:url_token/submit` → `status = submitted`, `submitted_at = now()`; the zero-priced line is deleted; a `submit` activity is logged; the page turns read-only; the Purchaser's RFQ row shows `has_submitted = true`, `pricelist.status = submitted`. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour |
| - | -------- | ------------------ |
| VPL-VND-PERM-01 | Vendor is an external party with no Carmen login; in-system RBAC is N/A. | N/A — there is no login, no role, and no permission matrix to test. The only gate is `UrlTokenGuard` (`VPL_VAL_027`): valid, unexpired token → the JWT's `{ bu, vendor_id, rfp_detail_id }` scope; the guard has no IP or session check. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected |
| - | -------- | ------- | -------- |
| VPL-VND-VAL-01 | Open the portal with a token that matches no `tb_shot_url` row | Malformed or unknown `url_token` | 401 `Invalid or expired url_token` from `UrlTokenGuard`; the page shows *This link has expired*. |
| VPL-VND-VAL-02 | Open the portal for an invitation whose linked template has been soft-deleted | Template `deleted_at IS NOT NULL` | `checkPriceList()` returns 404 `Pricelist template not found`. |
| VPL-VND-VAL-03 | Save or Submit after the pricelist is already `submitted` | Continue from HP-07; replay the `PATCH` / `POST` | Rejected — `saveDraft()` / `submit()` require `status = draft` (`Price list is not in draft status and cannot be submitted`); the UI hides the controls (`data.status !== "submitted"`). |
| VPL-VND-VAL-04 | Submit with every line unpriced | All rows at `price = 0` | **Accepted** — every row is deleted and an empty `submitted` pricelist remains (`VPL_VAL_023`); no "at least one priced row" check exists. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| VPL-VND-EDGE-01 | Portal link opened after the RFQ's `end_date` has passed | `tb_shot_url.expired_at < now()` | **Rejected** — 401 `url_token has expired` on every call including the first open; the portal renders the expired screen. Extending `end_date` afterwards does not revive the existing token. |
| VPL-VND-EDGE-02 | Portal link opened from any IP address | No allowlist | **No enforcement.** No IP check exists anywhere in the guard or the service. |
| VPL-VND-EDGE-03 | Same link opened in many simultaneous browser tabs | No session-limit code | **No enforcement.** Each tab independently works; concurrent saves race on the same rows (last write wins — `saveDraft()` does not use `doc_version`). |
| VPL-VND-EDGE-04 | Vendor saves after the Purchaser edited the same draft internally | Purchaser changed a price on the Price List screen | Last write wins; no conflict detection on the portal side. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md).
- User flow: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — step-by-step portal flow.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 5.4, `VPL_VAL_023`, `VPL_VAL_027`, `VPL_VAL_028`.
- Backend: `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/pricelists/check-pricelist.controller.ts`, `pricelist-external.controller.ts`, `apps/backend-gateway/src/auth/guards/url-token.guard.ts`; `apps/micro-business/src/master/check-price-list/check-price-list.service.ts`.
- Frontend: `../carmen-inventory-frontend-react/routes/external/pl/` (`use-price-list-external.ts`, `price-list-external-import-dialog.tsx`, `price-list-external-expired.tsx`).
- Sibling: [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) — how a Purchaser emails the link and activates the submitted pricelist.
