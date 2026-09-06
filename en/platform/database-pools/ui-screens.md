---
title: Database Pools — UI Screens
description: DatabasePoolManagement's single-DSN-per-row list with copy-to-clipboard, and DatabasePoolEdit's record-style read view and create/edit form — including the masked, never-revealed password field.
published: true
date: '2026-09-06T21:00:00.000Z'
tags: book/platform, database-pools, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Database Pools — UI Screens

> **Screens:** `DatabasePoolManagement` (list, `/platform/database-pools`) &nbsp;·&nbsp; `DatabasePoolEdit` — one component for both create (`/platform/database-pools/new`) and edit (`/platform/database-pools/:id/edit`) &nbsp;·&nbsp; **No tabs, no wizard** — a single card in both create and edit mode &nbsp;·&nbsp; **Dialogs:** Delete-pool confirm &nbsp;·&nbsp; **Persisted UI state:** 5 `localStorage` keys on the list (search/filters/page/perpage/sort); the edit page persists nothing &nbsp;·&nbsp; **Concurrency:** `doc_version` optimistic lock, required on every save &nbsp;·&nbsp; **Screenshots:** deferred per plan — no screenshot assets exist for this module

## 1. Overview

This module has two screens and no in-between states beyond loading/not-found/error, unlike the tabbed, multi-card edit pages elsewhere in this book ([Business Units](/en/platform/business-units/ui-screens), [Clusters](/en/platform/clusters/ui-screens)). `DatabasePoolManagement.tsx` (`../carmen-platform/src/pages/DatabasePoolManagement.tsx`, 467 lines) is a standard server-paginated `DataTable`. `DatabasePoolEdit.tsx` (`../carmen-platform/src/pages/DatabasePoolEdit.tsx`, 672 lines) is the create form and the single-record edit page in one component, following the same read-view/edit-mode toggle pattern this SPA uses elsewhere, but rendered as a plain labeled record (`RecordRow`) in read mode rather than a form with disabled inputs.

## 2. `DatabasePoolManagement` — list page (`/platform/database-pools`)

**Columns** (`columns`, `DatabasePoolManagement.tsx:200-295`):

| Column | Content |
|---|---|
| Connection (`id: 'host'`, sorts by `host`) | The composed DSN (`username@host:port/database`, `poolDsn()`) as a link to the pool's edit page, in monospace, with a copy-to-clipboard button beside it; below that, the pool's `name` (only when `!isDerivedName()` — see [Data Model](/en/platform/database-pools/data-model) §2); below that, `note` when set |
| Status | `is_active` rendered as a Badge (`success`/`secondary`) |
| Created / Updated | Standard shared `auditColumns()` |
| Actions | A `MoreHorizontal` dropdown (Edit, Delete) wrapped entirely in `<Can permission="database_pool.manage">` — a read-only session sees no actions column content at all, not a disabled one |

The sort column's `id` is literally `'host'`, not `'connection'` — per the code's own comment, sorting groups pools by physical machine, which is what an operator actually wants from this column, and `'connection'` is not a real backend field to sort by.

**Search** matches `name`/`host`/`database` (`defaultSearchFields`, confirmed identical to the backend's own `defaultSearchFields` in `database-pool.service.ts:80` — the frontend comment citing that exact file and line is accurate, verified by reading both). **Filters**: a Sheet panel with Active/Inactive toggle chips. Both chips can be selected at once in the UI, but `buildAdvance()` only emits a server-side `is_active` filter when **exactly one** is selected (`filters.length === 1`) — selecting neither or both both resolve to "no filter," showing every pool regardless of status.

**CSV export** (`handleExport`) — 12 columns: `dsn` (composed, not stored), `name`, `host`, `port`, `database`, `username`, `is_active`, `note`, then the four audit fields (`created_at`/`created_by`/`updated_at`/`updated_by`). **`password` and `description` are not exported.**

**Copy DSN button.** Present both in the Connection cell here and on the edit page (§3–4). Copies the exact composed DSN string via the Clipboard API; a rejected clipboard write (permission denied, or a non-secure-context page) surfaces an error toast rather than failing silently, per the handler's own comment about not letting the user believe a copy succeeded when it did not.

**Header actions:** Export CSV (disabled while loading or empty) and, gated `<Can permission="database_pool.manage">`, an Add Pool button. The same gate wraps the equivalent button in the empty state.

**Delete confirmation.** A `ConfirmDialog` on the row's Delete action; on confirm, a 409 `DATABASE_POOL_IN_USE` error is shown via its raw backend message (naming the blocking business units by `code`) rather than through the generic error-detail redactor, per the handler's own comment about not swallowing that BU list behind a generic "Please try again later." in production.

**Dev tooling:** A `DevDebugSheet` showing the raw `GET /api-system/platform/database-pools` response, matching the pattern used across this book's other list pages.

## 3. `DatabasePoolEdit` — create mode (`/platform/database-pools/new`)

The page opens already in edit mode (`editing = isNew`) — there is no separate "click Edit to start" step for a brand-new pool. See [landing page](/en/platform/database-pools) §4 for exactly which permission does and does not gate this.

**Fields**, all on one card, two-column responsive grid:

| Field | Required | Notes |
|---|---|---|
| Name | Yes | Plain text |
| Status (Active checkbox) | — | Defaults checked |
| Description | No | Multi-line textarea |
| Host | Yes | Plain text |
| Port | Yes | Number input, client-validated 1–65535 (`isValidPort()`); no shared `validateField` case exists for `port`, so this check lives locally in the page rather than colliding with an unrelated case of the same name elsewhere |
| Database | Yes | Plain text |
| Username | Yes | Plain text — **not** validated as an email; the page deliberately bypasses the shared `validateField('username')` case written for the Users module, since this is a raw database login |
| Password | Yes (create only) | Masked input with a show/hide toggle (`Eye`/`EyeOff`) |
| Note | No | Multi-line textarea |

On submit, a successful create shows a toast and navigates (`replace: true`) to the new pool's own edit URL — the page does not stay on `/new` after success. A 409 with the backend's `DATABASE_POOL_NAME_EXISTS` message is surfaced as a field-level error directly under Name, using the backend's own message text (which names the field) rather than the generic redacted message.

## 4. `DatabasePoolEdit` — edit mode (`/platform/database-pools/:id/edit`)

**Read mode** (default on load) renders as a labeled record, not a form:

- The composed DSN as the page's large, prominent text (same string as the list row), with its own copy button
- The Active/Inactive badge
- `description`, if set (`RecordRow`)
- `note`, if set — deliberately placed **before** the password row, not after, so the "this pool was auto-created" signal is not the last thing on the page
- A password row that never shows a value — only the fixed label "stored, hidden" (`passwordStoredHidden`), since the API never returns the real value to reveal

Clicking **Edit** (gated `<Can permission="database_pool.manage">`) switches to the same form fields as §3, pre-filled from the loaded record except password, which always starts blank — leaving it blank on save keeps the stored value unchanged (see [Data Model](/en/platform/database-pools/data-model) §4). A hint below the password field ("leave blank to keep the current password") only appears in edit mode, not create mode.

**Header** shows the pool's audit trail (`normalizeAudit()`) next to the title. The title itself is the pool's `name` in edit mode, but in **read** mode falls back to a generic "Database Pool" heading whenever `isDerivedName()` is true — avoiding printing the same DSN-shaped string as both the heading and the address line directly below it.

**Save/Cancel bar.** A fixed bottom bar appears only while editing, showing "Unsaved changes" or "No changes" and Cancel/Save buttons — the same `unsaved-bar` pattern used across this book's other edit pages. The Save button is wrapped in `<Can permission="database_pool.manage">`; `Ctrl/Cmd+S` triggers the same submit path via `useGlobalShortcuts`, and `handleSubmit` itself re-checks `hasPermission('database_pool.manage')` before doing anything else (see [landing page](/en/platform/database-pools) §4 for why this second check matters).

**Error handling on save:** a deleted-elsewhere pool (404) switches the page into its not-found state rather than showing a banner over stale data; a stale `doc_version` (409 version conflict) shows the shared conflict toast and reloads the record; a 409 name collision surfaces on the Name field specifically; any other validation error populates per-field messages from the backend's own field map when present.

**Not-found state.** A dedicated `EmptyState` card ("pool not found") with a button back to the list — rendered instead of the edit shell whenever the id does not resolve, whether from a bad URL or a pool deleted in another tab between navigation and load.

**Dev tooling:** A `DevDebugSheet` tab showing the raw `GET /api-system/platform/database-pools/:id` response (or a placeholder in create mode, since there is nothing to fetch yet).

## 5. Dialogs

### 5.1 Delete-pool confirm (list page only)

A `ConfirmDialog` triggered from the row actions menu. Confirming calls `DELETE`; the resulting 409 `DATABASE_POOL_IN_USE` (§2) is the only error path this dialog itself needs to surface, since a pool with no dependent business units always succeeds.

There is no dialog on the edit page equivalent to Business Units' "repoint database pool/schema" confirm ([Business Units — UI Screens](/en/platform/business-units/ui-screens) §5.5) — that confirmation belongs to the *consumer* of a pool (a business unit changing which pool it points at), not to this module, which only edits the pool record itself.

## 6. Persisted UI State

The list page persists five `localStorage` keys, all namespaced `*_database_pools(_database_pool)`: `search_database_pools`, `filters_database_pools`, `page_database_pools`, `perpage_database_pool` (singular, unlike its siblings — confirmed as written in source, not a typo introduced by this page), and `sort_database_pools`. Default sort is `created_at:desc` — per the code's own comment, `updated_at` was rejected as the default because most pools are never edited after creation, which would make the list order look arbitrary on first load.

The edit page persists nothing to `localStorage`; its only client-side state that survives a re-render is the in-memory unsaved-changes diff (`formData` vs. `savedFormData`), guarded by the shared `useUnsavedChanges` hook (browser "leave site?" prompt on an unsaved edit).

## 7. References

- `../carmen-platform/src/pages/DatabasePoolManagement.tsx` — read in full (467 lines).
- `../carmen-platform/src/pages/DatabasePoolEdit.tsx` — read in full (672 lines).
- `../carmen-platform/src/services/databasePoolService.ts` — REST client.
- `../carmen-platform/src/utils/databasePool.ts` — `poolDsn()`, `isDerivedName()`.
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/database-pool.service.ts:80` — `defaultSearchFields`, cross-checked against the frontend's own citing comment.
- `../carmen-platform-e2e/tests/` — listed directly; **no `database-pools` directory exists**, confirming the [landing page](/en/platform/database-pools) §1's "no e2e suite" claim.
- No screenshot assets exist for this module (`assets/screenshots/platform/database-pools/`) — deferred per the resync plan, consistent with every other newly-written module in this batch.
