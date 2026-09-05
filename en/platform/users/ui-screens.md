---
title: User — UI Screens
description: UserManagement (list) and UserEdit (BU assignment matrix).
published: true
date: 2026-09-05T12:30:00.000Z
tags: book/platform, users, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — UI Screens

> **At a Glance**
> **Screens:** `UserManagement` (list, `/users`) &nbsp;·&nbsp; `UserEdit` create (`/users/new`) &nbsp;·&nbsp; `UserEdit` view/edit (`/users/:id/edit`) &nbsp;·&nbsp; **New since last sync:** collapsed single-cell identity column + asymmetric Status column (list, #219), a 3-section always-visible-only-while-editing account form with required `firstname`/`lastname` (#220), a `GET /api-system/user/summary`-backed Directory strip, a **View History** action (`activity_log.read`, platform-scoped) on both the list row menu and the edit-page hero, `<Can>`-gated Change Password, per-BU-row audit meta in the Access tree &nbsp;·&nbsp; **Dialogs:** Add BU &nbsp;·&nbsp; Change Password &nbsp;·&nbsp; Soft Delete confirm (single + bulk) &nbsp;·&nbsp; Hard Delete typed-confirm (single + bulk random-code) &nbsp;·&nbsp; **Access:** routes guarded `user.read` / `user.create` / `user.update` (+ `feature="users"`); in-page `<Can>` gates on Add (`user.create`), Fetch Keycloak (`user.create`), View History (`activity_log.read`, platform-scoped), Edit + Change Password (`user.update`), Delete/Hard-Delete (`user.delete`); Add/Remove BU resolve `cluster.update` per-cluster &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list page

## 1. Overview

The Platform SPA follows a consistent two-screen pattern for every admin entity: a list page (`UserManagement`) with a server-side `DataTable`, filters in a slide-over Sheet, and header action buttons; and an edit page (`UserEdit`) that starts in read-only view mode and transitions to an editable form on demand — this module, unlike [clusters](/en/platform/clusters)/[business-units](/en/platform/business-units), kept the view/edit toggle rather than moving to a one-document always-editable page. The three routes under the `/users` prefix carry `requiredPermission` guards (`user.read` / `user.create` / `user.update`), and individual mutating buttons are wrapped in `<Can>` gates — none of which pass a `clusterId` at the route/row level, unlike the Clusters/Business Units pages (the two BU-assignment actions inside the Access card are the exception — see §4.2). See [Platform RBAC — Permissions](/en/platform/rbac/permissions) for how the gates compose.

Users carry several additions not found on simpler entities. The list page exposes a **Fetch Keycloak** button that pulls user records from the Keycloak identity provider into the platform database (gated `<Can permission="user.create">`) and a **Directory** summary strip (`UserDirectorySummary`, §2.1a). The view/edit page exposes a **Change Password** button (living in the `UserIdentityHero`'s actions slot, view mode only, and — since a recent fix — gated `<Can permission="user.update">` like its neighbouring Edit button) and, within the merged Access card, an **Add BU** button gated by a real per-cluster permission check (`canAddBU`, §4.2) rather than merely "the user belongs to at least one cluster." Both the list row menu and the edit-page hero also gained a **View History** action (`activity_log.read`, scoped to the whole platform record rather than any one cluster — the cross-cutting Activity Trail feature also documented for [clusters](/en/platform/clusters)/[business-units](/en/platform/business-units)). For super-admin sessions, the list page also offers bulk soft/hard delete (§2.4a).

## 2. `UserManagement` — list page (`/users`)

### 2.1 Layout

The page renders inside `Layout`, under a two-row header: a title/subtitle row and an actions row. Below the header sits the **Directory** summary card (§2.1a), then a search-and-filters row: debounced search input on the left, Filters button (opens a Sheet) on the right. Active filter badges are shown as a chip strip when any filter is set. The main content area is a `DataTable` component operating in server-side mode, with built-in pagination controls; for super-admin sessions it additionally renders selection checkboxes (§2.4a).

Columns in order: **User** (a single collapsed identity cell, replacing the previous separate avatar/username/name/email columns — design pass commit `fd1f6ae`, #219, prompted by 9 of 10 rows showing `username` and `email` as the exact same string in two columns), `BU` (a `Building2`-icon active/total count of the user's business-unit assignments), **Status** (see below — no longer a plain Active/Inactive badge pair), `created_at` + `created_by_name`, `updated_at` + `updated_by_name`, and conditionally `deleted_at` + `deleted_by_name` (see §2.5). The final column is an icon-button row action menu. The legacy `platform_role` badge column is gone with the role enum.

**The User cell** combines the avatar with two text lines built by `getNameDisplay` and a de-duplication step: the primary line is the composed display name (non-empty parts of `firstname`/`middlename`/`lastname` joined with spaces, falling back to the flat `name` field, then the handle, then `-`); the secondary line lists `username`/`email`, filtered to drop whichever value duplicates the primary line or duplicates each other, joined with `·` — so a row where `username`, `name`, and `email` are all identical shows only one string, while a row where all three differ still shows all three (one on the primary line, two on the secondary line). A red "Deleted" badge is appended inline next to the primary line when the row is soft-deleted (see §2.5).

**The Status column** is now asymmetric rather than a matched Active/Inactive badge pair: `is_active: true` renders as plain muted-foreground text reading "Active" (no badge chrome at all), while `is_active: false` still gets a `Badge` (`variant="secondary"`) reading "Inactive" — the rationale recorded in the component's own comment is that an all-(or nearly-all-)active table turns a badge column into a wall of identical green ink that carries no information; only the abnormal state now draws the eye.

### 2.1a Directory strip

A `UserDirectorySummary` card sits between the header and the search row, summarising **every user the caller can see** — sourced from a dedicated `GET /api-system/user/summary` endpoint (`userService.getDirectorySummary()`), not a client-side aggregation over a separately fetched page of rows. The endpoint ignores `search`/`advance`, so the numbers describe the whole directory, not the current filtered view:

- A large total count.
- A stacked Active/Inactive proportion bar with a legend (Active, Inactive, and — only when non-zero — Archived, i.e. soft-deleted).
- A **"Recently added"** overlapping-avatar stack showing the newest users the endpoint returns (`summary.newest`), each with the same initials-fallback/presigned-image pattern as the list's identity cell, collapsing any remainder past what fits into a `+N` badge.

The response also carries a `business_units` field — a backend-computed count of distinct business units the matched users belong to — but it is **not currently rendered anywhere in the strip's UI**. On a failed refresh the strip keeps the last known numbers rather than blanking them, dims them, and shows a "couldn't refresh" cue instead of an error screen; a skeleton is shown only on first load. The main table's own fetch is unaffected either way — the two requests are independent.

Within the **User** cell, the avatar renders as a small circular `Avatar` (`h-8 w-8`): an `AvatarFallback` shows initials (first letters of `firstname` + `lastname`; if both are empty, the first two characters of `name`/`username`/`email`; else `?`), and when the record carries a presigned `avatar_url` an `AvatarImage` is layered on top, hiding itself again on load error so the initials show through.

When a row is soft-deleted (visible only with the "Show soft-deleted users" filter on), the Name cell additionally renders a red "Deleted" badge whose `title` tooltip reads "Deleted by &lt;deleted_by_name&gt;" when that name is present.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet. Two filter groups are available (the legacy Role filter was removed along with the role enum — status is now the only field filter):

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). No tri-state "all" option; clearing both buttons removes the filter entirely — both off is equivalent to no status constraint (all rows shown). A **Clear** link appears when any status is selected.
- **Deleted** — a checkbox labelled "Show soft-deleted users". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge beside the user's name.

When any filter is active, a **Clear All Filters** button appears at the bottom of the Sheet, and active filter chips appear in the strip below the header.

### 2.3 Header actions

Three buttons appear in the header actions row, left to right:

- **Fetch Keycloak** — calls `userService.fetchKeycloakUsers()` → `POST /api-system/fetch-user`. A spinner replaces the icon while the request is in flight; on success a toast confirms the sync and both the table and the Directory strip reload. Wrapped in `<Can permission="user.create">`.
- **Export** — client-side CSV export (uses `generateCSV` / `downloadCSV` utilities, merged with `auditCsvFields(normalizeAudit(u))` per row). Exports the currently loaded page of rows with **7** columns: `username`, `email`, `is_active` (labelled "Status"), `created_at`, `created_by`, `updated_at`, `updated_by` — the two audit actor-name columns are new since the last sync. Timestamps in the CSV are always the absolute ISO value from `normalizeAudit()`, never the relative-time string the table cells display. The button is disabled while loading or when the table is empty. File name: `users-<YYYY-MM-DD>.csv`. Not `<Can>`-gated.
- **Add User** — navigates to `/users/new`. Wrapped in `<Can permission="user.create">`. Note: the empty-state's "Add User" shortcut (shown when the table has no rows and no search term) is **not** wrapped in `<Can>` — it renders for any `user.read` session, though the `/users/new` route guard still blocks navigation without `user.create`.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with **four** items (new since the last sync), each wrapped in a `<Can>` gate:

- **Edit** (`<Can permission="user.update">`, no `clusterId`) — navigates to `/users/:id/edit`.
- **View History** (`<Can permission="activity_log.read" clusterId={PLATFORM_SCOPED_RECORD}>`, new) — opens the shared `ActivityTrailSheet` for this user record (`entityType="user"`). Uses a platform-wide sentinel `clusterId` rather than any specific cluster, since a user is never scoped to one cluster; the same cross-cutting Activity Trail feature also documented on [clusters](/en/platform/clusters)/[business-units](/en/platform/business-units). Uses `onSelect`, not `onClick`, so the dropdown fully closes before the sheet opens — avoiding a focus-trap collision between the two Radix layers.
- **Delete** (`<Can permission="user.delete">`) — sets `deleteId` state; triggers the `ConfirmDialog` (§5.3). Submit calls `DELETE /api-system/user/:id`.
- **Hard Delete** (also `<Can permission="user.delete">`, separated by a `DropdownMenuSeparator` inside the same gate) — sets `hardDeleteUser` state; opens the typed-confirmation Dialog (§5.4), which also shows a super-admin-only "copy username" clipboard button.

A session holding only `user.read` sees a dropdown with none of these four items — the gates remove them entirely rather than disabling them.

### 2.4a Bulk actions (super-admin only, new since the last sync)

`enableRowSelection={isSuperAdmin}` — row checkboxes render only for super-admin sessions (a super-admin flag check, not a `user.*` permission key). Selecting one or more rows reveals a toolbar above the table: **Delete** (opens a plain `ConfirmDialog`, "Delete `<n>` user(s)... They can be restored later.") and **Hard Delete** (opens a random-6-character-code confirmation dialog, §5.5) and **Clear**. Each bulk action fires one request per selected row (`Promise.allSettled`, continuing past individual failures) then shows an aggregate toast. Selection is scoped to the current page/filter state and clears automatically whenever page, page size, search, sort, or filters change.

### 2.5 Audit columns

Two audit columns are always shown, now rendered by the shared `auditColumns()` factory (`../carmen-platform/src/components/auditColumns.tsx`) instead of a page-local formatter:

| Column header | Fields rendered |
|---|---|
| Created | `AuditMeta variant="cell"` — relative time (e.g. "5mo ago") on the first line, actor name on the second, with the absolute `YYYY-MM-DD HH:mm:ss` timestamp available as a `title` tooltip on hover, not printed inline |
| Updated | Same rendering, sourced from `normalizeAudit(row).updated` — renders `-` when that entry is absent |

Both columns read through `normalizeAudit()` (`../carmen-platform/src/utils/audit.ts`), which tries the **nested** `audit.created`/`audit.updated` shape first and falls back to the flat `created_at`/`created_by_name` columns only when the nested entry is missing — not the reverse. The Updated column is not suppressed by a plain `updated_at === created_at` comparison; `normalizeAudit()` omits `updated` from its result unless `everEdited` is true (the resolved updated actor has a `name`, or — absent a name — its timestamp differs from `created.at`), so a row that was edited by an unresolved/unnamed actor still shows an Updated value as long as the timestamps differ.

When the "Show soft-deleted users" filter toggle is on, a third audit column is appended:

| Column header | Fields rendered |
|---|---|
| Deleted By | `AuditMeta variant="cell"` over `normalizeAudit(row).deleted` (destructive-red styling); shows `-` for non-deleted rows |

Times render as relative ("5mo ago") with the absolute local-timezone timestamp in the cell's `title` attribute — no UTC offset indicator is displayed, and CSV export (§2.3) is the only place these columns still emit an absolute, always-parseable timestamp.

## 3. `UserEdit` — create mode (`/users/new`)

The create mode renders a single card titled **"Account details"** (`isNew ? "Account details" : "Edit account"`) with description "Fill in the details for the new user". The page's `PageHeader` title is "Add User", subtitle "Create a new user", and the whole page is now width-capped (`mx-auto max-w-5xl`) to keep the form readable, matching `ClusterEdit`'s create page. There is no hero card, no Access card, and no Change Password button — these only appear after the record is saved (`!isNew`).

**Since the design-consistency pass (commit `d21c57c`, #220), the seven fields from `UserFormData` are grouped into three labelled sections** instead of one flat two-column grid — the previous row-major 2-column layout tore First/Middle/Last Name across three separate rows and read as "First → Last → Middle":

| Section | Fields | Layout |
|---|---|---|
| Sign-in details ("How this person is identified and reached") | `username` (required; `disabled={!isNew}`), `email` (required) | 2 columns |
| Display name ("Shown across the platform. First and last name are required.") | `firstname` (**required — new**), `middlename` (optional), `lastname` (**required — new**) in that order, then `alias_name` (optional) below | 3 columns for the name row, in natural reading order — replacing the previous row-major grid, which read First → Last → Middle; `alias_name` on its own row |
| Status | `is_active` (checkbox, defaults `true`) | — |

**`firstname` and `lastname` are now required** — both carry the HTML `required` attribute and are checked by a client-side preflight (`validateOne`) before submit; this is new since the last sync, when all fields but `username`/`email` were optional. A footer hint below the Save/Cancel buttons in create mode reads "Next you will set a password and assign business units" — the account created here has no password and no BU assignment yet.

There is no `password` field on the create form — credentials are set later via the Change Password admin-reset dialog or via Keycloak — and no access/role field: the legacy `platform_role` select was removed with the RBAC migration. Granting Platform admin access is a separate step on `/platform/user-platform` (see [Platform RBAC](/en/platform/rbac)).

Submit calls `POST /api-system/user`. On success, if the response includes an `id`, the page redirects to `/users/:id/edit` with `{ replace: true }` (so Back goes to the list, not the create form). If no `id` is returned, it redirects to `/users`.

## 4. `UserEdit` — view/edit mode (`/users/:id/edit`)

The page starts in **view mode** (`editing = false`). A `BackLink` (the shared back-navigation component, now used across roughly a dozen edit pages — commit `d56e1cc`, #262) sits above a **`UserIdentityHero`** card: a `size-14` avatar (initials fallback from `firstname`/`lastname`, else the first two characters of username/email, with the presigned `avatar_url` image layered on top when present — loaded as `user.avatar_url || profile.avatar_url`, hidden again on load error), the user's full name as the page's only `<h1>`, username/email/alias chips, an Active/Inactive badge, a summary line — "Access to `<n>` business unit(s) across `<m>` cluster(s)" or "No access assigned yet" — and, new since the last sync, a `created`/`updated` audit-actor line rendered by `<AuditMeta variant="header">`. In view mode, the hero's actions slot shows a **View History** button (`<Can permission="activity_log.read" clusterId={PLATFORM_SCOPED_RECORD}>`, new, visible regardless of edit mode) plus two buttons that only render while `!editing`: **Change Password** and **Edit** — both now wrapped in `<Can permission="user.update">`. (Previously only Edit carried that gate; Change Password was ungated.) Clicking **Edit** sets `editing = true`, saves the current form state to `savedFormData`, hides those two buttons (Save and Cancel appear inside the form card instead), and reveals the form card titled "Edit account".

**There is no separate, always-present "User Details" card any more.** The design pass that grouped the account form into sections (§3, commit `d21c57c`) wrapped the *entire* card — including its `editing ? <Input> : <ReadOnlyField>` branches — in `{editing && (...)}`, so the read-only rendering path is now unreachable: in view mode nothing between the hero and the Access card renders at all, and the seven identity fields are visible only through the Hero's chips/badge (username, email, alias, active status) or by clicking Edit. This replaces the previous behaviour, where a permanently-visible card showed all seven fields as read-only `div` containers even in view mode.

Two things are stacked below the hero: the account-details card described in §3/§4.1 (only while `editing`), and — for an existing user only — a single merged **Access** card (`UserAccessTree`, unchanged in structure from the prior sync).

### 4.1 Account-details card (editing only)

- **Rendering condition**: the whole card — not just its inputs — is gated on `editing`. It is always shown in create mode (`editing` initialises to `isNew`) and shown in edit mode only after clicking the hero's Edit button.
- **Sections**: identical structure to the create form (§3) — Sign-in details / Display name / Status — titled "Edit account" rather than "Account details".
- `username` is always `disabled={!isNew}` and cannot be changed after creation; `firstname`/`lastname` are required exactly as on create.
- **Save Changes** → `PUT /api-system/user/:id`, with the loaded `doc_version` attached; on success, `fetchUser()` re-fetches (refreshing `doc_version` too) and `setEditing(false)` returns to view mode. A stale `409` shows a conflict toast and reloads the record instead.
- **Cancel button** → restores `formData` from `savedFormData`, calls `setEditing(false)`. No API call; in create mode the same button instead navigates to `/users` (`isNew ? () => navigate("/users") : handleCancelEdit`). Both are also bound as keyboard shortcuts via `useGlobalShortcuts`: `Ctrl`/`⌘`+`S` submits the form while `editing && !saving`; `Escape` calls `handleCancelEdit()` only while `editing && !isNew` — it is a no-op in create mode (the Escape shortcut does not trigger the button's create-mode "navigate to /users" behaviour).

### 4.2 Access card (`UserAccessTree`) — merged Clusters + Business Units, new since the last sync

One hierarchy for both clusters and BUs: `groupAccessByCluster()` folds the user's `tb_cluster_user` memberships and `tb_user_tb_business_unit` assignments into a list of **cluster groups**, each showing the cluster name (linked to `/clusters/:clusterId` — **still not a registered route**; re-confirmed against the current `App.tsx`, which only registers `/clusters`, `/clusters/new`, and `/clusters/:id/edit` — clicking a cluster name in this card still hits the SPA's `*` catch-all `NotFound` page, not the cluster's edit screen), code, the user's per-cluster role badge, and an Active/Inactive badge, followed by the business units assigned within that cluster. Any BU assignment whose own cluster isn't among the user's memberships collects into a trailing **"Other business units"** group so nothing is silently dropped. Each BU row shows its name (linked to `/business-units/:id/edit` — a real registered route), code, a compact audit line (new since the last sync — `latestActor()` picks whichever of `updated`/`created` is relevant and renders it via `<AuditMeta variant="compact">`), per-BU role badge, a `Default` badge (blue outline, `is_default`), an Active/Inactive badge, and a Remove (Trash) icon.

The card header shows "`<n>` business unit(s) across `<m>` cluster(s)" and an **Add BU** button. Two gating corrections since the last sync:

- **Add BU button** — visible only when `canAddBU` is true: `hasPermission('cluster.update', { clusterId })` evaluated across the user's own cluster memberships, **not** simply "the user belongs to at least one cluster" (the prior version's check). Previously undocumented as gated at all.
- **Remove (Trash) button per BU row** — now wrapped in `<Can permission="cluster.update" clusterId={bu's own cluster_id}>`, scoped to that specific BU's cluster (not the viewer's broader memberships), falling back to a sentinel that can never match a real cluster when the BU's own cluster is unresolved (the "Other business units" group). Previously undocumented as gated at all.

There is still no Add/Remove control for cluster *membership itself* on this page — only BU assignment is mutated here; cluster membership is managed on the cluster edit page.

## 5. Dialogs

### 5.1 Add BU dialog

Triggered by the **Add BU** button in the Access card header on `/users/:id/edit` (§4.2) — rendered only when `canAddBU` is true.

Fields in the dialog:

1. **Cluster** — select populated from `userClusters` (the user's existing cluster memberships). Choosing a cluster triggers an API call (`GET /api-system/business-units?...&advance={"where":{"cluster_id":"..."}}` — the BU endpoint is plural) to load the BUs for that cluster.
2. **Business Unit** — select populated from the cluster's BUs, filtered to exclude BUs the user is already assigned to (`availableBUs`). Shown only after a cluster is selected.
3. **BU Role** — select with values `Admin` and `User`.

There is no `is_default` checkbox in this dialog. The `is_default` field is shown on existing BU assignment rows but is not set during the Add BU flow. No Platform admin SPA surface currently sets `is_default`; the flag is writable only at the backend API or DB level.

Submit: re-checks `hasPermission('cluster.update', { clusterId: selectedClusterId })` against the specific cluster chosen (not just the broader `canAddBU`) before calling `businessUnitService.createUserBusinessUnit({ user_id, business_unit_id, role })` → `POST /api-system/user/business-units`. On success, dialog closes, a toast confirms, and `fetchUser()` re-fetches. The **Add** button is disabled while the request is in flight or if no BU has been selected. (Removal via the trash icon — gated `<Can permission="cluster.update" clusterId={bu's own cluster_id}>`, §4.2 — calls `deleteUserBusinessUnit(id)` → `DELETE /api-system/user/business-units/:id`, also re-checked against the BU's own cluster before firing.)

### 5.2 Change Password dialog

Triggered by the **Change Password** button visible in the `/users/:id/edit` header when in view mode.

Fields:

- **New Password** (password input) — required; validated: min 6 characters.
- **Confirm Password** (password input) — required; must match New Password.

Validation is performed client-side on submit (not on blur). Error messages are shown inline above the form.

Submit: `PUT /api-system/user/:id/reset-password` with body `{ newPassword }`. On success, dialog closes and a toast confirms — there is no profile re-fetch and no `AuthContext` refresh. The **Update Password** button shows a spinner while the request is in flight.

### 5.3 Soft Delete confirm

Triggered by **Delete** in the row action menu on `UserManagement`.

Uses the shared `ConfirmDialog` component — a simple Yes/No dialog. Title: "Delete User". Description: "Are you sure you want to delete this user? This action cannot be undone." Confirm button label: "Delete" (destructive variant). No typed confirmation required.

Submit: `DELETE /api-system/user/:id` (soft delete — sets `deleted_at`).

### 5.4 Hard Delete confirm

Triggered by **Hard Delete** in the row action menu on `UserManagement`.

A custom `Dialog` (not the shared `ConfirmDialog`). Title: "Permanently Delete User" with a destructive alert icon. The dialog displays the target user's `username || email` (with full name below) in a highlighted info box, then prompts the operator to type that value into an input field.

The **Permanently Delete** button stays disabled until `hardDeleteConfirm === (hardDeleteUser?.username || hardDeleteUser?.email || '')`. The fallback to `email` applies when `username` is absent or empty.

Submit: `DELETE /api-system/user/:id/hard`. The dialog cannot be closed while the delete request is in flight (`hardDeleting = true`). **New since the last sync:** for super-admin sessions, a small clipboard icon button beside the displayed username/email copies it (`navigator.clipboard.writeText`, `Check` icon confirms for 2 seconds) — a convenience, not a security control.

### 5.5 Bulk Soft Delete and Bulk Hard Delete confirm (super-admin only, new since the last sync)

Triggered by **Delete**/**Hard Delete** in the selection toolbar (§2.4a), visible only when `isSuperAdmin` and at least one row is selected.

**Bulk Soft Delete** uses the shared `ConfirmDialog`. Title: `Delete <n> user(s)`. Description: "Soft-delete the selected user(s)? They can be restored later." Confirm label: "Delete." On confirm, fans out one `DELETE /api-system/user/:id` per selected row (continuing past individual failures) and shows an aggregate result toast.

**Bulk Hard Delete** is a custom `Dialog` (not `ConfirmDialog`). Title: `Permanently Delete <n> User(s)` with a destructive alert icon. Lists every selected user by username/email/id in a scrollable box, then prompts the operator to type a **random 6-character alphanumeric code** generated fresh each time the dialog opens (input auto-uppercases as typed) — a materially different confirmation mechanism from the single-row flow's "type the exact username," since there is no single shared identifier across multiple rows. The **Permanently Delete** button stays disabled until the typed value matches the generated code exactly. On confirm, fans out one `DELETE /api-system/user/:id/hard` per selected row and shows the same aggregate-result toast pattern.

## 6. Persisted UI state

The list page writes 6 keys to `localStorage` so the filter and pagination state survives page reloads (the legacy `role_filters_users` key went away with the role filter). The edit page writes no `localStorage` keys.

| Key | Stored type | Persists |
|---|---|---|
| `search_users` | string | Current search term |
| `page_users` | number (string) | Current page number (reset to `1` on filter changes) |
| `perpage_users` | number (string) | Rows per page |
| `sort_users` | string | Current sort column/direction |
| `status_filters_users` | JSON array | Active status filter values (`["true"]` / `["false"]` / `[]`) |
| `filter_users_deleted` | JSON boolean | Show soft-deleted toggle state |

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan. **Note (2026-09-05):** since this page was last captured-for, the list's identity/status columns were redesigned into a single collapsed cell and an asymmetric Active/Inactive treatment, a View History row action and hero button appeared, and the edit page's view mode lost its separate User Details card entirely (the Hero now carries all view-mode identity display) — any future capture should target the current layout described in §2/§4.

## 8. References

- `../carmen-platform/src/App.tsx` — `requiredPermission` + `feature="users"` guards on the three user routes (route block, lines 267–289). (`SITEMAP.md` still shows the pre-RBAC "Authenticated" rows and lags the code.)
- `../carmen-platform/src/pages/UserManagement.tsx` and `userManagement/UserDirectorySummary.tsx` — list page: the collapsed identity column and asymmetric Status column (`fd1f6ae`, #219), Directory summary strip reading `getDirectorySummary()`, `getNameDisplay`, BU-count column, filters, header actions (`<Can>`-gated Fetch Keycloak/Add User, ungated Export), `<Can>`-gated row action menu (Edit / View History / Delete / Hard Delete), super-admin bulk soft/hard-delete with row selection, audit columns.
- `../carmen-platform/src/pages/UserEdit.tsx` and `userEdit/{UserIdentityHero,UserAccessTree}.tsx` — create/view/edit page: the sectioned account-details card rendered only while `editing` (`d21c57c`, #220), Hero audit line + View History button, `<Can>`-gated Edit toggle and Change Password, `canAddBU`/scoped-Remove permission checks, Add BU dialog, `doc_version` wiring, `username` disabled-in-edit behaviour.
- `../carmen-platform/src/utils/audit.ts` and `src/components/{auditColumns.tsx,AuditMeta.tsx}` — `normalizeAudit()`/`latestActor()` and the relative-time-with-tooltip cell renderer used throughout this page.
- `../carmen-platform/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail}.tsx` and `src/utils/permissions.ts` (`PLATFORM_SCOPED_RECORD`) — the View History feature.
- `../carmen-platform/src/utils/docVersion.ts` — optimistic-lock helpers.
- `../carmen-platform/src/services/userService.ts` — API surface: all endpoints referenced in this page, including `getDirectorySummary` (`GET /api-system/user/summary`).
- Cross-links: [users](/en/platform/users) (landing), [Data Model](/en/platform/users/data-model) (schema view), [Lifecycle](/en/platform/users/lifecycle) (operations view), [rbac permissions](/en/platform/rbac/permissions) (gate composition), [clusters](/en/platform/clusters) (mutates `tb_cluster_user`), [business-units](/en/platform/business-units) (the other surface mutating `tb_user_tb_business_unit`).
