---
title: News — แบบจำลองข้อมูล (Data Model)
description: ตาราง field ของ tb_news, คอลัมน์กำหนดเป้าหมาย business_unit_ids แบบ JSONB, enum_news_status, pipeline จาก image_file_token → presigned image_url และความแตกต่างจาก type News ของ SPA
published: true
date: 2026-06-10T15:45:00.000Z
tags: book/platform, news, data-model
editor: markdown
dateCreated: 2026-06-10T15:45:00.000Z
---

# News — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_news` — ตารางเดียว, **ไม่มีความสัมพันธ์ FK, ไม่มี unique constraint นอกเหนือจาก PK** &nbsp;·&nbsp; **Enum:** `enum_news_status` (draft · published · archived) &nbsp;·&nbsp; **การกำหนดเป้าหมาย:** `business_unit_ids Json @default("[]")` — array ของ UUID แบบ JSONB ไม่ใช่ join table; `[]` = global &nbsp;·&nbsp; **รูปภาพ:** จัดเก็บเป็น `image_file_token` (MinIO); response ของ API แทนที่มันด้วย presigned `image_url` (หมดอายุ 1 ชั่วโมง) &nbsp;·&nbsp; **Endpoint:** `/api/news` (CRUD แบบ authenticated) + `/api/public/news` (anonymous) — `/api` **ไม่ใช่** `/api-system`

> **Source of truth:** Prisma platform schema ฝั่ง backend อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

โมดูล News เป็นเจ้าของตารางเดียวเท่านั้น `tb_news` ถือตัวบทความเอง (`title`, `contents` แบบ markdown, `url` แหล่งที่มาแบบ optional), รูปภาพเป็น string ของ file-token จาก MinIO, สถานะการเผยแพร่ (`status`, `published_at`), รายการกำหนดเป้าหมาย (`business_unit_ids` แบบ JSONB) และ audit trio มาตรฐานของแพลตฟอร์ม สิ่งที่ผิดปกติสำหรับ platform schema คือ model นี้ประกาศ **ไม่มี directive `@relation` ใด ๆ เลย**: คอลัมน์ audit actor เป็น UUID เปล่า ๆ (เทียบกับ `tb_application` ซึ่งคอลัมน์ actor มี FK ไป `tb_user`) และการกำหนดเป้าหมาย BU เป็น array แบบ JSONB แทนที่จะเป็น join table referential integrity ของการกำหนดเป้าหมายถูกบังคับใช้ **ตอนเขียนเท่านั้น** โดย service ของ micro-cluster

เส้นทาง persistence คือ gateway → TCP → micro-cluster (client `PRISMA_SYSTEM`); ชั้น gateway เป็นเจ้าของ side-effect ของรูปภาพเพิ่มเติม (อัพโหลดไปยัง micro-file, rollback, cleanup ไฟล์เก่า) และการจัดรูป response (presigned URL, การ enrich audit แบบซ้อน) ที่อธิบายใน §5

## 2. เอนทิตี

### 2.1 `tb_news`

หนึ่งประกาศ/บทความ Schema บรรทัด 803

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `title` | `String @db.VarChar` | No | หัวข้อบทความ — field เนื้อหาตัวเดียวที่จำเป็น |
| `contents` | `String? @db.VarChar` | Yes | เนื้อหาแบบ markdown จัดเก็บแบบ verbatim |
| `url` | `String? @db.VarChar` | Yes | ลิงก์แหล่งที่มาแบบ optional (SPA ตรวจสอบรูปแบบ http(s)) |
| `image_file_token` | `String? @db.VarChar` | Yes | file token ของ MinIO จาก micro-file; **ไม่เคยถูกเปิดเผยต่อ consumer ของ API** — ถูก resolve เป็น `image_url` (§5) |
| `business_unit_ids` | `Json @default("[]") @db.JsonB` | No | array ของ UUID `tb_business_unit.id`; `[]` = global (ทุก BU) |
| `status` | `enum_news_status @default(draft)` | No | `draft` · `published` · `archived` |
| `published_at` | `DateTime? @db.Timestamptz(6)` | Yes | ค่าประทับการ publish ครั้งแรก (server เป็นผู้ตั้ง, §2.2); เป็น cutoff การมองเห็นของ public feed ด้วย (`<= now()`) |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้สร้าง — **UUID เปล่า ไม่มี FK** |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้อัพเดทล่าสุด — UUID เปล่า ไม่มี FK |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้ลบ — UUID เปล่า ไม่มี FK |

**Constraint:**
- `@id` บน `id` — constraint ตัวเดียวเท่านั้น ไม่มี `@@unique` (อนุญาตหัวข้อซ้ำกันได้) ไม่มี FK ไปยังตารางใด ๆ

**Index:**
- `@@index([status, published_at])` — map `"tb_news_status_published_at_idx"` — ขับเคลื่อน query ของ public feed (`status = published AND published_at <= now()` เรียงตาม `published_at DESC`)

### 2.2 semantics การเขียนของ `published_at`

เป็นของ micro-cluster (`news.service.ts`) ไม่ใช่ของฐานข้อมูล:

```
create(data):
    status = data.status ?? draft
    published_at = data.published_at ?? null
    if status == published and published_at is null:
        published_at = now()                      -- ค่าประทับการ publish ครั้งแรก

update(id, data):
    if data.published_at provided:                -- การ set หรือเคลียร์แบบระบุชัดชนะ
        published_at = data.published_at (null = เคลียร์)
    else if data.status == published
         and existing.status != published
         and existing.published_at is null:       -- เฉพาะ row ที่ไม่เคย publish เท่านั้น
        published_at = now()
    else:
        published_at ไม่เปลี่ยนแปลง
```

ผลสืบเนื่อง: ค่าประทับถูกตั้ง**ครั้งเดียว** — การลดสถานะเป็น `draft`/`archived` คงค่าไว้ และการ re-publish ภายหลังคงเวลา*เดิม*ไว้ `published_at` ที่ลงวันที่อนาคต (ตั้งได้ผ่าน API เท่านั้น; SPA ไม่เคยส่ง field นี้) กัน row ไว้นอก public feed จนกว่าเวลานั้นจะมาถึง — เป็นการกำหนดเวลาเผยแพร่โดยพฤตินัย

## 3. ความสัมพันธ์

`tb_news` มีส่วนร่วมใน **Prisma relation เป็นศูนย์** การอ้างอิงเชิงตรรกะสองตัวเป็นไปตาม convention เท่านั้น:

- **`business_unit_ids` → `tb_business_unit.id` (M:N เชิงตรรกะ จัดเก็บเป็น JSONB)** micro-cluster ตรวจสอบตอน create และตอน update ใด ๆ ที่แตะ field นี้: ค่าต้องเป็น array ของ string และทุก id ที่ unique ต้อง match กับ row ของ `tb_business_unit` ที่ **live** อยู่ (`deleted_at: null`) — ไม่เช่นนั้นได้ 400 `One or more business_unit_ids do not exist` เนื่องจากไม่มีอะไรบังคับใช้หลังจากนั้น BU ที่ถูก soft-delete ภายหลังจะทิ้ง **id ค้าง (stale)** ไว้ใน array; การ match แบบ `array_contains` ของ public feed ยังคงเสิร์ฟ id ของ BU นั้นหาก caller ส่งมันมา
- **คอลัมน์ audit actor → `tb_user.id` (เชิงตรรกะ ไม่มี FK)** ถูก resolve เป็นชื่อสำหรับแสดงตอนอ่านโดยการ enrich audit ของ gateway (§5) ไม่ใช่ด้วย join

## 4. Enum

### `enum_news_status` (schema บรรทัด 693)

| ค่า | ความหมาย |
|---|---|
| `draft` | ค่าเริ่มต้น งานระหว่างทำ — มองไม่เห็นจาก public feed |
| `published` | เผยแพร่อยู่ — ถูกเสิร์ฟโดย `/api/public/news` เมื่อ `published_at <= now()` |
| `archived` | ปลดระวางจาก public feed แต่ยังมองเห็นได้ใน admin list; แตกต่างจาก soft delete (§5, กรณีพิเศษใน [Permissions](./permissions.md) §4) |

การ transition ไม่มีข้อจำกัดทั้งใน SPA (select ธรรมดา) และ backend (ไม่มี transition guard) — สถานะใดก็ย้ายไปสถานะอื่นใดได้

## 5. ความแตกต่างจาก shape ของ carmen-platform SPA

type ของ SPA คือ `News` ใน `../carmen-platform/src/types/index.ts`; ชั้นการแปลคือ `src/services/newsService.ts` บวกตัวจัดรูป response ฝั่ง gateway สองตัว (`news-image.helper.ts` และ interceptor `EnrichAuditUsers`)

| Shape ของ SPA | แหล่งที่มาใน SPA | การจัดเก็บใน Prisma | หมายเหตุ |
| --------- | ---------- | -------------- | ----- |
| `image_url?: string` (presigned) + `image?: string` (fallback แบบ legacy) | `News`; list/edit อ่าน `image_url \|\| image` | `image_file_token String?` | gateway resolve ตัว token ผ่าน micro-file (`files.presigned-url`, หมดอายุ 3600 วินาที), ตั้ง `image_url` และ**ลบ `image_file_token` ออกจาก payload** URL หมดอายุได้ — ห้าม persist หรือ cache มันเด็ดขาด `image` เป็น field ของ payload รุ่นเก่าที่คงไว้เพียงเป็น fallback ตอนอ่าน |
| `audit?: Audit` — แบบซ้อน `{ created, updated, deleted }` แต่ละตัว `{ at, id, name, avatar }` | `News`, `Audit`, `AuditEntry` | คอลัมน์ audit แบบแบนหกตัว | `@EnrichAuditUsers()` บน route GET/POST/PUT ยุบคอลัมน์แบบแบนเป็น object แบบซ้อน (resolve ชื่อ actor) และลบ field แบบแบนออก เมื่อการ enrich ล้มเหลว payload แบบแบนเดิมจะผ่านออกไป — จึงเป็นที่มาของแถวถัดไป |
| การตรวจจับ soft-delete แบบคู่: `!n.deleted_at && !n.audit?.deleted?.at` | `newsService.getAll` | `deleted_at` | **endpoint ของ admin list คืน row ที่ถูก soft-delete มาด้วย** (query ของ list ใน micro-cluster ไม่ apply filter `deleted_at`); SPA ซ่อนพวกมันฝั่ง client โดยตรวจสอบทั้งตำแหน่งที่ enrich แล้วและแบบแบน `getById`/update/delete บังคับใช้ `deleted_at: null` ฝั่ง server (404) |
| `business_unit_ids?: string[]` | `News` | `Json @default("[]")` | ค่าเดียวกัน; ภายใต้การเขียนแบบ **multipart** SPA จะ encode array เป็น string แบบ JSON ลงใน field ซึ่ง `news-body.parser.ts` parse กลับ ไม่มี field/`[]` ทั้งคู่หมายถึง global |
| sort ของ list `published_at:desc` (ค่าเริ่มต้น; header คอลัมน์คลิก sort ได้) | `DataTable` ของ `NewsManagement` | n/a | **server เพิกเฉยต่อ parameter ของ sort**: list ของ micro-cluster spread อาร์กิวเมนต์ของ query แล้ว override ด้วย `orderBy: { updated_at: 'desc' }` list จึงเรียงตามอัพเดทล่าสุดก่อนเสมอ ไม่ว่า UI ของ sort ใน SPA จะตั้งอย่างไร |
| response ของ update | `newsService.update` → re-fetch ด้วย `fetchNews()` | n/a | `PUT` คืนเพียง `{ id, image_url }` ไม่ใช่เรคคอร์ดเต็ม — SPA re-fetch หลังการ save ทุกครั้ง; consumer ของ API ต้อง `GET :id` เพื่อเอา row ที่อัพเดทแล้ว |
| `published_at?: string` (read-only ใน SPA) | `NewsEdit` | `DateTime?` | API รับ `published_at` แบบระบุชัดตอน create/update (set หรือเคลียร์ด้วย `null`); SPA ไม่เคยส่งมันและพึ่งพาค่าประทับของ server (§2.2) |

## 6. แหล่งข้อมูลอ้างอิง

REST surface (backend-gateway) **สังเกต prefix: `/api/news` ไม่ใช่ `/api-system/...`** — News อยู่ในกลุ่มโมดูล `application/` ของ gateway ต่างจากโมดูล platform-admin ที่ book นี้ document เป็นส่วนใหญ่

| Method + Path | Auth | วัตถุประสงค์ | หมายเหตุ |
|---|---|---|---|
| `GET /api/news` | Bearer + `x-app-id` (`news.findAll`) | Admin list | แบ่งหน้า; SPA ค้นหา `title`,`contents`; filter สถานะผ่าน `advance` `{ where: { status: { in } } }`; **รวม row ที่ถูก soft-delete**; audit แบบซ้อน; sort ฝั่ง server ถูกตรึงเป็น `updated_at DESC` |
| `GET /api/news/:news_id` | Bearer + `x-app-id` (`news.findOne`) | Detail | param แบบ UUID v4; 404 เมื่อถูก soft-delete; audit แบบซ้อน; `image_url` แบบ presigned |
| `POST /api/news` | Bearer + `x-app-id` (`news.create`) | สร้าง | `multipart/form-data` (binary ใน field `image`; `business_unit_ids` เป็น string ที่ encode เป็น JSON) **หรือ** JSON ธรรมดาแบบไม่มีรูป คืน 201 `{ id, image_url }` (`image_url` เป็น `null` เว้นแต่มีการอัพโหลดไฟล์) create ที่ล้มเหลวจะ roll back ไฟล์ที่อัพโหลดไปแล้ว |
| `PUT /api/news/:news_id` | Bearer + `x-app-id` (`news.update`) | อัพเดท | ทางแยก multipart/JSON เดียวกัน; รูปใหม่จะแทนที่และลบไฟล์เก่า; update แบบ JSON อย่างเดียวไม่แตะรูป คืน `{ id, image_url }` เท่านั้น |
| `DELETE /api/news/:news_id` | Bearer + `x-app-id` (`news.delete`) | Soft delete | ตั้ง `deleted_at`/`deleted_by_id`; ลบไฟล์ MinIO แบบ best-effort |
| `GET /api/public/news` | **ไม่มี (anonymous)** | Public feed | query `bu_id`/`page`/`perpage`; published + `published_at <= now()` + ไม่ถูกลบ; ไม่มี `bu_id` → global เท่านั้น; มี `bu_id` → global + ที่กำหนดเป้าหมาย; projection แบบ lean (`id`,`title`,`contents`,`url`,`image_url`,`published_at`), เรียง `published_at DESC` |
| `GET /api/public/news/:news_id` | **ไม่มี (anonymous)** | Public detail | 404 เหมือนกันหมดสำหรับ draft/archived/ถูกลบ/ลงวันที่อนาคต/ไม่รู้จัก |

รายละเอียดรูปแบบ multipart (create/update): field `image` ถือ binary; `validateImageUpload` ของ gateway บังคับ MIME `image/jpeg`/`png`/`webp`, ≤5 MB และ ≤2048×2048 px (parse ล้มเหลว → 400 `BAD_DIMENSIONS`) field ที่เป็นข้อความมาถึงเป็น string; เฉพาะ `business_unit_ids` เท่านั้นที่ถูก decode จาก JSON

**หลัก (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_news` (บรรทัด 803), `enum_news_status` (บรรทัด 693)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` — การตรวจสอบ BU, การประทับ `published_at`, soft delete, filter ฝั่ง public, การ override sort เป็น `updated_at`

**รอง (gateway + shape ฝั่ง consumer):**
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/` — `news.controller.ts`, `news.service.ts` (อัพโหลด/rollback/cleanup), `news-image.helper.ts`, `news-body.parser.ts`, `public-news.controller.ts`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/helpers/image-upload.validator.ts` — ขีดจำกัดรูปภาพฝั่ง server
- `../carmen-platform/src/types/index.ts` — `News`, `NewsStatus`, `Audit`, `AuditEntry`; `src/services/newsService.ts` — ตัวสร้าง multipart, การเดิน envelope, filter soft-delete
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/news/` — สัญญาที่ execute ได้ รวมถึงคู่ `public/`

**Cross-link:** [หน้า landing ของ News](/th/platform/news) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Business Units data-model](../business-units/data-model.md) (id ที่ถูกกำหนดเป้าหมาย)
