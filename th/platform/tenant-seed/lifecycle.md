---
title: Tenant Seed — Lifecycle
description: การตรวจสถานะ seed และการรัน seed แบบ stream ทำงานตั้งแต่ต้นจนจบอย่างไร — การ resolve connection, การตรวจ row ที่ขาดราย set, โปรโตคอล event NDJSON, สรุป done และพฤติกรรมการยกเลิก
published: true
date: '2026-10-27T15:00:00.000Z'
tags: book/platform, tenant-seed, lifecycle
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Tenant Seed — Lifecycle

> **At a Glance**
> **Operation:** ตรวจสถานะ · seed stream ของ BU เดียว · fleet seed (SPA วน loop) &nbsp;·&nbsp; **ไม่มีในโมดูลนี้:** ลบหรือรีเซ็ตข้อมูล seed, อัปเดต row ที่มีอยู่, การตั้งเวลา, endpoint "ทุก BU" ฝั่ง server &nbsp;·&nbsp; **Endpoint:** `GET .../:bu_id/status`, `POST .../:bu_id/deploy/stream` ใต้ `api-system/tenant/seeds` &nbsp;·&nbsp; **ผลข้ามเอนทิตี:** เขียนลงฐานข้อมูล tenant ของ BU เท่านั้น

## 1. ภาพรวม

ทั้งสอง operation ผ่านเส้นทางเดียวกัน: SPA, gateway (`TenantSeedsController` ป้องกันด้วย `TenantMigrationGuard`), RPC ไป micro-business (`TenantSeedService`) แล้วเชื่อมต่อ Prisma ตรงไปยังฐานข้อมูล tenant ไม่มีการเขียนลงฐานข้อมูล backstage; audit trail คือบรรทัด log แบบมีโครงสร้าง `tenant-seed.audit`

## 2. การ resolve connection ของ tenant

`resolveConnection(bu_id)` (micro-business):

1. `bu_id` ต้องตรงกับรูปแบบ UUID ไม่งั้น `INVALID_ARGUMENT` ("Invalid bu_id format", HTTP 400)
2. โหลด `tb_business_unit` ที่ยังไม่ถูกลบ (`deleted_at: null`) พร้อม `db_schema` และ database pool (host, port, database, credentials, `is_active`) ไม่พบ: `NOT_FOUND` (404)
3. `tenantService.resolveConnectionForBusinessUnit` สร้าง connection URL ความล้มเหลว (ไม่มี pool, ไม่มี schema, provider ที่ไม่รองรับ) กลายเป็น `VALIDATION_FAILURE` (422, "no database connection configured")
4. สร้าง Prisma client อายุสั้นพร้อม adapter `pg` สำหรับ URL และ `schema` นั้น และ**ตัดการเชื่อมต่อใน `finally`** เมื่อ operation จบ

## 3. การตรวจสถานะ

`GET /api-system/tenant/seeds/:bu_id/status` (`tenant_seed.read`) สำหรับแต่ละ seed set ตามลำดับใน registry `listMissing(tenant)` คืน natural key ที่ไม่มีอยู่ Response:

```
{ bu_id, bu_code,
  sets: [ { key, label, defined, present, missing: [keys...] } ... ],
  all_seeded: every set has missing = [] }
present = defined - missing.length
```

เป็นการอ่านอย่างเดียวและรันแต่ละ set ตามลำดับบน connection เดียว SPA เก็บผลลัพธ์ไว้บน row และหา Seeded หรือ "N missing" จาก `sum(missing.length)`

## 4. Seed stream

`POST /api-system/tenant/seeds/:bu_id/deploy/stream` (`tenant_seed.apply`) body ที่เลือกใส่ได้ `{ "keys": ["running-code", ...] }` ถ้าไม่ใส่ `keys` (หรือเป็น array ว่าง) จะเลือกทุก set; SPA ส่ง key ที่ผู้ปฏิบัติงานติ๊กเสมอ และเฉพาะ set ที่มีอะไรขาด response เป็น `application/x-ndjson` (header `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`) หนึ่ง JSON object ต่อบรรทัด:

| `type` | ฟิลด์ | ส่งเมื่อ |
|---|---|---|
| `start` | `bu_id, bu_code, total` | หลังคำนวณรายการงาน: `total` = key ที่ขาดรวมทุก set ที่เลือก |
| `seeding` | `bu_id, bu_code, key` (set key), `row_type` (row key), `index`, `total` | หลังสร้าง**แต่ละ** row (`index` จึงนับ row ที่เสร็จแล้ว) |
| `done` | `success, summary { bu_id, bu_code, created, skipped }` | จบการรันที่สำเร็จ; `skipped` = row ที่นิยามไว้ของ set ที่เลือก ลบ `created` |
| `error` | `message` | ความล้มเหลวหลังสตรีมเริ่มไปแล้ว |

อัลกอริทึม (`deployStream`):

```
conn = resolveConnection(bu_id)                 # failure -> observable error (pre-stream)
work = []
for set in selected sets (registry order):
    for key in set.listMissing(tenant): work.push(set, key)
emit start{total = work.length}
for i, (set, key) in work:
    if cancelled: return
    await set.createOne(tenant, key)            # one write per row
    emit seeding{key = set.key, row_type = key, index = i+1, total}
emit done{created = work.length, skipped = definedTotal - created}
```

หมายเหตุ:

- รายการที่ขาด**ถูกคำนวณใหม่ตอน stream** ไม่ได้นำจากการเรียก status ก่อนหน้า ดังนั้น row ที่คนอื่นสร้างไว้ระหว่างนั้นจะไม่อยู่ในรายการงาน
- ไม่เป็น transaction: `createOne` แต่ละครั้งคือการเขียนของมันเอง ถ้าล้มเหลวที่ row 7 จะเหลือ row 1-6 ที่สร้างไว้แล้ว การตรวจสถานะครั้งถัดไปแสดงสิ่งที่เหลือ
- `createOne` ของ `email-templates` เป็น read-modify-write ของ row JSON หนึ่งแถว; ของ `notification-templates-legacy` แต่ละ "key" คือ action ที่เขียน workflow data ใหม่หรือ retire legacy template ที่ยังไม่ถูกแตะ (ป้องกันด้วย `doc_version: 0` และ `updated_by_id: null` เพื่อไม่ให้แตะ template ที่ถูกแก้แล้ว)

### 4.1 การจัดการ error ที่ gateway

| ช่วงเวลา | ผลลัพธ์ |
|---|---|
| Error ก่อน event แรก (connection, ไม่พบ, id ผิด) | JSON body `{ message, status, success: false }` โดย status: 404 ถ้าข้อความตรงกับ "not found"; 422 สำหรับ "no database connection configured" หรือ "unsupported database provider"; 400 สำหรับ "invalid bu_id format"; นอกนั้น 500 |
| Error หลังเริ่มสตรีมแล้ว | อีกหนึ่งบรรทัด `{ "type": "error", "message": ... }` แล้ว response จบ |
| Client ตัดการเชื่อมต่อ | `res.on('close')` unsubscribe จาก RPC stream คอมเมนต์ในโค้ดอธิบายว่าทำไมต้องไม่ใช้ `req.on('close')`: ตั้งแต่ Node 16 request ส่ง `close` เมื่ออ่าน body เสร็จ ซึ่งทำให้สตรีมถูกตัดสั้น |

### 4.2 SPA ใช้งานอย่างไร

`deployStream` ใน `tenantSeedService.ts` ใช้ `fetch` (ไม่ใช่ `EventSource`) เพื่อส่ง bearer token และ `x-app-id` ได้ มันแยก body ตามบรรทัดใหม่ parse ทีละบรรทัด ส่ง `start`/`seeding` ไปยังความคืบหน้าของ row, throw เมื่อเจอ event `error` และ resolve ด้วยสรุป `done`; สตรีมที่ว่างเปล่าจบด้วย "Seed stream ended without a result" หลังรันสำเร็จ หน้าแสดง toast "Created N rows in CODE." (หรือ "CODE was already fully seeded." เมื่อ `created = 0`) และตรวจ BU นั้นใหม่

## 5. Fleet seed

ไม่มีแนวคิดนี้ฝั่ง server `seedAll(selectedKeys)` สร้างแผนจาก row ที่ถูกทำเครื่องหมาย Missing อยู่ (`pickMissing` นำ set ที่ขาดของแต่ละ BU มาตัดกับ key ที่เลือก ข้าม BU ที่ไม่เหลืออะไร) แล้วรัน stream ของ BU เดียว**ตามลำดับ** BU ที่ล้มเหลวจะถูกนับและ loop ดำเนินต่อ; toast สุดท้ายคือ "Seeded N business units." หรือ "Seeded N - M failed." การ unmount ตั้ง flag cancelled ที่ยกเลิก fetch ที่ยังทำอยู่และกันไม่ให้เริ่ม BU ถัดไป

## 6. การยกเลิก พูดกันตรง ๆ

การ abort ในเบราว์เซอร์แค่หยุดให้ SPA ฟัง gateway จึง unsubscribe ซึ่งตั้ง flag `cancelled` ใน micro-business และถูกตรวจ**ระหว่าง row** ยังไม่ได้ตรวจสอบใน source ว่า unsubscribe ส่งต่อผ่าน RPC transport ไปถึง flag นั้นหรือไม่ (SPA service บอกไว้ในคอมเมนต์ของตัวเอง) ให้ถือว่าการรันที่ถูกยกเลิกอาจเสร็จไปแล้ว; ตรวจสถานะซ้ำก่อนรันอีกครั้ง

## 7. แหล่งอ้างอิง

- Gateway: `apps/backend-gateway/src/backstage/tenant-seeds/{tenant-seeds.controller.ts,tenant-seeds.service.ts}`, `src/auth/guards/tenant-migration.guard.ts`
- Micro-business: `apps/micro-business/src/authen/tenant_seed/{tenant_seed.service.ts,progress-event.ts}`, `seed-sets/*.seed-set.ts`
- SPA: `src/services/tenantSeedService.ts`, `src/pages/TenantSeedManagement.tsx`
- หน้าข้างเคียง: [Tenant Seed](/th/platform/tenant-seed), [UI Screens](/th/platform/tenant-seed/ui-screens); ที่เกี่ยวข้อง: [Tenant Migrations](/th/platform/tenant-migrations)
