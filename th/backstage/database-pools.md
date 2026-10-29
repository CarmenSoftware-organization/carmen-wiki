---
title: พูลฐานข้อมูล (Database Pools)
description: ทะเบียน CRUD ของ Postgres connection pool ที่แชร์ระดับแพลตฟอร์ม (tb_database_pool) — แหล่งเดียวของ credential ฐานข้อมูล tenant หลัง db_connection ถูกลบ แทนด้วย database_pool_id + db_schema
published: true
date: 2026-10-29T05:30:00.000Z
tags: book/backstage, database-pools
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# พูลฐานข้อมูล (Database Pools)

> **At a Glance**
> **จุดประสงค์โมดูล:** ทะเบียนของเซิร์ฟเวอร์ฐานข้อมูลที่แชร์กันระดับแพลตฟอร์ม ซึ่ง business unit แต่ละตัวชี้ schema ของ tenant ตัวเองไปหา — โมดูลนี้เป็นเจ้าของ `tb_database_pool` ตารางที่ `tb_business_unit.database_pool_id` ถูกผูกไปหลังจาก `db_connection` ถูกลบ &nbsp;·&nbsp; **หน้าจอ:** `DatabasePoolManagement` (รายการ, `/backstage/database-pools`) และ `DatabasePoolEdit` ใช้ทั้งสร้าง (`/backstage/database-pools/new`) และแก้ไข (`/backstage/database-pools/:id/edit`) &nbsp;·&nbsp; **Sidebar:** `permission: 'database_pool.read'` กลุ่ม `navGroup.database` (อยู่กลุ่มเดียวกับ Backstage Migrations — หน้า wiki [Backstage Migrations](/th/backstage/backstage-migrations) — และ `sql_workbench`) &nbsp;·&nbsp; **Feature flag:** `database_pools` &nbsp;·&nbsp; **`superAdminOnly`:** ไม่ใช่ — gate ด้วย RBAC permission ปกติ ไม่ใช่ flag super-admin &nbsp;·&nbsp; **โมเดลสอง permission:** `database_pool.read` (list/get และ — ดู §4 — เป็น permission **เดียว** ที่ frontend route guard เช็คบนทั้งสามเส้นทาง รวมถึง `/new` และ `/:id/edit`) กับ `database_pool.manage` (create/update/delete บังคับด้วย `<Can>` บนทุกปุ่มที่เขียนข้อมูล **และ** เช็คซ้ำใน submit handler) &nbsp;·&nbsp; **ความลับ:** ทุก pool มี `password` ที่รับเข้ามาเป็น plaintext แต่เก็บเป็น ciphertext — API มาสก์เป็น `••••••` ในทุก response และ**ไม่มี endpoint เปิดเผยค่าจริง**เลยในโค้ดชุดนี้ &nbsp;·&nbsp; **e2e suite:** ไม่มี — `../carmen-backstage-e2e/tests/` ไม่มีโฟลเดอร์ `database-pools` &nbsp;·&nbsp; **หน้าย่อย:** 2

![พูลฐานข้อมูล (Database Pools) screen](/screenshots/backstage/database-pools/index.png)

## 1. ภาพรวม

Database pool คือโปรไฟล์การเชื่อมต่อที่ตั้งชื่อได้หนึ่งชุดไปยังเซิร์ฟเวอร์ Postgres จริงหนึ่งเครื่อง — host, port, ชื่อฐานข้อมูล, username และรหัสผ่านที่เข้ารหัสแล้ว — ที่ business unit หนึ่งตัวหรือมากกว่าใช้ร่วมกัน `DatabasePoolManagement.tsx` (`../carmen-backstage/src/pages/DatabasePoolManagement.tsx`, 468 บรรทัด) แสดงรายการ pool ที่ยังไม่ถูกลบทุกตัวเป็น **DSN** เดียวต่อแถว (`username@host:port/database` ประกอบด้วย helper กลาง `poolDsn()`) พร้อมปุ่มคัดลอกครั้งเดียว, badge Active/Inactive และคอลัมน์ audit มาตรฐาน `DatabasePoolEdit.tsx` (`../carmen-backstage/src/pages/DatabasePoolEdit.tsx`, 672 บรรทัด) เป็น component เดียวกันทั้งตอนสร้าง pool ใหม่ (`/backstage/database-pools/new`) และแก้ไข pool ที่มีอยู่ (`/backstage/database-pools/:id/edit`) — โหมดอ่านของมัน render เป็นบันทึกธรรมดา (`RecordRow` แบบป้าย/ค่า) ไม่ใช่ฟอร์มที่ถูกล็อก

โมดูลนี้มีอยู่เพราะ `tb_business_unit` ไม่เก็บ credential ฐานข้อมูลของตัวเองอีกต่อไป ก่อนหน้า migration ใน `../carmen-turborepo-backend` เมื่อ 2026-08-13 connection ของ tenant หนึ่ง business unit เคยอยู่ใน JSON blob `db_connection` ของตัวเอง (host/port/database/schema/user/password รวมถึงรหัสผ่านแบบ **plaintext**) Migration `20260813000000_database_pool_additive` (commit `343b8c16b`) เพิ่มตาราง `tb_database_pool` และคอลัมน์ `database_pool_id`/`db_schema` บน `tb_business_unit` **ควบคู่กับ** blob เดิม จากนั้นสคริปต์ backfill ครั้งเดียว (`packages/prisma-shared-schema-backstage/prisma/migrate.database-pool.ts`) ย้าย `db_connection` ของทุก business unit ไปเป็นแถว pool ที่ไม่ซ้ำและเข้ารหัสแล้ว แล้วผูกแต่ละ BU กลับเข้า pool นั้น ก่อนที่ migration `20260813010000_database_pool_drop_db_connection` (commit `7f825bb20`) จะลบคอลัมน์ `db_connection` ทิ้งจริงในที่สุด ดู [Data Model](/th/backstage/database-pools/data-model) §2 สำหรับตารางฟิลด์เต็ม และ §5 สำหรับการยืนยันว่าหน้านี้พูดตรงกับ [Business Units](/th/backstage/business-units) และ [Tenant Migrations](/th/backstage/tenant-migrations) อย่างไร

## 2. บริบททางธุรกิจ

ข้อมูล inventory ของแต่ละ business unit ใน Carmen Blue อยู่ใน Postgres **schema** ของตัวเอง ไม่ใช่ฐานข้อมูลหรือเซิร์ฟเวอร์แยกทั้งชุด — connection ของ tenant หนึ่ง BU คือ "pool ไหน" (เซิร์ฟเวอร์ที่แชร์กัน) บวก "schema ไหน" (`db_schema` เฉพาะของ BU นั้น) ข้างในนั้น ก่อนมีโมดูลนี้ business unit ที่บังเอิญใช้เซิร์ฟเวอร์จริงเครื่องเดียวกันยังคงเก็บ host/port/username/password ของเซิร์ฟเวอร์นั้นซ้ำกันบนแถวของตัวเอง — credential เดียวกัน ไม่ว่าจะเข้ารหัสหรือไม่ ถูกพิมพ์ซ้ำหนึ่งครั้งต่อหนึ่ง tenant การรวม connection ไว้ที่ `tb_database_pool` ที่เดียวหมายความว่าการหมุนเวียน credential, การย้ายเซิร์ฟเวอร์ หรือการเปลี่ยน port คือการแก้ที่เดียวตรงนี้ ที่มีผลกับทุก business unit ที่อ้างถึง pool นั้น แทนที่จะต้องแก้และ deploy ใหม่ทีละ business unit

การทำแบบนี้ยังรวมจุดเดียวในสคีมาแพลตฟอร์มที่ถือ credential ฐานข้อมูลจริงไว้ที่เดียว รหัสผ่านถูกเข้ารหัสไว้ก่อนเก็บ (`encryptSecret()`/`decryptSecret()`, `../carmen-turborepo-backend/packages/secret-crypto/src/crypto.util.ts`, AES-256-GCM รูปแบบ `enc:v1:<iv>:<authTag>:<ciphertext>`) ภายใต้ environment key เดียว `SECRET_ENCRYPTION_KEY` ที่ `micro-cluster` (backend ของโมดูลนี้เอง), `micro-business` (backend ของ [Tenant Migrations](/th/backstage/tenant-migrations)) และ `micro-notification` ต้องตั้งค่าให้ตรงกันทุกตัว — ค่าที่ไม่ตรงกันจะล้มเหลวตอน **ถอดรหัส** ไม่ใช่ตอนเขียน จึงโผล่มาเป็น "เชื่อมต่อฐานข้อมูล tenant ไม่ได้" หรือ "ส่งอีเมลไม่ได้" แทนที่จะเป็น error เรื่อง config ทั้ง `apps/micro-cluster/src/libs/config.env.ts:52` และ `apps/micro-business/src/libs/config.env.ts:88` ประกาศ `SECRET_ENCRYPTION_KEY` เป็น string ที่จำเป็นและห้ามว่างเปล่า (`z.string().min(1, ...)`) — `getKey()` ของ `crypto.util.ts` เองก็ throw ทันทีถ้า env var ไม่ถูกตั้ง แทนที่จะถอยไปใช้ค่าใด ๆ ที่ฝังไว้ในโค้ด — ตรวจสอบตรงจาก source ไม่ได้เดาจากการที่ไม่เจอ **ไม่พบ credential หรือ key เข้ารหัสที่ฝังไว้แบบ hardcode ที่ใดเลยในเส้นทางเข้ารหัสของโมดูลนี้เอง** — ต่างจากโมดูลพี่น้องในกลุ่ม sidebar เดียวกันอย่างชัดเจน คือ [Backstage Migrations](/th/backstage/backstage-migrations) §3.1 ที่ deploy-token check ของมัน**มี** ค่า default เป็น string ว่าง

## 3. แนวคิดสำคัญ

- **Pool (แถว `tb_database_pool`)**: การลงทะเบียนเซิร์ฟเวอร์ Postgres จริงหนึ่งเครื่อง — `host`/`port`/`database`/`username`/`password` — บวก `name` ที่ผู้ดูแลตั้งเอง, `description` ที่เป็นทางเลือก, `note` ที่เป็นทางเลือก และ `is_active` ดูตารางฟิลด์เต็มที่ [Data Model](/th/backstage/database-pools/data-model) §2
- **แสดงเป็น DSN ไม่ใช่ห้าคอลัมน์**: หน้ารายการและหน้าอ่านของหน้าแก้ไขไม่เคยแสดง host/port/database/username แยกกันเป็นฟิลด์ — ประกอบเป็นสตริงเดียว `username@host:port/database` (`poolDsn()`, `../carmen-backstage/src/utils/databasePool.ts`) เพราะสี่ค่านั้นคือที่อยู่เดียว ไม่ใช่สี่ข้อเท็จจริงที่แยกกัน ปุ่ม**คัดลอก**ต่อแถวคัดลอกสตริงนี้เป๊ะ ๆ ไปวางต่อใน `psql` หรือเครื่องมือเชื่อมต่อได้ทันที
- **`name` กับ DSN**: ชื่อของ pool จะแสดงก็ต่อเมื่อมันบอกอะไรที่ DSN ยังไม่ได้บอก `isDerivedName()` (ไฟล์เดียวกัน) ซ่อนบรรทัดชื่อทุกครั้งที่มัน (ไม่สนตัวพิมพ์) เหมือนกับ DSN หรือกับ `host:port/database` ทุกตัวเป๊ะ — ซึ่งเป็นกรณีของทุก pool ที่สคริปต์ backfill เดิมสร้างขึ้นอัตโนมัติ เพราะถูกตั้งชื่อตาม connection string ของตัวเอง
- **`note` แยกจาก `description`**: ทั้งสองเป็นคอลัมน์ Prisma แบบ free-text (`tb_database_pool.description`, `tb_database_pool.note` — `schema.prisma:1718`, `:1729`) `description` เป็นฟิลด์ปกติที่ผู้ดูแลกรอกเอง ส่วน `note` คือจุดที่สคริปต์ backfill เดิมเขียนข้อความคงที่ลงไป — ค่าตายตัว `'สร้างอัตโนมัติจาก tb_business_unit.db_connection'` — บนทุก pool ที่มันสร้างจาก connection blob เดิมของ BU เพื่อให้คนอ่านภายหลังรู้ว่าแถวนั้นไม่ได้ถูกตั้งค่าด้วยมือ UI แสดง `note` บนหน้าอ่านทุกครั้งที่มีค่า โดยตั้งใจไม่ซ่อนไว้ท้ายสุดของบันทึก
- **วงจรของรหัสผ่าน**: การสร้างใหม่ต้องมีรหัสผ่านแบบ plaintext (ถ้าว่างเปล่าจะเป็น validation error) การอัปเดตปล่อยว่างได้เพื่อคงค่าเดิมไว้ หรือส่งค่า plaintext ใหม่เพื่อหมุนรหัสผ่าน API ไม่เคยคืนค่าจริงกลับมาเลย — ทุก response มาสก์เป็น `••••••` เสมอ และตัวประกอบ payload ของการอัปเดตปฏิบัติกับสตริงมาสก์นั้นเหมือนกับ "ไม่ได้ส่งมา" ทำให้ read-then-write ที่ฟิลด์อื่นทุกตัวบนฟอร์มนี้ทำอยู่ ไม่มีทางส่งค่ามาสก์กลับไปเป็นรหัสผ่านใหม่โดยไม่ตั้งใจ
- **`is_active`**: pool ที่ปิดอยู่ยังคงเลือกได้บน business unit ที่ผูกกับมันอยู่แล้ว (dropdown ที่แท็บ Technical ของ [Business Units](/th/backstage/business-units/ui-screens) จึงไม่ทิ้งค่าที่ผูกไว้แล้วอย่างเงียบ ๆ) แต่จะถูกตัดออกจาก option list เมื่อกำลังผูก business unit **ใหม่**
- **ป้องกันการลบขณะถูกใช้งาน**: การลบ pool จะตรวจก่อนว่ามี business unit ที่ยังไม่ถูกลบตัวใดชี้ `database_pool_id` มาที่มันหรือไม่ ถ้ามีจะปฏิเสธการลบ (409, `DATABASE_POOL_IN_USE`) พร้อมระบุ business unit ที่บล็อกอยู่สูงสุด 10 ตัวด้วย `code` ตรง ๆ ใน toast — จงใจไม่ผ่าน error redactor ทั่วไปที่จะยุบข้อความเหลือแค่ "Please try again later." ตอน production
- **`doc_version` จำเป็นบนทุกการอัปเดต ไม่มีเงื่อนไข**: ต่างจาก entity อื่นบางตัวในโค้ดชุดนี้ที่ token ของ optimistic lock จะถูกส่งก็ต่อเมื่อมีค่าอยู่แล้ว `DatabasePoolUpdateDto` บังคับทุก `PUT` ต้องส่งค่านี้มา — backend ปฏิเสธการอัปเดตที่ไม่ส่งมา (`COMMON_DOC_VERSION_REQUIRED`) แทนที่จะตีความ token ที่หายไปว่า "ไม่ต้องเช็ค conflict"
- **Permission ระดับ route คือ `database_pool.read` บนทั้งสามเส้นทาง** — รวมถึง `/new` และ `/:id/edit` permission ที่แคบกว่าคือ `database_pool.manage` ถูกบังคับใช้แค่ภายในหน้าจอเท่านั้น (ดู §4) ไม่ใช่ที่ route guard

## 4. บทบาทและสิทธิ์

| จุด | Gate | Key |
|---|---|---|
| route `/backstage/database-pools`, `/backstage/database-pools/new`, `/backstage/database-pools/:id/edit` | `PrivateRoute requiredPermission` + `feature` | `database_pool.read` + `database_pools` (`App.tsx:553-576` — **permission เดียวกันบนทั้งสามเส้นทาง** ไม่มีการเช็ค `.manage` ที่ระดับ route เลย) |
| รายการ sidebar "Database Pools" | filter ด้วย `permission` + `feature` | `database_pool.read` / `database_pools` (`backstageNav.ts:63`) |
| หน้ารายการ: ปุ่ม Add Pool (ทั้ง header และ empty state) | `<Can>` | `database_pool.manage` |
| หน้ารายการ: เมนู action Edit/Delete ต่อแถว | `<Can>` ครอบทั้ง `DropdownMenu` | `database_pool.manage` |
| หน้าแก้ไข (pool ที่มีอยู่): ปุ่ม "Edit" ที่สลับเข้าโหมดแก้ไข | `<Can>` | `database_pool.manage` |
| หน้าแก้ไข (pool ที่มีอยู่): ปุ่ม Save บนแถบยังไม่บันทึก | `<Can>` | `database_pool.manage` |
| หน้าแก้ไข: การเช็ค permission ของ `handleSubmit` เอง แยกจากปุ่ม Save | `hasPermission('database_pool.manage')` คืนค่าออกทันทีถ้าเป็นเท็จ | `database_pool.manage` |
| Backend: `GET` (list/one) | `AppIdGuard('database-pool.list'\|'.get')` + `BackstagePermissionGuard` | `database_pool.read` |
| Backend: `POST`/`PUT`/`DELETE` | `AppIdGuard('database-pool.create'\|'.update'\|'.delete')` + `BackstagePermissionGuard` | `database_pool.manage` |

มีสองเรื่องที่ควรพูดให้ชัดเจน ยืนยันจากการอ่านโค้ดตรง ๆ ไม่ใช่เดาจากชื่อ permission:

1. **session ที่มีแค่ `database_pool.read` เปิดฟอร์ม *สร้างใหม่* ได้** เพราะ route guard ของ `/backstage/database-pools/new` เช็คแค่ `database_pool.read` (`App.tsx:564`) และ `DatabasePoolEdit.tsx` เริ่ม pool ใหม่ในโหมดแก้ไขโดยไม่มีเงื่อนไข (`editing = isNew` ไม่ถูก gate ด้วย permission ใดเลย) session แบบนี้จึงเห็นและพิมพ์ทุกฟิลด์ของฟอร์มสร้างใหม่ได้ แต่ไม่สามารถ submit ผ่านทางไหนได้เลย: ปุ่ม Save เองจะ render ก็ต่อเมื่ออยู่ใน `<Can permission="database_pool.manage">` เท่านั้น และ `handleSubmit` เช็ค `hasPermission('database_pool.manage')` เองอีกชั้นแล้วคืนค่าก่อนจะตรวจสอบหรือเรียก API เลย — เป็นรูปแบบ defense-in-depth เดียวกับ `handleSave` ของ `BusinessUnitEdit.tsx` ที่ป้องกัน `Ctrl/Cmd+S` และ Enter-ในช่องกรอกไม่ให้ข้ามปุ่มที่ซ่อนอยู่ไปได้ route แก้ไข pool ที่มีอยู่แล้วไม่มีช่องโหว่แบบเดียวกันนี้: `editing` เริ่มที่ `false` และเปลี่ยนเป็น `true` ได้ผ่านปุ่ม "Edit" ที่ gate ด้วย `<Can>` เท่านั้น ดังนั้น session ที่มีแค่สิทธิ์อ่านจะเห็นแค่หน้าบันทึกอย่างเดียว
2. **backend ไม่มีช่องว่างแบบเดียวกัน** ทุกหนึ่งใน 5 operation ของ REST (list, get, create, update, delete) ซ้อนทั้ง `AppIdGuard` (การเช็ค allowlist ของ header `x-app-id` เทียบกับสตริงต่อ operation เช่น `database-pool.update` — `../carmen-turborepo-backend/apps/backend-gateway/src/common/guard/app-id.guard.ts`) และ `BackstagePermissionGuard` + `RequireBackstagePermission` สำหรับ key RBAC ต่างจาก [Business Units](/th/backstage/business-units) §4 ที่ endpoint `PUT` ของมันถูก gate ด้วย `AppIdGuard` เพียงอย่างเดียว ไม่มี RBAC check ซ้อนอยู่ด้วย — ช่องว่างแบบนั้นไม่มีอยู่ในโมดูลนี้

Controller ฝั่ง gateway (`BackstageDatabasePoolsController`, `apps/backend-gateway/src/backstage/backstage_database-pools/backstage_database-pools.controller.ts`) ไม่ทำงานฐานข้อมูลเองเลย — มันส่งต่อทุก call ผ่าน RPC (`RpcClient` / message pattern `DatabasePools` ของ `@repo/rpc-contract`) ไปยัง `DatabasePoolController` → `DatabasePoolService` ของ `micro-cluster` (`apps/micro-cluster/src/cluster/database-pool/`) ซึ่งเป็นจุดที่การอ่าน/เขียน Prisma, การเข้ารหัสรหัสผ่าน และการเช็คว่า pool กำลังถูกใช้งานอยู่หรือไม่เกิดขึ้นจริง

## 5. โมดูลที่เกี่ยวข้อง

- [Business Units](/th/backstage/business-units) — business unit ทุกตัวที่กำลังชี้มาที่ pool หนึ่งผ่าน `database_pool_id` คือความสัมพันธ์ `tb_business_unit[]` ของ pool นั้น หน้าแก้ไข BU แท็บ Technical เป็นหน้าจอเดียวนอกโมดูลนี้ที่อ่านชื่อของ pool (ไม่เคยอ่าน credential) และเป็นหน้าจอที่ตั้งค่า `db_schema` — อีกครึ่งหนึ่งของ connection ของ tenant ที่ resolve แล้ว
- [Tenant Migrations](/th/backstage/tenant-migrations) — โมดูลที่ `resolveConnection()`/`resolveConnectionForBusinessUnit()` ของมัน dereference `database_pool_id` ของ BU เป็น Postgres connection string จริงเพื่อรัน `prisma migrate` ต่อกับมัน pool ที่ถูกปิดหรือ soft-delete เป็นหนึ่งในเหตุผลที่บันทึกไว้ว่าการ resolve นี้ล้มเหลว
- [Backstage Migrations](/th/backstage/backstage-migrations) (`/backstage/migrations`) — ใช้กลุ่ม sidebar `navGroup.database` ร่วมกับโมดูลนี้ แต่ย้าย migration ของฐานข้อมูลแพลตฟอร์มเอง ไม่ใช่ของ tenant — คนละเส้นทางข้อมูลกัน
- [Backstage Roles](/th/backstage/rbac) — โมเดล permission เบื้องหลัง `database_pool.read`/`database_pool.manage` รวมถึงวิธีที่ session ที่ไม่มี `.manage` ยังเปิด (แต่ submit ไม่ได้) ฟอร์มสร้างใหม่ได้ ตาม §4

## 6. แหล่งอ้างอิง

- `../carmen-backstage/src/App.tsx:553-576` — สามเส้นทาง ทั้งหมด gate ด้วย `database_pool.read` อย่างเดียว
- `../carmen-backstage/src/components/nav/backstageNav.ts:63` — รายการ sidebar (`permission: 'database_pool.read'`, `groupKey: 'navGroup.database'`, `feature: 'database_pools'`)
- `../carmen-backstage/src/pages/DatabasePoolManagement.tsx` — หน้ารายการ อ่านครบ (468 บรรทัด)
- `../carmen-backstage/src/pages/DatabasePoolEdit.tsx` — หน้าสร้าง/แก้ไข อ่านครบ (672 บรรทัด)
- `../carmen-backstage/src/services/databasePoolService.ts` — REST client, comment เรื่องการมาสก์รหัสผ่าน
- `../carmen-backstage/src/utils/databasePool.ts` — `poolDsn()`, `isDerivedName()`
- `../carmen-backstage/src/components/Can.tsx` — helper render ตาม permission ที่อ้างถึงทั่ว §4
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage_database-pools/{backstage_database-pools.controller.ts,backstage_database-pools.service.ts,swagger/request.ts,swagger/response.ts}` — REST surface ฝั่ง gateway และ RPC proxy
- `../carmen-turborepo-backend/apps/backend-gateway/src/common/guard/app-id.guard.ts` — guard allowlist ของ `x-app-id` ที่ซ้อนอยู่บนทุก route
- `../carmen-turborepo-backend/apps/micro-cluster/src/cluster/database-pool/{database-pool.controller.ts,database-pool.service.ts}` — implementation CRUD จริง อ่านครบ
- `../carmen-turborepo-backend/packages/error-catalog/src/catalog.ts:3562-3581` — `DATABASE_POOL_NOT_FOUND`/`DATABASE_POOL_NAME_EXISTS`/`DATABASE_POOL_IN_USE`
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma:1713-1742` — `model tb_database_pool`
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/migrate.database-pool.ts` — สคริปต์ backfill `db_connection` → pool ครั้งเดียว อ่านครบ
- `../carmen-turborepo-backend/packages/secret-crypto/src/crypto.util.ts` — `encryptSecret`/`decryptSecret`, `SECRET_ENCRYPTION_KEY` (fail-closed ไม่มีค่า default)
- `../carmen-turborepo-backend/packages/db-connection-utils/src/tenant-url.ts` — `buildTenantUrl`/`resolveTenantUrl`
- ยืนยันกับ `carmen-backstage` HEAD `8405788f` และ `carmen-turborepo-backend` HEAD `c9d788829` (ทั้งสอง origin/main, 2026-10-27)
- `../carmen-backstage-e2e/tests/database-pools/database-pools-smoke.spec.ts` (HEAD `9584887`) — e2e เดียวที่ครอบคลุม: smoke test แบบอ่านอย่างเดียวสองตัว ใช้ path `/platform/database-pools` ที่ล้าสมัยแล้ว

## 7. หน้าในโมดูลนี้

- [Data Model](/th/backstage/database-pools/data-model) — ตารางฟิลด์เต็มของ `tb_database_pool`, วงจรการเข้ารหัส/มาสก์, ประวัติการย้ายจาก `db_connection` และการยืนยันตรงกับสิ่งที่ [Business Units](/th/backstage/business-units/data-model) §2.4 และ [Tenant Migrations](/th/backstage/tenant-migrations/data-model) §3 พูดถึงตารางนี้ไว้แล้ว
- [UI Screens](/th/backstage/database-pools/ui-screens) — พาชม `DatabasePoolManagement` (รายการ, ตัวกรอง, export CSV, คัดลอก DSN) และ `DatabasePoolEdit` (ฟอร์มสร้างใหม่, หน้าอ่านแบบบันทึก, โหมดแก้ไข, dialog) รวมถึงปฏิสัมพันธ์ระหว่าง permission อ่าน/ฟอร์มสร้างใหม่ที่บันทึกไว้ใน §4 ข้างต้น
