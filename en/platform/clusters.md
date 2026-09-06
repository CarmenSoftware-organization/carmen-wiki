---
title: Clusters
description: Cluster module overview — the top-level tenant grouping that owns business units and licensed users, now backed by a dated licence ledger rather than static caps.
published: true
date: 2026-09-06T12:00:00.000Z
tags: platform/clusters, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Clusters

The **Clusters** module is the entry point for the largest organizational container in the Carmen Platform. A cluster groups business units (BUs) and the users assigned to them. Licence limits — how many BUs a cluster may have, and how many named users it may cover — used to live as static columns on the cluster/BU rows; as of the 2026-07-29→2026-09-04 licensing rework they are now the *effective* rows of a dated purchase ledger (see §3). Routes and mutating actions in this module are gated by `cluster.*` permission keys **and** a `clusters` feature flag (see [Platform RBAC](/en/platform/rbac) and [Permissions](/en/platform/clusters/permissions)).

> **At a Glance**
> **Module purpose:** Tenant container that groups business units (BUs) and the users assigned to them, and links out to the licence ledger that now holds the BU-count and seat caps &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA; operator access requires `cluster.*` permission grants ([rbac](/en/platform/rbac)) plus the `clusters` feature flag being enabled &nbsp;·&nbsp; **Key entities/tables:** `tb_cluster` (fields: `code`, `name`, `alias_name`, `logo_file_token`, `avatar_file_token`, `is_active`, `doc_version`, soft-delete trio — **no licence-cap column any more**), `tb_business_unit` (1:N), `tb_cluster_user` (M:N join with per-cluster role `admin`/`user` — **no longer carries a `parent_bu_id`**), `tb_cluster_license` (new — the cluster's BU-quota purchase ledger) &nbsp;·&nbsp; **Sub-pages:** 3 &nbsp;·&nbsp; **Permission key:** `cluster.read` (list/nav) + `cluster.create`/`cluster.update`/`cluster.delete` &nbsp;·&nbsp; **Feature-flag key:** `clusters` &nbsp;·&nbsp; **superAdminOnly:** No — gated by permission, not a super-admin-only flag (per `../carmen-platform/src/components/nav/platformNav.ts`)

## 1. Overview

The Clusters module exposes the cluster aggregate root through two screens, rewritten twice since the last full sync of this page (2026-07-29):

- **`/clusters` → `ClusterManagement`** — server-side `DataTable` with debounced search, a Sheet-based filters panel (active/inactive, "show soft-deleted"), CSV export, a fleet-wide **Fleet Capacity** band above the table (now reading a dedicated `GET /api-system/clusters/summary` endpoint, not a client-computed aggregate), and persisted UI state in `localStorage`. The Fleet Capacity band adds a clickable **Quota expiring** stat (clusters whose winning BU-quota licence expires within 30 days) alongside the existing **Near limit** stat.
- **`/clusters/new` → `ClusterEdit` (create mode)** — a two-column layout: a live `ClusterDraftPlate` preview beside a two-card form — Identity, and (new) **First Quota Licence**, which issues the cluster's opening `tb_cluster_license` row at creation time. On success, navigates directly to `/clusters/:id/edit`.
- **`/clusters/:id/edit` → `ClusterEdit` (view/edit mode)** — an always-visible identity **plate** (`ClusterPlate`: branding, name, status, code/alias, two licence rails drawn as tick-strips) with a 3-tab body beneath it — **Licensing** (default), **Business Units**, **Users** — replacing the single-column scrollspy document (Overview/Details/Branding/Business Units/Users) this page described in July. There is no page-level Edit toggle — every plate field and tab action is independently editable per the `cluster.update` grant (`canEdit`), and a sticky "Unsaved changes" bar appears once a plate field differs from the last-saved snapshot. Saves are guarded by a `doc_version` optimistic-lock token (see [Data Model](/en/platform/clusters/data-model) §2.1).

Each cluster screen also offers a **View History** action (`activity_log.read` permission, new this cycle) that opens a shared change-history sheet for that cluster record.

The Business Units tab lists every BU whose `cluster_id` matches the current cluster, with its own search box, Active/Inactive filter, and sortable Code/Name columns; BUs whose rank (HQ first, then oldest, matching the database view exactly) exceeds the cluster's BU quota are flagged "Over limit." An **Add** button navigates to `/business-units/new?cluster_id=<id>` so the new BU is pre-linked. The Users tab lists rows from `tb_cluster_user`, with inline role editing directly in the table row and checkbox multi-select for a bulk **Remove** action — the bulk **Move to BU** action documented previously no longer exists, because the field it moved (`parent_bu_id`) has been removed from the schema entirely.

## 2. Business Context

A cluster typically represents a customer organization or a hotel group that has signed one Carmen Platform contract. The contract specifies how many BUs the customer may operate and how many seats they may license; those caps now live as **dated purchase rows**, not static fields on the cluster/BU record itself:

- **BU quota** comes from `tb_cluster_license` — a ledger of BU-quota purchases per cluster. The *effective* quota is the single **winning row** (covers "now", not cancelled), not a sum of every purchase ever made. No winning row means quota `0` — a real zero, never "unlimited."
- **Seats** come from `tb_business_unit_license` — a per-BU ledger, summed across every BU in the cluster that is currently in effect. Unlike BU quota, `null`/no covering rows still means "uncapped" for this dimension.
- The **Add BU** button on the cluster edit screen disables itself once `business_units.length >= bu_cap`, with a tooltip ("License limit reached (N/M)"). Exceeding the BU quota through other means (e.g. a purchase that shrinks below the current count) does not delete or block existing BUs — it flags the excess ones "Over limit" by rank instead (§ [UI Screens](/en/platform/clusters/ui-screens) §4.3).
- The **Add User** dialog's cap check is now cluster-wide, not per-BU — the dialog no longer asks which BU a new member belongs to at all, because there is no BU-scoped seat/parent field left on a cluster-user membership.
- Together, clusters + their BUs are how Carmen scopes which business units a given user can switch into.
- **Deletion guard:** the list page's row Delete action is blocked client-side (a toast, no API call) when the target cluster still has `bu_count > 0` — deleting a cluster does not cascade to its business units on the backend.
- Purchasing, renewing, or cancelling a BU-quota or seat licence happens entirely in the **licenses** module (License Center) — this module's pages link there but do not document the ledger's full CRUD; see [Data Model](/en/platform/clusters/data-model) §2.4–2.5.

## 3. Key Concepts

- **Cluster** — a named container with `code`, `name`, `alias_name` (≤ 3 chars), an `is_active` flag. Soft-deletes are tracked via `deleted_at` / `deleted_by_name`. **It no longer carries a licence-cap column** — `max_license_bu` was removed from both the Prisma model and every SPA read/write path (last SPA reference deleted by commit `7fda015`, "ลบโค้ดที่อ่าน max_license_bu ที่เหลือทั้งหมด").
- **Branding (logo + avatar)** — each cluster carries a rectangular **logo** and a square **avatar**, stored as file tokens and returned by the API as embedded presigned objects. The upload controls now live compactly inside the `ClusterPlate` header itself, not a separate "Branding" tab/section — clicking either mark opens the file picker directly.
- **Cluster ↔ Business Unit (1:N)** — every BU carries a `cluster_id`.
- **Cluster ↔ User (M:N via `tb_cluster_user`)** — a user is added to a cluster by inserting a row whose key fields are `user_id`, `cluster_id`, `role` (`admin` | `user`), `is_active`. **There is no `parent_bu_id` any more** — the column has been dropped from the schema, and the Users tab and Add-User dialog carry no Business Unit field.
- **BU-quota licence ledger (`tb_cluster_license`, new)** — one row per BU-quota purchase, with `licensed_bus`, `start_date`/`end_date`, and cancellation fields. The winning row's `licensed_bus` becomes `bu_cap`; its `end_date` becomes `bu_cap_end_date` (shown as "No expiry" when it carries the perpetual sentinel).
- **Seat licence ledger (`tb_business_unit_license`, new)** — per-BU seat purchases, summed to the cluster's `total_max_license_users`. This replaces the dropped `tb_business_unit.max_license_users` column (migration `20260821000000_drop_bu_max_license_users`).
- **Optimistic concurrency (`doc_version`)** — `tb_cluster` and `tb_cluster_user` still carry a `doc_version` counter; the edit page resends it with every `PUT` and a stale save surfaces a "changed by someone else" toast (see [Data Model](/en/platform/clusters/data-model) §2.1).
- **Audit columns** — the list shows Created and Updated (timestamp + actor), read through the shared `normalizeAudit()` helper that tolerates both the API's nested `audit` object and older flat shapes.
- **Soft delete** — the list view hides deleted rows unless "Show soft-deleted clusters" is on; deletion of a cluster that still owns business units is blocked client-side (§2).
- **Feature flag (`clusters`)** — every cluster route now also carries a `feature="clusters"` check on `PrivateRoute`, evaluated after the permission check: a session without `cluster.*` access still sees 403 (not a flag-driven 404), but a session that *does* have access sees `NotFound` or a "Coming Soon" placeholder if the flag is set to `hide`/`inactive` respectively.
- **View History (`activity_log.read`, new)** — both cluster screens offer a change-history action; recording only began 2026-08-31, so a cluster created earlier shows an empty timeline rather than implying nothing was ever changed.

## 4. Roles and Personas

Access is permission-based ([Platform RBAC](/en/platform/rbac)): each route carries a `requiredPermission` key plus a `feature` key on `PrivateRoute`, and mutating buttons are additionally wrapped in `<Can>` gates — some cluster-scoped via a `clusterId` prop.

| Surface | Gate type | Key | Scoped? |
|---|---|---|---|
| `/clusters` route | `requiredPermission` + `feature` | `cluster.read` + `clusters` | No |
| `/clusters/new` route | `requiredPermission` + `feature` | `cluster.create` + `clusters` | No |
| `/clusters/:id/edit` route | `requiredPermission` + `feature` | `cluster.update` + `clusters` | No |
| Sidebar "Clusters" entry | `permission` + `feature` filter | `cluster.read` + `clusters` | No |
| List: Add Cluster button | `<Can>` | `cluster.create` | No |
| List: row Edit action | `<Can>` | `cluster.update` | Yes — `clusterId={row.original.id}` |
| List: row **View History** action (new) | `<Can>` | `activity_log.read` | Yes — `clusterId={row.original.id}` |
| List: row Delete action | `<Can>` | `cluster.delete` | Yes — `clusterId={row.original.id}` |
| Edit page: plate fields, Branding uploads, Add User, bulk actions | `canEdit = hasPermission('cluster.update', {clusterId})` | `cluster.update` | Yes — `clusterId={id}` |
| Edit page: header **View History** action (new) | `<Can>` | `activity_log.read` | Yes — `clusterId={id}` |

Three things to note. First, a session with no platform-wide or cluster-scoped grant at all is now resolved *before* the permission check even runs: `PrivateRoute` redirects it to `/cluster-admin` if it holds that (separate) scope, rather than showing 403 — a new layer that did not exist at the last sync (see [Permissions](/en/platform/clusters/permissions) §5). Second, `cluster.delete` exists **only** as an in-page gate — no route requires it. Third, the scoped (`clusterId`) gates take the cluster-specific resolution branch: a role assignment scoped to cluster A enables Edit/Delete/View History on cluster A's row only, while the unscoped route guards pass on any cluster-scoped grant. The resolution algorithm and the full SPA-wide gate matrix live in [rbac permissions](/en/platform/rbac/permissions).

## 5. Related Modules

- [business-units](/en/platform/business-units) — clusters own BUs 1:N; the Business Units tab is the canonical place to create a BU pre-bound to a cluster. **Gotcha:** the `/business-units*` routes reuse the `cluster.read`/`cluster.create`/`cluster.update` keys — there are no `business_unit.*` keys, so granting cluster access also grants Business Units.
- [users](/en/platform/users) — clusters add users through the global user list; the user edit page is the other side of the join (`tb_cluster_user`).
- [rbac](/en/platform/rbac) — defines the permission catalog, roles, and scoped assignments behind every `cluster.*` gate in §4, plus the super-admin bypass and bootstrap exception.
- [licenses](/en/platform/licenses) — the full BU-quota/seat licence ledger and its purchase/cancel UI (License Center) now referenced from every cluster screen.
- [report-templates](/en/platform/report-templates) — same route-guard pattern with its own `report_template.*` keys.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — `PrivateRoute` wiring with `requiredPermission` + `feature` keys for all three cluster routes.
- `../carmen-platform/src/components/PrivateRoute.tsx` — the layered guard: auth → platform-authority/cluster-admin resolution → permission → super-admin → feature flag.
- `../carmen-platform/src/components/nav/platformNav.ts` — the Clusters/Business Units/Tenant Migrations nav rows (permission, feature, group).
- `../carmen-platform/src/pages/ClusterManagement.tsx` — list page, Fleet Capacity band (now backed by `GET /clusters/summary`), filters incl. Quota-expiring, CSV export, soft-delete handling, `<Can>`-gated row actions incl. View History.
- `../carmen-platform/src/pages/ClusterEdit.tsx` — create/view/edit orchestrator: `ClusterPlate`/`ClusterDraftPlate`, 3-tab body, `doc_version` optimistic locking, Add User dialog, Activity Trail header action.
- `../carmen-platform/src/pages/clusterEdit/{ClusterPlate,ClusterDraftPlate,PlateField,clusterTabs}.ts(x)` and `sections/{BusinessUnitsSection,UsersSection,SubscriptionCard}.tsx` — the current plate, tab definitions, and per-tab bodies.
- `../carmen-platform/src/pages/clusterManagement/{FleetCapacity,CapacityGauge,CapacityMeter,ClusterCreateForm,ClusterIdentityFields}.tsx` and `../carmen-platform/src/utils/capacity.ts` — capacity-gauge math and the two-card create form.
- `../carmen-platform/src/utils/businessUnitRank.ts` — the "Over limit" ranking shared with the cluster-admin persona's own BU list.
- `../carmen-platform/src/services/clusterService.ts` — REST client (`/api-system/clusters`, `/api-system/clusters/summary`, plus the `/logo` and `/avatar` upload endpoints).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_cluster`, `tb_cluster_user`, `tb_cluster_license`, `tb_business_unit_license` models (see [Data Model](/en/platform/clusters/data-model) §6 for exact line numbers).

## 7. Pages in This Module

- [Data Model](/en/platform/clusters/data-model) — cluster entity fields, the 1:N link to BUs, the join through `tb_cluster_user`, and the new licence-ledger tables that replaced the old static caps.
- [Permissions](/en/platform/clusters/permissions) — `requiredPermission`/`feature` route gates, the in-page `<Can>` gates (including the cluster-scoped variants and the new `activity_log.read` gate), and the new platform-authority resolution layer.
- [UI Screens](/en/platform/clusters/ui-screens) — `ClusterManagement` list screen (Fleet Capacity band) and the `ClusterPlate` + 3-tab (`ClusterEdit`) layout, including the create-mode draft preview, the add-user dialog, and bulk-action flows.
