---
title: Tenant Imports — UI Screens
description: TenantImportWizard's four-screen sequence — pick a business unit, upload Preconfig.xlsx, review the file check, then step through the import screens.
published: true
date: '2026-09-06T23:45:00.000Z'
tags: book/platform, tenant-imports, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Tenant Imports — UI Screens

> **At a Glance**
> **Screen state machine:** `pick-bu` → `upload` → `check` → `steps` (`type Screen`, `TenantImportWizard.tsx`) &nbsp;·&nbsp; **Shared chrome:** `Layout`, `PageHeader` (title "Tenant Data Import"), a header button that opens the shared `BuSwitcher` command palette, a dev-only `DevDebugSheet` &nbsp;·&nbsp; **No back button:** once `steps` is reached there is no control that returns to `check` while keeping the loaded file — the only way back to `upload` is through `BuSwitcher`, which discards all client-side wizard progress (§6) &nbsp;·&nbsp; **e2e suite:** none — every behavior below is read directly from `../carmen-platform` source

## 1. Overview

The four screens run strictly forward. Nothing on this page is reachable out of order: there is no BU picked without going through `pick-bu`, no file check without a BU, and no step work without a passed check. What varies per screen is how much you can undo without losing more than intended — covered per screen below, and summarized in §6.

## 2. Screen 1 — Pick Business Unit (`pick-bu`)

**What it asks for:** nothing yet — a centered prompt ("Pick the business unit that will receive the data," `pages.tenantImport.pickBuHint`) and a "Select business unit" button that opens `BuSwitcher`, the same command-palette component [SQL Workbench](/en/platform/sql-workbench) uses: type to filter by code/name/cluster, arrow keys to navigate, Enter to pick. This is also the header's persistent "BU: `{code}`" button on every later screen — reopening it from anywhere resets the wizard (§6).

**What it validates:** nothing — no file has been touched yet. In parallel with rendering this screen, the wizard fires two independent calls (`Promise.allSettled`, `TenantImportWizard.tsx`): `businessUnitService.getAll({ perpage: 200 })` to populate the picker, and `preconfigImportService.getSteps()` (`GET /steps`) to load the step catalog. Each failure is toasted independently and does not block the other — a session that can list business units but lacks `data_import.manage` still sees the picker populate, but with a catalog-load error banner waiting on the next screen (§3).

**What happens on failure:** a failed BU list fetch toasts an error and leaves the picker empty; a failed catalog fetch toasts an error, sets `catalogError`, and is shown as a persistent banner once the wizard reaches `upload` (§3) — the wizard does not retry either automatically. The banner's own copy volunteers a likely cause: *"this usually means the platform permission for Preconfig imports has not been granted yet"* (`pages.tenantImport.catalogError`) — a useful first thing to check when a session sees a blank Upload screen.

**Caveat, not a bug:** the BU fetch is capped at `perpage: 200` and the effect reads only `.data` from the response — the `total`/`paginate` fields `ApiListResponse` carries (`types/index.ts:20-24`) are never consulted. Unlike [Tenant Migrations](/en/platform/tenant-migrations) (§3.1 there), which explicitly warns when its own 1000-row fetch doesn't cover every business unit, this picker gives no on-screen signal if a cluster fleet exceeds 200 BUs — the list would simply stop at 200 with nothing said.

**Revisit:** trivially — this is the starting screen, and reopening `BuSwitcher` from any later screen returns here only if the operator clears the selection; picking a (possibly different) BU always advances to `upload`.

## 3. Screen 2 — Upload Workbook (`upload`)

**What it asks for:** one `.xlsx` file, via `WorkbookDropzone` (`../carmen-platform/src/pages/tenantImport/WorkbookDropzone.tsx`) — drag-and-drop or click-to-browse, built on plain DOM drag events (the component's own comment: the repo does not carry `react-dropzone` and this feature must not add the dependency).

**What it validates, and where:**

- **Client-side, before any request is sent:** the dropped/picked file's name must end in `.xlsx` (case-insensitive) — `WorkbookDropzone.tsx:26-29`. A wrong extension is rejected with a toast ("Only .xlsx workbooks are supported," `pages.tenantImport.onlyXlsx`) and never reaches the network.
- **Server-side, independently, on every call that accepts a file:** `assertXlsx()` (`preconfig-imports.controller.ts:29-36`) re-checks the extension **and** the exact multipart MIME type (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) **and** a 10 MB size cap (`MAX_FILE_SIZE_BYTES`, line 11; also enforced independently by Multer's own `FileInterceptor` limit at each route). A file that passes the browser's extension-only check can still be rejected by the server (e.g. a `.xlsx`-renamed file of a different type, or one over 10 MB) — this is the case a tester needs the API, not just the UI, to reproduce.

While the check request (`preconfigImportService.check()`) is in flight, the panel shows a "Checking workbook…" spinner in place of the dropzone (`busy` state).

**What happens on failure:** a server rejection (bad type, oversized) surfaces as a toast built from `parseApiError()`; the screen stays on `upload` with the dropzone available again — nothing advances. A successful check (regardless of how many steps come back `ready`) always advances to `check`, aborting any in-flight import and resetting every per-step state first (`resetGenerations()`, `TenantImportWizard.tsx`).

**Revisit:** re-uploading a different file here (there is no separate "cancel" — dropping a new file simply re-runs `check`) always re-checks from scratch; nothing from a prior attempt on this screen carries forward.

## 4. Screen 3 — File Check (`check`)

**What it shows:** `FileCheckPanel` (`../carmen-platform/src/pages/tenantImport/FileCheckPanel.tsx`) — a header line ("`{sheets}` sheets found · `{ready}` of `{total}` steps ready," `pages.tenantImport.fileSummary`) and a table, one row per catalog step, columns Step / Sheet / Rows / Missing / Status. A step not `ready` still appears here rather than disappearing silently (component's own comment) — this is the one place a tester sees **why** a step never reaches the rail: `sheet_missing` (the workbook has no matching sheet) or `columns_missing` (the sheet exists but is missing a `required` column; a missing *optional* column does not block readiness and simply appears in the Missing cell for visibility).

**What it validates:** nothing new here — this screen only **renders** the `CheckReport` the `upload` screen's `check` call already produced. No request is made from this screen itself.

**Actions and failure paths:**

- **"Continue"** is disabled while `readyCount === 0` — a workbook with zero ready steps cannot proceed past this screen at all, and there is no override.
- **"Choose another file"** aborts any in-flight run, clears the file/report/per-step state, and returns to `upload` — the only in-wizard way back to the upload screen that does **not** go through the BU switcher.

**Revisit:** freely, in the one direction "Choose another file" allows (back to `upload`); there is no way back to this exact screen once "Continue" is pressed (see §6).

## 5. Screen 4 — Steps (`steps`)

This is where preview and import actually happen, one catalog step at a time, split across `StepRail` (the left-hand list) and either `StepPanel` (eleven of the twelve steps) or `CompanyProfilePanel` (Company Profile only, §5.6 below) on the right.

### 5.1 `StepRail` — choosing which step to work on

A vertical list below `lg` breakpoint collapses to a `<select>` (`StepRail.tsx`); above it, each ready step is a row showing its display name, a status icon (pending / previewing / previewed / importing / completed / skipped / error, each with its own icon and color), and — once known — its row count. Clicking a row switches `activeId`; **switching rows never discards another step's state** — each step's preview, options, and summary live independently in the wizard's `states` map, keyed by step id, so returning to a step you previewed twenty minutes and three other steps ago shows exactly what you left it in.

### 5.2 `StepPanel` — preview

**What it asks for:** an On-duplicate mode (`skip` / `upsert` / `error`, defaulting to the catalog's `default_duplicate_mode` for that step) and, optionally, "Soft-delete existing rows first" (`clear_existing`). Pressing **Preview** sends the current file and options to `POST /:step_id/preview`.

**What it validates (per row, server-side):** the same coercion rules described on the [landing page](/en/platform/tenant-imports) §3.2 — required/maxLength/allowedValues/number/decimal/boolean — plus every declared lookup (a natural-key column resolved against another table) and every dependent-row column a related insert needs (e.g. a Product's Order-unit conversion requires a non-empty "Order unit" *and* "Order Conv. Rate" cell; an incomplete pair is skipped silently as "this product has no order-unit conversion," while a present-but-unresolvable one fails the whole parent row). Rows are classified `new` / `duplicate` / `error` against the target table's **current, live** contents — matched on the step's composite duplicate key, normalized case/whitespace-insensitively.

**What the response shows:** verdict badges with counts (New / Duplicate / Error) that double as filter toggles — click one or more to narrow the table below to just those verdicts; a caption states plainly how much of the *sample* you're looking at versus the sheet's true totals ("Showing 200 of 2,400 new," `captionText`, `StepPanel.tsx`) — the preview response caps at 200 rows per verdict bucket (`PREVIEW_ROW_CAP`), never per response, so a heavily-skewed sheet still surfaces some of every verdict rather than only whichever sorts first. A row's own Verdict cell shows its per-column error text inline when it has one.

**"New reference data will be created"** appears only when the preview found a lookup value with no matching row and that lookup allows auto-creation — listing every distinct value grouped by target table/column, with a checkbox to accept creating them (`accept_lookup_creation`). Ticking this checkbox is purely a client-side convenience for the *next* Import call; §3.3 on the landing page covers exactly how the server enforces this independently, per row, no matter what was previewed.

**Failure mode:** a preview request itself failing (network, permission, connection) sets the step to `error` with the message shown inline and toasted — no rows are shown; the step's options are untouched, so pressing Preview again retries with the same settings.

**Revisit:** yes, freely — Preview can be re-run any number of times, with different options each time. Changing **any** option (duplicate mode, the clear-existing checkbox, accepting lookups) invalidates the current preview immediately (`onOptionsChange`, `StepPanel.tsx`) and resets the step to `pending`, requiring a fresh Preview before Import re-enables.

### 5.3 The clear-existing confirmation dialog

Ticking "Soft-delete existing rows first" does **not** set `clear_existing` directly — it opens a dialog that must be explicitly confirmed. The checkbox itself is disabled until at least one preview exists for the step (`disabled={running || previewing || (!preview && !clearExisting)}`, `StepPanel.tsx:267`) — the hint text "(run a preview first)" explains why. The dialog states, using the counts the most recent preview already computed, either that there is nothing to delete, or exactly how many rows of the step's own table (plus how many dependent rows, e.g. unit conversions) would be soft-deleted — and requires **typing the exact business-unit code** into a text field before "Confirm" enables (`clearCodeMatches`, `StepPanel.tsx:112,517`). Un-ticking the checkbox afterward needs no confirmation at all — it is always available as the de-escalating action, even if a later options change invalidated the preview the tick was based on.

None of this sequencing is enforced by the server — see the landing page §3.3 for exactly what `import/stream` itself does and does not check.

### 5.4 Import

**What it does:** streams `POST /:step_id/import/stream` as NDJSON and renders a progress bar (`{index} / {total}`, updated at most every 50 rows or once per batch boundary) plus, once a `cleared` event arrives, how many rows were soft-deleted. The Import button is disabled while no preview exists, while another step is currently importing (only one step may stream at a time — attempting a second surfaces "Another step is still importing — wait for it to finish before starting this one," `pages.tenantImport.anotherStepImporting`), or while the current preview still has un-accepted lookup creations pending.

**What happens on failure:** a row-level failure (bad value, unaccepted lookup, database constraint) is recorded in that step's `summary.failed`/`summary.errors` and does **not** stop the run — the importer's own batch-retry mechanism (landing page §3.4) is what keeps one bad row from failing the other 199 in its batch. The step's terminal status is `completed` only when `summary.failed === 0`; any failures at all mark it `error`, with the summary numbers (inserted/updated/skipped/failed) still shown.

**Re-run:** once any step has been imported (`everImported`), it appears in the "Run summary" panel below the rail with a **Re-run** button that starts the exact same import again using whatever options are currently set for that step — available at any time, including after a completed run, as long as no other step is mid-import. Re-running with `clear_existing` still on repeats the soft-delete first.

**Cancellation:** navigating away from `steps` (BU switch, new file, or leaving the page) aborts the in-flight `fetch` stream. As detailed on the landing page §3.4, this does **not** roll back a batch transaction already committed on the server — only batches that had not yet started are skipped, and the server still writes a `tb_activity` audit row recording the run as `cancelled` with whatever partial summary it reached.

### 5.5 Row-level detail and captions

The preview/import row table renders one column per distinct key seen across the sample's rows (in first-seen order, so an optional column left blank on row 1 but populated on row 40 still gets a column) plus a Verdict column carrying inline per-column error text. A verdict filtered to zero visible rows still explains itself ("No `error` rows in this preview") rather than rendering an empty table with no context.

## 6. Navigating back — the one gap a tester should expect

There is no button anywhere on the `steps` screen that returns to `check` (to look at the file-check table again) or to `upload` (to load a different file) while **keeping** the current file loaded. The only paths back to an earlier screen are:

- **"Choose another file"** on the `check` screen (§4) — only reachable before "Continue" is pressed.
- **Reopening `BuSwitcher`** (the header's "BU: `{code}`" button, available on every screen) — picking any business unit, including the one already selected, unconditionally clears the file, the check report, and every step's preview/import state, and returns to `upload`.

Neither path undoes rows already committed by a completed batch during a prior import on that business unit — both only reset the wizard's own client-side view. A tester who needs to re-examine the file check after starting work on steps has to re-upload the same file (a fresh `check` call, harmless and idempotent on its own) rather than being able to step backward.

## 7. Company Profile panel (`CompanyProfilePanel`) — the exception to everything above

Selecting the Company Profile step in the rail renders `CompanyProfilePanel` instead of `StepPanel` — it shares the rail but nothing else about the mechanics in §5.

**What it asks for:** nothing beyond the file and BU already chosen — it loads automatically (and reloads on demand via its own "Refresh" button, independent of the other steps' Preview button).

**What it shows:** a field-by-field diff table — Field / Current (BU) / Workbook / Status — built from the same `preview()` call every other step uses, but read for its **field values** rather than its verdict. Every mapped hotel/company field the sheet carries is compared against the business unit's current record; the virtual "Default Currency" row additionally resolves the sheet's currency **code** against the tenant's own currency list to a UUID (states: resolving / cannot-resolve if the tenant database is unreachable / not-found if no such currency code exists yet — with a hint to run the Currency step first, then Refresh / resolved). "BU Code" renders as a **read-only** identity row with a mismatch banner when the sheet's code doesn't match the selected business unit — applying never renames anything, but every other changed field on the panel would still be written onto the **selected** BU, not the one the workbook describes, so the banner exists specifically to stop that mistake before it happens. "BU Name" is listed as "Not applied" for the same reason: identity fields are never written back from a workbook.

**What it validates on Apply:** the Inventory Cost Type value, if changed, must be one of `average`/`fifo` (checked client-side immediately before the request; the server's own catalog validates the same constraint independently on `preview`). The write itself carries `doc_version` for optimistic locking — a `409` reloads the record and rebuilds the diff rather than silently overwriting whatever the other party just saved.

**What happens on failure:** a load failure shows an inline error and an empty diff; an apply failure toasts the server's message and leaves the diff exactly as it was (no partial write — the whole call is one `PUT`).

**Revisit:** freely — "Refresh" reloads the diff at any time, and "Apply to BU" can be pressed again after a successful apply (it becomes disabled only once nothing is left to change). Unlike every other step, Company Profile never touches the wizard's own `states` map — it never appears in "Run summary," never counts toward "another step is importing," and never contributes to the unsaved-changes guard, because it writes immediately rather than participating in the streamed import model at all. See the landing page §3.5-§3.6 and §4 for exactly which permission this write does and does not check.

## 8. Reference Sources

All paths `../carmen-platform` (HEAD `157a65e`) unless prefixed `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`).

- `src/pages/TenantImportWizard.tsx` — the four-screen state machine, the parallel BU-list/catalog fetch, per-step generation tokens, and the abort/reset paths cited in §6.
- `src/pages/tenantImport/WorkbookDropzone.tsx:26-29` — the client-side `.xlsx` extension check (§3).
- `src/pages/tenantImport/FileCheckPanel.tsx` — the file-check table and its Continue/Choose-another-file actions (§4).
- `src/pages/tenantImport/StepRail.tsx` — the step list/status icons and the `<select>` fallback below `lg` (§5.1).
- `src/pages/tenantImport/StepPanel.tsx:112,267,517` — the clear-existing checkbox's disabled condition, the typed-BU-code confirmation, and the verdict filter/caption logic (§5.2-§5.3).
- `src/pages/tenantImport/CompanyProfilePanel.tsx` — the diff table, currency resolution states, and the BU-code mismatch banner (§7).
- `src/services/preconfigImportService.ts` — `check`/`preview`/`importStream` request shapes.
- `src/i18n/en.ts:3188-3283` (`tenantImport` namespace) — every quoted UI string on this page.
- `src/types/index.ts:20-24` (`ApiListResponse`) — the unread `total`/`paginate` fields cited in §2.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/preconfig-imports/preconfig-imports.controller.ts:11,29-36` — `MAX_FILE_SIZE_BYTES`, `assertXlsx()` (§3).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/preconfig-import/preconfig-import.service.ts` — row coercion/lookup/related-row validation invoked by Preview and Import (§5.2, §5.4).

**Cross-links:** [Tenant Imports landing](/en/platform/tenant-imports) &nbsp;·&nbsp; [Business Units](/en/platform/business-units) &nbsp;·&nbsp; [Tenant Migrations](/en/platform/tenant-migrations)
