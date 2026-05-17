---
title: การตั้งค่าอีเมล (Email Configuration)
description: การตั้งค่า SMTP / ผู้ส่ง / template สำหรับอีเมลขาออกของระบบ — การแจ้งเตือนเวิร์กโฟลว์ การส่งรายงานตามตารางเวลา การรีเซ็ตรหัสผ่าน
published: true
date: 2026-05-17T12:00:00.000Z
tags: system-config, email, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# การตั้งค่าอีเมล (Email Configuration)

> **At a Glance**
> **เจ้าของ:** Sysadmin เท่านั้น &nbsp;·&nbsp; **การจัดเก็บ:** Row ใน `tb_application_config` (`key = "report_email"`) &nbsp;·&nbsp; **ใช้โดย:** `micro-notification`, รายงานตามตารางเวลา, การรีเซ็ตรหัสผ่าน, การแจ้งเตือนการตรวจสอบ &nbsp;·&nbsp; **หนึ่ง SMTP profile ต่อ BU; รหัสผ่าน SMTP เข้ารหัสตอนเก็บ**

## 1. คืออะไรและใครใช้

Email Configuration คือ **SMTP profile ต่อ BU** ที่ Carmen ใช้สำหรับอีเมลขาออกทุกฉบับ — การแจ้งเตือนเวิร์กโฟลว์ (การอนุมัติ การส่งกลับ การปฏิเสธ PR / PO / GRN / SR), การส่งรายงานตามตารางเวลา, การแจ้งเตือนรีเซ็ตรหัสผ่าน และอีเมลทดสอบเฉพาะกิจ ไม่มีตารางเฉพาะ: SMTP host, port, credentials, default-from, default-to / CC และ subject prefix ทั้งหมดอยู่ในรูป **JSON blob เดียว** ใน `tb_application_config` ภายใต้ key `report_email`

**กลุ่มเป้าหมาย:** Sysadmin เท่านั้น (App ID `app-config.upsert`) ไม่มีตาราง email-template แยกอยู่ — body สร้างขึ้นโดย `micro-notification` จาก template ต่อประเภทการแจ้งเตือน; เพียง `subject_prefix` (default `[Carmen]`) เท่านั้นที่ผู้ใช้ปรับได้ใน subject line

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| อัปเดต SMTP host / port / username / from | System Admin → Email Configuration → ส่วน **SMTP Server** | `Save` เรียก `PUT /api/config/:bu_code/app-config/report_email` |
| หมุนเวียนรหัสผ่าน SMTP | พิมพ์รหัสผ่านใหม่ในฟิลด์ที่ mask แล้วกด **Save** | เข้ารหัสตอนเก็บโดย `encryptSecret`; ค่า masked ที่ไม่เปลี่ยน = "คงรหัสผ่านเดิม" |
| เพิ่ม / ลบ default recipient หรือ CC | ส่วน **Recipients**, แยกด้วย comma | ต้องเป็น email ที่ valid; Zod-validated ตอนเขียน |
| เปลี่ยน subject prefix | **Recipients** → Subject Prefix | นำหน้าทุก subject (default `[Carmen]`) |
| ส่งอีเมลทดสอบ | ปุ่ม **Test Email** (ด้านบนของฟอร์ม) | ใช้ config ที่ *บันทึกแล้ว* ไม่ใช่ form draft — **บันทึกก่อนแล้วทดสอบ** |
| ปิดอีเมลโดยไม่ทำลายเวิร์กโฟลว์ | ตั้ง `smtp.enabled = false` | Kill-switch: notification ลัดวงจร; เอกสารยังเดินต่อ |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Invalid SMTP config" Zod error | ขาด host / username / from หรือ port อยู่นอกช่วง `1..65535` | กรอกฟิลด์ที่จำเป็น; ตรวจสอบ port |
| "Recipient is not a valid email" | Address แย่ใน `recipients` หรือ `cc` | แก้รายการที่แยกด้วย comma |
| Test email สำเร็จในฟอร์มแต่ไม่มีเมลมา | Form draft ยังไม่บันทึก — Test ใช้ค่าที่บันทึกแล้ว | กด **Save** ก่อนแล้วค่อย **Test Email** |
| Notification ทั้งหมดเงียบใน production | `smtp.enabled = false` ถูกตั้งทิ้งไว้โดยไม่ตั้งใจ | เปิดใหม่ในฟอร์มและบันทึก |
| 403 ตอน save / load | User ไม่มี `app-config.upsert` (Sysadmin เท่านั้น) | Grant ผ่าน [[access-control/application-role]] |
| ฟิลด์รหัสผ่านแสดง `***ENCRYPTED***` | คาดหวัง — mask ตอนอ่านเพื่อไม่ให้ ciphertext ถึง browser | คงไว้เพื่อเก็บรหัสผ่านปัจจุบัน; พิมพ์ใหม่เพื่อหมุนเวียน |

## 4. กรณีพิเศษ

- **การเข้ารหัสรหัสผ่านตอนเก็บ** `smtp.password` ถูกเข้ารหัสด้วย `encryptSecret` ก่อน persist และแทนที่ด้วยตัวอักษร `***ENCRYPTED***` ตอน `GET` Idempotent — ค่าที่เข้ารหัสแล้วจะไม่ถูกเข้ารหัสซ้ำ
- **เส้นทางการเข้าถึงแบบถอดรหัส** เฉพาะ `getReportEmailForSend(bu_code)` ภายใน (TCP-only เรียกโดย `micro-notification` / cron) เท่านั้นที่ถอดรหัส เส้นทาง HTTP สาธารณะไม่เคยส่งคืน plaintext
- **ความปลอดภัยของ audit** ทุก upsert ถูกจับผ่าน `EnrichAuditUsers` ไปยัง [[reporting-audit/activity]] — แต่ค่าเองจะ *ไม่* ถูก log ป้องกันการเปิดเผย ciphertext โดยไม่ตั้งใจ
- **หนึ่ง row ต่อ BU** `tb_application_config` มี `@@unique([key, deleted_at])` การแยก cross-BU บังคับโดย route ที่ scope ตาม BU
- **`enabled` คือ kill-switch ไม่ใช่ delete** การปิดหยุดอีเมลอย่างสะอาดโดยไม่สูญเสีย config

---

## 5. Backing Service / Data Shape (Dev)

แหล่งที่มา: tenant schema **ไม่มี `tb_email_config` เฉพาะ** — profile ทั้งหมดเป็น JSON row เดียว

### 5.1 `tb_application_config` row (`key = "report_email"`)

`tb_application_config` คือ KV store ระดับ tenant ทั่วไป (ดู [[system-config/application-config]]) Shape ที่ Zod-validated:

```jsonc
{
  "smtp": {
    "host": "smtp.gmail.com",          // string, required
    "port": 587,                        // int 1..65535
    "username": "noreply@example.com", // string, required
    "password": "ENC:<ciphertext>",    // เข้ารหัสตอนเก็บ; mask ตอน GET
    "from": "noreply@example.com",     // From: header
    "enabled": true                     // master kill-switch
  },
  "recipients": ["admin@example.com"], // default To
  "cc": ["finance@example.com"],       // default CC
  "subject_prefix": "[Carmen]"         // นำหน้าทุก subject
}
```

### 5.2 ตารางปลายทางที่เกี่ยวข้อง

- `tb_report_schedule.recipients` (JSONB) — override ต่อ schedule
- `tb_report_job` — ความพยายามส่งจริง (`status`, `started_at`, `completed_at`, `error_message`)
- `tb_purchase_request.email_template_id`, `tb_purchase_order.email_template_id` — handle string สำหรับ template family ต่อเอกสารใน `micro-notification`

## 6. กฎทางธุรกิจ

- **Sysadmin เท่านั้น** Read และ write gate โดย App ID `app-config.upsert`
- **การเข้ารหัสและ mask รหัสผ่าน** เข้ารหัสผ่าน `encryptSecret`; แทนที่ด้วย `***ENCRYPTED***` ตอนอ่าน ค่า masked ที่ไม่เปลี่ยนหมายถึง "คงเดิม"
- **Zod validation ตอนเขียน** Host, port (1–65535), username, password, from, enabled ทั้งหมดจำเป็นโดย `ReportEmailSchema`; `recipients` / `cc` ต้องเป็น email ที่ valid
- **Kill-switch `enabled`** เมื่อ `false` notification service ลัดวงจรก่อนเปิด connection — เวิร์กโฟลว์ยังเดินต่อ ไม่มีอีเมลออก
- **Send context** การถอดรหัสเฉพาะผ่าน `getReportEmailForSend` ภายในผ่าน TCP จาก `micro-notification` / cron — ไม่ต้อง user_id
- **Test email** ใช้ config ที่ *บันทึกแล้ว* (ไม่ใช่ form draft) และส่งไปยัง recipient ที่ตั้งค่าไว้
- **Audit logging** ผ่าน `EnrichAuditUsers`; ค่า JSON เองจะ *ไม่* ถูก log

## 7. การอ้างอิงข้าม

- [[system-config/application-config]] — KV store แม่; `report_email` คือ key ที่สงวนไว้หนึ่งตัว
- [[reporting-audit/notification]] — `micro-notification` คือ consumer ตอน runtime
- [[reporting-audit/schedule]] / [[reporting-audit/report]] — การส่งรายงานตามตารางเวลาและตามคำขอ
- [[access-control/user]] — การรีเซ็ตรหัสผ่าน การเชิญ การให้สิทธิ์
- [[system-config/workflow]] — กฎเส้นทาง recipient (`requestor`, `current_approve`, `next_step`) resolve กับเวิร์กโฟลว์; transport คือ config นี้
- [[reporting-audit/activity]] — upserts log ที่นี่

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~4910-4924)
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts` — `ReportEmailSchema`, `encryptSensitiveFields`, `maskSensitiveFields`, `getReportEmailForSend`, `testEmail`
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts`
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/config-email/page.tsx` และ `_components/config-email-component.tsx`
- **Frontend hook:** `../carmen-inventory-frontend/hooks/use-app-config.ts` — `useAppConfigByKey('report_email')`, `useUpsertAppConfig`, `useTestEmail`
- **Notification consumer:** `micro-notification` อ่านผ่าน TCP จาก `getReportEmailForSend`
