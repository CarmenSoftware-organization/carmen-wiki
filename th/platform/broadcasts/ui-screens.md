---
title: Broadcasts — หน้าจอ UI (UI Screens)
description: สามหน้าจอของ Broadcasts — BroadcastManagement (list, filter, CSV export), BroadcastCompose (แท็บ target, preset วันหมดอายุ, preview แบบ live) และ BroadcastEdit (content lock, การแก้ schedule/วันหมดอายุ) — บวกแผง BroadcastPreview ที่ใช้ร่วมกันระหว่าง Compose และ Edit
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, broadcasts, ui
editor: markdown
dateCreated: 2026-06-10T16:00:00.000Z
---

# Broadcasts — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `BroadcastManagement` (`/broadcasts`, list) · `BroadcastCompose` (`/broadcasts/new`, ส่ง) · `BroadcastEdit` (`/broadcasts/:id/edit`, ดู/แก้) — **สามคอมโพเนนต์แยกกัน** ไม่ใช่หน้าจอเดียวที่มีหลายโหมด &nbsp;·&nbsp; **List:** แถบสรุปสถานะ, ค้นหา, sheet ของ filter, ตารางแบบ server-side, CSV export &nbsp;·&nbsp; **โครงของ Compose:** แท็บ Audience → ฟิลด์ Message → Type preset → ป้าย Related-BU → Delivery (เวลาส่ง + วันหมดอายุ) ข้างการ์ด **Preview** แบบ sticky &nbsp;·&nbsp; **โครงของ Edit:** สี่การ์ด (Info / Delivery / Content / Preview) — Content อ่านอย่างเดียวเว้นแต่ broadcast ยังเป็น `scheduled` &nbsp;·&nbsp; **ใช้ร่วมกัน:** คอมโพเนนต์ `BroadcastPreview`, `useUnsavedChanges`, Ctrl/Cmd+S, Escape, sticky action bar ด้านล่างแบบกระจก &nbsp;·&nbsp; **UI state ที่เก็บไว้:** 7 `localStorage` key เฉพาะหน้า List

## 1. ภาพรวม

Broadcasts เป็นโมดูลสามหน้าจอแล้วตอนนี้ ไม่ใช่หน้าจอเขียนหน้าเดียวเหมือนเดิม `/broadcasts` → `BroadcastManagement` (§2) แสดง broadcast แบบ `system_all`/`bu` ทั้งหมด; `/broadcasts/new` → `BroadcastCompose` (§3) ใช้ส่งอันใหม่; `/broadcasts/:id/edit` → `BroadcastEdit` (§4) ดูได้เสมอ และแก้ schedule/วันหมดอายุ/เนื้อหาได้ตราบใดที่ยัง `scheduled` **นี่คือสามไฟล์และสาม route ที่แยกกันจริง** — Compose กับ Edit โดยเฉพาะไม่ใช้คอมโพเนนต์ร่วมกันเลย มีแค่แผง preview (`BroadcastPreview`, §3.7) และ utility validation/formatting บางส่วนเท่านั้น

องค์ประกอบมาตรฐานเกิดซ้ำทั้งใน Compose และ Edit: `useUnsavedChanges` ตั้ง guard การนำทางทันทีที่ฟิลด์ต่างจากค่าที่ save/default ไว้, Ctrl/Cmd+S save หรือส่ง, Escape reset หรือยกเลิก, error แสดงเป็นข้อความสีแดงที่ฟิลด์บวก toast และ Debug Sheet เฉพาะ dev แสดง response ล่าสุดของ API ทั้งสองใช้ sticky bottom action bar แบบกระจกสไตล์ "iOS" เดียวกัน (`.unsaved-bar`, เพิ่มเมื่อ 2026-08-31) ที่แสดงจุดบ่งชี้การเปลี่ยนแปลงที่ยังไม่ save คู่กับ Reset/Send หรือ Cancel/Save

## 2. หน้าจอ List (`BroadcastManagement`)

`PageHeader` ("Broadcasts") พร้อม subtitle บวกข้อความบอกชัดเจน — *"ประกาศที่ส่งถึงผู้ใช้ที่ระบุเจาะจงจะไม่แสดงที่นี่ — ถูกบันทึกเป็นการแจ้งเตือนรายบุคคล"* — อยู่เหนือแถบสรุปสถานะที่คลิกได้, แถบค้นหา-กรอง และ `DataTable` แบบ server-side

### 2.1 Action ของ header และแถบสรุป

- **Export** (ปุ่ม outline, disable ระหว่างโหลดหรือไม่มีข้อมูล) สร้าง CSV ของแถวในหน้าปัจจุบันผ่าน `generateCSV`/`downloadCSV` คอลัมน์: Title, Message, Scope, BU Code, Severity, Status, Scheduled At, Expires At, Created At, Created By, Updated At, Updated By — **สองคอลัมน์สุดท้ายว่างเปล่าเสมอ** เพราะ API ไม่เคยส่ง `updated_at`/`updated_by` คืนมาสำหรับ broadcast row เลย ทั้งที่ฐานข้อมูลตอนนี้บันทึกทั้งสองอย่างทุกครั้งที่แก้ไข (ดู [Data Model](/th/platform/broadcasts/data-model) §5)
- **New Broadcast** (gate ด้วย `<Can permission="broadcast.send">`) นำทางไปยัง Compose
- `BroadcastSummary` render ห้าช่องที่คลิกได้ — All, Active, Scheduled, Expired, Deleted — มาจาก object `summary` ของ response list เอง (ไม่ใช่นับฝั่ง client) คลิก All/Active/Scheduled/Expired สลับ filter `status` ที่ตรงกัน; **Deleted ต่างออกไปโดยตั้งใจ** — มันสลับ `include_deleted` แทนค่า status เพราะ query param `status` รับได้แค่ `active|scheduled|expired` และแถวที่ถูกลบเข้าถึงผ่าน `include_deleted` เท่านั้น การโหลดล้มเหลว render สถานะ retry แทนแถบสรุป

### 2.2 การค้นหาและ filter

- `SearchInput` แบบ debounce (400 ms) จับคู่ title หรือ message แบบไม่สนตัวพิมพ์เล็กใหญ่ กลับไปหน้า 1 ทุกครั้งที่พิมพ์คำใหม่
- Sheet ของ **Filters** (`BroadcastFilters`) มี: ปุ่ม toggle สถานะ (Active/Scheduled/Expired, เลือกได้หลายอัน), ปุ่ม toggle scope (System/Business Unit, เลือกได้หลายอัน) และ checkbox "Show deleted broadcasts" — บวกปุ่ม "Clear all" เมื่อมี filter ใดถูกเปิดใช้งาน ปุ่ม Filters ของ header มี badge ตัวเลขนับกลุ่ม filter ที่ active อยู่ (status-any, scope-any, deleted)
- **เจ็ด `localStorage` key** เก็บ state ของหน้า List ข้ามการเข้าชม: `search_broadcasts`, `filters_broadcast_status` (JSON array), `filters_broadcast_scope` (JSON array), `filter_broadcast_deleted` (JSON boolean), `page_broadcasts`, `perpage_broadcasts`, `sort_broadcasts` (ค่าเริ่มต้น `created_at:desc`)

### 2.3 คอลัมน์

| คอลัมน์ | หมายเหตุ |
|---|---|
| Title | ลิงก์ไปยัง `/broadcasts/:id/edit`; message แสดงอยู่ด้านล่าง ตัดให้สั้นลง |
| Scope | "System" หรือ "BU · `<code>`" |
| Severity | Badge, สีอิงจาก `metadata.severity` ที่เป็นแค่ตกแต่งของผู้ส่ง (Critical→destructive, Warning→warning, Info→info, Maintenance→secondary); sort ไม่ได้ |
| Status | Badge — Active (success), Scheduled (info), Expired (secondary), Deleted (destructive) |
| Scheduled Date | `YYYY-MM-DD HH:mm`, `-` เมื่อไม่ได้กำหนดเวลา |
| Expires | รูปแบบเดียวกัน; แสดงเป็นสีอำพันเมื่อแถวเป็น `active`/`scheduled` และเหลือน้อยกว่า 24 ชั่วโมงก่อนหมดอายุ |
| Created | helper audit-columns ที่ใช้ร่วมกัน แสดงแค่ฝั่ง **Created** — **ไม่มีคอลัมน์ Updated เลย** เพราะ `BroadcastListItem` ไม่มีฟิลด์ `updated_at`/`updated_by` ให้อ่าน (การละไว้โดยตั้งใจ ตาม comment ของ source เอง เพื่อไม่ให้มีคอลัมน์ที่ว่างเปล่าตลอด) |
| Deleted Date | ปรากฏเฉพาะเมื่อ "Show deleted" เปิดอยู่ |
| Actions | dropdown ของแถว ทั้งสามรายการแสดงแบบมีเงื่อนไข |

Row action: **Edit** (`<Can permission="broadcast.update">`, ซ่อนเมื่อ `status === 'deleted'`) ลิงก์ไปยังหน้า Edit; **Expire Now** (`<Can permission="broadcast.update">`, แสดงเฉพาะเมื่อ `status === 'active'`) เปิด confirm dialog แล้วเมื่อยืนยัน จะ `PATCH` ค่า `end_at` เป็นเวลาปัจจุบัน; **Delete** (`<Can permission="broadcast.delete">`, ซ่อนเมื่อถูกลบไปแล้ว) เปิด confirm dialog แล้วเมื่อยืนยัน จะลบแบบ soft ผ่าน `DELETE` การลบหรือต่ออายุให้หมดจะ re-fetch หน้าปัจจุบันในที่เดิม (ไม่มีการนำทาง)

### 2.4 Empty state, loading, debug

Empty state (ไม่มีแถว ไม่มี error) แสดง CTA "New Broadcast" ที่ gate เหมือนปุ่มใน header การโหลดครั้งแรกแสดง skeleton เต็มตาราง; การ refetch ครั้งถัดไปจะซ้อนแถบ "Loading…" แบบจาง ๆ แทนที่จะล้างตารางทิ้ง `DevDebugSheet` (เฉพาะ dev) แสดง response ดิบของ `GET /api/notifications/broadcasts`

## 3. หน้าจอ Compose (`BroadcastCompose`)

`PageHeader` พร้อม `backTo="/broadcasts"` (ตอนนี้หน้านี้มีที่ให้กลับไปแล้ว — ต่างจากโมดูลหน้าจอเดียวก่อนปรับใหญ่ที่ไม่มีลิงก์ย้อนกลับเลย), หัวข้อ "Send Broadcast", subtitle "Push a notification to all users, specific users, or a business unit." grid สองคอลัมน์ถือการ์ด Compose และ `BroadcastPreview` แบบ sticky อยู่ทางขวา

### 3.1 Audience

แถบแท็บ `Tabs` — **All users** (Globe, `system_all`, ค่าเริ่มต้น), **Specific users** (Users, `system_users`), **Business Unit** (Building2, `bu`) สองแท็บของ system render เฉพาะเมื่อ session มี `broadcast.send` (`canSendSystem`); เพราะ route เองก็ต้องการ key เดียวกันอยู่แล้ว ผู้ใช้ทุกคนที่เข้าหน้านี้ได้จะเห็นครบทั้งสามแท็บ — gate ใน component นี้เป็น code ป้องกันที่ไปไม่ถึงจริง ตรวจสอบใหม่กับ source ปัจจุบันแล้ว การสลับแท็บสลับ section ที่มีเงื่อนไขด้านล่างแต่**ไม่ล้าง state ที่กรอกไว้ก่อนหน้า** — ดู edge case ของผู้รับเก่าตกค้างใน [Permissions](/th/platform/broadcasts/permissions) §4

- **Specific users**: `UserMultiSelect` — ค้นหาแบบ debounce 400 ms (ยิง search แบบ query ว่างตอนเปิดด้วย จึงมักมี 20 ผู้ใช้แรกปรากฏก่อนพิมพ์คำใดเลย), จับคู่ 20 อันดับแรกด้วยชื่อหรืออีเมล แต่ละอัน render เป็นชื่อทับอีเมลสีจาง (ชื่อที่แสดงคือ `firstname middlename lastname` ถอยไปใช้ `name`, `email`, แล้วสุดท้ายเป็น id ดิบ) คลิกผลลัพธ์เพิ่ม badge ที่ลบได้ (แถวที่เลือกแล้ว disable และติดป้าย "Selected"); Backspace ตอน query ว่างลบ badge ตัวสุดท้าย; Escape ปิด dropdown validation "Pick at least one recipient" ถูกล้างทันทีที่เพิ่มอันหนึ่งเข้ามา
- **Business Unit**: native select ที่โหลดครั้งเดียวผ่าน `businessUnitService.getAll({ page: 1, perpage: 100 })` — **เฉพาะ 100 BU แรก** เท่านั้นที่ถูกเสนอ — กรองเฉพาะ BU ที่ active, render เป็น `Name (CODE)`, ส่งค่า code; การโหลดล้มเหลวแสดง Retry แบบ inline

### 3.2 Message

Title (≤200 ตัวอักษร, ตัวนับแบบ live, ตัดที่ขีดจำกัดแบบ hard) และ Message (≤2000 ตัวอักษร, textarea, ตัดแบบเดียวกัน) ทั้งคู่ถูก trim ก่อน validate/submit

### 3.3 Type (ป้ายฝั่งผู้ส่งเท่านั้น)

Native select — Info (ค่าเริ่มต้น), Warning, Critical, Maintenance, **Other…** **ตัวเลือกนี้ไม่เคยถูกส่งไปยังผู้รับเลย** — มัน resolve เป็น `metadata.severity` สตริงธรรมดาที่หน้าแอดมิน List/Edit อ่านกลับมาแสดง badge ของตัวเอง; wire ไม่มีฟิลด์ `type` อีกต่อไปเลย (ดู [Data Model](/th/platform/broadcasts/data-model) §4) การเลือก Other… เผย input ของ custom type (อัพเปอร์เคสตอนพิมพ์, `[A-Z0-9_]+`, ≤50 ตัวอักษร)

### 3.4 Related Business Unit (ป้าย metadata แบบเป็นตัวเลือก)

Select ของ BU ตัวที่สองที่แยกกัน — **ไม่ใช่** ตัวเลือกผู้รับ — ที่ติดป้าย `metadata.bu_code` ให้กับ broadcast ใดก็ได้ (system หรือ BU) เพื่อจุดประสงค์อ้างอิง (เช่น การนำทางฝั่งปลายทาง) ไม่ว่าใครจะเป็นผู้รับจริง ๆ นี่เป็นของใหม่ตั้งแต่เวอร์ชันล่าสุดของหน้านี้ที่เคย document ไว้ และสับสนได้ง่ายกับ select ของ BU ที่เป็นผู้รับใน §3.1 — มันเป็นฟิลด์คนละตัวบน control คนละอันที่ไม่เกี่ยวข้องกันเลย

### 3.5 Delivery — เวลาส่ง

แถบแท็บ `Tabs` — **Send immediately** (ค่าเริ่มต้น) กับ **Schedule for later** ที่เผย input `datetime-local` เมื่อเลือกกำหนดเวลา (ต้องเป็นค่าที่ parse ได้และเป็นอนาคต)

### 3.6 Delivery — วันหมดอายุ (บังคับ)

ฟิลด์**ใหม่ที่บังคับ**: select ของ preset วันหมดอายุ — 7 วัน, 30 วัน (ค่าเริ่มต้น), 90 วัน หรือ **Custom…** (เผย input `datetime-local` ของตัวเอง) `resolveExpiryIso()` คำนวณ `end_at` จริง: จำนวนวันของ preset ถูกบวกเข้ากับเวลา*ที่กำหนดไว้ส่ง*เมื่อมีการตั้งเวลา ไม่งั้นบวกกับตอนนี้ — ดังนั้น broadcast ที่กำหนดส่งวันที่ 20 พร้อมวันหมดอายุ "7 days" จะหมดอายุวันที่ 27 ไม่ใช่วันที่ 18 (ซึ่งจะทำให้มันหมดอายุก่อนถูกส่งจริงด้วยซ้ำ) วันหมดอายุแบบกำหนดเองต้องอยู่หลังเวลากำหนดส่งที่เลือกไว้เสมอ

### 3.7 `BroadcastPreview` (ใช้ร่วมกับ Edit)

คอมโพเนนต์เดียว (`src/components/BroadcastPreview.tsx`) ที่ใช้ร่วมกันทั้ง Compose และ Edit คำนวณใหม่ทุกครั้งที่พิมพ์:

- **การ์ดการแจ้งเตือน** — แถบสีด้านซ้ายและ badge ที่ระบายสีตาม severity ที่เลือก, หัวข้อ (placeholder ตัวเอียงจนกว่าจะพิมพ์), ข้อความ (clamp ไว้ 6 บรรทัด)
- **Reaches** — "Every user in the system" (`system_all`, โทนสีเตือน + ไอคอนแจ้งเตือน), "N selected user(s)"/"No recipients picked yet" (`system_users`) หรือป้ายของ BU ที่เลือก (`bu`)
- **Delivery** — "Sends immediately" หรือ "Scheduled for `<datetime>`" บวกบรรทัด "Expires `<datetime>`" เมื่อคำนวณได้
- **คำเตือนถาวร**: *"สีและป้ายเป็นการจัดหมวดหมู่ภายในเท่านั้น — ผู้รับเห็นแค่การแจ้งเตือนแบบมาตรฐาน"* — นี่คือการยอมรับของ UI เองว่า severity เป็นแค่การตกแต่งฝั่งผู้ส่ง (ดู [Data Model](/th/platform/broadcasts/data-model) §4)

### 3.8 เส้นทางการส่ง

ปุ่ม **Send** (`<Can permission="broadcast.send">`; label เปลี่ยนเป็น **Schedule** ในโหมดกำหนดเวลา) validate ก่อน แล้วเปิด `ConfirmDialog`:

| Target mode | หัวข้อ Dialog | ปุ่ม Confirm |
|---|---|---|
| `system_all` | **Send to ALL users?** | destructive (แดง) |
| `system_users` | Send to N user(s)? | default |
| `bu` | Send to {ชื่อ BU}? (ถอยไปใช้ code) | default |

คำอธิบายของ dialog ขึ้นต้นด้วยเวลา ("Will be delivered immediately" หรือ "Scheduled for `<when>`") ตามด้วยกลุ่มผู้ชม: หัวข้อที่กำลังส่ง (`system_all`), รายชื่อผู้รับห้าคนแรกบวก "and N more" (`system_users`) หรือ "Business unit: Name (CODE)" (`bu`)

สำเร็จ: toast ("Broadcast sent"/"Broadcast scheduled for `<when>`"), form ทั้งหมด reset และ response ไปเติม Debug Sheet ล้มเหลว: error ที่ parse แล้วแสดงทั้งเป็น toast และเป็น banner ค้างในหน้า และ field error ถูก map ลงบนฟอร์ม ไม่มีการ redirect — การส่งแบบ `system_all`/`bu` ตอนนี้ปรากฏบนหน้า List; การส่งแบบ `system_users` ไม่ปรากฏ (§1)

**Reset** (ถูกกระตุ้นจาก Escape ด้วย) ล้าง form, ผู้รับ และ field error ทันที โดยไม่มี confirm dialog — การป้องกันก่อนทิ้งข้อมูลมีแค่ตอน *นำทาง* เท่านั้น ผ่าน `useUnsavedChanges` ต่างจาก bottom bar ของหน้า Edit ที่ render เฉพาะตอนกำลังแก้ไข sticky bottom bar ของ Compose **แสดงอยู่เสมอ**บนหน้านี้ เพราะ Compose ไม่มีโหมด "editing" แยกให้สลับ

## 4. หน้าจอ Edit (`BroadcastEdit`)

เข้าถึงได้จากลิงก์หัวข้อของ List หรือเมนูแถว **route ของมันต้องการแค่ `broadcast.read`** — ผู้อ่านคนไหนก็เปิดได้ เริ่มที่โหมดดูเสมอ; ปุ่ม Edit ต้องการ `broadcast.update` เพิ่มเติม

### 4.1 Loading, not-found, header

Skeleton แสดงระหว่างดึงข้อมูล id ที่ไม่พบ/ถูกลบแบบ soft-แต่เข้าถึงไม่ได้/ผิดรูปแบบ render `EmptyState` ของ `SearchX` ("Broadcast not found") พร้อมปุ่ม "Back to broadcasts" — แถวที่ถูกลบแบบ soft **ไม่ได้**ถูกจัดการแบบนี้ (§4.4) `PageHeader` แสดง `backTo="/broadcasts"`, หัวข้อปัจจุบัน, status Badge ข้าง ๆ และ `audit={normalizeAudit(rawResponse)}` สำหรับบรรทัด Created/Updated **ในทางปฏิบัติบรรทัดนี้แสดงแค่ "Created" เท่านั้น** — ไม่เคยแสดง "Updated" — เพราะ wire shape ไม่มีฟิลด์ `updated_at`/`updated_by` ให้ `normalizeAudit()` อ่าน แม้ broadcast นั้นจะถูกแก้ไขจริงก็ตาม (ดู [Data Model](/th/platform/broadcasts/data-model) §5) ปุ่ม Edit (Pencil) ปรากฏเฉพาะเมื่อยังไม่ได้แก้ไขและ `status !== 'deleted'`, gate ด้วย `<Can permission="broadcast.update">`

### 4.2 โครงการ์ด

สี่การ์ดใน grid สองคอลัมน์ แสดงเสมอ:

1. **Broadcast Info** — อ่านอย่างเดียวเสมอ: Scope ("System" หรือ "BU · `<code>`") และ Event, captioned "(System generated)" ค่า Event ที่แสดงที่นี่คือคอลัมน์ `event` ดิบ — ซึ่งเป็น `info` เสมอสำหรับทุก broadcast ที่โมดูลนี้สร้างได้ (§1 ของ [Data Model](/th/platform/broadcasts/data-model)) — ดังนั้นฟิลด์นี้จึงบอกอะไรตามชื่อเท่านั้น มันไม่เคยเปลี่ยนค่าเลย
2. **Delivery** — Scheduled At และ Expires At ทั้งสองสลับเป็น input `datetime-local` ตอนแก้ไข; Expires At มีปุ่มเพิ่มเติม +7d/+30d/+90d **แต่ไม่มี selector preset "Custom…"** — ต่างจาก dropdown-ของ-preset ของ Compose ปุ่มเพิ่มเติมของ Edit เป็นทางลัดบน input วันที่ตัวเดียวกันที่แสดงอยู่เสมอ Expires At บังคับ
3. **Content** — Title, Message และ select ของ Severity **แก้ได้ก็ต่อเมื่อ `editing` เป็น true และสถานะปัจจุบันของ broadcast เป็น `scheduled`** (`contentEditable`); ไม่งั้นทุกฟิลด์ render ผ่าน `ReadOnlyField` และตอนแก้ไข row ที่ไม่ scheduled หัวการ์ดแสดงคำเตือนชัดเจน: *"Already broadcast — content can't be edited, some recipients may have already seen it."* การพยายามส่ง `title`/`message`/`metadata` ใน PATCH อยู่ดีจะถูกปฏิเสธฝั่ง server ด้วย 400 `content_locked`
4. **Preview** — คอมโพเนนต์ `BroadcastPreview` ตัวเดียวกับ Compose (§3.7) ป้อนจาก state ของฟอร์มแบบ live; `recipientCount` เป็น 0 เสมอที่นี่เพราะ Edit ไม่เคยเปลี่ยนกลุ่มผู้รับ

### 4.3 เส้นทางการ Save

Save (ใน sticky bottom bar) disable จนกว่าจะมีอะไรเปลี่ยนแปลง เมื่อ submit `handleSubmit()` รัน client validation (title/message/วันหมดอายุบังคับตอน content แก้ได้; วันหมดอายุต้องหลังกำหนดส่ง) แล้วผ่านสอง confirmation branch ก่อน `PATCH` จริง:

- **Confirm วันหมดอายุเป็นอดีต** — ถ้า `end_at` ใหม่เป็นอดีตแล้วและ row ยังไม่ใช่ `expired`/`deleted` มาก่อน dialog เตือน *"The broadcast disappears from recipients immediately"* ก่อน submit (นี่คือวิธีต่ออายุ broadcast ที่ออกอากาศแล้วให้หมดจากหน้า Edit เอง แยกจาก action Expire Now เฉพาะของ List)
- **Confirm การเลื่อนกำหนดเวลาใหม่** — ถ้า row ปัจจุบันเป็น `active` และกำหนดเวลาใหม่ดันมันกลับไปอนาคต dialog เตือน *"The message disappears from recipients until the new time"*

Body ของ PATCH ส่งแค่**ฟิลด์ที่เปลี่ยนแปลงจริง**เท่านั้น (diff กับ snapshot ที่ save ล่าสุด ไม่ใช่ row ที่เพิ่ง fetch มา — เพราะการไป-กลับของ `datetime-local` เสียความละเอียดระดับวินาที ไม่งั้นจะดู "เปลี่ยนแปลง" ตลอด) บวก `doc_version` ที่บังคับ ถ้าไม่มีอะไรนอกจาก `doc_version` ที่จะถูกส่ง การ save จะถูกข้ามทั้งหมดพร้อม toast "No changes to save" แทนที่จะยิง PATCH เปล่าที่ยังทำให้ `doc_version` เพิ่มขึ้น 409 (`doc_version` เก่า) จะกระตุ้น toast version-conflict ที่ใช้ร่วมกันและ refetch เงียบ ๆ; ความล้มเหลวอื่นแสดง error ที่ map กับฟิลด์บวก toast

### 4.4 แถวที่ถูกลบแบบ soft ยังเปิดดูได้

ต่างจากโมดูล CRUD ส่วนใหญ่ `GET /api/notifications/broadcasts/:id` ตั้งใจยังคืน row ที่ถูกลบแบบ soft (`status: "deleted"`) แทนที่จะเป็น 404 — เพื่อให้รายการที่ถูกลบซึ่งคลิกจากประวัติของ List ยังดูได้ ปุ่ม Edit ถูกซ่อนสำหรับมัน (gate `status !== 'deleted'`) และเนื้อหาก็ถูกล็อกโดยธรรมชาติด้วย (status ไม่ใช่ `scheduled`) ทำให้ broadcast ที่ถูกลบเป็นแบบอ่านอย่างเดียวจริง ๆ ทุกที่บนหน้านี้

### 4.5 Sticky bar, shortcut, debug

`.unsaved-bar` แบบกระจกเดียวกับ Compose แสดงเฉพาะตอนกำลังแก้ไข แสดง Cancel/Save Changes Ctrl/Cmd+S save (เฉพาะตอนกำลังแก้ไขและยังไม่ save อยู่); Escape ยกเลิกการแก้ไข (เฉพาะตอนกำลังแก้ไข) — ต่างจาก binding ของ Compose ที่ Escape reset ฟอร์มทั้งหมด Debug Sheet ที่นี่มี**สองแท็บ** — Response (payload ล่าสุดของ `GET`/`PATCH`) และ Form State (local state แบบ live) — ต่างจากแท็บเดียวของ Compose

## 5. แหล่งอ้างอิง

- `../carmen-platform/src/pages/BroadcastManagement.tsx`, `src/pages/broadcastManagement/{BroadcastSummary,BroadcastFilters,broadcastColumns}.tsx` — หน้าจอ List
- `../carmen-platform/src/pages/BroadcastCompose.tsx` — ค่าคงที่ (`TITLE_MAX`, `MESSAGE_MAX`, `TYPE_CUSTOM_RE`), `resolveSeverity`, payload builder, `validate`, หัวข้อ/คำอธิบาย confirm
- `../carmen-platform/src/pages/BroadcastEdit.tsx` — `contentEditable`, confirm dialog ของ past/reschedule, ตัวสร้าง patch แบบฟิลด์ที่เปลี่ยนเท่านั้น
- `../carmen-platform/src/components/BroadcastPreview.tsx` — `severityStyle`, `reachSummary`, คำเตือนการจัดหมวดหมู่ภายใน
- `../carmen-platform/src/utils/broadcastExpiry.ts` — `resolveExpiryIso()`, preset 7/30/90 วัน
- `../carmen-platform/src/components/UserMultiSelect.tsx` — debounce, ขนาดหน้า, การถอยไปใช้ชื่อสำรอง
- `../carmen-platform/src/services/broadcastService.ts` — `sendSystem`/`sendBu`/`getAll`/`getById`/`update`/`remove`
- `../carmen-platform/src/utils/audit.ts` — `normalizeAudit()` (รูปแบบแบน `created_by: { id, name }` ที่ broadcast ใช้ — ถูกเอ่ยชื่อตรง ๆ ใน comment ของ source ไฟล์นี้เองว่าเป็นหนึ่งใน endpoint ที่ไม่มีรูปแบบ `audit.*` แบบ nested)
- `../carmen-platform/src/utils/docVersion.ts` — `isVersionConflict`/`notifyVersionConflict`/`getDocVersion`
- `../carmen-platform/src/components/KeyboardShortcuts.tsx`, `src/hooks/useUnsavedChanges.ts` — shortcut และ navigation guard
- `../carmen-platform/src/App.tsx` (สาม route), `src/components/nav/platformNav.ts` (รายการ nav "Broadcasts")

**Cross-links:** [หน้าแรก Broadcasts](/th/platform/broadcasts) &nbsp;·&nbsp; [Data Model](/th/platform/broadcasts/data-model) &nbsp;·&nbsp; [Permissions](/th/platform/broadcasts/permissions)
