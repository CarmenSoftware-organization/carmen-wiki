---
title: License Catalog — Data Model
description: tb_license_feature (generator-owned, n-tier tree since the 2026-09-03 catalog restructuring) and tb_license_feature_group / tb_license_feature_group_item (admin-curated bundles), with the verified current catalog counts.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, license-catalog, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# License Catalog — Data Model

> **At a Glance**
> **`tb_license_feature`** — the sellable-capability catalog. Rows come **only** from a backend generator; a platform admin edits `state` alone &nbsp;·&nbsp; **`tb_license_feature_group`** — an admin-curated, freely cross-module bundle of feature keys, sold as a unit &nbsp;·&nbsp; **`tb_license_feature_group_item`** — the join, `feature_key` referenced **by value, no FK** on purpose &nbsp;·&nbsp; **Tree shape:** n-tier since 2026-09-03 (`parent_key` = longest existing prefix, not "text before the first dot") &nbsp;·&nbsp; **Verified catalog size:** 89 rows / 11 root modules / 79 `active` / 10 `inactive` — corrects a stale in-source comment claiming 76/10/66 (§3) &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` on both tables, optimistic lock on every write

> **Source of truth:** the backend Prisma platform schema and the generator's own output file. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.license-feature.data.ts` (generated — do not hand-edit, but it is the authoritative current catalog content)
> - `../carmen-turborepo-backend-v2/scripts/generate-license-catalog/run.ts`
>
> Verified against `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) and `carmen-platform` HEAD `157a65e` (2026-09-04).

## 1. Overview

Two tables, no shared parent, and a deliberately weak link between them. `tb_license_feature` is a flat table shaped like a tree via a self-referencing `parent_key` column — it is the catalog of everything that *can* be sold, and it belongs entirely to a code generator; nothing in this module's UI can add or remove a row. `tb_license_feature_group` is the opposite kind of table: every row is created, named, and populated by a human through this module's own edit screen, and a group can hold any combination of feature keys regardless of which branch of the tree they come from. The two are joined only through `tb_license_feature_group_item`, and that join is intentionally **not** a foreign key — see §2.3.

## 2. Entities

### 2.1 `tb_license_feature` — the sellable-capability catalog

Schema line 1214. One row per feature key.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `key` | `String @db.VarChar` | No | The wire key, e.g. `accounting.config.ap` — this **is** the permission resource it derives from |
| `parent_key` | `String? @db.VarChar` | Yes | `null` for a root module; otherwise the **longest existing prefix** of `key` in the catalog (§3) |
| `label` | `String @db.VarChar` | No | `humanize()` of the segment after `parent_key`, generated — not hand-written |
| `description` | `String?` | Yes | Generator-authored; most values are a bare `"View " + label`, which the UI deliberately hides when it adds nothing (see [UI Screens](/en/platform/license-catalog/ui-screens) §3) |
| `sort_order` | `Int @default(0)` | No | See §3 for the module/child/grandchild banding formula |
| `state` | `enum_license_feature_state @default(active)` | No | `active` \| `inactive` \| `hide` (§5) — the **only** field an operator edits, and only via `PATCH` |
| `doc_version` | `Int @default(0)` | No | Optimistic-lock counter, required on `PATCH` |
| audit trio + soft delete | — | Yes | Standard `created_at`/`created_by_id`/`updated_at`/`updated_by_id`/`deleted_at`/`deleted_by_id` |

**Constraints:** `@@unique([key, deleted_at])` (map `license_feature_key_deleted_at_u`). **Indexes:** `(parent_key, deleted_at)`.

**A schema comment states the write boundary directly:** `state` is the one field the generator's own seeder never overwrites on an existing row (`seed.license-feature.data.ts`'s type comment: seeding writes `state` only when **creating** a row) — because it is the one value that belongs to a human operator, not the generator. A newly-created row (e.g. a freshly-registered `accounting.*` key) does get its seeded `state`, since no operator decision exists yet to protect.

### 2.2 `tb_license_feature_group` — an admin-curated bundle

Schema line 1284. One row per named, sellable bundle.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | Set once at create; the backend rejects `PATCH` payloads that include it — changing a bundle's code would change its identity, not just rename it |
| `name` | `String @db.VarChar` | No | Editable |
| `description` | `String?` | Yes | Editable, free text |
| `sort_order` | `Int @default(0)` | No | The bundle's position on the sales form — collisions across bundles are allowed by the schema and flagged (not blocked) by the UI (see [UI Screens](/en/platform/license-catalog/ui-screens) §4) |
| `is_active` | `Boolean @default(true)` | No | Whether the bundle is currently offered for sale |
| `doc_version` | `Int @default(0)` | No | Optimistic-lock counter, required on `PATCH` and on `PUT .../features` |
| audit trio + soft delete | — | Yes | Standard |

**Constraints:** `@@unique([code, deleted_at])` (map `license_feature_group_code_deleted_at_u`). **Indexes:** `(is_active, deleted_at)`.

**Relations:** `tb_license_feature_group_item[]` (§2.3), `tb_subscription_bu_group[]` — the [Licenses](/en/platform/licenses) module's join table that attaches this bundle to a specific business unit's subscription. A bundle referenced by one or more live `tb_subscription_bu_group` rows cannot be deleted (see §4).

### 2.3 `tb_license_feature_group_item` — the join, by value not by foreign key

Schema line 1313. One row per (group, feature key) pair.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `group_id` | `String @db.Uuid` | No | FK to `tb_license_feature_group.id` |
| `feature_key` | `String @db.VarChar` | No | **References `tb_license_feature.key` by value — no foreign key** |
| `doc_version` | `Int @default(0)` | No | — |
| audit trio + soft delete | — | Yes | Standard |

**Constraints:** `@@unique([group_id, feature_key, deleted_at])` (map `license_feature_group_item_group_key_deleted_at_u`). **Indexes:** `(feature_key, deleted_at)`.

**The missing foreign key is deliberate, per the schema's own doc-comment:** the feature catalog is regenerated wholesale by an external script, and that regeneration must never be able to cascade-delete a bundle's membership just because a key was momentarily absent from one generator run. The service layer (`LicenseFeatureGroupService.setFeatures`, backend `micro-business`) is the **only** place a key is validated against the live catalog — every `PUT` re-checks every desired key against `tb_license_feature` and rejects unknown or no-longer-`active` keys with a 400, rather than trusting a constraint the schema deliberately does not have.

## 3. Catalog shape — an n-tier tree, and the verified current counts

Since the 2026-09-03 "license feature tree" work (design doc `docs/superpowers/specs/2026-09-03-license-feature-tree-design.md`, Phases A–C, all shipped the same day), `parent_key` is **the longest prefix that actually exists as another row's `key`** — not simply everything before the first dot. A three-level key is real today: `accounting.config.ap`'s parent is `accounting.config`, whose own parent is `accounting`. `moduleOf()` (`featureSelection.ts:26`, frontend) still only ever strips to the first dot and remains correct **only** for finding the root module of a key — walking the true ancestor chain requires `ancestorsOf()`/`descendantKeys()`/`flattenDescendants()` (`utils/featureTree.ts`), which walk `parent_key` link by link.

**`sort_order` bands children and grandchildren separately, by design (Phase A, §4.2 of the design doc):** a root module's own row is `(module_index + 1) × 1000`; its direct children continue from `+1`; any grandchildren sit in a `+500` band above the module's own base, ordered depth-first by sibling order — not by raw `sort_order`, which would put every grandchild after every module's direct children platform-wide. This is why every UI surface that lists the catalog (`FeatureCatalogPanel`'s `ModuleShelf`, `FeatureSelectionCard`) sorts by walking the tree (`flattenDescendants`) rather than by `sort_order` alone.

**Verified current counts — do not trust the in-source comments.** `FeatureCatalogPanel.tsx`'s own doc-comment and `ModuleShelf.tsx`'s both still describe "76 rows" and "10 modules + 66 children," which predate the 2026-09-03 restructuring. Counting the generator's own output directly:

```
grep -c '"key":' seed.license-feature.data.ts           → 89
grep -c '"parent_key": null' seed.license-feature.data.ts → 11
grep -c '"state": "active"' seed.license-feature.data.ts   → 79
grep -c '"state": "inactive"' seed.license-feature.data.ts → 10
```

**89 total rows, 11 root modules** (`accounting`, `configuration`, `dashboard`, `inventory_management`, `operation_plan`, `procurement`, `product_management`, `report`, `store_operations`, `system_admin`, `vendor_management`), **78 non-root rows** spread across up to three tiers, **79 rows currently sellable** (`active`) and **10 reserved but not yet sellable** (`inactive` — the ten `accounting.*` keys registered in Phase C ahead of their real endpoints; the design doc's own §2.4 explains why they were seeded `inactive` rather than the schema's own `active` default: a feature with no route behind it yet must not be sellable on day one, the exact class of bug the generator's code comments say already happened once, with `report.schedule`).

**The hazard this tree shape creates — hiding a middle tier breaks every descendant's entitlement, invisibly on this screen.** The runtime license evaluator (`license.evaluator.ts` in `carmen-turborepo-backend-v2`, per the design doc §2.2/§4.5) drops every `state='hide'` key from a business unit's effective `features` set **before** checking that every ancestor of a held key is also held. Setting a middle-tier feature to `hide` therefore silently fails the ancestor check for every descendant, for every business unit that holds them — even though those descendants still display as `active` on this screen, since their own row's `state` never changed. `FeatureCatalogPanel`'s hide-confirmation dialog appends a descendant count specifically because of this hazard (see [UI Screens](/en/platform/license-catalog/ui-screens) §3); it is a deliberate, documented risk in the design, not something this page is flagging as a bug.

## 4. Relationships

```
tb_license_feature.parent_key              ──>  tb_license_feature.key       (self-reference, by value)
tb_license_feature_group_item.group_id     ──>  tb_license_feature_group.id
tb_license_feature_group_item.feature_key  ──>  tb_license_feature.key       (by value, no FK — §2.3)
tb_subscription_bu_group.group_id          ──>  tb_license_feature_group.id  (owned by the Licenses module)
*.created_by_id / *.updated_by_id / *.deleted_by_id  ──>  tb_user.id  (audit actors)
```

Neither `tb_license_feature` nor `tb_license_feature_group` has a foreign key toward the other's table — the catalog and its bundles are two independently-maintained sets, joined only through the by-value reference in §2.3.

## 5. Enum

`enum_license_feature_state` (schema line 740): `active` | `inactive` | `hide`. This spelling is the wire contract with the frontend (`FeatureState` in `src/constants/featureFlags.ts` states outright: "these three strings are the wire contract with the backend enum — do not rename them") — but see §3.3 of the [landing page](/en/platform/license-catalog) for why the identical three strings mean something different on the unrelated Feature Flags screen. There is no separate enum for `tb_license_feature_group` — `is_active` is a plain boolean, not a three-state field, because a bundle has no equivalent to `hide`: deactivating a bundle stops it being offered for **new** sales but a subscription that already references it keeps its entitlement live (removing the entitlement outright means editing the bundle's feature set, or deleting the bundle, both covered by §7 of [UI Screens](/en/platform/license-catalog/ui-screens)).

## 6. `affected_bu_count` — computed, not stored

`LicenseFeatureAdminRow.affected_bu_count` (only present on the admin `listAll` response, never on the plain catalog read) is computed server-side (`LicenseFeatureService.countAffectedBusinessUnits()`, `apps/micro-business/src/license-feature/license-feature.service.ts`) by walking the exact same join path the runtime evaluator uses to build a business unit's entitlement set: `tb_subscription_bu → tb_subscription_bu_group → tb_license_feature_group → tb_license_feature_group_item`, counting **distinct business units** per feature key (not distinct rows — one BU can reach the same key through more than one group or subscription). It **deliberately includes expired subscriptions**: a BU whose contract has expired still sees the menu today, per the service's own comment, so it would still lose it if the key were hidden — undercounting toward "safe" would be the wrong direction for a warning. The field is `optional`, and `undefined` must never be read as `0` — it means an older gateway response did not send the field at all, not that zero business units hold the key.

## 7. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_license_feature` (1214), `tb_license_feature_group` (1284), `tb_license_feature_group_item` (1313), `enum_license_feature_state` (740).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.license-feature.data.ts` — the generator's own current output; source of the verified counts in §3.
- `../carmen-turborepo-backend-v2/scripts/generate-license-catalog/run.ts` — the only writer of `tb_license_feature` rows.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/license-feature/license-feature.service.ts` — `listAll()`, `countAffectedBusinessUnits()` (§6), `setState()`.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/license-feature-group/license-feature-group.service.ts` — `list()`/`get()`/`create()`/`update()`/`setFeatures()`/`delete()`, the parent-drag rule, and delete-in-use protection.
- `../carmen-platform/docs/superpowers/specs/2026-09-03-license-feature-tree-design.md` — the n-tier restructuring design and its verification probes (§3).

**Secondary (consumer shape):**
- `../carmen-platform/src/utils/featureTree.ts` — `ancestorsOf()`, `descendantKeys()`, `flattenDescendants()`.
- `../carmen-platform/src/pages/licenses/subscriptionEdit/featureSelection.ts` — `moduleOf()`, `toggleFeature()`, `setModuleSelection()`, `groupCatalog()`.
- `../carmen-platform/src/types/index.ts` — `LicenseFeature`, `LicenseFeatureAdminRow`, `LicenseFeatureGroup`, `LicenseFeatureGroupDetail`, `LicenseFeatureGroupWriteInput`.
- `../carmen-platform/src/constants/featureFlags.ts` — `FeatureState`, `FEATURE_STATES` (the shared wire-contract type, §5).

**Cross-links:** [License Catalog landing](/en/platform/license-catalog) &nbsp;·&nbsp; [UI Screens](/en/platform/license-catalog/ui-screens) &nbsp;·&nbsp; [Licenses](/en/platform/licenses)
