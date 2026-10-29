---
title: Ask AI
description: Per-business-unit settings for the "Ask AI" menu on the Purchase Request page — which AI providers are offered and the prompt each one is sent. Stored as the ask_ai row of tb_application_config; provider catalogue is owned by Backstage.
published: true
date: 2026-10-29T03:30:00.000Z
tags: system-config, ask-ai, purchase-request, configuration, carmen-software
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Ask AI

> **At a Glance**
> **Route:** `/system-admin/ask-ai` &nbsp;·&nbsp; **Storage:** key `ask_ai` in `tb_application_config` (per BU) over a platform catalogue of AI providers (`tb_ai_provider`, managed in Backstage) &nbsp;·&nbsp; **Endpoints:** `GET`/`PUT api/config/:bu_code/ask-ai` (settings), `GET api/:bu_code/ask-ai/providers` (what the PR page consumes) &nbsp;·&nbsp; **Permission:** `system_admin.business_unit` `view` / `update` + nav licence `system_admin` &nbsp;·&nbsp; **Consumer:** the **Ask AI** button on [purchase-request](/en/inventory/purchase-request) item lines (`pr-ask-ai-menu.tsx`).

## 1. What & Who

The PR page has an **Ask AI** dropdown. Picking a provider builds a prompt from the provider's template plus a table of the PR's items (`#`, item name with local name, quantity and unit, quoted price with currency) and opens the provider's site in a new tab with the prompt pre-filled. The warehouse name is deliberately not sent (`build-pr-ai-query.ts`). Nothing is sent from Carmen's servers — the browser opens the provider URL.

This screen lets a Sysadmin decide, **for their own BU**, which of the platform's active providers appear and what prompt each uses. **Maintained by** Sysadmin; **provider catalogue** (label, icon, URL template, default prompt, default-enabled flag, sort order) by the platform operator in Backstage ([AI providers](/en/backstage/ai-providers)).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| See providers and their effective state | Ask AI → one compact row per active provider | A BU that never saved sees the platform defaults |
| Turn a provider on/off for this BU | **Edit** → row switch → **Save** | Without an override the provider follows `default_enabled_for_bu` |
| Override a provider's prompt | **Edit** → expand a row (one at a time) → prompt text | Empty = use the platform `default_prompt`; the row shows the prompt actually in effect |
| Use the item table at a chosen place in the prompt | Put `{items}` in the prompt | Without `{items}` the table is appended after a blank line |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| 422 on save | Unknown provider code, or prompt longer than 4000 characters (`PROMPT_MAX`, `config_ask-ai.service.ts:18`) | Reload the page; shorten the prompt |
| Ask AI button missing on the PR page | No provider is effective-enabled for the BU (`providers.length === 0` hides the menu) | Enable a provider here |
| Prompt copied to clipboard instead of prefilled | Provider URL template has no `{query}`, or the filled URL exceeds 8000 characters (`MAX_URL_LENGTH`) | Paste the prompt manually; a toast confirms the copy |
| Nothing opens | The resolved URL does not start with `https://` (the menu refuses it) | Fix the provider's URL template in Backstage |
| Generic app-config route refuses `ask_ai` | The key is managed only by this endpoint (`rejectAskAiKey`, `config_app-config.controller.ts:73`); it is also hidden from `GET /app-config` | Use `/ask-ai` |

## 4. Edge Cases

- **Disabled providers keep their override.** Saving never deletes the stored values of a provider that the platform has since deactivated (BE `7f7fe0843`); a `null` or empty string for `enabled` / `prompt` removes just that field.
- **BU isolation.** The controller requires the `bu_code` in the path to match the caller's context (`BuCodePathQueryMatchGuard`) — fixed in `7f7fe0843` after a cross-tenant gap.
- **Replace-all save.** `PUT` replaces the whole override block; the FE sends only providers whose draft differs from the loaded state (`buildSaveBody`).

---

## 5. Data Shape (Dev)

```
tb_application_config  key = "ask_ai"
{
  "providers": {
    "<provider code>": { "enabled": true|false, "prompt": "text" }   // both optional
  }
}

GET api/config/:bu_code/ask-ai  ->  items[{ code, label, icon_key, icon_url, sort_order,
                                            default_prompt, default_enabled_for_bu,
                                            bu_enabled|null, bu_prompt|null }]   (active providers only)
GET api/:bu_code/ask-ai/providers -> [{ code, label, icon_key, icon_url, url_template, prompt }]
   effective = is_active AND (bu.enabled ?? default_enabled_for_bu);  prompt = bu.prompt || default_prompt
```

Source: `apps/backend-gateway/src/config/config_ask-ai/ask-ai-resolve.ts`.

## 6. Business Rules

- Only `is_active` platform providers are listed or offered.
- Effective enablement and prompt follow the override-then-default rule above.
- Writes need `system_admin.business_unit.update` and the `askAi.saveConfig` App ID; reads need `.view` and `askAi.getConfig` (`config_ask-ai.controller.ts:57-90`).

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) — where the menu appears.
- [system-config/application-config](/en/inventory/system-config/application-config) — the `ask_ai` key lives in this store but is not writable through its generic routes.

## 8. References

- **Gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_ask-ai/` (controller, service, `ask-ai-resolve.ts`); `src/application/ask-ai/` (providers for the PR page).
- **Schema:** `packages/prisma-shared-schema-backstage/prisma/schema.prisma` (AI providers, comment at line 1259); seed `seed.ai-provider.data.ts`.
- **Frontend:** `../carmen-frontend/routes/system-admin/ask-ai/` (`ask-ai-component.tsx`, `ask-ai-provider-card.tsx`, `use-ask-ai-config.ts`); `routes/procurement/purchase-request/ai/` (`pr-ask-ai-menu.tsx`, `build-pr-ai-query.ts`, `use-ask-ai-providers.ts`); nav `constant/module-list.ts:793-799`.
- **Licence:** `config:ask-ai` → `configuration.app_config` (`permission.route-map.ts:94`).
