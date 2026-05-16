---
title: Request for Quotation
description: Outbound request-for-price (RFQ) sent to one or more vendors — collects bids before negotiating a new pricelist.
published: true
date: 2026-05-17T08:00:00.000Z
tags: vendor-pricelist, rfq, procurement, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Request for Quotation

> **At a Glance**
> **Owner:** Purchaser / Procurement Manager &nbsp;·&nbsp; **Table:** `tb_request_for_pricing` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** none (date-window driven) &nbsp;·&nbsp; **Upstream:** [[templates/price-list]] &nbsp;·&nbsp; Solicits price quotes from vendors before a `tb_pricelist` is awarded.

## 1. What & Who

**Request for Pricing (RFQ)** is the procurement-initiated outbound document that solicits quotes from one or more vendors before a [[vendor-pricelist]] is awarded. The buyer picks a [[templates/price-list]] (which carries currency, validity window, reminder schedule, and the product catalogue under quote), names candidate vendors, and dispatches the request. Each invited vendor gets a **tokenised link** to a portal where they submit prices; submissions land as draft `tb_pricelist` rows keyed back to the RFQ. After the deadline, the buyer compares bids and *awards* one (or more) by flipping its status to `active`.

**Created by** Purchaser / Procurement Manager &nbsp;·&nbsp; **Responded to by** invited vendors (no login — token-scoped portal) &nbsp;·&nbsp; **Produces no inventory or AP effect.**

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create an RFQ from a template | Vendor Management → Request Price List → **New** | Template binds currency + product catalogue |
| Invite vendors | Detail → **Add Vendor** | One row per (RFQ, vendor); unique constraint enforces no double-invite |
| Send / resend invitation email | Detail → **Send** | Idempotent — reuses existing `pricelist_url_token` |
| Extend the deadline | Header → edit `end_date` | Audit-logged; required to accept late bids |
| Compare bids | Detail → **Compare** | Normalises to BU base currency via [[master-data/exchange-rate]] |
| Award a pricelist | Pricelist row → **Activate** | Flips `enum_pricelist_status` to `active` — RFQ itself has no "awarded" status |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Vendor already invited" | A non-deleted detail row exists for (RFQ, vendor) | Edit the existing invitation instead |
| "end_date must be after start_date" | Date window invalid | Re-pick the deadline |
| "Cannot change template — invitations sent" | `pricelist_template_id` is immutable post-dispatch | Cancel the RFQ and start a new one |
| "Late submission rejected" | Portal POST after `end_date` | Extend `end_date` first (audit-logged) before re-sending |
| "Vendor must be active" | `tb_vendor.is_active = false` | Reactivate under [[master-data/vendor]] |
| Invitation link 404s | `pricelist_url_token` rotated or row soft-deleted | Re-issue the invitation; a fresh token is generated |

## 4. Edge Cases

- **Token security.** `pricelist_url_token` is a long random string per invitation; portal access is scoped by the token **alone** (vendors do not authenticate). Token rotation invalidates all outstanding invitations for that vendor.
- **Late submissions rejected.** A `tb_pricelist` insert after `end_date` is rejected at the API layer. The buyer must explicitly extend `end_date` before close to accept additional bids.
- **Award is a pricelist-level flip, not RFQ-level.** The RFQ has no system "awarded" status — awarding = flipping the chosen `tb_pricelist` to `active`. Multiple pricelists may be active per product (split awards).
- **Currency cascade.** RFQ inherits currency from the template; vendors cannot override per-line. Cross-currency RFQs require **separate rounds per currency**.
- **Idempotent dispatch.** Re-sending the invitation reuses the existing token; no new `tb_pricelist` is created.
- **Snapshot semantics.** Vendor name, contact, and template fields are snapshotted at invitation time. Master-record edits do not retroactively change the RFQ row.
- **No workflow engine.** RFQ has no `workflow_*` columns; lifecycle is purely date-window + pricelist-status driven.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_request_for_pricing`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | RFQ display name (e.g. "Q2-2026 Beverage RFQ"). |
| `pricelist_template_id` | `String @db.Uuid` | No | FK to [[templates/price-list]]. Carries currency, validity, reminders, catalogue. |
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

RFQ does **not** use the generic workflow engine. Lifecycle is driven by date windows and child `tb_pricelist` state:

- **Setup** — RFQ created from template; vendor detail rows added. No invitation sent yet.
- **Invitation sent** — each detail row gets `pricelist_url_token`; emails dispatch via `email_template_id`.
- **Open for response** (`start_date <= now < end_date`) — vendors submit through the portal; each submission creates a `tb_pricelist` in `draft`.
- **Reminders / escalation** — per [[templates/price-list]] `reminder_days[]` and `escalation_after_days`, a background job chases non-responding vendors.
- **Closed for response** (`now >= end_date`) — portal locked; late submissions rejected.
- **Award** — buyer flips the chosen `tb_pricelist` to `active`; losers stay `draft` or flip to `inactive`.

**Date validation:** `end_date > start_date`; both must be in the future when invitations are sent. **Template-bound:** `pricelist_template_id` immutable after first invitation. **Currency:** inherits from template; per-line override forbidden.

## 7. Cross-References

- [[vendor-pricelist]] — vendor responses materialise as `tb_pricelist` rows; the awarded one becomes the active catalogue.
- [[templates/price-list]] — RFQ requires a template (currency, validity, reminders, product catalogue).
- [[master-data/vendor]] — invited vendors must reference active vendor records.
- [[master-data/currency]] — currency cascades from the template.
- [[purchase-request]] / [[purchase-order]] — downstream consumers of the awarded pricelist.
- [[system-config/workflow]] — *not used* by RFQ; mentioned for contrast.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_request_for_pricing` (lines 4039-4070), `tb_request_for_pricing_detail` (lines 4106-4142), `tb_request_for_pricing_comment` (lines 4072-4104), `tb_request_for_pricing_detail_comment` (lines 4144-4176).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/vendor-management/request-price-list/`.
- **Carmen docs:** `../carmen/docs/business-analysis/price-list-ba.md`; `../carmen/docs/business-analysis/procurement-ba.md` (RFQ section).
