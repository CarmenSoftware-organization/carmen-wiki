---
title: Vendor Pricelist — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for vendor-pricelist.
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Test Scenarios

> **At a Glance**
> **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist) &nbsp;·&nbsp; **Personas covered:** Purchaser, Vendor (external portal — save/submit work since 2026-08/09)
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**
> **Executable coverage (2026-09-22):** `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts` (31 cases, 2 fixme) + `docs/test-cases/gaps/150-vendor-gap.md` (54), `tests/159-pl.spec.ts` (28, 4 fixme) + `gaps/159-pl-gap.md` (65), `tests/160-pl-template.spec.ts` (33) + `gaps/160-pl-template-gap.md` (58), `tests/043-certification.spec.ts` (6) + `gaps/043-certification-gap.md` (29); vendor portal: documentation-only catalog `docs/test-cases/1002-external-price-list.md` (42, no spec); Request for Pricing: no spec. This page does not mirror those cases.

## 1. Overview

This page is the overview entry point for the test-scenario set of the `vendor-pricelist` module. The previous version of this page described four personas (Purchaser, Vendor, Finance, Audit/Config) and ~12 cross-persona handoff scenarios built around a quality-scored, threshold-gated, multi-status campaign workflow. Re-verifying against the real frontend/backend (2026-07-16, re-checked 2026-09-22) found that workflow does not exist — this module is five plain CRUD screens (Vendor, Certification, Price List, Price List Template, Request for Pricing) plus an external vendor portal that, since 2026-08/09, really saves and submits (the Save/Submit gap reported on 2026-07-16 is closed). Test coverage below is re-anchored to that reality.

Scope of testing on the vendor-pricelist module: **functional coverage** of create/edit/delete on all five screens plus the template's dedicated status-flip endpoint; **the vendor portal round-trip** (open → save → submit → `submitted`, and expiry at `end_date`); **the RFQ send-email action**; **validation** of the checks that are actually implemented (see [02-business-rules](/en/inventory/vendor-pricelist/02-business-rules) § 2 for which rule IDs are confirmed vs. design-target); and **the `price-compare` mechanism** that downstream PR/PO pricing consumes.

## 2. Personas in Scope

- **Purchaser** — Owns all four CRUD screens end-to-end: Vendor, Price List, Price List Template, Request for Pricing. No Manager-elevation tier exists (there is nothing for one to gate). See [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md).
- **Vendor** — External party; token-authenticated portal (open, tax-profile/unit pickers, save, Excel import, submit; 401 after the RFQ `end_date`). Permission section reduced to a single N/A row (no Carmen login). See [04-test-scenarios-vendor.md](./04-test-scenarios-vendor.md).

Finance and Audit/Config are documented as correction pages ([04-test-scenarios-finance.md](./04-test-scenarios-finance.md), [04-test-scenarios-audit-config.md](./04-test-scenarios-audit-config.md)) — neither is a distinct persona in this module.

## 3. Persona Test Files

- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Vendor scenarios](./04-test-scenarios-vendor.md) — Permission section reduced to one N/A row.
- [Finance scenarios](./04-test-scenarios-finance.md) — correction page.
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md) — correction page.

## 4. Cross-Persona Scenarios

| # | Scenario | Personas in order | Confirmed? |
| - | -------- | ----------------- | ---------- |
| X-VPL-01 | Direct pricelist entry (no RFQ) — Purchaser creates a Price List for a vendor, adds detail rows, sets `status = active` | Purchaser only | **Confirmed** — plain CRUD; the more common path in practice given the portal gap below. |
| X-VPL-02 | RFQ → Send email → vendor opens portal → draft auto-created → vendor prices, saves, submits → Purchaser activates the `submitted` pricelist | Purchaser → Vendor → Purchaser | **Confirmed (2026-09-22)** — `submit()` sets `submitted` + `submitted_at`, prunes unpriced rows; the RFQ vendor row shows `has_submitted` and the pricelist status; the Purchaser sets `active` on the Price List screen. |
| X-VPL-03 | Vendor opens / saves / submits after the RFQ `end_date` | Vendor | **Confirmed rejection** — `UrlTokenGuard` returns 401 `url_token has expired`; the portal shows the expired screen. |
| X-VPL-05 | Purchaser sets a pricelist `draft → submitted` on the internal form with some zero-priced rows | Purchaser | **Confirmed** — `PriceListService.update()` stamps `submitted_at` and deletes the zero-priced rows after applying the request's own add/update/remove. |
| X-VPL-04 | Preferred-row pick feeds `price-compare` for downstream PR/PO pricing | Purchaser → (downstream PR/PO, out of scope here) | **Confirmed** — real endpoint, real per-row flag. |

Scenarios describing a Manager-only high-value approval, a Finance Manager co-signoff, a Sysadmin token revocation, an auto-expiry cron, campaign pause/cancel, or a quality-score gate have been removed — none of them have matching code (see [02-business-rules](/en/inventory/vendor-pricelist/02-business-rules)).

## 5. E2E Test Mapping

Real Playwright specs exist for four of the five screens (see the coverage note at the top for counts):

- `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts` — full CRUD, tab navigation (address/contact/info), validation (required fields, max-length, duplicate code), and admin-BU coverage for the **Vendor** screen; nothing yet for the certificates section or the backend-only `tax_no` / `branch_no` / `rating`.
- `../carmen-inventory-frontend-e2e/tests/043-certification.spec.ts` — the **Certification** master (dialog CRUD) under `/vendor-management/certification`.
- `../carmen-inventory-frontend-e2e/tests/159-pl.spec.ts` — list/search/filter, create, view detail, edit, and Export for **Price List**. Its Duplicate and "Mark as Expired" sections use loose, best-effort assertions (`.catch(() => {})`, `expect(true).toBe(true)`) and reference actions not found in the real list component (`use-pl-table.tsx`'s row actions are Edit + Delete only, plus a client-side Export button) — treat those two sections as aspirational test-plan scaffolding, not confirmed features.
- `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` — **Price List Template** coverage.
- **No spec exists yet** for Request for Pricing (including Send email) or for the external vendor portal — the portal has the documentation-only catalog `docs/test-cases/1002-external-price-list.md` (42 `TC-EPL-*` cases).

Downstream consumption is exercised indirectly by:

- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts` (TC-PO-060205..TC-PO-060208) — the From-Price-List PO wizard.

## 6. References

- Sibling: [03-user-flow.md](./03-user-flow.md) § 4 (handoff source).
- Sibling: [02-business-rules.md](./02-business-rules.md) — confirmed-vs-design-target status per rule.
- Sibling: [01-data-model.md](./01-data-model.md) — entities, enums, unique constraints.
