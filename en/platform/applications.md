---
title: Applications
description: Application module overview — registered API clients of the platform, their x-app-id identity, and allow-all vs explicit api_name access grants.
published: true
date: 2026-06-10T12:30:00.000Z
tags: platform/applications, carmen-software
editor: markdown
dateCreated: 2026-06-10T12:30:00.000Z
---

# Applications

The **Applications** module manages the platform's registered **API clients** — the machine callers of the backend gateway. An application record is an identity plus an access grant: its record UUID is the `x-app-id` header value the client sends on every request, and its grant is either "allow all APIs" or an explicit list of `api_name` keys picked from a backend-generated catalog. Where [Platform RBAC](/en/platform/rbac) answers "what may this *person* do," Applications answers "what may this *program* call."

> **At a Glance**
> **Module purpose:** Register machine clients and grant them API access — `allow_all` or an explicit `api_names` list selected from a catalog grouped by module &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA and the backend gateway's `AppIdGuard` enforcement &nbsp;·&nbsp; **Key entities/tables:** `tb_application` (the client: `name`, `is_active`, `allow_all`), `tb_application_api` (1:N grant rows, one `api_name` each) &nbsp;·&nbsp; **Identity:** record `id` (UUID) **is** the `x-app-id` value — there is no separate app-id field &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The module follows the SPA's standard two-screen pattern:

- **`/applications` → `ApplicationManagement`** — server-side `DataTable` with debounced search (name/description), a Sheet-based Active/Inactive filter, CSV export, and persisted UI state in `localStorage`. The **App ID** column renders the record UUID in monospace so operators can copy the exact `x-app-id` value, and the **Access** column summarizes the grant as an "All APIs" or "N APIs" badge.
- **`/applications/new` and `/applications/:id/edit` → `ApplicationEdit`** — a single "Application Details" card (create mode is immediately editable; the edit route starts read-only behind an Edit toggle). Its signature element is the **API Names selector**: a collapsible accordion of `api_name` keys grouped by module, with a filter box, per-module select-all, and selected-count badges. The selector renders only when `allow_all` is off.

The selector's options come from `GET /api-system/applications/api-catalog`. The SPA cannot add or edit catalog entries — the catalog is generated on the backend (§2) and the SPA only selects from it. See [UI Screens](/en/platform/applications/ui-screens) for the full walkthrough.

Everything else is the SPA's standard Management-page furniture: `TableSkeleton` on first load, `EmptyState` when the list is empty, toast feedback on mutations, the `useUnsavedChanges` navigation guard while editing, and the dev-only Debug Sheet exposing each screen's raw API response.

## 2. Business Context

Two kinds of callers hit the Carmen Platform backend: **human users**, whose sessions carry a bearer token and resolve through the RBAC permission snapshot, and **machine clients** — sibling services, integrations, and the SPAs themselves — which identify with an `x-app-id` header. Every request the Platform admin SPA makes carries both: `Authorization: Bearer <token>` for the user and `x-app-id` for the application (`src/services/api.ts` reads it from the `REACT_APP_API_APP_ID` build env var), meaning the SPA is itself a registered application record. A request can therefore fail on either axis independently — wrong user, or wrong/ungranted app id.

On the backend, guarded endpoints are wrapped in `AppIdGuard('module.action')` (backend-gateway). The guard resolves the incoming `x-app-id` to a `tb_application` row and passes when the application has `allow_all = true` or holds a live `tb_application_api` row whose `api_name` matches the guard's key.

The selectable catalog is **derived from those guards, not hand-maintained**: `scripts/generate-app-api-catalog/run.ts` in `carmen-turborepo-backend-v2` scans the gateway source for `new AppIdGuard('...')` calls and emits `app-api-catalog.generated.ts` (a flat sorted list plus module groups). A new guarded endpoint appears in the SPA's selector after regeneration and a backend deploy — no database seed is involved, which is the key operational difference from the RBAC permission catalog (a Postgres table seeded by migration).

## 3. Key Concepts

- **App ID = record UUID.** The `tb_application.id` primary key is the `x-app-id` value. There is no separate `app_id` column or field anywhere — the SPA simply surfaces `id` under the label "App ID" (read-only, server-generated).
- **`allow_all` vs explicit list.** A boolean fork: `allow_all = true` grants every guarded endpoint and makes any `tb_application_api` rows irrelevant; `allow_all = false` grants exactly the live `api_name` rows. The SPA hides the API Names selector entirely while `allow_all` is checked, and the write payload omits the names in that case.
- **`api_name` grammar.** Keys are `resource.action` strings — the same shape as RBAC permission keys, but a **separate vocabulary from a separate source**: `api_name`s come from the `AppIdGuard` scan, RBAC keys from `tb_platform_permission`. The action segments follow the backend controller methods, not the RBAC verb set — `cluster.findAll`, `cluster.findOne`, `cluster.uploadLogo` rather than `cluster.read` — so the two catalogs share grammar but not key strings. The generated catalog holds 777 keys across 125 module groups as of 2026-06-10. The module of an `api_name` is the prefix before the first `.`; a dotless name is its own module (`src/utils/apiCatalog.ts` mirrors the backend generator's split rule exactly).
- **Replace, not delta.** `PUT /api-system/applications/:id` sends the **full desired set** as `details: { add: [{ api_name }] }` — replace semantics. This is the opposite of RBAC role writes, which send `{ add, remove }` deltas; a developer porting code between the two modules must not assume one convention.
- **Standard platform hygiene.** `tb_application` carries `is_active`, the audit trio, and a soft-delete-aware unique name (`@@unique([name, deleted_at])`), so a deleted application's name can be reused.

## 4. Roles and Personas

Access to the module is permission-gated through [Platform RBAC](/en/platform/rbac), with both route guards and in-page `<Can>` gates:

| Surface | Gate | Key |
|---|---|---|
| `/applications` route + "Applications" sidebar entry (Platform group) | `PrivateRoute` / sidebar filter | `application.read` |
| `/applications/new` route | `PrivateRoute` | `application.create` |
| `/applications/:id/edit` route | `PrivateRoute` | `application.update` |
| Add Application button (list header) | `<Can>` | `application.create` |
| Row Edit (list actions dropdown) | `<Can>` | `application.update` |
| Row Delete (list actions dropdown) | `<Can>` | `application.delete` |
| Edit toggle (edit page header) | `<Can>` | `application.update` |

Note that `application.delete` exists **only as an in-page gate** — no route requires it, and the edit page offers no delete action at all; deletion happens exclusively from the list row dropdown. The full matrix, including a known ungated empty-state CTA, is in [Permissions](/en/platform/applications/permissions).

## 5. Related Modules

- [Platform RBAC](/en/platform/rbac) — the human-access counterpart. Same `resource.action` key grammar, different catalog and enforcement path: RBAC keys live in `tb_platform_permission` and gate user sessions; `api_name`s come from the `AppIdGuard` scan and gate `x-app-id` callers. The `application.*` keys that gate *this module's screens* are themselves RBAC keys — a human needs RBAC grants to manage machine grants.
- [users](/en/platform/users) — applications have no user binding; the only `tb_user` references on the application tables are the audit actor columns. The schema-only `tb_application_role` family (which does join users) is unrelated to this module — see the [Data Model](/en/platform/applications/data-model) divergences section.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — the three `application.*` route guards.
- `../carmen-platform/src/components/Layout.tsx` — the "Applications" sidebar entry (Platform group, `application.read`).
- `../carmen-platform/src/pages/ApplicationManagement.tsx` — list page: columns, filters, CSV export, `<Can>` gates.
- `../carmen-platform/src/pages/ApplicationEdit.tsx` — create/view/edit form and the API Names selector.
- `../carmen-platform/src/services/applicationService.ts` — REST client and the read/write translation (`details.add`, catalog fallback).
- `../carmen-platform/src/utils/apiCatalog.ts` + `src/types/index.ts` — grouping helpers and the `Application` / `ApplicationWritePayload` / `ApiCatalogGroup` types.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application` (line 75), `tb_application_api` (line 98).
- `../carmen-turborepo-backend-v2/scripts/generate-app-api-catalog/run.ts` — the catalog generator.

## 7. Pages in This Module

- [Data Model](/en/platform/applications/data-model) — `tb_application` and `tb_application_api` field tables, the asymmetric read/write shapes, replace semantics, the catalog endpoint, and the schema-only `tb_application_role` family.
- [UI Screens](/en/platform/applications/ui-screens) — the `ApplicationManagement` list and the `ApplicationEdit` form, including the grouped-accordion API Names selector and its ChipInput fallback.
- [Permissions](/en/platform/applications/permissions) — the gate matrix, how application access differs from user RBAC, and edge cases for testers.
