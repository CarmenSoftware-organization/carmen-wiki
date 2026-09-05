---
title: License Catalog
description: One screen, two tabs, two nav rows — the sellable feature catalog (Features) and the curated bundles sold from it (Bundles) — each with its own permission pair and feature flag.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, license-catalog
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# License Catalog

The **License Catalog** module is one screen, `LicenseCatalog`, rendered behind two separate routes and switched by a `tab` prop: `/license-features` (the **Features** tab, `FeatureCatalogPanel`) and `/license-feature-groups` (the **Bundles** tab, `GroupCatalogPanel`). This is a documentation merge, not a product merge — the two tabs kept their own historical nav rows, permission pairs, and feature-flag keys throughout, and this page documents both under one module because they answer one question together: *what does Carmen sell, and how is it packaged?* **Features** is the raw catalog of sellable capabilities, generated from the permission map and editable only for `state` (sellable / not-yet-sellable / hidden). **Bundles** is the admin-curated set of named packages — spanning any features from any part of the catalog — that a subscription actually picks from on the [Licenses](/en/platform/licenses) module's sales screen. A third route, `/license-feature-groups/{new,:id/edit}`, renders a distinct component, `LicenseFeatureGroupEdit`, for creating and editing one bundle.

> **At a Glance**
> **Component:** `LicenseCatalog` (one component, `tab: 'bundles' | 'features'` prop) &nbsp;·&nbsp; **Routes:** `/license-features` → Features tab, `/license-feature-groups` → Bundles tab, `/license-feature-groups/new` and `/license-feature-groups/:id/edit` → `LicenseFeatureGroupEdit` &nbsp;·&nbsp; **Permission keys — two independent pairs:** Features tab `license_feature.read` (nav/read) + `license_feature.manage` (edit `state`); Bundles tab `license_feature_group.read` (nav/read) + `license_feature_group.manage` (create/edit/delete/set-features) &nbsp;·&nbsp; **Feature-flag keys:** `license_features` and `license_feature_groups`, one per tab &nbsp;·&nbsp; **Nav group:** `navGroup.licenseManagement` — two rows, "License Feature Groups" and "License Features" (sidebar labels), which land on tabs the shell itself calls "Bundles" and "Features" &nbsp;·&nbsp; **Catalog size (verified against generator data, not an in-source comment):** 89 rows across 11 root modules — 79 sellable (`active`), 10 reserved (`inactive`, the newly-registered `accounting.*` keys awaiting their backend endpoints) &nbsp;·&nbsp; **Cross-module gate to know about:** the Bundles tab's Features-composition divisor and the group-editor's whole feature picker both load through `GET /api-system/platform/license-features` (no `/all`), which is gated by `subscription.read` — a **different module's** permission key entirely (§4) &nbsp;·&nbsp; **e2e suite:** **None** — every claim on these pages is sourced from `../carmen-platform` and `../carmen-turborepo-backend-v2` implementation directly &nbsp;·&nbsp; **Sub-pages:** 2

## 1. Overview

- **`/license-features` → `LicenseCatalog` (`tab="features"`) → `FeatureCatalogPanel`** — the read-oriented catalog screen. Every non-deleted feature row, including hidden ones, grouped into a "shelf" per root module with an n-tier indent for children and grandchildren. The only edit surface is a per-row state toggle (`active` / `inactive` / `hide`); rows themselves belong to a backend generator (`scripts/generate-license-catalog/run.ts`), not this screen.
- **`/license-feature-groups` → `LicenseCatalog` (`tab="bundles"`) → `GroupCatalogPanel`** — the curated-bundle list: one row per named group, a Features-composition bar sharing a page-wide divisor, a subscription-count column, active/inactive status, and row actions to edit or delete.
- **`/license-feature-groups/new`, `/license-feature-groups/:id/edit` → `LicenseFeatureGroupEdit`** — a standalone route (not a tab inside `LicenseCatalog`) for creating or editing one bundle: its identity, its sort position on the sales form, its active/inactive status, and the set of features it grants.

Both tab routes and both `LicenseFeatureGroupEdit` routes are guarded by `PrivateRoute` with a `requiredPermission` and a `feature` flag (`App.tsx:290-321`); see §4 for the full matrix, including the one route (`:id/edit`) that requires only the read key.

## 2. Business Context

Selling Carmen inventory features to a business unit happens in two decoupled steps, and this module owns both of them:

1. **Deciding what is sellable at all.** Every route in the product maps to a permission resource, and every permission resource that should be *sellable* — not just access-controlled — gets a matching row in `tb_license_feature`, generated automatically from the permission map (`permission.route-map.ts` + `seed.permission.data.ts`). A platform admin cannot add a feature by hand; the only lever this screen gives them is turning an existing one off (`inactive` — stop selling new instances of it) or all the way off (`hide` — take the menu away from everyone who already has it).
2. **Packaging what is sellable into something a salesperson picks from once.** Ticking 89 individual feature checkboxes for every new contract does not scale and does not match how Carmen actually sells — customers buy a plan, not a checklist. **Bundles** (`tb_license_feature_group`) are the admin-curated answer: a named, orderable, freely-cross-module set of feature keys that a [Licenses](/en/platform/licenses) subscription references as a whole (`tb_subscription_bu_group`), not by unpacking it into individual feature rows on the contract.

The two steps are deliberately separate roles: deciding what *can* be sold (this module) and deciding what a specific customer *did* buy (the [Licenses](/en/platform/licenses) module) are different jobs, gated by entirely different permission resources.

## 3. Key Concepts

### 3.1 One component, two tabs, three deliberate decisions

`LicenseCatalog.tsx`'s own comments name three choices a tester would otherwise file as bugs:

- **Switching tabs navigates — it does not swap state.** `TabStrip`'s `onChange` calls `navigate(TAB_PATH[next])`, which changes the route, remounts `LicenseCatalog`'s child panel, and triggers a fresh fetch. Nothing is cached across tabs. This is intentional: both panels fetch once and are already structurally capped in size (the feature catalog and the group list are both curated, not usage-scaled data), so the cost of a fresh fetch on every tab switch is negligible, and the alternative — an in-memory cache spanning two differently-permissioned routes — is complexity nobody asked for.
- **The page header's title never changes; only the subtitle does.** `PageHeader`'s `title` is always `t('pages.licenseCatalog.title')` ("License Catalog"), regardless of which tab is active — only `subtitle` switches between `pages.licenseFeatureGroups.subtitle` and `pages.licenseFeatures.subtitle`. A title that changed per tab would make the merge unreadable as *one place*; that is the entire reason this is documented as one module and not two.
- **The tab strip disappears when only one tab is reachable.** `tabs` is computed by filtering `TAB_ORDER` through both `hasPermission(gate.permission)` **and** `flagOf(gate.feature) === 'active'` for each tab's own gate (`TAB_GATE`, §4) — a client-side re-check of exactly what the route guard already enforced — and the strip renders only when `tabs.length > 1`. A session that can reach only one of the two tabs sees a single, un-tabbed screen with no dead control pointing at a tab it cannot open.

### 3.2 The catalog is a generator-owned n-tier tree, not a flat list

`tb_license_feature` rows come **only** from `scripts/generate-license-catalog/run.ts`; `licenseFeatureService` has no create or delete by design — the only thing an operator owns is `state`. Since the 2026-09-03 "license feature tree" work (`docs/superpowers/specs/2026-09-03-license-feature-tree-design.md`, phases A–C, all shipped same day), `parent_key` is **the longest prefix that actually exists in the catalog**, not simply the text before the first dot — so a key can sit three levels deep (`accounting.config.ap`, parent `accounting.config`, root `accounting`). `moduleOf()` (`featureSelection.ts:26`) still only ever returns the **root** module and remains valid for that one purpose; walking the full ancestor chain requires `ancestorsOf()`/`descendantKeys()`/`flattenDescendants()` (`utils/featureTree.ts`), not string-splitting on the first dot.

**A source comment in this codebase is stale — verify counts against generator data, not against it.** `FeatureCatalogPanel.tsx`'s own doc-comment and `ModuleShelf.tsx`'s describe "76 rows" / "10 modules + 66 children" — both predate the 2026-09-03 tree work. Counting `"key":`/`"parent_key": null` entries directly in `seed.license-feature.data.ts` (the generator's own output, `../carmen-turborepo-backend-v2` HEAD `937cf5ac4`) gives **89 rows across 11 root modules** — `accounting`, `configuration`, `dashboard`, `inventory_management`, `operation_plan`, `procurement`, `product_management`, `report`, `store_operations`, `system_admin`, `vendor_management` — of which **79 are seeded `active`** (sellable today) and **10 are seeded `inactive`** (the ten `accounting.*` keys registered ahead of their real endpoints, per Phase C of the design doc — seeded not-active specifically so a feature with no route behind it cannot sell on day one, the same class of bug the generator's own code comments say happened once already with `report.schedule`). See [Data Model](/en/platform/license-catalog/data-model) §3 for the full shape and the hide-at-a-middle-tier hazard this tree structure creates.

### 3.3 `state` here is not the same concept as `state` on the Feature Flags screen

`FeatureCatalogPanel.tsx` defines its own `LICENSE_STATE_LABEL`/`LICENSE_STATE_HINT` key sets specifically so nobody reuses the ones from `/platform/features` (the unrelated **Feature Flags** module, `feature_flag.manage`) — the two screens share the string values `active`/`inactive`/`hide` but mean different things by them. On Feature Flags, `hide` makes a whole screen and route vanish from the SPA. Here, `hide` means "no business unit may newly acquire this, and every BU that already holds it loses the menu item" — a commercial decision, not a routing one.

### 3.4 Bundles are curated, not derived from the module tree

A bundle (`tb_license_feature_group`) is a hand-picked, free-form set of feature keys — it can span `inventory.count` and `report.daily` in one group, unlike a "module" which is always a contiguous branch of the tree (§3.2). Two rules govern what a bundle can actually hold: **the server enforces "a selected child drags its full ancestor chain in with it"** on every `PUT .../features` call (walking `parent_key` to full depth before validating, not just once at the first level) — so a bundle can never be saved holding a feature but missing one of its parent modules, which the license evaluator would otherwise treat as an incomplete grant. The picker UI (`FeatureSelectionCard`, used **only** by [UI Screens](/en/platform/license-catalog/ui-screens) §5 now — it was removed from the sales/subscription flow entirely in License Catalog's own Phase 4, per the same design doc) enforces the identical rule client-side, but the server-side check is the real gate, since `PUT` can be called directly.

## 4. Roles and Permissions

This module has no dedicated Permissions sub-page — both permission pairs are small enough to document here in full.

### 4.1 Frontend route gate matrix

All routes resolve through `PrivateRoute`, which checks `requiredPermission` first (failure → `<Forbidden>`, in place) and the `feature` flag strictly afterward (failure → `NotFound` on `hide`, `ComingSoon` on `inactive`) — see [Platform RBAC — Permissions](/en/platform/rbac/permissions) for the shared resolver.

| Route | Permission | Feature flag | Component | Source |
|---|---|---|---|---|
| `/license-features` | `license_feature.read` | `license_features` | `LicenseCatalog` (`tab="features"`) | `../carmen-platform/src/App.tsx:290-297` |
| `/license-feature-groups` | `license_feature_group.read` | `license_feature_groups` | `LicenseCatalog` (`tab="bundles"`) | `App.tsx:298-305` |
| `/license-feature-groups/new` | `license_feature_group.manage` | `license_feature_groups` | `LicenseFeatureGroupEdit` | `App.tsx:306-313` |
| `/license-feature-groups/:id/edit` | **`license_feature_group.read`** | `license_feature_groups` | `LicenseFeatureGroupEdit` | `App.tsx:314-321` |
| Sidebar "License Feature Groups" | `license_feature_group.read` | `license_feature_groups` | — | `../carmen-platform/src/components/nav/platformNav.ts:21` |
| Sidebar "License Features" | `license_feature.read` | `license_features` | — | `platformNav.ts:22` |

**The edit route requires only the read key, matching the pattern the [Licenses](/en/platform/licenses) module documents for its own purchase-form edit routes.** A `license_feature_group.read`-only session can open `/license-feature-groups/:id/edit` and see a bundle's full detail; `LicenseFeatureGroupEdit.tsx:104`'s own `canManage = hasPermission('license_feature_group.manage')` is what actually decides whether any field renders editable, whether the feature picker is `readOnly`, and whether the sticky save bar renders at all (`{canManage && (...)}` — a `read`-only session sees no save bar, not a disabled one).

In-page gates, both on `license_feature_group.manage`: the **New group** button and empty-state action (`GroupCatalogPanel.tsx:349,371`), and the row-actions dropdown's **Edit**/**Delete** items (`:286`) — a `.read`-only session sees the list and the composition bars, but no way to create, edit, or delete a bundle from the list screen itself (it can still reach `:id/edit` by URL and see the read-only detail, per the paragraph above).

### 4.2 Backend enforcement

All paths below are `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/`, HEAD `937cf5ac4` (2026-09-06).

| Endpoint | Guard | Source |
|---|---|---|
| `GET license-features/all` | `AppIdGuard` + `PlatformPermissionGuard`, `license_feature.read` | `platform_license_features/platform_license_features.controller.ts:67-70` |
| `PATCH license-features/:id` | same, `license_feature.manage` | `platform_license_features.controller.ts:99-102` |
| `GET license-feature-groups` | `license_feature_group.read` | `platform_license_feature_groups/platform_license_feature_groups.controller.ts:78-81` |
| `GET license-feature-groups/:id` | `license_feature_group.read` | `platform_license_feature_groups.controller.ts:112-115` |
| `POST license-feature-groups` | `license_feature_group.manage` | `platform_license_feature_groups.controller.ts:146-149` |
| `PATCH license-feature-groups/:id` | `license_feature_group.manage` | `platform_license_feature_groups.controller.ts:182-185` |
| `PUT license-feature-groups/:id/features` | `license_feature_group.manage` | `platform_license_feature_groups.controller.ts:226-229` |
| `DELETE license-feature-groups/:id` | `license_feature_group.manage` | `platform_license_feature_groups.controller.ts:273-276` |

Unlike the [Licenses](/en/platform/licenses) module (where every `GET` on the licence ledgers carries no `@RequirePlatformPermission` at all, authorized instead by cluster scope), **every route in this module — reads included — carries an explicit `@RequirePlatformPermission` decorator.** There is no scope-based fallback here: this catalog and its bundles are platform-wide, not cluster-scoped, so there is no narrower scope for a guard to fall back to.

### 4.3 A cross-module permission dependency, not this module's own key

**Verify this before assuming the Bundles tab is self-contained on permissions.** `GroupCatalogPanel`'s Features-composition divisor and `LicenseFeatureGroupEdit`'s entire feature picker both load their catalog through `subscriptionService.getFeatureCatalog()`, which calls `GET /api-system/platform/license-features` — **not** `/license-features/all`. That plain route is defined in a different controller entirely, `platform_subscriptions/platform_subscriptions.controller.ts:198-200`, and requires **`subscription.read`** — the [Licenses](/en/platform/licenses) module's own key, not `license_feature.read` or `license_feature_group.read`.

Consequence: a session holding `license_feature_group.read` + `license_feature_group.manage` but **not** `subscription.read` can fully open `/license-feature-groups`, list bundles, and open `/license-feature-groups/:id/edit` to change a bundle's name, sort order, or active status — but the Features-count composition bar on the list silently disappears (`catalogTotal` stays `null`, no divisor to draw a bar against), and the feature picker on the edit page fails outright (`catalog.failed === true`, rendering a retry button in place of the picker) — blocking the one thing that screen exists for, without the route itself ever having said no. This is a real, verified cross-module dependency, not a bug in either module: the shared endpoint exists because the same "which features are currently sellable" catalog is what a subscription's feature picker needs too, and reusing one endpoint avoids two implementations of "filter out `hide`" ever disagreeing.

## 5. Related Modules

- [Licenses](/en/platform/licenses) — the *consumer* of this module's bundles: a subscription's "Purchased Groups" card picks from the bundles curated here, and its own group picker depends on the cross-module endpoint documented in §4.3.
- [Platform RBAC](/en/platform/rbac) — owns the permission-catalog UI (`/platform/category-permissions`) where `license_feature.*`/`license_feature_group.*` are visible alongside every other resource; this module does not define or edit permission keys itself.
- [Feature Flags](/en/platform/feature-flags) — a different screen entirely (`feature_flag.manage`) that this module's own source comments explicitly warn not to conflate with the `state` values documented in §3.3.

## 6. Reference Sources

All paths below are `../carmen-platform` (the Platform admin SPA, HEAD `157a65e`, 2026-09-04) unless prefixed `../carmen-turborepo-backend-v2` (the backend monorepo, HEAD `937cf5ac4`, 2026-09-06).

- `../carmen-platform/src/App.tsx` (lines 290–321) — all four routes this module documents.
- `../carmen-platform/src/components/nav/platformNav.ts` (lines 21–22) — the two sidebar entries.
- `../carmen-platform/src/pages/LicenseCatalog.tsx` — the shared shell, tab gating, and the three deliberate behaviours in §3.1.
- `../carmen-platform/src/pages/licenseCatalog/FeatureCatalogPanel.tsx`, `src/pages/licenseFeatures/{CatalogStateBar,ModuleShelf}.tsx` — the Features tab.
- `../carmen-platform/src/pages/licenseCatalog/GroupCatalogPanel.tsx` — the Bundles tab.
- `../carmen-platform/src/pages/LicenseFeatureGroupEdit.tsx`, `src/pages/licenses/subscriptionEdit/FeatureSelectionCard.tsx`, `src/pages/licenses/GroupCompositionPanel.tsx`, `src/pages/licenses/FeatureCompositionBar.tsx` — the bundle editor and its shared building blocks.
- `../carmen-platform/src/services/licenseFeatureService.ts`, `src/services/licenseFeatureGroupService.ts`, `src/services/subscriptionService.ts` (`getFeatureCatalog`, §4.3) — REST clients.
- `../carmen-platform/src/utils/featureTree.ts`, `src/pages/licenses/subscriptionEdit/featureSelection.ts` — tree-walking helpers (§3.2, §3.4).
- `../carmen-platform/docs/superpowers/specs/2026-09-03-license-feature-tree-design.md` — the design record for the n-tier catalog restructuring (§3.2).
- `../carmen-turborepo-backend-v2/scripts/generate-license-catalog/run.ts` — the only writer of `tb_license_feature` rows.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.license-feature.data.ts` — the generator's own output; source of the verified 89/11/79/10 counts in §3.2.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_license_feature` (line 1214), `tb_license_feature_group` (line 1284), `tb_license_feature_group_item` (line 1313), `enum_license_feature_state` (line 740).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/license-feature/license-feature.service.ts`, `apps/micro-business/src/license-feature-group/license-feature-group.service.ts` — RPC-layer business logic (`affected_bu_count`, the parent-drag rule, delete-in-use protection).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/{platform_license_features,platform_license_feature_groups,platform_subscriptions}/*.controller.ts` — permission enforcement (§4).

## 7. Pages in This Module

- [Data Model](/en/platform/license-catalog/data-model) — `tb_license_feature`, `tb_license_feature_group`, `tb_license_feature_group_item`; the n-tier tree shape and its hide-at-a-middle-tier hazard; the verified catalog counts.
- [UI Screens](/en/platform/license-catalog/ui-screens) — the `LicenseCatalog` shell's tab mechanics in full, `FeatureCatalogPanel`, `GroupCatalogPanel`, `LicenseFeatureGroupEdit`, and the shared feature-picker/composition-bar components.
