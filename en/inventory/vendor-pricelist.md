---
title: Vendor Pricelist
description: Vendor catalogs of products with agreed prices, units, and validity periods — the reference for PR/PO pricing.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Vendor Pricelist

> **At a Glance**
> **Module purpose:** Vendor-specific, time-bound MOQ-tiered price catalogue — Vendor master data, Price List, Price List Template, and Request-for-Pricing (RFQ) are four independent CRUD screens under Vendor Management, plus an unauthenticated external vendor portal — the reference for PR / PO pricing and GRN variance &nbsp;·&nbsp; **Audience:** Purchaser, Vendor (external portal) &nbsp;·&nbsp; **Key entities/tables:** `tb_pricelist`, `tb_pricelist_detail`, `tb_request_for_pricing`, `tb_pricelist_template`, [vendor-pricelist/request-price-list](/en/inventory/vendor-pricelist/request-price-list) &nbsp;·&nbsp; **Sub-pages:** 13
>
> **Verified 2026-07-16 against current source:** this module has **no workflow engine** (no `workflow_*` columns, unlike PR/PO/GRN/SR) and **no distinct approve/reject endpoints** — `tb_pricelist.status` and `tb_pricelist_template.status` are plain enum fields flipped by whoever has edit rights via the ordinary update call. There is no quality score, no validation engine beyond field-level checks, no high-value/multi-currency Manager threshold, no portal-token IP allowlist or session limit, no token-revocation action, and no automatic "system" comment logging on any transition — none of these have any matching code. Finance and Audit/Config are **not** distinct personas in this module. See [02-business-rules](/en/inventory/vendor-pricelist/02-business-rules), [03-user-flow-finance](/en/inventory/vendor-pricelist/03-user-flow-finance), and [03-user-flow-audit-config](/en/inventory/vendor-pricelist/03-user-flow-audit-config) for the corrected detail.

![Vendor Pricelist screen](/screenshots/vendor-pricelist/index.png)

## 1. Overview

A **Vendor Pricelist** (`tb_pricelist`) is the record of the prices a specific vendor has quoted for a specific set of products, expressed in the vendor's currency, scoped to a validity period, and structured around the unit and minimum-order-quantity (MOQ) tiers the vendor will honour. Each pricelist has a header — vendor, pricelist number, currency, validity-from and validity-to dates, submission method, and status — and one or more detail rows that carry the product reference, the MOQ-tiered pricing (unit, unit price, tax, lead time, an `is_preferred` flag), and notes. The same product on the same vendor's pricelist can carry multiple MOQ rows (e.g., MOQ 1 at ฿12.50/Each, MOQ 50 at ฿10.50/Each, MOQ 100 at ฿9.75/Each) because `moq_qty` is part of the row's uniqueness key.

Pricelists are vendor-specific and time-bound. Several vendors can carry the same product, each on their own pricelist at their own price and currency; the `is_preferred` checkbox on a pricelist's own detail rows marks which row the Purchaser wants used as the default source, and a `GET .../pricelists/price-compare` endpoint returns the matching rows across all vendors sorted `is_preferred desc, price asc` for a given product/currency/date — this is the real (and much simpler) mechanism behind "preferred vendor" pricing; there is no cross-vendor comparison screen and no automatic rule engine that sets the flag. Multi-currency is supported at the storage level — the pricelist's `currency_id` is whatever the creator picked — but no code converts or reconciles FX at the point of use; conversion, if needed, is a downstream-module concern.

A pricelist can be created directly by a Purchaser (manual entry, CSV import, or Excel upload), or it can arrive through the **Request for Pricing (RFQ)** flow: a Purchaser creates an RFQ from a [Price List Template](/en/inventory/vendor-pricelist/request-price-list) naming the invited vendors, and the backend immediately generates one cryptographic `pricelist_url_token` per invited vendor. Each vendor can open `/pl/:url_token` (the external portal) — visiting the link auto-creates a zero-priced draft pricelist from the template. **Confirmed gap:** the portal's Save and Submit buttons call backend routes (`PATCH`/`POST .../pricelist-external/:token[/submit]`) that do not exist anywhere in the current backend — so today a vendor can view the auto-created draft but cannot actually persist edits or submit through this portal. A Purchaser can still edit and activate that draft directly from the internal Price List screen once it exists.

Once a pricelist's `status` is set to `active` (by editing the record — no separate approval step), it becomes queryable as the reference for downstream procurement: PR pricing can default from the preferred row, PO conversion snapshots the price, and GRN posting can compare against it. Inactive and expired pricelists remain queryable for history.

## 2. Business Context

The vendor pricelist gives procurement a system-of-record for negotiated rates instead of relying on the vendor's quote-of-the-day. `price-compare` lets PR/PO pricing default to whichever vendor row is marked preferred (or the cheapest, if none is), and GRN variance checks (documented in [good-receive-note](/en/inventory/good-receive-note)) can compare a received price against the active pricelist.

Operationally, the module is four straightforward CRUD screens rather than a guided campaign wizard: **Vendor** (vendor master data — contacts, addresses, business type, certificates), **Price List** (the vendor's quoted prices), **Price List Template** (what a future RFQ will ask vendors to quote: products, default currency, validity window), and **Request for Pricing** (an outbound RFQ naming a template and a vendor cohort — see [request-price-list](/en/inventory/vendor-pricelist/request-price-list)). A `/vendor-management` dashboard shows KPI widgets (active-vendor count, active-pricelist count, pricelists expiring soon, RFQs upcoming) but there is no unified tabbed "workspace" joining the four screens. CSV import (grouped upsert keyed on `pricelist_no`) and an Excel-style upload/download exist for bulk pricelist maintenance.

## 3. Key Concepts

- **Pricelist Header** (`tb_pricelist`): vendor reference, pricelist number, currency, validity-from/-to, `submission_method` (`online`, `email`, `portal`, `manual`), and `status` (`draft`, `active`, `inactive`, `expired` — `enum_pricelist_status`). No campaign/quality-score/validation-result fields exist on the header; those live only in a schemaless `info` JSON bag that no current service reads or writes.
- **Pricelist Detail Row** (`tb_pricelist_detail`): product, unit, one MOQ-tier row per `(product, unit, moq_qty)` combination, `price_without_tax` / `tax_rate` / `tax_amt` / `price` (the tax breakdown is computed client-side before save; the backend persists whatever it receives without recomputing), `lead_time_days`, `rating`, and `is_preferred` (a plain per-row checkbox, independently settable on each pricelist — not a cross-vendor matrix screen).
- **Price List Template** (`tb_pricelist_template`): a reusable definition of what an RFQ will ask for — a product list (with a default order unit + MOQ-tier shape per product), a default currency, a `validity_period` (days), and a reminder-day array. Has its own `status` (`draft`/`active`/`inactive`) with a dedicated `PATCH :id/status` endpoint, but that endpoint performs no validation of any kind (no "must have at least one product" gate) — it is a bare status write.
- **Request for Pricing (RFQ)** (`tb_request_for_pricing` + `tb_request_for_pricing_detail`): pins one template to a named list of vendors with a `start_date`/`end_date` window. All per-vendor invitation tokens are generated in the same create call — there is no separate "launch" step, no reminder job, and no derived `paused`/`cancelled`/`completed` campaign state (no code reads or writes any such flag). The only per-vendor signal the UI shows is `has_submitted: !!pricelist_id`.
- **Portal Token** (`pricelist_url_token`): a random string per invited vendor, embedded in `/pl/:url_token`. It gates the one working portal call (auto-create/return the draft pricelist). There is no expiration check, no IP allowlist, no session limit, and no revoke action anywhere in the code — none of these exist.
- **Preferred Row** (`is_preferred` on `tb_pricelist_detail`): the Purchaser's manual pick of which vendor's row `price-compare` should surface first for a product/currency/date; there is no automatic rule engine that sets it.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Purchaser | Maintains vendor master data, creates and edits price list templates and price lists directly, creates RFQs naming a template and a vendor cohort, and (once a vendor's portal-created draft or an emailed/CSV submission exists) edits and activates the pricelist. There is no separate approval step or Manager-only gate — whoever has edit rights on the screen can flip `status`. |
| Vendor | External party with no Carmen login. Opens `/pl/:url_token` from the invitation; the portal auto-creates a draft pricelist from the template. **Confirmed gap:** the portal's Save/Submit calls hit backend routes that do not exist today, so the vendor cannot currently persist edits or submit through this screen — the Purchaser edits the auto-created draft directly on the internal Price List screen instead. |
| Receiver / Store Keeper | Indirect consumer — GRN posting can compare a received price against the active pricelist ([good-receive-note](/en/inventory/good-receive-note)). No write surface here. |

No distinct Finance or Audit/Config persona exists for this module — see [03-user-flow-finance](/en/inventory/vendor-pricelist/03-user-flow-finance) and [03-user-flow-audit-config](/en/inventory/vendor-pricelist/03-user-flow-audit-config) for what was previously documented and why it does not match current source.

## 5. Related Modules

**Cross-module flow:**
- [product](/en/inventory/product) — pricelist entries reference products
- [purchase-request](/en/inventory/purchase-request) — PRs default to preferred vendor pricelists
- [purchase-order](/en/inventory/purchase-order) — POs validate prices against the active pricelist
- [good-receive-note](/en/inventory/good-receive-note) — GRN price variance is calculated against pricelist

**Master configuration:**
- [master-data/vendor](/en/inventory/master-data/vendor) — vendor master each pricelist is scoped to
- [master-data/currency](/en/inventory/master-data/currency) — currency the vendor selects at submission
- [master-data/tax-profile](/en/inventory/master-data/tax-profile) — tax codes on each pricelist line
- [templates/price-list](/en/inventory/templates/price-list) — reusable template defining what products/currency/validity an RFQ asks vendors for
- [master-data/unit](/en/inventory/master-data/unit) — pricing unit (Box / Carton / Pack) referenced by pricelist detail rows

Note: this module has **no workflow engine** — `status` on `tb_pricelist` / `tb_pricelist_template` is a plain field, not a [system-config/workflow](/en/inventory/system-config/workflow) stage chain — and no automatic activity-log writes; the `*_comment` tables exist but are populated only by explicit user comments, not by transitions.

## 6. Reference Sources

- Concepts: `../carmen/docs/vendor-pricelist-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [vendor-pricelist/01-data-model](/en/inventory/vendor-pricelist/01-data-model) — entities, fields, relationships, enums for the ten tenant-schema models (`tb_pricelist_template`, `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, `tb_pricelist_template_detail_comment`, `tb_request_for_pricing`, `tb_request_for_pricing_comment`, `tb_request_for_pricing_detail`, `tb_request_for_pricing_detail_comment`, `tb_pricelist`, `tb_pricelist_detail`, `tb_pricelist_comment`, `tb_pricelist_detail_comment`) and the three module-local enums (`enum_pricelist_template_status`, `enum_pricelist_status`, `pricelist_submission_method`) plus the divergence table for the 12 material differences between carmen/docs `design.md` and Prisma.
- [01a — Data Model — Comment Tables](/en/inventory/vendor-pricelist/01a-data-model-comments) — Document-level and line-level comment / attachment tables across the pricelist template, request-for-pricing, and pricelist sub-entity families.
- [vendor-pricelist/02-business-rules](/en/inventory/vendor-pricelist/02-business-rules) — validation (`VPL_VAL_001`–`VPL_VAL_025`, confirmed subset), calculation (`VPL_CALC_001`–`VPL_CALC_003`), and cross-module rules — rewritten 2026-07-16 to drop unconfirmed authorization thresholds, posting-workflow rule IDs, and campaign/invitation state machines that have no matching code.
- [vendor-pricelist/03-user-flow](/en/inventory/vendor-pricelist/03-user-flow) — document-lifecycle overview + persona index.
  - [vendor-pricelist/03-user-flow-purchaser](/en/inventory/vendor-pricelist/03-user-flow-purchaser) — Purchaser path across the four real CRUD screens (Vendor, Price List, Price List Template, Request for Pricing).
  - [vendor-pricelist/03-user-flow-vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor) — Vendor (external, token-authenticated portal) path, including the confirmed Save/Submit backend gap.
  - [vendor-pricelist/03-user-flow-finance](/en/inventory/vendor-pricelist/03-user-flow-finance) — correction page: no distinct Finance persona or co-signoff mechanism exists in this module.
  - [vendor-pricelist/03-user-flow-audit-config](/en/inventory/vendor-pricelist/03-user-flow-audit-config) — correction page: no dedicated Audit workspace or Configuration console exists in this module.
- [vendor-pricelist/04-test-scenarios](/en/inventory/vendor-pricelist/04-test-scenarios) — test-scenarios overview + cross-persona scenarios grounded in the real CRUD screens + real E2E coverage.
  - [vendor-pricelist/04-test-scenarios-purchaser](/en/inventory/vendor-pricelist/04-test-scenarios-purchaser) — Purchaser scenarios.
  - [vendor-pricelist/04-test-scenarios-vendor](/en/inventory/vendor-pricelist/04-test-scenarios-vendor) — Vendor scenarios; Permission section is N/A because the vendor has no Carmen RBAC matrix.
  - [vendor-pricelist/04-test-scenarios-finance](/en/inventory/vendor-pricelist/04-test-scenarios-finance) — correction page.
  - [vendor-pricelist/04-test-scenarios-audit-config](/en/inventory/vendor-pricelist/04-test-scenarios-audit-config) — correction page.

> **Status (verified 2026-07-16):** data-model section is grounded in the canonical Prisma schema (`tb_pricelist*` + `tb_request_for_pricing*` + `tb_pricelist_template*` — ten entities, three module-local enums) and remains accurate. Business-rules, user-flow, and test-scenarios were substantially rewritten this pass — the previous draft described a 6-phase campaign workflow, quality scoring, a validation engine, Manager/Finance-Manager approval thresholds, portal-token IP/session policy, token revocation, and automatic activity-log writes, none of which have matching code; Finance and Audit/Config are documented as correction pages, matching the pattern already established for other inventory modules with fabricated persona axes. **E2E coverage exists** — `150-vendor.spec.ts`, `159-pl.spec.ts`, and `160-pl-template.spec.ts` in `../carmen-inventory-frontend-e2e/tests/` (the previous claim of "no dedicated spec" was wrong); no dedicated spec exists yet for Request for Pricing.
