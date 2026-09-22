---
title: Activity
description: Tenant-wide activity log — every state change as a row with actor, entity, before/after snapshot, IP and user agent; read via /system-admin/activity-log and, since 2026-08, a per-record Activity sheet on every list and detail page.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: reporting-audit, activity, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Activity

> **At a Glance**
> **Owner:** Append-only (audit service) &nbsp;·&nbsp; **Table:** `tb_activity` (tenant) &nbsp;·&nbsp; **Used by:** every transactional module's audit chain &nbsp;·&nbsp; **Read surfaces:** `/system-admin/activity-log` (platform-wide list) **and** the per-record **Activity sheet** (`components/share/activity-sheet.tsx`) reachable from the row menu of 27 lists and the header of 15 detail pages &nbsp;·&nbsp; **Not this table:** UI click/page-view telemetry (`tb_activity_event`) — see §9

![Activity screen](/screenshots/reporting-audit/activity.png)

## Implementation status (re-verified 2026-09-22)

Three corrections to the 2026-07-22 version of this page:

1. **A per-document Activity drawer now exists.** Frontend commits `cc37c779` (2026-08-04, "Activity" item in the `DataGrid` row menu, enabled for 27 lists) and `21dc1792` (2026-08-04, Activity button on 15 detail-page headers) added `components/share/activity-sheet.tsx`, opened from anywhere through `openActivity(id, label)` in `activity-sheet-host.tsx` (a `CustomEvent` host mounted once in `routes/root-layout.tsx`; 16 call sites at HEAD). It reads two endpoints that the previous page did not list: `GET /api/{bu}/activity-logs/record/{entity_id}` (timeline, oldest first, optional `entity_type`) and `GET /api/{bu}/activity-logs/{id}/detail` (one row plus a computed `changes` diff). Recipe and equipment lists are deliberately **not** in the activity registry (no row-menu Activity there).
2. **`enum_activity_action` has 25 values, not 20/21.** `comment`, `submit`, `review` (tenant migration `20260727120000_add_activity_action_comment_submit_review`) and `email_sent` (`20260908120000_add_email_sent_activity_action`) were appended; the `/system-admin/activity-log` action filter now offers **all 25** values with icons (`c07d6805`), not a curated 5.
3. **Redaction is concrete.** Snapshot values under the keys `password`, `hash`, `token`, `secret`, `api_key`, `url_token`, `pricelist_url_token` are masked before the row is written (`packages/prisma-shared-schema-tenant/src/client.ts` `sensitiveFields`; the two RFP magic-link keys were added on 2026-09-12, `14c3f1daf`, because `loadEntitySnapshot` copies whole rows and the matcher is exact-key).

## 1. What & Who

The activity table is the **tenant audit log** — one row per meaningful state change. It captures *who did what to which row* without coupling writer to consumer: every transactional module appends via a single audit service; consumers read by `entity_type` + `entity_id`. Complements per-row audit columns (`created_by_id`, etc.) with the full event chain plus old/new snapshots and request context.

The table is intentionally generic and write-heavy. `entity_type` is a free-form string discriminator; `entity_id` is the target UUID; `action` enum covers lifecycle verbs.

**Maintained by** the audit service (writes only). **Read by** two surfaces: the platform-wide list at `/system-admin/activity-log` (`useActivityLog`, `hooks/use-activity-log.ts`) and the per-record **Activity sheet** (§1.1).

### 1.1 Per-record Activity sheet

`ActivitySheet` shows one record's history as a timeline (newest first in the UI; the API returns oldest first). Tapping a row expands it and loads `GET .../activity-logs/{id}/detail`, whose `changes` object is computed server-side by `buildActivityDiff(old_data, new_data)` (`packages/log-events-library/src/activity/activity-diff.ts`):

```
changes: {
  fields:   [{ field, old, new }],                      -- header columns that differ
  children: [{ relation, added[], removed[], updated: [{ id, fields[] }] }],
  has_changes: boolean                                  -- ignores updated_at / updated_by_id / doc_version
}
```

A create has no `old_data` and a delete has no `new_data`, so every field of the one existing snapshot is reported as the change. The sheet needs only the entity id (UUIDs do not collide across tables); the child-table headings are derived from the `entity_type` returned on each row. The same timeline component is reused for workflow history so both sheets read alike on a document page.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Browse the activity log | `/system-admin/activity-log` | List or grid display; filters for **action**, **entity type**, and **user** (actor), plus free-text search; saved views and the Linear-style popover filter menu (2026-08) |
| See one document's history | Any list row menu → **Activity**, or the **Activity** button on a detail-page header | Opens `ActivitySheet` for that `entity_id`; expand a row to see the field/child-line diff. Not available on recipe/equipment lists |
| Filter by action | Action select | All 25 `enum_activity_action` values, ordered as in `schema.prisma` |
| Filter by entity type | Entity Type select | Curated 13-value list (`purchase_request`, `purchase_order`, `good_received_note`, `credit_note`, `store_requisition`, `inventory_transaction`, `product`, `vendor`, `location`, `department`, `currency`, `period`, `auth`) — `entity_type` itself is free-form, so other values can exist in the data without a matching option |
| Export the current filtered view | **Export** button | Client-side XLSX export (`useExportActivityLog`), same query params as the list |
| Print | **Print** button | Browser print of the current page |
| Inspect one row | Click a row | Opens `ActivityLogDetailSheet` — renders `old_data`/`new_data` JSONB |
| Delete rows | **Not in the UI** | The gateway exposes `DELETE …/activity-logs/{id}` (soft), `DELETE …/batch/soft`, `DELETE …/{id}/hard`, `DELETE …/batch/hard` (AppIdGuard `activityLog.delete|deleteMany|hardDelete|hardDeleteMany`) and the frontend declares `system_admin.activity_log.delete`, but `activity-log-component.tsx` renders no delete action — unconfirmed whether anything calls these routes |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Missing activity rows for a known change | Service-layer interceptor bypassed | Confirm change went through audit service, not raw SQL |
| `actor_id IS NULL` | System actor (background job) — expected | No fix; treat as system action |
| `old_data` empty on update | Snapshotter ran after the write | Bug — snapshotter must capture before-state |
| Activity sheet shows "no changes" for an update | `has_changes = false` — only housekeeping fields (`updated_at`, `updated_by_id`, `doc_version`) moved | Expected; nothing user-visible changed |
| Snapshot shows `***` / masked value | Key matched `sensitiveFields` (`password`, `hash`, `token`, `secret`, `api_key`, `url_token`, `pricelist_url_token`) | Expected — never stored in clear |
| Audit log slow | Date-range scan on `created_at` | Use entity-scoped query when possible (`/record/{entity_id}`); or partition |

## 4. Edge Cases

- **Append-only from application code.** Writers never update rows — `updated_*` exists for symmetry only. Soft/hard delete endpoints exist on the gateway (see §2) for retention purges; no UI path calls them.
- **No FK enforcement on `entity_id`.** Polymorphic across many tables; stale rows are intentional (still valuable for deleted-entity audit).
- **Cross-schema actor.** `actor_id` references platform `tb_user.id` without an enforced relation. `NULL` = system actor.
- **`email_sent` is written on failure too.** `purchase-order.service.ts` records one `email_sent` row per PO email-send attempt, success or failure (`1897b4fc1`); RFP email send does the same (`request-for-pricing.service.ts`).
- **Retention.** Tenant-policy driven; schema imposes no cap. No scheduled purge for `tb_activity` exists in `micro-cronjobs` (its `activity_retention` job targets `tb_activity_event`, the telemetry table — §9).

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_activity`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `action` | `enum_activity_action?` | Yes | Lifecycle verb. |
| `entity_type` | `String?` | Yes | Free-form discriminator (e.g. `purchase_request`). |
| `entity_id` | `String? @db.Uuid` | Yes | Target row UUID. |
| `actor_id` | `String? @db.Uuid` | Yes | Acting user (cross-schema; not enforced). |
| `meta_data` | `Json? @db.JsonB` | Yes | Default `{}`. Request context (route, session, correlation id). |
| `old_data` | `Json? @db.JsonB` | Yes | Default `{}`. Snapshot before (sensitive keys masked). |
| `new_data` | `Json? @db.JsonB` | Yes | Snapshot after (sensitive keys masked). |
| `ip_address` / `user_agent` / `description` | `String?` | Yes | Request metadata + optional summary. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Added 2026-06-12 across 103 tenant tables; not independently confirmed as read/written for this append-only table. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@index([entity_type, entity_id])` map `activity_entitytype_entityid_idx` — supports "history of row X in table Y" and the `/record/{entity_id}` timeline. `actor_id` has no DB relation (cross-schema).

**`enum_activity_action` (25):** `view`, `create`, `update`, `delete`, `login`, `logout`, `approve`, `reject`, `cancel`, `void`, `print`, `email`, `other`, `upload`, `download`, `export`, `import`, `copy`, `move`, `rename`, `save`, `comment`, `submit`, `review` (migration `20260727120000`), `email_sent` (migration `20260908120000`).

### 5.2 API surface (gateway `api/:bu_code/activity-logs`, `KeycloakGuard` + `x-app-id`)

| Verb & path | AppId guard | Returns |
|---|---|---|
| `GET /` (`?entity_type&entity_id&actor_id&action&start_date&end_date` + pagination/search/sort) | `activityLog.findAll` | Paginated rows with `actor_*` name fields and an `audit { created { at, id, name }, updated { at } }` object — there is no top-level `created_at` (`types/activity-log.ts` `getLogCreatedAt()`) |
| `GET /entity/:entity_type` | `activityLog.findAll` | Rows whose `entity_type` contains the value (case-insensitive) |
| `GET /record/:entity_id` (`?entity_type` optional) | `activityLog.findAll` | Every row for one record, **oldest first** (timeline). Bruno: `documents-and-reports/activity-log/GET-find-by-entity-id-…bru` |
| `GET /:activity_log_id/detail` | `activityLog.findOne` | One row + `changes` (§1.1). Bruno: `GET-find-one-detail-…bru` |
| `GET /:activity_log_id` | `activityLog.findOne` | One row |
| `DELETE /:id`, `DELETE /batch/soft`, `DELETE /:id/hard`, `DELETE /batch/hard` | `activityLog.delete` / `deleteMany` / `hardDelete` / `hardDeleteMany` | No frontend caller found |

Platform records (clusters, business units, users, report templates) have their own audit trail in the **platform** `tb_activity` with `api-system/platform/activity-logs/record/:entity_id` and `/:id/detail` (platform permissions `activity_log.read` / `activity_log.detail`, `platform-activity-logs.controller.ts`, 2026-08-31) — documented in the Platform book, not here.

## 6. Business Rules

- **Append-only.** No updates from app code; delete endpoints reserved for retention purges.
- **Snapshot fidelity.** `old_data` / `new_data` carry the full row JSON at change time; diffing is done on read (`buildActivityDiff`). Sensitive keys are masked before persistence (`sensitiveFields`, exact-key match — `token` does not cover `url_token`, which is why both are listed).
- **No `entity_id` FK enforcement.** Polymorphic; stale rows are intentional.
- **Cross-schema actor.** Unenforced FK; `NULL` = system actor.
- **Performance.** Indexing intentionally minimal (composite covers dominant pattern); date-range scans may need partitioning at scale.
- **Retention.** Tenant-policy driven; schema imposes no cap.

## 7. Cross-References

- All transactional modules — [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory](/en/inventory/inventory), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [costing](/en/inventory/costing), [vendor-pricelist](/en/inventory/vendor-pricelist), [product](/en/inventory/product), [recipe](/en/inventory/recipe).
- [access-control/user](/en/inventory/access-control/user) — `actor_id` resolution.
- [reporting-audit/user-activity](/en/inventory/reporting-audit/user-activity) — the `entity_type = 'auth'` projection of this table.
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) — workflow events typically fan out to both.
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — `upload` / `download` actions logged with `entity_type = 'attachment'`.
- [reporting-audit/report](/en/inventory/reporting-audit/report) — PO / RFP email-with-PDF sends write `email_sent`.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity`, `enum_activity_action`; migrations `20260727120000_add_activity_action_comment_submit_review`, `20260908120000_add_email_sent_activity_action`.
- **Redaction:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/src/client.ts` — `sensitiveFields`.
- **Diff:** `../carmen-turborepo-backend-v2/packages/log-events-library/src/activity/activity-diff.ts` — `buildActivityDiff()`; consumer `apps/micro-business/src/log/activity-log/activity-log.service.ts` `findOneDetail()`.
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/activity-logs/activity-logs.controller.ts`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/documents-and-reports/activity-log/*.bru` (list, by-id, find-by-entity, find-by-entity-id, find-one-detail, four delete variants).
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/activity-log/activity-log.route.tsx`, `activity-log-component.tsx` (`ACTION_OPTIONS`, `ENTITY_TYPE_OPTIONS`), `activity-log-detail-sheet.tsx`.
- **Frontend sheet:** `../carmen-inventory-frontend-react/components/share/activity-sheet.tsx`, `activity-sheet-host.tsx` (`openActivity()`, mounted in `routes/root-layout.tsx`).
- **Frontend hook/type:** `../carmen-inventory-frontend-react/hooks/use-activity-log.ts` (`useActivityLog`, `useActivityLogByRecord`, `useActivityLogDetail`, `useExportActivityLog`), `types/activity-log.ts` (`ActivityLog`, `ActivityLogDetail`, `ActivityFieldChange`, `ActivityChildChange`).
- **Writers (examples):** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` — `logAuthActivity()` (`login`/`logout`, default BU only); `apps/micro-business/src/procurement/purchase-order/purchase-order.service.ts` — `email_sent`.

## 9. Not this table — UI telemetry

Click and page-view events captured by the frontend (`lib/analytics.ts`: batches of up to 50, flushed every 10 s, `POST /api/analytics-events`, max 100 events per request, deduplicated by `event_id`, user/app/domain stamped server-side) land in the **platform** table `tb_activity_event`, are rolled up nightly into `tb_activity_event_daily` by the `micro-cronjobs` `activity_rollup` job and purged after 365 days by `activity_retention` (both 2026-07-30). That pipeline has nothing to do with `tb_activity` — it is documented in the Platform book: [Activity Events](/en/platform/activity-events) (per-event explorer, `activity_event.detail`) and [Usage Analytics](/en/platform/usage-analytics) (dashboard, `activity_event.read`).
