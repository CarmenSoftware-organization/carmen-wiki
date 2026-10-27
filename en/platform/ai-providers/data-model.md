---
title: AI Providers — Data Model
description: The tb_ai_provider table in the backstage schema - columns, indexes, the six seeded providers, and how a business unit's Ask AI override in tb_application_config combines with it.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, ai-providers, data-model
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# AI Providers — Data Model

> **At a Glance**
> **Tables:** 1 owned (`tb_ai_provider`) + 1 referenced (`tb_application_config` key `ask_ai`, tenant side) &nbsp;·&nbsp; **Enums:** none &nbsp;·&nbsp; **Audit columns:** `doc_version`, `created_*`, `updated_*`, `deleted_*` (soft delete) &nbsp;·&nbsp; **Seed:** 6 rows inserted by the migration &nbsp;·&nbsp; **Divergences vs SPA:** none found

> **Source of truth:** Backend Prisma backstage schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` (`model tb_ai_provider`)
> - `.../prisma/migrations/20261027120000_add_ai_provider/migration.sql`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The module owns a single, flat table in the **backstage (system) database**, not in any tenant database. It has no foreign keys. The tenant-side counterpart is not a table of its own: each business unit stores its overrides as one JSON value in the tenant's `tb_application_config` row whose `key` is `ask_ai` (§2.2).

## 2. Entities

### 2.1 `tb_ai_provider`

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| **Identity** | | | |
| `id` | `String @id @db.Uuid` (`gen_random_uuid()`) | No | Primary key. |
| `code` | `String @db.VarChar(50)` | No | Stable machine key, e.g. `claude`. Referenced by BU overrides. Immutable after create. |
| `label` | `String @db.VarChar(100)` | No | Display name. |
| `seed_key` | `String? @db.VarChar(100)` | Yes | Identity of rows owned by the seed (`db:seed.ai-provider`); `NULL` for rows created in the UI. |
| **Presentation** | | | |
| `icon_key` | `String? @db.VarChar(30)` | Yes | Built-in icon: `claude`, `chatgpt`, `gemini`, `deepseek`, `grok`, `google`. |
| `icon_url` | `String? @db.VarChar(500)` | Yes | https icon; takes precedence over `icon_key` in the UI. |
| `sort_order` | `Int @default(0)` | No | Menu order (ascending). New rows in the UI default to current max + 10. |
| **Behaviour** | | | |
| `url_template` | `String @db.VarChar(500)` | No | https URL; `{query}` is replaced with the encoded prompt. |
| `default_prompt` | `String @db.Text` | No | Prompt used when a BU has no override. `{items}` marks where the item table goes. |
| `is_active` | `Boolean @default(true)` | No | Inactive rows are hidden from every BU. |
| `default_enabled_for_bu` | `Boolean @default(false)` | No | Whether a BU that never chose sees the provider. |
| **Audit** | | | |
| `doc_version` | `Int @default(0)` | No | Optimistic-lock counter, incremented per update. |
| `created_at` / `created_by_id` | `DateTime? @db.Timestamptz(6)` / `String? @db.Uuid` | Yes | Creation audit. |
| `updated_at` / `updated_by_id` | same | Yes | Last update audit. |
| `deleted_at` / `deleted_by_id` | same | Yes | Soft delete; queries filter `deleted_at: null`. |

**Constraints and indexes**

- `@@unique([code, deleted_at], map: "ai_provider_code_u")` and `@@index([sort_order], map: "idx_ai_provider_sort_order")` (declared in Prisma).
- Two **partial unique indexes** exist only in the migration SQL (Prisma cannot declare them): `uq_ai_provider_seed_key` on `(seed_key) WHERE seed_key IS NOT NULL`, and `ai_provider_code_live_u` on `(code) WHERE deleted_at IS NULL`. The second is what actually prevents two live rows with the same `code`, because the composite unique does not stop duplicate `NULL deleted_at`. The service also checks for a duplicate before inserting.

**Seeded rows** (migration `INSERT`, idempotent): `claude`, `chatgpt`, `gemini`, `deepseek`, `grok`, `google` (label "Google Search"). `claude`, `chatgpt` and `google` use a `{query}` template; `gemini`, `deepseek` and `grok` use a plain URL, so those open without a pre-filled prompt. Source of truth for the rows is `prisma/seed.ai-provider.data.ts`.

### 2.2 BU override (referenced, tenant side)

Stored at `tb_application_config` where `key = 'ask_ai'`:

```
value = { providers: { <code>: { enabled?: boolean, prompt?: string } } }
```

Parsing is defensive (`parseAskAiBuConfig`): non-object shapes yield an empty config, a blank `prompt` is dropped. Resolution rules for one provider and one BU:

```
visible  = provider.is_active AND (override.enabled ?? provider.default_enabled_for_bu)
prompt   = override.prompt OR provider.default_prompt
```

The generic `/api/config/:bu_code/:key` routes refuse the `ask_ai` key; it is only writable through `PUT /api/config/:bu_code/ask-ai`.

## 3. Relationships

None. `tb_ai_provider.code` is a soft reference from the JSON override; there is no FK and nothing cascades when a provider is deleted (overrides stay, ignored).

## 4. Enums

None in this module. The icon list is a closed string set enforced in code (`AI_PROVIDER_ICON_KEYS`), not a database enum.

## 5. Divergences from carmen-backstage SPA shape

No divergences detected against the SPA `AiProvider` interface (`src/types/index.ts:2154`) as of 2026-10-27: same twelve fields; `AiProviderInput` omits `id`, `doc_version`, `created_at`, `updated_at`. The SPA type has no `seed_key` or `*_by_id` fields because the API does not need them in the UI. Note the gateway `findAll`/`findOne` responses are passed through as stored rows, so those extra columns are present in the payload but unused.

## 6. References

- Primary: `packages/prisma-shared-schema-backstage/prisma/schema.prisma`, migration `20261027120000_add_ai_provider`.
- Secondary: `../carmen-backstage/src/types/index.ts` (`AiProvider`, `AiProviderInput`).
- Code: `apps/micro-cluster/src/cluster/ai-provider/ai-provider.service.ts`; `apps/backend-gateway/src/config/config_ask-ai/ask-ai-resolve.ts`.
- Siblings: [AI Providers](/en/platform/ai-providers), [UI Screens](/en/platform/ai-providers/ui-screens).
