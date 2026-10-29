---
title: Tenant Seed — UI Screens
description: The Tenant Seed page piece by piece - fleet summary card, business-unit table with per-row Check and Seed actions, the set-picker confirmation dialog, batch progress line and CSV export.
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, tenant-seed, ui-screens
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Tenant Seed — UI Screens

> **At a Glance**
> **Screens:** 1 page &nbsp;·&nbsp; **Layout:** summary card, optional batch strip, searchable table &nbsp;·&nbsp; **Dialogs:** `SeedSetPickerDialog` (used twice: one BU, whole fleet) &nbsp;·&nbsp; **Access:** `tenant_seed.read` to open and Check; `tenant_seed.apply` to Seed &nbsp;·&nbsp; **Persisted UI state:** none

## 1. Overview

`TenantSeedManagement` at `/tenant-seeds` follows the same pattern as the Tenant Migrations console it was modelled on (it imports `withTooltip` from `TenantMigrationManagement`). All state lives in React memory: reloading the page forgets every check result. There is no create/edit route; the only navigation out is the BU code link in each row (`/business-units/:id/edit`) and the empty-state button.

## 2. `TenantSeedManagement` (`/tenant-seeds`)

### 2.1 Fleet summary card (`SeedFleetSummary`)

A card with three zones. **Left:** big counter "`seeded / checkable`" (a dash instead of the number until something has been checked), captioned "Tenants seeded"; `checkable` counts BUs that have a database. **Middle:** a three-segment bar (green seeded, amber missing, red error) with a legend; extras appear only when relevant: an Error legend when errors exist, "N missing rows" (total across Missing BUs), and a "No DB" legend. Before the first check it shows "Not checked yet - run Check all ...". **Right:** the action buttons below.

### 2.2 Header actions

| Button | Behaviour |
|---|---|
| **Check all** | Checks every BU that has a DB, 4 in parallel; toast "Checked N business units." or "Checked N - M failed." Disabled while anything is busy. |
| **Seed N missing** / **Seed all missing** | Opens the fleet picker (§2.5). Label is "Seed N missing" when N BUs are Missing, else "Seed all missing". Disabled, with a tooltip explaining why, when: the viewer lacks `tenant_seed.apply`; nothing has been checked yet ("Not checked yet. Run Check all first..."); or everything checked is fully seeded ("Every checked tenant is fully seeded - nothing to seed."). |
| **Export** | Downloads `tenant-seeds-YYYY-MM-DD.csv` with columns Code, Name, Status, Missing rows, Missing sets (`key present/defined`, comma separated), Last Checked, Error. Enabled once BUs are loaded and nothing is running. |

### 2.3 Table

Client-side `DataTable`, 25 rows per page, default sort by Code ascending, global filter from the search box (focus it with the global search shortcut). Columns:

| Column | Content |
|---|---|
| Code | Link to the BU's edit page |
| Name | |
| Status | Badge: Seeded (green), "N missing" (amber), No DB (grey, tooltip "This business unit has no database pool or schema configured."), Error (red), Not checked (outline). While seeding, a live line `Seeding done/total - <set key>`; an Error row also prints its message. |
| Missing sets | Chips `key present/defined` (the set's label as tooltip) for each set with something missing; a dash otherwise |
| Last Checked | Local `HH:MM:SS` of the last check on this row |
| Actions | **Check** (refresh icon) on every row except No DB; **Seed** (sprout icon, primary) only on Missing rows |

Check is available with `read`; Seed is disabled with a tooltip "Requires the tenant_seed.apply permission." without `apply`. Both are disabled while that row, a batch, or Check all is running.

States: `TableSkeleton` while BUs load; an inline red alert if the BU list fails ("Failed to load business units: ..."); `EmptyState` "No business units" with a "Go to Business Units" button when there are none.

### 2.4 Batch progress strip

While Seed-all runs, a monospace status line appears above the table: `BU i/n - CODE`, followed by the current set and `done/total` of that BU's stream.

### 2.5 `SeedSetPickerDialog`

One component, two uses.

| | Single BU (row Seed) | Fleet (header Seed) |
|---|---|---|
| Title | "Seed default data?" | "Seed all missing tenants?" |
| Description | names the BU; "Rows that already exist are skipped." | "...across N business units, one at a time ... Leaving this page stops before the next business unit." |
| Options | that BU's sets that have missing rows | union over all Missing BUs; badge "N missing in M BU" |
| Expand arrow | lists the missing row keys | lists `BU code - n` lines |

Every set starts ticked each time the dialog opens; "Select all / Clear" toggles all. The confirm button is disabled at zero selected rows and reads "Seed N rows". Confirming closes the dialog immediately; progress then shows on the page, because awaiting a long stream inside a modal would block the UI.

## 3. Persisted UI state

None. No `localStorage` keys. The search text, check results, and in-flight streams are page state only; leaving the page aborts the browser's streams and stops the batch before the next BU.

## 4. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 5. References

- `../carmen-backstage/src/pages/TenantSeedManagement.tsx`, `src/pages/tenantSeed/{SeedFleetSummary,SeedSetPickerDialog}.tsx`, `src/pages/tenantSeed/seedRowState.ts`.
- i18n: `pages.tenantSeed.*` in `src/i18n/en.ts`.
- Siblings: [Tenant Seed](/en/backstage/tenant-seed), [Lifecycle](/en/backstage/tenant-seed/lifecycle); embedded single-BU version: [Business Units: UI Screens](/en/backstage/business-units/ui-screens) §4.5.
