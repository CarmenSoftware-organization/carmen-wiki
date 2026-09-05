---
title: Email Settings — Data Model
description: tb_email_sender_profile (named SMTP sender profiles, encrypted credentials) plus the email_routing config shape it is resolved through — and the write-path guarantees (optimistic locking, password-patch semantics, name uniqueness) that differ from the shared platform-config table.
published: true
date: '2026-09-06T18:00:00.000Z'
tags: book/platform, email-settings, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Email Settings — Data Model

> **At a Glance**
> **`tb_email_sender_profile`** — one row per named SMTP sender, `micro-cluster`-owned, `doc_version` **actively enforced** as an optimistic lock on every update (§5) &nbsp;·&nbsp; **`email_routing`** — a `tb_platform_config` row (**not** a column on this table), resolved live by micro-notification for every outbound flow (landing page §3.2-3.3) &nbsp;·&nbsp; **Passwords:** `enc:v1` (AES-256-GCM) at rest, always masked (`••••••`) in every API response, decrypted only inside micro-notification at send time &nbsp;·&nbsp; **Uniqueness is on `name`, not on a purpose** — a stale controller Swagger description still says otherwise (§5) &nbsp;·&nbsp; **Redesigned once:** migration `20260808130000_email_profile_master_and_routing` (2026-08-08) split a one-purpose-per-row table into this named list plus the separate `email_routing` map

> **Source of truth:** the platform Prisma schema, the two migrations that shaped this table, and the two services (`micro-cluster` for CRUD, `micro-notification` for resolution/send). Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/email-sender-profile/email-sender-profile.service.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-notification/src/platform-email/platform-email.service.ts`
>
> Verified against `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) and `carmen-platform` HEAD `157a65e` (2026-09-04).

## 1. Overview

Two things back this screen, and they live in two different tables owned by two different services. `tb_email_sender_profile` (§2) is a named list of SMTP endpoints, CRUD-owned by **micro-cluster** and proxied by the gateway's `platform_email-settings.controller.ts`. `email_routing` (§3) is one row of the **shared** `tb_platform_config` table — the same table and the same generic `/api-system/platform/configs` REST surface the [Platform Config](/en/platform/platform-config) module's own data model documents in full — read and written through that module's client, `platformConfigService`, not this module's own `emailSettingService`. Resolving an outbound flow to an actual SMTP send (§4) requires both: the routing row to name a profile id, and that profile row to exist, be active, and decrypt.

## 2. Entity: `tb_email_sender_profile`

Schema lines 1433-1460 (`../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, `gen_random_uuid()` |
| `name` | `String @db.VarChar` | No | Operator-chosen, picked by name in the routing screen; unique among live rows (§5) — **not** tied to any fixed purpose since the 2026-08-08 redesign |
| `from_email` | `String @db.VarChar` | No | The `From:` address |
| `from_name` | `String? @db.VarChar` | Yes | Optional display name paired with `from_email` |
| `smtp_host` | `String @db.VarChar` | No | SMTP endpoint hostname |
| `smtp_port` | `Int @default(587) @db.Integer` | No | |
| `smtp_secure` | `Boolean @default(false) @db.Boolean` | No | Implicit TLS (the UI's "implicit TLS" checkbox) |
| `smtp_username` | `String? @db.VarChar` | Yes | |
| `smtp_password` | `String? @db.VarChar` | Yes | `enc:v1` ciphertext (AES-256-GCM) — never stored or returned in plaintext (§5) |
| `is_active` | `Boolean @default(true) @db.Boolean` | No | Deactivating a profile that still carries routed flows leaves those flows unable to send (`no-config`, landing page §3.3) — the edit form warns before this happens (`EmailSettingCard.tsx:471-476`) |
| `note` | `String? @db.VarChar` | Yes | |
| `doc_version` | `Int @default(0) @db.Integer` | No | **Actively enforced** as an optimistic lock (§5) — unlike the same-named column on `tb_platform_config` |
| audit trio + soft delete | — | Yes | Standard `created_at`/`created_by_id`/`updated_at`/`updated_by_id`/`deleted_at`/`deleted_by_id` |

**Indexes:** `(deleted_at)`, map `email_sender_profile_deleted_at_idx`; **unique** `(name)` filtered to live rows, map `email_sender_profile_name_live_u` (a partial unique index, `WHERE deleted_at IS NULL` — added by the 2026-08-08 migration, §5).

### 2.1 What this table used to be — and the fossil it left behind

Before migration `20260808130000_email_profile_master_and_routing`, this table carried a `purpose` column typed `enum_email_sender_purpose` (`no_reply` / `support` / `billing`) with a **unique** index on `(purpose, deleted_at)`: exactly one live profile per purpose, full stop, and adding a fourth kind of mail meant an enum value plus a deploy. That migration renamed each existing row after its purpose (`no_reply` → "No-reply", etc.), moved the unique constraint to `name`, dropped the `purpose` column, and seeded the first `email_routing` row pointing every flow at the surviving "No-reply" profile — read the full migration SQL for the exact rename/backfill/dedup logic (`.../20260808130000_email_profile_master_and_routing/migration.sql`).

**The enum type itself was never dropped.** `enum enum_email_sender_purpose` is still declared in the schema (`schema.prisma:1415-1425`), referencing zero columns anywhere — a repository-wide grep for the type name finds only its own declaration. It is also not the original three-value enum any more: at some point after the purpose model existed, the five mail-flow names (`register`, `verify_email`, `invitation`, `forgot_password`, `notification`) were added onto the **same** enum type — so it now carries eight values spanning two unrelated eras of the design, referenced by nothing. Its doc-comment compounds the problem: "a flow without its own profile falls back to `no_reply`" describes the *pre*-redesign behavior exactly, and is flatly false of the current one, where the fallback is whatever profile an operator names as `default` in `email_routing` (§3) — which need not be, and after a few renames likely will not be, a profile literally named "No-reply." Do not use this enum's comment as a citation for current fallback behavior.

## 3. The `email_routing` config entry

Not a column on this table — one row of `tb_platform_config` (`key = 'email_routing'`), validated by the same registry-and-Zod-schema mechanism the [Platform Config](/en/platform/platform-config) data model documents in full (its own §3 and §5 apply here unchanged: `PATCH` merges, `PUT` replaces-and-requires-every-field, and `doc_version` on that table is **not** an enforced optimistic lock — a real behavioral difference from this module's own `tb_email_sender_profile`, §5 below).

```
EmailRoutingConfig {
  default:         string (uuid)   // required — the fallback for every flow not listed below
  register?:       string (uuid)
  verify_email?:   string (uuid)
  invitation?:     string (uuid)
  forgot_password?: string (uuid)
  notification?:   string (uuid)
}
```

A flow key that is absent from the stored object — not present at all, distinct from present-and-empty — falls back to `default`; this is why the frontend's routing editor deletes a flow's key entirely when an operator picks "use default" rather than writing the default profile's id into it (`EmailRoutingCard.tsx:93-98`) — a newly added flow with no explicit entry in anyone's already-saved config still resolves through `default`, without needing every existing deployment to be updated.

**Registry default:** `{ default: '00000000-0000-0000-0000-000000000000' }` — an intentionally unusable placeholder, since a real profile id is environment-specific and cannot be baked into the registry (`platform-config.schema.ts`, same entry documented on [Platform Config](/en/platform/platform-config)'s data model §3). A genuinely fresh deployment with no seeded profile sits on this placeholder until an operator configures a real one; an upgraded deployment never sees it, because the 2026-08-08 migration seeds a real mapping at migration time (§2.1).

## 4. Resolving a flow to an SMTP send

`PlatformEmailService.resolveProfile(flow)` (micro-notification, `platform-email.service.ts:114-138`) is the single choke point every one of the five flows (landing page §3.2) passes through:

1. Read the live `email_routing` row from `tb_platform_config` (`findFirst`, `orderBy: updated_at desc` — the same most-recent-wins pattern [Platform Config](/en/platform/platform-config)'s data model documents for that table's own dead-on-active-rows unique constraint).
2. Validate it against `EmailRoutingSchema` (Zod). An invalid or missing row logs an error and the flow cannot send at all — there is no default-config fallback at this layer, only the per-flow `default` **inside** an already-valid routing object.
3. Resolve `routing[flow] ?? routing.default` to a profile id.
4. Load that `tb_email_sender_profile` row **filtered** to `deleted_at: null, is_active: true`. A row that exists but is deleted or deactivated is treated identically to a row that does not exist — both return `null` and log the same "routing points at a profile that is missing/deleted/inactive" warning.

`toEmailConfig()` then decrypts `smtp_password` (`decryptSecret`, `@repo/secret-crypto`) and builds the config nodemailer sends with. **A profile that fails to decrypt is reported as broken, not silently skipped** — the code's own comment is explicit that falling back to environment variables here would risk sending from the wrong account while the operator believes the configured profile is in use (`platform-email.service.ts:212-214`); the outcome is `{ sent: false, reason: 'decrypt-failed' }`, distinct from `no-config`.

**No environment-variable fallback exists in this file at all** (landing page §3.3 traces this in full, including the stale doc-comment on the unused, zero-caller `resolveSmtpConfig()` method that claims otherwise). Every failure mode below ends in a reported non-send, never a silent alternate send:

| Outcome | `reason` | Cause |
| --- | --- | --- |
| Sent | *(none — `sent: true`)* | Profile resolved, decrypted, and nodemailer confirmed delivery |
| Not sent | `no-config` | Routing row missing/invalid, or the resolved profile is missing/deleted/inactive |
| Not sent | `decrypt-failed` | Profile resolved but `smtp_password` could not be decrypted (e.g. a `SECRET_ENCRYPTION_KEY` mismatch) |
| Not sent | `lookup-failed` | The database query itself threw (reported, never re-thrown — a mail failure must never fail the caller's own operation, e.g. sign-up) |
| Not sent | `smtp-error` | Profile decrypted fine; the SMTP transport itself failed |

## 5. Write-path mechanics — `tb_email_sender_profile` specifically

CRUD lives entirely in `EmailSenderProfileService` (micro-cluster), proxied by the gateway over RPC (`EmailSenderProfiles.*`, `platform_email-settings.service.ts`).

- **`doc_version` is an actively enforced optimistic lock here** — the opposite of `tb_platform_config`'s same-named column (§3 above, and [Platform Config](/en/platform/platform-config)'s own data model §5). `update()` rejects a request with a missing/non-numeric `doc_version` outright (`COMMON_DOC_VERSION_REQUIRED`) and issues the actual write as `prisma.update({ where: { id, doc_version } , ... })` — a stale version simply matches no row, and the frontend's `isVersionConflict()`/`notifyVersionConflict()` pair (`utils/docVersion.ts`) turns that into a "someone else changed this — reloaded to the latest" toast while keeping the card open (landing page §1).
- **Uniqueness moved to `name`, and the gateway's own Swagger description has not caught up.** `create()`/`update()` both check `findFirst({ name, deleted_at: null })` before writing and return `EMAIL_SENDER_PROFILE_NAME_EXISTS` (409) on a collision (`email-sender-profile.service.ts:163-169, 219-226`) — enforced at the application layer, backed by the partial unique index (§2). The gateway controller's own `@ApiResponse` text for `POST`/`PUT` still reads "An active profile already exists for this purpose" (`platform_email-settings.controller.ts:144`) — a leftover from the pre-redesign, one-purpose-per-row model; the actual 409 condition today is a duplicate **name**, not a duplicate purpose, since `purpose` no longer exists as a column at all.
- **Password-patch semantics** (`passwordPatch()`, `email-sender-profile.service.ts:51-56`): the mask string or `undefined` means "leave unchanged" (no `smtp_password` field is written at all); `null` or `''` means "clear the stored password"; any other string is encrypted and stored. As documented on the landing page §3.4, the frontend's own `PasswordField` component never produces the clear-it value — it treats an emptied field the same as "unchanged" — so a password, once set, is only ever replaceable from this screen, never removable, even though the backend itself supports removal.
- **Delete is soft** (`deleted_at`/`deleted_by_id`), and a deleted profile is excluded from `findAll`/`findOne` but — as §4 states — is resolved identically to a missing one by the routing layer: any flow still pointing at it silently stops sending, with no error surfaced anywhere in the UI until someone notices mail has stopped or checks the routing panel's "broken lane" warning (`RoutingPanel.tsx`'s `broken` styling, landing page §3.1).

## 6. Edge Cases

| Scenario | What actually happens |
| --- | --- |
| A flow's routed profile is deleted or deactivated after routing was configured | The flow silently stops sending (`no-config`) — no notification fires; the only visible signal is the routing panel's "broken lane" warning icon (landing page §3.1) and, eventually, the absence of the mail itself |
| Two admins save the Email Routing card within the same second | Whichever `PUT` reaches `tb_platform_config` last wins the whole object — `doc_version` is not enforced on this table (§3), so there is no conflict detection at all, unlike a concurrent edit to a sender profile (§5, which does conflict-detect) |
| A profile's `smtp_password` cannot be decrypted (e.g. after a key rotation) | Every flow routed to it reports `decrypt-failed`, not `no-config` — distinguishable in logs, but the operator-facing outcome (mail does not go out) is the same either way |
| A never-configured deployment's `email_routing` row is still the registry placeholder UUID | Every flow reports `no-config` until an operator creates at least one profile and saves a routing map with a real `default` (§3) |
| A viewer holds `email_setting.read`/`.manage` but not `platform_config.read`/`.manage` | Sender Profiles load and are fully editable; the Email Routing card permanently shows a load error, and — if it somehow displayed anyway — Save would 403 (landing page §4.2, traced end to end) |
| More than 20 live sender profiles exist | `emailSettingService.getAll()` requests a fixed `perpage=20` with no pagination UI on the page (`emailSettingService.ts:7-9`) — a 21st profile would not appear in the grid, the routing menu, or any flow-count carried by it. The service's own comment justifies this as "the purpose enum caps this list at 3 rows," which is stale in exactly the same way as §2.1's enum fossil: there is no more enum-imposed cap, so the true ceiling today is this hardcoded page size, not any structural limit |

## 7. Recommendations

- **When testing routing changes, verify with the module's own Sender Profiles list open alongside it** — a profile that looks "configured" in its own card can still be silently unreachable by every flow if it is deactivated or if `email_routing` was never saved with a real `default` (§3, §6).
- **Do not cite `enum_email_sender_purpose`'s doc-comment, or `emailSettingService.ts`'s "purpose enum caps this list at 3 rows" comment, as current behavior** — both describe the pre-2026-08-08 one-purpose-per-row design and are stale (§2.1, §6).
- **Test a permission grant of `email_setting.*` alone, without any `platform_config.*` key, deliberately** — it is the single most informative RBAC test case this module has, since it reproduces both the read-side load error and the write-side 403 trap from one grant (landing page §4.2-4.3).
- **A test plan that expects deleting/deactivating a profile to visibly warn "N flows will stop sending" will fail** — the only in-product signal is the routing panel's broken-lane styling, not a blocking confirmation on the profile side beyond the existing "N flows carried" warning shown while still editing that profile (§5, §6).

## 8. References

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (lines 1415-1460) — `enum_email_sender_purpose`, `tb_email_sender_profile`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260729000000_email_sender_profile/migration.sql` — original purpose-enum table creation.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260808130000_email_profile_master_and_routing/migration.sql` — the redesign: rename, re-key uniqueness, drop `purpose`, seed `email_routing`.
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/email-sender-profile/email-sender-profile.service.ts` — CRUD, `doc_version` enforcement, `passwordPatch()`, name-uniqueness (§5).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_email-settings/platform_email-settings.controller.ts` (line 144) — the stale "purpose" Swagger description (§5).
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/platform-email/platform-email.service.ts` — `resolveProfile`/`toEmailConfig`/`send`/`sendTest`/`resolveSmtpConfig` (§4).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` — the `email_routing` registry entry and placeholder default (§3).
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts` (lines 513-514) — `EMAIL_SENDER_PROFILE_NOT_FOUND`/`EMAIL_SENDER_PROFILE_NAME_EXISTS`.
- `../carmen-platform/src/services/emailSettingService.ts` (lines 7-9) — the stale `PERPAGE` justification comment (§6).
- `../carmen-platform/src/pages/emailSettings/{PasswordField.tsx,EmailRoutingCard.tsx}` — password-patch UI semantics (§5) and the routing save call (§4 of the landing page).

**Cross-links:** [Email Settings landing](/en/platform/email-settings) &nbsp;·&nbsp; [Platform Config](/en/platform/platform-config)
