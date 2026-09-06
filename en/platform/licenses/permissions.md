---
title: Licenses — Permissions
description: subscription.read gates viewing (including opening an edit page read-only); subscription.manage alone gates every mutation. license.manage is a different module's key, not this one's.
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, licenses, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Licenses — Permissions

> **At a Glance**
> **Two keys only:** `subscription.read` (nav, all list/detail routes, and — deliberately — the two edit routes too) and `subscription.manage` (every create/update/delete/cancel route and in-page save/cancel-licence action) &nbsp;·&nbsp; **`license.manage` is NOT this module's key** — the pre-existing page description named it as a CRUD gate here; it actually gates an unrelated License Enforcement toggle on the [Platform Config](/en/platform/platform-config) screen (corrected below, §1) &nbsp;·&nbsp; **Feature flag:** `licenses`, checked by `PrivateRoute` after the permission check &nbsp;·&nbsp; **Backend reads are ungated by design** — every `GET` on this module's three purchase/contract controllers carries no `@RequirePlatformPermission` at all, authorized instead by cluster scope inside `micro-cluster` &nbsp;·&nbsp; **Cluster admins never reach this module** — `subscription.read`/`subscription.manage` come only from `tb_user_tb_platform_role`; a membership-only cluster admin has neither, and uses a separate read-only screen instead, gated by cluster membership (`ClusterAdminRoute`'s `isClusterAdminOf(clusterId)` check, not an RBAC key — edge case 5, §4) &nbsp;·&nbsp; **No e2e suite** — every claim below is sourced from `../carmen-platform` and `../carmen-turborepo-backend-v2` implementation directly

## 1. Overview

**Correction to this page's prior description.** Before this task, this page's frontmatter described the module's CRUD gate as "`subscription.manage` and `license.manage`." That is wrong: a repo-wide grep of `../carmen-platform/src` for `license.manage` finds it in exactly one place, `PlatformConfigManagement.tsx:75` (`hasPermission('license.manage')`) and its sibling `platformConfig/LicenseEnforcementCard.tsx`, both part of the **[Platform Config](/en/platform/platform-config)** module — gating an "enforce licence limits" toggle that is a platform-wide setting, unrelated to purchasing or editing any individual licence, subscription, or seat. Nothing under `src/pages/licenses/` references `license.manage` at all. This module has exactly two permission keys, both under the `subscription.*` resource, and this page documents only those two.

The module's one genuinely distinctive shape is that **`subscription.read` alone is enough to open an edit page** — `/licenses/subscriptions/:id/edit`, `/licenses/seats/:id/edit`, and `/licenses/bu-quota/:id/edit` all require `subscription.read` at the route level, the same key their read-only list/detail siblings require, while the three sibling `/new` routes require `subscription.manage`. This is not a route-guard inconsistency: every field on every edit form is independently gated inside the component (§3), so a `subscription.read`-only session sees the record but cannot change it.

## 2. Gate matrix

All routes resolve through `PrivateRoute`, which checks `requiredPermission` first (failure → `<Forbidden>`, in place, URL unchanged) and the `feature` flag strictly afterward (failure → `NotFound` on `hide`, `ComingSoon` on `inactive`) — see [Platform RBAC — Permissions](/en/platform/rbac/permissions) for the shared resolver.

| Route | Permission | Feature | Source |
|---|---|---|---|
| `/licenses` | `subscription.read` | `licenses` | `../carmen-platform/src/App.tsx:183-188` |
| `/licenses/:clusterId` | `subscription.read` | `licenses` | `App.tsx:190-197` |
| `/licenses/subscriptions/new` | `subscription.manage` | `licenses` | `App.tsx:198-205` |
| `/licenses/subscriptions/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:206-213` |
| `/licenses/seats/new` | `subscription.manage` | `licenses` | `App.tsx:214-221` |
| `/licenses/seats/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:222-229` |
| `/licenses/bu-quota/new` | `subscription.manage` | `licenses` | `App.tsx:230-237` |
| `/licenses/bu-quota/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:238-245` |
| `/subscriptions`, `/subscriptions/new`, `/subscriptions/:id/edit` | (none — bare redirects) | n/a | `App.tsx:246-249` |
| Sidebar "Licenses" (License Management group) | `subscription.read` | `licenses` | `../carmen-platform/src/components/nav/platformNav.ts:20` |

In-page `<Can>`/`hasPermission` gates, all on `subscription.manage`:

| Surface | Component |
|---|---|
| Save Changes (subscription edit, sticky bar) | `SubscriptionForm.tsx:591` |
| Create form's Submit button and every editable field (`editing={canEdit}`) | `SubscriptionCreateForm.tsx:254`, `SubscriptionForm.tsx:96` |
| Group picker's checkboxes (`readOnly={!canEdit}`) | `GroupSelectionCard` via `SubscriptionForm.tsx:569` |
| Save Changes / Create License (seat or BU-quota purchase form) | `LicensePurchaseForm.tsx:895,1020` |
| Cancel this license (BU-quota purchase form only — `config.cancel` non-null) | `LicensePurchaseForm.tsx:975` |
| Add Subscription (header + empty state, `SubscriptionTable`) | `SubscriptionTable.tsx:467,650` |
| `BuQuotaSection`/`SeatSection` Add/Edit/Cancel/Remove row actions | `canManage` prop, computed once by `ClusterLicenseDetail.tsx:59` from `hasPermission('subscription.manage')` and passed down — **not** re-checked per section |

Backend enforcement, proven directly against controller source (every write route requires `subscription.manage`; every read route carries no `@RequirePlatformPermission` at all):

| Endpoint | Guard | Source |
|---|---|---|
| `GET /api-system/clusters/:clusterId/licenses` | `AppIdGuard` only | `platform_cluster-licenses.controller.ts:88-89` |
| `POST /api-system/clusters/:clusterId/licenses` | `AppIdGuard` + `PlatformPermissionGuard`, `subscription.manage` | `platform_cluster-licenses.controller.ts:125-127` |
| `PATCH /api-system/clusters/:clusterId/licenses/:id` | same, `subscription.manage` | `platform_cluster-licenses.controller.ts:164-166` |
| `DELETE /api-system/clusters/:clusterId/licenses/:id` | same, `subscription.manage` | `platform_cluster-licenses.controller.ts:205-207` |
| `POST /api-system/clusters/:clusterId/licenses/:id/cancel` | same, `subscription.manage` | `platform_cluster-licenses.controller.ts:241-243` |
| `GET /api-system/platform/cluster-licenses[/:id]` | `AppIdGuard` only | `platform_cluster-licenses.controller.ts:323-324,359-360` (fleet controller) |
| `GET /api-system/business-units/:buId/licenses` | `AppIdGuard` only | `platform_business-unit-licenses.controller.ts:84-85` |
| `POST /api-system/business-units/:buId/licenses` | `subscription.manage` | `platform_business-unit-licenses.controller.ts:121-123` |
| `PATCH /api-system/business-units/:buId/licenses/:id` | `subscription.manage` | `platform_business-unit-licenses.controller.ts:160-162` |
| `DELETE /api-system/business-units/:buId/licenses/:id` | `subscription.manage` | `platform_business-unit-licenses.controller.ts:201-203` |
| `GET /api-system/platform/business-unit-licenses[/:id]` | `AppIdGuard` only | `platform_business-unit-licenses.controller.ts:274-275,310-311` |
| `GET .../subscriptions`, `.../subscriptions/summary`, `.../subscriptions/:id`, `.../license-features` | `subscription.read` | `platform_subscriptions.controller.ts:81-83,139-141,166-168,198-200` |
| `POST .../subscriptions` | `subscription.manage` | `platform_subscriptions.controller.ts:226-228` |
| `PATCH .../subscriptions/:id` | `subscription.manage` | `platform_subscriptions.controller.ts:263-265` |
| `PUT .../subscriptions/:id/groups` | `subscription.manage` | `platform_subscriptions.controller.ts:304-306` |
| `DELETE .../subscriptions/:id` | `subscription.manage` | `platform_subscriptions.controller.ts:349-351` |

All backend paths above are `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/{platform_cluster-licenses,platform_business-unit-licenses,platform_subscriptions}/*.controller.ts`.

## 3. Why the two purchase-form `:id/edit` routes require only `subscription.read`

This is deliberate, proven three separate ways, not an inconsistency to flag as a bug:

1. **The route guard.** `App.tsx` requires `subscription.read` on the `:id/edit` routes and `subscription.manage` only on the sibling `new` routes (§2). A session holding only `subscription.read` can therefore navigate to any existing subscription's or licence's edit URL.
2. **The component's own gate.** Both `SubscriptionForm.tsx:96` and `LicensePurchaseForm.tsx:461` compute `canEdit = hasPermission('subscription.manage')` independently of the route, and use it to decide whether form fields render as editable inputs or as `ReadOnlyField` text — `LicenseFieldsCard`'s own comment states this outright: "`editing` is `false` only for view-only (no `subscription.manage`) — create mode is always `true` (the route already enforces it)." Every Save/Create/Cancel-licence button is separately wrapped in `<Can permission="subscription.manage">`.
3. **The backend agrees.** `ClusterLicenseDetail.tsx:46-48` documents this explicitly: `canManage` is computed from `subscription.manage`, "**not** `cluster.update`," because the backend enforces `subscription.manage` on both license write endpoints regardless of what the frontend does — a session that somehow reached the Save button without holding the key would still get a 403 from the server.

**The reason this shape exists**, per the same source comments: read authorization for a cluster's or BU's own licences is intentionally **not** tied to an RBAC key on the read path — `GET` routes carry no `@RequirePlatformPermission` because that guard only ever consults `tb_user_tb_platform_role`, which has no way to represent "this user administers this specific cluster via `tb_cluster_user`." Gating reads with `subscription.read` at the backend would be harmless for a platform admin holding that key, but the frontend route guard mirrors the same key on purpose so that a platform admin's *browser-side* experience of "can I look" and "can I change" stay visibly distinct, even though the backend's actual read authorization for scoped data runs through cluster membership, not this key at all.

## 4. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Session holds `subscription.read` only | Can open `/licenses`, `/licenses/:clusterId`, and any `:id/edit` URL; sees every field as read-only text, no Save/Cancel-licence/Create buttons, no Add-subscription button on the list | Reproduce by opening a specific licence's edit URL directly — the page renders fully, just inert. `SubscriptionForm.test.tsx` and `SubscriptionTable.test.tsx` both pin this exact case |
| 2 | Session holds `subscription.manage` but not `subscription.read` | Cannot reach `/licenses` or `/licenses/:clusterId` at all (`<Forbidden>`) — but **can** reach `/licenses/subscriptions/new`, `/licenses/seats/new`, `/licenses/bu-quota/new` directly by URL, since those routes check `subscription.manage` only | An unusual grant shape (manage without read) is possible in principle since the two keys are independent RBAC rows; decide per test plan whether it represents a real role or a misconfiguration |
| 3 | Seat licence — attempting to cancel | No Cancel button exists anywhere for a seat licence (list row actions or the dedicated edit page) — `config.cancel` is `null` for `SEAT_CONFIG`, and no such endpoint exists on the backend for `tb_business_unit_license` at all | Do not treat the missing button as a permission problem to escalate — it is a capability that does not exist for this purchase kind, confirmed at both the schema (no `cancelled_at` column) and the config level |
| 4 | A cancelled BU-quota licence | Fields become permanently read-only on its edit page (a banner explains why) even for a `subscription.manage` session; there is no un-cancel — restoring coverage means creating a new licence | The read-only state here is a business rule (§2 of [Data Model](/en/platform/licenses/data-model)), not a permission gate — confirm the Save button is simply absent, not disabled-with-a-tooltip |
| 5 | Cluster admin (membership only, no RBAC role) | Cannot reach any `/licenses/*` route — `hasPermission('subscription.read')` is always `false` for a session with zero `tb_user_tb_platform_role` rows, regardless of cluster-admin standing | Cluster admins use the entirely separate `/cluster-admin/:clusterId/licenses` screen instead. `ClusterAdminRoute` checks scope before the feature flag, in this order: authenticated → `adminScope` loaded → a missing `clusterId` or a caller who is not `isClusterAdminOf` that cluster renders `<Forbidden>` — a non-member of the cluster is stopped there, before `feature="cluster_admin_licenses"` is even consulted. There is **no RBAC permission key** on this route (unlike this module's own `subscription.*` keys), but cluster membership is a real, enforced gate, not an absence of one — do not test this module's gates from a cluster-admin session regardless; it will 403 on the very first `/licenses/*` route it tries |
| 6 | Deep link to `/licenses/subscriptions/:id/edit` with a nonexistent or deleted id | The route guard passes (permission is checked before the id is even fetched); the page then loads, gets a 404 from the API, and renders its own "Subscription not found" `EmptyState` rather than a raw error | Distinguish a permission 403 (whole page replaced by `<Forbidden>`) from a data-layer not-found (`PageHeader` renders normally, only the body is the EmptyState) — they look different and mean different things |
| 7 | Legacy `/subscriptions/:id/edit` bookmark | Redirects via `SubscriptionEditRedirect` before any permission check on the *old* path runs — the permission check that actually applies is the one on the destination route, `/licenses/subscriptions/:id/edit` (`subscription.read`) | A session lacking `subscription.read` sees `<Forbidden>` only after the redirect completes, at the new URL — the address bar will show `/licenses/...`, not the bookmark's original path, which is expected `replace: true` behaviour, not a bug |
| 8 | Super-admin or bootstrap session | All gates in §2 pass regardless of grants — the [RBAC resolver](/en/platform/rbac/permissions) short-circuits before any key check | Never QA this module's gate matrix from a super-admin session; it cannot reveal a missing `subscription.*` grant |
| 9 | Expiry-threshold values (`GET /api-system/platform/expiry-thresholds`) | Readable by **any authenticated session**, independent of `subscription.read` — deliberately, so the warning badges on this module's screens reflect the administrator's real configuration for every viewer, not just those holding a licensing permission | Do not expect this one endpoint to 403 for a session that otherwise cannot reach `/licenses` at all; it is called from `ExpiryThresholdProvider` at the app root, before any route-level gate runs |

## 5. Recommendations

- **Test read and manage as two genuinely independent axes**, not a read≤manage hierarchy assumption carried over from other modules — a session can hold either key alone, and this module's edit routes specifically depend on that independence (§3).
- **Never infer the BU-quota Cancel button's absence as a permission bug** on the seat kind — verify against [Data Model](/en/platform/licenses/data-model) §2.2 first; it is a schema-level capability gap, not a gating oversight.
- **Route the `license.manage` correction forward.** If any other page in this book (particularly [Platform Config](/en/platform/platform-config)) is later found citing `license.manage` as a Licenses-module key, treat this page's §1 correction as authoritative and fix the citation at the source, not here.
- **Test cluster-admin access as its own, separate case** — it never reaches this module's gates at all (edge case 5), and a passing test there proves nothing about this module's own RBAC enforcement.
- **When this module eventually gets an e2e suite**, the read/manage-independence cases in §4 (particularly edge cases 1 and 2) are the highest-value ones to encode first, since they are the module's one genuinely non-obvious gating shape.

**References:** all paths `../carmen-platform` unless noted. `src/App.tsx:183-249` (routes + legacy redirects) · `src/components/nav/platformNav.ts:20` (sidebar entry) · `src/pages/licenses/{SubscriptionForm,LicensePurchaseForm}.tsx` (`canEdit`/`canEditFields` computation, `<Can>` gates) · `src/pages/licenses/ClusterLicenseDetail.tsx:46-59` (`canManage`, single source of truth passed to all three tabs) · `src/pages/PlatformConfigManagement.tsx:74-75`, `src/pages/platformConfig/LicenseEnforcementCard.tsx:14,109` (`license.manage` — a different module's key, §1) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/{platform_cluster-licenses,platform_business-unit-licenses,platform_subscriptions}/*.controller.ts` (backend enforcement, §2).
**Cross-links:** [Licenses landing](/en/platform/licenses) &nbsp;·&nbsp; [Data Model](/en/platform/licenses/data-model) &nbsp;·&nbsp; [UI Screens](/en/platform/licenses/ui-screens) &nbsp;·&nbsp; [Platform RBAC — Permissions](/en/platform/rbac/permissions) &nbsp;·&nbsp; [cluster-admin](/en/platform/cluster-admin) &nbsp;·&nbsp; [Platform Config](/en/platform/platform-config)
