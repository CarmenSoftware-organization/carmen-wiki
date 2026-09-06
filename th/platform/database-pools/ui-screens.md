---
title: พูลฐานข้อมูล — หน้าจอ UI (UI Screens)
description: หน้ารายการของ DatabasePoolManagement ที่ยุบทุกแถวเหลือ DSN เดียวพร้อมปุ่มคัดลอก และหน้าบันทึก/ฟอร์มของ DatabasePoolEdit — รวมถึงช่องรหัสผ่านที่มาสก์และไม่มีทางเปิดเผยค่าจริง
published: true
date: '2026-09-06T21:00:00.000Z'
tags: book/platform, database-pools, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# พูลฐานข้อมูล — หน้าจอ UI (UI Screens)

> **หน้าจอ:** `DatabasePoolManagement` (รายการ, `/platform/database-pools`) &nbsp;·&nbsp; `DatabasePoolEdit` — component เดียวทั้งสร้าง (`/platform/database-pools/new`) และแก้ไข (`/platform/database-pools/:id/edit`) &nbsp;·&nbsp; **ไม่มีแท็บ ไม่มี wizard** — การ์ดเดียวทั้งโหมดสร้างและแก้ไข &nbsp;·&nbsp; **Dialog:** ยืนยันการลบ pool &nbsp;·&nbsp; **สถานะที่ persist ใน UI:** 5 key `localStorage` บนหน้ารายการ (search/filters/page/perpage/sort); หน้าแก้ไขไม่ persist อะไรเลย &nbsp;·&nbsp; **Concurrency:** optimistic lock `doc_version` จำเป็นต้องส่งทุกครั้งที่บันทึก &nbsp;·&nbsp; **ภาพหน้าจอ:** เลื่อนออกไปตามแผน — ยังไม่มี asset ภาพหน้าจอสำหรับโมดูลนี้

## 1. ภาพรวม

โมดูลนี้มีสองหน้าจอและไม่มีสถานะระหว่างกลางนอกเหนือจากกำลังโหลด/ไม่พบข้อมูล/error ต่างจากหน้าแก้ไขแบบหลายแท็บหลายการ์ดที่อื่นในวิกินี้ ([Business Units](/th/platform/business-units/ui-screens), [Clusters](/th/platform/clusters/ui-screens)) `DatabasePoolManagement.tsx` (`../carmen-platform/src/pages/DatabasePoolManagement.tsx`, 467 บรรทัด) เป็น `DataTable` แบบแบ่งหน้าฝั่ง server มาตรฐาน `DatabasePoolEdit.tsx` (`../carmen-platform/src/pages/DatabasePoolEdit.tsx`, 672 บรรทัด) เป็นทั้งฟอร์มสร้างใหม่และหน้าแก้ไขระเบียนเดียวในตัวเดียวกัน ตามรูปแบบสลับโหมดอ่าน/แก้ไขที่ SPA นี้ใช้ที่อื่น แต่ render เป็นบันทึกแบบมีป้ายกำกับธรรมดา (`RecordRow`) ในโหมดอ่าน ไม่ใช่ฟอร์มที่มีช่องกรอกถูก disable

## 2. `DatabasePoolManagement` — หน้ารายการ (`/platform/database-pools`)

**คอลัมน์** (`columns`, `DatabasePoolManagement.tsx:200-295`):

| คอลัมน์ | เนื้อหา |
|---|---|
| Connection (`id: 'host'`, เรียงตาม `host`) | DSN ที่ประกอบแล้ว (`username@host:port/database`, `poolDsn()`) เป็นลิงก์ไปหน้าแก้ไข pool ตัวหนังสือแบบ monospace พร้อมปุ่มคัดลอกอยู่ข้าง ๆ ใต้ลงมาคือ `name` ของ pool (แสดงก็ต่อเมื่อ `!isDerivedName()` — ดู [Data Model](/th/platform/database-pools/data-model) §2) ใต้ลงมาอีกคือ `note` เมื่อมีค่า |
| Status | `is_active` แสดงเป็น Badge (`success`/`secondary`) |
| Created / Updated | `auditColumns()` ที่แชร์กันมาตรฐาน |
| Actions | เมนู dropdown `MoreHorizontal` (Edit, Delete) ครอบทั้งหมดด้วย `<Can permission="database_pool.manage">` — session ที่มีแค่สิทธิ์อ่านจะไม่เห็นเนื้อหาคอลัมน์ actions เลย ไม่ใช่เห็นแบบ disable |

`id` ของคอลัมน์เรียงลำดับคือ `'host'` ตรง ๆ ไม่ใช่ `'connection'` — ตาม comment ของโค้ดเอง การเรียงแบบนี้จัดกลุ่ม pool ตามเครื่องจริง ซึ่งเป็นสิ่งที่ operator ต้องการจากคอลัมน์นี้จริง ๆ และ `'connection'` ก็ไม่ใช่ฟิลด์ backend จริงที่จะเรียงตามได้อยู่แล้ว

**การค้นหา** ค้นใน `name`/`host`/`database` (`defaultSearchFields` ยืนยันแล้วว่าตรงกับ `defaultSearchFields` ของ backend เองใน `database-pool.service.ts:80` เป๊ะ — comment ของ frontend ที่อ้างไฟล์และบรรทัดนี้ถูกต้อง ยืนยันจากการอ่านทั้งสองไฟล์) **ตัวกรอง**: panel แบบ Sheet มี toggle chip Active/Inactive เลือกได้ทั้งสองพร้อมกันในหน้าจอ แต่ `buildAdvance()` จะสร้าง filter `is_active` ฝั่ง server ก็ต่อเมื่อเลือก**อย่างใดอย่างหนึ่งเท่านั้น** (`filters.length === 1`) — ไม่เลือกเลยหรือเลือกทั้งสองอย่างจะได้ผลเหมือนกันคือ "ไม่มี filter" แสดง pool ทุกตัวไม่ว่าสถานะใด

**Export CSV** (`handleExport`) — 12 คอลัมน์: `dsn` (ประกอบขึ้น ไม่ได้เก็บไว้จริง), `name`, `host`, `port`, `database`, `username`, `is_active`, `note` ตามด้วยฟิลด์ audit สี่ตัว (`created_at`/`created_by`/`updated_at`/`updated_by`) **`password` และ `description` ไม่ถูก export**

**ปุ่มคัดลอก DSN** ปรากฏทั้งในเซลล์ Connection ที่นี่และบนหน้าแก้ไข (§3–4) คัดลอกสตริง DSN ที่ประกอบแล้วเป๊ะ ๆ ผ่าน Clipboard API การเขียนคลิปบอร์ดที่ถูกปฏิเสธ (ไม่ได้รับสิทธิ์ หรืออยู่ในหน้าที่ไม่ใช่ secure context) จะขึ้น error toast แทนที่จะล้มเหลวแบบเงียบ ๆ ตาม comment ของ handler เองเรื่องการไม่ปล่อยให้ผู้ใช้เชื่อว่าคัดลอกสำเร็จทั้งที่ไม่สำเร็จ

**ปุ่มบน header:** Export CSV (disable ขณะโหลดหรือรายการว่าง) และปุ่ม Add Pool ที่ gate ด้วย `<Can permission="database_pool.manage">` gate เดียวกันครอบปุ่มที่เทียบเท่ากันบน empty state

**การยืนยันลบ** `ConfirmDialog` บน action Delete ของแถว เมื่อยืนยันแล้วเจอ 409 `DATABASE_POOL_IN_USE` จะแสดงข้อความดิบจาก backend (ระบุ business unit ที่บล็อกอยู่ด้วย `code`) แทนที่จะผ่าน error-detail redactor ทั่วไป ตาม comment ของ handler เองเรื่องการไม่กลืนรายชื่อ BU นั้นไปกับ "Please try again later." ทั่วไปตอน production

**เครื่องมือสำหรับ dev:** `DevDebugSheet` แสดง response ดิบของ `GET /api-system/platform/database-pools` ตรงกับรูปแบบที่หน้ารายการอื่นในวิกินี้ใช้

## 3. `DatabasePoolEdit` — โหมดสร้างใหม่ (`/platform/database-pools/new`)

หน้าเปิดมาในโหมดแก้ไขทันที (`editing = isNew`) — ไม่มีขั้นตอนแยก "กด Edit ก่อนถึงจะเริ่มได้" สำหรับ pool ใหม่ล้วน ดู [หน้าหลัก](/th/platform/database-pools) §4 ว่า permission อะไรบ้างที่ gate เรื่องนี้ไว้ และอะไรที่ไม่ gate

**ฟิลด์** ทั้งหมดอยู่บนการ์ดเดียว กริดสองคอลัมน์แบบ responsive:

| ฟิลด์ | จำเป็น | หมายเหตุ |
|---|---|---|
| Name | ใช่ | ข้อความธรรมดา |
| Status (checkbox Active) | — | ติ๊กไว้โดยดีฟอลต์ |
| Description | ไม่ | textarea หลายบรรทัด |
| Host | ใช่ | ข้อความธรรมดา |
| Port | ใช่ | ช่องกรอกตัวเลข ตรวจฝั่ง client 1–65535 (`isValidPort()`) — ไม่มี case `validateField` ที่แชร์กันสำหรับ `port` การตรวจนี้จึงอยู่ในหน้านี้เอง แทนที่จะไปชนกับ case ชื่อเดียวกันที่ไม่เกี่ยวข้องกันที่อื่น |
| Database | ใช่ | ข้อความธรรมดา |
| Username | ใช่ | ข้อความธรรมดา — **ไม่** ถูกตรวจว่าเป็นอีเมล หน้านี้จงใจไม่ใช้ case `validateField('username')` ที่แชร์กันซึ่งเขียนไว้สำหรับโมดูล Users เพราะนี่คือ login ฐานข้อมูลดิบ |
| Password | ใช่ (เฉพาะตอนสร้าง) | ช่องกรอกที่มาสก์ พร้อมปุ่มสลับแสดง/ซ่อน (`Eye`/`EyeOff`) |
| Note | ไม่ | textarea หลายบรรทัด |

เมื่อ submit สำเร็จ จะขึ้น toast แล้ว navigate (`replace: true`) ไปหน้าแก้ไขของ pool ใหม่นั้นเอง — หน้าไม่ค้างอยู่ที่ `/new` หลังสำเร็จ 409 ที่มีข้อความ `DATABASE_POOL_NAME_EXISTS` จาก backend จะแสดงเป็น error ระดับฟิลด์ตรงใต้ Name โดยใช้ข้อความของ backend เอง (ที่ระบุชื่อฟิลด์) แทนข้อความทั่วไปที่ถูก redact

## 4. `DatabasePoolEdit` — โหมดแก้ไข (`/platform/database-pools/:id/edit`)

**โหมดอ่าน** (ค่าเริ่มต้นตอนโหลด) render เป็นบันทึกมีป้ายกำกับ ไม่ใช่ฟอร์ม:

- DSN ที่ประกอบแล้วเป็นข้อความใหญ่เด่นของหน้า (สตริงเดียวกับที่แถวรายการแสดง) พร้อมปุ่มคัดลอกของตัวเอง
- Badge Active/Inactive
- `description` ถ้ามีค่า (`RecordRow`)
- `note` ถ้ามีค่า — จงใจวางไว้**ก่อน**แถวรหัสผ่าน ไม่ใช่หลัง เพื่อไม่ให้สัญญาณ "pool นี้ถูกสร้างอัตโนมัติ" กลายเป็นสิ่งสุดท้ายบนหน้า
- แถวรหัสผ่านที่ไม่เคยแสดงค่าเลย — มีแค่ป้ายตายตัว "เก็บไว้แล้ว ซ่อนอยู่" (`passwordStoredHidden`) เพราะ API ไม่เคยส่งค่าจริงกลับมาให้เปิดดู

การคลิก **Edit** (gate ด้วย `<Can permission="database_pool.manage">`) สลับไปเป็นฟิลด์ฟอร์มเดียวกับ §3 เติมค่ามาจากระเบียนที่โหลดไว้ยกเว้นรหัสผ่านที่เริ่มว่างเปล่าเสมอ — ปล่อยว่างไว้ตอนบันทึกจะคงค่าเดิมไว้ (ดู [Data Model](/th/platform/database-pools/data-model) §4) คำแนะนำใต้ช่องรหัสผ่าน ("เว้นว่างเพื่อคงรหัสผ่านปัจจุบัน") จะปรากฏเฉพาะในโหมดแก้ไข ไม่ปรากฏในโหมดสร้าง

**Header** แสดง audit trail ของ pool (`normalizeAudit()`) ข้าง ๆ หัวเรื่อง หัวเรื่องเองคือ `name` ของ pool ในโหมดแก้ไข แต่ในโหมด**อ่าน**จะถอยไปใช้หัวเรื่องทั่วไป "Database Pool" ทุกครั้งที่ `isDerivedName()` เป็นจริง — เพื่อไม่ให้พิมพ์สตริงรูปแบบ DSN เดียวกันทั้งเป็นหัวเรื่องและเป็นบรรทัดที่อยู่ที่อยู่ใต้มันโดยตรง

**แถบบันทึก/ยกเลิก** แถบล่างแบบ fixed ปรากฏเฉพาะขณะแก้ไข แสดง "มีการเปลี่ยนแปลงที่ยังไม่บันทึก" หรือ "ไม่มีการเปลี่ยนแปลง" พร้อมปุ่ม Cancel/Save — รูปแบบ `unsaved-bar` เดียวกับที่หน้าแก้ไขอื่นในวิกินี้ใช้ ปุ่ม Save ถูกครอบด้วย `<Can permission="database_pool.manage">`; `Ctrl/Cmd+S` เรียก path การ submit เดียวกันผ่าน `useGlobalShortcuts` และ `handleSubmit` เองก็เช็ค `hasPermission('database_pool.manage')` ก่อนทำอะไรเลย (ดู [หน้าหลัก](/th/platform/database-pools) §4 ว่าทำไมการเช็คซ้ำนี้ถึงสำคัญ)

**การจัดการ error ตอนบันทึก:** pool ที่ถูกลบไปจากที่อื่น (404) จะสลับหน้าไปเป็นสถานะไม่พบข้อมูล แทนที่จะแสดง banner ทับข้อมูลเก่า; `doc_version` ที่ค้าง (409 version conflict) จะแสดง toast ความขัดแย้งที่แชร์กันแล้ว reload ระเบียนใหม่; 409 ชื่อซ้ำจะแสดงตรงที่ฟิลด์ Name; error validation อื่นใดจะเติม error ต่อฟิลด์จาก field map ของ backend เมื่อมี

**สถานะไม่พบข้อมูล** การ์ด `EmptyState` เฉพาะ ("ไม่พบ pool") พร้อมปุ่มกลับไปหน้ารายการ — render แทนหน้าแก้ไขทุกครั้งที่ id ไม่ resolve ไม่ว่าจะจาก URL ผิดหรือ pool ถูกลบในอีกแท็บหนึ่งระหว่างที่ navigate มา

**เครื่องมือสำหรับ dev:** แท็บ `DevDebugSheet` แสดง response ดิบของ `GET /api-system/platform/database-pools/:id` (หรือ placeholder ในโหมดสร้าง เพราะยังไม่มีอะไรให้ fetch)

## 5. Dialog

### 5.1 ยืนยันการลบ pool (หน้ารายการเท่านั้น)

`ConfirmDialog` ที่ trigger จากเมนู action ของแถว การยืนยันจะเรียก `DELETE`; 409 `DATABASE_POOL_IN_USE` ที่เกิดขึ้น (§2) เป็น error path เดียวที่ dialog นี้ต้องแสดง เพราะ pool ที่ไม่มี business unit ผูกอยู่จะสำเร็จเสมอ

ไม่มี dialog บนหน้าแก้ไขที่เทียบเท่ากับ "ยืนยันการเปลี่ยน pool/schema" ของ Business Units ([Business Units — UI Screens](/th/platform/business-units/ui-screens) §5.5) — การยืนยันแบบนั้นเป็นของฝั่ง*ผู้บริโภค*ของ pool (business unit ที่กำลังเปลี่ยนว่าจะชี้ไป pool ไหน) ไม่ใช่ของโมดูลนี้ ซึ่งแก้ไขแค่ตัวระเบียน pool เอง

## 6. สถานะที่ persist ใน UI

หน้ารายการ persist ห้า key `localStorage` ทั้งหมดขึ้นต้นด้วย `*_database_pools(_database_pool)`: `search_database_pools`, `filters_database_pools`, `page_database_pools`, `perpage_database_pool` (เอกพจน์ ต่างจากพี่น้องตัวอื่น — ยืนยันตามที่เขียนไว้จริงใน source ไม่ใช่การพิมพ์ผิดที่หน้านี้ใส่เพิ่มเข้ามาเอง) และ `sort_database_pools` การเรียงเริ่มต้นคือ `created_at:desc` — ตาม comment ของโค้ดเอง `updated_at` ถูกปฏิเสธไม่ให้เป็นค่าเริ่มต้นเพราะ pool ส่วนใหญ่ไม่เคยถูกแก้ไขหลังสร้าง ซึ่งจะทำให้ลำดับรายการดูสุ่มตอนเปิดหน้าครั้งแรก

หน้าแก้ไขไม่ persist อะไรลง `localStorage` เลย สถานะฝั่ง client เดียวที่รอดข้ามการ re-render คือ diff ของการเปลี่ยนแปลงที่ยังไม่บันทึกใน memory (`formData` เทียบกับ `savedFormData`) ควบคุมโดย hook ที่แชร์กัน `useUnsavedChanges` (prompt "ออกจากหน้านี้หรือไม่" ของเบราว์เซอร์เมื่อมีการแก้ไขที่ยังไม่บันทึก)

## 7. แหล่งอ้างอิง

- `../carmen-platform/src/pages/DatabasePoolManagement.tsx` — อ่านครบ (467 บรรทัด)
- `../carmen-platform/src/pages/DatabasePoolEdit.tsx` — อ่านครบ (672 บรรทัด)
- `../carmen-platform/src/services/databasePoolService.ts` — REST client
- `../carmen-platform/src/utils/databasePool.ts` — `poolDsn()`, `isDerivedName()`
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/database-pool.service.ts:80` — `defaultSearchFields` ตรวจไขว้กับ comment ของ frontend ที่อ้างถึง
- `../carmen-platform-e2e/tests/` — ตรวจดูตรง ๆ **ไม่มีโฟลเดอร์ `database-pools`** ยืนยันคำกล่าวอ้าง "ไม่มี e2e suite" ของ[หน้าหลัก](/th/platform/database-pools) §1
- ไม่มี asset ภาพหน้าจอสำหรับโมดูลนี้ (`assets/screenshots/platform/database-pools/`) — เลื่อนออกไปตามแผน ตรงกับทุกโมดูลที่เขียนใหม่ในชุดนี้
