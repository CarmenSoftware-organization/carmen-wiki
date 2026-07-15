# Full Wiki Snapshot Re-sync — Progress Log (2026-07-15)

Branch: `docs/resync-2026-07-15`. Spec: `.specs/2026-07-15-full-wiki-snapshot-resync-design.md`.
Approach B: snapshot-verify every page against current source. Last sync: 2026-06-25 (`207d842`).

## Inventory book (source: ../carmen-inventory-frontend-react, backend-v2, bruno, e2e, micro-report/micro-data)

| Module | Pages | Status | Claims fixed | New pages | Screenshot routes flagged |
|--------|-------|--------|--------------|-----------|---------------------------|
| purchase-request | 16 | EDITED (6 pages) | Fixed doc-lifecycle wording on the module landing page (was `Draft→Submitted→Under Review→Approved/Rejected/Sent Back`, actual `enum_purchase_request_doc_status = {draft,in_progress,voided,approved,completed}` — no separate submitted/rejected states, reject converges on voided). Rewrote 03-user-flow-purchaser.md and 04-test-scenarios-purchaser.md: Purchaser is the `enum_stage_role=purchase` stage inside the PR's own approval chain (edit vendor/price/discount/tax + Auto Allocate + bulk Approve/Reject/Send-for-Review/Split, matches 304-pr-purchaser-journey.spec.ts) — the previous "Convert-to-PO workbench" (per-line vendor deviation %, convert-qty, Allocate Vendor dialog at conversion time) does not exist; real Convert-to-PO is a separate 2-step whole-PR dialog in the Purchase Order module (`po-from-pr-dialog.tsx`) grouping by vendor+delivery_date+currency (not vendor+currency). Rewrote 03-user-flow-procurement-manager.md and 04-test-scenarios-procurement-manager.md: stripped a fabricated "Vendor Allocation Rules / Stuck PR Oversight" configuration surface with no matching route/component/endpoint — PM is just the escalated `approve`-role stage using the identical Approver UI. Updated 04-test-scenarios.md personas/cross-persona table (X-PR-01, X-PR-04, X-PR-05, X-PR-07) to match. |
| purchase-order | 18 | pending | | | |
| good-receive-note | 13 | pending | | | |
| store-requisition | 16 | pending | | | |
| inventory | 14 | pending | | | |
| inventory-adjustment | 14 | pending | | | |
| physical-count | 10 | pending | | | |
| spot-check | 10 | pending | | | |
| product | 11 | pending | | | |
| recipe | 18 | pending | | | |
| vendor-pricelist | 14 | pending | | | |
| master-data | 14 | pending | | | |
| system-config | 11 | pending | | | |
| access-control | 6 | pending | | | |
| dashboard | 9 | pending | | | |
| reporting-audit | 8 | pending | | | |
| costing | 11 | pending | | | |
| templates | 2 | pending | | | |

## Platform book (source: ../carmen-platform)

| Module | Pages | Status | Claims fixed | New pages | Screenshot routes flagged |
|--------|-------|--------|--------------|-----------|---------------------------|
| clusters | 3 | pending | | | |
| business-units | 2 | pending | | | |
| users | 3 | pending | | | |
| applications | 3 | pending | | | |
| rbac | 3 | pending | | | |
| report-templates | 4 | pending | | | |
| print-template-mapping | 3 | pending | | | |
| news | 3 | pending | | | |
| broadcasts | 3 | pending | | | |
| changelog (page) | 1 | pending | | | |
| profile (page) | 1 | pending | | | |

## Root/landing pages

| Page | Status |
|------|--------|
| en/home.md + th/home.md | pending |
| en/inventory.md + th/inventory.md | pending |
| en/platform.md + th/platform.md | pending |

## Discrepancy log

(claims found in wiki with no source backing — one bullet each: page, claim, what source actually says)

- `en/th/inventory/purchase-request/03-user-flow-purchaser.md` + `04-test-scenarios-purchaser.md` (pre-fix): described a per-line "Convert-to-PO workbench" with a pricelist-deviation-tolerance indicator, per-line "convert quantity" field, and a per-line "Allocate Vendor dialog" invoked at conversion time. The actual conversion UI (`carmen-inventory-frontend-react/routes/procurement/purchase-order/po-from-pr-dialog.tsx`, confirmed against `POST .../purchase-orders/group-pr` and `POST .../purchase-orders/confirm-pr` Bruno specs) is a 2-step dialog that selects whole approved PRs and groups them server-side by `(vendor, delivery_date, currency)` — no per-line controls exist. Fixed in this pass.
- `en/th/inventory/purchase-request/03-user-flow-procurement-manager.md` + `04-test-scenarios-procurement-manager.md` (pre-fix): described a "Vendor Allocation Rules" configuration screen (scoring weights, per-vendor priority overrides) and a "Stuck PR Oversight" bulk-action view owned by the Procurement Manager. No matching route, frontend component, or backend endpoint found in `carmen-inventory-frontend-react` or `carmen-turborepo-backend-v2`, and no such route appears in `.specs/resync-2026-07-15-routes-inventory.txt`. Fixed in this pass — PM is documented as the escalated `approve`-role stage using the identical Approver UI.
- `en/th/inventory/purchase-request.md` (pre-fix): At-a-Glance and Overview described the PR lifecycle as `Draft→Submitted→Under Review→Approved/Rejected/Sent Back`. Prisma's `enum_purchase_request_doc_status` (confirmed in `carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`) and the frontend `PR_STATUS` enum (post commit `278fc91`, 2026-07-07: "trim PR document status to the 5 real backend values") only have `{draft, in_progress, voided, approved, completed}` — there is no distinct `submitted`/`under_review`/`rejected` document status; "Submitted" maps to `in_progress`, and reject converges on `voided`. Fixed in this pass. (Note: `01-data-model.md` and `02-business-rules.md` already documented this correctly — only the module landing page's prose was stale.)
- `en/th/inventory/purchase-request/03-user-flow-purchaser.md` + `04-test-scenarios-purchaser.md` PUR-PERM-04 (pre-fix, and briefly in the first pass of this resync): implied the Convert-to-PO dialog is gated by purchase-order create permissions and that a Requestor/HOD would be denied. Source shows **no enforcement**: Bruno docs for `POST .../purchase-orders/group-pr` and `POST .../purchase-orders/confirm-pr` both list `Permissions: None`; the backend controller methods have no permission/role guard; the frontend dialog chain (`po-create-dialog.tsx` → `po-from-pr-dialog.tsx`) has no `hasPermission` check, and the `PERMISSIONS` catalog defines `procurement.purchase_order` as `viewOnly()` (no `.create` key, unreferenced by the dialog). E2E `TC-PR-410004` ("No Permission to Convert PR", `301-pr.spec.ts`) exists but does not assert denial — an absent button passes via `expect(true).toBe(true)`. Pages corrected to state that access is gated only by reaching the Purchase Order module UI; denial behavior should be treated as unimplemented until a guard lands.
- **Unverified / deferred** — `03-user-flow-audit-config.md` and `04-test-scenarios-audit-config.md` describe a dedicated "PR Activity Queries" audit workspace and a "Configuration workspace" (PR Workflow Settings, PR Type Defaults, Delegation Rules, Tax Codes, Currency Rates as distinct pages) with per-scenario preview panels and forecasts. No matching routes were found in `routes-inventory.txt` or the frontend during this pass, but this heavily overlaps the **system-config** module's scope (generic workflow / running-code / tax-profile / currency screens do exist elsewhere in the product, just not under these PR-specific names) — recommend re-verifying against the actual system-config screens when that module's iteration runs, rather than concluding fabrication from this iteration alone. Not rewritten in this pass.

## Route gaps

(source routes with no wiki page — carried decisions in Task 5)

- carmen-platform: `/sql-workbench` (App.tsx:312) and `*` catch-all exist in App.tsx but are absent from SITEMAP.md — SITEMAP drift; route is captured in routes-platform.txt

## Deferred

(anything postponed, with reason — e.g. backend down for screenshots)
