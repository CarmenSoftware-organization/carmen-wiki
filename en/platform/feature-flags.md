---
title: Feature Flags
description: The single screen that sets every feature's visibility (active/inactive/hide) across both the Platform and Cluster-admin consoles — deliberately reachable through no feature key of its own, since a switch that could hide itself could never be restored from the UI.
published: true
date: '2026-09-06T23:30:00.000Z'
tags: book/platform, feature-flags
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Feature Flags

The **Feature Flags** module is one screen, `FeatureFlagManagement` at `/platform/features`, that sets a three-way visibility switch — `active`, `inactive`, or `hide` — for every gated menu row in both the Platform admin sidebar and the separate Cluster-admin sidebar. It is the mechanism every other module in this book states a feature key for, and the one module whose own menu row deliberately carries no feature key of its own (§2). Nothing else in the product resembles this page: it has no table, no search, no pagination, and edits nothing a person created — it edits a fixed catalog baked into the frontend build (§3.3).

> **At a Glance**
> **Component:** `FeatureFlagManagement` &nbsp;·&nbsp; **Route:** `/platform/features` &nbsp;·&nbsp; **Nav:** `permission: 'feature_flag.manage'`, **no `feature` key** — deliberately not gated by a feature flag (§2) &nbsp;·&nbsp; **Read gate:** none — `GET` is open to every signed-in user (§4.2) &nbsp;·&nbsp; **Write gate:** `feature_flag.manage` alone, held only by the `Platform Admin` role bundle among the four seeded platform roles (§4.1) &nbsp;·&nbsp; **Scope:** 28 flag keys total — 24 for the Platform console, 4 for the separate Cluster-admin console (§3.3) &nbsp;·&nbsp; **e2e suite:** **none** — `../carmen-platform-e2e/tests/` has no `feature-flags` directory; every claim below is sourced from `../carmen-platform` and `../carmen-turborepo-backend-v2` implementation directly (§4.4) &nbsp;·&nbsp; **Sub-pages:** 1

## 1. Overview

`FeatureFlagManagement.tsx` fetches the whole feature-state map once through `FeatureFlagContext` (data model page §5) and renders it as a stack of cards — one card per `groupKey`, in the same order the sidebar groups its own menu — with a three-way toggle (`FeatureStateToggle`) per feature. The page's own doc-comment states its category directly: "a Config page, not a Management one: the feature set comes from an in-code catalog" (`FeatureFlagManagement.tsx:25-27`) — confirmed by reading the component whole: there is no list endpoint with filters, no create/delete of a feature itself, only a save of the whole map (data model page §4). A card for a key the current build's catalog does not recognize ("Unknown keys") appears below the normal cards when the saved map carries one, with a Remove action (data model page §6).

## 2. Business Context

This module exists because every other gated screen in the product needs an operator-controllable kill switch that does not require a redeploy — `hide` lets an unfinished or broken feature disappear from the menu entirely, and `inactive` lets it stay visible as a "coming soon" preview without being reachable. Both states are read from the identical `tb_platform_config` row every other config key shares (data model page §2).

**Why this page's own row carries no `feature` key: no feature-flag comment is quoted as fact without being checked against the code around it.** `platformNav.ts` states the reasoning directly above the row: "ไม่มี feature โดยเจตนา — สวิตช์ที่ปิดตัวเองได้จะเปิดกลับไม่ได้อีกจากหน้าจอ" / "Deliberately ungated: a switch that could hide itself could never be restored from the UI" (`platformNav.ts:47-48`), and the row itself confirms it — it is the **only** entry in the entire 26-row `ALL_PLATFORM_NAV_ITEMS` array with a `permission` but genuinely no `feature` property at all (verified by reading every row in the file, not by trusting the comment). The honest phrasing for this row is **"no feature key, deliberately — gated by `feature_flag.manage`,"** never "no permission check" or "unguarded" — the permission gate is real and separately enforced server-side (§4.2).

A second, broader comment in `featureFlags.ts` lists eight routes as deliberately carrying no feature key at all: `/dashboard`, `/platform/features`, `/profile`, `/changelog`, `/login`, `/`, `/403`, `/404` (lines 39-41). Reading `App.tsx` confirms every one of them: `/`, `/login`, and `/changelog` are not wrapped in `PrivateRoute` at all; `/dashboard`, `/profile`, and `/403` are wrapped in a bare `<PrivateRoute>` with no `feature` prop; and `/404` is the unauthenticated catch-all route. The comment's own wording already separates two distinct reasons rather than treating all eight identically — "closing any of them would lock the app **or the switch itself**" — and only the second half of that sentence applies to this page: the other seven are ungated because they are unauthenticated, universal, or error destinations that gating would make nonsensical, not because gating them would create a self-referential lock the way gating Feature Flags would.

## 3. Key Concepts

### 3.1 Three states, three different effects — verified against the actual filter, not the comment beside it

`buildPlatformNav()`'s own filter (`platformNav.ts:91-98`) is the ground truth for what each state does to a menu row, read directly rather than taken from its adjacent comment:

| State | Effect on the sidebar row | Effect on the route |
| --- | --- | --- |
| `active` | Renders normally | Renders the page |
| `inactive` | **Stays in its original position**, rendered as `comingSoon: true` — a non-clickable, `aria-disabled` row, not a hidden one (data model page §5) | `PrivateRoute` renders `<ComingSoon />` in place, no redirect, no HTTP status code (data model page §5) |
| `hide` | Removed from the filtered array entirely | `PrivateRoute` renders `<NotFound />` in place — indistinguishable from a URL that never existed |

A key with no state saved at all — including every key on a deployment that has never opened this page and saved once — is treated as `active` (`flagOf()`'s unknown-key fallback, data model page §5); nothing needs to be `active` explicitly.

### 3.2 Why `inactive` never changes a row's position — verified against `Sidebar.tsx`, not just quoted from the nav file

The comment beside `buildPlatformNav()`'s filter states the reason `inactive` (unlike `hide`) never removes a row: "Sidebar จัดกลุ่มจากแถวที่ groupKey ซ้ำกันติด ๆ การตัดรายการกลางกลุ่มออกจึงทำให้กลุ่มเดียวแตกเป็นสองหัวข้อได้" / "the sidebar groups by consecutive runs of the same `groupKey`; dropping one mid-group would split its heading in two" (`platformNav.ts:95-97`). This is not just asserted by the nav file — reading `Sidebar.tsx`'s own `navGroups` computation confirms the actual rendering behavior matches: it walks the (already `hide`-filtered) array and starts a new heading only when the current item's `groupKey` differs from the previous item's, exactly the algorithm the comment describes (`Sidebar.tsx:105-114`). Several of `platformNav.ts`'s own inline comments exist purely to keep this invariant intact by hand — e.g. the note that Database's two rows "must stay last" because pulling them out mid-group once split the Platform heading in two (`platformNav.ts:50-52`) — a maintenance hazard the contiguity rule creates, not something `buildPlatformNav()` itself protects against.

### 3.3 Full flag-key inventory — both consoles

All 28 keys `FEATURE_CATALOG` defines, the menu each one controls, and which console it belongs to (full field-level detail — `groupKey`, default state — is on the [data model page](/en/platform/feature-flags/data-model) §3):

**Platform console (24 keys)** — `clusters`, `business_units`, `tenant_migrations`, `tenant_imports`, `users` (Organization); `licenses`, `license_feature_groups`, `license_features` (License Management); `report_templates`, `report_form_groups`, `news`, `broadcasts` (Content); `usage_analytics`, `activity_events` (Analytics); `cronjobs` (Scheduling); `applications`, `email_settings`, `platform_config`, `platform_roles`, `super_admins`, `user_platform` (Platform); `platform_migrations`, `sql_workbench`, `database_pools` (Database).

**Cluster-admin console (4 keys, a separate namespace)** — `cluster_admin_cluster` (Cluster), `cluster_admin_business_units` (Business Units), `cluster_admin_licenses` (Licenses), `cluster_admin_users` (Users). `clusterAdminNav.ts`'s own comment states these are deliberately separate from the platform side "ที่ชื่อเมนูซ้ำกัน" ("whose menu names happen to be the same," line 12) — three of the four labels (Business Units, Licenses, Users) are identical strings to a platform-console row, but setting the platform key `hide` never touches the cluster-admin row of the same name, and vice versa; a reader who assumes one key covers both consoles will be wrong.

**Not on this list:** the Feature Flags row itself carries no feature key (§2); neither does the Dashboard, Landing, Login, Changelog, or error-page routes (§2), since none of them is a *gated menu row* in the first place.

## 4. Roles and Permissions

### 4.1 Frontend and role-level gate

| Surface | Gate | Source |
| --- | --- | --- |
| Sidebar "Feature Flags" entry, `/platform/features` route | `permission: 'feature_flag.manage'` — **no `feature` key** | `platformNav.ts:49`; `App.tsx:555-561` (`<PrivateRoute requiredPermission="feature_flag.manage">`, no `feature` prop) |
| Every toggle on the page | No separate UI gate beyond reaching the route at all — a session that can open the page can flip any toggle | `FeatureFlagManagement.tsx` (no `hasPermission` call anywhere in the component) |

`feature_flag.manage` is seeded on exactly one of the four platform role bundles (`seed.platform-role-permission.data.ts:11-52`): `Platform Admin` (`feature_flag.*`, line 33). `Support Manager`, `Support Staff`, and `Security Officer` hold neither this key nor any other `feature_flag.*` permission — confirmed by reading all four role arrays in full, not just the one that has it. The permission catalog's own description states the resource was deliberately split out from `platform_config` rather than made an action of it, "so whoever gates unfinished features is not necessarily whoever edits invitation links or SMTP routing" (`seed.platform-permission.data.ts`, comment above the `feature_flag.manage` entry).

### 4.2 Backend enforcement

`../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts`, HEAD `937cf5ac4` (2026-09-06):

| Route | Guard | Source |
| --- | --- | --- |
| `GET /api-system/platform/feature-flags` | `KeycloakGuard` + `AppIdGuard('feature-flags.get')` **only** — no RBAC permission of any kind | lines 65-108 |
| `PUT /api-system/platform/feature-flags` | `KeycloakGuard` + `AppIdGuard('feature-flags.update')` + `PlatformPermissionGuard` + `@RequirePlatformPermission('feature_flag.manage')` | lines 65, 118-120 |

The `GET` being open to every authenticated caller — not just Platform Admins — is stated by the controller's own Swagger description as deliberate: "the map decides what the UI renders, so a user who cannot read it sees the frontend built-in defaults instead" (`feature_flags.controller.ts:88-89`). Reading `PlatformPermissionGuard.canActivate()` in full confirms the super-admin short-circuit applies here exactly as it does on every other `@RequirePlatformPermission` route: `is_super_admin === true` returns `true` before `feature_flag.manage` is checked at all — a super admin can write this endpoint with no `feature_flag.*` grant of their own.

### 4.3 This module's own row is UI-only — a security fact, not an inference

Three independent sources state the same thing, so this is reported as fact, not inferred from reading one mechanism and extrapolating:

1. **The permission catalog's own description**, seeded alongside every other permission key: "Frontend visibility only — it does NOT block the corresponding backend endpoints" (`seed.platform-permission.data.ts`, `feature_flag.manage` entry).
2. **The page's own subtitle, shown to every admin who opens it**: "Choose what each feature shows on screen. Frontend visibility only — it does not close the matching API" (`en.ts:967-968`, `pages.featureFlags.subtitle`).
3. **`ComingSoon.tsx`'s own design comment**, on what setting a flag to `inactive` actually produces at the route level: no HTTP status code, "because the server refused nothing — the UI did" (data model page §5).

The practical consequence for a tester: setting a route's feature to `hide` or `inactive` changes only what the SPA renders for that path. It has no bearing on whether the corresponding backend endpoint accepts a direct request — that is decided entirely by whatever RBAC permission the endpoint itself requires (documented on that module's own page), which continues to apply whether or not the frontend currently shows a menu entry for it.

### 4.4 e2e coverage: none

`../carmen-platform-e2e/tests/` has no `feature-flags` (or similarly named) directory — confirmed by listing the repository's `tests/` tree directly. Every behavioral claim on this page and its data model sub-page is sourced from reading `../carmen-platform` and `../carmen-turborepo-backend-v2` implementation, not from an executable spec.

## 5. Related Modules

- [Platform Config](/en/platform/platform-config) and its [data model](/en/platform/platform-config/data-model) — the shared `tb_platform_config` table this key's row lives on, including the general-purpose write-path mechanics (validation, the non-enforced `doc_version` column, the duplicate-live-row race) this module inherits without modification.
- [Platform RBAC](/en/platform/rbac) — the permission catalog where `feature_flag.manage` and the four seeded role bundles referenced in §4.1 are defined and browsable in full.
- Every other module in this book — each states the feature key that gates its own menu row; this page is where a reader learns what setting that key to `active`/`inactive`/`hide` actually does.

## 6. Reference Sources

All paths below are `../carmen-platform` (the Platform admin SPA, HEAD `157a65e`, 2026-09-04) unless prefixed `../carmen-turborepo-backend-v2` (the backend monorepo, HEAD `937cf5ac4`, 2026-09-06).

- `../carmen-platform/src/pages/FeatureFlagManagement.tsx` — the page component, its own "Config page, not Management" doc-comment (§1).
- `../carmen-platform/src/constants/featureFlags.ts` — `FEATURE_CATALOG`, the ungated-pages comment (§2), the contiguity-rule comment.
- `../carmen-platform/src/components/nav/platformNav.ts` (lines 9-56, 47-49, 91-103) and `src/components/nav/clusterAdminNav.ts` (lines 10-26) — the nav row itself, `buildPlatformNav()`/`buildClusterAdminNav()` (§2, §3).
- `../carmen-platform/src/components/Sidebar.tsx` (lines 105-114) — the consecutive-run grouping this page's contiguity claims are checked against (§3.2).
- `../carmen-platform/src/App.tsx` (lines 99-106, 555-561, 563-575, 606) — every route cited in §2 and §4.1.
- `../carmen-platform/src/pages/ComingSoon.tsx` — the no-status-code design note (§4.3).
- `../carmen-platform/src/i18n/en.ts` (lines 15-43, 965-985) — nav labels and the page's own copy (§4.3).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts` — the dedicated `GET`/`PUT` pair and guards (§4.2).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts` — the super-admin short-circuit shared by every `@RequirePlatformPermission` route (§4.2).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` and `seed.platform-role-permission.data.ts` — the `feature_flag.manage` catalog entry and its single role assignment (§4.1, §4.3).
- `../carmen-platform-e2e/tests/` — listed directly to confirm no `feature-flags` suite exists (§4.4).

## 7. Pages in This Module

- [Data Model](/en/platform/feature-flags/data-model) — the `feature_flags` row's exact shape, the full `FEATURE_CATALOG` table with every key's `groupKey` and default, the PUT-only write path, and the consumer-by-consumer breakdown of what each state does.
