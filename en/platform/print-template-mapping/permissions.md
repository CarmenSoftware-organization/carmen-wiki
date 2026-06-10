---
title: Print Template Mapping — Permissions
description: The print_template_mapping.* gate matrix, the resolve-time allow/deny precedence rules, and the edge-case matrix for testers — including the micro-business path that bypasses BU scoping.
published: true
date: 2026-06-10T12:45:00.000Z
tags: book/platform, print-template-mapping, permissions
editor: markdown
dateCreated: 2026-06-10T12:45:00.000Z
---

# Print Template Mapping — Permissions

> **At a Glance**
> **Gate:** routes carry `print_template_mapping.read` / `.create` / `.update` on `PrivateRoute`; sidebar entry on `.read` &nbsp;·&nbsp; **In-page `<Can>` gates:** New Mapping (`.create`), row Edit (`.update`), row Delete (`.delete` — in-page only, no route), Edit toggle (`.update`) &nbsp;·&nbsp; **Second authorization story:** resolve-time BU rules — deny wins, blank allow = all, **blank `bu_code` skips BU checks entirely** &nbsp;·&nbsp; **Known gap:** micro-business's print path resolves mappings without applying the BU lists at all

## 1. Overview

Two independent authorization stories meet in this module. The first is ordinary [Platform RBAC](/en/platform/rbac): the four `print_template_mapping.*` keys (seeded in `seed.platform-permission.ts`) that decide which *humans* may see and mutate mapping rows (§2). The second is what the rows themselves encode: the **resolve-time rules** — which mapping the print pipeline picks for a given `(document_type, bu_code)` pair, governed by `is_active`, `is_default`, `display_order`, and the allow/deny BU lists (§3). A human with full `print_template_mapping.*` keys is editing routing data whose enforcement happens entirely server-side at print time; conversely, no RBAC key ever influences which template a document prints with.

## 2. Gate matrix

All gates resolve through the single `hasPermission` resolver documented in [Platform RBAC — Permissions](../rbac/permissions.md); a failed route guard renders `<AccessDenied>` inside the normal `<Layout>` shell.

| Surface | Mechanism | Key | Source |
|---|---|---|---|
| `/print-template-mapping` | `PrivateRoute requiredPermission` | `print_template_mapping.read` | `src/App.tsx` |
| `/print-template-mapping/new` | `PrivateRoute requiredPermission` | `print_template_mapping.create` | `src/App.tsx` |
| `/print-template-mapping/:id/edit` | `PrivateRoute requiredPermission` | `print_template_mapping.update` | `src/App.tsx` |
| Sidebar "Print Mapping" (Content group, Printer icon) | `Layout.tsx` nav filter | `print_template_mapping.read` | `src/components/Layout.tsx` |
| New Mapping (list header) | `<Can>` | `print_template_mapping.create` | `PrintTemplateMappingManagement.tsx` |
| Row Edit (inline pencil button) | `<Can>` | `print_template_mapping.update` | `PrintTemplateMappingManagement.tsx` |
| Row Delete (inline trash button) | `<Can>` | `print_template_mapping.delete` | `PrintTemplateMappingManagement.tsx` |
| Edit toggle (edit-page header) | `<Can>` | `print_template_mapping.update` | `PrintTemplateMappingEdit.tsx` |

Tester-relevant asymmetries, mirroring the Applications module:

- **`.delete` is in-page only.** No route requires it and the edit page has no delete action — the key's entire surface is the list row's trash button. A `.read`-only session sees the grouped list with empty action cells.
- **Save is not separately gated.** Only the Edit *toggle* is `<Can>`-wrapped; the Save/Cancel row renders only in edit mode, which is unreachable without the toggle (create mode sits behind the route's `.create`). Backend enforcement on `PUT` remains the real boundary.
- **No ungated empty-state CTA.** Unlike Applications, the empty list shows plain text, not a button — there is no affordance leak for `.create`-less sessions.
- **Route keys are independent.** `PrivateRoute` checks one key each: `.update` alone deep-links to `/print-template-mapping/:id/edit` while the list denies; `.create` alone reaches `/print-template-mapping/new` by URL.
- The sidebar filter is UX, not security — a session lacking `.read` can still type the URL and hits the route guard. Super-admin and bootstrap sessions pass every gate; never QA this matrix from one.

## 3. Resolve-time rules

The canonical runtime contract is micro-report's `Resolve` (`db/print_template_mapping_repo.go`), exposed as `GET /api-system/print-template-mappings/resolve?document_type=X&bu_code=Y`:

```
resolve(document_type, bu_code):
    rows = mappings WHERE document_type = :document_type
                      AND deleted_at IS NULL
                      AND is_active = true
           ORDER BY is_default DESC, display_order ASC

    for row in rows:
        if permits_bu(row, bu_code):
            return row                  -- first permitted row wins
    return 404 "no active mapping found"

permits_bu(row, bu_code):
    if bu_code is blank:                return true
        -- BU lists are not consulted at all, including deny
    if bu_code in row.deny_business_unit:
                                        return false   -- deny wins, checked first
    if row.allow_business_unit is non-empty
       and bu_code not in row.allow_business_unit:
                                        return false
    return true                         -- blank allow = all BUs
```

Three consequences worth internalizing:

1. **The default flag is not absolute.** Ordering puts the default first, but if its BU lists reject the caller, resolution *falls through* to the next permitted row by `display_order` — a BU can effectively have a different "default" than everyone else.
2. **Deny beats allow**, including when the same code appears in both lists on one row.
3. **A blank `bu_code` bypasses BU scoping entirely** — even deny lists. Callers that omit `bu_code` always get the globally-first row.

**The bypass in practice:** micro-business's shared print helper (`renderViaMicroReport` in `apps/micro-business/src/common/print-report.helper.ts`) — the path behind the actual Print buttons in eight document services: PO, GRN, SR, CN (credit note), IA (inventory adjustment), PC (physical count), SC (spot check), and RFQ (request for pricing), with PR inlining the same query — does **not** call the resolve endpoint. It queries `tb_print_template_mapping` directly via Prisma with the same `is_default DESC, display_order ASC` ordering and active/non-deleted filters, **but applies no allow/deny check whatsoever**, even though it has the `bu_code` in hand (used only to address micro-report's viewer URL). As of 2026-06-10, BU scoping on mappings is therefore honoured by the `resolve` endpoint but **ignored by the main document-print flow**. Test plans should not assume per-BU template routing works end-to-end until that consumer adopts the resolve semantics.

## 4. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Two rows saved `is_default = true` for one document type | The UI never blocks it; the Go service runs `EnsureSingleDefault` after each create/update, demoting the *other* defaults — last save wins | Best-effort only: a demotion failure just logs a warning, and direct DB writes bypass it entirely. With duplicates present, `resolve` still works — `display_order ASC` tie-breaks |
| 2 | BU code present in both allow and deny on the same row | Denied — deny is checked first | The same precedence as `tb_report_template` scoping; verify with a two-row setup so the fall-through (§3.1) is observable |
| 3 | Mapping `is_active = false` | Skipped by `resolve` and by micro-business's query; still listed in the SPA unless "Active only" is checked | Deactivation is the safe way to retire a layout while keeping the row auditable |
| 4 | No `is_default` row for a document type | `resolve` returns the lowest-`display_order` active row anyway — defaults are an ordering preference, not a requirement | The legacy Print button still prints; only the *choice* of template may surprise |
| 5 | No active mapping at all for a document type | `resolve` → 404 "no active mapping found"; micro-business returns "No active \<type\> print mapping found" and the Print action fails | The seed registers one default per supported type — a 404 in a seeded environment means someone deactivated or deleted it |
| 6 | `resolve` with an unknown/typo `bu_code` | Treated as just another string: rejected by every row with a populated allow list, permitted by blank-allow rows | BU codes in the lists are free text with no FK — a typo on either side silently changes routing rather than erroring |
| 7 | `resolve` with no `bu_code` | All BU checks skipped — even rows denying every BU are eligible | Deliberate in the Go code; flag any caller that omits `bu_code` expecting deny lists to hold |
| 8 | Blanking an allow/deny list in the SPA edit form | The SPA sends `null`; the Go update treats `null` as "not provided" and keeps the stored list | The save toasts success while the list survives — verify via the Debug Sheet or `GET :id`. Clearing requires a direct `PUT` with `[]` ([Data Model](./data-model.md) §5) |
| 9 | Create/update with an unsupported `document_type` | 400 "unsupported document_type — see GET /document-types" (the update path omits the "— see GET /document-types" suffix) | Server-side validation against the hard-coded Go list; the SPA select makes this reachable only via direct API calls |
| 10 | Mapping pointing at a soft-deleted or non-print template | The row saves and lists (with `template_name` `-` when deleted); micro-business fails at render with "Mapped template … not found" for deleted targets | No FK and a soft `kind`/`report_group` match mean the UI cannot fully prevent dangling or mismatched targets |

## 5. Recommendations

**QA matrix for resolve precedence** — run each case against a document type with two active rows (A: `is_default`, `display_order 0`; B: not default, `display_order 1`):

| Row A allow | Row A deny | `bu_code` | Expected |
|---|---|---|---|
| blank | blank | any or blank | A (default, permits all) |
| `[T01,T03]` | blank | `T01` | A |
| `[T01,T03]` | blank | `T02` | **B** — A rejects, resolution falls through |
| blank | `[T02]` | `T02` | **B** — deny wins on A |
| `[T01]` | `[T01]` | `T01` | **B** — deny beats allow on A |
| `[T01]` | blank | (blank) | A — BU checks skipped entirely |
| `[T01]` | blank | unknown code | **B** if B permits, else 404 |

- **Test the two authorization stories separately.** Verify human gating with sessions holding exactly one `print_template_mapping.*` key at a time; verify routing with `resolve` calls — a passing SPA save says nothing about what prints.
- **Always exercise resolve through both paths.** The `resolve` endpoint and micro-business's inline query agree on ordering but disagree on BU scoping (§3) — any BU-scoped routing test must confirm behaviour on the real Print button, not just the endpoint.
- **Probe the single-default demotion.** Save row B as default, re-fetch row A, and confirm it was demoted; then induce the race (two concurrent saves) and confirm the survivor matches the audit columns.
- **Audit the BU lists against the BU registry.** Codes are free text — periodically diff list contents against `tb_business_unit.code`, since a renamed BU silently falls out of every allow list it appears in.
- **Treat the SPA's blank-list save as a known trap.** Until the update path interprets `null` as "clear", document the `PUT` with `[]` workaround in runbooks rather than filing duplicate defects.

**References:** `../carmen-platform/src/App.tsx` (the three route guards) · `src/components/Layout.tsx` (sidebar entry) · `src/pages/PrintTemplateMappingManagement.tsx` / `PrintTemplateMappingEdit.tsx` (`<Can>` gates) · `../micro-report/db/print_template_mapping_repo.go` (`Resolve`, `mappingPermitsBU`, `EnsureSingleDefault`) · `../micro-report/controller/print_template_mapping_controller.go` (validation, 404/400 paths) · `../carmen-turborepo-backend-v2/apps/micro-business/src/common/print-report.helper.ts` (the BU-scoping bypass) · `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.ts` (the four keys).
**Cross-links:** [Print Template Mapping landing](/en/platform/print-template-mapping) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md)
