---
title: AI Providers
description: Platform-wide catalog of "Ask AI" providers (Claude, ChatGPT, Gemini, ...) with the default prompt and link template that the Purchase Request page uses, editable from one dialog-driven list screen.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, ai-providers
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# AI Providers

The **AI Providers** module is the platform-owned catalog behind the "Ask AI" button on the Purchase Request page. Each row is one external assistant (Claude, ChatGPT, Gemini, DeepSeek, Grok, Google Search): its display name, icon, the URL the button opens, and the **default prompt** that gets sent or copied. The catalog used to be hard-coded in the inventory frontend; migration `20261027120000_add_ai_provider` moved it into `tb_ai_provider` and seeded the six defaults. Platform staff edit it here once and the change applies to every business unit, while each BU can still opt providers in/out and override the prompt on its own side.

> **At a Glance**
> **Screen:** `AiProviderManagement` (+ `AiProviderEditDialog`) &nbsp;·&nbsp; **Route:** `/purchase-request-ai-providers` (old `/ai-providers` redirects to it, `App.tsx:400`) &nbsp;·&nbsp; **Nav:** group `navGroup.ai`, `permission: 'ai_provider.read'`, `feature: 'ai_providers'` (`backstageNav.ts:57`) &nbsp;·&nbsp; **Permission keys:** `ai_provider.read` / `.create` / `.update` / `.delete` &nbsp;·&nbsp; **API:** `/api-system/ai-providers` &nbsp;·&nbsp; **Table:** `tb_ai_provider` &nbsp;·&nbsp; **Sub-pages:** 2 &nbsp;·&nbsp; **e2e suite:** none (`../carmen-backstage-e2e` has no ai-provider spec)

## 1. Overview

One list screen, one create/edit dialog. There is no detail route and no separate edit page. The list shows every provider **including inactive ones** (the gateway always asks micro-cluster with `include_inactive: true`, `backstage_ai-providers.service.ts` `findAll`), sorted by `sort_order`. The page is deliberately small because the catalog is small: six seeded rows, edited rarely.

Two things make the module worth documenting beyond its CRUD shape:

- **The `{query}` placeholder decides how the button behaves for end users.** A `url_template` containing `{query}` opens the provider with the prompt pre-filled; a template without it just opens the provider and the user pastes a prompt that was copied to the clipboard. The list's "Opens" column shows which of the two applies (§3.2).
- **Changes are global.** The page subtitle reads "Changes apply to every business unit." Deleting a provider hides it everywhere; per-BU settings are kept but ignored (delete dialog text).

## 2. Business Context: who consumes this table

| Consumer | Route | What it does |
|---|---|---|
| Purchase Request "Ask AI" menu | `GET /api/:bu_code/ask-ai/providers` (`application/ask-ai/ask-ai.controller.ts:20,35`) | Returns the providers usable by that BU: active, and `bu override enabled ?? default_enabled_for_bu`; prompt = BU override or `default_prompt` (`resolveBuProviders`, `config_ask-ai/ask-ai-resolve.ts`). No `@Permission` on purpose, so a role with only `view_department` still sees the menu. |
| BU Ask AI settings | `GET/PUT /api/config/:bu_code/ask-ai` (`config_ask-ai.controller.ts:42`) | Lists **active** providers with the BU's override (`bu_enabled`, `bu_prompt`); saving stores `{ providers: { <code>: { enabled?, prompt? } } }` under `tb_application_config` key `ask_ai`. Gated by `system_admin.business_unit` `view`/`update`. Overrides of inactive providers are preserved on save so re-activating a provider restores the BU's choice. |

The prompt text supports an `{items}` token where the item table is injected; without it the table is appended after a blank line (dialog hint `fieldPromptHint`).

## 3. Key Concepts

### 3.1 Provider fields

Full table in [Data Model](/en/platform/ai-providers/data-model). In short: `code` (immutable key), `label`, optional icon (`icon_key` from a closed list **or** an `icon_url`, the URL wins), `url_template`, `default_prompt`, `is_active`, `default_enabled_for_bu`, `sort_order`.

### 3.2 Validation (server side)

Enforced in micro-cluster (`ai-provider.validation.ts`) and only partly mirrored in the dialog (code pattern, prompt length, required fields, integer sort order):

| Rule | Value |
|---|---|
| `code` | `^[a-z0-9][a-z0-9_-]{1,49}$` (2-50 chars); required on create, **not accepted on update** |
| `label` | 1-100 characters |
| `icon_key` | one of `claude`, `chatgpt`, `gemini`, `deepseek`, `grok`, `google`, or `null` |
| `icon_url` | `https` only, no username/password, max 500 chars |
| `url_template` | `https` only, no credentials, max 500 chars; `{query}` allowed **only after the first `?` or `#`** |
| `default_prompt` | required on create; max 4000 characters |
| `is_active`, `default_enabled_for_bu` | boolean |
| `sort_order` | integer (dialog additionally requires `>= 0`) |

### 3.3 Optimistic locking

`PATCH` carries `doc_version`. The micro-cluster update puts `doc_version` inside the write's `where`, so a stale value matches zero rows and answers `ALREADY_EXISTS` ("AI provider was modified", surfaced as 409). The dialog handles that by showing the standard version-conflict toast, closing, and reloading the list. If `doc_version` is omitted the write is **not** guarded (`docVersion != null` check, `ai-provider.service.ts`); the SPA always sends it.

## 4. Permissions

Gate is the standard backstage RBAC story, with no module-specific twist:

| Where | Check |
|---|---|
| Route + sidebar | `ai_provider.read` plus feature flag `ai_providers` (default state `active`, `featureFlags.ts:66`) |
| "Add provider" button | `<Can permission="ai_provider.create">` |
| Row Edit / Delete | `<Can permission="ai_provider.update">` / `ai_provider.delete` |
| API read | `ai_provider.read` via `BackstagePermissionGuard` |
| API create / update / delete | the write key **plus** `BackstageWidePermissionGuard`, which rejects cluster-scoped grants: only super-admins or a backstage-wide grant pass (`backstage-wide-permission.guard.ts`) |

All SPA checks pass `BACKSTAGE_SCOPED_RECORD` because the record belongs to no cluster.

**Default roles** (`seed.backstage-role-permission.data.ts`): Backstage Admin holds `ai_provider.*`; Support Manager and Support Staff hold `ai_provider.read` only (they see the list but no buttons); Security Officer holds none and gets `<Forbidden>` at the route.

## 5. Edge Cases

| Case | Behaviour |
|---|---|
| Create with a `code` already used by a live row | 409 "AI provider code already exists". A soft-deleted row's code can be reused (partial unique index `ai_provider_code_live_u`). |
| Edit code | Field is disabled in edit mode; server ignores `code` on update. |
| Template has `{query}` before the `?`/`#` | Rejected (400). Dialog shows only a live preview, not this rule, so the error arrives from the server. |
| Prompt over 4000 chars | Save button disabled (counter turns red); server also rejects. |
| `icon_url` set and `icon_key` set | `icon_url` is displayed; `icon_key` kept in the row. |
| Set `is_active` to false | Provider vanishes from every BU's menu and from the BU settings page; stored BU overrides survive. |
| Delete | Soft delete (`deleted_at`, `deleted_by_id`); row no longer listed. |

## 6. Sub-pages

- [Data Model](/en/platform/ai-providers/data-model) - `tb_ai_provider` columns, indexes, seed rows, the BU override shape.
- [UI Screens](/en/platform/ai-providers/ui-screens) - list columns, the edit dialog sections, delete confirm, responsive behaviour.

## 7. References

- SPA: `../carmen-backstage/src/pages/AiProviderManagement.tsx`, `src/pages/aiProviders/AiProviderEditDialog.tsx`, `src/services/aiProviderService.ts`, `src/types/index.ts` (`AiProvider`, line 2154).
- Gateway: `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage_ai-providers/backstage_ai-providers.controller.ts` (`@Controller('api-system/ai-providers')`, line 39).
- Micro-service: `apps/micro-cluster/src/cluster/ai-provider/{ai-provider.service.ts,ai-provider.validation.ts}`.
- Schema: `packages/prisma-shared-schema-backstage/prisma/schema.prisma` (`model tb_ai_provider`) and migration `20261027120000_add_ai_provider`.
- Related: [Business Units](/en/platform/business-units), [Feature Flags](/en/platform/feature-flags).
