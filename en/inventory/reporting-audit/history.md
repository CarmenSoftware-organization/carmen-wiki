---
title: Report History
description: Read-only list of tb_report_job rows — confirmed structurally orphaned under the current live system, since neither on-demand report runs, Print, nor scheduled fires write a job row through any reachable code path.
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, history, archive, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Report History

> **At a Glance**
> **Route:** `/report/history` &nbsp;·&nbsp; **Table:** `tb_report_job` (tenant schema — real, not dead) &nbsp;·&nbsp; **Screen:** read-only list — no re-run, no requester column, no filter-by-date, no Print-History drawer &nbsp;·&nbsp; **Confirmed gap:** no reachable path in the current frontend or scheduler writes a row to this table.

![Report History screen](/screenshots/reporting-audit/history.png)

## Implementation status (verified 2026-07-22)

`tb_report_job` itself is real — unlike `tb_report_schedule` (see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule)), it is actively read and written by `micro-report`'s Go `ReportJobRepo`. The problem is which paths write it:

- **"Run a report" on the report list** (`report-component.tsx` → `useRunReportMutation` → `POST /reports/viewer`) calls the `viewReport` handler, which mints a viewer URL directly and returns it — it never calls `ReportJobRepo.Create`.
- **Every "Print" button** (`lib/print-document.ts`'s `printDocument()`) resolves a print-template mapping and then calls the same `POST .../report/viewer` endpoint — also no job row.
- **Scheduled report fires** (see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule)) always deliver via `format: "viewer_url"` from the current create-schedule UI, which the executor dispatches through `executeViewerURL()` — again, no job row. Only the executor's legacy `executeFile()` branch (unreachable from the current UI) calls `POST .../report/generate-async`, the one endpoint that does write `tb_report_job`.
- A repo-wide search of the frontend confirmed **zero callers of `generate-async`, `generateAsync`, or `job-status`/`jobStatus`** anywhere in `carmen-inventory-frontend-react`.

**Net effect:** under the currently reachable UI, nothing populates `tb_report_job`. The `/report/history` screen is real, wired correctly to a real table and a real backend endpoint, but is expected to be **empty in practice** unless some other caller (a direct API integration, a future UI change, or a schedule whose `delivery.type` was set to `"file"` outside the normal create-dialog flow) uses the async-job path. This page is corrected to describe the actual screen and the gap; the previous version's claims about "every report run" landing here, a "Re-run" action, and a "Print History" drawer per document are removed as unconfirmed/absent.

## 1. What & Who

Report History is the `tb_report_job` execution log — when populated, one row per **async** job (`queued → processing → completed | failed | cancelled`), each carrying the report identifier, concrete filter set, requesting user, lifecycle state, and a pointer to the produced artefact. The `/report/history` screen (`history-component.tsx`) renders it as a plain paginated list.

**Audience:** any authenticated user with report-read access can view this screen — no distinct Auditor/Sysadmin-only gate was found on the `GET .../history` endpoint beyond the standard `KeycloakGuard` + `X-App-Id` header.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Browse job history | `/report/history` | List or grid display toggle; search box (server-side, matches `job_id`/`report_type`/`format`/`status`/`file_url`/`file_name`/`filters` text) |
| Open a completed job's file | Click the report-name link in a row | Only rendered as a link when `file_url` is present |
| **Not available in the current screen** | — | Re-run, a dedicated Requester column, date-range filter, a "View Details" drill-down of the stored `filters`/`options` JSON, and a per-document "Print History" drawer — none of these were found anywhere in `history-component.tsx`, `history-card.tsx`, or `use-history-table.tsx` |

## 3. Common Questions

| Symptom / Question | Cause / Answer | Action |
|---|---|---|
| Why is my history list always empty? | Expected under the current system — see Implementation status above; no reachable UI path writes `tb_report_job` | Not a bug per se; flag if the product intent is for on-demand runs and Print to be logged here |
| Where did my "Run" report actually go? | It rendered directly via the viewer endpoint — no job row, no history entry, no download-later capability | Re-open it via the same report/filters combination in the report list |
| Can I edit a row? | No CRUD/update endpoint exists for `tb_report_job` beyond the executor's own internal status transitions | — |
| What columns does the table actually show? | `#`, report name (linked when `file_url` exists), report type, format, status badge, row count | Confirmed via `use-history-table.tsx` — no requester or date column |

## 4. Edge Cases

- **Structurally orphaned, not broken.** The screen, hook, and backend endpoint are all wired correctly to a real table — the gap is that no currently-reachable write path exists, not a bug in the read path.
- **Append-only where it is written.** `ReportJobRepo` only ever inserts on `generate-async` and updates lifecycle/artefact/error fields afterward — no other code path mutates the table.
- **Time-zone.** All timestamps are `Timestamptz(6)` UTC on the underlying model; the current list UI does not render `started_at`/`completed_at`/`expires_at` at all (only `row_count` beyond status/format).
- **Retention (unconfirmed for reachability reasons).** `expires_at` exists on the model and would govern artefact reaping if the async path were ever exercised — not independently verified against a live reaper job in this pass.

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
| `filters` | `Json? @db.JsonB` | Yes | Default `{}`. |
| `options` | `Json? @db.JsonB` | Yes | Default `{}`. |
| `file_url`, `file_name`, `file_size`, `row_count` | mixed | Yes | Artefact metadata. |
| `error_message` | `String?` | Yes | Populated when `status = failed`. |
| `started_at`, `completed_at`, `expires_at`, `duration_ms` | mixed | Yes | Execution / retention timestamps. |
| `requested_by_id` | `String @db.Uuid` | No | Requesting user. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** indexes on `status`, `report_type`, `requested_by_id`, `created_at DESC`. No FK to `tb_report_schedule` (which is itself dead — see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule)).

## 6. Business Rules

- **Lifecycle.** `queued → processing → (completed | failed | cancelled)`, mutated only by `micro-report`'s `ReportJobRepo` (`Create`, `UpdateStatus`, `Complete`, `Fail`).
- **Only `generate-async` writes rows.** `viewer`, `data`, and `viewer-with-data` (the paths actually used by the report list, Print, and viewer-delivery schedules) never touch this table.
- **No PII-scrubbing claim independently verified.** The previous version's "credentials/tokens/raw SQL values scrubbed from `error_message`" claim was not confirmed against `ReportJobRepo.Fail()` in this pass — left as an unconfirmed carry-over rather than restated as fact.

## 7. Cross-References

- [reporting-audit/report](/en/inventory/reporting-audit/report) — the on-demand "Run" and Print paths that do **not** populate this table.
- [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) — the recurring-fire path; also does not populate this table under the current `viewer_url`-only delivery.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [vendor-pricelist](/en/inventory/vendor-pricelist) — Print buttons that resolve through the viewer path, not this table.
- [access-control/user](/en/inventory/access-control/user) — `requested_by_id`.

## 8. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (line ~6094), `enum_report_job_status` (line ~6086), `enum_report_format` (line ~6070), `enum_report_category` (line ~6077).
- **Backend (real, but only reachable via the unreached legacy path):** `../micro-report/controller/report_controller.go` (`generateAsync`, `jobStatus`, `history` handlers), `../micro-report/db/report_job_repo.go`, `../micro-report/model/job.go`.
- **Backend (the paths actually used — no job row):** `../micro-report/controller/report_controller.go`'s `viewReport` handler.
- **Frontend route:** `../carmen-inventory-frontend-react/routes/report/history/report-history.route.tsx`, `history-component.tsx`, `use-history-table.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-report-history.ts` — `useReportHistory` (list only; no re-run/detail hook exists).
