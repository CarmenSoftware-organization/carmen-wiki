---
title: การตั้งค่าแพลตฟอร์ม — โมเดลข้อมูล (Data Model)
description: tb_platform_config ตารางแบบ namespace-ต่อ-แถว, PLATFORM_CONFIG_REGISTRY เต็มสิบคีย์ (แปดคีย์อยู่บนหน้าจอของโมดูลนี้เอง สองคีย์เป็นของโมดูลอื่น) และแผนที่ผู้อ่านหลายกระบวนการที่อยู่เบื้องหลังผลจริงของแต่ละคีย์
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, platform-config, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การตั้งค่าแพลตฟอร์ม — โมเดลข้อมูล (Data Model)

> **At a Glance**
> **`tb_platform_config`** — หนึ่งแถวต่อหนึ่ง config *namespace* (ออบเจกต์ JSON) ไม่เคยเป็นสเกลาร์เดี่ยว &nbsp;·&nbsp; **`PLATFORM_CONFIG_REGISTRY`** (micro-cluster) — แหล่งความจริงเดียวว่ามีคีย์อะไรบ้าง schema ฝั่งอ่าน/เขียนของแต่ละคีย์เป็น Zod แบบไหน และ default คืออะไร รวมสิบคีย์ แปดคีย์ render โดยหน้าจอของโมดูลนี้เอง (§3) &nbsp;·&nbsp; **ตรวจสองชั้นอิสระต่อกัน:** controller ฝั่ง gateway ตรวจส่วน `:config_key` ของ path ด้วย regex ก่อนถึงชั้น service ใด ๆ; `PlatformConfigService` ของ micro-cluster ตรวจการเป็นสมาชิกของ registry และค่ากับ Zod schema ของคีย์นั้นแยกต่างหากอีกที &nbsp;·&nbsp; **Concurrency:** `doc_version` มีเป็นคอลัมน์แต่**ไม่มี**เส้นทางเขียนไหนบังคับใช้เป็น optimistic lock ในวันนี้ &nbsp;·&nbsp; **หน้าจอเองไม่มี cache** — `GET /api-system/platform/configs` อ่านสดเสมอ ส่วน cache 60 วินาทีที่เอกสารไว้ใน [หน้าลงจอด](/th/platform/platform-config) §3.2 เป็นของ*ผู้อ่านฝั่งบังคับใช้*สามตัวที่เฉพาะเจาะจง ไม่ใช่ของ service อ่าน/เขียนตารางนี้เอง

> **Source of truth:** Prisma schema ฝั่ง backend และ registry ของ micro-cluster ที่นิยามทุกคีย์ อ่านสองไฟล์นี้ก่อนเสมอเมื่อจะเขียนหรือปรับหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.service.ts`
>
> ยืนยันกับ `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) และ `carmen-platform` HEAD `157a65e` (2026-09-04)

## 1. ภาพรวม

`tb_platform_config` คือตารางเดียวที่รับหน้าที่แทนอย่างน้อยสิบค่าตั้งที่ไม่เกี่ยวข้องกันเลย แยกกันด้วยสตริง `key` กับ JSONB `value` เท่านั้น ไม่มีตารางแยกต่อคีย์ ไม่มีชุดคอลัมน์แยกต่อคีย์ — ทุกฟิลด์ของทุกค่าตั้งอยู่ในออบเจกต์ JSON ก้อนเดียวนั้น และสิ่งเดียวที่บอกว่าฟิลด์ไหนถูกต้อง ต้องเป็นชนิดอะไร และควรคืนอะไรเมื่อแถวยังไม่มี คือ registry ในโค้ดตัวเดียว `PLATFORM_CONFIG_REGISTRY` (§3) ซึ่งอยู่ใน service ของ **micro-cluster** ไม่ใช่ใน controller ของ gateway ที่ UI ของโมดูลนี้คุยด้วยตรง ๆ gateway (`platform_configs.controller.ts`) เป็นแค่ตัวส่งต่อบาง ๆ: บังคับสองด่าน RBAC ที่เอกสารไว้ใน[หน้าลงจอด](/th/platform/platform-config) §4 แล้วส่งต่อไป micro-cluster ผ่าน RPC ซึ่งเป็นที่ที่ค่าทุกตัวถูกตรวจ เติม default และเขียนจริง

## 2. Entity: `tb_platform_config`

Schema บรรทัด 1462 (`../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1462-1477`)

| ฟิลด์ | ชนิด Prisma | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | Primary key, `gen_random_uuid()` |
| `key` | `String @db.VarChar` | ไม่ | namespace ของ config เช่น `invitation`, `license` — หนึ่งในสิบคีย์ของ `PLATFORM_CONFIG_KEYS` (§3) ค่าอื่นถูกปฏิเสธก่อนถึงตารางนี้ |
| `value` | `Json @default("{}") @db.JsonB` | ไม่ | ค่าตั้งทั้งหมดของ namespace นั้น เป็นออบเจกต์ JSON ก้อนเดียว ไม่เคยเป็นสเกลาร์ |
| `doc_version` | `Int @default(0) @db.Integer` | ไม่ | มีอยู่ในตาราง **ไม่ถูกอ่านหรือเพิ่มค่าโดยเส้นทางเขียนใดที่พบ** (§5) |
| ชุด audit + soft delete | — | ใช่ | `created_at`/`created_by_id`/`updated_at`/`updated_by_id`/`deleted_at`/`deleted_by_id` แบบมาตรฐาน |

**Constraints:** `@@unique([key, deleted_at], map: "platform_config_key_u")` **Indexes:** `(key)`, map `platform_config_key_idx`

**Unique constraint นี้ไม่ได้บังคับแถวที่ยังไม่ถูกลบจริง ๆ** unique index บน `(key, deleted_at)` กันแค่ไม่ให้สองแถวมี `key` เดียวกัน**และ** `deleted_at` เท่ากัน — เพราะทุกแถวที่ยังไม่ถูกลบมี `deleted_at = NULL` และ SQL ถือว่า `NULL` แต่ละตัวต่างกันเสมอสำหรับการตรวจ uniqueness ฐานข้อมูลจึง**ไม่**กันสองแถวที่ยังไม่ถูกลบให้มี key เดียวกันได้จริง คอมเมนต์ของ `PlatformConfigService.findAll()` เองระบุเรื่องนี้ตรง ๆ และป้องกันด้วยโครงสร้างแทนการพึ่ง constraint: มัน query ด้วย `orderBy: { updated_at: 'asc' }` แล้วพับผลลงใน `Map` ที่ key ด้วย `key` ถ้ามีแถวซ้ำที่ยังไม่ถูกลบเกิดขึ้นจริง แถวที่อัปเดตล่าสุดจะชนะแบบเงียบ ๆ — ทุกเส้นทางอ่านอื่น (`findOne`, `patch`, `upsert`) ก็ใช้แพทเทิร์นเดียวกันอย่างเป็นอิสระต่อกัน คือ `orderBy: { updated_at: 'desc' }` แล้วเอาแถวแรก นี่คือรูปแบบ dead-on-active-rows เดียวกับที่วิกินี้เคยเอกสารไว้สำหรับ uniqueness ของ `tb_business_unit.code` ในโมดูลอื่น — ควรจำได้ทันทีที่เห็น ไม่ต้องมานั่งไล่ซ้ำทุกครั้ง

## 3. `PLATFORM_CONFIG_REGISTRY` — ทุกคีย์ ครบทุกตัว

นิยามไว้ที่เดียว `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts:260-369` รวมสิบคีย์ สองคีย์สุดท้ายไม่เคย render โดยหน้าจอของโมดูลนี้เอง (ดู §3.5 ของหน้าลงจอดว่าทำไม และใครเป็นเจ้าของแทน)

| คีย์ | ฟิลด์ — ชนิด (ขอบเขต), default | อยู่บนหน้าจอนี้ไหม |
| --- | --- | --- |
| `invitation` | `base_url: string (url)` = `http://localhost:3000/invitations`; `expiry_days: int (1–365)` = `7`; `max_per_admin_per_hour: int (บวก ไม่มีเพดาน)` = `100`; `max_per_cluster_per_day: int (บวก ไม่มีเพดาน)` = `500` | ใช่ — แยกสองการ์ด (หน้าลงจอด §3.1) |
| `signup` | `verify_base_url: string (url)` = `http://localhost:3000/register/verify`; `link_expiry_hours: int (1–720)` = `24` | ใช่ |
| `email_verification` | `base_url: string (url)` = `http://localhost:3000/verify-email`; `expiry_hours: int (1–720)` = `24` | ใช่ |
| `password_reset` | `base_url: string (url)` = `http://localhost:3000`; `expiry_hours: int (1–720)` = `24` | ใช่ |
| `notification_email` | `enabled: boolean` = `false`; `recipients: string[] (email)` = `[]`; `cc: string[] (email)` = `[]`; `subject_prefix: string (ยาวไม่เกิน 64)` = `''` | ใช่ — ดูข้อสังเกต "ยังไม่พบผู้อ่าน" ที่หน้าลงจอด §3.2 |
| `license` | `enforcement_enabled: boolean` = `false` | ใช่ |
| `expiry_thresholds` | `subscription_days: int (1–365)` = `30`; `bu_quota_days: int (1–365)` = `30`; `seat_days: int (1–365)` = `30` | ใช่ |
| `platform_migration` | `api_enabled: boolean` = `false` | ใช่ |
| `email_routing` | `default: string (uuid)`; `register`, `verify_email`, `invitation`, `forgot_password`, `notification`: `string (uuid)` ทั้งหมด optional | **ไม่** — แก้จากโมดูล Email Settings (หน้าลงจอด §3.5) |
| `feature_flags` | `Record<string, 'active' \| 'inactive' \| 'hide'>` (ชุดคีย์แบบอิสระ) default `{}` | **ไม่** — เข้าถึงได้ผ่านคู่ `/api-system/platform/feature-flags` เฉพาะของตัวเองเท่านั้น (หน้าลงจอด §3.5) |

**`.default()` เป็นความสะดวกฝั่งอ่านเท่านั้น** ทุกฟิลด์ตัวเลข/บูลีนด้านบนมี `.default()` บน schema ฝั่ง*อ่าน* เพื่อให้แถวที่บันทึกไว้ก่อนมีฟิลด์นั้นยัง parse ผ่าน (`platform-config.schema.ts:146-149`) schema ฝั่ง*เขียน*ถอด `.default()` ออกทุกตัว (`toWriteSchema()`, บรรทัด 405-434) — payload ของ `PATCH` ที่ไม่ส่งฟิลด์ใดมาคือ "ปล่อยไว้เหมือนเดิม" จริง ๆ (ผสานจากค่าที่เก็บไว้เดิม, §5) ไม่เคยถูกบังคับให้เท่ากับ default เงียบ ๆ

## 4. ใครอ่านแต่ละคีย์จริง — ผลที่อยู่เบื้องหลัง §3.2 ของหน้าลงจอด

ไม่มีคีย์ใดในตารางนี้ที่ถูกอ่านโดยหน้าจอที่แก้มันเท่านั้น ตารางนี้รวมผู้อ่านที่ยืนยันแล้วทุกตัว process ของมัน และว่า cache หรือไม่

| คีย์ | ผู้อ่าน | Cache | ทิศทางเมื่ออ่านไม่ได้/ค่าไม่ถูกต้อง |
| --- | --- | --- | --- |
| `invitation` | เส้นทางออกคำเชิญของ micro-cluster (`PlatformConfigService.getInvitationConfig()`, `platform-config.service.ts:389-397`) | ไม่พบ — อ่านสดทุกครั้ง | Throw (`parseStored()` throw เมื่อไม่ตรง schema — ตั้งใจ ดูคอมเมนต์ของ service เองว่าทำไมการ fallback เงียบ ๆ แย่กว่าการล้มดัง ๆ สำหรับลิงก์ที่อีเมลกำลังจะส่ง) |
| `signup`, `email_verification`, `password_reset` | `auth.service.ts` ของ micro-business (`readSignupConfig`/`readEmailVerificationConfig`/`readPasswordResetConfig`, บรรทัด 319-350) อ่าน `tb_platform_config` ตรง ๆ (คนละ process กับ micro-cluster) | ไม่พบ — อ่านสดทุกครั้ง | **Throw** — คอมเมนต์ของ service เองระบุตรง ๆ: แถวที่เก็บไว้ไม่ถูกต้องแปลว่ามีคนแก้ฐานข้อมูลตรง การ fallback เงียบ ๆ ไปใช้ default จะส่งลิงก์ที่ผิดออกไปโดยไม่มีสัญญาณเตือน จึงล้มดัง ๆ แทน ส่วนแถวที่**ไม่มี** (ยังไม่เคยบันทึก) เป็นเรื่องปกติ คืน default ในโค้ดโดยไม่มี error |
| `notification_email` | **ไม่พบผู้อ่าน** — หน้าลงจอด §3.2 | — | — |
| `license` | `LicenseService.isEnforcementEnabled()` (backend-gateway) **และ** `SeatEnforcementFlagService.isEnabled()` (micro-cluster) — คนละ process มี cache 60 วิของตัวเองอิสระต่อกัน อ่านแถวเดียวกันเป๊ะ | 60 วิ แยกกัน | Fail-open ไปทาง**ทิศที่ปลอดภัย**: ค่าที่อ่านไม่ได้หรือผิดรูปแบบอ่านเป็น `false` (ไม่บังคับใช้) ทั้งสองฝั่ง — DB สะดุดต้องไม่กลายเป็น 403 ทั้งแพลตฟอร์ม |
| `expiry_thresholds` | `ExpiryThresholdsService` ใน micro-cluster, `ExpiryThresholdsService` ใน micro-business และ `ExpiryThresholdContext` ของ frontend เอง (ผ่าน endpoint แยกต่างหาก ไม่มี permission ไม่ใช่พื้นผิว REST ของตารางนี้) | 60 วิ ในทั้งสามที่ | Frontend: ถอยไปใช้ default ในโค้ดเงียบ ๆ ไม่มี toast (`ExpiryThresholdContext.tsx:52-54`) — หน้าต่างของ badge ค้างเก่า ส่วนที่เหลือของหน้ายังทำงานปกติ |
| `platform_migration` | `PlatformMigrationGuard` (backend-gateway) | 60 วิ | Fail-**closed**: ไม่มีแถว หรือแถวอ่านไม่ได้ อ่านเป็น `false` (ปิด API) — ทิศตรงข้ามกับ `license` เพราะสิ่งที่สวิตช์นี้คุ้มกัน (`prisma migrate deploy` บนฐานข้อมูลกลางที่ทุก cluster ใช้ร่วมกัน) ต้องไม่ถูก DB สะดุดเปิดค้างไว้ ขณะที่ลำดับความสำคัญของ `license` คือ "ต้องไม่บล็อกลูกค้าที่จ่ายเงินโดยผิดพลาด" |
| `email_routing` | `platform-email.service.ts` (micro-notification, `PlatformEmailService.resolveSmtpConfig()` และการค้นหาเส้นทาง) และ `useEmailRouting.ts:45` ของโมดูล Email Settings (frontend ผ่าน `platformConfigService.getByKey('email_routing')` — service ทั่วไปตัวเดียวกับที่โมดูลนี้ใช้) | ไม่ได้ตรวจในหน้านี้ — นอกขอบเขตของโมดูลนี้ | ไม่ได้ตรวจในหน้านี้ |
| `feature_flags` | ทุกหน้าของ SPA ผ่านคู่ `/api-system/platform/feature-flags` เฉพาะของตัวเอง ไม่ใช่พื้นผิวทั่วไปของตารางนี้ | ไม่ได้ตรวจในหน้านี้ | ไม่ได้ตรวจในหน้านี้ |

**ทิศทาง fail ที่ไม่สมมาตรกันระหว่าง `license` กับ `platform_migration` เป็นเรื่องตั้งใจ ไม่ใช่ความไม่สอดคล้อง** — ทั้งสองสวิตช์ใช้การ parse `=== true` (ไม่ใช่ truthy) แบบเดียวกัน และรูปแบบ cache 60 วินาทีเหมือนกัน แต่ default ของ `license` เมื่ออ่านไม่ได้คือ `false` = *อย่าบล็อกใครเลย* ส่วน default ของ `platform_migration` เมื่ออ่านไม่ได้ก็เป็น `false` เหมือนกันแต่หมายถึง *ปิดประตู migration ไว้* ทั้งสอง default ชี้ไปทางผลลัพธ์ที่ปลอดภัยกว่าสำหรับสิ่งที่สวิตช์แต่ละตัวคุ้มกันจริง — ไม่ใช่ทิศทางความปลอดภัยเดียวกันในเชิงสัมบูรณ์ เป็นแค่สัมพัทธ์กับความเสี่ยงของตัวมันเอง

## 5. กลไกฝั่งเขียน

ทุกการเขียน — `PUT` หรือ `PATCH` ตัวไหนก็ตาม — ถูกตรวจและบันทึกด้วยโค้ดชุดเดียวกัน (`PlatformConfigService.upsert()`/`.patch()` ทั้งคู่จบที่ `writeValue()` ร่วมกัน, `platform-config.service.ts:200-236,261-377`) เข้าถึงผ่านตัวส่งต่อของ gateway (`PlatformConfigsService`, backend-gateway) ทาง RPC สองจุดเข้าต่างกันแค่วิธีประกอบค่าที่จะตรวจ:

- **`PUT` (`upsert`)** — payload ของผู้เรียกถูกตรวจ*ตามที่ส่งมา*กับ schema ฝั่งเขียน (ถอด default แล้ว, §3) ต้องมีทุกฟิลด์ที่ schema รู้จัก ไม่งั้น `safeParse` ล้มเหลวและทั้งคำขอตอบ `COMMON_VALIDATION_FAILED` ไม่มีการ์ดใดในโมดูลนี้เรียกเส้นทางนี้ (หน้าลงจอด §3.4)
- **`PATCH` (`patch`)** — payload ของผู้เรียกถูกตรวจทีละฟิลด์กับรายชื่อฟิลด์ที่รู้จักของคีย์นั้นก่อน (`rejectBadPatchShape()`, บรรทัด 324-337): ออบเจกต์ว่างถูกปฏิเสธทันที (ไม่งั้นมันจะสร้างแถวเต็มไปด้วย default ให้คีย์ที่ไม่มีใครแตะเลย) และชื่อฟิลด์ใดที่ schema ไม่รู้จักถูกปฏิเสธโดยระบุชื่อ ไม่เคยถูกทิ้งเงียบ ๆ จากนั้นค่าที่เก็บไว้เดิมถูกอ่านและผ่าน `parseStored()` — ไม่ใช้ JSON ดิบ — เพื่อให้แถวที่บันทึกก่อนมีฟิลด์ใดถูกเติมด้วย default ของฟิลด์นั้น*ก่อน*ที่ payload บางส่วนของผู้เรียกจะถูกผสานทับ มีแค่ออบเจกต์ที่ผสานแล้วครบเท่านั้นที่ถูกตรวจกับ schema ฝั่งเขียนและบันทึกจริง

ทั้งสองเส้นทางตรวจ**คีย์ที่ไม่รู้จักด้วยตัวเอง**อีกชั้นหนึ่ง (`isPlatformConfigKey()`, micro-cluster) นอกเหนือจากการตรวจ `KEY_REGEX` (`^[a-zA-Z0-9_.-]+$`) ของ path segment ที่ gateway ทำไปแล้ว (`platform_configs.controller.ts:37`) — คีย์ที่ผ่าน regex แต่ไม่ใช่หนึ่งในสิบรายการของ registry (เช่นพิมพ์ผิด หรือคีย์ที่ถูกถอดออกจาก registry แล้ว) ก็ยังถูกปฏิเสธ พร้อมรายชื่อคีย์ที่รองรับทั้งหมดในข้อความ error

`user_id` เป็นข้อบังคับในทุกการเขียน (`upsert`/`patch` ทั้งคู่ปฏิเสธด้วย `COMMON_VALIDATION_FAILED` ถ้าไม่มี) ทุกแถวที่บันทึกจึงมี `created_by_id`/`updated_by_id` ระบุตัวได้เสมอ

**`doc_version` ไม่ใช่ optimistic lock ที่ทำงานอยู่จริง** คอลัมน์นี้มีอยู่ในตารางแต่ไม่ถูกอ่านหรือเพิ่มค่าโดย `writeValue()` เลย — การเรียก `PATCH` สองครั้งพร้อมกันไปที่คีย์เดียวกันจะสำเร็จทั้งคู่ โดยการผสานของครั้งที่สองชนะแบบเงียบ ๆ (สร้างจากสิ่งที่ครั้งแรกเพิ่งบันทึกไปแล้ว หรือจากค่าก่อนครั้งแรกถ้าทั้งสองอ่านก่อนที่ตัวใดตัวหนึ่งจะเขียน ขึ้นกับจังหวะเวลา) ไม่ถูกปฏิเสธเพราะฐานที่ใช้เก่าไปแล้ว คอมเมนต์ของ service ฝั่ง frontend เอง (`platformConfigService.ts:29`) ระบุตรง ๆ ว่า "ตารางนี้มีคอลัมน์นั้น แต่ backend ยังไม่บังคับ optimistic locking ด้วยมัน"

## 6. Edge Cases

| สถานการณ์ | สิ่งที่เกิดขึ้นจริง |
| --- | --- |
| แอดมินสองคน `PATCH` คนละฟิลด์ของคีย์เดียวกันภายในวินาทีเดียวกัน | สำเร็จทั้งคู่ ใครก็ตามที่ `findFirst` ทำงานทีหลังจะชนะฐานที่ตัวเองผสานทับ — เป็น race แบบ last-write-wins จริง ๆ บน JSON ก้อนทั้งหมด ไม่ใช่รายฟิลด์ เพราะ `doc_version` ไม่ถูกบังคับใช้ (§5) |
| แถวถูกแก้ตรงในฐานข้อมูลเป็นรูปที่ไม่ตรงกับ schema อีกต่อไป | ผู้อ่าน `invitation`/`signup`/`email_verification`/`password_reset` **throw** ในการอ่านครั้งถัดไป (ล้มดัง ๆ โดยตั้งใจ); ผู้อ่าน `license`/`platform_migration` ถือว่าเป็น `false` (fail ไปทางที่ปลอดภัยของตัวเอง, §4); `GET` ของหน้าจอ admin เอง (`findAll`/`findOne`) ก็เรียก `parseStored()` เช่นกัน แถวที่พังจริงจึงทำให้**ทั้งหน้าจอ Platform Config โหลดไม่ขึ้น** ไม่ใช่แค่การ์ดเดียว — นี่คือความเสี่ยงเดียวกับที่คอมเมนต์ `.default()` บนทุกฟิลด์ของ schema เอง (§3) มีไว้ลดให้กับวิวัฒนาการปกติของ schema แต่มันไม่ป้องกันค่าที่ไม่เคยตรง schema ตั้งแต่แรก |
| ถามหาคีย์ก่อนที่แถวจะเคยถูกบันทึก | ทุกเส้นทางอ่านคืนค่า default ในตัวจาก registry พร้อม `id: null` — ไม่เคยเป็น 404 ไม่เคยเป็นออบเจกต์ว่าง |
| ส่ง `PATCH` เป็น `{}` ว่างเปล่า | ถูกปฏิเสธ — `rejectBadPatchShape()` ถือว่าออบเจกต์ว่างคือ "ไม่มีอะไรจะทำ" ไม่ใช่ "ปล่อยทุกอย่างไว้เหมือนเดิม" |
| ส่ง `PATCH` ที่มีชื่อฟิลด์ที่ schema ของคีย์ปลายทางไม่รู้จัก | ถูกปฏิเสธโดยระบุชื่อ (เช่น `unknown field(s) foo (supported: base_url, expiry_days, ...)`) ไม่เคยถูกทิ้งเงียบ ๆ |
| สลับ `license.enforcement_enabled` เป็นเปิดแล้วปิดอีกครั้งภายในนาทีเดียว | ทั้ง `LicenseService` ของ backend-gateway และ `SeatEnforcementFlagService` ของ micro-cluster ต่างมี cache 60 วิของตัวเองอิสระต่อกัน — สองกระบวนการอาจเห็นค่าปัจจุบันไม่ตรงกันได้นานถึงหนึ่งนาที ไม่ใช่แค่ไม่ตรงกับฐานข้อมูล |
| ผู้อ่าน `/platform/configs` มี `platform_config.read` แต่ไม่มี `.manage` | เห็นทุกการ์ดเต็มข้อมูลในโหมดอ่านอย่างเดียว (ไม่มีปุ่ม Edit ที่ไหนเลย, §4.1 ของหน้าลงจอด) — การอ่านหน้าจอนี้ไม่เคยต้องการคีย์ที่ละเอียดกว่าที่เอกสารไว้ใน §4.4 ของหน้าลงจอด |

## 7. คำแนะนำ

- **ถือว่าการ์ด `notification_email` ยังไม่มีผลจริงจนกว่าจะยืนยันผู้อ่านได้** อย่าอิงสวิตช์ `enabled` ของการ์ดนี้ในแผนทดสอบที่คาดว่าจะมีอีเมลถูกส่งจริงหรือไม่ถูกส่ง — ไม่พบผู้อ่านที่ไหนใน backend ณ เวลาที่เขียนหน้านี้ (หน้าลงจอด §3.2)
- **เมื่อทดสอบ `license`/`platform_migration` ให้รอหน้าต่าง cache หรือคาดหวังว่าการสลับไปมาภายในนาทีเดียวจะดูไม่สอดคล้องกันระหว่างกระบวนการ** — เป็นพฤติกรรมที่คาดหมายได้จาก cache 60 วินาทีอิสระของแต่ละผู้อ่าน (§4) ไม่ใช่บั๊กที่ต้องรายงาน
- **`PATCH` ที่มีชื่อฟิลด์พิมพ์ผิดจะล้มเหลวดัง ๆ (422) ไม่ใช่สำเร็จเงียบ ๆ** — เป็นความตั้งใจ อย่า "แก้" เทสต์ที่คาดหวังการปฏิเสธแบบเข้มนี้
- **อย่าเขียน `doc_version` จากฝั่ง client integration ใด ๆ โดยคาดว่ามันจะถูกบังคับใช้** — มันไม่ถูกอ่านโดยเส้นทางเขียนใดในวันนี้ (§5) ถ้า backend เริ่มบังคับใช้ในอนาคต ควรกลับมาทบทวนข้อสังเกตนี้

## 8. แหล่งอ้างอิง

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_platform_config` (บรรทัด 1462)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` — `PLATFORM_CONFIG_REGISTRY` schema/default ของทุกคีย์ (§3), `toWriteSchema()` (§3, §5)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.service.ts` — `findAll`/`findOne`/`upsert`/`patch`/`writeValue`/`getInvitationConfig` (§2, §5)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_configs/{platform_configs.controller.ts,platform_configs.service.ts}` — ตัวส่งต่อของ gateway ด่าน RBAC `KEY_REGEX` (§5)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/license/{license.service.ts,license.interceptor.ts}` — ผู้อ่านคีย์ `license` ฝั่ง backend-gateway (§4)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/common/{seat-enforcement-flag.service.ts,expiry-thresholds.service.ts}` — ผู้อ่านคีย์ `license`/`expiry_thresholds` ฝั่ง micro-cluster (§4)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-migration.guard.ts` — ผู้อ่านคีย์ `platform_migration` (§4)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (บรรทัด 273-350, 389-397) — ผู้อ่าน `signup`/`email_verification`/`password_reset` (§4)
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/platform-email/platform-email.service.ts`, `apps/micro-notification/CLAUDE.md` — การค้นหาผู้อ่านของ `email_routing`/`notification_email` (§4)
- `../carmen-platform/src/services/platformConfigService.ts` — REST client ฝั่ง frontend รวมข้อสังเกตเรื่อง `doc_version` (§5)
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx` — ผู้อ่าน `expiry_thresholds` ของ frontend เองและพฤติกรรม fallback ของมัน (§4)

**Cross-links:** [หน้าลงจอด Platform Config](/th/platform/platform-config) &nbsp;·&nbsp; [Licenses](/th/platform/licenses)
