---
title: Carmen Platform
description: Overview of the Carmen Platform admin product — entry point for the book.
published: true
date: 2026-07-29T09:46:00.000Z
tags: book/platform, home
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Carmen Platform

Reference manual for developers and support engineers working on the Carmen Platform admin product — tenancy (clusters and business units), identity and access, content delivery (news and broadcasts), API clients, report and print templates, and the product changelog.

## 1. Tenancy

| Module | What it covers |
|---|---|
| [Clusters](/en/platform/clusters) | Tenant cluster hierarchy and ownership |
| [Business Units](/en/platform/business-units) | Property / BU management within a cluster |

## 2. Identity & Access

| Module | What it covers |
|---|---|
| [Users](/en/platform/users) | User accounts, avatars, and cluster/BU assignments |
| [Platform RBAC](/en/platform/rbac) | Permission catalog, roles, scoped user assignments, super-admin bypass |
| [Profile](/en/platform/profile) | The signed-in user's own profile and password change |

## 3. Content

| Module | What it covers |
|---|---|
| [News](/en/platform/news) | Markdown announcements with draft → published → archived lifecycle and global or per-BU targeting |
| [Broadcasts](/en/platform/broadcasts) | Push-notification compose with three target modes and immediate or scheduled delivery |

## 4. Platform

| Module | What it covers |
|---|---|
| [Applications](/en/platform/applications) | Registered API clients, their `x-app-id` identity, and `api_name` access grants |
| [SQL Workbench](/en/platform/sql-workbench) | Per-tenant SQL console — browse/run/save/drop views, procedures, and functions against a business unit's database |

## 5. Reporting

| Module | What it covers |
|---|---|
| [Report Templates](/en/platform/report-templates) | XML report template catalogue with tabbed editor and per-BU scoping |
| [Print Template Mapping](/en/platform/print-template-mapping) | Routing document types (PR, PO, GRN, …) to FastReport print templates |

## 6. Product & Shell

| Module | What it covers |
|---|---|
| [Landing](/en/platform/landing) | Public marketing page at `/` — redirects an authenticated session straight to Dashboard |
| [Dashboard](/en/platform/dashboard) | Signed-in home hub — merged recent-activity stream + per-domain active/total counts |
| [Changelog](/en/platform/changelog) | Versioned, public release history + version badge |

## 7. How to use this book

- Start with the module home page for an overview
- Drill into sub-pages for data models, UI flows, and edge cases
- See the [global wiki landing](/en/home) for the Inventory book
