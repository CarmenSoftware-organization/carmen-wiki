---
title: Carmen Platform
description: Overview of the Carmen Platform admin product — entry point for the book, organized by the SPA's own eight sidebar nav groups plus the separate cluster-admin persona.
published: true
date: 2026-09-06T22:00:00.000Z
tags: book/platform, home
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Carmen Platform

Reference manual for developers and QA engineers working on the Carmen Platform admin product — tenancy (clusters and business units), licensing, identity and access, content delivery, analytics, scheduling, platform-wide configuration, and shared databases.

The module list below reads top to bottom in the same order as the sidebar a reader just came from: the ungrouped Dashboard row, then the seven `groupKey` groups the SPA itself builds its navigation from (`../carmen-platform/src/components/nav/platformNav.ts`) — eight sections in total — then a final section for the cluster-admin console: a separate persona with its own nav file, not a ninth menu group.

## 1. Dashboard

The sidebar's own top row — ungrouped, above every `groupKey` group, and reachable by any authenticated session regardless of grants.

| Module | What it covers |
|---|---|
| [Dashboard](/en/platform/dashboard) | Signed-in home hub — a merged recent-activity stream across six domains plus a sticky per-domain active/total counts rail |

## 2. Organization

| Module | What it covers |
|---|---|
| [Clusters](/en/platform/clusters) | Top-level tenant grouping that owns business units and licensed users, backed by a dated license ledger |
| [Business Units](/en/platform/business-units) | Per-property/per-hotel entity — a six-tab form covering identity, formats, database-pool assignment, and BU-scoped users and licenses |
| [Tenant Migrations](/en/platform/tenant-migrations) | Fleet-wide screen that checks and applies pending tenant-database schema migrations across every business unit |
| [Tenant Imports](/en/platform/tenant-imports) | Wizard that loads `Preconfig.xlsx` master data into one business unit's tenant database, step by step |
| [Users](/en/platform/users) | Platform-level user accounts — identity, avatars, and cluster/BU assignments |

## 3. License Management

| Module | What it covers |
|---|---|
| [Licenses](/en/platform/licenses) | License centre — the per-cluster BU-quota ledger, the per-BU seat ledger, and subscriptions with feature-group entitlements |
| [License Catalog](/en/platform/license-catalog) | The sellable feature catalog (Features) and the curated bundles sold from it (Bundles) — one screen, two tabs |

## 4. Content

| Module | What it covers |
|---|---|
| [Report Templates](/en/platform/report-templates) | XML report template catalogue — tabbed editor, database source binding, BU allow/deny scoping, per-report-group default forms |
| [Report Form Groups](/en/platform/report-form-groups) | One card per fixed `report_group` code, each listing its form templates with a set-as-default action — the surface that replaced the deleted print-template-mapping module |
| [News](/en/platform/news) | Markdown announcements with a draft → published → archived lifecycle, global or per-BU targeting |
| [Broadcasts](/en/platform/broadcasts) | Push notifications across three target modes, with scheduling, editing, and a full sender-side lifecycle |

## 5. Analytics

| Module | What it covers |
|---|---|
| [Usage Analytics](/en/platform/usage-analytics) | UI-telemetry dashboard — StatCards, a daily chart, and Top Lists over recorded activity events |
| [Activity Events](/en/platform/activity-events) | The raw, per-event UI-telemetry explorer — every filter and column behind the events Usage Analytics summarizes |

## 6. Scheduling

| Module | What it covers |
|---|---|
| [Cronjobs](/en/platform/cronjobs) | The platform's scheduling console over the shared Cronjob table — job types, who runs them, and where a failed run surfaces |

## 7. Platform

| Module | What it covers |
|---|---|
| [Platform Config](/en/platform/platform-config) | One screen, nine cards — invitations, sign-up, password reset, license enforcement, expiry-warning thresholds, and more |
| [Email Settings](/en/platform/email-settings) | Named SMTP sender profiles and the routing map deciding which of five outbound mail flows uses which profile |
| [Applications](/en/platform/applications) | Registered API clients — their `x-app-id` identity and allow-all vs. explicit `api_name` access grants |
| [Platform RBAC](/en/platform/rbac) | Permission catalog, roles, scoped user assignments, and the super-admin bypass |
| [User Platform](/en/platform/user-platform) | Assigns RBAC platform roles — platform-wide or per-cluster — to existing user accounts |
| [Super Admins](/en/platform/super-admins) | The platform's god-mode allowlist — an add/remove roster of users who bypass every permission check |
| [Feature Flags](/en/platform/feature-flags) | The single screen that sets every feature's visibility (active/inactive/hide) across both the Platform and Cluster-admin consoles |

## 8. Database

| Module | What it covers |
|---|---|
| [Platform Migrations](/en/platform/platform-migrations) | Super-admin console for Prisma migrations against the shared platform database, plus its seed and drift-check operations |
| [SQL Workbench](/en/platform/sql-workbench) | Runs arbitrary SQL and browses/creates/drops views, procedures, and functions against a chosen tenant's database |
| [Database Pools](/en/platform/database-pools) | CRUD registry of shared, platform-managed Postgres connection targets — the single source of tenant database credentials |

## 9. Cluster Admin Console

Reached at `/cluster-admin/:clusterId/*` and built from its own navigation file, `clusterAdminNav.ts` — not one of the eight groups above. This is a second persona rather than an extra menu group: a membership-only cluster admin (no platform-wide permission at all) is routed here instead of into the groups above, and every route it exposes carries the current cluster's id so its own sidebar cannot navigate out of that cluster.

| Module | What it covers |
|---|---|
| [Cluster Admin](/en/platform/cluster-admin) | A second navigation and persona scoped to one cluster at a time — no RBAC permission key anywhere in it, gated instead by cluster membership |

## 10. Account & Product Chrome

Pages that exist outside the sidebar entirely — reached from the login flow, the avatar menu, or a version badge, not from either nav above.

| Module | What it covers |
|---|---|
| [Profile](/en/platform/profile) | Self-service page where a signed-in user views and edits their own identity fields and changes their password |
| [Landing](/en/platform/landing) | The public marketing page at `/` — redirects an already-authenticated session straight to Dashboard |
| [Changelog](/en/platform/changelog) | The platform's versioned, public changelog, reached via a version badge |

## 11. How to use this book

- Start with the module's own landing page for an overview
- Drill into its sub-pages for data models, UI flows, and edge cases
- See the [global wiki landing](/en/home) for the Inventory book
