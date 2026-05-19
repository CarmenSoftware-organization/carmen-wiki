---
title: Profile
description: Self-service page where a signed-in user views and edits their own identity fields and changes their password.
published: true
date: 2026-05-19T12:00:00.000Z
tags: platform/profile, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Profile

> **At a Glance**
> **Module purpose:** Self-service page where a signed-in user views and edits their own identity fields and changes their password &nbsp;·&nbsp; **Audience:** The signed-in user themselves &nbsp;·&nbsp; **Key entities/tables:** `user`, `user_info`, `business_unit` (read-only display) &nbsp;·&nbsp; **Sub-pages:** 0

## 1. Overview

Profile is the personal-account page of the Carmen Platform admin product. Every authenticated user reaches it from the avatar menu at the bottom of the sidebar — there is no top-level navigation entry for `/profile`. The page shows the user's current identity (alias name, first/middle/last name, telephone, email, platform role, account ID, member-since date) and, in a separate read-only card, the list of business units assigned to that account.

Two write operations are supported. The first edits the identity fields — alias name, first name, middle name, last name, telephone — via `PUT /api/user/profile`; email cannot be changed from this page. The second changes the account password through a modal dialog that requires the current password plus a new password of at least six characters, also posted to `PUT /api/user/profile`. Saving an identity edit re-fetches the profile and refreshes the local auth context, so the sidebar avatar and display name update immediately. Password changes do not refresh the auth context — the form just closes.

The page is intentionally narrow in scope. It does not assign or revoke business-unit memberships, change platform roles, or manage other users — those flows belong to the [[users]] and [[auth-roles]] modules and require admin privileges. Profile is the only Platform page every authenticated account can reach regardless of role.

## 2. Business Context

Profile is a self-service maintenance page; it has no external business driver beyond keeping each user's identity information current so that audit logs, notifications, and BU rosters reference accurate names and contact details.

## 3. Key Concepts

- **Profile**: The set of identity fields owned by an individual user account — alias name, first/middle/last name, telephone, email. All editable from this page except email.
- **Alias name**: Optional short label used to render the user's avatar initials and as a compact display name where space is tight.
- **Email (immutable)**: The user's sign-in identifier. Surfaced read-only on the Profile page; changing it is an administrative operation handled outside this module.
- **Password change**: A dedicated modal flow that requires the current password, a new password (minimum six characters), and a matching confirmation. Submitted through the same `PUT /api/user/profile` endpoint as identity edits, but with the password fields populated instead.
- **Assigned business units**: The list of BUs the user belongs to, shown as a read-only card. Membership is managed in the [[users]] module by an administrator; the Profile page only displays it.
- **Account ID and member-since date**: Read-only metadata stamped at account creation. Useful for support and audit conversations but not editable from this page.

## 4. Roles and Personas

Used by the signed-in user themselves. No admin role applies.

## 5. Related Modules

- [[users]] — the administrative counterpart that creates accounts, assigns business units, and sets platform roles; Profile only reads what Users writes
- [[auth-roles]] — owns the sign-in flow and role assignment that gates whether a user can reach Profile in the first place
- [[business-units]] — the source of the BU list rendered read-only on the Profile page

## 6. Reference Sources

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/Profile.tsx`

## 7. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
