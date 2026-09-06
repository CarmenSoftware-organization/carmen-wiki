---
title: Licenses
description: License centre — the per-cluster BU-quota ledger, the per-BU seat ledger, and subscriptions with feature-group entitlements, plus expiry thresholds and legacy /subscriptions redirects.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, licenses
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Licenses

The **Licenses** module is the platform's commercial ledger for what a cluster and its business units have actually bought: how many **business units** a cluster's contract entitles it to create (BU-quota), how many **user seats** each business unit's contract entitles it to fill, and the **subscription** contract itself — a per-BU record of a cluster's commercial relationship, carrying the feature groups that contract entitles the BU to use. Three purchase types, three ledgers, one module. `src/pages/licenses/` was the single most-changed directory in the SPA over this plan's drift window (228 commits) — nearly every screen described here was rebuilt at least once since the module's last documented baseline.

> **At a Glance**
> **Module purpose:** Purchase ledgers for cluster BU-quota (`tb_cluster_license`) and BU seats (`tb_business_unit_license`), plus subscription contracts (`tb_subscription`) carrying feature-group entitlements &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA's commercial/licensing surface &nbsp;·&nbsp; **Routes:** `/licenses` (`LicenseCenter`), `/licenses/:clusterId` (`ClusterLicenseDetail`), `/licenses/subscriptions/{new,:id/edit}` (`SubscriptionForm`), `/licenses/seats/{new,:id/edit}` and `/licenses/bu-quota/{new,:id/edit}` (both render the **same** `LicensePurchaseForm`, switched by a `config` prop) &nbsp;·&nbsp; **Legacy routes:** `/subscriptions`, `/subscriptions/new`, `/subscriptions/:id/edit` all redirect into `/licenses/...` — old links still work &nbsp;·&nbsp; **Permission key:** `subscription.read` (nav + view) and `subscription.manage` (create/edit/cancel) — **not** `license.manage`, which belongs to a different module (see §3) &nbsp;·&nbsp; **Feature-flag key:** `licenses` (checked on every route, after the permission gate) &nbsp;·&nbsp; **Nav group:** `navGroup.licenseManagement` ("License Management") &nbsp;·&nbsp; **superAdminOnly:** No &nbsp;·&nbsp; **e2e suite:** **None** — `../carmen-platform-e2e/tests/` has no `licenses` directory; every claim in this module's pages is sourced from implementation alone &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The module has four screens behind five distinct components:

- **`/licenses` → `LicenseCenter`** — the landing screen. A Fleet Capacity band (`FleetCapacity`, shared with the [Clusters](/en/platform/clusters) module, reading the same unfiltered `GET /api-system/clusters/summary`) sits above a `TabStrip` of four views over the same underlying data: **By cluster** (`ClusterLicenseTable` — one row per cluster, BU-quota and seat capacity meters, quota-expiry warning), **By subscription** (`SubscriptionTable`, rendered `embedded`), **By seat license** (`PurchaseLicenseTable` configured for seats), and **By BU quota** (the same `PurchaseLicenseTable` configured for BU-quota). The active view is written to both `?tab=` and `localStorage` (`license_center_view`) with `?tab=` taking precedence on load, so a shared link always opens on the sender's intended view regardless of the recipient's last-used tab.
- **`/licenses/:clusterId` → `ClusterLicenseDetail`** — a single cluster's licensing detail: a `LicenseHealthStrip` summarising all three ledgers at once (quota cap/used/days-left, seat total, subscription count/expired/expiring-soon), then a `TabStrip` of three sections that share one set of loaded data owned by the page itself (not fetched per-section, so the header strip and the tabs can never disagree): **Quota** (`BuQuotaSection`), **Seats** (`SeatSection`), **Subscriptions** (`SubscriptionSection`). Tabs read/write `?tab=` and additionally accept the legacy hash forms `#seats`/`#subscriptions` that the "Manage licences" links on the [Business Units](/en/platform/business-units) and [Clusters](/en/platform/clusters) edit pages still point at.
- **`/licenses/subscriptions/new`, `/licenses/subscriptions/:id/edit` → `SubscriptionForm`** — create/edit a subscription contract. See §3.2 and [UI Screens](/en/platform/licenses/ui-screens) §3.
- **`/licenses/seats/{new,:id/edit}` and `/licenses/bu-quota/{new,:id/edit}` → `LicensePurchaseForm`** — the **same component** serves both purchase types, switched entirely by a `config: LicenseKindConfig` prop (`SEAT_CONFIG` or `BU_QUOTA_CONFIG`, `src/pages/licenses/licenseKindConfig.ts`). See §3.1 for what differs between the two modes.

Both purchase-form routes' `:id/edit` variants are guarded by `subscription.read`, not `subscription.manage` — the same is true of `SubscriptionForm`'s edit route. See §4 for why that is not a gating gap.

## 2. Business Context

Carmen sells hospitality customers a cluster of business units, and that commercial relationship has three independently-purchasable dimensions:

1. **How many business units a cluster may create** — a cluster-level quota, purchased as a `tb_cluster_license` row and consumed by [Clusters](/en/platform/clusters)' create/edit screens.
2. **How many user seats a business unit may fill** — a per-BU quota, purchased as a `tb_business_unit_license` row and consumed by [Business Units](/en/platform/business-units)' Users tab.
3. **What software features a business unit's contract entitles it to use** — carried by a `tb_subscription` row (one BU per subscription since the `20260821130000_subscription_one_bu` migration) and its selected feature groups, defined in the [License Catalog](/en/platform/license-catalog) module and consumed at runtime by both `carmen-platform` and `carmen-inventory-frontend-react`.

This module is where all three purchases are recorded, browsed, and (for quota/seats) cancelled. It does not decide what a feature group *contains* — that catalog is owned and edited by [License Catalog](/en/platform/license-catalog); this module only lets a subscription pick from it.

## 3. Key Concepts

### 3.1 One form, two purchase kinds

`LicensePurchaseForm` is the single edit surface for both `tb_cluster_license` (BU-quota) and `tb_business_unit_license` (seats) rows. Everything that differs lives in `LicenseKindConfig` (`licenseKindConfig.ts`), never in an `if (kind === ...)` scattered through the form:

| Aspect | Seats (`SEAT_CONFIG`) | BU quota (`BU_QUOTA_CONFIG`) |
|---|---|---|
| Owner | A business unit (`ownerParam: 'bu'`) | A cluster (`ownerParam: 'cluster'`) |
| Amount field on the wire | `licensed_users` | `licensed_bus` |
| "No expiry" toggle | **Not offered** (`showNoExpiry: false`) | Offered — writes the sentinel `2099-12-31T23:59:59.999Z` |
| Note field | Not shown | Shown (free text — e.g. "migrated from `tb_cluster.max_license_bu` (old value: 2)") |
| Cluster shown as a separate read-only field | Yes — a seat's owning BU belongs to a cluster the form states explicitly | No — the owner **is** the cluster already |
| Counting rule | **Sum** of every active row (`sumActiveLicenses`) | **Single winning row** (`activeLicense` — newest `start_date` wins, not a sum) |
| "How much has the owner used" reader | None (`readUsage: null`) — a seat's divisor is the BU's user count, a different formula entirely | `clusterService.getById(clusterId).bu_used` |
| Cancel action | **Not available** (`cancel: null`) — no cancel endpoint exists for seats; a seat row can only be edited or hard-deleted | Available (`clusterLicenseService.cancel`) — the licence stays in the ledger but stops granting quota, irreversibly |
| Licence-number prefix | `SEAT-YYMM-####` | `BUQ-YYMM-####` |
| Edit-path segment | `seats` | `bu-quota` |
| Expiry-threshold field read | `thresholds.seat_days` | `thresholds.bu_quota_days` |

The counting-rule row is deliberate, not an oversight: seats are additive because a BU can hold several concurrent seat purchases that all count; BU quota is winner-take-all because the intended case is "buy a new, larger quota mid-contract" — the newer licence must fully replace the older one's cap the moment it starts, not add to it. The two formulas live in separate files (`utils/buLicense.ts` vs `utils/clusterLicense.ts`) specifically so nobody is tempted to reuse one for the other.

### 3.2 Subscriptions carry feature-group entitlements, not individual features

A `tb_subscription` row (one per cluster+BU pair, contract dates, `status`) exists to attach **feature-group** entitlements (`tb_subscription_bu_group`, joined through `tb_subscription_bu`) to a business unit — replaced wholesale on every save (`PUT .../groups`, full desired set, not a diff). `SubscriptionForm`'s "Purchased Groups" card (`GroupSelectionCard`) lets an editor pick from the groups [License Catalog](/en/platform/license-catalog) defines and expand each to see, read-only, what features it grants — there is no per-feature checkbox on this screen any more (that UI, `FeatureSelectionCard`, exists only inside License Catalog's own group-editing screen). A subscription still surfaces `feature_keys` (the flattened set the backend actually computed for the BU) alongside its `group_ids`, so a contract migrated before the group system existed — one with features but no group — is visibly flagged rather than silently misrepresented.

### 3.3 Legacy `/subscriptions*` routes still work

`/subscriptions` and `/subscriptions/new` render a bare `<Navigate>` to `/licenses` and `/licenses/subscriptions/new` respectively; `/subscriptions/:id/edit` renders `SubscriptionEditRedirect`, which reads the `:id` param and redirects to `/licenses/subscriptions/:id/edit` with the same id — an old bookmark to a specific contract still opens that exact contract. **`/licenses/subscriptions/...` is canonical**; the legacy paths exist only so nothing that already links to `/subscriptions*` breaks. One nuance worth a tester's attention: `/subscriptions` (the bare list) lands on License Center's **default "By cluster" tab**, not the "By subscription" tab — the two are one click apart, but a bookmark to the old subscription list does not reopen an equivalent view by default.

### 3.4 Expiry thresholds are configurable, not hardcoded

Every "expiring soon" badge on every screen in this module reads one of three independently-configurable day counts — `subscription_days`, `bu_quota_days`, `seat_days` — from `useExpiryThresholds()`, not a hardcoded 30. See [Data Model](/en/platform/licenses/data-model) §6 for the values, source, and per-ledger effect; the thresholds themselves are edited on the [Platform Config](/en/platform/platform-config) screen, not here.

### 3.5 Nav and feature gating

The "Licenses" sidebar entry (`platformNav.ts:20`) carries `permission: 'subscription.read'`, `groupKey: 'navGroup.licenseManagement'`, `feature: 'licenses'`, and **no** `superAdminOnly`. All five routes in §1 carry `feature="licenses"` on `PrivateRoute`, checked **after** the permission gate (permission failure always renders `<Forbidden>`; a passing permission with the flag set to `hide`/`inactive` instead renders `NotFound`/`ComingSoon` — see [Permissions](/en/platform/licenses/permissions) §2).

## 4. Roles and Personas

Access is permission-gated through [Platform RBAC](/en/platform/rbac). The module's one distinctive shape: **`:id/edit` routes require only `subscription.read`, while `new` routes and every mutation require `subscription.manage`.** This is not a gap — `SubscriptionForm` and `LicensePurchaseForm` both compute `canEdit = hasPermission('subscription.manage')` internally and render every field read-only, and every Save/Create/Cancel-licence button wrapped in `<Can permission="subscription.manage">`, when that key is absent. A `subscription.read`-only session can therefore open `/licenses/subscriptions/:id/edit` and see the contract, but the page shows no editable input and no Save button. The backend enforces the same asymmetry independently: `PlatformClusterLicensesController`/`PlatformBusinessUnitLicensesController`/the subscriptions controller all require `subscription.manage` on every `POST`/`PATCH`/`PUT`/`DELETE`/`cancel` route (proven in [Permissions](/en/platform/licenses/permissions) §2), while `GET` routes carry no `@RequirePlatformPermission` at all — read access to a cluster's own licences is authorized inside `micro-cluster` by cluster-scope, the same mechanism `GET /api-system/clusters/:id` uses, so a membership-only cluster admin viewing their own cluster is never 403'd by an RBAC key they were never issued.

A second, entirely separate persona reads a subset of this data with no permission key at all: **cluster admins** (`tb_cluster_user.role = 'admin'` membership, not an RBAC grant) see `/cluster-admin/:clusterId/licenses` → `ClusterAdminLicenses` — a read-only capacity view built from the same hooks and services this module uses (`useLicenseLedger`, `useClusterSeatLicenses`, `clusterLicenseService`), but answering "is this enough?" rather than "issue a new licence." That screen never even calls `GET /platform/subscriptions`, because every write endpoint 403s a cluster admin outright (no RBAC permission exists in their session at all) and the page has nothing useful to do with subscription data it cannot act on. It is a distinct module in this wiki (`cluster-admin`), documented separately — see [Related Modules](#5-related-modules).

The full gate matrix, the read/manage split proven against both frontend and backend source, and the module's edge cases are in [Permissions](/en/platform/licenses/permissions).

## 5. Related Modules

- [Clusters](/en/platform/clusters) — owns the BU-quota *consumer* side: `ClusterEdit`'s Licensing tab reads the same `tb_cluster_license` ledger this module writes, and the Fleet Capacity band on both `/clusters` and `/licenses` reads the same `GET /api-system/clusters/summary` endpoint.
- [Business Units](/en/platform/business-units) — owns the seat *consumer* side: `BusinessUnitEdit`'s Licenses tab (`BusinessUnitLicensesCard`) is a read-only summary of a BU's seat pool with "Manage licences" and "New subscription" links into this module; it neither fetches nor mutates seat data itself, to avoid a second source of truth.
- [License Catalog](/en/platform/license-catalog) — owns the feature/feature-group *catalog* this module's subscriptions select from (§3.2). This module has no create/edit surface for catalog entries.
- [cluster-admin](/en/platform/cluster-admin) — the membership-scoped, read-only "is this enough?" view of the same three ledgers, with no permission gate and no write path (§4).
- [Platform Config](/en/platform/platform-config) — owns the expiry-threshold values this module's "expiring soon" badges read (§3.4).

## 6. Reference Sources

All source paths below are `../carmen-platform` (the Platform admin SPA) unless prefixed `../carmen-turborepo-backend-v2` (the backend monorepo).

- `../carmen-platform/src/App.tsx` (lines 183–249) — the five `/licenses*` route guards plus the three legacy `/subscriptions*` redirects and `SubscriptionEditRedirect`.
- `../carmen-platform/src/components/nav/platformNav.ts` (line 20) — the "Licenses" sidebar entry: `permission: 'subscription.read'`, `groupKey: 'navGroup.licenseManagement'`, `feature: 'licenses'`.
- `../carmen-platform/src/pages/licenses/LicenseCenter.tsx` — the four-tab landing screen and the Fleet Capacity band.
- `../carmen-platform/src/pages/licenses/ClusterLicenseDetail.tsx` — the per-cluster three-tab detail screen and `LicenseHealthStrip`.
- `../carmen-platform/src/pages/licenses/SubscriptionForm.tsx` — the subscription create/edit form.
- `../carmen-platform/src/pages/licenses/LicensePurchaseForm.tsx` — the shared seat/BU-quota purchase form.
- `../carmen-platform/src/pages/licenses/licenseKindConfig.ts` — `SEAT_CONFIG`/`BU_QUOTA_CONFIG`, the single file that encodes every difference between the two purchase kinds (§3.1).
- `../carmen-platform/src/pages/licenses/sections/{BuQuotaSection,SeatSection,SubscriptionSection}.tsx` — the three tabs of `ClusterLicenseDetail`.
- `../carmen-platform/src/pages/clusterAdmin/ClusterAdminLicenses.tsx` — the cluster-admin read-only counterpart (§4).
- `../carmen-platform/src/services/{clusterLicenseService,businessUnitLicenseService,subscriptionService,expiryThresholdService}.ts` — REST clients.
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx` — `useExpiryThresholds()`, `DEFAULT_EXPIRY_THRESHOLDS`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_cluster_license` (line 1168), `tb_business_unit_license` (line 1133), `tb_subscription` (line 452).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql` and `20260901020000_cluster_license_cancel/migration.sql` — `v_cluster_bu_cap`/`v_cluster_bu_quota` (see [Data Model](/en/platform/licenses/data-model) §3).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/{platform_cluster-licenses,platform_business-unit-licenses,platform_subscriptions}/*.controller.ts` — permission enforcement (see [Permissions](/en/platform/licenses/permissions) §2).

## 7. Pages in This Module

- [Data Model](/en/platform/licenses/data-model) — `tb_cluster_license`, `tb_business_unit_license`, `tb_subscription` and its group join tables; the `v_cluster_bu_cap`/`v_cluster_bu_quota`/`v_business_unit_seat` views; and the expiry-threshold values and their per-ledger effect.
- [UI Screens](/en/platform/licenses/ui-screens) — `LicenseCenter`'s four tabs, `ClusterLicenseDetail`'s three sections, both purchase/subscription forms, and the legacy-redirect behaviour.
- [Permissions](/en/platform/licenses/permissions) — the gate matrix, the read-vs-manage split proven against both frontend and backend source, and edge cases for testers.
