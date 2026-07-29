---
title: Business Unit — UI Screens
description: BusinessUnitManagement (list) and BusinessUnitEdit (9 always-expanded form sections, Branding card, Users card, dialogs) — layout, filters, actions, persisted state.
published: true
date: 2026-07-29T06:50:54.000Z
tags: book/platform, business-units, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — UI Screens

> **At a Glance**
> **Screens:** `BusinessUnitManagement` (list, `/business-units`) &nbsp;·&nbsp; `BusinessUnitEdit` create (`/business-units/new`) &nbsp;·&nbsp; `BusinessUnitEdit` one-document edit (`/business-units/:id/edit`) &nbsp;·&nbsp; **Edit layout:** rewritten from 9 `CollapsibleSection` cards in a 2-column grid into a single continuous "one-document" scroll — hero card, 6 inline field groups (Details/Location/Contact/Company/Tax/Date & time), 4 complex sections (Calculation Settings/Number Formats/Branding/Configuration/Database Connection), 3 super-admin advanced cards (Tenant Migrations/Tenant Seed/Interface Entitlement, existing BUs only), then Users — **no read/edit toggle**, one `canEdit` boolean gates everything &nbsp;·&nbsp; **Dialogs:** Add User to BU · Edit BU User · Remove BU User confirm · Soft Delete BU confirm &nbsp;·&nbsp; **Access:** route guards reuse `cluster.read` / `cluster.create` / `cluster.update`; Add/Edit/Delete buttons behind `<Can>` gates (see [business-units](/en/platform/business-units) §4) &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys &nbsp;·&nbsp; **Concurrency:** `doc_version` optimistic lock on save

## 1. Overview

The business-unit surface follows the Platform SPA's standard two-screen pattern: a server-side `DataTable` list page (`BusinessUnitManagement`) and a shared create/edit page (`BusinessUnitEdit`). The edit page was rewritten (the "one-document rewrite") from 9 always-expanded `CollapsibleSection` cards in a 2-column grid into a single continuous scrolling document: a `PageHeader` with an inline-editable name (`HeroName`, rendered as the page's `<h1>`), then `BusinessUnitDocument` — a hero identity card followed by six inline field `Group`s (Details, Location, Contact, Company, Tax, Date & time, each rendered via a shared `InlineField` click-to-edit control), then the four remaining complex sections (Calculation Settings, Number Formats, Branding, Configuration, Database Connection — still `CollapsibleSection`-wrapped internally with `forceOpen`, but no longer arranged in a 2-column grid), then — for existing BUs only — three super-admin "advanced" cards and the Users card.

There is **no read/edit mode split any more**. A single `canEdit` boolean (`isNew ? hasPermission('cluster.create') : hasPermission('cluster.update', { clusterId: formData.cluster_id || UNRESOLVED_CLUSTER_ID })`) is computed once and passed down; every field, toggle, and section renders its editable form when `canEdit` is true and a read-only rendering otherwise — there is no separate "Edit" button anywhere on this page. A sticky bottom bar (Cancel / Save Changes, or just Create Business Unit + Cancel in create mode) appears whenever the document is dirty; `Ctrl/⌘+S` saves and `Escape` cancels via the shared keyboard-shortcut hook — the shortcut still checks `canEdit` itself, since a disabled Save button alone isn't a defense against a keyboard shortcut bypassing it.

The three registered routes are guarded by `requiredPermission` keys **reused from the Clusters module** — `cluster.read` (list), `cluster.create` (create), `cluster.update` (edit); there are no `business_unit.*` keys. The full gate matrix and the key-reuse gotcha live in [business-units](/en/platform/business-units) §4 and [clusters permissions](/en/platform/clusters/permissions) §2.

Note: although `tb_business_unit_tb_module` exists in the Prisma schema as a M:N modules-activation join, the Platform admin SPA does not currently surface module activation on this page — `BusinessUnitEdit` has no module-management dialog. The join is managed at the backend / DB level only. (The Interface Entitlement card, §4.9, is a related-sounding but distinct concept — it licenses *interface/brand* access via a separate service, not platform module activation.)

## 2. `BusinessUnitManagement` — list page (`/business-units`)

### 2.1 Layout

The page renders inside `Layout` with a two-row header: a title/subtitle row ("Business Unit Management" / "Manage business units and departments") and an actions row with **Export** and **Add Business Unit** buttons (the button label shortens to "Add BU" on small screens via responsive visibility classes). Below the header sits an **Overview** summary card (§2.1a), then a search-and-filters row inside a `Card`. The `DataTable` renders in server-side mode with pagination.

### 2.1a Overview strip

A `BuSummary` card summarises **every non-deleted BU** (a separate unpaginated `perpage: -1` fetch, plus a second lightweight count-only fetch for soft-deleted rows) — not just the current page. It shows a large total count and "across N cluster(s)" note on the left, and a stacked Active/Inactive proportion bar with a legend (Active, Inactive, and — only when non-zero — Archived, i.e. soft-deleted) on the right. On a failed fetch it renders an inline error with a Retry button rather than blocking the rest of the page.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side `Sheet` (slide-over panel). An active-filter count badge appears on the Filters button when any filter is set. Two filter groups are wired:

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). The two buttons may be toggled independently; when exactly one value is selected the query appends an `is_active` equality constraint, and when both or neither are selected no status constraint is applied.
- **Deleted** — a checkbox labelled "Show soft-deleted business units". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge in the `name` cell, and a conditional `Deleted By` column is appended to the `DataTable`.

There is no cluster filter group on the list page; filtering by cluster requires the search bar or server-side `advance` parameter. When any filter is active, active filter chips appear in a strip below the search row. Each chip has an inline remove button; a **Clear all** text link clears all filters at once. A **Clear All Filters** button also appears at the bottom of the Sheet when any filter is active. A **Clear** link appears in the Status group header when a status value is selected.

### 2.3 Header actions

Two buttons appear in the header actions row:

- **Export** — client-side CSV export using `generateCSV` / `downloadCSV` utilities (no server call). Exports the currently loaded page of rows with columns: `Code`, `Name`, `Alias Name`, `Cluster`, `Status` (`is_active`), `Max Licensed Users`, `Created` (`created_at`). File name: `business-units-<YYYY-MM-DD>.csv`. The button is disabled while loading or when the table is empty.
- **Add Business Unit** — navigates to `/business-units/new`. Wrapped in `<Can permission="cluster.create">`, so it renders only for sessions holding that key. Note: the **empty-state** Add Business Unit button (shown when the table has no rows and no search term) is *not* `<Can>`-gated — a `cluster.read`-only session can click it, and the `cluster.create` route guard on `/business-units/new` then renders the `Forbidden` (403) page.

There is no Fetch Keycloak button (that affordance exists only on the Users list) and no Hard Delete action anywhere in business-unit management.

### 2.4 Row actions

Columns in order: `code` (clickable link — navigates to `/business-units/:id/edit`), `name` (clickable link — also navigates to edit; a red `Deleted` badge is appended when `deleted_at` is non-null; the badge's tooltip reads "Deleted by &lt;name&gt;" when `deleted_by_name` is present), `alias_name` (muted text, header "Alias"), `cluster_name` (sortable server-side via the `tb_cluster.name` column id), `is_active` (Active/Inactive badge), `created_at` + `created_by_name`, `updated_at` + `updated_by_name` (suppressed when equal to `created_at`), and conditionally `deleted_at` + `deleted_by_name` in destructive red (only when "Show soft-deleted" filter is on). The final column is a `DropdownMenu` icon button (⋯) with two items, each behind a **cluster-scoped `<Can>` gate** — note the `clusterId` is the BU's *parent cluster* id, not the BU id. **There is no logo thumbnail column** — like the cluster list, a per-row logo/avatar image used to lead this column set and was removed, not relocated; a BU's logo/avatar is now visible only on its own edit page's hero and Branding section.

- **Edit** — inside `<Can permission="cluster.update" clusterId={row.original.cluster_id}>`; navigates to `/business-units/:id/edit`.
- **Delete** — inside `<Can permission="cluster.delete" clusterId={row.original.cluster_id}>`; sets `deleteId` state and opens the Soft Delete BU `ConfirmDialog` (§5.4). Unlike the cluster list's row Delete, there is **no** client-side dependency guard here — a BU can be deleted regardless of what it owns (module activations, subscription details, application roles), all handled application-side, not by this SPA.

A session whose grants cover neither key for a given BU's parent cluster sees an empty dropdown for that row. There is no Hard Delete option in the row action menu. The `BusinessUnitManagement` page calls only `DELETE /api-system/business-units/:id` (soft delete — sets `deleted_at`).

### 2.5 Audit columns

The API returns audit data as a nested `audit` object (`audit.created/updated/deleted`, each `{ at, id, name, avatar }`). `fetchBusinessUnits` flattens this into `created_at`/`created_by_name` etc. before rendering, tolerating the older flat shape, which wins when present (`item.created_at ?? item.audit?.created?.at`). Two audit columns are always shown:

| Column header | Fields rendered |
|---|---|
| Created | `created_at` (formatted `YYYY-MM-DD HH:mm:ss`, browser local time) + `created_by_name` on the next line |
| Updated | `updated_at` + `updated_by_name` — suppressed (renders `null`) when `updated_at === created_at` |

When "Show soft-deleted" is on, a third audit column is appended:

| Column header | Fields rendered |
|---|---|
| Deleted By | `deleted_at` + `deleted_by_name` (text in destructive red); shows `-` for non-deleted rows |

## 3. `BusinessUnitEdit` — create mode (`/business-units/new`)

In create mode (`isNew = true`) the page title is the inline-editable `HeroName` (empty, showing the "(unnamed business unit)" placeholder text) and the subtitle is "Create a new business unit". The document is immediately editable — no Edit header button, no Branding/advanced/Users content (`brandingSlot`/`advancedExtraSlot`/`usersSlot` are all `null` while `isNew`).

**`?cluster_id=<id>` query parameter:** the initial form state reads `searchParams.get('cluster_id') || ''` and sets it as the initial value of `cluster_id` in `formData`. When `BusinessUnitEdit` is reached by clicking **Add** in the Business Units section of [clusters](/en/platform/clusters) (`/business-units/new?cluster_id=<id>`), the Cluster select in the Details group is pre-selected to that cluster. The user can change it before saving.

**License limit check on submit:** before calling `POST /api-system/business-units`, the form fetches the selected cluster via `GET /api-system/clusters/:id`; if `max_license_bu` is non-null it counts the cluster's existing BUs via `GET /api-system/business-units?perpage=-1` with an `advance` filter on `cluster_id`. If `currentCount >= cluster.max_license_bu`, it blocks the submit with an inline error ("Cannot create business unit: cluster has reached its license limit (N/M)") and does not call the create endpoint.

Submit button label: **Create Business Unit** (sticky bottom bar, always visible in create mode). **Post-create navigation:** on success, if the response includes an `id`, navigates to `/business-units/:id/edit` with `{ replace: true }` — a registered route, so a successful create now lands the operator directly on the new BU's edit page rather than bouncing through the catch-all to the Dashboard (that quirk, previously documented here and still relevant history on the cluster side — see [clusters ui-screens](/en/platform/clusters/ui-screens) §3 — has been fixed on both pages). If no `id` is returned, navigates to `/business-units`. **Cancel** navigates to `/business-units` without an API call.

## 4. `BusinessUnitEdit` — one-document edit (`/business-units/:id/edit`)

There is no view/edit mode split. `canEdit` (`hasPermission('cluster.update', { clusterId: formData.cluster_id || UNRESOLVED_CLUSTER_ID })` for an existing BU) is computed once and threaded through every section; each control renders editable when `canEdit` is true and a read-only presentation otherwise — there is no header Edit button and no `editing` state toggle anywhere on this page.

### 4.1 Hero card

A `Card` at the top of `BusinessUnitDocument` shows the logo (or a code-initials placeholder) and avatar (or a name-initial placeholder) side by side, the `code` chip, the resolved cluster name, and two **clickable status badges** — Active/Inactive and HQ — that toggle `is_active`/`is_hq` directly on click (`disabled={!canEdit}`), with no separate checkbox anywhere in the document. The BU's name itself is edited via `HeroName` in the page's `PageHeader` title slot (§3), not inside this card.

### 4.2 Details group

Inline `InlineField` rows: **Code** (required, max 20 chars, mono, validated), **Alias** (max 3 chars, validated), **Cluster** (required `select` from all clusters via `GET /api-system/clusters?perpage=-1`), **Max users** (number, mono, validated), **Description** (`textarea`, max 500 chars). `code`, `name` (in the hero title), and `cluster_id` are the only three fields `validateRequired()` enforces before submit. There is no `disabled` guard beyond the page-wide `canEdit` — `code` and `cluster_id` remain editable after creation the same as every other field.

### 4.3 Location group (hotel address)

Eleven `InlineField` rows: **Hotel name** (max 100 chars), **Address line 1**, **Address line 2**, **Sub-district**, **District**, **City**, **Province**, **Postal code** (mono), **Country**, **Latitude** (mono), **Longitude** (mono). This replaces the former single free-text "Address" `textarea` + "Zip Code" pair with ten structured columns (`hotel_address_line1`…`hotel_longitude`) — see [Data Model](./data-model.md) §2.1 for the schema-level rename.

### 4.4 Contact group

Two `InlineField` rows: **Phone** (mono) and **Email** (`type="email"`) — both map to `hotel_tel`/`hotel_email`. Both optional, no required markers.

### 4.5 Company group

The same eleven-field structured-address pattern as Location (§4.3), prefixed `company_*`, plus **Company phone** and **Company email**. A **Copy from hotel address** button (visible only when `canEdit`) in the group header one-way-copies all ten hotel address fields (not phone/email) into their company counterparts via a single `setFormData` call — this goes through the same edit-in-place path as any manual edit, so it marks the document dirty and is included in the next Save, and is reverted by Cancel like any other change.

### 4.6 Tax group

Two `InlineField` rows: **Tax ID** (mono, `tax_no`) and **Branch** (mono, `branch_no`). Both free-text, no format validation, both nullable in the schema — surfaced on printed documents but not enforced at any data layer.

### 4.7 Date & time group

Six `InlineField` rows: **Timezone**, **Date format**, **Date-time format**, **Time format**, **Long time format**, **Short time format** (all mono, free-text with no dropdown or IANA picker) — merged into one inline group; this replaces the former standalone "Date/Time Formats" section.

### 4.8 Calculation Settings section

Still a `CollapsibleSection` (`forceOpen`), now always rendered with the page's document-wide `editing = canEdit`: **Calculation Method** (`select`, `average`/`fifo`, matching `enum_calculation_method`) and **Default Currency ID** — no longer a free-text UUID input. It is now a `<select>` populated from the BU's own tenant currency list (`GET /api/config/:buCode/currencies`, lazy-loaded once `formData.code` is known and only for an existing BU), showing `code - name` per option (inactive currencies suffixed `(inactive)`) and falling back silently to the old free-text UUID input if the currency fetch fails or hasn't started (`currenciesFailed` / not yet an array) — a saved id absent from the fetched list is still shown as an extra option so the value is never dropped. In read-only mode, when `defaultCurrency` data is present (fetched inline with the BU record), the same read-only currency detail panel (Code/Name/Symbol/Decimal Places/Description/Active badge) still renders below.

### 4.9 Number Formats section

Unchanged in shape from the prior sync: **Per Page Format**, **Amount Format**, **Quantity Format**, **Recipe Format**, all JSON strings edited as plain text inputs, parsed back to objects on save by `buildPayload` (a parse failure passes the raw string through). Still gated on the page-wide `canEdit` rather than its own toggle.

### 4.10 Branding section

Renders (existing BUs only — `brandingSlot` is `null` in create mode) two `BrandingImageUpload` controls side by side: **Logo** (`shape="rect"`) and **Avatar** (`shape="square"`), each `disabled={!canEdit}`, labelled **Upload**/**Replace** per control (replace semantics — no remove/clear affordance). Client-side validation: JPEG/PNG/WebP, max 5 MB. On file selection the page calls `POST /api-system/business-units/:id/logo` (field `logo`) or `POST /api-system/business-units/:id/avatar` (field `avatar`) and sets the preview from the returned presigned `url` directly — deliberately not re-fetching the BU, so unsaved Details/Location/etc. edits are not clobbered; an uploaded image persists immediately even if the operator then cancels the rest of the document. The cluster edit page carries the equivalent section — see [clusters ui-screens](/en/platform/clusters/ui-screens) §4.3.

### 4.11 Configuration section

The `config` column stores an array of `BusinessUnitConfig` entries (`{ key, label, datatype?, value }`). Gated on the page-wide `canEdit`, not its own toggle:

- **Editable** — each existing row is shown as an inline 5-column row (Key\*, Label\*, Data Type select, Value, Delete button). Data Type options: `string`, `number`, `boolean`, `date`, **`enum`** (new since the last sync), `json`. An **Add Config Entry** button appends a blank row; Delete removes the row from `formData.config` immediately with no confirmation. On save, `buildPayload` keeps only rows where both `key` and `label` are non-empty.
- **Read-only** — rows shown in a plain `<table>` (Key/Label/Type/Value); "No configuration entries." when empty.

There is no separate dialog for adding/editing config rows — editing is in-place within the section, the only inline-add surface on this page (the BU-user assignment elsewhere still uses modal dialogs — see [users](/en/platform/users) Add BU dialog and §5 below).

### 4.12 Database Connection section

**No longer a read-only `<pre>` blob** — `db_connection` is now a hybrid editable form, held in `formData` as an array of `{ key, value }` fields (`objectToDbFields`/`dbFieldsToObject` in `utils/dbConnection.ts`) rather than a JSON string:

- **Seven known fields**, each a typed control: `host`, `port` (number, with a client-side "Port must be a number" check), `database`, `schema`, `user` (all text), `password` (masked `<Input type="password">` with a show/hide eye-icon toggle), and `ssl` (checkbox). All render regardless of whether the underlying key is present in the stored JSON.
- **Additional fields** — any other keys in the stored `db_connection` object render as free Key/Value row pairs below a divider, each removable, with an **Add field** button to append a blank pair.
- **Password write-only, with a guarded reveal:** the backend always redacts `password` to an empty string on every list/detail read, so a blank field on save does *not* clear the stored password (`dbFieldsToObject` omits blank values from the payload entirely) — the placeholder text says so explicitly. A **Reveal current password** button, gated behind `<Can permission="cluster.update" clusterId={...}>` (defense-in-depth; the real boundary is the backend endpoint itself), calls a dedicated on-demand endpoint (`businessUnitService.revealDbPassword`, never fetched on mount) and displays the real value inline; the revealed value is cleared from local state the moment `canEdit` goes false (component `useEffect`), so it never lingers past the edit session.
- **Read-only rendering** uses `DbConnectionView`, which masks sensitive keys — everything **not** in a small safe allowlist (`host`/`hostname`/`port`/`schema`/`database`/`db`/`dialect`/`type`/`ssl`/`sslmode`) is masked, default-deny.

This is a substantial behavior change from the prior sync's documented "opaque read-only `<pre>` block, editable only via direct API access" — the field is now a first-class editable, masked form on this page.

### 4.13 Advanced cards (existing BUs only, super-admin only)

Three cards render after Database Connection, all gated on `isSuperAdmin` (a separate check from `canEdit` — a non-super-admin `cluster.update` holder never sees these regardless of edit rights) and rendered only when `!isNew`:

- **Tenant Migrations** (`TenantMigrationCard`) — checks pending database schema migrations for this BU's own tenant database (`GET`-style status check) and applies them via a streamed deploy action with a live applied/total progress readout and a running log of migration names, behind a confirm dialog. Disabled with a tooltip when not super-admin or when the BU has no `db_connection` configured yet.
- **Tenant Seed** (`TenantSeedCard`) — the same status-check/confirm/streamed-progress pattern, but for seed scripts instead of migrations; supports selecting a subset of seed keys before running.
- **Interface Entitlement** (`InterfaceEntitlementCard`) — controls which named interface/brand this BU is licensed to show, loaded and saved by `buCode` independently of the rest of the document (its own Save button, not part of the page's sticky bar). An empty selection means "unrestricted" — every interface shows, matching the gateway's own show-all default. Disabled until the BU has been saved at least once (needs a `buCode`).

None of these three cards existed in the prior sync — they are wholly new surfaces added to the BU edit page (commits `8fc1124`, `88ae453`, `ccb0754`), operating through their own dedicated service modules (`tenantMigrationService`, `tenantSeedService`, `interfaceEntitlementService`), not `businessUnitService`.

### 4.14 Users card

Unchanged in shape from the prior sync — still a full-width `Card` below the advanced cards (existing BUs only), with dialogs for Add/Edit/Remove rather than the inline-edit pattern the [clusters](/en/platform/clusters) Users section adopted. The only change is *how* it's gated: the card now takes a single `canEdit` prop from the page (§4.1) instead of each action carrying its own `<Can>` — see §5 for the dialog details, which remain accurate against current source.

## 5. Dialogs

### 5.1 Add User to BU dialog

**Trigger:** the **Add User** button (`UserPlus` icon) in the Users card header (§4.14). Only available for an existing BU (`!isNew`), and only rendered when `canEdit`.

The dialog (`sm:max-w-lg`) loads the cluster's user list when `formData.cluster_id` is set and the response is not yet cached (`GET /api-system/user/clusters/:clusterId` via `clusterService.getClusterUsers`). It shows a scrollable list of cluster users not already in this BU (`availableClusterUsers` filter). An inline search input filters the already-loaded list client-side (no debounce, no server call) by `username`, `email`, and full name (first/middle/last from `userInfo`); a "N available of M cluster users" count renders below the list.

After selecting a user (click on a row), the selected-user display replaces the search list; an X button on the display card deselects and returns to the list.

Fields:
- **BU Role** — select from `BU_ROLES = ['admin', 'user']`. Default: `user`.

Note: there is no `is_default` checkbox in the Add User dialog. The `is_default` field on the `tb_user_tb_business_unit` join exists in the schema but is not exposed in the current UI. See [Data Model](./data-model.md) §2.3 for the join-table schema and the `is_default` field definition.

On submit (clicking **Add User**, disabled until a user is selected and the request is not in flight), calls `POST /api-system/user/business-units` with body `{ user_id, business_unit_id, role }`. On success, the dialog closes, a toast confirms, and `fetchBuUsers()` re-fetches the BU record to refresh the Users table.

### 5.2 Edit BU User dialog

**Trigger:** the **Edit** (Pencil) icon button on a user row in the Users table — column rendered only when `canEdit`.

The dialog (`sm:max-w-md`) title is "Edit User in Business Unit". The description shows the user's `username` and display name (first/middle/last joined, falling back to `email`).

Editable fields:
- **BU Role** — select from `BU_ROLES` (`admin` / `user`). Pre-populated from `user.role`.
- **BU Status** — select `Active` / `Inactive`. Pre-populated from `user.is_active` (the `is_active` field on the BU-user join row, not the global user account status).

On submit, calls `PATCH /api-system/user/business-units/:id` with body `{ role, is_active }`. On success, the local `buUsers` state is updated optimistically without a full re-fetch; a toast confirms.

### 5.3 Remove BU User confirm

**Trigger:** the **Delete** (Trash, destructive colour) icon button on a user row in the Users table — column rendered only when `canEdit`.

Uses the shared `ConfirmDialog`. Title: "Remove User". Description: `Are you sure you want to remove "<display name>" from this business unit?` where display name resolves first/middle/last, then `username`, then `email`. Confirm button label: "Remove" (destructive variant). No typed confirmation required.

On confirm, calls `DELETE /api-system/user/business-units/:id` (the `tb_user_tb_business_unit.id`, not the `user_id`). On success, the matching entry is removed from local `buUsers` state; a toast confirms.

### 5.4 Soft Delete BU confirm

**Trigger:** the **Delete** row action in `BusinessUnitManagement` — which itself renders only inside `<Can permission="cluster.delete" clusterId={row.original.cluster_id}>` (§2.4).

Uses the shared `ConfirmDialog`. Title: "Delete Business Unit". Description: "Are you sure you want to delete this business unit? This action cannot be undone." Confirm button label: "Delete" (destructive variant). No hard-delete option exists anywhere in the BU management UI.

On confirm, calls `DELETE /api-system/business-units/:id` (soft delete — sets `deleted_at`). On success, a toast confirms and the list re-fetches.

## 6. Persisted UI state

The list page writes 6 keys to `localStorage`. `BusinessUnitEdit` writes no `localStorage` keys.

| Key | Stored type | Persists |
|---|---|---|
| `search_business_units` | string | Current search term |
| `page_business_units` | number (string) | Current page number (reset to `1` on filter or search changes) |
| `perpage_business_units` | number (string) | Rows per page |
| `sort_business_units` | string | Current sort column/direction (default `created_at:desc`) |
| `filters_business_units` | JSON array | Active status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filter_business_units_deleted` | JSON boolean | "Show soft-deleted business units" toggle state (default `false`) |

Note: the BU list persists no filter keys beyond the status array and the deleted toggle — there is no role filter group on this page. (The users list once persisted a role filter, but that disappeared along with the role-enum model; see [rbac](/en/platform/rbac) §5.)

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan. **Note (2026-07-29):** the edit page's layout changed from a 9-card 2-column grid to a single-column one-document scroll since this page was last captured-for — any future capture should target the new hero/inline-group/advanced-cards layout described in §4.

## 8. References

- `../carmen-platform/src/App.tsx` — three BU routes with `requiredPermission` keys (`cluster.read`/`cluster.create`/`cluster.update`); the create-navigation quirk previously documented here has been fixed — the catch-all now serves a dedicated 404 page rather than silently redirecting to Landing. (`SITEMAP.md` still shows the legacy role lists and is stale on access columns.)
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx` and `businessUnitManagement/BuSummary.tsx` — list page: Overview summary strip, filters (Status + Deleted), header actions (Export, `<Can>`-gated Add Business Unit), `<Can>`-gated row action menu (Edit / Delete soft, no client-side deletion guard), nested-audit column mapping, 6 `localStorage` keys.
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` — one-document orchestrator page: `canEdit` gating (no view/edit toggle), `doc_version` optimistic locking, license-limit pre-flight check on create, `?cluster_id` query-param pre-select.
- `../carmen-platform/src/pages/businessUnitEdit/{BusinessUnitDocument,HeroName,shared,types}.ts(x)` — hero card, inline field groups (Details/Location/Contact/Company/Tax/Date & time), `InlineField`, `BU_ROLES` constant, `BusinessUnitFormData`/`initialFormData`.
- `../carmen-platform/src/pages/businessUnitEdit/sections/{CalculationSettingsSection,NumberFormatsSection,ConfigurationSection,DatabaseConnectionSection}.tsx` — the four remaining complex sections; `DatabaseConnectionSection` now a structured editable form (known fields + extras + masked/revealable password), not a read-only `<pre>`.
- `../carmen-platform/src/components/{TenantMigrationCard,TenantSeedCard,InterfaceEntitlementCard}.tsx` — the three new super-admin-only advanced cards (§4.13).
- `../carmen-platform/src/utils/dbConnection.ts` — `objectToDbFields`/`dbFieldsToObject`/`parseDbConnection`/`SAFE_DB_CONNECTION_KEYS`; `../carmen-platform/src/components/DbConnectionView.tsx` — the read-only masked renderer.
- `../carmen-platform/src/services/currencyService.ts` — `GET /api/config/:buCode/currencies`, backing the Calculation Settings currency dropdown (§4.8).
- `../carmen-platform/src/pages/businessUnitEdit/{BusinessUnitUsersCard,useBusinessUnitUsers}.ts(x)` — Users card and its Add/Edit/Remove dialog logic (unchanged in shape; now `canEdit`-gated as a whole rather than per-action).
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — shared upload control: type/size validation, rect/square preview shapes, Upload/Replace button states.
- `../carmen-platform/src/services/businessUnitService.ts` — API surface: `GET/POST /api-system/business-units`, `PUT/DELETE /api-system/business-units/:id`, `POST /api-system/business-units/:id/logo`, `POST /api-system/business-units/:id/avatar`, `revealDbPassword`, `PATCH /api-system/user/business-units/:id`, `POST /api-system/user/business-units`, `DELETE /api-system/user/business-units/:id`.
- Cross-links: [business-units](/en/platform/business-units) (module landing; §4 gate matrix), [clusters](/en/platform/clusters) (parent cluster; source of `?cluster_id` navigate-to-new), [clusters permissions](/en/platform/clusters/permissions) (key-reuse gotcha from the cluster side), [users](/en/platform/users) (other surface mutating `tb_user_tb_business_unit`), [Data Model](./data-model.md).
