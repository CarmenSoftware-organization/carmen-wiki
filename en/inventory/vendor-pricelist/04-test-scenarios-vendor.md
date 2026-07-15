---
title: Vendor Pricelist — Test Scenarios — Vendor
description: Vendor's test cases for vendor-pricelist. External party — Permission section reduced to a single N/A row; Save/Submit confirmed non-functional against current backend.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, test-scenarios, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Test Scenarios — Vendor

> **At a Glance**
> **Persona:** Vendor (external — token-authenticated portal only) &nbsp;·&nbsp; **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist)
> **Confirmed 2026-07-16:** only the "open the link" call works; Save and Submit target backend routes that do not exist.

This page captures the test scenarios that exercise the **Vendor** persona's interaction with `/pl/:url_token`. Because there is no Carmen login for the vendor, the Permission / Authorization section is a single N/A row.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| VPL-VND-HP-01 | Open the portal link for the first time | RFQ created with vendor `V1` invited (see `VPL-PUR-HP-04`); `V1`'s `pricelist_url_token` known | Vendor opens `/pl/:url_token` | `POST /api/check-pricelist/:url_token` fires; a zero-priced draft `tb_pricelist` (one row per template product) is created and returned; the invitation row's `pricelist_id` is populated. |
| VPL-VND-HP-02 | Re-open the portal link after a pricelist already exists | Continue from VPL-VND-HP-01 | Vendor opens the same link again | The same call returns the existing pricelist rather than creating a second one. |
| VPL-VND-HP-03 | View the auto-created draft's prices | Continue from VPL-VND-HP-01 | Vendor toggles View mode | All rows show `price = 0` / `price_without_tax = 0` until a Purchaser fills them in on the internal Price List screen. |

## 2. Confirmed-Broken Actions

| # | Scenario | Steps | Expected |
| - | -------- | ----- | -------- |
| VPL-VND-BRK-01 | Vendor edits a price and clicks Save | Toggle Edit mode, type a price, click **Save** | `PATCH /api/external/api/pricelist-external/:url_token` fires. **Confirmed:** no matching backend route exists anywhere in `carmen-turborepo-backend-v2` — the call fails; the UI surfaces the backend's error message via toast, or falls back to "Failed to save changes" for a non-`HttpError` failure. |
| VPL-VND-BRK-02 | Vendor clicks Submit | Click **Submit** | `POST /api/external/api/pricelist-external/:url_token/submit` fires. **Confirmed:** same gap — no matching backend route exists. |

## 3. Permission / Authorization

| # | Scenario | Expected behaviour |
| - | -------- | ------------------ |
| VPL-VND-PERM-01 | Vendor is an external party with no Carmen login; in-system RBAC is N/A. | N/A — there is no login, no role, and no permission matrix to test. Token validity is the only gate on the one working call, and even that call performs no expiration, IP, or session check (see [02-business-rules](/en/inventory/vendor-pricelist/02-business-rules) § 4). |

## 4. Validation / Error

| # | Scenario | Trigger | Expected |
| - | -------- | ------- | -------- |
| VPL-VND-VAL-01 | Open the portal with a token that doesn't match any invitation row | Malformed or unknown `url_token` | `checkPricelist()` returns a not-found error (`Request for pricing detail not found`). |
| VPL-VND-VAL-02 | Open the portal for an invitation whose linked template has been soft-deleted | Template `deleted_at IS NOT NULL` | `checkPricelist()` returns a not-found error for the template (`Pricelist template not found`) — confirmed in `check-price-list.service.ts`. |

## 5. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| VPL-VND-EDGE-01 | Portal link opened after the RFQ's `end_date` has passed | `end_date < now()` | **No enforcement found.** `checkPricelist()` never reads `end_date`; the draft still auto-creates/returns normally. |
| VPL-VND-EDGE-02 | Portal link opened from any IP address | No allowlist | **No enforcement found.** No IP check exists anywhere in this call path. |
| VPL-VND-EDGE-03 | Same link opened in many simultaneous browser tabs | No session-limit code | **No enforcement found.** Each tab's call independently succeeds or returns the same existing pricelist; there is no concurrent-session cap. |

## 6. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md).
- User flow: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — full detail on the confirmed gap.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 5.4.
- Backend: `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/pricelists/check-pricelist.controller.ts`; `apps/micro-business/src/master/check-price-list/`.
- Frontend: `../carmen-inventory-frontend-react/routes/external/pl/`, `hooks/use-price-list-external.ts`.
- Sibling: [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) — how a Purchaser turns the auto-created draft into a real, priced, active pricelist today.
