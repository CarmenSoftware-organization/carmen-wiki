---
title: Applications — Permissions
description: The application.* gate matrix, how machine-client access (x-app-id + api_names) differs from user RBAC, and edge cases for testers.
published: true
date: 2026-06-10T12:30:00.000Z
tags: book/platform, applications, permissions
editor: markdown
dateCreated: 2026-06-10T12:30:00.000Z
---

# Applications — Permissions

> **At a Glance**
> **Gate:** routes carry `application.read` / `application.create` / `application.update` on `PrivateRoute`; sidebar entry on `application.read` &nbsp;·&nbsp; **In-page `<Can>` gates:** Add (`application.create`), row Edit (`application.update`), row Delete (`application.delete` — in-page only, no route), Edit toggle (`application.update`) &nbsp;·&nbsp; **Two access systems meet here:** RBAC keys gate *who may manage* applications; `api_name` grants decide *what the application may call* &nbsp;·&nbsp; **Known gap:** the empty-state "Add Application" CTA is not `<Can>`-wrapped

## 1. Overview

This page covers two distinct authorization stories that intersect on these screens. The first is ordinary [Platform RBAC](/en/platform/rbac): the `application.*` permission keys that decide which *humans* can see and mutate application records (§2). The second is what the records themselves encode: the **machine-client grant** — which `api_name`-guarded endpoints a caller presenting this application's `x-app-id` may invoke (§3). Testers need both lenses: a human with full `application.*` keys can grant an application powers the human does not hold, because the two vocabularies are independent.

## 2. Gate matrix

All gates resolve through the single `hasPermission` resolver documented in [Platform RBAC — Permissions](../rbac/permissions.md); a failed route guard renders `<AccessDenied>` inside the normal `<Layout>` shell.

| Surface | Mechanism | Key | Source |
|---|---|---|---|
| `/applications` | `PrivateRoute requiredPermission` | `application.read` | `src/App.tsx` |
| `/applications/new` | `PrivateRoute requiredPermission` | `application.create` | `src/App.tsx` |
| `/applications/:id/edit` | `PrivateRoute requiredPermission` | `application.update` | `src/App.tsx` |
| Sidebar "Applications" (Platform group) | `Layout.tsx` nav filter | `application.read` | `src/components/Layout.tsx` |
| Add Application (list header) | `<Can>` | `application.create` | `ApplicationManagement.tsx` |
| Row Edit (actions dropdown) | `<Can>` | `application.update` | `ApplicationManagement.tsx` |
| Row Delete (actions dropdown) | `<Can>` | `application.delete` | `ApplicationManagement.tsx` |
| Edit toggle (edit-page header) | `<Can>` | `application.update` | `ApplicationEdit.tsx` |

Three asymmetries worth a tester's attention:

- **`application.delete` is in-page only.** No route requires it and the edit page has no delete action — the key's entire surface is the list row's Delete item. A session holding only `application.read` sees the list but neither Edit nor Delete in the dropdown.
- **Save is not separately gated.** On the edit page only the Edit *toggle* is `<Can>`-wrapped; the Save button is plain but unreachable without entering edit mode (and the create route's Save sits behind the route's `application.create`). Client-side this is sound; backend enforcement on `PUT` remains the real boundary.
- **The empty-state CTA is ungated.** When the list is empty with no search term, the `EmptyState` card's "Add Application" button is **not** wrapped in `<Can permission="application.create">` (unlike the header button). A read-only session can click it and lands on `<AccessDenied>` at `/applications/new` — the route guard catches it, but the affordance leaks. Treat the button's visibility, not its outcome, as the defect if this surfaces in QA.

Export (CSV) and the dev-only Debug Sheet are intentionally ungated beyond the route's `application.read` — both are read-only over already-loaded data. As everywhere in the SPA, the sidebar filter is UX, not security: a session lacking `application.read` does not see the entry but can still type `/applications` into the address bar and will hit the route guard.

The three route keys are independent — `PrivateRoute` checks only the one key its route declares. Useful combinations to test deliberately: `application.update` without `application.read` can deep-link straight to `/applications/:id/edit` (given an id from elsewhere) while the list itself renders `<AccessDenied>`; `application.create` without `application.read` can reach `/applications/new` by URL even though both paths into it (header button, empty-state CTA) live on a page it cannot open.

## 3. How application access differs from user RBAC

The `resource.action` grammar is shared; almost everything else differs:

| Aspect | User RBAC | Application grants |
|---|---|---|
| Caller identifies by | `Authorization: Bearer <token>` (session) | `x-app-id: <tb_application.id>` header |
| Key vocabulary | `tb_platform_permission` rows (Postgres, seeded by backend migration); verb set `read`/`create`/`update`/… | `api_name`s harvested from `new AppIdGuard('...')` calls by `scripts/generate-app-api-catalog/run.ts` (generated file, no table); verbs follow controller methods (`findAll`, `findOne`, `uploadLogo`) — same grammar, different strings |
| Grant storage | role→permission join rows plus scoped user→role assignment rows (five tables — see [Platform RBAC data-model](../rbac/data-model.md)) | flat `tb_application_api` rows per application (no roles, no scopes) |
| Wildcard | super-admin flag (`tb_platform_super_admin`) per user | `allow_all` boolean per application |
| Scope dimension | platform-wide or per-cluster (`cluster_id` on the assignment) | none — a grant applies wherever the endpoint does |
| Write semantics (SPA) | role permissions sent as deltas `{ add, remove }` | full-set replace via `details.add[]` on every `PUT` |
| Enforcement point | SPA gates (advisory) + backend session checks | backend `AppIdGuard` per endpoint; the SPA never evaluates `api_name`s |
| Adding a key | backend seed/migration + redeploy | add a guard in backend-gateway, regenerate the catalog, redeploy |

Both headers travel together on every Platform SPA request — the SPA authenticates its user with the bearer token *and* identifies itself as a registered application via `x-app-id` from its build environment. A request can therefore fail on either axis independently: a valid user through an unknown/ungranted app id, or a fully-granted app id carrying an unauthorized user.

## 4. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | `allow_all = true` with `api_names` previously selected | The selector disappears; the write payload **omits `details` entirely**, and the backend grants every API regardless of stored grant rows | The list badge flips to "All APIs". Toggling `allow_all` back off within the same edit session restores the in-memory selection — verify what actually persists after each save, not what the form shows |
| 2 | Concurrent edits + replace semantics | Two operators editing the same application both send their *full* desired set; last save wins and silently discards the other's additions/removals | The replace-not-delta foot-gun. Unlike RBAC role deltas, there is no merge — reproduce with two sessions and verify the audit columns identify the surviving writer |
| 3 | Catalog fetch fails | The selector degrades to free-text `ChipInput`; any string can be entered as an `api_name` | Typos persist as dead grant rows — `tb_application_api.api_name` has no FK or enum to validate against. Check trailing-space handling (the service trims) and that bogus names simply never match a guard |
| 4 | Catalog response without `groups` (older backend) | The client derives identical groups via `groupApiNames()` — same prefix-before-first-dot rule as the generator | Deploy-order tolerance, not a bug; grouped UI must look the same either way |
| 5 | Application `is_active = false` | The SPA renders an Inactive badge and keeps the record fully editable; nothing in the SPA blocks the application's callers | Whether an inactive application's `x-app-id` is rejected is backend (`AppIdGuard`) behaviour — verify it server-side; do not infer enforcement from the badge |
| 6 | Session with `application.read` only | List loads; the actions dropdown is empty (no Edit/Delete), header Add is hidden — but the empty-state CTA still shows on an empty list and dead-ends at `<AccessDenied>` | The §2 gate gap; the canonical `<Can>` absence check otherwise |
| 7 | Deleting an application that clients still use | The confirm dialog warns it cannot be undone; once deleted, callers presenting that UUID should be rejected by the guard | Soft delete (`deleted_at`) — confirm the guard excludes soft-deleted rows and that the freed `name` can be reused (`@@unique` includes `deleted_at`) |
| 8 | Guard added in backend but catalog not regenerated | The endpoint enforces a key that no selector offers; explicit-list applications cannot be granted it through the UI | Regeneration + deploy is part of shipping a new `AppIdGuard`; until then only `allow_all` applications pass |
| 9 | Key held without its `read` sibling | `application.update` alone opens `/applications/:id/edit` by deep link; `application.create` alone opens `/applications/new` by URL — both while the list route denies | Route guards check one key each (§2); decide per test plan whether such partial grants are intended role shapes or misconfigurations |
| 10 | Super-admin or bootstrap session | All `application.*` gates pass regardless of grants — the [RBAC resolver](../rbac/permissions.md) short-circuits before any key check | Never QA this module's gate matrix from a super-admin session; it cannot reveal a missing key |

## 5. Recommendations

- **Test the two axes separately.** Verify human gating with sessions holding exactly one `application.*` key at a time, and machine gating with a scratch application toggled between `allow_all`, an explicit list, and no grants — never conflate a passing SPA action with a passing `x-app-id` call.
- **Treat replace semantics as the default hazard.** Any workflow or script that updates an application must read-modify-write the full `api_names` set; partial "just add one key" PUTs will wipe the rest. Flag any new client code that ports the RBAC delta shape here.
- **Audit explicit lists after catalog changes.** Renaming or removing an `AppIdGuard` key strands existing grant rows (no FK cleans them up); periodically diff `tb_application_api.api_name` values against the generated catalog.
- **Prefer explicit lists over `allow_all` outside dev.** `allow_all` is the machine equivalent of super-admin — useful for bootstrap and internal tooling, but it makes the grant list meaningless and hides missing-grant defects, exactly like testing RBAC from a super-admin session.
- **Close the empty-state gate gap at the source.** Wrap the `EmptyState` CTA in `<Can permission="application.create">` to match the header button; until then, document the dead-end in test plans rather than filing route-guard bugs.

**References:** `../carmen-platform/src/App.tsx` (the three `application.*` route guards) · `src/components/Layout.tsx` (sidebar entry) · `src/pages/ApplicationManagement.tsx` (`<Can>` gates, empty state) · `src/pages/ApplicationEdit.tsx` (Edit-toggle gate) · `../carmen-turborepo-backend-v2/scripts/generate-app-api-catalog/run.ts` (catalog generation).
**Cross-links:** [Applications landing](/en/platform/applications) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md)
