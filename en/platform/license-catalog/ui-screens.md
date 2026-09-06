---
title: License Catalog — UI Screens
description: The LicenseCatalog shell's tab mechanics in full, FeatureCatalogPanel (Features), GroupCatalogPanel (Bundles), LicenseFeatureGroupEdit, and the shared feature-picker/composition-bar components.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, license-catalog, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# License Catalog — UI Screens

> **At a Glance**
> **Shell:** `LicenseCatalog` (`/license-features`, `/license-feature-groups`) — one component, `tab` prop, tabs are routes not state &nbsp;·&nbsp; **Features tab:** `FeatureCatalogPanel` — read-mostly, per-row `state` toggle only, no create/delete &nbsp;·&nbsp; **Bundles tab:** `GroupCatalogPanel` — full CRUD list for `tb_license_feature_group` &nbsp;·&nbsp; **Editor:** `LicenseFeatureGroupEdit` (`/license-feature-groups/{new,:id/edit}`) — one component, two modes &nbsp;·&nbsp; **Shared picker:** `FeatureSelectionCard` — used **only** by the editor now, not by any sales screen &nbsp;·&nbsp; **No View History / Activity Trail** — a grep of `src/pages/licenseCatalog/`, `src/pages/licenseFeatures/`, `LicenseCatalog.tsx`, and `LicenseFeatureGroupEdit.tsx` for `activity_log.read`/`ActivityTrail`/`PLATFORM_SCOPED_RECORD` returns nothing &nbsp;·&nbsp; **No e2e suite** — every claim below is sourced from implementation, not a test spec

## 1. Overview

Three components render across four routes. `FeatureCatalogPanel` and `GroupCatalogPanel` are **panels, not pages** — `Layout` and `PageHeader` belong to the shared `LicenseCatalog` shell that wraps them, which is why each panel's own toolbar carries its Export (and, for Bundles, New group) button rather than pushing it up onto a header the other tab also uses: a primary action that swapped itself depending on which tab happened to be open would read as a stumble in work an administrator repeats every day. `LicenseFeatureGroupEdit` is a full standalone page with its own `Layout`/`PageHeader`, reached only from the Bundles tab's row links and New-group button, never nested inside the shell.

## 2. `LicenseCatalog` shell (`/license-features`, `/license-feature-groups`)

### 2.1 Tabs are routes, not client state

`TAB_PATH` maps each tab id to its own URL (`bundles` → `/license-feature-groups`, `features` → `/license-features`); `TabStrip`'s `onChange` calls `navigate(TAB_PATH[next])` rather than setting local state. Switching tabs therefore **remounts** whichever panel becomes active and triggers a fresh fetch — there is no shared cache between the two tabs. The component's own comment states the trade-off directly: both panels fetch once and are already structurally capped (the feature catalog and the bundle list are both curated data, not something that grows with product usage), so refetching on every switch costs nothing worth avoiding, and it sidesteps building a cache that would have to span two independently-permissioned routes.

### 2.2 One constant title, one switching subtitle

`PageHeader`'s `title` is always `t('pages.licenseCatalog.title')` — literally "License Catalog" — regardless of which tab is showing. Only `subtitle` changes, between `pages.licenseFeatureGroups.subtitle` ("Curated bundles of licence features, used when selling a subscription") and `pages.licenseFeatures.subtitle` ("Choose which features can still be sold. The catalog itself is generated — only the state is yours to set."). This is a deliberate identity choice, not an oversight: a title that changed per tab would read as two different screens that happen to share a URL prefix, undermining the entire premise that this is one module.

**A naming wrinkle worth stating for testers:** the sidebar rows say "License Feature Groups" and "License Features" (`platformNav.ts:21-22`), but once inside the shell, the tab labels themselves read "Bundles" and "Features" (`tabBundles`/`tabFeatures`, shorter labels used only inside the strip). A tester following the sidebar's exact wording will not find that wording repeated on the screen it opens — this is expected, not a copy bug.

### 2.3 The tab strip vanishes when only one tab is reachable

`tabs` is built by filtering `TAB_ORDER` (`['bundles', 'features']`) through each tab's own `TAB_GATE` — `hasPermission(gate.permission) && flagOf(gate.feature) === 'active'` — and `<TabStrip>` is rendered only when `tabs.length > 1`. This is a **client-side re-check** of exactly what the route guard (§4 of the [landing page](/en/platform/license-catalog)) already enforced before the panel could mount at all; it exists because both tabs share one shell, so the shell itself — not the router — is what decides whether to draw a control pointing at a tab the current session cannot open. A session holding only one of the two tab permissions sees a single, un-tabbed panel with no dead strip above it, on whichever of the two routes it can reach.

The component's own comment explains why this check does not need to wait for `flagsReady`: the route guard for whichever URL is currently mounted has already resolved both the permission and the flag before `LicenseCatalog` renders at all, so re-checking here can never observe a still-loading state — only re-deriving what has already been decided for the tab that is currently showing, plus checking the *other* tab's independent gate for whether to draw the strip.

## 3. `FeatureCatalogPanel` — Features tab

Client-filtered, not server-paginated: `licenseFeatureService.getAll()` (`GET /platform/license-features/all`) fetches every non-deleted row — including hidden ones, since the screen that hides a feature must be able to find it again to undo that — once, and every search/filter interaction operates on the in-memory result. There is no debounce on the search box and no pagination control, because the row count is structurally capped by the catalog generator (89 rows as of this writing, see [Data Model](/en/platform/license-catalog/data-model) §3), not something that grows with usage; splitting a set that size across pages previously forced an operator to open several pages to answer a question the summary bar now answers in one glance.

**Editable surface:** `state` only, one row at a time, saved immediately (`PATCH` per row, no draft/batch save) — deliberately unlike `/platform/features` (Feature Flags), where the backend accepts one PUT that overwrites the whole map at once; here every row carries its own `doc_version`, and batching several rows into one save would force a half-succeeded-save UX ("18 of 20 saved — but which two failed?") that a per-row save never has to solve. `key`/`label`/`sort_order` are read-only everywhere on this screen — they belong to the generator.

**The state summary bar (`CatalogStateBar`) counts before the state filter, after the search box** — standard facet-count behaviour: counting after the state filter too would make every unselected bucket read `0` the instant any filter was applied, making the whole bar meaningless exactly when it is being used. A count of `0` is never disabled — "nothing is hidden yet" is itself a meaningful answer a click should be able to confirm.

**`ModuleShelf` groups rows by root module**, one card per module, replacing what used to be a flat 76-to-89-row list with a repeated "Module" column value on every row. A shelf's header summarises **all children of that module, always, never the filtered subset** — a count that shrank under an active filter would misrepresent how large the module actually is; while filtering, the header instead reads "showing *N* of *total*," which describes the current view without touching the underlying fact. Children (and grandchildren, indented further — see [Data Model](/en/platform/license-catalog/data-model) §3 for why a tree can now be three levels deep) are listed depth-first, not by raw `sort_order`, so a grandchild always renders under its own parent rather than in whatever numeric band the generator assigned it.

A per-row description is shown **only when it says something the label does not already say** — most generator-authored descriptions are a bare `"View " + label`, which would otherwise repeat the row's own name on every one of 89 rows for no new information.

**Hiding is the one action gated by a confirmation, and only when it would cost someone something.** Turning a feature `inactive` needs no confirmation (it stops new sales, nothing existing changes). Turning it `hide` shows a `ConfirmDialog` naming `affected_bu_count` — the number of business units that would lose the menu item outright — **only when that count is greater than zero**; a feature nobody currently holds saves immediately. When the feature being hidden has descendants (a mid-tier node in the tree), the dialog appends a descendant count, because the runtime license evaluator drops a `hide`d key from a business unit's entitlement set before checking its descendants' ancestor chains — hiding a parent silently breaks every child's grant for anyone who holds it, even though the children's own rows never change state (see [Data Model](/en/platform/license-catalog/data-model) §3 for the full mechanism). The dialog's copy also states the action is reversible ("resets to active, and the menu returns within about a minute" — the gateway's own cache TTL) — deliberately not over-stated, since a warning that reads scarier than reality trains people to stop reading it.

`affected_bu_count` is `undefined`, not `0`, on a gateway response old enough not to send it — the row renders with no count shown at all in that case, never a printed "0," which would falsely assert nobody holds the key.

## 4. `GroupCatalogPanel` — Bundles tab

A `DataTable` of every non-deleted bundle, fetched with a bounded page size (`perpage: 200`, never `perpage: -1`) and then filtered client-side by name/code and an "active only" checkbox — the same "structurally capped, so client-side is fine" reasoning as the Features tab, since bundles are hand-curated rather than usage-scaled.

**Columns:** sort order (a small numeric chip, highlighted with a warning border when another bundle shares the same number — computed against the **full unfiltered set**, since a bundle filtered out of view still competes for the same slot on the sales form) · code (a link into `LicenseFeatureGroupEdit`, monospace) · name + description (one cell, description clamped to one line) · **Features** (a count plus, when the shared catalog total is known, a composition bar sharing one page-wide divisor — see §6 for what that divisor actually depends on) · subscription count (plain informational text on this screen; the number that becomes a warning only once someone tries to delete or deactivate the bundle it belongs to, §4.1) · active/inactive badge · a row-actions menu (Edit / Delete).

**Features composition bar — a divisor that can silently disappear.** The column's count-of-total label and bar both depend on `catalogTotal`, fetched from a **separate** request (`subscriptionService.getFeatureCatalog()`) that is deliberately decoupled from the bundle list's own load — a catalog-total failure hides the bar, it does not fail the whole screen, since `feature_count` alone (with no denominator) is still a legible number on its own. See §4.3 of the [landing page](/en/platform/license-catalog) for exactly which permission that separate request actually requires, which is **not** either of this module's own two permission pairs. The divisor can also be usable-but-suspicious in one specific way: if a bundle's stored `feature_count` ever exceeds the fetched catalog total (which can only happen once a feature is hidden after a bundle already held it — the catalog-total endpoint excludes hidden rows, the admin catalog does not), the column falls back to a bare count with no bar rather than drawing a percentage over 100%.

### 4.1 New group and row actions — gated; delete is gated but not blocked by the confirm dialog alone

The header's **New group** button, the empty-state's own New-group action, and the row-actions menu's **Edit**/**Delete** items are each wrapped in `<Can permission="license_feature_group.manage">` — a `.read`-only session sees the table and composition bars with no way to create, edit from the list, or delete.

**Deleting an in-use bundle is not blocked by the confirmation dialog's copy — it is blocked by the server.** The `ConfirmDialog` shown before delete reads a different, more serious message when `subscription_count > 0` (naming exactly how many contracts reference the bundle) versus a plain "delete this group?" when it does not — but confirming either version sends the same `DELETE` call regardless of the count. The backend rejects a delete when any live `tb_subscription_bu_group` row still references the bundle, returning an error the frontend maps to a 409 conflict; the UI surfaces it as a toast (`getErrorDetail`), and the bundle remains in the list, undeleted. Do not read the dialog's warning copy as the enforcement mechanism — it is a heads-up, not a lock; the lock is server-side.

## 5. `LicenseFeatureGroupEdit` (`/license-feature-groups/new`, `/license-feature-groups/:id/edit`)

One component serves both create and edit, distinguished only by whether `:id` is present. Layout follows *identity → composition → position and status → contents*, rather than a flat grid of six equal-weight fields: `code` (editable only at create — the field itself does not even render as an input in edit mode, only as a fixed monospace label, since the backend rejects `code` in every `PATCH` payload), `name`, `description`, then, in a fixed-width right-hand column that shares its width with the list screen's own composition-bar column so the two never disagree about what a given count means, `GroupCompositionPanel` (§6). Below a divider: `sort_order` (with the same sibling-duplicate warning border the list screen draws, computed from a separate, best-effort fetch of every other bundle's `sort_order` that fails silently rather than blocking the page if it cannot load) and a segmented "Selling / Not selling" control for `is_active` (replacing what used to be a bare checkbox with adjacent explanatory text — two mutually-exclusive states read faster as two buttons that swap places than as one box whose meaning depends on reading a sentence next to it).

**Saving is one request, or two, depending on what actually changed.** If only metadata changed, a single `PATCH` runs. If the feature selection changed too, metadata saves first (when it also changed) and the feature `PUT` runs second, **using the `doc_version` the metadata save just returned** — not the value held before either request started, since the `PATCH` has already advanced the version server-side and sending the stale one would 409 immediately with nobody having actually raced the edit. A version conflict from either request triggers the shared "someone else changed this" toast and a full reload of the record, discarding the local draft.

**Unknown feature keys are shown, not silently dropped.** A bundle can hold a key that was later removed from the active catalog (deactivated after the bundle already referenced it); `FeatureSelectionCard` renders these in a dedicated dashed-border block, separate from the tree, with a per-key remove button in edit mode — never removed automatically, since silently rewriting what a customer's contract grants without a visible action is the wrong kind of "helpful."

**A bundle's own subscription count becomes an active warning here, unlike on the list.** `GroupCompositionPanel` shows a distinct warning block once `subscription_count > 0`, and appends one more line — only while the operator is actively toggling the bundle from active to inactive — naming how many live contracts would be affected. It stays hidden (via `invisible`, not removed from layout) rather than only appearing on the exact click that would trigger it, specifically so the surrounding box does not change height at the moment a click lands, which had previously made a second click meant for a different control land in the wrong place.

## 6. Shared building blocks

- **`FeatureSelectionCard`** (`src/pages/licenses/subscriptionEdit/FeatureSelectionCard.tsx`) — the n-tier, per-module accordion feature picker. It has exactly **one caller left in the whole SPA: this editor.** Its own comment states it was previously named `FeatureMatrixCard` and used on the sales/subscription screen too; a 2026-09 sales-flow phase removed per-feature selection from subscriptions entirely in favour of picking whole bundles (the [Licenses](/en/platform/licenses) module's own `GroupSelectionCard`, a different component), leaving this card owned solely by this module now. It draws one tick-mark bar per module (`AllocationTicks`, the same component the seat-quota screens use) rather than a percentage bar, specifically because a percentage bar cannot be compared meaningfully across rows with different denominators, while "one tick per available slot" reads the same way regardless of how many slots a given module has.
- **`GroupCompositionPanel`** / **`FeatureCompositionBar`** (`src/pages/licenses/{GroupCompositionPanel,FeatureCompositionBar}.tsx`) — the composition summary and its bar, shared verbatim between the list screen's per-row bar and the editor's own header panel, specifically so the same bundle's "how much of the catalog" fact never has two different-looking answers depending on which screen shows it. The bar's divisor is always caller-supplied, never self-computed from the largest value on the page — the same discipline `FeatureCompositionBar`'s own comment traces back to an earlier bug on a different module's bar (`LicenseCoverageBar`'s `windowStart`/`windowEnd`).
- **`CatalogStateBar`** / **`ModuleShelf`** (`src/pages/licenseFeatures/{CatalogStateBar,ModuleShelf}.tsx`) — the Features tab's own summary strip and per-module shelf, described in §3. Their state-label/hint key sets (`LICENSE_STATE_LABEL`/`LICENSE_STATE_HINT` in `FeatureCatalogPanel.tsx`) are deliberately **not** shared with the unrelated Feature Flags screen — see §3.3 of the [landing page](/en/platform/license-catalog).

## 7. References

All paths are `../carmen-platform` unless prefixed otherwise.

- `src/pages/LicenseCatalog.tsx` — the shell, `TAB_PATH`/`TAB_GATE`/`TAB_ORDER`, and the three behaviours in §2.
- `src/pages/licenseCatalog/FeatureCatalogPanel.tsx` — the Features tab (§3).
- `src/pages/licenseFeatures/{CatalogStateBar,ModuleShelf}.tsx` — the Features tab's summary bar and per-module shelf.
- `src/pages/licenseCatalog/GroupCatalogPanel.tsx` — the Bundles tab (§4).
- `src/pages/LicenseFeatureGroupEdit.tsx` — the bundle editor (§5).
- `src/pages/licenses/subscriptionEdit/FeatureSelectionCard.tsx`, `src/pages/licenses/subscriptionEdit/featureSelection.ts` — the shared feature picker and its pure state-transition logic (§6).
- `src/pages/licenses/GroupCompositionPanel.tsx`, `src/pages/licenses/FeatureCompositionBar.tsx` — the shared composition summary and bar (§6).
- `src/hooks/useFeatureCatalog.ts` — the editor's single-load-per-page catalog hook, feeding both the picker and the composition panel from one request.
- `src/services/{licenseFeatureService,licenseFeatureGroupService,subscriptionService}.ts` — REST clients; `subscriptionService.getFeatureCatalog()` is the cross-module call documented in §4.3 of the [landing page](/en/platform/license-catalog).
- `src/utils/featureTree.ts` — `ancestorsOf()`, `descendantKeys()`, `flattenDescendants()`, used throughout §3 and §5.

**Cross-links:** [License Catalog landing](/en/platform/license-catalog) &nbsp;·&nbsp; [Data Model](/en/platform/license-catalog/data-model) &nbsp;·&nbsp; [Licenses](/en/platform/licenses)
