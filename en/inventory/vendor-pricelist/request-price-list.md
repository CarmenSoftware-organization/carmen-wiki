---
title: Request for Quotation
description: Outbound request-for-price (RFQ) sent to one or more vendors — collects bids before negotiating a new pricelist.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, rfq, procurement, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Request for Quotation

> **At a Glance**
> **Owner:** Purchaser / Procurement Manager &nbsp;·&nbsp; **Table:** `tb_request_for_pricing` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** none (date-window driven) &nbsp;·&nbsp; **Upstream:** [templates/price-list](/en/inventory/templates/price-list) &nbsp;·&nbsp; Solicits price quotes from vendors before a `tb_pricelist` is awarded.

![Request for Quotation screen](/screenshots/vendor-pricelist/request-price-list.png)

![Request for Quotation detail screen](/screenshots/vendor-pricelist/request-price-list-detail.png)

## 1. What & Who

**Request for Pricing (RFQ)** is the procurement-initiated outbound document that solicits quotes from one or more vendors before a [vendor-pricelist](/en/inventory/vendor-pricelist) is awarded. The buyer picks a [templates/price-list](/en/inventory/templates/price-list) (which carries currency, validity window, reminder schedule, and the product catalogue under quote), names candidate vendors, and dispatches the request. Each invited vendor gets a **tokenised link** to a portal where they submit prices; submissions land as draft `tb_pricelist` rows keyed back to the RFQ. After the deadline, the buyer compares bids and *awards* one (or more) by flipping its status to `active`.

**Created by** Purchaser &nbsp;·&nbsp; **Responded to by** invited vendors (no login — token-scoped portal; **confirmed gap:** the portal can only view the auto-created draft today, see [03-user-flow-vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor)) &nbsp;·&nbsp; **Produces no inventory or AP effect.**

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create an RFQ from a template | Vendor Management → Request Price List → **New** | Template binds currency + product catalogue |
| Invite vendors | Same create form → vendor rows | All invitation rows (and their `pricelist_url_token`s) are created in the same `POST` call as the RFQ header — there is no separate "launch" or "send" step. |
| Add more vendors to an existing RFQ | Detail → edit → add vendor row | `PATCH` supports `vendors.add`/`vendors.remove`/`vendors.update`; unique constraint on `(request_for_pricing_id, vendor_id)` enforces no double-invite. |
| Compare / award | Purchaser edits the vendor's pricelist directly on the **Price List** screen | Awarding = setting the winning `tb_pricelist.status = active` from the Price List edit form — there is no dedicated "Compare" or "Activate" button on the RFQ screen itself, and no bid-comparison UI was found. |

## 3. Validation & Errors

| Symptom / Message | Cause | Confirmed? |
|---|---|---|
| "Vendor already invited" | A non-deleted detail row exists for (RFQ, vendor) | **Confirmed** — `@@unique([request_for_pricing_id, vendor_id, deleted_at])`. |
| RFQ creation rejected with an invalid date range | `start_date > end_date` | **Confirmed** — `request-for-pricing.service.ts create()` explicitly checks this (`RFP_INVALID_DATE_RANGE`). |
| "Cannot change template — invitations sent" | `pricelist_template_id` immutable post-dispatch | **Not confirmed.** `update()` accepts a new `pricelist_template_id` with no immutability check once vendor rows exist. |
| Late submission rejected after `end_date` | Portal enforces the deadline | **Not confirmed.** `checkPricelist()` (the one working portal call) never reads `end_date`; there is no late-submission guard anywhere in this module's code. |
| "Vendor must be active" | `tb_vendor.is_active = false` blocks the invite | **Not confirmed.** No `is_active` check on the vendor was found in `create()` or `update()`. |
| Invitation link 404s / returns an error | Row soft-deleted, or the vendor-portal Save/Submit gap (see below) | Soft-delete on the RFQ detail row is real (`vendors.remove`); the Save/Submit 404/failure is the confirmed backend-route gap, not token rotation — no token-rotation code exists either. |

## 4. Edge Cases

- **Token security.** `pricelist_url_token` is a random string per invitation, generated once at RFQ-create time; portal access is scoped by the token alone (vendors do not authenticate). No expiration check, no IP restriction, and no revocation/rotation code exists anywhere in this module.
- **No late-submission enforcement found.** The design intent (reject a portal submission after `end_date`) has no matching code — moot in practice today anyway, since the portal's Save/Submit calls do not reach a working backend route at all (see [03-user-flow-vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor)).
- **Award is a pricelist-level flip, not RFQ-level.** The RFQ has no status column of its own — "awarding" is simply the Purchaser setting the chosen `tb_pricelist.status = active` directly on the Price List screen.
- **Currency cascade.** The template supplies a default currency to the auto-created draft pricelist; nothing was found preventing a Purchaser from changing `currency_id` afterwards on the Price List edit form.
- **No reminder job found.** A repo-wide search of this module and `micro-cronjobs` found no scheduled job reading `reminder_days`/`escalation_after_days` — those template fields are stored but currently inert.
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
- **Portal visit** — the vendor's first `POST /api/check-pricelist/:url_token` auto-creates a zero-priced draft `tb_pricelist` from the template. Confirmed **not** gated by `start_date`/`end_date` in any way.
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
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/request-for-pricing/request-for-pricing.service.ts`, `.../check-price-list/check-price-list.service.ts`.
- **Carmen docs:** `../carmen/docs/business-analysis/price-list-ba.md`; `../carmen/docs/business-analysis/procurement-ba.md` (RFQ section) — treat as design intent, not confirmed behaviour, per Section 6 above.
