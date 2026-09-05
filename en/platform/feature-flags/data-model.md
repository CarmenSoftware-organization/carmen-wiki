---
title: Feature Flags — Data Model
description: FEATURE_CATALOG (the frontend's 28-entry source of truth for what can be gated), the feature_flags row it is layered onto inside the shared tb_platform_config table, and the dedicated REST pair — PUT-only, no PATCH — that reads and writes it.
published: true
date: '2026-09-06T23:30:00.000Z'
tags: book/platform, feature-flags, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Feature Flags — Data Model

> **At a Glance**
> **Storage:** one row of the shared `tb_platform_config` table, `key = 'feature_flags'` — the entity itself is documented in full on [Platform Config](/en/platform/platform-config/data-model) §2; this page covers only what is specific to this key &nbsp;·&nbsp; **Shape:** a free-form `Record<string, 'active' | 'inactive' | 'hide'>` (`FeatureFlagsConfigSchema`, a Zod `record`, not an object) — the **only** registry key with no fixed field list, which is also why it is the only key that can never be `PATCH`ed (§4) &nbsp;·&nbsp; **Source of truth for *what exists*:** `FEATURE_CATALOG` in the frontend (`src/constants/featureFlags.ts`), 28 entries — the backend stores states only, never validates key names against any catalog &nbsp;·&nbsp; **Reachable only through its own pair:** `GET`/`PUT /api-system/platform/feature-flags`, never the generic `/api-system/platform/configs` surface (§4)

> **Source of truth:** the frontend catalog that defines what can be gated, and the backend schema/controller that store and serve it. Always read these first when writing or updating this page:
> - `../carmen-platform/src/constants/featureFlags.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts`
> - `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts`
>
> Verified against `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) and `carmen-platform` HEAD `157a65e` (2026-09-04).

## 1. Overview

Two things back this key, owned by two different sides of the stack. The **shape** of a valid value — a map from string key to one of three states — is defined once, in the backend's `FeatureFlagsConfigSchema` (§2), and enforced on every write. The **membership** of that map — which keys actually mean something to the UI — is defined once, in the frontend's `FEATURE_CATALOG` (§3), and is never checked by the backend at all: the schema's own doc-comment states this trade-off directly — "a deliberately free-form map: the feature list lives in the frontend, so adding one is not a backend deploy. The trade-off is that no key-name validation can happen here" (`platform-config.schema.ts`, comment immediately above `FeatureFlagsConfigSchema`). A key the backend has never heard of and a key the frontend catalog has since removed look identical to the backend — both are just entries in a JSON object — which is exactly the condition the Feature Flags landing page's orphan-key UI (§5) exists to surface back to a human.

## 2. Entity: the `feature_flags` row on `tb_platform_config`

`tb_platform_config` itself — every column, the non-enforcing `key`+`deleted_at` unique index, and the duplicate-live-row race that index does not prevent — is documented in full on [Platform Config — Data Model](/en/platform/platform-config/data-model) §2; nothing below repeats it. What is specific to this key:

- **`key = 'feature_flags'`**, one live row (or zero, before the first save).
- **`value`** is the map itself — `Record<string, 'active' | 'inactive' | 'hide'>` — never a fixed-shape object the way every other registry key's `value` is (`invitation`, `license`, etc. all have a bounded field list; this one does not).
- **Registry default: `{}`** (`platform-config.schema.ts`, `feature_flags` entry, `default: {}`) — an empty map, not a map pre-populated with every catalog key at `active`. A never-saved deployment therefore has **no row at all**, and every reader falls back to its own in-code defaults (§5) rather than reading anything from this table.
- **The two-process naming contract.** A comment directly above the dedicated controller states this row is "the same row `PLATFORM_CONFIG_REGISTRY` of micro-cluster calls `feature_flags`. Two processes, one row" (`feature_flags.controller.ts:29-31`) — the constant `FEATURE_FLAGS_KEY = 'feature_flags'` in backend-gateway and the registry key of the identical name in micro-cluster are two independent string literals in two different services that must be kept in sync by hand; nothing enforces they match beyond this comment.

## 3. `FEATURE_CATALOG` — every key, in full

Defined once, `../carmen-platform/src/constants/featureFlags.ts:47-84`. 28 entries — confirmed by direct count of the array, and cross-checked against the union of every `feature:` value used across `platformNav.ts` (24 keys) and `clusterAdminNav.ts` (4 keys): the two sets are identical, so nothing in either nav file references a key the catalog does not define, and the catalog defines nothing an actual menu row does not use. All 28 default to `active` — the file's own comment states this is deliberate: "a deploy must never hide anything on its own" (line 36-37).

| # | Key | Menu label | Console | `groupKey` |
| - | --- | --- | --- | --- |
| 1 | `clusters` | Clusters | Platform | `navGroup.organization` |
| 2 | `business_units` | Business Units | Platform | `navGroup.organization` |
| 3 | `tenant_migrations` | Tenant Migrations | Platform | `navGroup.organization` |
| 4 | `tenant_imports` | Data Import | Platform | `navGroup.organization` |
| 5 | `users` | Users | Platform | `navGroup.organization` |
| 6 | `licenses` | Licenses | Platform | `navGroup.licenseManagement` |
| 7 | `license_feature_groups` | License Feature Groups | Platform | `navGroup.licenseManagement` |
| 8 | `license_features` | License Features | Platform | `navGroup.licenseManagement` |
| 9 | `report_templates` | Report Templates | Platform | `navGroup.content` |
| 10 | `report_form_groups` | Form Groups | Platform | `navGroup.content` |
| 11 | `news` | News | Platform | `navGroup.content` |
| 12 | `broadcasts` | Broadcasts | Platform | `navGroup.content` |
| 13 | `usage_analytics` | Usage Analytics | Platform | `navGroup.analytics` |
| 14 | `activity_events` | Activity Events | Platform | `navGroup.analytics` |
| 15 | `cronjobs` | Scheduled Jobs | Platform | `navGroup.scheduling` |
| 16 | `applications` | Applications | Platform | `navGroup.platform` |
| 17 | `email_settings` | Email Settings | Platform | `navGroup.platform` |
| 18 | `platform_config` | Platform Config | Platform | `navGroup.platform` |
| 19 | `platform_roles` | Platform Roles | Platform | `navGroup.platform` |
| 20 | `super_admins` | Super Admins | Platform | `navGroup.platform` |
| 21 | `user_platform` | Platform Users | Platform | `navGroup.platform` |
| 22 | `platform_migrations` | Platform Migrations | Platform | `navGroup.database` |
| 23 | `sql_workbench` | SQL Workbench | Platform | `navGroup.database` |
| 24 | `database_pools` | Database Pools | Platform | `navGroup.database` |
| 25 | `cluster_admin_cluster` | Cluster | Cluster admin | `navGroup.clusterAdmin` |
| 26 | `cluster_admin_business_units` | Business Units | Cluster admin | `navGroup.clusterAdmin` |
| 27 | `cluster_admin_licenses` | Licenses | Cluster admin | `navGroup.clusterAdmin` |
| 28 | `cluster_admin_users` | Users | Cluster admin | `navGroup.clusterAdmin` |

Rows 25-28 are a **separate key namespace from the platform console**, despite three of the four sharing an identical menu label with a platform-side row (`business_units`/`Business Units`, `licenses`/`Licenses`, `users`/`Users`) — `clusterAdminNav.ts`'s own comment is explicit: "คีย์ของฝั่งนี้แยกจากของ platform ที่ชื่อเมนูซ้ำกัน" ("this side's keys are separate from the platform side's, whose menu names happen to be the same," line 12). Setting `business_units` to `hide` removes the platform-console **Business Units** row only; the cluster-admin console's own **Business Units** row keeps rendering until `cluster_admin_business_units` is separately set. There is no key that controls both at once.

Only **Feature Flags** carries no feature key at all, and so is the only menu row with no line in this table (`/platform/features`, permission-gated only, §4 of the landing page). **Super Admins** is not a second exception — it has a feature key, `feature: 'super_admins'` (row 20), gated by `hide`/`inactive` exactly like every other row in this table. What makes its row unusual is that it carries a **second, independent** gate on top of that: `superAdminOnly`, checked at the nav level and unrelated to the feature flag. The two mechanisms stack rather than substitute for each other — a session without super-admin status never sees the row regardless of what `super_admins` is set to, and for a session that does have super-admin status, `super_admins` can still `hide` the row or mark it `comingSoon` exactly as it would for any other key.

## 4. Write-path mechanics — validated twice, independently, and PUT-only

`GET`/`PUT /api-system/platform/feature-flags` (`feature_flags.controller.ts`) is the **only** surface that reads or writes this row — never the generic `/api-system/platform/configs/:key`, confirmed by the controller's own class-level comment giving two reasons: the `GET` on the generic surface requires `platform_config.read`, which an ordinary signed-in user does not hold, and the generic surface's per-key permission checks are additive on top of `platform_config.manage`, which would force a flag-only editor to also hold `platform_config.manage` (`feature_flags.controller.ts:54-60`).

- **`GET`** (line 83-108): guarded by `KeycloakGuard` (class-level) and `AppIdGuard('feature-flags.get')` only — **no** `PlatformPermissionGuard`, **no** `@RequirePlatformPermission` anywhere on this handler. Confirmed by reading the full method: it calls `platformConfigsService.findOne(FEATURE_FLAGS_KEY, ...)` directly and returns the bare map, with no permission check in between. Open to every authenticated caller by design (§4.2 of the landing page carries the security implication).
- **`PUT`** (line 118-174): `AppIdGuard('feature-flags.update')` **and** `PlatformPermissionGuard` **and** `@RequirePlatformPermission('feature_flag.manage')` (line 118-120) — the sole write gate.
- **Replaces the whole map — there is no `PATCH` for this key, and there structurally cannot be one.** `PlatformConfigService`'s shared `PLATFORM_CONFIG_ENTRIES` builder computes each key's known-`fields` list for `PATCH`'s unknown-field rejection, and for a non-`z.ZodObject` schema — which `feature_flags`'s `z.record(...)` is — that list is deliberately left empty (`platform-config.schema.ts:452-456`, comment: "there is no fixed field list, so PATCH is refused outright — such keys are replaced wholesale by PUT"). `rejectBadPatchShape()` rejects *any* non-empty patch payload it is given when `fields` is empty, so calling `PATCH` on `feature_flags` fails for every payload, not just malformed ones — this is a structural consequence of the schema being a `record` rather than an `object`, not a gap someone forgot to close.
- **Double validation on `PUT`, for a better error message.** The gateway controller loops over every key of the incoming body and checks its value against `['active', 'inactive', 'hide']` itself (`feature_flags.controller.ts:151-162`) **before** forwarding to micro-cluster, which validates the same body again with the real `FeatureFlagsConfigSchema` (key regex `^[a-z][a-z0-9_]*$` plus the enum) inside `PlatformConfigService.upsert()`. The comment explains why the gateway duplicates a check the backend will repeat anyway: "validated here as well so the 422 can name the offending key — a 422 that only says 'schema failed' leaves the admin unable to find which row broke" (line 148-150, paraphrased from the Thai). The gateway's own loop does **not** check the key-name regex, only the state value — an invalid key name (e.g. one with a capital letter) is caught only on the second pass, inside micro-cluster.
- **A key omitted from the `PUT` body is deleted, not left alone.** Both the frontend service (`featureFlagService.ts:24`, "แทนที่แมปทั้งใบ — คีย์ที่ไม่ได้ส่งไปถือว่าถูกลบ") and the controller's own Swagger description ("a key left out is removed") state this identically: the entire stored map is replaced by whatever object the caller sent, key for key. This is the mechanism behind the whole-map-overwrite race in §6.
- **`doc_version` must never be sent.** `tb_platform_config` carries the column, but no write path for any key on this table reads or increments it (verified on [Platform Config — Data Model](/en/platform/platform-config/data-model) §5) — `feature_flags` is not a special case here, it simply inherits the shared table's behavior. The frontend service's own comment states this as an instruction, not a discovery: "must not send `doc_version`: the `tb_platform_config` table has that column but the backend does not yet enforce it" (`featureFlagService.ts:25`).

## 5. Consumers — who reads a state, and what each one does with it

No consumer of this data caches it beyond the lifetime described below; every state check is a lookup into an already-fetched in-memory map, never a fresh network call per check.

| Consumer | Process | What it does with `hide` / `inactive` / `active` |
| --- | --- | --- |
| `FeatureFlagProvider` (`FeatureFlagContext.tsx`) | Frontend, app-wide | Fetches the whole map exactly **twice** per browser session — once on mount if a token is already in `localStorage` (line 49-62), and again on `login()` — never polled, never re-fetched by any other consumer below; all of them read the same in-memory `states` object. A failed fetch is caught and silently replaced with `DEFAULT_FEATURE_STATES` (every catalog key at `active`) — no toast, by explicit design: "an ordinary user can do nothing about it... and the app still works" (lines 23-27). `flagOf(key)` on an unrecognized key returns `'active'` (line 65) — a typo'd key can never hide a menu row. |
| `buildPlatformNav()` (`platformNav.ts:85-103`) | Frontend, platform sidebar | Filters `ALL_PLATFORM_NAV_ITEMS`: a row whose `feature` resolves to `hide` is dropped from the array entirely (line 98); a row resolving to `inactive` is kept in its original array position but gains `comingSoon: true` (line 100-102). A row with no `feature` key at all — like Feature Flags' own row — always passes both checks unconditionally. |
| `buildClusterAdminNav()` (`clusterAdminNav.ts:22-26`) | Frontend, cluster-admin sidebar | The **identical** hide-then-map-to-comingSoon logic, re-implemented independently rather than sharing a helper with `buildPlatformNav()` — confirmed by reading both functions in full; they are two separate 4-6 line blocks, not one shared utility. A future change to one filter's behavior (e.g. adding a fourth state) would need to be applied to both by hand. |
| `Sidebar.tsx`'s `navGroups` (lines 105-114) | Frontend, both sidebars | Groups the **already-filtered** array (post `hide`-removal) into headings by consecutive runs of `groupKey`, using the exact same "same key as the previous item → same group, otherwise start a new group" loop `FeatureFlagManagement.tsx`'s own `groups` useMemo (`featureFlags.ts` consumer, lines 58-66) replicates for the settings page's own card layout — two independent implementations of the identical algorithm, confirmed by reading both. A `comingSoon` row renders as a non-`<Link>`, `aria-disabled="true"` `<div>` — the component's own comment notes this is deliberate: a `<Link>` with `pointer-events: none` is still keyboard-focusable and activatable with Enter, which merely disabling via CSS would not prevent (`Sidebar.tsx`, comment above the `comingSoon` branch). |
| `PrivateRoute` (`PrivateRoute.tsx:84-102`) | Frontend, route guard | Checked **last**, after `requiredPermission` and `requireSuperAdmin` — the component's own comment states the ordering is deliberate: "permission answers 'can you access this?', the flag answers 'is this ready yet?' — someone without access should still see 403, not a flag-driven 404" (lines 90-91). `hide` renders `<NotFound />` in place (no redirect, same URL); `inactive` renders `<ComingSoon />`. Both are UI-level substitutions with **no HTTP status code involved** — `ComingSoon.tsx`'s own comment is explicit that the page carries no status code "because the server refused nothing — the UI did" (`ComingSoon.tsx:14-16`); a request to the underlying API from any other client is unaffected. |

## 6. Edge Cases

| Scenario | What actually happens |
| --- | --- |
| Two admins open the Feature Flags page at the same time and each change a different key, then both click Save | The second `PUT` to land wins outright — it sends its own full draft (seeded from the map as it was when *that* admin's page loaded), silently reverting the first admin's already-saved change to the key the second admin never touched. There is no merge, no conflict detection, and no version check (§4) — this is the ordinary last-write-wins-on-the-whole-map behavior every key of `tb_platform_config` has (documented generally on [Platform Config — Data Model](/en/platform/platform-config/data-model) §6), sharper here because the *entire* map is one key's value rather than one namespace among several. |
| A key is removed from `FEATURE_CATALOG` in a later frontend release, but its state was previously saved | `isFeatureKey()` returns `false` for it; the Feature Flags page's own `orphans` computation (`FeatureFlagManagement.tsx:44-47`) surfaces it in a dedicated "Unknown keys" card with a Remove action. Removing it only edits the in-memory `draft` (`setDraft`, line 163-168) — the row is not actually deleted from the backend until the next Save, because `PUT` always replaces the whole map (§4). Until then, refreshing the page without saving brings the orphaned key straight back. |
| The `GET /api-system/platform/feature-flags` request fails (network error, backend down) | Every consumer in §5 falls back to `DEFAULT_FEATURE_STATES` — every catalog key at `active` — silently, with `isReady` still flipping to `true` so no page hangs on a loader waiting for a request that already failed (`FeatureFlagContext.tsx:41-46`). The practical effect is that a failure to reach this endpoint makes the **entire product look fully enabled**, never partially hidden. |
| Two rapid `PUT`s race on an unsaved key (no row yet exists for `feature_flags`) | `PlatformConfigService.upsert()`'s `findFirst`-then-`create`/`update` pattern (documented for the shared table on [Platform Config — Data Model](/en/platform/platform-config/data-model) §2) applies identically here: both could observe no existing row and both `create()`, leaving two live rows for `key = 'feature_flags'`. Every reader (`findOne`, and this key's own `GET` handler) takes the most-recently-updated one, so the practical symptom is the *older* of the two writes silently disappearing rather than an error — not something this key's own code guards against specially. |
| A value that is not `'active'`/`'inactive'`/`'hide'` reaches a `flagOf()` call (e.g. a hand-edited row, or a key the frontend never uses `FEATURE_STATES` to validate against) | The gateway's `PUT` validation (§4) prevents this from ever being *saved* through the product's own UI, but does not retroactively fix a row edited directly in the database. `flagOf()` has no runtime guard beyond the TypeScript type — an unexpected string would be treated as neither `'hide'` nor `'inactive'` by every `!== 'hide'` / `=== 'inactive'` comparison in §5, which means it behaves exactly like `'active'` everywhere without ever being validated as such. Not verified against a live database — reasoned from the comparison operators alone. |

## 7. Recommendations

- **Never test a flag flip by editing `tb_platform_config` directly and expecting `PATCH` semantics** — `feature_flags` structurally rejects every `PATCH`, valid or not (§4); the only supported write is a full-map `PUT` through the dedicated endpoint.
- **A concurrent-edit test plan should expect last-write-wins on the whole map, not per-key** — see §6's first row. Do not file a bug for a change that "disappeared" when another admin saved seconds later; this is the documented, current behavior of `tb_platform_config`'s shared write path, not specific to this key.
- **Do not assume the backend can catch a mistyped key name** — outside the `PUT` value-validation loop (§4), nothing on the backend checks a key against `FEATURE_CATALOG`; a typo saved through direct API access would sit invisibly in the map, matching no menu row, until someone notices it as an "unknown key" on the page itself.
- **Treat `flagOf()`'s fallback-to-`'active'` as the default assumption for any key not in this document** — including a brand-new key added to `FEATURE_CATALOG` after this page was written; verify against `featureFlags.ts` directly rather than assuming this table (§3) is exhaustive at the time it is read.

## 8. References

- `../carmen-platform/src/constants/featureFlags.ts` — `FeatureState`, `FeatureDefinition`, `FEATURE_CATALOG` (§3), `isFeatureKey`, `DEFAULT_FEATURE_STATES`.
- `../carmen-platform/src/context/FeatureFlagContext.tsx` — fetch timing, fallback-on-failure, `flagOf` (§5).
- `../carmen-platform/src/components/nav/platformNav.ts` (lines 85-103) and `src/components/nav/clusterAdminNav.ts` (lines 10-26) — the two independent `hide`/`inactive` filters (§5).
- `../carmen-platform/src/components/Sidebar.tsx` (lines 105-114 and the `comingSoon` render branch) — consecutive-run grouping and the non-`<Link>` disabled row (§5).
- `../carmen-platform/src/components/PrivateRoute.tsx` (lines 84-102) — route-level enforcement ordering and outcomes (§5).
- `../carmen-platform/src/pages/ComingSoon.tsx` — the no-status-code design note (§5).
- `../carmen-platform/src/pages/FeatureFlagManagement.tsx` (lines 44-47, 58-66, 152-169) — orphan detection, settings-page grouping, draft-only removal (§6).
- `../carmen-platform/src/services/featureFlagService.ts` — the REST client, including the `doc_version` warning (§4).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts` — the dedicated `GET`/`PUT` pair, guards, and double validation (§4).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` (lines 242-246, 360-369, 452-456) — `FeatureFlagsConfigSchema`, the registry entry, and the empty-`fields`-means-PATCH-refused mechanism (§4).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (line 1462) — `tb_platform_config`, documented in full on [Platform Config — Data Model](/en/platform/platform-config/data-model).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` (line 43) — the `feature_flag.manage` catalog entry, cited on the landing page §4.

**Cross-links:** [Feature Flags landing](/en/platform/feature-flags) &nbsp;·&nbsp; [Platform Config — Data Model](/en/platform/platform-config/data-model)
