# Platform Re-sync 2026-09-05 — Progress Log

Spec: `.specs/2026-09-05-platform-resync-design.md`
Source HEAD: `157a65e` (2026-09-04)
Branch: `docs/resync-platform-2026-09-05`

## Ruling note (from controller pre-flight, binding on this map)

- **R1**: this book's page shape is a sibling landing file plus a folder of sub-pages
  (`en/platform/clusters.md` next to `en/platform/clusters/{data-model,ui-screens,permissions}.md`).
  There is **no `index.md` anywhere** in the book — every new module below follows this shape.
- The plan creates **16** new modules, not 17: `license-features` and
  `license-feature-groups` are two tabs (`FeatureCatalogPanel` / `GroupCatalogPanel`) of one
  screen, `LicenseCatalog.tsx` (confirmed by reading the component: it renders both panels
  behind a `TabStrip`, each backed by its own service). Documented as a single
  `license-catalog` module. The two original nav rows, permissions, and feature-flag keys
  are both preserved and noted in the row below — this is a documentation merge, not a
  product merge.
- `print-template-mapping` is being deleted in Task 11 (feature removed from the product,
  `de11377`, 2026-07-24). It has **no row** in this source map. Its route no longer exists in
  `src/App.tsx` (confirmed absent from the Step 2 regeneration below) — the SPA side of the
  removal is already done; only the wiki module remains to be deleted.
  **Stale e2e note**: `../carmen-platform-e2e/tests/print-template-mapping/` still exists on
  disk and is stale — do not treat it as coverage for anything; fixing/removing that e2e
  suite is out of scope for this plan.

## No static permission-key catalog

`../carmen-platform` has no static permission-key catalog file. `src/utils/permissions.ts`
defines only `PERMISSIONS.BROADCAST.SEND = 'broadcast.send'` (one constant, with a comment
directing future duplicated literals to be hoisted the same way) plus the pure
`checkPermission` / `checkPlatformAuthority` functions — every other permission key used in
the app is a bare string literal at its call site (nav item `permission:` field, or a
`<Can permission="...">` / `hasPermission('...')` call in a page component). Per-menu keys
live in `src/components/nav/platformNav.ts` (platform side) and
`src/components/nav/clusterAdminNav.ts` (cluster-admin side, which has **no permission
filtering at all** — see the `cluster-admin` row). The full permission catalog as humans can
browse it is served to `PermissionCatalog.tsx` (`/platform/category-permissions`) from the
backend at runtime; it is not enumerable from source alone.

The "Permission key" column below lists the nav-gating (list/read) key first; CRUD-level
keys found in the page components are noted in parentheses where they differ from the read
key. These are the keys later tasks should verify against; a module marked "list only"
had no separate create/update/delete literal found by grep and should be re-checked by
whichever task verifies that module's page.

## Source map

| Module | Routes | Components | Service | Permission key | Feature key | e2e suite |
|--------|--------|-----------|---------|----------------|-------------|-----------|
| `clusters` | `/clusters`, `/clusters/new`, `/clusters/:id/edit` | `ClusterManagement`, `ClusterEdit` | `clusterService.ts` | `cluster.read` (nav; also gates `business-units` and `tenant-migrations` nav rows) + `cluster.create`/`cluster.update`/`cluster.delete` | `clusters` | `clusters` |
| `business-units` | `/business-units`, `/business-units/new`, `/business-units/:id/edit` | `BusinessUnitManagement`, `BusinessUnitEdit` | `businessUnitService.ts` + `businessUnitLicenseService.ts` (Licenses tab, split out of Users per `#276`) | `cluster.read` (nav; BU shares the Clusters resource) | `business_units` | `business-units` |
| `users` | `/users`, `/users/new`, `/users/:id/edit` | `UserManagement`, `UserEdit` | `userService.ts` + `userRoleService.ts` | `user.read` (nav) + `user.create`/`user.update`/`user.delete` | `users` | `users` |
| `rbac` | `/platform/roles`, `/platform/roles/new`, `/platform/roles/:id/edit`, `/platform/category-permissions` | `RoleManagement`, `RoleEdit`, `PermissionCatalog` | `roleService.ts`, `permissionService.ts` | `platform_role.read` (nav, roles only) + `platform_role.create`/`update`/`delete`; **`/platform/category-permissions` has no nav entry and no permission gate** — reachable by any authenticated platform user (`PrivateRoute` only) | `platform_roles` (roles only; category-permissions has none) | `roles`, `permission-catalog` |
| `applications` | `/applications`, `/applications/new`, `/applications/:id/edit` | `ApplicationManagement`, `ApplicationEdit` | `applicationService.ts` | `application.read` (nav) + `application.create`/`update`/`delete` | `applications` | `applications` |
| `broadcasts` | `/broadcasts`, `/broadcasts/new`, `/broadcasts/:id/edit` | `BroadcastManagement`, `BroadcastCompose`, `BroadcastEdit` | `broadcastService.ts` | `broadcast.read` (nav) + `PERMISSIONS.BROADCAST.SEND` (`broadcast.send`, the one hoisted constant) / `broadcast.update` / `broadcast.delete` | `broadcasts` | `broadcast` |
| `news` | `/news`, `/news/new`, `/news/:id/edit` | `NewsManagement`, `NewsEdit` | `newsService.ts` | `news.read` (nav) + `news.create`/`update`/`delete` | `news` | `news` |
| `report-templates` | `/report-templates`, `/report-templates/new`, `/report-templates/:id/edit` | `ReportTemplateManagement`, `ReportTemplateEdit` | `reportTemplateService.ts` | `report_template.read` (nav) + `report_template.create`/`update`/`delete` | `report_templates` | `report-templates` |
| `licenses` | `/licenses`, `/licenses/:clusterId`, `/licenses/subscriptions/new`, `/licenses/subscriptions/:id/edit`, `/licenses/seats/new`, `/licenses/seats/:id/edit`, `/licenses/bu-quota/new`, `/licenses/bu-quota/:id/edit`, plus `/subscriptions*` legacy redirects (`Navigate` / `SubscriptionEditRedirect`) | `LicenseCenter`, `ClusterLicenseDetail`, `SubscriptionForm`, `LicensePurchaseForm` | `subscriptionService.ts`, `clusterLicenseService.ts`, `businessUnitLicenseService.ts`, `expiryThresholdService.ts` | `subscription.read` (nav) + `subscription.manage`/`license.manage` (CRUD) | `licenses` | **none — no e2e backing** |
| `license-catalog` | `/license-features`, `/license-feature-groups`, `/license-feature-groups/new`, `/license-feature-groups/:id/edit` | `LicenseCatalog` (single component, two tabs: `FeatureCatalogPanel`, `GroupCatalogPanel`), `LicenseFeatureGroupEdit` | `licenseFeatureService.ts`, `licenseFeatureGroupService.ts` (+ `subscriptionService.ts` inside `GroupCatalogPanel`) | Features tab: `license_feature.read` (nav) + `license_feature.manage`; Groups tab: `license_feature_group.read` (nav) + `license_feature_group.manage` — **two separate nav rows/permission pairs feed one documented module** | Features tab: `license_features`; Groups tab: `license_feature_groups` | **none — no e2e backing** |
| `cluster-admin` | `/cluster-admin`, `/cluster-admin/:clusterId/cluster`, `/cluster-admin/:clusterId/business-units`, `/cluster-admin/:clusterId/business-units/:buId/edit`, `/cluster-admin/:clusterId/users`, `/cluster-admin/:clusterId/licenses`, `/cluster-admin/:clusterId/profile` | `ClusterAdminEntry`, `ClusterProfile`, `ClusterAdminBusinessUnitList` (`BusinessUnitList.tsx`), `ClusterAdminBusinessUnitForm` (`BusinessUnitForm.tsx`), `ClusterAdminUsers` (`ClusterUsers.tsx`), `ClusterAdminLicenses`, `Profile` (shared with the platform-side profile page) | `clusterAdminService.ts` | **none** — `ClusterAdminRoute` applies no permission filtering; clearing the route guard is the whole check (second persona, distinct from platform-side RBAC) | `cluster_admin_cluster`, `cluster_admin_business_units`, `cluster_admin_licenses`, `cluster_admin_users` (from `clusterAdminNav.ts`, separate key namespace from the platform nav despite identical menu labels) | **none — no e2e backing** |
| `platform-config` | `/platform/configs` | `PlatformConfigManagement` | `platformConfigService.ts` | `platform_config.read` (nav) + `platform_config.manage` (all card saves) | `platform_config` | **none — no e2e backing** |
| `email-settings` | `/platform/email-settings` | `EmailSettingManagement` | `emailSettingService.ts` | `email_setting.read` (nav) + `email_setting.manage` | `email_settings` | **none — no e2e backing** |
| `user-platform` | `/platform/user-platform`, `/platform/user-platform/:userId` | `UserPlatformManagement`, `UserPlatformEdit` | `userPlatformService.ts` + `userRoleService.ts`, `roleService.ts`, `clusterService.ts`, `userService.ts` | `user_platform.read` (nav) + `user_platform.manage` | `user_platform` | `user-platform` |
| `super-admins` | `/platform/super-admins` | `SuperAdminManagement` | `superAdminService.ts` | none — gated by `superAdminOnly: true` in nav, not a `permission` string | `super_admins` | `super-admins` |
| `feature-flags` | `/platform/features` | `FeatureFlagManagement` | `featureFlagService.ts` | `feature_flag.manage` (nav; single key, no separate `.read`) | **none — deliberately ungated**: comment in `platformNav.ts` says a switch that could hide itself could never be restored from the UI | **none — no e2e backing** |
| `tenant-migrations` | `/tenant-migrations` | `TenantMigrationManagement` (+ `DeployConsole`, `FleetSync`) | `tenantMigrationService.ts` + `businessUnitService.ts` | `cluster.read` (nav; shares the Clusters resource, no dedicated `tenant_migration.*` key found) | `tenant_migrations` | **none — no e2e backing** |
| `tenant-imports` | `/tenant-imports` | `TenantImportWizard` | `preconfigImportService.ts` + `businessUnitService.ts` | `data_import.manage` (nav) | `tenant_imports` | **none — no e2e backing** |
| `usage-analytics` | `/analytics` | `UsageAnalytics` (+ `StatCards`, `TopList`, `UsageChart`) | `analyticsService.ts` | `activity_event.read` (nav) + `activity_event.detail` (drill-down) | `usage_analytics` | **none — no e2e backing** |
| `activity-events` | `/activity-events` | `ActivityEventManagement` (+ `EventDetailSheet`) | `analyticsService.ts` | `activity_event.detail` (nav) | `activity_events` | **none — no e2e backing** |
| `platform-migrations` | `/platform/migrations` | `PlatformMigrationManagement` (+ `OpRow`, `RunConsole`) | `platformMigrationService.ts`, `platformSeedService.ts` + `businessUnitService.ts` | none — gated by `superAdminOnly: true`, not a `permission` string | `platform_migrations` | **none — no e2e backing** |
| `database-pools` | `/platform/database-pools`, `/platform/database-pools/new`, `/platform/database-pools/:id/edit` | `DatabasePoolManagement`, `DatabasePoolEdit` | `databasePoolService.ts` | `database_pool.read` (nav) + `database_pool.manage` | `database_pools` | **none — no e2e backing** |
| `cronjobs` | `/cronjobs`, `/cronjobs/new`, `/cronjobs/:id/edit` | `CronJobManagement`, `CronJobEdit` (+ `CronJobFilterSheet`, `CronScheduleField`) | `cronjobService.ts` | `cronjob.read` (nav) + `cronjob.manage` | `cronjobs` | **none — no e2e backing** |
| `report-form-groups` | `/report-form-groups` | `ReportFormGroupManagement` (+ `GroupCard`) | `reportTemplateService.ts` (shared with `report-templates`, no dedicated service file) | `report_template.read` (nav; shares the Report Templates resource, no dedicated `report_form_group.*` key found) | `report_form_groups` | **none — no e2e backing** |
| `sql-workbench` | `/sql-workbench` | `SqlWorkbench` | `sqlQueryService.ts` | `sql_workbench.read` (nav) + `sql_workbench.manage` (Run/Save/Drop — three mutating actions share one permission string per a comment in `SqlWorkbench.tsx`) | `sql_workbench` | **none — no e2e backing** |
| `dashboard` | `/dashboard` | `Dashboard` | Aggregates `clusterService.ts`, `businessUnitService.ts`, `userService.ts`, `applicationService.ts`, `newsService.ts`, `reportTemplateService.ts` (summary counts only, no dedicated dashboard service) | none in nav — visible to anyone with platform authority | none | `dashboard` |
| `landing` | `/` | `Landing` | none (static; reads `AuthContext` only, redirects authenticated users) | none — public route | none | `landing` |
| `profile` | `/profile` (shared component also serves `/cluster-admin/:clusterId/profile`) | `Profile` | `api.ts` (generic client, no dedicated profile service) | none — acts on the caller's own account | none | `profile` |
| `changelog` | `/changelog` | `Changelog` | none — reads static `src/data/changelog.json`, not an API service | none — public route (not wrapped in `PrivateRoute`) | none | `changelog` |

### Modules with no e2e backing (15 of the 29 rows above)

`licenses`, `license-catalog`, `cluster-admin`, `platform-config`, `email-settings`,
`feature-flags`, `tenant-migrations`, `tenant-imports`, `usage-analytics`,
`activity-events`, `platform-migrations`, `database-pools`, `cronjobs`,
`report-form-groups`, `sql-workbench`. (`super-admins` and `user-platform` — both new
modules — DO have e2e backing; see the source-map table above.) Every claim written for
the 15 no-e2e modules in Phase 3 must be sourced from implementation alone and marked
"no e2e backing" in the Status table below, per the design doc's error-handling rule.

`../carmen-platform-e2e/tests/` also holds `auth` and `journeys`, which are cross-cutting
(login flow / multi-step journeys) and do not map one-to-one to any single wiki module.

## Status

| # | Module | Type | EN | TH | Claims fixed | e2e backing | Routes visually changed | Commit |
|---|--------|------|----|----|--------------|-------------|-------------------------|--------|
