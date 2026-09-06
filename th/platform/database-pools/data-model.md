---
title: พูลฐานข้อมูล — โมเดลข้อมูล (Data Model)
description: ตารางฟิลด์เต็มของ tb_database_pool — รหัสผ่านที่เข้ารหัส, note เทียบกับ description, ความหมายของ is_active — พร้อมการยืนยันตรงกับสิ่งที่ Business Units และ Tenant Migrations พูดถึงการ resolve connection ของ tenant ไว้แล้ว
published: true
date: '2026-09-06T21:00:00.000Z'
tags: book/platform, database-pools, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# พูลฐานข้อมูล — โมเดลข้อมูล (Data Model)

> **Source of truth:** อ่านสิ่งเหล่านี้ก่อนแก้ไขหน้านี้
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1382-1411` — `model tb_database_pool`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/database-pool.service.ts` — `POOL_SELECT`, `maskPassword`, `passwordPatch`, `create`, `update`, `delete` (อ่านครบ)
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrate.database-pool.ts` — สคริปต์ backfill `db_connection` → pool ครั้งเดียว (อ่านครบ)
> - `../carmen-turborepo-backend-v2/packages/secret-crypto/src/crypto.util.ts` — `encryptSecret`/`decryptSecret`
> - `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts` — `buildTenantUrl`/`resolveTenantUrl`
>
> ยืนยันกับ `carmen-platform` HEAD `157a65e` (2026-09-04) และ `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06)

## 1. ภาพรวม

`tb_database_pool` เป็นตารางแบนที่ไม่มีตารางลูกของตัวเองเลย — หนึ่งแถวต่อหนึ่งเซิร์ฟเวอร์ Postgres ที่ลงทะเบียนไว้ อ้างอิงจากที่เดียวเท่านั้นคือ `tb_business_unit.database_pool_id` มันแทนที่ `tb_business_unit.db_connection` ซึ่งเป็น JSON blob ต่อ BU (`{ host, port, database, schema, user, password }` ที่มีรหัสผ่านแบบ **plaintext**) ที่ถูกลบออกจากสคีมาจริงเมื่อ 2026-08-13 หน้านี้บันทึกชุดฟิลด์เต็มของตาราง วิธีที่รหัสผ่านเดินทางจาก plaintext ที่กรอกเข้ามาไปเป็น ciphertext ที่เก็บไว้และกลับมา และ — เนื่องจาก [Business Units](/th/platform/business-units/data-model) §2.4 กับ [Tenant Migrations](/th/platform/tenant-migrations/data-model) §3 ต่างก็พูดถึงตารางนี้ไว้แล้วเพื่อจุดประสงค์ที่แคบกว่าของแต่ละหน้า — สิ่งที่หน้านี้บอกไว้ตรงกับทั้งสองหน้านั้นอย่างไร (§5)

## 2. Entity: `tb_database_pool`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid` | ไม่ | Primary key |
| `name` | `String @db.VarChar` | ไม่ | ผู้ดูแลตั้งเองจากฟอร์มสร้าง/แก้ไข หรือ — สำหรับ pool ที่สคริปต์ backfill เดิมสร้างอัตโนมัติ — มาจาก DSN ของตัวเอง (`host:port/database` หรือมี `(username)` ต่อท้ายเมื่อ pool ที่สร้างอัตโนมัติสองตัวจะใช้สตริงเดียวกัน) ต้องไม่ซ้ำกันในบรรดา pool ที่ยังไม่ถูกลบ — ชื่อซ้ำตอนสร้างหรือตอนเปลี่ยนชื่อ pool ที่มีอยู่จะคืน `DATABASE_POOL_NAME_EXISTS` (409) |
| `description` | `String?` | ใช่ | หมายเหตุอิสระที่ผู้ดูแลกรอกเอง (เช่น "Singapore production cluster") แสดงบนหน้าบันทึกของหน้าแก้ไขก็ต่อเมื่อมีค่า |
| `host` | `String @db.VarChar` | ไม่ | ชื่อโฮสต์ของเซิร์ฟเวอร์ **ไม่เคยแสดงบนหน้าแก้ไข Business Units** ([UI Screens](/th/platform/business-units/ui-screens) §4.4) — เห็นได้เฉพาะ session ที่มี `database_pool.read` บนหน้าจอของโมดูลนี้เองเท่านั้น |
| `port` | `Int @default(5432) @db.Integer` | ไม่ | TCP port ฟอร์มสร้าง/แก้ไขตรวจสอบฝั่ง client ว่าเป็นจำนวนเต็ม 1–65535 และตั้งเป็น 5432 โดยดีฟอลต์ถ้าปล่อยว่างตอน submit |
| `database` | `String @db.VarChar` | ไม่ | ชื่อฐานข้อมูลบนเซิร์ฟเวอร์นั้น |
| `username` | `String @db.VarChar` | ไม่ | Username สำหรับเชื่อมต่อ — เป็น login ฐานข้อมูลดิบ ไม่ถูกตรวจว่าเป็นอีเมล (case `validateField('username')` ที่แชร์กัน เขียนไว้สำหรับโมดูล Users จงใจไม่ถูกนำมาใช้ซ้ำที่นี่) |
| `password` | `String @db.VarChar` | ไม่ | Ciphertext จาก `encryptSecret()` (AES-256-GCM, `enc:v1:<iv_b64>:<authTag_b64>:<ciphertext_b64>`, `../carmen-turborepo-backend-v2/packages/secret-crypto/src/crypto.util.ts`) ดู §4 สำหรับวงจรเต็ม — **ค่า plaintext ของมันไม่เคยปรากฏใน response ของ API, ในหน้านี้ หรือในวิกินี้เลย** |
| `is_active` | `Boolean @default(true) @db.Boolean` | ไม่ | ดู §3 สำหรับผลของมันต่อ picker ของ Business Units และการ resolve connection |
| `note` | `String?` | ใช่ | คนละคอลัมน์กับ `description` (`schema.prisma:1398`) สคริปต์ backfill เดิมเขียนค่าตายตัว `'สร้างอัตโนมัติจาก tb_business_unit.db_connection'` ลงไปโดยอัตโนมัติ (`migrate.database-pool.ts:412`) บนทุก pool ที่มันสร้างจาก connection blob เดิมของ BU — เป็นสัญญาณว่าแถวนั้นไม่ได้ถูกตั้งค่าด้วยมือ ไม่ใช่ช่องคอมเมนต์อเนกประสงค์ แม้ว่าฟอร์มสร้าง/แก้ไขจะให้ผู้ดูแลตั้งหรือเปลี่ยนค่านี้เองในภายหลังได้อย่างอิสระก็ตาม |
| `doc_version` | `Int @default(0) @db.Integer` | ไม่ | ตัวนับ optimistic lock **จำเป็นต้องส่งทุกครั้งที่ `PUT` ไม่มีข้อยกเว้น** — `DatabasePoolUpdateDto` ไม่มีค่า default และ backend ปฏิเสธการอัปเดตที่ `data.doc_version` ไม่ใช่ตัวเลข (`COMMON_DOC_VERSION_REQUIRED`) ต่างจาก entity พี่น้องบางตัวที่ตีความ token ที่หายไปว่า "ข้ามการเช็ค conflict" |
| `created_at` / `created_by_id` / `updated_at` / `updated_by_id` / `deleted_at` / `deleted_by_id` | `DateTime?` / `String? @db.Uuid` | ใช่ | คอลัมน์ audit/soft-delete มาตรฐาน แสดงผ่าน `auditColumns()`/`normalizeAudit()` ที่แชร์กันบนหน้ารายการและหน้าแก้ไข |

**เลือกเฉพาะบางฟิลด์ ไม่ใช่ทุกคอลัมน์ที่ถูกดึงมาทุกครั้ง** ค่าคงที่ `POOL_SELECT` ของ `DatabasePoolService` (`database-pool.service.ts:11-27`) คือรายการฟิลด์เต็มด้านบนลบ `deleted_at`/`deleted_by_id` — service กรอง `deleted_at: null` ที่ระดับ query แทนที่จะส่งคืนให้ client

**Index:** `@@index([deleted_at], map: "database_pool_deleted_at_idx")` ไม่มี unique constraint ระดับฐานข้อมูลบน `name` ที่ประกาศไว้ใน Prisma — ความไม่ซ้ำที่ API บังคับ (ดูข้างบน §2) เป็นการเช็ค `findFirst` ระดับ application ใน `create()`/`update()` ไม่ใช่ `@@unique`

## 3. ความสัมพันธ์กับ `tb_business_unit`

```
tb_database_pool  1 ─── M  tb_business_unit   (ผ่าน tb_business_unit.database_pool_id, nullable)
```

- `tb_business_unit.database_pool_id` — `String? @db.Uuid` FK ที่เป็น nullable ไปยัง `tb_database_pool.id`, `onDelete: NoAction` `NULL` หมายถึง business unit นั้นยังไม่เคยถูกผูกกับ pool ใดเลย
- `tb_business_unit.db_schema` — `String? @db.VarChar` ชื่อ schema ของ BU เอง **ภายใน** `database` ของ pool นั้น ไม่ใช่คอลัมน์บนตารางนี้ — อยู่ที่ business unit หนึ่งชื่อต่อหนึ่ง BU เพราะ pool (เซิร์ฟเวอร์ + ฐานข้อมูล) ใช้ร่วมกันได้ แต่ schema ไม่ได้
- Pool ที่ยังมี business unit ที่ยังไม่ถูกลบ (`deleted_at: null`) หนึ่งตัวหรือมากกว่าชี้มาหา **จะลบไม่ได้**: `DatabasePoolService.delete()` ค้นหา business unit แบบนี้สูงสุด 10 ตัวด้วย `code` แล้วคืน `DATABASE_POOL_IN_USE` (409) ระบุชื่อ แทนที่จะลบ pool ทิ้งไปทั้งที่ BU บางตัวยัง resolve connection ของ tenant ผ่านมันอยู่
- `is_active: false` ไม่ตัดการเช็คนี้ออก — pool ที่ปิดอยู่แต่ยังมี BU ที่ยังไม่ถูกลบผูกอยู่ก็ยังนับว่า "ถูกใช้งาน" และยังลบไม่ได้ `is_active` มีผลแค่กับ picker ของ Business Units เท่านั้น (pool ที่ปิดยังเลือกได้บน BU ที่ผูกอยู่แล้ว แต่หลุดจาก option list ตอนผูก BU **ใหม่**) และกับการ**resolve connection** (§5): pool ที่ปิดอยู่ทำให้ทุก BU ที่ชี้มาที่มัน resolve connection ไม่สำเร็จ โดยไม่ต้องถูกลบก่อนเลย

## 4. ความลับและการเข้ารหัส

1. **ค่าที่กรอกเข้ามา** ฟอร์มสร้างใหม่ต้องการรหัสผ่านแบบ plaintext (ถ้าว่างเปล่าจะไม่ผ่าน validation ฝั่ง client และถูกปฏิเสธแยกต่างหากฝั่ง server เป็น `COMMON_VALIDATION_FAILED` ถ้ามันหลุดไปถึง API ได้จริง) ช่องรหัสผ่านของฟอร์มแก้ไขเป็นทางเลือกและเริ่มว่างเปล่าเสมอแม้จะโหลด pool ที่มีอยู่แล้วมาแสดง — API ไม่เคยส่งค่าจริงกลับมา จึงไม่มีอะไรให้เติมล่วงหน้า
2. **ตอนเก็บ** `encryptSecret()` สร้าง `enc:v1:<iv>:<authTag>:<ciphertext>` ภายใต้ `SECRET_ENCRYPTION_KEY` (32 ไบต์ hex หรือ base64 อ่านครั้งเดียวแล้ว cache ไว้ต่อ process) key นี้ไม่มีค่า default ระดับโค้ด: `getKey()` throw ทันทีถ้า env var ไม่ถูกตั้ง และทั้ง `config.env.ts` ของ `micro-cluster` และ `micro-business` ประกาศให้เป็น string ที่จำเป็นและห้ามว่างเปล่าตอน startup ไม่ใช่ตัวเลือกที่มี fallback
3. **ในทุก API response** `maskPassword()` (`database-pool.service.ts:40-42`) แทนที่ ciphertext ด้วยสตริงตายตัว `••••••` ก่อนที่แถวจะออกจาก service เลย — list, get และแถวที่คืนจาก create/update ถูกมาสก์เหมือนกันหมด **ไม่มี endpoint ใดในโค้ดชุดนี้เปิดเผยค่าที่ถอดรหัสแล้ว หรือแม้แต่ ciphertext เลย**
4. **ตอนอัปเดต** `passwordPatch()` (`database-pool.service.ts:50-54`) ตีความค่าที่ส่งเข้ามาเป็น `undefined` **หรือสตริงมาสก์เป๊ะ ๆ** ว่า "ไม่เปลี่ยนแปลง" (คืน `{}` ปล่อย ciphertext เดิมไว้) ค่าว่างเปล่าหรือค่าที่ไม่ใช่ string ถูกปฏิเสธว่าไม่ถูกต้อง มีแต่ plaintext ใหม่ที่ต่างจากเดิมจริง ๆ เท่านั้นที่จะถูกเข้ารหัสใหม่แล้วเก็บ นี่คือสิ่งที่ทำให้ฟอร์มแก้ไขส่งค่าที่มาสก์หรือว่างกลับไปได้เสมอโดยไม่เสี่ยงเขียนทับรหัสผ่านจริงด้วยตัวมาสก์เองโดยไม่ตั้งใจ
5. **ตอนใช้งานจริง** ไม่มีอะไรในโมดูลนี้ถอดรหัสรหัสผ่านของ pool เอง — สิ่งนั้นเกิดขึ้นก็ต่อเมื่อ *ผู้บริโภค* resolve connection ของ tenant [Tenant Migrations](/th/platform/tenant-migrations/data-model) §3 บันทึกเส้นทางนั้นไว้: `resolveTenantUrl()` (`../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts`) เรียก `decryptSecret()` แล้ว throw เมื่อล้มเหลว แทนที่จะถอยไปเดาว่าเป็น plaintext — "ไม่มี fallback โดยตั้งใจ" ตาม comment ของฟังก์ชันนั้นเอง — จากนั้น `buildTenantUrl()` ประกอบ `postgresql://{user}:{password}@{host}:{port}/{database}?schema={db_schema}` โดย `host`/`port` ถูกตรวจสอบ (`isSafeHost`/`isSafePort`) และส่วนอื่นทุกส่วนถูก percent-encode
6. **ที่มาของการ backfill** สคริปต์ครั้งเดียว `migrate.database-pool.ts` (§1) เป็นจุดเดียวในโค้ดชุดนี้ที่เคยอ่านรหัสผ่านแบบ plaintext จาก `db_connection` ตรง ๆ เป็น dry-run โดยดีฟอลต์ ต้องใส่ `--apply` ถึงจะเขียนจริง และมีโหมด `--verify` แยกต่างหากที่ถอดรหัสผ่านของทุก pool ที่ยังไม่ถูกลบแล้วรายงานว่า pool *ชื่อ* ไหน (ไม่เคย log ciphertext หรือ plaintext) ถอดรหัสไม่ผ่านภายใต้ key ที่ตั้งค่าอยู่ปัจจุบัน — ตั้งใจให้รันครั้งเดียวก่อน migration ที่ลบ `db_connection` จะรัน สคริปต์นี้รันเส้นทาง scan/backfill ไม่ได้อีกแล้ววันนี้: มันต้องพึ่งคอลัมน์ `db_connection` ที่ migration `7f825bb20` ลบไปแล้ว มันยังอยู่ในโปรเจกต์แค่เป็นบันทึกว่าการย้ายข้อมูลครั้งเดียวนั้นทำอย่างไร ตามที่ comment หัวไฟล์ของมันเองระบุ

ไม่พบรหัสผ่าน, connection string หรือ encryption key ที่ฝังไว้แบบ hardcode ที่ใดเลยในฝั่ง frontend, backend หรือสคริปต์ backfill ของโมดูลนี้ — ตรวจแล้วทั้ง `emptyForm`/`buildPayload` ของ `DatabasePoolEdit.tsx` (มีแต่สตริงว่างเปล่า ไม่มี credential ที่ฝังไว้), `database-pool.service.ts` (เข้ารหัสสิ่งที่ส่งเข้ามาเท่านั้น ไม่มีค่า fallback) และ `crypto.util.ts` (throw แทนที่จะใช้ค่า default) เรื่องนี้ควรพูดให้ชัดเพราะโมดูลพี่น้องในวิกินี้เคยถูกแก้ไขจากการกล่าวอ้างแบบนี้พอดี: ดู [Platform Migrations](/th/platform/platform-migrations) §3.1 ที่ `PLATFORM_DEPLOY_TOKEN` ของมัน**มี** ค่า default เป็น string ว่างใน `config.env.ts` จริง

## 5. ความสอดคล้องกับ Business Units และ Tenant Migrations

หน้าพี่น้องทั้งสองพูดถึงตารางนี้ไว้แล้ว แต่ละหน้าลึกเท่าที่ผู้อ่านของตัวเองต้องใช้ หน้านี้เห็นตรงกับทั้งสองหน้า และเป็นที่เดียวที่ผู้อ่านควรมาหาตารางฟิลด์แบบเต็ม

- **[Business Units — Data Model](/th/platform/business-units/data-model) §2.4** บันทึก `id`, `name`, `description`, `host`, `port`, `database`, `username`, `password`, `is_active` และคู่ audit/soft-delete — เก้าจากสิบคอลัมน์จริง โดยระบุขอบเขตไว้ชัดเจนเอง ("documented here only to the depth a Business Units reader needs; the full module is out of this page's scope") มันตัด `note` ออกไปเพียงเพราะหน้านั้นไม่มีเหตุผลต้องพูดถึง — ไม่มีอะไรที่มันระบุเกี่ยวกับอีกเก้าฟิลด์, ทิศทางความสัมพันธ์ หรือการลบ `db_connection` ที่ขัดแย้งกับ §2–3 ข้างบน
- **[Tenant Migrations — Data Model](/th/platform/tenant-migrations/data-model) §3** บันทึกชุดย่อยของฟิลด์ที่ป้อนเข้า `resolveConnectionForBusinessUnit()` — `host`, `port`, `database`, `username`, `password`, `is_active`, `deleted_at` — ในกรอบ "Role here" และตาราง error 5 แถวของมัน (ไม่ได้ผูกกับ pool / ไม่ได้ตั้ง schema / pool ถูกลบ / pool ปิดอยู่ / รหัสผ่านถอดรหัสไม่ผ่าน) ตรงกับ `tenant.service.ts` เป๊ะตามที่อ่านมาสำหรับหน้านี้ ไม่พบความขัดแย้ง
- ทั้งสองหน้าระบุ และหน้านี้ยืนยันแยกต่างหากจาก `migrate.database-pool.ts` และ migration สองตัวเมื่อ 2026-08-13 ว่า `db_connection` ถูก**ลบออกจริง** ไม่ใช่แค่เลิกใช้ และ `database_pool_id`/`db_schema` เป็นเส้นทางเดียวไปสู่ connection ของ tenant ของ business unit หนึ่งตัวในวันนี้

## 6. Edge Cases

| สถานการณ์ | สิ่งที่เกิดขึ้นจริง | แหล่งที่มา |
|---|---|---|
| Pool ที่มี business unit ผูกอยู่ถูกสั่งลบ | ถูกปฏิเสธ (409 `DATABASE_POOL_IN_USE`) ระบุ BU ที่บล็อกอยู่สูงสุด 10 ตัวด้วย `code` | `database-pool.service.ts:247-272` |
| Pool ถูกปิด (`is_active: false`) ขณะที่ยังมี BU ผูกอยู่ | ไม่ถูกบล็อก — การปิดไม่ใช่การเช็ค in-use ทุก BU ที่ยังผูกอยู่จะ resolve connection ของ tenant ไม่สำเร็จด้วยข้อความ "is inactive" ครั้งถัดไปที่ [Tenant Migrations — Data Model](/th/platform/tenant-migrations/data-model) §3 พยายาม resolve มัน | `tenant.service.ts` (ตามหน้านั้น); `database-pool.service.ts` (ไม่มีการเช็ค active ตอนอัปเดต) |
| Business unit สองตัวมี `db_connection` เดิมที่ host/port/database/username ตรงกันแต่รหัสผ่านต่างกัน | สคริปต์ backfill ไม่เดาให้และหยุดทั้ง run ทั้งชุดด้วย error ที่ระบุ code ของทั้งสอง business unit — ถือเป็นข้อมูลขัดแย้งที่ต้องแก้ด้วยคน ไม่ใช่สิ่งที่จะเลือกฝ่ายใดฝ่ายหนึ่งให้เงียบ ๆ | `migrate.database-pool.ts:338-345` |
| `db_connection` เดิมไม่มีค่า `schema` | Business unit นั้นถูกข้าม (นับและรายงาน ไม่ใช่ตกหล่นแบบเงียบ ๆ) แทนที่จะย้ายด้วยการเดา schema | `migrate.database-pool.ts:316-319` |
| `SECRET_ENCRYPTION_KEY` ของ `micro-cluster` (เข้ารหัสตอนเขียน) กับ `micro-business` (ถอดรหัสตอน resolve connection) ไม่ตรงกัน | ทุก pool ที่ได้รับผลกระทบจะถอดรหัสไม่ผ่านตอน resolve connection ด้วยข้อความ "Failed to decrypt the database pool password (check `SECRET_ENCRYPTION_KEY`...)" — ความไม่ตรงกันนี้โผล่มาเป็นความล้มเหลวของ tenant-migration/connection ไม่ใช่ error ตรวจสอบ config ตอน startup ของ service ไหนเลย | `crypto.util.ts` (key แยกต่อ service ไม่มีการเช็คข้าม service); `tenant-url.ts:58-68` |
| session ที่มีแค่ `database_pool.read` เปิด `/platform/database-pools/new` | เห็นและกรอกทุกฟิลด์ของฟอร์มสร้างใหม่ได้ แต่ submit ไม่ได้ผ่านทั้งปุ่ม Save (ไม่ render) และผ่าน Enter/`Ctrl+S` (`handleSubmit` เช็ค `hasPermission('database_pool.manage')` เองแล้วคืนค่าก่อน) ดู [หน้าหลัก](/th/platform/database-pools) §4 | `DatabasePoolEdit.tsx:260`, `App.tsx:517` |

## 7. คำแนะนำ

- **เพิ่ม `@@unique` บน `name`** (จำกัดขอบเขตแค่แถวที่ยังไม่ถูกลบ ตามรูปแบบที่ใช้ที่อื่นในสคีมานี้ เช่น `business_unit_code_global_u`) เพื่อให้ความไม่ซ้ำที่โมดูลนี้บังคับไว้ที่ระดับ application ถูกรับประกันที่ระดับฐานข้อมูลด้วย ป้องกันเส้นทางเขียนที่สองที่โมดูลนี้ไม่ได้ควบคุม (backend service ในอนาคต, สคริปต์ หรือการ insert ผ่าน `psql` ด้วยมือ)
- **พิจารณา gate `/platform/database-pools/new` และ `/:id/edit` ด้วย `database_pool.manage` ที่ระดับ route** ให้ตรงกับที่ [Business Units](/th/platform/business-units) gate route `/new` และ `/:id/edit` ของตัวเองด้วย permission create/update ไม่ใช่ permission อ่าน — การตั้งค่า `database_pool.read` บนทุก route ปัจจุบัน (§4 ของหน้าหลัก) ไม่ได้ถูกใช้ประโยชน์ในทางที่เป็นอันตรายจากการเช็คภายในฟอร์ม แต่ก็ไม่ตรงกับรูปแบบที่โมดูล CRUD อื่นในวิกินี้ใช้เหมือนกัน
- **รัน `migrate.database-pool.ts --verify` เป็นประจำตามตารางเวลา** ไม่ใช่แค่ครั้งเดียวก่อน migration ที่ลบ `db_connection` ที่มันถูกเขียนมาเพื่อรองรับ — การหมุนเวียน `SECRET_ENCRYPTION_KEY` ที่ทำโดยไม่ได้เข้ารหัส pool ที่มีอยู่แล้วใหม่ จะถูกพบก็ต่อเมื่อมีคนพยายาม resolve connection ของ tenant ครั้งถัดไปเท่านั้น

## 8. แหล่งอ้างอิง

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1382-1411` — `model tb_database_pool`
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/database-pool.service.ts` — อ่านครบ
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/database-pool.controller.ts` — RPC message handler อ่านครบ
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_database-pools/platform_database-pools.service.ts` — RPC proxy จาก gateway
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts:515-517`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260813000000_database_pool_additive/` (commit `343b8c16b`) และ `.../20260813010000_database_pool_drop_db_connection/` (commit `7f825bb20`)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrate.database-pool.ts` — อ่านครบ
- `../carmen-turborepo-backend-v2/packages/secret-crypto/src/crypto.util.ts`, `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts`
- `../carmen-platform/src/pages/DatabasePoolEdit.tsx`, `src/utils/databasePool.ts`
- [Business Units — Data Model](/th/platform/business-units/data-model) §2.4; [Tenant Migrations — Data Model](/th/platform/tenant-migrations/data-model) §3 — ตรวจสอบไขว้กันใน §5 ข้างบน
