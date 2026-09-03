---
title: Vendor Pricelist — User Flow — Vendor
description: Vendor's flow within the vendor-pricelist module — external, token-authenticated portal; confirmed gap in the Save/Submit backend routes.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow — Vendor

> **At a Glance**
> **Persona:** Vendor (external — token-authenticated portal, no Carmen login) &nbsp;·&nbsp; **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist)
> **Confirmed gap (2026-07-16):** the portal's Save and Submit buttons call backend routes that do not exist. Only the initial "open the link" call works.

## 1. Role in This Module

The **Vendor** is an external party with no Carmen login. They receive a link of the form `/pl/:url_token` (route component `price-list-external-component.tsx`), where the token is the `pricelist_url_token` generated for their invitation row when a Purchaser created a [Request for Pricing](/en/inventory/vendor-pricelist/request-price-list). Unlike the "no dedicated portal, no persistent state" pattern for external vendors in other modules (e.g., the [purchase-order](/en/inventory/purchase-order) vendor), this module does give the vendor an actual page to interact with — but as verified this pass, most of what that page tries to do does not currently reach a working backend endpoint.

## 2. Entry Point and Primary Flow

**Entry point:** Vendor clicks the link from their invitation (however it was communicated — no email-dispatch code was found in this repo, so in practice the link would need to be sent out-of-band today; see Decision Branches).

**What actually happens, step by step:**

1. **Open the link.** The frontend calls `POST /api/check-pricelist/:url_token` (`usePriceListExternal`). On the backend, this reaches `CheckPricelistController` → `CheckPricelistService` → (via microservice message `check-pricelists.check`) `CheckPriceListService.checkPricelist()`. If the invitation row has no linked pricelist yet, this call **creates one**: a `tb_pricelist` row at `status = draft` with one zero-priced `tb_pricelist_detail` row per template product (price fields all `0`), and links it back to the invitation row. If a pricelist already exists for this token, the same call just returns it. **This is the only working call in the entire vendor-portal flow.**
2. **View/edit in the browser.** The page renders a header (`PriceListExternalHeader`) and a product table (`PriceListExternalProductTable`) with a View/Edit-mode toggle. In edit mode the vendor can type prices and MOQ tiers into the form.
3. **Click Save.** The frontend calls `PATCH /api/external/api/pricelist-external/:url_token` (`useUpdatePriceListExternal`). **Confirmed gap:** a repo-wide search of `carmen-turborepo-backend-v2` for the literal string `pricelist-external` returns zero hits outside the frontend's own `constant/api-endpoints.ts`. No controller, no module, no microservice message pattern matches this route. The call will fail (the frontend's own error-handling path is wired for this — a rejected `mutateAsync` shows a toast with the backend's error message, or a generic "Failed to save changes" if the error isn't an `HttpError`), but nothing about the frontend's own code, tests, or comments flags this as a known limitation — it is not a documented "coming soon" placeholder like `stock-replenishment` or `wastage-reporting` in other modules; it reads as a real feature whose backend half is simply missing from this repo snapshot.
4. **Click Submit.** Same story: the frontend calls `POST /api/external/api/pricelist-external/:url_token/submit` (`useSubmitPriceListExternal`); no matching backend route exists either.

Net effect: a vendor visiting the link today can **see** the auto-created draft (all-zero prices, until a Purchaser fills them in on the internal Price List screen — see [03-user-flow-purchaser](/en/inventory/vendor-pricelist/03-user-flow-purchaser) Step 5) but cannot **persist their own edits or submit** through this screen in the current codebase.

## 3. Decision Branches

- **If the vendor's edits don't seem to save.** This is expected given the confirmed gap above — there is currently no way to distinguish, from the vendor's side, "my edits didn't save because of a bug" from "this feature isn't wired up yet." Anyone testing this flow should not spend time chasing a client-side reproduction; the fix is a backend route, not a frontend one.
- **How does pricing actually get onto an RFQ-originated pricelist today?** A Purchaser edits the auto-created draft directly on the internal **Price List** screen (same screen used for pricelists entered without an RFQ at all) and sets `status = active` there.
- **How is the invitation link actually delivered to the vendor?** No email-dispatch code (SMTP call, email-template render, or queued job) was found anywhere in this module's backend services — `create()` on the RFQ generates the token and the JWT but does not send anything. In practice, delivering the link is a manual, out-of-band step today (e.g., pasted from the create-response payload), not an automated invitation email.

## 4. Exit Point / Handoffs

- **Portal visit → Purchaser.** The vendor's one working action (opening the link) hands a fresh draft pricelist to the Purchaser, who does the actual data entry and activation. There is no further vendor-driven state change today.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — real status fields and the confirmed cross-persona handoff table.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 5.4 — the same confirmed gap, cited alongside the module's other status rules.
- Frontend: `../carmen-inventory-frontend-react/routes/external/pl/price-list-external-component.tsx`, `hooks/use-price-list-external.ts`, `constant/api-endpoints.ts` (`PRICE_LIST_EXTERNAL`, `PRICE_LIST_EXTERNAL_CHECK`).
- Backend (working call only): `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/pricelists/check-pricelist.controller.ts` + `check-pricelist.service.ts`; `apps/micro-business/src/master/check-price-list/check-price-list.controller.ts` + `check-price-list.service.ts`.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — the internal persona that does the actual pricing entry on the auto-created draft.
- Cross-link: [product](/en/inventory/product) — every product on the template's detail rows becomes a zero-priced row on the auto-created draft.
