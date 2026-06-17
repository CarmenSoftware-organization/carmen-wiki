# Design: Master Configuration Umbrellas

**Date:** 2026-05-16
**Status:** Approved (user)
**Scope:** Documentation of ~29 master/configuration entities organized into 4 umbrella modules
**Predecessors:** the 12 transactional/master modules in `en/` already completed

This spec defines four new umbrella modules to document the master data and configuration entities that the existing 12 transactional modules depend on (units, departments, vendors, workflows, RBAC, reporting infrastructure, etc.). Treatment is **lighter than transactional modules** — each entity gets a single reference page, not the four-sub-page persona-axis treatment.

---

## 1. Goal

Give developers and testers a single place to find documentation for each master/config entity in Carmen — what it is, what it stores (Prisma), where it's used, who manages it, and the rules governing its lifecycle. Eliminate the implicit knowledge required to navigate the dozens of `tb_*` tables that aren't owned by any transactional module.

## 2. Umbrella Modules

Four umbrellas organized by audience and concern. Each umbrella is a sibling of the 12 existing modules under `en/`.

| Slug | Purpose | Audience | Entities |
|------|---------|----------|----------|
| `master-data` | Business master data referenced by transactional documents | Product Admin, Purchaser, Configurator | 13 |
| `system-config` | Document-flow and accounting-period system configuration | Sysadmin | 6 |
| `access-control` | Users, roles, permissions, multi-BU access | Sysadmin, Security Officer | 5 |
| `reporting-audit` | Activity log, attachments, notifications, reporting, dashboards | Auditor, Sysadmin | 5 |

Total: **29 entity pages + 4 umbrella `index.md` = 33 new files**, EN only.

## 3. Entity Assignment

### 3.1 `master-data/` (13 entities)

| Entity (page slug) | Prisma table(s) | One-line purpose |
|--------------------|-----------------|------------------|
| `unit` | `tb_unit`, `tb_unit_conversion` | Units of measure (kg, pcs, box) + conversion factors |
| `department` | `tb_department`, `tb_department_user` | Departments and the users assigned to them |
| `location` | `tb_location` | Warehouses, outlets, and storage locations |
| `delivery-point` | `tb_delivery_point` | Receiving points for PO delivery |
| `business-unit` | `tb_business_unit` (platform), `tb_business_unit_tb_module` (platform) | Tenant business unit — owns `calculation_method` (FIFO/avg) and module enablement |
| `currency` | `tb_currency`, `tb_currency_iso` (platform), `tb_exchange_rate` | Currencies + ISO codes + exchange rates |
| `vendor` | `tb_vendor`, `tb_vendor_address`, `tb_vendor_contact`, `tb_vendor_business_type` | Vendor master (header + addresses + contacts + business type) |
| `tax-profile` | `tb_tax_profile` | Tax codes and tax-rule profiles |
| `credit-term` | `tb_credit_term` | Vendor payment terms (Net 30, Net 60, COD, etc.) |
| `extra-cost-type` | `tb_extra_cost`, `tb_extra_cost_type` | Cost categories (freight, duty, handling) for GRN extra-cost allocation |
| `adjustment-type` | `tb_adjustment_type` | Reason codes for inventory adjustments |
| `credit-note-reason` | `tb_credit_note_reason` | Reason codes for credit notes |
| `pricelist-template` | `tb_pricelist_template` | Templates for vendor pricelist invitations |

### 3.2 `system-config/` (6 entities)

| Entity | Prisma table(s) | One-line purpose |
|--------|-----------------|------------------|
| `workflow` | `tb_workflow` | Approval workflow definitions used by PR, PO, store-requisition, etc. |
| `period` | `tb_period`, `tb_period_snapshot` | Accounting periods + period-end snapshots |
| `dimension` | `tb_dimension`, `tb_dimension_display_in` | Cost-centre dimensions for journal allocation |
| `running-code` | `tb_config_running_code` | Document-number sequencing per document type |
| `application-config` | `tb_application_config`, `tb_application_user_config` | Global app config + per-user preferences |
| `menu` | `tb_menu` | Application menu structure (not recipe menu) |

### 3.3 `access-control/` (5 entities)

| Entity | Prisma table(s) | One-line purpose |
|--------|-----------------|------------------|
| `user` | `tb_user` (platform), `tb_user_profile` (platform), `tb_password` (platform), `tb_user_login_session` (platform) | User account, profile, password, session |
| `application-role` | `tb_application_role` (platform), `tb_application_role_tb_permission` (platform), `tb_user_tb_application_role` (platform) | Role definitions and user-role assignments |
| `permission` | `tb_permission` (platform) | Permission atoms used in role definitions |
| `business-unit-user` | `tb_user_tb_business_unit` (platform), `tb_user_business_unit_role` enum (platform), `tb_temp_bu_user` (platform) | Per-business-unit access and roles |
| `user-location` | `tb_user_location` | Per-user location scoping inside a business unit |

### 3.4 `reporting-audit/` (5 entities)

| Entity | Prisma table(s) | One-line purpose |
|--------|-----------------|------------------|
| `activity` | `tb_activity` | Global activity / audit log |
| `attachment` | `tb_attachment` | Generic file attachment storage |
| `notification` | `tb_notification` (platform), `tb_message_format` (platform), `tb_news` (platform) | In-app notifications, message templates, news posts |
| `report` | `tb_report_job`, `tb_report_schedule`, `tb_report_template` (platform), `tb_print_template_mapping` (platform) | Report jobs + schedules + templates |
| `widget` | `tb_widget_dashboard`, `tb_widget_default_layout`, `tb_widget_workspace` | Dashboard widget definitions + layouts |

## 4. Per-Entity Page Template

Each of the 29 entity pages follows the template below. Substitute the entity name and content from sources. Frontmatter date `2026-05-16T08:00:00.000Z` for the whole batch.

```markdown
---
title: <Entity Title>
description: <one-line>
published: true
date: 2026-05-16T08:00:00.000Z
tags: <umbrella-slug>, <entity-slug>, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# <Entity Title>

## 1. Purpose
<1-2 paragraphs: what this entity stores, where it fits in the system, why developers and testers need to know about it.>

## 2. Prisma Model(s)
<Source: ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant or .../platform>

### 2.1 <table_name>
| Field | Prisma Type | Nullable | Description |

**Constraints:** <PK, FK, uniques, indexes — verbatim from Prisma>

<Repeat sub-section per table if the entity has multiple tables, e.g. vendor has 4.>

## 3. Usage / Cross-References
<Which transactional modules reference this entity. Use bullet list with [[slug]] cross-links to the 12 transactional modules.>
- [[<module>]] — how it uses this entity (FK column, lookup, validation)

## 4. Configuration UI
<Which screen / module manages this. Who has the role to edit it (Product Admin / Sysadmin / etc.).>

## 5. Business Rules
<Key rules:>
- Uniqueness (which fields, scope — global / per-BU / per-department)
- Deletion guards (cannot delete if referenced by N+ transactions)
- Validation rules at create / edit
- Lifecycle (active/inactive flags, soft delete)

## 6. References
- **Prisma:** specific file path + line numbers
- **Frontend route (if known):** `../carmen-inventory-frontend-react/routes/<route>/`
- **carmen/docs (if applicable):** specific file path
- **Cross-module:** the modules in Section 3 that depend on this entity
```

Target length per page: **60-120 lines** (much smaller than transactional sub-pages' 200-400). Vendor will be longer due to 4 tables; simple lookups like `credit-term` will be shorter.

## 5. Umbrella `index.md` Template

Each of the 4 umbrellas has an `index.md` that orients readers and lists the entities.

```markdown
---
title: <Umbrella Title>
description: <one-line>
published: true
date: 2026-05-16T08:00:00.000Z
tags: <umbrella-slug>, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# <Umbrella Title>

## 1. Overview
<2-3 paragraphs: what this umbrella covers, who manages it, where it sits in the Carmen system.>

## 2. Audience
<Typically Sysadmin / Product Admin / Auditor. Single persona — no 4-sub-page persona-axis treatment.>

## 3. Entity List
| Entity | Purpose | Managed by |
| ------ | ------- | ---------- |
| [unit](./unit.md) | Units of measure + conversion | Product Admin |
<one row per entity>

## 4. Cross-Module Dependencies
<Which transactional modules depend on these entities. Use [[slug]] cross-links.>
- [[purchase-order]] requires vendor, currency, tax-profile, credit-term, delivery-point
- [[inventory]] requires location, unit
- etc.

## 5. References
- Prisma paths
- carmen/docs links if applicable
```

## 6. Cross-Link Slug Expansion

The valid module-slug allowlist expands from **12 to 16**:

**Existing transactional (12):** `inventory`, `costing`, `inventory-adjustment`, `good-receive-note`, `store-requisition`, `physical-count`, `spot-check`, `purchase-request`, `purchase-order`, `vendor-pricelist`, `product`, `recipe`

**New umbrella (4):** `master-data`, `system-config`, `access-control`, `reporting-audit`

Entity references use path form: `[[master-data/unit]]`, `[[system-config/workflow]]`, `[[access-control/user]]`, `[[reporting-audit/activity]]`.

## 7. File List (33 new files)

```
en/master-data/index.md
en/master-data/unit.md
en/master-data/department.md
en/master-data/location.md
en/master-data/delivery-point.md
en/master-data/business-unit.md
en/master-data/currency.md
en/master-data/vendor.md
en/master-data/tax-profile.md
en/master-data/credit-term.md
en/master-data/extra-cost-type.md
en/master-data/adjustment-type.md
en/master-data/credit-note-reason.md
en/master-data/pricelist-template.md

en/system-config/index.md
en/system-config/workflow.md
en/system-config/period.md
en/system-config/dimension.md
en/system-config/running-code.md
en/system-config/application-config.md
en/system-config/menu.md

en/access-control/index.md
en/access-control/user.md
en/access-control/application-role.md
en/access-control/permission.md
en/access-control/business-unit-user.md
en/access-control/user-location.md

en/reporting-audit/index.md
en/reporting-audit/activity.md
en/reporting-audit/attachment.md
en/reporting-audit/notification.md
en/reporting-audit/report.md
en/reporting-audit/widget.md
```

## 8. Out of Scope

- **TH translations** — EN only this round (consistent with all post-PO modules).
- **Full 4-sub-page persona-axis treatment per entity** — master/config entities are lookups and Sysadmin-managed; persona-axis split adds no value.
- **Updating the existing 12 transactional modules' Section 5 cross-links** to point at new master-data entity pages — can be done in a follow-up if desired; new master-config pages link OUTWARD to the modules they support, not the reverse.
- **Wiki.js admin sidebar/navigation configuration** — handled in admin, not in this repo.
- **carmen/docs reconciliation** — carmen/docs has very little master-config content (`settings/locations.md` is essentially the only file). Synthesis draws primarily from Prisma.

## 9. Implementation Notes

1. **Per umbrella:** create the `index.md` first, then each entity page, then commit at granularity that makes sense (likely one commit per umbrella, or per entity for the large ones).
2. **Source-of-truth discipline:** Prisma is canonical for everything. carmen/docs is too thin to be meaningful for master/config.
3. **Cross-module backward references:** entity pages MAY reference the existing 12 modules in Section 3 (Usage). Use `[[slug]]` form.
4. **Vendor is the largest entity** — 4 tables, complex relationships, business-critical. Allow ~150-200 lines.
5. **Platform vs tenant schemas:** clearly mark which schema each model belongs to in Section 2.
6. **Audience uniformity:** for umbrella index Section 2, name a small audience (Sysadmin / Product Admin / Auditor — not the broader transactional personas).
7. **Verifier:** all 33 new files must pass `.specs/verify_frontmatter.py`.
8. **Cross-link audit:** every `[[slug]]` must resolve to one of the now-16 valid module slugs (transactional 12 + umbrella 4). Entity references use path form `[[umbrella/entity]]`.

## 10. Open Questions

None at design time.
