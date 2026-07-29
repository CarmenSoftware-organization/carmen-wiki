---
title: Print Template Mapping — Permissions
description: Historical record — the four print_template_mapping.* permission keys were removed from the platform permission catalog on 2026-07-23; no replacement keys exist for Form Groups.
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, print-template-mapping, permissions
editor: markdown
dateCreated: 2026-06-10T12:45:00.000Z
---

# Print Template Mapping — Permissions

> **Implementation status (verified 2026-07-29): the `print_template_mapping.*` keys no longer exist.** carmen-turborepo-backend-v2 commit `c135bb21e` removed all four rows (`read`/`create`/`update`/`delete`) from `seed.platform-permission.data.ts` and every reference to them from `seed.platform-role-permission.data.ts`'s role bundles (`platform_admin`, `support_manager`, `support_staff`). The permission catalog itself no longer defines these keys — a role built today cannot even select them from the `PermissionPicker`, since [Permission Catalog](/en/platform/rbac/ui-screens) only shows what the backend returns. This page documents the former gate matrix for historical reference; see [Report Templates — Permissions](/en/platform/report-templates/permissions) for how the Form Groups replacement is gated (it reuses `report_template.*` — there are no new keys for it).

## 1. Overview (historical)

Two independent authorization stories used to meet in this module: ordinary Platform RBAC gating on the four `print_template_mapping.*` keys (who could see/edit mapping rows), and resolve-time BU rules baked into the mapping rows themselves (which mapping the print pipeline picked for a given document type + business unit). Both are gone — the keys were deleted from the catalog, and the `resolve` endpoint and its BU allow/deny precedence logic were deleted along with the Go service's mapping repo.

## 2. Former gate matrix

| Surface | Key |
|---|---|
| `/print-template-mapping` | `print_template_mapping.read` |
| `/print-template-mapping/new` | `print_template_mapping.create` |
| `/print-template-mapping/:id/edit` | `print_template_mapping.update` |
| Sidebar "Print Mapping" (Content group) | `print_template_mapping.read` |
| Row Delete | `print_template_mapping.delete` (in-page only, no route ever required it) |

## 3. Former resolve-time rules

The removed `resolve(document_type, bu_code)` endpoint ordered active, non-deleted mappings for a document type by `is_default DESC, display_order ASC` and returned the first row whose allow/deny BU lists permitted the caller's `bu_code` (deny checked first; a blank `bu_code` skipped BU checks entirely). This logic, and the known gap that micro-business's actual print path queried the table directly without applying the BU checks, no longer applies to anything — the table and the endpoint are both gone.

## 4. What governs the replacement

The Form Groups screen (`/report-form-groups`) is gated by `report_template.read` (route + sidebar) and `report_template.update` / `.create` for its mutating actions (setting a group default, adding a new form template) — it reuses the Report Templates module's existing keys rather than introducing new ones. There is no per-business-unit routing rule in the replacement, so there is nothing analogous to test for allow/deny BU precedence — see [Report Templates — Permissions](/en/platform/report-templates/permissions).

## 5. References

- carmen-turborepo-backend-v2 commit `c135bb21e` — removal of the four keys from the permission seed and every role bundle.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` — current catalog seed (no `print_template_mapping` rows).

**Cross-links:** [Print Template Mapping landing](/en/platform/print-template-mapping) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Report Templates — Permissions](../report-templates/permissions.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md)
