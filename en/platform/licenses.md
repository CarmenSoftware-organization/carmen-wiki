---
title: Licenses
description: License centre — the per-cluster BU-quota ledger, the per-BU seat ledger, the per-BU interface (INF) licence ledger, and subscriptions with feature-group entitlements, plus expiry thresholds and legacy /subscriptions redirects.
published: true
date: 2026-09-23T10:06:26.000Z
tags: book/platform, licenses
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Licenses

The **Licenses** module is the platform's commercial ledger for what a cluster and its business units have actually bought: how many **business units** a cluster's contract entitles it to create (BU-quota), how many **user seats** each business unit's contract entitles it to fill, which **third-party interfaces** (POS / PMS / accounting brands) a business unit may switch on (interface licences, `INF`), and the **subscription** contract itself — a per-BU record of a cluster's commercial relationship, carrying the feature groups that contract entitles the BU to use. Four purchase types, four ledgers, one module. `src/pages/licenses/` was the single most-changed directory in the SPA over the previous sync's drift window (228 commits), and the 2026-09-09 interface-licence split (`../carmen-platform` PRs #286–#291, `docs/superpowers/specs/2026-09-09-interface-license-split-design.md`) added the fourth ledger on top of that — every screen described here has been touched again since the 2026-09-06 baseline.

> **At a Glance**
> **Module purpose:** Purchase ledgers for cluster BU-quota (`tb_cluster_license`), BU seats (`tb_business_unit_license`) and BU interface licences (`tb_business_unit_interface_license`, since 2026-09-10), plus subscription contracts (`tb_subscription`) carrying feature-group entitlements &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA's commercial/licensing surface &nbsp;·&nbsp; **Routes:** `/licenses` (`LicenseCenter`), `/licenses/:clusterId` (`ClusterLicenseDetail`), `/licenses/subscriptions/{new,:id/edit}` (`SubscriptionForm`), `/licenses/seats/{new,:id/edit}`, `/licenses/bu-quota/{new,:id/edit}` and `/licenses/interface/{new,:id/edit}` (all three render the **same** `LicensePurchaseForm`, switched by a `config` prop) &nbsp;·&nbsp; **Legacy routes:** `/subscriptions`, `/subscriptions/new`, `/subscriptions/:id/edit` all redirect into `/licenses/...` — old links still work &nbsp;·&nbsp; **Permission key:** `subscription.read` (nav + view) and `subscription.manage` (create/edit/cancel) — **not** `license.manage`, which belongs to a different module (see §3) &nbsp;·&nbsp; **Feature-flag key:** `licenses` (checked on every route, after the permission gate) &nbsp;·&nbsp; **Nav group:** `navGroup.licenseManagement` ("License Management") &nbsp;·&nbsp; **superAdminOnly:** No &nbsp;·&nbsp; **e2e suite:** **None** — `../carmen-platform-e2e/tests/` has no `licenses` directory; every claim in this module's pages is sourced from implementation alone &nbsp;·&nbsp; **Sub-pages:** 3

![Licenses screen](/screenshots/platform/licenses/index.png)

## 1. Overview

The module has four screens behind five distinct components:

- **`/licenses` → `LicenseCenter`** — the landing screen. A Fleet Capacity band (`FleetCapacity`, shared with the [Clusters](/en/platform/clusters) module, reading the same unfiltered `GET /api-system/clusters/summary`) sits above a `TabStrip` of five views over the same underlying data: **By cluster** (`ClusterLicenseTable` — one row per cluster, BU-quota and seat capacity meters, quota-expiry warning), **By subscription** (`SubscriptionTable`, rendered `embedded`), **By seat license** (`PurchaseLicenseTable` configured for seats), **By BU quota** (the same `PurchaseLicenseTable` configured for BU-quota), and — since PR #287 — **By interface license** (the same `PurchaseLicenseTable` configured for `INTERFACE_CONFIG`, where the amount column becomes a feature-group column). The active view is written to both `?tab=` and `localStorage` (`license_center_view`) with `?tab=` taking precedence on load, so a shared link always opens on the sender's intended view regardless of the recipient's last-used tab. Every column on every `/licenses` table has been sortable by header click since PR #290, including the client-derived Status column, which the backend now sorts server-side through its own `status` key (§3.6).
- **`/licenses/:clusterId` → `ClusterLicenseDetail`** — a single cluster's licensing detail: a `LicenseHealthStrip` summarising all three ledgers at once (quota cap/used/days-left, seat total, subscription count/expired/expiring-soon), then a `TabStrip` of three sections that share one set of loaded data owned by the page itself (not fetched per-section, so the header strip and the tabs can never disagree): **Quota** (`BuQuotaSection`), **Seats** (`SeatSection`), **Subscriptions** (`SubscriptionSection`). Tabs read/write `?tab=` and additionally accept the legacy hash forms `#seats`/`#subscriptions` that the "Manage licences" links on the [Business Units](/en/platform/business-units) and [Clusters](/en/platform/clusters) edit pages still point at.
- **`/licenses/subscriptions/new`, `/licenses/subscriptions/:id/edit` → `SubscriptionForm`** — create/edit a subscription contract. See §3.2 and [UI Screens](/en/platform/licenses/ui-screens) §3.
- **`/licenses/seats/{new,:id/edit}`, `/licenses/bu-quota/{new,:id/edit}` and `/licenses/interface/{new,:id/edit}` → `LicensePurchaseForm`** — the **same component** serves all three purchase types, switched entirely by a `config: LicenseKindConfig` prop (`SEAT_CONFIG`, `BU_QUOTA_CONFIG` or `INTERFACE_CONFIG`, `src/pages/licenses/licenseKindConfig.ts`). See §3.1 for what differs between the three modes.

All three purchase-form routes' `:id/edit` variants are guarded by `subscription.read`, not `subscription.manage` — the same is true of `SubscriptionForm`'s edit route. See §4 for why that is not a gating gap.

## 2. Business Context

Carmen sells hospitality customers a cluster of business units, and that commercial relationship has four independently-purchasable dimensions:

1. **How many business units a cluster may create** — a cluster-level quota, purchased as a `tb_cluster_license` row and consumed by [Clusters](/en/platform/clusters)' create/edit screens.
2. **How many user seats a business unit may fill** — a per-BU quota, purchased as a `tb_business_unit_license` row and consumed by [Business Units](/en/platform/business-units)' Users tab.
3. **What software features a business unit's contract entitles it to use** — carried by a `tb_subscription` row (one BU per subscription since the `20260821130000_subscription_one_bu` migration) and its selected `standard`-kind feature groups, defined in the [License Catalog](/en/platform/license-catalog) module and consumed at runtime by both `carmen-platform` and `carmen-inventory-frontend-react`.
4. **Which third-party interfaces a business unit may switch on** — POS (Micros, Infrasys, Square), PMS (Opera, Protel) and accounting (Carmen GL, BlueLedgers, external) brands, sold since 2026-09-10 as a separate **interface licence** (`tb_business_unit_interface_license`, number prefix `INF`) that carries exactly one `interface`-kind feature group and its own start/end dates. Before that (2026-09-08 to 2026-09-10) the same `interface.*` keys were sold as ordinary groups on the main subscription; before 2026-09-08 they were not licence features at all but a flat `tb_business_unit_interface` entitlement table edited from a card on the [Business Units](/en/platform/business-units) edit page — both the table and the card are gone (§3.6).

This module is where all four purchases are recorded, browsed, and (for BU quota) cancelled. It does not decide what a feature group *contains* — that catalog is owned and edited by [License Catalog](/en/platform/license-catalog); this module only lets a subscription or an interface licence pick from it.

## 3. Key Concepts

### 3.1 One form, three purchase kinds

`LicensePurchaseForm` is the single edit surface for `tb_cluster_license` (BU-quota), `tb_business_unit_license` (seats) and `tb_business_unit_interface_license` (interface) rows. Everything that differs lives in `LicenseKindConfig` (`licenseKindConfig.ts`), never in an `if (kind === ...)` scattered through the form — the interface split added one more switch to that config, `selector: 'amount' | 'feature-group'`, precisely so the form could swap a number input for a group picker without learning the word "interface":

| Aspect | Seats (`SEAT_CONFIG`) | BU quota (`BU_QUOTA_CONFIG`) | Interface (`INTERFACE_CONFIG`, PR #287) |
|---|---|---|---|
| Owner | A business unit (`ownerParam: 'bu'`) | A cluster (`ownerParam: 'cluster'`) | A business unit (`ownerParam: 'bu'`) |
| Main value (`selector`) | A number (`'amount'`) | A number (`'amount'`) | **A feature group** (`'feature-group'`) — one `kind = 'interface'` group per licence, picked from a `<Select>` on create only |
| Main field on the wire | `licensed_users` | `licensed_bus` | `license_feature_group_id` |
| "No expiry" toggle | **Not offered** (`showNoExpiry: false`) | Offered — writes the sentinel `2099-12-31T23:59:59.999Z` | **Offered** (`showNoExpiry: true`) — the design spec §3.2 had ruled it out ("an immortal INF licence is a lie on screen"), but the owner reversed that on 2026-09-09 (PR #291); the config's own comment records the reversal and why it is still safe: `in_force` is capped by the main contract regardless of the INF licence's own dates |
| Note field | Not shown | Shown | Shown |
| Cluster shown as a separate read-only field | Yes | No — the owner **is** the cluster already | Yes |
| Counting rule | **Sum** of every active row (`sumActiveLicenses`) | **Single winning row** (`activeLicense` — newest `start_date` wins, not a sum) | **Union of coverage windows** — the entitlement is on if *any* INF licence for that group covers `now` **and** the BU's main contract is `active` (§3.6). A third formula, deliberately distinct from the other two |
| "How much has the owner used" reader | None (`readUsage: null`) | `clusterService.getById(clusterId).bu_used` | None (`readUsage: null`) — there is no divisor for an interface |
| Cancel action | **Not available** (`cancel: null`) | Available (`clusterLicenseService.cancel`) — irreversible | **Not available** (`cancel: null`) — edit the dates or hard-delete, as for seats |
| Licence-number prefix | `SEAT-YYMM-####` | `BUQ-YYMM-####` | `INF-YYMM-####` (same `nextLicenseNumber()` counter family — counts soft-deleted rows too, a number once issued is never reused) |
| Edit-path segment | `seats` | `bu-quota` | `interface` |
| List path after create | `/licenses` | `/licenses` | `/licenses?tab=interface` |
| Expiry-threshold field read | `thresholds.seat_days` | `thresholds.bu_quota_days` | `thresholds.interface_days` (new key, default 30 — [Platform Config](/en/platform/platform-config)) |
| Owner sort key on the fleet table | `tb_business_unit.name` | `tb_cluster.name` | `tb_business_unit.name` |

The counting-rule row is deliberate, not an oversight: seats are additive because a BU can hold several concurrent seat purchases that all count; BU quota is winner-take-all because the intended case is "buy a new, larger quota mid-contract" — the newer licence must fully replace the older one's cap the moment it starts, not add to it; an interface licence is a coverage-window union because renewing one means issuing a new row while the old one stays as history, and the question is only "is there *any* live row." The formulas live in separate places (`utils/buLicense.ts`, `utils/clusterLicense.ts`, and — for interface — the backend only, see §3.6) specifically so nobody is tempted to reuse one for the other.

### 3.2 Subscriptions carry feature-group entitlements, not individual features

A `tb_subscription` row (one per cluster+BU pair, contract dates, `status`) exists to attach **feature-group** entitlements (`tb_subscription_bu_group`, joined through `tb_subscription_bu`) to a business unit — replaced wholesale on every save (`PUT .../groups`, full desired set, not a diff). `SubscriptionForm`'s "Purchased Groups" card (`GroupSelectionCard`) lets an editor pick from the groups [License Catalog](/en/platform/license-catalog) defines and expand each to see, read-only, what features it grants — there is no per-feature checkbox on this screen any more (that UI, `FeatureSelectionCard`, exists only inside License Catalog's own group-editing screen). A subscription still surfaces `feature_keys` (the flattened set the backend actually computed for the BU) alongside its `group_ids`, so a contract migrated before the group system existed — one with features but no group — is visibly flagged rather than silently misrepresented.

### 3.3 Legacy `/subscriptions*` routes still work

`/subscriptions` and `/subscriptions/new` render a bare `<Navigate>` to `/licenses` and `/licenses/subscriptions/new` respectively; `/subscriptions/:id/edit` renders `SubscriptionEditRedirect`, which reads the `:id` param and redirects to `/licenses/subscriptions/:id/edit` with the same id — an old bookmark to a specific contract still opens that exact contract. **`/licenses/subscriptions/...` is canonical**; the legacy paths exist only so nothing that already links to `/subscriptions*` breaks. One nuance worth a tester's attention: `/subscriptions` (the bare list) lands on License Center's **default "By cluster" tab**, not the "By subscription" tab — the two are one click apart, but a bookmark to the old subscription list does not reopen an equivalent view by default.

### 3.4 Expiry thresholds are configurable, not hardcoded

Every "expiring soon" badge on every screen in this module reads one of four independently-configurable day counts — `subscription_days`, `bu_quota_days`, `seat_days`, and (since PR #287) `interface_days` — from `useExpiryThresholds()`, not a hardcoded 30. See [Data Model](/en/platform/licenses/data-model) §6 for the values, source, and per-ledger effect; the thresholds themselves are edited on the [Platform Config](/en/platform/platform-config) screen, not here.

### 3.5 Nav and feature gating

The "Licenses" sidebar entry (`platformNav.ts:20`) carries `permission: 'subscription.read'`, `groupKey: 'navGroup.licenseManagement'`, `feature: 'licenses'`, and **no** `superAdminOnly`. All ten routes in §1 carry `feature="licenses"` on `PrivateRoute`, checked **after** the permission gate (permission failure always renders `<Forbidden>`; a passing permission with the flag set to `hide`/`inactive` instead renders `NotFound`/`ComingSoon` — see [Permissions](/en/platform/licenses/permissions) §2).

### 3.6 Interface licences: what an INF licence grants, and the two-condition entitlement

Three facts about the fourth ledger that the other three do not prepare a reader for:

1. **A feature group now has a `kind`**, `standard` or `interface` (`enum_license_feature_group_kind`, migration `20260910000000_license_feature_group_kind`), set once at creation and never editable afterward — changing it would move already-sold entitlements between licence kinds with no record of the move. The backend refuses to attach an `interface` group to a subscription and a `standard` group to an INF licence, with a **400, not a silent filter** (`PlatformBusinessUnitInterfaceLicensesService`'s group check; `GroupSelectionCard` on the subscription form hides `interface` groups from its picker for the same reason). The catalog gained a 12-key `interface` module for this — see [License Catalog](/en/platform/license-catalog) §3.2.
2. **The entitlement a BU actually gets is computed in exactly one place — the backend — and the SPA must never recompute it.** `license.service.ts` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/license/`) builds `GET /api/license`'s `features[]` as: the `standard` groups on the BU's main contract, **∪** the group of every INF licence covering `now` — **only while the main contract's `state` is `active`**. When the main contract is not active, every INF key (live or not) lands in `expired_features[]` instead, so the inventory app can show "expired" rather than "never bought." An INF licence never sets the BU's `state` or `end_date`; those still come from the main contract alone. The wire row for an INF licence therefore carries three server-computed fields — `state` (`active`/`scheduled`/`expired` from the licence's own dates), `contract_state` (the owning BU's main-contract state), and `in_force = state === 'active' && contract_state === 'active'` — and every badge on every screen in this module and on the BU edit page reads `in_force`, never the dates. The screen that most easily lies here is the BU's own Licenses tab: a licence "still within its dates" but `in_force = false` renders as **"Capped by contract"**, not "Active."
3. **The migration path deliberately destroyed and then rebuilt data on DEV, and the two data migrations are not symmetric.** The 2026-09-08 move from the old entitlement table to licence features dropped `tb_business_unit_interface` in the same commit as the (never-run) backfill script, losing interface entitlement for 13 of 14 DEV business units — `20260908000000_drop_business_unit_interface/migration.sql`'s own header now says it must never be treated as ready to apply without a pre-apply backup. The 2026-09-10 split learned from that: `20260910020000_migrate_interface_groups_to_inf_license` is an idempotent SQL data migration (marker `(sbg <uuid>)` in `note`) that issues one INF licence per interface group hanging off a subscription, copies the subscription's own dates onto it, and only then soft-deletes the `tb_subscription_bu_group` row — guarded by a mandatory `--preflight` / `--snapshot` / apply / `--verify` sequence in `prisma/check.interface-license-migration.ts`. Testers on a fresh environment should expect the three `20260910*` migrations to apply in one `migrate deploy`, and should read that migration's header before trusting the INF rows it produced.

## 4. Roles and Personas

Access is permission-gated through [Platform RBAC](/en/platform/rbac). The module's one distinctive shape: **`:id/edit` routes require only `subscription.read`, while `new` routes and every mutation require `subscription.manage`.** This is not a gap — `SubscriptionForm` and `LicensePurchaseForm` both compute `canEdit = hasPermission('subscription.manage')` internally and render every field read-only, and every Save/Create/Cancel-licence button wrapped in `<Can permission="subscription.manage">`, when that key is absent. A `subscription.read`-only session can therefore open `/licenses/subscriptions/:id/edit` and see the contract, but the page shows no editable input and no Save button. The backend enforces the same asymmetry independently: `PlatformClusterLicensesController`/`PlatformBusinessUnitLicensesController`/the subscriptions controller all require `subscription.manage` on every `POST`/`PATCH`/`PUT`/`DELETE`/`cancel` route (proven in [Permissions](/en/platform/licenses/permissions) §2), while `GET` routes carry no `@RequirePlatformPermission` at all — read access to a cluster's own licences is authorized inside `micro-cluster` by cluster-scope, the same mechanism `GET /api-system/clusters/:id` uses, so a membership-only cluster admin viewing their own cluster is never 403'd by an RBAC key they were never issued.

A second, entirely separate persona reads a subset of this data with no permission key at all: **cluster admins** (`tb_cluster_user.role = 'admin'` membership, not an RBAC grant) see `/cluster-admin/:clusterId/licenses` → `ClusterAdminLicenses` — a read-only capacity view built from the same hooks and services this module uses (`useLicenseLedger`, `useClusterSeatLicenses`, `useClusterInterfaceLicenses`, `clusterLicenseService`), but answering "is this enough?" rather than "issue a new licence." That screen never calls `GET /platform/subscriptions` — since PR #291 it reads the cluster's subscriptions through `GET /api-system/clusters/:id/subscriptions`, which is authorized by cluster membership rather than `subscription.read` — because every write endpoint 403s a cluster admin outright (no RBAC permission exists in their session at all). It is a distinct module in this wiki (`cluster-admin`), documented separately — see [Related Modules](#5-related-modules).

The full gate matrix, the read/manage split proven against both frontend and backend source, and the module's edge cases are in [Permissions](/en/platform/licenses/permissions).

## 5. Related Modules

- [Clusters](/en/platform/clusters) — owns the BU-quota *consumer* side: `ClusterEdit`'s Licensing tab reads the same `tb_cluster_license` ledger this module writes, and the Fleet Capacity band on both `/clusters` and `/licenses` reads the same `GET /api-system/clusters/summary` endpoint.
- [Business Units](/en/platform/business-units) — owns the seat and interface *consumer* side: `BusinessUnitEdit`'s Licenses tab holds two read-only cards (`BusinessUnitLicensesCard` for seats + the BU's subscriptions, `BusinessUnitInterfaceLicensesCard` for INF licences) with "Manage licences", "New subscription" and "Add interface license" links into this module; neither card mutates licence data itself, to avoid a second source of truth.
- [License Catalog](/en/platform/license-catalog) — owns the feature/feature-group *catalog* this module's subscriptions and interface licences select from (§3.2, §3.6), including the group `kind` that decides which of the two may hold a given group. This module has no create/edit surface for catalog entries.
- [cluster-admin](/en/platform/cluster-admin) — the membership-scoped, read-only "is this enough?" view of the same three ledgers, with no permission gate and no write path (§4).
- [Platform Config](/en/platform/platform-config) — owns the expiry-threshold values this module's "expiring soon" badges read (§3.4).

## 6. Reference Sources

All source paths below are `../carmen-platform` (the Platform admin SPA) unless prefixed `../carmen-turborepo-backend-v2` (the backend monorepo).

- `../carmen-platform/src/App.tsx` (lines 183–265) — the ten `/licenses*` route guards (interface routes at 247–262) plus the three legacy `/subscriptions*` redirects and `SubscriptionEditRedirect`.
- `../carmen-platform/src/components/nav/platformNav.ts` (line 20) — the "Licenses" sidebar entry: `permission: 'subscription.read'`, `groupKey: 'navGroup.licenseManagement'`, `feature: 'licenses'`.
- `../carmen-platform/src/pages/licenses/LicenseCenter.tsx` — the five-tab landing screen and the Fleet Capacity band.
- `../carmen-platform/src/pages/licenses/ClusterLicenseDetail.tsx` — the per-cluster three-tab detail screen and `LicenseHealthStrip`.
- `../carmen-platform/src/pages/licenses/SubscriptionForm.tsx` — the subscription create/edit form.
- `../carmen-platform/src/pages/licenses/LicensePurchaseForm.tsx` — the shared seat/BU-quota/interface purchase form.
- `../carmen-platform/src/pages/licenses/licenseKindConfig.ts` — `SEAT_CONFIG`/`BU_QUOTA_CONFIG`/`INTERFACE_CONFIG`, the single file that encodes every difference between the three purchase kinds (§3.1), including the `selector` switch and the `showNoExpiry: true` reversal note on the interface kind.
- `../carmen-platform/src/pages/licenses/useClusterInterfaceLicenses.ts`, `src/services/businessUnitInterfaceLicenseService.ts` — the INF ledger's read hook and REST client.
- `../carmen-platform/docs/superpowers/specs/2026-09-07-interface-entitlement-to-license-design.md`, `2026-09-09-interface-license-split-design.md` — the two design documents behind §3.6 (the second supersedes the first's "sell interfaces on the main subscription" model).
- `../carmen-platform/src/pages/licenses/sections/{BuQuotaSection,SeatSection,SubscriptionSection}.tsx` — the three tabs of `ClusterLicenseDetail`.
- `../carmen-platform/src/pages/clusterAdmin/ClusterAdminLicenses.tsx` — the cluster-admin read-only counterpart (§4).
- `../carmen-platform/src/services/{clusterLicenseService,businessUnitLicenseService,subscriptionService,expiryThresholdService}.ts` — REST clients.
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx` — `useExpiryThresholds()`, `DEFAULT_EXPIRY_THRESHOLDS`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_cluster_license` (line 1168), `tb_business_unit_license` (line 1133), `tb_business_unit_interface_license` (line 1149), `tb_license_feature_group.kind` (line 1308), `enum_license_feature_group_kind` (line 747), `tb_subscription` (line 452).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260910000000_license_feature_group_kind`, `20260910010000_business_unit_interface_license`, `20260910020000_migrate_interface_groups_to_inf_license`, and `20260908000000_drop_business_unit_interface` — the interface-licence schema and data migrations (§3.6).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/license/license.service.ts`, `license.types.ts` — where `features[]`/`expired_features[]` are built from the main contract ∪ live INF licences (§3.6).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql` and `20260901020000_cluster_license_cancel/migration.sql` — `v_cluster_bu_cap`/`v_cluster_bu_quota` (see [Data Model](/en/platform/licenses/data-model) §3).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/{platform_cluster-licenses,platform_business-unit-licenses,platform_business-unit-interface-licenses,platform_subscriptions}/*.controller.ts` — permission enforcement (see [Permissions](/en/platform/licenses/permissions) §2).

## 7. Pages in This Module

- [Data Model](/en/platform/licenses/data-model) — `tb_cluster_license`, `tb_business_unit_license`, `tb_business_unit_interface_license`, `tb_subscription` and its group join tables; the `v_cluster_bu_cap`/`v_cluster_bu_quota`/`v_business_unit_seat` views; the group `kind` enum; and the expiry-threshold values and their per-ledger effect.
- [UI Screens](/en/platform/licenses/ui-screens) — `LicenseCenter`'s five tabs, `ClusterLicenseDetail`'s three sections, the subscription form and the three-kind purchase form, and the legacy-redirect behaviour.
- [Permissions](/en/platform/licenses/permissions) — the gate matrix, the read-vs-manage split proven against both frontend and backend source, and edge cases for testers.
