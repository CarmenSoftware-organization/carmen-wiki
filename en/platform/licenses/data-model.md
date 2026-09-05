---
title: Licenses — Data Model
description: tb_cluster_license and its winning-row views, tb_business_unit_license and its summed view, tb_subscription's feature-group joins, and the three configurable expiry thresholds.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, licenses, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Licenses — Data Model

> **At a Glance**
> **Purchase ledgers:** `tb_cluster_license` (BU quota, per cluster, cancellable) &nbsp;·&nbsp; `tb_business_unit_license` (seats, per BU, not cancellable) &nbsp;·&nbsp; **Contract:** `tb_subscription` (one row per cluster+BU pair) → `tb_subscription_bu` → `tb_subscription_bu_group` (feature-group entitlements, replace-on-save) &nbsp;·&nbsp; **Views:** `v_cluster_bu_cap` (one row per **cluster** — the winning licence's cap) and `v_cluster_bu_quota` (one row per **business unit** — rank + the cap borrowed from the first view) are two different grains answering two different questions — do not conflate them &nbsp;·&nbsp; `v_business_unit_seat` (one row per BU — summed, not winner-take-all) &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` on all three purchase/contract tables, optimistic lock on every write &nbsp;·&nbsp; **Expiry thresholds:** three independent day-counts (`subscription_days`, `bu_quota_days`, `seat_days`), default 30 each, editable from Platform Config, read with no permission required

> **Source of truth:** Backend Prisma platform schema and its hand-written migration SQL. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql`, `20260824000000_add_cap_end_date_to_view/migration.sql`, `20260901020000_cluster_license_cancel/migration.sql`, `20260819000000_bu_user_license/migration.sql`, `20260821130000_subscription_one_bu/migration.sql`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative. Verified against `carmen-turborepo-backend-v2` HEAD `50cce6953` (2026-09-06) and `carmen-platform` HEAD `157a65e` (2026-09-04).

## 1. Overview

Three purchase types, three tables, no shared parent. `tb_cluster_license` is a cluster's purchased right to create up to N business units for a date range — a pure ledger of purchase rows; "which row wins right now" is a question the database answers with a view (§3), not a column on the table. `tb_business_unit_license` is the same shape one level down: a business unit's purchased right to fill up to N user seats for a date range, but counted by **summing** every currently-active row rather than picking a single winner (§3.2) — buying two concurrent seat blocks genuinely adds their capacities together, unlike BU quota, where a second purchase replaces the first's effect rather than adding to it. `tb_subscription` is a different kind of record entirely: not a capacity ledger but a commercial contract between a cluster and one specific business unit, whose only purpose in this schema is to anchor which **feature groups** (defined by [License Catalog](/en/platform/license-catalog)) that BU's contract entitles it to use.

All three purchase/contract tables carry the platform-standard audit trio, soft delete, and a `doc_version` optimistic-concurrency counter enforced on every write (`PATCH`/`PUT`/the cancel endpoint all require it and 409 on a stale value).

## 2. Entities

### 2.1 `tb_cluster_license` — BU-quota purchase ledger

One purchased licence granting a cluster the right to create up to `licensed_bus` business units for `[start_date, end_date)`. Schema line 1168.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `license_number` | `String @db.VarChar` | No | Server-issued `BUQ-YYMM-####`; not accepted on create — the client never sends it. Unique among live rows via a partial unique index declared only in raw SQL (Prisma cannot express a `WHERE` clause on `@@unique`) |
| `cluster_id` | `String @db.Uuid` | No | FK to `tb_cluster.id` — the owner |
| `licensed_bus` | `Int` | No | The quota this licence grants; `CHECK (licensed_bus >= 0)` |
| `start_date` / `end_date` | `DateTime @db.Timestamptz(6)` | No | Coverage window; `CHECK (end_date > start_date)`. A "no expiry" purchase writes the sentinel `2099-12-31T23:59:59.999Z` as `end_date` — there is no separate boolean column for "perpetual" |
| `reference_no` | `String? @db.VarChar` | Yes | Free-text purchase-order reference |
| `note` | `String?` | Yes | Free-text — also used by data migrations to record where a backfilled row's numbers came from |
| `cancelled_at` | `DateTime? @db.Timestamptz(6)` | Yes | Added by `20260901020000_cluster_license_cancel`. Non-null means this licence has been cancelled: it stays in the ledger and stays visible, but stops granting quota from that moment. **There is no un-cancel** — restoring coverage means issuing a new licence |
| `cancelled_by_id` | `String? @db.Uuid` | Yes | Actor who cancelled it |
| `cancel_reason` | `String?` | Yes | Optional free-text reason |
| `doc_version` | `Int` | No | Default `0`; optimistic-lock counter, required on `PATCH` and on `cancel` |
| audit trio + soft delete | — | Yes | Standard `created_at`/`created_by_id`/`updated_at`/`updated_by_id`/`deleted_at`/`deleted_by_id` |

**Constraints:** `CHECK (licensed_bus >= 0)`, `CHECK (end_date > start_date)`, FK `cluster_id → tb_cluster.id` (`NoAction`/`NoAction`).
**Indexes:** `(cluster_id, deleted_at)`, `(end_date)`, `(cluster_id, cancelled_at)` (added with the cancel columns — a cancelled licence never wins again, so the winning-row query can skip it entirely via this index).

Overlapping date ranges across rows are expected, not an error — buying extra quota mid-contract is a new row whose range overlaps an existing one (backend Swagger states this explicitly on the create/list endpoints).

### 2.2 `tb_business_unit_license` — seat purchase ledger

Same shape, one level down. Schema line 1133.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `license_number` | `String @db.VarChar` | No | Server-issued `SEAT-YYMM-####`; same partial-unique-index caveat as §2.1 |
| `business_unit_id` | `String @db.Uuid` | No | FK to `tb_business_unit.id` — the owner |
| `licensed_users` | `Int` | No | The seat count this licence grants; `CHECK (licensed_users >= 0)` |
| `start_date` / `end_date` | `DateTime @db.Timestamptz(6)` | No | Coverage window; `CHECK (end_date > start_date)`. **This table has no "no expiry" convention in the SPA** — `LicensePurchaseForm`'s no-expiry toggle is not offered for the seat kind (`SEAT_CONFIG.showNoExpiry: false`) |
| `reference_no` | `String? @db.VarChar` | Yes | Free-text purchase-order reference |
| `note` | `String?` | Yes | Free-text; a migrated placeholder row's note is prefixed `"migrated"`, which the SPA reads back to render an "end date required" warning badge |
| `doc_version` | `Int` | No | Default `0` |
| audit trio + soft delete | — | Yes | Standard |

**Constraints:** `CHECK (licensed_users >= 0)`, `CHECK (end_date > start_date)`, FK `business_unit_id → tb_business_unit.id`.
**Indexes:** `(business_unit_id, deleted_at)`, `(end_date)`.

**No `cancelled_at`/`cancelled_by_id`/`cancel_reason` columns exist on this table at all.** A seat licence can be edited or hard-deleted (`DELETE`), but never cancelled — there is no cancel endpoint on either the frontend service or the backend controller for this table. This is a genuine capability gap between the two purchase kinds, not an oversight this page is flagging as a bug: `licenseKindConfig.ts`'s own doc-comment states the reason directly — `cancel` is typed `null` for `SEAT_CONFIG` because reading it through a union with `ClusterLicenseConfig`'s real `cancel` function would fail type-checking, and casting past that would hide a call that fails at runtime.

### 2.3 `tb_subscription` and its feature-group joins

`tb_subscription` (schema line 452) is the contract header: `cluster_id`, `subscription_number` (server-issued `SUB-YYMM-####`), `start_date`/`end_date`, `status` (`enum_subscription_status`, line 723: `active` / `inactive` / `expired`), `doc_version`, audit trio, soft delete. `@@unique([cluster_id, subscription_number, deleted_at])`.

Since migration `20260821130000_subscription_one_bu`, a subscription binds to **exactly one** business unit via `tb_subscription_bu` (schema line 1257: `subscription_id`, `business_unit_id`, `doc_version`, audit trio, soft delete; `@@unique([subscription_id, business_unit_id, deleted_at])`) — the BU cannot be changed after creation (`SubscriptionForm`'s `business_unit_id` field is only ever writable on the create form). That join row's own child, `tb_subscription_bu_group` (schema line 1336: `subscription_bu_id`, `group_id → tb_license_feature_group.id`, doc_version, audit trio, soft delete; `@@unique([subscription_bu_id, group_id, deleted_at])`), is where the actual feature-group entitlements live — this is what `PUT /subscriptions/:id/groups` replaces wholesale on every save. A prior schema generation instead joined subscriptions directly to individual features (dropped by `20260901000000_drop_subscription_bu_feature`); that table no longer exists, and this module's UI has no equivalent per-feature picker any more (§3.2 of the [landing page](/en/platform/licenses)).

`tb_license_feature_group` (schema line 1284: `code`, `name`, `description`, `sort_order`, `is_active`, doc_version, audit trio, soft delete) and `tb_license_feature` (schema line 1214) are owned and documented by [License Catalog](/en/platform/license-catalog) — this page lists them only to show what `tb_subscription_bu_group.group_id` points at.

## 3. Views — the two capacity views, and why there are two

Both are defined in `20260822000000_add_cluster_license/migration.sql` (`v_cluster_bu_cap` line 36, `v_cluster_bu_quota` line 55) and amended by `20260824000000_add_cap_end_date_to_view` (adds `cap_end_date`) and `20260901020000_cluster_license_cancel` (adds `cancelled_at IS NULL` to the winning-row filter, plus a `winning_license_id` column). They answer **different questions at different grains**, and a page that cites the wrong one for a claim will be wrong in a way that looks plausible:

### 3.1 `v_cluster_bu_cap` — one row per **cluster**

```sql
SELECT c.id AS cluster_id,
       COALESCE(w.licensed_bus, 0)::int AS cap,
       w.end_date                       AS cap_end_date,
       w.id                             AS winning_license_id
FROM tb_cluster c
LEFT JOIN LATERAL (
  SELECT l.id, l.licensed_bus, l.end_date
  FROM tb_cluster_license l
  WHERE l.cluster_id = c.id
    AND l.deleted_at IS NULL
    AND l.cancelled_at IS NULL
    AND l.start_date <= now()
    AND l.end_date > now()
  ORDER BY l.start_date DESC, l.created_at DESC, l.id DESC
  LIMIT 1
) w ON true
WHERE c.deleted_at IS NULL;
```

Every live cluster gets exactly one row, even one with zero business units and even one with no licence at all (`cap = 0` via `COALESCE`). The `LATERAL` join picks the single **winning** licence covering `now()` — both `deleted_at` and (since 2026-09-01) `cancelled_at` must be `NULL`, and among the survivors the newest `start_date` wins (ties broken by `created_at`, then `id`). This is the *cluster-level* fact: "how many BUs may this cluster have right now, and until when." The frontend's `activeLicense()` (`utils/clusterLicense.ts`) reimplements this exact tie-break order client-side for pages that only hold the licence list, not this view's output.

### 3.2 `v_cluster_bu_quota` — one row per **business unit**

```sql
SELECT b.id         AS business_unit_id,
       b.cluster_id AS cluster_id,
       ROW_NUMBER() OVER (
         PARTITION BY b.cluster_id
         ORDER BY COALESCE(b.is_hq, false) DESC, b.created_at ASC, b.id ASC
       )::int       AS rank,
       q.cap        AS cap
FROM tb_business_unit b
JOIN v_cluster_bu_cap q ON q.cluster_id = b.cluster_id
WHERE b.deleted_at IS NULL;
```

This is a **different grain entirely**: one row per business unit, not per cluster. It joins `v_cluster_bu_cap` to **borrow** the cap — it never recomputes the winning-licence rule itself — and ranks every live BU within its cluster (HQ first, then oldest-created, then `id`). A BU whose `rank` exceeds its cluster's borrowed `cap` is **over the purchased limit**; this is exactly what the SPA's "Over limit" badge (`utils/businessUnitRank.ts`'s `rankBusinessUnits()`/`countOverLimit()`, used by [Clusters](/en/platform/clusters)' Business Units tab and this module's `BuQuotaSection`) must match rank-for-rank, since a badge that disagrees with which BU actually gets rejected at creation time is worse than no badge. The rank formula is duplicated client-side (rather than read from this view directly) because the SPA needs it against a BU list it already has loaded for other reasons — but it is documented in the source as required to match this view's `ORDER BY` exactly, field for field.

**Why two views instead of one:** `v_cluster_bu_cap` answers "what's the cluster's quota" (one number, needed by the cluster's own screens and by the health strip on `ClusterLicenseDetail`); `v_cluster_bu_quota` answers "is *this specific BU* within that quota" (one row per BU, needed by any screen that lists business units and wants to flag the ones over the line). Folding both into one view would force every BU-listing query to also carry cluster-quota columns it does not need, and every cluster-quota query to join through every BU it does not care about individually.

### 3.3 `v_business_unit_seat` — one row per **business unit**, summed

Defined in `20260819000000_bu_user_license/migration.sql`, alongside `tb_business_unit_license` itself:

```sql
SELECT bu.id         AS business_unit_id,
       bu.cluster_id AS cluster_id,
       coalesce(sum(l.licensed_users) FILTER (
         WHERE l.deleted_at IS NULL
           AND now() >= l.start_date
           AND now() <= l.end_date
       ), 0)::int AS licensed_users
  FROM "tb_business_unit" bu
  LEFT JOIN "tb_business_unit_license" l ON l.business_unit_id = bu.id
 WHERE bu.is_active = true
   AND bu.deleted_at IS NULL
 GROUP BY bu.id, bu.cluster_id;
```

Unlike either cluster view above, this one **sums** every currently-active row rather than picking a winner — matching the SPA's `sumActiveLicenses()` (§3.1 of the [landing page](/en/platform/licenses)). Two nuances worth a tester's attention: the coverage test is `now() BETWEEN start_date AND end_date` inclusive on both ends (not the exclusive-end convention `tb_cluster_license`'s winning-row query uses), and the view filters `bu.is_active = true` — a deactivated business unit's seat total disappears from this view entirely, even if its licence rows are still live and unexpired. `now()` here means `transaction_timestamp()`, deliberately, so a single request's seat pool/used/already-invited numbers all come from one consistent snapshot.

## 4. Relationships

```
tb_cluster_license.cluster_id            ──>  tb_cluster.id
tb_business_unit_license.business_unit_id ──>  tb_business_unit.id
tb_subscription.cluster_id                ──>  tb_cluster.id
tb_subscription_bu.subscription_id        ──>  tb_subscription.id
tb_subscription_bu.business_unit_id       ──>  tb_business_unit.id
tb_subscription_bu_group.subscription_bu_id ──>  tb_subscription_bu.id
tb_subscription_bu_group.group_id         ──>  tb_license_feature_group.id
*.created_by_id / *.updated_by_id / *.cancelled_by_id / *.deleted_by_id  ──>  tb_user.id  (audit actors)
```

`v_cluster_bu_cap` reads only `tb_cluster` and `tb_cluster_license`. `v_cluster_bu_quota` additionally reads `tb_business_unit`, joined through `v_cluster_bu_cap` rather than `tb_cluster_license` directly (§3.2). `v_business_unit_seat` reads only `tb_business_unit` and `tb_business_unit_license`. None of the three purchase/contract tables in §2 has a foreign key to any of the others — a cluster's BU quota, a BU's seat pool, and a BU's subscription contract are three independent purchase records that happen to be browsed together on this module's screens.

## 5. Enums

`enum_subscription_status` (`active` / `inactive` / `expired`) is the only enum this module defines, and it is **not** the same thing as the `state` a caller actually sees. The backend derives a display `state` (`SubscriptionState`) from `status` plus the current time via a single shared function, `deriveSubscriptionState()` (`packages/prisma-shared-schema-platform/src/index.ts`), used identically by the gateway and by `micro-business`:

```
inactive status  → state = 'inactive'   (unconditional)
expired  status  → state = 'expired'    (unconditional)
active   status  → state = 'expired' if end_date < now, else 'active'
```

The SPA is explicitly told never to recompute this itself (`src/utils/subscriptionState.ts`'s own doc-comment cites the Swagger note: "the frontend must not recompute this — use this field directly") — it only derives the separate, non-enum "expiring soon" flag from `state` plus a threshold (§6). `tb_cluster_license` and `tb_business_unit_license` have no status column at all; their status (`active`/`scheduled`/`expired`/`superseded`/`cancelled`) is computed entirely client-side from dates and, for BU quota, from `cancelled_at` and the winning-row comparison (`licenseStatus()`/`statusMap()` in `utils/clusterLicense.ts` and `utils/buLicense.ts`).

## 6. Expiry Thresholds

Three independent, backend-configurable day-counts decide when this module's screens paint an "expiring soon" warning — a value a tester cannot infer from the screen alone, since the same "expires in 12 days" fact reads as urgent at a 30-day threshold and unremarkable at a 7-day one.

| Field (`ExpiryThresholdsConfig`) | Governs | Default |
|---|---|---|
| `subscription_days` | `SubscriptionSection`'s expiring-soon count, `SubscriptionTable`'s per-row badge, `IssuedSubscriptionPlate` | 30 |
| `bu_quota_days` | `BuQuotaSection`, `ClusterLicenseTable`'s "Quota Expires" badge, `IssuedLicensePlate` (BU-quota mode), `LicenseHealthStrip` | 30 |
| `seat_days` | `SeatSection`'s per-row and per-BU earliest-expiry badge, `IssuedLicensePlate` (seat mode) | 30 |

**Source and delivery:** `GET /api-system/platform/expiry-thresholds` (`expiryThresholdService.getAll()`) is deliberately **open to any authenticated user with no permission check** — unlike `platformConfigService.getAll()`, which requires `platform_config.read`. The comment in `expiryThresholdService.ts` states the reason directly: gating this endpoint the same way would 403 every ordinary user who opens `/licenses`, silently pinning them to the in-code default forever regardless of what an administrator actually configured. The three values are stored as one JSON object under a `platform_config` key (edited from the [Platform Config](/en/platform/platform-config) module's Expiry Thresholds card, gated there by `platform_config.manage` alone — **not** `license.manage`, a different key entirely that gates an unrelated License Enforcement toggle on that same screen; see the correction in [Permissions](/en/platform/licenses/permissions) §1) and served through `ExpiryThresholdContext`, which merges the backend response onto `DEFAULT_EXPIRY_THRESHOLDS` **field by field** — a backend that has not yet learned a new field cannot turn it into `undefined` and silently break every comparison against it (an `undefined` operand makes every `<=` comparison `false`, which would make the warning badge vanish system-wide with no visible error). A fetch failure (including "not logged in yet") falls back silently to the in-code defaults (all three `30`) with no toast — the page still works, only the badge window reverts to the old value.

**Effect per ledger, precisely:**
- **Subscription:** `isExpiringSoon(state, endDate, days)` — `true` only when the backend-computed `state` is `'active'` **and** `daysLeft <= days`. An `'inactive'` or already-`'expired'` state never reads as "expiring soon."
- **BU quota:** `isExpiringSoon(lic, days)` — `false` unconditionally for a perpetual licence (`end_date >= 2099-01-01`) and for anything not currently `'active'` per `licenseStatus()` (a cancelled or superseded row is never "expiring," it is already inert).
- **Seat:** `isExpiringSoon(lic, days)` — `false` for anything not currently `'active'`; seats have no perpetual concept at all (§2.2), so every active seat licence is eligible to eventually warn.

## 7. Divergences from carmen-platform SPA shape

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `LicenseKindConfig.readUsage` returning `undefined` | `licenseKindConfig.ts` | n/a | `undefined` means "unknown" (fetch not attempted or failed); the seat kind's `readUsage` is `null` outright, meaning the concept does not apply. Callers must never coerce either to `0` — a seat licence has no owner-usage divisor at all, and a BU-quota licence whose usage read failed is not the same fact as a cluster that has used zero BUs |
| `ClusterLicense.is_in_force` | `utils/clusterLicense.ts` `statusMap()` | not stored — computed by `v_cluster_bu_cap`'s `winning_license_id` on the list/detail endpoints that join it | Trusted ahead of the client's own `activeLicense()` tie-break whenever present; the client formula exists only as a fallback for the one load path (`GET .../licenses` per-cluster) whose DTO predates this field |
| `FleetLicenseRow` (the fleet-wide `PurchaseLicenseTable` row shape) has no `updated_at` | `PurchaseLicenseTable.tsx` | Neither `BusinessUnitLicenseListRowDto` nor `ClusterLicenseListRowDto` sends it | Not a bug to fix — both fleet-list DTOs simply never project `updated_at`, so the table's CSV export and its single audit column show Created only, never Updated, for this one screen |
| `group_ids` / `feature_keys` on `SubscriptionDetail.bu` | `SubscriptionForm.tsx` `load()` | `tb_subscription_bu_group` (join) / server-computed flattening | `group_ids` is read as optional and defaulted to `[]` — a contract created before the group system existed carries `feature_keys` with no `group_ids`, and the SPA must not crash reading a field that plan-migration-era rows never had |
| `ExpiryThresholdsConfig` merge | `ExpiryThresholdContext.tsx` | one JSON value on a `platform_config` row (owned by [Platform Config](/en/platform/platform-config)) | Merged per field onto in-code defaults, not replaced wholesale (§6) |

## 8. References

REST surface consumed by this module's services:

| Method + Path | Purpose | Notes |
|---|---|---|
| `GET /api-system/clusters/:clusterId/licenses` | List one cluster's BU-quota licences | No `@RequirePlatformPermission` — scope-authorized inside `micro-cluster` |
| `GET /api-system/platform/cluster-licenses` | Fleet-wide BU-quota licence list, paginated | No `@RequirePlatformPermission`; scope-filtered per caller |
| `GET /api-system/platform/cluster-licenses/:id` | One BU-quota licence by bare id | Fails **403** (not 404) when outside the caller's readable cluster scope |
| `POST/PATCH/DELETE /api-system/clusters/:clusterId/licenses[/:id]` | Create/update/soft-delete a BU-quota licence | All three require `subscription.manage` |
| `POST /api-system/clusters/:clusterId/licenses/:id/cancel` | Cancel a BU-quota licence | Requires `subscription.manage`; irreversible; `doc_version` required |
| `GET /api-system/business-units/:buId/licenses` | List one BU's seat licences | No `@RequirePlatformPermission` |
| `GET /api-system/platform/business-unit-licenses[/:id]` | Fleet-wide seat licence list / one by bare id | Same scope rules as the cluster-licence fleet routes |
| `POST/PATCH/DELETE /api-system/business-units/:buId/licenses[/:id]` | Create/update/soft-delete a seat licence | All three require `subscription.manage`; **no cancel route exists for seats** |
| `GET/POST/PATCH/DELETE /api-system/platform/subscriptions[/:id]` | Subscription CRUD | `GET` requires `subscription.read`; write verbs require `subscription.manage` |
| `PUT /api-system/platform/subscriptions/:id/groups` | Replace a subscription's feature-group set | Requires `subscription.manage`; full desired set, not a delta |
| `GET /api-system/platform/subscriptions/summary` | Unfiltered fleet-wide subscription counts | Requires `subscription.read`; independent of the current list filter |
| `GET /api-system/platform/license-features` | Feature catalog (read-only, for the SPA's group-expansion display) | Owned by [License Catalog](/en/platform/license-catalog) |
| `GET /api-system/platform/expiry-thresholds` | The three configurable day-counts (§6) | No permission required |

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_subscription` (452), `enum_subscription_status` (723), `tb_business_unit_license` (1133), `tb_cluster_license` (1168), `tb_license_feature` (1214), `tb_subscription_bu` (1257), `tb_license_feature_group` (1284), `tb_subscription_bu_group` (1336).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260819000000_bu_user_license/migration.sql` — `tb_business_unit_license`, `v_business_unit_seat`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql` (lines 36, 55), `20260824000000_add_cap_end_date_to_view/migration.sql`, `20260901020000_cluster_license_cancel/migration.sql` — `tb_cluster_license`, `v_cluster_bu_cap`, `v_cluster_bu_quota`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260821130000_subscription_one_bu/migration.sql`, `20260831000000_subscription_bu_group/migration.sql`, `20260901000000_drop_subscription_bu_feature/migration.sql` — the one-BU-per-subscription model and the feature→group migration for entitlements.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/src/index.ts` — `deriveSubscriptionState()`, the single shared `state`-derivation function (§5).

**Secondary (consumer shape):**
- `../carmen-platform/src/pages/licenses/licenseKindConfig.ts` — `SEAT_CONFIG`/`BU_QUOTA_CONFIG`.
- `../carmen-platform/src/utils/clusterLicense.ts`, `src/utils/buLicense.ts`, `src/utils/subscriptionState.ts` — the three independent status/expiry-soon formulas.
- `../carmen-platform/src/utils/businessUnitRank.ts` — `rankBusinessUnits()`/`countOverLimit()`, must match `v_cluster_bu_quota`'s `ORDER BY` exactly.
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx`, `src/services/expiryThresholdService.ts` — threshold delivery (§6).
- `../carmen-platform/src/types/index.ts` — `ClusterLicense`, `BusinessUnitLicense`, `Subscription`, `SubscriptionDetail`, `ExpiryThresholdsConfig`.

**Cross-links:** [Licenses landing](/en/platform/licenses) &nbsp;·&nbsp; [UI Screens](/en/platform/licenses/ui-screens) &nbsp;·&nbsp; [Permissions](/en/platform/licenses/permissions) &nbsp;·&nbsp; [License Catalog](/en/platform/license-catalog) &nbsp;·&nbsp; [Platform Config](/en/platform/platform-config)
