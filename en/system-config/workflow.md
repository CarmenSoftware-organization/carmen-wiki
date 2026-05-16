---
title: Workflow
description: Named multi-stage approval workflows attached to transactional documents — defines stages, actions, recipients, SLA, and field visibility per stage.
published: true
date: 2026-05-16T08:00:00.000Z
tags: system-config, workflow, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Workflow

## 1. Purpose

A workflow record is the *document-routing definition* used by every approval-bearing transactional module. The header columns are minimal — name, type, active flag — but the heavy lifting lives in the `data` JSONB column, which holds an ordered list of **stages**, the **available actions** per stage (`submit`, `approve`, `reject`, `sendback`), the **recipients** notified on each action, the **fields hidden** at that stage, and the **users assigned** to act on the stage.

Workflows are *typed*: a Store Requisition workflow cannot be attached to a Purchase Request, and vice-versa. The typing comes from `enum_workflow_type` and is enforced when a document selects a workflow. Multiple workflows of the same type can coexist — properties typically operate a "Standard PR" and a "High-Value PR" workflow with different stage chains and approver assignments. The relevant document picks its workflow at create-time and stores the FK, which is then read by the runtime engine to drive stage transitions, permissions, and notifications.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_workflow`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`). |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Standard PR`, `High-Value PR`, `Store Requisition`). |
| `workflow_type` | `enum_workflow_type` | No | One of `purchase_request_workflow`, `store_requisition_workflow`, `purchase_order_workflow`. |
| `data` | `Json? @db.JsonB` | Yes | Full stage definition. Default `{}`. Schema described below. |
| `is_active` | `Boolean?` | Yes | Active flag (default `true`). |
| `description` | `String? @db.VarChar` | Yes | Free-text description. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `info` | `Json? @db.JsonB` | Yes | Free-form metadata (default `{}`). |
| `dimension` | `Json? @db.JsonB` | Yes | Dimension tag array (default `[]`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, workflow_type, deleted_at])` map `workflow_name_workflow_type_deletedat_u`. Indexes on `[name, workflow_type]` and `[name]`. Reverse relations to `tb_purchase_request`, `tb_purchase_request_template`, `tb_store_requisition`, plus `tb_workflow_comment` for audit chatter.

**`enum_workflow_type`:** `purchase_request_workflow`, `store_requisition_workflow`, `purchase_order_workflow`.

### 2.2 `data` JSONB shape

The runtime contract observed in seed data and consumed by the application is:

```jsonc
{
  "document_reference_pattern": "",
  "stages": [
    {
      "name": "Request Creation",
      "description": "",
      "sla": "24",
      "sla_unit": "hours",
      "available_actions": {
        "submit":   { "is_active": true,  "recipients": { "requestor": true, "current_approve": false, "next_step": false } },
        "approve":  { "is_active": false, "recipients": { "requestor": true, "current_approve": true,  "next_step": true  } },
        "reject":   { "is_active": false, "recipients": { "requestor": true, "current_approve": false, "next_step": true  } },
        "sendback": { "is_active": false, "recipients": { "requestor": true, "current_approve": false, "next_step": true  } }
      },
      "hide_fields": {
        "price_per_unit": false,
        "total_price":    false
      },
      "is_hod": false,
      "assigned_users": []
    }
  ]
}
```

Per-stage keys:

- `name`, `description` — display strings.
- `sla` + `sla_unit` (`hours` / `days`) — service-level target, surfaced to approvers and used by escalation reports.
- `available_actions` — keyed by action (`submit`, `approve`, `reject`, `sendback`). Each entry has an `is_active` flag (whether the action is enabled at this stage) and a `recipients` map (which audiences are notified when the action fires).
- `hide_fields` — boolean map controlling which financial / sensitive fields are masked at this stage. Wired up to the workflow-permissions UI layer.
- `is_hod` — marks the stage as a Head-of-Department gate (resolved against the document's department at runtime).
- `assigned_users` — list of user IDs (or role descriptors) authorised to act at this stage.

## 3. Usage / Cross-References

- [[purchase-request]] — PR header has `workflow_id` and a workflow-stage runtime state; submit / approve / reject / sendback move the document along the stage chain.
- [[purchase-order]] — POs may carry an approval workflow when policy requires; `workflow_type = purchase_order_workflow`.
- [[store-requisition]] — SR is the canonical multi-stage workflow user; `workflow_type = store_requisition_workflow`.
- [[good-receive-note]] — receiving may participate in a workflow for high-value GRNs; field visibility (price, totals) leans on the same `hide_fields` mechanism.
- [[inventory-adjustment]] — sensitive stock-in/out adjustments can be routed through approval workflows.
- [[vendor-pricelist]] — pricelist publication can be workflow-gated.
- [[physical-count]] — count freeze/unfreeze operations participate where policy requires approval.
- [[spot-check]] — same approval surface as physical-count for variance sign-off.

## 4. Configuration UI

Managed by **Sysadmin** (or a delegated Workflow Administrator) under System Configuration → Workflow. The screen lists workflows grouped by `workflow_type`, with a multi-step stage editor for the `data` blob: per stage the admin sets name, SLA, available actions, recipient checkboxes, hidden fields, and the user assignment grid. Stage order is drag-to-reorder. A preview pane renders the resulting permission matrix using the same rules consumed by the runtime ([[access-control/permission]] integrates with workflow-stage roles).

## 5. Business Rules

- **Uniqueness.** `(name, workflow_type)` is unique among non-deleted rows.
- **Type binding.** A document of type X can only attach a workflow whose `workflow_type` matches X. The runtime rejects mismatched assignments.
- **At-least-one submit stage.** The first stage in `data.stages` must enable `submit`; subsequent stages must enable at least one of `approve` / `reject` / `sendback`. Validation runs on save.
- **Deletion guards.** A workflow referenced by any non-completed document cannot be deleted; cloning and inactivating the old version is the supported migration path.
- **Versioning.** Editing a live workflow does not retroactively change documents already in-flight — the runtime reads the stage list as it was at attach-time (in practice via document-side cached state and `tb_workflow_comment` audit). For breaking changes the recommended approach is to clone the workflow under a new name.
- **Assigned users vs roles.** `assigned_users` accepts either explicit user IDs or role descriptors (resolved via [[access-control/application-role]]). Empty list at a non-`is_hod` approve stage means *anyone with the workflow-stage role* may act.
- **HOD resolution.** When `is_hod: true`, the runtime looks up the Head of Department for the document's [[master-data/department]] and routes there, ignoring `assigned_users`.
- **Hidden fields.** `hide_fields.price_per_unit` and `hide_fields.total_price` mask financial cells for the active stage's role. Hidden values still flow through the API but the UI suppresses them.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_workflow` (lines ~3398-3425), `enum_workflow_type` (lines ~265-269), `tb_workflow_comment` (lines ~3427+).
- **Seed example:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_workflow.json`.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role-type semantics (`requester`, `purchaser`, `approver`, `reviewer`) consumed by `hide_fields` and the permission matrix.
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/workflow/`.
- **Cross-module:** see Section 3.
