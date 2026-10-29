---
title: Tenant Seed — Lifecycle
description: How a seed status check and a streamed seed run work end to end - connection resolution, per-set missing detection, the NDJSON event protocol, the done summary and cancellation behaviour.
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, tenant-seed, lifecycle
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Tenant Seed — Lifecycle

> **At a Glance**
> **Operations:** status check · single-BU seed stream · fleet seed (SPA loop) &nbsp;·&nbsp; **Not in this module:** delete or reset seed data, update existing rows, scheduling, a server-side "all BUs" endpoint &nbsp;·&nbsp; **Endpoints:** `GET .../:bu_id/status`, `POST .../:bu_id/deploy/stream` under `api-system/tenant/seeds` &nbsp;·&nbsp; **Cross-entity effects:** writes into the BU's tenant database only

## 1. Overview

Both operations follow the same path: SPA, gateway (`TenantSeedsController`, guarded by `TenantMigrationGuard`), RPC to micro-business (`TenantSeedService`), then a direct Prisma connection to the tenant database. Nothing is written to the backstage database; the audit trail is the structured log line `tenant-seed.audit`.

## 2. Resolving the tenant connection

`resolveConnection(bu_id)` (micro-business):

1. `bu_id` must match a UUID pattern, else `INVALID_ARGUMENT` ("Invalid bu_id format", HTTP 400).
2. Load the live (`deleted_at: null`) `tb_business_unit` with its `db_schema` and database pool (host, port, database, credentials, `is_active`). Not found: `NOT_FOUND` (404).
3. `tenantService.resolveConnectionForBusinessUnit` builds the connection URL. Failure (no pool, no schema, unsupported provider) becomes `VALIDATION_FAILURE` (422, "no database connection configured").
4. A short-lived Prisma client with the `pg` adapter is created for that URL and its `schema`, and **disconnected in a `finally`** when the operation ends.

## 3. Status check

`GET /api-system/tenant/seeds/:bu_id/status` (`tenant_seed.read`). For each seed set, in registry order, `listMissing(tenant)` returns the natural keys that are absent. Response:

```
{ bu_id, bu_code,
  sets: [ { key, label, defined, present, missing: [keys...] } ... ],
  all_seeded: every set has missing = [] }
present = defined - missing.length
```

It is read-only and runs sets sequentially on one connection. The SPA stores the result on the row and derives Seeded or "N missing" from `sum(missing.length)`.

## 4. Seed stream

`POST /api-system/tenant/seeds/:bu_id/deploy/stream` (`tenant_seed.apply`), optional body `{ "keys": ["running-code", ...] }`. Omitting `keys` (or an empty array) selects every set; the SPA always sends the keys the operator ticked and only for sets that have something missing. The response is `application/x-ndjson` (headers `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`), one JSON object per line:

| `type` | Fields | Emitted when |
|---|---|---|
| `start` | `bu_id, bu_code, total` | After computing the work list: `total` = missing keys across the selected sets |
| `seeding` | `bu_id, bu_code, key` (set key), `row_type` (row key), `index`, `total` | After **each** row is created (so `index` counts completed rows) |
| `done` | `success, summary { bu_id, bu_code, created, skipped }` | End of a successful run; `skipped` = defined rows of the selected sets minus `created` |
| `error` | `message` | Failure after the stream already started |

Algorithm (`deployStream`):

```
conn = resolveConnection(bu_id)                 # failure -> observable error (pre-stream)
work = []
for set in selected sets (registry order):
    for key in set.listMissing(tenant): work.push(set, key)
emit start{total = work.length}
for i, (set, key) in work:
    if cancelled: return
    await set.createOne(tenant, key)            # one write per row
    emit seeding{key = set.key, row_type = key, index = i+1, total}
emit done{created = work.length, skipped = definedTotal - created}
```

Notes:

- The missing list is **recomputed at stream time**, not taken from the earlier status call, so a row created by someone else in between is simply not in the work list.
- Not transactional: each `createOne` is its own write. A failure at row 7 leaves rows 1-6 created. The next status check shows what remains.
- `createOne` for `email-templates` is a read-modify-write of one JSON row; for `notification-templates-legacy` each "key" is an action that rewrites workflow data or retires untouched legacy templates (guarded by `doc_version: 0` and `updated_by_id: null` so edited templates are left alone).

### 4.1 Error handling at the gateway

| Moment | Result |
|---|---|
| Error before the first event (connection, not found, bad id) | JSON body `{ message, status, success: false }` with status: 404 if the message matches "not found"; 422 for "no database connection configured" or "unsupported database provider"; 400 for "invalid bu_id format"; otherwise 500 |
| Error after streaming began | One more line `{ "type": "error", "message": ... }` and the response ends |
| Client disconnect | `res.on('close')` unsubscribes from the RPC stream. The code comment explains why `req.on('close')` must not be used: since Node 16 a request emits `close` once its body is read, which truncated streams. |

### 4.2 How the SPA consumes it

`deployStream` in `tenantSeedService.ts` uses `fetch` (not `EventSource`) so it can send the bearer token and `x-app-id`. It splits the body on newlines, parses each line, forwards `start`/`seeding` to the row's progress, throws on an `error` event, and resolves with the `done` summary; an empty stream ends with "Seed stream ended without a result". After a successful run the page toasts "Created N rows in CODE." (or "CODE was already fully seeded." when `created = 0`) and re-checks that BU.

## 5. Fleet seed

No server concept. `seedAll(selectedKeys)` builds a plan from the rows currently flagged Missing (`pickMissing` intersects each BU's missing sets with the chosen keys, skipping BUs with nothing left), then runs the single-BU stream **sequentially**. A failed BU is counted and the loop continues; the end toast is "Seeded N business units." or "Seeded N - M failed.". Unmount sets a cancelled flag that aborts live fetches and prevents starting the next BU.

## 6. Cancellation, honestly

Aborting in the browser stops the SPA listening. The gateway then unsubscribes, which sets the `cancelled` flag in micro-business and is checked **between rows**. Whether the unsubscribe propagates over the RPC transport to that flag is not verified in source (the SPA service says so in its own comment). Treat a cancelled run as possibly finished; re-check status before re-running.

## 7. References

- Gateway: `apps/backend-gateway/src/backstage/tenant-seeds/{tenant-seeds.controller.ts,tenant-seeds.service.ts}`, `src/auth/guards/tenant-migration.guard.ts`.
- Micro-business: `apps/micro-business/src/authen/tenant_seed/{tenant_seed.service.ts,progress-event.ts}`, `seed-sets/*.seed-set.ts`.
- SPA: `src/services/tenantSeedService.ts`, `src/pages/TenantSeedManagement.tsx`.
- Siblings: [Tenant Seed](/en/backstage/tenant-seed), [UI Screens](/en/backstage/tenant-seed/ui-screens); related: [Tenant Migrations](/en/backstage/tenant-migrations).
