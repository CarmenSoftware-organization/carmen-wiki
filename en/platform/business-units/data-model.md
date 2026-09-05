---
title: Business Unit — Data Model
description: BU entity, formatting/locale block, database-pool + schema pointer, config array, branding tokens, module activation join, and the per-BU license ledger that replaced the old max_license_users column.
published: true
date: 2026-09-05T07:00:00.000Z
tags: book/platform, business-units, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — Data Model

> **At a Glance**
> **Tables:** `tb_business_unit` (primary) &nbsp;·&nbsp; `tb_business_unit_tb_module` (M:N modules activation) &nbsp;·&nbsp; `tb_business_unit_license` (per-BU seat-purchase ledger, replaces the old `max_license_users` column) &nbsp;·&nbsp; `tb_database_pool` (referenced — shared DB server a BU's tenant schema lives in) &nbsp;·&nbsp; `tb_user_tb_business_unit` (M:N user-join, full doc in [users](/en/platform/users)) &nbsp;·&nbsp; `tb_module` (referenced, full catalog out of scope) &nbsp;·&nbsp; **Enums:** `enum_user_business_unit_role` (admin/user) &nbsp;·&nbsp; `enum_calculation_method` (average/fifo) &nbsp;·&nbsp; **Schema features:** formatting/locale block (date/time/currency/decimal/timezone) &nbsp;·&nbsp; `config` JSON column (key/value config pairs managed via SPA) &nbsp;·&nbsp; `info` JSON column (free-form metadata, no SPA path) &nbsp;·&nbsp; structured hotel/company address columns (10 fields each) &nbsp;·&nbsp; **Branding:** `logo_file_token` / `avatar_file_token`, resolved to embedded presigned `logo`/`avatar` objects &nbsp;·&nbsp; **Removed since the last sync:** `max_license_users` (column physically dropped) and `db_connection` (JSON blob physically dropped, replaced by `database_pool_id` + `db_schema`) &nbsp;·&nbsp; **`code` is now platform-wide unique**, not cluster-scoped, and is server-generated — see §2.1 &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` (added 2026-07-16), enforced as an optimistic lock on `PUT`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (read at commit `1aaab3c`, 2026-09-05)
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

`tb_business_unit` is the operational tenant unit in the Carmen Platform — the level at which inventory operations, user assignments, and module activations take place. Every BU belongs to exactly one cluster (via `cluster_id`, a non-nullable FK to `tb_cluster.id`). The cluster is the licensable grouping and billing entity; the BU is the working unit that inventory users log into and that accumulates stock transactions, purchase requests, and store requisitions. The relationship to [clusters](/en/platform/clusters) is therefore M:1 — many BUs beneath one cluster.

Two structural changes landed since the last sync, both confirmed directly against the current Prisma schema and the SPA source that consumes it:

1. **`max_license_users` is gone.** The column was dropped from the database by migration `20260821000000_drop_bu_max_license_users` (Task 6.1) — not just removed from the SPA type. The schema's own doc-comment on the line above `enum_calculation_method` states there is "no migration-level rollback left — restore from a backup." Seat counts now live in the new `tb_business_unit_license` ledger (§2.3), and the enforced pool is read from view `v_business_unit_seat`, summed client-side by `sumActiveLicenses()` (`src/utils/buLicense.ts`) into what the edit page's General tab labels "Max users" — now a read-only computed figure, not a typed field. See [UI Screens](/en/platform/business-units/ui-screens) §4 (General tab) and §4 (Licenses tab).
2. **`db_connection` is gone.** The JSON blob that used to hold `{ host, port, database, schema, user, password, ssl }` — and, before that, the editable structured form documented at the last sync — has been physically dropped from `tb_business_unit`. A BU no longer holds its own database credentials at all. It instead carries `database_pool_id` (`String? @db.Uuid`, FK to the new `tb_database_pool` table, §2.4) plus `db_schema` (`String? @db.VarChar`, the BU's own schema name inside that shared pool). The pool record — not the BU — holds `host`/`port`/`database`/`username`/`password`. See §2.4 and [UI Screens](/en/platform/business-units/ui-screens) §4 (Technical tab).

The schema is still notably richer than `tb_cluster`. Three groups of optional fields extend the core identity:

1. **Formatting/locale block** — nine columns (`date_format`, `date_time_format`, `time_format`, `short_time_format`, `long_time_format`, `timezone`, `amount_format`, `quantity_format`, `recipe_format`, `perpage_format`) that define how dates, times, and numbers are rendered in the inventory UI for this BU. All have application-level defaults pre-populated by the SPA (`BusinessUnitEdit.tsx`, `initialFormData`). The amount/quantity/recipe formats are stored as JSON objects (`{"locales":"th-TH","minimumIntegerDigits":2}`); the date/time formats are plain strings (`"yyyy-MM-dd"`).

2. **JSON config** — a `config` JSON column that stores an array of `BusinessUnitConfig` objects (shape: `{ id?, key, label, datatype?, value? }`). The SPA surfaces this as an editable list on the edit page's Technical tab, allowing operators to add, remove, and edit arbitrary key/value config pairs for the BU. These are not a fixed key namespace — they are open-ended operator-defined entries.

3. **Branding tokens** — a `logo_file_token` / `avatar_file_token` pair (`String? @db.VarChar`) storing file-service references for the BU's rectangular logo and square avatar. The same token pair exists on `tb_cluster`. The raw tokens never appear on list/detail read responses — those resolve the tokens to embedded presigned objects (`logo: { url, expires_at }`, `avatar: { url, expires_at }`); the upload endpoints do return the raw `file_token` alongside the URL. Writes go through dedicated multipart upload endpoints rather than the regular `PUT` payload (see §6 item 8).

Two M:N join tables extend the BU: `tb_business_unit_tb_module` activates which platform modules are enabled for a BU, and `tb_user_tb_business_unit` records which users are assigned to it (documented in full in [users](/en/platform/users)). A third table, `tb_business_unit_license` (§2.3), is a 1:M ledger, not a join — one row per seat purchase.

## 2. Entities

### 2.1 `tb_business_unit`

The primary business unit record. One row per operational BU, holding the identity fields used across the inventory and platform UIs, the hotel and company info blocks, the branding file tokens, the formatting/locale block, the config and info JSON columns, the calculation method, the database-pool pointer, and the full audit/soft-delete trio.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| **— Identity —** | | | | |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `cluster_id` | `String @db.Uuid` | No | — | FK to `tb_cluster.id`; determines which cluster owns this BU |
| `code` | `String @db.VarChar(30)` | No | — | Short identifier for the BU. **Server-generated, not user-entered** (SPA PR #279): the create form never sends `code` — `micro-cluster`'s `business-unit.service.ts` calls `generateBusinessUnitCode()` (`business-unit-code.helper.ts`) when the caller supplies none, producing an 8-character Crockford-base32 string (alphabet excludes `I`/`L`/`O`/`U`, e.g. `7K3M9Q2X`), and retries up to `MAX_CODE_ATTEMPTS` (5) on a `code`-column unique-constraint collision before giving up. If a caller *does* supply a `code` and it collides, the request fails immediately with `BUSINESS_UNIT_ALREADY_EXISTS` rather than being retried — the code path assumes only auto-generated values are safe to regenerate. **Unique platform-wide, not per-cluster** (see Constraints below) — this reverses what the last sync documented. |
| `name` | `String` | No | — | Full display name of the BU. Unique within its cluster among live rows — enforced by `business_unit_cluster_name_u` (Constraints below), which is also the field the create/update duplicate-submission guard keys on (a generated `code` differs on every submit, so a code-keyed guard could never catch a double submit) |
| `alias_name` | `String? @db.VarChar(10)` | Yes | — | Short alias (up to 10 chars); shown in compact UI surfaces. Bounded independently of `tb_cluster.alias_name` (`VarChar(3)`) — the SPA's `BU_ALIAS_MAX` constant (`businessUnitEdit/types.ts`) exists specifically because `validateField` used to dispatch on the shared field *name* `alias_name` and apply the tighter cluster bound to BUs too |
| `description` | `String?` | Yes | — | Optional free-text description |
| `info` | `Json?` | Yes | — | Free-form metadata blob; present in Prisma only — no longer carried on the `BusinessUnit` TS interface and not written or read by `BusinessUnitEdit.tsx`. Reserved for extensibility — see §5. |
| **— Status —** | | | | |
| `is_hq` | `Boolean?` | Yes | `true` | Marks this BU as the headquarter unit within its cluster. Uniqueness is enforced at the application layer only — Prisma declares no `@@unique` constraint on `(cluster_id, is_hq)`, so the schema permits multiple HQ flags per cluster. Prisma default is `true`; SPA `BusinessUnitEdit` `initialFormData` defaults to `false`. |
| `is_active` | `Boolean?` | Yes | `true` | When `false`, the BU is considered inactive |
| **— Database pool —** | | | | |
| `database_pool_id` | `String? @db.Uuid` | Yes | — | **New since the last sync**, replacing `db_connection` (removed). FK to `tb_database_pool.id` (§2.4) — the shared database server this BU's tenant schema lives on. `NULL` means not yet configured. |
| `db_schema` | `String? @db.VarChar` | Yes | — | **New since the last sync**, replacing `db_connection`. The BU's own schema name inside `database_pool_id`'s server. Free text, validated client-side against a Postgres-identifier pattern (`^[A-Za-z_][A-Za-z0-9_]{0,62}$`) when non-empty — see [UI Screens](/en/platform/business-units/ui-screens) §4 (Technical tab) for the "Generate schema" randomizer. |
| **— Modules-config —** | | | | |
| `config` | `Json?` | Yes | — | Array of `BusinessUnitConfig` objects (`{ id?, key, label, datatype?, value? }`); editable key/value pairs maintained via the SPA config panel — see §5 |
| **— License —** | | | | |
| `default_currency_id` | `String? @db.Uuid` | Yes | — | FK (logical, no Prisma `@relation`) to the default currency for this BU; displayed via the currency selector in `BusinessUnitEdit.tsx` |
| `calculation_method` | `enum_calculation_method` | No | `average` | Costing method used for inventory valuation: `average` or `fifo` |
| ~~`max_license_users`~~ | — | — | — | **Removed.** Physically dropped by migration `20260821000000_drop_bu_max_license_users`. Seats are now dated purchase rows in `tb_business_unit_license` (§2.3), summed via view `v_business_unit_seat`. |
| **— Company —** | | | | |
| `branch_no` | `String?` | Yes | — | Thai tax branch number (สาขา) for the BU's company entity |
| `company_name` | `String?` | Yes | — | Legal company name for the BU |
| `company_address_line1` | `String?` | Yes | — | Company address line 1 |
| `company_address_line2` | `String?` | Yes | — | Company address line 2 |
| `company_sub_district` | `String?` | Yes | — | Company sub-district (ตำบล/แขวง) |
| `company_district` | `String?` | Yes | — | Company district (อำเภอ/เขต) |
| `company_city` | `String?` | Yes | — | Company city |
| `company_province` | `String?` | Yes | — | Company province |
| `company_postal_code` | `String?` | Yes | — | Company postal code |
| `company_country` | `String?` | Yes | — | Company country |
| `company_latitude` | `String?` | Yes | — | Company address latitude (stored as text, not a numeric/geo type) |
| `company_longitude` | `String?` | Yes | — | Company address longitude (stored as text, not a numeric/geo type) |
| `company_email` | `String?` | Yes | — | Company email address |
| `company_tel` | `String?` | Yes | — | Company telephone number |
| `tax_no` | `String?` | Yes | — | Thai tax identification number (เลขภาษี) |
| **— Hotel —** | | | | |
| `hotel_name` | `String?` | Yes | — | Property/hotel name (may differ from company name) |
| `hotel_address_line1` | `String?` | Yes | — | Hotel/property address line 1 |
| `hotel_address_line2` | `String?` | Yes | — | Hotel/property address line 2 |
| `hotel_sub_district` | `String?` | Yes | — | Hotel/property sub-district (ตำบล/แขวง) |
| `hotel_district` | `String?` | Yes | — | Hotel/property district (อำเภอ/เขต) |
| `hotel_city` | `String?` | Yes | — | Hotel/property city |
| `hotel_province` | `String?` | Yes | — | Hotel/property province |
| `hotel_postal_code` | `String?` | Yes | — | Hotel/property postal code |
| `hotel_country` | `String?` | Yes | — | Hotel/property country |
| `hotel_latitude` | `String?` | Yes | — | Hotel/property address latitude (stored as text, not a numeric/geo type) |
| `hotel_longitude` | `String?` | Yes | — | Hotel/property address longitude (stored as text, not a numeric/geo type) |
| `hotel_email` | `String?` | Yes | — | Hotel/property email address |
| `hotel_tel` | `String?` | Yes | — | Hotel/property telephone number |
| **— Concurrency —** | | | | |
| `doc_version` | `Int` | No | `0` | Optimistic-concurrency token, added platform-wide (35 tables) on 2026-07-16. The edit page resends it with every `PUT`; a stale write is rejected with `409` and the SPA reloads the record with a conflict toast instead of overwriting silently |
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

**Constraints — read this before trusting the Prisma `@@unique` line below:**
- `@id` on `id`
- `@@unique([cluster_id, code, deleted_at], map: "business_unit_cluster_code_deleted_at_u")` — **declared but functionally inert against live rows.** The schema's own doc-comment (directly above this model) warns not to read this as "codes are unique per cluster among active rows": Postgres unique indexes treat `NULL <> NULL`, this index does not declare `NULLS NOT DISTINCT`, and every active row's `deleted_at` is `NULL` — so no two active rows sharing `(cluster_id, code)` will ever collide against *this* index. The real constraints are the two partial-unique indexes below, which exist only in migration SQL because Prisma cannot express a `WHERE` clause inside `@@unique`, and which `prisma db pull` cannot see:
  - **`business_unit_code_global_u`** — `(code) WHERE deleted_at IS NULL`, added by migration `20260904000000_business_unit_code_global_unique`. **`code` is unique across the entire platform, not just within a cluster** — this reverses the last sync's documented behavior.
  - **`business_unit_cluster_name_u`** — `(cluster_id, name) WHERE deleted_at IS NULL`, added by migration `20260904010000_business_unit_cluster_name_unique`. A BU's `name` must be unique within its own cluster among live rows; a violation returns `BUSINESS_UNIT_ALREADY_EXISTS` (409) on both create and update.
- FK: `cluster_id` → `tb_cluster.id` (NoAction / NoAction) — Prisma relation `tb_cluster`
- FK: `database_pool_id` → `tb_database_pool.id` (NoAction / NoAction) — Prisma relation `tb_database_pool`, nullable
- FK: `created_by_id` → `tb_user.id` (NoAction / NoAction) — Prisma named relation `"tb_business_unit_created_by_idTotb_user"`
- FK: `updated_by_id` → `tb_user.id` (NoAction / NoAction) — Prisma named relation `"tb_business_unit_updated_by_idTotb_user"`

**Indexes:**
- `@@index([cluster_id, deleted_at])` — map `"business_unit_cluster_deleted_at_idx"` — supports cluster-scoped BU listing
- `@@index([code, deleted_at])` — map `"business_unit_code_deleted_at_idx"` — supports code lookup
- `@@index([cluster_id, code, deleted_at])` — map `"business_unit_cluster_code_deleted_at_idx"` — composite; overlaps with the (inert) unique constraint but retained as an explicit index for query planning
- `@@index([database_pool_id])` — map `"business_unit_database_pool_idx"` — new, supports the pool→BUs lookup direction

### 2.2 `tb_business_unit_tb_module`

Many-to-many join that activates which platform modules are enabled for a given business unit. Each row asserts that module `module_id` is active for business unit `business_unit_id`. The M:N activation means a BU can have any subset of the available modules enabled; adding or removing a module creates or soft-deletes a row in this table. The full module catalog lives in `tb_module` (§2.6), which is referenced but not owned by the BU. Unchanged since the last sync.

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

### 2.3 `tb_business_unit_license` — NEW, the per-BU seat ledger

Replaces the single `max_license_users` integer with dated, individually-purchased seat rows — one row per seat purchase, not one row per BU. This is the table behind the edit page's **Licenses** tab (a tab of its own since PR #276 split it out of the Users tab — see [UI Screens](/en/platform/business-units/ui-screens) §4) and behind `sumActiveLicenses()`/`licenseStatus()` (`src/utils/buLicense.ts`), which the General tab's read-only "Max users" figure and the Licenses tab both call.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key |
| `license_number` | `String @db.VarChar` | No | — | System-issued, format `SEAT-YYMM-####`; immutable after creation. Uniqueness enforced only by a partial unique index in migration SQL (`(license_number) WHERE deleted_at IS NULL`) — the same NULL-vs-NULL trap as `code` above; not expressible as a Prisma `@@unique` |
| `business_unit_id` | `String @db.Uuid` | No | — | FK to `tb_business_unit.id` — the BU this seat purchase belongs to |
| `licensed_users` | `Int @db.Integer` | No | — | Seats this one purchase row grants |
| `start_date` | `DateTime @db.Timestamptz(6)` | No | — | Coverage start |
| `end_date` | `DateTime @db.Timestamptz(6)` | No | — | Coverage end. A row is "active" when `now()` falls in `[start_date, end_date]` inclusive on both ends (`licenseStatus()` in `buLicense.ts`, matching view `v_business_unit_seat`'s `now() >= start_date AND now() <= end_date`) |
| `reference_no` | `String?` | Yes | — | Free-text external reference (PO number, contract id) |
| `note` | `String?` | Yes | — | Free text. A backfill script prefixes migrated rows with `migrated` — the SPA's `isMigratedPlaceholder()` checks for that prefix to flag rows with no real dates yet set |
| `doc_version` | `Int @default(0)` | No | `0` | Optimistic-lock counter; `update`/`cancel` calls must resend it |
| (audit + soft-delete columns) | — | Yes | — | Standard `created_*`/`updated_*`/`deleted_*` trio |

**Seats vs. quota — do not confuse the two license ledgers that touch this module:** `tb_business_unit_license` (this table) counts **user seats for one BU**, summed across every currently-active row. It is unrelated to `tb_cluster_license` (documented from the cluster side in [clusters data-model](/en/platform/clusters/data-model) §2), which counts **how many BUs a cluster may hold** — a completely different dimension, one row per cluster's winning quota purchase, read via `v_cluster_bu_cap`/`v_cluster_bu_quota`. A BU's edit page shows both numbers in different places: the cluster's BU-quota (`bu_cap`/`bu_used`, checked as a pre-flight on create — §2.1's `code` uniqueness note has nothing to do with this) and this BU's own seat count.

**Relationships:**
- FK: `business_unit_id` → `tb_business_unit.id` (NoAction / NoAction) — Prisma relation `tb_business_unit`

**Indexes:**
- `@@index([business_unit_id, deleted_at])` — map `"bu_license_bu_deleted_at_idx"`
- `@@index([end_date])` — map `"bu_license_end_date_idx"` — supports expiry-threshold scans

**SPA read/write surface:** `businessUnitLicenseService.ts` — `getAll(buId)` (nested under the BU), `create`/`update`/`delete`. Creating and editing a license row happens on the full-page form at `/licenses/subscriptions/new` and `/licenses/seats/...` (the `licenses` module, not yet a documented wiki module) — the BU edit page's Licenses tab is **read-only summary + links**, not an inline editor; see [UI Screens](/en/platform/business-units/ui-screens) §4.

### 2.4 `tb_database_pool` (referenced) — NEW, replaces `db_connection`

A BU no longer owns its database credentials. Instead it points at a shared, platform-managed database server record via `database_pool_id`, and supplies only its own `db_schema` name within that server. This table is owned by the `database-pools` module (`/platform/database-pools`, permission `database_pool.read`/`database_pool.manage`) — documented here only to the depth a Business Units reader needs; the full module is out of this page's scope.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | Operator-chosen name, picked when configuring a BU's Technical tab (not derived from the DSN, per current convention — a pool auto-created from a legacy `db_connection` import got named after its own DSN, which the SPA's `isDerivedName()` helper detects to avoid printing the same string twice) |
| `description` | `String?` | Yes | Optional description |
| `host` | `String @db.VarChar` | No | DB server hostname — **never rendered on the Business Units edit page**; visible only to a session holding `database_pool.read` on the Database Pools screen itself |
| `port` | `Int @default(5432)` | No | DB server port |
| `database` | `String @db.VarChar` | No | Database name on that server |
| `username` | `String @db.VarChar` | No | Connection username |
| `password` | `String @db.VarChar` | No | Ciphertext from the backend's `encryptSecret()` — never leaves the service over the API in any form |
| `is_active` | `Boolean @default(true)` | No | Inactive pools stay selectable on a BU that already points at them (so the picker never silently drops a bound value) but are excluded from the "assign a new BU" option list |
| `doc_version` / audit / soft-delete | — | — | Same shape as every other platform table |

**Relationship:** `tb_business_unit.database_pool_id` → `tb_database_pool.id`, one pool serving many BUs (each with its own `db_schema`). **Indexes:** `@@index([deleted_at])`.

**What the Business Units edit page actually shows:** the read-only view (`DatabaseConnectionSection.tsx`) and the picker both display only the pool's **name** and this BU's **schema** — host/port/username/password are deliberately never fetched into this page's state, even in edit mode. A session without `database_pool.read` sees the same name+schema (the BU response embeds `database_pool: { id, name }` directly) but cannot open the pool picker to change it — see [UI Screens](/en/platform/business-units/ui-screens) §4.

### 2.5 `tb_user_tb_business_unit` (BU-side view)

The full field table for `tb_user_tb_business_unit` is documented in [users data-model](../users/data-model.md) §2.3. From the business-unit perspective, the key points are:

- **`business_unit_id` FK** — `String? @db.Uuid` (nullable), FK to `tb_business_unit.id` with `onDelete: NoAction, onUpdate: NoAction`. Removing a BU does not automatically remove join rows — application-layer cleanup is required.
- **`role`** — `enum_user_business_unit_role` (non-nullable, default `user`). Records the per-BU role for this user-BU assignment: `admin` or `user`. This role is independent of the platform RBAC assignments on the user account ([rbac](/en/platform/rbac)) and of `enum_cluster_user_role` on `tb_cluster_user`. See §4 for the full enum definition.
- **`is_default`** — `Boolean?` (default `false`). Marks the BU as the user's default; the inventory application lands the user on their default BU at login. Only one BU per user should carry `is_default = true` at a given time; the uniqueness constraint does not enforce this — it is an application-layer convention.
- **`is_active`** — `Boolean?` (default `true`). Soft-activity flag for the assignment.
- **Cluster-scoping rule** — the Add BU dialog in the user edit screen (`UserEdit.tsx`) filters the available BU list to those BUs whose `cluster_id` matches a cluster the user already belongs to (via `tb_cluster_user`). This scoping is enforced at the application layer, not as a FK constraint — `tb_user_tb_business_unit` does not carry a `cluster_id` column in Prisma.
- **`frees_seat` (SPA-only, backend-optional field)** — not a Prisma column; an optional boolean the backend attaches to a user row when available, read by `BUUser.frees_seat` in the SPA. When a user is active but `frees_seat === false`, the Users tab shows a "Shared" badge — the user holds membership in more than one BU inside the same cluster, so deactivating them here alone would not return a seat to the cluster's shared pool. Being `optional` (not `false`) matters: `undefined` means the backend in this environment hasn't shipped the field yet, and the SPA is explicit about not guessing in that case.
- **Unique constraint** — `@@unique([user_id, business_unit_id, deleted_at])` — map `"user_businessunit_user_business_unit_deleted_at_u"` — allows a user to be re-assigned to a BU after the original assignment is soft-deleted.

### 2.6 `tb_module` (referenced, brief)

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
tb_business_unit  M ─── 1  tb_database_pool                   (via tb_business_unit.database_pool_id, nullable)
tb_business_unit  1 ─── M  tb_business_unit_tb_module  M ─── 1  tb_module
tb_business_unit  1 ─── M  tb_business_unit_license            (per-BU seat purchases)
tb_business_unit  1 ─── M  tb_user_tb_business_unit    M ─── 1  tb_user
tb_business_unit  1 ─── M  tb_subscription_bu                  (billing, out of scope)
tb_business_unit  1 ─── M  tb_application_role                 (application roles, out of scope)
tb_business_unit  self-FK  created_by_id, updated_by_id  → tb_user.id  (audit relations)
```

FK directions (all `onDelete: NoAction, onUpdate: NoAction` unless noted):

- `tb_business_unit.cluster_id` → `tb_cluster.id`
- `tb_business_unit.database_pool_id` → `tb_database_pool.id` (nullable — a BU may have no pool assigned yet)
- `tb_business_unit.created_by_id` → `tb_user.id` — Prisma named relation `"tb_business_unit_created_by_idTotb_user"`
- `tb_business_unit.updated_by_id` → `tb_user.id` — Prisma named relation `"tb_business_unit_updated_by_idTotb_user"`
- `tb_business_unit_tb_module.business_unit_id` → `tb_business_unit.id`
- `tb_business_unit_tb_module.module_id` → `tb_module.id`
- `tb_business_unit_license.business_unit_id` → `tb_business_unit.id`
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

`config` is stored as `Json?` in Prisma and is typed as `BusinessUnitConfig[] | null` in the SPA (`src/types/index.ts`). The `BusinessUnitConfig` interface has the shape:

```
BusinessUnitConfig {
  id?:       string      -- optional; row identifier if persisted
  key:       string      -- config key name (operator-defined)
  label:     string      -- display label shown in the SPA config panel
  datatype?: string      -- optional type hint (not enforced) — string/number/boolean/date/enum/json
  value?:    unknown     -- the config value
}
```

The SPA surfaces this as an editable list on the edit page's Technical tab: operators can add rows (empty `{ key, label, datatype, value }` objects are appended), edit individual fields, and remove rows. The key namespace is entirely open-ended — there is no fixed set of recognised keys declared in either the Prisma schema or the SPA type definitions. On save, `buildPayload()` keeps only rows where both `key` and `label` are non-empty.

Because the keys are operator-defined, this page cannot enumerate them. If your team uses specific `config` keys (e.g. for fiscal year settings, tax-inclusive flags, or integration credentials), document them in the BU's operational runbook.

### `info` — free-form metadata blob

`info` is stored as `Json?` in Prisma but has **no representation in the SPA at all**: the field has been dropped from the `BusinessUnit` TS interface (it previously appeared as `info?: unknown`), and there is no edit path for it in `BusinessUnitEdit.tsx` or its extracted sections — the SPA does not read or write any key under `info` for the BU. The column appears to be reserved for future extensibility, analogous to the `info Json? @db.Json` column on `tb_cluster` which is also documented as a free-form metadata blob with no currently documented key structure.

## 6. Divergences from carmen-platform SPA shape

The `BusinessUnit` interface in `../carmen-platform/src/types/index.ts` and the `BusinessUnitFormData` interface in `../carmen-platform/src/pages/businessUnitEdit/types.ts` were compared against the current Prisma `tb_business_unit` model.

| # | Item | Prisma has | SPA expects | Notes |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `cluster_name` | Not present on `tb_business_unit` | `cluster_name?: string` on `BusinessUnit` interface | API-resolved display name for the cluster; the Prisma model carries only `cluster_id`. Not in `BusinessUnitFormData` — read-only display field. |
| 2 | Audit columns | `created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id` (flat columns, raw IDs) | Nested `audit` object — `audit.created`, `audit.updated`, `audit.deleted`, each an `AuditEntry` `{ at, id, name, avatar }` | The API resolves the `_id` FKs to actor names and groups everything under `audit`. Both the list page and the edit page read every audit value through the shared `normalizeAudit()` helper now, which tolerates the older flat shape too, preferring it when present. |
| 3 | `max_license_users` | **Column dropped** — does not exist | Not present on `BusinessUnit`; not present in `BusinessUnitFormData` | Fully removed from both sides since the last sync (item was previously a form-string-vs-Prisma-Int divergence; the divergence itself no longer exists because the field is gone). See §1 and §2.3. |
| 4 | `amount_format` / `quantity_format` / `recipe_format` / `perpage_format` | `Json?` (JSON objects) | Typed as `string?` on `BusinessUnit` interface; `string` in `BusinessUnitFormData` | The SPA serialises these JSON objects to strings for plain text inputs (`toJsonString()` helper) and parses them back before the API call. The `BusinessUnit` read interface types them as `string?` rather than `Json`, which reflects the serialised wire shape rather than the Prisma storage shape. |
| 5 | `db_connection` | **Column dropped** — does not exist | Not present; replaced by `database_pool_id: string` / `db_schema: string` on `BusinessUnitFormData`, and `database_pool_name: string` (read-only display, never sent back) | **Structural change, not a value-shape divergence.** The BU no longer holds any database credential fields at all — see §1 and §2.4. `objectToDbFields`/`dbFieldsToObject`/`SAFE_DB_CONNECTION_KEYS` and the guarded password-reveal endpoint documented at the last sync no longer exist anywhere in the SPA. |
| 6 | `config` | `Json?` | `config?: BusinessUnitConfig[] | null` on `BusinessUnit`; `config: BusinessUnitConfig[]` in `BusinessUnitFormData` | The only JSON column with a structured TS type; programmatic reads and writes should use `BusinessUnitConfig[]` from `src/types/index.ts` rather than raw `Json` or `unknown`. The Data Type selector offers `enum` alongside `string`/`number`/`boolean`/`date`/`json` — not itself a distinct Prisma-level constraint, just a UI hint stored in `datatype`. |
| 7 | `info` | `Json?` | Not present | Dropped from the `BusinessUnit` read interface (previously `info?: unknown`); never in `BusinessUnitFormData`. Prisma-only column with no SPA path — see §5. |
| 8 | Branding | `logo_file_token`, `avatar_file_token` (`String? @db.VarChar` storage tokens) | `logo?: PresignedImage \| null`, `avatar?: PresignedImage \| null` — embedded objects `{ url, expires_at }` on list and detail responses | Read responses never carry the raw tokens. Images are written through dedicated multipart endpoints (`POST /api-system/business-units/:id/logo` with form field `logo`, `POST /api-system/business-units/:id/avatar` with form field `avatar`), each returning `{ file_token, url, expires_at }`; the regular `PUT` update payload does not carry branding fields. |
| 9 | `doc_version` | `Int @default(0)` | `doc_version?: number` on `BusinessUnit` | Aligned, not a divergence — both sides carry the optimistic-lock counter (added 2026-07-16). |
| 10 | `code` | `String @db.VarChar(30)`, no `@default` — caller (or the generator) must supply it | `code: string` on `BusinessUnit`; **absent from the create payload, stripped from the update payload** | `BusinessUnitEdit.tsx`'s `buildPayload()` deletes `code` unconditionally before every submit — the platform assigns it on create and ignores any value sent on update. The form still displays it (read-only) once a BU exists. See §2.1. |

All core identity, hotel info, company info, format, locale, and soft-delete fields align between Prisma and the SPA shapes, as does the `doc_version` counter (item 9). The two structural removals (items 3 and 5) are the most consequential changes since the last sync — anything written against the old `max_license_users`/`db_connection` shapes needs to be re-derived from §2.3/§2.4 instead.

## 7. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (commit `1aaab3c`, 2026-09-05) — `model tb_business_unit`, `model tb_business_unit_tb_module`, `model tb_business_unit_license` (line 1133), `model tb_database_pool` (line 1382), `model tb_module`, `model tb_user_tb_business_unit`, `enum enum_user_business_unit_role`, `enum enum_calculation_method`. Line numbers shift often on this file (licensing models keep growing) — search by model name rather than trusting a cached line number.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260821000000_drop_bu_max_license_users/` — drops `max_license_users`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260904000000_business_unit_code_global_unique/` and `.../20260904010000_business_unit_cluster_name_unique/` — the two partial-unique indexes that actually enforce code/name uniqueness (§2.1 Constraints).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/business-unit/business-unit.service.ts` — `createBusinessUnit()`: the BU-quota pre-flight check, the name-keyed duplicate-submission guard, and the `code`-generation retry loop.
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/business-unit/business-unit-code.helper.ts` — `generateBusinessUnitCode()` (Crockford base32, 8 chars, `randomBytes`-backed).

**Secondary (consumer shape):**
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` — orchestrator: tab state, `buildPayload` (strips `code`, diffs `database_pool_id`/`db_schema` against the last-saved snapshot before including them), `doc_version` wiring, logo/avatar upload handlers, the pool-repoint confirm gate.
- `../carmen-platform/src/pages/businessUnitEdit/types.ts` — `BusinessUnitFormData` interface and `initialFormData` defaults.
- `../carmen-platform/src/pages/businessUnitEdit/BusinessUnitLicensesCard.tsx`, `useLicenseLedger` (`src/pages/licenses/useLicenseLedger.ts`), `src/utils/buLicense.ts` (`licenseStatus`, `sumActiveLicenses`, `isExpiringSoon`) — the Licenses tab's read model.
- `../carmen-platform/src/pages/businessUnitEdit/sections/DatabaseConnectionSection.tsx`, `src/utils/databasePool.ts` (`generateSchemaName`) — the pool picker and schema-name randomizer.
- `../carmen-platform/src/services/businessUnitService.ts`, `businessUnitLicenseService.ts`, `databasePoolService.ts` — REST clients.
- `../carmen-platform/src/types/index.ts` — `BusinessUnit`, `BusinessUnitConfig`, `BusinessUnitLicense`, `DatabasePool`, `PresignedImage`, `Audit`/`AuditEntry`.

**Cross-links:**
- [business-units](/en/platform/business-units) — module landing page
- [clusters data-model](/en/platform/clusters/data-model) — parent entity (`tb_cluster`), and the *other* license ledger (`tb_cluster_license`, BU-quota) that this page's §2.3 note distinguishes from
- [users](/en/platform/users) — full `tb_user_tb_business_unit` field table and `enum_user_business_unit_role` canonical doc
- [UI Screens](/en/platform/business-units/ui-screens) — SPA screens for BU management
