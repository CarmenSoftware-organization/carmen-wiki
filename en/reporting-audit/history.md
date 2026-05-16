---
title: Report History
description: Append-only archive of every executed report run — date, parameters, status, link to the generated artefact.
published: true
date: 2026-05-17T08:00:00.000Z
tags: reporting-audit, history, archive, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Report History

> **At a Glance**
> **Owner:** `micro-report` executor (read-only UI) &nbsp;·&nbsp; **Table:** `tb_report_job` &nbsp;·&nbsp; **Retention:** `expires_at` per tenant policy (artefact reaped; row kept) &nbsp;·&nbsp; **Used by:** Reports → History, Print History drawer &nbsp;·&nbsp; **Append-only audit log of every report run.**

## 1. What & Who

Report History is the **append-only execution log** for every report run on the tenant — ad-hoc exports, Print invocations, and scheduled runs all land here. Each row captures the report identifier, the concrete filter set, requesting user (or schedule), lifecycle state, and a pointer to the produced artefact in blob storage.

**Audience:** **Auditor** (who ran what), **Sysadmin** (failed-run triage), **Compliance** (export trail), **Tester** (verify the right template fired).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Find yesterday's report run | Reports → **History** | Filter by date range + report type |
| Re-download an output | History row → **Download** | Works until `expires_at` reaper deletes artefact |
| See who triggered a run | History row → **Requester** column | Schedule runs show schedule owner via `requested_by_id` |
| Re-run a report with the same filters | History row → **Re-run** | Re-enqueues a fresh job with identical `filters` / `options` |
| View full filter set used | History row → **View Details** | Renders the `filters` and `options` JSON |
| Investigate a failed run | Filter by `status = failed`, open Details | `error_message` carries the scrubbed cause |
| Confirm a Print fired | Document detail → **Print History** drawer | Shows recent jobs against that document |

## 3. Common Questions

| Symptom / Question | Cause / Answer | Action |
|---|---|---|
| Download link returns 404 | `expires_at` passed; reaper deleted the artefact | Row remains for audit; **Re-run** to regenerate |
| Why is my row missing? | RBAC filtered — you are neither the requester nor a category reader | Ask Sysadmin or hold the report's read permission |
| Can I edit a row? | No — table is **append-only**; only the executor mutates `status` / terminal fields | Re-run instead |
| Why is `started_at` null? | Job is still `queued` (executor hasn't picked it up) | Wait, or check executor health |
| What format will I get? | Whatever was requested at enqueue: `pdf` / `excel` / `csv` / `json` | Pick at submit, not re-download |
| Where do output files live? | Blob storage; `file_url` is the resolved download URL | Backed by tenant storage config |
| Is the error message safe to share? | Yes — credentials, tokens, raw SQL values are scrubbed; only bound param names survive | — |

## 4. Edge Cases

- **Append-only.** Executor writes on enqueue and updates only lifecycle / artefact / error fields. No other path mutates this table.
- **Retention split.** Artefact (file_url) ages out at `expires_at`; row stays so "who ran what against which filters" survives forever (subject to tenant policy).
- **Time-zone.** All timestamps are `Timestamptz(6)` UTC; UI renders in profile timezone. Scheduled runs encode intended fire time in `options.scheduled_fire_at`.
- **RBAC on reading.** Visible to requester, category readers, or Sysadmin / Auditor. Frontend filters server-side; never trust the client.
- **Failed / cancelled jobs** may use a shorter retention horizon since they have no artefact.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 5.1 `tb_report_job`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `report_type` | `String @db.VarChar(100)` | No | Logical identifier matching the template. |
| `report_category` | `enum_report_category` | No | `inventory` / `procurement` / `recipe` / `vendor` / `financial` / `operational`. |
| `format` | `enum_report_format` | No | `pdf` / `excel` / `csv` / `json`. |
| `status` | `enum_report_job_status` | No | Default `queued`. `queued` / `processing` / `completed` / `failed` / `cancelled`. |
| `filters` | `Json? @db.JsonB` | Yes | Default `{}`. Concrete filter values for this run. |
| `options` | `Json? @db.JsonB` | Yes | Default `{}`. Render options + `scheduled_fire_at` for scheduled runs. |
| `file_url`, `file_name`, `file_size`, `row_count` | mixed | Yes | Artefact metadata. |
| `error_message` | `String?` | Yes | Populated when `status = failed`; scrubbed of secrets. |
| `started_at`, `completed_at`, `expires_at`, `duration_ms` | mixed | Yes | Execution / retention timestamps. |
| `requested_by_id` | `String @db.Uuid` | No | Requesting user (or schedule's `created_by_id`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** indexes on `status`, `report_type`, `requested_by_id`, and `created_at DESC` (dominant access pattern). No FK to `tb_report_schedule`; the link is logical via matching `report_type` + correlation id in `options`.

## 6. Business Rules

- **Lifecycle.** `queued → processing → (completed | failed | cancelled)`. `started_at` set on entering `processing`; `completed_at` + `duration_ms` set on every terminal state. `cancelled` reachable from `queued` or `processing`.
- **Output retention.** `expires_at` drives the storage reaper. After it passes, the artefact behind `file_url` is deleted; the row remains.
- **RBAC.** Row visible to (a) requester, (b) category read permission holder, or (c) Sysadmin / Auditor.
- **Time-zone of record.** Timestamps stored UTC. Scheduled runs persist intended fire time in `options.scheduled_fire_at` so review is unambiguous.
- **No PII in errors.** Executor scrubs credentials, tokens, raw SQL values; only bound param names survive.

## 7. Cross-References

- [[reporting-audit/report]] — parent module; every `kind = report` template firing produces a row here.
- [[reporting-audit/schedule]] — recurring runs enqueue jobs here; `last_run_at` derived from latest completed job.
- [[reporting-audit/activity]] — `export` and `print` actions are also logged with `entity_type = 'report_job'`.
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]] — Print invocations land here.
- [[access-control/user]] — `requested_by_id` resolves through platform `tb_user`.

## 8. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (lines 5652-5683), `enum_report_job_status` (5644-5650), `enum_report_format` (~5628-5633), `enum_report_category` (~5635-5642).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/report/history/`.
- **Reports microservice:** `../micro-report/controller/report_controller.go`, `../micro-report/db/report_job_repo.go`.
