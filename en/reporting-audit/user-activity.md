---
title: User Activity
description: Per-user activity timeline — login, logout, session lifetime, sensitive-page views — distinct from the entity-level activity log.
published: true
date: 2026-05-16T17:00:00.000Z
tags: reporting-audit, activity, security, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# User Activity

## 1. Purpose

User Activity is the **user-centric forensic timeline** — every login, logout, token refresh, password change, role change, and sensitive-page view captured per actor. It answers the security and compliance questions *"when did user X sign in and from where?"*, *"which sensitive documents did user X open during their last session?"*, and *"are there failed login attempts clustered on this account?"*. It is intentionally distinct from [[reporting-audit/activity]] — activity is **entity-centric** (one row per state change against a row in some `tb_*` table), user-activity is **actor-centric** (one row per user-action event, regardless of whether any business row was changed).

In the current schema the surface is **reconstructed** rather than stored in a dedicated table: session state lives in platform `tb_user_login_session`, and user-action events live in tenant `tb_activity` filtered by `action IN ('login', 'logout', 'view')`. The frontend page at `/system-admin/user-activity` joins these views per user. A dedicated `tb_user_activity` table is on the roadmap but not yet in either schema as of this revision — mark "(Inferred — table to be verified)" against any forward-looking field below.

## 2. Prisma Model(s)

Two tables compose the surface; no single `tb_user_activity` table exists today.

### 2.1 `tb_user_login_session` (platform)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `token` | `String @db.VarChar` | No | Issued session token (or hashed reference). |
| `token_type` | `enum_token_type` | No | Default `access_token`. One of `access_token`, `refresh_token`. |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user.id`. |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + 1 day`. Session expiry. |

**Constraints:** unique on `token` (`user_login_session_token_u`). FK to `tb_user.id` (`tb_user_login_session.user_id`). Row insertion marks "session opened" (functional login); deletion or expiry marks "session closed" (functional logout). No `created_at` / IP / user-agent columns on this table — those are sourced from `tb_activity` when the login event is logged.

### 2.2 `tb_activity` (tenant) — filtered view

The audit log doubles as the user-action event store. Filter on `action IN ('login', 'logout', 'view')` and group by `actor_id` to recover the user timeline.

| Field | Used as | Description |
| --- | --- | --- |
| `actor_id` | User identity | Joins to platform `tb_user.id`. |
| `action` | Event type | `login` / `logout` / `view` for user-activity; other actions for the entity-activity view. |
| `entity_type`, `entity_id` | Target (if any) | For `view`, identifies the sensitive document opened. For `login` / `logout`, typically `entity_type = 'session'` and `entity_id = tb_user_login_session.id`. |
| `ip_address`, `user_agent` | Forensic context | Captured per request; the canonical source for client info. |
| `meta_data` | Extra context | Failed-login reason, MFA flag, impersonation chain. |
| `created_at` | Event timestamp | UTC, `Timestamptz(6)`. |

See [[reporting-audit/activity]] for the full table definition. Records with `entity_type = 'session'` are the login/logout pair; records with `action = 'view'` are sensitive-page open events that opt in to view-logging (PR/PO detail, costing, financial reports).

**Inferred — to be verified.** A future `tb_user_activity` table is on the roadmap to denormalize this view for performance; if introduced it would carry `(user_id, event_type, event_at, ip_address, user_agent, target_type, target_id, meta_data)` with composite indexes on `(user_id, event_at DESC)` and `(event_type, event_at DESC)`. Treat any reference to a dedicated table here as forward-looking until the schema lands.

## 3. Usage / Cross-References

- [[reporting-audit/activity]] — the underlying table for action events. User-activity is a filtered + joined projection over activity plus session.
- [[access-control/user]] — `actor_id` and session `user_id` resolve through platform `tb_user`. The user-activity screen renders username, email, and role chips alongside each event.
- [[access-control/permission]] — view-permission grants drive which sensitive-page opens are eligible for logging. Pages without a logged-view requirement do not emit `action = 'view'` rows.
- Authentication middleware in `carmen-turborepo-backend-v2` writes login / logout to `tb_activity` and creates / deletes the `tb_user_login_session` row in a single transactional path.

## 4. Configuration UI

User Activity is **read-only** with no end-user configuration.

- **System Admin → User Activity** (`/system-admin/user-activity`): the consolidated screen. Default view groups by user and shows the most recent session, with drill-down into the session's event timeline (login → views → logout). Filters: user, date range, IP, event type, failed-login flag. Visible only to Sysadmin / Security Officer / Auditor roles.
- **Per-user drawer** on the user detail page (`/system-admin/user/[id]`): a condensed timeline limited to that user, useful when investigating an individual report.
- **Compliance export** hits the same query path and ships rows to long-term storage outside the application — typically a CSV or JSON snapshot per quarter shipped to SIEM.

## 5. Business Rules

- **Append-only.** Application code never updates user-activity events. `tb_activity` rows are immutable post-insert; `tb_user_login_session` is insert / delete only.
- **Login / logout pairing.** A `login` event always precedes a session row insert in the same transaction; the activity row's `entity_id` matches the session's `id`. Logout deletes the session and inserts a `logout` activity row with the same `entity_id`. Orphaned sessions (no logout event by `expired_on`) are reaped by a cleanup job and emit a synthetic `logout` activity row with `meta_data.cause = 'expired'`.
- **Failed-login capture.** Failed authentications insert a `tb_activity` row with `actor_id = NULL` (unauthenticated context), `action = 'login'`, `meta_data.success = false`, and `meta_data.username_attempted` for the offered identifier. They do not create a session row. The `tb_user.failed_login_count` (on platform schema, where present) is incremented in the same path.
- **PII consideration.** `ip_address` and `user_agent` are PII under most jurisdictions. The retention policy on `tb_activity` controls how long these survive; the user-activity screen further redacts `user_agent` to a parsed family/version pair on display unless the operator holds a security-officer grant.
- **RBAC on reading.** A user can read their own activity timeline via the profile screen. The platform-wide user-activity screen is gated to Sysadmin / Security Officer / Auditor. Cross-tenant viewing is reserved for Platform Admin and only against audit-log copies in long-term storage, never via the live tenant table.
- **Time-zone of timestamps.** All event timestamps are `Timestamptz(6)` in UTC; the screen renders in the operator's profile timezone with a tooltip showing the raw UTC. Session `expired_on` is also UTC.
- **Retention.** Same horizon as [[reporting-audit/activity]] — tenant-policy driven, with rows older than the horizon migrated to cold storage by a scheduled job. Session rows are deleted at `expired_on` or sooner on logout; no long-term retention of session tokens.

## 6. References

- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_login_session` (lines 456-465), `enum_token_type` (lines 577-580), `tb_user` (lines ~360-454) for the FK target.
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (lines ~277-297), `enum_activity_action` (lines ~67-89) — see [[reporting-audit/activity]].
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/user-activity/` — list and drill-down, with `_components/` for the per-user timeline.
- **Authentication middleware:** `../carmen-turborepo-backend-v2/apps/` — login / logout handlers write the paired session + activity rows.
- **Cross-module:** see Section 3.
