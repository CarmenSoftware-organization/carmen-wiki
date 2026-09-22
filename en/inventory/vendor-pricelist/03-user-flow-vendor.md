---
title: Vendor Pricelist — User Flow — Vendor
description: Vendor's flow within the vendor-pricelist module — external, token-authenticated portal; open, price, save, import, submit; link expires at the RFQ end date.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: vendor-pricelist, user-flow, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow — Vendor

> **At a Glance**
> **Persona:** Vendor (external — token-authenticated portal, no Carmen login) &nbsp;·&nbsp; **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist)
> **Re-synced 2026-09-22:** the Save/Submit gap reported on 2026-07-16 is **closed** — `PATCH /api/pricelist-external/:url_token` and `POST …/:url_token/submit` exist (`pricelist-external.controller.ts`), the link expires at the RFQ `end_date` (`UrlTokenGuard`), and every portal action is logged to `tb_activity`.

## 1. Role in This Module

The **Vendor** is an external party with no Carmen login. They receive an email (sent from the RFQ's vendor row — `POST …/request-for-pricings/:id/send-email`) containing a link of the form `/pl/:url_token` (route `routes/external/pl/price-list-external.route.tsx` → `price-list-external-component.tsx`), where the token is the `pricelist_url_token` generated for their invitation row when a Purchaser created a [Request for Pricing](/en/inventory/vendor-pricelist/request-price-list). The token maps, through the platform table `tb_shot_url`, to a JWT carrying `{ bu, vendor_id, rfp_detail_id }` and an `expired_at` equal to the RFQ `end_date`; the gateway's `UrlTokenGuard` accepts the token in place of a Keycloak session and rejects it with 401 once it has expired. Unlike the "no dedicated portal" pattern for external vendors in other modules (e.g. the [purchase-order](/en/inventory/purchase-order) vendor), this module gives the vendor a real page that reads and writes their own pricelist.

## 2. Entry Point and Primary Flow

**Entry point:** the vendor clicks the link in the RFQ email (or receives it out of band — the token is visible on the RFQ vendor row as `url_token`).

**What happens, step by step:**

1. **Open the link.** The frontend calls `POST /api/external/api/check-pricelist/:url_token` (`usePriceListExternal`). Behind `UrlTokenGuard`, `CheckPriceListService.checkPriceList()` looks the invitation row up; if it has no pricelist yet it **creates one** — `tb_pricelist` at `status = draft`, `pricelist_no` from the running code, `effective_from/to` = the RFQ `start_date`/`end_date` (fallback today + template `validity_period`), `url_token`, `submission_method = online`, plus one zero-priced `tb_pricelist_detail` row per template product × order unit / MOQ tier (deduplicated on `unit::moq`), each pre-filled with the product's tax profile — and links it to the invitation row (`pricelist_id`, `pricelist_no`). A `create` activity is logged. Later visits return the existing pricelist. An expired or unknown token yields 401 and the page renders `price-list-external-expired.tsx` (*This link has expired … Contact the hotel that sent it*).
2. **Pick per-line options.** The page loads the BU's tax profiles (`GET …/check-pricelist/:url_token/tax-profiles`) and each product's allowed order units (`GET …/units`, default flagged) so the vendor can choose a tax profile and unit per line in edit mode.
3. **Price the products.** The table (`price-list-external-product-table.tsx`, with a MOQ-tier sub-table per product) lets the vendor type `price_without_tax` / `price`, lead time and notes per tier, or add another `(unit, MOQ)` line. An **Import** dialog (`price-list-external-import-dialog.tsx`) accepts an Excel sheet parsed client-side (`price-list-external-excel.ts`) into the same form values.
4. **Save.** `PATCH /api/external/api/pricelist-external/:url_token` with `{ note, pricelist_detail: { update: [...], add: [...] } }` (`useUpdatePriceListExternal`). The backend requires the pricelist to still be `draft`, writes the lines, and logs `vendor.pricelist.draft_saved` with before/after snapshots. The pricelist stays `draft`, so the vendor can return and continue until the link expires.
5. **Submit.** `POST /api/external/api/pricelist-external/:url_token/submit` (`useSubmitPriceListExternal`). Requires `status = draft`; deletes every line with `price IS NULL OR price <= 0` (a zero is "no offer", not a free item — `price-list.zero-price.ts`), sets `status = submitted` and `submitted_at = now()`, logs a `submit` activity. The page switches to read-only (`data.status !== "submitted"` gates the edit controls); the Purchaser's RFQ row now shows `has_submitted = true` with the pricelist number and status.

Net effect: the vendor's own submission is the pricelist the Purchaser reviews and activates — no internal re-keying is needed any more (see [03-user-flow-purchaser](/en/inventory/vendor-pricelist/03-user-flow-purchaser) Step 5).

## 3. Decision Branches

- **The link says it has expired.** The RFQ `end_date` has passed (or the token is unknown). Nothing on the vendor side can renew it — the Purchaser must re-invite (new RFQ, or remove and re-add the vendor row) and send a new email.
- **The vendor wants to change prices after submitting.** The portal is read-only once `submitted` and the backend refuses `saveDraft` / `submit` on a non-`draft` pricelist. The Purchaser can still edit the `submitted` pricelist on the internal Price List screen (no immutability guard) — changes are then on the buyer's side.
- **The vendor does not sell some of the requested products.** Leave them at `0`; they are deleted at submit rather than surfacing as ฿0 offers to procurement.
- **Late submission.** Not a business rule in the service — the deadline bites only because the token dies at `end_date` (`UrlTokenGuard`); the service itself never compares `now()` to `end_date`.
- **Reminders.** None are sent; `reminder_days` / `escalation_after_days` on the template are inert.

## 4. Exit Point / Handoffs

- **Submit → Purchaser.** The `submitted` pricelist (with `submitted_at`) is the hand-off; the Purchaser reviews it and sets `status = active` on the Price List screen. The vendor sees no further state — there is no "accepted" / "rejected" feedback loop.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — real status fields and the confirmed cross-persona handoff table.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 5.4 (portal routes), `VPL_VAL_023` (submit), `VPL_VAL_027` (token expiry), `VPL_VAL_028` (save shape).
- Frontend: `../carmen-inventory-frontend-react/routes/external/pl/` — `price-list-external-component.tsx`, `price-list-external-product-table.tsx`, `moq-tiers-sub-table.tsx`, `price-list-external-import-dialog.tsx`, `price-list-external-excel.ts`, `price-list-external-expired.tsx`, `use-price-list-external.ts`; `types/price-list-external.ts`; `constant/api-endpoints.ts` (`PRICE_LIST_EXTERNAL`, `PRICE_LIST_EXTERNAL_CHECK`, `PRICE_LIST_EXTERNAL_TAX_PROFILES`).
- Backend: `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/pricelists/check-pricelist.controller.ts` (`POST :url_token`, `GET :url_token/tax-profiles`, `GET :url_token/units`), `pricelist-external.controller.ts` (`PATCH :url_token`, `POST :url_token/submit`), `apps/backend-gateway/src/auth/guards/url-token.guard.ts`; `apps/micro-business/src/master/check-price-list/check-price-list.service.ts` (`checkPriceList`, `saveDraft`, `submit`, `getBuTaxProfiles`, `getPricelistProductUnits`), `apps/micro-business/src/master/price-list/price-list.zero-price.ts`.
- Bruno: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/pricelist/` — `POST-check-pricelist`, `GET-get-bu-tax-profiles`, `GET-get-pricelist-product-units`, `PATCH-save-draft`, `POST-submit`.
- E2E: documentation-only catalog `../carmen-inventory-frontend-e2e/docs/test-cases/1002-external-price-list.md` (42 cases, `TC-EPL-*`); no Playwright spec yet.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — the internal persona that emails the link and activates the submitted pricelist.
- Cross-link: [product](/en/inventory/product) — every product on the template's detail rows becomes a zero-priced row on the auto-created draft.
