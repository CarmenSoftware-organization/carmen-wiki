---
title: Activity
description: Tenant-wide activity log — every meaningful state change captured as a row with actor, entity, before/after snapshot, IP, and user agent.
published: true
date: 2026-05-16T08:00:00.000Z
tags: reporting-audit, activity, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Activity

## 1. Purpose

The activity table is the **tenant audit log** — one row per meaningful state change. It captures *who did what to which row* without coupling the writer to the consumer: every transactional module appends to `tb_activity` through a single audit service, and any downstream consumer (compliance export, in-app history panel, security forensics) reads from this table by `entity_type` + `entity_id`. It complements the per-row audit columns (`created_by_id`, `updated_by_id`, `deleted_by_id`) on each transactional model by recording the full chain of events with old/new snapshots and request-context metadata.

The table is intentionally generic and write-heavy. `entity_type` is a free-form string discriminator (e.g. `purchase_request`, `good_receive_note`, `inventory_adjustment`) and `entity_id` is the target row's UUID. `action` is an enum covering the lifecycle verbs the system tracks (`create`, `update`, `delete`, `approve`, `reject`, `cancel`, `void`, `print`, `email`, `upload`, `download`, `export`, `import`, `copy`, `move`, `rename`, `save`, `login`, `logout`, `view`, `other`). `old_data` and `new_data` are JSONB snapshots; `meta_data` carries request-level context.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_activity`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `action` | `enum_activity_action?` | Yes | The verb. See enum values below. |
| `entity_type` | `String?` | Yes | Free-form discriminator naming the target entity (e.g. `purchase_request`). |
| `entity_id` | `String? @db.Uuid` | Yes | The target row's UUID. |
| `actor_id` | `String? @db.Uuid` | Yes | The acting user. Conceptually FK to platform `tb_user.id`; no in-schema relation. |
| `meta_data` | `Json? @db.JsonB` | Yes | Default `{}`. Request context (route, session, correlation id). |
| `old_data` | `Json? @db.JsonB` | Yes | Default `{}`. Snapshot before the change. |
| `new_data` | `Json? @db.JsonB` | Yes | Snapshot after the change. |
| `ip_address` | `String?` | Yes | Client IP captured from the request. |
| `user_agent` | `String?` | Yes | Client user-agent string. |
| `description` | `String?` | Yes | Optional human-readable summary. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key on `id`. Composite index `@@index([entity_type, entity_id])` map `activity_entitytype_entityid_idx` — supports the dominant query "give me the history of row X in table Y". `actor_id` is conceptually a FK to platform `tb_user.id` but the relation is *not* declared (tenant schema cannot enforce cross-schema FKs).

**`enum_activity_action` values:** `view`, `create`, `update`, `delete`, `login`, `logout`, `approve`, `reject`, `cancel`, `void`, `print`, `email`, `other`, `upload`, `download`, `export`, `import`, `copy`, `move`, `rename`, `save`.

## 3. Usage / Cross-References

- **Every transactional module's audit chain** writes here. The audit service is invoked from service-layer interceptors in [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[costing]], [[vendor-pricelist]], [[product]], and [[recipe]].
- [[access-control/user]] — `actor_id` resolves to a user row for display ("X changed status to Approved").
- [[reporting-audit/notification]] — workflow stage transitions logged here may also fan out as notifications.
- [[reporting-audit/attachment]] — `upload` / `download` actions against attachments are logged here with `entity_type = 'attachment'`.

## 4. Configuration UI

There is no end-user configuration screen for activity itself — the table is **append-only by design**. The Sysadmin / Auditor read paths are:

- An **Activity History** drawer on each document detail page filters by `entity_type` + `entity_id` and renders the chronological event list.
- A platform-wide **Audit Log** screen (Sysadmin / Security Officer only) lists recent rows with filters on `actor_id`, `action`, date range, and entity_type.
- Compliance export hits the same query path and ships rows to long-term storage outside the application.

## 5. Business Rules

- **Append-only.** Application code never updates `tb_activity` rows. The `updated_*` audit columns exist for schema symmetry but are unused in normal flow. Hard-delete is reserved for retention-policy purges only.
- **No FK enforcement on `entity_id`.** Because `entity_type` is polymorphic across many tables, the FK to the target row cannot be declared. Stale rows (referencing a deleted entity) are acceptable — they are still valuable for "what was deleted, when, by whom".
- **Snapshot fidelity.** `old_data` and `new_data` should contain the full row JSON at the moment of change, not a diff. Diffing is a render concern. Snapshots may be redacted (passwords, tokens) by the audit service before persistence.
- **Cross-schema actor.** `actor_id` references platform `tb_user.id` but the relation is unenforced. Treat `NULL` as system actor (background jobs, migrations).
- **Performance.** Activity is the highest-write-volume table in the tenant. Indexing is deliberately minimal — the `(entity_type, entity_id)` composite covers the dominant access pattern. Date-range scans on `created_at` for the platform-wide audit log accept a full-table scan or rely on a separate partition strategy in production.
- **Retention.** Retention windows are tenant-policy driven; the schema imposes no cap. A scheduled job may move rows older than the retention horizon to cold storage.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (lines ~277-297), `enum_activity_action` (lines ~67-89).
- **Frontend route (if known):** Activity history drawer is embedded on each document detail page. Platform-wide audit log lives under Sysadmin tooling.
- **Cross-module:** see Section 3.
