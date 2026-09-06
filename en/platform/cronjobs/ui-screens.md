---
title: Cronjobs — UI Screens
description: CronJobManagement's list, filters, and summary stats; CronJobEdit's basics/schedule/execution/type-config cards; and CronScheduleField's six-mode schedule builder.
published: true
date: '2026-09-06T23:10:00.000Z'
tags: book/platform, cronjobs, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Cronjobs — UI Screens

> **Screens:** `CronJobManagement` (list, `/cronjobs`) &nbsp;·&nbsp; `CronJobEdit` — one component for both create (`/cronjobs/new`) and edit (`/cronjobs/:id/edit`) &nbsp;·&nbsp; **No tabs, no wizard** — four stacked cards on the edit form &nbsp;·&nbsp; **Sub-component:** `CronScheduleField`, a six-mode cron builder, plus six per-job-type config field components (`jobConfig/`) &nbsp;·&nbsp; **Dialogs:** Delete-job confirm (ownership-aware message) &nbsp;·&nbsp; **Persisted UI state:** one `localStorage` key (`perpage_cronjob`) &nbsp;·&nbsp; **Concurrency:** `doc_version` optimistic lock, sent only when the GET that loaded the form returned one &nbsp;·&nbsp; **Screenshots:** deferred per plan — no screenshot assets exist for this module

## 1. Overview

This module has two screens. `CronJobManagement.tsx` (read in full) is a standard server-paginated `DataTable` with a six-figure summary band above it. `CronJobEdit.tsx` (read in full) is the create form and the single-record edit page in one component — unlike the read-view/edit-mode toggle pattern used elsewhere in this book ([Database Pools](/en/platform/database-pools/ui-screens) §3–4), this page has no separate "view" mode at all: an existing job's form is simply pre-filled and always editable (subject to the `cronjob.manage` permission checks in [landing page](/en/platform/cronjobs) §4). The one piece of UI shared between create and edit that has real internal complexity of its own is `CronScheduleField` (§4), the cron-expression builder.

## 2. `CronJobManagement` — list page (`/cronjobs`)

### 2.1 Summary stat band

Six figures, rendered as a `grid` above the table, with a caption underneath stating the scope explicitly:

| Stat | Source | Scope |
|---|---|---|
| Total | `paginate.total` from the server | Whole table |
| Running | `items.filter(j => j.is_active).length` | **Loaded page only** |
| Stopped | `items.filter(j => !j.is_active).length` | **Loaded page only** |
| With Errors | `items.filter(j => !!j.last_error).length` | **Loaded page only** |
| Foreign-Owned | `items.filter(j => !!j.source_service).length` | **Loaded page only** |
| Active in Scheduler | `GET /api/cronjobs/status` → `scheduler.ActiveJobCount()` | Live, whole scheduler — independent of every other figure here |

The caption below the band exists specifically because four of the six numbers are page-scoped, not table-wide — see [Data Model](/en/platform/cronjobs/data-model) §5.2 for why "With Errors" in particular should not be read as "every failing job."

### 2.2 Search and filters

- **Search** is a debounced (300ms), server-side free-text match against `name`, `description`, `job_type`, `cron_expression`, and `source_service` (`cronjobService.ts`'s `defaultSearchFields`).
- **Filters** open a side sheet (`CronJobFilterSheet`) with exactly two fixed Selects: **Job Type** (all six types plus "All") and **Status** (Running / Stopped / "All"). There is no free-text/advanced filter grammar.
- An **Owner** filter ("All" vs. "Platform-owned only") existed at one point and was removed. The reason is a backend limitation, not a design change: the gateway's shared query-string parser (`parseFilterString`, `apps/backend-gateway/src/shared-dto/paginate.dto.ts`) drops any `key:value` pair whose value is an empty string before `platform_cronjobs.service.ts` ever sees it — so a "Platform-owned only" filter, which would need to send `source_service:` (empty), silently matched everything instead of excluding foreign-owned jobs. The component's own comment states the conclusion plainly: "A select that cannot filter is worse than an absent one."

### 2.3 Columns

| Column | Sortable | Notes |
|---|---|---|
| Name | Yes | Description shown as a muted line underneath when present |
| Type | Yes | Badge, one of the six `job_type` labels |
| Business Unit | No (value lives inside `job_config` JSON, not a sortable server column) | Populated only for `report`/`dashboard_refresh` (the two BU-scoped types); shows the first two `bu_codes` plus a `+N` overflow, "All" for an empty `dashboard_refresh` list, or a dash for every other type / an empty `report` list (empty `bu_codes` on a `report` job is a config error, not "all business units" — the column deliberately does not conflate the two) |
| Schedule | No | Raw cron expression plus a plain-language description (`describeCron`) underneath |
| Status | Yes | Running / Stopped badge from `is_active` |
| Owner | No | `source_service` badge, or "Platform" when unset |
| Last Run | Yes | Relative time; warning-triangle icon with the raw error tooltip when `last_error` is set — see [Data Model](/en/platform/cronjobs/data-model) §5.2 |
| Next Run | Yes | Absolute timestamp |
| Runs | Yes | `run_count`, right-aligned tabular figure |
| (actions) | — | Hidden entirely unless the session holds `cronjob.manage` |

### 2.4 Row actions

All four icons in the actions column are disabled (not hidden) for the specific row currently mid-flight, tracked by a single `actingJobId` piece of state rather than a whole-table lock — the component's own comment explains why this matters specifically for **Run Now**: unlike Start/Stop, a duplicated click does not merely repeat a harmless toggle, it independently starts a second real background run (a duplicate report email, a duplicate notification, or — for a `cleanup` job, once implemented — a deletion running twice).

| Icon | Action | Result |
|---|---|---|
| Play / Pause | Start / Stop | `POST /:id/start` or `/stop`; toast success; list refreshes |
| Zap | Run Now | `POST /:id/execute`; **`toast.info` "dispatched," not `toast.success`** — the endpoint hands the job to a background worker and returns before the outcome is known |
| Pencil | Edit | Navigates to `/cronjobs/:id/edit` |
| Trash | Delete | Opens the confirm dialog (§5) |

### 2.5 CSV export

Exports the **currently loaded page only** — the component's own comment notes that `perpage: -1` is not honoured by this endpoint (it silently returns 10 rows regardless), so this is never a full-table export. Ten columns: name, description, type label, business-unit label, cron expression, status label, owner label, last run, next run, run count.

### 2.6 Dev-only debug panel

In `NODE_ENV === 'development'` builds only, a floating `DevDebugSheet` exposes the raw loaded items, the current query parameters, and `{ total, activeJobs }` — not present in production.

## 3. `CronJobEdit` — create (`/cronjobs/new`) and edit (`/cronjobs/:id/edit`)

Four stacked cards, always in this order, plus a conditional fifth:

### 3.1 Basics

- **Name** (required — the only field with client-side blur validation; the backend's own update handler has no non-empty check, so a blank name typed then cleared could otherwise reach the database if not caught here).
- **Job Type** — a Select, **disabled once the job exists** (locked after creation; changing it would leave a stale `job_config` shaped for the old type, since the six configs share almost no fields).
- **Description** — free text, optional.
- **Active** — checkbox; equivalent to the list page's Start/Stop toggle.

### 3.2 Schedule

`CronScheduleField` (§4), plus — **`report` job type only** — a `notify_at` time input with a hint explaining it controls when recipients are told the report is ready, separately from when the job itself runs. No other job type renders this field, matching the backend fact that no other executor reads it ([Data Model](/en/platform/cronjobs/data-model) §3.1).

### 3.3 Execution

Two number inputs: **Max Retries** (default 0) and **Timeout (seconds)** (default 300). No explanatory copy beyond the labels; see [Data Model](/en/platform/cronjobs/data-model) §4.3 for what these values actually control.

### 3.4 Type Config

Renders one of six components (`jobConfig/`) selected by `job_type`, each backing the fields in [Data Model](/en/platform/cronjobs/data-model) §3:

| `job_type` | Component | Notable UI behavior |
|---|---|---|
| `report` | `ReportConfigFields` | Loads report templates and users live for two pickers (template dropdown, a searchable multi-select of recipient users by name/email — not a free-text field); a **Delivery Type** select (`file`/`viewer_url`); **no field for `viewer_url`'s endpoint at all**, by deliberate design (see [Data Model](/en/platform/cronjobs/data-model) §3.1's SSRF note) |
| `notification` | `NotificationConfigFields` | Same searchable multi-select pattern for `user_ids`; a hint states the field is required, correcting an earlier hint copied from `dashboard_refresh` that wrongly implied empty meant "everyone" |
| `cleanup` | `CleanupConfigFields` | Three free-text inputs (`action`, `type`, `older_than`) with no validation — matching the backend, which also validates nothing here |
| `dashboard_refresh` | `DashboardRefreshConfigFields` | A business-unit multi-select (empty genuinely means "every active BU" — the one type where that hint is accurate) and a Tier select (`operational`/`breakdown`/`matrix`/"All") |
| `activity_rollup` | `ActivityRollupConfigFields` | One number input, `days_back` (default 2) |
| `activity_retention` | `ActivityRetentionConfigFields` | Two number inputs, `retention_days` (default 365) and `batch_size` (default 10000) |

Switching Job Type on the **create** form resets `job_config` to `{}` in the same state update as the type change — never leaving a previous type's fields dangling in a shape TypeScript's weak union check would otherwise let compile silently.

### 3.5 History (existing job only, when audit data is present)

Renders `AuditMeta` — `created_at`/`created_by_id`/`updated_at`/`updated_by_id` only. **Does not show `last_run_at`, `next_run_at`, `last_error`, or `run_count`** — see [Data Model](/en/platform/cronjobs/data-model) §5.3 for why a tester should not expect run-failure evidence on this page at all.

### 3.6 Foreign-owned banner

When the loaded job's `source_service` is set, a warning banner appears above the form: "editing a job another service owns — changes here affect that business unit's schedule directly." The list page's delete-confirmation dialog carries an equivalent, more specific warning naming the owning service (§5).

### 3.7 Save, validation, and version conflicts

- **Client-side validation before submit:** name required (re-checked here, not only on blur, since `Ctrl/Cmd+S` and the native form submit both bypass the blur handler); cron expression required, then validated as parseable (`describeCron(...) === null` is treated as "invalid," distinct from an untouched/empty field, which reads as "required" instead).
- **`doc_version`** is included in the update payload only when the GET that loaded the form returned one — omitting it tells the gateway to skip the conflict check entirely, matching the pattern other optimistic-locked entities in this SPA use.
- **Version conflict (`409`, `error_code: VERSION_CONFLICT`)** — `micro-cronjobs`'s own error-code contract, read at the top level of the response body, distinct from the `DOC_VERSION_CONFLICT`/message-pattern contract the shared `isVersionConflict()` helper was written for Prisma-backed resources. The page checks the Go-specific code first, then falls back to the shared helper, and the component's own comment explicitly warns against ever removing either check as "redundant" — they are genuinely different contracts.
- **`FOREIGN_OWNED_JOB` (`409`)** — still handled in a dedicated branch (checked **before** the version-conflict branches, since both are 409s and only the error code tells them apart), even though the current gateway no longer emits it. Kept for an older gateway build that might still be deployed. See [landing page](/en/platform/cronjobs) §4.

## 4. `CronScheduleField` — the schedule builder

A single component shared by create and edit, built around one rule: **the cron expression string is the only state that exists.** Every render re-parses it (`parseCron(value)`) into the mode and field values the UI shows; there is no separate "which mode is active" flag stored anywhere, so typing directly into the raw expression field and using the guided controls can never drift out of sync with each other.

- **Six modes:** every N minutes, hourly, daily, weekly, monthly, and a raw 5-field custom grid (minute / hour / day-of-month / month / day-of-week). An expression the guided modes cannot represent (a range like `1-5`, a specific list of months) falls into custom mode automatically — not treated as an error, since the expression itself is perfectly valid.
- **Live description:** `describeCron()` renders a plain-language sentence under the expression field (e.g., "every day at 02:00"), distinguishing an untouched/empty field (blank sentence, no error) from a genuinely malformed one (`null` return, shown as an inline validation error).
- **Next 3 runs preview:** computed and shown under the description, with an explicit caption naming the **browser's** local timezone — deliberately not presented as the same fact as the server's resolved scheduler timezone (normally Asia/Bangkok), since the two can differ and the component has no way to know the server's zone from here. This caveat is the component's own fix, called out in its source comment as correcting an earlier version that presented the two as interchangeable.

## 5. Dialogs

### 5.1 Delete-job confirm (list page only)

Two message variants, chosen by whether the target job has a `source_service`:

- **Platform-owned:** a plain "delete this job?" naming the job.
- **Foreign-owned:** names both the job and the owning service, framed as removing that business unit's schedule permanently, since it cannot be recreated from this screen.

## 6. Persisted UI State

One `localStorage` key: `perpage_cronjob`, the list page's rows-per-page choice. Search, filters, sort, and page number are not persisted across visits.

## 7. References

- `../carmen-platform/src/pages/cronjobs/CronJobManagement.tsx` — list page, read in full.
- `../carmen-platform/src/pages/cronjobs/CronJobEdit.tsx` — create/edit page, read in full.
- `../carmen-platform/src/pages/cronjobs/CronJobFilterSheet.tsx`, `CronScheduleField.tsx` — read in full.
- `../carmen-platform/src/pages/cronjobs/jobConfig/{index.tsx,ReportConfigFields.tsx,NotificationConfigFields.tsx,CleanupConfigFields.tsx,DashboardRefreshConfigFields.tsx,ActivityRollupConfigFields.tsx,ActivityRetentionConfigFields.tsx}` — all six type-specific config components plus the dispatcher, read in full.
- `../carmen-platform/src/services/cronjobService.ts` — REST client, filter-encoding comment (§2.2).
- `../carmen-platform/src/utils/cronExpression.ts`, `cronSchedule.ts` — `describeCron`, `nextRuns`, `parseCron`, `buildCron`.
- `../carmen-platform/src/components/Can.tsx` — permission-gated render helper referenced throughout.
- [Data Model](/en/platform/cronjobs/data-model) — the field table and scheduler mechanics this page's screen tour points back to throughout.
- [Cronjobs landing page](/en/platform/cronjobs) §4 — the permission gates behind every button referenced here.
- Verified against `carmen-platform` HEAD `157a65e` (2026-09-04).
