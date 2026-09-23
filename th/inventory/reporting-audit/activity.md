---
title: บันทึกกิจกรรม (Activity)
description: บันทึก activity ระดับ tenant — ทุกการเปลี่ยนสถานะเป็นหนึ่งแถวพร้อม actor, entity, snapshot ก่อน/หลัง, IP และ user agent; อ่านผ่าน /system-admin/activity-log และตั้งแต่ 2026-08 ผ่าน Activity sheet ต่อระเบียนบนทุกหน้ารายการและหน้า detail
published: true
date: '2026-09-23T01:30:00.000Z'
tags: reporting-audit, activity, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# บันทึกกิจกรรม (Activity)

> **At a Glance**
> **เจ้าของ:** Append-only (audit service) &nbsp;·&nbsp; **ตาราง:** `tb_activity` (tenant) &nbsp;·&nbsp; **ใช้โดย:** chain audit ของทุกโมดูลธุรกรรม &nbsp;·&nbsp; **surface สำหรับอ่าน:** `/system-admin/activity-log` (รายการทั่วแพลตฟอร์ม) **และ** **Activity sheet** ต่อระเบียน (`components/share/activity-sheet.tsx`) ที่เข้าถึงได้จาก row menu ของ 27 รายการและ header ของ 15 หน้า detail &nbsp;·&nbsp; **ไม่ใช่ตารางนี้:** telemetry การคลิก/page-view ของ UI (`tb_activity_event`) — ดู §9

![บันทึกกิจกรรม (Activity) screen](/screenshots/reporting-audit/activity.png)

## สถานะการทำงานจริง (ตรวจสอบซ้ำเมื่อ 2026-09-22)

การแก้ไขสามข้อจากหน้านี้ฉบับ 2026-07-22:

1. **ตอนนี้มี Activity drawer ต่อเอกสารแล้ว** commit ของ frontend `cc37c779` (2026-08-04, รายการ "Activity" ใน row menu ของ `DataGrid` เปิดใช้กับ 27 รายการ) และ `21dc1792` (2026-08-04, ปุ่ม Activity บน header ของ 15 หน้า detail) เพิ่ม `components/share/activity-sheet.tsx` ซึ่งเปิดได้จากทุกที่ผ่าน `openActivity(id, label)` ใน `activity-sheet-host.tsx` (host แบบ `CustomEvent` ที่ mount ครั้งเดียวใน `routes/root-layout.tsx`; มี 16 จุดเรียกที่ HEAD) มันอ่านสอง endpoint ที่หน้าฉบับก่อนไม่ได้ระบุ: `GET /api/{bu}/activity-logs/record/{entity_id}` (timeline เรียงเก่าสุดก่อน, `entity_type` ไม่บังคับ) และ `GET /api/{bu}/activity-logs/{id}/detail` (หนึ่งแถวพร้อม diff `changes` ที่คำนวณให้) รายการ recipe และ equipment **ไม่อยู่** ใน activity registry โดยตั้งใจ (ไม่มี Activity ใน row menu ที่นั่น)
2. **`enum_activity_action` มี 25 ค่า ไม่ใช่ 20/21** `comment`, `submit`, `review` (tenant migration `20260727120000_add_activity_action_comment_submit_review`) และ `email_sent` (`20260908120000_add_email_sent_activity_action`) ถูกเพิ่มต่อท้าย; filter action ของ `/system-admin/activity-log` ตอนนี้มีให้ **ครบ 25** ค่าพร้อมไอคอน (`c07d6805`) ไม่ใช่ 5 ค่าที่คัดสรร
3. **การ redact เป็นรูปธรรม** ค่าใน snapshot ภายใต้ key `password`, `hash`, `token`, `secret`, `api_key`, `url_token`, `pricelist_url_token` ถูก mask ก่อนเขียนแถว (`packages/prisma-shared-schema-tenant/src/client.ts` `sensitiveFields`; สอง key ของ RFP magic-link ถูกเพิ่มเมื่อ 2026-09-12, `14c3f1daf` เพราะ `loadEntitySnapshot` คัดลอกทั้งแถวและ matcher จับคู่ key แบบตรงตัว)

## 1. ภาพรวมและผู้ใช้งาน

ตาราง activity คือ **audit log ของ tenant** — หนึ่งแถวต่อหนึ่งการเปลี่ยนสถานะที่มีความหมาย เก็บข้อมูล *ใครทำอะไรกับแถวไหน* โดยไม่ผูกผู้เขียนกับผู้บริโภค ทุกโมดูลธุรกรรม append ผ่าน audit service เดียว ผู้บริโภคอ่านโดย `entity_type` + `entity_id` เสริมคอลัมน์ audit ระดับแถว (`created_by_id` ฯลฯ) ด้วย chain ของ event แบบเต็มพร้อม snapshot เก่า/ใหม่และ context ของ request

ตารางออกแบบให้เป็น generic และ write-heavy โดยตั้งใจ `entity_type` เป็น discriminator ที่เป็น string แบบอิสระ; `entity_id` คือ UUID ของเป้าหมาย; enum `action` ครอบคลุมคำกริยา lifecycle

**ดูแลโดย** audit service (เขียนอย่างเดียว) **อ่านโดย** สอง surface: รายการทั่วแพลตฟอร์มที่ `/system-admin/activity-log` (`useActivityLog`, `hooks/use-activity-log.ts`) และ **Activity sheet** ต่อระเบียน (§1.1)

### 1.1 Activity sheet ต่อระเบียน

`ActivitySheet` แสดงประวัติของหนึ่งระเบียนเป็น timeline (ใหม่สุดก่อนใน UI; API คืนเก่าสุดก่อน) แตะแถวเพื่อขยายและโหลด `GET .../activity-logs/{id}/detail` ซึ่ง object `changes` ถูกคำนวณฝั่งเซิร์ฟเวอร์โดย `buildActivityDiff(old_data, new_data)` (`packages/log-events-library/src/activity/activity-diff.ts`):

```
changes: {
  fields:   [{ field, old, new }],                      -- คอลัมน์ header ที่ต่างกัน
  children: [{ relation, added[], removed[], updated: [{ id, fields[] }] }],
  has_changes: boolean                                  -- ไม่นับ updated_at / updated_by_id / doc_version
}
```

การสร้างไม่มี `old_data` และการลบไม่มี `new_data` ดังนั้นทุกฟิลด์ของ snapshot เดียวที่มีอยู่จะถูกรายงานเป็นการเปลี่ยนแปลง sheet ต้องการเพียง entity id (UUID ไม่ชนกันข้ามตาราง); หัวข้อของตารางลูก derive จาก `entity_type` ที่คืนมากับแต่ละแถว component timeline ตัวเดียวกันถูกใช้ซ้ำสำหรับ workflow history เพื่อให้ทั้งสอง sheet อ่านเหมือนกันบนหน้าเอกสาร

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดูรายการ activity log | `/system-admin/activity-log` | มุมมองรายการหรือ grid; filter สำหรับ **action**, **entity type** และ **ผู้ใช้** (actor) บวกค้นหาแบบข้อความอิสระ; saved view และเมนู filter แบบ popover สไตล์ Linear (2026-08) |
| ดูประวัติของเอกสารหนึ่งฉบับ | row menu ของรายการใดก็ได้ → **Activity** หรือปุ่ม **Activity** บน header ของหน้า detail | เปิด `ActivitySheet` สำหรับ `entity_id` นั้น; ขยายแถวเพื่อดู diff ของฟิลด์/บรรทัดลูก ไม่มีบนรายการ recipe/equipment |
| กรองตาม action | Select Action | ครบทั้ง 25 ค่าของ `enum_activity_action` เรียงตาม `schema.prisma` |
| กรองตามประเภท entity | Select Entity Type | รายการคัดสรร 13 ค่า (`purchase_request`, `purchase_order`, `good_received_note`, `credit_note`, `store_requisition`, `inventory_transaction`, `product`, `vendor`, `location`, `department`, `currency`, `period`, `auth`) — `entity_type` เองเป็น free-form ดังนั้นค่าอื่นอาจมีอยู่ในข้อมูลโดยไม่มีตัวเลือกที่ตรงกัน |
| Export มุมมองที่กรองปัจจุบัน | ปุ่ม **Export** | export XLSX แบบ client-side (`useExportActivityLog`) ใช้ query params เดียวกับรายการ |
| Print | ปุ่ม **Print** | Print หน้าปัจจุบันของ browser |
| ตรวจดูหนึ่งแถว | คลิกแถว | เปิด `ActivityLogDetailSheet` — render `old_data`/`new_data` JSONB |
| ลบแถว | **ไม่มีใน UI** | gateway เปิด `DELETE …/activity-logs/{id}` (soft), `DELETE …/batch/soft`, `DELETE …/{id}/hard`, `DELETE …/batch/hard` (AppIdGuard `activityLog.delete|deleteMany|hardDelete|hardDeleteMany`) และ frontend ประกาศ `system_admin.activity_log.delete` แต่ `activity-log-component.tsx` ไม่ render action ลบเลย — ยังไม่ยืนยันว่ามีอะไรเรียก route เหล่านี้ |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| ไม่มีแถว activity สำหรับการเปลี่ยนที่ทราบ | service-layer interceptor ถูกข้าม | ยืนยันว่าการเปลี่ยนเดินผ่าน audit service ไม่ใช่ raw SQL |
| `actor_id IS NULL` | actor ของระบบ (background job) — เป็นไปตามคาด | ไม่ต้องแก้; ถือเป็น action ของระบบ |
| `old_data` ว่างเปล่าบน update | snapshotter รันหลังการเขียน | บั๊ก — snapshotter ต้องจับ state ก่อน |
| Activity sheet แสดง "no changes" สำหรับ update | `has_changes = false` — มีแค่ฟิลด์ housekeeping (`updated_at`, `updated_by_id`, `doc_version`) ที่เปลี่ยน | เป็นไปตามคาด; ไม่มีอะไรที่ผู้ใช้มองเห็นเปลี่ยน |
| Snapshot แสดง `***` / ค่าที่ถูก mask | key ตรงกับ `sensitiveFields` (`password`, `hash`, `token`, `secret`, `api_key`, `url_token`, `pricelist_url_token`) | เป็นไปตามคาด — ไม่เคยเก็บแบบ clear text |
| Audit log ช้า | scan ช่วงวันที่บน `created_at` | ใช้ query แบบ scope ตาม entity เมื่อทำได้ (`/record/{entity_id}`); หรือ partition |

## 4. กรณีพิเศษ

- **Append-only จากโค้ดแอปพลิเคชัน** ผู้เขียนไม่อัปเดตแถวเลย — `updated_*` มีไว้เพื่อความสมมาตรเท่านั้น endpoint soft/hard delete มีอยู่บน gateway (ดู §2) สำหรับการล้างตาม retention; ไม่มี UI path เรียกใช้
- **ไม่มีการบังคับ FK บน `entity_id`** เป็น polymorphic ข้ามหลายตาราง; แถวค้างเป็นความตั้งใจ (ยังมีค่าสำหรับ audit ของ entity ที่ถูกลบ)
- **Actor ข้าม schema** `actor_id` อ้างอิง `tb_user.id` ของแพลตฟอร์มโดยไม่มี relation ที่บังคับใช้ `NULL` = actor ของระบบ
- **`email_sent` ถูกเขียนแม้ตอนล้มเหลวด้วย** `purchase-order.service.ts` บันทึกแถว `email_sent` หนึ่งแถวต่อความพยายามส่งอีเมล PO หนึ่งครั้ง ไม่ว่าสำเร็จหรือล้มเหลว (`1897b4fc1`); การส่งอีเมล RFP ก็ทำเช่นเดียวกัน (`request-for-pricing.service.ts`)
- **Retention** ขับโดยนโยบายของ tenant; schema ไม่กำหนดเพดาน ไม่มี job ล้างตามเวลาสำหรับ `tb_activity` ใน `micro-cronjobs` (job `activity_retention` ของมันเล็งไปที่ `tb_activity_event` ซึ่งเป็นตาราง telemetry — §9)

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_activity`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `action` | `enum_activity_action?` | Yes | คำกริยา lifecycle |
| `entity_type` | `String?` | Yes | discriminator แบบอิสระ (เช่น `purchase_request`) |
| `entity_id` | `String? @db.Uuid` | Yes | UUID ของแถวเป้าหมาย |
| `actor_id` | `String? @db.Uuid` | Yes | ผู้ใช้ที่ดำเนินการ (ข้าม schema; ไม่ถูกบังคับ) |
| `meta_data` | `Json? @db.JsonB` | Yes | Default `{}` Context ของ request (route, session, correlation id) |
| `old_data` | `Json? @db.JsonB` | Yes | Default `{}` Snapshot ก่อน (key ที่ละเอียดอ่อนถูก mask) |
| `new_data` | `Json? @db.JsonB` | Yes | Snapshot หลัง (key ที่ละเอียดอ่อนถูก mask) |
| `ip_address` / `user_agent` / `description` | `String?` | Yes | metadata ของ request + สรุปแบบเลือกได้ |
| `doc_version` | `Int @db.Integer` | No | Default `0` เพิ่มเมื่อ 2026-06-12 ทั่ว 103 ตาราง tenant; ยังไม่ยืนยันว่าถูกอ่าน/เขียนสำหรับตาราง append-only นี้โดยเฉพาะ |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@index([entity_type, entity_id])` map `activity_entitytype_entityid_idx` — รองรับ "ประวัติของแถว X ในตาราง Y" และ timeline `/record/{entity_id}` `actor_id` ไม่มี relation DB (ข้าม schema)

**`enum_activity_action` (25):** `view`, `create`, `update`, `delete`, `login`, `logout`, `approve`, `reject`, `cancel`, `void`, `print`, `email`, `other`, `upload`, `download`, `export`, `import`, `copy`, `move`, `rename`, `save`, `comment`, `submit`, `review` (migration `20260727120000`), `email_sent` (migration `20260908120000`)

### 5.2 API surface (gateway `api/:bu_code/activity-logs`, `KeycloakGuard` + `x-app-id`)

| Verb และ path | AppId guard | คืนค่า |
|---|---|---|
| `GET /` (`?entity_type&entity_id&actor_id&action&start_date&end_date` + pagination/search/sort) | `activityLog.findAll` | แถวแบบ paginated พร้อมฟิลด์ชื่อ `actor_*` และ object `audit { created { at, id, name }, updated { at } }` — ไม่มี `created_at` ระดับบนสุด (`types/activity-log.ts` `getLogCreatedAt()`) |
| `GET /entity/:entity_type` | `activityLog.findAll` | แถวที่ `entity_type` มีค่านั้นอยู่ (ไม่สนตัวพิมพ์เล็ก/ใหญ่) |
| `GET /record/:entity_id` (`?entity_type` ไม่บังคับ) | `activityLog.findAll` | ทุกแถวของหนึ่งระเบียน **เก่าสุดก่อน** (timeline) Bruno: `documents-and-reports/activity-log/GET-find-by-entity-id-…bru` |
| `GET /:activity_log_id/detail` | `activityLog.findOne` | หนึ่งแถว + `changes` (§1.1) Bruno: `GET-find-one-detail-…bru` |
| `GET /:activity_log_id` | `activityLog.findOne` | หนึ่งแถว |
| `DELETE /:id`, `DELETE /batch/soft`, `DELETE /:id/hard`, `DELETE /batch/hard` | `activityLog.delete` / `deleteMany` / `hardDelete` / `hardDeleteMany` | ไม่พบผู้เรียกจาก frontend |

ระเบียนของ platform (cluster, business unit, user, report template) มี audit trail ของตัวเองใน `tb_activity` ของ **platform** ผ่าน `api-system/platform/activity-logs/record/:entity_id` และ `/:id/detail` (สิทธิ์ platform `activity_log.read` / `activity_log.detail`, `platform-activity-logs.controller.ts`, 2026-08-31) — บันทึกไว้ในเล่ม Platform ไม่ใช่ที่นี่

## 6. กติกาทางธุรกิจ

- **Append-only** ไม่มี update จากโค้ดแอป; endpoint ลบสงวนไว้สำหรับการล้างตาม retention
- **ความเที่ยงตรงของ snapshot** `old_data` / `new_data` carry JSON ของแถวเต็มในเวลาที่เปลี่ยน การ diff ทำตอนอ่าน (`buildActivityDiff`) key ที่ละเอียดอ่อนถูก mask ก่อน persist (`sensitiveFields`, จับคู่ key แบบตรงตัว — `token` ไม่ครอบคลุม `url_token` จึงต้องระบุทั้งสอง)
- **ไม่บังคับ FK บน `entity_id`** เป็น polymorphic; แถวค้างเป็นความตั้งใจ
- **Actor ข้าม schema** FK ไม่ถูกบังคับ; `NULL` = actor ของระบบ
- **ประสิทธิภาพ** การทำดัชนีน้อยโดยตั้งใจ (composite ครอบคลุมรูปแบบหลัก) การ scan ช่วงวันที่อาจต้อง partition เมื่อมีขนาดใหญ่
- **Retention** ขับโดยนโยบาย tenant; schema ไม่กำหนดเพดาน

## 7. ความเชื่อมโยงข้ามโมดูล

- โมดูลธุรกรรมทั้งหมด — [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory](/th/inventory/inventory), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [costing](/th/inventory/costing), [vendor-pricelist](/th/inventory/vendor-pricelist), [product](/th/inventory/product), [recipe](/th/inventory/recipe)
- [access-control/user](/th/inventory/access-control/user) — การ resolve `actor_id`
- [reporting-audit/user-activity](/th/inventory/reporting-audit/user-activity) — projection `entity_type = 'auth'` ของตารางนี้
- [reporting-audit/notification](/th/inventory/reporting-audit/notification) — event ของ workflow โดยปกติ fan-out ไปทั้งสองทาง
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — action `upload` / `download` บันทึกด้วย `entity_type = 'attachment'`
- [reporting-audit/report](/th/inventory/reporting-audit/report) — การส่งอีเมล PO / RFP พร้อม PDF เขียน `email_sent`

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity`, `enum_activity_action`; migration `20260727120000_add_activity_action_comment_submit_review`, `20260908120000_add_email_sent_activity_action`
- **การ redact:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/src/client.ts` — `sensitiveFields`
- **Diff:** `../carmen-turborepo-backend-v2/packages/log-events-library/src/activity/activity-diff.ts` — `buildActivityDiff()`; ผู้บริโภค `apps/micro-business/src/log/activity-log/activity-log.service.ts` `findOneDetail()`
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/activity-logs/activity-logs.controller.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/documents-and-reports/activity-log/*.bru` (list, by-id, find-by-entity, find-by-entity-id, find-one-detail, delete สี่แบบ)
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/activity-log/activity-log.route.tsx`, `activity-log-component.tsx` (`ACTION_OPTIONS`, `ENTITY_TYPE_OPTIONS`), `activity-log-detail-sheet.tsx`
- **Frontend sheet:** `../carmen-inventory-frontend-react/components/share/activity-sheet.tsx`, `activity-sheet-host.tsx` (`openActivity()`, mount ใน `routes/root-layout.tsx`)
- **Frontend hook/type:** `../carmen-inventory-frontend-react/hooks/use-activity-log.ts` (`useActivityLog`, `useActivityLogByRecord`, `useActivityLogDetail`, `useExportActivityLog`), `types/activity-log.ts` (`ActivityLog`, `ActivityLogDetail`, `ActivityFieldChange`, `ActivityChildChange`)
- **ผู้เขียน (ตัวอย่าง):** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` — `logAuthActivity()` (`login`/`logout`, เฉพาะ BU default); `apps/micro-business/src/procurement/purchase-order/purchase-order.service.ts` — `email_sent`

## 9. ไม่ใช่ตารางนี้ — UI telemetry

event การคลิกและ page-view ที่ frontend จับไว้ (`lib/analytics.ts`: batch ละไม่เกิน 50, flush ทุก 10 วินาที, `POST /api/analytics-events`, สูงสุด 100 event ต่อ request, dedup ด้วย `event_id`, ประทับ user/app/domain ฝั่งเซิร์ฟเวอร์) ลงที่ตาราง **platform** `tb_activity_event`, ถูก roll up ทุกคืนเข้า `tb_activity_event_daily` โดย job `activity_rollup` ของ `micro-cronjobs` และถูกลบทิ้งหลัง 365 วันโดย `activity_retention` (ทั้งคู่ 2026-07-30) pipeline นั้นไม่เกี่ยวอะไรกับ `tb_activity` เลย — บันทึกไว้ในเล่ม Platform: [Activity Events](/th/platform/activity-events) (explorer ต่อ event, `activity_event.detail`) และ [Usage Analytics](/th/platform/usage-analytics) (dashboard, `activity_event.read`)
