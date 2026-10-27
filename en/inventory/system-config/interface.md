---
title: Interface (External API and POS)
description: The /system-admin/interface screen: per-BU external connections — inbound BU API key, API docs, the api/ext/v1 ap-invoices and gl-journals endpoints, and a summary of POS (Simphony / Micros 3700) settings.
published: true
date: 2026-10-27T00:00:00.000Z
tags: system-config, interface, external-api, api-key, pos, accounting-export, carmen-software
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Interface (External API and POS)

> **At a Glance**
> **Route:** `/system-admin/interface` (list) and `/system-admin/interface/:category/:brand` (detail); External lives at `/system-admin/interface/export/external` (the old `/interface/accounting/external` redirects there, `router.tsx:833-841`) &nbsp;·&nbsp; **Categories:** Accounting (Carmen GL, BlueLedgers), POS (Simphony, Micros 3700, Infrasys, Square), PMS (Opera, Protel), **Export tools** (External) &nbsp;·&nbsp; **Gating:** licence only on the page (`licenseFeature: "interface"`, no `permission` key — `module-list.ts:856-866`); the BU API key itself needs `system_admin.bu_api_key.view|update` **and** licence `interface.export.external` &nbsp;·&nbsp; **Key endpoints:** `api/config/:bu_code/bu-api-key` (manage) and `GET api/ext/v1/ap-invoices`, `GET api/ext/v1/gl-journals` (consume) &nbsp;·&nbsp; **Storage:** key in the backstage schema (`tb_bu_api_key`, `tb_external_api` allowlist); other brands are `tb_application_config` rows `interface_<category>_<brand>` &nbsp;·&nbsp; **Config storage only** — no sync or test-connection buttons.

## 1. What & Who

The Interface screen lists one row per external-system connection a business unit may use. Visibility is decided by the BU's licence chain (`interface` → `interface.<category>` → `interface.<category>.<brand>`; `interface-registry.ts`, `use-interface-entitlement.ts`): a brand not in the chain is hidden, a brand present only in `expired_features` is readable but locked, and the list never reads config for a brand the BU does not hold (the backend would answer 403 and break the page — FE `c70d9ebc`, `08e827ce`).

| Category | Brand | What the screen does | Inventory relevance |
|---|---|---|---|
| Export tools | External | **API Access** (BU API key) + **API documentation** — no form, no Save, writes no `interface_export_external` row any more | An external accounting system pulls GRN / CN / SR / SI / SO as Dr/Cr data |
| POS | Simphony, Micros 3700 | Connection / enable switch; see §6 | Switches Import POS and Sales Consumption on |
| Accounting, PMS | Carmen GL, BlueLedgers, Opera, Protel, Infrasys, Square | Plain config forms stored in `tb_application_config` | Config storage only; GL account defaults moved to the Accounting settings page |

**Used by** developers wiring an external accounting system and by QA verifying the key lifecycle and the export contract. **Maintained by** a sysadmin holding `system_admin.bu_api_key.update`.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create the BU's key | External → API Access → **Create key** | `POST api/config/:bu_code/bu-api-key`; one live key per BU (second create = 409). The raw secret is shown **once** in a dialog |
| See the key | Same card | Shows base URL, Client ID, secret as `••••••••` + last 4, created-by, last-used, Active/Inactive switch. `GET` never returns the secret; `exists: false` before the first create |
| Reveal the secret | **View** button | `POST …/reveal`; counts as an **update** permission and writes a `view` activity (`event_type: bu_api_key.reveal`) to the BU activity log every time |
| Rotate the secret | **Regenerate** (confirm dialog) | `POST …/regenerate`; same client id, **old secret dies immediately**, no grace period |
| Disable without deleting | Active switch | `PATCH …/bu-api-key { is_active }`; an inactive key is rejected with 401 on every ext call |
| Hand integrators the contract | **API documentation** section | Pre-filled curl quick start (`$CARMEN_CLIENT_SECRET` placeholder, never the real secret), `openapi.json` download, copyable link to the public `/developers/api` page (Scalar, no login, EN/TH) |

There is no delete action for the key in the UI or API (no `DELETE` route). Everything the page does is **live** — it saves on click, hence the "takes effect immediately" divider (`external-interface-form.tsx`).

## 3. Validation & Errors

| Symptom | Cause | Source |
|---|---|---|
| 403 on any `bu-api-key` call | Caller lacks `system_admin.bu_api_key.view` (GET) / `.update` (POST create, regenerate, reveal; PATCH), or the BU lacks / has an expired `interface.export.external` licence | `config_bu-api-key.controller.ts`; `permission.route-map.ts:277,302,315` |
| 409 on create | The BU already has a live key (also a unique-index race: partial unique index on `business_unit_id WHERE deleted_at IS NULL`) | `bu_api_key.service.ts` `create` |
| 404 on regenerate / reveal / PATCH | The BU has no key yet | `findLiveKey` |
| 400 `bu_code in query and path differ` | `BuCodePathQueryMatchGuard` | controller |
| 500 on create / regenerate / reveal | micro-business has no `SECRET_ENCRYPTION_KEY` (32 bytes, identical across instances) — the secret is stored hashed (for auth) **and** encrypted (for reveal) | BE `docs/external-api/accounting-export.md` |
| Reveal fails for old keys after env change | Rotating `SECRET_ENCRYPTION_KEY` breaks reveal; authentication keeps working through the hash | same |
| API Access / API documentation sections missing entirely | Caller lacks `system_admin.bu_api_key.view` — the sections are not rendered (the page itself stays reachable by licence) | `external-api-access-section.tsx` |
| Page shows "unavailable" for the key card | Licence not readable / expired: the page stays viewable (`viewableWhenExpired`) but write buttons are hidden and the key `GET` is not fired | `external-api-access-section.tsx`, FE `87a67e55` |
| Base URL shows the frontend origin | Backstage value `external_api.base_url` is empty or unreadable; FE falls back to `BACKEND_URL`/origin + `/api/ext/v1`. The gateway caches the value 60 s (10 s on failure) | `external-api-base-url.service.ts`; `use-bu-api-key.ts` `externalApiBaseUrl` |

## 4. The external read API (`api/ext/v1/*`)

### 4.1 Authentication chain

`BuApiKeyGuard` (not a user login — no `Authorization`, no `x-app-id`; the caller is a synthetic actor `external-api`) runs these checks in order (`bu-api-key.guard.ts`):

```
route has @ExternalApi(name)?            no  -> 403 "This API is not enabled"
x-client-id AND x-client-secret present? no  -> 401 "Invalid API credentials"
look up key by client_id; compare secret hash (dummy hash if id unknown -> no timing oracle)
mismatch | key inactive | BU deleted/inactive -> 401 "Invalid API credentials"   (one uniform body)
per-key rate limit: 300 requests / minute (fixed window)  -> 429
allowlist (tb_external_api, is_enabled, GET only)         -> 403 (503 until first load)
licence interface.export.external:  expired -> 403 | missing -> 403 | unresolvable -> 503
attach BU context; force query.bu_code = key's BU; throttle last_used_at (>= 60 s apart)
```

Facts a tester needs: the BU always comes from the key (any `bu_code` in the query is ignored); `HEAD` is a 403 (GET only); 403 and 429 rejections still count against the per-key quota; a global per-source-IP throttle (`RATE_LIMIT_MAX`, default 300/min) also applies, so several keys polled from one IP can hit 429 first; the allowlist refreshes every 60 s and licence revocation reaches the API within about 60 s.

### 4.2 Endpoints

| Endpoint | `api_name` (allowlist) | Documents | Dr/Cr data |
|---|---|---|---|
| `GET /api/ext/v1/ap-invoices` | `apInvoice.list` | GRN (`committed`), CN (`completed`) | One record per document, one line per GRN item / CN detail; two accounts by **role** (`debit_*` = inventory, `ap_*` = payable) because a CN flips the sides; tax amounts only (input-VAT account lives in the accounting system); CN amounts are positive |
| `GET /api/ext/v1/gl-journals` | `glJournal.list` | SR, SI, SO (`completed`) | One balanced journal per document; `side` Dr/Cr, `role` `inventory` / `adjustment` / `sr_in` / `sr_out`; `balanced` is reported, never forced |

A document is in exactly one endpoint; asking for the other endpoint's type in `doc_types` is a 400. The former `inventory-postings` endpoint (`inventoryPosting.list`) was removed and de-allowlisted by migration `20261017120000_external_api_ap_gl_export`.

**Query parameters (both endpoints, `accounting-export-query.ts`):**

| Param | Required | Default | Rule |
|---|---|---|---|
| `date_from`, `date_to` | yes | — | `YYYY-MM-DD`, inclusive, BU timezone; `date_from <= date_to`; span below 366 days |
| `date_field` | no | `document` | `document` = document date; `updated` = last update (use for incremental sync) |
| `doc_types` | no | all of the endpoint | Comma list, case-insensitive (AP: `GRN,CN`; GL: `SR,SI,SO`) |
| `page`, `perpage` | no | 1, 50 | `perpage` 1 to 200 (above = 400) |

Response: `{ data: [...], paginate: { total, page, perpage, pages } }`. Money fields are JSON numbers rounded half-up to 2 decimals; `qty`, `price`, `tax_rate`, `exchange_rate` keep stored precision. Lines with `unmapped: true` carry correct amounts but the GL / AP account mapping needs fixing in Carmen Blue (`issues` / `issue` lists the reason code, e.g. `missing_inventory_account`, `cost_not_found`).

### 4.3 What gets exported (selection rules)

| Rule | Behaviour | Source |
|---|---|---|
| Status | Only final documents: GRN `committed`; CN, SR, SI, SO `completed`. Drafts never | `export-core.service.ts` `HEADER[*].final` |
| Voided | Exported with `status: "voided"` **only if the document had posted stock** (has an inventory transaction). In practice SI / SO voided after completion; amounts are the original ones, the consumer reverses | `HEADER[*].posted`, `accounting-export.types.ts` `exportStatus` |
| Consignment | GRN / CN lines at consignment locations are dropped (and left out of totals); a document with no remaining line is not returned and not counted in `total`. SI / SO whose header location is consignment, and SR with both sides consignment, are excluded; an SR with no transfer cost layers (no stock movement) is excluded | `HEADER[*].owned` |
| Ordering | Document date, document no, doc type, id — across all requested types, paginated together | docs |
| Idempotence | Nothing is marked "exported"; consumers upsert by `(doc_type, id)` and replace all lines (mapping can change) | BE docs |

## 5. Edge Cases

- **Never put the secret in a test fixture, log or query cache.** The FE holds a revealed secret only in component state and drops it when the dialog closes (`useSecretMutation`, `gcTime: 0`); the backend never logs it, and the guard deletes `x-client-secret` from `request.headers` after verification.
- **Reveal is audited, regenerate and toggle are audited, `get` is not.** Check the activity log ([activity-log](/en/inventory/system-config/activity-log)) with entity `bu_api_key` after a reveal.
- **Regenerate and PATCH use optimistic locking** (`where: { id, doc_version }`): two admins regenerating at the same moment produce one winner and one 409 rather than a lost secret (see [doc-version](/en/inventory/system-config/doc-version)).
- **Unknown client id and wrong secret are indistinguishable** (same 401 body, same work). A test asserting different bodies is a bug in the test.
- **Incremental sync is the supported pattern.** Edits and voids after first read are only visible via `date_field=updated`; first run use `document`, later runs poll `updated` from one day before the last successful sync, upsert by `(doc_type, id)`.
- **SR and SR-like rounding:** SR amounts come from per-layer costs, so `balanced: false` by a few cents is expected, and an SR with one consignment side can be unbalanced because that side is dropped.
- **5xx never leaks internals.** The gateway replaces a micro-business 5xx message with `Internal server error` for ext calls (`gl-journal.service.ts`, `ap-invoice.service.ts`).
- **Swagger for integrators** is a separate document at `{base_url}/api/ext/docs` and `/api/ext/docs-json`, enabled in development or when `SWAGGER_ENABLED=true`; the in-app page links to the public docs page instead of embedding Swagger UI (FE `af1bba88`) and has no "Try it" so no secret is pasted into a browser.

## 6. POS interface summary

POS brands are stored as `tb_application_config` rows `interface_pos_simphony` and `interface_pos_micros3700` (the old combined POS form was split, FE `f0439af8`, `f447132b`). At least one brand with `enabled = true` is what makes the Import POS and Sales Consumption menus appear (`licenseFeature: "interface.pos"`). Simphony carries the SFTP pull settings (host, port, credentials, remote folder, file pattern, daily schedule time); Micros 3700 is upload-only with just an enable switch. Field-level rules, import statuses, duplicate/overwrite behaviour and the scheduled pull are documented once, at [Import POS](/en/inventory/recipe/import-pos) (§6 there); Sales Consumption at [sales-consumption](/en/inventory/recipe/sales-consumption).

## 7. Cross-References

- [recipe/import-pos](/en/inventory/recipe/import-pos) — POS settings, import flow and statuses.
- [general-ledger/ap-invoice-from-grn](/en/inventory/general-ledger/ap-invoice-from-grn) and [general-ledger](/en/inventory/general-ledger) — how the export relates to the Dr/Cr data the ledger side builds from GRN and stock documents.
- [system-config/application-config](/en/inventory/system-config/application-config) — `interface_*` keys and the licence split (the generic app-config list no longer returns them).
- [system-config/activity-log](/en/inventory/system-config/activity-log) — where key reveal / regenerate / toggle events land.
- [system-config/doc-version](/en/inventory/system-config/doc-version) — the optimistic lock on `tb_bu_api_key`.
- [access-control/permission](/en/inventory/access-control/permission) — `system_admin.bu_api_key` (`view` for GET, `update` for everything else including reveal).

## 8. References

- **Frontend:** `../carmen-frontend/routes/system-admin/interface/` — `external-interface-form.tsx`, `external-api-access-section.tsx`, `external-api-docs-section.tsx`, `use-bu-api-key.ts` (`EXTERNAL_API_PATH = "/api/ext/v1"`), `interface-read-mode.ts` (a React context used by the other brand forms: before **Edit**, empty fields show `—` instead of sample placeholders), `interface-registry.ts`, `hooks/use-interface-entitlement.ts`, `CLAUDE.md` (module notes). Permission keys: `constant/permissions.ts` (`bu_api_key`).
- **Backend, key management:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_bu-api-key/` and `apps/micro-business/src/authen/bu_api_key/bu_api_key.service.ts`; schema `packages/prisma-shared-schema-backstage/prisma/schema.prisma` (`tb_bu_api_key`, `tb_external_api`); migrations `20261016150000_bu_api_key`, `20261017120000_external_api_ap_gl_export`.
- **Backend, ext API:** `apps/backend-gateway/src/external-api/` (`bu-api-key.guard.ts`, `external-api.constants.ts`, `gl-journal/`, `ap-invoice/`); builders in `apps/micro-business/src/inventory/accounting-export/`; query contract `packages/rpc-contract/src/schemas/accounting-export-query.ts`; contract doc and static OpenAPI `docs/external-api/{accounting-export.md,mapping-and-calculation.md,openapi.json}`.
- **E2E:** `../carmen-frontend-e2e/docs/test-cases/1118-interface.md` — catalog only; it predates the External rework and has no case for the BU API key or the ext endpoints (gap).
