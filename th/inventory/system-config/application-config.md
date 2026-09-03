---
title: การตั้งค่าแอปพลิเคชัน (Application Config)
description: การตั้งค่าแอปพลิเคชันแบบ key-value ทั่วไป — เป็น backing store จริงที่ใช้งานอยู่ (config-email, การตั้งค่า signature) ที่ถูก consume เป็นราย key โดยฟีเจอร์เฉพาะ แต่ไม่มีหน้าจอ Sysadmin สำหรับ browse/edit ทั่วไป และไม่มี permission guard บน endpoint อ่าน/เขียนเลย
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, application-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# การตั้งค่าแอปพลิเคชัน (Application Config)

> **At a Glance**
> **เจ้าของ:** ไม่มีหน้าจอเดียว — แต่ละ key ถูกจัดการโดย frontend feature ที่เป็นเจ้าของมัน (เช่น Email Configuration เขียน `report_email`) &nbsp;·&nbsp; **ตาราง:** `tb_application_config` (+ `tb_application_user_config`) &nbsp;·&nbsp; **ใช้โดย:** ยืนยันจริงสำหรับ `report_email` (SMTP) และการตั้งค่า signature; **ไม่มีหน้าจอ admin "Application Settings" ทั่วไป** &nbsp;·&nbsp; **ไม่มี permission guard** บน endpoint อ่าน/เขียน นอกเหนือจาก authentication พื้นฐาน

## สถานะการ implement (ตรวจสอบ 2026-07-16)

`tb_application_config` เป็นตารางจริงที่ถูกเขียนใช้งานอยู่ — แต่ถูก **consume เป็นราย key โดยฟีเจอร์เฉพาะ** ไม่ใช่ผ่าน editor สำหรับใช้งานทั่วไป:

- **ไม่มีหน้าจอ "System Config → Application Settings"** ไม่มี path `application-config` ใน `../carmen-inventory-frontend-react/routes/router.tsx` และไม่มี directory แบบนี้ใต้ `routes/system-admin/` ผู้บริโภคฝั่ง frontend มีเพียง `hooks/use-app-config.ts` (`useAppConfigByKey`, `useUpsertAppConfig`, `useTestEmail`) ที่ถูกเรียกโดยฟีเจอร์เฉพาะชื่อ: [system-config/config-email](/th/inventory/system-config/config-email) (key `report_email`) และหน้าจอ signature-candidates ของ workflow (`signature-config.tsx`) ไม่มีอะไรให้ Sysadmin browse หรือแก้ key ใดก็ได้ตามใจ
- **ไม่มี permission guard บน controller** `config_app-config.controller.ts` ใช้แค่ `KeycloakGuard` (authentication) ระดับ class — ไม่มี decorator `AppIdGuard` หรือ `RequirePlatformPermission` บน endpoint list/get/upsert ใดเลย (ต่างจาก [system-config/document](/th/inventory/system-config/document) ที่ controller gate ทุก endpoint ด้วย `AppIdGuard('documents.*')` ที่มีชื่อชัดเจน) การ gate ด้วย "App ID `app-config.upsert`" ที่อธิบายไว้ด้านล่างในหน้านี้ และใน [system-config/config-email](/th/inventory/system-config/config-email) **ไม่ได้ implement ใน backend** — ผู้เรียกที่ authenticated แล้วพร้อม `x-app-id` ที่ลงทะเบียนถูกต้องสามารถอ่านและเขียนทุก row config ระดับ tenant ได้ รวมถึง SMTP credentials การบังคับใช้ (ถ้ามี) มีแค่ระดับ navigation/route ฝั่ง frontend ไม่ใช่ server-side check

Schema, JSONB shape และคำอธิบายลำดับการ resolve ด้านล่างยังคงถูกต้องสำหรับ row ที่มีจริง (`report_email`, การตั้งค่าที่เกี่ยวกับ `signature-candidates`); ตาราง "งานทั่วไป" ถูกแก้ไขให้ลบหน้าจอ admin ทั่วไปที่ไม่มีอยู่จริงออกแล้ว

## 1. คืออะไรและใครใช้

Application Config คือ **ที่เก็บ key-value ทั่วไป** สำหรับการตั้งค่าที่ไม่คุ้มที่จะมี schema เฉพาะของตัวเอง ตารางสองตารางใช้ shape เดียวกัน: `tb_application_config` เก็บการตั้งค่าระดับ tenant (การใช้งานจริงที่ยืนยันแล้ว: SMTP profile `report_email` ที่ consume โดย [system-config/config-email](/th/inventory/system-config/config-email)) และ `tb_application_user_config` เก็บการ override preference ต่อผู้ใช้ (ลำดับคอลัมน์ของตาราง ฟิลเตอร์ที่บันทึก theme location เริ่มต้น) — การใช้งานจริงฝั่ง frontend ของตารางที่สองนี้ไม่ได้ถูก re-verify แยกในรอบนี้ ทั้งคู่เก็บค่าเป็น JSONB ดังนั้น shape ใดก็ตาม — string, number, object, array — ใช้งานได้โดยไม่ต้อง migration

รูปแบบนี้คือ *ทางออก* — การตั้งค่าขนาดเล็กที่ไม่อย่างนั้นจะ pollute schema เป็นตารางคอลัมน์เดียวมาอยู่ที่นี่ภายใต้ key ที่เสถียร trade-off: schema ไม่บังคับ shape — consumer ต้อง validate ตอนอ่าน (ยืนยัน: `report_email` ถูก validate ด้วย Zod ผ่าน `ReportEmailSchema` ใน `app-config.service.ts`)

**บำรุงรักษาโดย** ฟีเจอร์ frontend ที่เป็นเจ้าของ key นั้นๆ (ไม่มี editor Sysadmin ทั่วไป) **อ่านโดย** ฟีเจอร์เฉพาะที่นิยาม key นั้น — ไม่ใช่ "ทุก list view" ซึ่งยังไม่ยืนยันและถูกลบออกแล้ว

## 2. งานทั่วไป

ไม่มี editor ทั่วไป — มีแค่งานเฉพาะฟีเจอร์ด้านล่างที่ยืนยันแล้ว

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ตั้งค่า SMTP ขาออก | [system-config/config-email](/th/inventory/system-config/config-email) | เขียน `tb_application_config` key `report_email` ผ่าน `useUpsertAppConfig` |
| ค้นหา signature candidate สำหรับ document type | การตั้งค่า signature ของ workflow (`signature-config.tsx`) | อ่านผ่าน `useSignatureCandidates` backed โดย app-config service เดียวกัน |
| เพิ่ม key ระดับ tenant ใหม่ | แก้โค้ด backend | ไม่มี admin UI — ฟีเจอร์ใหม่ต้องเรียก `useAppConfigByKey`/`useUpsertAppConfig` ด้วย key ของตัวเองและเพิ่มหน้าจอของตัวเอง |
| จัดเรียงคอลัมน์ใหม่ (ต่อผู้ใช้) | ~~ลากใน list view ใดก็ได้~~ | ยังไม่ยืนยันในรอบนี้ — ยังไม่ได้ re-verify กับ `tb_application_user_config` |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Key collision ตอน insert | มี row ที่ไม่ถูก delete อยู่แล้ว | Update row เดิมหรือเลือก key อื่น |
| Value ถูก reject ตอน runtime | Zod schema mismatch (ยืนยันสำหรับ `ReportEmailSchema` ของ `report_email`) | แก้ shape ตาม contract ของ consumer |
| ผู้ใช้ที่ authenticated ใครก็ได้อ่าน/เขียน config key ใดก็ได้ | ไม่มี permission guard บน `config_app-config.controller.ts` | ช่องโหว่ที่ยืนยันแล้ว — flag ไว้สำหรับติดตามผลต่อ ไม่ได้แก้ในรอบนี้ |
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
| `key` | `String @db.VarChar` | No | Key ของการตั้งค่า ที่ยืนยันว่าใช้จริง: `report_email` |
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
- **ค่าที่ sensitive** `smtp.password` ของ `report_email` คือฟิลด์เดียวที่ยืนยัน encrypt at rest; ไม่พบการบังคับแบบเหมารวมสำหรับ key อื่น

## 7. การอ้างอิงข้าม

- [system-config/config-email](/th/inventory/system-config/config-email) — ผู้ใช้จริงที่ยืนยันแล้วเพียงหนึ่งเดียว (key `report_email`)
- การตั้งค่า signature ของ workflow (`signature-config.tsx`) — ผู้ใช้จริงที่ยืนยันแล้วผ่าน `useSignatureCandidates`
- "preference ของ list view ผ่าน `tb_application_user_config`" ของโมดูลอื่น — ยังไม่ได้ re-verify แยกในรอบนี้ เก็บไว้เป็นเจตนาการออกแบบที่ยังไม่ยืนยัน

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~5287-5301), `tb_application_user_config` (lines ~5304-5319)
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts`
- **Backend gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts` — ยืนยันว่าไม่มี `AppIdGuard`/`RequirePlatformPermission`
- **Frontend:** ไม่มีหน้าจอ admin ทั่วไป ผู้บริโภค: `../carmen-inventory-frontend-react/hooks/use-app-config.ts` (`useAppConfigByKey`, `useUpsertAppConfig`, `useTestEmail`, `useSignatureCandidates`) ใช้โดย `routes/system-admin/config-email/` และ `routes/system-admin/signature-config.tsx`
