---
title: Tenant Imports
description: TenantImportWizard at /tenant-imports — sidebar label "Data Import," gated by the manage-not-read key data_import.manage — loads Preconfig.xlsx master data into one business unit's tenant database, step by step, with a live gap in the stream endpoint's error-status mapping.
published: true
date: '2026-09-06T23:00:00.000Z'
tags: book/platform, tenant-imports
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Tenant Imports

> **At a Glance**
> **Component:** `TenantImportWizard` at `/tenant-imports`, added `../carmen-platform` commit `80d6872` (2026-08-03) &nbsp;·&nbsp; **Three names, one page:** the sidebar entry reads **"Data Import"** (`labelKey: 'nav.dataImport'`, `platformNav.ts:15`), the route is `/tenant-imports`, and the page's own `PageHeader` title reads **"Tenant Data Import"** (`pages.tenantImport.title`, `src/i18n/en.ts:3211`) — a reader searching any of the three should land here &nbsp;·&nbsp; **Nav gate:** `permission: 'data_import.manage'` — a **`manage`** key, not `.read` like every other row in the Organization group (Clusters, Business Units, Tenant Migrations and Users all gate on a `.read` key); an administrator who holds only read-level access anywhere else in this book does not see this menu entry at all &nbsp;·&nbsp; **Backend gate:** the identical `data_import.manage` key, checked independently at every one of the importer's four endpoints via `@RequirePlatformPermission` (`preconfig-imports.controller.ts:104,123,149,179`) — a real RBAC check enforced on the server, not only a hidden sidebar row &nbsp;·&nbsp; **Feature flag:** `tenant_imports`, `groupKey: 'navGroup.organization'`, not `superAdminOnly` &nbsp;·&nbsp; **Scope:** one business unit's tenant database per wizard run &nbsp;·&nbsp; **e2e suite:** none — `../carmen-platform-e2e/tests/` has no `tenant-imports` (or `preconfig-import`) directory; every claim below is sourced from `../carmen-platform` and `../carmen-turborepo-backend-v2` implementation directly &nbsp;·&nbsp; **Sub-pages:** 1

## 1. Overview

Tenant Imports is a single-screen wizard, `TenantImportWizard` (`../carmen-platform/src/pages/TenantImportWizard.tsx`), that loads a fixed workbook — "Preconfig.xlsx" — of baseline master data into **one** business unit's tenant database: currencies, units of measurement, tax profiles, delivery points, departments, storage locations, a three-level product taxonomy (category → subcategory → item group), products (with their unit conversions), vendors (with a contact and an address), and the business unit's own hotel/company profile fields. It exists so onboarding a new business unit does not require an operator to enter each of those rows by hand, one CRUD screen at a time — the whole set is prepared once in a spreadsheet and walked through as a sequence of preview-then-import steps.

Reaching the page at all requires `data_import.manage` — not the `cluster.read` key that gates the neighboring [Clusters](/en/platform/clusters), [Business Units](/en/platform/business-units) and [Tenant Migrations](/en/platform/tenant-migrations) rows in the same Organization sidebar group. This is the one row in that group an operator can be denied independently of whether they can otherwise browse clusters and business units at all, and — because the key is `.manage` rather than `.read` — there is no lesser "can see this exists but not run it" tier: holding the key means being able to run every step of every import, including the destructive `clear_existing` option (§3.3).

The wizard is a strict four-screen sequence — pick a business unit, upload a workbook, review the per-step file check, then work through the ready steps one at a time — detailed screen by screen, including exactly what each step validates and what happens on failure, on [UI Screens](/en/platform/tenant-imports/ui-screens). This page covers the mechanics that cut across the whole wizard: the step catalog, the three-tier validation model (check → preview → import), what is enforced only in the browser versus what the server enforces independently, the streaming import's batching and audit trail, and a live defect in how one of its four endpoints reports failure.

## 2. Business Context

The twelve-step catalog (§3.1) is declared once, entirely on the backend (`PRECONFIG_STEPS` in `../carmen-turborepo-backend-v2/apps/micro-business/src/preconfig-import/preconfig-catalog.ts`) — which sheet maps to which table, which columns are required, which values are legal, which columns resolve foreign keys, and which insert dependent rows. The frontend never sees more than the client-facing projection of that catalog (`GET /steps`, `toStepMetadata()`) and cannot redirect an import at a table or column of its own choosing. This split is what makes the wizard safe to expose behind a single coarse `data_import.manage` key: the worst a session holding that key can do is run the fixed steps the catalog defines, against the one business unit it has picked.

Eleven of the twelve steps write into the **tenant** database selected by the wizard's business-unit picker. The twelfth, Company Profile, is different in kind: it edits the **platform** database's own `tb_business_unit` row for that business unit, and does so by calling the same `businessUnitService.update()` the ordinary [Business Units](/en/platform/business-units) edit page uses — not through the importer's streaming pipeline at all (§3.5).

## 3. Key Concepts

### 3.1 The twelve-step catalog

Every step is one Excel sheet mapped onto one database table (or, for Company Profile, the business unit record). `duplicate_key` is the composite natural key a row is matched against for skip/upsert/error handling (§3.3); `default_duplicate_mode` is what a client omits `options.duplicate_mode` to get.

| Step id | Sheet | Table | Target | Duplicate key | Default mode | Clears? | Notable lookups / related rows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `company-profile` | Company Profile (vertical) | `tb_business_unit` | **platform** | `code` (match only, never written) | upsert | no | Virtual `default_currency_code` column, resolved client-side (§3.5) |
| `currency` | Currency | `tb_currency` | tenant | `code` | skip | yes | — |
| `unit` | Unit | `tb_unit` | tenant | `name` | skip | yes | — |
| `tax-profile` | Tax Profile | `tb_tax_profile` | tenant | `name` | skip | yes | — |
| `delivery-point` | Delivery Point | `tb_delivery_point` | tenant | `name` | skip | yes | — |
| `department` | Department | `tb_department` | tenant | `code` | skip | yes | — |
| `location` | Store Location | `tb_location` | tenant | `code` | skip | yes | Looks up (and can auto-create) `tb_delivery_point.name` |
| `product-category` | Item Group | `tb_product_category` | tenant | `code` | skip | yes | Reads the same "Item Group" sheet as the next two steps |
| `product-subcategory` | Item Group | `tb_product_sub_category` | tenant | `code, name` | skip | yes | Looks up `tb_product_category.code` (required) |
| `item-group` | Item Group | `tb_product_item_group` | tenant | `code, name, product_subcategory_id` | skip | yes | Looks up `tb_product_sub_category.code` (required) |
| `product` | Product list | `tb_product` | tenant | `code` | skip | yes | Looks up/creates `tb_unit`; looks up `tb_product_item_group`, `tb_tax_profile`; writes up to two `tb_unit_conversion` child rows (order unit, recipe unit) |
| `vendor` | Vendor | `tb_vendor` | tenant | `code` | skip | yes | Looks up `tb_tax_profile.name`; writes one `tb_vendor_contact` and one `tb_vendor_address` child row |

`product-category`, `product-subcategory` and `item-group` deliberately read the **same** "Item Group" sheet three times into three tables, in dependency order — not a duplication bug (catalog comment, `preconfig-catalog.ts:210-211`). The Vendor sheet's headers are lower-case/snake_case (`code`, `name`, `active`, `payee`, …), unlike every other sheet in the workbook, which uses Title Case (`preconfig-catalog.ts:438-440`); header matching is whitespace/case-insensitive either way (`normalizeKey()`, `preconfig-workbook.ts`).

### 3.2 Three tiers: Check, Preview, Import — and what each one touches

The wizard runs a workbook through three distinct backend calls, in order, each doing strictly more than the last:

1. **`POST /:bu_id/check`** (`preconfigImportService.check()`) parses the workbook and reports, per step, whether its sheet is present and which required/optional columns are missing — **nothing about the selected business unit is read**. The `:bu_id` path segment is validated as a UUID but deliberately never forwarded to the service call (`preconfig-imports.controller.ts:126-130`, comment): it exists only so the frontend can reuse one URL shape across all four endpoints. A step reports `sheet_missing`, `columns_missing`, or `ready` (`buildCheckReport()`, `preconfig-workbook.ts`); only `ready` steps ever reach the wizard's step rail.
2. **`POST /:bu_id/:step_id/preview`** opens the tenant connection (except for Company Profile, §3.5) and dry-runs one step: every row is coerced, validated, and classified `new` / `duplicate` / `error` against the table's current contents — **nothing is written**.
3. **`POST /:bu_id/:step_id/import/stream`** repeats preview's classification and actually writes, streaming NDJSON progress (§3.4).

A step passing Check only means its sheet and required columns exist — it says nothing about whether individual cell values will validate. Coercion rules applied per column (`coerceValue()`, `preconfig-workbook.ts`): a `required` column with an empty cell fails the row; a value past `maxLength` fails the row; a column with `allowedValues` matches case-insensitively and is normalized to the catalog's own spelling (a workbook's `Average` becomes the enum member `average`); `number`/`decimal` cells that don't parse fail the row; `boolean` cells accept `true/1/yes/y/active` or `false/0/no/n/inactive` (case-insensitive) and nothing else.

### 3.3 What the browser enforces, and what the server enforces independently

Two options carry very different guarantees, and a tester reproducing a failure needs to know which is which:

- **`clear_existing`** (soft-delete every existing row of the step's table, plus dependent rows, before importing) is gated **only in the browser**: the checkbox itself is `disabled` until at least one preview has run for that step (`!preview && !clearExisting`, `StepPanel.tsx`), and ticking it opens a dialog that requires typing the exact business-unit code before "Confirm" enables (`StepPanel.tsx`'s clear-existing `Dialog`). Neither precondition exists on the server: `POST /import/stream` accepts `options.clear_existing: true` on its very first call for a step, with no preview and no typed confirmation — the browser's sequencing is a UI safeguard, not something the API depends on or checks for.
- **`accept_lookup_creation`** (permit auto-creating a missing reference row, e.g. a new delivery point named on the Store Location sheet) genuinely is enforced by the server, independent of the client: `validateRowLookups()` (`preconfig-import.service.ts:254-304`) rejects a **per-row** creatable-lookup miss with `Unaccepted new lookup value: "<value>"` whenever the option is not set on that specific request — regardless of whether the client ever ran a preview showing the pending creation. A row failing this check fails only that row, not the whole import run.

`clear_will_soft_delete`/`clear_will_soft_delete_related` (the counts the confirmation dialog shows) are always computed by `preview`, whether or not `clear_existing` was requested (`PreviewResult` doc-comment, `preconfig-types.ts`) — the dialog can only show a real number because preview already knows it before the operator opts in.

The gateway's `parseOptions()` (`preconfig-imports.controller.ts:47-79`) validates `duplicate_mode` against the three legal strings and `clear_existing`/`accept_lookup_creation` against `boolean`, rejecting a wrong type with 400 — but its own doc-comment ("anything else … is a 400") overstates what the code does: an **unknown extra key** in the submitted `options` JSON is silently dropped, not rejected. Read the function, not the comment, if testing malformed payloads.

### 3.4 Streaming import: batching, partial-batch retry, and the audit row it always leaves

`import/stream` writes rows in batches of 200 inside one Prisma transaction per batch (`IMPORT_BATCH_SIZE`, `preconfig-import.service.ts`). If a whole-batch transaction fails — most often one row violating a constraint the catalog's own duplicate key doesn't catch — the importer does not fail the other ~199 rows with it: it rewinds its in-memory counters to the pre-batch snapshot and **replays the batch one row at a time, each in its own transaction**, so only the genuinely bad row(s) end up `failed` (`preconfig-import.service.ts:967-1008`, comment: "this intentionally makes a failed batch non-atomic"). `summary.errors` keeps at most 100 entries; `summary.failed` still counts every failure, and `errors_truncated: true` is recorded once the cap is hit (`MAX_SUMMARY_ERRORS`).

`clear_existing`'s soft-delete runs bundled inside batch 1's own transaction when there is a batch to bundle it into, or standalone via `ensureCleared()` for a zero-row sheet or after a batch-1 rollback (`preconfig-import.service.ts:882-897`).

**Cancellation does not undo committed batches.** Closing the wizard's stream (switching business unit, uploading a new file, or navigating away) sets a `cancelled` flag the run loop checks only *between* batches and between per-row retries (`preconfig-import.service.ts:917-920, 991-995`) — a batch transaction already in flight when cancellation arrives runs to completion and commits normally; only batches that have not yet started are skipped. The frontend's own `useUnsavedChanges(runInProgress)` guard (`TenantImportWizard.tsx`) only warns on closing or refreshing the **browser tab** (a `beforeunload` listener) — it does not block or warn on navigating to a different page inside the SPA while an import is running.

Every run — completed, cancelled, or failed — writes exactly one `tb_activity` row on the **tenant** database (`writeActivity()`, `preconfig-import.service.ts:1051-1083`): `action: 'import'`, `entity_type: 'preconfig_import'`, and a `meta_data` blob carrying `step_id`, `file_name`, `options`, the full `summary`, the `outcome`, and `errors_truncated` when applicable. This write is itself best-effort — a failure writing the audit row is logged and swallowed, never surfaced as an import failure (`preconfig-import.service.ts:1079-1082`). For a tester, this row is the one durable, server-side record of what a run actually did, independent of whether anyone was watching the NDJSON stream at the time.

### 3.5 Company Profile: the one step outside the importer, and a permission seam worth knowing

Company Profile's sheet is vertical (label in column A, value in column B — `isVerticalSheet()`, `preconfig-workbook.ts`), not a headered table, and its `target` is `platform`, not `tenant`. `import/stream` refuses it outright before opening any connection (`step.target !== 'tenant'` → the run errors immediately, `preconfig-import.service.ts:682-690`); it is previewed only, through the same `preview()` endpoint, which for a platform-target step runs **before** any tenant connection is resolved (`previewVerticalStep()`, `preconfig-import.service.ts:471-477`) — so a business unit with no tenant database provisioned yet can still be diffed.

`CompanyProfilePanel` (`../carmen-platform/src/pages/tenantImport/CompanyProfilePanel.tsx`) renders the diff and applies it directly through `businessUnitService.update()` — the identical `PUT /api-system/business-units/:id` call the ordinary [Business Units](/en/platform/business-units) edit page's Save button makes, with `doc_version` optimistic locking (a `409` reloads the record and re-diffs rather than overwriting). `BU Code` is shown read-only with a mismatch banner when the sheet's code doesn't match the selected BU, and is never sent in the update payload; `BU Name` is listed as "Not applied" for the same identity reason.

**This write is not gated by `cluster.update`, the permission key the ordinary edit page's own route requires.** `PUT /api-system/business-units/:business_unit_id` is guarded only by `AppIdGuard('businessUnit.update')` (`platform_business-units.controller.ts:374-375`) — an **application-identity allowlist check** against the `x-app-id` header (`app-id.guard.ts`), not a platform-RBAC permission check against the calling user. The endpoint's class-level guard is `KeycloakGuard` alone (authentication only); no `PlatformPermissionGuard`/`@RequirePlatformPermission` sits on this route at all. Concretely: a session holding `data_import.manage` but **not** `cluster.update` is blocked by the frontend from ever opening `/business-units/:id/edit`, but is **not** blocked, at either the frontend (no `<Can>` gate wraps `CompanyProfilePanel`'s Apply button) or the backend, from writing the same fields through this wizard's Company Profile step — the `cluster.update` key that looks like it should also gate this write is never checked on this path.

### 3.6 A live gap in `import/stream`'s error-status mapping

`preview`, `check` and `steps` map backend errors to HTTP status through the generic `Result` → `StdStatus` → `HttpStatus` pipeline (`packages/nest-result/src/base-microservice-controller.ts:194-225`), where `ErrorCode.VALIDATION_FAILURE` always becomes `422 Unprocessable Entity`. `import/stream` cannot use that pipeline — it streams an `Observable`, not a `Result` — so it hand-rolls its own pre-stream mapping, `resolvePreStreamErrorStatus()` (`preconfig-imports.controller.ts:91-95`):

```
if (/not found/i.test(message)) return HttpStatus.NOT_FOUND;
if (/no database connection configured|unsupported database provider/i.test(message)) return HttpStatus.UNPROCESSABLE_ENTITY;
if (/invalid bu_id format/i.test(message)) return HttpStatus.BAD_REQUEST;
return HttpStatus.INTERNAL_SERVER_ERROR;
```

The middle regex matches the connection-failure wording that existed **before** commit `af2437074` (2026-08-13, `resolveConnection` moved from `tb_business_unit.db_connection` to `db_schema` + `tb_database_pool`; confirmed by reading its diff on `tenant.service.ts`). That refactor changed the actual thrown messages to four new ones (`tenant.service.ts:488-503`): `"Business unit {code} is not linked to a database pool"`, `"…has no database schema configured"`, `"Database pool '{name}' … has been deleted"`, `"…is inactive"` — **none of which match the regex**. `preconfig-import.service.ts`'s own `resolveConnection()` (line 129) already calls the post-refactor `resolveConnectionForBusinessUnit()` (confirmed at line 156) and propagates whichever of those four messages `tenant.service.ts` throws straight into `subscriber.error()` (line 696) when the run hasn't started streaming yet. Since the gateway controller `preconfig-imports.controller.ts` was added 2026-08-03 — **before** the Aug 13 refactor — and no commit since has touched `resolvePreStreamErrorStatus()` (checked: `cc0c3b4e6`, `b188a4d80`, `d9cc3ecde`, `2f134a614`, all same-day 2026-08-03, none touch this function), this is a currently-live defect, not a historical one already fixed elsewhere: **a business unit with no linked database pool, no schema, or a deleted/inactive pool returns `500 Internal Server Error` from `import/stream`, instead of the `422` that the identical failure correctly produces from `preview` against the same business unit.** `"Business unit not found"` (→ 404) and `"Invalid bu_id format"` (→ 400, in practice unreachable here since `ParseUUIDPipe` already rejects a malformed id before the service runs) are unaffected. The sibling [Tenant Migrations](/en/platform/tenant-migrations) page (§4.4) documents the identical stale-regex defect on `/deploy/stream`, introduced by the same Aug-13 refactor against a different hand-rolled mapping function.

## 4. Roles and Permissions

| Surface | Permission | Notes |
| --- | --- | --- |
| Sidebar entry, `/tenant-imports` route | `data_import.manage` | `platformNav.ts:15`; `App.tsx:261` — a `manage` key with no separate `.read` tier (§1) |
| `GET /steps`, `POST /:bu_id/check`, `POST /:bu_id/:step_id/preview`, `POST /:bu_id/:step_id/import/stream` | `data_import.manage` | `@RequirePlatformPermission`, checked independently on the backend at every one of the four routes (`preconfig-imports.controller.ts:104,123,149,179`) — the same single key gates read-only Check/Preview and the writing Import stream alike; no finer-grained key exists anywhere in this module |
| Company Profile's "Apply to BU" | **No RBAC permission at all** — `AppIdGuard('businessUnit.update')`, an application-identity allowlist check, not a user-permission check (§3.5) | Neither the frontend (`CompanyProfilePanel.tsx` wraps its Apply button in no `<Can>` gate) nor the backend (`platform_business-units.controller.ts:374-375`, `KeycloakGuard` only at the class level) checks `cluster.update` on this path, even though that is the key the ordinary [Business Units](/en/platform/business-units) edit route requires to reach the same write |

## 5. Related Modules

- [Business Units](/en/platform/business-units) — owns `tb_business_unit` and the `PUT /api-system/business-units/:id` endpoint Company Profile writes through (§3.5); the ordinary edit page's Technical tab and this wizard's picker both read `businessUnitService.getAll()`.
- [Clusters](/en/platform/clusters) — the `cluster.read`/`cluster.update` keys referenced by contrast throughout §1 and §3.5; not used by this module itself.
- [Tenant Migrations](/en/platform/tenant-migrations) — the sibling Organization-group module whose fleet-wide `/deploy/stream` endpoint carries the same class of stale connection-error regex (§4.4 there), introduced by the identical `af2437074` schema-pool refactor.
- [Platform RBAC](/en/platform/rbac) — the platform permission catalog `data_import.manage` and `cluster.update` both live in; this module defines no permission keys of its own beyond `data_import.manage`.

## 6. Reference Sources

All paths `../carmen-platform` (HEAD `157a65e`, 2026-09-04) unless prefixed `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`, 2026-09-06) or `../carmen-platform-e2e` (HEAD `a8e3b31`, 2026-08-25, cited only to confirm the absence of a suite).

- `src/pages/TenantImportWizard.tsx` — the wizard shell, its four-screen state machine, generation-token staleness guards, and the BU switcher wiring.
- `src/pages/tenantImport/{WorkbookDropzone,FileCheckPanel,StepRail,StepPanel,CompanyProfilePanel}.tsx` — every screen and panel, documented in full on [UI Screens](/en/platform/tenant-imports/ui-screens).
- `src/services/preconfigImportService.ts` — the four REST/stream calls (`getSteps`, `check`, `preview`, `importStream`).
- `src/components/nav/platformNav.ts:15`, `src/App.tsx:37,258-264` — nav entry and route registration; commit `80d6872` (2026-08-03).
- `src/i18n/en.ts:3188-3283`, `src/i18n/th.ts:2179-2273` (`tenantImport` namespace) — every user-facing string quoted on this page and [UI Screens](/en/platform/tenant-imports/ui-screens); `src/i18n/en.ts:22,88` / `th.ts:21,85` (`dataImport` nav label).
- `src/types/index.ts:332-418` — `PreconfigStepMeta`, `PreconfigCheckReport`, `PreconfigPreview`, `PreconfigImportOptions`, `PreconfigImportSummary`, `PreconfigImportEvent`.
- `src/utils/docVersion.ts` — the optimistic-lock helpers Company Profile's Apply reuses.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/preconfig-imports/{preconfig-imports.controller,preconfig-imports.service}.ts` — the gateway proxy, its four permission decorators, upload validation (`assertXlsx`), options parsing (`parseOptions`), and the stale `resolvePreStreamErrorStatus()` (lines 47-79, 91-95, 224).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/preconfig-import/{preconfig-import.service,preconfig-catalog,preconfig-workbook,preconfig-lookup,preconfig-related,preconfig-types}.ts` — the importer itself: connection resolution, the twelve-step catalog, workbook parsing/coercion, lookup resolution and staged-creation rollback, dependent-row building, batching/retry, and the `tb_activity` audit write.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/tenant/tenant.service.ts:480-515` — `resolveConnection`/`resolveConnectionForBusinessUnit`, the four connection-failure messages cited in §3.6.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_business-units/platform_business-units.controller.ts:66-70,374-375` — the Business Units controller's class-level guard and the `PUT` route's `AppIdGuard` (§3.5).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/guard/app-id.guard.ts` — what `AppIdGuard` actually checks (an `x-app-id` allowlist, not a user permission).
- `../carmen-turborepo-backend-v2/packages/nest-result/src/base-microservice-controller.ts:194-225` — the generic `ErrorCode` → `HttpStatus` mapping `check`/`preview`/`steps` use, contrasted with `import/stream`'s hand-rolled one.
- Commit `af2437074` (`../carmen-turborepo-backend-v2`, 2026-08-13) — the database-pool connection refactor behind §3.6's finding.
- `../carmen-platform-e2e/tests/` — confirmed to hold no `tenant-imports`/`preconfig-import` suite.

## 7. Pages in This Module

- [UI Screens](/en/platform/tenant-imports/ui-screens) — the four wizard screens walked through step by step: what each asks for, what it validates, what happens on failure, and whether it can be revisited.
