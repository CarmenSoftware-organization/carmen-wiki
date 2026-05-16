---
title: Email Configuration
description: SMTP / sender / template configuration for outbound system email — workflow notifications, scheduled report delivery, password reset.
published: true
date: 2026-05-16T17:00:00.000Z
tags: system-config, email, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Email Configuration

## 1. Purpose

Email Configuration is the per-business-unit SMTP profile Carmen uses for every outbound email — workflow notifications (PR / PO / GRN / SR approvals, sendbacks, rejections), scheduled report delivery from [[reporting-audit/report]] / [[reporting-audit/schedule]], password-reset and access-grant notices from [[access-control]], audit / alert emails from [[reporting-audit/activity]], and ad-hoc test emails fired from the admin screen. There is no separate "email server" record — the SMTP host, port, credentials, default-from address, default-to / CC list, and subject prefix all live as a single JSON blob in `tb_application_config` under the key `report_email`. Sysadmin curates the profile per BU; rotation of SMTP credentials is logged via [[reporting-audit/activity]] and the SMTP password is encrypted at rest before it leaves the request handler.

There is currently **no separate email-template table** in the tenant schema — message bodies are built by the notification service from a fixed template per notification type, with the document's denormalised display fields substituted at send time. The `subject_prefix` field on this config (default `[Carmen]`) is the one user-tunable string in the subject line.

## 2. Prisma Model(s) OR Data Model

There is no dedicated `tb_email_config` table — the entire profile is one JSON row in `tb_application_config` keyed by `key = "report_email"`.

### 2.1 `tb_application_config` row (`key = "report_email"`)

`tb_application_config` is the generic tenant-wide KV store ([[system-config/application-config]] for the umbrella entity). The `report_email` row carries a Zod-validated value with this shape:

```jsonc
{
  "smtp": {
    "host": "smtp.gmail.com",          // string, required
    "port": 587,                        // int 1..65535
    "username": "noreply@example.com", // string, required
    "password": "ENC:<ciphertext>",    // string, encrypted at rest
    "from": "noreply@example.com",     // string, From: header
    "enabled": true                     // boolean, master kill-switch
  },
  "recipients": ["admin@example.com"], // array of email — default To
  "cc": ["finance@example.com"],       // array of email — default CC
  "subject_prefix": "[Carmen]"         // string, prepended to every subject
}
```

When the row is read by the admin UI, the `smtp.password` field is masked as `***ENCRYPTED***` so the ciphertext never reaches the browser. When it is read by the internal `getReportEmailForSend(bu_code)` path (TCP-only, called by `micro-notification` / cron), the password is decrypted and handed to nodemailer.

### 2.2 Related downstream tables

- `tb_report_schedule.recipients` (JSONB array) — per-schedule overrides for who receives a scheduled report.
- `tb_report_job` — captures the actual send attempt with `status`, `started_at`, `completed_at`, `error_message`.
- `tb_purchase_request.email_template_id`, `tb_purchase_order.email_template_id` (VarChar) — string handle for the per-document email template family; the actual template body lives in `micro-notification`, not in this table.

## 3. Usage / Cross-References

- [[reporting-audit/notification]] — every workflow notification (submit / approve / reject / sendback) reads this config to send. `micro-notification` is the runtime consumer.
- [[reporting-audit/schedule]] — scheduled report emails (`tb_report_schedule`) use this SMTP profile for delivery; per-schedule `recipients` overrides the default-to list.
- [[reporting-audit/report]] — on-demand report delivery routes through the same SMTP.
- [[access-control/user]] — password reset, invite, and access-grant emails route here.
- [[system-config/workflow]] — recipient routing rules (`requestor`, `current_approve`, `next_step`) are resolved against the workflow definition; the actual SMTP transport is this config.
- [[system-config/application-config]] — `report_email` is one of several reserved keys; this page documents that one key in detail.

## 4. Configuration UI

Managed by **Sysadmin** under System Admin → Email Configuration (`/system-admin/config-email`). The screen is a single form with two sections:

1. **SMTP Server** — Host, Port (default `587`), Username, Password (`type=password`, never round-trips the ciphertext), From Address, Enabled toggle.
2. **Recipients** — To (comma-separated), CC (comma-separated), Subject Prefix.

Two top-level actions: **Save** persists the value via `PUT /api/config/:bu_code/app-config/report_email`; **Test Email** calls `POST /api/config/:bu_code/app-config/test-email`, which delegates to `micro-notification` and sends an audit-traced test message to the configured recipients using the *currently-saved* config (not the form draft — save first, then test).

## 5. Business Rules

- **One row per BU.** `tb_application_config` has `@@unique([key, deleted_at])`. Only Sysadmin can read or write this row (App ID `app-config.upsert`).
- **Password encryption at rest.** The `smtp.password` field is encrypted with the platform secret (`encryptSecret` / `decryptSecret` in `@/common/crypto.util`) before being persisted. Idempotent — if the value is already encrypted it is not re-encrypted.
- **Password masking on read.** The `GET` endpoint replaces `smtp.password` with the literal string `***ENCRYPTED***` before returning. The admin form treats an unchanged masked value as "leave password as-is".
- **Zod validation on write.** Host, port (1-65535), username, password, from, and enabled are all required by `ReportEmailSchema`; `recipients` and `cc` must be valid email addresses if provided. Invalid writes are rejected with the validation error.
- **Enabled flag is a kill-switch.** When `smtp.enabled` is `false`, the notification service short-circuits before opening a connection — the document still progresses through workflow, but no email leaves the system. This is the safe way to silence email in staging or during incidents.
- **Send context.** The decrypted password is only accessible through the internal `getReportEmailForSend` path, which uses `getdb_connection_for_external` so system callers (cron, micro-notification) don't need a real user_id. The public HTTP path never returns the decrypted value.
- **Test email behaviour.** Tests use the *saved* config and go to the configured recipients — they do *not* validate the form's current draft. Failures bubble up as a toast and are logged.
- **Audit logging.** Every upsert is captured via the `EnrichAuditUsers` interceptor and lands in [[reporting-audit/activity]] with the actor's user_id; the value itself is *not* logged (avoiding accidental ciphertext disclosure).

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~4910-4924).
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts` — `ReportEmailSchema`, `encryptSensitiveFields`, `maskSensitiveFields`, `getReportEmailForSend`, `testEmail`.
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts`.
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/config-email/page.tsx` and `_components/config-email-component.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend/hooks/use-app-config.ts` — `useAppConfigByKey('report_email')`, `useUpsertAppConfig`, `useTestEmail`.
- **Notification consumer:** `micro-notification` reads `tb_application_config(report_email)` via TCP from `getReportEmailForSend`.
- **Cross-module:** see Section 3.
