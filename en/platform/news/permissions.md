---
title: News — Permissions
description: The news.* gate matrix for authors (including bulk publish/archive/delete), the reader-side visibility rules on the anonymous public endpoints (status, published_at cutoff, global vs BU targeting), and the edge-case matrix for testers.
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, news, permissions
editor: markdown
dateCreated: 2026-06-10T13:00:00.000Z
---

# News — Permissions

> **At a Glance**
> **Gate:** routes carry `news.read` / `.create` / `.update` on `PrivateRoute`; sidebar entry on `.read` &nbsp;·&nbsp; **In-page `<Can>`/in-component gates:** Add News (header **and** empty-state CTA, `.create`), row Edit (`.update`), row Delete (`.delete` — no SPA route requires it), Edit toggle (`.update`), bulk Publish/Archive Selected (`.update`), bulk Delete Selected (`.delete`), row / edit-page-header **View History** (`activity_log.read`, `PLATFORM_SCOPED_RECORD` — not in the `NewsMasthead` actions slot) &nbsp;·&nbsp; **Server-side (API):** `POST`/`PUT`/`DELETE` enforce the caller's own `news.*` permission (`PlatformPermissionGuard`, added 2026-08-20); all four `GET` routes check only `x-app-id` — deliberately unenforced on the user-permission axis, so the mobile app's tenant-level users can keep reading news &nbsp;·&nbsp; **Reader side:** `/api/public/news` is **anonymous** — visibility is decided by `status = published` + `published_at <= now()` + targeting, not by any permission key

## 1. Overview

Two independent authorization stories meet in this module. The first is ordinary [Platform RBAC](/en/platform/rbac): the four `news.*` keys (seeded in `seed.platform-permission.ts`) that decide which *authors* may see and mutate articles in the admin SPA (§2). The second is what the rows themselves encode: the **reader-side visibility rules** — which articles the anonymous public endpoints serve to which audience, governed by `status`, `published_at`, soft deletion, and the `business_unit_ids` targeting list (§3). No RBAC key plays any part in delivery, and no bearer token or `x-app-id` is checked on the public controller — an author with zero `news.*` keys can still read every published article through `/api/public/news`, like anyone else.

Machine callers of the authenticated `/api/news` CRUD (including the tag-list and summary endpoints) are gated on a third, parallel axis: `AppIdGuard` grants (`news.findAll`, `news.findOne`, `news.create`, `news.update`, `news.delete`) checked against the calling application's allowlist — see [Applications](/en/platform/applications).

**That third axis is not the whole server-side story, and it changed mid-project.** Until 2026-08-20, `news.controller.ts` carried **zero** `@RequirePlatformPermission` decorators — only `KeycloakGuard` (must be logged in) and `AppIdGuard` (the calling app must hold the key). Any authenticated user, from any application with `news.*` in its allowlist, could create, update, or delete news regardless of their own RBAC keys; hiding the SPA's buttons was the only real control. A fix that day added `PlatformPermissionGuard` + `@RequirePlatformPermission('news.create'/'news.update'/'news.delete')` to the three **write** routes only, closing that gap (the equivalent check on `broadcast.*` routes had existed for longer, which is what exposed `news.controller.ts` as the outlier). The four **read** routes (`findAll`, `findOne`, `tags`, `summary`) were left unguarded on purpose, not by oversight: the DEV database shows the `mobile-app` application holds `news.findAll`/`news.findOne` in its allowlist and serves tenant-level users who hold **no platform role at all** — adding a `news.read` check there would lock every mobile user out of news. So today: a request can fail on the application axis alone (any route) or on **both** the application axis and the user-permission axis (write routes only) — the user-permission axis simply does not exist for reads.

## 2. Gate matrix

All SPA gates resolve through the single permission resolver documented in [Platform RBAC — Permissions](/en/platform/rbac/permissions); a failed route guard renders the dedicated `Forbidden` page (renamed from the earlier inline `AccessDenied`; still a 403 "Access Denied" heading, now with Go Back / Go to Dashboard actions) inside the normal `Layout` shell.

| Surface | Mechanism | Key | Source |
|---|---|---|---|
| `/news` | `PrivateRoute requiredPermission` | `news.read` | `src/App.tsx` |
| `/news/new` | `PrivateRoute requiredPermission` | `news.create` | `src/App.tsx` |
| `/news/:id/edit` | `PrivateRoute requiredPermission` | `news.update` | `src/App.tsx` |
| Sidebar "News" (Content group, Newspaper icon) | nav filter | `news.read` | `src/components/nav/platformNav.ts` (line 27 — not `Layout.tsx`, which defines no nav rows) |
| Add News (list header) | `<Can>` | `news.create` | `NewsManagement.tsx` |
| Add News (empty-state CTA) | `<Can>` | `news.create` | `NewsManagement.tsx` |
| Row Edit (actions dropdown) | `<Can>` | `news.update` | `NewsManagement.tsx` |
| Row Delete (actions dropdown) | `<Can>` | `news.delete` | `NewsManagement.tsx` |
| Row selection checkbox column | in-component (`canSelect = canUpdate \|\| canDelete`) | `news.update` or `news.delete` | `NewsManagement.tsx` |
| Bulk Publish Selected / Archive Selected | in-component (`canUpdate`) | `news.update` | `NewsManagement.tsx` |
| Bulk Delete Selected | in-component (`canDelete`) | `news.delete` | `NewsManagement.tsx` |
| Edit toggle (edit-page masthead) | `<Can>` | `news.update` | `NewsEdit.tsx` |
| Row **View History** (actions dropdown) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` | `NewsManagement.tsx` — cross-cutting Activity Trail feature |
| Edit-page **View History** (top header row, next to the back link — existing records only; not in the masthead) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` | `NewsEdit.tsx` |
| `GET /api/news/tags` | `AppIdGuard` only | `news.findAll` (same key as the list) | `news.controller.ts` |
| `GET /api/news/summary` | `AppIdGuard` only | `news.findAll` (reused, not a distinct key) | `news.controller.ts` |
| `POST /api/news` | `AppIdGuard` **+ `PlatformPermissionGuard`** (server-side, added 2026-08-20) | `news.create` (both axes) | `news.controller.ts` |
| `PUT /api/news/:id` | `AppIdGuard` **+ `PlatformPermissionGuard`** (added 2026-08-20) | `news.update` (both axes) | `news.controller.ts` |
| `DELETE /api/news/:id` | `AppIdGuard` **+ `PlatformPermissionGuard`** (added 2026-08-20) | `news.delete` (both axes) | `news.controller.ts` |
| `GET /api/news`, `GET /api/news/:id` | `AppIdGuard` only — no platform-permission check | `news.findAll` / `news.findOne` | `news.controller.ts` |

Tester-relevant asymmetries, mirroring the Applications module:

- **`.delete` has no SPA route, but it does have a server-side check.** No route requires it and the edit page has no delete action — the key's *client-side* surface is the list row's dropdown item plus the bulk Delete Selected button. A `.read`-only session sees the list with an empty actions dropdown and no selection checkboxes at all (`canSelect` requires `.update` or `.delete`). This is a client-routing fact only: since 2026-08-20 the `DELETE` endpoint itself also rejects a caller lacking `news.delete`, independent of what the SPA shows.
- **Save is not separately gated.** Only the Edit *toggle* is `<Can>`-wrapped; the Save/Cancel row renders only in edit mode, which is unreachable without the toggle (create mode sits behind the route's `.create`). Backend enforcement on `PUT` — the `doc_version` requirement **and**, since 2026-08-20, the `news.update` permission check — is the real boundary.
- **The empty-state CTA is gated, matching the header Add button.** `ListEmptyState`'s "Add News" affordance is wrapped in the same `<Can permission="news.create">` as the header button (`NewsManagement.tsx:640`) — a `.create`-less session sees neither.
- **Export is ungated.** Any session that reaches the list (`.read`) can CSV-export the loaded page; there is no `<Can>` wrap on the Export button.
- **The read routes are permanently, deliberately ungated on the user-permission axis.** `news.read` gates only the SPA's route/sidebar; `GET /api/news`, `/:id`, `/tags`, and `/summary` accept any authenticated caller from an app-id-allowed application, with no `news.read` check server-side — because the same routes serve the mobile app's tenant-level users, who hold no platform role. Do not expect a 403 from these four routes based on a missing `news.*` key; expect one only from a missing/disallowed `x-app-id`.
- **Bulk actions reuse the single-row keys** — Publish/Archive Selected gate on `.update` (the same key as row Edit and the Edit toggle), Delete Selected on `.delete`. There is no separate "bulk" permission; a session that can edit or delete one row can bulk-edit or bulk-delete many, subject to the same server-side `doc_version` check per row, and (since 2026-08-20) the same server-side permission check per row.
- **Route keys are independent.** `.update` alone deep-links to `/news/:id/edit` while `/news` denies; `.create` alone reaches `/news/new` by URL.
- **`activity_log.read` is a genuinely separate grant** from every `news.*` key — a session can hold View History without holding any `news.*` key, or vice versa; test the two independently.
- **Seeded roles split unevenly across the four keys** (`seed.platform-role-permission.data.ts`): Platform Admin holds `news.*` (all four); Support Manager holds `news.read`/`.create`/`.update` but **not** `.delete`; Support Staff holds `news.read` only; Security Officer holds none of the four. A Support Manager session is the cheapest way to reproduce "`.delete` denied, everything else allowed" without a custom role.
- The sidebar filter is UX, not security — a session lacking `news.read` can still type the URL and hits the route guard. Super-admin and bootstrap sessions pass every gate; never QA this matrix from one.

## 3. Targeting and visibility rules

Write-side, micro-cluster validates targeting on create and on any update that touches the field: `business_unit_ids` must be an array of strings and every unique id must match a live `tb_business_unit` row, else 400. The SPA additionally requires ≥1 BU whenever the "Visible to all business units" checkbox is unchecked — so `[]` can only be produced deliberately, by checking the box.

Read-side, the public feed (`GET /api/public/news`, anonymous) decides visibility entirely from row data:

```
visible(article, bu_id?):
    if article.deleted_at is not null:        return false
    if article.status != published:           return false   -- draft and archived alike
    if article.published_at is null
       or article.published_at > now():       return false   -- future-dated = scheduled;
                                                             -- an API-cleared stamp also hides it
    if bu_id is absent:
        return article.business_unit_ids == []               -- global only
    return article.business_unit_ids == []
        or bu_id in article.business_unit_ids                 -- global + targeted
```

Consequences for testers:

1. **A reader in BU X sees:** all global articles plus articles whose list contains X's BU id — provided the caller passes `bu_id=X`. The endpoint trusts the parameter; there is no session to derive it from. An unknown or malformed `bu_id` silently degrades to global-only (no error).
2. **Omitting `bu_id` hides every targeted article**, even from audiences it targets — the burden of sending the right id is on the consuming client.
3. **The single-item endpoint** (`GET /api/public/news/:id`) applies the status/date/deletion filters but **no BU check** — any caller who knows a targeted article's UUID can fetch it. Targeting on the public surface is feed-scoping, not access control.
4. Draft, archived, soft-deleted, future-dated, and nonexistent ids all answer the same 404 — existence does not leak.

## 4. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Archived vs soft-deleted | `archived` stays in the admin list (badge, filterable) and out of the public feed; soft-deleted rows are now **excluded server-side** from `GET /api/news` (confirmed fixed since the last sync — micro-cluster's list query filters `deleted_at: null`) and 404 on `GET :id` | Archive to retire content visibly; delete to remove it from the admin list entirely. The SPA's old client-side `deleted_at`/`audit.deleted.at` hiding is now a no-op — the Debug Sheet's raw list JSON no longer contains deleted rows either |
| 2 | Status flipped `published` → `draft` | `published_at` is **retained**, not cleared (verified in micro-cluster `update`); the article leaves the public feed because of the status filter alone | The list still shows the old Published timestamp on a draft row — by design, not a bug. Re-publishing keeps the original stamp |
| 3 | Re-publishing an archived article | Returns to the public feed under its **original** `published_at` (server stamps only never-published rows) | Sorted by `published_at DESC` publicly, an old re-published article does *not* jump to the top |
| 4 | Explicit/future `published_at` | Settable via API only (SPA never sends it); a future date keeps a `published` row out of the feed until the time passes | De-facto scheduled publishing; only testable through the API or Bruno, not the SPA |
| 5 | Legacy `image` field | SPA reads `image_url \|\| image` everywhere; current gateway emits `image_url` (presigned, 1-hour expiry) and strips the stored token | A thumbnail that 404s after sitting on a stale list page is an expired presigned URL — refresh refetches fresh URLs |
| 6 | GIF or oversized image | The SPA picker accepts `image/gif` and only enforces ≤5 MB; the backend rejects GIF (`BAD_FILE_TYPE`) and >2048×2048 px (`BAD_DIMENSIONS`) at save time | Client/server accept lists diverge — the failure surfaces as a form-level "Failed to save news", not at file-pick time |
| 7 | Removing a saved image | Not possible from the SPA: JSON updates leave the image unchanged, and the ImageUpload Remove button only clears a *pending* selection | The only way to drop an image is to replace it (the old MinIO file is then deleted server-side) |
| 8 | BU soft-deleted after being targeted | Validation runs at write time only; the stale id stays in `business_unit_ids` and still matches the public feed's `array_contains` | Saving the article again with the targeting field touched re-validates and then **rejects** the stale id — the editor must drop it to save |
| 9 | List sort appears broken | The server overrides every sort to `updated_at DESC`; the SPA's `published_at:desc` default and clickable headers are sent but ignored | Known divergence ([Data Model](/en/platform/news/data-model) §5) — don't file per-column sort defects until the override is removed |
| 10 | Two articles, same title | Allowed — no unique constraint on `title` | Disambiguate via id (Debug Sheet) when testing |
| 11 | Stale `doc_version` on save or bulk action | `PUT` with an outdated `doc_version` returns 409; the SPA shows "This record was changed by someone else", discards any pending image, and refetches | Reproduce by opening the same article in two tabs, saving in one, then saving (or bulk-publishing) in the other |
| 12 | Bulk action on a mixed selection | Each row is updated/deleted independently via `Promise.allSettled`; one row's failure (e.g. a `doc_version` conflict) does not block the others | Expect a "N succeeded, M failed" toast rather than an all-or-nothing outcome — there is no transaction across the selection |
| 13 | Tag exceeds server limits | ≤20 tags and ≤40 characters per tag are enforced by micro-cluster only; the SPA's `ChipInput` has no client-side cap | Adding a 21st tag or a >40-character tag passes the UI silently and only fails on save (400) |
| 14 | Support Staff (or any `news.read`-only) session calls `POST`/`PUT`/`DELETE /api/news*` directly | 403, since 2026-08-20 (`PlatformPermissionGuard` + `RequirePlatformPermission`) — previously (before that fix) it would have succeeded regardless of RBAC keys | A regression here (a write succeeding for a read-only role) is a real security bug, not a UX gap — unlike edge case 15's read-side behaviour |
| 15 | A session with **zero** `news.*` keys, from an app-id-allowed application, calls `GET /api/news` directly | 200 — succeeds. This is intentional, not a bug: the four read routes check only `x-app-id`, never the caller's own permissions, because the mobile app's tenant-level users share these routes and hold no platform role at all | Do not file this as a permission-bypass defect; verify instead that the *SPA* still hides the "News" sidebar item and denies `/news` for such a session (client-side only) |

## 5. Recommendations

- **Test the two stories separately.** Verify author gating with sessions holding exactly one `news.*` key at a time; verify delivery with raw anonymous calls to `/api/public/news` — a passing SPA save says nothing about who can read the article.
- **Probe the lifecycle × feed matrix.** For one article, walk draft → published → archived → published and confirm feed membership and the constant `published_at` at each step (cases 2–3 above).
- **Targeting QA needs three calls per article:** public feed without `bu_id`, with a targeted BU's id, and with a non-targeted id — plus the single-item endpoint to confirm it skips the BU check (§3, item 3).
- **Exercise the machine axis once.** Hit `/api/news` with a valid bearer but an application lacking the `news.*` grants to confirm the `AppIdGuard` rejection is independent of the user's RBAC keys.
- **Exercise the write-permission axis separately.** With a session holding `news.read` only, confirm `POST`/`PUT`/`DELETE /api/news*` now return 403 (fixed 2026-08-20) — and confirm the four read routes still return 200 for that same session, since that half is deliberate, not a leftover gap (edge cases 14–15).
- **QA the bulk toolbar's failure path**, not just its happy path: seed a mix of a healthy row and a row someone else just edited, bulk-publish both, and confirm the partial-failure toast and the confirm-code gate (a fresh 6-character code per dialog open).
- **Test View History independently of the `news.*` keys** — `activity_log.read` is a separate grant; a session can hold one, both, or neither.
- **Treat the ignored list sort as a known issue** — verify behaviour matches [Data Model](/en/platform/news/data-model) §5 rather than filing a duplicate; it is an affordance/UX gap with server-side enforcement (the `updated_at DESC` override) intact. The empty-state CTA is **not** a known issue any more — it is `<Can>`-gated the same as the header button.

**References:** `../carmen-platform/src/App.tsx` (the three route guards) · `src/components/nav/platformNav.ts` (sidebar entry, line 27 — not `Layout.tsx`, which defines no nav rows) · `src/pages/NewsManagement.tsx` / `NewsEdit.tsx` (`<Can>` gates, bulk toolbar, View History) · `src/utils/permissions.ts` (`PLATFORM_SCOPED_RECORD`) · `src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail,constants}.tsx` (View History; `AUDIT_RECORDING_STARTED_ON_PHASE_2` = 2026-08-31) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/news.controller.ts` (KeycloakGuard on every route; `AppIdGuard` per route including `GET tags`/`summary`; `PlatformPermissionGuard` + `RequirePlatformPermission` added to the three write routes only, commit `9b474a3fc1c4478ef18d5e5caf9b62d9098f1344`, 2026-08-20) · `public-news.controller.ts` (no guards) · `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` (BU validation, tag normalization, `doc_version` lock, soft-delete filtering, `findPublicAll`/`findPublicOne` filters) · `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` (the four keys) · `seed.platform-role-permission.data.ts` (Platform Admin holds all four; Support Manager holds read/create/update, not delete; Support Staff holds read only; Security Officer holds none).
**Cross-links:** [News landing](/en/platform/news) &nbsp;·&nbsp; [Data Model](/en/platform/news/data-model) &nbsp;·&nbsp; [UI Screens](/en/platform/news/ui-screens) &nbsp;·&nbsp; [Platform RBAC — Permissions](/en/platform/rbac/permissions) &nbsp;·&nbsp; [Applications](/en/platform/applications)
