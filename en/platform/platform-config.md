---
title: Platform Config
description: One screen, nine cards, eight config keys — invitations, sign-up, legacy email verification, password reset, internal notification email, license enforcement, expiry-warning thresholds, and the platform-migration API switch.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, platform-config
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Platform Config

The **Platform Config** module is one screen, `PlatformConfigManagement` at `/platform/configs`, that reads and writes rows in a single shared table, `tb_platform_config`. Each row is a namespace (a JSON object), not a single value, and the screen renders one card per namespace it knows how to edit — nine cards for eight of the ten keys the backend registry defines (§3.5 covers the two it does not touch). Everything on this screen is either a link-and-lifetime setting migrated off an environment variable so an operator can change it without a redeploy, a platform-wide kill switch, or a purely cosmetic display threshold — and mixing those three categories up is the single easiest way to misjudge what a save actually does, which is why §3.2 walks every key by its *effect*, not just its fields.

> **At a Glance**
> **Component:** `PlatformConfigManagement` &nbsp;·&nbsp; **Route:** `/platform/configs` &nbsp;·&nbsp; **Nav:** `permission: 'platform_config.read'`, `feature: 'platform_config'`, `groupKey: 'navGroup.platform'` (`platformNav.ts:38`) &nbsp;·&nbsp; **Base write gate:** `platform_config.manage`, required by the backend on every key's `PUT`/`PATCH` regardless of which screen calls it &nbsp;·&nbsp; **Two keys need a second gate to save:** `license` also needs `license.manage` (§4.3 — **not** a `licenses`-module key); `platform_migration` needs super-admin status outright, no permission string accepted &nbsp;·&nbsp; **Cards:** 9, mapped from 8 keys (`invitation` has two cards, §3.1) &nbsp;·&nbsp; **e2e suite:** **None** — `../carmen-platform-e2e/tests/` has no `platform-config`/`configs` directory; every claim below is sourced from `../carmen-platform` and `../carmen-turborepo-backend-v2` implementation directly &nbsp;·&nbsp; **Sub-pages:** 1

## 1. Overview

`PlatformConfigManagement` fetches every supported key in one call, `platformConfigService.getAll()` → `GET /api-system/platform/configs` (`platformConfigService.ts:11-14`), gated by `platform_config.read`. A key that has never been saved still comes back with a row — the backend fills in the registry's built-in default and returns `id: null` (`platform_configs.service.ts` `findAll`, proxied through `PlatformConfigsService` to micro-cluster) — so the screen never has to special-case "not configured yet" versus "configured to the default."

The page lays its cards out in four groups (`SectionHeading`, `PlatformConfigManagement.tsx:220-351`):

| Section | Cards | Keys |
| --- | --- | --- |
| Email Links | Invitation, Sign-up, Email Verification, Password Reset | `invitation` (base_url/expiry_days half), `signup`, `email_verification`, `password_reset` |
| Invitation Limits | Rate Limits | `invitation` (limits half) |
| Notifications | Notification Email | `notification_email` |
| Licensing | License Enforcement, Expiry Thresholds | `license`, `expiry_thresholds` |
| Platform Migration | Platform Migration | `platform_migration` |

A status strip above the cards (`PlatformConfigManagement.tsx:198-218`) surfaces the three settings a reader could otherwise miss by not scrolling: license enforcement (**Enforced**/**Shadow Mode**), internal notification email (**On**/**Off**), and the platform-migration API (**On**/**Off**) — each read with `=== true`, not truthy, so a malformed stored value reads as off rather than crashing the badge. Every card follows the same shell (`ConfigCardShell`/`ConfigField`, `pages/platformConfig/ConfigCardShell.tsx`): a read-only `<dl>` of label/value rows when closed, an inline form when open, and one audit footer line ("Updated 3 days ago by …" or "Created …", via `normalizeAudit()`/`latestActor()`, `utils/audit.ts:72-108`) — nested `audit.*` tried first, flat `updated_at`/`updated_by_name` as the fallback, with `updated` suppressed unless the record was genuinely edited (a name is present, or the timestamp differs from `created_at`).

Saves go through `PATCH /api-system/platform/configs/:key` (`platformConfigService.patch()`, never `.update()`/`PUT` from any card — see §3.4), each card sending only the fields it displays. On success the page refetches the whole list (`handleSaved` → `fetchAll()`), which both closes the editing card and remounts every card whose `key` prop includes the row's updated timestamp — so a card's form always resets to the freshly-saved value, never a stale in-memory copy.

A dev-only debug panel (`DevDebugSheet`, bottom-right) renders the raw `GET` payload — but only in a local dev build: `DevDebugSheet` itself returns `null` unless `import.meta.env.DEV` is true, and the page only populates `rawResponse` in the first place when `process.env.NODE_ENV === 'development'` (`PlatformConfigManagement.tsx:97,356-360`). This is **not an RBAC gate** — a production build compiles the panel away regardless of the viewer's permissions.

The page-level unsaved-changes guard (`useUnsavedChanges(editingCard !== null)`) is coarse by design: only one card can be in edit mode at a time (`editingCard: CardId | null`), and the guard fires whenever any card is open, because each card owns its own form state and the page cannot compute per-field dirtiness without coupling to every card individually — the code's own comment calls this the safer side of that trade-off.

## 2. Business Context

Every key on this screen used to be an environment variable read once at process boot: `INVITATION_BASE_URL`/`INVITATION_EXPIRY_DAYS`, `SIGNUP_VERIFY_BASE_URL`, `SMTP_ENABLED`/`SMTP_RECIPIENTS`/`SMTP_CC`/`SMTP_SUBJECT_PREFIX`, `PLATFORM_MIGRATION_API_ENABLED`. Moving them into `tb_platform_config` lets an operator change a link destination, a token lifetime, or a kill switch from a screen — no redeploy, no restart — while keeping the values out of source control and out of every deploy pipeline's env-var list. The trade-off this module's own source comments are explicit about: three of the nine cards (License Enforcement, Platform Migration, and indirectly the rate-limit note on Invitation Limits) are not "preferences" in the ordinary sense — they are switches other parts of the platform treat as authoritative, checked on a hot request path, with a 60-second read cache standing between "you clicked Save" and "the new behavior is live everywhere." Reading the wrong intent into a save here — treating `license.enforcement_enabled` as a display toggle, or `expiry_thresholds` as an enforcement lever — is the single most consequential mistake a tester of this screen can make, which is why §3.2 states each key's actual effect, not just its stored shape.

## 3. Key Concepts

### 3.1 Nine cards, eight keys — `invitation` alone has two

`tb_platform_config` is a namespace-per-row table: every row is a JSON object, never a single scalar (`platform-config.schema.ts:176-184` states this convention explicitly — a dotted key like `license.enforcement_enabled` as its own row would be "a second convention in one table," and would also be invisible on this screen, since `findAll` filters by the registry's key list). `invitation` is the one key two cards share: `InvitationConfigCard` edits `base_url`/`expiry_days`, `InvitationLimitsCard` edits `max_per_admin_per_hour`/`max_per_cluster_per_day` — both `PATCH` the same `invitation` row, and each card deliberately uses `patch()` rather than `update()` so that saving one half never wipes the other half's fields (`InvitationConfigCard.tsx:105-107`, `InvitationLimitsCard.tsx:96-97`).

`email_verification` and `password_reset` share one generic component, `LinkConfigCard` (`pages/platformConfig/LinkConfigCard.tsx`), parameterized by `configKey`/`title`/`urlExample`/`defaults` — both keys have the identical `{ base_url, expiry_hours }` shape, so a dedicated card per key would be pure duplication (`LinkConfigCard.tsx:34-39`).

### 3.2 What each key controls, and where the effect actually lives

| Card / Key | Fields (default) | What changes in the product when saved | Enforced in |
| --- | --- | --- | --- |
| **Invitation** (`invitation`) | `base_url` (`http://localhost:3000/invitations`), `expiry_days` (7, 1–365) | The link text sent inside every new cluster/BU invitation email, and how many days the invite token stays redeemable. `base_url` is composed with `new URL()` + `searchParams.set('token', …)`, never string concatenation — a value that already carries a query string is valid on purpose. | micro-cluster's invitation-issuing flow, reading this same `tb_platform_config` row directly (registry doc-comment, `platform-config.schema.ts:4-23`) |
| **Rate Limits** (`invitation`, other half) | `max_per_admin_per_hour` (100), `max_per_cluster_per_day` (500), both positive integers with **no upper bound enforced by the backend** | The ceiling on how many invitations one admin (per hour) or one cluster (per day) can issue before further invites are rejected. The in-page warning note states the counters are **in-memory per process**, so the effective ceiling across a multi-instance deployment multiplies by instance count — raise these deliberately for a mass-onboarding event, not casually. | An in-process rate limiter on the invitation-issuing endpoint (micro-cluster); not a security boundary, an abuse guard |
| **Sign-up** (`signup`) | `verify_base_url` (`http://localhost:3000/register/verify`), `link_expiry_hours` (24, 1–720) | The destination link and token lifetime for the **self-service sign-up** verification email (`auth.service.ts` `signupRequest`, micro-business) — the flow a brand-new account uses to confirm its own email before the account exists. | micro-business `readSignupConfig()` reading the row directly (`auth.service.ts:319-327`) |
| **Email Verification** (`email_verification`) | `base_url` (`http://localhost:3000/verify-email`), `expiry_hours` (24, 1–720) | The link and token lifetime for the **legacy** verification email — sent to an account created *before* the sign-up flow was reversed, or one an admin created directly, where the account already exists and only its email needs confirming. Distinct code path from Sign-up above; both are live simultaneously. | micro-business `readEmailVerificationConfig()` (`auth.service.ts:329-338`, consumed in the request-verification handler around line 1362) |
| **Password Reset** (`password_reset`) | `base_url` (`http://localhost:3000`), `expiry_hours` (24, 1–720) | The link and token lifetime for the forgot-password email. A source comment on the read path is explicit about why this moved off `process.env`: the old code path read the raw env var with no schema and a **1-hour** hardcoded default that did not match the `.env` file's actual 24-hour setting — the value shown to the user in the email and the value that actually expired the token could silently disagree. That class of drift is what this migration removes. | micro-business `readPasswordResetConfig()` (`auth.service.ts:340-350`, consumed at `auth.service.ts:1684-1687`) |
| **Notification Email** (`notification_email`) | `enabled` (off), `recipients` (`[]`), `cc` (`[]`), `subject_prefix` ('') | On paper: who receives internal notification mail (reports / BU-level notifications) and the subject-line prefix, independent of the SMTP *credentials* that live in the separate Email Setting module's `tb_email_sender_profile`. **In practice: saving this card currently changes nothing observable.** A repository-wide search of `carmen-turborepo-backend-v2`, `micro-notification`, `micro-report`, `micro-cronjobs`, and `micro-data` for any reader of the `notification_email` key or its fields (`recipients`, `cc`, `subject_prefix`) returns no hits outside the registry definition itself — `micro-notification`'s own internal docs (`apps/micro-notification/CLAUDE.md`) describe SMTP *credentials* as fully migrated off environment variables to `tb_email_sender_profile`, but do not mention this key at all. Treat this card as **write-and-persist-only** until a consumer is confirmed; do not assume toggling `enabled` changes whether any report or notification email actually sends. | **No consumer found** — flagged, not asserted as enforced anywhere |
| **License Enforcement** (`license`) | `enforcement_enabled` (`false`, shadow mode) | The platform-wide licensing kill switch. When `true`, `LicenseInterceptor` (backend-gateway) blocks every write — and every read whose feature is not entitled — on routes matching `/api/:bu_code/*` or `/api/config/:bu_code/*` for a business unit lacking the required entitlement, returning `403 LICENSE_REQUIRED` (never sold) or `403 LICENSE_EXPIRED` (write attempted on an expired contract; reads still pass). The same switch simultaneously enables seat-cap enforcement in micro-cluster's `assertSeatAvailable`, returning `403 SEAT_LIMIT_REACHED` when a new invite would exceed the cluster's purchased seats. `/api-system/*` — everything this admin screen itself calls — is **out of scope** for the switch, so turning it on can never lock the admin screen out of itself. Both readers cache the flag for 60 seconds, so a save takes effect within about a minute, not instantly, and a value that fails to parse reads as `false` (fail-open) on both sides. | `license.interceptor.ts` (backend-gateway, route scope in `license-route-resolver.ts:21,25`) + `seat-enforcement-flag.service.ts` (micro-cluster) |
| **Expiry Thresholds** (`expiry_thresholds`) | `subscription_days`, `bu_quota_days`, `seat_days` — all `30`, 1–365 | Purely a **display/counting** window — raising or lowering a value changes only when an "expiring soon" badge starts appearing on the [Licenses](/en/platform/licenses) and Clusters screens, and what a summary strip's `expiring_soon` count includes. **Nobody is blocked more or less by this card** — it shares a section with License Enforcement above only because both are about licence lifecycle, not because they share a mechanism. Consumed live by three separate processes (micro-cluster's cluster list/counter, micro-business's subscription summary, and this frontend's own `ExpiryThresholdContext`, which calls `refresh()` right after a save so `/licenses` and `/clusters` reflect the new window without a full app reload), each with its own 60-second cache. | `ExpiryThresholdsService` in micro-cluster and micro-business; `ExpiryThresholdContext.tsx` on the frontend (public, permission-free endpoint — see §4.1) |
| **Platform Migration** (`platform_migration`) | `api_enabled` (`false`) | The on/off switch for `/api-system/platform/migrations/*`, which runs `prisma migrate deploy` against the **shared platform database every cluster uses** — not a single BU's database. Formerly the env var `PLATFORM_MIGRATION_API_ENABLED`; moving it here traded "requires machine access to flip" for "requires super-admin status to flip" (§4.3). `PlatformMigrationGuard` caches the flag for 60 seconds, so — per the in-card note — a freshly-enabled switch can still answer 403 for up to a minute, which is expected, not a bug. | `platform-migration.guard.ts` (backend-gateway), same 60s-cache pattern as License Enforcement |

### 3.3 Two keys need more than `platform_config.manage` to save — see §4.3 for the exact permission conjunction

The endpoint-level decorator on both write routes is the same for every key, `@RequirePlatformPermission('platform_config.manage')` (`platform_configs.controller.ts:238,287`). Two keys add a **second**, key-specific gate inside the handler itself, `writeKeyDenial()` (`platform_configs.controller.ts:145-159`), because `@RequirePlatformPermission` is an endpoint-level decorator and cannot distinguish one config key's `PATCH` from another's:

- `license` also requires `license.manage` — or `is_super_admin === true` as an unconditional short-circuit (`platform_configs.controller.ts:147-151`).
- `platform_migration` requires `is_super_admin === true` **only** — no permission string accepts it, by contrast with `license` (`platform_configs.controller.ts:153-157`).

Every other key behaves exactly as `@RequirePlatformPermission('platform_config.manage')` alone implies — `writeKeyDenial()` returns `null` (allow) immediately for them.

### 3.4 Why every save is `PATCH`, never `PUT`

`platformConfigService.update()` (`PUT`) exists but no card in this module calls it — `PUT` requires every field the target key's schema knows about, and a payload missing one is rejected with `422` rather than silently refilled with the default (`platformConfigService.ts:21-30`, backend PR #319). `PATCH` merges only the fields sent, leaving the rest untouched — the correct choice for every card here because none of them ever display 100% of a key's *possible* future fields; the backend strips `.default()` from the write-side schema specifically so a field genuinely omitted from a `PATCH` payload cannot be confused with a field the caller deliberately set to its default value (`toWriteSchema()`, `platform-config.schema.ts:405-434`). `doc_version` exists as a column on this table but the backend does not yet enforce optimistic locking with it — `platformConfigService.update()`'s own comment says not to send it.

### 3.5 Two more registry keys exist on this table but never appear on this screen

The backend's `PLATFORM_CONFIG_REGISTRY` (`platform-config.schema.ts:260-369`) defines ten keys total, not eight — `email_routing` and `feature_flags` share the same `tb_platform_config` table and the same generic `/api-system/platform/configs/:key` REST surface, but neither is rendered by `PlatformConfigManagement`:

- **`email_routing`** — which sender profile handles which mail flow — is edited from the separate **Email Settings** module's own screen (`EmailRoutingCard.tsx:124`, calling `platformConfigService.update('email_routing', …)` — the identical generic service this module uses). **Worth flagging precisely, in the same spirit as §4.3 below:** that screen gates its own Edit affordance on `email_setting.manage` (`EmailSettingManagement.tsx:48`) — but the endpoint it actually calls to save still requires `platform_config.manage` at the controller level, exactly like every key in this module (§3.3). A session holding `email_setting.manage` without `platform_config.manage` would see a working-looking Edit UI on the Email Settings screen and get a 403 on every save — the identical shape of bug this module's own `license.manage` note (§4.3) exists to prevent, just on a different screen. Not yet confirmed against the Email Settings module's own pages; flagged here for whoever verifies or writes that module next.
- **`feature_flags`** — per-feature availability flags the frontend reads to decide what to render — is **not** reachable through `/api-system/platform/configs` at all despite living in the same registry and the same table. It has its own dedicated pair, confirmed directly in `feature_flags.controller.ts`: `GET /api-system/platform/feature-flags` carries **no** `PlatformPermissionGuard`/`RequirePlatformPermission` — only an `AppIdGuard` (`feature_flags.controller.ts:83-84`) — because every authenticated app must be able to read flags, not just platform admins; `PUT /api-system/platform/feature-flags` requires `feature_flag.manage` (`feature_flags.controller.ts:118-120`), a key this module never checks. This pair belongs to the separate **Feature Flags** module.

## 4. Roles and Permissions

### 4.1 Frontend gate matrix

| Surface | Permission | Feature flag | Source |
| --- | --- | --- | --- |
| Sidebar entry, `/platform/configs` route | `platform_config.read` | `platform_config` | `platformNav.ts:38`; `App.tsx:501-502` |
| Every card's Edit button, except License Enforcement and Platform Migration | `platform_config.manage` (`canManage`) | — | `PlatformConfigManagement.tsx:72` |
| License Enforcement card's Edit button | `platform_config.manage` **and** `license.manage` (`canManageLicense`) | — | `PlatformConfigManagement.tsx:75` |
| Platform Migration card's Edit button | `platform_config.manage` **and** `isSuperAdmin` (`canManagePlatformMigration`) | — | `PlatformConfigManagement.tsx:79` |
| Expiry Thresholds card's Edit button | `platform_config.manage` (`canManage`) **only** — deliberately not `canManageLicense` | — | `PlatformConfigManagement.tsx:326-335`, with an in-code comment warning against copying the License card's tighter gate here |

`ConfigCardShell` hides the Edit button entirely when `canManage` is false (`ConfigCardShell.tsx:75-80`) — a reader without the permission never sees an edit affordance to begin with, on any card; there is no disabled-but-visible state.

The frontend's own `checkPermission()` short-circuits to `true` for any key when the caller is a super admin (`src/utils/permissions.ts:56`), so a super admin sees the Edit button on **every** card, including License Enforcement, without needing the literal `license.manage` string — consistent with the backend's own super-admin short-circuit in `writeKeyDenial()` (§3.3).

### 4.2 Backend enforcement

All paths below are `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_configs/platform_configs.controller.ts`, HEAD `937cf5ac4` (2026-09-06).

| Route | Guard | Source |
| --- | --- | --- |
| `GET /api-system/platform/configs` | `AppIdGuard` + `PlatformPermissionGuard`, `platform_config.read` | line 168-170 |
| `GET /api-system/platform/configs/:config_key` | same, `platform_config.read` | line 198-200 |
| `PUT /api-system/platform/configs/:config_key` | same, `platform_config.manage`, **plus** `writeKeyDenial()` for `license`/`platform_migration` | line 236-238, 262-266 |
| `PATCH /api-system/platform/configs/:config_key` | same, `platform_config.manage`, **plus** `writeKeyDenial()` for `license`/`platform_migration` | line 285-287, 311-315 |

Both write handlers validate the `config_key` path segment against `KEY_REGEX` (`^[a-zA-Z0-9_.-]+$`) before touching the service layer, rejecting a malformed key with `422` rather than letting it reach the RPC call (`platform_configs.controller.ts:37,219-222,258-261,307-310`).

### 4.3 `license.manage` lives here, not in the Licenses module — the exact conjunction a tester needs

**A repository-wide grep finds `license.manage` in exactly one place: this module.** It appears at `PlatformConfigManagement.tsx:75` (`canManageLicense = canManage && hasPermission('license.manage')`) and in the matching backend check, `writeKeyDenial()`'s `LICENSE_MANAGE_PERMISSION` constant (`platform_configs.controller.ts:58,149-151`). It does **not** gate anything in the [Licenses](/en/platform/licenses) module — that module's own two keys are `subscription.read`/`subscription.manage`, confirmed in its own permissions documentation.

**The conjunction matters, both halves of it:**

- `canManage` alone (`platform_config.manage`) is **necessary but not sufficient** — a holder of `platform_config.manage` who lacks `license.manage` sees the License Enforcement card's Edit button **hidden entirely** (the `&&` is evaluated before the button ever renders, `PlatformConfigManagement.tsx:75` feeding `ConfigCardShell`'s `canManage` prop), so this reads as "no Edit control," not as an Edit-then-403 trap.
- The reverse gap is the one worth remembering precisely: **`license.manage` alone, without `platform_config.manage`, cannot save this card either** — the backend's endpoint-level decorator on `PUT`/`PATCH` (§4.2) is `platform_config.manage`, checked *before* `writeKeyDenial()`'s per-key logic ever runs. A role granted only `license.manage` — created, say, to let someone manage licensing without touching the rest of platform config — would still 403 on every save here, because the resource this decorator is `platform_config`, not `license`. The backend's own comment on `LICENSE_MANAGE_PERMISSION` states the reasoning directly: it is a distinct resource by design, specifically so a role built to let someone edit an unrelated key (say, Email Verification) does not silently inherit the platform-wide licensing kill switch along with it. It does not exist to let `license.manage` stand alone as a lesser-scoped path to this card.

An earlier scaffolded description of the [Licenses](/en/platform/licenses) module wrongly assigned `license.manage` to that module's own CRUD gating. It has been corrected there; this page is the definitive source for what the key actually controls.

### 4.4 What `platform_config.read`/`.manage` do *not* cover

Reading this screen's data does not require any of the finer-grained keys that gate the individual settings elsewhere in the product — e.g. Expiry Thresholds' own values are also exposed through a **separate, deliberately permission-free** endpoint (`expiryThresholdService`, consumed by `ExpiryThresholdContext`) precisely so an ordinary user viewing `/licenses` or `/clusters` — who does not hold `platform_config.read` — can still see accurate "expiring soon" badges without being granted access to this admin screen.

## 5. Related Modules

- [Licenses](/en/platform/licenses) — the consumer of both the `license.enforcement_enabled` kill switch and the `expiry_thresholds` display window; also the module whose own permission pair (`subscription.read`/`subscription.manage`) is unrelated to `license.manage` (§4.3).
- Clusters, Business Units — also read the `expiry_thresholds` window for their own "expiring soon" badges and quota counters (see the [Licenses](/en/platform/licenses) module's data model for the shared threshold-consumption pattern).
- Email Settings — owns `tb_email_sender_profile` (SMTP credentials) and the `email_routing` registry key (§3.5), edited from its own screen but written through this same generic `/api-system/platform/configs` surface.
- Feature Flags — owns the `feature_flags` registry key (§3.5) through its own dedicated, differently-permissioned endpoint pair, not this module's surface.
- [Platform RBAC](/en/platform/rbac) — the permission catalog where `platform_config.read`/`.manage`, `license.manage`, and every other key on this page are visible alongside every other platform resource.

## 6. Reference Sources

All paths below are `../carmen-platform` (the Platform admin SPA, HEAD `157a65e`, 2026-09-04) unless prefixed `../carmen-turborepo-backend-v2` (the backend monorepo, HEAD `937cf5ac4`, 2026-09-06).

- `../carmen-platform/src/pages/PlatformConfigManagement.tsx` — the page shell, permission wiring (lines 69-81), status strip, card grid, `DevDebugSheet`.
- `../carmen-platform/src/pages/platformConfig/ConfigCardShell.tsx` — the shared card shell and read/edit field renderer.
- `../carmen-platform/src/pages/platformConfig/{InvitationConfigCard,InvitationLimitsCard,invitationDefaults}.ts(x)` — the `invitation` key's two cards.
- `../carmen-platform/src/pages/platformConfig/SignupConfigCard.tsx`, `LinkConfigCard.tsx`, `NotificationEmailConfigCard.tsx`, `LicenseEnforcementCard.tsx`, `ExpiryThresholdsCard.tsx`, `PlatformMigrationConfigCard.tsx` — the remaining seven cards.
- `../carmen-platform/src/services/platformConfigService.ts` — `getAll`/`getByKey`/`update`/`patch` REST client.
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx`, `src/services/expiryThresholdService.ts` — the separate, permission-free threshold reader consumed platform-wide.
- `../carmen-platform/src/utils/audit.ts` — `normalizeAudit`/`latestActor`, shared by every card's footer.
- `../carmen-platform/src/utils/permissions.ts` — `checkPermission`'s super-admin short-circuit (§4.1).
- `../carmen-platform/src/components/nav/platformNav.ts` (line 38), `src/App.tsx` (lines 501-502) — nav entry and route registration.
- `../carmen-platform/src/pages/emailSettings/EmailRoutingCard.tsx` (line 124), `src/pages/EmailSettingManagement.tsx` (line 48) — the cross-module `email_routing` fact in §3.5.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_configs/platform_configs.controller.ts` — REST surface, `writeKeyDenial()` (§3.3, §4.2).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` — `PLATFORM_CONFIG_REGISTRY`, every key's Zod schema and default (§3.2, §3.5).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/license/{license.service.ts,license.interceptor.ts,license.evaluator.ts,license-route-resolver.ts}` — license-enforcement mechanics (§3.2).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/common/{seat-enforcement-flag.service.ts,expiry-thresholds.service.ts}` — seat enforcement and expiry-threshold reading in micro-cluster.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-migration.guard.ts` — the platform-migration API's own 60s-cached guard.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (lines 319-350, 1362-1385, 1684-1687) — `signup`/`email_verification`/`password_reset` consumers.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts` — the `feature_flags` key's separate endpoint pair (§3.5).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_platform_config` (line 1462).

## 7. Pages in This Module

- [Data Model](/en/platform/platform-config/data-model) — the `tb_platform_config` entity, the full `PLATFORM_CONFIG_REGISTRY` (all ten keys, including the two this screen never shows), and the multi-process reader map behind §3.2's effects.
