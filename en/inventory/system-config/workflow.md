---
title: Workflow
description: Multi-stage approval workflows for PR / PO / SR: stages, actions, recipients, SLA, field visibility, routing rules, product scope; stage rail detail page; type fixed at creation; in-flight docs lock stages.
published: true
date: '2026-10-27T00:00:00.000Z'
tags: system-config, workflow, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Workflow

> **At a Glance**
> **Owner:** Sysadmin / Workflow Administrator &nbsp;·&nbsp; **Table:** `tb_workflow` &nbsp;·&nbsp; **Routes:** `/system-admin/workflow/purchase-request`, `/purchase-order`, `/store-requisition` (+ `/workflow/new`, `/workflow/:id`); `/system-admin/workflow` redirects to the PR page — **no combined list since 2026-09-16** &nbsp;·&nbsp; **Endpoints:** `GET api/config/:bu_code/workflows/{purchase-request|purchase-order|store-requisition}` per type, plus `edit-availability`, `assignees/:user_id` (+ `/handover`), `:id/products/:product_id/locations` &nbsp;·&nbsp; **Permission / licence:** `system_admin.workflow` + per-type `system_admin.workflow.{purchase_request,purchase_order,store_requisition}` &nbsp;·&nbsp; **Used by:** PR / SR / PO (approval-bearing modules); `gl_jv` exists in the enum for the GL module but has no page here &nbsp;·&nbsp; Stage-chain definitions — actions, recipients, SLA, hidden fields, assignees, stage roles, routing rules, product scope.

![Workflow screen](/screenshots/system-config/workflow.png)

![Workflow detail screen](/screenshots/system-config/workflow-detail.png)

## Implementation status (re-verified 2026-10-27)

- **Detail page is built around a stage rail, not a diagram** (FE `0b0fbf6b`, `f89c0427`). The ReactFlow diagram (`wf-diagram.tsx`) and the validation panel (`wf-validation-panel.tsx`) are deleted. `/system-admin/workflow/:id` (`wf-detail.tsx`) is a two-column layout: a sticky **stage rail** on the left (`wf-stage-list.tsx`, drag-to-reorder with `@dnd-kit`, **Add stage**, delete, approver count, total cycle time from the SLAs, and the validation issues listed under the stage they belong to) and the detail on the right. The right side has three workflow-level tabs — **Overview** (identity fields while editing plus the insights block), **Routing**, **Products** — and clicking a stage in the rail swaps the right side to that stage's own tabs (**General**, **Notifications**, **Assigned Users**; `wf-stage-detail.tsx`). The old standalone **Stages** tab no longer exists. Stage detail also has a read-only "view" presentation in all three tabs when not editing (FE `e4cdaa93`). The header has **Duplicate**, which opens the new copy straight away (FE `935b2fce`, `wf-header.tsx:151-156`).
- **Overview / Insights tab** (`wf-insights.tsx`, FE `1b589ed0`): a pre-save check list (validation errors / warnings, routing-rule problems, "no products selected" warning), a document path proportioned by each stage's SLA, quick stats (cycle time, approver stages, HoD stages, total users, routing rules, products, inherit-signature for PO), and a stage × action matrix showing which buttons are active, how many recipients each has, who is HoD, and which price fields are hidden.
- **Workflow type is fixed once created** (BE `49c5f0872`): `WorkflowUpdateSchema` no longer has `workflow_type`; the micro-service drops it if a client still sends it, because every stage `role` is validated against the type. The FE shows the type as locked beside the title on both the create and detail pages (`wf-new-form.tsx`, FE `a8a32ae7`). Roles offered per stage are restricted by type (`wf-role-colors.ts`: PR `create/approve/purchase`, PO `create/approve`, SR `create/approve/issue`) and the validator reports `role_not_allowed` if a stage holds a role outside that set.
- **Skeleton-lock comparison ignores JSON key order** (BE `7b01e2cc5`): Postgres returns JSONB keys reordered, so a workflow with routing rules could not be saved while any document was in progress; `workflow-edit-scope.helper.ts` now compares routing rules with key-sorted JSON (`toCanonicalJson`). Array order is still significant (rule order = priority).
- **The lock is explained on every tab** (FE `d590dbc7`): `WfStructureLockNotice` shows the number of in-progress documents with a link to the document list pre-filtered to that workflow's `in_progress` documents (`getInProgressDocumentsHref`: PR `/procurement/purchase-request`, PO `/procurement/purchase-order`, SR `/store-operation/store-requisition`), and the rail, Routing tab and structure fields are disabled with a lock icon.
- **Seeded notification templates are pre-selected** (FE `18405175`, `d40bf6c5`): when a stage is created the empty notification slots are filled with the system templates whose `code` is `wf.<action>.<slot>` (`wf-seeded-templates.ts`, `use-seeded-template-ids.ts`; templates listed in [system-config/notification-template](/en/inventory/system-config/notification-template)). Only empty slots are filled and the switches are never touched. `wf.complete.requestor` is not selectable — the backend uses it by itself on final approval.
- **Recipient slots changed**: a fourth slot `previous_step` exists (`recipients.previous_step`, optional). The Reject action's "previous approver" row now writes `previous_step` (it used to write `current_approve`, which the dispatcher sends to the person who clicked); on load the FE migrates old values (`moveRejectPreviousApprover`) and **clears `current_approve` everywhere** (`clearCurrentApprover`), since the row is no longer shown and the backend never delivers that slot. On save `syncRecipientChannels` forces `is_notification` and `notification_channel.app.is_active` to equal the recipient switch — one switch per recipient (FE `d32a7958`; `wf-form-schema.ts`).
- **Routing tab reads as sentences** (FE `626ef5f3`): each rule is shown "when [stage] … if [field op value] … then go to [stage]" with the skipped stages named. The condition field is `total_amount` (operators `eq/gt/lt/gte/lte/between`, with `min_value`/`max_value` for `between`), `department` (picked from a paged checklist, so more than 30 departments can be chosen — FE `56362c10`) or `category`. The target can only be a stage **after** the trigger stage, and the `SKIP_STAGE` / `NEXT_STAGE` action type is derived from the target rather than chosen (`wf-routing-utils.ts`); `category` rules are flagged as inert because documents do not yet carry a document-level category (backend `evaluateCondition` comment, `workflows.navagation.service.ts`).
- **Products tab** (FE `b6e3818a`): shows selected / total and a coverage bar, with a toggle to list only the selected products. **Stage Notifications** is one row and one switch per recipient and warns when a recipient is on without a template; **Assigned Users** has whole-row checkboxes, a tri-state select-all and HoD as a switch.
- **Per-stage action switches are enforced** (`workflow-orchestrator.service.ts:560-604`, `checkStageActionAllowed`): when the document's current stage has role `approve`, `purchase` or `issue` and `available_actions.<verb>.is_active === false` for `approve`, `reject` or `sendback`, the action is refused with **422 `WORKFLOW_STAGE_ACTION_DISABLED`** (`Action "{action}" is turned off for stage {stage} in this workflow`, `error-catalog/src/catalog.ts:3219`). Stages with other roles (`create`, `view_only`) are not checked, and AP documents deliberately skip the check. PR / PO / SR detail responses carry the derived flags as `stage_actions: { approve, reject, sendback }` (booleans; gateway `purchase-request.serializer.ts`, `purchase-order.serializer.ts`, `store-requisition.serializer.ts`; BE `aeafc119d`), and the FE hides the matching buttons from it (`getStageActionFlags` in `pr-form.tsx` / `po-form.tsx` / `sr-form.tsx`). Price hiding is the stage's `hide_fields.price_per_unit` / `hide_fields.total_price` (stage General tab, "Visibility" section; §5.2).
- **Hidden price badge** (FE `a2734e55`, `88252a4a`): lists and My Approvals show a badge when the current stage hides prices; a PR hiding only the unit price still shows the total from the backend.
- **Backend enum grew**: `enum_workflow_type` now has seven members — `purchase_request`, `store_requisition`, `purchase_order`, `gl_jv`, `ap_invoice`, `ap_payment`, `ar_invoice` (`schema.prisma:271-279`); the three AP/AR types allow roles `create`/`approve` and are handled in `getEditAvailability` and the handover code (`workflow-stage-role.helper.ts:45-47`, `workflows.service.ts`). They belong to the accounting module and have no page in this FE (`WORKFLOW_TYPE` has only PR/PO/SR).
- **Client validator codes at HEAD** (`wf-validate.ts`): `empty_name`, `duplicate_name`, `no_users_assigned`, `no_actions_enabled`, `no_sla`, `missing_create_role`, `missing_completed_stage`, `role_not_allowed`. `submit_only_on_first` is still declared in the `IssueCode` type but nothing emits it.

### Earlier status (2026-09-22) — the per-type split, handover and skeleton lock below remain current

## 1. What & Who

A workflow record is the *document-routing definition* used by every approval-bearing module. Header columns are minimal — name, type, active flag — but the heavy lifting is in `data` JSONB: an ordered list of **stages**, the **available actions** per stage (`submit`, `approve`, `reject`, `sendback`), the **recipients** notified on each action, the **fields hidden** at that stage, and the **users assigned** to act.

Workflows are *typed*: an SR workflow cannot attach to a PR. Typing is via `enum_workflow_type` and enforced when a document selects a workflow. Multiple workflows of the same type can coexist — properties typically operate a "Standard PR" and a "High-Value PR" with different chains.

**Since 2026-09-16 the screen is split per document type.** The sidebar's Workflows group has three children — Purchase Request, Purchase Order, Store Requisition (FE `a5b49e68`, `293009f0`, `f3e13d30`) — each rendered by `workflow-doc-type.route.tsx`, which reads the type from the last URL segment and calls that type's own endpoint (`GET api/config/:bu_code/workflows/purchase-request` etc., BE `003e12fb8`, guards `AppIdGuard('workflow.findAllPurchaseRequest' | 'findAllPurchaseOrder' | 'findAllStoreRequisition')`, `config_workflows.controller.ts:192-301`). The generic `GET …/workflows` (`:542`) still exists (it was briefly removed and restored, `4263c78f8`) but the FE no longer renders a combined list; `/system-admin/workflow` is a `<Navigate>` to the PR page (`router.tsx:769-775`). The split lets an application or role be granted one document type without the others — the nav entries gate on `system_admin.workflow.purchase_request.view` etc. (`module-list.ts:809-850`; the group's fourth child is Notification Template, not a document type).

**Maintained by** Sysadmin (or delegated Workflow Admin). **Read by** the workflow runtime engine on every stage transition.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a new workflow | Workflows → *(document type)* → **New** (`/system-admin/workflow/new`, `wf-new-form.tsx`) | Pick `workflow_type`; build stages; the type page you came from is pre-selected |
| Edit a stage | `/system-admin/workflow/:id` → click the stage in the rail (`wf-stage-list.tsx`, `wf-stages.tsx`, `wf-stage-detail.tsx`) | Drag-reorder in the rail; per stage set SLA, stage `role`, `creator_access`, actions, recipients, hidden fields, signature |
| Assign users to a stage | Stage → **Assigned Users** (`wf-stage-users.tsx`) | User records (`user_id`, name, email, department); empty list at non-HOD approve stage = anyone with the stage role |
| Mark a stage as HoD gate | Toggle `is_hod = true` | Routes to document's department HoD; ignores `assigned_users` |
| Choose which stages print a signature | Stage → **Show signature** | At most **5** signature stages per workflow (`wf-signature-limit.ts` `MAX_SIGNATURES`); PO workflows can additionally `inherit_signature_from_pr` (FE `409fcc81`) |
| Add a routing rule | **Routing** tab (`wf-routing.tsx`) | `trigger_stage` + condition on `total_amount`, `department` or `category` (`eq`/`lt`/`gt`/`lte`/`gte`/`between`) → go to a `target_stage` later in the chain (`SKIP_STAGE` / `NEXT_STAGE` is derived) |
| Scope the workflow to products | **Products** tab (`wf-products.tsx`, table view since `53a4b0ee`, coverage bar since `b6e3818a`) | Stored as `data.products: string[]` (ids only, `ff2b55db`); used by the location picker (below) |
| Check whether a workflow can be edited | Opening `/system-admin/workflow/:id` calls `GET …/workflows/:id/edit-availability` (`use-wf-availability.ts`) | Returns `can_edit`, `can_edit_stages`, `can_delete`, `blocked_reason`, `documents{draft,in_progress,done,total}`; the header shows the counts (`613e649c`) and `wf-structure-lock-notice.tsx` explains a lock |
| Hand a leaver's stages to someone else | `GET …/workflows/assignees/:target_user_id` then `POST …/workflows/assignees/:target_user_id/handover` | Lists every stage the user is named in, whether they hold it alone, and the `in_progress` count per stage; handover replaces them in the listed stages **and re-stamps the documents already waiting there** in one call (BE `4fecf678f`, `00ffaaeba`); no FE screen for this yet — Bruno only |
| Find where a product can be used under a workflow | `GET …/workflows/:workflow_id/products/:product_id/locations` | Intersection of `data.products`, `tb_product_location`, and the caller's `tb_location_user` rows; 404 for an unknown workflow, `[]` for every other empty case (BE `383fc4ca4`, `ec3f10704`) |
| Clone for a new variant | Row action **Duplicate** (`wf-row-actions.tsx`) or the **Duplicate** button on the detail header (`wf-header.tsx:151`), which opens the copy | Standard migration path for breaking changes |
| Retire an old version | Set `is_active = false` (row toggle) | New documents pick from `is_active = true` only |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Workflow name exists" | `(name, workflow_type)` duplicate | Pick different name |
| Mismatched type assignment | Document type ≠ `workflow_type` | Pick a workflow of the correct type |
| Client validation issues (listed under the stage in the rail and in the Overview check list) | `wf-validate.ts` codes: `empty_name`, `duplicate_name`, `no_users_assigned`, `no_actions_enabled`, `no_sla`, `missing_create_role`, `missing_completed_stage`, `role_not_allowed` | Fix the flagged stage (`wf-validation-panel.tsx` was deleted; `submit_only_on_first` is declared but never emitted) |
| `WORKFLOW_STAGE_CHANGE_BLOCKED` on save | Stage list or routing rules changed while `documents.in_progress > 0` (`workflows.service.ts:1380-1387`; `workflow-edit-scope.helper.ts` diffs stages/routing) | Wait for in-flight documents to finish, or clone; name / description / `is_active` / notifications / products / assignees remain editable |
| `WORKFLOW_HAS_IN_PROGRESS_DOCUMENTS` on delete | Any document `in_progress` on this workflow (`delete()` `:1554-1571`) | Inactivate instead |
| Cannot delete workflow | Referenced by non-completed documents | Clone + inactivate the old version |
| Approver sees masked prices | `hide_fields.price_per_unit = true` at active stage | Expected — adjust stage if unintended |
| HoD route fails | No HoD configured for document's department | Configure HoD on [master-data/department](/en/inventory/master-data/department) |

## 4. Edge Cases

- **Versioning.** Editing a live workflow does NOT retroactively change in-flight documents — runtime reads stage list as it was at attach-time. Breaking changes: clone under a new name.
- **In-flight documents lock the skeleton, not the form (2026-09-02, BE `b1bcb1e98`; FE `8cac942d`).** `getEditAvailability` returns `can_edit: true` always, `can_edit_stages: !(in_progress > 0)`, `blocked_reason: WORKFLOW_STAGE_CHANGE_BLOCKED` when locked (`workflows.service.ts:830-880`). The status columns differ per type — PR `pr_status`, PO `po_status`, SR `doc_status` — and only `draft` / `in_progress` are named; everything else counts as `done` (`countDocumentsByStatus` `:892`). A prior FE version (`c60430ea`, 2026-09-01) refused to enter edit mode at all; that was relaxed a day later.
- **Handover re-stamps waiting documents.** `POST …/assignees/:user_id/handover` applies all replacements in one call precisely so a half-applied handover cannot happen; it also rewrites `user_action` on documents already waiting at those stages (Bruno `POST-handover-assignee-config-workflows.bru`). Stages whose actors come from a department HOD or a whole department are not listed by the impact endpoint because losing one person does not empty them.
- **Assigned users vs stage role.** `assigned_users` holds full user records (`user_id`, names, email, department — see §5.3), not role descriptors; the stage's `role` (`enum_stage_role`) is a separate field. Empty list at a non-HOD approve stage = anyone with the workflow-stage role.
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
| `workflow_type` | `enum_workflow_type` | No | `purchase_request`, `store_requisition`, `purchase_order`, `gl_jv` (added 2026-09-09, `0d119b990`; GL module only), `ap_invoice`, `ap_payment`, `ar_invoice` (accounting, added after 2026-09-22; no page here). Fixed at create — the update DTO has no `workflow_type`. |
| `data` | `Json? @db.JsonB` | Yes | Full stage definition. Default `{}`. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-concurrency token — `PUT` echoes it. |
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

### 5.3 Keys added since the shape above was written (FE `wf-form-schema.ts:96-160`, verified 2026-09-22)

| Key | Level | Shape | Notes |
|---|---|---|---|
| `inherit_signature_from_pr` | `data` | `boolean?` | PO workflows only — print the source PR's signatures before the PO's own. Declared in the FE schema so a full-`data` `PUT` from the list page cannot silently drop it |
| `products` | `data` | `string[]` (product ids) | Product scope; backend contract `products: string[]` (`workflow-products.helper.ts`); feeds `GET …/products/:product_id/locations` |
| `routing_rules` | `data` | `[{ name, description, trigger_stage, condition{ field: total_amount\|department\|category, operator: eq\|lt\|gt\|lte\|gte\|between, value[], min_value?, max_value? }, action{ type: SKIP_STAGE\|NEXT_STAGE, parameters{ target_stage } } }]` | Evaluated by `workflows.navagation.service.ts:340-348`; changing them while documents are in progress is a `WORKFLOW_STAGE_CHANGE_BLOCKED` |
| `notifications`, `notification_templates` | `data` | `[]` | Present in the payload; empty arrays at HEAD |
| `available_stage_role` | `data` (server-stamped) | `enum_stage_role[]` | `withAvailableStageRole()` stamps the roles legal for the type: PR `create/approve/purchase`, PO `create/approve`, SR `create/approve/issue`, and `create/approve` for `gl_jv`, `ap_invoice`, `ap_payment`, `ar_invoice` (`workflow-stage-role.helper.ts:32-48`); `enum_stage_role` also has `view_only`, which is deliberately not offered |
| `role` | stage | `enum_stage_role?` | The stage's role; the client validator requires a `create` role somewhere (`missing_create_role`) |
| `creator_access` | stage | `string?` | Whether the document creator may act at this stage (`wf-stage-general.tsx:119`); a change while documents are in progress is treated as a skeleton change (`workflow-edit-scope.helper.ts:104`) |
| `is_show_signature` | stage | `boolean?` | Print this stage's approver signature; max 5 per workflow |
| `sla_warning_notification` | stage | `{ recipients{ requestor, current_approve }, template? }` | SLA-breach warning target |
| `assigned_users[]` | stage | `{ user_id, firstname, middlename, lastname, email, department{ id?, name? }, initials? }` | Full user records, not bare ids |
| `available_actions.<verb>.recipients.<slot>` | stage | `boolean` **or** `{ is_active, is_notification, notification_channel{ app{ is_active, notification_template_id }, email{…} } }` | Slots `requestor`, `current_approve` (kept in the data but never dispatched and cleared on load), `next_step`, `previous_step` (optional; Reject only in practice); the editor now offers only the `app` channel (`WfChannel = "app"`, `wf-stage-notifications.tsx:11`) — `email` persists for old rows but is never dispatched (see [system-config/notification-template](/en/inventory/system-config/notification-template)) |

### 5.4 API surface (gateway, verified 2026-09-22)

```
config_workflows.controller.ts  (api/config/:bu_code/workflows)          AppIdGuard api_name
  GET    assignees/:target_user_id                                        workflow.findAssigneeImpact
  POST   assignees/:target_user_id/handover                               workflow.handoverAssignee
  GET    purchase-request | purchase-order | store-requisition            workflow.findAllPurchaseRequest | …PurchaseOrder | …StoreRequisition
  GET    :workflow_id/products/:product_id/locations                      workflow.findProductLocations
  GET    :workflow_id/edit-availability                                   workflow.getEditAvailability
  GET    :workflow_id · GET (all) · POST · PUT :workflow_id · DELETE      workflow.findOne / findAll / create / update / delete
  PUT    :workflow_id/notification                                        workflow.updateNotification
workflows.controller.ts  (application)
  GET    /type/:type · GET :workflow_id/previous_stages · PATCH patch-user-action
```

Licence: every `config:workflows` route resolves to `system_admin.workflow` with per-type sub-features (`permission.route-map.ts:234`, BE `6832493b7` "sell workflow per document type").

## 6. Business Rules

- **Uniqueness.** `(name, workflow_type)` unique among non-deleted.
- **Type binding.** Document type X attaches workflows where `workflow_type = X` only; runtime rejects mismatch.
- **At-least-one submit stage.** First stage must enable `submit`; subsequent must enable at least one of `approve` / `reject` / `sendback`.
- **Deletion guards.** Workflow with any `in_progress` document cannot be deleted (`WORKFLOW_HAS_IN_PROGRESS_DOCUMENTS`); clone + inactivate is the migration path.
- **Skeleton lock.** While any document is `in_progress`, changes to the stage list, stage order, `creator_access`, or `routing_rules` are rejected with `WORKFLOW_STAGE_CHANGE_BLOCKED`; other fields save normally.
- **Versioning.** Live edits do NOT retroactively change in-flight documents.
- **Stage roles are type-bound.** Only the roles in `available_stage_role` for the workflow's type are valid on its stages.
- **HoD resolution.** Looks up document department's HoD; ignores `assigned_users`.
- **Hidden fields.** Mask UI cells; API values still flow.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) — primary consumer (`purchase_request`).
- [store-requisition](/en/inventory/store-requisition) — canonical multi-stage user (`store_requisition`).
- [purchase-order](/en/inventory/purchase-order) — high-value approval (`purchase_order`).
- **These three are the only inventory modules that can attach a workflow.** `enum_workflow_type` has seven members at HEAD (`schema.prisma:271-279`): the three above plus `gl_jv` (GL journal voucher) and `ap_invoice` / `ap_payment` / `ar_invoice` — accounting modules, no inventory page, no per-type endpoint here. [good-receive-note](/en/inventory/good-receive-note), [inventory-adjustment](/en/inventory/inventory-adjustment), [vendor-pricelist](/en/inventory/vendor-pricelist), [physical-count](/en/inventory/physical-count), and [spot-check](/en/inventory/spot-check) have no enum member and **cannot** attach a `tb_workflow` row (a prior version of this list wrongly described "optional workflow gating" for them).
- [access-control/application-role](/en/inventory/access-control/application-role) — role descriptors in `assigned_users`.
- [master-data/department](/en/inventory/master-data/department) — HoD resolution.

## 8. References

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_workflow`, `enum_workflow_type` (lines 271-279), `enum_stage_role`.
- **Seed:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_workflow.json`.
- **Backend gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_workflows/config_workflows.controller.ts`; `apps/backend-gateway/src/application/workflows/workflows.controller.ts`.
- **Backend service:** `../carmen-turborepo-backend/apps/micro-business/src/master/workflows/` — `workflows.service.ts` (`getEditAvailability` `:830`, `countDocumentsByStatus` `:892`, lock `:1380-1387`, `delete` `:1554`), `workflow-edit-scope.helper.ts` (what counts as a skeleton change), `workflow-stage-role.helper.ts`, `workflow-products.helper.ts`, `workflows.navagation.service.ts` (routing rules).
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/workflows/` — `GET-find-all-{purchase-request,purchase-order,store-requisition}-…`, `GET-find-assignee-impact-…`, `POST-handover-assignee-…`, `GET-find-product-locations-…`, `GET-get-edit-availability-…`.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role-type semantics (frozen 2026-04-27; predates per-type pages, routing rules, and the skeleton lock).
- **Frontend:** `../carmen-frontend/routes/system-admin/workflow/` — `workflow-doc-type.route.tsx` (per-type list), `wf-component.tsx`, `wf-new-form.tsx`, `wf-edit-content.tsx`, `wf-detail.tsx` (layout), `wf-stage-list.tsx` / `wf-stage-rail-node.tsx` (rail), `wf-stages.tsx` / `wf-stage-*.tsx`, `wf-insights*.ts(x)`, `wf-routing*.ts(x)`, `wf-products*.tsx`, `wf-seeded-templates.ts`, `wf-form-schema.ts` (data shape), `wf-validate.ts` (client rule codes), `wf-signature-limit.ts`, `use-wf-availability.ts`, `wf-structure-lock-notice.tsx`; `constant/module-list.ts:805-850`.
- **E2E:** `../carmen-frontend-e2e/docs/test-cases/1103-workflow.md` — catalog only (no Playwright spec).
