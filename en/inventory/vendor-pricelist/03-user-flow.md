---
title: Vendor Pricelist — User Flow
description: Document lifecycle and persona-specific flow files for vendor-pricelist.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow

> **At a Glance**
> **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist) &nbsp;·&nbsp; **Personas:** Purchaser &nbsp;·&nbsp; Vendor (external, confirmed-broken submit path)
> **Real screens:** Vendor, Price List, Price List Template, Request for Pricing (RFQ) — four independent CRUD pages, no unified workspace, no workflow engine
> **Verified 2026-07-16:** Finance and Audit/Config are not distinct personas in this module — see [03-user-flow-finance](/en/inventory/vendor-pricelist/03-user-flow-finance) and [03-user-flow-audit-config](/en/inventory/vendor-pricelist/03-user-flow-audit-config)

## 1. Overview

This page is the overview entry point for the user-flow set of the `vendor-pricelist` module. A vendor pricelist (`tb_pricelist` header + `tb_pricelist_detail` rows) can be created two ways: **directly** by a Purchaser (manual entry, CSV import, or Excel upload on the Price List screen), or **via a Request for Pricing (RFQ)** — a Purchaser picks a [Price List Template](/en/inventory/vendor-pricelist/request-price-list) and names a vendor cohort in one create call, which immediately mints one cryptographic `pricelist_url_token` per invited vendor. Each vendor can open `/pl/:url_token`, the external portal; visiting it auto-creates a zero-priced draft pricelist from the template. That is the entire "workflow" this module's code actually implements — there is no campaign-launch step, no reminder schedule, no quality scoring, and (per the confirmed gap below) no working way for the vendor to actually save or submit through that portal today.

Section 2 below lists the real status fields and what actually changes them. Section 3 links the two persona files that reflect real behaviour (Purchaser, Vendor). Section 4 lists the confirmed cross-persona handoffs. The previous version of this page described a 6-phase collection process (vendor setup → template → campaign → invitation → portal submission → validation) driven by three application-derived status machines (template / campaign / invitation) plus Manager and Finance-Manager approval gates — none of that state machinery, other than the two real Prisma-backed enums noted below, has any matching code.

## 2. Real Status Fields

| Table | Field | Values | What changes it |
| ----- | ----- | ------ | ---------------- |
| `tb_pricelist_template` | `status` | `draft`, `active`, `inactive` (`enum_pricelist_template_status`) | The template edit form's status control, or a direct call to `PATCH :id/status` — either way, a bare field write with no validation gate (no "must have ≥1 product" check, no re-activation guard). |
| `tb_request_for_pricing` | *(none)* | — | No status column and no derived state anywhere in code. The closest per-vendor signal is `has_submitted: !!pricelist_id` on each invitation row. |
| `tb_pricelist` | `status` | `draft`, `active`, `inactive`, `expired` (`enum_pricelist_status`) | The Price List edit form's status control, via the ordinary update call — same caveat: no transition guard, no distinct approve/reject/submit action, no auto-expire cron found in this repo. |
| External portal | *(none persisted by the portal itself)* | — | `POST /api/check-pricelist/:url_token` auto-creates or returns a draft pricelist. The portal's own Save/Submit buttons call routes (`PATCH`/`POST .../pricelist-external/:token[/submit]`) that do not exist in the backend — confirmed by a repo-wide search finding zero matches for `pricelist-external` outside the frontend's own endpoint-constant file. |

## 3. Persona Index

- [Purchaser](./03-user-flow-purchaser.md) — the only internal persona with a write surface: maintains Vendor master data, creates/edits Price List Templates and Price Lists directly, creates RFQs, and edits/activates whatever draft a vendor's portal visit (or an emailed/CSV submission) produces.
- [Vendor](./03-user-flow-vendor.md) — external party with no Carmen login. Opens the portal link; the portal auto-creates a draft. The portal's Save/Submit calls are confirmed broken against the current backend.

Note: **Finance** and **Audit / Config** were documented as distinct personas in the previous draft. Neither has any matching code in this module — see [03-user-flow-finance.md](./03-user-flow-finance.md) and [03-user-flow-audit-config.md](./03-user-flow-audit-config.md), both rewritten as correction pages this pass.

## 4. Cross-Persona Handoffs

| From persona | Trigger | To persona | Confirmed? |
| ------------ | ------- | ---------- | ---------- |
| Purchaser | Create an RFQ naming a template + vendor cohort | Vendor | **Confirmed** — one `create()` call mints all invitation tokens at once. |
| Vendor | Open the portal link | (auto) | **Confirmed** — `check-pricelists.check` auto-creates/returns a draft pricelist. |
| Vendor | Attempt Save / Submit on the portal | (nobody — call fails) | **Confirmed gap** — the target route does not exist in the backend. |
| Purchaser | Edit and activate the auto-created draft directly on the Price List screen | (terminal — pricelist live) | **Confirmed** — this is the real path to an `active` pricelist sourced from an RFQ today, since the portal itself cannot persist. |
| Purchaser | Preferred-row pick (`is_preferred` checkbox on one pricelist's own detail rows) | (feeds `price-compare`) | **Confirmed** — real per-row field, real comparison endpoint; not a cross-vendor matrix screen. |

Every cross-persona flow involving a Manager approval gate, a Finance Manager co-signoff, a Sysadmin token revocation, an auto-expiry cron, or an audit query workspace has been removed from this table — none of them have matching code (see [02-business-rules](/en/inventory/vendor-pricelist/02-business-rules) for the evidence).

## 5. References

- Sibling: [01-data-model.md](./01-data-model.md) — canonical entity / enum reference.
- Sibling: [02-business-rules.md](./02-business-rules.md) — the confirmed-vs-design-target status table this page's claims are drawn from.
- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/`, `routes/external/pl/`.
- Related modules: [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [product](/en/inventory/product).
