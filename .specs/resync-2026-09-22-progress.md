# Re-sync 2026-09-22 — progress log

Scope agreed 2026-09-22 (grilling session): both books, EN only (TH deferred by
owner decision), diff-based against each book's last sync + a ~10-page/book
spot-check of permission / enum / API-shape claims, no screenshot recapture,
one branch + PR per book, push to dev Wiki.js before merge, merge is the
owner's step. Coverage checklists updated in the same PR; `carmen/docs` drift
recorded in `.specs/carmen-docs-drift-2026-09-22.md` (Inventory phase).

## Platform book — branch `docs/resync-platform-2026-09-22`

Baseline: carmen-platform `157a65e` (2026-09-04) → HEAD `f1c69f1` (2026-09-22),
20 commits / 78 files. Backend-v2 platform-side: `20260908…drop_business_unit_interface`,
`20260910…{license_feature_group_kind,business_unit_interface_license,migrate_interface_groups_to_inf_license}`,
`20260916…{rename_period_to_inventory_period,fix_license_group_item_inventory_period_key}`.
Status: **done, EN only** — 27 pages edited, 0 new pages, nav unchanged.

| Theme | SPA PRs | Pages touched | Notes |
|---|---|---|---|
| Interface entitlement → licence feature → INF licence | #286, #287, #288, #289, #291 | `licenses` (+3 sub-pages), `license-catalog` (+2), `business-units` (+3), `cluster-admin` (+1), `platform-config` (+1) | New §3.6 on the Licenses landing; new DM §2.4 (`tb_business_unit_interface_license`); group `kind`; `interface_days`; `INTERFACE_CONFIG.showNoExpiry: true` recorded as an owner reversal of spec §3.2; catalog re-counted 107/12/100/7 by diffing the seed file (+19/−2, incl. `system_admin.period` → `inventory_period`) |
| Tenant migration Resolve + Schema column | #296, #297 | `tenant-migrations` (+DM), `business-units/tenant-migrations`, `business-units/ui-screens` §4.5 | Closes the "resolve() has no frontend caller" finding; DM §6 recommendation struck through as done |
| Sortable column headers | #290, #292, #293 | `licenses/ui-screens`, `activity-events`, `applications/ui-screens`, `news/ui-screens`, `rbac/ui-screens`, `broadcasts/ui-screens`, `users`, `clusters/ui-screens`, `cluster-admin/ui-screens`, `business-units/ui-screens` | Backend keys verified where cheap (`buildSortable` 8 keys; `access`; `JSON_SORT_KEYS`; `permission_count`; `status` on 3 licence services); broadcasts `severity` noted as "verify on a gateway newer than 2026-09-09" |
| Landing Print Mapping row removed | #283 | `landing` | Drift table updated; Report Form Groups still missing |
| `seed/check-application-api` ops | #282 | `platform-migrations` | 9 seeds + 7 checks |
| BU list stored-page snap-back | #298 | `business-units`, `business-units/ui-screens` | `outOfRangePage()` |

Spot-check (claim-type sample, 10 pages): `licenses/permissions` §2 controller line numbers re-read against HEAD; `cluster-admin/ui-screens` §7 "no `<Link to=`" claim found **stale** and corrected; `tenant-migrations` §3.3 "no frontend caller" claim found **stale** and corrected; `landing` §4 Print Mapping claim found **stale** and corrected; `license-catalog` counts found **stale** and corrected; `activity-events` §3.1 sort whitelist line numbers found stale (service moved to `micro-business`) and corrected. No fabricated claim found in the sample — every stale claim traced to real drift after 2026-09-06.

Not touched (out of scope by decision): screenshots; TH mirrors (all 27 TH twins now lag EN — see wiki_structure_decisions memory); Inventory-book consequences of the `GET /api/license` change (handled in the Inventory phase).

## Inventory book — branch `docs/resync-inventory-2026-09-22`

(pending — baseline `21fa189`, 2026-07-29)
