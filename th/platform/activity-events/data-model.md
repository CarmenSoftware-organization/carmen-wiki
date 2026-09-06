---
title: บันทึกกิจกรรม — โมเดลข้อมูล (Data Model)
description: ทุกฟิลด์ของเรคคอร์ด tb_activity_event — ใครเป็นคนเขียน ฟิลด์ไหนจำเป็น ฟิลด์ที่เพิ่มเข้ามาเฉพาะตอนอ่าน พร้อมงาน retention 365 วันและ rollup รายวันที่คุมว่าแถวมีชีวิตอยู่นานแค่ไหน
published: true
date: '2026-09-06T01:55:00.000Z'
tags: book/platform, activity-events, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# บันทึกกิจกรรม — โมเดลข้อมูล (Data Model)

หน้านี้บันทึก `tb_activity_event` ตาราง UI telemetry แบบ append-only ที่อยู่เบื้องหลัง [Activity Events](/th/platform/activity-events) และโมดูลพี่น้องที่เป็นตัวสรุป [Usage Analytics](/th/platform/usage-analytics) มันไม่ใช่ `tb_activity` ตาราง change-history/audit ที่อยู่เบื้องหลังปุ่ม "View History" ที่อื่นในผลิตภัณฑ์ — ดูความแตกต่างเต็ม ๆ ที่ §2 ของหน้าหลัก ไม่มีเนื้อหาส่วนไหนในหน้านี้พูดถึง `tb_activity`

โมเดลนี้นิยามอยู่ที่ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1489-1509` (HEAD `937cf5ac4`, 2026-09-06) คอมเมนต์หัวไฟล์ของมันเองระบุเจตนาการออกแบบไว้ตรง ๆ และเส้นทาง write/retention ด้านล่างก็ยืนยันสิ่งนี้ ไม่ใช่แค่พูดซ้ำ: "Raw UI telemetry (append-only) — ไม่มี soft delete / audit columns โดยตั้งใจ: ปริมาณสูง ไม่แก้ไขราย row มีแต่ retention job ลบเป็นชุด (micro-cronjobs)" (`schema.prisma:1487-1488`)

## 1. เรคคอร์ด (Record)

| ฟิลด์ | ชนิด | จำเป็นไหม | ใครกำหนดค่า | หมายเหตุ |
| --- | --- | --- | --- | --- |
| `id` | uuid | เสมอ | ฐานข้อมูล (`gen_random_uuid()` default) | primary key ของแถวเอง ไม่แสดงเป็นค่าที่มีป้ายกำกับบน UI ที่ไหนเลย แต่ใช้เป็นตัวตัดสินความเท่ากันตอนเรียงลำดับ (§3) |
| `event_id` | uuid | เสมอ | Client ต่อ event | คีย์ dedupe — `@unique`; batch ที่ retry ซ้ำสร้างแถวซ้ำไม่ได้ (§2) |
| `session_id` | string | เสมอ | Client ต่อแท็บเบราว์เซอร์ | `crypto.randomUUID()` เก็บใน `sessionStorage`; อยู่ตลอดอายุของแท็บ ไม่ใช่ของผู้ใช้ |
| `user_id` | uuid | เสมอ | **Server** จาก auth token ของผู้เรียก | ไม่เคยอยู่ใน payload ของ client เลย — ดู §2 |
| `bu_code` | string, สูงสุด 64 ตัวอักษร | ไม่จำเป็น | Client ต่อ event | BU ที่ผู้ใช้เลือกอยู่ ณ ขณะนั้น; ไม่มีค่าถ้า profile/BU ยังโหลดไม่เสร็จ นี่คือฟิลด์เดียวกับที่การจำกัดขอบเขตตาม cluster ใช้กรอง (ดู Usage Analytics §4.3) — แถวที่ไม่มี `bu_code` จะมองไม่เห็นสำหรับผู้เรียกที่ถูกจำกัดขอบเขตตาม cluster |
| `app_id` | uuid | ไม่จำเป็น | **Server** จาก header `x-app-id` | ค่าเดียวกันทุกแถวในหนึ่ง batch (หนึ่ง HTTP request = หนึ่ง header); เป็น `null` ถ้า header หายไปหรือไม่ใช่ UUID |
| `domain` | string, สูงสุด 253 ตัวอักษร | ไม่จำเป็น | **Server** จาก header `Origin` | เฉพาะ hostname (ตัด scheme/port/path ออก, แปลงเป็นตัวพิมพ์เล็ก); เป็น `null` ถ้า `Origin` หายไปหรือแปลงไม่ได้ |
| `user_agent` | string, สูงสุด 512 ตัวอักษร | ไม่จำเป็น | **Server** จาก header `User-Agent` | ตัดความยาวเหลือ 512 ตัวอักษรก่อนบันทึก |
| `event_type` | enum: `click` \| `page_view` | เสมอ | Client ต่อ event | `enum_activity_event_type` (`schema.prisma:1482-1485`) |
| `page_path` | string, สูงสุด 512 ตัวอักษร | เสมอ | Client ต่อ event | `window.location.pathname` ณ ขณะเกิด event |
| `element_id` | string, สูงสุด 100 ตัวอักษร | ไม่จำเป็น | Client เฉพาะ event ประเภท `click` | ได้จากลำดับ: attribute `data-track` → `id` ของ element → `aria-label` → ข้อความที่ตัดช่องว่างแล้ว ไม่เคยถูกตั้งค่าสำหรับ `page_view` |
| `element_text` | string, สูงสุด 200 ตัวอักษร | ไม่จำเป็น | Client เฉพาะ event ประเภท `click` | `textContent` ของ element ที่ถูกคลิก ตัดช่องว่างแล้ว ไม่เคยถูกตั้งค่าสำหรับ `page_view` |
| `props` | JSON object, default `{}` | ไม่จำเป็น | Client ต่อ event | สำหรับ `page_view`: มี `{ route_pattern }` เสมอ (path ที่ normalize ส่วน dynamic แล้ว เช่น `/procurement/purchase-request/:id`) สำหรับ `click`: มีเฉพาะ attribute เสริม `data-track-*` ถ้ามี |
| `client_ts` | timestamptz | เสมอ | Client ต่อ event | `new Date().toISOString()` ณ ขณะที่ event ถูก *queue* — ไม่จำเป็นต้องเป็นเวลาที่ batch ถูกส่งจริง (การ queue/retry อาจทำให้ request จริงช้ากว่านั้น) |
| `server_ts` | timestamptz | เสมอ | **ฐานข้อมูล** `@default(now())` | client หรือโค้ดแอปกำหนดค่าไม่ได้เลย — ไม่มีอะไรใน payload ของ `createBatch()` ที่ตั้งค่านี้ ทุกแถวในหนึ่ง `createMany()` batch มีค่าเท่ากันเป๊ะ เพราะ default `now()` ของ Postgres คำนวณที่เวลาเริ่ม transaction ไม่ใช่ต่อแถวตามเวลานาฬิกาจริง (§3) |

ไม่มีคอลัมน์ไหนถูกอัปเดตหลัง insert เลย และไม่มีคอลัมน์ soft-delete (`deleted_at`) — แถวจะคงอยู่ตามที่เขียนไว้จนกว่างาน retention จะลบทิ้งจริง (§4)

## 2. ฟิลด์ที่ client ไม่เคยส่งมาเอง

มีสองจุดที่อ่านผิดง่ายถ้าดูแค่ type `AnalyticsEvent`/`ActivityEvent` ฝั่ง frontend เพียงอย่างเดียว จึงขอระบุตรง ๆ ที่นี่ แต่ละจุดยืนยันจากการอ่าน source จริงของฟิลด์นั้น ไม่ใช่เดาจาก type definition:

- **`user_id` ไม่เคยอยู่ใน payload ของ client เลย** interface `AnalyticsEvent` ฝั่ง frontend เอง (`../carmen-inventory-frontend-react/lib/analytics.ts:32-42`) ไม่มีฟิลด์ `user_id` และ Zod schema ต่อ event ฝั่ง backend (`ActivityEventSchema`, `activity-event.dto.ts:9-46`) ก็ไม่มีฟิลด์นี้เช่นกัน มันถูกอ่านจาก request ที่ authenticate แล้ว (`ExtractRequestHeader(req)` ใน `analytics-events.controller.ts:87`) แล้วส่งลงมาเป็นพารามิเตอร์ `user_id` แยกต่างหาก ประทับเหมือนกันทุก event ใน batch โดย `createBatch()` (`activity-event.service.ts:92-96`) client จึงอ้างว่าเป็นผู้ใช้คนอื่นนอกเหนือจาก Bearer token ของตัวเองไม่ได้
- **`app_id`, `domain`, และ `user_agent` ก็ไม่เคยอยู่ใน payload ต่อ event เช่นกัน** — ทั้งสามเป็น "client context" ชุดเดียวต่อหนึ่ง HTTP request ดึงมาจาก header โดย `ExtractClientContext()` (`extract_client_context.ts` เต็ม 62 บรรทัด) แล้วประทับเหมือนกันทุก event ใน batch นั้น (`activity-event.service.ts:98-101` คอมเมนต์ของตัวเอง: "client context เหมือนกันทุกแถว — batch หนึ่งมาจาก request เดียว") `ExtractClientContext()` ไม่ throw เลยแม้ header จะผิดรูป (คอมเมนต์ของตัวเอง: "header ที่ผิดรูปต้องไม่ทำให้คำขอที่ผ่าน guard มาแล้วล้ม") — มันจะลดค่าฟิลด์นั้นเป็น `null` แทน

## 3. ฟิลด์ที่เพิ่มเข้ามาเฉพาะตอนอ่าน (ไม่ได้เก็บจริง)

`findEvents()` (`activity-event.service.ts:246-347`, query ของ raw explorer) เติมสามฟิลด์ให้กับแถวที่คืนกลับมา ซึ่ง **ไม่มีอยู่บน `tb_activity_event` เลย**:

| ฟิลด์ | ที่มา | ค่า fallback |
| --- | --- | --- |
| `user_name` | lookup จาก `tb_user`/`tb_user_profile` ด้วย `user_id` หลังจากได้แถวของหน้านั้นแล้ว (query lookup เดียวต่อทั้งหน้า ไม่ใช่ต่อแถว) — ชื่อ+นามสกุล ถ้าไม่มีใช้ `username` ถ้าไม่มีใช้ `email` | `null` ถ้า resolve เรคคอร์ดผู้ใช้ไม่ได้ |
| `user_email` | lookup เดียวกัน, `tb_user.email` | `null` |
| `app_name` | lookup จาก `tb_application` ด้วย `app_id` รูปแบบ query-เดียวต่อหน้าเดียวกัน | `null` ถ้า `app_id` เองไม่มีค่า |

เพราะสามฟิลด์นี้คำนวณตอนอ่าน จึงอาจเก่ากว่าความจริงเทียบกับ actor/application ตัวจริง (เช่น ผู้ใช้เปลี่ยนชื่อภายหลัง) — `user_id`/`app_id` ดิบบนแถวที่เก็บไว้ไม่เปลี่ยน เปลี่ยนแค่ผลลัพธ์ของการ join ตอนอ่านครั้งต่อไปเท่านั้น

## 4. การเก็บรักษาข้อมูล (Retention) และการสรุปยอดรายวัน (Rollup)

งานตามเวลาสองงานคุมอายุของตารางนี้ ทั้งคู่นิยามอยู่ใน `../micro-cronjobs` (HEAD `d17d8eb9bc3`, 2026-09-04) และทั้งคู่ถูก seed เป็น cron entry ที่ **active** อยู่ในตาราง `"CRONJOBS"."Cronjob"` เดียวกับที่หน้า [Cronjobs](/th/platform/cronjobs) ของแพลตฟอร์มเองบริหารจัดการ (ยืนยันโดย backend proxy ของโมดูลนั้นเอง `platform_cronjobs.service.ts:7-30` ซึ่งระบุ `CronJobRow` ว่าเป็น "one row of `\"CRONJOBS\".\"Cronjob\"` as micro-cronjob serialises it" — ชื่อตารางเดียวกับที่ migration seed ด้านล่าง insert เข้าไป)

### 4.1 Retention — คำตอบ และจุดที่บังคับใช้จริง

**แถวดิบถูกเก็บไว้ 365 วัน แล้วถูกลบทิ้งจริง** จุดบังคับใช้คือ `ActivityRetentionExecutor.Execute()` (`../micro-cronjobs/internal/executor/activity_retention.go` เต็ม 65 บรรทัด) ถูก dispatch เมื่อ `job_type` ของ cron job เป็น `"activity_retention"` (`executor.go:80-81`) มันทำงานเป็นลูปลบแบบแบ่ง batch ไม่ใช่คำสั่งเดียว:

```
DELETE FROM tb_activity_event
WHERE id IN (
    SELECT id FROM tb_activity_event
    WHERE server_ts < NOW() - make_interval(days => retention_days)
    LIMIT batch_size
)
```

— วนซ้ำจนกว่าจะมีรอบที่ลบได้ศูนย์แถว โดยเช็ค deadline ของ context งาน (`ctx.Err()`) ระหว่างแต่ละ batch เพื่อให้การลบที่ใช้เวลานานถูกตัดจบอย่างสะอาดโดย timeout ของ scheduler เอง แทนที่จะค้างครึ่ง ๆ กลาง ๆ โดยไม่มีบันทึกว่าไปถึงไหนแล้ว

งานนี้ไม่ใช่แค่ทฤษฎี: migration seed ตัวหนึ่งใส่มันเป็น cron entry ที่ตั้งเวลาไว้และ **active** อยู่จริง — `../micro-cronjobs/migrations/20260730093731_seed_activity_retention_job.up.sql` — ชื่อ "Activity events retention (365d)", `job_type = 'activity_retention'`, `cron_expression = '0 4 * * *'` (04:00 ทุกวัน), `job_data = {"retention_days":365,"batch_size":10000}`, `is_active = true` (struct ค่า default ของ Go ใน executor เองก็เป็นตัวเลขชุดเดียวกัน — `RetentionDays: 365, BatchSize: 10000` — ถ้า config ของงานไหนขาดสองค่านี้ไป แต่แถวที่ seed ไว้ระบุค่าตรง ๆ อยู่แล้ว)

เพราะแถวนี้อยู่ในตารางเดียวกับที่หน้า Cronjobs ของแพลตฟอร์มบริหารจัดการ operator ที่ถือ `cronjob.manage` จึงอาจปิดหรือปรับค่าช่วงเวลา retention นี้ผ่านหน้าจอนั้นได้ในหลักการ — ยืนยันเชิงโครงสร้างแล้ว (ตารางเดียวกัน รูปแถวเดียวกัน) แต่ไม่ได้ทดสอบกับ deployment จริง และอยู่นอกขอบเขตของหน้านี้เกินกว่าการชี้ให้เห็นความเชื่อมโยงนี้

### 4.2 Rollup — อะไร feed เข้า `tb_activity_event_daily` และใครอ่านมันบ้าง

ก่อน retention จะรันในแต่ละวัน มีงานที่สองสรุปยอดแถวดิบล่าสุดเข้า `tb_activity_event_daily` (`schema.prisma:1511-1529`) — ตารางสรุปที่ key ด้วย `(day, bu_code, domain, app_id, event_type, page_path, element_id)` เก็บ `clicks`/`sessions`/`users` จุดบังคับใช้คือ `ActivityRollupExecutor.Execute()` (`../micro-cronjobs/internal/executor/activity_rollup.go` เต็ม 80 บรรทัด) ถูก dispatch เมื่อ `job_type = "activity_rollup"` (`executor.go:78-79`) seed ไว้เป็น active ที่ `cron_expression = '30 3 * * *'` (03:30 ทุกวัน ก่อนหน้า retention ตอน 04:00), `job_data = {"days_back":2}` (`migrations/20260730092930_seed_activity_rollup_job.up.sql`) มันจะสรุปยอดใหม่ทีละหนึ่งวันปฏิทินแบบ **UTC** เต็มวัน ย้อนหลังไป `days_back` วัน และข้ามวันปัจจุบัน (ที่ยังไม่จบ) เสมอ การ upsert ใช้ `ON CONFLICT ... DO UPDATE` การรันซ้ำสำหรับวันที่สรุปไปแล้วจึงปลอดภัยและ idempotent — เป็นการออกแบบที่คอมเมนต์ของไฟล์เองยืนยันว่าตั้งใจ ("Idempotent — upserts via `ON CONFLICT` so re-running the same day is safe")

`tb_activity_event_daily` **ไม่เคยถูกลบ** โดยงานทั้งสองนี้ หรือโดยสิ่งอื่นใดที่พบ: การ grep ประวัติ migration/model ทั้งหมดหาคำว่า `tb_activity_event_daily` นอกเหนือจากตอนสร้างตารางเองกับ `INSERT` ของ rollup เจอ `DELETE` อยู่แค่จุดเดียว และมันไม่ใช่กลไก retention — เป็นคำสั่งครั้งเดียวที่มี guard อยู่ใน schema migration ตัวหนึ่ง (`20260731000000_activity_event_client_context/migration.sql`) ที่ล้างตาราง *เฉพาะเมื่อ* unique index ของมันยังไม่มีคอลัมน์ `domain`/`app_id` ที่กำลังถูกเพิ่มใน migration เดียวกัน เพื่อป้องกันไม่ให้ rollup รอบถัดไปนับซ้ำภายใต้ key แบบเก่า มันรันได้อย่างมากแค่ครั้งเดียว เป็น no-op บนฐานข้อมูลใดก็ตามที่ apply ไปแล้ว และไม่เกี่ยวข้องกับ retention 365 วันของแถวดิบที่รันต่อเนื่องอยู่เลย

**ไม่พบผู้อ่าน `tb_activity_event_daily` เลย** การค้นหาในทุก repository ที่ใช้อ้างอิงสำหรับวิกินี้ — `../carmen-turborepo-backend-v2`, `../micro-cronjobs`, `../micro-report`, `../micro-data` — หา `SELECT`/query ใด ๆ ต่อตารางนี้ นอกเหนือจาก `INSERT ... ON CONFLICT` ของ rollup เอง ไม่พบเลย [Usage Analytics](/th/platform/usage-analytics) คำนวณการแบ่งกลุ่มรายวันของตัวเองสด ๆ จากแถวดิบ `tb_activity_event` ภายในหน้าต่างเวลาของ query (จำกัดที่ 90 วัน) แทนที่จะอ่านตารางนี้ ข้อความนี้เป็นข้อค้นพบจาก repository ที่มีอยู่เท่านั้น ไม่ใช่การพิสูจน์ว่าไม่มีผู้บริโภคข้อมูลนี้อยู่ที่ไหนเลย — อาจมีผู้อ่านอยู่ใน repository นอกเหนือจากชุดอ้างอิงของวิกินี้ก็ได้

## 5. โมดูลที่เกี่ยวข้อง

- [Activity Events](/th/platform/activity-events) — หน้าจอที่ใช้เรคคอร์ดนี้; ตัวกรอง คอลัมน์ และเส้นทางการเขียนโดยสรุป (§3.4 ของหน้านั้น)
- [Usage Analytics](/th/platform/usage-analytics) — แดชบอร์ดสรุปที่คำนวณจากตารางดิบเดียวกัน
- [Cronjobs](/th/platform/cronjobs) — หน้าจัดการของแพลตฟอร์มเองบนตาราง `"CRONJOBS"."Cronjob"` เดียวกันที่ตั้งเวลา retention และ rollup (§4)
- [Applications](/th/platform/applications) — เจ้าของแถว `tb_application` ที่ถูก join เป็น `app_name` ตอนอ่าน (§3)

## 6. แหล่งอ้างอิง

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1479-1529` (HEAD `937cf5ac4`, 2026-09-06) — `enum_activity_event_type`, `tb_activity_event`, `tb_activity_event_daily`, และคอมเมนต์หัวไฟล์ของแต่ละตัว
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/dto/activity-event/activity-event.dto.ts` (เต็ม) — `ActivityEventSchema`/`ActivityEventBatchSchema`, เพดานความยาวของทุกฟิลด์และเพดาน batch 1–100 event
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/helpers/extract_client_context.ts` (เต็ม 62 บรรทัด) — `ExtractClientContext()`, การประทับ `app_id`/`domain`/`user_agent` พร้อมเพดาน/ค่า fallback
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/analytics-events/analytics-events.controller.ts` (เต็ม) — `POST api/analytics-events`, `ExtractRequestHeader` สำหรับ `user_id`, guard ต่าง ๆ
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/analytics-events/analytics-events.service.ts` (เต็ม) — ตัว proxy จาก gateway ไป microservice
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.service.ts:82-112,246-347` — `createBatch()` (การ insert) และ `findEvents()` (การเติมชื่อผู้ใช้/แอปตอนอ่าน)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/platform_cronjobs.service.ts:7-30` — `CronJobRow` ยืนยันว่าหน้า Cronjobs ของแพลตฟอร์มกับงาน retention/rollup ที่ seed ไว้ใช้ตารางเดียวกัน
- `../carmen-inventory-frontend-react/lib/analytics.ts:30-42` (HEAD `72d6cd340`, 2026-09-04) — รูปร่าง `AnalyticsEvent` ฝั่ง client (ยืนยันว่าไม่มี `user_id` อยู่ในนั้น)
- `../micro-cronjobs/internal/executor/activity_retention.go` (เต็ม 65 บรรทัด, HEAD `d17d8eb9bc3`, 2026-09-04) — executor การลบแบบ batch สำหรับ retention
- `../micro-cronjobs/internal/executor/activity_rollup.go` (เต็ม 80 บรรทัด) — executor การ upsert รายวันสำหรับ rollup
- `../micro-cronjobs/internal/executor/executor.go:68-84` — switch การ dispatch ตาม `job.JobType` ยืนยันว่า job type ทั้งสองต่อเข้ากับ executor ของตัวเองจริง
- `../micro-cronjobs/migrations/20260730093731_seed_activity_retention_job.up.sql` — cron entry retention ที่ seed ไว้และ active (365 วัน, 04:00 ทุกวัน)
- `../micro-cronjobs/migrations/20260730092930_seed_activity_rollup_job.up.sql` — cron entry rollup ที่ seed ไว้และ active (03:30 ทุกวัน, ย้อนหลัง 2 วัน)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260731000000_activity_event_client_context/migration.sql` — การล้าง `tb_activity_event_daily` แบบครั้งเดียวที่มี guard ผูกกับการเปลี่ยน dimension key `domain`/`app_id` ไม่ใช่กลไก retention
