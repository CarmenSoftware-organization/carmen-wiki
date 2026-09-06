---
title: การวิเคราะห์การใช้งาน (Usage Analytics)
description: หน้าแดชบอร์ด UI telemetry ที่ /analytics (module slug คือ usage-analytics) — ทุก StatCard, กราฟรายวัน, และ Top List ทั้งสองชุด นิยามจาก tb_activity_event พร้อมช่องว่างสิทธิ์ activity_event.read/activity_event.detail ที่คุมการ drill-down
published: true
date: '2026-09-06T01:40:06.000Z'
tags: book/platform, usage-analytics
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การวิเคราะห์การใช้งาน (Usage Analytics)

**Usage Analytics** คือหน้าเดียว `UsageAnalytics` ที่เข้าถึงได้ที่ route **`/analytics`** — สังเกตว่า route กับ slug ของโมดูลในวิกินี้เอง (`usage-analytics`) ไม่ตรงกัน ผู้อ่านที่ค้นหาคำใดคำหนึ่งจึงควรมาเจอหน้านี้ทั้งคู่ มันคือแดชบอร์ดสรุปแบบอ่านอย่างเดียวของ UI telemetry (การเปิดหน้าและการคลิกที่ตัว frontend เองบันทึกไว้) สร้างจากการเรียก backend ครั้งเดียว คือ `GET /api-system/platform/analytics/overview` มันมีโมดูลพี่น้องที่แคบกว่า คือ [Activity Events](/th/platform/activity-events) ที่ `/activity-events` ซึ่งแสดง telemetry ชุดเดียวกันแบบเป็นแถวรายบุคคลแทนที่จะเป็นตัวเลขสรุป — ทั้งสองหน้าถูก gate ด้วยสิทธิ์คนละคีย์ ดูรายละเอียดที่ §4

## 1. ภาพรวม

หน้านี้ (`UsageAnalytics.tsx` 251 บรรทัด อ่านแบบเต็ม) render จากบนลงล่างดังนี้:

1. page header พร้อมปุ่ม **Export CSV** (ปิดใช้งานระหว่างโหลด)
2. แถบตัวกรอง: ตัวเลือกช่วงวัน (preset 7/30/90 วัน หรือกำหนดเอง), dropdown Business Unit, dropdown Application, และ dropdown Event type (`click` / `page_view`)
3. banner error ที่แสดงเฉพาะตอน fetch ล้มเหลวเท่านั้น
4. การ์ดสถิติ **StatCards** ห้าใบ (`events`, `clicks`, `page_views`, `sessions`, `users`)
5. ด้านล่างนั้น เลือกแสดงอย่างใดอย่างหนึ่งจากสองแบบ: การ์ด **empty-state** เมื่อช่วงที่เลือกไม่มี event เลย หรือ **กราฟพื้นที่รายวัน** พร้อมการ์ด **Top List** สองใบ (Top Pages, Top Elements)

ทุกค่าบนหน้านี้มาจาก response รูปเดียว `AnalyticsOverview` (`src/types/index.ts:1360-1365` อยู่ใต้หัวข้อ `// ==================== Usage Analytics (tb_activity_event) ====================` ของไฟล์เอง) — `summary`, `daily[]`, `top_pages[]`, `top_elements[]` ทั้งสี่ชุดคำนวณจากการเรียก backend ครั้งเดียวรอบเดียว ไม่มี endpoint แยกต่อวิดเจ็ต

## 2. บริบททางธุรกิจ

แดชบอร์ดนี้มีอยู่เพื่อให้ operator เห็นว่าคอนโซล Platform admin (และแอปอื่นที่บันทึก telemetry ผ่านท่อเดียวกันโดยแชร์ `app_id`) ถูกใช้งานจริงอย่างไร — หน้าไหนถูกเปิด ปุ่มไหนถูกกด กี่ session กี่ผู้ใช้ที่ไม่ซ้ำกัน — โดยไม่ต้องให้สิทธิ์เข้าถึงแถวดิบรายบุคคลที่อยู่เบื้องหลังตัวเลขเหล่านั้น ความแตกต่างนี้ตั้งใจและถูกบังคับด้วยสิทธิ์สองคีย์แยกกัน (§4) ไม่ใช่มุมมองสองแบบของสิทธิ์เดียวกัน

ไม่มีเอกสารเชิงแนวคิดของโมดูลนี้มาก่อน การค้นหาใน `../carmen/docs` ด้วยคำว่า usage analytics / activity_event เจอแค่ bullet ที่ไม่เกี่ยวข้อง ("Permission usage analytics") ใน `workflow-permissions-system.md` ซึ่งไม่ได้พูดถึงหน้านี้ ทุกอย่างในหน้านี้มาจากการอ่าน implementation ของ `../carmen-platform` และ `../carmen-turborepo-backend-v2` โดยตรง

## 3. ตัวเลขแต่ละตัว — นับอะไร มาจากไหน และช่วงเวลาใด

### 3.1 ช่วงเวลาและตัวกรอง

- backend บังคับให้ต้องมี `from`/`to` เป็น ISO 8601 UTC และถือว่าช่วงเป็นแบบ **half-open**: `server_ts >= from AND server_ts < to` (`buildWhere()` ใน `activity-event.query.ts`) คอลัมน์ที่ใช้ตัดคือ `server_ts` — เวลาที่ platform database บันทึกตอนเขียนแถว — ไม่ใช่ `client_ts` ซึ่งเป็นเวลาที่เบราว์เซอร์รายงานว่า event เกิดขึ้นจริง
- ช่วงถูกจำกัดไว้ที่ **90 วัน** (`MAX_RANGE_DAYS`, `analytics-range.ts`) บังคับโดย `parseRange()` ซึ่งตอบ `400 Bad Request` ถ้ากว้างเกินนั้น (`analytics-range.ts:16-32`) ฝั่ง frontend มีค่าคงที่เดียวกันสะท้อนไว้ (`utils/analyticsRange.ts:14` คอมเมนต์ "ต้องตรงกับ MAX_RANGE_DAYS ฝั่ง backend") เพื่อปฏิเสธช่วงกำหนดเองที่กว้างเกินตั้งแต่ฝั่ง client ก่อนที่จะยิง request ที่ server จะตอบ 400 อยู่แล้ว
- ค่าเริ่มต้นตอนโหลดคือ **7 วันล่าสุด** คำนวณจาก `presetRange(7)` (`UsageAnalytics.tsx:30`) ขอบของ preset ถูกตัดที่ **เที่ยงคืนเวลาไทย** ไม่ใช่เที่ยงคืน UTC (`presetRange()`/`tzMidnightToUtc()`, `analyticsRange.ts:72-93`) — คอมเมนต์หัวไฟล์ของมันเองระบุเหตุผล (`analyticsRange.ts:1-7`): ถ้าตัดที่เที่ยงคืน UTC วันแรกและวันสุดท้ายในกราฟจะโผล่มาเป็นวันที่ไม่เต็ม เพราะการจัดกลุ่มรายวันฝั่ง backend ก็กลุ่มตามวันเวลาไทยเช่นกัน (§3.3)
- มีตัวกรองอีกสามตัวที่ทำให้ช่วงเดียวกัน **แคบลงเท่านั้น ไม่ขยาย**: **Business Unit**, **Application**, และ **Event type** (`click`/`page_view`) dropdown ของ BU และ Application โหลดครั้งเดียวตอน mount จาก `businessUnitService`/`applicationService` จำกัดไว้ที่ `perpage: 100` ทั้งคู่ (`useAnalyticsFilterOptions.ts:32-33`) — fleet ที่มี business unit หรือ application เกิน 100 รายการจะไม่เห็นตัวเลือกครบใน dropdown ทั้งสองนี้ นี่คือขีดจำกัดเชิงโครงสร้างในตัว hook ไม่ใช่ความล้มเหลวขณะทำงาน และไม่ได้ตรวจสอบกับจำนวนจริงของ deployment ใด ๆ
- บน wire ตัวกรอง BU ถูกส่งเป็น `filter_bu_code` ไม่ใช่ `bu_code` — ตั้งใจ คอมเมนต์ของ `analyticsService.ts` เองอธิบายว่า `KeycloakGuard` (ที่ครอบทั้ง controller) จะสาขาตาม *การมีอยู่* ของ query parameter ที่ชื่อ `bu_code` เป๊ะ ๆ แล้วบังคับว่าผู้เรียกต้องเป็นสมาชิกของ BU นั้นหรือเป็น super-admin ไม่งั้นโยน `401` — ซึ่งจะทำให้ทุกการเรียกของ `support_manager` ที่กรองตาม BU โดน 401 และทำให้ทุกคน (แม้แต่ super-admin) ที่พิมพ์รหัสไม่ตรง BU จริงโดน 401 ด้วย ฝั่ง backend controller ก็เขียนคำเตือนเดียวกันซ้ำเหนือพารามิเตอร์ของตัวเอง (`platform-analytics.controller.ts` คอมเมนต์เหนือ `filter_bu_code` ทั้งสอง route): "อย่า 'จัดระเบียบ' กลับ" เป็น `bu_code`

### 3.2 การ์ดสถิติทั้งห้าใบ (`summary`)

ทั้งห้าค่ามาจากแถว Postgres แถวเดียวจาก query เดียว คำนวณตามช่วงเวลาและตัวกรองด้านบนเป๊ะ ๆ (ฟังก์ชัน `getOverview()` ใน `activity-event.service.ts`, query `summaryRows`):

| การ์ด | นับอะไร | SQL |
| --- | --- | --- |
| Events | ทุกแถวที่ตรงเงื่อนไข ทั้งสอง event type | `COUNT(*)` |
| Clicks | แถวที่ `event_type = 'click'` | `COUNT(*) FILTER (WHERE event_type = 'click')` |
| Page views | แถวที่ `event_type = 'page_view'` | `COUNT(*) FILTER (WHERE event_type = 'page_view')` |
| Sessions | ค่า `session_id` ที่ไม่ซ้ำกันในแถวที่ตรงเงื่อนไข | `COUNT(DISTINCT session_id)` |
| Active users | ค่า `user_id` ที่ไม่ซ้ำกันในแถวที่ตรงเงื่อนไข | `COUNT(DISTINCT user_id)` |

คำว่า "Active" ใน "Active users" หมายถึงแค่ "มี click หรือ page_view อย่างน้อยหนึ่งครั้งในช่วงนี้" เท่านั้น ไม่มีนิยามเรื่อง session duration หรือ idle-timeout แยกต่างหากอยู่เบื้องหลัง

เมื่อ fetch ล้มเหลว `StatCards` จะแสดงขีด (`—`) แทนทุกการ์ด ไม่ใช่ `0` (`StatCards.tsx` คอมเมนต์ของตัวเอง: "ไม่มี `summary` (โหลดไม่สำเร็จ) ≠ ค่าเป็นศูนย์") เป็นการตัดสินใจออกแบบโดยเจตนา เพื่อไม่ให้การวัดที่ล้มเหลวดูเหมือนค่าที่วัดได้จริงว่าเป็นศูนย์

### 3.3 สถิติรายวัน — อะไรถูกวาดกราฟ อะไรอยู่แค่ในไฟล์ export

`WHERE` ชุดเดียวกันยังขับเคลื่อน query แบบ `GROUP BY` ตามวัน (query `daily` ใน `activity-event.service.ts`): `clicks`, `page_views`, `sessions`, `users` ต่อวัน โดยใช้

```
to_char((server_ts AT TIME ZONE 'Asia/Bangkok')::date, 'YYYY-MM-DD') AS day
```

`'Asia/Bangkok'` คือ `ANALYTICS_TZ` ค่าคงที่จุดเดียวฝั่ง backend (`activity-event.types.ts:1-2` คอมเมนต์ "จุดเดียวในระบบ อย่า hardcode ซ้ำที่อื่น") และแยกกันคือค่า offset คงที่ที่ hardcode ไว้ (`TZ_OFFSET_MS = 7 * 60 * 60 * 1000`) ฝั่ง frontend ซึ่งคอมเมนต์ของไฟล์เองระบุว่าต้องแก้พร้อมกันกับค่าคงที่ฝั่ง backend หากมีการเปลี่ยน เพราะไม่มีการคำนวณเชื่อมกันอัตโนมัติ (`analyticsRange.ts:17-30`) คอมเมนต์เดียวกันยังระบุเหตุผลที่ใช้ offset คงที่แทนการ resolve timezone ผ่าน `Intl`: กรุงเทพฯ ใช้ UTC+7 มาโดยไม่มี DST ตั้งแต่ปี 1920

**มีแค่ `sessions` และ `users` เท่านั้นที่ถูกวาดในกราฟ** `UsageChart.tsx` render `Area` แค่สองเส้น คือ `sessions` และ `users` — `clicks` กับ `page_views` ถูกคำนวณต่อวันและอยู่ใน response เดียวกัน แต่ไม่เคยถูกวาดกราฟเลย เข้าถึงได้ผ่านไฟล์ export CSV ด้านล่างเท่านั้น

เพราะ `sessions` และ `users` ในแถวรายวันเป็น `COUNT(DISTINCT ...)` **เฉพาะภายในวันนั้นวันเดียว** ตัวเลขจึงไม่รวมกันเป็นยอดของการ์ด `summary` เมื่อ session หรือผู้ใช้คนเดียวกันมีกิจกรรมมากกว่าหนึ่งวันในช่วงที่เลือก — ตัวเลขสองชุดนี้ไม่ได้ถูกออกแบบให้กระทบยอดกัน ความต่างระหว่าง "ผลรวมของคอลัมน์รายวัน" กับ "การ์ดสรุป" จึงไม่ใช่บั๊ก

**การ export CSV** (ปุ่ม "Export CSV" ที่ page header) เขียน `day, clicks, page_views, sessions, users` ตรงจาก array `overview.daily` ที่ดึงมาแล้ว ไม่มี endpoint export แยกต่างหาก (`UsageAnalytics.tsx:101-118`, `generateCSV`/`downloadCSV` ใน `utils/csvExport.ts`) ก่อนสร้าง blob ฝั่ง client ทุกเซลล์ผ่าน `neutraliseFormulaPrefix()` (`csvExport.ts:1-13` อ่านจากตัวฟังก์ชันตรง ๆ ไม่ใช่จากคอมเมนต์ของมัน): ค่าที่ขึ้นต้นด้วย `=`, `+`, `@`, tab, CR, **หรือเครื่องหมายลบ (hyphen)** (`/^[=+@\t\r-]/`) จะถูกใส่เครื่องหมายคำพูดเดี่ยวนำหน้า เพื่อให้สเปรดชีตอ่านเป็นข้อความล้วน — คอมเมนต์ของฟังก์ชันเองระบุแค่ `=`, `+`, `@`, และ tab/CR เท่านั้น ไม่ได้พูดถึงเครื่องหมายลบที่ regex จริง ๆ ตรวจอยู่ ค่าที่ขึ้นต้นด้วยเครื่องหมายลบมีข้อยกเว้นก่อน: `isValidNegativeNumber()` (`/^-\d+(\.\d+)?$/`) ตรวจว่าค่านั้นเป็นจำนวนลบแบบสะอาด (จำนวนเต็มหรือทศนิยม เช่น `-42`, `-3.14`) หรือไม่ ถ้าใช่ `neutraliseFormulaPrefix()` จะคืนค่านั้นโดยไม่ใส่เครื่องหมายคำพูด ค่าที่ขึ้นต้นด้วยเครื่องหมายลบแต่ *ไม่ใช่* จำนวนลบแบบสะอาด — เช่น payload สูตรอย่าง `-cmd|'/c calc'!A1` หรือค่าที่มีตัวคั่นหลักพันอย่าง `-1,234` — จะตกไปที่กิ่ง neutralize และถูกใส่เครื่องหมายคำพูดเหมือนค่าที่ขึ้นต้นด้วยอักขระเสี่ยงตัวอื่น เนื่องจากทุกค่าที่หน้านี้ export (StatCard/รายวัน) เป็นจำนวนเต็มที่ไม่ติดลบล้วน กิ่งเครื่องหมายลบจึงเป็นโค้ดที่ไม่ถูกใช้งานจริงสำหรับ export ชุดนี้โดยเฉพาะ แต่ไม่ใช่โค้ดที่ตายใน `generateCSV` โดยรวม เพราะฟังก์ชันนี้ใช้ร่วมกับการ export CSV อื่นในโค้ดเบส ชื่อไฟล์คำนวณช่วงวันผ่านการแปลงเวลาไทยแบบเดียวกับที่ UI แสดง (`ymdInTz()`) ไม่ใช่การตัดสตริง UTC ตรง ๆ — คอมเมนต์ในโค้ดยกตัวอย่างจริงที่หลีกเลี่ยงได้: ช่วง "1–7 ส.ค. เวลาไทย" ที่ `from` เป็น `2026-07-31T17:00Z` ถ้าไม่แปลงก่อนจะได้ชื่อไฟล์ที่ขึ้นต้นด้วยวันที่ 31 ก.ค. แทน

### 3.4 Top Pages (`top_pages`)

query อีกชุด ใช้ `WHERE` เดียวกัน กลุ่มตาม `page_path` เรียงตามจำนวน event มากไปน้อย `LIMIT 10` (query `topPages` ใน `activity-event.service.ts`): `events` (`COUNT(*)`), `sessions` และ `users` (ทั้งคู่เป็น `COUNT(DISTINCT ...)` ขอบเขตเฉพาะแถวของ `page_path` นั้นเอง — ไม่ใช่ตัวเลข sessions/users รวมทั้งช่วง) ป้ายย่อยใต้แต่ละแถว ("`{sessions} sessions · {users} users`", `pages.usageAnalytics.topPageSub`) รายงานค่า distinct ต่อหน้าเหล่านี้ ไม่ใช่สัดส่วนของยอดสรุป

`page_path` คือ pathname ดิบตามที่ frontend บันทึกไว้ — คอมเมนต์ของ query ฝั่ง backend controller ระบุว่าค่านี้อาจมี record id ของ route แบบ detail อยู่ในนั้น ซึ่งเป็นเหตุผลที่ list นี้ (ต่างจาก Top Elements) ถูกจำกัดขอบเขตตาม cluster ด้วย (§4.2)

### 3.5 Top Elements (`top_elements`)

กลุ่มตาม `element_id` จำกัดเฉพาะ `event_type = 'click' AND element_id IS NOT NULL AND element_id <> ''` เรียงตามจำนวนคลิกมากไปน้อย `LIMIT 10` (query `topElements` ใน `activity-event.service.ts`): `clicks` (`COUNT(*)`) `element_text` และ `page_path` แต่ละตัวถูกเลือกด้วย Postgres `mode() WITHIN GROUP (...)` — ค่าที่ถูกบันทึกบ่อยที่สุดสำหรับ `element_id` นั้นภายในช่วงเวลา ไม่จำเป็นต้องเป็นข้อความหรือหน้าปัจจุบันจริง ๆ ของ element นั้น ถ้า `element_id` เดียวกันถูก render ภายใต้ page path ต่างกันสองที่ หรือมีป้ายข้อความต่างกันสองแบบในช่วงเวลานั้น แถวที่แสดงจะเป็นค่าที่เกิดขึ้นบ่อยกว่า ซึ่งไม่จำเป็นต้องเป็นค่าที่เป็นจริงล่าสุด

Top Elements กดไม่ได้เลยสำหรับทุกคน: `TopList.tsx` จะทำให้แถวเป็น `<button>` ก็ต่อเมื่อมี prop `onSelect` ส่งมาเท่านั้น และ `UsageAnalytics.tsx` ไม่เคยส่ง `onSelect` ให้ตอน render list ของ Top Elements เลย (ต่างจาก Top Pages, §4.1)

### 3.6 ความสอดคล้องกันของทั้งสี่ชุดตัวเลข — ไม่ใช่ snapshot เดียวกัน

`summary`, `daily`, `top_pages`, และ `top_elements` เป็น SQL statement อิสระสี่คำสั่งที่ยิงพร้อมกันด้วย `Promise.all` เพื่อลด latency เท่านั้น ไม่ได้อยู่ใน transaction เดียวกัน (คอมเมนต์ของ `getOverview()` ใน `activity-event.service.ts` เอง: "ไม่ใช่เพื่อความสอดคล้องของข้อมูล... ไม่มี transaction ร่วมกัน") การเขียนข้อมูลที่เกิดขึ้นระหว่างทั้งสี่ query อาจทำให้ตัวเลขเหลื่อมกันเล็กน้อย คอมเมนต์เดียวกันระบุว่ายอมรับได้สำหรับแดชบอร์ดแบบนี้ ("เป็นตัวเลขเชิงภาพรวม ไม่ใช่ยอดที่ต้องกระทบยอด") ไม่ใช่สิ่งที่ตัวเลขบนหน้านี้ถูกคาดหวังให้รับประกัน

### 3.7 สถานะว่างเปล่า vs. สถานะ error — สองเหตุผลที่ทำให้ไม่มีกราฟ

`UsageAnalytics.tsx` แยกสองสถานะที่อาจดูเหมือนกันออกจากกัน:

- **fetch ล้มเหลว** (มีการตั้งค่า `error`): banner error แสดงขึ้น; `overview` ถูกรีเซ็ตเป็น `null`; พื้นที่กราฟ/Top List ไม่ถูก render เลย แม้แต่การ์ด empty-state คอมเมนต์ในโค้ดระบุเหตุผลตรง ๆ ว่าการ render กราฟเปล่ากับ Top List ที่ขึ้น "ไม่มีข้อมูล" จะ "อ่านเหมือนผลที่วัดมาได้จริงว่าเป็นศูนย์ ทั้งที่จริงคือยังไม่รู้ค่า" (`UsageAnalytics.tsx:184-188`)
- **fetch สำเร็จ แต่ไม่มี event เลย** (`isEmpty` คือ `overview.summary.events === 0`): กราฟ/Top List ถูกแทนที่ด้วยการ์ด `EmptyState` ที่ขึ้นว่า "No events in the selected range" พร้อมคำแนะนำให้ขยายช่วงวันหรือเอาตัวกรอง BU/Application ออก (`pages.usageAnalytics.emptyTitle`/`emptyDescription`) การ์ด StatCards ยังแสดงศูนย์จริงในกรณีนี้ เพราะ `overview` เองไม่ใช่ null

## 4. บทบาทและสิทธิ์

### 4.1 สองคีย์ — แต่ละคีย์ให้สิทธิ์อะไร และเปิดหน้าไหน

permission catalog ระบุความต่างระหว่างสอง action ของ `activity_event` ไว้ตรง ๆ (`seed.platform-permission.data.ts:95-96`, `../carmen-turborepo-backend-v2`):

| คีย์ | คำอธิบายใน catalog | เปิดหน้าไหน |
| --- | --- | --- |
| `activity_event.read` | "View the Usage Analytics dashboard (aggregate figures only)" | หน้านี้ `/analytics` |
| `activity_event.detail` | "View raw UI telemetry events, including which user clicked what" | [Activity Events](/th/platform/activity-events), `/activity-events` |

ผู้เรียกอาจถือคีย์ใดคีย์หนึ่งได้โดยไม่มีอีกคีย์ — ทั้งสองเป็นสิทธิ์อิสระต่อกัน ไม่ใช่ระดับของสิทธิ์เดียวกัน ทั้งคู่ถูก gate สามชั้นที่มีรูปแบบเหมือนกันแต่คีย์ต่างกัน:

| ชั้น | `/analytics` (หน้านี้) | `/activity-events` |
| --- | --- | --- |
| แถว nav ใน sidebar | `permission: 'activity_event.read'`, `feature: 'usage_analytics'`, `groupKey: 'navGroup.analytics'` | `permission: 'activity_event.detail'`, `feature: 'activity_events'`, กลุ่มเดียวกัน |
| Route (`PrivateRoute`) | `requiredPermission="activity_event.read"` `feature="usage_analytics"` | `requiredPermission="activity_event.detail"` `feature="activity_events"` |
| Backend endpoint | `GET .../analytics/overview` — `@RequirePlatformPermission('activity_event.read')` | `GET .../analytics/records` — `@RequirePlatformPermission('activity_event.detail')` |

ที่มา: `platformNav.ts:30-33` (สองแถวอยู่ที่บรรทัด 32-33 ตั้งใจให้อยู่ติดกัน ตามคอมเมนต์ที่บรรทัด 30-31 ซึ่งระบุว่าถ้าแยกออกจากกันจะทำให้ sidebar ขึ้นหัวข้อ "Analytics" สองอัน); `App.tsx:475-489`; `platform-analytics.controller.ts` (`@RequirePlatformPermission` บน `overview()` และ `events()`) ทั้งสองแถวไม่มี `superAdminOnly`

`PrivateRoute.tsx` (อ่านแบบเต็ม) ตรวจสิทธิ์ **ก่อน** feature flag เสมอ: session ที่ไม่มีคีย์ที่ต้องการจะเห็น `<Forbidden />` ไม่ว่า flag จะเป็นอะไร มีแค่ session ที่ผ่านการตรวจสิทธิ์แล้วเท่านั้นที่จะไปเจอ `hide` (→ `<NotFound />`) หรือ `inactive` (→ `<ComingSoon />`) ของ feature key `usage_analytics` (`src/constants/featureFlags.ts:64`, `groupKey: 'navGroup.analytics'`, `defaultState: 'active'`)

### 4.2 `activity_event.detail` ยังคุมการ drill-down ภายในหน้านี้ด้วย

การคลิกแถวใน list **Top Pages** โดยปกติจะพาไปที่ `/activity-events` พร้อมตัวกรองปัจจุบันแนบไปเป็น query parameter (`goToEvents()`, `UsageAnalytics.tsx:93-99`) — คอมเมนต์ของฟังก์ชันเองอธิบายว่าทำไมต้องส่งตัวกรองที่ใช้อยู่ **ทั้งชุด** ไปด้วย ไม่ใช่แค่ page path กับช่วงวัน: ผู้ใช้ที่กรอง BU อยู่แล้วไปเจอหน้า explorer ที่ไม่กรองอะไรเลยจะเห็นจำนวนแถวที่ไม่ตรงกับตัวเลขที่เพิ่งคลิกมา โดยไม่มีอะไรบนหน้าจอบอกว่าทำไม

การ drill-down นี้ถูกห่อด้วย `<Can permission="activity_event.detail">` (`UsageAnalytics.tsx:207-223`): ผู้ที่ถือสิทธิ์นี้จะเห็น list Top Pages **ชุดเดียวกัน** render พร้อม `onSelect={goToEvents}` (แถวกดได้); ผู้ที่ไม่ถือจะเห็น list **เหมือนกันทุกประการ** — แถวเดียวกัน ตัวเลขเดียวกัน ป้ายย่อยเดียวกัน — ผ่าน `fallback` ของ `<Can>` เพียงแต่ไม่มี prop `onSelect` แถวจึงถูก render เป็นข้อความธรรมดา (กดไม่ได้) (`Can.tsx`, `TopList.tsx`) ไม่มีอะไรถูกซ่อนหรือเว้นว่างไว้ มีแค่ affordance การนำทางเท่านั้นที่ถูกงดไว้ Top Elements ไม่เคยได้รับ `onSelect` ไม่ว่ากรณีใด (§3.5) — การ drill-down มีอยู่แค่สำหรับ Top Pages เท่านั้น

การตรวจของ `Can` (ผ่าน `AuthContext.hasPermission` ที่เรียกโดยไม่ระบุ `clusterId`) จะ resolve ผ่าน `checkPermission(eff, 'activity_event.detail')` โดยไม่มีอาร์กิวเมนต์จำกัด cluster ซึ่งนิยามว่าเป็นจริง "ถ้า `activity_event.detail` มีอยู่ใน scope ระดับ platform **หรือใน cluster scope ใดก็ได้แม้แต่อันเดียว**" (`utils/permissions.ts:43-61` คอมเมนต์ของตัวเอง) นี่คือการตรวจแบบหยาบ "คนนี้เห็น affordance ได้ไหม" เท่านั้น — ไม่ได้แปลว่าหน้าปลายทางจะแสดงข้อมูลแบบไม่จำกัดขอบเขต backend จะจำกัดสิ่งที่ `/activity-events` คืนจริงต่อ request แยกต่างหาก (§4.3) ไม่ขึ้นกับสิ่งที่ทำให้ปุ่มบนหน้านี้กดได้

### 4.3 การบังคับใช้ฝั่ง backend และการจำกัดขอบเขตตาม cluster

`platform-analytics.controller.ts` (`../carmen-turborepo-backend-v2`) ซ้อน guard สามชั้นในแต่ละ route:

| Route | Guards | สิทธิ์ที่ต้องมี |
| --- | --- | --- |
| `GET /api-system/platform/analytics/overview` | `KeycloakGuard` (ระดับ class) + `AppIdGuard('analytics.overview')` + `PlatformPermissionGuard` | `activity_event.read` |
| `GET /api-system/platform/analytics/records` | `KeycloakGuard` (ระดับ class) + `AppIdGuard('analytics.events')` + `PlatformPermissionGuard` | `activity_event.detail` |

`AppIdGuard` (`apps/backend-gateway/src/common/guard/app-id.guard.ts` อ่านแบบเต็ม) ตรวจแค่ว่า header `x-app-id` เป็น UUID ที่อยู่ใน allowlist ในหน่วยความจำสำหรับ `api_name` นั้น (`appAllowlistStore.isAllowed(appId, this.api_name)`) — ไม่เคยอ่าน `request.user` หรือสิทธิ์ใด ๆ เลย มันตอบว่า "แอปตัวนี้เรียก API นี้ได้ไหม" ไม่ใช่ "ผู้ใช้คนนี้เข้าถึงได้ไหม" client `api.ts` ที่ใช้ร่วมกันฝั่ง frontend (อ่านตรง บรรทัด 1-23) แนบ `x-app-id` จาก env var ตอน build ไปกับทุก request (บรรทัด 8) และแนบ token `Bearer` จาก `localStorage` ทับไปอีกชั้นผ่าน request interceptor (บรรทัด 23) — นี่คือ session ของผู้ใช้จริงที่อยู่ใต้ด่านตรวจ app-identity ไม่ใช่การเรียกแบบ service-to-service ที่ `AppIdGuard` เพียงอย่างเดียวจะเหมาะกับการ gate

`PlatformPermissionGuard.canActivate()` (`auth/guards/platform-permission.guard.ts` อ่านแบบเต็ม) ถูกระบุไว้ในคอมเมนต์หัวไฟล์ของตัวเองว่าเป็น **"coarse-grained platform RBAC gate"** (ด่านตรวจ RBAC ระดับแพลตฟอร์มแบบหยาบ): มันผ่านถ้าคีย์ที่ต้องการมีอยู่ใน scope ระดับ platform ของผู้เรียก **หรือใน cluster scope ใดก็ได้แม้แต่อันเดียว** (บรรทัด 13) แนบ object `EffectivePlatformPermissions` ที่ resolve แล้วเข้ากับ request ไม่ว่าผลจะเป็นอย่างไร และ short-circuit เป็น `true` ทันทีสำหรับ `is_super_admin === true` ก่อนตรวจคีย์เลยด้วยซ้ำ ทั้งสอง route ของ analytics มี `@RequirePlatformPermission` ครบถูกต้อง จึงไม่เข้าสาขา fail-open ของ guard สำหรับ route ที่ *ไม่มี decorator* (ซึ่งไม่งั้นจะ log คำเตือนแล้วปล่อยผ่านทุกคนโดย default ตามไฟล์เดียวกัน)

controller จำกัดขอบเขตต่ออีกชั้นต่อ request ด้วย `resolveAllowedClusterIds()` (`analytics-scope.ts` อ่านแบบเต็ม) — และที่สำคัญคือใช้ **คีย์ที่คุม endpoint นั้นจริง ๆ** ไม่ใช่ค่า default ที่ใช้ร่วมกัน: `overview()` resolve ขอบเขตด้วย `ACTIVITY_EVENT_READ`; `events()` resolve ด้วย `ACTIVITY_EVENT_DETAIL` (พารามิเตอร์ `required` ของฟังก์ชันไม่มีค่า default โดยเจตนา ตามคอมเมนต์ของมันเอง เพื่อไม่ให้ endpoint ที่เพิ่มมาทีหลัง "สืบทอด" คีย์ผิดตัวไปเงียบ ๆ) ผลลัพธ์เป็นหนึ่งในสามรูปแบบ ถูกส่งเข้าไปในทุก query ของ `getOverview()` เหมือนกันหมด (`buildScopedWhere()` ใน `activity-event.query.ts`):

- `null` — ไม่จำกัด (super-admin หรือถือคีย์ที่ต้องการระดับ platform)
- `[]` — จำกัดจนไม่เหลือ (fail-closed): ผู้เรียกไม่ถือคีย์นี้ใน cluster ไหนเลย หรือ object สิทธิ์เองหายไป/ผิดรูป
- `[...clusterIds]` — จำกัดเฉพาะ business unit ที่สังกัด cluster เหล่านั้น ผ่าน `bu_code IN (...)` คำนวณจากการ query แถว `tb_business_unit` ที่ `deleted_at: null` ของ cluster เหล่านั้น (`resolveBuScope()`, `activity-event.service.ts`) เงื่อนไข `bu_code IN (...)` จะตัดแถวที่ `bu_code` เป็น `NULL` ออกโดยอัตโนมัติตามตรรกะสามค่าของ SQL — event ระดับแพลตฟอร์ม (ที่บันทึกก่อนมีการเลือก BU) จึงมองไม่เห็นสำหรับผู้เรียกที่ถูกจำกัดขอบเขตตาม cluster โดยธรรมชาติของเงื่อนไข ไม่ใช่จากการตรวจเพิ่ม

คอมเมนต์ของ `getOverview()` เองระบุว่าการจำกัดขอบเขตนี้ใช้กับ **ทั้งสี่ชุด** query ไม่ใช่แค่รายการแถวดิบ — เพราะ `top_pages.page_path` อาจมี record id อยู่ในนั้น และ `summary.users` เพียงตัวเดียวก็เปิดเผยกรณีผู้ใช้คนเดียวได้ ทั้งสองอย่างอาจรั่วตัวตนข้าม tenant ให้ผู้เรียกที่ควรเห็นแค่ cluster ของตัวเอง (คอมเมนต์เหนือ `getOverview()` ใน `activity-event.service.ts`)

### 4.4 การมอบสิทธิ์ตาม role bundle

permission catalog seed action ของ resource `activity_event` ไว้แค่สองตัว คือ `read` และ `detail` (`seed.platform-permission.data.ts:95-96`) และคอมเมนต์ของมันเองแยก resource นี้ออกจาก `activity_log` (`tb_activity` ตาราง audit trail/"View History" แยกต่างหากที่ใช้ที่อื่นในผลิตภัณฑ์): "คนละตารางกับ activity_event ข้างบนซึ่งเป็น UI telemetry" (บรรทัด 97) ทั้งสองเป็นกลไกที่ไม่เกี่ยวข้องกันแต่บังเอิญมีคำว่า "activity" ร่วมกัน ผู้อ่านไม่ควรสรุปว่าสิทธิ์ audit trail (`activity_log.read`) มีผลอะไรกับหน้านี้

จาก role bundle ที่ seed ไว้ทั้งสี่ตัวของแพลตฟอร์ม (`seed.platform-role-permission.data.ts:11-52` อ่านแบบเต็ม):

| Role | `activity_event.read` (หน้านี้) | `activity_event.detail` (drill-down / `/activity-events`) |
| --- | --- | --- |
| Platform Admin | มี — ผ่าน `activity_event.*` (บรรทัด 14) | มี — ผ่าน `activity_event.*` |
| Support Manager | มี — `activity_event.read` ระบุตรง ๆ (บรรทัด 40) | **ไม่มี** |
| Support Staff | ไม่มี | ไม่มี |
| Security Officer | ไม่มี | ไม่มี |

คอมเมนต์ในซอร์สเหนือสิทธิ์ของ Platform Admin ระบุเหตุผลของการให้ Support Manager แคบกว่าไว้ตรง ๆ ในบริบทของ resource พี่น้อง `activity_log.*` แต่บรรยายรูปแบบการแยก read/detail แบบเดียวกัน: การให้แค่ `.read` "พอสำหรับตอบลูกค้า" โดยไม่ต้องเปิดเผยแถวดิบรายบุคคลที่อยู่เบื้องหลัง พูดให้เป็นรูปธรรม: Support Manager เปิดแดชบอร์ดนี้และเห็นทุกตัวเลขสรุปได้ แต่เปิด `/activity-events` ไม่ได้ และคลิกผ่านจาก Top Pages ไม่ได้ เพราะถือแค่ `.read` ไม่มี `.detail` ส่วน Support Staff และ Security Officer ไม่ถือคีย์ไหนเลย จึงเข้าหน้าไหนไม่ได้ทั้งคู่

### 4.5 ชุดทดสอบ e2e: ไม่มี

`../carmen-platform-e2e/tests/` (HEAD `a8e3b31`, 2026-08-25) ไม่มีโฟลเดอร์ `usage-analytics`, `analytics`, หรือ `activity-events` เลย — ยืนยันโดย list โครงสร้าง repository นั้นตรง ๆ ร่องรอยเดียวของหน้านี้ใน repository นั้นคือไฟล์ screenshot จากการรันด้วยมือครั้งหนึ่ง `runs/screens/2026-08-25_10-37-26/images/analytics.png` ซึ่งไม่ใช่เทสต์ ทุกข้อความเชิงพฤติกรรมบนหน้านี้มาจากการอ่าน implementation ของ `../carmen-platform` และ `../carmen-turborepo-backend-v2` ไม่ใช่จาก spec ที่รันได้จริง

## 5. โมดูลที่เกี่ยวข้อง

- [Activity Events](/th/platform/activity-events) — หน้า explorer แสดง event ดิบรายบุคคลที่การ drill-down จาก Top Pages ของหน้านี้พาไป ถูก gate ด้วย `activity_event.detail` (§4.1–§4.2) ใช้ `analyticsService.ts` ร่วมกันและอ่านจากตาราง `tb_activity_event` เดียวกัน
- [Feature Flags](/th/platform/feature-flags) — เจ้าของ feature key `usage_analytics` ที่ gate หน้านี้หลังผ่านการตรวจสิทธิ์แล้ว (§4.1)
- [Platform RBAC](/th/platform/rbac) — permission catalog และนิยาม role bundle ที่อ้างถึงใน §4
- [Business Units](/th/platform/business-units) และ [Applications](/th/platform/applications) — เป็นแหล่งข้อมูลของ dropdown ตัวกรองสองตัว (§3.1) หน้านี้ไม่ได้เป็นเจ้าของ list ทั้งสอง

## 6. แหล่งอ้างอิง

path ทั้งหมดด้านล่างเป็น `../carmen-platform` (Platform admin SPA, HEAD `157a65e`, 2026-09-04) เว้นแต่จะขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (backend monorepo, HEAD `937cf5ac4`, 2026-09-06) หรือ `../carmen-platform-e2e` (HEAD `a8e3b31`, 2026-08-25)

- `../carmen-platform/src/pages/UsageAnalytics.tsx` (เต็ม 251 บรรทัด) — ตัวหน้า, `fetchOverview`, `goToEvents` (93-99), `handleExport` (101-118), `isEmpty` (120), การ drill-down ของ Top Pages ที่ห่อด้วย `<Can>` (184-236)
- `../carmen-platform/src/pages/usageAnalytics/StatCards.tsx`, `TopList.tsx`, `UsageChart.tsx` — การ์ด KPI ห้าใบและกฎขีดแทนเมื่อล้มเหลว; การ render แถวกดได้/กดไม่ได้; กราฟพื้นที่สองเส้น (sessions/users)
- `../carmen-platform/src/services/analyticsService.ts` — `getOverview`/`getEvents`, คอมเมนต์เรื่องเปลี่ยนชื่อเป็น `filter_bu_code` (§3.1), คอมเมนต์เรื่องตั้งชื่อ `analytics/records` เทียบ `analytics/event*` เพื่อเลี่ยงตัวบล็อกโฆษณา
- `../carmen-platform/src/types/index.ts:1327-1365` — `AnalyticsSummary`, `AnalyticsDaily`, `AnalyticsTopPage`, `AnalyticsTopElement`, `AnalyticsOverview` อยู่ใต้หัวข้อ `tb_activity_event` ของไฟล์เอง
- `../carmen-platform/src/utils/analyticsRange.ts` (เต็ม) — `ANALYTICS_TZ`, `MAX_RANGE_DAYS`, `TZ_OFFSET_MS` และคอมเมนต์เรื่อง lockstep กับ backend, `presetRange`/`customRange`/`rangeSpanDays`
- `../carmen-platform/src/components/analytics/DateRangeFilter.tsx` — UI preset/กำหนดเอง, การตรวจเพดานช่วงฝั่ง client
- `../carmen-platform/src/hooks/useAnalyticsFilterOptions.ts` — การโหลด dropdown BU/Application, เพดาน 100 แถว, เหตุผลของ `Promise.allSettled`
- `../carmen-platform/src/utils/csvExport.ts:1-13` — `neutraliseFormulaPrefix()` และ `isValidNegativeNumber()` อ่านจากตัวฟังก์ชันตรง ๆ (ข้อค้นพบเรื่องเครื่องหมายลบใน §3.3); `generateCSV`, `downloadCSV`
- `../carmen-platform/src/components/Can.tsx`, `src/components/PrivateRoute.tsx` (ทั้งคู่แบบเต็ม) — ลำดับการ gate สิทธิ์ก่อน feature flag; ผลลัพธ์ `Forbidden`/`ComingSoon`/`NotFound`
- `../carmen-platform/src/context/AuthContext.tsx:268-272`, `src/utils/permissions.ts` (เต็ม) — bootstrap escape hatch ของ `hasPermission` และความหมายของ `checkPermission` แบบมี/ไม่มี `clusterId` (§4.2)
- `../carmen-platform/src/App.tsx:475-489` — การลงทะเบียน route `/analytics` และ `/activity-events`
- `../carmen-platform/src/components/nav/platformNav.ts:30-33` — สองแถว nav (32-33) และคอมเมนต์เรื่อง contiguity เหนือแถว (30-31)
- `../carmen-platform/src/constants/featureFlags.ts:64` — entry ของ feature catalog `usage_analytics`
- `../carmen-platform/src/i18n/en.ts` (บรรทัด 99-102, 4089-4116) และ `src/i18n/th.ts` (บรรทัด 3112-3129) — ข้อความหน้าที่ยกมาอ้างใน §3.2/§3.3/§3.7
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/platform-analytics.controller.ts` (เต็ม) — ทั้งสอง route, guard ของแต่ละตัว, และคอมเมนต์เรื่องกับดักการตั้งชื่อทุกจุดที่อ้างใน §3.1/§4.3
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/platform-analytics.service.ts` — ตัว proxy จาก gateway ไป microservice และรูปร่าง `IAnalyticsQuery`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/analytics-range.ts` (เต็ม) — `parseRange`, `MAX_RANGE_DAYS`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/analytics-scope.ts` (เต็ม) — `ACTIVITY_EVENT_READ`/`ACTIVITY_EVENT_DETAIL`, ตารางการตัดสินของ `resolveAllowedClusterIds()`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts` (เต็ม) — กลไก coarse-gate, super-admin short-circuit, สาขา fail-open ของ route ที่ไม่มี decorator
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/guard/app-id.guard.ts` (เต็ม) — กลไก `x-app-id`/allowlist (§4.3)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.service.ts` (เต็ม 348 บรรทัด) — สี่ query SQL ดิบของ `getOverview()`, `resolveBuScope()`, `findEvents()`
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.types.ts` (เต็ม) — `ANALYTICS_TZ`, รูปร่างแถว, คอมเมนต์เรื่องความหมาย `allowed_cluster_ids` แบบ null/`[]`/`undefined`
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.query.ts` (เต็ม) — `buildWhere()` (ช่วง `server_ts`), `NEVER_MATCH`, `buildBuCodeScope()` (การตัด BU ที่ถูกลบ/bu_code เป็น NULL), `buildScopedWhere()`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts:93-99` — คำอธิบาย catalog ของ `activity_event.read`/`.detail` และคอมเมนต์แยกจาก `activity_log`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-role-permission.data.ts:11-52` (เต็ม) — อาร์เรย์สิทธิ์ที่แน่นอนของทั้งสี่ role bundle
- `../carmen-platform-e2e/tests/` — list ตรง ๆ เพื่อยืนยันว่าไม่มีชุดทดสอบ `usage-analytics`/`analytics`/`activity-events` (§4.5)

## 7. หน้าย่อยของโมดูลนี้

โมดูลนี้มีหน้าเดียว ดูหน้าดัชนีของหนังสือได้ที่ [ดัชนี Platform book](/th/platform)
