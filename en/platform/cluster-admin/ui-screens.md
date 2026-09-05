---
title: Cluster Admin — UI Screens
description: ClusterAdminEntry, ClusterProfile, BusinessUnitList/BusinessUnitForm, ClusterUsers and the read-only ClusterAdminLicenses, plus the shared Profile screen — every one scoped to a single :clusterId and contrasted with its platform-side twin.
published: true
date: '2026-09-06T11:00:00.000Z'
tags: book/platform, cluster-admin, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Cluster Admin — UI Screens

> **At a Glance**
> **Screens:** `ClusterAdminEntry` (`/cluster-admin`) &nbsp;·&nbsp; `ClusterProfile` (`/cluster-admin/:clusterId/cluster`) &nbsp;·&nbsp; `BusinessUnitList`/`BusinessUnitForm` (`/cluster-admin/:clusterId/business-units[/:buId/edit]`) &nbsp;·&nbsp; `ClusterUsers` (`/cluster-admin/:clusterId/users`) &nbsp;·&nbsp; `ClusterAdminLicenses` (`/cluster-admin/:clusterId/licenses`, fully read-only) &nbsp;·&nbsp; shared `Profile` (`/cluster-admin/:clusterId/profile`) &nbsp;·&nbsp; **Gate on every per-cluster screen:** no RBAC permission key — gated instead by cluster membership via `isClusterAdminOf`, checked before the feature flag (see [Permissions](/en/platform/cluster-admin/permissions)) &nbsp;·&nbsp; **In-page writes are gated only by having reached the route** — `ClusterProfile` and `BusinessUnitForm` compute `canEdit` from reachability alone, not from any permission or role check inside the component &nbsp;·&nbsp; **No e2e suite** — every claim below is sourced from `../carmen-platform` implementation directly

## 1. Overview

Every screen in this module shares the same shell, `ClusterAdminLayout`, and most share a small set of conventions worth stating once rather than per screen: a `PageHeader`, skeleton placeholders on first load (not spinners), a dev-only `DevDebugSheet` exposing the raw API response by tab, and — on `ClusterProfile`/`BusinessUnitForm` — `doc_version`-based optimistic-lock saves, the `useUnsavedChanges` navigation guard, and `Ctrl/⌘+S`/`Escape` via the shared `useGlobalShortcuts` hook. Four of the six screens (`ClusterProfile`, `BusinessUnitList`, `BusinessUnitForm`, `ClusterUsers`) individually catch a mid-session 403 (membership revoked while the page was open) and render `ClusterAccessLost` in place of the body — see [Landing](/en/platform/cluster-admin) §3.6. `ClusterAdminLicenses` does not (§7).

This module has **no cross-cutting View History / Activity Trail action** anywhere — a grep of `src/pages/clusterAdmin/` for `activity_log.read`/`ActivityTrailSheet`/`PLATFORM_SCOPED_RECORD` returns nothing, the same negative finding [Licenses](/en/platform/licenses/ui-screens) recorded for its own module.

## 2. `ClusterAdminEntry` — landing (`/cluster-admin`)

Guarded by `AuthedRoute` only (authentication, no membership check yet — see [Landing](/en/platform/cluster-admin) §1). Behaviour branches on the freshly-loaded `adminScope`:

- **`adminScope === null`** — still resolving; renders a loading state rather than deciding early.
- **Exactly one administered cluster, and not a super admin** (`!adminScope.all && adminScope.clusters.length === 1`) — `<Navigate replace>` straight to `/cluster-admin/:id/cluster`. A super admin sees the picker even when their own local page happens to hold only one row, since `adminScope.all` short-circuits this branch — `adminScope.clusters` is only ever a searchable page for them, never the complete set.
- **Zero clusters** — an `EmptyState` ("No clusters to administer"), which the component's own comment frames deliberately as not a 403 in substance: the caller is authenticated, they simply administer nothing.
- **Otherwise (several clusters, or a super admin)** — a responsive card grid, one card per administered cluster, each navigating to that cluster's `/cluster` route on click or Enter/Space.

`ClusterAdminEntry.tsx` renders inside a bare `Layout` with an empty `navItems` array — there is no sidebar at all on this one screen, since no cluster is selected yet for `buildClusterAdminNav` to scope against.

## 3. `ClusterProfile` — cluster home (`/cluster-admin/:clusterId/cluster`)

The landing target once inside a cluster: for `/cluster-admin`'s single-cluster redirect, for the brand link, and for every `ClusterSwitcher` selection. Reads as a licence position first, an identity form second:

1. **`CapacityStrip`** — the two finite pools (BU quota, seats) the cluster draws down, side by side; each pool links to `/licenses` (this module's own, at `licensesTo`) once it crosses into warn/over territory, or unconditionally when BU quota is `0` (nothing purchased at all). Shared with `ClusterAdminLicenses` (§7) and the `BuPropertyPlate` hero on `BusinessUnitForm` (§5).
2. **`ClusterBusinessUnitsCard`** and **`ClusterPeopleCard`** — read-only summaries (max 8 business units, max 5 administrators shown before a "+N more" line), each linking to the full Business Units or Users screen. Both cards source their data straight from the single `GET /clusters/:id` call this page already makes — no second request — and the component's own comment is explicit about the design choice: "Eleven names on a landing page is a table nobody asked for — the Users page already has one."
3. **An Identity card** (`DetailsSection`, reused verbatim from the platform `ClusterEdit.tsx`) — a **Pencil → Save/Cancel** edit toggle, editing only `name` and `alias_name`. `code` is not shown (`showCode={false}`) and `is_active` renders **read-only even while editing** (`canEditPlatformFields={false}`) — the component's own comment explains why: the backend silently strips `max_license_users`, `is_active`, and `info` from a membership admin's cluster update, a discarded write with no error surfaced, so the page never offers a control for a field the backend will not actually change.
4. **A Branding card** — logo/avatar upload, always editable by a cluster admin (uploads use dedicated presigned-URL endpoints, not the same write path the backend silently truncates).

**Contrast with the platform twin:** [Clusters — UI Screens](/en/platform/clusters/ui-screens) documents `ClusterEdit` as a `ClusterPlate` hero plus a 3-tab body (Licensing/Business Units/Users). `ClusterProfile` has none of that structure — no tabs, no Licensing tab (licensing here is the separate, fully read-only `/licenses` route, §7), no Business Units/Users editing tabs (those are the separate `BusinessUnitList`/`ClusterUsers` routes, §4/§6). What survives from the platform form is only the identity/branding editing surface, narrowed to the two fields a membership admin is actually allowed to change.

A 403 mid-session renders `ClusterAccessLost` in place of everything below the header.

## 4. `BusinessUnitList` — cluster BUs (`/cluster-admin/:clusterId/business-units`)

A `DataTable` list in the same established Management-page pattern as `BusinessUnitManagement`, narrowed to one cluster — but with three deliberate differences from its platform twin:

1. **No create action anywhere** — no header button, no empty-state CTA. `BusinessUnitForm.tsx`'s own comment states the reason: "creating a BU consumes `max_license_bu` (BU quota), which is a platform decision" — the route `/cluster-admin/:clusterId/business-units/new` does not exist at all; the sibling edit route always requires an existing `:buId`.
2. **An "Over limit" rank badge** on the Name column, using the identical formula [Business Units](/en/platform/business-units) documents for its own module (`rankBusinessUnits()`/`countOverLimit()`, matching the DB view `v_cluster_bu_quota` exactly) — duplicated into this page's own i18n namespace rather than imported cross-module, per the source comment's stated convention that a page namespace is owned by its own slice.
3. **Header actions are Export only.** The list is otherwise the same shape: debounced search, a status Filters sheet, `localStorage`-persisted state (its own `_ca_business_units`-suffixed keys, distinct from the platform list's), and Created/Updated audit columns via the shared `auditColumns()`.

The Over-limit rank/count comes from a second, unpaginated fetch of every BU in the cluster (needed because ranking requires seeing every row, not just the current page) that fails open — a failed fetch simply leaves the cap unknown and the badge unrendered, rather than showing a wrong number.

A 403 mid-session renders `ClusterAccessLost` in place of the table.

## 5. `BusinessUnitForm` — cluster BU editor (`/cluster-admin/:clusterId/business-units/:buId/edit`)

Edit-only — there is no create route (§4). `canEdit` is computed as `!accessLost`: the component's own comment states this plainly — "identical permission scope: whoever can reach the route can edit" (`สิทธิ์เท่าเดิมเป๊ะ: ใครเข้า route ได้ก็แก้ได้`) — a change of the platform's own edit-scope model is explicitly deferred to a future spec, not attempted here.

**Layout:** a `BuPropertyPlate` hero (logo/avatar, an inline-editable name, `is_active`/`is_hq` toggles, the read-only `code`, and a `SeatMeter` for the cluster-wide seat pool) sits above a **5-tab document** — Overview, People, Hotel, Company, Configuration — replacing the platform edit page's single continuous form for this narrower scope.

**Contrast with the platform twin:** [Business Units — UI Screens](/en/platform/business-units/ui-screens) documents a **6-tab** platform form (General, Location, Formats, Technical, Users, Licenses). This module's tab split differs deliberately, not just in count:

| Cluster-admin tab | Platform equivalent | What differs |
|---|---|---|
| Overview | (no equivalent) | A `TabJumpList` summarising the other four tabs' contents — added because an empty-looking tab label otherwise forces clicking through all four to learn what's set |
| People | Users tab (General's Licenses split-out on platform) | Combines the platform's separate Users and Licenses tabs into one: a fully editable `BusinessUnitUsersCard` (add/edit/remove BU membership) plus a **read-only** `BusinessUnitLicensesCard` summary |
| Hotel | Location (combined with Company) | Split from Company deliberately — the source comment states a cluster admin reads "the hotel is the property they run, the company is who invoices for it" as two different jobs, unlike a platform admin reading both as one "geography" |
| Company | Location (combined with Hotel) | See above; retains the one-way "Copy from hotel address" action |
| Configuration | Formats + part of Technical | **Fully read-only** — no `canEdit` branch at all. Timezone, date/time/number formats, and calculation method are shown as plain text; they round-trip unchanged in the save payload so a save from this page can never silently clear them |

Two things the platform form has that this one omits entirely, both by design per the component's own comment: the `config[]` key-value table (provisioned once at BU setup, not a cluster admin's job — still loaded and still round-tripped in the save payload, so it survives a save from this page untouched) and the database-pool section (`database_pool_id`/`db_schema` are platform-only fields, gated on a platform role at the backend, and this page neither reads nor writes them).

**The one write asymmetry worth flagging for testers:** the People tab's `BusinessUnitUsersCard` is the *same component* the platform `BusinessUnitEdit` renders, but the two pages compute `canEdit` completely differently — the platform page ties it to `cluster.update`, an RBAC permission; this page ties it to `!accessLost`, i.e. simply having gotten past `ClusterAdminRoute`. A cluster admin can therefore add, edit, and remove BU users with **no permission key of any kind involved**, the same "route guard is the whole check" shape as the rest of this module. The sibling `BusinessUnitLicensesCard` on this page is passed no `createHref` at all (so no "New subscription" button ever appears) because a cluster admin holds no `subscription.manage` and could not pass `PrivateRoute` on `/licenses/subscriptions/new` if the button existed; its `manageHref` points at this module's own `/licenses` route rather than the platform's, since a cluster admin cannot reach `/licenses/*` without `subscription.read` either.

Address fields collapse into plain text with a click-to-expand toggle (`AddressBlock`) rather than showing 10 input boxes per address permanently — a UI simplification with no permission implication.

A 403 mid-session renders `ClusterAccessLost` in place of the whole document; a BU whose `cluster_id` no longer matches the URL's `:clusterId` (a stale bookmark, or a hand-edited URL) has its URL corrected in place via `navigate(..., { replace: true })` rather than rendering the BU under the wrong cluster's chrome.

## 6. `ClusterUsers` — cluster membership and invitations (`/cluster-admin/:clusterId/users`)

A tabbed shell (Members / Invitations), not a Management-page list — the data set is one cluster's roster, not a paginated catalog. This is an **entirely different data model** from the platform [Users](/en/platform/users) module: this screen manages `tb_cluster_user` membership rows and cluster invitations, never the underlying `tb_user` platform account record. There is no way to create, edit identity fields on, or delete a `tb_user` from this screen at all — only to grant, change, or revoke that user's standing within this one cluster.

- **Members tab** (`MembersTable`) — search-filterable list of active cluster members. A row's action menu offers **Make Admin**/**Make User** (`clusterService.updateClusterUser`) and **Remove** (`clusterService.deleteClusterUser`), both plain writes with no permission string of any kind — membership alone, via the route guard, is the entire check. There is deliberately **no Status column and no Activate/Deactivate action**: the backend endpoint this table reads (`GET /api-system/user/clusters/:clusterId`) hard-filters to `is_active: true` and never selects the column at all, so every row's `is_active` would read `undefined` — a Status column here could only ever show one value, and a Deactivate action would remove the row from a list that has no way to show it again.
- **Invitations tab** (`InvitationsTable` + `InviteUserDialog`) — pending/terminal invitations, plus a dialog to create a new one (email, cluster role, and a per-business-unit role/default picker scoped to the cluster's own BUs). **Resend**/**Revoke** are gated on the invitation's *terminal* states (`accepted`/`declined`/`revoked`), not on `status === 'pending'` — the list's displayed `status` includes a computed `expired` value for a lapsed-but-still-`pending` database row, and resending a lapsed invitation is precisely why an admin opens this tab, so gating on the working state instead of the terminal ones would block exactly that. A `409` on create is routed to whichever tab actually answers it — "already a member" switches to Members with the email pre-filled into search; "already pending" switches to Invitations — rather than showing a bare error.

Both writes here are again purely route-gated, with no RBAC permission key involved anywhere on this screen.

## 7. `ClusterAdminLicenses` — read-only capacity view (`/cluster-admin/:clusterId/licenses`)

The one screen in this module confirmed to have **no write path anywhere**. A grep of the page and its four child components (`CapacityStrip`, `SeatsByBuTable`, `QuotaLedgerCard`, `BuRankingCard`) for any of `onClick|<Link to=|<Button|navigate(|Service\.(create|update|delete|cancel)|<form|onSubmit` finds only two "Retry" buttons on a failed fetch (`QuotaLedgerCard.tsx:75`, `SeatsByBuTable.tsx:58`) — no create, edit, delete, or navigate-to-write affordance of any kind. The page's own comment explains why this is not a hidden-button decision but a structural one: a cluster admin holds no RBAC permission in their session at all (membership comes from `tb_cluster_user`, not `tb_user_tb_platform_role`), every licence-write endpoint requires `subscription.manage` at the backend, and this page therefore never even calls `GET /platform/subscriptions` — there is nothing useful to do with subscription data it cannot act on.

Layout:

1. **`CapacityStrip`** — same component and same two pools as `ClusterProfile` §3, reading the cluster's own `bu_used`/`bu_cap`/`users_count`/`total_max_license_users` fields directly (not a client-side sum of the rows loaded below), so this strip and `ClusterProfile`'s never disagree.
2. **`SeatsByBuTable`** — one row per business unit in the cluster, each showing its own summed active-seat count and nearest expiry, fetched in parallel per BU (`useClusterSeatLicenses`, `Promise.allSettled` since there is no per-cluster seat endpoint) and explicit about a failed-to-load row: it renders "could not load" text, never a silent `0`, since in this system zero seats means new users genuinely cannot be invited.
3. **`QuotaLedgerCard`** (collapsed by default) — every BU-quota purchase row for the cluster, with the single currently-winning licence (`activeLicense`, newest `start_date`) badged "In force" — reinforcing the winner-take-all counting rule [Licenses — Data Model](/en/platform/licenses/data-model) §3 documents, never a sum.
4. **`BuRankingCard`** (collapsed by default) — every business unit ranked by the same `rankBusinessUnits()` formula as `BusinessUnitList`'s Over-limit badge (§4), answering "if the cluster is over quota, which BU gets cut first" — a question only worth surfacing once the strip above has already turned a warning colour.

**This is the one screen that does not implement the `ClusterAccessLost` mid-session-403 pattern** the other four module screens share (§1) — a grep of `ClusterAdminLicenses.tsx` finds only an `isNotFoundError` branch for a deleted/missing cluster, no 403-specific handling. See [Permissions](/en/platform/cluster-admin/permissions) §4, edge case 9.

[Licenses](/en/platform/licenses) §4/§5 already documents this exact screen from its own module's side, using the identical gate description.

## 8. Shared `Profile` (`/cluster-admin/:clusterId/profile`)

The same `Profile` component the platform mounts at `/profile`. [Profile](/en/platform/profile) §1.1 documents both mountings side by side in full (guard, nav, brand identity, brand-mark destination, header extra) — this page agrees with that account rather than restating it. The one thing worth repeating here: this is the single per-cluster route `App.tsx` passes `ClusterAdminRoute` with **no `feature` prop at all** (`App.tsx:603-604`), so unlike the other five per-cluster routes it has no feature-flag gate whatsoever — membership is the entire check, with nothing checked afterward.

## 9. Shared visual components

- **`CapacityStrip`**/**`AllocationTicks`** — the licence-pool visuals shared by `ClusterProfile` and `ClusterAdminLicenses`. `AllocationTicks` draws one tick per licence up to 40; past that it falls back to a plain percentage bar, since individual ticks stop being legible past roughly that count.
- **`SeatMeter`** — the compact cluster-wide seat gauge shown in `BusinessUnitForm`'s hero; deliberately never shows the BU's own seat purchases (that number lives in `BusinessUnitLicensesCard`, §5) to avoid two different meanings of "licensed" appearing in the same visual block.
- **`ClusterAccessLost`** — the shared mid-session-403 empty state (§1, §7).
- **`CollapsibleGroupCard`** — the collapsed-by-default card pattern used by `QuotaLedgerCard`/`BuRankingCard`, distinct from the platform's own `CollapsibleSection` (`CardTitle`/`CardDescription`-based) so the two do not read as two different design systems on one screen.

## 10. References

All paths `../carmen-platform` (HEAD `157a65e`).

- `src/pages/clusterAdmin/ClusterAdminEntry.tsx` (§2)
- `src/pages/clusterAdmin/ClusterProfile.tsx`, `src/pages/clusterAdmin/{CapacityStrip,ClusterBusinessUnitsCard,ClusterPeopleCard,SummaryCardHeader}.tsx` (§3)
- `src/pages/clusterAdmin/BusinessUnitList.tsx`, `src/utils/businessUnitRank.ts` (§4)
- `src/pages/clusterAdmin/BusinessUnitForm.tsx`, `src/pages/clusterAdmin/businessUnitForm/{BuPropertyPlate,ClusterBuDocument,ClusterBuTabs,SeatMeter,AddressBlock}.tsx`, `src/pages/businessUnitEdit/{BusinessUnitUsersCard,BusinessUnitLicensesCard,useBusinessUnitUsers}.tsx` (§5)
- `src/pages/clusterAdmin/{ClusterUsers,MembersTable,InvitationsTable,InviteUserDialog}.tsx`, `src/services/clusterAdminService.ts` (§6)
- `src/pages/clusterAdmin/ClusterAdminLicenses.tsx`, `src/pages/clusterAdmin/licenses/{BuRankingCard,CollapsibleGroupCard,QuotaLedgerCard,SeatsByBuTable}.tsx`, `src/pages/licenses/{useLicenseLedger,useClusterSeatLicenses}.ts` (§7)
- `src/pages/Profile.tsx` (§8)
- `src/pages/clusterAdmin/ClusterAccessLost.tsx`, `src/pages/clusterAdmin/AllocationTicks.tsx` (§9)

**Cross-links:** [Cluster Admin landing](/en/platform/cluster-admin) &nbsp;·&nbsp; [Permissions](/en/platform/cluster-admin/permissions) &nbsp;·&nbsp; [Clusters — UI Screens](/en/platform/clusters/ui-screens) &nbsp;·&nbsp; [Business Units — UI Screens](/en/platform/business-units/ui-screens) &nbsp;·&nbsp; [Users — UI Screens](/en/platform/users/ui-screens) &nbsp;·&nbsp; [Licenses](/en/platform/licenses) &nbsp;·&nbsp; [Profile](/en/platform/profile)
