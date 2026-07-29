---
title: Clusters
description: Cluster module overview — the top-level tenant grouping that owns business units and licensed users.
published: true
date: 2026-07-29T06:35:38.000Z
tags: platform/clusters, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Clusters

The **Clusters** module is the entry point for the largest organizational container in the Carmen Platform. A cluster groups business units (BUs) and the users assigned to them, and it is also where license limits live — "how many BUs may this cluster have" and (via aggregation across its BUs) "how many users does it cover." Routes and mutating actions in this module are gated by `cluster.*` permission keys (see [Platform RBAC](/en/platform/rbac)).

> **At a Glance**
> **Module purpose:** Tenant container that groups business units (BUs) and the users assigned to them, and holds the license limits ("how many BUs this cluster may have" and aggregated user counts across its BUs) &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA; operator access requires `cluster.*` permission grants ([rbac](/en/platform/rbac)) &nbsp;·&nbsp; **Key entities/tables:** `tb_cluster` (fields: `code`, `name`, `alias_name`, `logo_file_token`, `avatar_file_token`, `max_license_bu`, `is_active`, soft-delete trio), `tb_business_unit` (1:N), `tb_cluster_user` (M:N join with per-cluster role `admin`/`user`) &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The Clusters module exposes the cluster aggregate root through the standard two-screen pattern used everywhere in the Platform SPA:

- **`/clusters` → `ClusterManagement`** — server-side `DataTable` with debounced search, a Sheet-based filters panel (active/inactive, optional "show soft-deleted"), CSV export, a fleet-wide **Fleet Capacity** strip above the table, and persisted UI state in `localStorage` (search, page, perpage, sort, filters). The list no longer shows a per-row logo thumbnail column — that column was removed when the Fleet Capacity strip was introduced.
- **`/clusters/new` → `ClusterEdit` (create mode)** — single "Cluster details" card; on successful create the page now navigates directly to `/clusters/:id/edit` (a registered route) — a create no longer bounces the operator to the Dashboard.
- **`/clusters/:id/edit` → `ClusterEdit` (view/edit mode)** — a single-column, edit-in-place document following the platform-wide "A4" pattern, not the earlier three-column card layout. A sticky left-hand `ClusterEditNav` (desktop) / horizontal chip row (mobile) scrollspies five sections stacked in one column: **Overview** (a `ClusterHero` identity + capacity card — logo/avatar, code/alias/status, and BU/user capacity gauges), **Details** (identity + licensing fields, editable in place), **Branding** (logo/avatar upload), **Business Units** in this cluster, and **Users** in this cluster. There is no page-level Edit toggle any more — each field or table row is independently editable (or not) based on the `cluster.update` grant (`canEdit`), and a sticky "Unsaved changes" bar appears at the bottom of the viewport with Save/Cancel once any field differs from the last-saved snapshot. Saves are guarded by a `doc_version` optimistic-lock token (see [Data Model](/en/platform/clusters/data-model) §2.1); a stale save surfaces a conflict toast and reloads the record. `Ctrl/⌘+S` saves and `Escape` cancels while changes are pending.

The Business Units section lists every BU whose `cluster_id` matches the current cluster (with its own search box, Active/Inactive filter, and sortable Code/Name columns) and includes an **Add** button that navigates to `/business-units/new?cluster_id=<id>` so the new BU is pre-linked. The Users section lists rows from `tb_cluster_user` (cluster_id-scoped), also with search/filter, and supports add via a dialog plus **inline** role and parent-BU editing directly in the table row (no separate edit dialog) — along with checkbox multi-select and bulk **Remove** / bulk **Move to BU** actions.

## 2. Business Context

A cluster typically represents a customer organization or a hotel group that has signed one Carmen Platform contract. The contract specifies how many BUs the customer may operate and (per BU) how many named users they may license; the cluster record is where those caps live and where the "are we under the limit?" math is run.

- The **Add BU** button on the cluster edit screen disables itself once `business_units.length >= max_license_bu`, with a tooltip ("License limit reached (N/M)").
- The **Add User** dialog disables BU options whose own `max_license_users` cap is reached, and surfaces the running "X of Y licensed users" total per BU.
- Together, clusters + their BUs are how Carmen scopes which business units a given user can switch into; user assignments live in `tb_cluster_user` and carry a `parent_bu_id` pointer.
- **Deletion guard:** the list page's row Delete action is blocked client-side (a toast, no API call) when the target cluster still has `bu_count > 0` — deleting a cluster does not cascade to its business units on the backend, so removing a cluster with live BUs would orphan them. Operators must move or delete the BUs first.
- **Fleet Capacity strip:** the list page rolls up every non-deleted cluster into a fleet-wide view — total BU/user capacity used vs. capped, a count of uncapped clusters and their in-use total, and counts of total / active / near-limit (≥ 90% of a finite cap) clusters.

Because clusters frame both **commercial licensing** and **access scoping**, every cluster route and mutating action is gated by `cluster.*` permission keys (§4). A session without the required key lands on the `Forbidden` (403) page when hitting `/clusters*` directly, and does not see the Add/Edit/Delete buttons that its grants do not cover — with one exception: the empty-state Add Cluster button is ungated and only caught by the route guard (see [Permissions](/en/platform/clusters/permissions) §7).

## 3. Key Concepts

- **Cluster** — a named container with `code`, `name`, `alias_name` (≤ 3 chars, shown only in the edit form and the CSV export's Alias column — no UI badge renders it), an `is_active` flag, and an optional `max_license_bu` cap. Soft-deletes are tracked via `deleted_at` / `deleted_by_name`.
- **Branding (logo + avatar)** — each cluster carries a rectangular **logo** and a square **avatar**, stored in Prisma as file tokens (`logo_file_token`, `avatar_file_token`) and returned by the API as embedded presigned objects (`logo: { url, expires_at }`, `avatar: { url, expires_at }`). Uploads happen on the edit page's Branding section via dedicated multipart endpoints; the list page no longer shows a logo thumbnail column (removed when the Fleet Capacity strip was added) — the `ClusterHero` card on the edit page's Overview section is now the only place a cluster's logo/avatar is visible outside the Branding section itself.
- **Cluster ↔ Business Unit (1:N)** — every BU carries a `cluster_id`. The cluster edit screen filters the global BU list down to its own children and counts how many are active.
- **Cluster ↔ User (M:N via `tb_cluster_user`)** — a user is added to a cluster by inserting a row whose key fields are `user_id`, `cluster_id`, `role` (`admin` | `user`), `is_active`, and an optional `parent_bu_id`. The Users section on `ClusterEdit` reads this join via `GET /api-system/user/clusters/:clusterId`.
- **License caps** — two independent limits: cluster-level `max_license_bu` (caps how many BUs may be attached) and BU-level `max_license_users` (caps how many cluster_users may have that BU as their parent). The cluster edit screen aggregates the per-BU cap into a "total licensed users" figure on the `ClusterHero` card, and the list/Fleet-Capacity strip roll the same math up fleet-wide.
- **Optimistic concurrency (`doc_version`)** — `tb_cluster` (and `tb_cluster_user`) now carry a `doc_version` counter. The edit page reads it on load and resends it with every `PUT`; a stale save is rejected with `409` and the SPA shows a "changed by someone else" toast and reloads the record rather than silently overwriting it (see [Data Model](/en/platform/clusters/data-model) §2.1).
- **Audit columns** — the list shows Created and Updated columns (timestamp plus actor name). The SPA flattens the nested `audit` object from API responses (`audit.created.{at,name}`, `audit.updated.{at,name}`) for the date columns, tolerating the older flat shape, which wins when present (`item.created_at ?? item.audit?.created?.at`). The Updated cell is omitted when `updated_at` equals `created_at`.
- **Soft delete** — the list view hides `deleted_at IS NOT NULL` rows unless the "Show soft-deleted clusters" filter is on. Soft-deleted rows are tagged with a destructive "Deleted" badge (its tooltip names the deleter), and the filter additionally appends a Deleted By audit column. Deletion of a cluster that still owns business units is blocked client-side (§2).

## 4. Roles and Personas

Access is permission-based ([Platform RBAC](/en/platform/rbac)): each route carries a `requiredPermission` key on `PrivateRoute`, and mutating buttons are additionally wrapped in `<Can>` gates — some of them cluster-scoped via a `clusterId` prop.

| Surface | Gate type | Key | Scoped? |
|---|---|---|---|
| `/clusters` route | `requiredPermission` | `cluster.read` | No |
| `/clusters/new` route | `requiredPermission` | `cluster.create` | No |
| `/clusters/:id/edit` route | `requiredPermission` | `cluster.update` | No |
| Sidebar "Clusters" entry | `permission` filter | `cluster.read` | No |
| List: Add Cluster button | `<Can>` | `cluster.create` | No |
| List: row Edit action | `<Can>` | `cluster.update` | Yes — `clusterId={row.original.id}` |
| List: row Delete action | `<Can>` | `cluster.delete` | Yes — `clusterId={row.original.id}` |
| Edit page: Details/Branding fields, Add User button, bulk actions | `canEdit = hasPermission('cluster.update', {clusterId})` | `cluster.update` | Yes — `clusterId={id}` |

Two things to note. First, `cluster.delete` exists **only** as an in-page gate — no route requires it, so a session holding `cluster.read` alone sees the list but an empty row-action menu. Second, the scoped (`clusterId`) gates take the cluster-specific resolution branch: a role assignment scoped to cluster A enables Edit/Delete on cluster A's row only, while the unscoped route guards pass on any cluster-scoped grant. There is no separate Edit-toggle gate any more — the edit page computes a single `canEdit` boolean once (`!isNew && hasPermission('cluster.update', { clusterId: id })`) and passes it down to every section; a session without the grant can reach `/clusters/:id/edit` (the route guard is unscoped) but sees every field, upload control, and user-management action rendered read-only/hidden. The resolution algorithm and the full SPA-wide gate matrix live in [rbac permissions](/en/platform/rbac/permissions).

## 5. Related Modules

- [business-units](/en/platform/business-units) — clusters own BUs 1:N; the cluster edit page is the canonical place to create a BU pre-bound to a cluster (it calls `navigate('/business-units/new?cluster_id=<id>')`). **Gotcha:** the `/business-units*` routes reuse the `cluster.read`/`cluster.create`/`cluster.update` keys — there are no `business_unit.*` keys, so granting cluster access also grants Business Units.
- [users](/en/platform/users) — clusters add users through the global user list; the user edit page is the other side of the join (`tb_cluster_user`), where the same assignment can be inspected per user.
- [rbac](/en/platform/rbac) — defines the permission catalog, roles, and scoped assignments behind every `cluster.*` gate in §4, plus the super-admin bypass and bootstrap exception. Its §5 documents the legacy role-enum model this module was gated by until 2026-06.
- [report-templates](/en/platform/report-templates) — same route-guard pattern with its own `report_template.*` keys, so the gating model documented here transfers one-for-one.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — `PrivateRoute` wiring with `requiredPermission` keys (authoritative for route gating; `SITEMAP.md` still shows the legacy role lists and is stale on access columns).
- `../carmen-platform/src/pages/ClusterManagement.tsx` — list page, Fleet Capacity strip, filters, CSV export, soft-delete handling, audit columns, deletion guard, `<Can>`-gated row actions.
- `../carmen-platform/src/pages/ClusterEdit.tsx` — create/view/edit orchestrator page: scrollspy nav, hero, edit-in-place Details/Branding/Business-Units/Users sections, `doc_version` optimistic locking, Add User dialog, license-cap logic.
- `../carmen-platform/src/pages/clusterManagement/{ClusterHero,FleetCapacity,CapacityGauge,CapacityMeter}.tsx` and `../carmen-platform/src/utils/capacity.ts` — capacity-gauge math and rendering shared by the list and edit pages.
- `../carmen-platform/src/pages/clusterEdit/{ClusterEditNav,useClusterUsers}.ts(x)` and `sections/{DetailsSection,BrandingSection,BusinessUnitsSection,UsersSection}.tsx` — the edit page's scrollspy nav and per-section components.
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — shared logo/avatar upload control used by the Branding section.
- `../carmen-platform/src/services/clusterService.ts` — REST client (`/api-system/clusters`, plus the `/logo` and `/avatar` upload endpoints).
- `../carmen-platform/src/types/` — the `Cluster`, `PresignedImage`, and `BusinessUnit` TypeScript interfaces consumed by both screens.

## 7. Pages in This Module

- [Data Model](/en/platform/clusters/data-model) — cluster entity fields, the 1:N link to BUs, the join through `tb_cluster_user`, and the two license-cap fields.
- [Permissions](/en/platform/clusters/permissions) — `requiredPermission` route gates, the in-page `<Can>` gates (including the cluster-scoped variants), and what each `cluster.*` key opens.
- [UI Screens](/en/platform/clusters/ui-screens) — `ClusterManagement` list screen (Fleet Capacity strip) and the scrollspy `ClusterEdit` layout (Overview/Details/Branding/Business Units/Users), including the add-user dialog and bulk-action flows.
