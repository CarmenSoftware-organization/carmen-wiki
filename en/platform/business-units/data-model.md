---
title: Business Unit — Data Model
description: BU entity, formatting/locale block, DB connection, config array, branding tokens, module activation join, and license field.
published: true
date: 2026-06-10T13:45:00.000Z
tags: book/platform, business-units, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — Data Model

> **At a Glance**
> **Tables:** `tb_business_unit` (primary) &nbsp;·&nbsp; `tb_business_unit_tb_module` (M:N modules activation) &nbsp;·&nbsp; `tb_user_tb_business_unit` (M:N user-join, full doc in [users](/en/platform/users)) &nbsp;·&nbsp; `tb_module` (referenced, full catalog out of scope) &nbsp;·&nbsp; **Enums:** `enum_user_business_unit_role` (admin/user) &nbsp;·&nbsp; `enum_calculation_method` (average/fifo) &nbsp;·&nbsp; **Schema features:** formatting/locale block (date/time/currency/decimal/timezone) &nbsp;·&nbsp; DB connection block &nbsp;·&nbsp; `config` JSON column (key/value config pairs managed via SPA) &nbsp;·&nbsp; `info` JSON column (free-form metadata) &nbsp;·&nbsp; **Branding:** `logo_file_token` / `avatar_file_token` columns, resolved to embedded presigned `logo`/`avatar` objects in API responses &nbsp;·&nbsp; **License field:** `max_license_users` caps how many users may be assigned to this BU

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

`tb_business_unit` is the operational tenant unit in the Carmen Platform — the level at which inventory operations, user assignments, and module activations take place. Every BU belongs to exactly one cluster (via `cluster_id`, a non-nullable FK to `tb_cluster.id`). The cluster is the licensable grouping and billing entity; the BU is the working unit that inventory users log into and that accumulates stock transactions, purchase requests, and store requisitions. The relationship to [clusters](/en/platform/clusters) is therefore M:1 — many BUs beneath one cluster.

The schema is notably richer than `tb_cluster`. Four groups of optional fields extend the core identity beyond what any other Platform table carries:

1. **Formatting/locale block** — nine columns (`date_format`, `date_time_format`, `time_format`, `short_time_format`, `long_time_format`, `timezone`, `amount_format`, `quantity_format`, `recipe_format`, `perpage_format`) that define how dates, times, and numbers are rendered in the inventory UI for this BU. All have application-level defaults pre-populated by the SPA (`BusinessUnitEdit.tsx`, `initialFormData`). The amount/quantity/recipe formats are stored as JSON objects (`{"locales":"th-TH","minimumIntegerDigits":2}`); the date/time formats are plain strings (`"yyyy-MM-dd"`).

2. **DB connection block** — a `db_connection` JSON column that stores the connection parameters for the BU's operational database. This field is handled as an opaque JSON blob by the SPA (serialised to a string in form state, parsed back to JSON on save; the current UI renders it read-only — see [UI Screens](./ui-screens.md) §4.9). The internal key structure of `db_connection` is not enumerated in the SPA type definitions.

3. **JSON config** — a `config` JSON column that stores an array of `BusinessUnitConfig` objects (shape: `{ id?, key, label, datatype?, value? }`). The SPA surfaces this as an editable list in `BusinessUnitEdit.tsx`, allowing operators to add, remove, and edit arbitrary key/value config pairs for the BU. These are not a fixed key namespace — they are open-ended operator-defined entries.

4. **Branding tokens** — a `logo_file_token` / `avatar_file_token` pair (`String? @db.VarChar`) storing file-service references for the BU's rectangular logo and square avatar. The same token pair exists on `tb_cluster`. The raw tokens never appear on list/detail read responses — those resolve the tokens to embedded presigned objects (`logo: { url, expires_at }`, `avatar: { url, expires_at }`); the upload endpoints do return the raw `file_token` alongside the URL. Writes go through dedicated multipart upload endpoints rather than the regular `PUT` payload (see §6 item 8).

Two M:N join tables extend the BU: `tb_business_unit_tb_module` activates which platform modules are enabled for a BU, and `tb_user_tb_business_unit` records which users are assigned to it (documented in full in [users](/en/platform/users)).

## 2. Entities

### 2.1 `tb_business_unit`

The primary business unit record. One row per operational BU, holding the identity fields used across the inventory and platform UIs, the hotel and company info blocks, the branding file tokens, the formatting/locale block, the DB connection block, the config and info JSON columns, the calculation method, and the full audit/soft-delete trio.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| **— Identity —** | | | | |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `cluster_id` | `String @db.Uuid` | No | — | FK to `tb_cluster.id`; determines which cluster owns this BU |
| `code` | `String @db.VarChar(30)` | No | — | Short identifier for the BU; unique within the cluster among live rows (with `deleted_at`) |
| `name` | `String` | No | — | Full display name of the BU |
| `alias_name` | `String? @db.VarChar(10)` | Yes | — | Short alias (up to 10 chars); shown in compact UI surfaces |
| `description` | `String?` | Yes | — | Optional free-text description |
| `info` | `Json?` | Yes | — | Free-form metadata blob; present in Prisma only — no longer carried on the `BusinessUnit` TS interface and not written or read by `BusinessUnitEdit.tsx`. Reserved for extensibility — see §5. |
| **— Status —** | | | | |
| `is_hq` | `Boolean?` | Yes | `true` | Marks this BU as the headquarter unit within its cluster. Uniqueness is enforced at the application layer only — Prisma declares no `@@unique` constraint on `(cluster_id, is_hq)`, so the schema permits multiple HQ flags per cluster. Prisma default is `true`; SPA `BusinessUnitEdit` `initialFormData` defaults to `false`. |
| `is_active` | `Boolean?` | Yes | `true` | When `false`, the BU is considered inactive |
| **— DB Connection —** | | | | |
| `db_connection` | `Json?` | Yes | — | DB connection parameters for the BU's operational database; stored as opaque JSON |
| **— Modules-config —** | | | | |
| `config` | `Json?` | Yes | — | Array of `BusinessUnitConfig` objects (`{ id?, key, label, datatype?, value? }`); editable key/value pairs maintained via the SPA config panel — see §5 |
| **— License —** | | | | |
| `default_currency_id` | `String? @db.Uuid` | Yes | — | FK (logical, no Prisma `@relation`) to the default currency for this BU; displayed via the currency selector in `BusinessUnitEdit.tsx` |
| `calculation_method` | `enum_calculation_method` | No | `average` | Costing method used for inventory valuation: `average` or `fifo` |
| `max_license_users` | `Int?` | Yes | — | Cap on the number of users that may be assigned to this BU. `NULL` means no cap. Enforcement is at the application layer; not a DB constraint |
| **— Company —** | | | | |
| `branch_no` | `String?` | Yes | — | Thai tax branch number (สาขา) for the BU's company entity |
| `company_name` | `String?` | Yes | — | Legal company name for the BU |
| `company_address` | `String?` | Yes | — | Company street/postal address |
| `company_email` | `String?` | Yes | — | Company email address |
| `company_tel` | `String?` | Yes | — | Company telephone number |
| `company_zip_code` | `String?` | Yes | — | Company postal code |
| `tax_no` | `String?` | Yes | — | Thai tax identification number (เลขภาษี) |
| **— Hotel —** | | | | |
| `hotel_name` | `String?` | Yes | — | Property/hotel name (may differ from company name) |
| `hotel_address` | `String?` | Yes | — | Property street/postal address |
| `hotel_email` | `String?` | Yes | — | Property email address |
| `hotel_tel` | `String?` | Yes | — | Property telephone number |
| `hotel_zip_code` | `String?` | Yes | — | Property postal code |
| **— Branding —** | | | | |
| `logo_file_token` | `String? @db.VarChar` | Yes | — | File-storage token for the BU's rectangular logo. Never exposed raw to the SPA — the API resolves it to an embedded presigned `logo` object `{ url, expires_at }` (see §6 item 8). `tb_cluster` carries the identical token pair |
| `avatar_file_token` | `String? @db.VarChar` | Yes | — | File-storage token for the BU's square avatar. Same resolution path as the logo (embedded presigned `avatar` object) |
| **— Formatting & Locale —** | | | | |
| `date_format` | `String?` | Yes | `"yyyy-MM-dd"` | Date display format string used in the inventory UI |
| `date_time_format` | `String?` | Yes | `"yyyy-MM-dd HH:mm:ss"` | Date-time display format string |
| `time_format` | `String?` | Yes | `"HH:mm:ss"` | Full time display format string |
| `short_time_format` | `String?` | Yes | `"HH:mm"` | Short time display format string |
| `long_time_format` | `String?` | Yes | `"HH:mm:ss"` | Long time display format string (same default as `time_format`; separate field for future divergence) |
| `timezone` | `String?` | Yes | `"Asia/Bangkok"` | IANA timezone identifier for the BU's locale |
| `amount_format` | `Json?` | Yes | — | JSON object for monetary amount formatting (e.g. `{"locales":"th-TH","minimumIntegerDigits":2}`) |
| `quantity_format` | `Json?` | Yes | — | JSON object for quantity number formatting |
| `perpage_format` | `Json?` | Yes | — | JSON object for pagination defaults (e.g. `{"default":10}`) |
| `recipe_format` | `Json?` | Yes | — | JSON object for recipe quantity formatting |
| **— Audit —** | | | | |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: row creation time |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the creator |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: last update time |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the last updater |
| **— Soft-delete —** | | | | |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Soft-delete timestamp; `NULL` = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the deleter (stored by convention; no Prisma `@relation`) |

**Constraints:**
- `@id` on `id`
- `@@unique([cluster_id, code, deleted_at])` — map `"business_unit_cluster_code_deleted_at_u"` — BU codes are unique within a cluster among live rows; allows code reuse after soft delete
- FK: `cluster_id` → `tb_cluster.id` (NoAction / NoAction) — Prisma relation `tb_cluster`
- FK: `created_by_id` → `tb_user.id` (NoAction / NoAction) — Prisma named relation `"tb_business_unit_created_by_idTotb_user"`
- FK: `updated_by_id` → `tb_user.id` (NoAction / NoAction) — Prisma named relation `"tb_business_unit_updated_by_idTotb_user"`

**Indexes:**
- `@@index([cluster_id, deleted_at])` — map `"business_unit_cluster_deleted_at_idx"` — supports cluster-scoped BU listing
- `@@index([code, deleted_at])` — map `"business_unit_code_deleted_at_idx"` — supports code lookup
- `@@index([cluster_id, code, deleted_at])` — map `"business_unit_cluster_code_deleted_at_idx"` — composite; overlaps with the unique constraint but retained as an explicit index for query planning

### 2.2 `tb_business_unit_tb_module`

Many-to-many join that activates which platform modules are enabled for a given business unit. Each row asserts that module `module_id` is active for business unit `business_unit_id`. The M:N activation means a BU can have any subset of the available modules enabled; adding or removing a module creates or soft-deletes a row in this table. The full module catalog lives in `tb_module` (§2.4), which is referenced but not owned by the BU.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `business_unit_id` | `String @db.Uuid` | No | — | FK to `tb_business_unit.id`; the BU whose module set this row belongs to |
| `module_id` | `String @db.Uuid` | No | — | FK to `tb_module.id`; the module being activated |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: row creation time |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the creator |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: last update time |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the last updater |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Soft-delete timestamp; `NULL` = activation is live |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: deleter's `tb_user.id` (stored by convention; no Prisma `@relation`) |

**Constraints:**
- `@id` on `id`
- FK: `business_unit_id` → `tb_business_unit.id` (NoAction / NoAction) — Prisma relation `tb_business_unit`
- FK: `module_id` → `tb_module.id` (NoAction / NoAction) — Prisma relation `tb_module`
- FK: `created_by_id` → `tb_user.id` (NoAction / NoAction) — Prisma named relation `"tb_business_unit_tb_module_created_by_idTotb_user"`
- FK: `updated_by_id` → `tb_user.id` (NoAction / NoAction) — Prisma named relation `"tb_business_unit_tb_module_updated_by_idTotb_user"`

**Indexes:**
- `@@index([business_unit_id, module_id, deleted_at])` — map `"businessunit_module_business_unit_module_deleted_at_idx"` — supports querying all active modules for a BU

### 2.3 `tb_user_tb_business_unit` (BU-side view)

The full field table for `tb_user_tb_business_unit` is documented in [users data-model](../users/data-model.md) §2.3. From the business-unit perspective, the key points are:

- **`business_unit_id` FK** — `String? @db.Uuid` (nullable), FK to `tb_business_unit.id` with `onDelete: NoAction, onUpdate: NoAction`. Removing a BU does not automatically remove join rows — application-layer cleanup is required.
- **`role`** — `enum_user_business_unit_role` (non-nullable, default `user`). Records the per-BU role for this user-BU assignment: `admin` or `user`. This role is independent of the platform RBAC assignments on the user account ([rbac](/en/platform/rbac)) and of `enum_cluster_user_role` on `tb_cluster_user`. See §4 for the full enum definition.
- **`is_default`** — `Boolean?` (default `false`). Marks the BU as the user's default; the inventory application lands the user on their default BU at login. Only one BU per user should carry `is_default = true` at a given time; the uniqueness constraint does not enforce this — it is an application-layer convention.
- **`is_active`** — `Boolean?` (default `true`). Soft-activity flag for the assignment.
- **Cluster-scoping rule** — the Add BU dialog in the user edit screen (`UserEdit.tsx`) filters the available BU list to those BUs whose `cluster_id` matches a cluster the user already belongs to (via `tb_cluster_user`). This scoping is enforced at the application layer, not as a FK constraint — `tb_user_tb_business_unit` does not carry a `cluster_id` column in Prisma.
- **Unique constraint** — `@@unique([user_id, business_unit_id, deleted_at])` — map `"user_businessunit_user_business_unit_deleted_at_u"` — allows a user to be re-assigned to a BU after the original assignment is soft-deleted.

### 2.4 `tb_module` (referenced, brief)

The module catalog table. Each row names one activatable platform module (e.g. Inventory, Purchase Request, Store Requisition). `tb_business_unit_tb_module` references `tb_module.id` on the FK side — the BU side of the relationship activates modules, but does not own the module catalog.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | Module name; unique with `deleted_at` |
| `description` | `String?` | Yes | Optional description |
| (audit columns) | — | Yes | Standard `created_*`/`updated_*`/`deleted_*` trio |

**Unique constraint:** `@@unique([name, deleted_at])` — map `"module_name_deleted_at_u"`. From the BU perspective, only `id` and `name` are relevant — the rest of the module catalog is out of scope for this page.

## 3. Relationships

```
tb_business_unit  M ─── 1  tb_cluster                         (via tb_business_unit.cluster_id)
tb_business_unit  1 ─── M  tb_business_unit_tb_module  M ─── 1  tb_module
tb_business_unit  1 ─── M  tb_user_tb_business_unit    M ─── 1  tb_user
tb_business_unit  1 ─── M  tb_subscription_detail              (billing, out of scope)
tb_business_unit  1 ─── M  tb_application_role                 (application roles, out of scope)
tb_business_unit  self-FK  created_by_id, updated_by_id  → tb_user.id  (audit relations)
```

FK directions (all `onDelete: NoAction, onUpdate: NoAction` unless noted):

- `tb_business_unit.cluster_id` → `tb_cluster.id`
- `tb_business_unit.created_by_id` → `tb_user.id` — Prisma named relation `"tb_business_unit_created_by_idTotb_user"`
- `tb_business_unit.updated_by_id` → `tb_user.id` — Prisma named relation `"tb_business_unit_updated_by_idTotb_user"`
- `tb_business_unit_tb_module.business_unit_id` → `tb_business_unit.id`
- `tb_business_unit_tb_module.module_id` → `tb_module.id`
- `tb_user_tb_business_unit.business_unit_id` → `tb_business_unit.id`

Note: `deleted_by_id` on both `tb_business_unit` and `tb_business_unit_tb_module` is stored as `String? @db.Uuid` by convention but is **not** declared as a Prisma `@relation` — the FK is not enforced at the database level for the delete path, consistent with the pattern used across the platform schema.

Note: `default_currency_id` on `tb_business_unit` is a logical reference to the currency catalog but carries no Prisma `@relation` directive — it is enforced at the application layer only.

## 4. Enums

### `enum_user_business_unit_role` — 2 values

Carried on `tb_user_tb_business_unit.role`. Controls what a user can do within a specific business unit. Orthogonal to both the platform RBAC assignments on the user account ([rbac](/en/platform/rbac) — which replaced the removed `platform_role` enum) and `enum_cluster_user_role` on `tb_cluster_user` — the role axes are evaluated independently. This enum is also documented in [users data-model](../users/data-model.md) §4 — restated here for readers who arrive from the business-units module.

| Value | Meaning |
| ----- | ------- |
| `admin` | BU-level administrator; can manage the BU's settings and inventory operations |
| `user` | Standard BU member; operational access to the BU's inventory workflows |

### `enum_calculation_method` — 2 values

Carried on `tb_business_unit.calculation_method`. Determines the costing method used when the inventory system calculates the cost of goods for this BU.

| Value | Meaning |
| ----- | ------- |
| `average` | Weighted average cost method (default). Each receipt adjusts the running average cost of inventory items |
| `fifo` | First-In First-Out method. Issues are costed at the price of the oldest stock layer |

The default is `average`. Both values match the costing methods documented in the Carmen Inventory ERP ([calculation-methods](../../inventory/costing/calculation-methods.md)).

## 5. The `config` and `info` JSON columns

These two JSON columns differ in both structure and editability: `config` carries a typed, SPA-editable array of operator-defined key/value pairs; `info` is an unstructured `Json?` column with no SPA edit path, mirroring the same dormant pattern as `tb_cluster.info`.

### `config` — operator-defined key/value pairs

`config` is stored as `Json?` in Prisma and is typed as `BusinessUnitConfig[] | null` in the SPA (`src/types/index.ts`, line 134). The `BusinessUnitConfig` interface (`src/types/index.ts`, lines 77–83) has the shape:

```
BusinessUnitConfig {
  id?:       string      -- optional; row identifier if persisted
  key:       string      -- config key name (operator-defined)
  label:     string      -- display label shown in the SPA config panel
  datatype?: string      -- optional type hint (not enforced)
  value?:    unknown     -- the config value
}
```

The SPA (`BusinessUnitEdit.tsx`) surfaces this as an editable list: operators can add rows (empty `{ key, label, datatype, value }` objects are appended), edit individual fields, and remove rows. The key namespace is entirely open-ended — there is no fixed set of recognised keys declared in either the Prisma schema or the SPA type definitions. The initial value from `initialFormData` is an empty array (`config: []`).

Because the keys are operator-defined, this page cannot enumerate them. If your team uses specific `config` keys (e.g. for fiscal year settings, tax-inclusive flags, or integration credentials), document them in the BU's operational runbook.

### `info` — free-form metadata blob

`info` is stored as `Json?` in Prisma but has **no representation in the SPA at all** as of 2026-06-10: the field has been dropped from the `BusinessUnit` TS interface (it previously appeared as `info?: unknown`), and there is no edit path for it in `BusinessUnitEdit.tsx` — the SPA does not read or write any key under `info` for the BU. The column appears to be reserved for future extensibility, analogous to the `info Json? @db.Json` column on `tb_cluster` which is also documented as a free-form metadata blob with no currently documented key structure.

## 6. Divergences from carmen-platform SPA shape

The `BusinessUnit` interface in `../carmen-platform/src/types/index.ts` (lines 90–142) and the `BusinessUnitFormData` interface in `../carmen-platform/src/pages/BusinessUnitEdit.tsx` (lines 63–105) were compared against the Prisma `tb_business_unit` model (as of 2026-06-10).

| # | Item | Prisma has | SPA expects | Notes |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `cluster_name` | Not present on `tb_business_unit` | `cluster_name?: string` on `BusinessUnit` interface | API-resolved display name for the cluster; the Prisma model carries only `cluster_id`. Not in `BusinessUnitFormData` — read-only display field. |
| 2 | Audit columns | `created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id` (flat columns, raw IDs) | Nested `audit` object — `audit.created`, `audit.updated`, `audit.deleted`, each an `AuditEntry` `{ at, id, name, avatar }` | The API resolves the `_id` FKs to actor names and groups everything under `audit`. The SPA list page flattens this back into `created_at`/`created_by_name` etc. for its date columns, tolerating the older flat shape, which wins when present (`item.created_at ?? item.audit?.created?.at`). The `BusinessUnit` TS interface keeps the flat optional fields as the post-mapping shape; raw IDs are not in the interface. |
| 3 | `max_license_users` | `Int?` | `max_license_users?: number` on `BusinessUnit`; `max_license_users: string` in `BusinessUnitFormData` | Form holds the value as a string (HTML input coercion: `String(bu.max_license_users)`); converted back to number before the API call. Read interface correctly types it as `number`. |
| 4 | `amount_format` / `quantity_format` / `recipe_format` / `perpage_format` | `Json?` (JSON objects) | Typed as `string?` on `BusinessUnit` interface; `string` in `BusinessUnitFormData` | The SPA serialises these JSON objects to strings for plain text inputs (`toJsonString()` helper) and parses them back before the API call. The `BusinessUnit` read interface types them as `string?` rather than `Json`, which reflects the serialised wire shape rather than the Prisma storage shape. |
| 5 | `db_connection` | `Json?` | `db_connection?: unknown` on `BusinessUnit`; `db_connection: string` in `BusinessUnitFormData` | Same string-serialisation pattern as the format JSON fields, but the current UI renders it as a read-only `<pre>` — there is no editable input ([UI Screens](./ui-screens.md) §4.9). |
| 6 | `config` | `Json?` | `config?: BusinessUnitConfig[] | null` on `BusinessUnit`; `config: BusinessUnitConfig[]` in `BusinessUnitFormData` | The only JSON column with a structured TS type; programmatic reads and writes should use `BusinessUnitConfig[]` from `src/types/index.ts` rather than raw `Json` or `unknown`. |
| 7 | `info` | `Json?` | Not present | Dropped from the `BusinessUnit` read interface (previously `info?: unknown`); never in `BusinessUnitFormData`. Prisma-only column with no SPA path — see §5. |
| 8 | Branding | `logo_file_token`, `avatar_file_token` (`String? @db.VarChar` storage tokens) | `logo?: PresignedImage \| null`, `avatar?: PresignedImage \| null` — embedded objects `{ url, expires_at }` on list and detail responses | Read responses never carry the raw tokens. Images are written through dedicated multipart endpoints (`POST /api-system/business-units/:id/logo` with form field `logo`, `POST /api-system/business-units/:id/avatar` with form field `avatar`), each returning `{ file_token, url, expires_at }`; the regular `PUT` update payload does not carry branding fields. |

All core identity, hotel info, company info, format, locale, and soft-delete fields align between Prisma and the SPA shapes. Divergences are API-resolved display names and audit regrouping (items 1–2), form-layer string coercions for JSON fields (items 3–5), a Prisma-only column (item 7), or token→presigned-object resolution (item 8).

## 7. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `model tb_business_unit` (line 124), `model tb_business_unit_tb_module` (line 194), `model tb_user_tb_business_unit` (line 600), `model tb_module` (line 296), `enum enum_user_business_unit_role` (line 661), `enum enum_calculation_method` (line 119). Line numbers as of 2026-06-10.

**Secondary (consumer shape):**
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` — `BusinessUnitFormData` interface (lines 63–105); `initialFormData` defaults (lines 107–142); config array add/remove/edit handlers; logo/avatar upload handlers.
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx` — BU list view; nested-audit flattening; logo thumbnail column.
- `../carmen-platform/src/services/businessUnitService.ts` — REST client for BU API calls (`/api-system/business-units`, plus the `/logo` and `/avatar` upload endpoints).
- `../carmen-platform/src/types/index.ts` — `BusinessUnit` interface (lines 90–142), `BusinessUnitConfig` interface (lines 77–83), `PresignedImage` (lines 85–88), `Audit`/`AuditEntry` (lines 254–265).

**Cross-links:**
- [business-units](/en/platform/business-units) — module landing page
- [clusters](/en/platform/clusters) — parent entity (`tb_cluster`, `max_license_bu`)
- [users](/en/platform/users) — full `tb_user_tb_business_unit` field table and `enum_user_business_unit_role` canonical doc
- [UI Screens](./ui-screens.md) — SPA screens for BU management
