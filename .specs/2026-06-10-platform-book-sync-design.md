# Platform Book Sync — Design (2026-06-10)

Full synchronization of the Carmen Platform wiki book with the current state of
`../carmen-platform/` (commit `f9e4a22`, 2026-06-10). The existing book was written
2026-05-19/20 and the app has since gained eight new modules and replaced its entire
access-control model.

**Source of truth:** carmen-platform source code (`src/App.tsx`, `src/pages/`,
`src/services/`, `src/types/index.ts`, `src/context/AuthContext.tsx`,
`src/utils/permissions.ts`, `src/data/changelog.json`, `docs/OVERVIEW.md`, `CLAUDE.md`).
Do **not** trust `SITEMAP.md` in that repo — it is stale (missing `/applications`,
`/news`, `/broadcasts/new`, `/platform/*` routes; still documents `allowedRoles` guards).

## 1. Why

Two drivers:

1. **The access model changed out from under the book.** The app moved from a
   `platform_role` enum (`platform_admin`, `support_manager`, `support_staff`, …) with
   `allowedRoles` route guards to a permission-based RBAC system:
   - Permission keys `resource.action` (e.g. `cluster.read`) in a backend-generated catalog.
   - Roles = named permission bundles (`/platform/roles`), delta add/remove semantics.
   - Assignments per user with **scope** = `{type:'platform'}` or `{type:'cluster', cluster_id}`
     (`/platform/user-platform`).
   - Super admin = separate `is_super_admin` flag that bypasses all checks
     (`/platform/super-admins`), not an enum value.
   - Route guards now `requiredPermission="resource.action"`; sidebar filters on
     `hasPermission()`; `platform_role` removed from the User model (commit `6091ffc`).
   - Login validates effective permissions (`GET /api/user/permission/platform`) with a
     bootstrap exception (user count 0–1 skips the check).

   The wiki's `auth-roles.md` documents the old model and is therefore wrong in kind,
   not merely stale. Module pages' "Roles and Personas" sections (§4) all cite
   `allowedRoles` arrays that no longer exist.

2. **Eight new app modules have no wiki coverage:** Applications, Print Template
   Mapping, News, Broadcasts, Platform Roles, Permission Catalog, Super Admins,
   User Platform.

## 2. Decisions (user-approved)

- **Scope: full sync** — add all missing modules AND update all stale existing pages, EN+TH.
- **Depth: full structure for every new module** — landing + `data-model.md` +
  `ui-screens.md` + `permissions.md`.
- **Structure: Approach B — consolidate RBAC.** The four `/platform/*` identity screens
  are one system (catalog → roles → assignments → bypass) and share one data model, so
  they become a single wiki module `rbac/` instead of four thin folders. The other four
  app modules are independent entities and get their own folders.
- **`auth-roles.md` is deleted** (EN+TH), replaced by `rbac.md`. Old URL
  `/en/platform/auth-roles` will 404; acceptable for an internal manual. All inbound
  links are rewritten.

## 3. New modules (5 folders, mirrored EN + TH)

Every landing follows the existing Platform-book shape (see `en/platform/clusters.md`):
frontmatter → intro → **At a Glance** blockquote → numbered §1 Overview … §7 Sub-pages.
Sub-pages follow `.specs/platform-sub-page-template.md`.

### 3.1 `rbac/` — Platform RBAC (replaces `auth-roles`)

| Page | Content |
|---|---|
| `rbac.md` | Concept overview: permission keys, catalog, roles, user assignments + scope, super-admin bypass, `EffectivePermissions` shape (`{platform: string[], clusters: Record<string,string[]>, is_super_admin?}`), `checkPermission()` resolution order (super-admin → platform perms → cluster perms), login flow + bootstrap exception, migration note from the legacy role enum. |
| `rbac/data-model.md` | `Role`, `RoleWriteData` (delta `permissions: {add, remove}`), `PermissionCatalogItem` (`key`/`resource`/`action`/`description`), `UserRoleAssignment` + `Scope` union, `SuperAdminRow`, `EffectivePermissions`. Endpoints: `GET/POST/PUT/DELETE /api-system/platform/roles[/:id]`, `GET /api-system/platform/permissions`, `GET/POST/DELETE /api-system/platform/super-admins[/:id]`, `GET/POST/DELETE /api-system/platform/users/:userId/roles[/:assignmentId]`, `GET /api/user/permission/platform`. Note multi-layer `{data}` envelope tolerance. |
| `rbac/ui-screens.md` | Four screens: Roles list/edit (PermissionPicker accordion, permission-count badge, Created/Updated audit columns), Permission Catalog (read-only resource-grouped cards, reached from Roles header — no sidebar item), Super Admins (add/remove rows, super-admin-only route), User Platform list (Roles count badge via background N+1 fetch, name composed from firstname/middlename/lastname) + detail (Roles & Scope card, add-role form with platform/cluster scope select, `user_platform.manage` gates). |
| `rbac/permissions.md` | Gate matrix: `role.read/create/update` for Roles + Catalog, `requireSuperAdmin` for Super Admins, `user_platform.read` vs `user_platform.manage` for User Platform. How route guards (`requiredPermission`) and in-page `<Can>` gates compose. Bootstrap exception. Edge cases + recommendations. |

### 3.2 `applications/`

| Page | Content |
|---|---|
| `applications.md` | API client registry; each application's UUID is the `x-app-id` header clients send; access model `allow_all` vs explicit `api_names`. |
| `data-model.md` | `Application`, `ApplicationWritePayload` (`details.add` only when `allow_all` false; PUT = replace semantics, full set not delta), `ApiCatalogGroup`. Endpoints under `/api-system/applications` incl. `/api-catalog` (grouped response with client-side `groupApiNames()` fallback; module = prefix before first `.`). |
| `ui-screens.md` | List (App ID monospace column, Access badge "All APIs"/"N APIs", status filter, CSV export, Created/Updated columns) + edit (grouped-by-module accordion selector: filter input auto-expands matches, per-module All/None, expand/collapse-all, selected/total badges; read mode grouped badges; ChipInput fallback when catalog load fails). |
| `permissions.md` | `application.read/create/update/delete` gates; sidebar item in Platform group gated on `application.read`. |

### 3.3 `print-template-mapping/`

| Page | Content |
|---|---|
| `print-template-mapping.md` | Resolves which FastReport template prints for a document type (PR, PO, SR, GRN, …), with BU allow/deny rules, default flag, display label/order. |
| `data-model.md` | `PrintTemplateMapping`, `DocumentType`, `PrintTemplateMappingCreateInput`; relation to `ReportTemplate` (`kind='print'`, `report_group` matches document type, denormalized `template_name`/`template_group`). Endpoints under `/api-system/print-template-mappings` incl. `/document-types` and `/resolve?document_type=X&bu_code=Y` (allow-list AND not-deny-list at runtime). |
| `ui-screens.md` | List is a **deliberate deviation** from the standard DataTable Management pattern: card layout grouped by document type, document-type select + active-only checkbox, no search/CSV/pagination. Edit: single-mode form, template dropdown filtered by `kind='print'` + matching `report_group` with "N match / M total" badge, comma-separated allow/deny BU inputs, default + active checkboxes. |
| `permissions.md` | `print_template_mapping.read/create/update/delete`; sidebar in Content group. Edge cases: one default per document type is a convention the UI does not enforce. |

### 3.4 `news/`

| Page | Content |
|---|---|
| `news.md` | Announcements/news articles, global or BU-targeted, draft → published → archived. |
| `data-model.md` | `News` (`contents` markdown, `image_url` + legacy `image` fallback, `business_unit_ids` [] = global, `published_at` server-set, nested `Audit` object, soft delete via `deleted_at` / `audit.deleted.at`), `NewsStatus`. Endpoints under `/api/news` (note: `/api`, not `/api-system`); create/update are `multipart/form-data` with inline `image` file and JSON-encoded `business_unit_ids`. |
| `ui-screens.md` | List (image thumbnail column preserving aspect ratio, status badges, Target column "Global"/"N BUs", Published + Updated columns with actor) + edit (MarkdownEditor write/preview tabs, ImageUpload drag-drop, Publishing card, Targeting card with global checkbox + BU multi-select, Metadata card, unsaved-changes guard, Ctrl/Cmd+S). |
| `permissions.md` | `news.read/create/update` gates; targeting validation (≥1 BU when not global). |

### 3.5 `broadcasts/`

| Page | Content |
|---|---|
| `broadcasts.md` | Push-notification compose; the only module that is a single compose screen (`/broadcasts/new`), no list. |
| `data-model.md` | `BroadcastTargetMode` (`system_all`/`system_users`/`bu`), `BroadcastSystemPayload` (optional `userIds`), `BroadcastBuPayload` (`bu_code`, code not ID), type resolution `SYS_<PRESET>`/`BU_<PRESET>` incl. custom `[A-Z0-9_]+`, `scheduled_at`. Endpoints `POST /api/notifications/broadcasts/system|bu` (note: `/api`). Fire-and-forget — nothing to list or edit afterward in this SPA. |
| `ui-screens.md` | Compose form: three target-mode tabs, recipients UserMultiSelect, BU select (active BUs, "Name (CODE)"), title 200-char / message 2000-char counters, type presets + custom, send-now vs schedule (future datetime), confirmation dialog (destructive styling for ALL-users), reset, keyboard shortcuts. |
| `permissions.md` | Single `broadcast.send` gate (route, sidebar "Send Broadcast" in Content group, send button). |

New-page count: 5 landings + 15 sub-pages = 20 EN + 20 TH = **40 new pages**.

## 4. Updates to existing pages (EN + TH)

| Page(s) | Changes |
|---|---|
| `clusters.md`, `clusters/{data-model,ui-screens,permissions}.md` | §4 / permissions: replace `allowedRoles` model with `requiredPermission` (verify exact keys in `src/App.tsx` during implementation) and link to `rbac`. Add: logo/avatar branding upload on edit (`BrandingImageUpload`, rect logo + square avatar), logo thumbnail column, Created/Updated columns with actor from nested `audit` object, optional Deleted-by info. |
| `business-units.md`, `business-units/{data-model,ui-screens}.md` | Same branding + audit-column + permission-guard updates as clusters. |
| `users.md`, `users/{data-model,lifecycle,ui-screens}.md` | Avatar column (initials fallback, presigned `avatar_url`), avatar in edit header, name composed from firstname/middlename/lastname, `platform_role` removed → point role assignment to `rbac` (User Platform), audit columns, Deleted badge with `deleted_by_name`. |
| `report-templates.md` + sub-pages | Permission guards updated; cross-link to `print-template-mapping` explaining `kind='print'` + `report_group` relationship. Content otherwise unchanged (no app changes since 2026-05-20). |
| `profile.md` | `PATCH` (not PUT) per backend alignment commit `9dc27ee`; `platform_role` no longer shown. |
| `changelog.md` | Sync v0.1.0 entries from `src/data/changelog.json`; document version badge on landing page and sidebar footer. |
| `platform.md` (book landing) | New section layout: 1 Tenancy (Clusters, Business Units) · 2 Identity & Access (Users, **RBAC**, Profile) · 3 Content (News, Broadcasts) · 4 Platform (Applications) · 5 Reporting (Report Templates, **Print Template Mapping**) · 6 Product (Changelog). |
| All pages linking `/platform/auth-roles` | Rewrite to `/platform/rbac`. Known referrers (both locales): users, business-units, report-templates, profile, clusters/permissions, platform.md. Re-grep before finishing. |

## 5. Cross-cutting

- **TH parity backfill:** create `th/platform/report-templates/data-model.md` and
  `th/platform/report-templates/permissions.md` (EN exists, TH missing).
- **Deletions:** `en/platform/auth-roles.md`, `th/platform/auth-roles.md`.
- **Nav:** update `scripts/nav-overrides.yaml` platform block — rename group entries
  (`auth-roles` → `rbac`), add Content + Platform groups, add `changelog` (currently
  missing from nav), add the five new module slugs. Rebuild with
  `python3 scripts/sync_nav.py --mode=build`.
- **Frontmatter:** every new page gets `date` = `dateCreated` = creation timestamp;
  every edited page updates `date` only. Validate all touched pages with
  `python3 .specs/verify_frontmatter.py`.
- **Conventions:** numbered `## N.` sections, comparison tables over prose, pseudo-code
  fenced blocks without language tag, ฿ for money examples, Edge Cases table +
  Recommendations at the end of design-ish pages, no inline cross-locale links.
- **Screenshots: out of scope.** `assets/screenshots/platform/` has only `.gitkeep`;
  no capture pipeline exists for the platform SPA. Pages are written without screenshot
  embeds (can be added later when a pipeline exists).

## 6. Out of scope / intentionally not done

- No changes to the Inventory book.
- No edits to `SITEMAP.md` or any other file in the carmen-platform repo (different
  repo; its staleness is noted to the user, not fixed here).
- No persona-split sub-pages (inventory-PR-style 01–04 files) — the Platform book keeps
  its own established sub-page set (data-model / ui-screens / permissions).
- No screenshot capture for platform screens.

## 7. Risks / verification

- **Facts drift:** all module facts in this design come from three Explore-agent reports
  over the carmen-platform source at `f9e4a22`. During implementation, verify exact
  permission keys and route gates directly in `src/App.tsx` and `src/components/Layout.tsx`
  rather than trusting the summaries.
- **Rendering check:** after push, spot-check new pages on the dev Wiki.js instance
  (`http://dev.blueledgers.com:3987/`) — especially tables and the rbac landing.
- **Link integrity:** grep for `auth-roles` after the rewrite; expect zero hits outside
  `.specs/` and `docs/` historical records.
