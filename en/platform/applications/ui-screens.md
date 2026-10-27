---
title: Applications — UI Screens
description: The ApplicationManagement list and the ApplicationEdit form, including the grouped-accordion API Names selector and its ChipInput fallback.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, applications, ui
editor: markdown
dateCreated: 2026-06-10T12:30:00.000Z
---

# Applications — UI Screens

> **At a Glance**
> **Screens:** `ApplicationManagement` (`/applications`) · `ApplicationEdit` (`/applications/new`, `/applications/:id/edit`) &nbsp;·&nbsp; **New since last sync (2026-09-02, `#254`/`#255`):** the Access column and the edit-page hero/API-access card now share one **reach ruler** (`utils/apiReach.ts`'s `reachOf()`) — a bar + `granted/catalogSize` fraction anchored against the live API catalog (1,140 keys / 181 modules as counted 2026-10-27), replacing the old "All APIs"/"N APIs" badge; the list's Status column was folded away in September and has since returned as a four-value service status; Device is now quiet text, not a badge; authority-verb chips (`delete`/`approve`/`submit`/…) are tinted and sorted first; stale/retired grants and never-reached modules are now called out explicitly &nbsp;·&nbsp; **Also new:** cross-cutting **View History** (`activity_log.read`, `BACKSTAGE_SCOPED_RECORD`) on the list row menu and the edit hero; the Registry strip reads a dedicated `GET /api-system/applications/summary` endpoint (2026-08-24) instead of a client-side sweep; Created/Updated now render via the shared `auditColumns()`/`AuditMeta` (relative time + tooltip, `everEdited` suppression) instead of a fixed timestamp string; all three routes carry a `feature="applications"` flag &nbsp;·&nbsp; **Edit layout:** still a view/edit toggle (unlike clusters/business-units' one-document rewrite) &nbsp;·&nbsp; **Signature UI:** API Names selector — accordion grouped by module, filter box, per-module All/None, action-only button labels, authority-verb tinting &nbsp;·&nbsp; **Fallback:** `ChipInput` free-text entry when the catalog fetch fails &nbsp;·&nbsp; **New since 2026-10-09:** service-status modes (Running / Maintenance / Read-only / Disabled), a bypass-users list, and an `x-app-secret` card, all in a "Live controls" zone of the edit page (§3.5), plus a Status column/filter and Registry segments on the list &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list page

![Applications — UI Screens screen](/screenshots/platform/applications/ui-screens.png)

![Applications — UI Screens form screen](/screenshots/platform/applications/ui-screens-form.png)

## 1. Overview

Applications follows the SPA's standard two-screen Management/Edit pattern: a server-side `DataTable` list with debounced search, Sheet filters, CSV export, a **Registry** summary strip, and persisted state; plus a create/view/edit page built around an `ApplicationIdentityHero` above a two-column **API access** / **Settings** layout. Three things are module-specific. First, the **App ID** treatment — the record UUID is surfaced read-only via a copyable chip in the hero (and, on the list, inline under the application's name) because it is the `x-app-id` credential operators need to copy into client configuration. Second, the **API Names selector**, the module's signature component (§3.4): an accordion of catalog keys grouped by module, shown only while "Allow all APIs" is unchecked (with a warning banner in its place when `allow_all` is on) — since `#255` (2026-09-02) it also tints authority-verb chips and reports stale/untouched-module counts. Third, both screens now carry the cross-cutting **View History** action (`activity_log.read`, scoped with the `BACKSTAGE_SCOPED_RECORD` sentinel since an application has no cluster) — the list's row-actions dropdown and the edit page's hero actions slot — the same Activity Trail feature documented for [clusters](/en/platform/clusters)/[business-units](/en/platform/business-units)/[users](/en/platform/users). Recording started 2026-08-31 (`AUDIT_RECORDING_STARTED_ON_PHASE_2`).

Both screens ship the dev-only **Debug Sheet** (amber floating button, `import.meta.env.DEV` only) exposing the raw JSON of `GET /api-system/applications` (list) or `GET /api-system/applications/:id` (edit) — the quickest way for QA to confirm the actual envelope and audit nesting. Both also register the SPA's global keyboard shortcuts (`useGlobalShortcuts`): on the list the search shortcut focuses the search input; on the edit form the save shortcut submits while editing and the cancel shortcut exits edit mode (view/edit route only, not create).

## 2. `ApplicationManagement` — list (`/applications`)

### 2.1 Layout and header actions

Header (`PageHeader`): title "Application Management" / subtitle "Manage applications and their API access", with two actions — **Export** (client-side CSV of the loaded page, 10 columns: Name, App ID, Description, Access, Status, Expected back (`status_until`), Created At, Created By, Updated At, Updated By — the four audit columns were added `2026-08-22` alongside the `auditColumns()` migration; file `applications-<YYYY-MM-DD>.csv`; disabled while loading or empty) and **Add Application** (navigates to `/applications/new`; wrapped in `<Can permission="application.create">`). Below the header sits the **Registry** summary strip (§2.1a), then the search/filter row.

### 2.1a Registry strip

An `ApplicationRegistrySummary` card summarises **every application** in the registry — since 2026-08-24 (`99a93c8`, one of 5 Management pages migrated the same day) it reads a dedicated, unfiltered `GET /api-system/applications/summary` endpoint rather than sweeping every row with a client-side `perpage: -1` fetch:

- A large total count. Underneath, a **Service status** segment (stacked bar over the four statuses, legend showing Running always and the others only when non-zero) when the summary carries `statuses`; a backend that predates status modes sends none, and the band falls back to "`<n>` active" / "`<n>` active · `<n>` inactive".
- An **"API access scope"** proportion bar — full-access (`allow_all`, styled in the warning colour, since an unrestricted app is audit-worthy) vs. scoped (explicit list), with a legend; the "Full access" legend entry itself switches to a warning triangle icon when the count is non-zero.
- An **"App secret"** segment (shown only when the summary carries `secrets`): Enforced / Unenforced / None, which sum to full-access + scoped.
- A **"Devices"** breakdown — one chip per device value in use, ordered `web`/`mobile`/`desktop`/`pos` then alphabetically (`byPlatform()`, applied at render so the rule holds regardless of the order the endpoint sends `devices`), each showing its count via the shared `formatDevice()` label.

The response also carries a fleet-wide `deleted` (soft-deleted) count that **this card does not render** — on the wire but unused, the same "counted but not shown" pattern found on other summary bands. Shows a skeleton on first load; a failure with no prior data yet renders a retry banner (`FetchErrorState`), while a failure **after** a successful load keeps the previous numbers visible (not cleared) with a dimmed treatment and an announced "couldn't refresh" cue rather than blanking the band — mirroring `ClusterManagement`'s Fleet Capacity strip. The main table underneath is unaffected either way.

### 2.2 Search and filters

A debounced (400 ms) search input over `name`/`description` (server-side via the `search` param), plus a **Filters** Sheet (description "Filter applications by status and device") with two groups: a **Status** group — four toggle buttons (Running / Maintenance / Read-only / Disabled, multi-select) that translate to the `advance` query `{ where: { status: { in: [...] } } }` when any is selected (stored values that are not one of the four are discarded on load) — and a **Device** dropdown whose options are "All devices" (clears the filter) plus `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`); a chosen device adds `{ where: { device } }` to the same `advance` clause. Each active filter (status and device) counts toward the filter badge and renders as a chip under the search row with per-chip remove and a "Clear all" link.

### 2.3 Columns

**The App ID and Description columns do not exist as separate columns** — they are folded under Name (mirrors the equivalent "report-templates-style" table adopted across the SPA). Since `897ebdc4` (2026-10-09) every row carries a **Status** column again, now showing the four-value service status; the old exception-only Inactive badge beside Name was replaced by a Secret-required chip:

| Column | Rendering |
|---|---|
| Name | A small stack: the name (link to `/applications/:id/edit`) with a **Secret required** outline `Badge` (key icon) beside it, shown only when the application has `require_secret` on (the same chip the edit hero shows); the record UUID underneath in monospace muted text with an inline copy-to-clipboard icon button (`Copy`/`Check` toggle, 2 s confirm, toast on copy); and the description (if any) below that in smaller muted text |
| Access | **No longer a plain badge.** `ApplicationReachCell` (new, `#254`): a bar sized against the live API catalog plus a `granted/catalogSize` fraction (e.g. `207/900`), switching to the warning colour with an alert-triangle icon once reach equals the whole catalog; `allow_all` renders as `n/n` on the same ruler rather than the word "All APIs". A second, smaller line names the module count reached. Fixed-width column (`lg:w-56`) so every row's bar is comparable; **sortable since 2026-09-09** (PR #293) through a backend-derived `access` key — `DERIVED_SORT_KEYS = ['access']` in `micro-cluster`'s `application.service.ts:119`, which also fixed a bug the sortable-headers audit surfaced: the service used to place a hard-coded `orderBy` *after* the caller's query args, silently discarding every `sort` the headers sent. If the list's own (separate, best-effort) catalog-size fetch fails or hasn't resolved yet, the bar and denominator disappear and the cell falls back to a bare granted count — there is no retry UI for this fetch |
| Device | Quiet muted text via `formatDevice(row.original.device || 'web')` (e.g. `POS`, `Mobile`) — falls back to `web` when absent, same as before; no longer a `Badge`, since `#254` judged a per-row pill redundant with the Registry strip's device histogram above the table |
| Status | Fixed-width (`w-36`), not sortable. A coloured dot plus the label (Running muted; Maintenance, Read-only and Disabled in foreground weight with warning / info / hollow dots). The cell's tooltip shows the "Expected back …" time, or the passed-time warning once `status_until` is in the past (an alert-triangle appears beside the label). Read through `statusOf()`, which falls back to `is_active` for a backend without status modes |
| Created | Rendered via the shared `auditColumns()`/`AuditMeta` helpers (since `a85a166`, 2026-08-22 — one of 5 Management tables migrated off a bespoke `fmt()`): relative time (e.g. "5mo ago") with the absolute timestamp as a `title` tooltip, actor name on the line below. Reads `normalizeAudit()`, which tries the **nested** `audit.created` shape first and falls back to the **flat** `created_at`/`created_by_name` columns only when nested is absent |
| Updated | Same `AuditMeta` cell shape from `audit.updated`/flat fallback. **Not a raw `updated_at === created_at` comparison** — the actor is included only when `everEdited` (an actor name is present, or its `at` differs from the created timestamp) |
| Actions | `⋯` dropdown — see §2.4, now three items |

Default sort is `name:asc`. First load renders a `TableSkeleton` sized to the current column count; subsequent loads overlay a "Loading applications..." scrim on the existing table.

### 2.4 Row actions and delete dialog

The actions dropdown carries **Edit** (navigate to the edit route) wrapped in `<Can permission="application.update">`; **View History** (new — opens the shared `ActivityTrailSheet` for this application) wrapped in `<Can permission="activity_log.read" clusterId={BACKSTAGE_SCOPED_RECORD}>`, using `onSelect` rather than `onClick` so the dropdown menu finishes closing before the sheet opens (avoids two Radix focus traps colliding); and **Delete** (destructive styling) wrapped in `<Can permission="application.delete">`. Delete opens a `ConfirmDialog` ("Delete Application — Are you sure you want to delete this application? This action cannot be undone."); confirming calls `DELETE /api-system/applications/:id`, toasts, and refetches the page (and reloads the Registry strip). There is no delete affordance anywhere else in the module.

### 2.5 Empty state and persisted UI state

An empty result renders an `EmptyState` card (AppWindow icon) whose title is always "No applications yet"; only the description beneath it varies — `No applications matching "<term>"` when a search term is active, or "Get started by creating your first application." with an inline **Add Application** CTA when none is. **Corrected since the last sync: this CTA is now `<Can permission="application.create">`-wrapped**, same as the header button — the gap previously flagged in [Permissions](/en/platform/applications/permissions) is closed.

| `localStorage` key | Stored type | Persists |
|---|---|---|
| `search_applications` | string | Search term |
| `filters_applications` | JSON string array | Status filter selections |
| `devicefilter_applications` | string | Device filter selection (empty = all devices) |
| `page_applications` | number string | Current page |
| `perpage_applications` | number string | Page size |
| `sort_applications` | string | Sort (`column:dir`, default `name:asc`) |

The edit page persists no UI state.

## 3. `ApplicationEdit` (`/applications/new`, `/applications/:id/edit`)

### 3.1 Create mode (`/applications/new`)

Title "Add Application" (`PageHeader`, no hero — the hero needs an existing `id` for its App ID chip and audit lines). Both cards (API access, Settings) render immediately editable in the two-column layout described in §3.3. On submit the SPA validates `name` (required; also validated on blur, with the error cleared on focus), calls `POST /api-system/applications` (payload includes `doc_version: undefined`, which the client drops), toasts, and redirects to `/applications/:id/edit` for the created id (`replace: true`), falling back to the list when the response carries no id.

### 3.2 View mode (`/applications/:id/edit`, default)

Loads via `GET /api-system/applications/:id` (a hero + two-card skeleton while in flight, matching the loaded layout exactly). A dedicated **not-found** state (new since the last sync) replaces the whole shell with an `EmptyState` ("Application not found... Back to applications") when the id doesn't resolve to a live record, rather than rendering the edit page over blank data.

Above the form sits the **`ApplicationIdentityHero`**: an `AppWindow`-icon avatar tile, the name as the page's `<h1>`, Device and Active/Inactive badges, an App ID chip (monospace, with its own copy button) shown once the record exists, and Created/Updated audit lines. **Since `#255` (2026-09-02) the reach line is the same ruler the list uses** (`utils/apiReach.ts`'s `reachOf()`, catalog-anchored): when the catalog has loaded, a bar plus `granted/catalogSize` fraction (warning-toned with an alert-triangle icon at full reach) and a "`N` of `M` modules" line — with a "`N` can delete or approve" authority count appended when the granted set includes any authority-verb keys. If the catalog hasn't loaded (or failed), the hero falls back to the unanchored summary it always had: "Full access to every endpoint" (warning colour, alert-triangle icon) or "`<n>` endpoint(s) across `<m>` module(s)" / "No endpoints granted yet" in muted text. In view mode, the hero's actions slot shows the (always-visible, mode-independent) **View History** button (`<Can permission="activity_log.read" clusterId={BACKSTAGE_SCOPED_RECORD}>`) and a single **Edit** button wrapped in `<Can permission="application.update">` — without the latter key the page is permanently read-only, since Save is unreachable outside edit mode.

The two-column body renders read-only in view mode: the **API access** card shows either the warning banner (`allow_all` — with, new since `#255`, a note when `api_names` are still stored underneath: "Still holds `N` scoped endpoints...") or, when names are granted, read-only grouped badges — one sub-list per module (`groupApiNames` over the loaded `api_names`), each labelled with a catalog-anchored `known/total` fraction (falling back to a bare count when the catalog hasn't loaded) and, when any grants point at retired catalog keys, a `+N` warning annotation naming them apart from the numerator. Chips within a module are ordered authority-verbs-first, each labelled with the action segment only (`actionOf`) and carrying the full key in its `title` attribute (or "No endpoints granted." when empty); an authority-verb chip is tinted (warning border/outline) with its `title` naming what it does. A "`N` can delete or approve in this app's name" legend line appears above the groups when any are granted, and a "`N` more module(s) never reached" line appears below them, naming every catalog module this application's `api_names` never touch (`#252`'s "say what a grant does not reach" rule). The **Settings** card shows Name/Description as static fields; **Device and Status now render as quiet read-only text** (`ReadOnlyField`), not badges — `#255` removed the duplicate badge treatment 60px below the hero's own Device/Active badges.

### 3.3 Edit mode — two-column layout

The Edit toggle (hero action button) snapshots the current form, then switches both cards to editable. **The single "Application Details" card from the prior sync no longer exists** — the form is now `grid-cols-1 lg:grid-cols-[1fr_minmax(300px,340px)]`: a wide left column holds the **"API access"** card (title + "Which endpoints this app may call." description) with the `allow_all` checkbox and the selector; a narrower right column holds a **sticky** ("Settings") card with the remaining fields:

| Field | Edit-mode control | Notes |
|---|---|---|
| Full access to every API (`allow_all`) | Checkbox, in the API access card | Labelled "Full access to every API" with a description line; checking it replaces the selector with a warning banner (also shown in view mode) |
| API Names | Grouped accordion selector (§3.4), in the API access card | Only when `allow_all` is unchecked |
| Name * | Text input, in the Settings card | Required; blur + pre-submit validation |
| Description | Text input, in the Settings card | Optional |
| Device | `<select>` of `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`), in the Settings card | Defaults to `web` (also the fallback when a loaded value is outside the option set); **renders as quiet read-only text via `formatDevice()` in view mode, not a badge** — the hero already carries a Device badge, so `#255` de-duplicated the rail's copy to plain text |
| ~~Active (`is_active`)~~ | **Removed.** | **Renders as plain read-only text ("Active"/"Inactive") in view mode, not a Status badge** — same de-duplication as Device, since the hero's own Active/Inactive badge already states it |

**App ID is no longer a Settings-card field row** — it now lives only in the hero chip (§3.2), not repeated in the form.

A **sticky bottom bar** (new since the last sync, replacing the previous in-card Save/Cancel row) shows **Save Changes** / **Create Application** (with a spinner while saving) and **Cancel**, plus an "Unsaved changes" / "No changes" indicator, fixed to the viewport bottom while `editing` is true. Cancel restores the pre-edit snapshot and exits edit mode (in create mode it navigates back to the list). Unsaved changes (any diff against the snapshot while editing) arm the `useUnsavedChanges` navigation guard, and the global keyboard shortcuts trigger save and cancel. On a successful update the page **re-fetches the application (refreshing `doc_version`) and drops back to view mode**; a stale save (`409`) shows a conflict toast and reloads instead of overwriting.

### 3.4 The API Names selector

The module's signature component, rendered inline in the API access card (no separate component file). Options come from `GET /api-system/applications/api-catalog`, fetched once on mount; until groups arrive the box shows "Loading catalog…", and a genuinely empty catalog ("No API endpoints are defined in the catalog yet.") is now distinguished from the loading state (a fix since the last sync).

- **Accordion grouped by module** — one row per `ApiCatalogGroup`, in a bordered scroll container (`max-h-80`, ~320 px). Each module row is a real ≥44px tap target (`min-h-11` on the toggle, not an overlay); it packs a chevron (expand/collapse), the module name, a `selected/total` count badge (filled variant once anything is selected), and an **All/None** button (a `HIT_SLOP_44` overlay on this compact button, since only one per module row is needed) that selects or clears the whole module in one click.
- **Filter input** — matches against the module name *or* any `api_name` (case-insensitive). A module-name match shows the entire group; otherwise the group narrows to matching names. Matching groups **auto-expand** while a filter is active (manual chevron toggling is suspended); a non-matching filter shows `No API names matching "<term>"`.
- **Expand all / Collapse all** — a single toggle scoped to the currently *visible* groups, so it composes with the filter.
- **Per-key toggle buttons** — inside an expanded group, each `api_name` is a small button labelled with the **action segment only** (`actionOf(api)`), with the full key in the `title` attribute; selected keys render filled with an `X` glyph. **Since `#255` (2026-09-02), authority-verb keys** (`isAuthorityAction()` — `delete`, `approve`, `submit`, `revoke`, and similar; deliberately narrower than "any write", so `create`/`update`/`upload` are not tinted) **render tinted** (warning-coloured border when unselected, warning fill when selected) with a `title` explaining why. **These chips deliberately do NOT get a 44px hit-slop overlay** — at their compact size (`h-7`) with only a 6px row gap, a centred 44px overlay would bleed past each edge further than the gap and let vertically-adjacent rows' tap zones overlap; on this permission-granting surface an overlapping tap could grant the wrong API, so the chips were kept at their smaller, non-overlapping size instead (a documented, deliberate accessibility trade-off, not an oversight). **The "N selected" line was replaced by a live meter** (`#255`): a bar + `granted/catalogSize` fraction on the same ruler as the list and the hero, plus a "`N` can delete or approve" count when any authority-verb keys are selected — both update on every click (verified in the source commit by clicking Delete and watching the meter move, e.g. `207→208`).
- **`ChipInput` fallback** — if the catalog fetch fails (`catalogFailed`), the selector degrades to a free-text chip input ("Type an api_name and press Enter") behind a `FetchErrorState` retry banner, so grants remain editable without the catalog; entries are comma-joined into the same `api_names` array.

Selections live in flat form state (`api_names: string[]`); on save the service converts them to the write payload's `details.add[]` (replace semantics — see [Data Model](/en/platform/applications/data-model) §5).

### 3.5 Live controls (existing records only)

Below the form, a `ZoneHeading` "Live controls" ("Each section applies with its own button and takes effect right away — not with Save.") introduces the status and secret cards; the form above it is headed "Access definition" ("Changed with Edit, applied with Save."). The zone is not rendered on `/applications/new`. The status card takes the left grid cell with the bypass-users section embedded inside it (separated by a rule); the secret card takes the right cell on `lg` and up, and appears only when the loaded record carries a boolean `has_secret`; otherwise the status card spans the row.

**Service status card** (`ApplicationStatusCard.tsx`):

- A radiogroup of the four statuses, each with a one-line effect description and a "Current" badge on the saved one. A non-running draft reveals a message textarea (max 1000 characters) and an **Expected back** `datetime-local` field ("Shown to users only — the app does not switch back by itself").
- **Apply status** is disabled until the draft differs from the saved state. Clicking it validates that an entered expected-back time is in the future ("Expected-back time must be in the future"), then opens a confirm dialog titled "Switch {name} to {status}?" with the per-status effect text (about a minute to take effect; maintenance → 503 for callers off the bypass list except sign-in; read-only → only GET requests; disabled → 403 for everyone, bypass users included). Re-applying the current status with a changed message/time is a "notice only" update with its own title and a non-destructive button.
- A saved non-running status shows who changed it and when ("Changed by {name} · {when}"), and a warning line once the announced time has passed ("the app stays {status} until someone switches it back").
- Self-lock: if the page's own App ID is the one being edited, every status except Running is disabled with a note; a `409 APP_SELF_LOCK` from the server toasts "Refused — this page uses this App ID, so it cannot leave Running". A `409` for a stale `doc_version` shows the shared conflict toast and refetches.
- Without `application.update` the card is a read-only view (badge, message, expected-back).

**Bypass users** (`ApplicationBypassUsersCard.tsx`, embedded): a `UserMultiSelect` ("Search users by name or email…"), "No one — every user is held to the status" when empty, and its own **Save bypass list** button (sends the whole set via `PUT …/bypass-users`; toasts "Bypass list saved"). The description reads "Keep full access during Maintenance and Read-only. Has no effect on Disabled." Without `application.update` the saved users show as badges.

**App secret card** (`ApplicationSecretCard.tsx`):

- Header: "App secret" / "Clients send it as the x-app-secret header." with an Enforced / Not enforced badge. With no secret yet: "No secret yet" and a **Generate secret** button (manage only).
- With a secret: the masked stub (`cas_` + dots + last four, announced to screen readers as "Secret ending in …"), a Reveal/Hide eye button and a Copy button (both for `application.secret.reveal`, or while a freshly generated plaintext is on screen). Revealing calls `GET …/secret`, shows the 44-character plaintext in place, and re-masks after 30 seconds (`REMASK_MS`) with a draining bar (static when the user prefers reduced motion). Copy reveals first when masked. A response that arrives after the admin navigated to another application is discarded, so one app's plaintext never appears on another app's card.
- Meta lines: "Rotated {when} by {name}" and, while the grace window is open, "Previous secret valid until {when}".
- For `application.secret.manage`: a **Require secret** switch (disabled until a secret exists, and disabled when turning it on would lock this very page out) with a confirm dialog each way ("Make sure every client of this app already sends it" / "anyone who knows the App ID can call the API as this app again"), and a **Rotate secret** button whose dialog text changes when the app is enforced ("Every client must switch to the new secret within 24 hours…") or is this page's own app ("set REACT_APP_API_APP_SECRET to the new secret and redeploy this site within 24 hours").
- Error routing (`reportError`): `APP_SECRET_INVALID` is handled by the axios interceptor's own toast; `APP_SECRET_SELF_LOCK`, `APP_SECRET_KEY_UNAVAILABLE` ("…check SECRET_ENCRYPTION_KEY") and `APP_SECRET_MISSING` get their own toasts (missing and not-found also refetch the record); a version conflict shows the conflict toast and refetches.
- The list and the Registry strip surface the same state: the Secret-required chip on rows and the App-secret segment.

## 4. References

All paths are `../carmen-backstage` unless prefixed otherwise.

- `src/pages/ApplicationManagement.tsx` and `applicationManagement/{ApplicationRegistrySummary,ApplicationReachCell}.tsx` — list page: Registry summary strip (dedicated summary endpoint), the reach-bar Access column (`ApplicationReachCell`, `#254`), Name-column App-ID/description/Inactive-badge fold-in, filter Sheet, CSV export, `<Can>` gates (incl. row View History), `auditColumns()`-based Created/Updated, persisted keys.
- `src/pages/ApplicationEdit.tsx` and `applicationEdit/ApplicationIdentityHero.tsx` — hero card (shared reach ruler, authority count, View History action), two-column API-access/Settings form, `allow_all` fork with the dormant-grants note, the inline accordion selector (authority tinting, stale/untouched-module accounting, selection meter), ChipInput fallback, `doc_version`-aware save flow, not-found gating.
- `src/utils/apiReach.ts` — `reachOf()`, the single reach-arithmetic function shared by `ApplicationReachCell` and `ApplicationIdentityHero`.
- `src/utils/apiCatalog.ts` — `moduleOf` / `actionOf` / `groupApiNames` (shared by the selector and the read-only badge view) plus (new, `#255`) `verbOf` / `isAuthorityAction` / `countAuthority` and the `AUTHORITY_VERBS` set.
- `src/utils/device.ts` — `formatDevice()`, the single device-label formatter used by the Registry strip, the list's Device column, and the Settings rail's read-only text.
- `src/utils/permissions.ts` — `BACKSTAGE_SCOPED_RECORD`, the sentinel `clusterId` the View History gates use.
- `src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail,constants}.tsx` — the View History feature; `AUDIT_RECORDING_STARTED_ON_PHASE_2` (2026-08-31).
- `src/utils/audit.ts` and `src/components/{AuditMeta,auditColumns}.tsx` — `normalizeAudit()` (nested-first, flat-fallback; `everEdited` suppression) and the shared Created/Updated columns.
- `src/utils/docVersion.ts` — optimistic-lock helpers.
- `src/services/applicationService.ts` — endpoints, `toWritePayload` (incl. `doc_version`), `getApiCatalog` with grouping fallback, `getRegistrySummary()`.
- `src/App.tsx` — route definitions (lines 139–162), each with `feature="applications"`.
- `src/pages/applicationEdit/{ApplicationStatusCard,ApplicationBypassUsersCard,ApplicationSecretCard,ZoneHeading}.tsx`, `src/utils/{applicationStatus,applicationSecret}.ts` — the Live controls zone (§3.5); `src/pages/ApplicationEdit.tsx:930` is where the zone starts.
- `CLAUDE.md` — "Application Management Specifics" section (read/write asymmetry, grouped catalog pattern).

**Cross-links:** [Applications landing](/en/platform/applications) &nbsp;·&nbsp; [Data Model](/en/platform/applications/data-model) &nbsp;·&nbsp; [Permissions](/en/platform/applications/permissions)
