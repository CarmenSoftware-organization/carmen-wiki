---
title: Document Version (Optimistic Concurrency)
description: The doc_version integer that guards every tenant table against lost updates — clients echo the version on save; a stale value is a 409 DOC_VERSION_CONFLICT, a missing one COMMON_DOC_VERSION_REQUIRED. Enforced by a Prisma client extension.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: system-config, concurrency, doc-version, optimistic-lock, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# Document Version (Optimistic Concurrency)

> **At a Glance**
> **Field:** `doc_version` (integer) on each document's update payload &nbsp;·&nbsp; **Guards against:** lost updates from concurrent edits &nbsp;·&nbsp; **On mismatch:** **409** with code `DOC_VERSION_CONFLICT`; **on omission:** `COMMON_DOC_VERSION_REQUIRED` &nbsp;·&nbsp; **Applies to:** every tenant model except `tb_gl_balance` and `tb_gl_jv_template_run` (157 of 159 at HEAD — verified 2026-09-22) &nbsp;·&nbsp; **Not** the attachment re-render counter (see §5).

## Implementation status (re-verified 2026-09-22)

The mechanism is centralised in the tenant Prisma client, not hand-written per service. `packages/prisma-shared-schema-tenant/src/client.ts` (`$extends` on `update`, ~`:440-490`):

- If the caller puts `doc_version` in the `where` clause, the extension treats it as a version guard; on success it **auto-increments** `doc_version` (`{ increment: 1 }`) unless the caller set `data.doc_version` explicitly.
- When Prisma answers `P2025` ("record to update not found") under a version guard, the extension re-reads the row by id: if it still exists the update lost a race and an `OptimisticLockError` (`code = 'DOC_VERSION_CONFLICT'`) is thrown; if it is really gone the original not-found error propagates.
- `@TryCatch` (`apps/micro-business/src/common/decorators/try-catch.decorator.ts:7-12,67`) recognises `DOC_VERSION_CONFLICT` and maps it to **409**.
- Services therefore write `where: { id, doc_version: data.doc_version }` and reject a missing version up front with `ERROR_CATALOG.COMMON_DOC_VERSION_REQUIRED` (e.g. `notification-template.service.ts:129-150`, `running-code.service.ts:301`, `inventory-period.service.ts:243`).

Coverage has widened since this page was written: 157 of the 159 tenant models declare `doc_version Int @default(0)` (only `tb_gl_balance` and `tb_gl_jv_template_run` do not), including tables the §3 list never mentioned — `tb_inventory_period*`, `tb_workflow`, `tb_notification_template`, `tb_application_config`, `tb_location_user`, `tb_department_user`. The platform schema uses the same column on `tb_user`, `tb_application_role`, `tb_permission`, `tb_user_invitation`, etc. Frontend forms echo the loaded value (`doc_version` on every `PATCH`/`PUT` payload in `types/*.ts`).

## 1. What & Who

`doc_version` is an **optimistic-concurrency** guard: a monotonically increasing integer carried on the aggregate root of a document. Every read returns the current `doc_version`; every **update must echo the version the client started from**. The server only applies the write if the supplied version still matches the stored one — then it increments the version. If two users open the same document and both save, the second save fails instead of silently overwriting the first.

It is *optimistic*: no row is locked while a user is editing. Conflicts are detected at save time rather than prevented up front, which suits human-paced document editing where conflicts are rare but costly.

**Set by** every service's update path (rolled out across the backend on 2026-06-04). **Checked by** the same update handlers. **Surfaced to** clients as a `409 Conflict` they must recover from.

## 2. Behaviour

```
function update(id, payload):
    current = load(id)                       # current.doc_version = N
    if payload.doc_version != current.doc_version:
        raise Conflict(409)                  # someone saved first
    apply(payload)
    current.doc_version = N + 1              # bump on success
    save(current)
    return current                           # client reads back N+1
```

The client must send the `doc_version` it received on its last read. After a successful save it must use the returned, incremented value for any further edit.

## 3. Entities that carry it

| Group | Entities |
|---|---|
| Procurement | purchase-request, purchase-order, purchase-request-template, request-for-pricing, credit-note |
| Receiving & stock | good-received-note, stock-in, stock-out |
| Counting | spot-check |
| Requisition | store-requisition |
| Pricing | pricelist, pricelist-template |
| Config masters | credit-term, extra-cost-type, running-code, vendor-business-type, recipe-category, recipe-cuisine, recipe-equipment, recipe-equipment-category |
| System config (added since) | inventory-period, workflow, notification-template, application-config, application-user-config, business-unit (Company Profile / Default Setting `PATCH`) |
| Access control (added since) | location-user, department-user, application-role, user-application-role (platform) |

The table above is illustrative; the authoritative rule is "every tenant model except the two GL tables named in the status block".

## 4. Test scenarios

| # | Setup | Action | Expected |
|---|---|---|---|
| 1 | Two clients A and B both load document at `doc_version = 5` | A saves a change | A succeeds; document is now `doc_version = 6` |
| 2 | Continuing #1 | B saves its change, still sending `doc_version = 5` | **409 Conflict**; B's write is rejected, no data lost |
| 3 | Continuing #2 | B re-fetches (gets `doc_version = 6`), re-applies its edit, saves with `6` | B succeeds; document is now `doc_version = 7` |
| 4 | Single client | Update without any `doc_version` | Rejected with `COMMON_DOC_VERSION_REQUIRED` before any write |
| 5 | Client A holds `doc_version = 5`; another user deletes the row | A saves | Not-found error, **not** 409 — the extension re-reads by id and only raises `DOC_VERSION_CONFLICT` when the row still exists |

## 5. Not to be confused with

`tb_attachment.doc_version` (tenant schema) carries the same `Int @default(0)` shape as every other `doc_version` column, but **it is not an active re-render counter** — a repo-wide search found zero code that increments, reads, or otherwise touches it. In fact `tb_attachment` itself has zero non-schema references anywhere: it is a dead table. The real file-metadata registry is `tb_file_tag`, in a separate file-service database, which has no `doc_version` column at all. See [system-config/document](/en/inventory/system-config/document) §5 for the corrected data model. Treat `tb_attachment.doc_version` as inert schema, not a working concurrency guard *or* a working re-render counter.

Also unrelated: `micro-cronjobs` added its own `docVersion` column + audit user to the platform cron-job registry (`5aa1cc6`, 2026-09-02) for the Platform SPA's cron screen — same idea, different database, not covered by the tenant client extension.

## 6. References

- **Client extension:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/src/client.ts` — `update` extension, `OptimisticLockError` (`code = 'DOC_VERSION_CONFLICT'`).
- **HTTP mapping:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/decorators/try-catch.decorator.ts` (`isOptimisticLockError` → 409).
- **Error catalog:** `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts` — `COMMON_DOC_VERSION_REQUIRED` (`:18`).
- **Schema:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `doc_version Int @default(0) @db.Integer` on 157 of 159 models.
