---
title: การตั้งค่าอีเมล — โมเดลข้อมูล (Data Model)
description: tb_email_sender_profile (โปรไฟล์ผู้ส่ง SMTP ที่ตั้งชื่อได้ credential เข้ารหัส) บวกโครงสร้าง config email_routing ที่มันถูก resolve ผ่าน — และการรับประกันฝั่งเขียน (optimistic locking, ความหมายของ password-patch, ความไม่ซ้ำของชื่อ) ที่ต่างจากตาราง platform-config ที่ใช้ร่วมกัน
published: true
date: '2026-09-06T18:00:00.000Z'
tags: book/platform, email-settings, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การตั้งค่าอีเมล — โมเดลข้อมูล (Data Model)

> **At a Glance**
> **`tb_email_sender_profile`** — หนึ่งแถวต่อหนึ่งผู้ส่ง SMTP ที่ตั้งชื่อได้ เป็นของ `micro-cluster`, `doc_version` **บังคับใช้จริง** เป็น optimistic lock ทุกครั้งที่อัปเดต (§5) &nbsp;·&nbsp; **`email_routing`** — แถวหนึ่งของ `tb_platform_config` (**ไม่ใช่**คอลัมน์บนตารางนี้) ที่ micro-notification resolve สดทุกครั้งสำหรับทุกเส้นทางขาออก (หน้า landing §3.2-3.3) &nbsp;·&nbsp; **รหัสผ่าน:** `enc:v1` (AES-256-GCM) ตอนเก็บ มาสก์เสมอ (`••••••`) ในทุกการตอบกลับ API ถอดรหัสเฉพาะข้างใน micro-notification ตอนส่งจริงเท่านั้น &nbsp;·&nbsp; **ความไม่ซ้ำอยู่ที่ `name` ไม่ใช่ purpose** — คำบรรยาย Swagger ของ controller ยังบอกตรงข้ามอยู่ (§5) &nbsp;·&nbsp; **ปรับดีไซน์ครั้งเดียว:** migration `20260808130000_email_profile_master_and_routing` (2026-08-08) แยกตารางแบบหนึ่ง-purpose-ต่อ-หนึ่งแถว ออกเป็นรายการที่ตั้งชื่อได้นี้ บวก mapping `email_routing` แยกต่างหาก

> **แหล่งความจริง:** Prisma schema ฝั่งแพลตฟอร์ม สอง migration ที่ปรับรูปตารางนี้ และสอง service (`micro-cluster` สำหรับ CRUD, `micro-notification` สำหรับ resolve/ส่ง) อ่านสิ่งเหล่านี้ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/email-sender-profile/email-sender-profile.service.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-notification/src/platform-email/platform-email.service.ts`
>
> ตรวจสอบกับ `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) และ `carmen-platform` HEAD `157a65e` (2026-09-04)

## 1. ภาพรวม

หน้าจอนี้อาศัยสองสิ่งที่อยู่คนละตาราง เป็นของคนละ service `tb_email_sender_profile` (§2) คือรายการที่ตั้งชื่อได้ของปลายทาง SMTP เป็นของ **micro-cluster** ทั้ง CRUD และถูกส่งต่อโดย `platform_email-settings.controller.ts` ฝั่ง gateway `email_routing` (§3) คือหนึ่งแถวของตาราง `tb_platform_config` ที่**ใช้ร่วมกัน** — ตารางเดียวกันและ endpoint กลาง `/api-system/platform/configs` เดียวกับที่ data model ของโมดูล [Platform Config](/th/platform/platform-config) บันทึกไว้แบบเต็ม อ่านและเขียนผ่าน client ของโมดูลนั้น `platformConfigService` ไม่ใช่ `emailSettingService` ของโมดูลนี้ การ resolve เส้นทางขาออกให้กลายเป็นการส่ง SMTP จริง (§4) ต้องใช้ทั้งสองอย่าง: แถว routing ต้องระบุ id โปรไฟล์ และแถวโปรไฟล์นั้นต้องมีอยู่จริง ใช้งานอยู่ และถอดรหัสได้

## 2. Entity: `tb_email_sender_profile`

Schema บรรทัด 1433-1460 (`../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | Primary key, `gen_random_uuid()` |
| `name` | `String @db.VarChar` | ไม่ | ผู้ดูแลตั้งเอง เลือกด้วยชื่อในหน้าจอ routing ไม่ซ้ำกันในแถวที่ยังไม่ถูกลบ (§5) — **ไม่**ผูกกับ purpose ตายตัวอีกต่อไปตั้งแต่ปรับดีไซน์ 2026-08-08 |
| `from_email` | `String @db.VarChar` | ไม่ | ที่อยู่ `From:` |
| `from_name` | `String? @db.VarChar` | ใช่ | ชื่อแสดงคู่กับ `from_email`, ไม่บังคับ |
| `smtp_host` | `String @db.VarChar` | ไม่ | ชื่อโฮสต์ปลายทาง SMTP |
| `smtp_port` | `Int @default(587) @db.Integer` | ไม่ | |
| `smtp_secure` | `Boolean @default(false) @db.Boolean` | ไม่ | implicit TLS (checkbox "implicit TLS" ใน UI) |
| `smtp_username` | `String? @db.VarChar` | ใช่ | |
| `smtp_password` | `String? @db.VarChar` | ใช่ | ciphertext `enc:v1` (AES-256-GCM) — ไม่เคยเก็บหรือคืนเป็น plaintext (§5) |
| `is_active` | `Boolean @default(true) @db.Boolean` | ไม่ | การปิดใช้งานโปรไฟล์ที่ยังมีเส้นทางชี้มาอยู่ ทำให้เส้นทางเหล่านั้นส่งไม่ได้ (`no-config`, หน้า landing §3.3) — ฟอร์มแก้ไขเตือนก่อนที่จะเกิดเหตุนี้ (`EmailSettingCard.tsx:471-476`) |
| `note` | `String? @db.VarChar` | ใช่ | |
| `doc_version` | `Int @default(0) @db.Integer` | ไม่ | **บังคับใช้จริง** เป็น optimistic lock (§5) — ตรงข้ามกับคอลัมน์ชื่อเดียวกันบน `tb_platform_config` |
| กลุ่ม audit + soft delete | — | ใช่ | มาตรฐาน `created_at`/`created_by_id`/`updated_at`/`updated_by_id`/`deleted_at`/`deleted_by_id` |

**Index:** `(deleted_at)`, map `email_sender_profile_deleted_at_idx`; **unique** `(name)` กรองเฉพาะแถวที่ยังไม่ถูกลบ, map `email_sender_profile_name_live_u` (partial unique index, `WHERE deleted_at IS NULL` — เพิ่มโดย migration 2026-08-08, §5)

### 2.1 สิ่งที่ตารางนี้เคยเป็น — และฟอสซิลที่ทิ้งไว้

ก่อน migration `20260808130000_email_profile_master_and_routing` ตารางนี้มีคอลัมน์ `purpose` พิมพ์เป็น `enum_email_sender_purpose` (`no_reply` / `support` / `billing`) พร้อม unique index บน `(purpose, deleted_at)` — หนึ่งโปรไฟล์ที่ยังไม่ถูกลบต่อหนึ่ง purpose เท่านั้น การเพิ่มอีเมลชนิดที่สี่แปลว่าต้องเพิ่มค่า enum แล้ว deploy migration นั้นตั้งชื่อแถวเดิมแต่ละแถวตาม purpose ของมัน (`no_reply` → "No-reply" ฯลฯ) ย้าย unique constraint ไปที่ `name` ลบคอลัมน์ `purpose` และ seed แถว `email_routing` แถวแรกที่ชี้ทุกเส้นทางไปยังโปรไฟล์ "No-reply" ที่รอดมา — อ่าน migration SQL เต็มสำหรับ logic การเปลี่ยนชื่อ/backfill/แก้ชนกันที่แม่นยำ (`.../20260808130000_email_profile_master_and_routing/migration.sql`)

**ตัว enum เองไม่เคยถูกลบ** `enum enum_email_sender_purpose` ยังคงประกาศอยู่ใน schema (`schema.prisma:1415-1425`) และไม่มีคอลัมน์ใดอ้างถึงมันเลย — ค้นทั่ว repository หาชื่อ type นี้พบแค่การประกาศของมันเอง มันยังไม่ใช่ enum สามค่าดั้งเดิมด้วย: หลังจากดีไซน์แบบ purpose มีอยู่แล้วช่วงหนึ่ง มีคนเพิ่มชื่อห้าเส้นทางอีเมล (`register`, `verify_email`, `invitation`, `forgot_password`, `notification`) เข้าไปใน enum type **เดียวกัน**นี้ — ตอนนี้มันจึงมีแปดค่าคาบเกี่ยวกันสองยุคของดีไซน์ ที่ไม่มีอะไรอ้างถึงเลย คอมเมนต์ของมันซ้ำเติมปัญหานี้: "เส้นทางที่ไม่มีโปรไฟล์ของตัวเองจะถอยไปใช้ `no_reply`" บรรยายพฤติกรรมก่อนปรับดีไซน์ได้แม่นยำ และเป็นเท็จอย่างชัดเจนสำหรับดีไซน์ปัจจุบัน ที่ปลายทางสำรองคือโปรไฟล์ที่ผู้ดูแลตั้งเป็น `default` ใน `email_routing` (§3) ซึ่งไม่จำเป็นและหลังเปลี่ยนชื่อไม่กี่ครั้งก็คงไม่ใช่โปรไฟล์ที่ชื่อ "No-reply" แล้ว อย่าใช้คอมเมนต์ของ enum นี้เป็นคำอ้างอิงพฤติกรรม fallback ปัจจุบัน

## 3. entry ของ config `email_routing`

ไม่ใช่คอลัมน์บนตารางนี้ — เป็นแถวหนึ่งของ `tb_platform_config` (`key = 'email_routing'`) ตรวจสอบด้วยกลไก registry-กับ-Zod-schema เดียวกับที่ data model ของ [Platform Config](/th/platform/platform-config) บันทึกไว้แบบเต็ม (§3 และ §5 ของหน้านั้นใช้ได้ตรงนี้เหมือนกันไม่เปลี่ยนแปลง: `PATCH` merge ฟิลด์ `PUT` แทนที่ทั้งหมดและต้องมีทุกฟิลด์ ส่วน `doc_version` บนตารางนั้น**ไม่ใช่** optimistic lock ที่บังคับใช้จริง — ต่างจาก `tb_email_sender_profile` ของโมดูลนี้เองอย่างแท้จริง, §5 ด้านล่าง)

```
EmailRoutingConfig {
  default:         string (uuid)   // จำเป็น — ค่าสำรองสำหรับทุกเส้นทางที่ไม่ได้ระบุด้านล่าง
  register?:       string (uuid)
  verify_email?:   string (uuid)
  invitation?:     string (uuid)
  forgot_password?: string (uuid)
  notification?:   string (uuid)
}
```

คีย์เส้นทางที่*ไม่มีอยู่*ในออบเจกต์ที่เก็บไว้ — ไม่มีเลย ต่างจากมีอยู่แต่ว่างเปล่า — จะถอยไปใช้ `default` นี่คือเหตุผลที่ตัวแก้ไข routing ฝั่ง frontend ลบคีย์ของเส้นทางนั้นทิ้งทั้งหมดเมื่อผู้ดูแลเลือก "ใช้ค่าเริ่มต้น" แทนที่จะเขียน id ของโปรไฟล์ default ลงไป (`EmailRoutingCard.tsx:93-98`) — เส้นทางใหม่ที่ยังไม่มี entry ชัดเจนใน config ที่บันทึกไว้แล้วของทุก deployment จะยัง resolve ผ่าน `default` ได้โดยไม่ต้องอัปเดต deployment เดิมสักตัว

**Default ของ registry:** `{ default: '00000000-0000-0000-0000-000000000000' }` — placeholder ที่ตั้งใจให้ใช้งานไม่ได้ เพราะ id โปรไฟล์จริงเจาะจงตาม environment ใส่ตายตัวใน registry ไม่ได้ (`platform-config.schema.ts`, entry เดียวกับที่ data model ของ [Platform Config](/th/platform/platform-config) §3 บันทึกไว้) deployment ใหม่ล้วนที่ไม่มีโปรไฟล์ให้ seed จะค้างอยู่กับ placeholder นี้ จนกว่าผู้ดูแลจะตั้งค่าจริง; deployment ที่ upgrade มาจะไม่มีวันเจอมัน เพราะ migration 2026-08-08 seed mapping จริงตอน migrate (§2.1)

## 4. การ resolve เส้นทางให้กลายเป็นการส่ง SMTP

`PlatformEmailService.resolveProfile(flow)` (micro-notification, `platform-email.service.ts:114-138`) เป็นจุดคอขวดเดียวที่ทั้งห้าเส้นทาง (หน้า landing §3.2) ไหลผ่าน:

1. อ่านแถว `email_routing` ล่าสุดจาก `tb_platform_config` (`findFirst`, `orderBy: updated_at desc` — รูปแบบ "ล่าสุดชนะ" เดียวกับที่ data model ของ [Platform Config](/th/platform/platform-config) บันทึกไว้สำหรับ unique constraint แบบ dead-on-active-rows ของตารางนั้นเอง)
2. ตรวจสอบด้วย `EmailRoutingSchema` (Zod) แถวที่ไม่ถูกต้องหรือหายไปจะบันทึก error และเส้นทางนั้นส่งไม่ได้เลย — ไม่มี default-config fallback ในชั้นนี้ มีแค่ `default` **ภายใน**ออบเจกต์ routing ที่ถูกต้องแล้วเท่านั้น
3. resolve `routing[flow] ?? routing.default` เป็น id โปรไฟล์
4. โหลดแถว `tb_email_sender_profile` นั้น **โดยกรอง** `deleted_at: null, is_active: true` แถวที่มีอยู่แต่ถูกลบหรือปิดใช้งาน จะถูกปฏิบัติเหมือนแถวที่ไม่มีอยู่เลยทุกประการ — ทั้งคู่คืน `null` และบันทึก warning ข้อความเดียวกันว่า "routing ชี้ไปโปรไฟล์ที่หาย/ถูกลบ/ปิดใช้งาน"

`toEmailConfig()` จากนั้นถอดรหัส `smtp_password` (`decryptSecret`, `@repo/secret-crypto`) และสร้าง config ที่ nodemailer ใช้ส่งจริง **โปรไฟล์ที่ถอดรหัสไม่ได้จะถูกรายงานว่าเสีย ไม่ใช่ข้ามไปเงียบ ๆ** — คอมเมนต์ในโค้ดเองระบุตรงว่าการถอยไปใช้ environment variable ตรงนี้เสี่ยงต่อการส่งจากบัญชีผิดในขณะที่ผู้ดูแลเชื่อว่ากำลังใช้โปรไฟล์ที่ตั้งไว้ (`platform-email.service.ts:212-214`); ผลลัพธ์คือ `{ sent: false, reason: 'decrypt-failed' }` ต่างจาก `no-config`

**ไม่มี environment-variable fallback ในไฟล์นี้เลย** (หน้า landing §3.3 ไล่เรื่องนี้ให้ครบวงจร รวมถึงคอมเมนต์ที่ล้าสมัยบน `resolveSmtpConfig()` ที่ไม่มีผู้เรียกเลย ซึ่งอ้างตรงข้าม) ทุกกรณีความล้มเหลวด้านล่างจบลงที่การรายงานว่าไม่ส่ง ไม่เคยส่งไปที่อื่นแบบเงียบ ๆ:

| ผลลัพธ์ | `reason` | สาเหตุ |
| --- | --- | --- |
| ส่งสำเร็จ | *(ไม่มี — `sent: true`)* | resolve โปรไฟล์ได้ ถอดรหัสได้ และ nodemailer ยืนยันการส่ง |
| ไม่ส่ง | `no-config` | แถว routing หายไปหรือไม่ถูกต้อง หรือโปรไฟล์ที่ resolve ได้หาย/ถูกลบ/ปิดใช้งาน |
| ไม่ส่ง | `decrypt-failed` | resolve โปรไฟล์ได้แต่ถอดรหัส `smtp_password` ไม่ได้ (เช่น `SECRET_ENCRYPTION_KEY` ไม่ตรง) |
| ไม่ส่ง | `lookup-failed` | คิวรีฐานข้อมูลเอง throw (รายงานผล ไม่เคย throw ซ้ำ — ความล้มเหลวของอีเมลต้องไม่ทำให้การกระทำของผู้เรียกล้มไปด้วย เช่น การสมัคร) |
| ไม่ส่ง | `smtp-error` | โปรไฟล์ถอดรหัสได้ดี แต่ตัว transport SMTP เองล้มเหลว |

## 5. กลไกฝั่งเขียน — เฉพาะ `tb_email_sender_profile`

CRUD อยู่ทั้งหมดใน `EmailSenderProfileService` (micro-cluster) ส่งต่อโดย gateway ผ่าน RPC (`EmailSenderProfiles.*`, `platform_email-settings.service.ts`)

- **`doc_version` เป็น optimistic lock ที่บังคับใช้จริงที่นี่** — ตรงข้ามกับคอลัมน์ชื่อเดียวกันบน `tb_platform_config` (§3 ด้านบน และ data model ของ [Platform Config](/th/platform/platform-config) §5 เอง) `update()` ปฏิเสธคำขอที่ `doc_version` หายไป/ไม่ใช่ตัวเลขทันที (`COMMON_DOC_VERSION_REQUIRED`) และเขียนจริงเป็น `prisma.update({ where: { id, doc_version } , ... })` — เวอร์ชันเก่าจะไม่ตรงกับแถวไหนเลย และคู่ `isVersionConflict()`/`notifyVersionConflict()` ฝั่ง frontend (`utils/docVersion.ts`) แปลงมันเป็น toast "มีคนอื่นแก้สิ่งนี้ — โหลดค่าล่าสุดแล้ว" พร้อมทั้งคงการ์ดไว้ในโหมดแก้ (หน้า landing §1)
- **ความไม่ซ้ำย้ายไปที่ `name` แล้ว แต่คำบรรยาย Swagger ของ gateway เองยังตามไม่ทัน** `create()`/`update()` ทั้งคู่ตรวจ `findFirst({ name, deleted_at: null })` ก่อนเขียน และคืน `EMAIL_SENDER_PROFILE_NAME_EXISTS` (409) เมื่อชนกัน (`email-sender-profile.service.ts:163-169, 219-226`) — บังคับที่ชั้นแอปพลิเคชัน หนุนหลังด้วย partial unique index (§2) คำบรรยาย `@ApiResponse` ของ controller ฝั่ง gateway เองสำหรับ `POST`/`PUT` ยังเขียนว่า "An active profile already exists for this purpose" (`platform_email-settings.controller.ts:144`) — ของตกค้างจากดีไซน์แบบหนึ่ง-purpose-ต่อ-หนึ่งแถวก่อนปรับ; เงื่อนไข 409 จริงวันนี้คือ**ชื่อ**ซ้ำ ไม่ใช่ purpose ซ้ำ เพราะ `purpose` ไม่มีเป็นคอลัมน์อีกต่อไปแล้ว
- **ความหมายของ password-patch** (`passwordPatch()`, `email-sender-profile.service.ts:51-56`): สตริงมาสก์หรือ `undefined` แปลว่า "ไม่เปลี่ยน" (ไม่เขียนฟิลด์ `smtp_password` เลย); `null` หรือ `''` แปลว่า "ล้างรหัสผ่านที่เก็บไว้"; สตริงอื่นถูกเข้ารหัสแล้วเก็บ ตามที่บันทึกไว้ในหน้า landing §3.4 component `PasswordField` ฝั่ง frontend เองไม่เคยสร้างค่าล้างนี้ได้ — มันปฏิบัติต่อ field ที่ว่างเปล่าเหมือน "ไม่เปลี่ยน" — รหัสผ่านเมื่อตั้งแล้วจึงแทนที่ได้อย่างเดียวจากหน้าจอนี้ ไม่มีทางลบออกได้เลย ทั้งที่ backend เองรองรับการลบ
- **การลบเป็น soft delete** (`deleted_at`/`deleted_by_id`) และโปรไฟล์ที่ถูกลบจะถูกกันออกจาก `findAll`/`findOne` — แต่อย่างที่ §4 บอก ชั้น routing ปฏิบัติต่อมันเหมือนแถวที่หายไปทุกประการ: เส้นทางใดที่ยังชี้มาที่มันจะหยุดส่งเงียบ ๆ ไม่มี error โผล่ที่ไหนใน UI จนกว่าจะมีใครสังเกตว่าเมลหยุดหรือเช็คคำเตือน "เลนพัง" ในผัง routing (สไตล์ `broken` ของ `RoutingPanel.tsx`, หน้า landing §3.1)

## 6. Edge Cases

| สถานการณ์ | สิ่งที่เกิดขึ้นจริง |
| --- | --- |
| โปรไฟล์ที่เส้นทางหนึ่งชี้ไปถูกลบหรือปิดใช้งานหลังตั้ง routing ไว้แล้ว | เส้นทางนั้นหยุดส่งเงียบ ๆ (`no-config`) — ไม่มีการแจ้งเตือนเกิดขึ้นเลย สัญญาณที่มองเห็นได้อย่างเดียวคือไอคอนคำเตือน "เลนพัง" ในผัง routing (หน้า landing §3.1) และในที่สุดคือการไม่มีเมลนั้นเอง |
| แอดมินสองคนบันทึกการ์ด Email Routing ในวินาทีเดียวกัน | `PUT` ตัวไหนถึง `tb_platform_config` ทีหลังชนะออบเจกต์ทั้งใบ — `doc_version` ไม่ถูกบังคับใช้บนตารางนี้ (§3) จึงไม่มีการตรวจ conflict เลย ต่างจากการแก้โปรไฟล์ผู้ส่งพร้อมกัน (§5 ที่ตรวจ conflict จริง) |
| `smtp_password` ของโปรไฟล์ถอดรหัสไม่ได้ (เช่นหลังหมุนกุญแจเข้ารหัส) | ทุกเส้นทางที่ routing ไปยังมันจะรายงาน `decrypt-failed` ไม่ใช่ `no-config` — แยกออกได้ใน log แต่ผลที่ผู้ดูแลเห็น (เมลไม่ออก) เหมือนกันทั้งสองแบบ |
| แถว `email_routing` ของ deployment ที่ยังไม่เคยตั้งค่ายังเป็น UUID placeholder ของ registry | ทุกเส้นทางรายงาน `no-config` จนกว่าผู้ดูแลจะสร้างโปรไฟล์อย่างน้อยหนึ่งตัวและบันทึก routing map ที่มี `default` จริง (§3) |
| ผู้ดูมี `email_setting.read`/`.manage` แต่ไม่มี `platform_config.read`/`.manage` | Sender Profiles โหลดและแก้ไขได้เต็มที่; การ์ด Email Routing แสดง error การโหลดค้างถาวร และ — ถ้ามันแสดงได้จริงด้วยเหตุผลใดก็ตาม — การ Save จะโดน 403 (หน้า landing §4.2, ไล่ครบวงจรแล้ว) |
| มีโปรไฟล์ที่ยังไม่ถูกลบมากกว่า 20 ตัว | `emailSettingService.getAll()` ขอด้วย `perpage=20` ตายตัว ไม่มี UI แบ่งหน้าบนหน้าจอเลย (`emailSettingService.ts:7-9`) — โปรไฟล์ตัวที่ 21 จะไม่โผล่ในกริด เมนู routing หรือจำนวนเส้นทางที่มันแบกอยู่เลย คอมเมนต์ของ service เองให้เหตุผลว่า "purpose enum จำกัดรายการนี้ไว้ที่ 3 แถว" ซึ่งล้าสมัยพอ ๆ กับฟอสซิล enum ใน §2.1: ไม่มีเพดานที่ enum บังคับอีกต่อไปแล้ว เพดานจริงวันนี้คือขนาดหน้าที่ hardcode ไว้นี้ ไม่ใช่ข้อจำกัดเชิงโครงสร้างใด ๆ |

## 7. คำแนะนำ

- **ตอนทดสอบการเปลี่ยน routing ให้เปิดรายการ Sender Profiles ของโมดูลนี้เองไว้ควบคู่กัน** — โปรไฟล์ที่ดู "ตั้งค่าแล้ว" ในการ์ดของตัวเอง ยังอาจไม่มีเส้นทางไหนเข้าถึงได้เงียบ ๆ ถ้ามันถูกปิดใช้งาน หรือถ้า `email_routing` ไม่เคยถูกบันทึกด้วย `default` จริง (§3, §6)
- **อย่าอ้างคอมเมนต์ของ `enum_email_sender_purpose` หรือคอมเมนต์ "purpose enum จำกัดไว้ 3 แถว" ใน `emailSettingService.ts` ว่าเป็นพฤติกรรมปัจจุบัน** — ทั้งคู่บรรยายดีไซน์แบบหนึ่ง-purpose-ต่อ-หนึ่งแถวก่อน 2026-08-08 และล้าสมัยแล้ว (§2.1, §6)
- **ทดสอบการให้สิทธิ์แค่ `email_setting.*` โดยไม่มี `platform_config.*` เลยโดยตั้งใจ** — มันเป็น test case RBAC ที่ให้ข้อมูลมากที่สุดของโมดูลนี้ เพราะมันสร้างทั้ง error ฝั่งอ่านและกับดัก 403 ฝั่งเขียนจากการให้สิทธิ์ชุดเดียว (หน้า landing §4.2-4.3)
- **แผนทดสอบที่คาดว่าการลบ/ปิดใช้งานโปรไฟล์จะเตือนชัดเจนว่า "N เส้นทางจะหยุดส่ง" จะล้มเหลว** — สัญญาณเดียวในโปรดักต์คือสไตล์ "เลนพัง" ในผัง routing ไม่ใช่ dialog ยืนยันที่บล็อกไว้ฝั่งโปรไฟล์ นอกเหนือจากคำเตือน "N เส้นทางแบกอยู่" ที่มีอยู่แล้วขณะแก้ไขโปรไฟล์นั้น (§5, §6)

## 8. แหล่งอ้างอิง

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (บรรทัด 1415-1460) — `enum_email_sender_purpose`, `tb_email_sender_profile`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260729000000_email_sender_profile/migration.sql` — การสร้างตารางแบบ purpose-enum ดั้งเดิม
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260808130000_email_profile_master_and_routing/migration.sql` — การปรับดีไซน์: เปลี่ยนชื่อ, ย้ายความไม่ซ้ำ, ลบ `purpose`, seed `email_routing`
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/email-sender-profile/email-sender-profile.service.ts` — CRUD, การบังคับใช้ `doc_version`, `passwordPatch()`, ความไม่ซ้ำของชื่อ (§5)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_email-settings/platform_email-settings.controller.ts` (บรรทัด 144) — คำบรรยาย Swagger "purpose" ที่ล้าสมัย (§5)
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/platform-email/platform-email.service.ts` — `resolveProfile`/`toEmailConfig`/`send`/`sendTest`/`resolveSmtpConfig` (§4)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` — entry ของ registry `email_routing` และ default placeholder ของมัน (§3)
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts` (บรรทัด 513-514) — `EMAIL_SENDER_PROFILE_NOT_FOUND`/`EMAIL_SENDER_PROFILE_NAME_EXISTS`
- `../carmen-platform/src/services/emailSettingService.ts` (บรรทัด 7-9) — คอมเมนต์เหตุผล `PERPAGE` ที่ล้าสมัย (§6)
- `../carmen-platform/src/pages/emailSettings/{PasswordField.tsx,EmailRoutingCard.tsx}` — ความหมาย UI ของ password-patch (§5) และการเรียก save ของ routing (§4 ของหน้า landing)

**Cross-links:** [หน้าลงจอด Email Settings](/th/platform/email-settings) &nbsp;·&nbsp; [Platform Config](/th/platform/platform-config)
