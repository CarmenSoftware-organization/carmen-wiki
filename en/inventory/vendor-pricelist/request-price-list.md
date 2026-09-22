---
title: Request for Quotation
description: Outbound request-for-price (RFQ) emailed to one or more vendors — each gets an expiring portal link; submissions land as submitted pricelists.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: vendor-pricelist, rfq, procurement, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Request for Quotation

> **At a Glance**
> **Owner:** Purchaser / Procurement Manager &nbsp;·&nbsp; **Table:** `tb_request_for_pricing` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** none (date-window driven) &nbsp;·&nbsp; **Upstream:** [templates/price-list](/en/inventory/templates/price-list) &nbsp;·&nbsp; Solicits price quotes from vendors before a `tb_pricelist` is awarded.
> **Re-synced 2026-09-22:** per-vendor **Send email** action (`POST …/request-for-pricings/:id/send-email`, 2026-09-16); the portal link now expires at the RFQ `end_date` (`UrlTokenGuard`); the portal's Save/Submit work and produce a `submitted` pricelist; the detail response expands `vendor`, `pricelist { id, no, name, status }` and `pricelist_template { …, currency }` as objects.

![Request for Quotation screen](/screenshots/vendor-pricelist/request-price-list.png)

![Request for Quotation detail screen](/screenshots/vendor-pricelist/request-price-list-detail.png)

## 1. What & Who

**Request for Pricing (RFQ)** is the procurement-initiated outbound document that solicits quotes from one or more vendors before a [vendor-pricelist](/en/inventory/vendor-pricelist) is awarded. The buyer picks a [templates/price-list](/en/inventory/templates/price-list) (which carries currency, validity window, reminder schedule, and the product catalogue under quote), names candidate vendors, and dispatches the request. Each invited vendor gets a **tokenised link** (emailed from the RFQ's vendor row) to a portal where they price the template's products, save drafts, and submit; a submission is a `tb_pricelist` at `status = submitted` keyed back to the RFQ row. After the deadline the link stops working; the buyer reviews the submitted pricelists on the Price List screen and *awards* one (or more) by flipping its status to `active`.

**Created by** Purchaser &nbsp;·&nbsp; **Responded to by** invited vendors (no login — token-scoped portal that saves and submits; see [03-user-flow-vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor)) &nbsp;·&nbsp; **Produces no inventory or AP effect.**

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create an RFQ from a template | Vendor Management → Request Price List → **New** | Template binds currency + product catalogue |
| Invite vendors | Same create form → **Add vendors** dialog (multi-select, 2026-08-06) | All invitation rows (and their `pricelist_url_token`s, JWTs and `tb_shot_url` rows with `expired_at = end_date`) are created in the same `POST` call as the RFQ header — there is no separate "launch" step. |
| Email the link to a vendor | Detail → vendor row → **Send email** (action column, 2026-09-10) | Opens the same dialog as the PO email: pick an email profile (`profile_id`), enter `to` / optional `cc`, and a `subject` / HTML `body` pre-filled from an email template with `rfp` placeholders (the portal link `/pl/:url_token` is composed client-side); `POST …/request-for-pricings/:id/send-email` (`vendor_id` optional) → `email_sent` activity. One vendor per send; there is no "send to all" button. |
| Add more vendors to an existing RFQ | Detail → edit → add vendor row | `PATCH` supports `vendors.add`/`vendors.remove`/`vendors.update`; unique constraint on `(request_for_pricing_id, vendor_id)` enforces no double-invite. |
| Track responses | RFQ detail → vendor rows | `has_submitted` and the linked `pricelist { no, status }` per vendor (`submitted` once the vendor clicks Submit; still `draft` if they only opened/saved). |
| Compare / award | Purchaser opens the vendor's `submitted` pricelist on the **Price List** screen | Awarding = setting the winning `tb_pricelist.status = active` from the Price List edit form — there is no "Compare" or "Activate" button on the RFQ screen itself, and no bid-comparison UI was found. |

## 3. Validation & Errors

| Symptom / Message | Cause | Confirmed? |
|---|---|---|
| "Vendor already invited" | A non-deleted detail row exists for (RFQ, vendor) | **Confirmed** — `@@unique([request_for_pricing_id, vendor_id, deleted_at])`. |
| RFQ creation rejected with an invalid date range | `start_date > end_date` | **Confirmed** — `request-for-pricing.service.ts create()` explicitly checks this (`RFP_INVALID_DATE_RANGE`). |
| "Cannot change template — invitations sent" | `pricelist_template_id` immutable post-dispatch | **Not confirmed.** `update()` accepts a new `pricelist_template_id` with no immutability check once vendor rows exist. |
| Late submission rejected after `end_date` | The portal link expires | **Confirmed (2026-09-22) — at the guard, not in the service.** `UrlTokenGuard` returns 401 `url_token has expired` once `tb_shot_url.expired_at` (set to the RFQ `end_date` when the token is minted) has passed; every portal call, including the first open, is blocked and the React portal shows *This link has expired*. Extending `end_date` afterwards does **not** refresh existing tokens. |
| "Vendor must be active" | `tb_vendor.is_active = false` blocks the invite | **Not confirmed.** No `is_active` check on the vendor was found in `create()` or `update()`. |
| Invitation link returns 401 | Unknown token, or `expired_at` passed | `UrlTokenGuard`; a soft-deleted RFQ detail row is reported by `checkPriceList()` as `Request for pricing detail not found` (404). No token-rotation or revoke code exists. |
| Send email fails with a permission/login bounce | App-id `requestForPricing.sendEmail` missing from the tenant's app-id allow-list | Add it in the platform app catalog before use (noted in commit `2b750267e`). |

## 4. Edge Cases

- **Token security.** `pricelist_url_token` is a random string per invitation, generated once at RFQ-create time and mapped in the platform table `tb_shot_url` to a JWT (`{ bu, vendor_id, rfp_detail_id }`, `JWT_EXPIRES_IN`) and `expired_at = end_date`; portal access is scoped by the token alone (vendors do not authenticate). Expiry is enforced by `UrlTokenGuard`; no IP restriction and no revocation/rotation code exists.
- **Late submission is blocked by expiry, not by a business rule.** Nothing in `check-price-list.service.ts` reads `start_date`/`end_date` except to date the auto-created pricelist (`effective_from/to`); the deadline bites only because the link dies at `end_date`. An RFQ created without `end_date` gets a token whose expiry is `null`-driven — treat that as an open question.
- **Award is a pricelist-level flip, not RFQ-level.** The RFQ has no status column of its own — "awarding" is simply the Purchaser setting the chosen `tb_pricelist.status = active` directly on the Price List screen.
- **Currency cascade.** The template supplies a default currency to the auto-created draft pricelist; nothing was found preventing a Purchaser from changing `currency_id` afterwards on the Price List edit form.
- **No reminder job found.** A repo-wide search of this module and `micro-cronjobs` found no scheduled job reading `reminder_days`/`escalation_after_days` — those template fields are stored but currently inert. The only outbound communication is the manual per-vendor **Send email**.
- **Portal activity is logged.** First open (`create`), each draft save (`vendor.pricelist.draft_saved`) and the submit are written to `tb_activity` with before/after snapshots (2026-09-11/12); the send-email action writes `email_sent`. These appear in the Activity panel of the RFQ / pricelist.
- **No workflow engine.** RFQ has no `workflow_*` columns and no status column at all; the closest per-vendor signal is `has_submitted: !!pricelist_id`.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_request_for_pricing`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | RFQ display name (e.g. "Q2-2026 Beverage RFQ"). |
| `pricelist_template_id` | `String @db.Uuid` | No | FK to [templates/price-list](/en/inventory/templates/price-list). Carries currency, validity, reminders, catalogue. |
| `start_date` | `DateTime? @db.Timestamptz(6)` | Yes | Date vendors may begin submitting. |
| `end_date` | `DateTime? @db.Timestamptz(6)` | Yes | Submission deadline; drives reminders. |
| `custom_message` | `String? @db.Text` | Yes | Free text rendered in the invitation email. |
| `email_template_id` | `String? @db.VarChar` | Yes | Identifier for invitation / reminder mails. |
| `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `request_for_pricing_name_u`; `@@index([pricelist_template_id])`; `@@index([name])`. FK to `tb_pricelist_template` `onDelete: NoAction`.

### 5.2 `tb_request_for_pricing_detail`

One row per invited vendor.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `request_for_pricing_id`, `sequence_no` | mixed | No / No / Yes | PK, parent FK, ordinal. |
| `vendor_id`, `vendor_name` | `String @db.Uuid` / `VarChar` | No / Yes | Invited vendor + snapshot. |
| `contact_person`, `contact_phone`, `contact_email` | `String? @db.VarChar` | Yes | Vendor-side contact for this round. |
| `pricelist_id`, `pricelist_no` | `String? @db.Uuid` / `VarChar` | Yes | FK to `tb_pricelist` created on submission — null until then. |
| `pricelist_url_token` | `String? @db.VarChar` | Yes | Tokenised URL fragment for the portal invitation. |
| `comment`, `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([request_for_pricing_id, vendor_id, deleted_at])` — one invitation per (RFQ, vendor); `@@index([request_for_pricing_id, vendor_id])`. FKs to `tb_request_for_pricing`, `tb_vendor`, `tb_pricelist` — all `onDelete: NoAction`.

### 5.3 Comment tables

`tb_request_for_pricing_comment` and `tb_request_for_pricing_detail_comment` follow the canonical comment shape.

## 6. Workflow / Business Rules

RFQ has **no status column and no workflow engine** — `tb_request_for_pricing` carries only `start_date`/`end_date` as descriptive fields; nothing in the code reads them to gate or derive a lifecycle state. What actually happens, confirmed against `request-for-pricing.service.ts` and `check-price-list.service.ts`:

- **Create** — RFQ header + all vendor detail rows (with their `pricelist_url_token`s) are inserted in one `create()` call. There is no separate "invitation sent" step or dispatch code — the tokens exist from the moment of creation, whether or not anything communicates them to the vendor.
- **Portal visit** — the vendor's first `POST /api/check-pricelist/:url_token` auto-creates a zero-priced draft `tb_pricelist` from the template, dated `effective_from/to = start_date/end_date` when the RFQ has them. Gated only by the token's `expired_at` (= `end_date`) in `UrlTokenGuard`, not by `start_date`.
- **Portal save / submit** — `PATCH …/pricelist-external/:url_token` keeps the pricelist `draft`; `POST …/submit` sets `submitted` + `submitted_at` and deletes unpriced rows. Both require the pricelist to still be `draft`.
- **Send email** — `POST …/request-for-pricings/:id/send-email` through a configured email profile; body HTML is sanitised with an allow-list (`common/email-body.ts`); result logged as `email_sent`.
- **No reminders, no escalation, no deadline enforcement** — `reminder_days[]` and `escalation_after_days` are stored on the template but nothing reads them; no scheduled job was found in this repo or in `micro-cronjobs`.
- **Award** — the Purchaser sets the chosen `tb_pricelist.status = active` directly on the Price List screen; this module's own code does not touch that field.

**Date validation:** `start_date <= end_date` is checked at RFQ create (`RFP_INVALID_DATE_RANGE`); no other date rule was found. **Template binding:** `pricelist_template_id` can be changed on `update()` with no immutability guard, contradicting a previously-documented "immutable after first invitation" claim. **Currency:** the auto-created draft inherits `currency_id` from the template, but nothing prevents changing it afterwards on the Price List edit form.

## 7. Cross-References

- [vendor-pricelist](/en/inventory/vendor-pricelist) — vendor responses materialise as `tb_pricelist` rows; the awarded one becomes the active catalogue.
- [templates/price-list](/en/inventory/templates/price-list) — RFQ requires a template (currency, validity, reminders, product catalogue).
- [master-data/vendor](/en/inventory/master-data/vendor) — invited vendors reference `tb_vendor`; no `is_active` check was found on invite.
- [master-data/currency](/en/inventory/master-data/currency) — currency defaults from the template.
- [purchase-request](/en/inventory/purchase-request) / [purchase-order](/en/inventory/purchase-order) — downstream consumers of the awarded pricelist.
- [system-config/workflow](/en/inventory/system-config/workflow) — *not used* by RFQ; mentioned for contrast.
- [03-user-flow-vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor) — the confirmed gap in the portal's Save/Submit backend routes.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_request_for_pricing` (line 4405), `tb_request_for_pricing_comment` (line 4438), `tb_request_for_pricing_detail` (line 4473), `tb_request_for_pricing_detail_comment` (line 4511). *(Corrected 2026-07-16 — the previous citation of lines 4039-4176 no longer matches the current schema file.)*
- **Frontend route:** `../carmen-inventory-frontend-react/routes/vendor-management/request-price-list/`; external portal: `routes/external/pl/`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/request-for-pricing/request-for-pricing.service.ts` (`create`, `createVendorDetailWithToken`, `generateVendorToken`, `insertVendorPricelist`, `sendEmail`), `.../check-price-list/check-price-list.service.ts`; gateway `apps/backend-gateway/src/application/request-for-pricings/request-for-pricings.controller.ts` (`POST :id/send-email`, app-id `requestForPricing.sendEmail`; `GET :id/print-viewer`), `apps/backend-gateway/src/auth/guards/url-token.guard.ts`; platform schema `tb_shot_url`.
- **Frontend:** `routes/vendor-management/request-price-list/` — `rfp-send-email-dialog.tsx`, `use-rfp-send-email.ts`, `rfp-vendor-add-dialog.tsx`, `rfp-vendor-cells.tsx`; `types/request-price-list.ts`.
- **E2E:** no spec for the RFQ screen; the portal has a documentation-only catalog `../carmen-inventory-frontend-e2e/docs/test-cases/1002-external-price-list.md` (42 cases, `TC-EPL-*`).
- **Carmen docs:** `../carmen/docs/business-analysis/price-list-ba.md`; `../carmen/docs/business-analysis/procurement-ba.md` (RFQ section) — treat as design intent, not confirmed behaviour, per Section 6 above.
