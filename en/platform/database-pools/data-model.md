---
title: Database Pools — Data Model
description: The full tb_database_pool field table — encrypted password, note vs. description, is_active semantics — plus how it reconciles with what Business Units and Tenant Migrations already document about resolving a tenant connection.
published: true
date: '2026-09-06T21:00:00.000Z'
tags: book/platform, database-pools, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Database Pools — Data Model

> **Source of truth:** read these before updating this page.
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1382-1411` — `model tb_database_pool`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/database-pool.service.ts` — `POOL_SELECT`, `maskPassword`, `passwordPatch`, `create`, `update`, `delete` (read in full)
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrate.database-pool.ts` — the one-off `db_connection` → pool backfill (read in full)
> - `../carmen-turborepo-backend-v2/packages/secret-crypto/src/crypto.util.ts` — `encryptSecret`/`decryptSecret`
> - `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts` — `buildTenantUrl`/`resolveTenantUrl`
>
> Verified against `carmen-platform` HEAD `157a65e` (2026-09-04) and `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06).

## 1. Overview

`tb_database_pool` is a flat table with no child tables of its own — one row per registered Postgres server, referenced from exactly one place: `tb_business_unit.database_pool_id`. It replaced `tb_business_unit.db_connection`, a per-BU JSON blob (`{ host, port, database, schema, user, password }`, with a **plaintext** password) that was physically dropped from the schema on 2026-08-13. This page documents the table's full field set, how a password moves from plaintext input to encrypted storage and back, and — since [Business Units](/en/platform/business-units/data-model) §2.4 and [Tenant Migrations](/en/platform/tenant-migrations/data-model) §3 both already describe this table for their own narrower purposes — exactly how this page's account lines up with theirs (§5).

## 2. Entity: `tb_database_pool`

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | Operator-chosen, picked from the create/edit form or — for a pool the legacy backfill auto-created — derived from its own DSN (`host:port/database`, or with `(username)` appended when two auto-created pools would otherwise share that string). Must be unique among non-deleted pools; a duplicate on create or on renaming an existing pool returns `DATABASE_POOL_NAME_EXISTS` (409). |
| `description` | `String?` | Yes | Free-text operator note about the pool (e.g. "Singapore production cluster"). Shown on the edit-page record view only when set. |
| `host` | `String @db.VarChar` | No | Server hostname. **Never rendered on the Business Units edit page** ([UI Screens](/en/platform/business-units/ui-screens) §4.4) — visible only to a session with `database_pool.read` on this module's own screens. |
| `port` | `Int @default(5432) @db.Integer` | No | TCP port; the create/edit form validates it client-side as an integer 1–65535 and defaults to 5432 if left blank on submit. |
| `database` | `String @db.VarChar` | No | Database name on that server. |
| `username` | `String @db.VarChar` | No | Connection username — a raw database login, not validated as an email (the shared `validateField('username')` case, written for the Users module, is deliberately not reused here). |
| `password` | `String @db.VarChar` | No | Ciphertext from `encryptSecret()` (AES-256-GCM, `enc:v1:<iv_b64>:<authTag_b64>:<ciphertext_b64>`, `../carmen-turborepo-backend-v2/packages/secret-crypto/src/crypto.util.ts`). See §4 for the full lifecycle — **its plaintext value never appears in any API response, in this page, or in this wiki.** |
| `is_active` | `Boolean @default(true) @db.Boolean` | No | See §3 for its effect on the Business Units picker and on connection resolution. |
| `note` | `String?` | Yes | Distinct column from `description` (`schema.prisma:1398`). Set automatically by the legacy backfill script to the fixed, Thai-language value `'สร้างอัตโนมัติจาก tb_business_unit.db_connection'` ("auto-created from `tb_business_unit.db_connection`") on every pool it created from an old BU's connection blob (`migrate.database-pool.ts:412`) — a flag that the record was not hand-configured, not a general-purpose comment field, though the create/edit form does let an operator set or change it freely afterward. |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-lock counter. **Required, not optional, on every `PUT`** — `DatabasePoolUpdateDto` has no default and the backend rejects an update where `data.doc_version` is not a number (`COMMON_DOC_VERSION_REQUIRED`), unlike some sibling entities where an absent token is read as "skip the conflict check." |
| `created_at` / `created_by_id` / `updated_at` / `updated_by_id` / `deleted_at` / `deleted_by_id` | `DateTime?` / `String? @db.Uuid` | Yes | Standard audit/soft-delete columns, rendered through the shared `auditColumns()`/`normalizeAudit()` helpers on the list and edit pages. |

**Selected fields, not all columns fetched by every query.** `DatabasePoolService`'s `POOL_SELECT` constant (`database-pool.service.ts:11-27`) is the complete field list above minus `deleted_at`/`deleted_by_id` — the service filters on `deleted_at: null` at the query level rather than returning it to the client.

**Index:** `@@index([deleted_at], map: "database_pool_deleted_at_idx")`. No unique database constraint on `name` is declared in Prisma — the uniqueness the API enforces (§2 above) is an application-level `findFirst` check in `create()`/`update()`, not a `@@unique`.

## 3. Relationship to `tb_business_unit`

```
tb_database_pool  1 ─── M  tb_business_unit   (via tb_business_unit.database_pool_id, nullable)
```

- `tb_business_unit.database_pool_id` — `String? @db.Uuid`, nullable FK to `tb_database_pool.id`, `onDelete: NoAction`. `NULL` means the business unit has never been pointed at a pool.
- `tb_business_unit.db_schema` — `String? @db.VarChar`, the BU's own schema name **inside** that pool's `database`. Not a column on this table — it lives on the business unit, one per BU, because the pool (the server + database) is shared while the schema is not.
- A pool with one or more live (`deleted_at: null`) business units still pointing at it **cannot be deleted**: `DatabasePoolService.delete()` looks up to 10 such business units by `code` and returns `DATABASE_POOL_IN_USE` (409) naming them, rather than deleting the pool out from under a BU that still resolves its tenant connection through it.
- `is_active: false` does not block this in-use check — an inactive pool with live BUs still attached is still "in use" and still cannot be deleted. `is_active` only affects the Business Units *picker* (an inactive pool stays selectable on a BU already bound to it, but drops out of the option list for assigning a **new** BU) and tenant **connection resolution** (§5): an inactive pool makes every BU pointing at it fail to resolve a connection, without needing to be deleted first.

## 4. Secrets and Encryption

1. **Input.** The create form requires a plaintext password (blank fails client-side validation, and is independently rejected server-side as `COMMON_VALIDATION_FAILED` if it somehow reaches the API). The edit form's password field is optional and starts empty even when loaded for an existing pool — the API never sends the real value back, so there is nothing to prefill.
2. **At rest.** `encryptSecret()` produces `enc:v1:<iv>:<authTag>:<ciphertext>` under `SECRET_ENCRYPTION_KEY` (32 bytes, hex or base64, read once and cached per process). The key has no code-level default: `getKey()` throws immediately if the env var is unset, and both `micro-cluster`'s and `micro-business`'s `config.env.ts` declare it as a required non-empty string at startup, not an optional one with a fallback.
3. **In every API response.** `maskPassword()` (`database-pool.service.ts:40-42`) replaces the ciphertext with the literal string `••••••` before the row ever leaves the service — list, get, and the row returned by create/update all mask it identically. **No endpoint in this codebase reveals the decrypted or even the encrypted value.**
4. **On update.** `passwordPatch()` (`database-pool.service.ts:50-54`) treats an `undefined` incoming value **or the exact mask string** as "no change" (returns `{}`, leaving the stored ciphertext untouched); an empty string or any non-string value is rejected as invalid; only a genuinely different plaintext string is re-encrypted and stored. This is what makes it safe for the edit form to always send back whatever masked/blank value it holds without accidentally overwriting a real password with the mask itself.
5. **On use.** Nothing in this module decrypts a pool's password — that happens only when a *consumer* resolves a tenant connection. [Tenant Migrations](/en/platform/tenant-migrations/data-model) §3 documents that path: `resolveTenantUrl()` (`../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts`) calls `decryptSecret()` and, on failure, throws rather than falling back to any plaintext guess — "no fallback on purpose," per that function's own comment — then `buildTenantUrl()` assembles `postgresql://{user}:{password}@{host}:{port}/{database}?schema={db_schema}` with `host`/`port` validated (`isSafeHost`/`isSafePort`) and every other part percent-encoded.
6. **Backfill provenance.** The one-off `migrate.database-pool.ts` script (§1) is the only place in the codebase that ever read a plaintext password from `db_connection` directly; it is dry-run by default, requires `--apply` to write, and has a separate `--verify` mode that decrypts every live pool's password and reports which pool *names* (never ciphertext or plaintext) fail to decrypt under the currently configured key — meant to be run once, immediately before the `db_connection`-dropping migration lands. The script is unable to run its scan/backfill path today: it depends on the `db_connection` column that migration `7f825bb20` already removed. It remains in the repository only as a record of how the one-time migration was performed, per its own header comment.

No hardcoded default password, connection string, or encryption key was found anywhere in this module's frontend, backend, or the backfill script — checked `DatabasePoolEdit.tsx`'s `emptyForm`/`buildPayload` (empty strings only, no literal credential), `database-pool.service.ts` (encrypts whatever is supplied, no fallback value), and `crypto.util.ts` (throws rather than defaulting). This is worth stating explicitly because a sibling module in this book was corrected for exactly this kind of claim: see [Platform Migrations](/en/platform/platform-migrations) §3.1, whose `PLATFORM_DEPLOY_TOKEN` **does** default to an empty string in `config.env.ts`.

## 5. Consistency with Business Units and Tenant Migrations

Both sibling pages already describe this table, each to the depth their own readers need. This page agrees with both and is the one place a reader should come for the complete field list.

- **[Business Units — Data Model](/en/platform/business-units/data-model) §2.4** documents `id`, `name`, `description`, `host`, `port`, `database`, `username`, `password`, `is_active`, and the audit/soft-delete trio — nine of the ten real columns, explicitly scoped ("documented here only to the depth a Business Units reader needs; the full module is out of this page's scope"). It omits `note` only because that page has no reason to mention it; nothing it states about the other nine fields, the relationship direction, or the `db_connection` removal is inconsistent with §2–3 above.
- **[Tenant Migrations — Data Model](/en/platform/tenant-migrations/data-model) §3** documents the subset of fields that feed `resolveConnectionForBusinessUnit()` — `host`, `port`, `database`, `username`, `password`, `is_active`, `deleted_at` — framed as "Role here," and its five-row error table (not linked to a pool / no schema configured / pool deleted / pool inactive / password fails to decrypt) matches `tenant.service.ts` exactly as read for this page. No divergence found.
- Both pages state, and this page confirms independently from `migrate.database-pool.ts` and the two 2026-08-13 migrations, that `db_connection` is **physically dropped**, not merely deprecated, and that `database_pool_id`/`db_schema` are the only path to a business unit's tenant connection today.

## 6. Edge Cases

| Scenario | What actually happens | Source |
|---|---|---|
| A pool with live business units attached is deleted | Refused (409 `DATABASE_POOL_IN_USE`), naming up to 10 blocking BUs by `code` | `database-pool.service.ts:247-272` |
| A pool is deactivated (`is_active: false`) while BUs still point at it | Not blocked — deactivation is not the in-use check. Every dependent BU's tenant connection resolution then fails with "is inactive" the next time [Tenant Migrations](/en/platform/tenant-migrations/data-model) §3 tries to resolve it | `tenant.service.ts` (per that page); `database-pool.service.ts` (no active-check on update) |
| Two business units' legacy `db_connection` values agreed on host/port/database/username but disagreed on password | The backfill script refuses to guess and stops the entire run with an error naming both business unit codes — a data conflict it treats as requiring a human fix, not something to silently pick one side of | `migrate.database-pool.ts:338-345` |
| A legacy `db_connection` had no `schema` value | That business unit is skipped by the backfill (counted and reported, not silently dropped) rather than migrated with a guessed schema | `migrate.database-pool.ts:316-319` |
| `SECRET_ENCRYPTION_KEY` differs between `micro-cluster` (which encrypts on write) and `micro-business` (which decrypts to resolve a connection) | Every affected pool fails to decrypt at connection-resolution time with "Failed to decrypt the database pool password (check `SECRET_ENCRYPTION_KEY`...)" — the mismatch surfaces as a tenant-migration/connection failure, not as a config-validation error at either service's startup | `crypto.util.ts` (per-service key, no cross-service check); `tenant-url.ts:58-68` |
| A `database_pool.read`-only session opens `/platform/database-pools/new` | Sees and can fill in every field of the create form; cannot submit it through the Save button (not rendered) or through Enter/`Ctrl+S` (`handleSubmit` itself checks `hasPermission('database_pool.manage')` and returns early) — see [landing page](/en/platform/database-pools) §4 | `DatabasePoolEdit.tsx:260`, `App.tsx:517` |

## 7. Recommendations

- **Add a `@@unique` constraint on `name`** (scoped to non-deleted rows, matching the pattern used elsewhere in this schema, e.g. `business_unit_code_global_u`) so the uniqueness this module already enforces at the application layer is also guaranteed at the database layer against a second write path this module does not control (a future backend service, a script, a manual `psql` insert).
- **Consider gating `/platform/database-pools/new` and `/:id/edit` on `database_pool.manage` at the route level**, matching how [Business Units](/en/platform/business-units) gates its own `/new` and `/:id/edit` routes on the create/update permission rather than the read one — the current `database_pool.read`-on-every-route setup (§4, landing page) is not exploitable given the in-form checks, but it is also not the pattern this book's other CRUD modules follow.
- **Run `migrate.database-pool.ts --verify` on a schedule**, not only immediately before the `db_connection`-drop migration it was written for — a `SECRET_ENCRYPTION_KEY` rotation performed without re-encrypting existing pools would otherwise only be discovered the next time someone tries to resolve a tenant connection.

## 8. References

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1382-1411` — `model tb_database_pool`.
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/database-pool.service.ts` — read in full.
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/database-pool.controller.ts` — RPC message handlers, read in full.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_database-pools/platform_database-pools.service.ts` — RPC proxy from the gateway.
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts:515-517`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260813000000_database_pool_additive/` (commit `343b8c16b`) and `.../20260813010000_database_pool_drop_db_connection/` (commit `7f825bb20`).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrate.database-pool.ts` — read in full.
- `../carmen-turborepo-backend-v2/packages/secret-crypto/src/crypto.util.ts`, `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts`.
- `../carmen-platform/src/pages/DatabasePoolEdit.tsx`, `src/utils/databasePool.ts`.
- [Business Units — Data Model](/en/platform/business-units/data-model) §2.4; [Tenant Migrations — Data Model](/en/platform/tenant-migrations/data-model) §3 — cross-checked in §5 above.
