# Master Configuration Umbrellas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 4 new umbrella modules under `en/` (`master-data`, `system-config`, `access-control`, `reporting-audit`) documenting 29 master/config Prisma entities as reference pages, plus 4 umbrella `index.md` files. EN only.

**Architecture:** Each entity gets a single 6-section reference page (Purpose / Prisma / Usage / Configuration UI / Business Rules / References) — much lighter than the 4-sub-page persona-axis treatment used for transactional modules. Each umbrella has an `index.md` listing its entities and their cross-module dependencies. One subagent dispatch per umbrella creates the index + all entity pages + commits incrementally.

**Tech Stack:** Markdown only. Frontmatter verifier at `.specs/verify_frontmatter.py`. Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main` (user-approved direct commits).

**Reference spec:** `.specs/2026-05-16-master-config-design.md`

---

## Common Context

### Sources

**Prisma (primary, source of truth for every entity):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (tenant models)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (platform models — RBAC, business-unit, currency-iso, notification, news, report-template, message-format, etc.)

Mark each entity's Section 2 with which schema (tenant vs platform) its tables live in.

**carmen/docs (very thin):**
- `../carmen/docs/settings/locations.md` — only for `master-data/location`
- `../carmen/docs/workflow-permissions-system.md` — only for `system-config/workflow` (and `access-control/*` may reference)

For everything else, Prisma is the only source.

### Module-level substitutions per umbrella

| Umbrella slug | Title | Description (one-line) | Audience |
|---------------|-------|------------------------|----------|
| `master-data` | Master Data | Business master data referenced by transactional documents — units, departments, vendors, currencies, tax profiles, etc. | Product Admin, Configurator |
| `system-config` | System Configuration | Document-flow and accounting-period system configuration — workflow, period, dimensions, numbering. | Sysadmin |
| `access-control` | Access Control | Users, roles, permissions, multi-business-unit access. | Sysadmin, Security Officer |
| `reporting-audit` | Reporting and Audit | Activity log, attachments, notifications, reporting, dashboards. | Auditor, Sysadmin |

### Common frontmatter timestamp

Use `2026-05-16T08:00:00.000Z` for both `date` and `dateCreated` on every new file.

### Per-entity tag format

`<umbrella-slug>, <entity-slug>, configuration, carmen-software`

### Per-umbrella-index tag format

`<umbrella-slug>, configuration, carmen-software`

### Cross-link discipline

Valid module slugs expand from 12 to 16:
- Existing 12 transactional: `inventory`, `costing`, `inventory-adjustment`, `good-receive-note`, `store-requisition`, `physical-count`, `spot-check`, `purchase-request`, `purchase-order`, `vendor-pricelist`, `product`, `recipe`
- New umbrella 4: `master-data`, `system-config`, `access-control`, `reporting-audit`

Entity references use path form: `[[master-data/unit]]`, `[[system-config/workflow]]`, etc.

### Per-task verification

After writing each batch (one umbrella), the implementer subagent runs:
```bash
for f in en/<umbrella-slug>/index.md en/<umbrella-slug>/*.md; do
  python3 .specs/verify_frontmatter.py "$f"
done
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/<umbrella-slug>/ && echo "FAIL" || echo "OK: no placeholders"
grep -hRn '\[\[' --include='*.md' en/<umbrella-slug>/ | grep -o '\[\[[^]]*\]\]' | sort -u
```

Expected per umbrella: N+1 OK lines (N entities + 1 index), no placeholders, only valid 16-slug or `<slug>/<entity>` cross-links.

### Per-entity page template (canonical, reused in every entity page)

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
<Source: tenant or platform schema — mark clearly.>

### 2.1 <table_name>
| Field | Prisma Type | Nullable | Description |

**Constraints:** <PK, FK, uniques, indexes — verbatim from Prisma>

<Repeat sub-section per table if the entity groups multiple tables.>

## 3. Usage / Cross-References
- [[<module>]] — how it uses this entity (FK column, lookup, validation)

## 4. Configuration UI
<Which screen / module manages this. Who has the role.>

## 5. Business Rules
<Uniqueness, deletion guards, validation rules, lifecycle.>

## 6. References
- **Prisma:** specific file path + approximate line range
- **Frontend route (if known):** `../carmen-inventory-frontend/app/<route>/`
- **carmen/docs (if applicable):** specific file path
- **Cross-module:** the modules from Section 3
```

### Per-umbrella `index.md` template

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
<2-3 paragraphs.>

## 2. Audience
<Single persona — Sysadmin / Product Admin / etc.>

## 3. Entity List
| Entity | Purpose | Managed by |
| ------ | ------- | ---------- |
| [unit](./unit.md) | Units of measure + conversion | Product Admin |
<one row per entity in this umbrella>

## 4. Cross-Module Dependencies
- [[<module>]] requires <entity>, <entity>, ...
<one bullet per transactional module that depends on this umbrella's entities>

## 5. References
- Prisma paths (tenant + platform as applicable)
- carmen/docs links if applicable
```

---

## File Structure

**Created files: 33 total across 4 umbrellas.** Listed per-task below.

---

## Task 1: `master-data/` umbrella (1 index + 13 entity pages = 14 files)

**Files:**
- `en/master-data/index.md`
- `en/master-data/unit.md`
- `en/master-data/department.md`
- `en/master-data/location.md`
- `en/master-data/delivery-point.md`
- `en/master-data/business-unit.md`
- `en/master-data/currency.md`
- `en/master-data/vendor.md`
- `en/master-data/tax-profile.md`
- `en/master-data/credit-term.md`
- `en/master-data/extra-cost-type.md`
- `en/master-data/adjustment-type.md`
- `en/master-data/credit-note-reason.md`
- `en/master-data/pricelist-template.md`

**Entity → Prisma table(s) mapping** (per spec Section 3.1, repeated here for self-containment):

| Entity slug | Tables | Schema |
|-------------|--------|--------|
| `unit` | `tb_unit`, `tb_unit_conversion` | tenant |
| `department` | `tb_department`, `tb_department_user` | tenant |
| `location` | `tb_location` | tenant |
| `delivery-point` | `tb_delivery_point` | tenant |
| `business-unit` | `tb_business_unit`, `tb_business_unit_tb_module`, `enum_calculation_method` | platform |
| `currency` | `tb_currency` (tenant), `tb_currency_iso` (platform), `tb_exchange_rate` (tenant) | mixed |
| `vendor` | `tb_vendor`, `tb_vendor_address`, `tb_vendor_contact`, `tb_vendor_business_type` | tenant |
| `tax-profile` | `tb_tax_profile` | tenant |
| `credit-term` | `tb_credit_term` | tenant |
| `extra-cost-type` | `tb_extra_cost_type`, `tb_extra_cost` | tenant |
| `adjustment-type` | `tb_adjustment_type` | tenant |
| `credit-note-reason` | `tb_credit_note_reason` | tenant |
| `pricelist-template` | `tb_pricelist_template` | tenant |

**Section 3 (Usage) cross-link guidance** — for each entity, identify which of the 12 transactional modules reference it. Examples:

- `unit` → referenced by `[[product]]`, `[[recipe]]`, `[[purchase-request]]`, `[[purchase-order]]`, `[[good-receive-note]]`, `[[store-requisition]]`, `[[inventory]]`, `[[inventory-adjustment]]`
- `vendor` → `[[purchase-request]]`, `[[purchase-order]]`, `[[good-receive-note]]`, `[[vendor-pricelist]]`
- `business-unit` → `[[costing]]` (owns `calculation_method`), `[[inventory]]`, all others
- `delivery-point` → `[[purchase-order]]`, `[[good-receive-note]]`
- `tax-profile` → `[[purchase-request]]`, `[[purchase-order]]`, `[[good-receive-note]]`, `[[vendor-pricelist]]`
- `credit-term` → `[[purchase-order]]`, `[[vendor]]`
- `extra-cost-type` → `[[good-receive-note]]` (allocation by_value / by_qty / manual)
- `adjustment-type` → `[[inventory-adjustment]]`, `[[physical-count]]`, `[[spot-check]]`
- `credit-note-reason` → `[[good-receive-note]]` (credit-note flow), `[[inventory-adjustment]]`
- `pricelist-template` → `[[vendor-pricelist]]`

### Steps

- [ ] **Step 1: Read Prisma sources for all 13 entities**

```bash
grep -n -A 30 'model tb_unit\b\|model tb_unit_conversion\b\|model tb_department\b\|model tb_department_user\b\|model tb_location\b\|model tb_delivery_point\b\|model tb_currency\b\|model tb_exchange_rate\b\|model tb_vendor\b\|model tb_vendor_address\b\|model tb_vendor_contact\b\|model tb_vendor_business_type\b\|model tb_tax_profile\b\|model tb_credit_term\b\|model tb_extra_cost\b\|model tb_extra_cost_type\b\|model tb_adjustment_type\b\|model tb_credit_note_reason\b\|model tb_pricelist_template\b' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma | less

grep -n -A 30 'model tb_business_unit\b\|model tb_business_unit_tb_module\b\|model tb_currency_iso\b\|enum enum_calculation_method' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma | less
```

- [ ] **Step 2: Read the only relevant carmen/docs file**

```bash
cat ../carmen/docs/settings/locations.md
```

- [ ] **Step 3: Create directory + write `en/master-data/index.md`**

Frontmatter: title `Master Data`, description `Business master data referenced by transactional documents — units, departments, vendors, currencies, tax profiles, and related catalogs.`, tags `master-data, configuration, carmen-software`. Use the umbrella `index.md` template. Section 3 lists all 13 entities. Section 4 cross-module dependencies (the bullets above as starting material).

- [ ] **Step 4: Write the 13 entity pages**

One commit per entity (13 commits) using the per-entity template. Each commit message: `docs(master-data): add <entity-slug> (EN)` plus a one-line body. Target 60-120 lines per entity (vendor may go to 150-200 due to 4 tables).

For each entity:
- Section 2 cites Prisma table(s) with field tables.
- Section 3 lists cross-module dependencies using `[[slug]]` form.
- Section 4 names the screen/role (typically Product Admin or Configurator).
- Section 5 covers uniqueness, deletion guards, validation, active/inactive lifecycle.
- Section 6 references the Prisma file paths.

- [ ] **Step 5: Commit the index (after all 13 entities are done)**

```bash
git add en/master-data/index.md
git commit -m "docs(master-data): add umbrella index (EN)"
```

- [ ] **Step 6: Verify**

```bash
for f in en/master-data/index.md en/master-data/*.md; do python3 .specs/verify_frontmatter.py "$f"; done
grep -rn '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/master-data/ && echo "FAIL" || echo "OK: no placeholders"
grep -hRn '\[\[' --include='*.md' en/master-data/ | grep -o '\[\[[^]]*\]\]' | sort -u
```

Expected: 14 OK lines, no placeholders, only valid 16-slug or `<slug>/<entity>` cross-links.

- [ ] **Step 7: Show git log**

```bash
git log --oneline -16
```

Expected: 14 new master-data commits + 2 prior commits visible.

**DO NOT push.** Final push happens after all 4 umbrellas.

---

## Task 2: `system-config/` umbrella (1 index + 6 entity pages = 7 files)

**Files:**
- `en/system-config/index.md`
- `en/system-config/workflow.md`
- `en/system-config/period.md`
- `en/system-config/dimension.md`
- `en/system-config/running-code.md`
- `en/system-config/application-config.md`
- `en/system-config/menu.md`

**Entity → Prisma table(s) mapping:**

| Entity slug | Tables | Schema |
|-------------|--------|--------|
| `workflow` | `tb_workflow` | tenant |
| `period` | `tb_period`, `tb_period_snapshot` | tenant |
| `dimension` | `tb_dimension`, `tb_dimension_display_in` | tenant |
| `running-code` | `tb_config_running_code` | tenant |
| `application-config` | `tb_application_config`, `tb_application_user_config` | tenant |
| `menu` | `tb_menu` | tenant |

**Cross-link guidance:**
- `workflow` → `[[purchase-request]]`, `[[purchase-order]]`, `[[store-requisition]]`, `[[inventory-adjustment]]`, `[[good-receive-note]]`, `[[vendor-pricelist]]`, `[[physical-count]]`, `[[spot-check]]`
- `period` → `[[inventory]]`, `[[costing]]`, `[[good-receive-note]]`, `[[inventory-adjustment]]`
- `dimension` → `[[purchase-request]]`, `[[store-requisition]]`, `[[inventory-adjustment]]`, `[[inventory]]` (cost-centre allocation)
- `running-code` → every document module (PR, PO, GRN, SR, etc.)
- `application-config` → all modules (global config)
- `menu` → app menu structure, indirectly relevant to all modules

### Steps

- [ ] **Step 1: Read Prisma sources**

```bash
grep -n -A 30 'model tb_workflow\b\|model tb_period\b\|model tb_period_snapshot\b\|model tb_dimension\b\|model tb_dimension_display_in\b\|model tb_config_running_code\b\|model tb_application_config\b\|model tb_application_user_config\b\|model tb_menu\b' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma | less
```

- [ ] **Step 2: Read carmen/docs**

```bash
cat ../carmen/docs/workflow-permissions-system.md
```

- [ ] **Step 3: Write `en/system-config/index.md`**

Title `System Configuration`, description `Document-flow and accounting-period system configuration — workflow, period, dimensions, numbering.`, tags `system-config, configuration, carmen-software`. Audience: Sysadmin. Section 3 lists 6 entities. Section 4 cross-module dependencies.

- [ ] **Step 4: Write the 6 entity pages**

One commit per entity using template. Commit messages: `docs(system-config): add <entity-slug> (EN)`.

- [ ] **Step 5: Commit the index**

```bash
git add en/system-config/index.md
git commit -m "docs(system-config): add umbrella index (EN)"
```

- [ ] **Step 6: Verify**

```bash
for f in en/system-config/index.md en/system-config/*.md; do python3 .specs/verify_frontmatter.py "$f"; done
grep -rn '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/system-config/ && echo "FAIL" || echo "OK: no placeholders"
grep -hRn '\[\[' --include='*.md' en/system-config/ | grep -o '\[\[[^]]*\]\]' | sort -u
```

Expected: 7 OK lines, no placeholders, valid cross-links.

**DO NOT push.**

---

## Task 3: `access-control/` umbrella (1 index + 5 entity pages = 6 files)

**Files:**
- `en/access-control/index.md`
- `en/access-control/user.md`
- `en/access-control/application-role.md`
- `en/access-control/permission.md`
- `en/access-control/business-unit-user.md`
- `en/access-control/user-location.md`

**Entity → Prisma table(s) mapping** (mostly platform schema):

| Entity slug | Tables | Schema |
|-------------|--------|--------|
| `user` | `tb_user`, `tb_user_profile`, `tb_password`, `tb_user_login_session` | platform |
| `application-role` | `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role` | platform |
| `permission` | `tb_permission` | platform |
| `business-unit-user` | `tb_user_tb_business_unit`, `tb_temp_bu_user`, enum `enum_user_business_unit_role` | platform |
| `user-location` | `tb_user_location` | tenant |

**Cross-link guidance:**
- All access-control entities are referenced indirectly by every transactional module (RBAC governs every action). Surface this in `[[<umbrella>]]` cross-references at the umbrella level rather than entity-by-entity.
- `user-location` is specifically referenced by `[[inventory]]`, `[[store-requisition]]`, `[[physical-count]]`, `[[spot-check]]` for location scoping.

### Steps

- [ ] **Step 1: Read Prisma sources**

```bash
grep -n -A 30 'model tb_user\b\|model tb_user_profile\b\|model tb_password\b\|model tb_user_login_session\b\|model tb_application_role\b\|model tb_application_role_tb_permission\b\|model tb_user_tb_application_role\b\|model tb_permission\b\|model tb_user_tb_business_unit\b\|model tb_temp_bu_user\b\|enum enum_user_business_unit_role' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma | less

grep -n -A 30 'model tb_user_location\b' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma
```

- [ ] **Step 2: Read carmen/docs**

```bash
cat ../carmen/docs/workflow-permissions-system.md
```

- [ ] **Step 3: Write `en/access-control/index.md`**

Title `Access Control`, description `Users, roles, permissions, and multi-business-unit access.`, tags `access-control, configuration, carmen-software`. Audience: Sysadmin, Security Officer.

- [ ] **Step 4: Write the 5 entity pages**

One commit per entity. Commit messages: `docs(access-control): add <entity-slug> (EN)`.

- [ ] **Step 5: Commit the index**

```bash
git add en/access-control/index.md
git commit -m "docs(access-control): add umbrella index (EN)"
```

- [ ] **Step 6: Verify**

```bash
for f in en/access-control/index.md en/access-control/*.md; do python3 .specs/verify_frontmatter.py "$f"; done
grep -rn '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/access-control/ && echo "FAIL" || echo "OK: no placeholders"
grep -hRn '\[\[' --include='*.md' en/access-control/ | grep -o '\[\[[^]]*\]\]' | sort -u
```

Expected: 6 OK lines, no placeholders, valid cross-links.

**DO NOT push.**

---

## Task 4: `reporting-audit/` umbrella (1 index + 5 entity pages = 6 files)

**Files:**
- `en/reporting-audit/index.md`
- `en/reporting-audit/activity.md`
- `en/reporting-audit/attachment.md`
- `en/reporting-audit/notification.md`
- `en/reporting-audit/report.md`
- `en/reporting-audit/widget.md`

**Entity → Prisma table(s) mapping:**

| Entity slug | Tables | Schema |
|-------------|--------|--------|
| `activity` | `tb_activity` | tenant |
| `attachment` | `tb_attachment` | tenant |
| `notification` | `tb_notification`, `tb_message_format`, `tb_news` | platform |
| `report` | `tb_report_job` (tenant), `tb_report_schedule` (tenant), `tb_report_template` (platform), `tb_print_template_mapping` (platform) | mixed |
| `widget` | `tb_widget_dashboard`, `tb_widget_default_layout`, `tb_widget_workspace` | tenant |

**Cross-link guidance:**
- `activity` → referenced by every transactional module's audit chain
- `attachment` → `[[purchase-request]]`, `[[purchase-order]]`, `[[good-receive-note]]`, `[[inventory-adjustment]]`, `[[physical-count]]`, etc.
- `notification` → workflow stage transitions across all approval modules
- `report` + `widget` → dashboards and exports

### Steps

- [ ] **Step 1: Read Prisma sources**

```bash
grep -n -A 30 'model tb_activity\b\|model tb_attachment\b\|model tb_report_job\b\|model tb_report_schedule\b\|model tb_widget_dashboard\b\|model tb_widget_default_layout\b\|model tb_widget_workspace\b' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma | less

grep -n -A 30 'model tb_notification\b\|model tb_message_format\b\|model tb_news\b\|model tb_report_template\b\|model tb_print_template_mapping\b' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma | less
```

- [ ] **Step 2: Write `en/reporting-audit/index.md`**

Title `Reporting and Audit`, description `Activity log, attachments, notifications, reporting, dashboards.`, tags `reporting-audit, configuration, carmen-software`. Audience: Auditor, Sysadmin.

- [ ] **Step 3: Write the 5 entity pages**

One commit per entity. Commit messages: `docs(reporting-audit): add <entity-slug> (EN)`.

- [ ] **Step 4: Commit the index**

```bash
git add en/reporting-audit/index.md
git commit -m "docs(reporting-audit): add umbrella index (EN)"
```

- [ ] **Step 5: Verify**

```bash
for f in en/reporting-audit/index.md en/reporting-audit/*.md; do python3 .specs/verify_frontmatter.py "$f"; done
grep -rn '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/reporting-audit/ && echo "FAIL" || echo "OK: no placeholders"
grep -hRn '\[\[' --include='*.md' en/reporting-audit/ | grep -o '\[\[[^]]*\]\]' | sort -u
```

Expected: 6 OK lines, no placeholders, valid cross-links.

**DO NOT push.**

---

## Task 5: Final batch verification + push

**Files:** none — verification only.

- [ ] **Step 1: Confirm all 33 files exist across 4 umbrellas**

```bash
echo "=== master-data ===" && ls en/master-data/ | wc -l && ls en/master-data/
echo "=== system-config ===" && ls en/system-config/ | wc -l && ls en/system-config/
echo "=== access-control ===" && ls en/access-control/ | wc -l && ls en/access-control/
echo "=== reporting-audit ===" && ls en/reporting-audit/ | wc -l && ls en/reporting-audit/
```

Expected file counts: 14, 7, 6, 6 — total 33.

- [ ] **Step 2: Comprehensive frontmatter verification**

```bash
total_ok=0
total_fail=0
for umb in master-data system-config access-control reporting-audit; do
  for f in en/$umb/*.md; do
    result=$(python3 .specs/verify_frontmatter.py "$f" 2>&1)
    if echo "$result" | grep -q '^OK:'; then
      total_ok=$((total_ok + 1))
    else
      echo "$result"
      total_fail=$((total_fail + 1))
    fi
  done
done
echo ""
echo "Total OK: $total_ok"
echo "Total FAIL: $total_fail"
```

Expected: 33 OK, 0 FAIL.

- [ ] **Step 3: Placeholder scan**

```bash
grep -rn --include='*.md' '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/master-data/ en/system-config/ en/access-control/ en/reporting-audit/ && echo "FAIL" || echo "OK: no placeholders"
```

Expected: `OK: no placeholders`.

- [ ] **Step 4: Cross-link slug audit**

```bash
grep -hRn '\[\[' --include='*.md' en/master-data/ en/system-config/ en/access-control/ en/reporting-audit/ | grep -o '\[\[[^]]*\]\]' | sort -u
```

Every slug must be one of:
- Existing 12 transactional: `inventory`, `costing`, `inventory-adjustment`, `good-receive-note`, `store-requisition`, `physical-count`, `spot-check`, `purchase-request`, `purchase-order`, `vendor-pricelist`, `product`, `recipe`
- New umbrella 4: `master-data`, `system-config`, `access-control`, `reporting-audit`
- Path form: `<slug>/<entity>` where `<slug>` is one of the 16 and `<entity>` matches an existing file

Flag and fix any invalid slugs.

- [ ] **Step 5: Push**

```bash
git status
git log --oneline | head -40
git push origin main
```

Expected: clean working tree, push succeeds.

- [ ] **Step 6: Final summary report**

Report back:
- File counts per umbrella (expected 14, 7, 6, 6)
- Total verifier OK count (expected 33)
- Placeholder scan result
- Cross-link slug list with any invalid flagged
- Total commits since this round started (expected ~37)
- Push success confirmation
- Status: DONE | DONE_WITH_CONCERNS | BLOCKED
