---
title: การตั้งค่าแอปพลิเคชัน (Application Config)
description: การตั้งค่าแบบ key-value ทั่วไปที่ถูก consume เป็นราย key (email profile, email template, interface, print/approval-flow config) ตรวจสอบซ้ำ 2026-09-22: ไม่มี RBAC guard บน endpoint; gate ด้วย licence ต่อ key ตั้งแต่ 2026-09-20
published: true
date: '2026-09-23T01:30:00.000Z'
tags: system-config, application-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# การตั้งค่าแอปพลิเคชัน (Application Config)

> **At a Glance**
> **เจ้าของ:** ไม่มีหน้าจอเดียว — แต่ละ key ถูกจัดการโดย frontend feature ที่เป็นเจ้าของมัน (Email Profile เขียน `email_profiles`, Email Template เขียน `email_templates`, Interface เขียน `interface_<category>_<brand>`) &nbsp;·&nbsp; **ตาราง:** `tb_application_config` (+ `tb_application_user_config`) &nbsp;·&nbsp; **ใช้โดย:** เก้า key ที่มี Zod schema ฝั่ง backend (§1.1) บวก `email_templates` และ key `list_views_*` / signature; **ไม่มีหน้าจอ admin "Application Settings" ทั่วไป** &nbsp;·&nbsp; **ไม่มี RBAC permission guard** บน endpoint อ่าน/เขียน นอกเหนือจาก authentication (ตรวจสอบซ้ำ 2026-09-22) ยกเว้นการตรวจ BU-admin แบบแคบสำหรับ key `list_views_*`; ตั้งแต่ 2026-09-20 ชั้น **licence** gate สามกลุ่ม key แยกกัน (`configuration.email_profile`, `configuration.email_template`, `interface`)

## สถานะการ implement (ตรวจสอบ 2026-07-16; ตรวจสอบซ้ำ 2026-09-06 และ 2026-09-22)

**อ่านซ้ำ `config_app-config.controller.ts` ที่ HEAD เมื่อ 2026-09-22** `@UseGuards(KeycloakGuard)` ระดับ class ที่ `:56` ยังเป็น guard เดียว route: `GET` (`:72`), `GET :key` (`:105`), `PUT :key` (`:141`), `DELETE :key` (`:224`), `GET signature-candidates/:doc_type` (`:305`), `POST test-email` (`:353`), `POST test-email-profile` (`:395`, ใหม่ 2026-08 — ส่งอีเมลทดสอบผ่าน sender profile ที่ระบุชื่อหนึ่งตัว `to` ไม่บังคับ) ไม่มี `AppIdGuard`, ไม่มี `@Permission`, ไม่มี `RequirePlatformPermission` บนตัวไหนเลย; `assertSharedListViewsAdmin()` (`:264`) ยังถูกเรียกเฉพาะจาก `PUT :key` (`:210`) และ `DELETE :key` (`:245`) และยัง return ออกทันทีสำหรับทุก key ที่ไม่ตรง `/^list_views_/` **ข้อค้นพบจาก PR #10 (ผู้เรียกที่ authenticated ใครก็ได้อ่านและเขียนทุก row config ระดับ tenant ได้) ยังคงอยู่** — แต่มีสองชั้นเพิ่มเข้ามารอบ ๆ มันซึ่งเปลี่ยนสิ่งที่ผู้เรียก*เข้าถึง*ได้:

1. **gate ด้วย licence ต่อ key (2026-09-20, `84667a405`)** `LicenseInterceptor` ระดับ global resolve ทุก request URL ไปยัง licence feature `config:app-config` map ไป `configuration.app_config` (ซึ่งทุก BU มี) แต่ `LICENSE_ROUTE_OVERRIDES` (`packages/prisma-shared-schema-platform/prisma/permission.route-map.ts:257-268`) map ใหม่ `…/app-config/email_profiles` และ `…/app-config/test-email-profile` → `configuration.email_profile`, `…/app-config/email_templates` → `configuration.email_template` และ key `…/app-config/interface_<category>_<brand>` แปดตัว → `interface` BU ที่สัญญาไม่มี feature นั้นได้ `403 LICENSE_REQUIRED` (หรือ `LICENSE_EXPIRED` ตอนเขียน) พร้อม `bu_codes`/`bu_names` ใน body (`c7a0d9168`) นี่คือการตรวจ **licence** (BU เป็นเจ้าของ feature หรือไม่) ไม่ใช่การตรวจ RBAC (ผู้ใช้คนนี้ทำได้หรือไม่) — ไม่ได้ปิดข้อค้นพบ
2. **endpoint รายการซ่อน key ที่แยกออกไป (2026-09-20, `9c52288c0`, `5ff86e322`)** `GET /app-config` ตอนนี้กรอง `email_profiles`, `email_templates` และ key `interface_*` ใด ๆ ออก (`config_app-config.service.ts:198` `isListExcluded`) รายการจึงใช้อ่านพวกมันภายใต้ feature ทั่วไปไม่ได้; แต่ละตัวอ่านได้ผ่าน `GET /app-config/:key` เท่านั้น ซึ่งตาราง override ครอบคลุม service ยังรัน `assertInterfaceEntitled()` สำหรับ key `interface_*` ผู้เรียกภายในของ gateway service (เช่น `EmailLookupService`) ข้าม licence gate ต่อ key โดยตั้งใจ — comment ของ module เองระบุไว้

ข้อค้นพบที่เหลือจาก 2026-09-06 ด้านล่างไม่เปลี่ยน

`tb_application_config` เป็นตารางจริงที่ถูกเขียนใช้งานอยู่ — แต่ถูก **consume เป็นราย key โดยฟีเจอร์เฉพาะ** ไม่ใช่ผ่าน editor สำหรับใช้งานทั่วไป:

- **ไม่มีหน้าจอ "System Config → Application Settings"** ไม่มี path `application-config` ใน `../carmen-inventory-frontend-react/routes/router.tsx` และไม่มี directory แบบนี้ใต้ `routes/system-admin/` ผู้บริโภคฝั่ง frontend ผ่าน `hooks/use-app-config.ts` (`useAppConfigByKey`, `useAppConfigs`, `useUpsertAppConfig`, `useTestEmail`) หรือ hook ของตัวเอง (`hooks/use-email-profiles.ts`, `hooks/use-email-templates.ts`, `routes/system-admin/interface/use-interface-config.ts`) แต่ละตัวผูกกับ key เดียว: [system-config/config-email](/th/inventory/system-config/config-email) (`email_profiles`, `email_templates`; หน้าจอ `report_email` แบบเก่ายังอยู่ใน `routes/system-admin/config-email/` แต่ **ไม่มี route แล้ว** — ไม่มี entry `config-email` ใน `router.tsx` หรือ `constant/module-list.ts` ที่ HEAD), `/system-admin/interface` (`interface_*`) และการตั้งค่า signature ของ workflow ไม่มีอะไรให้ Sysadmin browse หรือแก้ key ใดก็ได้ตามใจ
- **ไม่มี permission guard บน controller — ตรวจสอบซ้ำ 2026-09-06 ยังเปิดอยู่** `config_app-config.controller.ts` ใช้แค่ `@UseGuards(KeycloakGuard)` (authentication) ระดับ class (`:46`) ไม่มี decorator `AppIdGuard` หรือ `RequirePlatformPermission` บน route ใดเลย (ต่างจาก [system-config/document](/th/inventory/system-config/document) ที่ controller gate ทุก endpoint ด้วย `AppIdGuard('documents.*')` ที่มีชื่อชัดเจน) รอบนี้ตรวจและตัดออกเพิ่มเติม: ไม่มี `APP_GUARD` ใน `app.module.ts` ของ gateway นอกจาก throttler สำหรับจำกัดอัตรา — ซึ่งคอมเมนต์ในไฟล์ระบุเองว่าเป็นคนละแกนกับการตรวจสิทธิ์ — และไม่มี guard ที่ลงทะเบียนใน `config_app-config.module.ts` **ผู้เรียกที่ authenticated ใครก็ได้อ่านและเขียนทุก row config ระดับ tenant ได้ รวมถึง SMTP credentials**

  ไม่มี `x-app-id` ให้พึ่ง: `@ApiHeaderRequiredXAppId()` ประกาศ header ไว้สำหรับ Swagger เท่านั้น และไม่มี `AppIdGuard` ที่นี่ ข้อความเดิมในหน้านี้ที่สื่อว่าต้องมี "`x-app-id` ที่ลงทะเบียนถูกต้อง" ถูกแก้แล้ว — authentication คือด่านเดียว

  **ข้อยกเว้นหนึ่งเดียว ที่เพิ่มเข้ามาหลังหน้านี้ถูกเขียน:** commit `1b76f2caa` (2026-07-29) เพิ่ม `assertSharedListViewsAdmin()` (`:256-287`) เรียกจาก `PUT :key` (`:202`) และ `DELETE :key` (`:237`) บังคับให้ต้องมี role **`admin` ระดับ BU** ของ `bu_code` เป้าหมาย แต่เฉพาะ key ที่ตรงกับ `/^list_views_/` (`:262`) เท่านั้น key อื่นทั้งหมด return ออกทันทีโดยไม่ตรวจ ส่วน `GET`, `GET :key`, `signature-candidates` และ `POST test-email` ไม่มีการตรวจเลย role ถูกอ่านจาก header `x-bu-datas` ซึ่ง `KeycloakGuard` เขียนทับทุกคำขอที่ authenticate แล้ว (`keycloak.guard.ts:192`, `:211`, `:301`, `:327`) จึงปลอมจากฝั่ง client ไม่ได้ และ fail closed เมื่อไม่มี header

  การ gate ด้วย "App ID `app-config.upsert`" ที่อธิบายไว้ด้านล่างในหน้านี้ และใน [system-config/config-email](/th/inventory/system-config/config-email) **ไม่ได้ implement ใน backend** การบังคับใช้ (ถ้ามี) มีแค่ระดับ navigation/route ฝั่ง frontend ไม่ใช่ server-side check

Schema, JSONB shape และคำอธิบายลำดับการ resolve ด้านล่างยังคงถูกต้องสำหรับ row ที่มีจริง (`report_email`, การตั้งค่าที่เกี่ยวกับ `signature-candidates`); ตาราง "งานทั่วไป" ถูกแก้ไขให้ลบหน้าจอ admin ทั่วไปที่ไม่มีอยู่จริงออกแล้ว

## 1. คืออะไรและใครใช้

Application Config คือ **ที่เก็บ key-value ทั่วไป** สำหรับการตั้งค่าที่ไม่คุ้มที่จะมี schema เฉพาะของตัวเอง ตารางสองตารางใช้ shape เดียวกัน: `tb_application_config` เก็บการตั้งค่าระดับ tenant (การใช้งานจริงที่ยืนยันแล้ว: SMTP profile `report_email` ที่ consume โดย [system-config/config-email](/th/inventory/system-config/config-email)) และ `tb_application_user_config` เก็บการ override preference ต่อผู้ใช้ (ลำดับคอลัมน์ของตาราง ฟิลเตอร์ที่บันทึก theme location เริ่มต้น) — การใช้งานจริงฝั่ง frontend ของตารางที่สองนี้ไม่ได้ถูก re-verify แยกในรอบนี้ ทั้งคู่เก็บค่าเป็น JSONB ดังนั้น shape ใดก็ตาม — string, number, object, array — ใช้งานได้โดยไม่ต้อง migration

รูปแบบนี้คือ *ทางออก* — การตั้งค่าขนาดเล็กที่ไม่อย่างนั้นจะ pollute schema เป็นตารางคอลัมน์เดียวมาอยู่ที่นี่ภายใต้ key ที่เสถียร trade-off: schema ไม่บังคับ shape — consumer ต้อง validate ตอนอ่าน (ยืนยัน: `report_email` ถูก validate ด้วย Zod ผ่าน `ReportEmailSchema` ใน `app-config.service.ts`)

**บำรุงรักษาโดย** ฟีเจอร์ frontend ที่เป็นเจ้าของ key นั้นๆ (ไม่มี editor Sysadmin ทั่วไป) **อ่านโดย** ฟีเจอร์เฉพาะที่นิยาม key นั้น — ไม่ใช่ "ทุก list view" ซึ่งยังไม่ยืนยันและถูกลบออกแล้ว

### 1.1 registry ของ key ที่ HEAD (ตรวจสอบ 2026-09-22)

`AppConfigService.validateValue()` (`apps/micro-business/src/app-config/app-config.service.ts:488-500`) คือสิ่งที่ใกล้เคียง schema registry ที่สุด key ที่มี Zod schema ฝั่ง backend:

| Key | Schema | path ของ secret (encrypt at rest, mask เป็น `***ENCRYPTED***` ตอนอ่าน) | หน้าจอ / ฟีเจอร์ที่เป็นเจ้าของ |
|---|---|---|---|
| `report_email` | `ReportEmailSchema` | `smtp.password` | config SMTP เดี่ยวแบบ legacy (หน้าจอไม่มี route); `getReportEmailForSend` |
| `email_profiles` | `EmailProfilesSchema` (`{ default_profile_id, profiles[] }`) | `profiles.*.smtp.password` (wildcard — restore ตาม id ไม่ใช่ตาม index, `49162675a`) | `/system-admin/email-profile`; `getEmailProfileForSend` (อีเมล PO / RFP) |
| `gl_setting` | `GlSettingSchema` | — | โมดูล GL (นอกขอบเขต) |
| `pr_approval_flow`, `po_approval_flow` | `ApprovalFlowSchema` | — | candidate ของ approval stage PR / PO (`min_required_last_n`) |
| `pr_print_config`, `po_print_config`, `grn_print_config`, `sr_print_config` | `PrintConfigSchema` | — | ชั้น print |
| `interface_accounting_carmen_gl` | `InterfaceAccountingCarmenGlSchema` | `authorize_token` | `/system-admin/interface` |
| `interface_accounting_<brand>` (blueledgers, external) | `InterfaceAccountingSchema` | — | `/system-admin/interface` |
| `interface_pos_<brand>`, `interface_pms_<brand>` | `InterfacePosSchema` / `InterfacePmsSchema` (จับคู่ด้วย pattern) | `api_key` | `/system-admin/interface` |

`email_templates` (`{ defaults, templates[] }`, seed โดย `packages/prisma-shared-schema-tenant/src/seed-data/email-templates.ts`) **ไม่มี entry ใน `schemaByKey`** — backend เก็บอะไรก็ตามที่ client ส่งมา; body HTML ถูก sanitise ฝั่ง frontend เท่านั้น (`sanitizeEmailHtml`, `types/email-template.ts`) การตั้งค่า signature (`signature-candidates/:doc_type`) และ `list_views_*` ก็อ่าน/เขียนโดยไม่มี schema เช่นกัน

## 2. งานทั่วไป

ไม่มี editor ทั่วไป — มีแค่งานเฉพาะฟีเจอร์ด้านล่างที่ยืนยันแล้ว

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| จัดการ SMTP sender profile | `/system-admin/email-profile` — ดู [system-config/config-email](/th/inventory/system-config/config-email) | `PUT /app-config/email_profiles`; ทดสอบ profile หนึ่งตัวด้วย `POST /app-config/test-email-profile` `{ profile_id, to? }` |
| จัดการคลังข้อความอีเมลขาออก | `/system-admin/email-template` — ดู [system-config/config-email](/th/inventory/system-config/config-email) | `PUT /app-config/email_templates` |
| ตั้งค่า interface accounting / POS / PMS | `/system-admin/interface/:category/:brand` (`interface-registry.ts`) | `PUT /app-config/interface_<category>_<brand>`; licence เท่านั้น (feature `interface` จาก INF licence ของ BU) ไม่มี permission key |
| ค้นหา signature candidate สำหรับ document type | การตั้งค่า signature ของ workflow | `GET /app-config/signature-candidates/:doc_type` |
| อ่าน / บันทึก preference ต่อผู้ใช้ | `GET` / `PUT api/config/:bu_code/app-user-config/:key` (`config_app-user-config.controller.ts:54,89`; Bruno `config/app-user-config/{GET-get,PUT-upsert}`) | backed โดย `tb_application_user_config`; ยังไม่ได้ trace ว่าหน้าจอไหนใช้ในรอบนี้ |
| เพิ่ม key ระดับ tenant ใหม่ | แก้โค้ด backend | เพิ่ม schema ใน `validateValue()` (และ secret path ถ้าจำเป็น) แล้วเพิ่มหน้าจอฟีเจอร์ — ไม่มี admin UI |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Key collision ตอน insert | มี row ที่ไม่ถูก delete อยู่แล้ว | Update row เดิมหรือเลือก key อื่น |
| Value ถูก reject ตอน runtime | Zod schema mismatch (ยืนยันสำหรับ `ReportEmailSchema` ของ `report_email`) | แก้ shape ตาม contract ของ consumer |
| ผู้ใช้ที่ authenticated ใครก็ได้อ่าน/เขียน config key ใดก็ได้ | ไม่มี RBAC guard บน `config_app-config.controller.ts` | **ช่องโหว่ที่ยืนยันแล้ว — ยังเปิดอยู่ ตรวจสอบซ้ำ 2026-09-22** มีเพียง key `list_views_*` ที่ถูกป้องกัน และเฉพาะบน `PUT`/`DELETE`; การแยก licence เมื่อ 2026-09-20 gate ว่า *BU ไหน* เข้าถึง `email_profiles` / `email_templates` / `interface_*` ได้ ไม่ใช่ *ผู้ใช้คนไหน* |
| `403 LICENSE_REQUIRED` / `LICENSE_EXPIRED` บน `GET`/`PUT /app-config/email_profiles`, `/email_templates`, `/interface_*` | สัญญาของ BU ไม่มี `configuration.email_profile` / `configuration.email_template` / `interface` (INF licence) | ซื้อ / ต่ออายุผ่าน Platform; `GET /api/license` แสดง `features[]` / `expired_features[]` ต่อ BU |
| `GET /app-config` ไม่มี `email_profiles`, `email_templates`, `interface_*` | เป็นไปตามคาดตั้งแต่ `9c52288c0` — อ่านตาม key | ใช้ `GET /app-config/:key` |
| Secret รั่ว | เก็บ credentials ใน config | ย้ายไป env / secrets manager — config แก้ไขได้โดยมนุษย์; หมายเหตุ `smtp.password` ของ `report_email` *ถูก* encrypt at rest (ดู [system-config/config-email](/th/inventory/system-config/config-email)) |

## 4. กรณีพิเศษ

- **Schema by convention** ไม่มีการบังคับ shape ระดับ DB บน `value` — code ที่ consume เป็นเจ้าของ shape
- **ไม่มี backend permission check** ยืนยันว่าไม่มี — ดูสถานะการ implement ด้านบน
- **ไม่มี secret แบบ plaintext** ฟิลด์ password ของ `report_email` คือข้อยกเว้นเดียวที่ยืนยันว่า encrypt; ไม่พบ key อื่นที่ยืนยันว่าเก็บ secret
- **Hard-delete ใช้ได้** สำหรับ row ระดับ tenant (fallback ไปที่ default ที่ compile-time) — ยังไม่ได้ re-verify ในรอบนี้ สืบทอดจากเอกสารเดิม

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_application_config`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `key` | `String @db.VarChar` | No | Key ของการตั้งค่า ที่ยืนยันว่าใช้จริง: ดู §1.1 |
| `value` | `Json @db.JsonB` | No | Default `{}` Shape นิยามโดยแอปพลิเคชันต่อ key |
| `doc_version` | `Int` | No | Default `0` Optimistic-concurrency token — ยืนยันว่าใช้จริง (ดู payload `PATCH` ใน [system-config/config-email](/th/inventory/system-config/config-email)) |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([key, deleted_at])` Index บน `[key]`

### 5.2 `tb_application_user_config`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String @db.Uuid` | No | เจ้าของ (cross-schema ไปยัง `tb_user` ของแพลตฟอร์ม) |
| `key` | `String @db.VarChar` | No | Key ของ preference — ยังไม่ได้ re-verify แยกในรอบนี้ |
| `value` | `Json @db.JsonB` | No | Default `{}` |
| `doc_version` | `Int` | No | Default `0` Optimistic-concurrency token |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([user_id, key, deleted_at])` Index บน `[user_id, key]` ไม่มี FK ไปยัง `tb_user` (cross-schema)

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว (ระดับ schema)** `key` unique ใน row ที่ไม่ถูก delete ในตาราง tenant; `(user_id, key)` unique ในตาราง user
- **Schema by convention** Consumer validate shape ตอนอ่าน; ยืนยันสำหรับ `report_email` ผ่าน `ReportEmailSchema`
- **ไม่มี backend permission check** บนการอ่าน/เขียน `tb_application_config` — ดูสถานะการ implement ด้านบน
- **ลำดับการ resolve, ข้อตกลง key namespace, hard-delete-ใช้ได้** — สืบทอดจากเอกสารเดิมเป็นเจตนาการออกแบบ; ยังไม่ได้ re-verify แยกในรอบนี้
- **ค่าที่ sensitive** path ที่ encrypt at rest ระบุไว้ใน `secretPathsFor()` (`:216-225`): `report_email.smtp.password`, `email_profiles.profiles[*].smtp.password`, `interface_accounting_carmen_gl.authorize_token`, `interface_pos_*` / `interface_pms_*` `.api_key` ค่าว่างหรือค่าที่ mask ที่ post กลับมาจะคง secret ที่เก็บไว้ (`3580f5142`); การล้าง secret ทำด้วย `enabled: false` ไม่ใช่ string ว่าง ไม่มีการบังคับแบบเหมารวมสำหรับ key อื่น
- **licence ไม่ใช่ permission ต่อกลุ่ม key** `configuration.app_config` ครอบคลุม route ทั่วไป; `configuration.email_profile`, `configuration.email_template` และ `interface` ครอบคลุมกลุ่ม key ของตน (2026-09-20) RBAC resource `configuration.app_config` มีอยู่ใน `tb_permission` แต่ไม่มี route ใน controller นี้ตรวจมัน

## 7. การอ้างอิงข้าม

- [system-config/config-email](/th/inventory/system-config/config-email) — `email_profiles` + `email_templates` (และ `report_email` แบบ legacy)
- `/system-admin/interface` (ยังไม่มีหน้า wiki) — key `interface_*` licence เท่านั้น
- การตั้งค่า signature ของ workflow — ผู้บริโภคของ `signature-candidates/:doc_type`
- "preference ของ list view ผ่าน `tb_application_user_config`" ของโมดูลอื่น — ยังไม่ได้ re-verify แยกในรอบนี้ เก็บไว้เป็นเจตนาการออกแบบที่ยังไม่ยืนยัน

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~5287-5301), `tb_application_user_config` (lines ~5304-5319)
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts`
- **Backend gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts` — อ่านซ้ำ 2026-09-22: `KeycloakGuard` ระดับ class (`:56`) เท่านั้น; การตรวจสิทธิ์เพียงอย่างเดียวคือ `assertSharedListViewsAdmin()` (`:264`) ซึ่งจำกัดที่ key แบบ `list_views_*` gateway service `config_app-config.service.ts` (`isListExcluded` `:198`, `assertInterfaceEntitled` `:94`)
- **ชั้น licence:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/permission.route-map.ts` (`LICENSE_ROUTE_OVERRIDES` `:257-268`); `apps/backend-gateway/src/license/{license.interceptor,license-route-resolver,license.evaluator}.ts`; `GET /api/license` (`license.controller.ts:40`)
- **config ต่อผู้ใช้:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-user-config/config_app-user-config.controller.ts`; Bruno `config/app-user-config/`
- **Frontend:** ไม่มีหน้าจอ admin ทั่วไป ผู้บริโภค: `../carmen-inventory-frontend-react/hooks/use-app-config.ts`, `hooks/use-email-profiles.ts`, `hooks/use-email-templates.ts`, `routes/system-admin/interface/use-interface-config.ts`; หน้าจอ `routes/system-admin/email-profile/`, `routes/system-admin/email-template/`, `routes/system-admin/interface/` `routes/system-admin/config-email/` ยังอยู่บนดิสก์แต่ไม่มี route
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/app-config/POST-test-email-profile-config-app-config.bru`, `config/app_config/`
