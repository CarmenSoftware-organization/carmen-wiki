---
title: Dashboard Templates — Lifecycle
description: Operations on dashboard templates - create, edit, reorder, delete with their version-bump and cache side effects, plus the BU-default status check and the deploy flow including 409/422 handling.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, dashboard-templates, lifecycle
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Dashboard Templates — Lifecycle

> **At a Glance**
> **Operations:** create · edit · reorder · delete · deploy-status · deploy &nbsp;·&nbsp; **Not in this module:** hard delete, restore, per-module version, undo of a deploy, scheduled deploy &nbsp;·&nbsp; **Endpoints:** `/api-system/dashboard-templates` and `/deploy/:target_bu_code` &nbsp;·&nbsp; **Cross-entity effects:** version counter, gateway cache, tenant `tb_dashboard_bu_widget`

## 1. Overview

Template CRUD is plain, with two hidden side effects tied to `kind`. Deploying is the only operation that crosses databases: it reads the BU-default set from the backstage database through micro-cluster and writes into one tenant at a time through micro-data. There is no endpoint to deploy to many BUs at once; "deploy to N BUs" is the SPA looping over the single-BU endpoint.

## 2. Create flow

`POST /api-system/dashboard-templates` (`dashboard_template.create`, backstage-wide). Gateway first validates `dataset_id` and `widget_type` against the micro-data catalog (422 on unknown dataset or unsupported render), then sends the write to micro-cluster. Micro-cluster stores only whitelisted fields (`kind`, `module`, `dataset_id`, `widget_type`, `order_index`, `params`, `display`, allow/deny lists, `is_active`) plus the title columns resolved from `title_i18n`/`title`. Response: `{ id, doc_version }`.

Side effects: `kind = bu_default` bumps the version in the same transaction; `kind = system` clears the gateway cache after the RPC returns.

## 3. Edit flow

`PATCH /:id` (`dashboard_template.update`). The gateway reads the stored row first, then applies rules that need it: `allow/deny` on a `bu_default` row, and `module: null` on a `system` row, are rejected with 422; the dataset/render check runs only when either changed (using the merged values). Micro-cluster then updates under optimistic locking: `doc_version` is part of the `UPDATE ... WHERE`, a mismatch writes nothing and returns `ALREADY_EXISTS` ("Dashboard template was modified", 409). If the client omits `doc_version` the write is unguarded; the backstage SPA sends it whenever the row has one.

Fields that cannot change after create: `kind` (not in the update whitelist). `module` is whitelisted for update at the API level, but the SPA never sends it.

Title rule on update: if `title_i18n` is present it wins; a legacy `title` alone is merged into the stored `title_i18n` so the Thai text survives an old client's edit.

## 4. Reorder

`PATCH /api-system/dashboard-templates/reorder` with `{ kind, module, items: [{ id, order_index }] }` (`dashboard_template.update`). Micro-cluster counts that every id is a live row of that kind and module; if any id is not, the whole request is `NOT_FOUND` and nothing changes. Otherwise it writes each `order_index`, and for `bu_default` bumps the version. The SPA renumbers the entire module list as 10, 20, 30..., so one arrow click touches every row's `order_index` and `updated_at`.

## 5. Delete

`DELETE /:id` (`dashboard_template.delete`). Soft delete: sets `deleted_at`/`deleted_by_id`. `bu_default` deletes bump the version. The gateway clears the system-widget cache on **every** delete, regardless of kind (harmless extra invalidation).

## 6. Status and deploy

### 6.1 Status check

`GET /deploy/:target_bu_code/status` (`dashboard_template.deploy`). The gateway reads the current `{version, widgets}` snapshot from micro-cluster, asks micro-data for the BU's deploy row (`GET /api/dashboard/bu-widgets/deploy-state?bu_code=`), and returns:

```
{ version, status, deployed_version, deployed_at, customized_at }

status = never        if no deploy row
       = customized   if row.customized_at is set
       = outdated     if row.deployed_version < version
       = current      otherwise
```

Note the order: `customized` wins over `outdated`.

### 6.2 Deploy

`POST /deploy/:target_bu_code` with `{ mode, expected_version }` (`dashboard_template.deploy`):

```
snapshot = micro-cluster.getBuDefault()      # version + active bu_default widgets, one RepeatableRead read
if snapshot.version != expected_version  -> 409 "BU default version changed"
if snapshot.widgets is empty             -> 422 "BU default set is empty"
micro-data POST /api/dashboard/bu-widgets/deploy?bu_code&user_id
   body: { mode, version, widgets[module,dataset_id,widget_type,title,title_i18n,order_index,params,display] }
```

In micro-data (`service/bu_widget_deploy.go`) one tenant transaction locks or creates the deploy row; if `mode = skip_customized` and the BU is customized it returns `{ result: "skipped" }`; otherwise it **soft-deletes every existing BU widget, inserts the template widgets**, and marks the row deployed (version, time, actor; customized fields cleared) and returns `{ result: "deployed", count }`. In overwrite mode, any manual BU widgets are therefore lost; there is no merge.

Snapshot consistency matters: version and widgets are read in one `RepeatableRead` transaction so a concurrent edit cannot pair new widgets with an old version and slip past the 409 check (`getBuDefault`, `dashboard-template.service.ts`).

### 6.3 SPA batch behaviour

| Aspect | Behaviour |
|---|---|
| Concurrency | Status checks 4 at a time; deploys 3 at a time (`mapWithConcurrency`) |
| 409 on any BU | Sets a stop flag; remaining queued BUs are not started; toast "The BU default changed while deploying. The run was stopped; refresh the status and deploy again." |
| 422 on any BU | Same stop; the backend's message is toasted |
| Other error | Counted as failed, row shows its message, run continues; final toast is a partial summary |
| Stop button | Aborts in-flight deploy requests (status checks continue). Aborting only stops the browser waiting; a request that already reached micro-data may still complete, so re-check status afterwards |
| After each deploy | The row's status is re-fetched |
| Refresh status | Reloads version and active count, clears prior per-row outcomes, rechecks every BU |

## 7. Cross-entity side effects

| Mutation | Effect elsewhere |
|---|---|
| Any `bu_default` write | Version +1, so every deployed BU turns `outdated` (or stays `customized`) |
| Any `system` write | Gateway cache cleared; BUs see it on the next `/dashboard-widgets/<module>` call (other gateway instances within the 60 s TTL) |
| Deploy | Replaces all widgets of one BU's `tb_dashboard_bu_widget`; resets its customized flag |
| BU admin edits the BU board | Tenant row gets `customized_at`; later `skip_customized` deploys skip that BU |

## 8. References

- Gateway: `.../backstage/backstage_dashboard-templates/{backstage_dashboard-templates.service.ts,dashboard-template-deploy.service.ts,deploy-status-of.ts,micro-data-template.client.ts}`, deploy controller `api-system/dashboard-templates/deploy` (`:target_bu_code/status` line 50, `:target_bu_code` line 85).
- Micro-cluster: `.../dashboard-template/{dashboard-template.service.ts,dashboard-template-version.ts,dashboard-template-title.ts}`.
- Micro-data: `service/bu_widget_deploy.go`, `db/widget_repo.go`.
- SPA: `src/pages/dashboardTemplates/DeployPanel.tsx`.
- Siblings: [Dashboard Templates](/en/platform/dashboard-templates), [Data Model](/en/platform/dashboard-templates/data-model), [UI Screens](/en/platform/dashboard-templates/ui-screens).
