---
title: Business Unit — UI Screens
description: BusinessUnitManagement (list) and the six-tab BusinessUnitEdit — code auto-generation, the schema-name randomizer, and the Licenses tab split out of Users.
published: true
date: 2026-09-06T23:45:00.000Z
tags: book/platform, business-units, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — UI Screens

> **At a Glance**
> **Screens:** `BusinessUnitManagement` (list, `/business-units`) &nbsp;·&nbsp; `BusinessUnitEdit` create (`/business-units/new`) &nbsp;·&nbsp; `BusinessUnitEdit` edit (`/business-units/:id/edit`) &nbsp;·&nbsp; **Edit layout — rewritten a second time since the last sync:** the "one-document" continuous scroll (hero + inline groups + collapsible sections in one page) was itself replaced by a **6-tab document** — General, Location, Formats, Technical, Users, Licenses — behind a pinned `ClusterPlate`-style hero + `TabStrip`, the same redesign pattern [clusters](/en/platform/clusters/ui-screens) went through &nbsp;·&nbsp; **Four confirmed behavior changes:** (a) `code` is no longer typed by the user — the backend generates it; (b) the Technical tab has a schema-name randomizer button; (c) **Licenses is its own tab**, split out of Users; (d) the Licenses tab has a **New subscription** button &nbsp;·&nbsp; **Dialogs:** Add User to BU · Edit BU User · Remove BU User confirm · Soft Delete BU confirm · Repoint database pool/schema confirm &nbsp;·&nbsp; **Access:** route guards reuse `cluster.read` / `cluster.create` / `cluster.update`, all three gated behind the `business_units` feature flag too; Add/Edit/Delete buttons behind `<Can>` gates (see [business-units](/en/platform/business-units) §4) &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list; the edit page's active tab lives in `?tab=`, not `localStorage` &nbsp;·&nbsp; **Concurrency:** `doc_version` optimistic lock on save

## 1. Overview

The business-unit surface follows the Platform SPA's standard two-screen pattern: a server-side `DataTable` list page (`BusinessUnitManagement`) and a shared create/edit page (`BusinessUnitEdit`). The edit page has now been rewritten **twice** since the module was last synced: first from 9 always-expanded `CollapsibleSection` cards in a 2-column grid into a single continuous "one-document" scroll, and then — the change this sync captures — from that one-document scroll into a **6-tab document** (`dde5787`/`fd087f1`/`c305b61`, 2026-08-31 to 2026-09-01), matching the redesign [clusters](/en/platform/clusters/ui-screens) got around the same time. There is still no read/edit mode split: a single `canEdit` boolean gates every field across every tab, every field, toggle, and section rendering its editable form when `canEdit` is true and a read-only presentation otherwise. Both rewrites left one interaction pattern untouched: each field still commits to `formData` on blur or Enter and reverts on `Escape` via the shared `InlineField` click-to-edit control (`businessUnitEdit/InlineField.tsx` — read-mode shows the value with a pencil affordance; clicking it opens an inline input, autofocused).

A sticky bottom bar (Cancel / Save Changes, or just Create Business Unit + Cancel in create mode) appears whenever the document is dirty; `Ctrl/⌘+S` saves and `Escape` cancels page-wide via the shared `useGlobalShortcuts` hook (`components/KeyboardShortcuts.tsx`) — confirmed still wired in current source (`BusinessUnitEdit.tsx` line 161). Two nuances, re-verified against the current handlers rather than carried forward from the last sync unchecked: the save shortcut only calls `handleSave()` when `canEdit && !saving && (isNew || hasChanges)`, and `handleSave()` re-checks `canEdit` itself at its own top — so a disabled Save button alone is never the only thing standing between a read-only session and a write, exactly as documented before this rewrite. The cancel shortcut only fires `handleCancelEdit()` (revert to the last-saved snapshot, not a navigation) when `!isNew && hasChanges` — it is a no-op in create mode and a no-op on a clean existing record, a nuance the last sync's wording didn't spell out.

The six tabs, in the order the strip renders them (`BU_TAB_IDS`, `businessUnitEdit/BusinessUnitTabs.tsx`):

| Tab | Contents | Visible when |
|---|---|---|
| **General** | Details group (Code — read-only, Alias, Cluster, Max users — read-only, Description), Calculation Settings section, Branding section | Always |
| **Location** | Hotel group (11 fields), Company group (11 fields + Copy from hotel address), Tax group | Always |
| **Formats** | Date & time group, Number Formats section | Always |
| **Technical** | Configuration section, Database Connection section (pool + schema picker), the three advanced cards (Tenant Migrations/Tenant Seed/Interface Entitlement) | Always (advanced cards render content only when `!isNew`) |
| **Users** | Users card | `!isNew` only — the tab itself is omitted from the strip entirely while creating |
| **Licenses** | User Licenses card | `!isNew` only — omitted from the strip while creating |

A field's tab is resolved by `tabForField()` (prefix-based: `hotel_*`/`company_*`/`tax_no`/`branch_no` → Location; `timezone`/`*_format` → Formats; `database_pool_id`/`db_schema`/`config*` → Technical; everything else → General; `name` returns no tab because it lives in the page header, visible from every tab). When Save fails validation, `tabsWithErrors()` walks the tab order and jumps to the first tab holding an errored field, and that tab's trigger shows a red-dot indicator — so a failed save on the Technical tab's `db_schema` field, say, is visible even before the user switches tabs. The active tab is deep-linkable via `?tab=<id>` (survives a reload, can be bookmarked/shared); switching tabs calls `replace: true` on the URL so tab-hopping doesn't pollute browser Back history. An unrecognized or missing `?tab=` value falls back to General.

The three registered routes are guarded by `requiredPermission` keys **reused from the Clusters module** — `cluster.read` (list), `cluster.create` (create), `cluster.update` (edit) — **and, new since the last sync, all three also require `feature="business_units"`** on `PrivateRoute` (`src/App.tsx`), checked after the permission gate. There are still no `business_unit.*` keys. The full gate matrix and the key-reuse gotcha live in [business-units](/en/platform/business-units) §4.

Note: although `tb_business_unit_tb_module` exists in the Prisma schema as a M:N modules-activation join, the Platform admin SPA does not currently surface module activation on this page — `BusinessUnitEdit` has no module-management dialog. The join is managed at the backend / DB level only. (The Interface Entitlement card, §4, is a related-sounding but distinct concept — it licenses *interface/brand* access via a separate service, not platform module activation.)

## 2. `BusinessUnitManagement` — list page (`/business-units`)

### 2.1 Layout

The page renders inside `Layout` with a two-row header: a title/subtitle row ("Business Unit Management" / "Manage business units and departments") and an actions row with **Export** and **Add Business Unit** buttons (the button label shortens to "Add BU" on small screens). Below the header sits an **Overview** summary card (§2.1a), then a search-and-filters row inside a `Card`. The `DataTable` renders in server-side mode with pagination and 3 sticky-left columns.

### 2.1a Overview strip

**Changed since the last sync:** `BuSummary` now reads a single dedicated endpoint — `GET /api-system/business-units/summary` (`businessUnitService.getSummary()`) — instead of the previous unpaginated fetch-everything-then-count approach. The card still shows the same numbers (total, active, inactive, archived, cluster count) with the same layout (a large total + "across N cluster(s)" note on the left; a stacked Active/Inactive proportion bar with a legend, plus an Archived legend entry only when non-zero, on the right). A failed refresh keeps the last-known numbers on screen (dimmed, with a "could not refresh" note) rather than blanking the card — the same stale-but-plausible pattern `FleetCapacity` uses on the clusters list.

### 2.2 Filters (Sheet panel)

Unchanged since the last sync. Clicking **Filters** opens a right-side `Sheet`. An active-filter count badge appears on the Filters button when any filter is set. Two filter groups are wired:

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). Toggled independently; when exactly one value is selected the query appends an `is_active` equality constraint, and when both or neither are selected no status constraint is applied.
- **Deleted** — a checkbox labelled "Show soft-deleted business units". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge in the `name` cell, and a conditional `Deleted By` column is appended to the `DataTable`.

There is no cluster filter group on the list page. Active filter chips appear below the search row when any filter is set, each with an inline remove button; a **Clear all** link and a **Clear All Filters** Sheet-bottom button both clear everything at once.

### 2.3 Header actions

- **Export** — client-side CSV export (`generateCSV`/`downloadCSV`, no server call) of the currently loaded page of rows. **Columns changed since the last sync**: `Code`, `Name`, `Alias Name`, `Cluster`, `Status`, `Created At`, `Created By`, `Updated At`, `Updated By` — the **`Max Licensed Users` column is gone** (the underlying field was dropped, see [Data Model](/en/platform/business-units/data-model) §1), and Created/Updated are now four separate columns (via the shared `auditCsvFields()` helper) rather than two combined "timestamp + name" text cells. File name unchanged: `business-units-<YYYY-MM-DD>.csv`. `is_active` is mapped to its translated label before export so the file shows "Active"/"Inactive" rather than a raw boolean.
- **Add Business Unit** — navigates to `/business-units/new`. Wrapped in `<Can permission="cluster.create">`.

**Correction to the last sync's documented behavior:** the **empty-state** Add Business Unit button (shown when the table has no rows and no search term) is now correctly wrapped in the same `<Can permission="cluster.create">` gate as the header button — a `cluster.read`-only session no longer sees a clickable Add button that would only bounce them to a 403. (The last sync's page claimed this button was *not* gated; that claim is no longer true, whether it changed or was simply mis-verified before — either way, `ListEmptyState`'s `addAction` prop is `<Can>`-wrapped in current source.)

There is no Fetch Keycloak button (that affordance exists only on the Users list) and no Hard Delete action anywhere in business-unit management.

### 2.4 Row actions

Columns in order: `code` (clickable link → edit page), `name` (clickable link → edit page; **now paired with a small `BrandMark` avatar** — the BU's `avatar.url` if set, otherwise initials derived from name/code — reintroduced to this column the same way the clusters list re-added one; a red `Deleted` badge is appended when `deleted_at` is non-null), Status (`is_active` badge — moved next to Name, ahead of Cluster, so the two things a reader actually pairs together sit together), `cluster_name` (sortable server-side via the `tb_cluster.name` column id, truncated with a title tooltip), `alias_name` (muted, truncated), Created/Updated (via the shared `auditColumns()` helper), and conditionally Deleted By (only when "Show soft-deleted" is on). The final column is a `DropdownMenu` icon button (⋯) with **three items now**, not two:

- **Edit** — `<Can permission="cluster.update" clusterId={row.original.cluster_id}>`; navigates to the edit page.
- **View History** — `<Can permission="activity_log.read" clusterId={row.original.cluster_id || UNRESOLVED_CLUSTER_ID}>` (new since the last sync, matching the cross-cutting Activity Trail feature added across the Platform SPA — see [clusters ui-screens](/en/platform/clusters/ui-screens) §4) — opens the shared `ActivityTrailSheet` for this BU.
- **Delete** — `<Can permission="cluster.delete" clusterId={row.original.cluster_id}>`; opens the Soft Delete BU `ConfirmDialog` (§5.4). Still no client-side dependency guard — a BU can be deleted regardless of what it owns.

A session whose grants cover none of these keys for a given BU's parent cluster sees an empty dropdown for that row. There is no Hard Delete option. The list calls only `DELETE /api-system/business-units/:id` (soft delete).

### 2.5 Audit columns

Unchanged in mechanism since the last sync, but now shared code: both `BusinessUnitManagement` and `BusinessUnitEdit` read every audit value through `normalizeAudit()` (`src/utils/audit.ts`), which tries the nested `audit.{created,updated,deleted}.{at,id,name,avatar}` shape first (`fromNested()`) and only falls back to the older flat shape (`fromFlat()` — `created_at`/`created_by_name` or `created_by`, etc.) when the nested value is absent or empty. An `updated` entry is included only when the record was actually edited: `everEdited` is true when the updated actor carries a name, or — absent a name — when its timestamp differs from `created`'s; a record with neither is treated as never-edited and its Updated cell is omitted (not a plain `updated_at === created_at` check, since `updated_at` defaults to `now()` on every row while `updated_by_id` is only ever written on a real update). The list's Created/Updated columns come from the shared `auditColumns()` helper rather than a page-local formatter.

## 3. `BusinessUnitEdit` — create mode (`/business-units/new`)

In create mode (`isNew = true`) the page title is the inline-editable `HeroName` (empty, "(unnamed business unit)" placeholder) and the subtitle is "Create a new business unit". Only four tabs are shown — General, Location, Formats, Technical — because Users and Licenses both need a BU to already exist (`base.push(...)` for those two tabs is conditioned on `!isNew`). Branding, the three advanced cards, Users, and Licenses are all `null` slots while `isNew`.

**No `code` field anywhere on the create form.** PR #279 removed it: the platform assigns `code` when the row is created (see [Data Model](/en/platform/business-units/data-model) §2.1, `generateBusinessUnitCode()`), and there is nothing for the operator to type or validate. `code` also dropped out of `validateRequired()`'s enforced-fields list — only `cluster_id` and `name` remain required.

**`?cluster_id=<id>` query parameter:** the initial form state reads `searchParams.get('cluster_id') || ''` and seeds `formData.cluster_id`. Reached from the Business Units section of [clusters](/en/platform/clusters) via `/business-units/new?cluster_id=<id>`, this pre-selects the Cluster field in the Details group; the operator can still change it before saving.

**BU-quota check on submit, re-sourced since the last sync:** before calling `POST /api-system/business-units`, if `cluster_id` is set the form fetches that cluster via `GET /api-system/clusters/:id` and reads `cluster.bu_cap` / `cluster.bu_used` (the Task 7 licence-view fields documented in [clusters data-model](/en/platform/clusters/data-model) §2) — **not** the retired `max_license_bu` column the last sync's page described. If `buUsed >= buCap`, the submit is blocked with an inline error before the create call is made. The backend enforces the same limit authoritatively (`business-unit.service.ts`'s `createBusinessUnit()`), so this pre-flight is a friendlier message only, not the real gate.

**Duplicate name (409):** if the backend rejects a create because another live BU in the same cluster already has this `name` (`BUSINESS_UNIT_ALREADY_EXISTS`, enforced by the `business_unit_cluster_name_u` partial index — see [Data Model](/en/platform/business-units/data-model) §2.1), the SPA routes the error onto the `name` field specifically (`isDuplicateName` detection in `doSave()`'s catch block) rather than showing a generic save-failed toast, since `name` is the field the operator actually has to change.

Submit button label: **Create Business Unit** (sticky bottom bar, always visible in create mode). On success, if the response includes an `id`, navigates to `/business-units/:id/edit` with `{ replace: true }`. If no `id` is returned, navigates to `/business-units`. **Cancel** navigates to `/business-units` without an API call.

## 4. `BusinessUnitEdit` — tabbed edit (`/business-units/:id/edit`)

`canEdit` (`hasPermission('cluster.update', { clusterId: formData.cluster_id || UNRESOLVED_CLUSTER_ID })` for an existing BU) is computed once and threaded through every tab; each control renders editable when `canEdit` is true and read-only otherwise. A pinned identity strip sits above the tab bar: logo/avatar (or initials/code placeholder), the resolved cluster name, and two clickable status badges (Active/Inactive, HQ) that toggle `is_active`/`is_hq` directly (`disabled={!canEdit}`). The BU's name is edited via `HeroName` in the page's `PageHeader` title slot, not inside this strip. The tab bar itself is sticky (`sticky top-14`/`md:top-16`, matching `Layout`'s header heights) and shows the BU's `code` chip beside the tabs so it stays visible after the identity strip scrolls out of view.

### 4.1 General tab

**Details group** — inline fields: **Code** (read-only display, mono; not an `InlineField` — there is nothing to click into edit mode, see below), **Alias** (max 10 chars — `BU_ALIAS_MAX`, bounded independently of the cluster's 3-char alias limit), **Cluster** (required `select`), **Max users** (read-only display — see below), **Description** (`textarea`, max 500 chars). Only `cluster_id` and `name` (the latter in the page header) are enforced by `validateRequired()`.

- **Code is no longer editable, on either create or edit.** The platform assigns it at creation and the backend ignores any value sent on update — `buildPayload()` deletes `payload.code` unconditionally before every save. The row only appears at all when `!isNew` (a BU being created has no code yet to show).
- **Max users is no longer a typed integer.** It now reads `activeSeats` — the sum of every currently-active row in this BU's `tb_business_unit_license` ledger (`sumActiveLicenses()`), computed in `BusinessUnitEdit.tsx` and passed down as a prop, not part of `formData`. A caption line under the value reads "from N active license(s)". There is no click-to-edit affordance on this row — the only way to change the number is to add/edit/cancel a license row on the **Licenses tab** (§4.6).

**Calculation Settings section** (`CollapsibleSection`, `forceOpen`) — unchanged in shape and location within the tab: **Calculation Method** (`average`/`fifo`) and **Default Currency** — a `<select>` populated from `GET /api/config/:buCode/currencies` (lazy-loaded once `formData.code` is known, existing BUs only), showing `code - name` per option (inactive currencies suffixed `(inactive)`) and falling back to a free-text UUID input if the fetch fails or hasn't started; a saved id absent from the fetched list is still synthesized as an extra option so the value is never silently dropped. Hidden entirely in create mode (`showCurrencyField={!isNew}`) since there is no BU code yet to fetch currencies for. In read-only mode, when `defaultCurrency` data is present (fetched inline with the BU record), a read-only currency detail panel (Code/Name/Symbol/Decimal Places/Description/Active badge) still renders below the field — re-confirmed unchanged in `CalculationSettingsSection.tsx`.

**Branding section** — existing BUs only. Two `BrandingImageUpload` controls (Logo `rect`, Avatar `square`), each `disabled={!canEdit}`. Client-side validation: JPEG/PNG/WebP, max 5 MB. Uploads via `POST /api-system/business-units/:id/logo`/`/avatar`; the page sets the preview from the returned presigned URL directly rather than refetching the whole record (so unsaved edits on other tabs are not clobbered).

### 4.2 Location tab

Unchanged in field shape from the last sync, only relocated. **Hotel** group (11 fields: name, two address lines, sub-district, district, city, province, postal code, country, latitude, longitude, plus phone and email) then **Company** group (the identical 11-field shape, `company_*`, plus a **Copy from hotel address** button that one-way-copies the ten address fields — not phone/email — into their company counterparts; goes through the normal edit-in-place path, so it marks the document dirty like any manual edit) then **Tax** group (Tax ID, Branch).

### 4.3 Formats tab

Unchanged in field shape. **Date & time** group (Timezone, Date format, Date-time format, Time format, Long time format, Short time format — all free-text, no picker) then the **Number Formats** section (Per Page/Amount/Quantity/Recipe formats, each a JSON string parsed back to an object on save, with a live preview of what the format actually renders).

### 4.4 Technical tab

This tab absorbed the module's biggest structural change.

**Configuration section** — unchanged: an editable list of `{ key, label, datatype, value }` rows (Data Type options `string`/`number`/`boolean`/`date`/`enum`/`json`), add/remove inline, no confirmation on delete.

**Database Connection section — completely rebuilt.** A BU no longer holds `host`/`port`/`database`/`user`/`password`/`ssl` at all (that whole hybrid editable form, including the guarded password-reveal button, is gone along with the Prisma column behind it — see [Data Model](/en/platform/business-units/data-model) §1, §2.4). In its place:

- **Database Pool** — a `<select>` of shared, platform-managed `tb_database_pool` records (`GET`-loaded once per mount, `perpage: 200`, active pools only plus whatever pool is already bound even if inactive or outside the first 200 — synthesized into the option list so the dropdown never silently "forgets" a bound value). Gated behind `<Can permission="database_pool.read">`: a `canEdit` session that lacks this narrower permission still sees the pool's name and the schema value read-only, plus a note that changing them needs `database_pool.read`. **Host/port/username/password are never fetched into this page at all**, in either mode — they belong to the Database Pools module (`/platform/database-pools`), out of reach from here even for a super-admin editing a BU.
- **Schema** — a free-text field for `db_schema`, validated against a Postgres-identifier pattern (`^[A-Za-z_][A-Za-z0-9_]{0,62}$`) on blur when non-empty; the field is otherwise optional.
- **"Generate schema" button (Wand2 icon) — new since the last sync, PR #280.** Fills the Schema field with a randomized name: `bu_` followed by 16 random lowercase letters/digits (e.g. `bu_k3f9x2mq7pv1zt8w`), drawn via `crypto.getRandomValues()` with rejection sampling for an unbiased alphabet (`src/utils/databasePool.ts`, `generateSchemaName()`). The button is **disabled once the Schema field holds any non-blank value** — intentionally disabled, not hidden, so the field's position doesn't jump and the operator can see that clearing the field re-enables randomizing. No client-side uniqueness check is performed (the SPA has no endpoint to list a pool's existing schema names); the random space is 36¹⁶ (~8×10²⁴), so a real collision is left to the backend to reject at provisioning time.
- **Repoint confirmation.** Changing `database_pool_id` or `db_schema` away from a value that was already saved (not from blank — a BU being configured for the first time needs no confirmation) opens a `ConfirmDialog` before Save actually submits, naming the schema being repointed to. This guards against silently reassigning an already-provisioned tenant to a different physical database.
- **Read-only rendering** shows only the pool's name and the schema string — no masking logic is needed any more because there is nothing sensitive left on this page to mask.

**Advanced cards** (existing BUs only, rendering unconditional on `canEdit`/`isSuperAdmin` — see §4.5) render at the bottom of this tab, after Database Connection, unchanged in position relative to it.

### 4.5 Advanced cards (Tenant Migrations / Tenant Seed / Interface Entitlement)

Unchanged in behavior from the last sync — still rendered on the Technical tab whenever `!isNew`, regardless of `canEdit` or `isSuperAdmin`; `isSuperAdmin` is checked only inside each card as a `disabledReason` on that card's own action buttons:

- **Tenant Migrations** (`TenantMigrationCard`) — checks pending schema migrations for this BU's tenant database and applies them via a streamed deploy with a live applied/total readout, behind a confirm dialog. Both its status-check and Apply buttons are disabled (with a "Super-admin required." tooltip) for a non-super-admin, or when the BU has no pool/schema configured yet (`hasDbConnection={!!(database_pool_id && db_schema)}`).
- **Tenant Seed** (`TenantSeedCard`) — same status-check/confirm/streamed-progress pattern for seed scripts, with a subset-selection option. Disabled the same two ways as Tenant Migrations.
- **Interface Entitlement** (`InterfaceEntitlementCard`) — controls which named interface/brand this BU may show, keyed by `buCode` independently of the rest of the document (its own Save button). Empty selection = unrestricted. Skips its data fetch entirely (rather than just disabling a button) when not super-admin or before the BU has been saved once.

None of these three cards existed before commits `8fc1124`/`88ae453`/`ccb0754`; each calls its own dedicated service, not `businessUnitService`.

### 4.6 Users tab

Existing BUs only; the tab itself is omitted from the strip in create mode. Content is the Users card (`BusinessUnitUsersCard`), largely unchanged in shape from the last sync but with two additions:

- **Cluster seat pool indicator.** When the parent cluster carries a `total_max_license_users` cap, the card shows "N / M cluster seats used" above the user table, turning destructive-colored (with a "deactivate N more users" hint) when the BU's active-user count would push the cluster over its pool. This is the **cluster's** shared seat pool, not this BU's own license ledger (§4.7) — a user active in several BUs of the same cluster still only consumes one seat of that shared pool.
- **"Shared" badge.** A user row shows a small "Shared" badge (tooltip explains) when the user is active in this BU but `frees_seat === false` — meaning they hold membership in another BU of the same cluster too, so removing them from just this BU would not free a seat in the cluster pool. This flag is backend-optional (`frees_seat?: boolean` — absent, not `false`, when the backend hasn't populated it yet); the SPA never guesses a value for it.

Dialogs (Add User to BU, Edit BU User, Remove BU User) are unchanged from the last sync — see §5.

### 4.7 Licenses tab — NEW, split out of Users (PR #276)

Previously, seat information lived inside the Users tab/card. As of PR #276 it is its own tab, backed by `BusinessUnitLicensesCard` and the `tb_business_unit_license` ledger (see [Data Model](/en/platform/business-units/data-model) §2.3). The rationale, from the card's own source comment: seats and the user roster answer two different questions — seats come from a cluster-level contract, the roster is who is actually assigned — and conflating them in one tab made "how many seats do we have" and "who is using them" compete for the same screen.

The card is **read-only summary + links** — there is no inline seat-editing form here:

- A summary line: "N seats from M active license(s)" (`sumActiveLicenses()`/count of rows where `licenseStatus() === 'active'`).
- A cluster-pool line, mirroring the Users tab's own indicator (§4.6), same over-limit styling.
- A warning badge per license that is expiring soon (`isExpiringSoon()`, threshold from `useExpiryThresholds()` — configurable per platform config, not hardcoded — showing "N days left").
- **Manage licences** button — always shown, links to `/licenses/:clusterId#seats` (the License Center — a separate [Licenses](/en/platform/licenses) module). The href is supplied by the parent page, not built here, because this same card is reused in a shell (cluster-admin) that cannot reach `/licenses/*` at all (no `subscription.read`) — a caller that can't route there passes a fallback href.
- **New subscription button — new since the last sync, PR #275.** Rendered only when the parent page supplies a `createHref` (which it does only when the session holds `subscription.manage` **and** a cluster is set on the BU — the button and the destination route `/licenses/subscriptions/new` are gated by the exact same permission, `subscription.manage`, deliberately not this page's own `canEdit`: editing a BU and selling it a licence are different authorities, and a cluster-admin session has the first without the second). The link pre-fills `cluster_id` and `business_unit_id` as query parameters so the full-page subscription form opens already scoped to this BU.
- A footer note: "Seats are managed in the License Center" — reinforcing that this tab does not itself create or edit license rows.

## 5. Dialogs

### 5.1 Add User to BU dialog

**Trigger:** the **Add User** button in the Users card header (§4.6). Only available for an existing BU, and only rendered when `canEdit`.

Loads the cluster's user list when `formData.cluster_id` is set and not yet cached (`GET /api-system/user/clusters/:clusterId`). Shows a scrollable list of cluster users not already in this BU, with an inline client-side search (username/email/full name, no debounce). After selecting a user, the selected-user display replaces the search list; an X button deselects.

Fields:
- **BU Role** — select from `BU_ROLES = ['admin', 'user']`. Default: `user`.

No `is_default` checkbox — that field exists on the join row but is not exposed in this UI (see [Data Model](/en/platform/business-units/data-model) §2.5). On submit, `POST /api-system/user/business-units` with `{ user_id, business_unit_id, role }`.

### 5.2 Edit BU User dialog

**Trigger:** the Edit (Pencil) icon on a user row — column rendered only when `canEdit`.

Editable fields: **BU Role** (`admin`/`user`), **BU Status** (Active/Inactive — the join row's `is_active`, not the global user account status). On submit, `PATCH /api-system/user/business-units/:id` with `{ role, is_active }`; the local table updates optimistically without a full re-fetch.

### 5.3 Remove BU User confirm

**Trigger:** the Delete (Trash) icon on a user row — column rendered only when `canEdit`.

Shared `ConfirmDialog`. Title: "Remove User". On confirm, `DELETE /api-system/user/business-units/:id` (the join row's own id, not `user_id`); the matching entry is removed from local state.

### 5.4 Soft Delete BU confirm

**Trigger:** the Delete row action in `BusinessUnitManagement`, itself only rendered inside `<Can permission="cluster.delete" clusterId={row.original.cluster_id}>` (§2.4).

Shared `ConfirmDialog`. Title: "Delete Business Unit". On confirm, `DELETE /api-system/business-units/:id` (soft delete). No hard-delete option exists anywhere in the BU management UI.

### 5.5 Repoint database pool/schema confirm — NEW

**Trigger:** clicking Save on the Technical tab when `database_pool_id` or `db_schema` has changed away from a previously-saved non-blank value (§4.4). Not shown for a BU being configured for the first time (going from blank to a value needs no confirmation — there is nothing to repoint away from).

Shared `ConfirmDialog`, naming the target schema in its description. On confirm, calls the actual save directly, bypassing the normal Save gate (a second `Ctrl/⌘+S` while this dialog is open is deliberately swallowed rather than falling through and saving unconfirmed).

## 6. Persisted UI state

The list page writes 6 keys to `localStorage`, unchanged from the last sync. `BusinessUnitEdit` writes no `localStorage` keys — its one piece of UI state that needs to survive a reload (the active tab) lives in the URL's `?tab=` query parameter instead (§1).

| Key | Stored type | Persists |
|---|---|---|
| `search_business_units` | string | Current search term |
| `page_business_units` | number (string) | Current page number (reset to `1` on filter or search changes) |
| `perpage_business_units` | number (string) | Rows per page |
| `sort_business_units` | string | Current sort column/direction (default `created_at:desc`) |
| `filters_business_units` | JSON array | Active status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filter_business_units_deleted` | JSON boolean | "Show soft-deleted business units" toggle state (default `false`) |

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan. **Note (2026-09-05):** the edit page's layout changed *again* since any prior capture — first to a one-document scroll, then to the current 6-tab document. Any future capture should target the tabbed layout described in §4, not the one-document layout §1 mentions only as history.

## 8. References

- `../carmen-platform/src/App.tsx` — three BU routes with `requiredPermission` (`cluster.read`/`cluster.create`/`cluster.update`) **and** `feature="business_units"`.
- `../carmen-platform/src/components/nav/platformNav.ts` — sidebar entry (`permission: 'cluster.read'`, `feature: 'business_units'`); nav item definitions live here, not in `Layout.tsx`.
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx` and `businessUnitManagement/BuSummary.tsx` — list page: dedicated summary endpoint, filters, header actions, `<Can>`-gated row action menu (Edit / View History / Delete), `BrandMark` avatar in the Name cell, CSV export column list.
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` — tabbed orchestrator: `canEdit` gating, tab state (`?tab=`), `tabsWithErrors`/`tabForField`, `doc_version` optimistic locking, BU-quota pre-flight check on create, duplicate-name (409) handling, the pool-repoint confirm gate.
- `../carmen-platform/src/pages/businessUnitEdit/BusinessUnitTabs.tsx` — tab id list, `tabForField`/`tabsWithErrors`, thin wrapper over the shared `TabStrip` component (also used by cluster-admin's BU form).
- `../carmen-platform/src/pages/businessUnitEdit/BusinessUnitDocument.tsx` — per-tab content composition; hero identity strip; sticky tab bar.
- `../carmen-platform/src/pages/businessUnitEdit/{HeroName,shared,types,InlineField}.ts(x)` — `InlineField`, `Group`, `BU_ROLES`/`BU_ALIAS_MAX` constants, `BusinessUnitFormData`/`initialFormData`.
- `../carmen-platform/src/pages/businessUnitEdit/sections/{CalculationSettingsSection,NumberFormatsSection,ConfigurationSection,DatabaseConnectionSection}.tsx` — the four remaining complex sections; `DatabaseConnectionSection` rebuilt around the database-pool picker (no more host/port/user/password fields — see §4.4).
- `../carmen-platform/src/utils/databasePool.ts` — `generateSchemaName` (the randomizer), `poolDsn`/`isDerivedName` (address formatting shared with the Database Pools module).
- `../carmen-platform/src/pages/businessUnitEdit/BusinessUnitLicensesCard.tsx`, `src/pages/licenses/useLicenseLedger.ts`, `src/utils/buLicense.ts` — the Licenses tab.
- `../carmen-platform/src/components/{TenantMigrationCard,TenantSeedCard,InterfaceEntitlementCard}.tsx` — the three advanced cards.
- `../carmen-platform/src/services/{businessUnitService,businessUnitLicenseService,databasePoolService,currencyService}.ts` — REST clients.
- `../carmen-platform/src/pages/businessUnitEdit/{BusinessUnitUsersCard,useBusinessUnitUsers}.ts(x)` — Users tab and its Add/Edit/Remove dialog logic; `frees_seat`/cluster-seat indicator additions.
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — shared upload control.
- Cross-links: [business-units](/en/platform/business-units) (module landing; §4 gate matrix), [clusters](/en/platform/clusters) (parent cluster; source of `?cluster_id` navigate-to-new; same tabbed-edit redesign pattern), [users](/en/platform/users) (other surface mutating `tb_user_tb_business_unit`), [Data Model](/en/platform/business-units/data-model).
