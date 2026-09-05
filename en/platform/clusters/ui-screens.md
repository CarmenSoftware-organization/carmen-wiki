---
title: Cluster — UI Screens
description: ClusterManagement (list) and ClusterEdit (create/view/edit) screens — the tabbed plate layout, licensing tab, filters, dialogs, and persisted state.
published: true
date: 2026-09-05T14:00:00.000Z
tags: book/platform, clusters, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — UI Screens

> **At a Glance**
> **Screens:** `ClusterManagement` (list, `/clusters`) &nbsp;·&nbsp; `ClusterEdit` create (`/clusters/new`) &nbsp;·&nbsp; `ClusterEdit` view/edit (`/clusters/:id/edit`) &nbsp;·&nbsp; **Edit layout (rewritten 2026-08-23, commit `69027b9`):** an always-visible `ClusterPlate` header (identity, branding, status, two licence rails) plus a 3-tab `TabStrip` — **Licensing** (default), **Business Units**, **Users** — replacing the earlier 5-section scrollspy document (Overview/Details/Branding/Business Units/Users) &nbsp;·&nbsp; **Dialogs:** Add User to Cluster · Remove Cluster User confirm (single + bulk) · Soft Delete Cluster confirm &nbsp;·&nbsp; **Access:** route guards `cluster.read` / `cluster.create` / `cluster.update`, each also gated by the `clusters` feature flag; Add/Edit/Delete buttons behind `<Can>` gates (see [Permissions](/en/platform/clusters/permissions)) &nbsp;·&nbsp; **Persisted UI state:** 7 `localStorage` keys on the list page &nbsp;·&nbsp; **Concurrency:** `doc_version` optimistic lock on save &nbsp;·&nbsp; **BU quota is licence-based now** — the create form issues the cluster's first BU-quota licence; ongoing quota purchases happen in the **licenses** module, not on this page

## 1. Overview

The Platform SPA follows a two-screen pattern for cluster management: a list page (`ClusterManagement`) with a server-side `DataTable`, a slide-over filters Sheet, and a Fleet Capacity summary band; and an edit page (`ClusterEdit`) built around a persistent identity **plate** (`ClusterPlate`) with a 3-tab body beneath it. Both screens are registered under the `/clusters` route prefix and are guarded by `requiredPermission` keys — `cluster.read` (list), `cluster.create` (create), `cluster.update` (edit) — plus a `feature="clusters"` flag check on the same `PrivateRoute` (see [Permissions](/en/platform/clusters/permissions) §2).

**The edit page's layout changed twice since this page was last fully verified (2026-07-29):** first from a 3-column card grid to a single-column scrollspy document, then (2026-08-23, `69027b9`) from that scrollspy document to the current plate-plus-tabs shape. There is no `ClusterEditNav`/`useScrollSpy` on this page any more — those files still exist on disk but their only remaining caller is `ClusterProfile.tsx`, the **cluster-admin** persona's own cluster page (a different module; see [business-units](/en/platform/business-units) and the source map's `cluster-admin` row). Likewise `DetailsSection.tsx`/`BrandingSection.tsx` (the old scrollspy sections) are now used only by that cluster-admin page — `ClusterEdit.tsx` itself no longer imports either.

`ClusterPlate` sits above the tabs and never disappears when you switch tabs: logo/avatar upload controls, the editable name/status/code/alias identity, audit metadata, and two **licence rails** (Business Units, Seats) drawn as `AllocationTicks` — one tick per licence, not a percentage bar. Below the plate, a sticky `TabStrip` (pinned under the app header once the plate scrolls out of view, at which point a compact `used/cap` readout fades in beside the tabs) switches between three tab bodies: **Licensing** (default — a read-only subscription summary plus a link to the License Center), **Business Units**, and **Users**. The active tab is reflected in the URL as `?tab=business-units` / `?tab=users` (via `replace`, so switching tabs does not add browser-history entries); the plain URL with no `?tab=` means Licensing. There is no separate "Details"/"Branding"/"Overview" tab any more — those fields now live directly in the plate header, always visible regardless of which tab is open.

In create mode (`isNew = true`) the page instead renders a two-column layout: a live-updating `ClusterDraftPlate` preview (sticky, right column on `lg`+) beside a two-card form (`ClusterCreateForm`) — Identity (code/alias/name) and **First Quota Licence** (the BU count and expiry that become the cluster's opening `tb_cluster_license` row). See §3.

A dedicated **not-found** state renders when `GET /api-system/clusters/:id` returns no record (bad or deleted id): an `EmptyState` card with a "Back to clusters" button, gating the entire plate/tab shell so it never renders over blank data.

## 2. `ClusterManagement` — list page (`/clusters`)

### 2.1 Layout

The page renders inside `Layout` with a `PageHeader` (title "Cluster Management" / subtitle) and an actions row containing **Export** and **Add Cluster** buttons. Below the header sits the **Fleet Capacity** band (§2.1a), then a search-and-filters row: a debounced (400 ms) search `Input` on the left, and a **Filters** Sheet trigger on the right (shows an active-filter count badge when any filter is set). Active filter chips appear as a strip below the search row when any filter is active. The main content area is a `DataTable` in server-side mode with pagination, with the first three columns frozen (sticky) on horizontal scroll (`stickyLeftColumns={3}`).

Columns in order: **Code** (a muted, monospace link — no longer the blue link it once was; only **Name** now carries the link colour, to avoid two same-meaning coloured marks per row), **Name** (a small `BrandMark` avatar/initials chip + the primary link, with a red `Deleted` badge appended when `deleted_at` is non-null — tooltip "Deleted by &lt;name&gt;" when `deleted_by_name` is present), **Status** (a small dot + muted text for Active, bold text for Inactive — colour is reserved for the abnormal state, not a filled badge on every row), **Business Units** (`bu_count`/`bu` — a `CapacityMeter` bar, `finite` mode: `bu_used / bu_cap`, `0` cap reads as zero not infinite, sortable — sorts by `bu_used`, resolved server-side against a view join, not the cap), **Quota Expires** (`bu_cap_end_date` — sortable, NULLS LAST both directions; shows "No expiry" for the perpetual sentinel, "—" when there is no covering licence at all, else a plain `YYYY-MM-DD` date), **Users** (`user_count` — a `CapacityMeter` bar against `total_max_license_users`, `null`/absent renders `∞`, sortable by `users_count`), then the shared `auditColumns()` (Created; Updated, suppressed when equal to Created — both rendered one visual weight lighter than Name/Users), and conditionally a **Deleted By** column (only when the "Show soft-deleted" filter is on). The final column is a narrow icon-button `DropdownMenu` for row actions.

**There is no dedicated logo-thumbnail column any more** (removed when the Fleet Capacity band was introduced, before the 2026-07-29 sync) — but the Name cell itself now carries a small `BrandMark` avatar next to the link, added alongside the current column set. A cluster's full-size logo/avatar is visible on its own edit page (the `ClusterPlate` header) and the Branding upload controls there.

**Row-level colour is reserved for anomalies.** Both `CapacityMeter` bars (Business Units, Users) render a neutral grey fill at normal headroom, amber at ≥ 90% of a finite cap ("NEAR" tag appended inline), and red at/over 100% — matching the same `ok`/`warn`/`over` thresholds used everywhere licence capacity is drawn (`../carmen-platform/src/utils/capacity.ts`, `NEAR = 0.9`).

### 2.1a Fleet Capacity band

A `FleetCapacity` card sits between the header and the search row, reading a **dedicated, unfiltered summary endpoint** — `clusterService.getFleetSummary()` → `GET /api-system/clusters/summary` — rather than any locally-fetched page of rows. This endpoint takes no `search`/`advance` params, so the band's numbers always describe the whole fleet and never shift as the operator types into the search box (a bug fixed by commit `42a0fac`, "แถบ Fleet capacity เลิกเดินตามช่องค้นหา"). It shows:

- Two `CapacityGauge` bars — **Business units** (`finite` mode, fleet-wide `bu.used`/`bu.cap`) and **Users** (`null`-cap-means-uncapped mode, fleet-wide `users.used`/`users.cap`) — each with an "N clusters uncapped, using M" note when applicable.
- Four plain stats: **Clusters** (total), **Active**, **Near limit** (amber, count of clusters at ≥ 90% of either cap), and **Quota expiring** (amber, count of clusters whose *winning BU-quota licence* expires within 30 days — a distinct dimension from Near limit, and from `bu_cap = 0`, which means "no licence at all", not "expiring soon"; seat/subscription expiry is not counted here).
- The **Quota expiring** stat is clickable when non-zero: clicking it toggles a `bu_quota_expiring_soon` advance-filter marker (resolved entirely server-side against the view `v_cluster_bu_cap` — the frontend holds no copy of the "which licence wins, how many days left" rule) and highlights the stat as active. This filter, like the others, is persisted to `localStorage` (`filter_clusters_quota_expiring`) and cleared by **Clear All Filters**.
- **Failure handling:** a first failed load shows "Capacity unavailable"; a load that fails *after* a prior success keeps the stale numbers visible (dimmed, with a "couldn't refresh" cue) rather than either freezing on a spinner or silently pretending they're current (fixed by commit `f7944bc`).

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet. Two filter groups are wired:

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). The two buttons may be toggled independently; when both are active or both are off, no `is_active` constraint is applied. A **Clear** link appears in the group header when any status value is selected.
- **Deleted** — a checkbox labelled "Show soft-deleted clusters". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface with a red `Deleted` badge in the `name` cell, and the conditional `Deleted By` audit column is appended to the `DataTable`.

The **Quota expiring** filter (§2.1a) is not in this Sheet — it is toggled only from the Fleet Capacity band's own stat — but it still counts toward the active-filter badge and chip strip, and **Clear All Filters** clears it too (a deliberate consistency fix: what's on screen must equal what's sent to the API).

When any filter is active a **Clear All Filters** button appears at the bottom of the Sheet, and active filter chips appear in the strip below the search row, each with an inline remove button.

### 2.3 Header actions

- **Export** — client-side CSV export (`generateCSV`/`downloadCSV`). Columns: `Code`, `Name`, `Alias`, `Status`, **`BU Quota`** (`bu_cap`), **`Quota Expires`** (`bu_cap_end_date`, perpetual sentinel converted to "No expiry" text before export — never a raw 2099 date), `Users` (`users_count`), `Max Licensed Users` (`total_max_license_users`), `Created`/`Created By`, `Updated`/`Updated By`. File name: `clusters-<YYYY-MM-DD>.csv`. Disabled while loading or when the table is empty. **`Max Licensed BUs`/`max_license_bu` is no longer a column** — the ledger-derived `bu_cap`/`bu_cap_end_date` pair replaces it.
- **Add Cluster** — navigates to `/clusters/new`. Wrapped in `<Can permission="cluster.create">`. The **empty-state** Add Cluster button (shown when the table has no rows) is **also** wrapped in `<Can permission="cluster.create">` (`ClusterManagement.tsx` lines 670–671) — an earlier version of this page stated the empty-state button was ungated and reachable by a `cluster.read`-only session; it is not, and that session never sees it. The `cluster.create` route guard on `/clusters/new` remains a second layer regardless.

There is no Hard Delete action anywhere in cluster management — the row action menu contains only Edit, View History, and Delete (soft). No hard-delete endpoint is called from the clusters UI.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with up to three items, each behind a **cluster-scoped `<Can>` gate** (`clusterId={row.original.id}` — see [Permissions](/en/platform/clusters/permissions) §3):

- **Edit** — `<Can permission="cluster.update" clusterId={row.original.id}>`; navigates to `/clusters/:id/edit`.
- **View History** — `<Can permission="activity_log.read" clusterId={row.original.id}>` — **new since the last sync**. Opens a shared `ActivityTrailSheet` (one instance for the whole table, its `entityId` swapped per row via `activityTrail.openFor(id)` rather than mounting per-row) showing this cluster's change history. Change history recording only started `2026-08-31` (`AUDIT_RECORDING_STARTED_ON_PHASE_2` — a cluster created before that date shows an empty timeline rather than implying "never edited").
- **Delete** — `<Can permission="cluster.delete" clusterId={row.original.id}>`; calls `handleDelete(id)`. If the cluster's `bu_count > 0`, the click is blocked client-side with an error toast ("Can't delete `<name>`… it still has N business unit(s)…") and **no** `ConfirmDialog` opens — deleting a cluster does not cascade to its BUs on the backend. Otherwise it opens the Soft Delete Cluster `ConfirmDialog` (§5.4); on confirm, `DELETE /api-system/clusters/:id` (soft delete).

A session whose grants cover none of the three keys for a given cluster sees an empty dropdown for that row.

### 2.5 Audit columns

Unchanged from the prior sync: the API's nested `audit` object is read through the shared `normalizeAudit()` helper (`../carmen-platform/src/utils/audit.ts`), tolerating both the nested and an older flat shape (flat wins when present). Created and Updated columns render `at` + `by_name`; Updated is suppressed when it equals Created. A third **Deleted By** column is appended only when the "Show soft-deleted clusters" filter is on. All timestamps are formatted in the browser's local timezone.

## 3. `ClusterEdit` — create mode (`/clusters/new`)

**Rewritten** (commit `50386b9`, "แผ่นป้ายร่างพรีวิวสด + แยกฟอร์มเป็น 2 section") to require the cluster's opening BU-quota licence at creation time, and to show a live preview beside the form rather than a header banner above it.

Layout: a `BackLink` to the list, then a two-column grid from `lg` up — the form on the left (DOM order first, so it stacks above the preview on narrower screens), a sticky `ClusterDraftPlate` preview on the right. The preview draws the cluster's `BrandMark` initials (from `code`, falling back to `name` while `code` is invalid), the name/status/code/alias exactly as typed, and — instead of the edit plate's two licence rails — a single **Business units** tick-strip showing the `licensed_bus` count as issued-but-unused licences (neutral grey ticks, not the "in use" green), with a note stating when it expires or "Never expires" or (while the field is empty) "No quota yet".

The form is two cards:

| Card | Fields | Required | Notes |
|---|---|---|---|
| **Identity** | `code` (text, mono), `alias_name` (text, max 3 chars), `name` (text) | `code`*, `name`* | Same three fields as before; laid out on one row now rather than stacked |
| **First Quota Licence** | `licensed_bus` (number, min 1), `license_end_date` (date, min = today), **Never expires** (checkbox) | `licensed_bus`*, `license_end_date`* unless "Never expires" is checked | **New.** This becomes the cluster's first `tb_cluster_license` row — see [Data Model](/en/platform/clusters/data-model) §2.4. The date input stays mounted and merely disables when "Never expires" is checked (so ticking the box does not yank the field out from under the pointer) |

There is **no `max_license_bu` field, and no `is_active` checkbox, on the create form any more** — status defaults to Active and is set from the draft plate's `StatusToggle`, not a form checkbox. Branding is still not part of the create form — the upload endpoints need a cluster id, so the logo/avatar controls only appear once the record exists.

On submit, the page builds the payload as `{ code, name, alias_name, is_active, initial_license: { licensed_bus: Number(licensed_bus), end_date: <PERPETUAL_END_DATE or the chosen date, end-of-day> } }` and calls `POST /api-system/clusters`. Submit button label: **Create Cluster**. On success, if the response includes an `id`, navigates to `/clusters/:id/edit` with `{ replace: true }`. If no `id` is returned, navigates to `/clusters`. **Cancel** (a ghost-styled button, not outline — the page has exactly one accent) navigates to `/clusters` without an API call.

## 4. `ClusterEdit` — view/edit mode (`/clusters/:id/edit`)

`canEdit = !isNew && hasPermission('cluster.update', { clusterId: id })`, computed once and passed down; every field/action in the plate and every tab body is disabled or hidden per this single boolean — there is still no page-level Edit toggle. `PageHeader`/back-link behaviour is folded into the plate itself now (§4.1) rather than a separate header row; a `headerAction` slot next to the back-link carries the **View History** button (`<Can permission="activity_log.read" clusterId={id}>`, same `ActivityTrailSheet` pattern as the list page, using the fixed date `2026-08-31` as this cluster's own recording-start constant).

### 4.1 `ClusterPlate` — the persistent identity header

Replaces the prior sync's four stacked surfaces (hero card, Details section, Branding section, and the scrollspy nav) with one card that never leaves the screen while a tab is open:

- **Left/main area:** compact logo (`shape="rect"`) and avatar (`shape="square"`) upload controls side by side (via `BrandingImageUpload`, `compact` mode) — clicking either opens the file picker directly; there is no separate "Branding" tab any more. Beside the marks: the cluster **name** as an inline-editable `<h1>` (click-to-edit, commits on blur/Enter, reverts on Escape — via the shared `HeroName` control), a `StatusToggle` badge beside it (outside the heading, so "Active"/"Inactive" is never folded into the `<h1>`'s accessible name) that toggles `is_active` directly on click, then a row of two `PlateField` chips for **Code**\* and **Alias** (same click-to-edit behaviour, each showing its own inline validation error), and an `AuditMeta` line (Created/Updated, actor + relative time).
- **Branding upload behaviour** (`BrandingImageUpload.tsx`, still accurate today — the last sync's coverage of this was compressed away and is restored here): client-side `validate()` rejects a file whose MIME type is not `image/jpeg`/`image/png`/`image/webp` (the `DEFAULT_ACCEPT` list, line 10) or whose size exceeds `maxSizeMB` (default `5`, line 40; checked at line 65 as `file.size > maxSizeMB * 1024 * 1024`) — a rejection shows an error toast and makes **no API call at all**; only a file that passes both checks reaches `onUpload`. On a successful upload, `ClusterEdit.tsx`'s `handleUploadLogo`/`handleUploadAvatar` set `logoUrl`/`avatarUrl` directly from the endpoint's returned presigned URL and **deliberately do not re-fetch the cluster record** — the handlers' own comment states this is "so we don't refetch (which would clobber unsaved form edits)," i.e. any in-progress, uncommitted identity edit on the plate survives a branding upload. When `canEdit` is `false`, the control renders only its preview with no button/file-input wrapper at all (view-only, not clickable) — for the avatar (square) that preview falls back to a `BrandMark` initials circle when no image is set, and for the logo (rect) it falls back to a dashed-border placeholder box with a muted image icon; neither case shows literal "No logo"/"No avatar" text (that wording belonged to an earlier, non-compact version of this control that this page no longer uses).
- **Right/muted band** (stacks below on narrower screens, sits beside on `lg`+): two **licence rails** — **Business units** and **Seats** — each drawn via `AllocationTicks`: one tick per licence rather than a percentage fill, because "5 of 5" is something you can see is full at a glance, not something you compute from a 100% bar. The Business units rail is always finite (`bu_cap`, `bu_used`, active/inactive sub-counts); the Seats rail can show `∞` when `total_max_license_users` is `null`/unset.
- **Sticky compact strip:** once the plate scrolls out from under the app header, a thin bar carrying just the `TabStrip` (still interactive) plus a fading-in `bu.used/bu.cap` · `users.used/users.cap` readout pins below the header — so the licence headroom stays visible without permanently eating a third of the viewport with the full plate.

All Details/Branding fields that the prior 5-section scrollspy exposed as separate sections are here now: there is no dedicated "Details" or "Branding" tab body.

### 4.2 Licensing tab (default, `?tab=` omitted)

A single card titled "Subscriptions" with a **Manage licences** button (outline, links to `/licenses/:id#quota` — the License Center's BU-quota anchor, out of this module's scope) in its header, and below it an embedded, read-only `SubscriptionCard` (`embedded` prop — no card chrome of its own, folded into this one card). `SubscriptionCard` renders **nothing at all**, and fires no request, for a session without `subscription.read` — the parent hides the border/empty space entirely (`empty:hidden`) rather than showing a hairline over blank content. There is no BU-quota edit UI on this page any more — purchasing or cancelling a BU-quota licence happens only in the License Center.

### 4.3 Business Units tab

A client-side-filtered/sorted table (`TableToolbar` search + Active/Inactive toggle filters, `cycleSort` on **Code**/**Name** headers) over every `tb_business_unit` row whose `cluster_id` matches this cluster (fetched via `GET /api-system/business-units?perpage=-1`, filtered client-side). Columns: **Code** (outline badge), **Name** (with an "Over limit" red badge appended when the BU's rank — per `../carmen-platform/src/utils/businessUnitRank.ts`, matching `v_cluster_bu_quota`'s `is_hq DESC, created_at ASC, id ASC` — exceeds the cluster's `bu_cap`; plus a compact audit line showing the latest actor/verb), **Status** (muted text for Active, a badge for Inactive), and a right-aligned **Edit** icon (navigates to `/business-units/:buId/edit`).

**There is no per-BU Users/seat column any more** — the seat pool is cluster-wide now (§ Data Model §2.5), not a per-BU cap, so there is nothing meaningful to meter per row here. A note above the table reports how many BUs are currently over the quota line when `overLimitCount > 0`. Toolbar actions: a **Refresh** icon and an **Add** button (`<Can permission="cluster.create">`, unscoped) that navigates to `/business-units/new?cluster_id=<id>`, disabled with a "License limit reached (N/M)" tooltip once `businessUnits.length >= bu_cap`. There is still no Remove/Unlink button on BU rows.

### 4.4 Users tab

A client-side-filtered table (same `TableToolbar` pattern: search across name/email/username, Active/Inactive filters) over `tb_cluster_user` rows for this cluster (`useClusterUsers` hook, `GET /api-system/user/clusters/:id`), sorted by display name then email. Columns: an optional leading **checkbox** (only rendered when `canEdit`), **Name** (with email folded onto a second line — there is no separate Email column), **Role** (an inline-editable `InlineCell` select, `admin`/`user`, committing via `PUT /api-system/user/clusters/:clusterUserId` per keystroke-equivalent change with an optimistic update that rolls back on failure), a centered **Status** badge, and (when `canEdit`) a right-aligned **Remove** (Trash) icon per row.

**There is no Parent Business Unit column, select, or bulk "Move to BU" action any more** — `tb_cluster_user.parent_bu_id` was removed from both the schema and the UI (see [Data Model](/en/platform/clusters/data-model) §2.2). The bulk-action bar (visible only when `canEdit` and at least one row is selected) now offers a single action: **Remove** (destructive, opens the bulk confirm, §5.3). The header offers a **Refresh** icon and, when `canEdit`, an **Add User** button (opens the Add User to Cluster dialog, §5.1).

### 4.5 Sticky "Unsaved changes" bar

Appears fixed to the bottom of the viewport (offset by the sidebar width on `md`+/`lg`+, an iOS-glass surface since commit `cf5bdc6`) whenever `formData !== savedFormData` — i.e. an uncommitted edit to a `ClusterPlate` identity field (name/status/code/alias). Branding uploads and Business-Units/Users tab actions are independently persisted and never trigger this bar. `Ctrl/⌘+S` triggers **Save Changes** and `Escape` triggers **Cancel** via the shared `useGlobalShortcuts` hook.

- **Save Changes** → `PUT /api-system/clusters/:id` with the loaded `doc_version` attached (when present) — the payload no longer carries any BU-quota field at all, since quota now lives only in the licence ledger. On success, `fetchCluster()` re-fetches the record (refreshing `doc_version`). On a `409` version conflict, shows a "changed by someone else" toast and reloads the record.
- **Cancel** → restores `formData` from `savedFormData` and clears pending field errors. No API call.
- The `useUnsavedChanges` hook still fires if the operator attempts to navigate away while a change is pending.

## 5. Dialogs

### 5.1 Add User to Cluster dialog

Triggered by **Add User** in the Users tab (only rendered when `canEdit`). Searches the global user pool ([users](/en/platform/users), `GET /api-system/user`) with a 400 ms debounced input across `username`/`email`/`firstname`/`lastname`, paginated at 10 per page with infinite-scroll load-more (within 40 px of the bottom). Users already in this cluster are excluded. Selecting a user shows a confirmation card (`username`, `email`, full name); the X on that card deselects.

Fields after selection: **Cluster Role** (select, `admin`/`user`, default `user`). **There is no Business Unit field any more** — the dialog no longer asks which BU a new member belongs to, matching the removal of `parent_bu_id`. The **Add User** button is disabled when no user is selected, a request is in flight, or the cluster's aggregate seat pool is already at its cap (`userCap != null && userUsed >= userCap` — a cluster-wide check now, not per-BU). On submit, `POST /api-system/user/clusters` with body `{ user_id, cluster_id, role, is_active: true }` — no `parent_bu_id` in the payload.

### 5.2 Remove Cluster User confirm (single)

Triggered by the row-level **Trash** icon in the Users tab, rendered only when `canEdit`. A simple Yes/No `ConfirmDialog` (no typed confirmation). Description names the user (first/middle/last, falling back to `name` then `email`). On confirm, `DELETE /api-system/user/clusters/:clusterUserId`; on success, `fetchClusterUsers()` re-fetches.

### 5.3 Remove selected users confirm (bulk)

Triggered by the **Remove** bulk action. Fans out one `DELETE` per selected id (continuing past individual failures), then shows an aggregate result toast and clears the selection.

### 5.4 Soft Delete Cluster confirm

Triggered by the list page's **Delete** row action, and only after the client-side `bu_count > 0` guard has passed. A simple Yes/No `ConfirmDialog`. Confirm calls `DELETE /api-system/clusters/:id` (soft delete). No hard-delete dialog exists for clusters anywhere in the Platform SPA.

## 6. Persisted UI state

The list page writes 7 keys to `localStorage`. The `ClusterEdit` page writes no `localStorage` keys of its own (its tab selection lives in the URL query string instead, §1).

| Key | Stored type | Persists |
|---|---|---|
| `search_clusters` | string | Current search term |
| `page_clusters` | number (string) | Current page number (reset to `1` on filter or search changes) |
| `perpage_clusters` | number (string) | Rows per page |
| `sort_clusters` | string | Current sort column/direction (default `created_at:desc`) |
| `filters_clusters` | JSON array | Active status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filter_clusters_deleted` | JSON boolean | "Show soft-deleted clusters" toggle state (default `false`) |
| `filter_clusters_quota_expiring` | JSON boolean | "Quota expiring" fleet-band stat toggle state (default `false`) — **new since the 2026-07-29 sync** |

## 7. Developer tooling

Both `ClusterManagement` and `ClusterEdit` mount a `DevDebugSheet` (dev-only floating action button) exposing the raw API payloads behind the page — cluster record, business-units list, cluster-users list, and (on the edit page) the activity-history response — labelled with their exact endpoint strings. Not user-facing; useful when QA needs to compare what the API actually returned against what the page rendered.

## 8. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. **Note (2026-09-05):** the edit page's layout changed again since the last capture-note (2026-07-29) — from the single-column scrollspy document to the current plate-plus-3-tab layout (`69027b9`, 2026-08-23), and the create page gained a live side-by-side draft preview (`50386b9`). Any future capture should target `ClusterPlate` + `TabStrip` (Licensing/Business Units/Users) and the two-column create layout described in §3–§4, not either earlier layout.

## 9. References

- `../carmen-platform/src/App.tsx` — three cluster routes with `requiredPermission` keys, each also carrying `feature="clusters"` (see [Permissions](/en/platform/clusters/permissions) §2).
- `../carmen-platform/src/pages/ClusterManagement.tsx` — list page: Fleet Capacity band, filters (Status + Deleted + Quota-expiring), header actions, deletion guard, `<Can>`-gated row action menu (Edit / View History / Delete soft), nested-audit column mapping, 7 `localStorage` keys, `DevDebugSheet`.
- `../carmen-platform/src/pages/ClusterEdit.tsx` — create/edit orchestrator: `ClusterPlate`/`ClusterDraftPlate`, 3-tab body, `doc_version` optimistic locking, Add User dialog (no BU field), Activity Trail header action.
- `../carmen-platform/src/pages/clusterManagement/{FleetCapacity,CapacityGauge,CapacityMeter,ClusterCreateForm,ClusterIdentityFields}.tsx`, `../carmen-platform/src/utils/capacity.ts` — fleet-wide and per-row capacity gauges, the two-card create form.
- `../carmen-platform/src/pages/clusterEdit/{ClusterPlate,ClusterDraftPlate,PlateField,clusterTabs,useClusterUsers,TableToolbar,BulkActionBar,InlineCell,tableSort}.ts(x)` and `sections/{BusinessUnitsSection,UsersSection,SubscriptionCard}.tsx` — the current plate, tab definitions, and per-tab components. `ClusterEditNav.tsx`/`useScrollSpy.ts` and `sections/{DetailsSection,BrandingSection}.tsx` still exist on disk but are no longer imported by this page — their only caller now is the cluster-admin persona's `ClusterProfile.tsx`.
- `../carmen-platform/src/utils/businessUnitRank.ts` — `rankBusinessUnits()`/`countOverLimit()` behind the Business Units tab's "Over limit" badge.
- `../carmen-platform/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail}.tsx`, `constants.ts` — the shared change-history sheet used by both cluster screens.
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — shared upload control (compact mode on the plate; type/size validation, rect/square preview shapes).
- `../carmen-platform/src/services/clusterService.ts` — API surface: `GET/POST /api-system/clusters`, `GET /api-system/clusters/summary`, `PUT/DELETE /api-system/clusters/:id`, `GET /api-system/user/clusters/:clusterId`, `POST /api-system/clusters/:id/logo`, `POST /api-system/clusters/:id/avatar`.
- Cross-links: [clusters](/en/platform/clusters) (module landing), [rbac](/en/platform/rbac) (permission model behind every gate on these screens), [users](/en/platform/users) (global user pool searched by Add User dialog; `tb_cluster_user` doc), [business-units](/en/platform/business-units) (Add BU navigate-to-new flow; `cluster_id` FK), [licenses](/en/platform/licenses) (License Center — BU-quota purchase/cancel UI; forward link, module not yet documented), [Data Model](/en/platform/clusters/data-model), [Permissions](/en/platform/clusters/permissions).

## 10. E2E note

`../carmen-platform-e2e/tests/clusters/` (7 spec files, 904 lines) was last touched 2026-06-26, and its page object `pages/ClusterEditPage.ts` was last touched 2026-08-22 — both **predate** the 2026-08-23 plate/tabs rewrite (`69027b9`) and, in the page object's case, an even earlier UI generation: `ClusterEditPage.editButton`/`expectReadOnlyMode()` assert a page-level "Edit" button and a read-only/edit-mode toggle that has not existed on this page since before the 2026-07-29 scrollspy revision, let alone the current plate. `cluster-create.spec.ts`'s `fillForm()` never fills the now-required `licensed_bus`/`license_end_date` fields, so its "create with minimum required fields" case is likely to stall on the native `required`-field validation rather than reach the save API. Treat this suite as **stale, not current evidence** for `clusters` until it is updated — do not cite it as behavioral confirmation for anything in this module without re-checking against source first.
