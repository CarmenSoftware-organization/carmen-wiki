---
title: Licenses — Permissions
description: subscription.read gates viewing (including opening an edit page read-only); subscription.manage alone gates every mutation. license.manage is a different module's key, not this one's.
published: true
date: 2026-10-29T05:30:00.000Z
tags: book/backstage, licenses, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Licenses — Permissions

> **At a Glance**
> **Two keys only:** `subscription.read` (nav, all list/detail routes, and — deliberately — the three purchase-form edit routes and the subscription edit route too) and `subscription.manage` (every create/update/delete/cancel route and in-page save/cancel-licence action — the interface-licence routes added in PR #287 reuse exactly these two keys, no new key was minted) &nbsp;·&nbsp; **`license.manage` is NOT this module's key** — the pre-existing page description named it as a CRUD gate here; it actually gates an unrelated License Enforcement toggle on the [Backstage Config](/en/backstage/backstage-config) screen (corrected below, §1) &nbsp;·&nbsp; **Feature flag:** `licenses`, checked by `PrivateRoute` after the permission check &nbsp;·&nbsp; **Backend reads are ungated by design** — every `GET` on this module's four purchase/contract controllers (except the subscription ones, and the super-admin-only `deleted` lists) carries no `@RequireBackstagePermission` at all, authorized instead by cluster scope inside `micro-cluster` &nbsp;·&nbsp; **Cluster admins never reach this module** — `subscription.read`/`subscription.manage` come only from `tb_user_tb_backstage_role`; a membership-only cluster admin has neither, and uses a separate read-only screen instead, gated by cluster membership (`ClusterAdminRoute`'s `isClusterAdminOf(clusterId)` check, not an RBAC key — edge case 5, §4) &nbsp;·&nbsp; **e2e: smoke only** (`licenses-smoke.spec.ts` — renders + sidebar, super-admin session, mutations aborted) — every claim below is sourced from `../carmen-backstage` and `../carmen-turborepo-backend` implementation directly

## 1. Overview

**Correction to this page's prior description.** Before this task, this page's frontmatter described the module's CRUD gate as "`subscription.manage` and `license.manage`." That is wrong: a repo-wide grep of `../carmen-backstage/src` for `license.manage` finds it in exactly one place, `BackstageConfigManagement.tsx:75` (`hasPermission('license.manage')`) and its sibling `backstageConfig/LicenseEnforcementCard.tsx`, both part of the **[Backstage Config](/en/backstage/backstage-config)** module — gating an "enforce licence limits" toggle that is a platform-wide setting, unrelated to purchasing or editing any individual licence, subscription, or seat. Nothing under `src/pages/licenses/` references `license.manage` at all. This module has exactly two permission keys, both under the `subscription.*` resource, and this page documents only those two.

The module's one genuinely distinctive shape is that **`subscription.read` alone is enough to open an edit page** — `/licenses/subscriptions/:id/edit`, `/licenses/seats/:id/edit`, `/licenses/bu-quota/:id/edit`, and `/licenses/interface/:id/edit` all require `subscription.read` at the route level, the same key their read-only list/detail siblings require, while the four sibling `/new` routes require `subscription.manage`. This is not a route-guard inconsistency: every field on every edit form is independently gated inside the component (§3), so a `subscription.read`-only session sees the record but cannot change it.

## 2. Gate matrix

All routes resolve through `PrivateRoute`, which checks `requiredPermission` first (failure → `<Forbidden>`, in place, URL unchanged) and the `feature` flag strictly afterward (failure → `NotFound` on `hide`, `ComingSoon` on `inactive`) — see [Backstage Roles — Permissions](/en/backstage/rbac/permissions) for the shared resolver.

| Route | Permission | Feature | Source |
|---|---|---|---|
| `/licenses` | `subscription.read` | `licenses` | `../carmen-backstage/src/App.tsx:187-194` |
| `/licenses/:clusterId` | `subscription.read` | `licenses` | `App.tsx:195-202` |
| `/licenses/subscriptions/new` | `subscription.manage` | `licenses` | `App.tsx:203-210` |
| `/licenses/subscriptions/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:211-218` |
| `/licenses/seats/new` | `subscription.manage` | `licenses` | `App.tsx:219-226` |
| `/licenses/seats/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:227-234` |
| `/licenses/bu-quota/new` | `subscription.manage` | `licenses` | `App.tsx:235-242` |
| `/licenses/bu-quota/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:243-250` |
| `/licenses/interface/new` | `subscription.manage` | `licenses` | `App.tsx:251-258` (PR #287) |
| `/licenses/interface/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:259-266` (PR #287) |
| `/subscriptions`, `/subscriptions/new`, `/subscriptions/:id/edit` | (none — bare redirects) | n/a | `App.tsx:268-270` |
| Sidebar "Licenses" (License Management group) | `subscription.read` | `licenses` | `../carmen-backstage/src/components/nav/backstageNav.ts:24` |

In-page `<Can>`/`hasPermission` gates, all on `subscription.manage`:

| Surface | Component |
|---|---|
| Save Changes (subscription edit, sticky bar) | `SubscriptionForm.tsx:591` |
| Create form's Submit button and every editable field (`editing={canEdit}`) | `SubscriptionCreateForm.tsx:254`, `SubscriptionForm.tsx:96` |
| Group picker's checkboxes (`readOnly={!canEdit}`) | `GroupSelectionCard` via `SubscriptionForm.tsx:569` |
| Save Changes / Create License (seat, BU-quota or interface purchase form) | `LicensePurchaseForm.tsx` (`canEdit`, `<Can permission="subscription.manage">` on both buttons) |
| "Add interface license" / "New subscription" links on the BU edit page's Licenses tab | `BusinessUnitEdit.tsx:793,810` — `createHref` is supplied only when `canCreateSubscription` (= `hasPermission('subscription.manage')`), the same key the destination routes check, so the link never leads to a `<Forbidden>` |
| Cancel this license (BU-quota purchase form only — `config.cancel` non-null) | `LicensePurchaseForm.tsx:975` |
| Add Subscription (header + empty state, `SubscriptionTable`) | `SubscriptionTable.tsx:467,650` |
| License Center **Deleted** summary card and the deleted-licence view (`?deleted=1`) | `LicenseCenter.tsx` passes a `deletedView` control only when `isSuperAdmin` and the tab is not "By cluster"; for everyone else the card is a read-only number (a pasted `?deleted=1` link still shows the normal table) |
| Restore (deleted view row action) | `<Can permission="subscription.manage">` in `DeletedLicenseTable.tsx`; **Delete permanently** is shown only when `isSuperAdmin` and asks the operator to type the licence number (`TypeToConfirmDialog`) |
| Soft-delete button at the foot of the **subscription** edit page and the **interface-licence** edit page (not seats, not BU quota) | `<Can permission="subscription.manage">` in `SubscriptionForm.tsx` / `LicensePurchaseForm.tsx` (`config.kind === 'interface'`); behind a `ConfirmDialog`, then redirects to the list |
| `BuQuotaSection`/`SeatSection` Add/Edit/Cancel/Remove row actions | `canManage` prop, computed once by `ClusterLicenseDetail.tsx:59` from `hasPermission('subscription.manage')` and passed down — **not** re-checked per section |

Backend enforcement, proven directly against controller source (every write route requires `subscription.manage`; every read route carries no `@RequireBackstagePermission` at all):

| Endpoint | Guard | Source |
|---|---|---|
| `GET /api-system/clusters/:clusterId/licenses` | `AppIdGuard` only | `backstage_cluster-licenses.controller.ts:104-105` |
| `POST /api-system/clusters/:clusterId/licenses` | `AppIdGuard` + `BackstagePermissionGuard`, `subscription.manage` | `backstage_cluster-licenses.controller.ts:144-146` |
| `PATCH /api-system/clusters/:clusterId/licenses/:id` | same, `subscription.manage` | `backstage_cluster-licenses.controller.ts:189-191` |
| `DELETE /api-system/clusters/:clusterId/licenses/:id` | same, `subscription.manage` | `backstage_cluster-licenses.controller.ts:237-239` |
| `POST /api-system/clusters/:clusterId/licenses/:id/cancel` | same, `subscription.manage` | `backstage_cluster-licenses.controller.ts:277-279` |
| `GET /api-system/backstage/cluster-licenses[/:id]` | `AppIdGuard` only | `backstage_cluster-licenses.controller.ts:370-371,500-501` (fleet controller) |
| `GET /api-system/business-units/:buId/licenses` | `AppIdGuard` only | `backstage_business-unit-licenses.controller.ts:99-100` |
| `POST /api-system/business-units/:buId/licenses` | `subscription.manage` | `backstage_business-unit-licenses.controller.ts:139-141` |
| `PATCH /api-system/business-units/:buId/licenses/:id` | `subscription.manage` | `backstage_business-unit-licenses.controller.ts:184-186` |
| `DELETE /api-system/business-units/:buId/licenses/:id` | `subscription.manage` | `backstage_business-unit-licenses.controller.ts:232-234` |
| `GET /api-system/backstage/business-unit-licenses[/:id]` | `AppIdGuard` only | `backstage_business-unit-licenses.controller.ts:316-317,436-437` |
| `GET /api-system/business-units/:buId/interface-licenses` | `AppIdGuard('businessUnitInterfaceLicense.findAll')` only | `backstage_business-unit-interface-licenses.controller.ts:105-106` |
| `POST /api-system/business-units/:buId/interface-licenses` | `AppIdGuard` + `BackstagePermissionGuard`, `subscription.manage` | `backstage_business-unit-interface-licenses.controller.ts:148-150` |
| `PATCH /api-system/business-units/:buId/interface-licenses/:id` | same, `subscription.manage` | `backstage_business-unit-interface-licenses.controller.ts:194-196` |
| `DELETE /api-system/business-units/:buId/interface-licenses/:id` | same, `subscription.manage` | `backstage_business-unit-interface-licenses.controller.ts:241-243` |
| `GET /api-system/backstage/interface-licenses[/:id]` | `AppIdGuard` only | `backstage_business-unit-interface-licenses.controller.ts:328-329,458-459` (fleet controller, same file) |
| `GET .../subscriptions`, `.../subscriptions/summary`, `.../subscriptions/:id`, `.../license-features` | `subscription.read` | `backstage_subscriptions.controller.ts:90-92,145-147,215-217,251-253` |
| `POST .../subscriptions` | `subscription.manage` | `backstage_subscriptions.controller.ts:282-284` |
| `PATCH .../subscriptions/:id` | `subscription.manage` | `backstage_subscriptions.controller.ts:322-324` |
| `PUT .../subscriptions/:id/groups` | `subscription.manage` | `backstage_subscriptions.controller.ts:369-371` |
| `DELETE .../subscriptions/:id` | `subscription.manage` | `backstage_subscriptions.controller.ts:421-423` |
| `GET .../{cluster-licenses,business-unit-licenses,interface-licenses}/summary` (fleet controllers) | `AppIdGuard` only, scope-filtered | `backstage_cluster-licenses.controller.ts:430-431`, `backstage_business-unit-licenses.controller.ts:366-367`, `backstage_business-unit-interface-licenses.controller.ts:388-389` |
| `GET .../{cluster-licenses,business-unit-licenses,interface-licenses}/deleted`, `GET .../subscriptions/deleted` | `AppIdGuard` + **`BackstageSuperAdminGuard`** — no permission key at all | `…cluster-licenses.controller.ts:460-461`, `…business-unit-licenses.controller.ts:396-397`, `…interface-licenses.controller.ts:418-419`, `backstage_subscriptions.controller.ts:178-179` |
| `POST .../{cluster-licenses,business-unit-licenses,interface-licenses}/:id/restore`, `POST .../subscriptions/:id/restore` | `subscription.manage` | `…cluster-licenses.controller.ts:539-541`, `…business-unit-licenses.controller.ts:475-477`, `…interface-licenses.controller.ts:499-501`, `backstage_subscriptions.controller.ts:459-461` |
| `DELETE .../{cluster-licenses,business-unit-licenses,interface-licenses}/:id/hard`, `DELETE .../subscriptions/:id/hard` | **`BackstageSuperAdminGuard`** only | `…cluster-licenses.controller.ts:573-574`, `…business-unit-licenses.controller.ts:512-513`, `…interface-licenses.controller.ts:536-537`, `backstage_subscriptions.controller.ts:498-499` |

All backend paths above are `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/{backstage_cluster-licenses,backstage_business-unit-licenses,backstage_business-unit-interface-licenses,backstage_subscriptions}/*.controller.ts`. The interface-licence controller's header comment repeats the same reasoning the other two give for leaving reads ungated: `BackstagePermissionGuard` builds its permission set only from `tb_user_tb_backstage_role`, so an RBAC key on the read path would 403 a membership-only cluster admin looking at their own cluster.

## 3. Why the two purchase-form `:id/edit` routes require only `subscription.read`

This is deliberate, proven three separate ways, not an inconsistency to flag as a bug:

1. **The route guard.** `App.tsx` requires `subscription.read` on the `:id/edit` routes and `subscription.manage` only on the sibling `new` routes (§2). A session holding only `subscription.read` can therefore navigate to any existing subscription's or licence's edit URL.
2. **The component's own gate.** Both `SubscriptionForm.tsx:96` and `LicensePurchaseForm.tsx:461` compute `canEdit = hasPermission('subscription.manage')` independently of the route, and use it to decide whether form fields render as editable inputs or as `ReadOnlyField` text — `LicenseFieldsCard`'s own comment states this outright: "`editing` is `false` only for view-only (no `subscription.manage`) — create mode is always `true` (the route already enforces it)." Every Save/Create/Cancel-licence button is separately wrapped in `<Can permission="subscription.manage">`.
3. **The backend agrees.** `ClusterLicenseDetail.tsx:46-48` documents this explicitly: `canManage` is computed from `subscription.manage`, "**not** `cluster.update`," because the backend enforces `subscription.manage` on both license write endpoints regardless of what the frontend does — a session that somehow reached the Save button without holding the key would still get a 403 from the server.

**The reason this shape exists**, per the same source comments: read authorization for a cluster's or BU's own licences is intentionally **not** tied to an RBAC key on the read path — `GET` routes carry no `@RequireBackstagePermission` because that guard only ever consults `tb_user_tb_backstage_role`, which has no way to represent "this user administers this specific cluster via `tb_cluster_user`." Gating reads with `subscription.read` at the backend would be harmless for a platform admin holding that key, but the frontend route guard mirrors the same key on purpose so that a platform admin's *browser-side* experience of "can I look" and "can I change" stay visibly distinct, even though the backend's actual read authorization for scoped data runs through cluster membership, not this key at all.

## 4. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Session holds `subscription.read` only | Can open `/licenses`, `/licenses/:clusterId`, and any `:id/edit` URL; sees every field as read-only text, no Save/Cancel-licence/Create buttons, no Add-subscription button on the list | Reproduce by opening a specific licence's edit URL directly — the page renders fully, just inert. `SubscriptionForm.test.tsx` and `SubscriptionTable.test.tsx` both pin this exact case |
| 2 | Session holds `subscription.manage` but not `subscription.read` | Cannot reach `/licenses` or `/licenses/:clusterId` at all (`<Forbidden>`) — but **can** reach `/licenses/subscriptions/new`, `/licenses/seats/new`, `/licenses/bu-quota/new` directly by URL, since those routes check `subscription.manage` only | An unusual grant shape (manage without read) is possible in principle since the two keys are independent RBAC rows; decide per test plan whether it represents a real role or a misconfiguration |
| 3 | Seat or interface licence — attempting to cancel | No Cancel button exists anywhere for a seat or interface licence (list row actions or the dedicated edit page) — `config.cancel` is `null` for `SEAT_CONFIG` and `INTERFACE_CONFIG`, and no such endpoint exists on the backend for either table | Do not treat the missing button as a permission problem to escalate — it is a capability that does not exist for these purchase kinds, confirmed at both the schema (no `cancelled_at` column) and the config level |
| 3a | `subscription.manage` session attaches an `interface`-kind group to a subscription (`PUT .../subscriptions/:id/groups`), or a `standard` group to an interface licence (`POST .../interface-licenses`) | **400 from the backend**, not a silent filter and not a 403 — the permission is fine, the payload is not. The SPA never offers either combination (the subscription form's `GroupSelectionCard` hides `interface` groups; the purchase form's picker lists only `interface` groups), so this is reachable only by direct API call | A 400 here is the group-kind rule (`enum_license_feature_group_kind`, [Data Model](/en/backstage/licenses/data-model) §5), not a gating defect; do not file it against RBAC |
| 4 | A cancelled BU-quota licence | Fields become permanently read-only on its edit page (a banner explains why) even for a `subscription.manage` session; there is no un-cancel — restoring coverage means creating a new licence | The read-only state here is a business rule (§2 of [Data Model](/en/backstage/licenses/data-model)), not a permission gate — confirm the Save button is simply absent, not disabled-with-a-tooltip |
| 5 | Cluster admin (membership only, no RBAC role) | Cannot reach any `/licenses/*` route — `hasPermission('subscription.read')` is always `false` for a session with zero `tb_user_tb_backstage_role` rows, regardless of cluster-admin standing | Cluster admins use the entirely separate `/cluster-admin/:clusterId/licenses` screen instead. `ClusterAdminRoute` checks scope before the feature flag, in this order: authenticated → `adminScope` loaded → a missing `clusterId` or a caller who is not `isClusterAdminOf` that cluster renders `<Forbidden>` — a non-member of the cluster is stopped there, before `feature="cluster_admin_licenses"` is even consulted. There is **no RBAC permission key** on this route (unlike this module's own `subscription.*` keys), but cluster membership is a real, enforced gate, not an absence of one — do not test this module's gates from a cluster-admin session regardless; it will 403 on the very first `/licenses/*` route it tries |
| 6 | Deep link to `/licenses/subscriptions/:id/edit` with a nonexistent or deleted id | The route guard passes (permission is checked before the id is even fetched); the page then loads, gets a 404 from the API, and renders its own "Subscription not found" `EmptyState` rather than a raw error | Distinguish a permission 403 (whole page replaced by `<Forbidden>`) from a data-layer not-found (`PageHeader` renders normally, only the body is the EmptyState) — they look different and mean different things |
| 7 | Legacy `/subscriptions/:id/edit` bookmark | Redirects via `SubscriptionEditRedirect` before any permission check on the *old* path runs — the permission check that actually applies is the one on the destination route, `/licenses/subscriptions/:id/edit` (`subscription.read`) | A session lacking `subscription.read` sees `<Forbidden>` only after the redirect completes, at the new URL — the address bar will show `/licenses/...`, not the bookmark's original path, which is expected `replace: true` behaviour, not a bug |
| 8 | Super-admin or bootstrap session | All gates in §2 pass regardless of grants — the [RBAC resolver](/en/backstage/rbac/permissions) short-circuits before any key check | Never QA this module's gate matrix from a super-admin session; it cannot reveal a missing `subscription.*` grant |
| 9 | Expiry-threshold values (`GET /api-system/backstage/expiry-thresholds`) | Readable by **any authenticated session**, independent of `subscription.read` — deliberately, so the warning badges on this module's screens reflect the administrator's real configuration for every viewer, not just those holding a licensing permission | Do not expect this one endpoint to 403 for a session that otherwise cannot reach `/licenses` at all; it is called from `ExpiryThresholdProvider` at the app root, before any route-level gate runs |
| 10 | A `subscription.manage` session (not a super admin) wants to see deleted licences | No way in: the Deleted card is inert for them and the `…/deleted` endpoints answer 403 (`BackstageSuperAdminGuard`). They can *soft-delete* a subscription or interface licence from its edit page and, if they know the id, call `restore`, but cannot list what they deleted | Test restore with a super-admin session; test the card as inert with a plain `subscription.manage` one |
| 11 | Permanent delete of an active licence | Backend refuses with 409 `LICENSE_HARD_DELETE_ACTIVE` — hard delete is allowed only for a soft-deleted row, or (BU quota) a cancelled one. The SPA offers it only in the deleted view, plus a row action on cancelled BU-quota rows in the live table (`PurchaseLicenseTable.tsx`, `hardDeleteRow`) | A permanently deleted number is written to `tb_license_number_retired` and never reissued ([Data Model](/en/backstage/licenses/data-model) §2.5) |

## 5. Recommendations

- **Test read and manage as two genuinely independent axes**, not a read≤manage hierarchy assumption carried over from other modules — a session can hold either key alone, and this module's edit routes specifically depend on that independence (§3).
- **Never infer the BU-quota Cancel button's absence as a permission bug** on the seat kind — verify against [Data Model](/en/backstage/licenses/data-model) §2.2 first; it is a schema-level capability gap, not a gating oversight.
- **Route the `license.manage` correction forward.** If any other page in this book (particularly [Backstage Config](/en/backstage/backstage-config)) is later found citing `license.manage` as a Licenses-module key, treat this page's §1 correction as authoritative and fix the citation at the source, not here.
- **Test cluster-admin access as its own, separate case** — it never reaches this module's gates at all (edge case 5), and a passing test there proves nothing about this module's own RBAC enforcement.
- **When this module gets more than a smoke e2e spec**, the read/manage-independence cases in §4 (particularly edge cases 1 and 2) are the highest-value ones to encode first, since they are the module's one genuinely non-obvious gating shape.

**References:** all paths `../carmen-backstage` unless noted. `src/App.tsx:187-270` (routes + legacy redirects) · `src/components/nav/backstageNav.ts:24` (sidebar entry) · `src/pages/licenses/{SubscriptionForm,LicensePurchaseForm}.tsx` (`canEdit`/`canEditFields` computation, `<Can>` gates) · `src/pages/licenses/ClusterLicenseDetail.tsx:46-59` (`canManage`, single source of truth passed to all three tabs) · `src/pages/BackstageConfigManagement.tsx:74-75`, `src/pages/backstageConfig/LicenseEnforcementCard.tsx:14,109` (`license.manage` — a different module's key, §1) · `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/{backstage_cluster-licenses,backstage_business-unit-licenses,backstage_subscriptions}/*.controller.ts` (backend enforcement, §2).
**Cross-links:** [Licenses landing](/en/backstage/licenses) &nbsp;·&nbsp; [Data Model](/en/backstage/licenses/data-model) &nbsp;·&nbsp; [UI Screens](/en/backstage/licenses/ui-screens) &nbsp;·&nbsp; [Backstage Roles — Permissions](/en/backstage/rbac/permissions) &nbsp;·&nbsp; [cluster-admin](/en/backstage/cluster-admin) &nbsp;·&nbsp; [Backstage Config](/en/backstage/backstage-config)
