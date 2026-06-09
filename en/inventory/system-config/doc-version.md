---
title: Document Version (Optimistic Concurrency)
description: The doc_version integer that guards transactional documents against lost updates — clients must echo the current version on save or get a 409 Conflict.
published: true
date: 2026-06-09T00:00:00.000Z
tags: system-config, concurrency, doc-version, optimistic-lock, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# Document Version (Optimistic Concurrency)

> **At a Glance**
> **Field:** `doc_version` (integer) on each document's update payload &nbsp;·&nbsp; **Guards against:** lost updates from concurrent edits &nbsp;·&nbsp; **On mismatch:** **409 Conflict** &nbsp;·&nbsp; **Applies to:** ~20 transactional & config entities (see §3) &nbsp;·&nbsp; **Not** the attachment re-render counter (see §5).

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

## 4. Test scenarios

| # | Setup | Action | Expected |
|---|---|---|---|
| 1 | Two clients A and B both load document at `doc_version = 5` | A saves a change | A succeeds; document is now `doc_version = 6` |
| 2 | Continuing #1 | B saves its change, still sending `doc_version = 5` | **409 Conflict**; B's write is rejected, no data lost |
| 3 | Continuing #2 | B re-fetches (gets `doc_version = 6`), re-applies its edit, saves with `6` | B succeeds; document is now `doc_version = 7` |
| 4 | Single client | Update without any `doc_version`, or with a stale one | Rejected — the field is required for the compare-and-set |

## 5. Not to be confused with

`tb_attachment.doc_version` is a **different field with a different meaning** — it is a *re-render counter* for regenerated documents (e.g. a re-printed PDF), incremented each time the owning module re-renders the file, and it retains older versions for audit. It is **not** a concurrency guard. See [reporting-audit/attachment](/en/inventory/reporting-audit/attachment).
