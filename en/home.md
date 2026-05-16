---
title: Carmen Inventory ERP — Developer & Tester Manual
description: Landing page for the Carmen Inventory ERP wiki — module index for developers and testers across procure-to-pay, inventory control, costing, master configuration, and reporting.
published: true
date: 2026-05-17T11:00:00.000Z
tags: home, index, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-16T14:00:00.000Z
---

# Carmen Inventory ERP — Developer & Tester Manual

> **At a Glance**
> **Audience:** Inventory devs & QA on the Carmen Software platform &nbsp;·&nbsp; **Scope:** procure-to-pay, inventory control, costing, master config, reporting &nbsp;·&nbsp; Module index — start at the section for your area, then drill into `01-data-model` / `02-business-rules` / `03-user-flow` / `04-test-scenarios`.

## 1. About This Wiki

This wiki is the canonical user manual for developers and QA engineers working on the **Carmen Inventory ERP** — the inventory slice of the Carmen Software hospitality supply chain platform. Pages document the platform's data model, business rules, user flows by persona, and test scenarios at a level useful for building inventory features and verifying them against the BRD and live UI. End-user training materials, vendor portal contracts, and platform-architecture documents live elsewhere; this wiki sits one layer below those, between the spec and the code.

Content is organised by module under the top-level locale directories `en/` (canonical) and `th/` (translation tracking). Each module folder follows the same sub-page convention: `01-data-model`, `02-business-rules`, `03-user-flow*`, `04-test-scenarios*`, with role-specific sub-pages under user-flow and test-scenarios when the module has multiple personas. Cross-module references use Wiki.js `[[slug]]` links so the navigation stays internal to the current locale.

## 2. Dashboard

The post-login landing surface — cross-module KPI tiles, aging buckets, and exception lists. Each tile drills into the underlying transactional module with a pre-applied filter.

- [[dashboard]] — Module index for the six dashboard pages (Main, PR, PO, GRN, Inventory, SR).

## 3. Procure-to-Pay

The procurement chain — from internal demand signal through external vendor commitment, physical receipt, and three-way match for AP posting.

- [[purchase-request]] — Internal demand document; multi-stage approval workflow, soft-budget commitment, vendor allocation, PR-to-PO conversion bridge.
- [[purchase-order]] — Vendor-facing commitment document; manual or PR-sourced creation, high-value approval, transmission, amendment under post-`sent` restrictions.
- [[good-receive-note]] — Physical receipt against PO (or standalone for emergency receipts); lot/expiry capture, segregation of duties with PO creator, commit fires inventory and cost-layer writes.
- [[vendor-pricelist]] — Vendor master, pricelist coverage, ranking criteria, tolerance bands that feed PR/PO snapshot semantics and deviation routing.

## 4. Inventory Control

The inventory side — stock balances, lot management, adjustments, and the count-vs-spot-check cadence that gates period-end close.

- [[inventory]] — System of record for stock balances by product × warehouse × location, with current/average unit cost, on-hand / allocated / available quantities, and movement workflow status.
- [[inventory-adjustment]] — Manual stock-in (`tb_stock_in`) and stock-out (`tb_stock_out`) corrections; FIFO new-layer creation vs oldest-layer consumption, AVCO re-average vs cost hold.
- [[physical-count]] — Full-scope period-end count; location lock while `IN PROGRESS`, variance handling, Stage-3 prerequisite for end-period close.
- [[spot-check]] — Narrower-scope cycle count; Stage-2 prerequisite for end-period close, faster cadence than full physical.
- [[store-requisition]] — Internal stock transfer (three variants: DIR, CONS, INV-to-INV); no AVCO re-average, cost flows through at existing layer.
- [[product]] — Product master, SKU catalogue, inventory unit base UoM, costing-method assignment per item.

## 5. Costing & Recipe

How unit cost is computed, recalculated, and consumed by the recipe / menu side.

- [[costing]] — AVCO vs FIFO cost engine; trigger transactions (GRN, stock adjustments, physical count), pass-through for SR, period-lock semantics. AVCO/FIFO is selected at Business Unit setup and cannot change after go-live.
- [[recipe]] — Recipe master, ingredient lines, yield, allergen flags; menu-engineering inputs that consume the cost engine's output.

## 6. Master Configuration

Cross-cutting master data and configuration that every transactional module consumes.

- [[master-data]] — Vendor, currency, tax-profile, unit (UoM), department, location, dimension — the reference data snapshotted onto every transaction document.
- [[system-config]] — Workflow definitions, running-code numbering schemes, dimension setup; the policy surface that drives every approval / posting / numbering decision.
- [[access-control]] — Role / permission map, user-action gates, segregation-of-duties rules; the authorisation backbone referenced by every `*_AUTH_*` rule.
- [[templates]] — Reusable scaffold definitions (PR, Price List) cloned into new transactional records; seed-only, never enter a workflow themselves.

## 7. Reporting & Audit

The off-path observation and governance surface.

- [[reporting-audit]] — Activity logs, attachments, notifications, report catalogue, widgets, and the audit-case file mechanism cited by Auditor and System Administrator personas across every transactional module.

## 8. How to Navigate

Each module's `index.md` is its landing page (Overview, Business Context, Key Concepts, Roles & Personas, Related Modules, Reference Sources, Pages in This Module). From there:

- **Data model** → `01-data-model.md` — Prisma entities, enums, relationships, rounding precision.
- **Business rules** → `02-business-rules.md` — Validation, calculation, authorization, posting, and cross-module rules with stable rule IDs (`<MOD>_VAL_NNN`, `<MOD>_AUTH_NNN`, etc.). Section 5.1 in transactional modules carries the **Status Lifecycle — Live UI vs BRD Mapping** table and discrepancy callouts.
- **User flow** → `03-user-flow.md` (overview with state-machine Mermaid) + per-persona drill-downs `03-user-flow-{role}.md` with workflow-position Mermaid and a Permission Matrix.
- **Test scenarios** → `04-test-scenarios.md` (cross-persona) + per-persona drill-downs with happy-path / permission / validation / edge-case scenarios mapped to rule IDs and E2E spec files.

## 9. Reference Sources

The wiki is synthesised from these external sources (sibling repos in the Carmen Software organisation):

- `../carmen/docs/` — primary concept and design references for every module.
- `../carmen-inventory-frontend/` — Next.js inventory UI, source of truth for screen behaviour.
- `../carmen-turborepo-backend-v2/` — Turborepo monorepo, REST API surface.
- `../micro-report/`, `../micro-cronjobs/` — Go microservices for reporting and scheduled jobs.
- `../carmen-turborepo-backend-bruno/` — Bruno API collections, exact request/response shapes.
- `../carmen-inventory-frontend-e2e/` — Playwright suite; executable spec for behaviour.
- `Test_case/` (held outside this wiki repo) — Screen-level and process-level Test_case files cited by discrepancy callouts; capture state of the live UI at known dates.

When in doubt about what the system actually does, implementation and E2E tests beat `../carmen/docs/`; `../carmen/docs/` beats memory.
