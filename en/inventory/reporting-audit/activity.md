---
title: Activity
description: Tenant-wide activity log — every meaningful state change captured as a row with actor, entity, before/after snapshot, IP, and user agent. Surfaced only through the platform-wide /system-admin/activity-log screen — no embedded per-document drawer exists.
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, activity, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Activity

> **At a Glance**
> **Owner:** Append-only (audit service) &nbsp;·&nbsp; **Table:** `tb_activity` &nbsp;·&nbsp; **Used by:** every transactional module's audit chain &nbsp;·&nbsp; The tenant audit log — one row per meaningful state change.

![Activity screen](/screenshots/reporting-audit/activity.png)

## 1. What & Who

The activity table is the **tenant audit log** — one row per meaningful state change. It captures *who did what to which row* without coupling writer to consumer: every transactional module appends via a single audit service; consumers (compliance export, in-app history panel, security forensics) read by `entity_type` + `entity_id`. Complements per-row audit columns (`created_by_id`, etc.) with the full event chain plus old/new snapshots and request context.

The table is intentionally generic and write-heavy. `entity_type` is a free-form string discriminator; `entity_id` is the target UUID; `action` enum covers lifecycle verbs.

**Maintained by** the audit service (writes only). **Read by** exactly one screen — `/system-admin/activity-log`. No embedded per-document "Activity drawer" was found anywhere in `carmen-inventory-frontend-react`; `useActivityLog`/the `ACTIVITY_LOGS` endpoint is referenced only by `activity-log-component.tsx` and its own table hook.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Browse the activity log | `/system-admin/activity-log` | List or grid display; filters for **action**, **entity type**, and **user** (actor), plus free-text search |
| Filter by action | Action multi-select | Curated to 5 options in the UI (`create`, `update`, `delete`, `login`, `logout`) — the enum has 20 values total; other actions are written but not offered as a quick filter |
| Filter by entity type | Entity Type multi-select | Curated ~13-value list (`purchase_request`, `purchase_order`, `good_received_note`, `credit_note`, `store_requisition`, `inventory_transaction`, `product`, `vendor`, `location`, `department`, `currency`, `period`, `auth`) — `entity_type` itself is free-form, so other values can exist in the data without a matching filter chip |
| Export the current filtered view | **Export** button | Client-side XLSX export (`useExportActivityLog`), same query params as the list |
| Print | **Print** button | Browser print of the current page |
| Inspect one row | Click a row | Opens `ActivityLogDetailSheet` — the closest equivalent to a "diff old vs new" view; renders `old_data`/`new_data` JSONB |
| **Not available anywhere** | — | A per-document "Activity" drawer/tab embedded on PR/PO/GRN/etc. detail pages does not exist — the platform-wide list screen is the only surface, filterable by `entity_type` + a manually-copied `entity_id` if needed via URL params |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Missing activity rows for a known change | Service-layer interceptor bypassed | Confirm change went through audit service, not raw SQL |
| `actor_id IS NULL` | System actor (background job) — expected | No fix; treat as system action |
| `old_data` empty on update | Snapshotter ran after the write | Bug — snapshotter must capture before-state |
| Audit log slow | Date-range scan on `created_at` | Use entity-scoped query when possible; or partition |

## 4. Edge Cases

- **Append-only.** App code never updates rows — `updated_*` exists for symmetry only. Hard-delete reserved for retention purges.
- **No FK enforcement on `entity_id`.** Polymorphic across many tables; stale rows are intentional (still valuable for deleted-entity audit).
- **Cross-schema actor.** `actor_id` references platform `tb_user.id` without an enforced relation. `NULL` = system actor.
- **Retention.** Tenant-policy driven; schema imposes no cap. Scheduled job may move old rows to cold storage.

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
| `old_data` | `Json? @db.JsonB` | Yes | Default `{}`. Snapshot before. |
| `new_data` | `Json? @db.JsonB` | Yes | Snapshot after. |
| `ip_address` / `user_agent` / `description` | `String?` | Yes | Request metadata + optional summary. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Added 2026-06-12 across 103 tenant tables; not independently confirmed as read/written for this append-only table. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@index([entity_type, entity_id])` map `activity_entitytype_entityid_idx` — supports "history of row X in table Y". `actor_id` has no DB relation (cross-schema).

**`enum_activity_action`:** `view`, `create`, `update`, `delete`, `login`, `logout`, `approve`, `reject`, `cancel`, `void`, `print`, `email`, `other`, `upload`, `download`, `export`, `import`, `copy`, `move`, `rename`, `save`.

## 6. Business Rules

- **Append-only.** No updates from app code; hard-delete reserved for retention purges.
- **Snapshot fidelity.** `old_data` / `new_data` carry the full row JSON at change time; diffing is a render concern. Secrets redacted before persistence.
- **No `entity_id` FK enforcement.** Polymorphic; stale rows are intentional.
- **Cross-schema actor.** Unenforced FK; `NULL` = system actor.
- **Performance.** Indexing intentionally minimal (composite covers dominant pattern); date-range scans may need partitioning at scale.
- **Retention.** Tenant-policy driven; schema imposes no cap.

## 7. Cross-References

- All transactional modules — [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory](/en/inventory/inventory), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [costing](/en/inventory/costing), [vendor-pricelist](/en/inventory/vendor-pricelist), [product](/en/inventory/product), [recipe](/en/inventory/recipe).
- [access-control/user](/en/inventory/access-control/user) — `actor_id` resolution.
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) — workflow events typically fan out to both.
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — `upload` / `download` actions logged with `entity_type = 'attachment'`.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (line ~280), `enum_activity_action` (line ~56).
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/activity-log/activity-log.route.tsx`, `activity-log-component.tsx`, `activity-log-detail-sheet.tsx`.
- **Frontend hook/type:** `../carmen-inventory-frontend-react/hooks/use-activity-log.ts` (`useActivityLog`, `useExportActivityLog`), `types/activity-log.ts`.
- **Writer (example):** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` — `logAuthActivity()` writes `login`/`logout` rows to the user's default business unit only.
