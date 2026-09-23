---
title: Notification Template
description: Reusable in-app message templates (tb_notification_template) picked per workflow stage/action/recipient. Since 2026-09-16 the screen is app-channel only with eight real {{variables}}, insert chips and a preview.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: system-config, notification-template, workflow, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:45:00.000Z
---

# Notification Template

> **At a Glance**
> **Routes:** `/system-admin/notification-template` (+ `/new`, `/:id`) — nav entry now lives under the **Workflows** group (FE `00f2196d`, 2026-09-16) &nbsp;·&nbsp; **Table:** `tb_notification_template` (tenant schema; the platform-schema `tb_message_format` this page used to contrast with was **dropped** from `prisma-shared-schema-platform` since baseline) &nbsp;·&nbsp; **Endpoint:** `api/config/{bu_code}/notification-templates` &nbsp;·&nbsp; **Permission / licence:** `configuration.notification_template` &nbsp;·&nbsp; **Consumed by:** [system-config/workflow](/en/inventory/system-config/workflow)'s per-stage notification config, dispatched by `WorkflowNotificationDispatcher` &nbsp;·&nbsp; **Channel:** `app` only — since 2026-09-16 (FE `541690f5`) the list is filtered `type:app`, the create form has no Channel or Subject control, and the workflow editor's `WfChannel` is `"app"` alone; the dispatcher never delivered anything else. `enum_notification_channel` still has four values and ~60 legacy `email`/`line`/`sms` rows survive in seeded tenants.

## Implementation status (re-verified 2026-09-22)

The 2026-07-29 finding ("only `app` is dispatched, `email` is pickable but ignored") was resolved on the **UI side**, not by adding delivery: the screen and the workflow editor now only offer `app`. What changed (FE `541690f5`):

- **List** requests `filter=type:app` unconditionally, so the 20 seeded app templates show instead of the 80-row 20-events × 4-channels matrix; the Channel column is gone.
- **Form** (`noti-tmpl-form.tsx`, `noti-tmpl-edit-content.tsx`) creates with `type: "app"` fixed (`noti-tmpl-form-schema.ts:25`) and has no Subject field (subject was an email concept). The Zod `type` enum still accepts all four values (`:12`) and `mapToPayload` echoes the loaded `type`/`subject` back, so a legacy `email`/`line`/`sms` row opened by direct URL still validates and saves without being silently converted.
- **Variables are real now.** `noti-tmpl-variables.ts` declares the eight placeholders the dispatcher fills — `docNo`, `actorName`, `recipientName`, `url`, `currentStage`, `department`, `totalAmount`, `reason` — ordered by how often the seeded templates use them; the form renders them as insert-at-cursor chips (`noti-tmpl-variable-chips.tsx`) and a live notification-card preview (`noti-tmpl-preview.tsx`) that substitutes sample values and **highlights unknown `{{tokens}}`** (`splitTemplate` / `unknownVariables`). Sample values are never sent.
- **Workflow editor** `WfChannel = "app"` (`wf-stage-notifications.tsx:11`); the `email` slot still exists in the persisted `notification_channel` shape (`wf-form-schema.ts:66-82`) for old rows.
- **Backend** unchanged in substance: `WorkflowNotificationDispatcher.dispatch()` still skips every channel except `"app"` (`channel_not_supported`, `workflow-notification-dispatcher.service.ts:197`) and `render()` is still the flat `{{var}}` substitution (`:402-404`); the only commits since baseline are RPC refactors and an enum-label fix (`5cc7fd712`).

![Notification Template list](/screenshots/notification-template/index.png)

![Notification Template detail](/screenshots/notification-template/detail.png)

![Notification Template create form](/screenshots/notification-template/new.png)

## 1. What & Who

Notification Template is a plain CRUD screen for **`tb_notification_template`** rows — reusable in-app message bodies with a `name`, a required `body` (with `{{variables}}`), an optional `description`, and an `is_active` flag; `type` is always `app` for rows created here and `subject` is no longer editable (the dispatcher falls back to `${docType} update` / the template name). The screen's own translated description states its purpose directly: *"Manage reusable notification templates for workflow events."*

Templates are not free-standing content — they exist to be **picked by a workflow stage's notification configuration**. On [system-config/workflow](/en/inventory/system-config/workflow)'s stage editor, each `available_actions[<action>].recipients[<slot>].notification_channel[<channel>]` entry carries its own `notification_template_id`, filtered to active templates whose `type` matches that channel (`LookupNotificationTemplate`'s `channelType` prop). At runtime, `WorkflowNotificationDispatcher.dispatch()` reads that `notification_template_id` back off `tb_workflow.data`, loads the referenced `tb_notification_template` row, and renders its `subject`/`body` through a small `{{placeholder}}` substitution engine before dispatching an in-app notification. See §6 for the full trigger-to-delivery chain.

**Maintained by** Sysadmin (template content), Workflow Administrator (which template is wired to which stage/action/recipient/channel — done on the Workflow screen, not here). **Read by** the workflow notification dispatcher at submit/approve/reject/sendback time.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a template | Notification Template → **Add** → Name, Body (insert variables via chips, check the preview), Description, Active | `type` is sent as `app`; `name` + `type` must be unique together — duplicate rejected server-side (`ALREADY_EXISTS`); a `{{token}}` outside the eight known variables is flagged in the preview and would reach recipients literally |
| Edit a template | Template detail → **Edit** | `PUT`, `doc_version`-guarded (optimistic lock) |
| Deactivate without deleting | Detail → **Edit** → toggle **Active** off | `is_active = false`; inactive templates simply disappear from the workflow editor's picker (`filter: tpl.is_active && tpl.type === channelType`) — they are not deleted |
| Delete a template | Detail → **Edit** mode → **Delete** | Soft delete (`deleted_at` + forces `is_active = false`) — **no check for whether a workflow still references this template's id** (see §4) |
| Wire a template to a workflow stage | [system-config/workflow](/en/inventory/system-config/workflow) → stage → Notifications → toggle the (only) `app` channel → select a template | Not done from this screen at all — this screen only authors the content; the picker no longer shows a redundant "app" badge |
| Edit a legacy `email` / `line` / `sms` template | Open `/system-admin/notification-template/:id` by URL | Not listed (list is `type:app`); loads and saves with its original `type`/`subject` intact — it still will not be delivered |

## 3. Validation & Errors

| Symptom / Message | Cause | Confirmed? |
|---|---|---|
| `Notification template "<name>" already exists for channel <type>` | Duplicate `(name, type)` on create or on rename/channel-change during update | **Confirmed** — `notification-template.service.ts` `create()`/`update()` both run an explicit `findFirst` check before writing; matches the schema's `@@unique([name, type, deleted_at])` |
| Update rejected for missing `doc_version` | `update()` requires a numeric `doc_version` in the payload | **Confirmed** — `COMMON_DOC_VERSION_REQUIRED` error if absent |
| `body` is required, `subject` is not editable | Form-level Zod validation (`noti-tmpl-form-schema.ts`); `subject` is echoed from the loaded row (null for new rows) | **Confirmed** (2026-09-22) |
| An `email` channel in an old workflow stage never delivers | The dispatcher only recognizes `channelName === "app"` — any other channel is skipped with reason `channel_not_supported`; the editor no longer offers `email`, but rows saved before 2026-09-16 may still carry it | **Confirmed** — see §6 |
| A workflow stage still shows a notification_template_id after its template was deleted | No reference check on delete | **Confirmed** — the stale id resolves to `template_not_found` at dispatch time and that slot/channel is silently skipped (see §4) |

## 4. Edge Cases

- **Delete has no usage guard.** `notification-template.service.ts`'s `delete()` soft-deletes unconditionally — it does not check whether any `tb_workflow.data.stages[].available_actions[].recipients[].notification_channel[].notification_template_id` still points at the row being deleted (there is no FK; `tb_workflow.data` is JSONB). A deleted-but-still-referenced template produces a silent `template_not_found` skip at dispatch time rather than an error surfaced anywhere in the UI.
- **Only the `app` channel is ever dispatched — confirmed by reading the dispatcher, not inferred.** `WorkflowNotificationDispatcher.dispatch()` iterates `Object.keys(channels)` and explicitly skips (`reason: 'channel_not_supported'`) anything other than the literal string `"app"`. Since 2026-09-16 the workflow stage editor's `WfChannel` type is `"app"` only and this screen creates `app` rows only, so new configuration cannot produce an undelivered channel; `email`/`sms`/`line` remain valid `enum_notification_channel` values with legacy rows and no consumer.
- **Rendering is a flat Mustache-style substitution, not a template engine.** `render()` in `workflow-notification-dispatcher.service.ts` only supports `{{varName}}` (no nesting, no helpers, no conditionals). The available placeholders are fixed and now mirrored on the frontend (`NOTIFICATION_VARIABLES`): `{{docNo}}`, `{{actorName}}`, `{{recipientName}}`, `{{url}}`, `{{currentStage}}`, `{{department}}`, `{{totalAmount}}`, `{{reason}}` — any other `{{...}}` token renders as an empty string at dispatch (the preview flags it as unknown so an author sees it before saving).
- **`subject` has a fallback, `body` does not.** If `subject` is empty, the dispatcher falls back to `${docType} update` or the template's own `name`; if `body` is empty, the rendered message is simply an empty string — there is no equivalent fallback for body content.
- **Recipient-name personalization is best-effort.** `fetchUserProfiles()` looks up display names via a TCP call to the auth service and swallows any failure into an empty map — a failed lookup renders `{{recipientName}}` as `""` rather than blocking the send.
- **Delivery destination is `tb_notification` (platform schema), not this table.** The dispatcher's `notifications.create` TCP call is documented in full at [reporting-audit/notification](/en/inventory/reporting-audit/notification) — this page's table only supplies the rendered `subject`/`body` content, it is not where the sent message is recorded.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_notification_template`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Template display name. |
| `type` | `enum_notification_channel` | No | `app` / `email` / `sms` / `line`. The screen writes `app` only. |
| `subject` | `String? @db.VarChar` | Yes | Rendered as the notification title; falls back to `${docType} update` or `name` if empty. Not editable in the form since 2026-09-16. |
| `body` | `String? @db.Text` | Yes | Rendered as the notification message; no fallback if empty. |
| `description` | `String? @db.VarChar` | Yes | Internal note — not sent to recipients. |
| `is_active` | `Boolean` | No | Default `true`. Inactive templates are excluded from the workflow editor's picker. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Optimistic-concurrency guard — see [system-config/doc-version](/en/inventory/system-config/doc-version). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, type, deleted_at])` map `notificationtemplate_name_type_deletedat_u`; `@@index([name])`; `@@index([type])`.

**`enum_notification_channel`:** `app`, `email`, `sms`, `line` — 4 values. Only `app` has a live dispatch path (§4).

## 6. How a template gets used — the full trigger-to-delivery chain

1. **Author** a template here (`tb_notification_template`), setting its `type` to the channel it's meant for.
2. **Wire** it on [system-config/workflow](/en/inventory/system-config/workflow)'s stage editor: pick a recipient slot (`requestor` / `current_approve` / `next_step`, plus a fourth `previous_step` slot the dispatcher supports but this particular editor component's type doesn't expose), toggle the `app` channel (the only one offered since 2026-09-16), and pick a template from a dropdown scoped to active `app` templates.
3. **Persist** — this writes `notification_template_id` into `tb_workflow.data.stages[].available_actions[<action>].recipients[<slot>].notification_channel[<channel>]`. No FK — a loose JSONB reference.
4. **Trigger** — on a workflow submit/approve/reject/sendback action, `WorkflowOrchestratorService` (documented at [system-config/workflow](/en/inventory/system-config/workflow)) calls `WorkflowNotificationDispatcher.dispatch()` with the action taken and the doc context.
5. **Resolve recipients** — the dispatcher maps each configured slot to concrete user ids (`requestor` → the doc's `requestor_id`; `current_approve` → the actor who just acted; `next_step` → `assigned_users` of the stage now waiting; `previous_step` → `assigned_users` of the stage before the actor).
6. **Resolve channel** — for each slot, iterate its configured channels; **only `app` proceeds** (§4); the referenced template is loaded by id (`deleted_at: null` — a soft-deleted template resolves as not-found).
7. **Render** — `subject`/`body` run through the flat `{{placeholder}}` substitution (§4) using the actor, document, and recipient context.
8. **Dispatch** — a `notifications.create` TCP call to the micro-notification service inserts a `tb_notification` row (platform schema), emits over Socket.io, then flips `is_sent = true`. See [reporting-audit/notification](/en/inventory/reporting-audit/notification) for the full shape of that destination table — this page does not duplicate it.

## 7. Cross-References

- [system-config/workflow](/en/inventory/system-config/workflow) — where templates are actually wired to a stage/action/recipient/channel; that page's own `recipients` documentation is a `{ ... }` opaque blob today — this page is the first to document the `notification_channel`/`notification_template_id` shape inside it.
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) — the destination table (`tb_notification`, platform schema) the dispatcher writes to, and the unified inbox that reads it back.
- [system-config/doc-version](/en/inventory/system-config/doc-version) — the optimistic-lock mechanism this table's `doc_version` participates in.
- [system-config](/en/inventory/system-config) — parent module.

## 8. References

- **Frontend routes:** `../carmen-inventory-frontend-react/routes/system-admin/notification-template/notification-template.route.tsx`, `notification-template-new.route.tsx`, `notification-template-edit.route.tsx`, `noti-tmpl.tsx` (list, `filter=type:app`), `noti-tmpl-form.tsx` + `noti-tmpl-edit-content.tsx` (create/view/edit), `noti-tmpl-form-schema.ts`, `noti-tmpl-variables.ts` (`NOTIFICATION_VARIABLES`, `splitTemplate`, `unknownVariables`), `noti-tmpl-variable-chips.tsx`, `noti-tmpl-preview.tsx`, `use-noti-tmpl-table.tsx`.
- **Frontend type:** `../carmen-inventory-frontend-react/types/noti-tmpl.ts` (`NotificationTemplateType = "app" | "email" | "line" | "sms"` — kept at four values on purpose so legacy rows load).
- **Frontend lookup (consumer):** `../carmen-inventory-frontend-react/components/lookup/lookup-noti-tmpl.tsx` — `LookupNotificationTemplate`, filtered by `channelType`.
- **Frontend workflow-editor consumer:** `../carmen-inventory-frontend-react/routes/system-admin/workflow/wf-stage-notifications.tsx` — `WfChannel = "app"` (`:11`).
- **Nav / permission:** `../carmen-inventory-frontend-react/constant/module-list.ts:656-659` — child of the Workflows group, `licenseFeature: "configuration.notification_template"`, `PERMISSIONS.configuration.notification_template.view`.
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1104-notification-template.md` — catalog only.
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/notification-template/notification-template.service.ts` (CRUD + duplicate-name/channel validation), `.controller.ts`.
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_notification-templates/config_notification-templates.controller.ts` — `api/config/:bu_code/notification-templates`.
- **Dispatcher:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/workflow/workflow-notification-dispatcher.service.ts` — `WorkflowNotificationDispatcher.dispatch()`, `render()`.
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_notification_template`, `enum_notification_channel` (four values, unchanged).
- **Translations:** `../carmen-inventory-frontend-react/messages/en.json` — `systemAdmin.notificationTemplate.*` (namespace confirms "Manage reusable notification templates for workflow events").
