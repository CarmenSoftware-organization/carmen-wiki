---
title: News — Permissions
description: The news.* gate matrix for authors (including bulk publish/archive/delete), the reader-side visibility rules on the anonymous public endpoints (status, published_at cutoff, global vs BU targeting), and the edge-case matrix for testers.
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, news, permissions
editor: markdown
dateCreated: 2026-06-10T13:00:00.000Z
---

# News — Permissions

> **At a Glance**
> **Gate:** routes carry `news.read` / `.create` / `.update` on `PrivateRoute`; sidebar entry on `.read` &nbsp;·&nbsp; **In-page `<Can>`/in-component gates:** Add News (`.create`), row Edit (`.update`), row Delete (`.delete` — in-page only, no route), Edit toggle (`.update`), bulk Publish/Archive Selected (`.update`), bulk Delete Selected (`.delete`) &nbsp;·&nbsp; **Known gap:** the empty-state "Add News" CTA is ungated &nbsp;·&nbsp; **Reader side:** `/api/public/news` is **anonymous** — visibility is decided by `status = published` + `published_at <= now()` + targeting, not by any permission key

## 1. Overview

Two independent authorization stories meet in this module. The first is ordinary [Platform RBAC](/en/platform/rbac): the four `news.*` keys (seeded in `seed.platform-permission.ts`) that decide which *authors* may see and mutate articles in the admin SPA (§2). The second is what the rows themselves encode: the **reader-side visibility rules** — which articles the anonymous public endpoints serve to which audience, governed by `status`, `published_at`, soft deletion, and the `business_unit_ids` targeting list (§3). No RBAC key plays any part in delivery, and no bearer token or `x-app-id` is checked on the public controller — an author with zero `news.*` keys can still read every published article through `/api/public/news`, like anyone else.

Machine callers of the authenticated `/api/news` CRUD (including the tag-list endpoint) are gated on a third, parallel axis: `AppIdGuard` grants (`news.findAll`, `news.findOne`, `news.create`, `news.update`, `news.delete`) checked against the calling application's allowlist — see [Applications](/en/platform/applications). A request can fail on the user axis, the application axis, or both.

## 2. Gate matrix

All SPA gates resolve through the single permission resolver documented in [Platform RBAC — Permissions](../rbac/permissions.md); a failed route guard renders the dedicated `Forbidden` page (renamed from the earlier inline `AccessDenied`; still a 403 "Access Denied" heading, now with Go Back / Go to Dashboard actions) inside the normal `Layout` shell.

| Surface | Mechanism | Key | Source |
|---|---|---|---|
| `/news` | `PrivateRoute requiredPermission` | `news.read` | `src/App.tsx` |
| `/news/new` | `PrivateRoute requiredPermission` | `news.create` | `src/App.tsx` |
| `/news/:id/edit` | `PrivateRoute requiredPermission` | `news.update` | `src/App.tsx` |
| Sidebar "News" (Content group, Newspaper icon) | `Layout.tsx` nav filter | `news.read` | `src/components/Layout.tsx` |
| Add News (list header) | `<Can>` | `news.create` | `NewsManagement.tsx` |
| Row Edit (actions dropdown) | `<Can>` | `news.update` | `NewsManagement.tsx` |
| Row Delete (actions dropdown) | `<Can>` | `news.delete` | `NewsManagement.tsx` |
| Row selection checkbox column | in-component (`canSelect = canUpdate \|\| canDelete`) | `news.update` or `news.delete` | `NewsManagement.tsx` |
| Bulk Publish Selected / Archive Selected | in-component (`canUpdate`) | `news.update` | `NewsManagement.tsx` |
| Bulk Delete Selected | in-component (`canDelete`) | `news.delete` | `NewsManagement.tsx` |
| Edit toggle (edit-page header) | `<Can>` | `news.update` | `NewsEdit.tsx` |
| `GET /api/news/tags` | `AppIdGuard` | `news.findAll` (same key as the list) | `news.controller.ts` |

Tester-relevant asymmetries, mirroring the Applications and Print Template Mapping modules:

- **`.delete` is in-page only.** No route requires it and the edit page has no delete action — the key's entire surface is the list row's dropdown item plus the bulk Delete Selected button. A `.read`-only session sees the list with an empty actions dropdown and no selection checkboxes at all (`canSelect` requires `.update` or `.delete`).
- **Save is not separately gated.** Only the Edit *toggle* is `<Can>`-wrapped; the Save/Cancel row renders only in edit mode, which is unreachable without the toggle (create mode sits behind the route's `.create`). Backend enforcement on `PUT` — including the `doc_version` requirement — remains the real boundary.
- **The empty-state CTA is ungated.** When the list is empty and no search/filter is active, `ListEmptyState` offers an "Add News" button with no `<Can>` wrap — a `.create`-less session sees the affordance, clicks it, and lands on the `/news/new` route guard's `Forbidden` page. Affordance leak only, not an enforcement hole.
- **Export is ungated.** Any session that reaches the list (`.read`) can CSV-export the loaded page.
- **Bulk actions reuse the single-row keys** — Publish/Archive Selected gate on `.update` (the same key as row Edit and the Edit toggle), Delete Selected on `.delete`. There is no separate "bulk" permission; a session that can edit or delete one row can bulk-edit or bulk-delete many, subject to the same server-side `doc_version` check per row.
- **Route keys are independent.** `.update` alone deep-links to `/news/:id/edit` while `/news` denies; `.create` alone reaches `/news/new` by URL.
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
| 9 | List sort appears broken | The server overrides every sort to `updated_at DESC`; the SPA's `published_at:desc` default and clickable headers are sent but ignored | Known divergence ([Data Model](./data-model.md) §5) — don't file per-column sort defects until the override is removed |
| 10 | Two articles, same title | Allowed — no unique constraint on `title` | Disambiguate via id (Debug Sheet) when testing |
| 11 | Stale `doc_version` on save or bulk action | `PUT` with an outdated `doc_version` returns 409; the SPA shows "This record was changed by someone else", discards any pending image, and refetches | Reproduce by opening the same article in two tabs, saving in one, then saving (or bulk-publishing) in the other |
| 12 | Bulk action on a mixed selection | Each row is updated/deleted independently via `Promise.allSettled`; one row's failure (e.g. a `doc_version` conflict) does not block the others | Expect a "N succeeded, M failed" toast rather than an all-or-nothing outcome — there is no transaction across the selection |
| 13 | Tag exceeds server limits | ≤20 tags and ≤40 characters per tag are enforced by micro-cluster only; the SPA's `ChipInput` has no client-side cap | Adding a 21st tag or a >40-character tag passes the UI silently and only fails on save (400) |

## 5. Recommendations

- **Test the two stories separately.** Verify author gating with sessions holding exactly one `news.*` key at a time; verify delivery with raw anonymous calls to `/api/public/news` — a passing SPA save says nothing about who can read the article.
- **Probe the lifecycle × feed matrix.** For one article, walk draft → published → archived → published and confirm feed membership and the constant `published_at` at each step (cases 2–3 above).
- **Targeting QA needs three calls per article:** public feed without `bu_id`, with a targeted BU's id, and with a non-targeted id — plus the single-item endpoint to confirm it skips the BU check (§3, item 3).
- **Exercise the machine axis once.** Hit `/api/news` with a valid bearer but an application lacking the `news.*` grants to confirm the `AppIdGuard` rejection is independent of the user's RBAC keys.
- **QA the bulk toolbar's failure path**, not just its happy path: seed a mix of a healthy row and a row someone else just edited, bulk-publish both, and confirm the partial-failure toast and the confirm-code gate (a fresh 6-character code per dialog open).
- **Treat the ungated empty-state CTA and the ignored list sort as known issues** — verify behaviour matches this page rather than filing duplicates; both are affordance/UX gaps with server-side enforcement intact.

**References:** `../carmen-platform/src/App.tsx` (the three route guards) · `src/components/Layout.tsx` (sidebar entry) · `src/pages/NewsManagement.tsx` / `NewsEdit.tsx` (`<Can>` gates, bulk toolbar, ungated CTA) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/news.controller.ts` (KeycloakGuard + per-route `AppIdGuard`, including `GET tags`) · `public-news.controller.ts` (no guards) · `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` (BU validation, tag normalization, `doc_version` lock, soft-delete filtering, `findPublicAll`/`findPublicOne` filters) · `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.ts` (the four keys).
**Cross-links:** [News landing](/en/platform/news) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md) &nbsp;·&nbsp; [Applications](/en/platform/applications)
