---
title: Profile
description: Self-service page where a signed-in user views and edits their own identity fields and changes their password.
published: true
date: 2026-06-10T14:15:00.000Z
tags: platform/profile, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Profile

> **At a Glance**
> **Module purpose:** Self-service page where a signed-in user views and edits their own identity fields and changes their password &nbsp;·&nbsp; **Audience:** The signed-in user themselves &nbsp;·&nbsp; **Access:** authenticated-only — the `/profile` route carries no `requiredPermission` &nbsp;·&nbsp; **Key entities/tables:** `user`, `user_info`, `business_unit` (read-only display) &nbsp;·&nbsp; **Sub-pages:** 0

## 1. Overview

Profile is the personal-account page of the Carmen Platform admin product. Every authenticated user reaches it from the avatar menu at the bottom of the sidebar — there is no top-level navigation entry for `/profile`. The page shows the user's current identity (alias name, first/middle/last name, telephone, email, account ID, member-since date) and, in a separate read-only card, the list of business units assigned to that account. The Profile Overview card renders a small role badge only when the API response carries a `role` string; the legacy `platform_role` display was removed when the SPA moved to permission-based RBAC ([rbac](/en/platform/rbac)).

Two write operations are supported, both sent as `PATCH /api/user/profile`. The first edits the identity fields — alias name, first name, middle name, last name, telephone; the Profile Information card opens read-only and an **Edit** button switches it into edit mode (with a Save Changes / Cancel pair and an unsaved-changes guard). Email cannot be changed from this page. The second changes the account password through a **Change Password** modal dialog that requires the current password plus a new password of at least six characters and a matching confirmation. Saving an identity edit re-fetches the profile and refreshes the local auth context, so the sidebar avatar and display name update immediately. Password changes do not refresh the auth context — the dialog just closes on success.

The page is intentionally narrow in scope. It does not assign or revoke business-unit memberships, grant permissions, or manage other users — those flows belong to the [users](/en/platform/users) and [rbac](/en/platform/rbac) modules and require the corresponding permission grants. The `/profile` route is wrapped in a plain `<PrivateRoute>` with no `requiredPermission` — like the Dashboard, it is reachable by any authenticated session regardless of permission grants.

## 2. Business Context

Profile is a self-service maintenance page; it has no external business driver beyond keeping each user's identity information current so that audit logs, notifications, and BU rosters reference accurate names and contact details.

## 3. Key Concepts

- **Profile**: The set of identity fields owned by an individual user account — alias name, first/middle/last name, telephone, email. All editable from this page except email.
- **Alias name**: Optional short label used to render the user's avatar initials and as a compact display name where space is tight.
- **Email (immutable)**: The user's sign-in identifier. Surfaced read-only on the Profile page; changing it is an administrative operation handled outside this module.
- **View/edit toggle**: The Profile Information card opens read-only; an **Edit** button (visible alongside **Change Password** when not editing) switches the identity fields into edit mode. Cancel restores the saved values without an API call; the `useUnsavedChanges` hook fires a browser warning on navigation with unsaved edits. Ctrl/Cmd+S submits, Escape cancels.
- **Password change**: A dedicated modal flow that requires the current password, a new password (minimum six characters), and a matching confirmation. Submitted through the same `PATCH /api/user/profile` endpoint as identity edits, but with `currentPassword` / `newPassword` populated instead.
- **Assigned business units**: The list of BUs the user belongs to, shown as a read-only card. Membership is managed in the [users](/en/platform/users) module by an administrator; the Profile page only displays it.
- **Account ID and member-since date**: Read-only metadata stamped at account creation. Useful for support and audit conversations but not editable from this page.

## 4. Roles and Personas

Used by the signed-in user themselves. The `/profile` route is wrapped in a plain `<PrivateRoute>` with no `requiredPermission` prop — authentication is the only gate, and no `<Can>` gates appear within the page. No RBAC grant is required or checked.

## 5. Related Modules

- [users](/en/platform/users) — the administrative counterpart that creates accounts and assigns business units; Profile only reads what Users writes
- [rbac](/en/platform/rbac) — owns the permission model that gates every other surface; Profile itself requires only an authenticated session, and role/permission assignment happens in the RBAC module's User Platform screen
- [business-units](/en/platform/business-units) — the source of the BU list rendered read-only on the Profile page

## 6. Reference Sources

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/Profile.tsx` (calls `GET` / `PATCH /api/user/profile` directly via the shared axios instance in `src/services/api.ts` — there is no dedicated profile service file), `../carmen-platform/src/App.tsx` (the bare `<PrivateRoute>` on `/profile`)

## 7. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
