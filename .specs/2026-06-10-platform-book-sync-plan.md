# Platform Book Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Synchronize the Carmen Platform wiki book with carmen-platform@`f9e4a22` — add 5 new modules (rbac, applications, print-template-mapping, news, broadcasts) with full landing + 3 sub-pages each, update all stale existing pages from the legacy `allowedRoles` model to permission-based RBAC, delete `auth-roles`, backfill TH parity, and rebuild nav. EN + TH mirrored.

**Architecture:** Pure Markdown content work in this repo. EN pages are authored first from source-code facts (Prisma platform schema primary for data-model pages, SPA source for ui/permissions pages); TH pages are then full Thai translations of the finished EN pages (Thai prose, English technical terms, same structure). Existing-page updates are surgical edits, not rewrites. `auth-roles` deletion happens only after every inbound link is rewritten to `rbac`.

**Tech Stack:** Markdown + Wiki.js frontmatter. Verifier: `.specs/verify_frontmatter.py`. Nav: `scripts/nav-overrides.yaml` + `scripts/sync_nav.py`. Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main` (direct commits approved).

**Reference spec:** `.specs/2026-06-10-platform-book-sync-design.md`
**Sub-page convention:** `.specs/platform-sub-page-template.md` (read before any sub-page task)
**Calibration targets (tone, density, At-a-Glance shape):**
- Landing: `en/platform/clusters.md` (section titles §1 Overview, §2 Business Context, §3 Key Concepts, §4 Roles and Personas, §5 Related Modules, §6 Edge Cases & Gotchas, §7 Sub-pages — verify exact titles by reading the file)
- data-model: `en/platform/users/data-model.md`
- ui-screens: `en/platform/clusters/ui-screens.md`
- permissions: `en/platform/clusters/permissions.md`

---

## Common Context

### Sources of truth

**Primary for data-model pages (Prisma platform schema):**
`../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`

| Module | Models (start line) |
|---|---|
| rbac | `tb_platform_permission` (921), `tb_platform_role` (939), `tb_platform_role_tb_permission` (958), `tb_user_tb_platform_role` (978), `tb_platform_super_admin` (1000) |
| applications | `tb_application` (75), `tb_application_api` (98). Also present: `tb_application_role` (31), `tb_application_role_tb_permission` (55), `tb_user_tb_application_role` (580) — check whether the SPA surfaces these; if not, mention in §5 Divergences as schema-only entities. |
| print-template-mapping | `tb_print_template_mapping` (776); referenced: `tb_report_template` (701) |
| news | `tb_news` (803), `enum_news_status` (693) |
| broadcasts | `tb_broadcast_notification` (357), `tb_user_broadcast_action` (388); referenced: `tb_notification` (316) |

Every data-model page carries the source-of-truth callout from `.specs/platform-sub-page-template.md` §2.1 (Prisma path + "generated copy is not authoritative" note).

**Secondary (carmen-platform SPA, at commit `f9e4a22`):**

| Area | Files |
|---|---|
| Routing + guards | `src/App.tsx`, `src/components/PrivateRoute.tsx`, `src/components/Layout.tsx` (sidebar groups + `permission:` / `superAdminOnly:` gates) |
| Auth/RBAC runtime | `src/context/AuthContext.tsx`, `src/utils/permissions.ts` (`checkPermission`), `src/types/index.ts` (`EffectivePermissions`, `Scope`, `Role`, `PermissionCatalogItem`, `UserRoleAssignment`) |
| RBAC screens | `src/pages/RoleManagement.tsx`, `RoleEdit.tsx`, `PermissionCatalog.tsx`, `SuperAdminManagement.tsx`, `UserPlatformManagement.tsx`, `UserPlatformEdit.tsx`; services `roleService.ts`, `permissionService.ts`, `superAdminService.ts`, `userRoleService.ts` |
| Applications | `src/pages/ApplicationManagement.tsx`, `ApplicationEdit.tsx`, `src/services/applicationService.ts`, `src/utils/apiCatalog.ts` |
| Print mapping | `src/pages/PrintTemplateMappingManagement.tsx`, `PrintTemplateMappingEdit.tsx`, `src/services/printTemplateMappingService.ts` |
| News | `src/pages/NewsManagement.tsx`, `NewsEdit.tsx`, `src/services/newsService.ts`, `src/components/ImageUpload.tsx` |
| Broadcasts | `src/pages/BroadcastCompose.tsx`, `src/services/broadcastService.ts`, `src/components/UserMultiSelect.tsx` |
| Existing-module deltas | `src/pages/ClusterManagement.tsx`, `ClusterEdit.tsx`, `BusinessUnitManagement.tsx`, `BusinessUnitEdit.tsx`, `UserManagement.tsx`, `UserEdit.tsx`, `Profile.tsx`, `src/components/BrandingImageUpload.tsx` |

Do **not** consult `../carmen-platform/SITEMAP.md` (stale: missing `/applications`, `/news`, `/broadcasts/new`, `/platform/*`; still documents `allowedRoles`).

### Route → guard matrix (verified in `src/App.tsx` @ f9e4a22)

| Route | Guard |
|---|---|
| `/`, `/login`, `/changelog` | Public |
| `/dashboard`, `/profile` | Authenticated (PrivateRoute, no permission prop) |
| `/clusters` · `/new` · `/:id/edit` | `cluster.read` · `cluster.create` · `cluster.update` |
| `/applications` · `/new` · `/:id/edit` | `application.read` · `application.create` · `application.update` |
| `/business-units` · `/new` · `/:id/edit` | `cluster.read` · `cluster.create` · `cluster.update` — **reuses cluster keys; BUs have no keys of their own. Call this out explicitly in business-units and rbac pages.** |
| `/users` · `/new` · `/:id/edit` | `user.read` · `user.create` · `user.update` |
| `/report-templates` · `/new` · `/:id/edit` | `report_template.read` · `.create` · `.update` |
| `/print-template-mapping` · `/new` · `/:id/edit` | `print_template_mapping.read` · `.create` · `.update` |
| `/news` · `/new` · `/:id/edit` | `news.read` · `news.create` · `news.update` |
| `/broadcasts/new` | `broadcast.send` |
| `/platform/roles` · `/new` · `/:id/edit` | `role.read` · `role.create` · `role.update` |
| `/platform/permissions` | `role.read` |
| `/platform/super-admins` | `requireSuperAdmin` |
| `/platform/user-platform` · `/:userId` | `user_platform.read` (both); in-page `<Can permission="user_platform.manage">` gates Add/Remove |

### RBAC runtime facts (for Tasks 1, 6–10)

- `EffectivePermissions = { platform: string[], clusters: Record<string,string[]>, is_super_admin?: boolean }`, fetched post-login via `GET /api/user/permission/platform`, cached in localStorage.
- `checkPermission(eff, key, {clusterId?})` resolution order: super-admin → `platform[]` → (no clusterId: any cluster) / (clusterId: that cluster only). See `src/utils/permissions.ts:10-22`.
- Bootstrap exception: if total user count is 0 or 1, login skips the "must have ≥1 permission" gate (`AuthContext.tsx`).
- Legacy `platform_role` enum removed from frontend in commit `6091ffc`; login no longer validates role names (commit `5f629f2`); Profile aligned to `PATCH` (commit `9dc27ee`).
- Role write payloads use delta semantics: `permissions: { add: string[], remove?: string[] }`.

### Module API endpoints (confirmed in SPA services)

| Module | Endpoints |
|---|---|
| rbac | `GET/POST /api-system/platform/roles`, `GET/PUT/DELETE /api-system/platform/roles/:id`, `GET /api-system/platform/permissions`, `GET/POST /api-system/platform/super-admins`, `DELETE /api-system/platform/super-admins/:id`, `GET/POST /api-system/platform/users/:userId/roles`, `DELETE /api-system/platform/users/:userId/roles/:assignmentId`, `GET /api/user/permission/platform` |
| applications | `GET/POST /api-system/applications`, `GET/PUT/DELETE /api-system/applications/:id`, `GET /api-system/applications/api-catalog` (returns `{api_names, groups?}`; client falls back to `groupApiNames()` — module = prefix before first `.`) |
| print-template-mapping | `GET/POST /api-system/print-template-mappings`, `GET/PUT/DELETE /api-system/print-template-mappings/:id`, `GET .../document-types`, `GET .../resolve?document_type=X&bu_code=Y` |
| news | `GET/POST /api/news`, `GET/PUT/DELETE /api/news/:id` — **`/api`, not `/api-system`**; create/update are `multipart/form-data` (inline `image` file; `business_unit_ids` JSON-encoded string) |
| broadcasts | `POST /api/notifications/broadcasts/system`, `POST /api/notifications/broadcasts/bu` — **`/api`, not `/api-system`** |

### Frontmatter rules

- New pages: `date` = `dateCreated` = `2026-06-10T12:00:00.000Z` (EN) / `2026-06-10T13:00:00.000Z` (TH).
- Edited pages: update `date` to `2026-06-10T12:00:00.000Z` (or TH time), never touch `dateCreated`.
- Tags: landings `platform/<module>, carmen-software`; sub-pages match their module's existing sub-page tag shape (check a sibling).
- `published: true`, `editor: markdown` always.

### TH translation conventions (match existing `th/platform/*.md`)

- H1: `# <Thai name> (<English name>)` — e.g. `# คลัสเตอร์ (Clusters)`. If no natural Thai noun exists, keep English (existing TH pages title "Clusters" as `คลัสเตอร์`).
- Thai prose; keep code identifiers, route paths, permission keys, component names, table/field names in English.
- Internal links point to `/th/...` paths only — never `/en/...` (no cross-locale links).
- Same section numbering and table structure as the EN page.

### Per-page verification (run before each commit)

```bash
python3 .specs/verify_frontmatter.py <file>.md
grep -L '^> \*\*At a Glance\*\*' <file>.md | grep . && echo "FAIL: missing At a Glance" || echo "OK"
grep -nE 'TBD|TODO' <file>.md && echo "FAIL: placeholder" || echo "OK: no placeholders"
grep -nE '\(/th/' <en-file>.md && echo "FAIL: cross-locale link" || echo "OK"   # for EN pages
grep -nE '\(/en/' <th-file>.md && echo "FAIL: cross-locale link" || echo "OK"   # for TH pages
grep -nE 'allowedRoles|platform_role|support_manager|support_staff' <file>.md && echo "CHECK: legacy-role mention — allowed only in explicit migration/history notes" || echo "OK"
```

### Page size calibration

Landings 120–200 lines; sub-pages 150–300 lines. Match the prose density of the calibration targets — these are reference pages, not stubs.

---

## File Structure

**Created (EN):** `en/platform/{rbac,applications,print-template-mapping,news,broadcasts}.md` + `en/platform/{rbac,applications,print-template-mapping,news,broadcasts}/{data-model,ui-screens,permissions}.md` — 20 files.
**Created (TH):** same 20 under `th/platform/`, plus backfill `th/platform/report-templates/{data-model,permissions}.md` — 22 files.
**Modified (EN):** `en/platform.md`; `en/platform/clusters.md` + 3 sub-pages; `business-units.md` + 2 sub-pages; `users.md` + 3 sub-pages; `report-templates.md` + `report-templates/permissions.md`; `profile.md`; plus any other `auth-roles` referrers found by grep (includes `README.md`).
**Modified (TH):** mirrors of the EN modifications.
**Deleted:** `en/platform/auth-roles.md`, `th/platform/auth-roles.md`.
**Modified (infra):** `scripts/nav-overrides.yaml`.
**Untouched:** everything under `*/inventory/`, `assets/`, `.specs/` history, carmen-platform repo.

---

## Task 1: EN `rbac` module (4 pages)

**Files:**
- Create: `en/platform/rbac.md`, `en/platform/rbac/data-model.md`, `en/platform/rbac/ui-screens.md`, `en/platform/rbac/permissions.md`

- [ ] **Step 1: Read calibration + sources.** Read `en/platform/clusters.md`, `.specs/platform-sub-page-template.md`, then the RBAC SPA files and Prisma models listed in Common Context (models at lines 921–1023).

- [ ] **Step 2: Write `en/platform/rbac.md` (landing).** Frontmatter title `Platform RBAC`, tags `platform/rbac, carmen-software`. At-a-Glance: module purpose (permission-based access control replacing the legacy role enum), audience, key entities (`tb_platform_permission`, `tb_platform_role`, `tb_user_tb_platform_role`, `tb_platform_super_admin`), sub-pages: 3. Sections:
  - §1 Overview — the four screens (`/platform/roles`, `/platform/permissions`, `/platform/super-admins`, `/platform/user-platform`) as one pipeline: catalog defines keys → roles bundle keys → assignments bind role+scope to users → super-admin bypasses all.
  - §2 Business Context — why permission-based: per-cluster scoping for support staff, API-client parity (Applications use the same `resource.action` shape), bootstrap story.
  - §3 Key Concepts — permission key format; role (delta add/remove writes); `Scope` union (`{type:'platform'} | {type:'cluster', cluster_id}`); `EffectivePermissions` + `checkPermission()` resolution order; bootstrap exception; super-admin flag ≠ role.
  - §4 Roles and Personas — the route→guard matrix rows for the four screens + the `<Can>` in-page gates; note `/dashboard`, `/profile` are permissionless-authenticated.
  - §5 Migration from the legacy role model — table mapping old (`platform_role` enum, `allowedRoles` guards, `hasRole()`) to new (catalog/roles/assignments, `requiredPermission`, `hasPermission()`); cite removal commits `6091ffc`, `5f629f2`. This is the ONLY place legacy names should appear unqualified.
  - §6 Related Modules — Users (accounts live there, role assignment here), Applications (same key grammar for machine clients), Clusters (scope target), Business Units (reuse `cluster.*` keys — call out).
  - §7 Sub-pages — absolute links `/en/platform/rbac/data-model`, `/en/platform/rbac/ui-screens`, `/en/platform/rbac/permissions`.

- [ ] **Step 3: Write `en/platform/rbac/data-model.md`** per template §2.1: source-of-truth callout; §1 Overview; §2 Entities — full field tables for the 5 owned Prisma models; §3 Relationships (role M:N permission via `tb_platform_role_tb_permission`; user M:N role via `tb_user_tb_platform_role` with scope columns; super-admin 1:1-ish user flag table); §4 Enums (if any on these models); §5 Divergences vs SPA TS types (`Role`, `PermissionCatalogItem`, `UserRoleAssignment`, `Scope`, `EffectivePermissions` from `src/types/index.ts` — e.g. SPA receives `permission_count` aggregates, multi-layer `{data}` envelopes); §6 References. Include the rbac endpoint table from Common Context.

- [ ] **Step 4: Write `en/platform/rbac/ui-screens.md`** per template §2.2: §1 Overview (four screens, which follow the standard Management/Edit pattern and which deviate); §2 Roles list + edit (PermissionPicker accordion, permission-count badge, Created/Updated audit columns, CSV export, delta save); §3 Permission Catalog (read-only resource-grouped cards; reached from Roles header button — no sidebar item); §4 Super Admins (add/remove rows, user dropdown excludes existing super admins; not a DataTable); §5 User Platform list (Roles-count badge via background N+1 `userRoleService.list()` fetch; Name composed firstname/middlename/lastname) + detail (Roles & Scope card, add-role form with platform/cluster scope select, delete confirmation); §6 References.

- [ ] **Step 5: Write `en/platform/rbac/permissions.md`**: §1 Overview; §2 Gate matrix (the four screens' guards from Common Context); §3 How guards compose (route `requiredPermission` → sidebar `permission:`/`superAdminOnly:` filter → in-page `<Can>`); §4 Permission resolution walkthrough (pseudo-code block, no language tag, of `checkPermission` incl. clusterId branch); §5 Edge Cases table (bootstrap login, super-admin invisible to permission checks, `user_platform.read` users who can view but not manage, catalog requires backend redeploy to change); §6 Recommendations.

- [ ] **Step 6: Verify all 4 pages** with the per-page verification block (legacy-role grep must flag ONLY the rbac.md §5 migration table).

- [ ] **Step 7: Commit**

```bash
git add en/platform/rbac.md en/platform/rbac/
git commit -m "docs(platform/rbac): add RBAC module — landing + data-model + ui-screens + permissions (EN)"
```

## Task 2: EN `applications` module (4 pages)

**Files:**
- Create: `en/platform/applications.md`, `en/platform/applications/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Read sources** — `ApplicationManagement.tsx`, `ApplicationEdit.tsx`, `applicationService.ts`, `src/utils/apiCatalog.ts`, Prisma `tb_application` (75) + `tb_application_api` (98), carmen-platform `CLAUDE.md` grouped-catalog section.

- [ ] **Step 2: Write `en/platform/applications.md` (landing)** — clusters.md section shape. Key content: API client registry; record UUID is the `x-app-id` header value clients send on every request; access model `allow_all` vs explicit `api_names`; backend guards via `AppIdGuard('module.action')`; catalog generated by backend script scanning those guards. §4 uses `application.*` guard rows. §7 links the 3 sub-pages.

- [ ] **Step 3: Write `applications/data-model.md`** — Prisma callout; field tables for `tb_application`, `tb_application_api`; §5 Divergences vs SPA `Application` / `ApplicationWritePayload` / `ApiCatalogGroup` (write payload `details.add` only when `allow_all` false; PUT = full-set replace, not delta — contrast with rbac roles' delta semantics; `tb_application_role`-family models are schema-only if the SPA doesn't surface them — state what you find). Endpoint table from Common Context incl. `/api-catalog` fallback behavior.

- [ ] **Step 4: Write `applications/ui-screens.md`** — list page (App ID monospace truncated column, Access badge "All APIs"/"N APIs", status filter sheet, CSV export, Created/Updated audit columns, debug sheet); edit page (Name required, App ID read-only, Status + Allow-all checkboxes, grouped-by-module accordion selector: filter auto-expands matches, per-module All/None + selected/total badge, expand/collapse-all scoped to filtered groups, action-name buttons with full key in title attr; read-mode grouped Badge view; ChipInput fallback when catalog load fails).

- [ ] **Step 5: Write `applications/permissions.md`** — `application.read/create/update/delete` gates; sidebar Platform group gated on `application.read`; Edge Cases (catalog fetch failure → manual ChipInput; `allow_all` flips ignore the selected list; replace-semantics foot-gun when two admins edit concurrently); Recommendations.

- [ ] **Step 6: Verify + commit**

```bash
git add en/platform/applications.md en/platform/applications/
git commit -m "docs(platform/applications): add Applications module — landing + 3 sub-pages (EN)"
```

## Task 3: EN `print-template-mapping` module (4 pages)

**Files:**
- Create: `en/platform/print-template-mapping.md`, `en/platform/print-template-mapping/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Read sources** — `PrintTemplateMappingManagement.tsx`, `PrintTemplateMappingEdit.tsx`, `printTemplateMappingService.ts`, Prisma `tb_print_template_mapping` (776), `en/platform/report-templates.md` (positioning — do not restate).

- [ ] **Step 2: Write landing** — resolves which FastReport template prints for a document type (PR, PO, SR, GRN, …); fields: default flag (legacy Print button), display label/order (print-as menu), allow/deny BU lists; runtime `resolve(document_type, bu_code)`; relation to Report Templates (`kind='print'`, `report_group` matches document type). §4 uses `print_template_mapping.*` rows.

- [ ] **Step 3: Write `data-model.md`** — Prisma callout; `tb_print_template_mapping` field table; relationship to `tb_report_template` (denormalized `template_name`/`template_group` in API responses); §5 Divergences vs SPA type (`allow_business_unit`/`deny_business_unit` typed `unknown` — CSV string OR array tolerance); endpoint table incl. `/document-types` and `/resolve` semantics (allow-list AND NOT deny-list).

- [ ] **Step 4: Write `ui-screens.md`** — open §1 by flagging the **deliberate deviation** from the standard Management pattern: card layout grouped by document type, document-type select + active-only checkbox, no search/CSV/pagination/debug-sheet, groups sorted by code, rows by `display_order`. Edit page: single-mode form (no view/edit toggle), template dropdown filtered `kind='print'` + matching `report_group` with "N match / M total" badge, comma-separated allow/deny inputs, default + active checkboxes.

- [ ] **Step 5: Write `permissions.md`** — `print_template_mapping.*` gates; sidebar Content group. Edge Cases: one-default-per-document-type is a convention the UI does NOT enforce; BU in both allow and deny lists (deny wins at resolve); inactive mapping skipped by resolve. Recommendations (QA scenarios for resolve precedence).

- [ ] **Step 6: Verify + commit**

```bash
git add en/platform/print-template-mapping.md en/platform/print-template-mapping/
git commit -m "docs(platform/print-template-mapping): add module — landing + 3 sub-pages (EN)"
```

## Task 4: EN `news` module (4 pages)

**Files:**
- Create: `en/platform/news.md`, `en/platform/news/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Read sources** — `NewsManagement.tsx`, `NewsEdit.tsx`, `newsService.ts`, `ImageUpload.tsx`, Prisma `tb_news` (803) + `enum_news_status` (693).

- [ ] **Step 2: Write landing** — announcements for platform users; statuses draft → published → archived (`published_at` server-set on publish); global vs BU-targeted (`business_unit_ids` empty = global); markdown body; image attachment. §4 uses `news.*` rows.

- [ ] **Step 3: Write `data-model.md`** — Prisma callout; `tb_news` field table + `enum_news_status`; §5 Divergences vs SPA `News` type (`image_url` new vs `image` legacy fallback; nested `Audit` object `{created,updated,deleted}` each `{at,id,name,avatar}`; soft-delete surfaced via `deleted_at` OR `audit.deleted.at` — list filters both). Endpoint table — emphasize `/api` (not `/api-system`) and multipart create/update (inline `image` file, JSON-encoded `business_unit_ids` string field).

- [ ] **Step 4: Write `ui-screens.md`** — list (image thumbnail preserving aspect ratio, Title link, status badges with colors, Target column "Global" badge or "N BUs", Published + Updated columns with actor names, status filter sheet, CSV export); edit (Content card: title required, MarkdownEditor write/preview tabs, source URL validation, ImageUpload drag-drop preview; Publishing card: status select, read-only published_at; Targeting card: global checkbox, BU multi-select required when not global; Metadata card from nested audit; unsaved-changes guard; Ctrl/Cmd+S, Escape).

- [ ] **Step 5: Write `permissions.md`** — `news.read/create/update` gates (no separate delete key — verify in `App.tsx`/page actions and document what delete actually requires); targeting validation rule; Edge Cases (soft-deleted rows hidden, legacy `image` field, archived ≠ deleted); Recommendations.

- [ ] **Step 6: Verify + commit**

```bash
git add en/platform/news.md en/platform/news/
git commit -m "docs(platform/news): add News module — landing + 3 sub-pages (EN)"
```

## Task 5: EN `broadcasts` module (4 pages)

**Files:**
- Create: `en/platform/broadcasts.md`, `en/platform/broadcasts/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Read sources** — `BroadcastCompose.tsx`, `broadcastService.ts`, `UserMultiSelect.tsx`, Prisma `tb_broadcast_notification` (357), `tb_user_broadcast_action` (388).

- [ ] **Step 2: Write landing** — push-notification compose; the only Platform module that is a single compose screen (`/broadcasts/new` — no list/edit routes in the SPA); three target modes (`system_all`, `system_users`, `bu`); immediate vs scheduled. §4 single row: `broadcast.send`.

- [ ] **Step 3: Write `data-model.md`** — Prisma callout; `tb_broadcast_notification` + `tb_user_broadcast_action` field tables (delivery/read tracking lives in schema even though the SPA is fire-and-forget); §5 Divergences vs SPA payload types (`BroadcastSystemPayload` with optional `userIds`, `BroadcastBuPayload` with `bu_code` — code not ID; type resolution `SYS_<PRESET>`/`BU_<PRESET>`, custom type regex `[A-Z0-9_]+` max 50). Endpoint table — `/api/notifications/broadcasts/system|bu`.

- [ ] **Step 4: Write `ui-screens.md`** — compose form walkthrough: target tabs (gates: system tabs need `broadcast.send`… verify whether BU tab differs in `BroadcastCompose.tsx`), UserMultiSelect, BU select ("Name (CODE)", active only), title 200-char + message 2000-char live counters, type preset select + custom input, send-now vs schedule tabs (future datetime validation), confirmation dialog variants (destructive styling for ALL-users; labels Send vs Schedule), reset, keyboard shortcuts, dev debug sheet.

- [ ] **Step 5: Write `permissions.md`** — single `broadcast.send` gate everywhere (route, sidebar "Send Broadcast" in Content group, send button); Edge Cases (scheduled time must be future; no list UI to cancel a scheduled broadcast — note where that lives if anywhere, else state it doesn't); Recommendations (QA matrix per target mode × timing).

- [ ] **Step 6: Verify + commit**

```bash
git add en/platform/broadcasts.md en/platform/broadcasts/
git commit -m "docs(platform/broadcasts): add Broadcasts module — landing + 3 sub-pages (EN)"
```

## Task 6: EN clusters updates

**Files:**
- Modify: `en/platform/clusters.md`, `en/platform/clusters/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Re-read current pages + delta sources** — `ClusterManagement.tsx`, `ClusterEdit.tsx`, `BrandingImageUpload.tsx` (rect logo + square avatar), nested-audit commits (`065f87c`, `30b5bd6`), branding commits (`5d0bf11`, `4a3547e`).

- [ ] **Step 2: Update `clusters.md`** — intro + At-a-Glance: replace "gated to the three admin-tier roles" with `cluster.*` permission gating; §4 Roles and Personas: replace the `allowedRoles` table with a `requiredPermission` matrix (`cluster.read/create/update` per route) + link to `/en/platform/rbac`; §3 Key Concepts: add branding (logo + avatar objects, `logo?.url`/`avatar?.url`); mention Created/Updated/Deleted audit columns.

- [ ] **Step 3: Update `clusters/ui-screens.md`** — list: add logo thumbnail column, Created/Updated columns (timestamp + actor from nested `audit` object, Updated omitted when equal to created); edit: add BrandingImageUpload section (rect logo, square avatar, replace flow).

- [ ] **Step 4: Update `clusters/data-model.md`** — add/adjust branding fields (embedded logo/avatar objects in API responses) and nested audit shape in the divergences section; refresh the "as of" date.

- [ ] **Step 5: Update `clusters/permissions.md`** — rewrite from role-gating to `cluster.*` permission gating; note BU routes reuse these same keys; cross-link `/en/platform/rbac/permissions`.

- [ ] **Step 6: Bump `date` frontmatter on all 4 files, verify, commit**

```bash
git add en/platform/clusters.md en/platform/clusters/
git commit -m "docs(platform/clusters): RBAC permission model + branding + audit columns (EN)"
```

## Task 7: EN business-units updates

**Files:**
- Modify: `en/platform/business-units.md`, `en/platform/business-units/{data-model,ui-screens}.md`

- [ ] **Step 1: Read delta sources** — `BusinessUnitManagement.tsx`, `BusinessUnitEdit.tsx`, branding/audit commits (`4a991c5`, `72d1fba`, `5c7efa5`).

- [ ] **Step 2: Update `business-units.md`** — §4: `requiredPermission` matrix; **explicitly call out that BU routes are gated on `cluster.*` keys, not `business_unit.*`** + link to rbac; add branding + audit-column mentions in key concepts.

- [ ] **Step 3: Update `business-units/ui-screens.md`** — logo thumbnail column, Created/Updated audit columns, BrandingImageUpload on edit page.

- [ ] **Step 4: Update `business-units/data-model.md`** — branding fields + nested audit divergence note; refresh "as of" date.

- [ ] **Step 5: Bump `date`, verify, commit**

```bash
git add en/platform/business-units.md en/platform/business-units/
git commit -m "docs(platform/business-units): cluster.* permission gating + branding + audit columns (EN)"
```

## Task 8: EN users updates

**Files:**
- Modify: `en/platform/users.md`, `en/platform/users/{data-model,lifecycle,ui-screens}.md`

- [ ] **Step 1: Read delta sources** — `UserManagement.tsx` (avatar column ~line 285-320, `getNameDisplay`), `UserEdit.tsx` (avatar header), commits `d7e7f20`, `137922d`, `68a772c`, `f9b61cb`, plus `6091ffc` (platform_role removal).

- [ ] **Step 2: Update `users.md`** — §4: `user.*` permission matrix + rbac link; remove/replace any `platform_role` discussion → "platform access is granted via RBAC role assignments, see `/en/platform/rbac`"; key concepts: avatar (initials fallback / presigned `avatar_url`), name composition firstname/middlename/lastname.

- [ ] **Step 3: Update `users/data-model.md`** — `platform_role` no longer read by the SPA (note removal commit); nested audit divergence; avatar fields.

- [ ] **Step 4: Update `users/lifecycle.md`** — login flow now validates effective permissions (`GET /api/user/permission/platform`) with bootstrap exception instead of role allowlist; cross-link rbac landing §3.

- [ ] **Step 5: Update `users/ui-screens.md`** — avatar column (leftmost, initials fallback), name composition, Created/Updated audit columns, Deleted badge with `deleted_by_name`, avatar in edit header.

- [ ] **Step 6: Bump `date`, verify, commit**

```bash
git add en/platform/users.md en/platform/users/
git commit -m "docs(platform/users): RBAC gating, avatar column, name composition, audit columns (EN)"
```

## Task 9: EN report-templates + profile updates

**Files:**
- Modify: `en/platform/report-templates.md`, `en/platform/report-templates/permissions.md`, `en/platform/profile.md`

- [ ] **Step 1: Update `report-templates.md`** — §4/§5: `report_template.*` permission matrix replacing role table + rbac link; Related Modules: add Print Template Mapping (`kind='print'` templates are selected per document type there; link `/en/platform/print-template-mapping`).

- [ ] **Step 2: Update `report-templates/permissions.md`** — same permission-model rewrite.

- [ ] **Step 3: Update `profile.md`** — saves via `PATCH` (commit `9dc27ee`); `platform_role` no longer displayed (commit `6091ffc`); route is authenticated-only (no permission key). Check for `auth-roles` links — leave for Task 10's sweep but fix any inline prose claims about roles now.

- [ ] **Step 3b: `changelog.md` — no edit needed.** Verified 2026-06-10: the page (dateCreated 2026-06-09) already documents v0.1.0, the JSON source, the version badge surfaces, and `build:bump`. Skip unless a newer version exists in `src/data/changelog.json` at execution time — check, and only touch the page if `versions[0].version` ≠ `0.1.0`.

- [ ] **Step 4: Bump `date` on all 3, verify, commit**

```bash
git add en/platform/report-templates.md en/platform/report-templates/permissions.md en/platform/profile.md
git commit -m "docs(platform): report-templates + profile aligned to RBAC and current API verbs (EN)"
```

## Task 10: EN book landing, link rewrite, auth-roles deletion

**Files:**
- Modify: `en/platform.md`, every EN file matching `grep -rl 'auth-roles' en/ README.md`
- Delete: `en/platform/auth-roles.md`

- [ ] **Step 1: Rewrite `en/platform.md` module tables** into six sections: 1 Tenancy (Clusters, Business Units) · 2 Identity & Access (Users, **Platform RBAC** → `/en/platform/rbac`, Profile) · 3 Content (News, Broadcasts) · 4 Platform (Applications) · 5 Reporting (Report Templates, Print Template Mapping) · 6 Product (Changelog). One-line "What it covers" per module, matching the existing table shape.

- [ ] **Step 2: Rewrite every `/en/platform/auth-roles` link** in `en/` and `README.md` to `/en/platform/rbac` with display text "Platform RBAC" (adjust sentence grammar where "Authentication & Roles" was prose). Find them:

```bash
grep -rn 'auth-roles' en/ README.md
```

- [ ] **Step 3: Delete the page**

```bash
git rm en/platform/auth-roles.md
```

- [ ] **Step 4: Verify zero EN references remain**

```bash
grep -rn 'auth-roles' en/ README.md && echo "FAIL" || echo "OK"
```

- [ ] **Step 5: Bump `date` on touched pages, verify frontmatter, commit**

```bash
git add -A en/ README.md
git commit -m "docs(platform): restructure book landing, replace auth-roles with rbac (EN)"
```

## Task 11: TH `rbac` module (4 pages)

**Files:**
- Create: `th/platform/rbac.md`, `th/platform/rbac/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Read the finished EN rbac pages** (Task 1 output) and one existing TH page (`th/platform/clusters.md`) for register/terminology.

- [ ] **Step 2: Translate all 4 pages** following the TH conventions in Common Context (Thai prose; permission keys/components/routes in English; links `/th/platform/...`; H1 e.g. `# RBAC ของแพลตฟอร์ม (Platform RBAC)` — match how existing TH pages compose names; frontmatter `date`/`dateCreated` = `2026-06-10T13:00:00.000Z`).

- [ ] **Step 3: Verify (TH cross-locale grep variant) + commit**

```bash
git add th/platform/rbac.md th/platform/rbac/
git commit -m "docs(platform/rbac): Thai translation — landing + 3 sub-pages"
```

## Task 12: TH `applications` module (4 pages)

**Files:**
- Create: `th/platform/applications.md`, `th/platform/applications/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Translate the 4 finished EN applications pages** per TH conventions.
- [ ] **Step 2: Verify + commit**

```bash
git add th/platform/applications.md th/platform/applications/
git commit -m "docs(platform/applications): Thai translation — landing + 3 sub-pages"
```

## Task 13: TH `print-template-mapping` module (4 pages)

**Files:**
- Create: `th/platform/print-template-mapping.md`, `th/platform/print-template-mapping/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Translate the 4 finished EN pages** per TH conventions.
- [ ] **Step 2: Verify + commit**

```bash
git add th/platform/print-template-mapping.md th/platform/print-template-mapping/
git commit -m "docs(platform/print-template-mapping): Thai translation — landing + 3 sub-pages"
```

## Task 14: TH `news` module (4 pages)

**Files:**
- Create: `th/platform/news.md`, `th/platform/news/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Translate the 4 finished EN pages** per TH conventions.
- [ ] **Step 2: Verify + commit**

```bash
git add th/platform/news.md th/platform/news/
git commit -m "docs(platform/news): Thai translation — landing + 3 sub-pages"
```

## Task 15: TH `broadcasts` module (4 pages)

**Files:**
- Create: `th/platform/broadcasts.md`, `th/platform/broadcasts/{data-model,ui-screens,permissions}.md`

- [ ] **Step 1: Translate the 4 finished EN pages** per TH conventions.
- [ ] **Step 2: Verify + commit**

```bash
git add th/platform/broadcasts.md th/platform/broadcasts/
git commit -m "docs(platform/broadcasts): Thai translation — landing + 3 sub-pages"
```

## Task 16: TH existing-page updates

**Files:**
- Modify: `th/platform/clusters.md` + `th/platform/clusters/{data-model,ui-screens,permissions}.md`, `th/platform/business-units.md` + `th/platform/business-units/{data-model,ui-screens}.md`, `th/platform/users.md` + `th/platform/users/{data-model,lifecycle,ui-screens}.md`, `th/platform/report-templates.md`, `th/platform/profile.md`

- [ ] **Step 1: For each file, diff its EN counterpart's Task 6–9 changes** (`git log -p en/platform/clusters.md` etc.) and apply the same edits in Thai: permission matrices replacing role tables, branding/audit additions, platform_role removal, PATCH note, print-template-mapping cross-link (TH link targets `/th/platform/...`).

- [ ] **Step 2: Bump `date` (TH timestamp), verify each file, commit**

```bash
git add th/platform/
git commit -m "docs(platform): mirror RBAC/branding/audit updates to Thai pages"
```

## Task 17: TH report-templates parity backfill (2 pages)

**Files:**
- Create: `th/platform/report-templates/data-model.md`, `th/platform/report-templates/permissions.md`

- [ ] **Step 1: Translate from the (Task 9-updated) EN counterparts** per TH conventions. `dateCreated` = TH new-page timestamp (these are new TH files even though EN originals are older).

- [ ] **Step 2: Check `th/platform/report-templates.md` §7 sub-page list** — it must now link all 4 sub-pages (the EN landing lists 4; mirror in Thai).

- [ ] **Step 3: Verify + commit**

```bash
git add th/platform/report-templates/
git commit -m "docs(platform/report-templates): backfill Thai data-model + permissions sub-pages"
```

## Task 18: TH book landing, link rewrite, auth-roles deletion

**Files:**
- Modify: `th/platform.md`, every TH file matching `grep -rl 'auth-roles' th/`
- Delete: `th/platform/auth-roles.md`

- [ ] **Step 1: Mirror the Task 10 `en/platform.md` six-section layout** in `th/platform.md` (links `/th/platform/...`).

- [ ] **Step 2: Rewrite `/th/platform/auth-roles` links** → `/th/platform/rbac`, then delete:

```bash
grep -rn 'auth-roles' th/
git rm th/platform/auth-roles.md
grep -rn 'auth-roles' th/ && echo "FAIL" || echo "OK"
```

- [ ] **Step 3: Bump `date`, verify, commit**

```bash
git add -A th/
git commit -m "docs(platform): restructure book landing, replace auth-roles with rbac (TH)"
```

## Task 19: Nav rebuild

**Files:**
- Modify: `scripts/nav-overrides.yaml` (platform block, lines ~87–117)

- [ ] **Step 1: Replace the platform `groups:` block** with:

```yaml
  platform:
    label_en: "Carmen Platform"
    label_th: "Carmen Platform"
    groups:
      - label_en: "Tenancy"
        label_th: "Tenancy"
        modules:
          - slug: clusters
            label_en: "Clusters"
            label_th: "Clusters"
          - slug: business-units
            label_en: "Business Units"
            label_th: "Business Units"
      - label_en: "Identity & Access"
        label_th: "Identity & Access"
        modules:
          - slug: users
            label_en: "Users"
            label_th: "Users"
          - slug: rbac
            label_en: "Platform RBAC"
            label_th: "Platform RBAC"
          - slug: profile
            label_en: "Profile"
            label_th: "Profile"
      - label_en: "Content"
        label_th: "Content"
        modules:
          - slug: news
            label_en: "News"
            label_th: "News"
          - slug: broadcasts
            label_en: "Broadcasts"
            label_th: "Broadcasts"
      - label_en: "Platform"
        label_th: "Platform"
        modules:
          - slug: applications
            label_en: "Applications"
            label_th: "Applications"
      - label_en: "Reporting"
        label_th: "Reporting"
        modules:
          - slug: report-templates
            label_en: "Report Templates"
            label_th: "Report Templates"
          - slug: print-template-mapping
            label_en: "Print Template Mapping"
            label_th: "Print Template Mapping"
      - label_en: "Product"
        label_th: "Product"
        modules:
          - slug: changelog
            label_en: "Changelog"
            label_th: "Changelog"
```

- [ ] **Step 2: Rebuild nav** (requires the dev Wiki.js instance reachable and credentials per `scripts/README.md` — read it first; if the instance is unreachable, commit the YAML and flag the rebuild as pending for the user):

```bash
python3 scripts/sync_nav.py --mode=build
```

- [ ] **Step 3: Commit**

```bash
git add scripts/nav-overrides.yaml
git commit -m "nav(platform): add rbac/news/broadcasts/applications/print-template-mapping/changelog groups"
```

## Task 20: Final verification sweep

- [ ] **Step 1: Frontmatter over every touched page**

```bash
git diff --name-only HEAD~19 -- 'en/**/*.md' 'th/**/*.md' en/platform.md th/platform.md | xargs -I{} python3 .specs/verify_frontmatter.py {}
```

(Adjust `HEAD~19` to the actual first commit of this plan; or simply run the verifier over `en/platform/` and `th/platform/` wholesale.)

- [ ] **Step 2: Link + legacy sweeps**

```bash
grep -rn 'auth-roles' en/ th/ README.md && echo FAIL || echo OK            # zero outside .specs/docs history
grep -rn 'allowedRoles' en/platform/ th/platform/ && echo CHECK || echo OK # only rbac migration tables may mention legacy names
grep -rnE '\(/en/' th/platform/ && echo FAIL || echo OK                    # no cross-locale links
grep -rnE '\(/th/' en/platform/ && echo FAIL || echo OK
```

- [ ] **Step 3: Page-count sanity** — `find en/platform th/platform -name '*.md' | wc -l` must print **76**. Derivation: EN before = 19 files, − 1 (auth-roles deleted) + 20 (new module pages) = 38; TH before = 17 files, − 1 + 20 + 2 (report-templates backfill) = 38. The book-opener pages `en/platform.md` / `th/platform.md` sit outside these folders and are not in this count.

- [ ] **Step 4: Optional rendering spot-check** — if the dev wiki at `http://dev.blueledgers.com:3987/` is reachable and pages have been pushed (`scripts/push_pages.py` — separate operation, ask the user), open `/en/platform/rbac` and `/en/platform/applications` and check tables + At-a-Glance render.

- [ ] **Step 5: Update `.specs/process-coverage-checklist.md`?** — that checklist tracks the **Inventory** book only; platform pages are out of its scope. Do not edit it. (Listed here so an executor doesn't "helpfully" add platform rows.)

- [ ] **Step 6: Final commit if any verification fixes were needed**

```bash
git add -A
git commit -m "docs(platform): verification sweep fixes"
```
