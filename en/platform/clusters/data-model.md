---
title: Cluster — Data Model
description: Cluster entity, relationships to BUs and users, and the licence-ledger model that replaced the static max_license_bu/max_license_users caps.
published: true
date: 2026-09-05T04:42:43.000Z
tags: book/platform, clusters, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Data Model

> **At a Glance**
> **Tables:** `tb_cluster` (primary) &nbsp;·&nbsp; `tb_cluster_user` (M:N user-join, full doc in [users](/en/platform/users)) &nbsp;·&nbsp; `tb_business_unit` (`cluster_id` FK side, full doc in [business-units](/en/platform/business-units)) &nbsp;·&nbsp; `tb_cluster_license` (cluster's own BU-quota purchase ledger — new) &nbsp;·&nbsp; **Enums:** `enum_cluster_user_role` (admin/user) &nbsp;·&nbsp; **Branding:** `logo_file_token` / `avatar_file_token` columns, resolved to embedded presigned `logo`/`avatar` objects in API responses &nbsp;·&nbsp; **Audit columns:** standard `created_*`/`updated_*`/`deleted_*` trio on `tb_cluster`, surfaced as a nested `audit` object by the API &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` on `tb_cluster` and `tb_cluster_user`, enforced as an optimistic lock on `PUT` &nbsp;·&nbsp; **BU quota is no longer a static field.** `tb_cluster.max_license_bu` is gone; BU quota now comes from `tb_cluster_license`, a dated purchase ledger whose *winning* row (via view `v_cluster_bu_cap`) sets the effective cap — see §2.4.

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative. The full licensing/quota ledger (`tb_cluster_license`, `tb_business_unit_license`, `tb_subscription`, `tb_license_feature`, and their views) is the domain of the **licenses** module — this page documents only the cluster-side shape of that ledger; see [licenses](/en/platform/licenses) for the full model once that page exists.

## 1. Overview

`tb_cluster` is the top-level tenant container in the Carmen Platform. Every business unit and every cluster-scoped user membership hangs beneath a cluster row. Clusters represent a licensable grouping of business units — typically one hotel brand, hotel group, or company entity.

**Licensing was reworked between 2026-07-29 and 2026-09-04** (Tasks 2–13 of the licensing feature, `../carmen-platform` history). Two static caps that earlier revisions of this page documented as columns on `tb_cluster`/`tb_business_unit` **no longer exist**:

- `tb_cluster.max_license_bu` (`Int?`, capped how many BUs a cluster could have) — removed from the Prisma model. The last SPA code that read it was deleted by commit `7fda015` ("ลบโค้ดที่อ่าน max_license_bu ที่เหลือทั้งหมด", Task 13). The cluster's `code`/`name`/`alias_name`/`is_active`/`info`/`doc_version`/audit-trio fields are unaffected.
- `tb_business_unit.max_license_users` (`Int?`, capped how many `tb_cluster_user` rows could name that BU as `parent_bu_id`) — column **physically dropped** from the database by migration `20260821000000_drop_bu_max_license_users` (backfilled from `tb_business_unit_license` first; one cluster's stale value, CARMEN-FIFO's 30, was deliberately discarded per the migration's own note — it had never been enforced since the seat pool moved to the view).

In their place, both caps are now the *effective* row of a dated purchase ledger:

- **BU quota** — `tb_cluster_license` (§2.4): a cluster's BU-quota purchases over time. The quota in effect right now is the single **winning row** (current date falls in `[start_date, end_date]`, not cancelled), resolved by the view `v_cluster_bu_cap` — not a sum of every row. `0` (no winning row) is a real zero, never "unlimited".
- **User seats** — `tb_business_unit_license` (§2.5): a per-BU ledger of seat purchases, summed across all of a cluster's BUs currently in effect via the view `v_business_unit_seat` to produce the cluster's aggregate seat cap (`total_max_license_users` in the SPA's `Cluster` read shape). `null`/absent still means "uncapped" for this dimension — the seat pool did **not** adopt the BU-quota ledger's "0 = zero" convention (see the file-header comment in `../carmen-platform/src/utils/capacity.ts`).

**`tb_cluster_user.parent_bu_id` is also gone.** The column does not appear in the current Prisma `tb_cluster_user` model at all (confirmed absent by grep across `schema.prisma`), matching the SPA's removal of the field from the Users tab UI (`../carmen-platform` commit `1fbaf35`, "ถอด UI ของ parent_bu_id ออกจากหน้า Cluster Edit"). A cluster-user membership no longer names a "billing-owner BU" — see §2.2.

All audit and soft-delete lifecycle fields still follow the same `created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id` pattern used across every table in the platform schema. A cluster row with a non-null `deleted_at` is soft-deleted; its child BUs and cluster-user memberships are not automatically soft-deleted by a database cascade (all FK relations use `onDelete: NoAction`), so application-layer logic is responsible for cascading soft-deletes where required.

`tb_cluster` also owns a `tb_subscription` 1:M relation (billing subscription rows; one subscription binds to exactly one BU as of `../carmen-platform` commit `6626514`, "หน้าสัญญาเป็น 1 ใบ = 1 BU") — out of scope for this page, documented under the licenses module. The `info` field (`Json? @db.Json`) is a free-form metadata blob reserved for future extensibility; it is present in the Prisma model and exposed in the `Cluster` TS interface but has no currently documented key structure.

## 2. Entities

### 2.1 `tb_cluster`

The primary cluster record. One row per tenant cluster, holding the identity fields used throughout the Platform SPA (`code`, `name`, `alias_name`), the branding file tokens (`logo_file_token`, `avatar_file_token`), and the full audit/soft-delete trio. It no longer holds a licence cap column of its own — see §1.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `code` | `String @db.VarChar(30)` | No | — | Short identifier for the cluster; unique with `name` and `deleted_at` |
| `name` | `String @db.VarChar` | No | — | Full display name of the cluster |
| `alias_name` | `String? @db.VarChar(3)` | Yes | — | 3-character maximum alias (unusually tight `VarChar(3)` cap — tighter than any other varchar in this schema). Shown in compact UI surfaces where the full `name` does not fit, e.g. the cluster plate's identifier row and the CSV export "Alias" column |
| `logo_file_token` | `String? @db.VarChar` | Yes | — | File-storage token for the cluster's rectangular logo. Never exposed raw to the SPA — the API resolves it to an embedded presigned `logo` object (see §5) |
| `avatar_file_token` | `String? @db.VarChar` | Yes | — | File-storage token for the cluster's square avatar. Same resolution path as the logo (embedded presigned `avatar` object). `tb_business_unit` carries the identical token pair |
| `is_active` | `Boolean?` | Yes | `true` | When `false`, the cluster and its BUs are considered inactive |
| `info` | `Json? @db.Json` | Yes | — | Free-form metadata blob; reserved for future extensibility |
| `doc_version` | `Int` | No | `0` | Optimistic-concurrency token, added platform-wide (35 tables, incl. `tb_cluster` and `tb_cluster_user`) on 2026-07-16. The SPA reads it on load and resends it with every `PUT /api-system/clusters/:id`; a stale write is rejected with `409` and the edit page reloads the record and shows a "changed by someone else" toast instead of overwriting silently |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: row creation time |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the creator |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: last update time |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the last updater |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Soft-delete timestamp; `NULL` = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the deleter |

**Constraints:**
- `@id` on `id`
- `@@unique([code, name, deleted_at])` — map `"cluster_code_name_deleted_at_u"` — allows code/name reuse after soft delete; a cluster with a given `code`+`name` pair can be recreated after soft-delete without a uniqueness violation
- FK: `created_by_id` → `tb_user.id` (NoAction / NoAction) — Prisma named relation `"tb_cluster_created_by_idTotb_user"`
- FK: `updated_by_id` → `tb_user.id` (NoAction / NoAction) — Prisma named relation `"tb_cluster_updated_by_idTotb_user"`
- `deleted_by_id` — stored as `String? @db.Uuid` by convention, matching the deleter's `tb_user.id`; no Prisma `@relation` directive (FK not enforced at DB level for the delete path, consistent with the pattern used on `tb_cluster_user` and `tb_business_unit`)

**Indexes:**
- No explicit `@@index` declarations beyond the unique constraint above. The unique constraint on `[code, name, deleted_at]` covers the primary lookup path. Additional indexes on `id` (primary key) are created automatically by PostgreSQL.

### 2.2 `tb_cluster_user` (cluster-side view)

The full field table for `tb_cluster_user` is documented in [users data-model](/en/platform/users/data-model) (§2.2). From the cluster perspective, the key points are:

- **`cluster_id` FK** — `String @db.Uuid` (non-nullable), FK to `tb_cluster.id` with `onDelete: NoAction, onUpdate: NoAction`. Deleting or soft-deleting a cluster does not automatically remove join rows; application code must handle cascading cleanup.
- **`role`** — `enum_cluster_user_role` (non-nullable, default `user`). Records the per-cluster role for this user-cluster relationship: `admin` or `user`. This role is completely independent of the platform RBAC model ([rbac](/en/platform/rbac)) that gates the admin SPA — a user may hold cluster `admin` rights on one cluster while holding `user` rights on another, regardless of which `cluster.*` permission keys (if any) their platform role assignments grant.
- **No `parent_bu_id` any more.** The field does not exist on the current `tb_cluster_user` model — grep across `schema.prisma` returns no match. A cluster-user membership is scoped to the cluster as a whole; there is no per-membership "billing-owner BU" pointer, and the Users tab's table and Add-User dialog carry no Business Unit column/field (see [UI Screens](/en/platform/clusters/ui-screens) §4).
- **`is_active`** — `Boolean?` (default `true`). Soft-activity flag for the membership; a user may be deactivated within a cluster without soft-deleting the row.
- **Unique constraint** — `@@unique([user_id, cluster_id, deleted_at])` — allows a user to be re-added to a cluster after the original membership is soft-deleted, without a unique-key collision.
- **`doc_version`** — `Int @default(0)`, same optimistic-lock counter as `tb_cluster` (§2.1). The Users tab's inline Role edit (`PUT /api-system/user/clusters/:clusterUserId`) still does not send it — only the cluster-level `PUT` on `ClusterEdit`'s Save Changes bar attaches `doc_version`.

For the complete field table, all audit columns, and the user-side relationship view, see [users](/en/platform/users) and [users data-model](/en/platform/users/data-model).

### 2.3 `tb_business_unit` (cluster_id FK side)

The full field table for `tb_business_unit` is documented in [business-units data-model](/en/platform/business-units/data-model). From the cluster perspective, the key points are:

- **`cluster_id` FK** — `String @db.Uuid` (non-nullable), FK to `tb_cluster.id` with `onDelete: NoAction, onUpdate: NoAction`. This establishes the 1:M cluster→BU relationship. A BU belongs to exactly one cluster and cannot be moved between clusters without a data migration.
- **`max_license_users` is gone.** Dropped by migration `20260821000000_drop_bu_max_license_users` (2026-08-21) after seat data was backfilled into `tb_business_unit_license` (§2.5). The per-BU seat cap this column used to hold is now derived from that ledger via the view `v_business_unit_seat`, aggregated to the cluster level as `total_max_license_users` in the SPA's read shape (§5). Because there is no longer a per-BU cap column, the Business Units tab's table on `ClusterEdit` no longer shows a per-row seat/user meter at all — see [UI Screens](/en/platform/clusters/ui-screens) §4.2.
- **BU-quota interaction** — a cluster's BU quota (from `tb_cluster_license`, §2.4) caps how many live (non-soft-deleted) `tb_business_unit` rows may exist for that `cluster_id`. Enforcement of "which BU is over the line" once the count exceeds quota is a **ranking**, not a hard block: BUs are ordered `COALESCE(is_hq, false) DESC, created_at ASC, id ASC` (matching the view `v_cluster_bu_quota` exactly — see `../carmen-platform/src/utils/businessUnitRank.ts`), and any BU whose rank exceeds the quota is flagged "Over limit" in the Business Units tab. Creating a *new* BU is still blocked outright once `businessUnits.length >= bu_cap` (the Add button disables).
- **Unique constraint on `tb_business_unit`** — `@@unique([cluster_id, code, deleted_at])` — ensures that BU codes are unique within a cluster among live rows, but allows code reuse after soft delete.

### 2.4 `tb_cluster_license` — the cluster's BU-quota ledger

New table (added as part of the licensing rework). One row per BU-quota purchase for a cluster; the *effective* quota is the single winning row, never a sum.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `license_number` | `String @db.VarChar` | No | System-issued number, format `BUQ-YYMM-####`; immutable after creation. Uniqueness is enforced only by a partial SQL index (`WHERE deleted_at IS NULL`) not expressible as a Prisma `@@unique` |
| `cluster_id` | `String @db.Uuid` | No | FK to `tb_cluster.id` |
| `licensed_bus` | `Int @db.Integer` | No | The BU quota this licence row grants |
| `start_date` / `end_date` | `DateTime @db.Timestamptz(6)` | No | Coverage window. A perpetual licence uses a sentinel end date (year 2099) rather than `NULL` — the SPA's `isPerpetual()` helper (`../carmen-platform/src/utils/clusterLicense.ts`) hides that sentinel from the UI (shows "No expiry") |
| `reference_no` / `note` | `String?` | Yes | Free-text reference and note fields |
| `cancelled_at` / `cancelled_by_id` / `cancel_reason` | `DateTime?` / `String? @db.Uuid` / `String?` | Yes | Cancellation is distinct from soft delete: a cancelled row still appears in the ledger and CSV/UI history but can never again be the winning row (the view `v_cluster_bu_cap`, added by migration `20260901020000_cluster_license_cancel`, filters `cancelled_at IS NULL`). There is no uncancel endpoint — cancelling the wrong row means issuing a new one |
| `doc_version` | `Int @default(0)` | No | Same optimistic-lock convention as every other platform table |
| Audit trio | — | — | `created_at`/`created_by_id`, `updated_at`/`updated_by_id`; no `deleted_by_id` on this model |

FK: `tb_cluster_license.cluster_id` → `tb_cluster.id` (`onDelete: NoAction, onUpdate: NoAction`). Indexes on `[cluster_id, deleted_at]`, `[end_date]`, `[cluster_id, cancelled_at]`.

**Two views, two jobs — do not conflate them.** Both are created by migration `20260822000000_add_cluster_license` (`v_cluster_bu_cap` later `CREATE OR REPLACE`d, unchanged column signature, by `20260901020000_cluster_license_cancel` to add the cancellation filter):

- **`v_cluster_bu_cap`** — one row **per cluster** (`cluster_id`, `cap`). Picks the single winning `tb_cluster_license` row via a `LEFT JOIN LATERAL` (`deleted_at IS NULL AND cancelled_at IS NULL AND start_date <= now() AND end_date > now()`, tie-broken `start_date DESC, created_at DESC, id DESC`) and returns its `licensed_bus`, `COALESCE`d to `0` when no row wins. **This is the view that computes the effective quota** — its result becomes `bu_cap`/`bu_cap_end_date` on every SPA surface that reads a cluster (list, plate, CSV export), and it is what the Fleet Capacity band's "Quota expiring" filter resolves against (see [UI Screens](/en/platform/clusters/ui-screens) §2.1a).
- **`v_cluster_bu_quota`** — one row **per business unit** (`business_unit_id`, `cluster_id`, `rank`, `cap`). Joins `tb_business_unit` to `v_cluster_bu_cap` and computes each BU's 1-based rank within its cluster (`ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY COALESCE(is_hq, false) DESC, created_at ASC, id ASC)`) — it **borrows** the cap from `v_cluster_bu_cap` rather than recomputing it, and does not filter on `is_active` (an inactive BU still consumes quota and still gets a rank). **This is the view the "Over limit" ranking badge matches** (`../carmen-platform/src/utils/businessUnitRank.ts`, §2.3 above and [UI Screens](/en/platform/clusters/ui-screens) §4.3) — it is not the source of `bu_cap` itself.

No winning row in `v_cluster_bu_cap` ⇒ `bu_cap = 0` — a real zero, never "unlimited", unlike the seat dimension in §2.5. This page documents only the cluster-side shape of the ledger; the full purchase/cancel/edit UI lives in the **licenses** module (License Center, `/licenses/:clusterId`) — out of scope here, cross-linked from [UI Screens](/en/platform/clusters/ui-screens) §3.

### 2.5 `tb_business_unit_license` — the per-BU seat ledger (cross-reference only)

Also new, and also outside this module's scope to document in full (it belongs to **licenses**), but it is the reason `tb_business_unit.max_license_users` no longer exists: one row per BU seat-quota purchase (`license_number` format `SEAT-YYMM-####`, `business_unit_id` FK, `licensed_users Int`, `start_date`/`end_date`). Unlike the cluster-quota ledger, seats **sum**: every row currently in effect (via view `v_business_unit_seat`) for every BU in a cluster adds to that cluster's aggregate seat cap. `null`/no covering rows still means "uncapped" for this dimension.

## 3. Relationships

```
tb_cluster  1 ─── M  tb_business_unit          (via tb_business_unit.cluster_id)
tb_cluster  1 ─── M  tb_cluster_user  M ─── 1  tb_user
tb_cluster  1 ─── M  tb_cluster_license         (BU-quota purchase ledger)
tb_cluster  1 ─── M  tb_subscription            (billing rows; 1 subscription : 1 BU as of 2026-08-21)
tb_business_unit  1 ─── M  tb_business_unit_license  (per-BU seat purchase ledger)
tb_cluster  self-FK  created_by_id, updated_by_id  → tb_user.id  (audit relations)
```

FK directions (all `onDelete: NoAction, onUpdate: NoAction` unless noted):

- `tb_business_unit.cluster_id` → `tb_cluster.id`
- `tb_cluster_user.cluster_id` → `tb_cluster.id`
- `tb_cluster_license.cluster_id` → `tb_cluster.id`
- `tb_business_unit_license.business_unit_id` → `tb_business_unit.id`
- `tb_subscription.cluster_id` → `tb_cluster.id` (subscription rows reference the cluster; each also binds to exactly one BU via `tb_subscription_bu`)
- `tb_cluster.created_by_id` → `tb_user.id`
- `tb_cluster.updated_by_id` → `tb_user.id`

Note: `deleted_by_id` on `tb_cluster` is **not** declared as a Prisma FK relation (`@relation`) — the field stores the UUID of the deleter by convention but carries no Prisma-level FK enforcement. This matches the pattern on `tb_cluster_user` and `tb_business_unit`. The Platform API resolves the three audit-ID fields (`created_by_id`, `updated_by_id`, `deleted_by_id`) to actor entries inside a nested `audit` object (`audit.created/updated/deleted`, each `{ at, id, name, avatar }`) before returning a cluster record to the SPA; see §5 for the divergence detail.

## 4. Enums

### `enum_cluster_user_role` — 2 values

Carried on `tb_cluster_user.role`. Controls what a user can do within a specific cluster. This enum is also documented in [users](/en/platform/users) / [users data-model](/en/platform/users/data-model) §4 — restated here because readers of the Clusters module may not have visited that page.

| Value | Meaning |
| ----- | ------- |
| `admin` | Cluster-level administrator; can manage the cluster's BUs and user roster |
| `user` | Standard cluster member; read and operational access within the cluster |

This role is orthogonal to the platform RBAC model ([rbac](/en/platform/rbac)). Cluster-user `admin`/`user` standing is a tenant-membership attribute; no SPA permission gate consults it, and a user can hold `role = admin` on one cluster and `role = user` on another simultaneously. The two axes are evaluated independently by the application.

The two values are mirrored as a `const` tuple `CLUSTER_ROLES = ['admin', 'user'] as const` in `ClusterEdit.tsx`, used to populate the role selector in the Add-User dialog and the Users tab's inline role editor. The SPA does not introduce any additional values beyond what the Prisma enum declares.

There are no `tb_cluster`-local enums. `tb_cluster` itself does not carry a status or type enum — `is_active` is a plain `Boolean?` flag.

## 5. Divergences from carmen-platform SPA shape

The `Cluster` interface in `../carmen-platform/src/types/index.ts` (lines 26–51) and the `ClusterFormData` interface (`../carmen-platform/src/pages/clusterManagement/ClusterIdentityFields.ts`, lines 12–21) were compared against the Prisma `tb_cluster` model (re-verified 2026-09-05, `../carmen-platform` source HEAD `157a65e`).

| # | Item | Prisma has | SPA expects | Notes |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `description` | Not present on `tb_cluster` | `description?: string` on `Cluster` interface | Carried over from an earlier schema version; `ClusterFormData` does not include it, so no edit path writes this field. |
| 2 | `bu_cap` / `bu_used` / `bu_cap_end_date` | Not present on `tb_cluster` (computed from `tb_cluster_license` via `v_cluster_bu_cap`) | `bu_cap?: number`, `bu_used?: number`, `bu_cap_end_date?: string \| null` on `Cluster` | Replaces the old `max_license_bu` field entirely (see §1). `bu_used` is the count of non-soft-deleted BUs, including inactive ones. `bu_cap_end_date` carries the perpetual-licence sentinel (year 2099) when the winning row never expires — the SPA hides that sentinel behind "No expiry" text, never a raw date. |
| 3 | `bu_count` | Not present on `tb_cluster` | `bu_count?: number` on `Cluster` interface | Legacy alias for the same BU count `bu_used` now names; `ClusterManagement.tsx`'s row mapper still falls back to `item._count?.tb_business_unit` when neither is present. |
| 4 | `users_count` | Not present on `tb_cluster` | `users_count?: number` on `Cluster` interface | Count of `tb_cluster_user` rows where `cluster_id = this cluster` and `deleted_at IS NULL`. |
| 5 | `total_max_license_users` | Not present on `tb_cluster` (computed from `tb_business_unit_license` via `v_business_unit_seat`, aggregated per cluster) | `total_max_license_users?: number` on `Cluster` interface | **No longer** a sum of a static `tb_business_unit.max_license_users` column — that column is dropped (§2.3). `null`/absent still means "uncapped" for this dimension, unlike `bu_cap` above. |
| 6 | Audit columns | `created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id` (flat columns, raw IDs) | Nested `audit` object — `audit.created`, `audit.updated`, `audit.deleted`, each an `AuditEntry` `{ at, id, name, avatar }` | The API resolves the `_id` FKs to actor names and groups everything under `audit`. Every SPA reader now goes through the shared `normalizeAudit()` helper (`../carmen-platform/src/utils/audit.ts`), which tolerates both the nested and the older flat shape (flat wins when present). |
| 7 | Branding | `logo_file_token`, `avatar_file_token` (`String? @db.VarChar` storage tokens) | `logo?: PresignedImage \| null`, `avatar?: PresignedImage \| null` — embedded objects `{ url, expires_at }` | The raw tokens are never exposed. Images are written through dedicated multipart endpoints (`POST /api-system/clusters/:id/logo` with form field `logo`, `POST /api-system/clusters/:id/avatar` with form field `avatar`), each returning `{ file_token, url, expires_at }`; the regular `PUT` update payload does not carry branding fields. |
| 8 | `doc_version` | `Int @default(0)` | `doc_version?: number` | Aligned — both carry the optimistic-lock counter, no divergence. |

**Field removed since the last sync (2026-07-29):** `max_license_bu` — was previously listed here as `Int?` on Prisma vs. `max_license_bu: string` on `ClusterFormData` (a form-layer string coercion). Both sides are gone now; do not resurrect this row from an older revision of this page.

All core identity fields (`id`, `code`, `name`, `alias_name`, `is_active`, `info`, `deleted_at`) align between Prisma and the SPA read shape.

## 6. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `model tb_business_unit` (line 176), `model tb_cluster` (line 270), `model tb_cluster_user` (line 299), `model tb_business_unit_license` (line 1133), `model tb_cluster_license` (line 1168), `enum enum_cluster_user_role` (line 718). Line numbers as of 2026-09-05 (`../carmen-turborepo-backend-v2` source HEAD `e0f7d0b`, a different repo from the `../carmen-platform` HEAD cited above — both are correct, they are two separate checkouts); `doc_version` added to all 35 platform tables on 2026-07-16 (`8e53bbe`); `max_license_users` dropped from `tb_business_unit` by migration `20260821000000_drop_bu_max_license_users` (2026-08-21).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql` — `CREATE VIEW "v_cluster_bu_cap"` (the winning-row cap computation) and `CREATE VIEW "v_cluster_bu_quota"` (the per-BU rank, borrowing that cap) — read in full to resolve the two views' distinct jobs (§2.4).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260901020000_cluster_license_cancel/migration.sql` — adds `cancelled_at`/`cancelled_by_id`/`cancel_reason` to `tb_cluster_license` and `CREATE OR REPLACE VIEW "v_cluster_bu_cap"` to add the `cancelled_at IS NULL` filter (column signature held identical, per the migration's own comment).

**Secondary (consumer shape):**
- `../carmen-platform/src/types/index.ts` — `Cluster` interface (lines 26–51, incl. `bu_cap`/`bu_used`/`bu_cap_end_date`/`doc_version`), `PresignedImage` (lines 100–103), `ClusterUser` (lines 448–464, no `parent_bu_id`), `AuditEntry` (lines 864–869), `Audit` (lines 871–875).
- `../carmen-platform/src/pages/clusterManagement/ClusterIdentityFields.ts` — `ClusterFormData` interface (lines 12–21; also carries the create-only `licensed_bus`/`license_end_date`/`license_no_expiry` fields used to seed the cluster's first `tb_cluster_license` row on create — see [UI Screens](/en/platform/clusters/ui-screens) §3).
- `../carmen-platform/src/utils/docVersion.ts` — `getDocVersion`/`isVersionConflict`/`notifyVersionConflict` optimistic-lock helpers used by `ClusterEdit.tsx`.
- `../carmen-platform/src/utils/capacity.ts` — `utilization()` (the `null`/`0`-means-uncapped rule, still used for the seat dimension) vs. `seatUtilization()` (the finite-always rule now used for BU quota); file-header comment is the authoritative statement of which rule applies to which field.
- `../carmen-platform/src/utils/businessUnitRank.ts` — `rankBusinessUnits()`/`countOverLimit()`, the exact ranking (`is_hq DESC, created_at ASC, id ASC`) that must match the view `v_cluster_bu_quota`.
- `../carmen-platform/src/services/clusterService.ts` — REST client for cluster API calls (`/api-system/clusters`, `/api-system/clusters/summary`, plus the `/logo` and `/avatar` multipart upload endpoints).

**Landing cross-link:** [clusters](/en/platform/clusters) for the module overview.

**Sibling cross-links:** [Permissions](/en/platform/clusters/permissions) &nbsp;·&nbsp; [UI Screens](/en/platform/clusters/ui-screens).

**Related module cross-links:** [users](/en/platform/users) (full `tb_cluster_user` field table and enum docs) &nbsp;·&nbsp; [business-units](/en/platform/business-units) (full `tb_business_unit` field table) &nbsp;·&nbsp; [licenses](/en/platform/licenses) (full `tb_cluster_license`/`tb_business_unit_license`/`tb_subscription` ledger model and the License Center UI — module not yet documented as of this sync; forward link).
