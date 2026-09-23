---
title: Inventory Period (formerly Period)
description: Inventory (accounting) periods and per-period cost snapshots. Renamed from Period on 2026-09-16 — tb_inventory_period*, /system-admin/inventory-period, api/:bu_code/inventory-periods, key system_admin.inventory_period. Plain CRUD.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: system-config, period, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Inventory Period (formerly Period)

> **At a Glance**
> **Owner:** Sysadmin / Finance Manager &nbsp;·&nbsp; **Table:** `tb_inventory_period` (+ `tb_inventory_period_snapshot`, `tb_inventory_period_comment`) — renamed from `tb_period*` on 2026-09-16 &nbsp;·&nbsp; **Route:** `/system-admin/inventory-period` (old `/system-admin/period` redirects) &nbsp;·&nbsp; **Endpoint:** `api/:bu_code/inventory-periods` (old `api/:bu_code/periods` kept as a hidden alias) &nbsp;·&nbsp; **Permission / licence key:** `system_admin.inventory_period` &nbsp;·&nbsp; **Used by:** GRN, stock-in, stock-out/SR issue, physical count, costing engine, footer status bar &nbsp;·&nbsp; **Admin screen is a plain list + create/edit dialog — no dedicated Close/Lock/Reopen actions or Snapshot tab exist.**

![Period screen](/screenshots/system-config/period.png)

## Rename notice (2026-09-16)

The module was renamed from **Period** to **Inventory Period** in three breaking backend commits on 2026-09-16 (`7601e6e83` internal rename, `a92151730` HTTP path, `c8de2fa76` permission/licence/`api_name` keys, `3933277dc` tables) to separate it from the GL accounting period (`tb_gl_period`, `config/gl-periods` — an accounting-module concept outside this book) and from `tb_physical_count_period`. This page keeps its wiki slug (`period`) so existing links keep working; every code-facing name below is the new one.

| Surface | Before | After (HEAD) | Source |
|---|---|---|---|
| Tenant tables | `tb_period`, `tb_period_comment`, `tb_period_snapshot` | `tb_inventory_period`, `tb_inventory_period_comment`, `tb_inventory_period_snapshot` | tenant migration `20260916141000_rename_tb_period_to_tb_inventory_period` (metadata-only `ALTER TABLE … RENAME`; constraint names re-prefixed; index names untouched because the schema `map:`s them; `enum_period_status` deliberately **not** renamed) |
| HTTP path | `api/:bu_code/periods[/current|/next|/:period_id]` | `api/:bu_code/inventory-periods[/current|/next|/:period_id]` | `apps/backend-gateway/src/application/inventory-periods/inventory-periods.controller.ts:67-416`; the old path still resolves through `inventory-periods-legacy.controller.ts` (`@ApiExcludeController`, same guards, same service — deprecated alias) |
| `AppIdGuard` api names | `period.*` | `inventoryPeriod.findOne` / `findAll` / `create` / `update` / `delete` | same controller |
| Permission resource | `system_admin.period` | `system_admin.inventory_period` (`view`/`create`/`update`/`delete`) | platform migration `20260916140000_rename_period_to_inventory_period`; `seed.permission.data.ts` |
| Licence feature | `system_admin.period` ("Period") | `system_admin.inventory_period` ("Inventory Period") | same migration + `20260916150000_fix_license_group_item_inventory_period_key`; `license-catalog.generated.ts` |
| Licence route map | `app:periods` | `app:inventory-periods` → `system_admin.inventory_period`; `config:period-comments` also points at the new key | `packages/prisma-shared-schema-platform/prisma/permission.route-map.ts` |
| Frontend | `routes/system-admin/period/`, `/system-admin/period` | `routes/system-admin/inventory-period/` (`inventory-period-component.tsx`, `-dialog.tsx`, `-card.tsx`, `-form-schema.ts`, `use-inventory-period.ts`, `use-inventory-period-table.tsx`), `/system-admin/inventory-period`; `router.tsx:640-643` keeps `period` as a `<Navigate replace>` redirect "so old bookmarks don't break"; `constant/permissions.ts:119` `system_admin.inventory_period`; `constant/module-list.ts:611-615` | FE `06c68975`, `1caecb42` |
| Bruno | `master-data/period/*` | folder **not renamed**, but every request URL inside it already points at `/api/{{bu_code}}/inventory-periods…` (Bruno PR #27); `config/period-comment/*` still uses `api/config/:bu_code/period-comments/:period_id` (that controller was not renamed) | `carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/period/` |
| Comments | `config_period-comments` controller, `tb_period_comment` | controller path unchanged (`api/config/:bu_code/period-comments`), table renamed to `tb_inventory_period_comment` | `apps/backend-gateway/src/config/config_period-comments/` |

Deploy order matters: the platform migration must run before or with the gateway — a gateway that renames `api_name` before the `tb_application_api` rows are renamed answers 401 and bounces users to login (commit message of `c8de2fa76`). The tenant table rename is a hard cutover: old code pointing at `tb_period` breaks the moment the migration runs.

## Implementation status (re-verified 2026-09-22)

The `/system-admin/inventory-period` screen (`inventory-period-component.tsx` + `inventory-period-dialog.tsx`) is still a **generic CRUD list**: search, status filter, Add / Generate Next / Export / Print, and a row-edit dialog with plain fields — `fiscal_year`, `fiscal_month`, `start_at`, `end_at`, and a **status `<Select>`** offering `open`/`closed`/`locked` directly (`inventory-period-form-schema.ts:17` `z.enum(["open","closed","locked"])`, dialog `:192-207`), submitted like any other field via `PATCH`. Status renders as an icon + label in the list since 2026-08-24 (`26a403d4`). There is still no distinct "Close" / "Lock" / "Reopen" button, confirmation or audit-reason prompt, or "Snapshot" tab anywhere in the component tree. The enum values and posting-guard semantics (§5, §6) are unaffected by the rename — but §6's guard description was corrected this pass after reading `inventory-period.helper.ts`: **`locked` does not block inbound postings; only `closed` does.**

## 1. What & Who

Inventory periods define the accounting calendar Carmen's inventory ledger operates on — one row per fiscal month, identified by `YYMM` plus `fiscal_year` / `fiscal_month` integers and a `[start_at, end_at]` day range. Every period has a status (`open`, `closed`, `locked`) gating which dated documents can be numbered and posted. Periods are the unit at which inventory cost is closed and snapshotted: when finance closes January, no further January GRNs / stock-ins may post, and the closing balance becomes February's opening balance.

`tb_inventory_period_snapshot` stores the per-location / per-product / per-lot inventory snapshot at a point in time — generated by the costing engine and used for trial balances and roll-forward. No screen in this module renders it (see Implementation status) — it is written and read by the costing engine only.

The **footer status bar** of every screen (`components/footer/status-bar.tsx`, FE `ad213a11`, 2026-09-18) shows the current period as `YYYY-MM` next to the app and backend versions. It reads the period from the `/user/profile` payload the bar already loads — *not* from `inventory-periods/current` — and the backend version from `GET /version` (`{ version, commit }`, `apps/backend-gateway/src/app.controller.ts:71-75`, BE `94b44828d`), failing soft to nothing when the gateway predates that endpoint.

**Maintained by** Sysadmin (typically Finance Manager) via the plain edit dialog. **Read by** every posting guard and the costing engine.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Open the next periods | Inventory Period list → **Generate Next** (`CalendarPlus` button) | `POST api/:bu_code/inventory-periods/next` with `{ count, start_day }` (`types/inventory-period.ts` `GenerateNextInventoryPeriodDto`); `count` must be positive (`COMMON_COUNT_MUST_BE_POSITIVE`); the service starts from the month after the last *open* period, else the last period of any status, else the current month, and creates them as `open` (`inventory-period.service.ts:315-470`) |
| Change a period's status | Row → **Edit** → **Status** dropdown → Save | Same generic edit dialog as fiscal year/month/dates — picking `closed` or `locked` here is a plain field edit, not a distinct workflow action; `PATCH` requires `doc_version` (`COMMON_DOC_VERSION_REQUIRED`, `:243`) |
| Find the current period | `GET api/:bu_code/inventory-periods/current` | Earliest period whose status is `open` **or `locked`** (`:478-497`) |
| View snapshot | ~~Period detail → Snapshot tab~~ | **No such screen exists** — snapshots are costing-engine-internal |
| Generate close snapshot | Costing engine job | Writes `tb_inventory_period_snapshot` for every (location, product, lot); not triggered from this screen |
| Export the period list | Inventory Period list → **Export** | XLSX with period / fiscal year / fiscal month / dates / status columns |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| `GRN_DATE_OUTSIDE_OPEN_PERIOD` (GRN), equivalent stock-in / stock-out catalog errors | Document date resolves to no period, or to a `closed` one — see §6 | Use a date inside an `open`/`locked` period; for issues (stock-out / SR) the date must be inside the *current* period |
| `PERIOD_ALREADY_EXISTS` / `PERIOD_FISCAL_COMBINATION_EXISTS` | Duplicate `period` or `(fiscal_year, fiscal_month)` among non-deleted rows | Edit the existing row (`packages/error-catalog/src/catalog.ts:959-978`) |
| `PERIOD_NOT_FOUND` | Unknown `period_id` | Refresh the list |
| `period` mismatch with fiscal date | `period != (fiscal_year-2000) * 100 + fiscal_month` | Recompute and fix one value |
| Roll-forward discrepancy | Closing N ≠ Opening N+1 | Surfaces in `diff_amount`; review snapshot (not visible in any UI — query directly) |
| Status changed to `closed`/`locked` with no confirmation step | Expected — the edit dialog has no distinct guard for this field | There is no undo screen; re-edit the row back to `open` if this was a mistake |
| Old bookmark `/system-admin/period` | Route renamed | Client-side redirect to `/system-admin/inventory-period` (`router.tsx:640-643`) |
| 401 bounce to login right after a deploy | Gateway deployed before platform migration `20260916140000` renamed `tb_application_api.api_name` | Apply the migration; see Rename notice |

## 4. Edge Cases

- **Status is a plain editable field, not a workflow.** Any user with `system_admin.inventory_period.update` can set any status value directly — there is no separate audit-reason prompt for reopening a closed period.
- **`locked` is not "closed" to the posting guards.** `OPEN_STATUSES = [open, locked]` in `inventory-period.helper.ts:18`; both `findOpenPeriodForDate` and `findCurrentOpenPeriod` accept `locked`. The only status that blocks postings is `closed`. Treat `locked` as a Finance-facing label with no runtime effect at HEAD.
- **Last-day membership.** `end_at` is stored as midnight UTC of the last day of the month, so the guard compares day-to-day (`toValidDate` + day normalisation, `:20-42`); a document dated on the last day belongs to that period (a live bug fixed since baseline — every tenant used to report "no open period" on the 31st).
- **Guard runs where the running number is issued**, not only on create — a draft raised while the period was open and submitted after it closed is rejected at submit (`:167-176`).
- **Snapshot regeneration.** Re-running close for the same period either overwrites or appends per Finance policy; **append at new `snapshot_at`** is the recommended audit-preserving pattern (costing-engine behaviour, unconfirmed against a UI since none exists here).
- **Roll-forward integrity.** Opening N+1 must equal Closing N for every (location, product, lot); discrepancies tracked in `diff_amount`.

---

## 5. Data Model (Dev)

Source: tenant schema (`schema.prisma:1223-1351`).

### 5.1 `tb_inventory_period`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `period` | `String @db.VarChar` | No | `YYMM` (e.g. `2609`). |
| `fiscal_year` / `fiscal_month` | `Int @db.Integer` | No | `YYYY` + `1`-`12`. |
| `start_at` / `end_at` | `DateTime @db.Timestamptz(6)` | No | Midnight UTC of the first / last day (day-granular, see §4). |
| `status` | `enum_period_status` | No | `open` (default), `closed`, `locked`. Enum name unchanged by the rename. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-concurrency token — see [system-config/doc-version](/en/inventory/system-config/doc-version). |
| `note` / `info` / `dimension` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([period, deleted_at])` (`period_period_u`) + `@@unique([fiscal_year, fiscal_month, deleted_at])` (`period_fiscal_year_month_u`). Indexes on `[fiscal_year, fiscal_month]` and `[period]` (index names kept from the old table). Reverse relations to `tb_inventory_period_snapshot`, `tb_inventory_transaction_cost_layer`, `tb_inventory_period_comment`, `tb_physical_count_period`. **`enum_period_status`:** `open`, `closed`, `locked`.

### 5.2 `tb_inventory_period_snapshot`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` / `period_id` | `String @db.Uuid` | No | Keys. |
| `snapshot_at` | `DateTime @db.Timestamptz(6)` | No | Exact snapshot instant (typically close datetime). |
| `location_id` / `product_id` | `String @db.Uuid` | No | Position keys. |
| `location_code` / `location_name` / `product_code` / `product_name` / `product_local_name` / `product_sku` | `String?` | Yes | Denormalised display. |
| `lot_no` / `lot_index` / `lot_at_date` / `lot_seq_no` | — | Yes | Optional lot identification. |
| `opening_qty` / `opening_cost_per_unit` / `opening_total_cost` | `Decimal? @db.Decimal(20,5)` | Yes | Carried from prior period. |
| `receipt_qty` / `receipt_total_cost` | `Decimal?` | Yes | In-period GRN. |
| `issue_qty` / `issue_total_cost` | `Decimal?` | Yes | In-period SR / stock-out. |
| `adjustment_qty` / `adjustment_total_cost` | `Decimal?` | Yes | In-period IA / count / spot-check. |
| `closing_qty` / `closing_cost_per_unit` / `closing_total_cost` | `Decimal?` | Yes | Position at `snapshot_at`. |
| `diff_amount` | `Decimal?` | Yes | Rounding / true-up residual. |
| `doc_version` | `Int` | No | Default `0`. |
| `note` / `info` / `dimension` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([period_id, snapshot_at, deleted_at])` (`periodsnapshot_period_id_snapshot_at_u`). Index on `[period_id, snapshot_at]`. FK `onDelete: NoAction`.

### 5.3 API surface

```
GET    api/:bu_code/inventory-periods            list (default sort status asc, fiscal_year asc, fiscal_month asc)
GET    api/:bu_code/inventory-periods/current    earliest period with status in (open, locked)
GET    api/:bu_code/inventory-periods/:period_id
POST   api/:bu_code/inventory-periods            { fiscal_year, fiscal_month, start_at, end_at, status? }
POST   api/:bu_code/inventory-periods/next       { count, start_day }
PATCH  api/:bu_code/inventory-periods/:period_id { doc_version, ...fields }
DELETE api/:bu_code/inventory-periods/:period_id
```

Every route is `KeycloakGuard` + `AppIdGuard('inventoryPeriod.<verb>')`; RBAC resource `system_admin.inventory_period` via the licence/permission route map. The same seven routes exist under the deprecated `api/:bu_code/periods…` prefix (hidden from Swagger).

## 6. Business Rules

- **Uniqueness.** Both `period` and `(fiscal_year, fiscal_month)` unique among non-deleted; should agree (`period == (fiscal_year-2000) * 100 + fiscal_month` for 2000-2099).
- **Date integrity.** `start_at < end_at`; periods contiguous, non-overlapping (Generate Next produces them that way; the edit dialog does not re-check overlap server-side — unconfirmed, no overlap error in the catalog).
- **Status is a free-form field in the UI, not an enforced state machine.** The edit dialog's status `<Select>` offers all three values unconditionally regardless of the row's current status, and no backend transition guard (e.g. blocking `locked → open`) exists in `inventory-period.service.ts`. Treat `open → closed → locked` as *intended* usage discipline.
- **Inbound posting guard (GRN, stock-in): the document date must fall inside a period whose status is `open` or `locked`.** `assertDateInOpenPeriod` — `good-received-note.logic.ts:113`, `good-received-note.verify-create.ts`, `stock-in.service.ts:525`.
- **Outbound posting guard (stock-out, SR issue): the document date must fall inside the *current* period** (earliest still open/locked), deliberately stricter so back-dated issues cannot consume lots in an order the ledger never saw — `assertDateInCurrentPeriod`, `stock-out.service.ts:400,534`, `sr-date.helper.ts`.
- **`closed` is the only blocking status.** A prior version of this page said "closed/locked"; corrected 2026-09-22.
- **Snapshot generation.** `(period_id, snapshot_at)` per `(location, product, optional lot)`; append-at-new-`snapshot_at` preserves audit.
- **Roll-forward integrity.** Opening N+1 = Closing N per tuple.
- **Deletion guards.** Periods with snapshots / cost layers / postings cannot be deleted (FKs are `NoAction`).

## 7. Cross-References

- [inventory](/en/inventory/inventory) — current-stock writes pass the period guard.
- [costing](/en/inventory/costing) — engine reads movement layers and writes snapshots at close.
- [good-receive-note](/en/inventory/good-receive-note), [inventory-adjustment](/en/inventory/inventory-adjustment) (stock-in / stock-out) — posting-date period check.
- [store-requisition](/en/inventory/store-requisition) — issue date must be inside the current period; SR date is frozen on submit.
- [physical-count](/en/inventory/physical-count) — count documents frozen against a period via `tb_physical_count_period` (the FE reads `period.tb_inventory_period.period` / `.end_at`, `pc-component.tsx:245-248`).
- [spot-check](/en/inventory/spot-check) — variance posting period guard.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `enum_period_status` (line 1223), `tb_inventory_period` (1229-1261), `tb_inventory_period_comment` (1263-1296), `tb_inventory_period_snapshot` (1298-1351).
- **Migrations:** tenant `20260916141000_rename_tb_period_to_tb_inventory_period`; platform `20260916140000_rename_period_to_inventory_period`, `20260916150000_fix_license_group_item_inventory_period_key`.
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/inventory-periods/inventory-periods.controller.ts` (+ `inventory-periods-legacy.controller.ts` alias).
- **Service / guards:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-period/inventory-period.service.ts`; `.../inventory/inventory-period.helper.ts` (`findOpenPeriodForDate`, `findCurrentOpenPeriod`, `assertDateInOpenPeriod`, `assertDateInCurrentPeriod`).
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/inventory-period/`; `types/inventory-period.ts`; footer `components/footer/status-bar.tsx`, `hooks/use-backend-version.ts`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/period/` (URLs already `/inventory-periods`), `config/period-comment/`.
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1105-system-period.md` — catalog only (32 cases, re-audited against `routes/system-admin/inventory-period` on 2026-09-20; no Playwright spec).
