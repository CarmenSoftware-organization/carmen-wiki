# Resync to React/Vite stack — progress log (2026-06-18)

Source of truth: `../carmen-inventory-frontend-react`. Scope: inventory book only.

| Module | Pass1 routes-fixed | Pass2 arch-deltas | Pass3 behavior | Notes |
|--------|--------------------|-------------------|----------------|-------|
| config | no stale routes found | no infra prose found | | |
| procurement (PR/PO/GRN/credit-note) | no stale routes found | no infra prose found | | |
| inventory-management (adjustment/physical-count/spot-check/period-end/transaction) | no stale routes found (period-end-process refs are carmen/docs file paths, not app routes) | no infra prose found | | |
| vendor-management (vendor/price-list/request-price-list) | no stale routes found | no infra prose found | | |
| store-operation (store-requisition/wastage/stock-replenishment) | `/store-operations/store-requisitions` → `/store-operation/store-requisition` (EN+TH, REQ-HP-01 test step) | no infra prose found | | |
| operation-plan (recipe/category/cuisine/equipment) | no stale routes found | no infra prose found | | |
| product-management | no stale routes found | no infra prose found | | |
| system-admin (user-activity/period/workflow/etc.) | no stale routes found | no infra prose found | | |
| report | no stale routes found | no infra prose found | | |
| dashboard | no stale routes found (dashboard/main etc. are justified mock-section docs, not router entries) | no infra prose found; only Next.js ref is intentional historical annotation in widget-workspace.md | | |

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
(filled in Task 4)
