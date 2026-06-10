---
title: Clusters
description: Cluster module overview — the top-level tenant grouping that owns business units and licensed users.
published: true
date: 2026-06-10T13:30:00.000Z
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

- **`/clusters` → `ClusterManagement`** — server-side `DataTable` with debounced search, a Sheet-based filters panel (active/inactive, optional "show soft-deleted"), CSV export, and persisted UI state in `localStorage` (search, page, perpage, sort, filters).
- **`/clusters/new` → `ClusterEdit` (create mode)** — single "Cluster Details" card; on successful create the page navigates to `/clusters/:id`, which is not a registered route — the catch-all currently lands the operator on the Dashboard (see [UI Screens](/en/platform/clusters/ui-screens) §3).
- **`/clusters/:id/edit` → `ClusterEdit` (view/edit mode)** — three-column layout. The left column is the Cluster Details card (view-only by default, switched to editable via the Edit button — rendered only inside `<Can permission="cluster.update" clusterId={id}>`). The right column spans two columns and holds three stacked cards: **Branding** (logo + avatar upload), **Business Units** in this cluster, and **Users** in this cluster. These cards are always rendered side-by-side in the grid; they are not user-collapsible.

The Business Units card lists every BU whose `cluster_id` matches the current cluster and includes an **Add** button that navigates to `/business-units/new?cluster_id=<id>` so the new BU is pre-linked. The Users card lists rows from `tb_cluster_user` (cluster_id-scoped) and supports add / edit / remove via dialogs — the add dialog searches the global user pool and lets the operator pick a cluster role (`admin` or `user`) and a parent BU for the assignment.

## 2. Business Context

A cluster typically represents a customer organization or a hotel group that has signed one Carmen Platform contract. The contract specifies how many BUs the customer may operate and (per BU) how many named users they may license; the cluster record is where those caps live and where the "are we under the limit?" math is run.

- The **Add BU** button on the cluster edit screen disables itself once `business_units.length >= max_license_bu`, with a tooltip ("License limit reached (N/M)").
- The **Add User** dialog disables BU options whose own `max_license_users` cap is reached, and surfaces the running "X of Y licensed users" total per BU.
- Together, clusters + their BUs are how Carmen scopes which business units a given user can switch into; user assignments live in `tb_cluster_user` and carry a `parent_bu_id` pointer.

Because clusters frame both **commercial licensing** and **access scoping**, every cluster route and mutating action is gated by `cluster.*` permission keys (§4). A session without the required key lands on `AccessDenied` when hitting `/clusters*` directly, and does not see the Add/Edit/Delete buttons that its grants do not cover — with one exception: the empty-state Add Cluster button is ungated and only caught by the route guard (see [Permissions](/en/platform/clusters/permissions) §7).

## 3. Key Concepts

- **Cluster** — a named container with `code`, `name`, `alias_name` (≤ 3 chars, shown only in the edit form and the CSV export's Alias column — no UI badge renders it), an `is_active` flag, and an optional `max_license_bu` cap. Soft-deletes are tracked via `deleted_at` / `deleted_by_name`.
- **Branding (logo + avatar)** — each cluster carries a rectangular **logo** and a square **avatar**, stored in Prisma as file tokens (`logo_file_token`, `avatar_file_token`) and returned by the API as embedded presigned objects (`logo: { url, expires_at }`, `avatar: { url, expires_at }`). Uploads happen on the edit page's Branding card via dedicated multipart endpoints; the list page shows a logo thumbnail (falling back to the avatar).
- **Cluster ↔ Business Unit (1:N)** — every BU carries a `cluster_id`. The cluster edit screen filters the global BU list down to its own children and counts how many are active.
- **Cluster ↔ User (M:N via `tb_cluster_user`)** — a user is added to a cluster by inserting a row whose key fields are `user_id`, `cluster_id`, `role` (`admin` | `user`), `is_active`, and an optional `parent_bu_id`. The Users card on `ClusterEdit` reads this join via `GET /api-system/user/clusters/:clusterId`.
- **License caps** — two independent limits: cluster-level `max_license_bu` (caps how many BUs may be attached) and BU-level `max_license_users` (caps how many cluster_users may have that BU as their parent). The cluster edit screen aggregates the per-BU cap into a "total licensed users" badge.
- **Audit columns** — the list shows Created and Updated columns (timestamp plus actor name). The SPA flattens the nested `audit` object from API responses (`audit.created.{at,name}`, `audit.updated.{at,name}`) for the date columns, tolerating the older flat shape, which wins when present (`item.created_at ?? item.audit?.created?.at`). The Updated cell is omitted when `updated_at` equals `created_at`.
- **Soft delete** — the list view hides `deleted_at IS NOT NULL` rows unless the "Show soft-deleted clusters" filter is on. Soft-deleted rows are tagged with a destructive "Deleted" badge (its tooltip names the deleter), and the filter additionally appends a Deleted By audit column.

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
| Edit page: Edit toggle | `<Can>` | `cluster.update` | Yes — `clusterId={id}` |

Two things to note. First, `cluster.delete` exists **only** as an in-page gate — no route requires it, so a session holding `cluster.read` alone sees the list but an empty row-action menu. Second, the scoped (`clusterId`) gates take the cluster-specific resolution branch: a role assignment scoped to cluster A enables Edit/Delete on cluster A's row only, while the unscoped route guards pass on any cluster-scoped grant. The edit form's Save button is not separately wrapped — without the `<Can>`-gated Edit toggle the form never leaves view mode, so Save is unreachable. The resolution algorithm and the full SPA-wide gate matrix live in [rbac permissions](/en/platform/rbac/permissions).

## 5. Related Modules

- [business-units](/en/platform/business-units) — clusters own BUs 1:N; the cluster edit page is the canonical place to create a BU pre-bound to a cluster (it calls `navigate('/business-units/new?cluster_id=<id>')`). **Gotcha:** the `/business-units*` routes reuse the `cluster.read`/`cluster.create`/`cluster.update` keys — there are no `business_unit.*` keys, so granting cluster access also grants Business Units.
- [users](/en/platform/users) — clusters add users through the global user list; the user edit page is the other side of the join (`tb_cluster_user`), where the same assignment can be inspected per user.
- [rbac](/en/platform/rbac) — defines the permission catalog, roles, and scoped assignments behind every `cluster.*` gate in §4, plus the super-admin bypass and bootstrap exception. Its §5 documents the legacy role-enum model this module was gated by until 2026-06.
- [report-templates](/en/platform/report-templates) — same route-guard pattern with its own `report_template.*` keys, so the gating model documented here transfers one-for-one.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — `PrivateRoute` wiring with `requiredPermission` keys (authoritative for route gating; `SITEMAP.md` still shows the legacy role lists and is stale on access columns).
- `../carmen-platform/src/pages/ClusterManagement.tsx` — list page, logo thumbnail, filters, CSV export, soft-delete handling, audit columns, `<Can>`-gated row actions.
- `../carmen-platform/src/pages/ClusterEdit.tsx` — create/view/edit page, Branding card, Business Units card, Users card, add-user dialog, license-cap logic.
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — shared logo/avatar upload control used by the Branding card.
- `../carmen-platform/src/services/clusterService.ts` — REST client (`/api-system/clusters`, plus the `/logo` and `/avatar` upload endpoints).
- `../carmen-platform/src/types/` — the `Cluster`, `PresignedImage`, and `BusinessUnit` TypeScript interfaces consumed by both screens.

## 7. Pages in This Module

- [Data Model](/en/platform/clusters/data-model) — cluster entity fields, the 1:N link to BUs, the join through `tb_cluster_user`, and the two license-cap fields.
- [Permissions](/en/platform/clusters/permissions) — `requiredPermission` route gates, the in-page `<Can>` gates (including the cluster-scoped variants), and what each `cluster.*` key opens.
- [UI Screens](/en/platform/clusters/ui-screens) — `ClusterManagement` list screen and the four-card `ClusterEdit` layout (Details, Branding, Business Units, Users), including the add-user dialog flow.
