---
title: Cluster — Data Model
description: Cluster entity, relationships to BUs and users, license fields.
published: true
date: 2026-05-19T23:55:00.000Z'
tags: book/platform, clusters, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Data Model

> **At a Glance**
> **Tables:** `tb_cluster` (primary) &nbsp;·&nbsp; `tb_cluster_user` (M:N user-join, full doc in [users](/en/platform/users)) &nbsp;·&nbsp; `tb_business_unit` (`cluster_id` FK side, full doc in [business-units](/en/platform/business-units)) &nbsp;·&nbsp; **Enums:** `enum_cluster_user_role` (admin/user) &nbsp;·&nbsp; **Audit columns:** standard `created_*`/`updated_*`/`deleted_*` trio on `tb_cluster` &nbsp;·&nbsp; **License field:** `max_license_bu` caps how many BUs this cluster may have

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

`tb_cluster` is the top-level tenant container in the Carmen Platform. Every business unit and every cluster-scoped user membership hangs beneath a cluster row. Clusters represent a licensable grouping of business units — typically one hotel brand, hotel group, or company entity — and the `max_license_bu` field on the cluster enforces how many BUs may be provisioned within it; this cap is checked at the application layer (Platform SPA UI), not as a database constraint.

The cluster entity participates in two principal one-to-many relationships that extend its scope into the rest of the platform. First, `tb_business_unit` carries a `cluster_id` foreign key, making each BU a child of exactly one cluster; this relationship is documented in full in the [business-units](/en/platform/business-units) module. Second, `tb_cluster_user` is the M:N join table that records which platform users belong to a cluster and at what per-cluster role; this table is documented in full in [users](/en/platform/users) — the present page covers only the cluster-side view of both relationships.

All audit and soft-delete lifecycle fields follow the same `created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id` pattern used across every table in the platform schema. A cluster row with a non-null `deleted_at` is soft-deleted; its child BUs and cluster-user memberships are not automatically soft-deleted by a database cascade (all FK relations use `onDelete: NoAction`), so application-layer logic is responsible for cascading soft-deletes where required.

`tb_cluster` also owns a `tb_subscription` 1:M relation in the Prisma schema, recording billing subscription rows. The subscription data model is not within the scope of this page — it is documented in the billing/subscription module — but the relation is listed in §3 for completeness. The `info` field (`Json? @db.Json`) is a free-form metadata blob reserved for future extensibility; it is present in the Prisma model and exposed in the `Cluster` TS interface but has no currently documented key structure.

## 2. Entities

### 2.1 `tb_cluster`

The primary cluster record. One row per tenant cluster, holding the identity fields used throughout the Platform SPA (`code`, `name`, `alias_name`, `logo_url`), the license cap (`max_license_bu`), and the full audit/soft-delete trio.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `code` | `String @db.VarChar(30)` | No | — | Short identifier for the cluster; unique with `name` and `deleted_at` |
| `name` | `String @db.VarChar` | No | — | Full display name of the cluster |
| `alias_name` | `String? @db.VarChar(3)` | Yes | — | 3-character maximum alias (unusually tight `VarChar(3)` cap — tighter than any other varchar in this schema). Shown in compact cluster-selector UI surfaces where the full `name` does not fit, e.g. the cluster list table "Alias" column and CSV export |
| `logo_url` | `String? @db.VarChar` | Yes | — | URL of the cluster's logo image |
| `max_license_bu` | `Int?` | Yes | — | Cap on the number of live (non-soft-deleted) `tb_business_unit` rows in this cluster. `NULL` means no cap enforced. Enforcement is at the application layer (Platform SPA UI); the database does NOT enforce this constraint |
| `is_active` | `Boolean?` | Yes | `true` | When `false`, the cluster and its BUs are considered inactive |
| `info` | `Json? @db.Json` | Yes | — | Free-form metadata blob; reserved for future extensibility |
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

The full field table for `tb_cluster_user` is documented in [users data-model](../users/data-model.md) (§2.2). From the cluster perspective, the key points are:

- **`cluster_id` FK** — `String @db.Uuid` (non-nullable), FK to `tb_cluster.id` with `onDelete: NoAction, onUpdate: NoAction`. Deleting or soft-deleting a cluster does not automatically remove join rows; application code must handle cascading cleanup.
- **`role`** — `enum_cluster_user_role` (non-nullable, default `user`). Records the per-cluster role for this user-cluster relationship: `admin` or `user`. This role is completely independent of `platform_role` on `tb_user` — a `support_staff` platform user may hold cluster `admin` rights on one cluster while holding `user` rights on another.
- **`parent_bu_id`** — `String? @db.Uuid` (nullable). Identifies the billing-owner BU for this user within the cluster. The Prisma comment reads: "เพื่อบอกว่าใคร BU ใหนเป็นเจ้าของ User คนนี้ เอาไว้ทำ invoice เก็บตังค์" (to track which BU owns this user for invoicing purposes). This field does **not** carry a FK constraint in Prisma — it is a logical reference to `tb_business_unit.id` enforced at the application layer.
- **`is_active`** — `Boolean?` (default `true`). Soft-activity flag for the membership; a user may be deactivated within a cluster without soft-deleting the row.
- **Unique constraint** — `@@unique([user_id, cluster_id, deleted_at])` — allows a user to be re-added to a cluster after the original membership is soft-deleted, without a unique-key collision.

For the complete field table, all audit columns, and the user-side relationship view, see [users](/en/platform/users) and [users data-model](../users/data-model.md).

### 2.3 `tb_business_unit` (cluster_id FK side)

The full field table for `tb_business_unit` is documented in the [business-units](/en/platform/business-units) module (forthcoming). From the cluster perspective, the key points are:

- **`cluster_id` FK** — `String @db.Uuid` (non-nullable), FK to `tb_cluster.id` with `onDelete: NoAction, onUpdate: NoAction`. This establishes the 1:M cluster→BU relationship. A BU belongs to exactly one cluster and cannot be moved between clusters without a data migration.
- **`max_license_bu` interaction** — `tb_cluster.max_license_bu` is an `Int?` cap on the count of live (non-soft-deleted) BUs beneath this cluster. When `max_license_bu` is non-null, the Platform SPA enforces this cap at the UI layer on the cluster edit screen before allowing creation of a new BU. The Prisma schema does not enforce the cap as a database constraint — it is a business-rule check in the application layer.
- **Unique constraint on `tb_business_unit`** — `@@unique([cluster_id, code, deleted_at])` — ensures that BU codes are unique within a cluster among live rows, but allows code reuse after soft delete.
- **BU count query** — the `bu_count` field on the SPA `Cluster` interface (see §5) reflects the count of non-soft-deleted `tb_business_unit` rows for a given `cluster_id`; this is the value compared against `max_license_bu` to determine whether the "Add Business Unit" action is available.

## 3. Relationships

```
tb_cluster  1 ─── M  tb_business_unit          (via tb_business_unit.cluster_id)
tb_cluster  1 ─── M  tb_cluster_user  M ─── 1  tb_user
tb_cluster  1 ─── M  tb_subscription            (billing/subscription rows)
tb_cluster  self-FK  created_by_id, updated_by_id  → tb_user.id  (audit relations)
```

FK directions (all `onDelete: NoAction, onUpdate: NoAction` unless noted):

- `tb_business_unit.cluster_id` → `tb_cluster.id`
- `tb_cluster_user.cluster_id` → `tb_cluster.id`
- `tb_subscription.cluster_id` → `tb_cluster.id` (subscription rows reference the cluster)
- `tb_cluster.created_by_id` → `tb_user.id`
- `tb_cluster.updated_by_id` → `tb_user.id`

Note: `deleted_by_id` on `tb_cluster` is **not** declared as a Prisma FK relation (`@relation`) — the field stores the UUID of the deleter by convention but carries no Prisma-level FK enforcement. This matches the pattern on `tb_cluster_user` and `tb_business_unit`. The Platform API resolves the three audit-ID fields (`created_by_id`, `updated_by_id`, `deleted_by_id`) to their corresponding display names (`created_by_name`, `updated_by_name`, `deleted_by_name`) before returning a cluster record to the SPA; see §5 for the divergence detail.

## 4. Enums

### `enum_cluster_user_role` — 2 values

Carried on `tb_cluster_user.role`. Controls what a user can do within a specific cluster. This enum is also documented in [users](/en/platform/users) / [users data-model](../users/data-model.md) §4 — restated here because readers of the Clusters module may not have visited that page.

| Value | Meaning |
| ----- | ------- |
| `admin` | Cluster-level administrator; can manage the cluster's BUs and user roster from the cluster edit screen |
| `user` | Standard cluster member; read and operational access within the cluster |

This role is orthogonal to `platform_role` on `tb_user`. A user with `platform_role = support_staff` can hold `role = admin` on one cluster and `role = user` on another simultaneously. The two role axes are evaluated independently by the application.

The two values are mirrored as a `const` tuple `CLUSTER_ROLES = ['admin', 'user'] as const` in `ClusterEdit.tsx`, used to populate the role selector in the cluster user-management UI. The SPA does not introduce any additional values beyond what the Prisma enum declares.

There are no `tb_cluster`-local enums. `tb_cluster` itself does not carry a status or type enum — `is_active` is a plain `Boolean?` flag.

## 5. Divergences from carmen-platform SPA shape

The `Cluster` interface in `../carmen-platform/src/types/index.ts` (lines 24–44) and the `ClusterFormData` interface in `../carmen-platform/src/pages/ClusterEdit.tsx` (lines 26–33) were compared against the Prisma `tb_cluster` model.

| # | Item | Prisma has | SPA expects | Notes |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `description` | Not present on `tb_cluster` | `description?: string` on `Cluster` interface | The `Cluster` TS interface carries a `description` field that has no corresponding column on `tb_cluster` in Prisma. This is likely an API-layer annotation or a carry-over from an earlier schema version. The `ClusterFormData` interface does **not** include `description`, so no edit path writes this field. |
| 2 | `bu_count` | Not present on `tb_cluster` | `bu_count?: number` on `Cluster` interface | Count of `tb_business_unit` rows where `cluster_id = this cluster` and `deleted_at IS NULL` (live BUs only). Computed server-side (Prisma `_count` include on `tb_business_unit`); returned on list and detail endpoints. SPA falls back to `item._count?.tb_business_unit` when the pre-aggregated field is absent. |
| 3 | `users_count` | Not present on `tb_cluster` | `users_count?: number` on `Cluster` interface | Count of `tb_cluster_user` rows where `cluster_id = this cluster` and `deleted_at IS NULL` (active cluster-user assignments). Computed server-side (Prisma `_count` include on `tb_cluster_user`); SPA falls back to `item._count?.tb_cluster_user` when the pre-aggregated field is absent. |
| 4 | `total_max_license_users` | Not present on `tb_cluster` | `total_max_license_users?: number` on `Cluster` interface | Sum of `tb_business_unit.max_license_users` across non-soft-deleted BUs in this cluster. Computed server-side; `NULL` BU values treated per API implementation — verify against the backend service before relying on the precise null-handling. |
| 5 | `created_by_id` / `updated_by_id` / `deleted_by_id` | `String? @db.Uuid` (raw IDs) | `created_by_name`, `updated_by_name`, `deleted_by_name` (name strings) | API resolves the `_id` FKs to display names before returning the response. The raw IDs are not exposed in the `Cluster` TS interface. |
| 6 | `max_license_bu` | `Int?` | `max_license_bu: string` in `ClusterFormData` | The form holds the value as a string (HTML input), converted to a number before the API call. The `Cluster` read interface correctly types it as `max_license_bu?: number`. |

All core identity and license fields (`id`, `code`, `name`, `alias_name`, `logo_url`, `max_license_bu`, `is_active`, `info`, `created_at`, `updated_at`, `deleted_at`) align between Prisma and the SPA read shape. Divergences are either computed API annotations (items 2–4), ID→name resolution (item 5), or a form-layer string coercion (item 6).

## 6. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `model tb_cluster` (line 166), `model tb_cluster_user` (line 194), `model tb_business_unit` (line 79), `enum enum_cluster_user_role` (line 534).

**Secondary (consumer shape):**
- `../carmen-platform/src/types/index.ts` — `Cluster` interface (lines 24–44).
- `../carmen-platform/src/pages/ClusterEdit.tsx` — `ClusterFormData` interface (lines 26–33).
- `../carmen-platform/src/services/clusterService.ts` — REST client for cluster API calls.

**Landing cross-link:** [clusters](/en/platform/clusters) for the module overview.

**Sibling cross-links:** [Permissions](./permissions.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md).

**Related module cross-links:** [users](/en/platform/users) (full `tb_cluster_user` field table and enum docs) &nbsp;·&nbsp; [business-units](/en/platform/business-units) (full `tb_business_unit` field table).
