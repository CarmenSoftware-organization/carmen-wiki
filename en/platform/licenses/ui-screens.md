---
title: Licenses — UI Screens
description: LicenseCenter's four tabs, ClusterLicenseDetail's three sections, the SubscriptionForm and shared LicensePurchaseForm, and the legacy /subscriptions redirect behaviour.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, licenses, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Licenses — UI Screens

> **At a Glance**
> **Screens:** `LicenseCenter` (`/licenses`, 4 tabs) &nbsp;·&nbsp; `ClusterLicenseDetail` (`/licenses/:clusterId`, 3 tabs) &nbsp;·&nbsp; `SubscriptionForm` (`/licenses/subscriptions/{new,:id/edit}`) &nbsp;·&nbsp; `LicensePurchaseForm` — **one component, two modes**, switched by a `config` prop (`/licenses/seats/*`, `/licenses/bu-quota/*`) &nbsp;·&nbsp; **Legacy:** `/subscriptions*` redirect into `/licenses/...` &nbsp;·&nbsp; **Shared visual:** `LicenseCoverageBar` — a div-based (no chart library) horizontal timeline of coverage intervals, used on all three `ClusterLicenseDetail` tabs &nbsp;·&nbsp; **No View History / Activity Trail** — unlike most other modules in this plan, this module has no `activity_log.read`-gated audit-trail action anywhere on its screens &nbsp;·&nbsp; **No e2e suite** — every claim below is sourced from implementation, not from a test spec

## 1. Overview

The module's four routes render five components, three of which share one loaded dataset across tabs rather than each fetching its own copy — deliberately, so a summary strip can never disagree with the tab beneath it. Two purchase kinds (seats, BU quota) share **one** edit form (`LicensePurchaseForm`), switched entirely by the `LicenseKindConfig` passed in from the route (see [Data Model](/en/platform/licenses/data-model) §2.1–2.2 and the [landing page](/en/platform/licenses) §3.1 for what the config changes). Every screen reads its "expiring soon" thresholds from `useExpiryThresholds()`, never a hardcoded number (see [Data Model](/en/platform/licenses/data-model) §6).

All four screens carry the SPA's standard furniture — `TableSkeleton` on first load, `EmptyState` for an empty result, toast feedback on mutations, `doc_version`-based optimistic-lock saves with a conflict toast + reload on `409`, the `useUnsavedChanges` navigation guard while a form is dirty, `useGlobalShortcuts` (⌘/Ctrl+S to save, Escape to cancel), and a dev-only `DevDebugSheet` exposing each screen's raw API response. **This module has no View History / Activity Trail action anywhere** — every other module task in this plan documents a cross-cutting `activity_log.read`-gated "View History" item on its list rows and edit-page headers; a direct grep of `src/pages/licenses/` and `LicenseCenter.tsx` for `activity_log.read`/`ActivityTrailSheet`/`PLATFORM_SCOPED_RECORD` returns nothing. This module simply never received that feature.

## 2. `LicenseCenter` (`/licenses`)

### 2.1 Fleet Capacity band

A `PageHeader` ("Licenses") sits above the shared `FleetCapacity` component — the identical band [Clusters](/en/platform/clusters)' own list uses, reading the same unfiltered `GET /api-system/clusters/summary`. Its "BU quota expiring" stat is clickable and toggles a client-side `expiringSoonFilter` that narrows the **By cluster** tab's table only — the band's own totals are never filtered by it, since they must always describe the whole fleet regardless of which tab or filter is active below.

### 2.2 The four-tab switch

A `TabStrip` (desktop) / `<Select>` (mobile, `sm:hidden`, since four tabs at 386px width leave the fourth tab's label only 4px visible) switches between:

| Tab | Component | Content |
|---|---|---|
| By cluster | `ClusterLicenseTable` | One row per cluster: BU-quota and seat capacity meters, quota-expiry date/badge, cluster active/inactive status, Updated audit column |
| By subscription | `SubscriptionTable` (rendered `embedded`) | The fleet-wide subscription list — every contract across every cluster |
| By seat license | `PurchaseLicenseTable` (`config={SEAT_CONFIG}`) | Every seat-purchase row across every business unit |
| By BU quota | `PurchaseLicenseTable` (`config={BU_QUOTA_CONFIG}`) | Every BU-quota-purchase row across every cluster |

The active tab is written to **both** the URL (`?tab=`) and `localStorage` (`license_center_view`) on every change, and on load the URL wins over storage — a shared deep link to `?tab=seat` always opens on that view even if the recipient's browser last had a different tab open. An unrecognised or stale `?tab=` value (a typo, or a value from a version of the app that used different tab names) is corrected in place: the page renders its fallback view and rewrites the URL to match, rather than leaving the address bar claiming a view that is not actually showing.

### 2.3 `ClusterLicenseTable` — By cluster

Columns: **Cluster** (code, links to `/licenses/:clusterId`) · **Name** · **BU Quota** (a `CapacityMeter` of `bu_used`/`bu_cap`; a cluster with `bu_cap = 0` shows "No licence" text instead of a 0/0 meter, since zero capacity and "no licence purchased at all" read identically on a bare ratio) · **Seats** (a `CapacityMeter` of the cluster's aggregate seat usage/capacity) · **Quota Expires** (the date `v_cluster_bu_cap`'s `cap_end_date` gives, with a warning badge once `daysLeft <= thresholds.bu_quota_days`; a perpetual or absent expiry renders a plain dash, not the words "No expiry" repeated on every row) · **Status** (the **cluster's own** `is_active` flag — an exception-only Inactive badge, not a licence-status column) · **Updated** (shared `AuditMeta`/`auditColumns()`). Default sort `code:asc`.

Search is a plain text box; the Filters sheet carries two independent groups — a **Status** group (Active/Inactive on the cluster) and a **License** group of three backend-recognised special keys (`bu_quota_missing`, `bu_over_limit`, `seats_full`) that the backend translates into an id list against the same views this page's numbers come from, so a filter and the table's own numbers can never disagree about which clusters qualify. These are not real column names — sending one to a backend that does not yet recognise it fails hard (a Prisma error on an unknown `where` key), which is why the frontend must always ship behind the backend that defines them.

### 2.4 `SubscriptionTable` — By subscription

The fleet-wide contract list, `embedded` inside `LicenseCenter` (its standalone, non-embedded rendering path — with its own `<Layout>`/`<PageHeader>` — is dead in production routing today: no route mounts `<SubscriptionTable>` without `embedded`, now that `/subscriptions` redirects to `/licenses` rather than to a bare subscription list). Columns: **Subscription** (number, links to the edit form) · **Cluster** · **Business Unit** · **State** (the backend-computed `active`/`inactive`/`expired`, plus a separate warning "Expiring soon" badge computed client-side from `thresholds.subscription_days`) · **Features** (count) · **Period** (`start_date → end_date`) · **Created**/**Updated** (shared `AuditMeta`). Default sort `end_date:desc` with an `id:asc` tiebreaker appended to every sort value the table sends — the backend has no default `orderBy` at all, and a single-column sort with ties would silently reshuffle rows across pages.

A `SubscriptionSummary` band above the table (clickable filter chips, `SummaryFilterKey`) and a Filters sheet narrow the list by cluster and state. Header actions are **Export** (CSV of the current page) and **Add Subscription** (`<Can permission="subscription.manage">`, navigates to `/licenses/subscriptions/new` with no prefilled query params — creating from here means picking both cluster and BU on the create form itself, unlike creating from a business unit's own edit page, which prefills both). **There is no row-actions menu and no Delete anywhere in this table** — the only thing a row's Subscription/Cluster links do is navigate to the edit form; a one-item "Edit" dropdown that only duplicates an already-clickable link was removed as redundant chrome, and Delete itself was removed because a soft-deleted subscription can never be surfaced again by any endpoint, making a delete button nobody could verify or undo worse than no button at all. `subscriptionService.delete()` still exists in the client and the backend route still enforces `subscription.manage` on it, but no UI in this module calls it.

### 2.5 `PurchaseLicenseTable` — By seat license / By BU quota

One component, `config`-switched, listing every purchase row of one kind across the whole fleet. Columns: **License Number** (links to `/licenses/{seats|bu-quota}/:id/edit`) · **Cluster** (seat kind only — `config.showCluster`, since a seat's owner is a BU and the table also states which cluster that BU belongs to; BU-quota rows omit this column because the owner already **is** the cluster) · **[Business Unit | Cluster]** (the owner, label switches with `config.kind`) · **Amount** (`licensed_users`/`licensed_bus`) · **Coverage** (`start_date – end_date` as plain text) · **Status** (computed client-side from dates — `active`/`scheduled`/`expired`, plus `superseded`/`cancelled` for the BU-quota kind only; not a sortable column, since it is not a real backend field) · **Reference No** · **Created** (this table's rows carry no `updated_at` on either DTO, so there is no Updated column here, unlike every other Management-style table in this module). A Filters sheet offers only `active`/`scheduled`/`expired` regardless of kind — `superseded`/`cancelled` are deliberately left off the filter list even for the BU-quota tab, since a filter button that returns nothing while the seat tab is open would be a control that lies about what it can do.

CSV export (client-side, current page only) adds four audit columns (Created/Updated At/By) beyond the visible table columns.

## 3. `ClusterLicenseDetail` (`/licenses/:clusterId`)

### 3.1 Header and health strip

`PageHeader` shows the cluster's name (or "Cluster not found or deleted" vs. a generic "unavailable" message, distinguishing a genuine 404 from any other load failure) with its code as the subtitle. Beneath it, `LicenseHealthStrip` is a single summary line — not a card grid like the list page's Fleet Capacity band, because this page already has exactly one cluster to describe and nothing to compare it against — surfacing, in one glance: BU-quota cap/used/days-left, total active seats and the count of BUs with zero seats, and subscription total/expired/expiring-soon. Every number on the strip and every number inside the three tabs beneath it come from **the same page-level data load** (`useLicenseLedger`, `useClusterSeatLicenses`, `useClusterSubscriptions`, all owned by `ClusterLicenseDetail` itself, not by the tab sections) — the sections receive their data as props rather than fetching independently, specifically so the strip's totals and a tab's own rows can never drift apart when one request succeeds and a duplicate one fails.

### 3.2 Three tabs, shared timeline visual

A `TabStrip` switches **Quota** / **Seats** / **Subscriptions**, reading and writing `?tab=` — and additionally accepting the legacy hash forms `#seats`/`#subscriptions` that the "Manage licences" links on [Business Units](/en/platform/business-units)' and [Clusters](/en/platform/clusters)' own edit pages still point at, so an existing cross-link into this page keeps landing on the right tab. All three sections draw a `LicenseCoverageBar` per row group — a plain nested-`<div>` horizontal timeline (no charting library; solid = covered, gap = uncovered, a vertical line = today) sharing one fixed time window per table (three months back, twelve months forward from "now," rounded to month boundaries) so that two bars of equal length on the same screen always represent equal spans of calendar time.

- **Quota** (`BuQuotaSection`) — two cards. The first shows the winning BU-quota licence's coverage bar, the `buUsed`/`cap` ratio (reading the same `cluster.bu_used` field [Clusters](/en/platform/clusters)' own edit page and `ClusterLicenseTable` read, never a client-side count of the loaded BU list), and a purchase-ledger table (Quota, Start, End, Status, Reference, Note, and — when `canManage` — row actions: **Edit**, **Cancel** (soft, irreversible, a separate confirm dialog naming the projected BU count after cancelling), and **Remove** (hard `DELETE`, a second, differently-worded confirm dialog)). The second card ranks every business unit in the cluster (HQ first, then oldest-created, matching `v_cluster_bu_quota`'s own `ORDER BY` exactly — see [Data Model](/en/platform/licenses/data-model) §3.2) and marks any BU whose rank exceeds the cap with an **Over limit** badge, plus that BU's own subscription coverage bar reused from the Subscriptions tab's data so the two tabs never compute two different answers to "does this BU have an active contract."
- **Seats** (`SeatSection`) — a single table, one row-group per business unit (not one card per BU — an earlier one-card-per-BU layout was replaced specifically because each BU no longer needs its own data fetch, and a ~360px empty-state card per BU with zero licences no longer earns its footprint once ten or more BUs are involved). Row groups are ordered by **severity**, not alphabetically — a BU that failed to load, then one with zero seats, then one expiring soon, then everything healthy — so a page opened to find problems does not bury them under alphabetical ordering. Each BU's header row carries the active-seat total, its coverage bar, and (when `canManage`) an **Add seat license** link; each licence row beneath it offers **Edit** and **Remove** (hard delete) only — **there is no Cancel action for seats anywhere on this screen**, matching the schema fact that `tb_business_unit_license` has no `cancelled_at` column at all (see [Data Model](/en/platform/licenses/data-model) §2.2).
- **Subscriptions** (`SubscriptionSection`) — the cluster-scoped subset of the same contract list the fleet-wide `SubscriptionTable` shows, with the same state badges and expiring-soon logic, and (when `canManage`) an Add Subscription link that prefills this cluster's id.

`canManage` (`hasPermission('subscription.manage')`) is computed **once**, at the page level, and passed down as a single prop to all three sections — none of them re-checks the permission itself, precisely so the page has one source of truth for "can this session mutate anything here" rather than three call sites that could theoretically disagree.

## 4. `SubscriptionForm` (`/licenses/subscriptions/new`, `/licenses/subscriptions/:id/edit`)

**Create mode** (`isNew`, no `:id`): a two-column layout — the form on the left, a live `SubscriptionDraftPlate` preview on the right (sticky on `lg`+ screens, stacked below the form on narrower ones) showing the cluster/BU/dates as they are typed. The cluster picker (`useAllClusters`, a bounded 10-page fetch, never `perpage: -1`) and the BU-of-that-cluster picker (fetched only once a cluster is chosen) are both required; a "Term" helper offers 14 month-end presets (every month of the current year, plus January/February of next year) that fill the end date from a chosen start date in one click, alongside the plain date input. Start date defaults to today. On submit, only the five fields the create endpoint accepts are sent — `subscription_number` is never part of the payload; the server always issues it.

**View/edit mode** (`:id/edit`): an `IssuedSubscriptionPlate` (identity + dates + a computed "days left"/"expired N days ago" line, driven by the backend's `state`, never a client-recomputed one) replaces the old scrollspy-nav layout entirely — a left navigation rail for two cards on a page that scrolled barely half a screen was removed as cost with no benefit, the same simplification [Licenses' shared purchase form](#5-licensepurchaseform-licensesseats-licensesbu-quota) received. Below the plate: a `SubscriptionInfoCard` (start/end dates and status, editable only when `subscription.manage` is held — `editing={canEdit}`, not a separate toggle button) and a "Purchased Groups" card (`GroupSelectionCard`, §3.2 of the [landing page](/en/platform/licenses)) letting an editor pick feature groups from the catalog, each expandable read-only to show what it grants, plus a warning when the contract carries `feature_keys` but no `group_ids` (a pre-group-system contract that has not yet been reconciled). The BU picked at creation is never editable afterward — the edit form has no BU field at all, only a read-only identity on the plate.

A sticky bottom bar (shown only when unsaved changes exist) carries **Save Changes** (`<Can permission="subscription.manage">`) and **Cancel** (reverts to the last-loaded values). Because `subscription.manage` gates only the Save button and the field-editability flag — not the route itself, which requires only `subscription.read` — a read-only session can open this exact URL and see every field, just not change or save any of them (see [Permissions](/en/platform/licenses/permissions) §3).

## 5. `LicensePurchaseForm` (`/licenses/seats/*`, `/licenses/bu-quota/*`)

The **same component and the same route handler code** serves four routes, distinguished only by the `config: LicenseKindConfig` and `mode: 'create' | 'edit'` props `App.tsx` passes in — see [Data Model](/en/platform/licenses/data-model) §2.1–2.2 and the [landing page](/en/platform/licenses) §3.1 for the full seat-vs-BU-quota difference table. What the screen itself looks like:

**Create mode** requires an owner supplied entirely via query parameters (`?bu=` or `?cluster=`, plus an optional `?ownerLabel=` for a readable name) — there is no owner picker in this form; every entry point into it (the "Add seat license"/"Add BU-quota license" links on `SeatSection`/`BuQuotaSection`, and on [Business Units](/en/platform/business-units)' own Licenses card) supplies the owner directly. If the owner param is missing, the page renders a dedicated "missing owner" empty state rather than a broken form — this can only happen from a hand-edited or stale URL.

**View/edit mode** shows an `IssuedLicensePlate` — the licence's own identity (number, owner, cluster where applicable), a computed status badge, a "days left"/"expired N days ago" line coloured against the kind-specific threshold, and, for the BU-quota kind only, the owning cluster's current usage (`bu_used`) read via `config.readUsage`. Beneath the plate, a single `LicenseFieldsCard` — used by both create and edit, differing only by an `editing` boolean — holds Amount, Reference No, a segmented "Has end date / No expiry" toggle (**shown only for BU quota** — `config.showNoExpiry`; the seat kind has no such toggle and no perpetual concept at all), the coverage dates, and — BU-quota only — a free-text Note field (`config.showNote`). **A cancelled BU-quota licence's fields become permanently read-only** (`canEditFields = canEdit && !isCancelled`) with an explanatory banner above the card, rather than silently accepting edits to a record that no longer grants anything; seat licences have no cancelled state to reach this branch at all.

A **Cancel this license** action (destructive-styled, at the foot of the page, behind a `ConfirmDialog`) appears **only when `config.cancel` is non-null** — i.e. only on the BU-quota kind. There is no equivalent button anywhere on a seat licence's edit page, matching the schema fact that no cancel endpoint exists for `tb_business_unit_license` rows at all. Neither purchase kind's edit page offers a hard-delete action — that exists only from the per-cluster ledger's own row menu (§3.2 above), not from the dedicated single-licence URL.

## 6. Legacy `/subscriptions*` redirects

| Old path | Renders | Destination |
|---|---|---|
| `/subscriptions` | `<Navigate to="/licenses" replace>` | License Center, default **By cluster** tab — **not** the By subscription tab |
| `/subscriptions/new` | `<Navigate to="/licenses/subscriptions/new" replace>` | The create form, unchanged behaviour |
| `/subscriptions/:id/edit` | `SubscriptionEditRedirect` | Reads the `:id` param and redirects to `/licenses/subscriptions/:id/edit` with the same id — an old bookmark to a specific contract opens that exact contract |

All three use `replace: true`, so the redirect does not leave an extra entry in browser history for the Back button to land on. `/licenses/subscriptions/...` is canonical; testers should treat the legacy paths as "still works," not as "the current URL to use" — nothing in the SPA links to `/subscriptions*` any more.

## 7. References

All paths are `../carmen-platform` unless prefixed otherwise.

- `src/pages/licenses/LicenseCenter.tsx` — the four-tab landing screen, Fleet Capacity band, tab persistence.
- `src/pages/licenses/ClusterLicenseTable.tsx`, `src/pages/licenses/SubscriptionTable.tsx`, `src/pages/licenses/PurchaseLicenseTable.tsx` — the four tab bodies.
- `src/pages/licenses/ClusterLicenseDetail.tsx` — the per-cluster detail screen and its shared data-loading hooks (`useLicenseLedger`, `useClusterSeatLicenses`, `useClusterSubscriptions`).
- `src/pages/licenses/LicenseHealthStrip.tsx`, `src/pages/licenses/LicenseCoverageBar.tsx` — the summary strip and the shared timeline visual.
- `src/pages/licenses/sections/{BuQuotaSection,SeatSection,SubscriptionSection}.tsx` — the three `ClusterLicenseDetail` tabs.
- `src/utils/businessUnitRank.ts` — `rankBusinessUnits()`/`countOverLimit()`, the Over-limit badge logic (§3.2).
- `src/pages/licenses/SubscriptionForm.tsx`, `src/pages/licenses/subscriptionCreate/{SubscriptionCreateForm,SubscriptionDraftPlate,subscriptionTerm}.tsx`, `src/pages/licenses/subscriptionEdit/{IssuedSubscriptionPlate,SubscriptionInfoCard,GroupSelectionCard}.tsx` — the subscription form and its supporting components.
- `src/pages/licenses/LicensePurchaseForm.tsx`, `src/pages/licenses/licenseKindConfig.ts`, `src/pages/licenses/licenseEdit/IssuedLicensePlate.tsx`, `src/pages/licenses/plate/plateParts.tsx` — the shared purchase form and its kind-switching config.
- `src/App.tsx` (lines 183–249) — every route this page documents, plus the legacy redirects (§6).
- `src/hooks/useAllClusters.ts`, `src/hooks/useExpiryThresholds` (`src/context/ExpiryThresholdContext.tsx`) — shared data hooks used across the forms.
- `src/pages/licenses/subscriptionEdit/SeatsCard.tsx` — **not part of the live UI.** A cluster-level seat-pool card that exists in source and has its own test file, but is imported by no production page component (`SubscriptionForm.tsx` renders no such card); a comment in its sibling test file claims it is "still used at License Center," which is stale relative to current source — confirmed by a full-repo grep finding zero non-test imports. Not documented as a screen above because it is not reachable from any route.

**Cross-links:** [Licenses landing](/en/platform/licenses) &nbsp;·&nbsp; [Data Model](/en/platform/licenses/data-model) &nbsp;·&nbsp; [Permissions](/en/platform/licenses/permissions)
