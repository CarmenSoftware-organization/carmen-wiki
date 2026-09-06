---
title: Platform Config — Data Model
description: tb_platform_config, a namespace-per-row key/value table; the full ten-key PLATFORM_CONFIG_REGISTRY (eight shown on this module's own screen, two owned by other modules); and the multi-process reader map behind each key's real-world effect.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, platform-config, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Platform Config — Data Model

> **At a Glance**
> **`tb_platform_config`** — one row per config *namespace* (a JSON object), never a single scalar value &nbsp;·&nbsp; **`PLATFORM_CONFIG_REGISTRY`** (micro-cluster) — the single source of truth for which keys exist, their Zod read/write schemas, and their defaults; ten keys total, eight rendered by this module's own screen (§3) &nbsp;·&nbsp; **Validated twice, independently:** the gateway controller checks the `:config_key` path segment against a regex before it reaches any service; micro-cluster's `PlatformConfigService` separately checks registry membership and the value against the key's own Zod schema &nbsp;·&nbsp; **Concurrency:** `doc_version` exists as a column but is **not** enforced as an optimistic lock by any write path today &nbsp;·&nbsp; **No cache on the admin screen itself** — `GET /api-system/platform/configs` always reads live; the 60-second caches documented on the [landing page](/en/platform/platform-config) §3.2 belong to three specific *downstream enforcement readers*, not to this table's own read/write service

> **Source of truth:** the backend Prisma platform schema and the micro-cluster registry that defines every key. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.service.ts`
>
> Verified against `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) and `carmen-platform` HEAD `157a65e` (2026-09-04).

## 1. Overview

`tb_platform_config` is one table doing duty for at least ten unrelated settings, distinguished only by a `key` string and a `value` JSONB blob. There is no per-key table, no per-key column set — every field of every setting lives inside that one JSON object, and the only thing that says which fields are valid, what type they must be, and what to return when the row does not exist yet is a single in-code registry, `PLATFORM_CONFIG_REGISTRY` (§3), that lives in the **micro-cluster** service, not in the gateway controller this module's UI talks to directly. The gateway (`platform_configs.controller.ts`) is a thin proxy: it enforces the two RBAC gates documented on the [landing page](/en/platform/platform-config) §4, then forwards to micro-cluster over RPC, which is where every value actually gets validated, defaulted, and written.

## 2. Entity: `tb_platform_config`

Schema line 1462 (`../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1462-1477`).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, `gen_random_uuid()` |
| `key` | `String @db.VarChar` | No | The config namespace, e.g. `invitation`, `license` — one of the ten `PLATFORM_CONFIG_KEYS` (§3); anything else is rejected before it reaches this table |
| `value` | `Json @default("{}") @db.JsonB` | No | The entire namespace's settings, as one JSON object — never a scalar |
| `doc_version` | `Int @default(0) @db.Integer` | No | Present on the table; **not read or incremented by any write path found** (§5) |
| audit trio + soft delete | — | Yes | Standard `created_at`/`created_by_id`/`updated_at`/`updated_by_id`/`deleted_at`/`deleted_by_id` |

**Constraints:** `@@unique([key, deleted_at], map: "platform_config_key_u")`. **Indexes:** `(key)`, map `platform_config_key_idx`.

**The unique constraint does not actually constrain live rows.** A unique index on `(key, deleted_at)` only stops two rows from sharing the same `key` **and** the same `deleted_at` value — since every live row has `deleted_at = NULL`, and SQL treats every `NULL` as distinct from every other `NULL` for uniqueness purposes, the database itself does **not** prevent two undeleted rows from existing for the same key. `PlatformConfigService.findAll()`'s own comment states this directly and defends against it structurally rather than relying on the constraint: it queries `orderBy: { updated_at: 'asc' }` and folds the results into a `Map` keyed by `key`, so if a duplicate live row ever exists, the most-recently-updated one silently wins — every other read path (`findOne`, `patch`, `upsert`) independently applies the same `orderBy: { updated_at: 'desc' }` + "take the first" pattern. This is the identical dead-on-active-rows shape the wiki has documented for `tb_business_unit.code`'s uniqueness elsewhere in this book — worth recognizing on sight rather than re-deriving each time.

## 3. `PLATFORM_CONFIG_REGISTRY` — every key, in full

Defined once, `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts:260-369`. Ten keys total; the last two are never rendered by this module's own screen (see the landing page §3.5 for why, and which module owns each instead).

| Key | Fields — type (bounds), default | Shown on this screen? |
| --- | --- | --- |
| `invitation` | `base_url: string (url)` = `http://localhost:3000/invitations`; `expiry_days: int (1–365)` = `7`; `max_per_admin_per_hour: int (positive, no ceiling)` = `100`; `max_per_cluster_per_day: int (positive, no ceiling)` = `500` | Yes — split across two cards (landing §3.1) |
| `signup` | `verify_base_url: string (url)` = `http://localhost:3000/register/verify`; `link_expiry_hours: int (1–720)` = `24` | Yes |
| `email_verification` | `base_url: string (url)` = `http://localhost:3000/verify-email`; `expiry_hours: int (1–720)` = `24` | Yes |
| `password_reset` | `base_url: string (url)` = `http://localhost:3000`; `expiry_hours: int (1–720)` = `24` | Yes |
| `notification_email` | `enabled: boolean` = `false`; `recipients: string[] (email)` = `[]`; `cc: string[] (email)` = `[]`; `subject_prefix: string (max 64)` = `''` | Yes — see landing §3.2 for the "no confirmed reader" finding |
| `license` | `enforcement_enabled: boolean` = `false` | Yes |
| `expiry_thresholds` | `subscription_days: int (1–365)` = `30`; `bu_quota_days: int (1–365)` = `30`; `seat_days: int (1–365)` = `30` | Yes |
| `platform_migration` | `api_enabled: boolean` = `false` | Yes |
| `email_routing` | `default: string (uuid)`; `register`, `verify_email`, `invitation`, `forgot_password`, `notification`: `string (uuid)`, all optional | **No** — edited from the Email Settings module (landing §3.5) |
| `feature_flags` | `Record<string, 'active' \| 'inactive' \| 'hide'>` (free-form key set), default `{}` | **No** — reachable only through its own dedicated `/api-system/platform/feature-flags` pair (landing §3.5) |

**`.default()` is a read-side-only convenience.** Every numeric/boolean field above carries `.default()` on the *read* schema so a row saved before a field existed still parses (`platform-config.schema.ts:146-149`). The *write* schema strips every `.default()` (`toWriteSchema()`, lines 405-434) — a `PATCH` payload that omits a field is genuinely "leave it alone" (merged from the existing stored value, §5), never silently coerced to that field's default.

## 4. Who actually reads each key — the effect behind landing page §3.2

No key in this table is read only by the screen that edits it. This table lists every confirmed reader, its process, and whether it caches.

| Key | Reader(s) | Cache | Fail-direction on an unreadable/invalid row |
| --- | --- | --- | --- |
| `invitation` | micro-cluster's invitation-issuing flow (`PlatformConfigService.getInvitationConfig()`, `platform-config.service.ts:389-397`) | None found — reads live each call | Throws (`parseStored()` throws on a schema mismatch; deliberate — see the service's own comment on why silent fallback is worse than a loud failure for a link an email is about to send) |
| `signup`, `email_verification`, `password_reset` | micro-business's `auth.service.ts` (`readSignupConfig`/`readEmailVerificationConfig`/`readPasswordResetConfig`, lines 319-350), reading `tb_platform_config` directly (a separate process from micro-cluster) | None found — reads live each call | **Throws** — the service's own comment states this explicitly: an invalid stored row means someone edited the database directly, and silently falling back to the default would send a wrong link with no signal, so it fails loudly instead. A **missing** row (never saved) is normal and returns the in-code default without error. |
| `notification_email` | **No confirmed reader** — landing page §3.2 | — | — |
| `license` | `LicenseService.isEnforcementEnabled()` (backend-gateway) **and** `SeatEnforcementFlagService.isEnabled()` (micro-cluster) — two separate processes, two independent 60s caches, both reading the identical row | 60s each, independently | Fails **open in the safe direction**: an unreadable or malformed value reads as `false` (not enforcing) on both sides — a DB hiccup must never turn into a platform-wide 403 |
| `expiry_thresholds` | `ExpiryThresholdsService` in micro-cluster, `ExpiryThresholdsService` in micro-business, and the frontend's own `ExpiryThresholdContext` (via a separate, permission-free endpoint, not this table's own REST surface) | 60s in each of the three | Frontend: silently falls back to in-code defaults, no toast (`ExpiryThresholdContext.tsx:52-54`) — the badge window is stale, everything else on the page still works |
| `platform_migration` | `PlatformMigrationGuard` (backend-gateway) | 60s | Fails **closed**: no row, or an unreadable one, reads as `false` (API disabled) — the opposite fail-direction from `license`, because what this switch guards (`prisma migrate deploy` against the shared platform database) must never be left open by a database hiccup, whereas `license`'s failure-mode priority is "never wrongly block a paying customer" |
| `email_routing` | `platform-email.service.ts` (micro-notification, `PlatformEmailService.resolveSmtpConfig()` and the routing lookup) and the Email Settings module's `useEmailRouting.ts:45` (frontend, via `platformConfigService.getByKey('email_routing')` — the identical generic client this module uses) | Not verified here — out of this module's scope | Not verified here |
| `feature_flags` | Every SPA page, through the dedicated `/api-system/platform/feature-flags` pair, not this table's generic surface | Not verified here | Not verified here |

**Note the fail-direction asymmetry between `license` and `platform_migration` is deliberate, not inconsistent** — both switches share the identical `=== true` (not truthy) parsing and the identical 60-second cache shape, but `license`'s unreadable-row default is `false` = *don't block anyone*, while `platform_migration`'s unreadable-row default is also `false` but that means *keep the migration door shut*. Both defaults point toward the safer outcome for what each switch actually guards — they are not the same safety direction in absolute terms, only in relative terms to their own risk.

## 5. Write-path mechanics

Every write — `PUT` or `PATCH`, either one — is validated and persisted by the same code (`PlatformConfigService.upsert()`/`.patch()`, both ending in a shared `writeValue()`, `platform-config.service.ts:200-236,261-377`), reached through the gateway's proxy (`PlatformConfigsService`, backend-gateway) over RPC. The two entry points differ only in how the value they validate is assembled:

- **`PUT` (`upsert`)** — the caller's payload is validated *as-is* against the write schema (defaults stripped, §3). Every field the schema knows about must be present, or `safeParse` fails and the whole call returns `COMMON_VALIDATION_FAILED`. No card in this module's UI calls this path (landing page §3.4).
- **`PATCH` (`patch`)** — the caller's payload is checked field-by-field against the key's known field list first (`rejectBadPatchShape()`, lines 324-337): an empty object is rejected outright (it would otherwise silently create a full-default row for a key nobody had touched), and any field name the schema does not recognize is rejected by name, never dropped silently. The existing stored value is then read and run through `parseStored()` — not used as raw JSON — specifically so a row saved before a field existed is filled in with that field's default *before* the caller's partial payload is merged on top; only the merged, complete object is validated against the write schema and persisted.

Both paths perform their **own** independent unknown-key check (`isPlatformConfigKey()`, micro-cluster) in addition to the gateway's `KEY_REGEX` (`^[a-zA-Z0-9_.-]+$`) path-segment check (`platform_configs.controller.ts:37`) — a key that passes the regex but is not one of the ten registry entries (e.g. a typo, or a key retired from the registry) is still rejected, with the full list of supported keys echoed back in the error.

`user_id` is required on every write (`upsert`/`patch` both reject a missing one with `COMMON_VALIDATION_FAILED`) — every saved row's `created_by_id`/`updated_by_id` is always attributable.

**`doc_version` is not an active optimistic lock.** The column exists on the table and is never read or incremented by `writeValue()` — two concurrent `PATCH` calls to the same key will both succeed, with the second call's merge silently winning (built from whatever the first call had already committed, or from the pre-first-call value if both reads happened before either write, depending on timing) rather than being rejected for a stale base. The frontend's own service-layer comment (`platformConfigService.ts:29`) states this outright: "the table has that column, but the backend does not yet enforce optimistic locking with it."

## 6. Edge Cases

| Scenario | What actually happens |
| --- | --- |
| Two admins `PATCH` the same key's different fields within the same second | Both succeed; whichever write's `findFirst` ran last wins the base it merges onto — a genuine last-write-wins race on the whole JSON blob, not per-field, since `doc_version` is not enforced (§5) |
| A row is edited directly in the database to a shape that no longer matches its schema | `invitation`/`signup`/`email_verification`/`password_reset` readers **throw** on the next read (fail loud, by design); `license`/`platform_migration` readers treat it as `false` (fail toward their own safe direction, §4); the admin screen's own `GET` (`findAll`/`findOne`) also calls `parseStored()`, so a genuinely broken row would make the **entire Platform Config screen fail to load**, not just the one card — this is the exact risk the schema's own `.default()`-on-every-field comment (§3) exists to minimize for ordinary schema evolution, but it does not protect against a value that never fit the schema in the first place |
| A key is queried before its row has ever been saved | Every read path returns the registry's built-in default with `id: null` — never a 404, never an empty object |
| `PATCH` sent with an empty `{}` body | Rejected — `rejectBadPatchShape()` treats an empty object as "nothing to do," not as "leave everything unchanged" |
| `PATCH` sent with a field name the target key's schema does not recognize | Rejected by name (e.g. `unknown field(s) foo (supported: base_url, expiry_days, ...)`) — never silently dropped |
| `license.enforcement_enabled` toggled on, then off again within the same minute | Both backend-gateway's `LicenseService` and micro-cluster's `SeatEnforcementFlagService` each hold their own independent 60s cache — the two processes can disagree about the current value for up to a minute even from each other, not just from the database |
| A reader on `/platform/configs` holds `platform_config.read` but not `.manage` | Sees every card fully populated in read-only mode (no Edit button anywhere, §4.1 of the landing page) — reading this screen never requires the finer-grained keys documented in landing page §4.4 |

## 7. Recommendations

- **Treat `notification_email` as inert until a consumer is confirmed.** Do not rely on this card's `enabled` toggle in a test plan that expects an actual email to send or not send — no reader was found anywhere in the backend at the time of writing (landing page §3.2).
- **When testing `license`/`platform_migration`, wait for the cache window, or expect a same-minute flip-flop to look inconsistent between processes** — this is expected behavior given each reader's independent 60-second cache (§4), not a bug to file.
- **A `PATCH` with a typo'd field name will fail loudly (422), not silently succeed** — this is intentional; do not "fix" a test that expects the strict rejection.
- **Never write `doc_version` from a client integration expecting it to be enforced** — it is not read by any write path today (§5); a future backend change could start enforcing it, at which point this note should be revisited.

## 8. References

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_platform_config` (line 1462).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` — `PLATFORM_CONFIG_REGISTRY`, every key's schema/default (§3), `toWriteSchema()` (§3, §5).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.service.ts` — `findAll`/`findOne`/`upsert`/`patch`/`writeValue`/`getInvitationConfig` (§2, §5).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_configs/{platform_configs.controller.ts,platform_configs.service.ts}` — the gateway proxy, RBAC gates, `KEY_REGEX` (§5).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/license/{license.service.ts,license.interceptor.ts}` — the `license` key's backend-gateway reader (§4).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/common/{seat-enforcement-flag.service.ts,expiry-thresholds.service.ts}` — the `license`/`expiry_thresholds` keys' micro-cluster readers (§4).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-migration.guard.ts` — the `platform_migration` key's reader (§4).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (lines 273-350, 389-397) — `signup`/`email_verification`/`password_reset` readers (§4).
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/platform-email/platform-email.service.ts`, `apps/micro-notification/CLAUDE.md` — the `email_routing`/`notification_email` consumer search (§4).
- `../carmen-platform/src/services/platformConfigService.ts` — the frontend REST client, including the `doc_version` note (§5).
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx` — the frontend's own `expiry_thresholds` reader and its fallback behavior (§4).

**Cross-links:** [Platform Config landing](/en/platform/platform-config) &nbsp;·&nbsp; [Licenses](/en/platform/licenses)
