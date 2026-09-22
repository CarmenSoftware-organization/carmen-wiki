---
title: Vendor Pricelist — User Flow
description: Document lifecycle and persona-specific flow files for vendor-pricelist.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: vendor-pricelist, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow

> **At a Glance**
> **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist) &nbsp;·&nbsp; **Personas:** Purchaser &nbsp;·&nbsp; Vendor (external portal — save and submit work since 2026-08/09)
> **Real screens:** Vendor, Certification, Price List, Price List Template, Request for Pricing (RFQ) — five independent CRUD pages, no unified workspace, no workflow engine
> **Re-synced 2026-09-22:** portal Save/Submit routes exist and produce a `submitted` pricelist; the link expires at the RFQ `end_date`; the RFQ has a per-vendor Send-email action; Certification moved under Vendor Management.
> **Verified 2026-07-16:** Finance and Audit/Config are not distinct personas in this module — see [03-user-flow-finance](/en/inventory/vendor-pricelist/03-user-flow-finance) and [03-user-flow-audit-config](/en/inventory/vendor-pricelist/03-user-flow-audit-config)

## 1. Overview

This page is the overview entry point for the user-flow set of the `vendor-pricelist` module. A vendor pricelist (`tb_pricelist` header + `tb_pricelist_detail` rows) can be created two ways: **directly** by a Purchaser (manual entry, CSV import, or Excel upload on the Price List screen), or **via a Request for Pricing (RFQ)** — a Purchaser picks a [Price List Template](/en/inventory/vendor-pricelist/request-price-list) and names a vendor cohort in one create call, which immediately mints one cryptographic `pricelist_url_token` per invited vendor. Each vendor can open `/pl/:url_token`, the external portal; visiting it auto-creates a zero-priced draft pricelist from the template. The vendor prices the template's products, saves drafts, and submits — the pricelist becomes `submitted` and the Purchaser activates it on the internal Price List screen. That is the entire "workflow" this module's code implements — there is no campaign-launch step, no reminder schedule, no quality scoring, and no approve/reject action; delivery of the link is a manual per-vendor **Send email**.

Section 2 below lists the real status fields and what actually changes them. Section 3 links the two persona files that reflect real behaviour (Purchaser, Vendor). Section 4 lists the confirmed cross-persona handoffs. The previous version of this page described a 6-phase collection process (vendor setup → template → campaign → invitation → portal submission → validation) driven by three application-derived status machines (template / campaign / invitation) plus Manager and Finance-Manager approval gates — none of that state machinery, other than the two real Prisma-backed enums noted below, has any matching code.

## 2. Real Status Fields

| Table | Field | Values | What changes it |
| ----- | ----- | ------ | ---------------- |
| `tb_pricelist_template` | `status` | `draft`, `active`, `inactive` (`enum_pricelist_template_status`) | The template edit form's status control, or a direct call to `PATCH :id/status` — either way, a bare field write with no validation gate (no "must have ≥1 product" check, no re-activation guard). |
| `tb_request_for_pricing` | *(none)* | — | No status column and no derived state anywhere in code. The closest per-vendor signal is `has_submitted: !!pricelist_id` on each invitation row. |
| `tb_pricelist` | `status` | `draft`, `submitted`, `active`, `inactive`, `expired` (`enum_pricelist_status`) | The Price List edit form's status control (via the ordinary update call — no transition guard, no approve/reject action, `expired` never assigned) **or** the vendor's portal Submit (`draft → submitted`). The `draft → submitted` edge stamps `submitted_at` and deletes unpriced rows. |
| External portal | `tb_pricelist.status`, `submitted_at`; `tb_activity` events | `draft` → `submitted` | `POST /api/check-pricelist/:url_token` auto-creates or returns the draft; `PATCH /api/pricelist-external/:url_token` saves edits (stays `draft`); `POST …/submit` sets `submitted`. All three sit behind `UrlTokenGuard` (401 after the RFQ `end_date`). Events `create` / `save` / `submit` are logged to `tb_activity`. |

## 3. Persona Index

- [Purchaser](./03-user-flow-purchaser.md) — the only internal persona with a write surface: maintains Vendor master data and the Certification master, creates/edits Price List Templates and Price Lists directly, creates RFQs and emails each vendor its link, and activates the `submitted` pricelist a vendor returns (or keys in an emailed/CSV sheet).
- [Vendor](./03-user-flow-vendor.md) — external party with no Carmen login. Opens the emailed portal link before it expires, prices the products (tax profile and order unit per line), saves, imports an Excel sheet if preferred, and submits.

Note: **Finance** and **Audit / Config** were documented as distinct personas in the previous draft. Neither has any matching code in this module — see [03-user-flow-finance.md](./03-user-flow-finance.md) and [03-user-flow-audit-config.md](./03-user-flow-audit-config.md), both rewritten as correction pages this pass.

## 4. Cross-Persona Handoffs

| From persona | Trigger | To persona | Confirmed? |
| ------------ | ------- | ---------- | ---------- |
| Purchaser | Create an RFQ naming a template + vendor cohort | Vendor | **Confirmed** — one `create()` call mints all invitation tokens (and their `tb_shot_url` rows, expiring at `end_date`) at once. |
| Purchaser | **Send email** on a vendor row | Vendor | **Confirmed** — `POST …/request-for-pricings/:id/send-email` through an email profile; `email_sent` activity. |
| Vendor | Open the portal link | (auto) | **Confirmed** — `check-pricelists.check` auto-creates/returns a draft pricelist (401 once the link has expired). |
| Vendor | Save / Submit on the portal | Purchaser | **Confirmed (gap closed)** — `saveDraft()` keeps `draft`; `submit()` sets `submitted`, stamps `submitted_at`, prunes unpriced rows; the RFQ vendor row shows `has_submitted = true` and the pricelist status. |
| Purchaser | Review the `submitted` pricelist and set `status = active` on the Price List screen | (terminal — pricelist live) | **Confirmed** — no approve endpoint; the status control on the edit form is the award. |
| Purchaser | Preferred-row pick (`is_preferred` checkbox on one pricelist's own detail rows) | (feeds `price-compare`) | **Confirmed** — real per-row field, real comparison endpoint; not a cross-vendor matrix screen. |

Every cross-persona flow involving a Manager approval gate, a Finance Manager co-signoff, a Sysadmin token revocation, an auto-expiry cron, or an audit query workspace has been removed from this table — none of them have matching code (see [02-business-rules](/en/inventory/vendor-pricelist/02-business-rules) for the evidence).

## 5. References

- Sibling: [01-data-model.md](./01-data-model.md) — canonical entity / enum reference.
- Sibling: [02-business-rules.md](./02-business-rules.md) — the confirmed-vs-design-target status table this page's claims are drawn from.
- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/`, `routes/external/pl/`.
- Related modules: [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [product](/en/inventory/product).
