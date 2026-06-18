# Resync to React/Vite stack — progress log (2026-06-18)

Source of truth: `../carmen-inventory-frontend-react`. Scope: inventory book only.

| Module | Pass1 routes-fixed | Pass2 arch-deltas | Pass3 behavior | Notes |
|--------|--------------------|-------------------|----------------|-------|
| config | no stale routes found | no infra prose found | verified — no change (config/page.tsx → config-dashboard.tsx; KPI/bar/pie widget grid with location, business-type, CN-reason, tax-profile, exchange-rate tiles; sub-module list pages follow list+filter+new pattern; matches wiki config module description) | |
| procurement (PR/PO/GRN/credit-note) | no stale routes found | no infra prose found | verified — no change (procurement/page.tsx → procurement-dashboard.tsx; PR/PO/GRN/CN sub-modules each render list component + new/detail routes; approval queue at /procurement/approval; wiki lifecycle flows and screen shapes (list, detail, new) match) | |
| inventory-management (adjustment/physical-count/spot-check/period-end/transaction) | no stale routes found (period-end-process refs are carmen/docs file paths, not app routes) | no infra prose found | verified — no change (inventory-management/page.tsx → inventory-dashboard.tsx; each sub-module renders dedicated _component (ia-component, pc-component, sc-component, pe-component, transaction-component); list+detail+new shape matches wiki; adjustment doc notes Stock-In/Stock-Out tabs which match ia-component JSDoc) | |
| vendor-management (vendor/price-list/request-price-list) | no stale routes found | no infra prose found | verified — no change (vendor-management/page.tsx → vendor-dashboard.tsx; vendor/price-list/price-list-template/request-price-list sub-modules each have page.tsx → list component + [id]/new routes; matches wiki screen shape) | |
| store-operation (store-requisition/wastage/stock-replenishment) | `/store-operations/store-requisitions` → `/store-operation/store-requisition` (EN+TH, REQ-HP-01 test step) | no infra prose found | verified — no change (list/grid, my-pending/all-document, filters, export, print, delete all match sr-component.tsx) | |
| operation-plan (recipe/category/cuisine/equipment) | no stale routes found | no infra prose found | verified — no change (operation-plan/page.tsx → operation-dashboard.tsx; recipe/category/cuisine/equipment each have page.tsx → list component + [id]/new routes; matches wiki screen shape) | |
| product-management | no stale routes found | no infra prose found | verified — no change (product-management/page.tsx → product-dashboard.tsx; product/category sub-modules have page.tsx → pd-component/list component + [id]/new routes; matches wiki product and category screen shape) | |
| system-admin (user-activity/period/workflow/etc.) | no stale routes found | no infra prose found | verified — no change (system-admin/page.tsx → system-admin-landing with LandingHero/LandingChapter tiles; sub-modules (user, role, workflow, period, running-code, activity-log, notification-template, etc.) each have page.tsx → list component + [id]/new routes; matches wiki system-admin module structure) | |
| report | no stale routes found | no infra prose found | verified — no change (report/page.tsx → report-landing.tsx with 3-chapter marketing landing (list → /report/list, schedules → /report/schedules, history → /report/history); report/list/page.tsx → report-component; matches wiki reporting-audit module description of report job pipeline and export) | |
| dashboard | no stale routes found (dashboard/main etc. are justified mock-section docs, not router entries) | no infra prose found; only Next.js ref is intentional historical annotation in widget-workspace.md | verified — no change (dashboard/page.tsx → dashboard-component.tsx; personalised greeting + saved-widgets section with drag-and-drop KPI/pie/bar cards, LookupDataset add-widget picker; matches wiki dashboard/widget-workspace description) | |

## Route gaps (app route with no wiki page) — log only, do not author

Excluded (non-inventory — expected, no action): `/login`, `/not-found`, `/external/pl`, `/pl/:url_token`, `/profile`, `/profile/setting`, `/notifications`

Routes in routes.txt with no explicit wiki page reference (GAP — log only, no pages authored):

| Route | Notes |
|-------|-------|
| `/config/adjustment-type` | config sub-page not yet documented |
| `/config/business-type` | config sub-page not yet documented |
| `/config/certification` | config sub-page not yet documented |
| `/config/credit-note-reason` | config sub-page not yet documented |
| `/config/credit-term` | config sub-page not yet documented |
| `/config/currency` | config sub-page not yet documented |
| `/config/delivery-point` | config sub-page not yet documented |
| `/config/department`, `/:id`, `/new` | config sub-page not yet documented |
| `/config/eco` | config sub-page not yet documented |
| `/config/extra-cost` | config sub-page not yet documented |
| `/config/location`, `/:id`, `/new` | config sub-page not yet documented |
| `/config/tax-profile` | config sub-page not yet documented |
| `/config/unit` | config sub-page not yet documented |
| `/config/exchange-rate` | referenced but as frontend directory path; no wiki sub-page for route |
| `/inventory-management/inventory-adjustment`, `/:id`, `/new` | module documented but route not quoted explicitly |
| `/inventory-management/period-end/review` | period-end documented but /review sub-route not referenced |
| `/inventory-management/physical-count`, `/:id`, `/:id/entry`, `/:id/review`, `/new` | module documented but individual routes not quoted |
| `/inventory-management/spot-check`, `/:id`, `/:id/review`, `/location/:location_id` | module documented but individual routes not quoted |
| `/operation-plan/category/:id`, `/new` | parent route documented; detail routes not quoted |
| `/operation-plan/cuisine/:id`, `/new` | parent route documented; detail routes not quoted |
| `/operation-plan/equipment/:id`, `/new` | parent route documented; detail routes not quoted |
| `/operation-plan/recipe/:id`, `/new` | parent route documented; detail routes not quoted |
| `/procurement/credit-note/:id`, `/new` | parent documented; detail routes not quoted |
| `/procurement/goods-receive-note/:id`, `/new` | parent documented; detail routes not quoted |
| `/procurement/purchase-order/:id`, `/new`, `/from-price-list` | parent documented; detail routes not quoted |
| `/procurement/purchase-request-template/:id`, `/new` | parent documented; detail routes not quoted |
| `/procurement/purchase-request/:id`, `/new` | parent documented; detail routes not quoted |
| `/product-management/product/:id`, `/new` | parent documented; detail routes not quoted |
| `/report/list` | report documented but /list sub-route not quoted |
| `/store-operation/store-requisition/:id`, `/new` | parent documented; detail routes not quoted |
| `/store-operation/wastage-reporting/:id`, `/new` | parent documented; detail routes not quoted |
| `/system-admin/activity-log` | system-admin documented but this sub-route not quoted |
| `/system-admin/notification-template`, `/:id`, `/new` | system-admin documented but this sub-route not quoted |
| `/system-admin/period` | system-admin documented but this sub-route not quoted |
| `/system-admin/role`, `/:id`, `/new` | system-admin documented but this sub-route not quoted |
| `/system-admin/running-code` | system-admin documented but this sub-route not quoted |
| `/system-admin/user/:id` | system-admin documented but detail route not quoted |
| `/system-admin/workflow`, `/:id`, `/new` | system-admin documented but this sub-route not quoted |
| `/vendor-management/price-list-template/:id`, `/new` | parent documented; detail routes not quoted |
| `/vendor-management/price-list/:id`, `/new` | parent documented; detail routes not quoted |
| `/vendor-management/request-price-list/:id`, `/new` | parent documented; detail routes not quoted |
| `/vendor-management/vendor/:id`, `/new` | parent documented; detail routes not quoted |

## Behavior signals (Task 4)

### Signal sources

**Pass 1 route fixes (Task 2):** one module flagged — `store-operation/store-requisition` (route corrected `/store-operations/store-requisitions` → `/store-operation/store-requisition`).

**`-react` git history — functional commits (last 40, grep `feat|fix`, exclude merge/spec/docs/runtime-config/deploy):**

| SHA | Subject | Classification |
|-----|---------|---------------|
| `3af3e24` | feat(profile): signature drawing pad component | out-of-scope (profile, not inventory) — skip |
| `a732c5d` | feat(profile): signature upload/delete hooks | out-of-scope (profile, not inventory) — skip |
| `7067319` | feat(profile): signature endpoint constant, type, and draw library | out-of-scope (profile, not inventory) — skip |
| `1e9cb0b` | fix(build): emit dist/config.json from config.prod.json | infra — skip (build pipeline, no per-module screen behavior) |
| `9e54732` | fix(vendor): send doc_version on update (optimistic concurrency) | already-synced — skip (doc_version documented in `system-config/doc-version.md`, synced 2026-06-17) |
| `ab89572` | fix: round-trip doc_version on update across all config modules | already-synced — skip |
| `ca05512` | fix(delivery-point): send doc_version in update payload | already-synced — skip |
| `d95adcb` | fix(api): strip unsubstituted placeholders from server error messages | infra — skip (cross-cutting HTTP client detail; no per-module screen behavior documented by page) |
| `4ac7b62` | fix(location): display delivery point even when inactive | **ACTIONABLE** — `master-data/location`: location form/view now shows the assigned delivery point even when it is inactive; previously showed "—". Display-only fix but changes observable field value in UI. Not yet documented. |
| `5ec3b23` | fix(location): send doc_version in update payload | already-synced — skip |
| `9d66520` | feat(tables): show "..." placeholder when name is empty | infra — skip (cross-cutting cosmetic default across all list tables; no per-module workflow change) |
| `4c5e276` | fix(data-grid): opt out of React Compiler for table-state consumers | infra — skip (internal React Compiler workaround restoring expected pagination/sort behavior; no new behavior) |
| `76703be` | fix(product-category): round-trip doc_version on category/subcategory/item-group update | already-synced — skip |
| `b0a4c04` | fix(eco): wrap create/update payload under metadata + doc_version on PATCH | already-synced — skip (doc_version synced; payload structure is internal API detail) |
| `1f48d8b` | fix(adjustment-type): send doc_version on PATCH + use lowercase enum values | already-synced — skip (doc_version synced; enum casing is internal API detail) |
| `fe39361` | fix(tax-profile): send doc_version on PATCH (optimistic concurrency) | already-synced — skip |
| `5f3b105` | fix(currency): send doc_version on PATCH + guard decimal_places on edit | already-synced — skip (doc_version synced; decimal_places fallback is a form-default bug fix, not a new behavior) |
| `73c091d` | fix(extra-cost): send doc_version on update (PATCH requires it) | already-synced — skip |
| `9d41e9f` | fix(business-type): send doc_version on update (PATCH requires it) | already-synced — skip |

**grep cross-check** (`grep -ril 'doc_version\|optimistic' en/inventory`): 62 files — confirms doc_version is broadly documented across config, vendor, master-data, GRN, store-requisition, physical-count, adjustment, purchase-order, and system-config sub-pages. The `system-config/doc-version.md` page is the canonical explanation. All doc_version commits above are already synced.

### Actionable modules for Pass 3b (Task 5)

| Module | Reason | Pass3 result |
|--------|--------|--------------|
| `store-operation/store-requisition` | `route-changed` — route fix in Task 2; behavior re-read needed to confirm flow docs still accurate | verified — no change (read sr-component.tsx; list/grid views, my-pending/all-document toggle, status/from-location/to-location/sr-type filters, export, print, delete all match wiki) |
| `master-data/location` | `git:4ac7b62 display delivery point even when inactive` — location form/view now shows inactive delivery point label (reads `delivery_point.name` from nested object, not stale `delivery_point_name`; edit form passes `defaultLabel` so inactive value resolves). Behavior not yet documented in `en/inventory/master-data/location.md`. | fixed: added sentence to §6 Lifecycle bullet (inactive delivery point label still displays, reads nested `delivery_point.name`) and rewrote §4 Delivery-point coupling edge case to reflect nested-object read + `defaultLabel` pattern — EN+TH |

**Total ACTIONABLE: 2 modules. Dropped: 17 commits (8 already-synced, 6 infra/build, 3 out-of-scope).**
