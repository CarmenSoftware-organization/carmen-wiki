---
title: Email Configuration (Sender Profiles & Message Library)
description: Outbound email is two screens — Email Profile (SMTP sender profiles, key email_profiles) and Email Template (per-document message library, key email_templates). The single report_email screen is unrouted. No RBAC guard.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: system-config, email, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Email Configuration (Sender Profiles & Message Library)

> **At a Glance**
> **Screens:** `/system-admin/email-profile` (sender profiles, since 2026-09-08) and `/system-admin/email-template` (UI label "Email Messages", since 2026-09-16) &nbsp;·&nbsp; **Storage:** `tb_application_config` rows `email_profiles` and `email_templates` (JSONB; no dedicated table) &nbsp;·&nbsp; **Licence:** `configuration.email_profile` / `configuration.email_template` (split out of `configuration.app_config` on 2026-09-20) &nbsp;·&nbsp; **Permission (FE nav only):** `system_admin.config_email.view` &nbsp;·&nbsp; **Backend RBAC guard: none** (re-verified 2026-09-22) &nbsp;·&nbsp; **Consumers:** the *Send by email* dialogs on Purchase Order and Request for Pricing, via the secret-free lookups `GET /api/:bu_code/email-senders` and `/email-messages` &nbsp;·&nbsp; **Legacy:** the single-SMTP `report_email` screen (`routes/system-admin/config-email/`) still exists on disk but has **no route** in `router.tsx` or the nav.

![Email Configuration screen](/screenshots/system-config/config-email.png)

## Implementation status (re-verified 2026-09-22)

This page previously described one screen editing one `report_email` JSON blob. Between 2026-08-08 and 2026-09-20 outbound email was rebuilt as a **master list of named sender profiles** plus a **per-document-type message library**, each on its own screen with its own licence feature:

| Concern | Before (baseline 2026-07-29) | HEAD |
|---|---|---|
| Screen | `/system-admin/config-email` (one form) | `/system-admin/email-profile` (`routes/system-admin/email-profile/`) + `/system-admin/email-template` (`routes/system-admin/email-template/`); `config-email` is absent from `routes/router.tsx` and `constant/module-list.ts` — the component folder is dead code |
| Config key | `report_email` (single SMTP + recipients + `subject_prefix`) | `email_profiles` = `{ default_profile_id, profiles[] }` (BE `f5c3e5c5b` 2026-08-08); `email_templates` = `{ defaults, templates[] }` (FE `2b80f83c` 2026-09-16) |
| Backend schema | `ReportEmailSchema` | `EmailProfilesSchema` / `EmailProfileSchema` (`app-config.service.ts:101-128`); **`email_templates` has no backend Zod schema** — stored as sent, HTML sanitised on the frontend only (`sanitizeEmailHtml`) |
| Secret handling | `smtp.password` encrypted, masked `***ENCRYPTED***` | `profiles[*].smtp.password` encrypted and masked; masked/blank values on save are restored **by profile `id`, not array index** (`49162675a`), so deleting a profile mid-list cannot shift another profile's password |
| Test send | `POST /app-config/test-email` using the saved `report_email` | `POST /api/config/:bu_code/app-config/test-email-profile` `{ profile_id, to? }` — per profile, optional explicit recipient (`f00088307`, `7d82d77f9`); the dialog is `email-profile-test-dialog.tsx` |
| Runtime consumer | `micro-notification` via `getReportEmailForSend` (RPC) | `getEmailProfileForSend(bu_code, profile_id?)` (`app-config.service.ts:828`), exported to the Purchase Order module for `POST /api/:bu_code/purchase-orders/:id/send-email` (`purchase-orders.controller.ts:2474`, BE `1897b4fc1`) and Request for Pricing `POST …/request-for-pricings/:id/send-email` (`:480`); each send writes a `tb_activity` row with the new `enum_activity_action.email_sent` |
| Lookup for the send dialog | — | `GET /api/:bu_code/email-senders` → `{ default_profile_id, profiles[{ id, name, enabled, from_email, from_name }] }` and `GET /api/:bu_code/email-messages` — the `smtp` block is stripped entirely so the dialog never receives host/username (`email-lookup.service.ts:22-54`, BE `6a859f9e2` 2026-09-20); both map to the generic `configuration.app_config` licence (`permission.route-map.ts:55-56`) |
| Licence | `configuration.app_config` | `configuration.email_profile` for `app-config/email_profiles` + `test-email-profile`; `configuration.email_template` for `app-config/email_templates` (`LICENSE_ROUTE_OVERRIDES`, 2026-09-20); `GET /app-config` (list) no longer returns either key |
| Profile fields | — | `id`, `name`, `enabled`, `smtp{host,port,secure,username,password}`, `from_email`, `from_name` (FE `types/email-profile.ts`); the backend schema still accepts `reply_to`, `default_cc`, `subject_template`, `body_template`, `note` with defaults — the form dropped them on 2026-09-16 (`e98ef3ee`) because message content moved to the template library |
| Template fields | — | `id`, `name`, `doc_type` (`po` \| `rfp`), `enabled`, `subject_template` (plain text), `body_template` (HTML), `default_cc[]`, `note`; `defaults[doc_type]` names the template pre-selected in that document's send dialog |

**Permission finding — still open.** `config_app-config.controller.ts` at HEAD carries only the class-level `@UseGuards(KeycloakGuard)` (`:56`). `PUT :key` (`:141`) and `DELETE :key` (`:224`) call `assertSharedListViewsAdmin()` (`:264`), which returns early for every key not matching `/^list_views_/` — so `email_profiles` and `email_templates` are writable by **any authenticated member of the BU** whose contract holds the licence feature. `system_admin.config_email.view` exists in `tb_permission` and gates the sidebar entries (`module-list.ts:680,687`), but no route checks it. The licence interceptor answers "may this BU use the feature", never "may this user". See [system-config/application-config](/en/inventory/system-config/application-config) for the module-wide version of this finding.

## 1. What & Who

Two settings screens, one runtime path:

- **Email Profile** (`/system-admin/email-profile`) — a list of named SMTP sender identities for the business unit. Each profile is one SMTP host + credentials + `From:` identity with an `enabled` toggle; exactly one profile is the **default** (`default_profile_id`, "Set as default" row action). Deleting the last remaining profile clears the default; adding the first one makes it the default automatically (`email-profile.route.tsx:71,98`).
- **Email Template / "Email Messages"** (`/system-admin/email-template`) — a library of subject + HTML body templates keyed by document type. Supported `doc_type`s at HEAD: `po` and `rfp` (`EMAIL_DOC_TYPES`, `types/email-template.ts`). Placeholders are fixed per type (`lib/email-template.ts:14-24`): PO `{{po_no}}`, `{{vendor_name}}`, `{{bu_name}}`, `{{total}}`, `{{delivery_date}}`; RFP `{{rfp_name}}`, `{{vendor_name}}`, `{{contact_person}}`, `{{bu_name}}`, `{{start_date}}`, `{{end_date}}`, `{{portal_url}}`. Unsupplied placeholders render as empty strings.
- **Runtime** — the *Send by email* dialogs on a Purchase Order (`po-send-email-dialog.tsx`) and a Request for Pricing (`rfp-send-email-dialog.tsx`) load senders and messages through the secret-free lookups, let the user pick a profile and a message (pre-filled from `defaults[doc_type]`), and `POST …/send-email`. The backend decrypts the chosen profile's password via `getEmailProfileForSend`, sends the PDF-attached mail, and logs `email_sent`.

Workflow approval notifications do **not** use these profiles — the workflow dispatcher only delivers in-app notifications (see [system-config/notification-template](/en/inventory/system-config/notification-template)). The legacy `report_email` key is still readable/writable through the generic endpoints and still has its `ReportEmailSchema` + `getReportEmailForSend` RPC handler, but no screen in this product routes to it and no in-repo consumer other than that handler was found (grep `getReportEmailForSend` → `app-config.service.ts`, `app-config.controller.ts` only). Treat it as legacy.

**Audience:** Sysadmin by nav convention (`system_admin.config_email.view`); not enforced server-side.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a sender profile | Email Profile → **Add** → name, SMTP host/port/secure/username/password, From email/name, Enabled | `PUT /api/config/:bu_code/app-config/email_profiles` with the whole `{ default_profile_id, profiles }` value (`hooks/use-email-profiles.ts:60`); port `1..65535`, `secure` defaults `true`, port default 587 (`email-profile-schema.ts`) |
| Rotate a profile's password | Edit the profile, type the new password, Save | Unchanged masked value or blank = keep the stored secret; the backend refuses to store the literal mask when no secret exists (`app-config.service.ts:396-437`) |
| Make a profile the default | Row action **Set as default** | Sends the same array with only `default_profile_id` changed |
| Send a test email | Row action **Test** → optional recipient → Send | `POST …/app-config/test-email-profile` `{ profile_id, to? }`; uses the *saved* profile, so save first |
| Disable a profile without deleting it | Toggle **Enabled** off | Disabled profiles are still returned by `email-senders` with `enabled: false`; the send dialog should not offer them |
| Write a PO / RFP email message | Email Messages → **Add** → doc type, name, subject, HTML body, default CC, Enabled | `PUT …/app-config/email_templates`; insert placeholders from the chip list; preview uses sample values that are never sent |
| Pick the default message per document type | Email Messages → **Set as default** | Writes `defaults[doc_type]` |
| Send a PO / RFP to the vendor | PO / RFP detail → **Send email** | Dialog reads `email-senders` + `email-messages`, then `POST …/send-email` |
| ~~Configure the single SMTP profile~~ | ~~System Admin → Email Configuration~~ | **Unrouted since 2026-09** — `report_email` can only be edited by calling `PUT …/app-config/report_email` directly |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| Zod error on profile save | Missing name/host/username/password, port outside `1..65535`, invalid `from_email` | Fix the field; the backend re-validates with `EmailProfileSchema` |
| `Cannot save email_profiles: no stored secret to restore for profiles.*.smtp.password (id=…)` | Client posted the mask or a blank password for a profile that never had one | Type a real password |
| Test send fails | Wrong SMTP host/port/`secure`, or credentials | Fix and re-test; the test uses the saved value, not the form draft |
| `403 LICENSE_REQUIRED` / `LICENSE_EXPIRED` on either screen | BU's contract lacks `configuration.email_profile` / `configuration.email_template` | Renew/buy via the Platform; `GET /api/license` lists `features[]` and `expired_features[]` |
| Send dialog shows no senders | No enabled profile, or `email_profiles` never saved | Create and enable a profile |
| Placeholder left literally in the sent mail (`{{something}}`) | Placeholder not in the list for that `doc_type` | Use only the keys in `EMAIL_PLACEHOLDERS[doc_type]` |
| Any authenticated user can load/save both keys, not just Sysadmin | **Confirmed gap — still open, re-verified 2026-09-22** (no RBAC guard on `config_app-config.controller.ts`) | Do not assume a 403 protects these endpoints today |
| Password field shows `***ENCRYPTED***` | Expected — masked on read | Leave as-is to keep the current password |

## 4. Edge Cases

- **Two keys, two licences, one controller.** The licence split is by URL (`resolveRouteFeature`), so a BU with `configuration.email_template` but not `configuration.email_profile` can edit messages but not senders; the send dialogs' lookups sit under the generic `configuration.app_config` and keep working either way.
- **Secret restore is id-based.** `retainMaskedEmailProfileSecrets` (`app-config.service.ts:396`) matches incoming profiles to stored ones by `id`; a profile with a new `id` must carry a real password.
- **`email_templates` is unvalidated server-side.** No `schemaByKey` entry — a direct API caller can store any shape; the screens are the only shape enforcement.
- **Audit safety.** Upserts are captured via `EnrichAuditUsers`; the config value is not logged. Sends log `email_sent` on the document, not on the profile.
- **`report_email` is orphaned, not removed.** Its schema, secret path and RPC reader remain; only the screen is unreachable.

---

## 5. Backing Service / Data Shape (Dev)

Source: tenant schema. **No dedicated table** — two `tb_application_config` rows.

### 5.1 `email_profiles` (Zod: `EmailProfilesSchema`, `app-config.service.ts:101-128`)

```
{
  "default_profile_id": "p-001",             // string | null
  "profiles": [
    {
      "id": "p-001",                         // required, stable — secrets are matched by it
      "name": "Purchasing",
      "enabled": true,
      "smtp": {
        "host": "smtp.example.com",
        "port": 587,                         // int 1..65535
        "secure": true,
        "username": "purchasing@example.com",
        "password": "***ENCRYPTED***"        // encrypted at rest, masked on read
      },
      "from_email": "purchasing@example.com",
      "from_name": "Carmen Purchasing",
      "reply_to": "", "default_cc": [], "subject_template": "", "body_template": "", "note": ""
                                             // accepted with defaults; no longer edited by the form
    }
  ]
}
```

### 5.2 `email_templates` (no backend schema; FE `types/email-template.ts`, seed `packages/prisma-shared-schema-tenant/src/seed-data/email-templates.ts`)

```
{
  "defaults": { "po": "t-po-1", "rfp": null },
  "templates": [
    {
      "id": "t-po-1",
      "name": "Standard PO",
      "doc_type": "po",                       // "po" | "rfp"
      "enabled": true,
      "subject_template": "Purchase Order {{po_no}} from {{bu_name}}",
      "body_template": "<p>Dear {{vendor_name}}, …</p>",   // HTML, sanitised client-side
      "default_cc": ["finance@example.com"],
      "note": ""
    }
  ]
}
```

### 5.3 Endpoints

```
GET  /api/config/:bu_code/app-config/email_profiles         licence configuration.email_profile
PUT  /api/config/:bu_code/app-config/email_profiles         { value }  (doc_version echoed by the hook)
POST /api/config/:bu_code/app-config/test-email-profile     { profile_id, to? }  licence configuration.email_profile
GET  /api/config/:bu_code/app-config/email_templates        licence configuration.email_template
PUT  /api/config/:bu_code/app-config/email_templates        { value }
GET  /api/:bu_code/email-senders                            secret-free { default_profile_id, profiles[] }
GET  /api/:bu_code/email-messages                           the message library
POST /api/:bu_code/purchase-orders/:id/send-email           consumer
POST /api/:bu_code/request-for-pricings/:id/send-email      consumer
```

All under `KeycloakGuard`; the two lookups additionally carry no `AppIdGuard` (`email-lookup.controller.ts:2`).

## 6. Business Rules

- **Sysadmin-only by convention, not by enforcement.** No RBAC guard on the app-config controller (re-verified 2026-09-22).
- **Licence per key group** (`configuration.email_profile`, `configuration.email_template`) via `LICENSE_ROUTE_OVERRIDES`; generic list endpoint hides both keys.
- **Password encryption + masking**, id-based restore; blank never deletes a secret.
- **One default profile per BU** (`default_profile_id`); `enabled: false` keeps the profile but should exclude it from send dialogs.
- **Message library per document type** (`po`, `rfp`); fixed placeholder sets; HTML bodies sanitised on the frontend.
- **Every send is audited** as `enum_activity_action.email_sent` on the document.

## 7. Cross-References

- [system-config/application-config](/en/inventory/system-config/application-config) — umbrella KV store; key registry and the licence split.
- [purchase-order](/en/inventory/purchase-order) — *Send email* dialog and `POST …/send-email`.
- [vendor-pricelist](/en/inventory/vendor-pricelist) — RFP *Send email* dialog.
- [system-config/notification-template](/en/inventory/system-config/notification-template) — in-app workflow notifications (no email).
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — `email_sent` rows.

## 8. References

- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts` — `EmailProfileSchema`/`EmailProfilesSchema` (`:96-128`), `secretPathsFor` (`:216`), `retainMaskedEmailProfileSecrets` (`:396`), `getEmailProfileForSend` (`:828`), `testEmailProfile`; `app-config.module.ts` (export for the PO module).
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts` (`test-email-profile` `:395`); `apps/backend-gateway/src/application/email-lookup/{email-lookup.controller,email-lookup.service}.ts`; `packages/prisma-shared-schema-platform/prisma/permission.route-map.ts:55-56,257-260`.
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/src/seed-data/email-templates.ts`; `apps/micro-business/src/authen/tenant_seed/seed-sets/email-templates.seed-set.ts`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/email-profile/` (`email-profile.route.tsx`, `email-profile-dialog.tsx`, `email-profile-test-dialog.tsx`, `email-profile-schema.ts`); `routes/system-admin/email-template/`; `hooks/use-email-profiles.ts`, `hooks/use-email-templates.ts`, `hooks/use-email-senders.ts`, `hooks/use-email-messages.ts`; `types/email-profile.ts`, `types/email-template.ts`, `lib/email-template.ts`; `routes/procurement/purchase-order/po-send-email-dialog.tsx`, `routes/vendor-management/request-price-list/rfp-send-email-dialog.tsx`. Legacy: `routes/system-admin/config-email/` (unrouted).
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/app-config/POST-test-email-profile-config-app-config.bru`.
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1116-email-profile.md` (30 cases), `1117-email-template.md` (30 cases) — catalogs only, no Playwright spec.
