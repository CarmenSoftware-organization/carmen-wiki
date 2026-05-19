---
title: Clusters
description: Cluster module overview — the top-level tenant grouping that owns business units and licensed users.
published: true
date: '2026-05-19T23:30:00.000Z'
tags: platform/clusters, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Clusters

The **Clusters** module is the entry point for the largest organizational
container in the Carmen Platform. A cluster groups business units (BUs) and
the users assigned to them, and it is also where license limits live —
"how many BUs may this cluster have" and (via aggregation across its BUs)
"how many users does it cover." Routes in this module are gated to the
three admin-tier roles.

> **At a Glance**
> **Module purpose:** Tenant container that groups business units (BUs) and the users assigned to them, and holds the license limits ("how many BUs this cluster may have" and aggregated user counts across its BUs) &nbsp;·&nbsp; **Audience:** Platform admin and Carmen support engineers (`platform_admin`, `support_manager`, `support_staff`) &nbsp;·&nbsp; **Key entities/tables:** `cluster` (fields: `code`, `name`, `alias_name`, `logo_url`, `max_license_bu`, `is_active`, soft-delete trio), `business_unit` (1:N), `tb_cluster_user` (M:N join with per-cluster role `admin`/`user`) &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The Clusters module exposes the cluster aggregate root through the standard
two-screen pattern used everywhere in the Platform SPA:

- **`/clusters` → `ClusterManagement`** — server-side `DataTable` with
  debounced search, a Sheet-based filters panel (active/inactive, optional
  "show soft-deleted"), CSV export, and persisted UI state in
  `localStorage` (search, page, perpage, sort, filters).
- **`/clusters/new` → `ClusterEdit` (create mode)** — single "Cluster
  Details" card; on successful create the page redirects to the edit
  route for the new id.
- **`/clusters/:id/edit` → `ClusterEdit` (view/edit mode)** — three-column
  layout. The left column is the Cluster Details card (view-only by
  default, switched to editable via the Edit button). The right column
  spans two columns and holds two stacked cards: **Business Units** in
  this cluster and **Users** in this cluster. These cards are always
  rendered side-by-side in the grid; they are not user-collapsible.

The Business Units card lists every BU whose `cluster_id` matches the
current cluster and includes an **Add** button that navigates to
`/business-units/new?cluster_id=<id>` so the new BU is pre-linked. The
Users card lists rows from `tb_cluster_user` (cluster_id-scoped) and
supports add / edit / remove via dialogs — the add dialog searches the
global user pool and lets the operator pick a cluster role (`admin` or
`user`) and a parent BU for the assignment.

## 2. Business Context

A cluster typically represents a customer organization or a hotel group
that has signed one Carmen Platform contract. The contract specifies how
many BUs the customer may operate and (per BU) how many named users they
may license; the cluster record is where those caps live and where the
"are we under the limit?" math is run.

- The **Add BU** button on the cluster edit screen disables itself once
  `business_units.length >= max_license_bu`, with a tooltip
  ("License limit reached (N/M)").
- The **Add User** dialog disables BU options whose own
  `max_license_users` cap is reached, and surfaces the running
  "X of Y licensed users" total per BU.
- Together, clusters + their BUs are how Carmen scopes which business
  units a given user can switch into; user assignments live in
  `tb_cluster_user` and carry a `parent_bu_id` pointer.

Because clusters frame both **commercial licensing** and **access
scoping**, only the three admin-tier roles can create, edit, or delete
them. Anyone else hitting `/clusters*` lands on `AccessDenied`.

## 3. Key Concepts

- **Cluster** — a named container with `code`, `name`, `alias_name` (≤ 3
  chars, used as a short prefix in UI badges), an optional `logo_url`,
  an `is_active` flag, and an optional `max_license_bu` cap. Soft-deletes
  are tracked via `deleted_at` / `deleted_by_name`.
- **Cluster ↔ Business Unit (1:N)** — every BU carries a `cluster_id`.
  The cluster edit screen filters the global BU list down to its own
  children and counts how many are active.
- **Cluster ↔ User (M:N via `tb_cluster_user`)** — a user is added to a
  cluster by inserting a row whose key fields are `user_id`,
  `cluster_id`, `role` (`admin` | `user`), `is_active`, and an optional
  `parent_bu_id`. The Users card on `ClusterEdit` reads this join via
  `GET /api-system/user/cluster/:clusterId`.
- **License caps** — two independent limits: cluster-level
  `max_license_bu` (caps how many BUs may be attached) and BU-level
  `max_license_users` (caps how many cluster_users may have that BU as
  their parent). The cluster edit screen aggregates the per-BU cap into
  a "total licensed users" badge.
- **Soft delete** — the list view hides `deleted_at IS NOT NULL` rows
  unless the "Show soft-deleted clusters" filter is on. Soft-deleted
  rows are tagged with a destructive "Deleted" badge.

## 4. Roles and Personas

All three cluster routes are wrapped in `PrivateRoute` with the same
`allowedRoles` array. There is no in-page action gate beyond the route
gate — once the route resolves, the user can use every button on the
page (Add, Edit, Delete, Export, Add User, Remove User).

| Role | List (`/clusters`) | Create (`/clusters/new`) | Edit / Delete | Manage BUs and Users |
|---|---|---|---|---|
| `platform_admin` | Full | Full | Full | Full |
| `support_manager` | Full | Full | Full | Full |
| `support_staff` | Full | Full | Full | Full |
| Any other authenticated role | `AccessDenied` | `AccessDenied` | `AccessDenied` | `AccessDenied` |

The exact gating string in `src/App.tsx` is
`allowedRoles={["platform_admin", "support_manager", "support_staff"]}`
on each of the three routes. This is the same shape as the Report
Templates module.

## 5. Related Modules

- [[business-units]] — clusters own BUs 1:N; the cluster edit page is the
  canonical place to create a BU pre-bound to a cluster (it calls
  `navigate('/business-units/new?cluster_id=<id>')`).
- [[users]] — clusters add users through the global user list; the user
  edit page is the other side of the join (`tb_cluster_user`), where
  the same assignment can be inspected per user.
- [[auth-roles]] — defines what `platform_admin`, `support_manager`, and
  `support_staff` mean. Cluster route gating is just an application of
  those role values inside `PrivateRoute`.
- [[report-templates]] — uses the identical `allowedRoles` shape, so the
  permission model documented here transfers one-for-one.

## 6. Reference Sources

- `../carmen-platform/SITEMAP.md` — the route table is the source of
  truth for the three cluster routes and their access lists.
- `../carmen-platform/src/App.tsx` — `PrivateRoute` wiring with
  `allowedRoles`.
- `../carmen-platform/src/pages/ClusterManagement.tsx` — list page,
  filters, CSV export, soft-delete handling, BU/user count columns.
- `../carmen-platform/src/pages/ClusterEdit.tsx` — create/view/edit
  page, Business Units card, Users card, add-user dialog, license-cap
  logic.
- `../carmen-platform/src/services/clusterService.ts` — REST client
  (`/api-system/cluster`).
- `../carmen-platform/src/types/` — the `Cluster` and `BusinessUnit`
  TypeScript interfaces consumed by both screens.

## 7. Pages in This Module

- [Data Model](/en/platform/clusters/data-model) — cluster entity fields, the 1:N link to BUs,
  the join through `tb_cluster_user`, and the two license-cap fields.
- [Permissions](/en/platform/clusters/permissions) — exact `allowedRoles` gates per route and
  what each admin-tier role can do on the screen.
- [UI Screens](/en/platform/clusters/ui-screens) — `ClusterManagement` list screen and the
  three-card `ClusterEdit` layout, including the add-user dialog flow.
