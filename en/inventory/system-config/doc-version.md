---
title: Document Version (Optimistic Concurrency)
description: The doc_version integer that guards every tenant table against lost updates — clients echo the version on save; a stale value is a 409 DOC_VERSION_CONFLICT, a missing one COMMON_DOC_VERSION_REQUIRED. Enforced by a Prisma client extension.
published: true
date: '2026-10-27T00:00:00.000Z'
tags: system-config, concurrency, doc-version, optimistic-lock, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# Document Version (Optimistic Concurrency)

> **At a Glance**
> **Field:** `doc_version` (integer) on each document's update payload &nbsp;·&nbsp; **Guards against:** lost updates from concurrent edits &nbsp;·&nbsp; **On mismatch:** HTTP **409** (internal error `code = 'DOC_VERSION_CONFLICT'`); **on omission:** `COMMON_DOC_VERSION_REQUIRED` (HTTP 400) from services that check it &nbsp;·&nbsp; **Applies to:** 181 of the 195 tenant models declare the column (counted 2026-10-27 over `schema.prisma`); the 14 without it are `tb_gl_balance`, `tb_gl_jv_template_run`, `tb_dashboard_bu_widget_deploy` and the new AP/AR child tables (`tb_ap_invoice_detail_source`, `tb_ap_invoice_detail_dimension`, `tb_ap_invoice_reference`, `tb_ap_payment_detail`, `tb_ap_payment_expense`, `tb_ap_payment_wht`, `tb_ar_invoice_detail_dimension`, `tb_ar_invoice_reference`, `tb_ar_receipt_detail`, `tb_ar_receipt_wht`, `tb_gl_jv_detail_dimension`) &nbsp;·&nbsp; **Not** the attachment re-render counter (see §5).

## Implementation status (re-verified 2026-10-27)

The mechanism is centralised in the tenant Prisma client, not hand-written per service. `packages/prisma-shared-schema-tenant/src/client.ts` (`$extends` on `update`, `:519-553`):

- **The guard is opt-in at the client layer.** It engages only when `where.doc_version` is a number (`typeof expectedVersion !== 'number'` → plain pass-through, `:523-526`). Rejecting a *missing* version is therefore each service's job, not the extension's — an update path that forgets the check silently skips locking. If the caller puts `doc_version` in the `where` clause, the extension treats it as a version guard; on success it **auto-increments** `doc_version` (`{ increment: 1 }`) unless the caller set `data.doc_version` explicitly.
- When Prisma answers `P2025` ("record to update not found") under a version guard, the extension re-reads the row by id: if it still exists the update lost a race and an `OptimisticLockError` (`code = 'DOC_VERSION_CONFLICT'`) is thrown; if it is really gone the original not-found error propagates.
- `@TryCatch` (`apps/micro-business/src/common/decorators/try-catch.decorator.ts`: `isOptimisticLockError` `:23-29`, mapping `:88-91`) recognises `DOC_VERSION_CONFLICT` and returns `Result.error(err.message, ErrorCode.ALREADY_EXISTS)` — i.e. **409**, with the message `Record was modified by another request (model=<name>, expected doc_version=<n>).` and **no** catalog `app_code`. Clients should key on the 409 status, not on a `DOC_VERSION_CONFLICT` string in the body.
- Services therefore write `where: { id, doc_version: data.doc_version }` and reject a missing version up front with `ERROR_CATALOG.COMMON_DOC_VERSION_REQUIRED` (HTTP 400, `catalog.ts:18-24`) where they check explicitly — e.g. `notification-template.service.ts:129-130`, `inventory-period.service.ts:405`. `running-code.service.ts:337-342` uses the guard (`where: { id, doc_version }`) without an explicit required-check, so the omission path there is the plain pass-through described above.

Coverage has widened since this page was written: 181 of 195 tenant models declare `doc_version Int @default(0)` (the accounting module added many models; its detail/child tables mostly do not carry one — see At a Glance), including tables the §3 list never mentioned — `tb_inventory_period*`, `tb_workflow`, `tb_notification_template`, `tb_application_config`, `tb_location_user`, `tb_department_user`. The backstage schema uses the same column on `tb_user`, `tb_application_role`, `tb_permission`, `tb_user_invitation`, etc. Frontend forms echo the loaded value (`doc_version` on every `PATCH`/`PUT` payload in `types/*.ts`). For workflow documents (PR / PO / CN / GRN / SR) the FE rule, enforced by a source-reading test (`routes/doc-version-freshness.test.ts`), is that **every mutation fetches a fresh `doc_version` from the server immediately before firing** rather than trusting the form or page-load prop — a 2026-09-09 bug had `/save` and the irreversible GRN commit sending a stale value.

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
| Access control (added since) | location-user, department-user, application-role, user-application-role (backstage) |

The table above is illustrative; the authoritative rule is the schema itself — `doc_version Int @default(0)` is present on 181 of 195 tenant models, and absent on the 14 listed in At a Glance.

## 4. Test scenarios

| # | Setup | Action | Expected |
|---|---|---|---|
| 1 | Two clients A and B both load document at `doc_version = 5` | A saves a change | A succeeds; document is now `doc_version = 6` |
| 2 | Continuing #1 | B saves its change, still sending `doc_version = 5` | **409 Conflict**; B's write is rejected, no data lost |
| 3 | Continuing #2 | B re-fetches (gets `doc_version = 6`), re-applies its edit, saves with `6` | B succeeds; document is now `doc_version = 7` |
| 4 | Single client | Update without any `doc_version` | Rejected with `COMMON_DOC_VERSION_REQUIRED` before any write |
| 5 | Client A holds `doc_version = 5`; another user deletes the row | A saves | Not-found error, **not** 409 — the extension re-reads by id and only raises `DOC_VERSION_CONFLICT` when the row still exists |

### 4.1 Related 409 that is not a version conflict

`PUT`/`PATCH api/business-units` (Company Profile / Default Setting) also answer **409 `BUSINESS_UNIT_NOT_CURRENT`** (BE `291f81c54`, 2026-10-26; catalog id 8030005) when the page sends the `id` of the BU it loaded and that BU is no longer the caller's current one (switched in another tab/device). The check runs before any read or write; omitting `id` keeps the old behaviour. QA: a stale `doc_version` and a switched BU are two different 409s on the same screen.

## 5. Not to be confused with

`tb_attachment.doc_version` (tenant schema) carries the same `Int @default(0)` shape as every other `doc_version` column, but **it is not an active re-render counter** — a repo-wide search found zero code that increments, reads, or otherwise touches it. In fact `tb_attachment` itself has zero non-schema references anywhere: it is a dead table. The real file-metadata registry is `tb_file_tag`, in a separate file-service database, which has no `doc_version` column at all. See [system-config/document](/en/inventory/system-config/document) §5 for the corrected data model. Treat `tb_attachment.doc_version` as inert schema, not a working concurrency guard *or* a working re-render counter.

Also unrelated: `micro-cronjobs` added its own `docVersion` column + audit user to the backstage cron-job registry (`5aa1cc6`, 2026-09-02) for the Backstage SPA's cron screen — same idea, different database, not covered by the tenant client extension.

## 6. References

- **Client extension:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/src/client.ts` — `update` extension, `OptimisticLockError` (`code = 'DOC_VERSION_CONFLICT'`).
- **HTTP mapping:** `../carmen-turborepo-backend/apps/micro-business/src/common/decorators/try-catch.decorator.ts` (`isOptimisticLockError` `:23-29` → `ErrorCode.ALREADY_EXISTS` → 409, `:88-91`).
- **Error catalog:** `../carmen-turborepo-backend/packages/error-catalog/src/catalog.ts` — `COMMON_DOC_VERSION_REQUIRED` (`:18-24`, `http_status: 400`).
- **Schema:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `doc_version Int @default(0) @db.Integer` on 181 of 195 models (counted 2026-10-27).
