---
title: Cluster — UI Screens
description: ClusterManagement (list) and ClusterEdit (create/view/edit) screens — layout, filters, dialogs, persisted state.
published: true
date: 2026-07-29T06:35:38.000Z
tags: book/platform, clusters, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — UI Screens

> **At a Glance**
> **Screens:** `ClusterManagement` (list, `/clusters`) &nbsp;·&nbsp; `ClusterEdit` create (`/clusters/new`) &nbsp;·&nbsp; `ClusterEdit` view/edit (`/clusters/:id/edit`) &nbsp;·&nbsp; **Edit layout:** single-column scrollspy document ("A4" pattern) — sticky nav (Overview/Details/Branding/Business Units/Users) + edit-in-place fields, no page-level Edit toggle &nbsp;·&nbsp; **Dialogs:** Add User to Cluster · Remove Cluster User confirm (single + bulk) · Soft Delete Cluster confirm &nbsp;·&nbsp; **Access:** route guards `cluster.read` / `cluster.create` / `cluster.update`; Add/Edit/Delete buttons behind `<Can>` gates (see [Permissions](./permissions.md)) &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list page &nbsp;·&nbsp; **Concurrency:** `doc_version` optimistic lock on save

## 1. Overview

The Platform SPA follows a consistent two-screen pattern for cluster management: a list page (`ClusterManagement`) with a server-side `DataTable`, a slide-over filters Sheet, and a Fleet Capacity summary strip; and an edit page (`ClusterEdit`) that follows the platform-wide "A4" edit-in-place pattern — no page-level Edit toggle, no separate view/edit mode. Both screens are registered under the `/clusters` route prefix and are guarded by `requiredPermission` keys — `cluster.read` (list), `cluster.create` (create), `cluster.update` (edit); mutating fields and buttons inside the pages carry an additional `canEdit` gate resolved from `cluster.update` (see [Permissions](./permissions.md)).

The cluster edit page renders as a single scrolling column with a sticky `ClusterEditNav` sidebar (desktop: vertical scrollspy list; mobile: a horizontal scrollable chip row) that jumps between five `id`-anchored sections: **Overview** (a read-first `ClusterHero` card — logo/avatar, code/alias/status badge, audit lines, and two `CapacityGauge` meters for BU and user license usage), **Details** (identity + licensing fields), **Branding** (logo/avatar upload), **Business Units**, and **Users** — the last two sections show a live row count as a nav badge. There is no Edit button anywhere in the header: every field renders via `InlineField` (click-to-edit; commits on blur/Enter, reverts on Escape) gated by a single `canEdit = !isNew && hasPermission('cluster.update', { clusterId: id })` boolean computed once per page, and a sticky bottom bar reading "Unsaved changes" with Cancel/Save Changes buttons appears whenever `formData` differs from the last-loaded/saved snapshot — `Ctrl/⌘+S` saves and `Escape` cancels via the shared keyboard-shortcut hook. In create mode (`isNew = true`) the page instead renders a single "Cluster details" card with the older `ClusterIdentityFields` component (still a plain form, no inline-edit or scrollspy) — the Branding, BU, and Users sections don't exist until the record is saved and the SPA navigates straight to `/clusters/:id/edit`. The Business Units section uses a navigate-to-create flow (`/business-units/new?cluster_id=<id>`) to pre-link a new BU to this cluster; the Users section has its own in-page **Add User to Cluster** dialog that searches the global user pool, plus inline role/parent-BU editing and bulk actions directly in the table (§4.4).

A dedicated **not-found** state renders when `GET /api-system/clusters/:id` returns no record (bad or deleted id): an `EmptyState` card with a "Back to clusters" button, gating the entire hero/section shell so it never renders over blank data.

## 2. `ClusterManagement` — list page (`/clusters`)

### 2.1 Layout

The page renders inside `Layout` with a two-row header: a title/subtitle row ("Cluster Management" / "Manage and configure clusters") and an actions row containing **Export** and **Add Cluster** buttons. Below the header sits the **Fleet Capacity** card (§2.1a), then a search-and-filters row: a debounced (400 ms) search `Input` on the left, and a **Filters** Sheet trigger on the right (shows an active-filter count badge when any filter is set). Active filter chips appear as a strip below the search row when any filter is active. The main content area is a `DataTable` in server-side mode with pagination, with the Name column frozen (sticky) on horizontal scroll (`stickyLeftColumns={3}`).

Columns in order: `code` (clickable link — navigates to `/clusters/:id/edit`), `name` (clickable link — also navigates to edit, with a red `Deleted` badge appended when `deleted_at` is non-null; the badge's tooltip reads "Deleted by &lt;name&gt;" when `deleted_by_name` is present), `is_active` (Active/Inactive badge), `bu_count` (rendered as a `CapacityMeter` bar — `used / cap` with a coloured fill, "near"/"over" tag near or at the cap, `∞` when uncapped), `user_count` (same `CapacityMeter` treatment against `total_max_license_users`), `created_at` + `created_by_name`, `updated_at` + `updated_by_name` (suppressed when equal to `created_at`), and conditionally `deleted_at` + `deleted_by_name` in destructive red (appended only when the "Show soft-deleted" filter is active). The final column is a narrow (`max-w-12`) icon-button `DropdownMenu` for row actions. **There is no logo thumbnail column** — a per-row logo/avatar image was shown here before the Fleet Capacity strip and `CapacityMeter` columns were introduced; it was removed, not relocated. A cluster's logo/avatar is now only visible on its own edit page (`ClusterHero`, §4) and the Branding section.

### 2.1a Fleet Capacity strip

A `FleetCapacity` card sits between the header and the search row, summarising **every non-deleted cluster** (fetched as a separate, unpaginated `perpage: -1` call, not the current page's rows) via `summarizeFleet()` (`../carmen-platform/src/utils/capacity.ts`):

- Two `CapacityGauge` bars — **Business units** and **Users** — showing fleet-wide `used / cap` (capped clusters' caps and usage summed together) plus a note of how many clusters are uncapped and how much they use (uncapped clusters are excluded from the cap sum so an unlimited cluster doesn't zero out the ratio).
- Three plain stats: total cluster count, active count, and a **near-limit** count (clusters at ≥ 90% or over on either the BU or the user cap — the same `NEAR = 0.9` threshold used by the row-level `CapacityMeter`).

The strip shows a skeleton while `loadFleet()` is in flight and silently falls back to `null` (rendering the skeleton indefinitely, not an error) if the aggregate fetch fails — the main table is unaffected either way.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet. Two filter groups are wired:

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). The two buttons may be toggled independently; when both are active or both are off, no `is_active` constraint is applied (the filter is elided from the query). A **Clear** link appears in the group header when any status value is selected.
- **Deleted** — a checkbox labelled "Show soft-deleted clusters". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge in the `name` cell, and the conditional `Deleted By` audit column is appended to the `DataTable`.

There is no Role filter group. When any filter is active a **Clear All Filters** button appears at the bottom of the Sheet, and active filter chips appear in the strip below the search row. Each chip has an inline remove button; a **Clear all** text link also clears all filters at once.

### 2.3 Header actions

Two buttons appear in the header actions row, left to right:

- **Export** — client-side CSV export using `generateCSV` / `downloadCSV` utilities. Exports the currently loaded page of rows with columns: `Code`, `Name`, `Alias`, `Status` (`is_active`), `Max Licensed BUs` (`max_license_bu`), `Users` (`users_count`), `Max Licensed Users` (`total_max_license_users`), `Created` (`created_at`). File name: `clusters-<YYYY-MM-DD>.csv`. The button is disabled while loading or when the table is empty.
- **Add Cluster** — navigates to `/clusters/new`. Wrapped in `<Can permission="cluster.create">`, so it renders only for sessions holding that key. Note: the **empty-state** Add Cluster button (shown when the table has no rows and no search term) is *not* `<Can>`-gated — a `cluster.read`-only session can click it, and the `cluster.create` route guard on `/clusters/new` then renders the `Forbidden` (403) page.

There is no Fetch Keycloak button (that affordance exists only on the Users list). There is no Hard Delete action anywhere in cluster management — the `ClusterManagement.tsx` row action menu contains only **Edit** and **Delete** (soft). No hard-delete endpoint is called from the clusters UI.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with two items, each behind a **cluster-scoped `<Can>` gate** (the `clusterId={row.original.id}` prop makes the check resolve against that specific cluster's grants — see [Permissions](./permissions.md) §3):

- **Edit** — inside `<Can permission="cluster.update" clusterId={row.original.id}>`; navigates to `/clusters/:id/edit`.
- **Delete** — inside `<Can permission="cluster.delete" clusterId={row.original.id}>`; calls the row's `handleDelete(id)` first. If the cluster's `bu_count > 0`, the click is blocked client-side with an error toast ("Can't delete `<name>`... it still has N business unit(s). Delete or move them to another cluster first.") and **no** `ConfirmDialog` opens — deleting a cluster does not cascade to its BUs on the backend, so this guard prevents orphaning them. Otherwise it sets `deleteId` state and opens the Soft Delete Cluster `ConfirmDialog` (§5.4); on confirm, calls `DELETE /api-system/clusters/:id` (soft delete — sets `deleted_at`).

A session whose grants cover neither key for a given cluster sees an empty dropdown for that row. There is no **Hard Delete** option in the cluster row action menu. Hard deletion of cluster records is not exposed through the Platform SPA.

### 2.5 Audit columns

The API returns audit data as a nested `audit` object (`audit.created/updated/deleted`, each `{ at, id, name, avatar }`). `fetchClusters` flattens this into `created_at`/`created_by_name` etc. before rendering, tolerating the older flat shape, which wins when present (`item.created_at ?? item.audit?.created?.at`). Two audit columns are always shown:

| Column header | Fields rendered |
|---|---|
| Created | `created_at` (formatted `YYYY-MM-DD HH:mm:ss`, browser local time) + `created_by_name` on the next line |
| Updated | `updated_at` + `updated_by_name` — suppressed (renders `null`) when `updated_at === created_at` |

When the "Show soft-deleted clusters" filter toggle is on, a third audit column is conditionally appended:

| Column header | Fields rendered |
|---|---|
| Deleted By | `deleted_at` + `deleted_by_name` (text in destructive red); shows `-` for non-deleted rows |

All timestamps are formatted in the browser's local timezone using JS `Date` — no UTC offset indicator is displayed. This matches the audit-column format used across all Platform SPA list pages.

## 3. `ClusterEdit` — create mode (`/clusters/new`)

In create mode (`isNew = true`) the page title is "Add Cluster" and the subtitle is "Create a new cluster". The page renders a single **Cluster details** card (no scrollspy nav, no hero, no Branding/BU/Users sections). There is no Edit button in the header — the form is immediately editable, using the older `ClusterIdentityFields` component (not `InlineField`/`DetailsSection`).

The form contains five fields from `ClusterFormData`:

| Field | Input type | Required | Notes |
|---|---|---|---|
| `code` | text | Yes | Cluster short identifier. **Editable in create mode** — see §4.1 for edit-mode behaviour |
| `alias_name` | text | No | Max 3 characters (`maxLength={3}`). Used in compact UI surfaces |
| `name` | text | Yes | Full display name |
| `max_license_bu` | number | No | Leave blank for unlimited; placeholder text "Unlimited" |
| `is_active` | checkbox | — | Defaults to `true` |

Branding is **not** part of the create form — the former `logo_url` text field is gone, and the logo/avatar upload section (§4.2) only appears once the cluster exists, because the upload endpoints need a cluster id.

Submit button label: **Create Cluster**. On submit, calls `POST /api-system/clusters`. On success, if the response includes an `id`, navigates to `/clusters/:id/edit` with `{ replace: true }` — a registered route, so a successful create now lands the operator directly on the new cluster's edit page. (Earlier behaviour navigated to `/clusters/:id` without the `/edit` suffix, an unregistered route that bounced through the catch-all to the Dashboard — that gap has been fixed.) If no `id` is returned, navigates to `/clusters`. **Cancel** navigates to `/clusters` without an API call.

## 4. `ClusterEdit` — view/edit mode (`/clusters/:id/edit`)

There is no page-level view/edit mode split any more. The page computes `canEdit = !isNew && hasPermission('cluster.update', { clusterId: id })` once and renders every section unconditionally — the same JSX tree serves both a read-only viewer and an editor, with individual controls disabled/hidden per `canEdit`. `PageHeader` shows the cluster's name as the title and "Cluster details" as the subtitle, with a **back-to-list** button; there is no header Edit button.

The layout is `lg:grid-cols-[200px_1fr]`: a sticky `ClusterEditNav` (§1) occupies the narrow left column, and the right column stacks five `id`-anchored `<section>`s in a single flow — **Overview**, **Details**, **Branding**, **Business Units**, **Users** — each inside its own `Card`. A dedicated loading skeleton mirrors this exact stack (header → hero → details → BU table → users table) so nothing reflows once data arrives, and a not-found `EmptyState` gates the whole shell when the id doesn't resolve to a live record (§1).

### 4.1 Overview section — `ClusterHero`

A read-first identity + capacity card with **no title and no actions** (the page's `PageHeader` owns those). It shows the logo (or a code-initials placeholder) and avatar (or a name-initial placeholder) side by side, the `code`/`alias_name` chips and an Active/Inactive badge, "Tenant group" plus Created/Updated audit lines (date-only, no time), and — in a shaded footer strip — two `CapacityGauge` bars: **Business units** (`used/cap`, active/inactive counts, licences-free note) and **Users** (`used/cap`, licences-free note, or "no per-BU user cap set" when no BU in the cluster has `max_license_users`).

### 4.2 Details section

Identity + licensing as an **edit-in-place document** (`DetailsSection` + `InlineField`) — not a form with Save/Cancel of its own. Each of the five `ClusterFormData` fields (`code`, `name`, `alias_name`, `max_license_bu`, `is_active`) renders as a compact read-mode row that turns into an inline editor on click; `Enter`/blur commits into `formData`, `Escape` reverts the field to its last-committed value. Every field carries `disabled={!canEdit}` — a session without the `cluster.update` grant for this cluster sees the same rows but cannot open any editor. **`code` remains editable** here (no `disabled={!isNew}` guard, unlike `username` on the user form) — a code change that collides with the `@@unique([code, name, deleted_at])` constraint is rejected by the API, not pre-validated client-side.

There is no per-section Save button: committing a field only updates local `formData`. The page-wide **Save Changes** action lives in the sticky bottom bar (§4.5), which appears once `formData` differs from `savedFormData` and calls `PUT /api-system/clusters/:id` with the current `doc_version` attached.

### 4.3 Branding section

Renders two `BrandingImageUpload` controls side by side when `canEdit` is true: **Logo** with `shape="rect"` and **Avatar** with `shape="square"`, each showing the current image from its presigned URL (`cluster.logo?.url` / `cluster.avatar?.url`) or an empty placeholder, labelled **Upload**/**Replace** per control (replace semantics — no remove/clear affordance). The component validates client-side before uploading: accepted types JPEG/PNG/WebP, max 5 MB — failures surface as an error toast without an API call. When `canEdit` is false the section instead renders two plain, non-interactive preview boxes ("No logo"/"No avatar" placeholders) with no upload affordance at all.

On file selection the page calls the dedicated multipart endpoint — `POST /api-system/clusters/:id/logo` (form field `logo`) or `POST /api-system/clusters/:id/avatar` (form field `avatar`) — and sets the preview from the returned presigned `url` directly, deliberately *not* re-fetching the cluster so unsaved Details edits are not clobbered. Uploads are independent of the sticky Save bar: an uploaded image is persisted immediately even if the operator then discards the Details changes via Cancel.

### 4.4 Business Units section

Lists every `tb_business_unit` row whose `cluster_id` matches the current cluster, fetched from `GET /api-system/business-units?perpage=-1` and filtered client-side on `bu.cluster_id === id`. Unlike the earlier plain table, this section now has its own **`TableToolbar`**: a search box (matches `code`/`name`) and **Active**/**Inactive** toggle filters (mutually exclusive), plus sortable **Code**/**Name** column headers (`cycleSort`/`sortRows` — ascending/descending/none). The section header shows loading state or a "`<n>` total · `<n>` active" summary.

The table has columns **Code** (outline badge), **Name**, **Users** (a `CapacityMeter` bar for `parent_bu_id === bu.id` count vs. `bu.max_license_users`), **Status** (Active/Inactive badge), and a right-aligned **Edit** icon button (navigates to `/business-units/:buId/edit`). Toolbar controls: a **Refresh** icon button (re-calls `onRefresh`) and an **Add** button — inside `<Can permission="cluster.create">` — that navigates to `/business-units/new?cluster_id=<id>` ([business-units](/en/platform/business-units)), disabled with a "License limit reached (N/M)" title when `businessUnits.length >= max_license_bu`. There is no Remove/Unlink button on BU rows and no in-place BU create dialog, same as before.

### 4.5 Users section

Lists `tb_cluster_user` rows for this cluster (`useClusterUsers` hook, `GET /api-system/user/clusters/:id`), sorted by display name then email. Like Business Units, it now has its own `TableToolbar` (search across name/email/username, Active/Inactive filters).

Columns: an optional leading **checkbox** column (only rendered `canEdit`), **Name** (plain text — no longer a clickable link; there is no per-user edit dialog any more, see below), **Email**, **Parent Business Unit** — an **inline-editable** `InlineCell` select (badge display `code - name` when set, disabled when `!canEdit`), **Role** — also an inline-editable `InlineCell` select (`admin`/`user`, plain text display), a centered Active/Inactive **Status** badge, and (when `canEdit`) a right-aligned **Remove** (Trash) icon button per row. **The former "Edit Cluster User" dialog no longer exists** — Parent Business Unit and Role are edited directly in the table cell (`PUT /api-system/user/clusters/:clusterUserId` fires per commit, with an optimistic local update that rolls back on failure) rather than through a modal. The section header shows a **Refresh** icon and, when `canEdit`, an **Add User** button (opens the Add User to Cluster dialog, §5.1).

When `canEdit` is true, checkbox multi-select drives a **bulk-action bar**: a "Move target BU…" select plus a `BulkActionBar` showing the selected count and two actions — **Remove** (destructive, opens the bulk confirm, §5.3) and **Move to BU** (disabled until a target BU is chosen; calls `PUT` once per selected row via a sequential fan-out that never aborts on a single failure, then shows an aggregate "`<n>` updated" / "`<n>` updated, `<n>` failed" toast). Selection resets whenever the search term or Active/Inactive filter changes.

### 4.6 Sticky "Unsaved changes" bar

Replaces the old in-card Save Changes/Cancel buttons. Appears fixed to the bottom of the viewport whenever `formData !== savedFormData` (Details-section edits only — Branding uploads and Users/BU actions are independently persisted and don't trigger it): a pulsing dot, "Unsaved changes" label, and **Cancel**/**Save Changes** buttons. `Ctrl/⌘+S` triggers Save and `Escape` triggers Cancel via the shared `useGlobalShortcuts` hook, matching the same shortcuts used on other A4 edit pages.

- **Save Changes** → `PUT /api-system/clusters/:id` with the loaded `doc_version` attached (when present). On success, `fetchCluster()` re-fetches the record (refreshing `doc_version` too). On a `409` version conflict, shows a "This record was changed by someone else" toast and reloads the record instead of retrying the stale write.
- **Cancel** → restores `formData` from `savedFormData` and clears any pending field errors. No API call.
- **Unsaved changes guard**: the `useUnsavedChanges` hook still fires if the operator attempts to navigate away while `hasChanges` is true.

## 5. Dialogs

### 5.1 Add User to Cluster dialog

Triggered by the **Add User** button in the Users section header on `/clusters/:id/edit` (only rendered when `canEdit`).

The dialog searches the global user pool ([users](/en/platform/users), `GET /api-system/user` via `userService.getAll`) with a 400 ms debounced search input. Search fields: `username`, `email`, `firstname`, `lastname`. Results are paginated at 10 per page with infinite-scroll load-more (triggered by scrolling to within 40 px of the bottom of the results list). Users already in this cluster are excluded from the results (`availableUsers` filter). Selecting a user shows a confirmation card with `username`, `email`, and full name; clicking the X on that card deselects and returns to the search list.

Fields after a user is selected:
- **Cluster Role** — select populated from `CLUSTER_ROLES = ['admin', 'user']`. Default: `user`.
- **Business Unit** — select populated from the cluster's current BUs (all BUs, not filtered by active status). Shows `code - name (count/max users)` per option; options are disabled when their BU is at `max_license_users` limit. Empty default: "Select business unit" (the BU assignment is optional).

The **Add User** button is disabled when: no user is selected, the request is in flight (`addingUser`), or the selected BU is at its user license limit. On submit, calls `POST /api-system/user/clusters` with body `{ user_id, cluster_id, role, is_active: true }` (plus `parent_bu_id` if a BU was selected). On success, dialog closes, a toast confirms, and `fetchClusterUsers()` re-fetches.

### 5.2 Remove Cluster User confirm (single)

Triggered by the row-level **Trash** icon button in the Users section (§4.5), rendered only when `canEdit`.

Uses the shared `ConfirmDialog` component — a simple Yes/No confirm (no typed confirmation required). Title: "Remove User from Cluster". Description: `Remove "<display name>" from this cluster?` where the display name is resolved from `userInfo` first/middle/last, falling back to `name` then `email` (no `username` fallback step).

On confirm, calls `DELETE /api-system/user/clusters/:clusterUserId` using the `tb_cluster_user.id` field returned by the cluster users endpoint. On success, toast confirms and `fetchClusterUsers()` re-fetches.

### 5.3 Remove selected users confirm (bulk)

Triggered by the **Remove** bulk action in the Users section's `BulkActionBar` (§4.5). Title: "Remove selected users". Description: `Remove <n> user(s) from this cluster?`. On confirm, fans out one `DELETE` per selected id (continuing past individual failures), then shows an aggregate result toast and clears the selection.

### 5.4 Soft Delete Cluster confirm

Triggered by the **Delete** row action in `ClusterManagement` — which itself renders only inside `<Can permission="cluster.delete" clusterId={row.original.id}>` (§2.4), and only opens once the client-side deletion guard (bu_count check) has passed.

Uses the shared `ConfirmDialog` — a simple Yes/No confirm (no typed confirmation required). Title: "Delete Cluster". Description: "Are you sure you want to delete this cluster? This action cannot be undone." Confirm button label: "Delete" (destructive variant).

On confirm, calls `DELETE /api-system/clusters/:id` (soft delete — sets `deleted_at`). No hard-delete dialog exists for clusters in the Platform SPA.

## 6. Persisted UI state

The list page writes 6 keys to `localStorage` so that filter and pagination state survives page reloads. The `ClusterEdit` page writes no `localStorage` keys.

| Key | Stored type | Persists |
|---|---|---|
| `search_clusters` | string | Current search term |
| `page_clusters` | number (string) | Current page number (reset to `1` on filter or search changes) |
| `perpage_clusters` | number (string) | Rows per page |
| `sort_clusters` | string | Current sort column/direction (default `created_at:desc`) |
| `filters_clusters` | JSON array | Active status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filter_clusters_deleted` | JSON boolean | "Show soft-deleted clusters" toggle state (default `false`) |

Note: the clusters list persists no filter keys beyond the status array and the deleted toggle — there is no role filter group on this page. (The users list once persisted a role filter, but that disappeared along with the role-enum model; see [rbac](/en/platform/rbac) §5.)

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan. **Note (2026-07-29):** the edit page's layout changed from a 3-column card grid to a single-column scrollspy document since this page was last captured-for — any future capture should target the new `ClusterEditNav`/`ClusterHero`/edit-in-place layout described in §4, not the earlier grid.

## 8. References

- `../carmen-platform/src/App.tsx` — three cluster routes with `requiredPermission` keys (`cluster.read`/`cluster.create`/`cluster.update`); the create-navigation quirk documented in a prior sync (§3) has been fixed — the catch-all now serves a dedicated 404 page (`NotFound.tsx`) rather than silently redirecting to Landing.
- `../carmen-platform/src/pages/ClusterManagement.tsx` — list page: Fleet Capacity strip, filters (Status + Deleted), header actions (Export, `<Can>`-gated Add Cluster), deletion guard (blocks delete when `bu_count > 0`), `<Can>`-gated row action menu (Edit / Delete soft), nested-audit column mapping, 6 `localStorage` keys.
- `../carmen-platform/src/pages/ClusterEdit.tsx` — create/edit-in-place orchestrator page: scrollspy layout, `canEdit` gating (no page-level Edit toggle), `doc_version` optimistic locking, Add User dialog, license-cap logic.
- `../carmen-platform/src/pages/clusterManagement/{ClusterHero,FleetCapacity,CapacityGauge,CapacityMeter,ClusterIdentityFields}.tsx`, `../carmen-platform/src/utils/capacity.ts` — hero card, fleet-wide and per-row capacity gauges, and the create-mode-only identity form.
- `../carmen-platform/src/pages/clusterEdit/{ClusterEditNav,useScrollSpy,useClusterUsers,TableToolbar,BulkActionBar,InlineCell,tableSort}.ts(x)` and `sections/{DetailsSection,BrandingSection,BusinessUnitsSection,UsersSection}.tsx` — scrollspy nav, per-section components, bulk-action and inline-edit primitives shared with other A4 edit pages.
- `../carmen-platform/src/pages/businessUnitEdit/InlineField.tsx` — shared click-to-edit field control reused by `DetailsSection` (also used by the Business Units edit page).
- `../carmen-platform/src/utils/docVersion.ts` — `getDocVersion`/`isVersionConflict`/`notifyVersionConflict` optimistic-lock helpers.
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — shared upload control: type/size validation, rect/square preview shapes, Upload/Replace button states.
- `../carmen-platform/src/services/clusterService.ts` — API surface: `GET/POST /api-system/clusters`, `PUT/DELETE /api-system/clusters/:id`, `GET /api-system/user/clusters/:clusterId`, `POST /api-system/clusters/:id/logo`, `POST /api-system/clusters/:id/avatar`.
- Cross-links: [clusters](/en/platform/clusters) (module landing), [rbac](/en/platform/rbac) (permission model behind every gate on these screens), [users](/en/platform/users) (global user pool searched by Add User dialog; `tb_cluster_user` doc), [business-units](/en/platform/business-units) (Add BU navigate-to-new flow; `cluster_id` FK), [Data Model](./data-model.md), [Permissions](./permissions.md).
