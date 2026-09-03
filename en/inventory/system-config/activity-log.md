---
title: Activity Log (Screen)
description: The /system-admin/activity-log screen — list/grid views over tb_activity with action/entity-type/actor filters, XLSX export, print, and a raw JSON before/after detail sheet. Data model lives at reporting-audit/activity — this page documents the screen only.
published: true
date: 2026-07-29T11:00:00.000Z
tags: system-config, activity-log, audit, carmen-software
editor: markdown
dateCreated: 2026-07-29T11:00:00.000Z
---

# Activity Log (Screen)

> **At a Glance**
> **Route:** `/system-admin/activity-log` &nbsp;·&nbsp; **Sidebar label:** "Activity Monitor" (`modules.activityLog`), distinct from the route's own path segment &nbsp;·&nbsp; **Table:** `tb_activity` — full data model at [reporting-audit/activity](/en/inventory/reporting-audit/activity) &nbsp;·&nbsp; **Permission:** `system_configuration.view` &nbsp;·&nbsp; **This page documents the screen's own mechanics** (view modes, filters, export, detail sheet) — see [reporting-audit/activity](/en/inventory/reporting-audit/activity) for the table/enum/business-rules and confirmation that this is the *only* activity UI in the product.

![Activity Log screen](/screenshots/activity-log/index.png)

## 1. What & Who

This is the **only screen** that reads `tb_activity` — confirmed at [reporting-audit/activity](/en/inventory/reporting-audit/activity) ("Read by exactly one screen — `/system-admin/activity-log`. No embedded per-document 'Activity drawer' was found anywhere"). It is listed here under System Configuration because it is one of the routed screens under `/system-admin/*` (alongside [workflow](/en/inventory/system-config/workflow), [period](/en/inventory/system-config/period), etc.) — this page is scoped to how the **screen itself** behaves; the underlying entity, its enum, and its business rules are documented once, at [reporting-audit/activity](/en/inventory/reporting-audit/activity), and are not repeated here.

The screen offers two rendering modes (list and card/grid), three filter axes (action, entity type, actor), free-text search, XLSX export, browser print, and a slide-in detail sheet showing the raw `old_data`/`new_data` JSON for a selected row.

**Maintained by** the audit service, append-only (see [reporting-audit/activity](/en/inventory/reporting-audit/activity)). **Read by** Sysadmin / auditors browsing this screen.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Switch between list and grid view | Toolbar → list/grid icon toggle | Desktop only — on mobile the screen always uses the grid/card layout regardless of this toggle |
| Filter by action | Action multi-select | 5 curated options (`create`, `update`, `delete`, `login`, `logout`) out of 20 enum values — see [reporting-audit/activity](/en/inventory/reporting-audit/activity) §5.1 for the full enum |
| Filter by entity type | Entity Type multi-select (searchable) | ~13 curated values; `entity_type` itself is free-form so other values can exist in the data with no matching filter chip |
| Filter by user (actor) | User multi-select (searchable) | Populated from `useAllUsers()` — every user in the tenant, not just ones who appear in the log |
| Search free-text | Search box | Combined with the three filters (all query params merge into one request) |
| Toggle table columns (list view only) | Columns icon → column-visibility popover | Not available in grid view |
| Export the current filtered view | **Export** button | Client-side XLSX (`useExportActivityLog`), same query params as the on-screen list; columns: Date, Action, Entity Type, Entity ID, User, IP Address, Description |
| Print | **Print** button | Browser's native print of the current page (`window.print()`) — not a formatted report |
| Inspect one row | Click a row / card | Opens the detail sheet — see §4 |

## 3. Validation & Errors

| Symptom | Cause | Confirmed? |
|---|---|---|
| Grid/card view uses infinite scroll instead of pagination | Desktop **grid** mode and **any mobile view** (regardless of list/grid toggle) both switch to `useGridPagination` (sentinel-based infinite scroll); only desktop **list** mode uses classic page-based `DataGridPagination` | **Confirmed** — `useInfiniteScroll = isMobile || displayMode === "grid"` in `activity-log-component.tsx`, and the two branches call different hooks (`useActivityLog` vs `useGridPagination`) |
| Export button disabled with a spinner | Export already in progress (`isExporting`) | **Confirmed** |
| `exportNoData` toast on Export | The current filtered query returned zero rows | **Confirmed** |
| Filter badge count on the mobile filter-sheet icon | Counts individual selected values across all three filters, not filter *types* | **Confirmed** — `activeFilters.length`, one entry per selected value |

## 4. Edge Cases

- **Two independent list-rendering paths, not one shared component with a view-mode flag.** List mode fetches via `useActivityLog` (classic page param) *only when* `!useInfiniteScroll`; grid/mobile mode fetches via `useGridPagination` (sentinel-triggered `loadMore`) *only when* `useInfiniteScroll` is true — both hooks hit the same endpoint but with different pagination mechanics, and the component conditionally renders one `<DataGrid>` or one card grid, never both.
- **Detail sheet shows two raw JSON blocks, not a computed diff.** The sheet (`activity-log-detail-sheet.tsx`) pretty-prints `old_data` and `new_data` side by side via a plain `JsonBlock` renderer — there is no field-level diff highlighting (no "changed fields" computation was found). [reporting-audit/activity](/en/inventory/reporting-audit/activity) describes this as "the closest equivalent to a diff old vs new view" — accurate, but worth being precise that it is two raw blocks, not a computed diff.
- **The sidebar calls this module "Activity Monitor", not "Activity Log".** `modules.activityLog` in the translation file resolves to `"Activity Monitor"` — the route segment (`/system-admin/activity-log`) and the in-page title (`systemAdmin.activityLog.title` → also `"Activity Monitor"`) are consistent with each other but differ from the URL slug and this wiki page's own naming. No functional impact; noted to avoid confusion when cross-referencing screenshots or nav.
- **No permission finer than `system_configuration.view`.** Every `/system-admin/*` sidebar entry — this one included — gates on the same single generic permission key (`constant/module-list.ts`); there is no activity-log-specific read/export permission.
- **Actor filter list is not scoped to actors who actually appear in the log.** `useAllUsers()` returns every tenant user, so the Actor filter can offer names with zero matching activity rows.

---

## 5. Data model — deferred by design

This page intentionally does **not** repeat `tb_activity`'s field table, `enum_activity_action` values, or business rules (append-only, no `entity_id` FK enforcement, retention policy, etc.) — all of that is authoritative at [reporting-audit/activity](/en/inventory/reporting-audit/activity) §5-§6. Duplicating it here would risk the two pages drifting out of sync; this page links to it instead.

The one screen-specific type worth noting: the frontend's `ActivityLog` interface (`types/activity-log.ts`) flattens the API response's actor fields (`actor_username`, `actor_firstname`, `actor_middlename`, `actor_lastname`) and reads the creation timestamp from a nested `audit.created.at` path rather than a top-level `created_at` — `getLogCreatedAt()` exists specifically to extract that nested value for both the on-screen date column and the XLSX export.

## 6. Cross-References

- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — the authoritative `tb_activity` data model, `enum_activity_action`, business rules, and the confirmation that this screen is the only activity UI in the product.
- [reporting-audit/user-activity](/en/inventory/reporting-audit/user-activity) — the sibling `/system-admin/user-activity` screen: a per-user filtered client-side view over the same `tb_activity` table (not a separate table or a two-table join).
- [system-config](/en/inventory/system-config) — parent module; §3 Entity List places this alongside the other real `/system-admin/*` screens.
- [access-control/user](/en/inventory/access-control/user) — source of the Actor filter's user list.

## 7. References

- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/activity-log/activity-log.route.tsx`, `activity-log-component.tsx`, `activity-log-card.tsx`, `activity-log-detail-sheet.tsx`, `use-activity-log-table.tsx`.
- **Frontend hook/type:** `../carmen-inventory-frontend-react/hooks/use-activity-log.ts` — `useActivityLog()`, `useExportActivityLog()`; `types/activity-log.ts` — `ActivityLog`, `getLogCreatedAt()`.
- **Nav entry:** `../carmen-inventory-frontend-react/constant/module-list.ts` — `activityLog`, `permission: PERMISSIONS.system_configuration.view`.
- **Translations:** `../carmen-inventory-frontend-react/messages/en.json` — `systemAdmin.activityLog.*` (`title: "Activity Monitor"`), `modules.activityLog`.
- **Table/enum/rules (not repeated here):** see [reporting-audit/activity](/en/inventory/reporting-audit/activity) §8 for its own Prisma/frontend/writer citations.
