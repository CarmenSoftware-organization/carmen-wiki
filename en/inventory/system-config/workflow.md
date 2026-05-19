---
title: Workflow
description: Named multi-stage approval workflows attached to transactional documents — defines stages, actions, recipients, SLA, and field visibility per stage.
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, workflow, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Workflow

> **At a Glance**
> **Owner:** Sysadmin / Workflow Administrator &nbsp;·&nbsp; **Table:** `tb_workflow` &nbsp;·&nbsp; **Used by:** PR / SR / PO (approval-bearing modules) &nbsp;·&nbsp; Stage-chain definitions — actions, recipients, SLA, hidden fields, assignees.

![Workflow screen](/screenshots/system-config/workflow.png)

## 1. What & Who

A workflow record is the *document-routing definition* used by every approval-bearing module. Header columns are minimal — name, type, active flag — but the heavy lifting is in `data` JSONB: an ordered list of **stages**, the **available actions** per stage (`submit`, `approve`, `reject`, `sendback`), the **recipients** notified on each action, the **fields hidden** at that stage, and the **users assigned** to act.

Workflows are *typed*: an SR workflow cannot attach to a PR. Typing is via `enum_workflow_type` and enforced when a document selects a workflow. Multiple workflows of the same type can coexist — properties typically operate a "Standard PR" and a "High-Value PR" with different chains.

**Maintained by** Sysadmin (or delegated Workflow Admin). **Read by** the workflow runtime engine on every stage transition.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a new workflow | System Config → Workflow → New | Pick `workflow_type`; build stages |
| Edit a stage | Workflow detail → stage editor | Drag-reorder; per stage set SLA, actions, recipients, hidden fields |
| Assign users to a stage | Stage → assigned_users grid | User IDs or role descriptors |
| Mark a stage as HoD gate | Toggle `is_hod = true` | Routes to document's department HoD; ignores `assigned_users` |
| Clone for a new variant | Use UI clone action | Standard migration path for breaking changes |
| Retire an old version | Set `is_active = false` | New documents pick from `is_active = true` only |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Workflow name exists" | `(name, workflow_type)` duplicate | Pick different name |
| Mismatched type assignment | Document type ≠ `workflow_type` | Pick a workflow of the correct type |
| Validation: missing submit stage | First stage lacks `submit: is_active=true` | Add submit action to first stage |
| Cannot delete workflow | Referenced by non-completed documents | Clone + inactivate the old version |
| Approver sees masked prices | `hide_fields.price_per_unit = true` at active stage | Expected — adjust stage if unintended |
| HoD route fails | No HoD configured for document's department | Configure HoD on [master-data/department](/en/inventory/master-data/department) |

## 4. Edge Cases

- **Versioning.** Editing a live workflow does NOT retroactively change in-flight documents — runtime reads stage list as it was at attach-time. Breaking changes: clone under a new name.
- **Assigned users vs roles.** `assigned_users` accepts either user IDs or role descriptors (resolved via [access-control/application-role](/en/inventory/access-control/application-role)). Empty list at non-HOD approve stage = anyone with the workflow-stage role.
- **HoD resolution.** When `is_hod: true`, runtime looks up department HoD and routes there — `assigned_users` ignored.
- **Hidden fields** mask UI cells but values still flow through API.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_workflow`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`). |
| `name` | `String @db.VarChar` | No | Display name. |
| `workflow_type` | `enum_workflow_type` | No | `purchase_request_workflow`, `store_requisition_workflow`, `purchase_order_workflow`. |
| `data` | `Json? @db.JsonB` | Yes | Full stage definition. Default `{}`. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `description` / `note` | `String? @db.VarChar` | Yes | Free text. |
| `info` / `dimension` | `Json? @db.JsonB` | Yes | Metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, workflow_type, deleted_at])`. Indexes on `[name, workflow_type]` and `[name]`. Reverse relations to `tb_purchase_request`, `tb_purchase_request_template`, `tb_store_requisition`, `tb_workflow_comment`.

### 5.2 `data` JSONB shape

```
{
  "document_reference_pattern": "",
  "stages": [
    {
      "name": "Request Creation",
      "sla": "24",
      "sla_unit": "hours",
      "available_actions": {
        "submit":   { "is_active": true,  "recipients": { ... } },
        "approve":  { "is_active": false, "recipients": { ... } },
        "reject":   { "is_active": false, "recipients": { ... } },
        "sendback": { "is_active": false, "recipients": { ... } }
      },
      "hide_fields": { "price_per_unit": false, "total_price": false },
      "is_hod": false,
      "assigned_users": []
    }
  ]
}
```

Per-stage keys: `name`, `description`; `sla` + `sla_unit` (`hours`/`days`); `available_actions` (`is_active` + `recipients` per verb); `hide_fields` (mask financials); `is_hod` (HoD gate); `assigned_users` (user IDs or role descriptors).

## 6. Business Rules

- **Uniqueness.** `(name, workflow_type)` unique among non-deleted.
- **Type binding.** Document type X attaches workflows where `workflow_type = X` only; runtime rejects mismatch.
- **At-least-one submit stage.** First stage must enable `submit`; subsequent must enable at least one of `approve` / `reject` / `sendback`.
- **Deletion guards.** Workflow referenced by non-completed documents cannot be deleted; clone + inactivate is the migration path.
- **Versioning.** Live edits do NOT retroactively change in-flight documents.
- **HoD resolution.** Looks up document department's HoD; ignores `assigned_users`.
- **Hidden fields.** Mask UI cells; API values still flow.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) — primary consumer (`purchase_request_workflow`).
- [store-requisition](/en/inventory/store-requisition) — canonical multi-stage user (`store_requisition_workflow`).
- [purchase-order](/en/inventory/purchase-order) — high-value approval (`purchase_order_workflow`).
- [good-receive-note](/en/inventory/good-receive-note), [inventory-adjustment](/en/inventory/inventory-adjustment), [vendor-pricelist](/en/inventory/vendor-pricelist), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check) — optional workflow gating.
- [access-control/application-role](/en/inventory/access-control/application-role) — role descriptors in `assigned_users`.
- [master-data/department](/en/inventory/master-data/department) — HoD resolution.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_workflow` (lines ~3398-3425), `enum_workflow_type` (lines ~265-269).
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_workflow.json`.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role-type semantics.
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/workflow/`.
