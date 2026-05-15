---
title: <Module> — Data Model
description: Entities, fields, relationships, and enums for the <module> module.
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, data-model, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# <Module> — Data Model

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview
<Entities owned by this module + brief positioning relative to neighbouring modules.>

## 2. Entities

### 2.1 <EntityName>
| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |

**Constraints:** <PK, FK, unique, indexes — verbatim from Prisma.>
**Indexes:** <`@@index` and `@@unique` declarations from Prisma.>

### 2.2 <EntityName>
<Repeat per entity owned by this module.>

## 3. Relationships
<Text diagram or bullet list of FK relationships derived from Prisma `@relation` directives. Indicate 1-to-1, 1-to-many, many-to-many cardinality.>

## 4. Enums
- **<EnumName>**: `VALUE1` / `VALUE2` / ... — meaning of each value (one bullet per enum, sourced from Prisma `enum` blocks).

## 5. Divergences from carmen/docs

When writing this page, cross-check entities, fields, and enums against the corresponding `../carmen/docs/<source>/` files. Any discrepancy goes here:

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|

If no divergences are found, replace the table with: "No divergences detected against carmen/docs as of <YYYY-MM-DD>."

## 6. References
- **Primary (source of truth):** Prisma schemas listed in the header callout.
- **Secondary (concept cross-check):** `../carmen/docs/<source-folder>/` — specific file paths.
