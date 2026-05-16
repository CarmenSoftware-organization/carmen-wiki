---
title: Email Configuration
description: SMTP / sender / template configuration for outbound system email — workflow notifications, scheduled report delivery, password reset.
published: true
date: 2026-05-17T08:00:00.000Z
tags: system-config, email, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Email Configuration

> **At a Glance**
> **Owner:** Sysadmin only &nbsp;·&nbsp; **Storage:** `tb_application_config` row (`key = "report_email"`) &nbsp;·&nbsp; **Used by:** `micro-notification`, scheduled reports, password reset, audit alerts &nbsp;·&nbsp; **One SMTP profile per BU; SMTP password encrypted at rest.**

## 1. What & Who

Email Configuration is the **per-BU SMTP profile** Carmen uses for every outbound email — workflow notifications (PR / PO / GRN / SR approvals, sendbacks, rejections), scheduled report delivery, password-reset notices, and ad-hoc test emails. There is no dedicated table: the SMTP host, port, credentials, default-from, default-to / CC, and subject prefix all live as a **single JSON blob** in `tb_application_config` under the key `report_email`.

**Audience:** Sysadmin only (App ID `app-config.upsert`). No separate email-template table exists — bodies are built by `micro-notification` from per-notification-type templates; only `subject_prefix` (default `[Carmen]`) is user-tunable in the subject line.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Update SMTP host / port / username / from | System Admin → Email Configuration → **SMTP Server** section | `Save` calls `PUT /api/config/:bu_code/app-config/report_email` |
| Rotate SMTP password | Type the new password in the masked field, then **Save** | Encrypted at rest by `encryptSecret`; unchanged masked value = "leave password as-is" |
| Add / remove a default recipient or CC | **Recipients** section, comma-separated | Must be valid emails; Zod-validated on write |
| Change subject prefix | **Recipients** → Subject Prefix | Prepended to every subject (default `[Carmen]`) |
| Send a test email | **Test Email** button (top of form) | Uses the *saved* config, not the form draft — **save first, then test** |
| Silence email without breaking workflow | Set `smtp.enabled = false` | Kill-switch: notifications short-circuit; documents still progress |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Invalid SMTP config" Zod error | Missing host / username / from, or port outside `1..65535` | Fill the required fields; check the port |
| "Recipient is not a valid email" | Bad address in `recipients` or `cc` | Fix the comma-separated list |
| Test email succeeds in form but no mail arrives | Form draft not saved — Test uses the saved value | Click **Save** first, then **Test Email** |
| All notifications silent in production | `smtp.enabled = false` accidentally left set | Re-enable on the form and Save |
| 403 on save / load | User lacks `app-config.upsert` (Sysadmin only) | Grant via [[access-control/role]] |
| Password field shows `***ENCRYPTED***` | Expected — masked on read so ciphertext never reaches the browser | Leave as-is to keep current password; type new to rotate |

## 4. Edge Cases

- **Password encryption at rest.** `smtp.password` is encrypted with `encryptSecret` before persistence and replaced with literal `***ENCRYPTED***` on `GET`. Idempotent — already-encrypted values are not re-encrypted.
- **Decrypted access path.** Only the internal `getReportEmailForSend(bu_code)` (TCP-only, called by `micro-notification` / cron) decrypts. The public HTTP path never returns plaintext.
- **Audit safety.** Every upsert is captured via `EnrichAuditUsers` into [[reporting-audit/activity]] — but the value itself is *not* logged, avoiding accidental ciphertext disclosure.
- **One row per BU.** `tb_application_config` has `@@unique([key, deleted_at])`. Cross-BU isolation is enforced by the BU-scoped route.
- **`enabled` is a kill-switch, not a delete.** Toggling off pauses email cleanly without losing the config.

---

## 5. Backing Service / Data Shape (Dev)

Source: tenant schema. **No dedicated `tb_email_config`** — the entire profile is one JSON row.

### 5.1 `tb_application_config` row (`key = "report_email"`)

`tb_application_config` is the generic tenant-wide KV store (see [[system-config/application-config]]). The Zod-validated shape:

```jsonc
{
  "smtp": {
    "host": "smtp.gmail.com",          // string, required
    "port": 587,                        // int 1..65535
    "username": "noreply@example.com", // string, required
    "password": "ENC:<ciphertext>",    // encrypted at rest; masked on GET
    "from": "noreply@example.com",     // From: header
    "enabled": true                     // master kill-switch
  },
  "recipients": ["admin@example.com"], // default To
  "cc": ["finance@example.com"],       // default CC
  "subject_prefix": "[Carmen]"         // prepended to every subject
}
```

### 5.2 Related downstream tables

- `tb_report_schedule.recipients` (JSONB) — per-schedule override.
- `tb_report_job` — actual send attempt (`status`, `started_at`, `completed_at`, `error_message`).
- `tb_purchase_request.email_template_id`, `tb_purchase_order.email_template_id` — string handle for the per-document template family in `micro-notification`.

## 6. Business Rules

- **Sysadmin-only.** Read and write gated by App ID `app-config.upsert`.
- **Password encryption + masking.** Encrypted via `encryptSecret`; replaced with `***ENCRYPTED***` on read. Unchanged masked value means "leave as-is".
- **Zod validation on write.** Host, port (1–65535), username, password, from, enabled all required by `ReportEmailSchema`; `recipients` / `cc` must be valid emails.
- **`enabled` kill-switch.** When `false`, the notification service short-circuits before opening a connection — workflow still progresses, no email leaves.
- **Send context.** Decryption only via internal `getReportEmailForSend` over TCP from `micro-notification` / cron — no user_id required.
- **Test email** uses the *saved* config (not the form draft) and goes to configured recipients.
- **Audit logging** via `EnrichAuditUsers`; the JSON value itself is *not* logged.

## 7. Cross-References

- [[system-config/application-config]] — umbrella KV store; `report_email` is one reserved key.
- [[reporting-audit/notification]] — `micro-notification` is the runtime consumer.
- [[reporting-audit/schedule]] / [[reporting-audit/report]] — scheduled and on-demand report delivery.
- [[access-control/user]] — password reset, invite, access-grant emails.
- [[system-config/workflow]] — recipient routing rules (`requestor`, `current_approve`, `next_step`) resolved against workflow; transport is this config.
- [[reporting-audit/activity]] — upserts logged here.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~4910-4924).
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts` — `ReportEmailSchema`, `encryptSensitiveFields`, `maskSensitiveFields`, `getReportEmailForSend`, `testEmail`.
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts`.
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/config-email/page.tsx` and `_components/config-email-component.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend/hooks/use-app-config.ts` — `useAppConfigByKey('report_email')`, `useUpsertAppConfig`, `useTestEmail`.
- **Notification consumer:** `micro-notification` reads via TCP from `getReportEmailForSend`.
