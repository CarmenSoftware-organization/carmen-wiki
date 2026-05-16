---
title: Request for Quotation
description: Outbound request-for-price (RFQ) sent to one or more vendors — collects bids before negotiating a new pricelist.
published: true
date: 2026-05-16T17:00:00.000Z
tags: vendor-pricelist, rfq, procurement, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Request for Quotation

## 1. Purpose

**Request for Pricing (RFQ)** is the procurement-initiated outbound document that solicits quotes from one or more vendors before a `tb_pricelist` is awarded. The Purchaser or Procurement Manager picks a [[templates/price-list]] (which carries the currency, validity window, reminder schedule, and the catalogue of products to be quoted), names a set of candidate vendors on it, and dispatches the request. Each invited vendor receives a tokenised link to a portal where they submit their prices; the submission lands as a draft `tb_pricelist` keyed back to this RFQ. Once the deadline passes, the buyer compares bids and either *awards* one pricelist (flipping it to `active`) or runs a second round.

The RFQ sits **upstream** of every transactional document — PR, PO, GRN. Wiki coverage treats it as the entry point into the [[vendor-pricelist]] catalogue, not a transactional document, because it produces no inventory or AP effect.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_request_for_pricing`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | RFQ display name (e.g. "Q2-2026 Beverage RFQ"). |
| `pricelist_template_id` | `String @db.Uuid` | No | FK to [[templates/price-list]]. The template defines currency, validity, reminders, and the product catalogue under quote. |
| `start_date` | `DateTime? @db.Timestamptz(6)` | Yes | Date vendors may begin submitting prices. |
| `end_date` | `DateTime? @db.Timestamptz(6)` | Yes | Submission deadline; drives reminder scheduling and escalation. |
| `custom_message` | `String? @db.Text` | Yes | Free-text message rendered in the invitation email. |
| `email_template_id` | `String? @db.VarChar` | Yes | Identifier of the email template used for invitation and reminder mails. |
| `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `request_for_pricing_name_u`; `@@index([pricelist_template_id])`; `@@index([name])`. FK to `tb_pricelist_template` `onDelete: NoAction`. Reverse relations to `tb_request_for_pricing_detail` and `tb_request_for_pricing_comment`.

### 2.2 `tb_request_for_pricing_detail`

One row per invited vendor on the RFQ.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `request_for_pricing_id`, `sequence_no` | mixed | No / No / Yes | PK, parent FK, ordinal. |
| `vendor_id`, `vendor_name` | `String @db.Uuid` / `VarChar` | No / Yes | Invited vendor + display snapshot. |
| `contact_person`, `contact_phone`, `contact_email` | `String? @db.VarChar` | Yes | Vendor-side contact for this RFQ round. |
| `pricelist_id`, `pricelist_no` | `String? @db.Uuid` / `VarChar` | Yes | FK to the `tb_pricelist` row created when the vendor submits — null until submission. |
| `pricelist_url_token` | `String? @db.VarChar` | Yes | Tokenised URL fragment used by the invitation email; vendor follows this link to a portal scoped to their submission. |
| `comment`, `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([request_for_pricing_id, vendor_id, deleted_at])` map `request_for_pricing_detail_request_for_pricing_id_vendor_id_u` — one invitation row per (RFQ, vendor); `@@index([request_for_pricing_id, vendor_id])`. FKs to `tb_request_for_pricing`, `tb_vendor`, `tb_pricelist` — all `onDelete: NoAction`.

### 2.3 Comment tables

`tb_request_for_pricing_comment` and `tb_request_for_pricing_detail_comment` follow the canonical comment shape (type, user, message, JSON attachments, audit columns).

## 3. Workflow / Lifecycle

RFQ does **not** use the generic workflow engine — it has no `workflow_*` columns. Lifecycle is driven by date windows and the state of child `tb_pricelist` rows (see [[vendor-pricelist]] for the pricelist's own `enum_pricelist_status`):

- **Setup** — RFQ row created from a template; vendor detail rows added. No invitation has been sent yet.
- **Invitation sent** — each detail row gets a `pricelist_url_token`; invitation emails dispatch via the `email_template_id`.
- **Open for response** (`start_date <= now < end_date`) — vendors submit through the portal. Each submission creates a `tb_pricelist` in `draft`, linked back via `tb_request_for_pricing_detail.pricelist_id`.
- **Reminders / escalation** — per [[templates/price-list]] `reminder_days[]` and `escalation_after_days`, a background job sends chasers to non-responding vendors and escalates after the configured grace period.
- **Closed for response** (`now >= end_date`) — portal is locked; late submissions are rejected.
- **Award** — buyer reviews the candidate `tb_pricelist` rows and flips the chosen one to `active`. Non-winning pricelists stay `draft` (visible for audit) or are flipped to `inactive`.

There is no system "awarded" status on the RFQ itself; the act of awarding is the pricelist status flip.

## 4. Usage / Cross-References

- [[vendor-pricelist]] — vendor responses materialise here as `tb_pricelist` rows; the awarded pricelist becomes the active catalogue PR/PO consume.
- [[templates/price-list]] — RFQ requires a template, which carries currency, validity, reminder schedule, and the product catalogue.
- [[master-data/vendor]] — invited vendors must reference active vendor records.
- [[master-data/currency]] — currency cascades from the template; all submissions are in that single currency.
- [[purchase-request]] / [[purchase-order]] — downstream consumers of the awarded pricelist's prices.
- [[system-config/workflow]] — *not used* by the RFQ itself; mentioned only to clarify the difference from approvable documents.

## 5. Business Rules

- **One invitation per vendor.** Unique constraint on `(request_for_pricing_id, vendor_id, deleted_at)` prevents double-inviting the same vendor on the same round.
- **Template-bound.** `pricelist_template_id` is required and immutable after the first invitation has been sent — switching templates mid-round would invalidate the existing portal links.
- **Date validation.** `end_date > start_date`; both must be in the future at the moment invitations are sent. The reminder job uses these dates literally — no implicit grace.
- **Token security.** `pricelist_url_token` is a long random string per invitation; portal access is scoped by the token alone (vendors do not authenticate). Token rotation invalidates all outstanding invitations for that vendor.
- **Bid evaluation.** When the buyer awards, the system surfaces each invited vendor's pricelist alongside the historic price (from the previous active pricelist for the same product). Money is normalised to BU base currency via [[master-data/exchange-rate]] on the comparison date for fair ranking, even though storage stays in the template's currency.
- **Late submission.** A `tb_pricelist` insert after `end_date` is rejected at the API layer. Buyer may extend `end_date` (an explicit edit, audit-logged) before close to accept additional bids.
- **Award is non-exclusive at the engine level.** The system allows multiple pricelists to be flipped to `active` per product — split awards across vendors are supported. The catalogue's ranking rule (typically lowest-price-wins on PR auto-allocation) decides which wins at PR/PO time.
- **Currency.** Inherits from the template — vendors cannot override per-line currency. Cross-currency RFQs require separate RFQ rounds per currency.
- **Idempotent dispatch.** Re-sending the invitation email reuses the existing `pricelist_url_token` on the detail row; no new `tb_pricelist` is created.
- **Snapshot semantics.** Vendor name, contact, and template fields are snapshotted at invitation time. Edits to the underlying master records do not retroactively change the RFQ row.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_request_for_pricing` (lines 4039-4070), `tb_request_for_pricing_detail` (lines 4106-4142), `tb_request_for_pricing_comment` (lines 4072-4104), `tb_request_for_pricing_detail_comment` (lines 4144-4176).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/vendor-management/request-price-list/`.
- **Carmen docs:** `../carmen/docs/business-analysis/price-list-ba.md`; `../carmen/docs/business-analysis/procurement-ba.md` (RFQ section).
- **Cross-module:** see Section 4.
