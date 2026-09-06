---
title: Business Units — Tenant Migrations
description: The fleet-wide /tenant-migrations screen now has its own top-level module — this page covers only what remains specific to Business Units, the embedded per-BU TenantMigrationCard on the edit page's Technical tab.
published: true
date: '2026-09-06T19:00:00.000Z'
tags: book/platform, business-units, tenant-migrations
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Business Units — Tenant Migrations

> **Moved:** the fleet-wide `/tenant-migrations` screen (`TenantMigrationManagement`, its own route, nav entry, and `tenant_migrations` feature key) is documented in full at **[Tenant Migrations](/en/platform/tenant-migrations)** and its [Data Model](/en/platform/tenant-migrations/data-model) sub-page. This page now covers only the one piece of that screen that is genuinely Business-Units-specific: the embedded per-BU `TenantMigrationCard`.

## 1. The per-BU card

The Business Units edit page's Technical tab embeds `TenantMigrationCard` (existing BUs only), a scaled-down version of the fleet screen scoped to the one BU currently open: it checks that BU's own tenant-database migration status and applies pending migrations via the same streamed-progress mechanism, behind the same confirm dialog. Full screen-tour detail — layout, disabled states, the raw-output toggle — is documented in [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.5, where it lives alongside its two sibling advanced cards (Tenant Seed, Interface Entitlement).

The card and the fleet-wide screen call the exact same `tenantMigrationService` (`getStatus`, `deployStream`) and the same backend controller — there is one implementation of "check status" and "apply migrations," surfaced from two screens. See [Tenant Migrations](/en/platform/tenant-migrations) §3.5 for the full comparison, including a re-verified correction: both surfaces gate **every** action, including the read-only status check, on `isSuperAdmin` — the card is not more permissive here than the fleet table. The one real difference is that the card additionally disables its buttons when the BU has no database pool/schema configured yet (`hasDbConnection`), a pre-check the fleet table does not perform.

There is no in-app link between this card and the fleet-wide screen in either direction; the fleet screen's own "Code" column links back to this BU's edit page, not to a filtered version of itself.

## 2. References

- `../carmen-platform/src/components/TenantMigrationCard.tsx` — the embedded card.
- [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.5 — full screen-tour detail for this card, alongside Tenant Seed and Interface Entitlement.
- [Tenant Migrations](/en/platform/tenant-migrations) — the fleet-wide screen's full account: layout, actions and gating, migration states, known gaps, and data model.
