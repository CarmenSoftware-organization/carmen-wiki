---
title: การตั้งค่าอีเมล (Sender Profiles & Message Library)
description: อีเมลขาออกมีสองหน้าจอ — Email Profile (SMTP sender profile, key email_profiles) และ Email Template (คลังข้อความต่อเอกสาร, key email_templates) หน้าจอ report_email แบบเดี่ยวไม่มี route แล้ว ไม่มี RBAC guard
published: true
date: '2026-09-23T01:30:00.000Z'
tags: system-config, email, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# การตั้งค่าอีเมล (Sender Profiles & Message Library)

> **At a Glance**
> **หน้าจอ:** `/system-admin/email-profile` (sender profile ตั้งแต่ 2026-09-08) และ `/system-admin/email-template` (label บน UI "Email Messages" ตั้งแต่ 2026-09-16) &nbsp;·&nbsp; **การจัดเก็บ:** row ใน `tb_application_config` คือ `email_profiles` และ `email_templates` (JSONB; ไม่มีตารางเฉพาะ) &nbsp;·&nbsp; **Licence:** `configuration.email_profile` / `configuration.email_template` (แยกออกจาก `configuration.app_config` เมื่อ 2026-09-20) &nbsp;·&nbsp; **Permission (nav ฝั่ง FE เท่านั้น):** `system_admin.config_email.view` &nbsp;·&nbsp; **RBAC guard ฝั่ง backend: ไม่มี** (ตรวจสอบซ้ำ 2026-09-22) &nbsp;·&nbsp; **ผู้บริโภค:** dialog *Send by email* บน Purchase Order และ Request for Pricing ผ่าน lookup ที่ไม่มี secret `GET /api/:bu_code/email-senders` และ `/email-messages` &nbsp;·&nbsp; **Legacy:** หน้าจอ `report_email` แบบ SMTP เดี่ยว (`routes/system-admin/config-email/`) ยังอยู่บนดิสก์แต่ **ไม่มี route** ใน `router.tsx` หรือ nav

![การตั้งค่าอีเมล (Email Configuration) screen](/screenshots/system-config/config-email.png)

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

หน้านี้เคยอธิบายหน้าจอเดียวที่แก้ JSON blob `report_email` ก้อนเดียว ระหว่าง 2026-08-08 ถึง 2026-09-20 อีเมลขาออกถูกสร้างใหม่เป็น **master list ของ sender profile ที่มีชื่อ** บวก **คลังข้อความต่อประเภทเอกสาร** แต่ละอย่างมีหน้าจอของตัวเองและ licence feature ของตัวเอง:

| ประเด็น | ก่อน (baseline 2026-07-29) | HEAD |
|---|---|---|
| หน้าจอ | `/system-admin/config-email` (ฟอร์มเดียว) | `/system-admin/email-profile` (`routes/system-admin/email-profile/`) + `/system-admin/email-template` (`routes/system-admin/email-template/`); `config-email` หายไปจาก `routes/router.tsx` และ `constant/module-list.ts` — folder ของ component เป็น dead code |
| Config key | `report_email` (SMTP เดี่ยว + recipient + `subject_prefix`) | `email_profiles` = `{ default_profile_id, profiles[] }` (BE `f5c3e5c5b` 2026-08-08); `email_templates` = `{ defaults, templates[] }` (FE `2b80f83c` 2026-09-16) |
| Schema ฝั่ง backend | `ReportEmailSchema` | `EmailProfilesSchema` / `EmailProfileSchema` (`app-config.service.ts:101-128`); **`email_templates` ไม่มี Zod schema ฝั่ง backend** — เก็บตามที่ส่งมา HTML ถูก sanitise ฝั่ง frontend เท่านั้น (`sanitizeEmailHtml`) |
| การจัดการ secret | `smtp.password` เข้ารหัส mask เป็น `***ENCRYPTED***` | `profiles[*].smtp.password` เข้ารหัสและ mask; ค่าที่ mask/ว่างตอนบันทึกถูก restore **ตาม `id` ของ profile ไม่ใช่ index ของ array** (`49162675a`) การลบ profile กลางรายการจึงไม่ทำให้รหัสผ่านของ profile อื่นเลื่อน |
| ส่งทดสอบ | `POST /app-config/test-email` ใช้ `report_email` ที่บันทึกไว้ | `POST /api/config/:bu_code/app-config/test-email-profile` `{ profile_id, to? }` — ต่อ profile ระบุผู้รับได้ (`f00088307`, `7d82d77f9`); dialog คือ `email-profile-test-dialog.tsx` |
| ผู้บริโภคตอน runtime | `micro-notification` ผ่าน `getReportEmailForSend` (RPC) | `getEmailProfileForSend(bu_code, profile_id?)` (`app-config.service.ts:828`) export ให้โมดูล Purchase Order สำหรับ `POST /api/:bu_code/purchase-orders/:id/send-email` (`purchase-orders.controller.ts:2474`, BE `1897b4fc1`) และ Request for Pricing `POST …/request-for-pricings/:id/send-email` (`:480`); การส่งแต่ละครั้งเขียนแถว `tb_activity` ด้วย `enum_activity_action.email_sent` ตัวใหม่ |
| Lookup สำหรับ dialog ส่ง | — | `GET /api/:bu_code/email-senders` → `{ default_profile_id, profiles[{ id, name, enabled, from_email, from_name }] }` และ `GET /api/:bu_code/email-messages` — block `smtp` ถูกตัดออกทั้งหมด dialog จึงไม่เคยได้รับ host/username (`email-lookup.service.ts:22-54`, BE `6a859f9e2` 2026-09-20); ทั้งคู่ map ไปที่ licence ทั่วไป `configuration.app_config` (`permission.route-map.ts:55-56`) |
| Licence | `configuration.app_config` | `configuration.email_profile` สำหรับ `app-config/email_profiles` + `test-email-profile`; `configuration.email_template` สำหรับ `app-config/email_templates` (`LICENSE_ROUTE_OVERRIDES`, 2026-09-20); `GET /app-config` (รายการ) ไม่คืน key ทั้งสองอีกแล้ว |
| ฟิลด์ของ profile | — | `id`, `name`, `enabled`, `smtp{host,port,secure,username,password}`, `from_email`, `from_name` (FE `types/email-profile.ts`); schema ฝั่ง backend ยังรับ `reply_to`, `default_cc`, `subject_template`, `body_template`, `note` พร้อม default — ฟอร์มตัดออกเมื่อ 2026-09-16 (`e98ef3ee`) เพราะเนื้อหาข้อความย้ายไปคลัง template |
| ฟิลด์ของ template | — | `id`, `name`, `doc_type` (`po` \| `rfp`), `enabled`, `subject_template` (ข้อความธรรมดา), `body_template` (HTML), `default_cc[]`, `note`; `defaults[doc_type]` ระบุ template ที่ถูกเลือกไว้ล่วงหน้าใน dialog ส่งของเอกสารนั้น |

**ข้อค้นพบด้าน permission — ยังเปิดอยู่** `config_app-config.controller.ts` ที่ HEAD มีเพียง `@UseGuards(KeycloakGuard)` ระดับ class (`:56`) `PUT :key` (`:141`) และ `DELETE :key` (`:224`) เรียก `assertSharedListViewsAdmin()` (`:264`) ซึ่ง return ออกทันทีสำหรับทุก key ที่ไม่ตรง `/^list_views_/` — ดังนั้น `email_profiles` และ `email_templates` เขียนได้โดย **สมาชิก BU ที่ authenticated คนใดก็ได้** ที่สัญญาของ BU มี licence feature `system_admin.config_email.view` มีอยู่ใน `tb_permission` และ gate sidebar entry (`module-list.ts:680,687`) แต่ไม่มี route ใดตรวจมัน licence interceptor ตอบว่า "BU นี้ใช้ feature ได้ไหม" ไม่เคยตอบว่า "ผู้ใช้คนนี้ทำได้ไหม" ดู [system-config/application-config](/th/inventory/system-config/application-config) สำหรับเวอร์ชันที่ครอบคลุมทั้งโมดูลของ finding นี้

## 1. คืออะไรและใครใช้

สองหน้าจอตั้งค่า เส้นทาง runtime เดียว:

- **Email Profile** (`/system-admin/email-profile`) — รายการ SMTP sender identity ที่มีชื่อของ business unit แต่ละ profile คือ SMTP host หนึ่งตัว + credential + identity `From:` พร้อม toggle `enabled`; มี profile **default** หนึ่งตัวพอดี (`default_profile_id`, row action "Set as default") การลบ profile สุดท้ายที่เหลือจะล้าง default; การเพิ่มตัวแรกจะทำให้เป็น default อัตโนมัติ (`email-profile.route.tsx:71,98`)
- **Email Template / "Email Messages"** (`/system-admin/email-template`) — คลัง template subject + body HTML แยกตามประเภทเอกสาร `doc_type` ที่รองรับที่ HEAD: `po` และ `rfp` (`EMAIL_DOC_TYPES`, `types/email-template.ts`) placeholder คงที่ต่อประเภท (`lib/email-template.ts:14-24`): PO `{{po_no}}`, `{{vendor_name}}`, `{{bu_name}}`, `{{total}}`, `{{delivery_date}}`; RFP `{{rfp_name}}`, `{{vendor_name}}`, `{{contact_person}}`, `{{bu_name}}`, `{{start_date}}`, `{{end_date}}`, `{{portal_url}}` placeholder ที่ไม่ได้ให้ค่า render เป็น string ว่าง
- **Runtime** — dialog *Send by email* บน Purchase Order (`po-send-email-dialog.tsx`) และ Request for Pricing (`rfp-send-email-dialog.tsx`) โหลด sender และ message ผ่าน lookup ที่ไม่มี secret ให้ผู้ใช้เลือก profile และ message (เติมล่วงหน้าจาก `defaults[doc_type]`) แล้ว `POST …/send-email` backend ถอดรหัสรหัสผ่านของ profile ที่เลือกผ่าน `getEmailProfileForSend` ส่งเมลพร้อมแนบ PDF และ log `email_sent`

การแจ้งเตือนอนุมัติของ workflow **ไม่** ใช้ profile เหล่านี้ — workflow dispatcher ส่งเฉพาะการแจ้งเตือนในแอป (ดู [system-config/notification-template](/th/inventory/system-config/notification-template)) key `report_email` แบบ legacy ยังอ่าน/เขียนได้ผ่าน endpoint ทั่วไปและยังมี `ReportEmailSchema` + handler RPC `getReportEmailForSend` แต่ไม่มีหน้าจอใดในผลิตภัณฑ์นี้ route ไปหามัน และไม่พบผู้บริโภคใน repo นอกจาก handler นั้น (grep `getReportEmailForSend` → `app-config.service.ts`, `app-config.controller.ts` เท่านั้น) ถือเป็น legacy

**กลุ่มเป้าหมาย:** Sysadmin ตามข้อตกลง nav (`system_admin.config_email.view`); ไม่บังคับฝั่ง server

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม sender profile | Email Profile → **Add** → ชื่อ, SMTP host/port/secure/username/password, From email/name, Enabled | `PUT /api/config/:bu_code/app-config/email_profiles` พร้อม value `{ default_profile_id, profiles }` ทั้งก้อน (`hooks/use-email-profiles.ts:60`); port `1..65535`, `secure` default `true`, port default 587 (`email-profile-schema.ts`) |
| หมุนเวียนรหัสผ่านของ profile | แก้ profile พิมพ์รหัสผ่านใหม่ Save | ค่า masked ที่ไม่เปลี่ยนหรือว่าง = คง secret ที่เก็บไว้; backend ปฏิเสธการเก็บ mask ตามตัวอักษรเมื่อไม่มี secret อยู่ (`app-config.service.ts:396-437`) |
| ตั้ง profile เป็น default | Row action **Set as default** | ส่ง array เดิมโดยเปลี่ยนเฉพาะ `default_profile_id` |
| ส่งอีเมลทดสอบ | Row action **Test** → ผู้รับ (ไม่บังคับ) → Send | `POST …/app-config/test-email-profile` `{ profile_id, to? }`; ใช้ profile ที่ *บันทึกแล้ว* จึงต้องบันทึกก่อน |
| ปิด profile โดยไม่ลบ | Toggle **Enabled** ปิด | profile ที่ปิดยังถูกคืนโดย `email-senders` พร้อม `enabled: false`; dialog ส่งไม่ควรเสนอมัน |
| เขียนข้อความอีเมล PO / RFP | Email Messages → **Add** → ประเภทเอกสาร, ชื่อ, subject, body HTML, default CC, Enabled | `PUT …/app-config/email_templates`; แทรก placeholder จากรายการ chip; preview ใช้ค่าตัวอย่างที่ไม่เคยถูกส่ง |
| เลือก message default ต่อประเภทเอกสาร | Email Messages → **Set as default** | เขียน `defaults[doc_type]` |
| ส่ง PO / RFP ให้ vendor | หน้า detail ของ PO / RFP → **Send email** | Dialog อ่าน `email-senders` + `email-messages` แล้ว `POST …/send-email` |
| ~~ตั้งค่า SMTP profile เดี่ยว~~ | ~~System Admin → Email Configuration~~ | **ไม่มี route ตั้งแต่ 2026-09** — `report_email` แก้ได้เฉพาะโดยเรียก `PUT …/app-config/report_email` ตรง ๆ |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Zod error ตอนบันทึก profile | ขาด name/host/username/password, port อยู่นอกช่วง `1..65535`, `from_email` ไม่ valid | แก้ฟิลด์; backend validate ซ้ำด้วย `EmailProfileSchema` |
| `Cannot save email_profiles: no stored secret to restore for profiles.*.smtp.password (id=…)` | Client post mask หรือรหัสผ่านว่างสำหรับ profile ที่ไม่เคยมีรหัสผ่าน | พิมพ์รหัสผ่านจริง |
| ส่งทดสอบล้มเหลว | SMTP host/port/`secure` หรือ credential ผิด | แก้แล้วทดสอบใหม่; การทดสอบใช้ค่าที่บันทึกแล้ว ไม่ใช่ form draft |
| `403 LICENSE_REQUIRED` / `LICENSE_EXPIRED` บนหน้าจอใดหน้าจอหนึ่ง | สัญญาของ BU ไม่มี `configuration.email_profile` / `configuration.email_template` | ต่ออายุ/ซื้อผ่าน Platform; `GET /api/license` แสดง `features[]` และ `expired_features[]` |
| Dialog ส่งไม่แสดง sender | ไม่มี profile ที่ enabled หรือ `email_profiles` ไม่เคยถูกบันทึก | สร้างและเปิดใช้ profile |
| placeholder ค้างตามตัวอักษรในเมลที่ส่ง (`{{something}}`) | placeholder ไม่อยู่ในรายการของ `doc_type` นั้น | ใช้เฉพาะ key ใน `EMAIL_PLACEHOLDERS[doc_type]` |
| ผู้ใช้ที่ authenticated ใครก็ได้ load/save ทั้งสอง key ได้ ไม่ใช่แค่ Sysadmin | **ช่องโหว่ที่ยืนยันแล้ว — ยังเปิดอยู่ ตรวจสอบซ้ำ 2026-09-22** (ไม่มี RBAC guard บน `config_app-config.controller.ts`) | อย่าคิดว่า 403 ปกป้อง endpoint เหล่านี้อยู่วันนี้ |
| ฟิลด์รหัสผ่านแสดง `***ENCRYPTED***` | คาดหวัง — mask ตอนอ่าน | คงไว้เพื่อเก็บรหัสผ่านปัจจุบัน |

## 4. กรณีพิเศษ

- **สอง key สอง licence หนึ่ง controller** การแยก licence ทำตาม URL (`resolveRouteFeature`) BU ที่มี `configuration.email_template` แต่ไม่มี `configuration.email_profile` จึงแก้ message ได้แต่แก้ sender ไม่ได้; lookup ของ dialog ส่งอยู่ใต้ `configuration.app_config` ทั่วไปและยังทำงานได้ไม่ว่ากรณีใด
- **การ restore secret ยึดตาม id** `retainMaskedEmailProfileSecrets` (`app-config.service.ts:396`) จับคู่ profile ที่ส่งเข้ามากับที่เก็บไว้ด้วย `id`; profile ที่มี `id` ใหม่ต้องมีรหัสผ่านจริง
- **`email_templates` ไม่ถูก validate ฝั่ง server** ไม่มี entry ใน `schemaByKey` — ผู้เรียก API โดยตรงเก็บรูปร่างใดก็ได้; หน้าจอคือการบังคับรูปร่างเพียงอย่างเดียว
- **ความปลอดภัยของ audit** upsert ถูกจับผ่าน `EnrichAuditUsers`; ค่า config ไม่ถูก log การส่ง log `email_sent` บนเอกสาร ไม่ใช่บน profile
- **`report_email` ถูกทิ้งร้าง ไม่ได้ถูกลบ** schema, secret path และ RPC reader ยังอยู่; มีเพียงหน้าจอที่เข้าถึงไม่ได้

---

## 5. Backing Service / Data Shape (Dev)

แหล่งที่มา: tenant schema **ไม่มีตารางเฉพาะ** — row ใน `tb_application_config` สองแถว

### 5.1 `email_profiles` (Zod: `EmailProfilesSchema`, `app-config.service.ts:101-128`)

```
{
  "default_profile_id": "p-001",             // string | null
  "profiles": [
    {
      "id": "p-001",                         // required, คงที่ — secret จับคู่ด้วยค่านี้
      "name": "Purchasing",
      "enabled": true,
      "smtp": {
        "host": "smtp.example.com",
        "port": 587,                         // int 1..65535
        "secure": true,
        "username": "purchasing@example.com",
        "password": "***ENCRYPTED***"        // เข้ารหัสตอนเก็บ mask ตอนอ่าน
      },
      "from_email": "purchasing@example.com",
      "from_name": "Carmen Purchasing",
      "reply_to": "", "default_cc": [], "subject_template": "", "body_template": "", "note": ""
                                             // รับพร้อม default; ฟอร์มไม่แก้ไขอีกแล้ว
    }
  ]
}
```

### 5.2 `email_templates` (ไม่มี schema ฝั่ง backend; FE `types/email-template.ts`, seed `packages/prisma-shared-schema-tenant/src/seed-data/email-templates.ts`)

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
      "body_template": "<p>Dear {{vendor_name}}, …</p>",   // HTML, sanitise ฝั่ง client
      "default_cc": ["finance@example.com"],
      "note": ""
    }
  ]
}
```

### 5.3 Endpoints

```
GET  /api/config/:bu_code/app-config/email_profiles         licence configuration.email_profile
PUT  /api/config/:bu_code/app-config/email_profiles         { value }  (hook ส่ง doc_version กลับมา)
POST /api/config/:bu_code/app-config/test-email-profile     { profile_id, to? }  licence configuration.email_profile
GET  /api/config/:bu_code/app-config/email_templates        licence configuration.email_template
PUT  /api/config/:bu_code/app-config/email_templates        { value }
GET  /api/:bu_code/email-senders                            ไม่มี secret { default_profile_id, profiles[] }
GET  /api/:bu_code/email-messages                           คลังข้อความ
POST /api/:bu_code/purchase-orders/:id/send-email           ผู้บริโภค
POST /api/:bu_code/request-for-pricings/:id/send-email      ผู้บริโภค
```

ทั้งหมดอยู่ใต้ `KeycloakGuard`; lookup สองตัวยังไม่มี `AppIdGuard` ด้วย (`email-lookup.controller.ts:2`)

## 6. กฎทางธุรกิจ

- **Sysadmin เท่านั้นตามข้อตกลง ไม่ใช่การบังคับ** ไม่มี RBAC guard บน app-config controller (ตรวจสอบซ้ำ 2026-09-22)
- **licence ต่อกลุ่ม key** (`configuration.email_profile`, `configuration.email_template`) ผ่าน `LICENSE_ROUTE_OVERRIDES`; endpoint รายการทั่วไปซ่อนทั้งสอง key
- **การเข้ารหัสและ mask รหัสผ่าน** restore ตาม id; ค่าว่างไม่เคยลบ secret
- **default profile หนึ่งตัวต่อ BU** (`default_profile_id`); `enabled: false` คง profile ไว้แต่ควรถูกตัดออกจาก dialog ส่ง
- **คลังข้อความต่อประเภทเอกสาร** (`po`, `rfp`); ชุด placeholder คงที่; body HTML sanitise ฝั่ง frontend
- **ทุกการส่งถูก audit** เป็น `enum_activity_action.email_sent` บนเอกสาร

## 7. การอ้างอิงข้าม

- [system-config/application-config](/th/inventory/system-config/application-config) — KV store แม่; registry ของ key และการแยก licence
- [purchase-order](/th/inventory/purchase-order) — dialog *Send email* และ `POST …/send-email`
- [vendor-pricelist](/th/inventory/vendor-pricelist) — dialog *Send email* ของ RFP
- [system-config/notification-template](/th/inventory/system-config/notification-template) — การแจ้งเตือน workflow ในแอป (ไม่มีอีเมล)
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — แถว `email_sent`

## 8. แหล่งข้อมูลอ้างอิง

- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts` — `EmailProfileSchema`/`EmailProfilesSchema` (`:96-128`), `secretPathsFor` (`:216`), `retainMaskedEmailProfileSecrets` (`:396`), `getEmailProfileForSend` (`:828`), `testEmailProfile`; `app-config.module.ts` (export ให้โมดูล PO)
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts` (`test-email-profile` `:395`); `apps/backend-gateway/src/application/email-lookup/{email-lookup.controller,email-lookup.service}.ts`; `packages/prisma-shared-schema-platform/prisma/permission.route-map.ts:55-56,257-260`
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/src/seed-data/email-templates.ts`; `apps/micro-business/src/authen/tenant_seed/seed-sets/email-templates.seed-set.ts`
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/email-profile/` (`email-profile.route.tsx`, `email-profile-dialog.tsx`, `email-profile-test-dialog.tsx`, `email-profile-schema.ts`); `routes/system-admin/email-template/`; `hooks/use-email-profiles.ts`, `hooks/use-email-templates.ts`, `hooks/use-email-senders.ts`, `hooks/use-email-messages.ts`; `types/email-profile.ts`, `types/email-template.ts`, `lib/email-template.ts`; `routes/procurement/purchase-order/po-send-email-dialog.tsx`, `routes/vendor-management/request-price-list/rfp-send-email-dialog.tsx` Legacy: `routes/system-admin/config-email/` (ไม่มี route)
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/app-config/POST-test-email-profile-config-app-config.bru`
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1116-email-profile.md` (30 case), `1117-email-template.md` (30 case) — แคตตาล็อกเท่านั้น ไม่มี Playwright spec
