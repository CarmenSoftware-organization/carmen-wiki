---
title: Business Units
description: Per-property/per-hotel entity with a multi-section form covering identity, contact, tax, formats, calculation, configuration, database connection, and BU-scoped user roster.
published: true
date: 2026-05-19T21:00:00.000Z
tags: platform/business-units, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Business Units

> **At a Glance**
> **Module purpose:** Authoring surface where the operational entity that Carmen calls a **business unit** (BU) is created and configured — one row per hotel/property/legal-entity, with the form fields that drive both the inventory app's tenant context and the platform's user-role assignments &nbsp;·&nbsp; **Audience:** Any authenticated platform user — Carmen-internal admins and customer-side managers alike &nbsp;·&nbsp; **Key entities/tables:** `business_unit` (identity fields `code`, `name`, `alias_name`, `is_hq`, `is_active`, `max_license_users`; contact blocks for hotel/company; tax fields; date/time/number format fields; `calculation_method`, `default_currency_id`; `db_connection`; `config[]` key/value rows) plus the BU-to-user join carrying a per-BU `role` of `admin` or `user` &nbsp;·&nbsp; **Sub-pages:** 2

## 1. Overview

A business unit is the operational tenant of the Carmen platform: one BU is one hotel, one property, or one legal entity that buys, receives, counts, and consumes inventory. The list view at `/business-units` (`BusinessUnitManagement.tsx`) is a server-paginated, searchable catalogue with Active/Inactive and soft-deleted facets and CSV export. The edit page at `/business-units/:id/edit` and `/business-units/new` (`BusinessUnitEdit.tsx`) renders nine form sections as cards in a two-column grid — Basic Information, Hotel Information, Company Information, Tax Information, Date/Time Formats, Number Formats, Calculation Settings, Configuration, and Database Connection — followed by a separate Users card that lists the people assigned to the BU. The Users card only appears after the BU exists; creation is a save-then-assign flow.

Each BU belongs to exactly one **cluster** (the `cluster_id` foreign key, selected from a dropdown). The "create BU" flow can be entered either from the BU list page or from the cluster edit page, which navigates to `/business-units/new?cluster_id=<id>` to preselect the parent. Beyond identity and contact fields, the BU stores the locale knobs that the inventory runtime reads — `date_format`, `time_format`, `timezone`, the JSON `amount_format`/`quantity_format`/`recipe_format` formatters defaulting to `th-TH`, the `calculation_method`, and `default_currency_id` — plus a `config[]` array of free-form key/value rows and a JSON `db_connection` block that points the BU at its tenant schema. Detail on individual fields and screen behaviour lives on the sub-pages — this landing page only orients.

## 2. Business Context

In hospitality, the smallest unit that has its own books, its own currency, and its own local supply chain is the property — a single hotel inside a brand group. Carmen models that as a business unit: every inventory transaction (GRN, store requisition, physical count, spot check) is scoped to one BU; every report runs against one BU's schema; every user is granted access to one or more BUs with a role inside each. The `business_unit` row therefore carries far more than identity. It carries the locale settings the inventory UI displays in (date and number formats, timezone, default currency), the costing knob (`calculation_method`) the valuation engine consults, the per-tenant database connection the platform uses to route queries to that property's schema, and the licence ceiling (`max_license_users`) that caps how many users may sign in.

Because a BU is also where users become operationally meaningful, the edit page doubles as a user-assignment workbench. The Users card lists everyone with access to this BU, each with a **BU role** (`admin` or `user`) that is orthogonal to the platform-level role on the user account itself. New BU members are picked from the BU's parent cluster — a user must already exist on the cluster before they can be added to one of its BUs, which keeps tenant boundaries clean. Anyone with a platform login can reach these routes today; the platform-level role differentiates what they can do across other modules (clusters, report templates, etc.), not whether they can open the BU edit page.

## 3. Key Concepts

- **Business unit (BU)**: A single row in `business_unit` representing one hotel/property/legal entity. Every inventory transaction belongs to exactly one BU; every report runs against one BU.
- **Cluster membership**: Every BU has a non-nullable `cluster_id` selected from the cluster dropdown. The cluster edit page can launch a create-BU flow with `cluster_id` preselected via the `/business-units/new?cluster_id=<id>` query parameter.
- **HQ flag (`is_hq`)**: Marks the BU as the headquarters within its cluster — a single Boolean displayed alongside the Active flag in Basic Information; semantics depend on consuming modules.
- **Active flag (`is_active`)**: Toggles whether the BU is operationally live. Inactive BUs remain editable in the admin surface but are filtered out of normal runtime selection. The list view exposes Active/Inactive as filter chips.
- **Max licensed users (`max_license_users`)**: Optional integer cap on how many users may be assigned to the BU. Blank means unlimited.
- **Hotel vs. Company information**: Two parallel contact blocks (`hotel_*` and `company_*` — name, telephone, email, address, ZIP) because the property's operational identity (hotel) often differs from the invoicing legal entity (company).
- **Tax information**: `tax_no` and `branch_no` capture the Thai tax registration plus branch designator used on printed documents.
- **Date/Time formats**: `date_format`, `date_time_format`, `time_format`, `long_time_format`, `short_time_format`, and `timezone` configure how the inventory UI renders timestamps for this BU.
- **Number formats**: Three JSON formatters — `amount_format`, `quantity_format`, `recipe_format` — plus a `perpage_format` JSON that drives pagination defaults. Each formatter defaults to `{"locales":"th-TH","minimumIntegerDigits":2}`.
- **Calculation settings**: `calculation_method` (the BU's costing approach, e.g. FIFO/Weighted Average — consumed by the inventory valuation engine) and `default_currency_id` (foreign key to the currency table, with the resolved code/name/symbol/decimals shown alongside in read mode).
- **Configuration array (`config[]`)**: An ordered list of free-form `{ key, value }` rows persisted as a JSON array on the BU. Used by the inventory app for per-BU feature toggles and integration settings; the admin surface does not impose a schema.
- **Database connection (`db_connection`)**: A JSON block stored on the BU that tells the platform which database/schema this BU's transactions live in. Rendered as a pretty-printed `<pre>` block; the admin surface validates it as JSON only.
- **BU role (`admin` vs. `user`)**: The role attached to each user-BU assignment, stored on the BU-user join row alongside `is_active` and `is_default`. The `BU_ROLES` constant in `BusinessUnitEdit.tsx` defines exactly two values. This is **orthogonal** to the platform-level role on the user account; the BU role governs the user's behaviour inside the inventory app for that BU, not access to admin routes.
- **Add-user-from-cluster pattern**: New BU members are picked from the parent cluster's user list (`clusterUsers`) — a user must be a member of the cluster before they can be added to one of its BUs.
- **Soft delete**: BUs are soft-deleted via `deleted_at` / `deleted_by_name`; the list view has a "Show soft-deleted business units" filter toggle that overlays a red `Deleted` badge and an extra "Deleted By" column for audit.

## 4. Roles and Personas

The `/business-units`, `/business-units/new`, and `/business-units/:id/edit` routes use `PrivateRoute` **without an `allowedRoles` prop** — confirmed by reading `../carmen-platform/src/App.tsx` and `../carmen-platform/SITEMAP.md`. Any user holding a valid session reaches these routes; there is no platform-role gate at the route level, and `BusinessUnitEdit.tsx` does not gate individual buttons (Edit, Delete, Add User, role change, soft-delete) by platform role either. The only role concept used by this page is the BU-scoped `admin`/`user` value applied to user-BU assignments inside the Users card, which is data the page edits — not a guard on it.

| Persona | Route access | What they typically do here |
|---|---|---|
| All authenticated platform users | Full access to list, create, edit, soft-delete BUs and manage the BU user roster | Whatever the operational context calls for — Carmen support engineers configure new properties end-to-end; customer-side managers update contact details, formats, and their own BU user roster |

Because there is no `allowedRoles` array, the responsibility for limiting who can mutate BU state currently lives outside the admin product (typically at the backend API and at provisioning time). Pages cross-referenced in Section 5 cover how the platform's other admin surfaces are gated more strictly.

## 5. Related Modules

- [[clusters]] — every BU is owned by exactly one cluster via `cluster_id`; the cluster edit page launches the create-BU flow with the parent preselected through the `/business-units/new?cluster_id=<id>` query parameter
- [[users]] — supplies the user accounts that get assigned to BUs through the Users card; new BU members are drawn from the parent cluster's user list, and clicking a name in the Users card jumps to the user edit page
- [[auth-roles]] — explains the `PrivateRoute` mechanism that gates every platform route, and why the BU routes are reachable by any authenticated user given that no `allowedRoles` array is supplied
- [[report-templates]] — `allow_business_unit` / `deny_business_unit` chip inputs there scope a report template by the BU `code` values defined here

## 6. Reference Sources

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/BusinessUnitManagement.tsx`, `../carmen-platform/src/pages/BusinessUnitEdit.tsx`, `../carmen-platform/src/App.tsx`

## 7. Pages in This Module

- [Data Model](./data-model.md) — BU entity reference: identity fields, hotel/company contact blocks, date/time/number format fields, calculation settings, the `config[]` key/value array, the `db_connection` JSON block, and the BU-user join schema.
- [UI Screens](./ui-screens.md) — Tour of the list view (`BusinessUnitManagement`) and the edit page (`BusinessUnitEdit`) form sections, plus the Users card with its BU-role select and add-from-cluster dialog.
