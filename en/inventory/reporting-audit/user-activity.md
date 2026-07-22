---
title: User Activity
description: Actor-centric login/logout timeline reconstructed entirely from tb_activity rows. tb_user_login_session (previously documented as half the data model) is a dead table with zero non-schema code references — Keycloak-issued JWTs are the real session mechanism, with no local session-table backing.
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, activity, security, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# User Activity

> **At a Glance**
> **Owner:** Sysadmin / Auditor (read-only) &nbsp;·&nbsp; **Table:** `tb_activity` filtered on `action IN ('login','logout')` — **not** `tb_user_login_session`, which is dead &nbsp;·&nbsp; **Confirmed writer:** `micro-business`'s `AuthService.logAuthActivity()`, scoped to the user's **default business unit only** &nbsp;·&nbsp; **Used by:** `/system-admin/user-activity` &nbsp;·&nbsp; **Login/logout only — no confirmed page-view or failed-login logging exists.**

![User Activity screen](/screenshots/reporting-audit/user-activity.png)

## Implementation status (verified 2026-07-22)

The previous version of this page described `tb_user_login_session` (platform schema) as one of two tables composing this surface, with a detailed field table and "Row insert = session opened... deletion/expiry = session closed" semantics. A repo-wide code search found **zero references to `tb_user_login_session` anywhere in `carmen-turborepo-backend-v2/apps`** outside its own Prisma model declaration — it is dead, the same pattern already confirmed for `tb_attachment`, `tb_report_schedule`, and the old `tb_widget_*` family. This system authenticates through **Keycloak** (`KEYCLOAK_SERVICE` client proxy in `micro-business`'s `AuthService`) and issues JWT access/refresh tokens directly — there is no local session-table backing to a login at all.

What IS confirmed real: `AuthService.login()` calls `logAuthActivity('login', ...)` on successful authentication, and `AuthService.logout()` calls `logAuthActivity('logout', ...)` — both write a `tb_activity` row (`entity_type: 'auth'`) to the user's **default business unit only** (`tb_user_tb_business_unit` row where `is_default: true`; if the user has no default BU, the write is skipped entirely and logged at debug level, not raised as an error). Both calls are wrapped in their own try/catch that logs failures without failing the surrounding login/logout request.

**Not confirmed by this pass:** failed-login capture (the `login()` method's failure branches — rate-limited, user-not-found — return before any `logAuthActivity` call; no `tb_activity` row is written for a failed attempt), sensitive-page "view" logging (a repo-wide search of `logTenantEvent`/`logEvents` callers found only auth login/logout and product/recipe image upload-delete events — never `action: 'view'`), impersonation-chain tracking, and MFA/role-change events. All of these were previously documented as real and are now marked unconfirmed/likely-absent below.

## 1. What & Who

User Activity is the **login/logout timeline per user** — confirmed to cover exactly two events (`login`, `logout`), each written once per successful authentication or logout call, scoped to the user's default business unit. Distinct from [reporting-audit/activity](/en/inventory/reporting-audit/activity) only in that this page's screen pre-filters to those two `action` values and groups by `actor_id`; it is not a separate table or a separate write path.

**Audience:** Sysadmin / Auditor via `/system-admin/user-activity` — no distinct "Security Officer" role or gate was found anywhere in the frontend or backend-gateway permission decorators for this screen; treat that persona label as unconfirmed.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Browse login/logout history | `/system-admin/user-activity` | Same list component as [reporting-audit/activity](/en/inventory/reporting-audit/activity), hard-scoped client-side to `entity_type = "auth"` — it calls the identical `ACTIVITY_LOGS` endpoint, not a separate API |
| Filter to just logins or just logouts | **Action** filter (Login / Logout only — 2 options) | Server-side `action` query param |
| Filter by user | **User** (actor) filter | Multi-select over `useAllUsers()` |
| Export for compliance | **Export** button | Client-side XLSX export, same query params |
| Inspect one row | Click a row | Opens `UserActivityDetailSheet` (renders `meta_data`/`old_data`/`new_data` like the general activity detail sheet) |
| **Not available / not confirmed** | — | Session timeline drill-down, failed-login investigation, impersonation-chain review, "own activity" profile tab, expired-session reap filtering — none of these have a confirmed backing mechanism (see Implementation status above) |

## 3. Common Questions

| Symptom / Question | Cause / Answer | Action |
|---|---|---|
| Why no `tb_user_activity` table? | It never existed as a distinct concept — this screen is the same `tb_activity` table as [reporting-audit/activity](/en/inventory/reporting-audit/activity), pre-filtered to `entity_type = "auth"` | Not a "reconstruction from two tables" — `tb_user_login_session` (the previously-claimed second table) is dead |
| Why does a failed login attempt not show up here? | `AuthService.login()`'s failure branches (rate-limited, user not found) return before `logAuthActivity()` is ever called | No confirmed code path logs failed attempts — treat any prior claim of `actor_id = NULL` failed-login rows as unconfirmed |
| Why doesn't this page show page views? | No `action: 'view'` write was found anywhere in the backend — `logTenantEvent`/`logEvents` callers are limited to auth login/logout and product/recipe image events | Sensitive-page-view logging does not exist in the current system |
| Can I edit a row? | No — `tb_activity` is append-only; only lifecycle-relevant status fields on other tables get updated, never this one | — |
| Does login/logout cover every business unit the user belongs to? | No — `logAuthActivity()` only writes to the user's **default** business unit (`is_default: true`); if no default BU is set, the write is skipped entirely | A user's login/logout activity is invisible from any non-default BU's screen |
| Cross-tenant viewing? | Not independently confirmed in this pass — no cross-tenant cold-storage mechanism was traced | Treat as unconfirmed rather than a documented feature |

## 4. Edge Cases

- **Only two actions are confirmed: `login` and `logout`.** Both write a single `tb_activity` row with `entity_type = 'auth'`, wrapped in their own try/catch (a logging failure never fails the login/logout request itself).
- **Default-BU-only scoping is a real limitation, not a design choice documented elsewhere.** A user active across multiple BUs will only ever have login/logout rows attributed to their default BU's tenant schema.
- **Time-zone.** `tb_activity.created_at` is `Timestamptz(6)` UTC; the UI renders in the operator's profile timezone via `formatDate()`.
- **Retention.** Governed by [reporting-audit/activity](/en/inventory/reporting-audit/activity)'s tenant-policy retention — no separate retention rule was found for auth-entity rows specifically.
- **RBAC.** The screen itself requires standard Sysadmin navigation access; no finer-grained "Security Officer" permission was found gating any part of it.

---

## 5. Data Model (Dev)

**One table, not two.** This surface is the same `tb_activity` table as [reporting-audit/activity](/en/inventory/reporting-audit/activity), filtered to `entity_type = 'auth'` (which in practice means `action IN ('login', 'logout')`, since those are the only two actions this entity type's writer ever produces). `tb_user_login_session` — previously documented as the other half of this model — is dead.

### 5.1 `tb_activity` (tenant) — filtered projection, `entity_type = 'auth'`

| Field | Used as | Description |
| --- | --- | --- |
| `actor_id` | User identity | Joins platform `tb_user.id`. |
| `action` | Event type | `login` or `logout` — confirmed the only two values this writer produces. |
| `entity_type` | Filter key | Always `'auth'` for this screen's rows. |
| `meta_data` | Extra | `{ login_time: ... }` on login per `logAuthActivity()`'s call site — no confirmed richer payload (MFA flag, impersonation chain) in the traced code. |
| `created_at` | Event timestamp | UTC `Timestamptz(6)`. |

See [reporting-audit/activity](/en/inventory/reporting-audit/activity) §5.1 for the full table definition (including `doc_version`, `old_data`/`new_data`, `ip_address`/`user_agent`, which this writer may or may not populate — not independently traced field-by-field in this pass).

### 5.2 `tb_user_login_session` (platform schema — dead table, kept for contrast)

`id`, `token`, `token_type` (`enum_token_type`: `access_token`/`refresh_token`), `user_id`, `expired_on` (default `now() + 1 day`). Shaped like a session table, but **zero non-schema code references were found anywhere** in `carmen-turborepo-backend-v2/apps`. This system authenticates via Keycloak-issued JWTs — there is no local session-table backing.

## 6. Business Rules

- **Single writer, single table.** `AuthService.logAuthActivity()` in `micro-business` is the only confirmed writer — called from `login()` (success only) and `logout()`, both scoped to `entity_type = 'auth'`.
- **Default-business-unit scoping.** The write resolves the user's default BU (`tb_user_tb_business_unit` where `is_default: true, is_active: true`); if none exists, the activity write is silently skipped (debug-logged, not an error).
- **Failure-tolerant, not failure-blocking.** Both call sites wrap `logAuthActivity()` in try/catch — a logging failure never fails the surrounding login/logout request.
- **No confirmed failed-login capture, page-view logging, or impersonation tracking.** All three were previously documented as real; none were found in this pass.
- **`tb_user_login_session` is dead.** No code path creates, reads, updates, or deletes rows in it.

## 7. Cross-References

- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — the underlying (and only) table; this page is a client-side filtered view over the exact same data.
- [access-control/user](/en/inventory/access-control/user) — `actor_id` resolves through platform `tb_user`.

## 8. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (line ~280), `enum_activity_action` (line ~56).
- **Prisma platform (dead table, for contrast):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_login_session` (line ~567), `enum_token_type` (line ~577).
- **Confirmed writer:** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` — `logAuthActivity()` (private method), called from `login()` and `logout()`.
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/user-activity/user-activity.route.tsx`, `user-activity-component.tsx` (hard-sets `entity_type = "auth"` on every query), `use-user-activity-table.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-user-activity.ts` — calls the same `API_ENDPOINTS.ACTIVITY_LOGS(buCode)` endpoint as [reporting-audit/activity](/en/inventory/reporting-audit/activity)'s screen.
