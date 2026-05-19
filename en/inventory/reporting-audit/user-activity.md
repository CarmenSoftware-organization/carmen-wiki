---
title: User Activity
description: Actor-centric forensic timeline — login, logout, session lifetime, sensitive-page views — distinct from entity-level activity.
published: true
date: 2026-05-19T23:55:00.000Z
tags: reporting-audit, activity, security, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# User Activity

> **At a Glance**
> **Owner:** Sysadmin / Security Officer / Auditor (read-only) &nbsp;·&nbsp; **Tables:** `tb_user_login_session` (platform) + `tb_activity` filtered projection (tenant) &nbsp;·&nbsp; **Retention:** activity rows per tenant policy; session rows deleted at `expired_on` &nbsp;·&nbsp; **Used by:** `/system-admin/user-activity`, compliance export &nbsp;·&nbsp; **Per-user forensic timeline of logins, logouts, and sensitive-page views.**

![User Activity screen](/screenshots/reporting-audit/user-activity.png)

> **No dedicated `tb_user_activity` table exists today.** The surface is **reconstructed** by joining platform `tb_user_login_session` to tenant `tb_activity` filtered on `action IN ('login', 'logout', 'view')` and grouped by `actor_id`. A dedicated table is on the roadmap — mark "(Inferred — table to be verified)" against any forward-looking field.

## 1. What & Who

User Activity is the **actor-centric forensic timeline** — every login, logout, token refresh, password change, role change, and sensitive-page view per user. Distinct from [reporting-audit/activity](/en/inventory/reporting-audit/activity) which is **entity-centric** (one row per business-row change); user-activity is one row per **user-action event**, whether or not a business row changed.

**Audience:** **Auditor** (compliance trail), **Sysadmin** (account review), **Security Officer** (failed-login investigation, impersonation chain), **Compliance** (PII-aware exports to SIEM).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Find a user's login history | System Admin → **User Activity** → pick user | Default view groups by user; drill into session timeline |
| Investigate failed logins | Filter **event type = login**, **failed-login flag = true** | `actor_id = NULL`, `meta_data.username_attempted` carries offered identifier |
| See sensitive docs opened in a session | Drill into session → timeline shows `login → views → logout` | Only pages with logged-view permission emit `view` rows |
| Export for compliance | Same query path → CSV / JSON snapshot | Typically shipped quarterly to SIEM |
| Review impersonation chain | Open event → `meta_data.impersonation_chain` | Security Officer grant required |
| Check own activity | Profile screen → activity tab | Users can read their own timeline |
| Find expired-session reaps | Filter `meta_data.cause = 'expired'` | Synthetic logout rows emitted by cleanup job |

## 3. Common Questions

| Symptom / Question | Cause / Answer | Action |
|---|---|---|
| Why no `tb_user_activity` table? | Surface is **reconstructed** — session + filtered `tb_activity` | See callout above; dedicated table is roadmap |
| Are sessions PII? | Yes — `ip_address` and `user_agent` are PII in most jurisdictions | `user_agent` redacted to family/version on screen unless Security Officer grant |
| Why doesn't this page show every page view? | Only pages opting into view-logging (PR/PO detail, costing, financial reports) emit `view` rows | Other navigations are not logged |
| Can I edit a row? | No — `tb_activity` is **immutable post-insert**; `tb_user_login_session` is insert / delete only | — |
| Failed login has `actor_id = NULL` — bug? | Intentional — unauthenticated context. Identifier sits in `meta_data.username_attempted` | — |
| Where is the orphaned-session logout? | Cleanup job emits synthetic `logout` with `meta_data.cause = 'expired'` after `expired_on` | — |
| Cross-tenant viewing? | Only Platform Admin, only against cold-storage audit copies, never live tenant tables | — |

## 4. Edge Cases

- **Append-only.** `tb_activity` rows are immutable post-insert; `tb_user_login_session` is insert / delete only. No application path updates user-activity events.
- **Login / logout pairing.** Login event and session insert happen in the same transaction; `entity_id` matches session `id`. Logout deletes session + inserts paired `logout` activity row.
- **Orphaned sessions** are reaped at `expired_on` by the cleanup job, which emits a synthetic `logout` with `meta_data.cause = 'expired'`.
- **Time-zone.** All timestamps `Timestamptz(6)` UTC; UI renders in operator's profile timezone with raw-UTC tooltip.
- **Retention.** `tb_activity` ages out per tenant policy (cold storage); session rows deleted at `expired_on` or sooner on logout — no long-term retention of session tokens.
- **RBAC.** Own timeline via profile; platform-wide screen gated to Sysadmin / Security Officer / Auditor; cross-tenant only via cold storage.

---

## 5. Data Model (Dev)

Two tables compose the surface — **no single `tb_user_activity` table exists today.**

### 5.1 `tb_user_login_session` (platform)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `token` | `String @db.VarChar` | No | Issued session token (or hashed reference). |
| `token_type` | `enum_token_type` | No | Default `access_token`. `access_token` / `refresh_token`. |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user.id`. |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + 1 day`. Session expiry. |

**Constraints:** unique on `token`. FK to `tb_user.id`. Row insert = "session opened" (functional login); deletion / expiry = "session closed". No `created_at` / IP / user-agent on this table — those live in `tb_activity` for the paired login event.

### 5.2 `tb_activity` (tenant) — filtered projection

Filter on `action IN ('login', 'logout', 'view')` and group by `actor_id`.

| Field | Used as | Description |
| --- | --- | --- |
| `actor_id` | User identity | Joins platform `tb_user.id`. `NULL` for failed logins. |
| `action` | Event type | `login` / `logout` / `view` for user-activity. |
| `entity_type`, `entity_id` | Target | For `view`, sensitive document opened. For `login` / `logout`, typically `entity_type = 'session'` with `entity_id = tb_user_login_session.id`. |
| `ip_address`, `user_agent` | Forensic context | Canonical source for client info (PII — redacted on display). |
| `meta_data` | Extra | Failed-login reason, MFA flag, impersonation chain, `cause = 'expired'` for synthetic logouts. |
| `created_at` | Event timestamp | UTC `Timestamptz(6)`. |

See [reporting-audit/activity](/en/inventory/reporting-audit/activity) for the full table definition.

**Inferred — to be verified.** A future `tb_user_activity` table would carry `(user_id, event_type, event_at, ip_address, user_agent, target_type, target_id, meta_data)` with composite indexes on `(user_id, event_at DESC)` and `(event_type, event_at DESC)`.

## 6. Business Rules

- **Login / logout pairing.** Activity row + session row inserted in the same transaction; `entity_id` matches session id. Logout deletes session + inserts paired `logout` row.
- **Failed-login capture.** Insert with `actor_id = NULL`, `action = 'login'`, `meta_data.success = false`, `meta_data.username_attempted = <offered>`. No session row created. `tb_user.failed_login_count` incremented same path.
- **PII redaction.** `user_agent` rendered as parsed family/version on screen unless operator holds Security Officer grant.
- **RBAC.** Own timeline via profile; platform-wide gated to Sysadmin / Security Officer / Auditor; cross-tenant via cold storage only.
- **Retention.** Activity per tenant policy (cold-storage migration); sessions deleted at `expired_on` or earlier.
- **Time-zone.** All timestamps UTC; rendered in profile timezone.

## 7. Cross-References

- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — underlying tenant table; user-activity is a filtered + joined projection over it plus session.
- [access-control/user](/en/inventory/access-control/user) — `actor_id` / session `user_id` resolve through platform `tb_user`.
- [access-control/permission](/en/inventory/access-control/permission) — view-permission grants drive which sensitive-page opens emit `view` rows.

## 8. References

- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_login_session` (lines 456-465), `enum_token_type` (577-580), `tb_user` (~360-454).
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (~277-297), `enum_activity_action` (~67-89).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/user-activity/`.
- **Authentication middleware:** `../carmen-turborepo-backend-v2/apps/` — login / logout handlers write paired session + activity rows.
