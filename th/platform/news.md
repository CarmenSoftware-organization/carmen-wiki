---
title: ข่าวสาร (News)
description: ภาพรวมโมดูล News — ประกาศแบบ markdown พร้อมรูปภาพแบบ optional, tags, lifecycle ของสถานะ draft → published → archived, การกำหนดเป้าหมายแบบ global หรือราย BU และ bulk publish/archive/delete เขียนใน admin SPA และส่งมอบผ่าน public endpoint แบบ anonymous
published: true
date: 2026-09-05T00:00:00.000Z
tags: platform/news, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:45:00.000Z
---

# ข่าวสาร (News)

โมดูล **News** จัดการประกาศและบทความสำหรับผู้ใช้แพลตฟอร์ม: เนื้อหา markdown, รูปภาพแบบ optional, URL ของแหล่งที่มา, tags แบบอิสระ และ lifecycle ของสถานะ `draft → published → archived` กำหนดเป้าหมายแบบ global หรือไปยังรายการ business unit แบบระบุชัด Platform admin SPA คือ**ฝั่งผู้เขียน (authoring)**; การส่งมอบไปยังผู้ใช้ปลายทางเกิดขึ้นผ่านคู่ **public endpoint แบบ anonymous** ที่แยกต่างหาก (`/api/public/news`) ซึ่งเปิดเผยเฉพาะบทความที่ published, ไม่ถูกลบ และเวลาเผยแพร่มาถึงแล้วเท่านั้น (ยังไม่มี client ใน repo ใดบริโภค endpoint เหล่านี้ — ดู §2)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เขียนและจัดการประกาศ — `contents` แบบ markdown, รูปภาพแบบ optional (อัพโหลด multipart → file token ของ MinIO → presigned `image_url`), tags แบบอิสระ, lifecycle ของสถานะพร้อม `published_at` ที่ server ประทับให้, การกำหนดเป้าหมายแบบ global หรือราย BU, bulk publish/archive/delete &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA, โมดูล news ของ backend-gateway และ news service ของ micro-cluster &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_news` (ตารางเดียว, `business_unit_ids` และ `tags` แบบ JSONB, `doc_version` เป็น optimistic lock, ไม่มีความสัมพันธ์ FK) &nbsp;·&nbsp; **Endpoint:** `/api/news` (CRUD แบบ authenticated — สังเกตว่าเป็น `/api` **ไม่ใช่** `/api-system`), `/api/news/tags` (รายการ tag ที่ไม่ซ้ำ), `/api/news/summary` (ค่าสรุปห้องข่าวแบบไม่กรอง เพิ่มเมื่อ 2026-08-24) และ `/api/public/news` (อ่านแบบ anonymous) &nbsp;·&nbsp; **การบังคับใช้ฝั่ง server:** `POST`/`PUT`/`DELETE` ตรวจสอบ permission `news.create`/`.update`/`.delete` ของผู้เรียกเอง (`PlatformPermissionGuard` เพิ่มเมื่อ 2026-08-20); route `GET` ทั้งสี่ตรวจสอบเฉพาะ allowlist ของ `x-app-id` ของ application ที่เรียก โดยตั้งใจ เพื่อให้ผู้ใช้ระดับ tenant ของแอปมือถือ — ซึ่งไม่มี role ระดับแพลตฟอร์มเลย — ยังอ่านข่าวได้ &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูลนี้ทำตามรูปแบบสองหน้าจอมาตรฐานของ SPA:

- **`/news` → `NewsManagement`** — `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce (title/contents), filter สถานะ + tag แบบ Sheet, ส่งออก CSV, การเลือก row แบบ checkbox พร้อม bulk Publish/Archive/Delete และจดจำสถานะ UI ใน `localStorage` เหนือตารางมีการ์ด **`NewsroomSummary`**: แถบ pipeline Draft → Published → Archived บวก tile "Latest" ของบทความที่เพิ่ง publish ล่าสุด พร้อม thumbnail ปกและ "เวลาที่ผ่านมา" แบบสัมพัทธ์ คอลัมน์เฉพาะของโมดูล: **thumbnail รูปภาพ**, คอลัมน์ **Target** (Global เทียบกับ "N BUs"), คอลัมน์ **Tags** และคอลัมน์ timestamp **Published**/**Updated**
- **`/news/new` และ `/news/:id/edit` → `NewsEdit`** — layout แบบ masthead + สองคอลัมน์ แทนที่การ์ดสี่ใบแบบเดิม: การ์ด `NewsMasthead` (รูปปก, badge สถานะ/reach/state, หัวข้อเอง) อยู่เหนือการ์ด **Article** (เนื้อหา markdown, source URL, tags) และ rail **Publish** แบบ sticky (สถานะ, การกำหนดเป้าหมาย BU, published-at) บวกการ์ด **History** สำหรับเรคคอร์ดที่มีอยู่แล้ว มี action bar แบบ sticky ด้านล่างพร้อม Cancel/Save โหมด create แก้ไขได้ทันที; route edit เปิดแบบ read-only อยู่หลัง toggle Edit องค์ประกอบที่เป็นเอกลักษณ์คือ **MarkdownEditor** (แท็บ Write/Preview), โซน drag-and-drop **ImageUpload** (ตอนนี้ฝังอยู่ใน masthead) และ **ChipInput** สำหรับ tags พร้อม autocomplete

เรคคอร์ดข่าวหนึ่งตัวคือหนึ่ง row ใน `tb_news`: `title` (จำเป็น), `contents` (markdown), `url` (ลิงก์แหล่งที่มาแบบ optional), รูปภาพที่จัดเก็บเป็น **file token** ของ MinIO (`image_file_token` — API จะ resolve มันเป็น presigned `image_url` และไม่เคยเปิดเผยตัว token), `tags` (array ของ string แบบ JSONB), `status`, `published_at`, `business_unit_ids` (array แบบ JSONB; ว่าง = มองเห็นได้ทุก business unit) และ `doc_version` (ตัวนับ optimistic-lock) ดู [Data Model](/th/platform/news/data-model) สำหรับตาราง field ฉบับเต็มและ [UI Screens](/th/platform/news/ui-screens) สำหรับ walkthrough ของหน้าจอ

ทั้งสองหน้าจอยังมีฟีเจอร์ **Activity Trail** ข้ามโมดูลที่เพิ่มเข้ามาทั้งแพลตฟอร์ม: action **View History** (dropdown action ของ row ในหน้า list; ที่หน้า edit อยู่ในแถว header บนสุดข้าง back link) ถูก gate ด้วย `activity_log.read` พร้อม sentinel `clusterId={PLATFORM_SCOPED_RECORD}` เพราะบทความหนึ่งชิ้นกำหนดเป้าหมายได้หลาย business unit จึงไม่มี cluster เดียวให้ผูก (ดู [Permissions](/th/platform/news/permissions)) การบันทึกเริ่มตั้งแต่ 2026-08-31 (`AUDIT_RECORDING_STARTED_ON_PHASE_2`) บทความที่สร้างก่อนหน้านั้นจึงมี timeline ว่างเปล่า ไม่ได้หมายความว่าไม่เคยมีการแก้ไข ตั้งแต่ 2026-08-24 การ์ด `NewsroomSummary` ก็อ่านจาก endpoint `GET /api/news/summary` แบบไม่กรองโดยเฉพาะแล้ว แทนที่การกวาดทั้งตารางฝั่ง client แบบเดิม (ดู [Data Model](/th/platform/news/data-model) §6)

ส่วนที่เหลือทั้งหมดเป็นองค์ประกอบมาตรฐานของหน้า Management: `TableSkeleton`, `ListEmptyState` ที่รับรู้ filter, toast feedback, navigation guard `useUnsavedChanges`, คีย์ลัด global (Ctrl/Cmd+S save, Escape cancel, Ctrl/Cmd+K โฟกัสช่องค้นหา) และ Debug Sheet เฉพาะ dev

## 2. บริบททางธุรกิจ

News มีไว้เพื่อสื่อสารข้อมูลอัพเดทเชิงปฏิบัติการ — การเปลี่ยนนโยบาย, ประกาศปิดปรับปรุงระบบ, ประกาศของกลุ่มโรงแรม — ไปยังพนักงานของ business unit หนึ่งแห่ง หลายแห่ง หรือทั้งหมด โมดูลแบ่งออกเป็นสองส่วนอย่างชัดเจนโดยมี security model ต่างกัน:

- **Authoring** (SPA นี้ + `/api/news`): CRUD เต็มรูปแบบ ถูก gate ด้วย key `news.*` ของ RBAC สำหรับมนุษย์ และ grant ของ `AppIdGuard` สำหรับ application ที่เรียก — แต่ไม่เหมือนกันทุก route `POST`/`PUT`/`DELETE` ตรวจสอบ permission `news.create`/`.update`/`.delete` ของผู้เรียกเองที่ฝั่ง server (`PlatformPermissionGuard` เพิ่มเมื่อ 2026-08-20 — ก่อนแก้ API ยอมรับผู้เรียกที่ authenticated และ app-id ผ่าน โดยไม่สนใจ RBAC เลย) route `GET` ทั้งสี่ (list, detail, tags, summary) ตั้งใจไม่มีการตรวจสอบแบบนี้: DB แสดงว่า application `mobile-app` ถือ `news.findAll`/`news.findOne` อยู่ใน allowlist และให้บริการผู้ใช้ระดับ tenant ที่ไม่มี role ระดับแพลตฟอร์มเลย การเพิ่ม `news.read` ที่นั่นจะทำให้ผู้ใช้มือถือทุกคนอ่านข่าวไม่ได้ — `news.read` จึงยังเป็นเพียง key สำหรับ "ซ่อนเมนู admin" (ดู [Permissions](/th/platform/news/permissions) §1) ผู้เขียนเห็นทุกเรคคอร์ดไม่ว่าสถานะใด รวมถึง row ที่เป็น draft และ archived
- **Delivery** (`/api/public/news` + `/api/public/news/:id`): **anonymous** — controller ไม่มี authentication guard ใด ๆ เลย มันเสิร์ฟเฉพาะ row ที่ `status = published`, ไม่ถูก soft-delete **และ** `published_at <= now()` เมื่อไม่มี query parameter `bu_id` จะคืนเฉพาะข่าว global; เมื่อมี `bu_id` จะคืนข่าว global บวกข่าวที่กำหนดเป้าหมายไปยัง BU นั้น บทความที่เป็น draft, archived, ถูกลบ หรือลงวันที่อนาคตตอบกลับ 404 — response เดียวกับ id ที่ไม่รู้จัก การมีอยู่ของเรคคอร์ดจึงไม่เคยรั่วไหล

filter `published_at <= now()` หมายความว่าผู้เขียนสามารถ**กำหนดเวลาเผยแพร่ (schedule)** บทความได้โดย publish พร้อม timestamp อนาคตผ่าน API (ตัว SPA เองไม่เคยส่ง `published_at` — ดู §3) ยังไม่มี client ใน repo ใด render public feed: web frontend ของ Carmen Inventory ไม่มี surface สำหรับข่าว ให้ปฏิบัติกับ public endpoint เป็นสัญญาการส่งมอบ (delivery contract) ของโมดูล

## 3. แนวคิดสำคัญ

- **Lifecycle ของสถานะ** — `enum_news_status`: `draft` (ค่าเริ่มต้น) → `published` → `archived` select ของสถานะเป็นแบบอิสระ: ค่าใดก็ย้ายไปค่าอื่นใดได้; ไม่มีอะไรใน SPA หรือ backend ห้ามการ un-publish กลับเป็น draft หรือการชุบชีวิต row ที่ archived
- **`published_at` ถูก server ประทับให้ ครั้งเดียว** ตอน create ด้วย `status = published` และตอน transition เข้าสู่ `published` ครั้งแรก micro-cluster จะประทับ `published_at = now()` — แต่เฉพาะเมื่อเรคคอร์ดไม่เคยมีเวลาเผยแพร่มาก่อนเท่านั้น การย้ายกลับเป็น draft หรือ archived **ไม่**เคลียร์ค่านี้ และการ re-publish ภายหลังคงค่าประทับ*เดิม*ไว้ caller ของ API สามารถ set หรือเคลียร์ `published_at` แบบระบุชัดได้; SPA ไม่เคยส่ง field นี้และ render มันแบบ read-only (helper text: Set automatically when status becomes "Published".)
- **Global เทียบกับการกำหนดเป้าหมายราย BU** — `business_unit_ids` คือ array แบบ JSONB ของ UUID ของ BU บนตัว row เอง ไม่ใช่ join table array ว่าง (ค่า default ของคอลัมน์) = global SPA model สิ่งนี้เป็น checkbox "Visible to all business units" ซึ่งเมื่อไม่ติ๊กจะต้องมี BU อย่างน้อยหนึ่งตัวใน multi-select backend ตรวจสอบทุก id กับ row ของ `tb_business_unit` ที่ live อยู่ตอนเขียน แต่จัดเก็บแบบไม่มี FK — ดู [Data Model](/th/platform/news/data-model) §3
- **Tags** — `tags` คือ array ของ string แบบ JSONB แก้ไขผ่าน `ChipInput` (Enter/comma/Tab เพื่อ commit chip หนึ่งตัว; Backspace ตอน draft ว่างจะลบตัวสุดท้าย) พร้อมคำแนะนำ autocomplete จาก `GET /api/news/tags` (tag ที่ไม่ซ้ำทั่วทั้งข่าวที่ไม่ถูกลบ) ทั้ง SPA และ micro-cluster ทำ lowercase, trim และ de-duplicate รายการ; backend ยังจำกัด tag ไว้ที่ 20 ตัวต่อบทความและ 40 ตัวอักษรต่อ tag และแยก element ที่มี comma อยู่ข้างใน (ป้องกัน tag ที่จัดเก็บไว้ทำให้ comma delimiter ของ chip input เองเสียหาย) คอลัมน์ Tags ในหน้า list แสดง badge สูงสุด 3 ตัวบวก overflow "+N"; Filters Sheet จะมีกลุ่ม Tags เพิ่มขึ้นเมื่อมี tag อย่างน้อยหนึ่งตัวอยู่แล้ว
- **Optimistic locking (`doc_version`)** — ทุก `PUT /api/news/:id` ต้องมี `doc_version` ที่ client อ่านมาล่าสุด; backend ปฏิเสธเมื่อไม่มี version มา (`COMMON_DOC_VERSION_REQUIRED`) และปฏิเสธ version ที่ล้าสมัยด้วย 409 conflict helper `getDocVersion`/`isVersionConflict` ของ SPA แสดงสิ่งนี้เป็น "This record was changed by someone else" ทิ้งการเลือกรูปที่ค้างอยู่ และ refetch เรคคอร์ด — กลไกเดียวกับที่ใช้ในโมดูลอื่น ๆ ของ Platform book (clusters, business units, users, applications, RBAC)
- **เนื้อหาแบบ markdown** — `contents` คือ string แบบ markdown ที่แก้ไขในแท็บ Write/Preview (`react-markdown` + `remark-gfm` สำหรับ preview) backend จัดเก็บมันแบบ verbatim; กฎการ render เป็นเรื่องของ consumer แต่ละราย
- **อัพโหลดรูปผ่าน multipart** — create/update รับ `multipart/form-data` โดย binary อยู่ใน field `image` (ภายใต้ multipart, `business_unit_ids` และ `tags` เดินทางเป็น field string ที่ encode เป็น JSON) gateway อัพโหลดไฟล์ไปยัง micro-file (MinIO), จัดเก็บ token ที่คืนมาใน `image_file_token` และทุกการอ่านจะสลับ token เป็น **presigned URL (หมดอายุ 1 ชั่วโมง)** เปิดเผยเป็น `image_url` การแทนที่รูปจะลบไฟล์เก่า; การลบข่าวจะลบไฟล์ของมันแบบ best-effort การเขียนแบบ JSON (ไม่ใช่ multipart) จะไม่แตะรูปเลย — ซึ่งหมายความว่า SPA **ไม่มีวิธีลบรูปออกโดยไม่แทนที่มัน**ด้วย
- **Soft delete และตอนนี้ admin list filter มันแล้ว (ยืนยันว่าแก้แล้ว)** — `DELETE /api/news/:id` ตั้ง `deleted_at`/`deleted_by_id` interceptor `EnrichAuditUsers` ของ gateway ยุบคอลัมน์ audit แบบแบนหกตัวเป็น object `audit: { created, updated, deleted }` แบบซ้อน ต่างจากสถานะที่ document ไว้ตอน sync ครั้งก่อน **ตอนนี้ query ของ admin list ผสาน `deleted_at: null` เข้าไปใน `where` clause แล้ว** (`findAll` ของ micro-cluster เหมือนกับที่แก้ใน Applications และ Business Units) — ข่าวที่ถูก soft-delete ไม่ปรากฏใน `GET /api/news` อีกต่อไปเลย การ filter คู่ฝั่ง client ของ SPA (`deleted_at`/`audit.deleted.at`) ตอนนี้เป็นเพียง no-op เชิงป้องกัน ไม่ใช่แนวป้องกันด่านเดียวอีกต่อไป
- **Bulk action** — การเลือก row ตั้งแต่หนึ่งแถวขึ้นไป (คอลัมน์ checkbox แสดงให้ session ที่ถือ `news.update` หรือ `news.delete`) จะเผย toolbar **Publish Selected** / **Archive Selected** / **Delete Selected** แต่ละตัวเปิด confirm dialog ที่ต้องพิมพ์รหัส 6 ตัวอักษรแบบสุ่มก่อนจะรันได้ ไม่มี bulk API จริง: SPA ยิง `PUT` (publish/archive พร้อม `doc_version`) หรือ `DELETE` หนึ่งครั้งต่อ row ที่เลือกผ่าน `Promise.allSettled` และรายงาน toast สำเร็จ/สำเร็จบางส่วน/ล้มเหลวรวมกัน

## 4. บทบาทและ Persona

การเข้าถึงถูก gate ด้วย permission ผ่าน [Platform RBAC](/th/platform/rbac) (key `news.*` ทั้งสี่ถูก seed ใน `seed.platform-permission.ts`) ด้วย route guard และ gate `<Can>` ภายในหน้า:

| Surface | Gate | Key |
|---|---|---|
| route `/news` + รายการ sidebar "News" (กลุ่ม Content, ไอคอน Newspaper) | `PrivateRoute` / sidebar filter | `news.read` |
| route `/news/new` | `PrivateRoute` | `news.create` |
| route `/news/:id/edit` | `PrivateRoute` | `news.update` |
| ปุ่ม Add News (header ของหน้า list **และ** CTA ของ empty-state) | `<Can>` | `news.create` |
| Edit ของ row (dropdown action ในหน้า list) | `<Can>` | `news.update` |
| Delete ของ row (dropdown action ในหน้า list) | `<Can>` | `news.delete` |
| Bulk Publish / Archive Selected | in-component (`canUpdate`) | `news.update` |
| Bulk Delete Selected | in-component (`canDelete`) | `news.delete` |
| toggle Edit (masthead ของหน้า edit) | `<Can>` | `news.update` |
| **View History** ของ row/header หน้า edit (Activity Trail ข้ามโมดูล) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` |

เช่นเดียวกับ Applications, `news.delete` **ไม่มี route ของ SPA ที่ต้องการมัน** — การลบเป็น action ของ row/bulk ไม่ใช่หน้าที่ navigate ไปถึง แต่นั่นเป็นข้อเท็จจริงเรื่อง client-routing เท่านั้น ไม่ใช่เรื่องการบังคับใช้ทั้งหมด ฝั่ง server `POST`/`PUT`/`DELETE /api/news` แต่ละตัวตรวจสอบ permission `news.create`/`.update`/`.delete` ของผู้เรียกเองผ่าน `PlatformPermissionGuard` (เพิ่มเมื่อ 2026-08-20; ก่อนแก้ API ไม่มีการตรวจสอบ permission ของผู้ใช้เลยและยอมรับผู้เรียกที่ authenticated และ app-id ผ่านทุกคน — ดู [Permissions](/th/platform/news/permissions) §1) route guard ที่ไม่ผ่านตอนนี้ render หน้า `Forbidden` แบบเฉพาะ (เปลี่ยนชื่อจาก `AccessDenied` แบบ inline เดิม ยังคงเป็นหัวข้อ 403 "Access Denied" เหมือนเดิม ตอนนี้มี action Go Back / Go to Dashboard เพิ่มมา) ภายใน shell `Layout` ปกติ caller ที่เป็น machine ถูก gate แยกต่างหากด้วย key ของ `AppIdGuard` (`news.findAll`, `news.findOne`, `news.create`, `news.update`, `news.delete` — key `news.findAll` เดียวกันนี้ยัง gate `GET /api/news/tags` และ `GET /api/news/summary` ด้วย) — คลังศัพท์คนละชุดกับ key ของ RBAC และเป็นการตรวจสอบฝั่ง server เพียงอย่างเดียวของ route `GET` ทั้งสี่ (ดู [Permissions](/th/platform/news/permissions) §1 สำหรับเหตุผล) เมทริกซ์ฉบับเต็มอยู่ใน [Permissions](/th/platform/news/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [Business Units](/th/platform/business-units) — การกำหนดเป้าหมายอ้างอิงค่า `tb_business_unit.id`: ถูกตรวจสอบว่าเป็น BU ที่ live อยู่ตอนเขียน จัดเก็บแบบไม่มี FK ใน JSONB multi-select ของการกำหนดเป้าหมายโหลดรายการ BU ทั้งหมดจาก API ของโมดูลนั้น
- [Broadcasts](/th/platform/broadcasts) — คู่เทียบแบบ **push** ของ News ซึ่งเป็นแบบ **pull**: broadcast push การแจ้งเตือนไปยังผู้ใช้ทั้งหมด ผู้ใช้ที่เลือก หรือ business unit หนึ่งแห่ง (ทันทีหรือตามกำหนดเวลา) ขณะที่บทความข่าวนั่งรออยู่ใน `tb_news` ให้ถูก fetch จาก public feed ใช้ Broadcasts เพื่อขัดจังหวะ ใช้ News เพื่อแจ้งข้อมูล
- [Platform RBAC](/th/platform/rbac) — กำหนดและ resolve permission key `news.*` ทั้งสี่ที่ gate surface ของ SPA
- [Applications](/th/platform/applications) — แกน `x-app-id`: ทุกการเรียก `/api/news` ต้องมาจาก application ที่ได้รับ grant `api_name` `news.*` ที่ตรงกัน (หรือ `allow_all`) controller `/api/public/news` แบบ anonymous ไม่ตรวจสอบทั้ง token และ app id

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — route guard `news.*` ทั้งสาม
- `../carmen-platform/src/components/nav/platformNav.ts` — รายการ sidebar "News" (บรรทัด 27: กลุ่ม Content, ไอคอน Newspaper, `news.read`, `feature: 'news'`, `dividerBefore: true`) ไม่ใช่ `Layout.tsx` ซึ่งไม่ได้กำหนดรายการ nav ใด ๆ แล้ว
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/news.controller.ts` — `PlatformPermissionGuard`/`RequirePlatformPermission` บน route เขียนสามตัว (เพิ่มเมื่อ 2026-08-20) และ route `/summary` (เพิ่มเมื่อ 2026-08-24)
- `../carmen-platform/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail,constants}.tsx` — ฟีเจอร์ View History; `AUDIT_RECORDING_STARTED_ON_PHASE_2` (2026-08-31)
- `../carmen-platform/src/utils/permissions.ts` — `PLATFORM_SCOPED_RECORD` sentinel `clusterId` ที่ gate ของ View History ใช้
- `../carmen-platform/src/pages/NewsManagement.tsx`, `src/pages/newsManagement/NewsroomSummary.tsx` — หน้า list: คอลัมน์ thumbnail/Target/Tags, filter สถานะ/tag, ส่งออก CSV, bulk toolbar, gate `<Can>`
- `../carmen-platform/src/pages/NewsEdit.tsx`, `src/pages/newsEdit/NewsMasthead.tsx` — layout แบบ masthead + สองคอลัมน์ของ create/view/edit และการ validate
- `../carmen-platform/src/services/newsService.ts` — REST client, ตัวสร้าง multipart, `getTags`
- `../carmen-platform/src/components/MarkdownEditor.tsx`, `ImageUpload.tsx`, `BusinessUnitMultiSelect.tsx`, `ui/chip-input.tsx`, `ReadOnlyField.tsx` — component ของฟอร์มในโมดูล
- `../carmen-platform/src/utils/docVersion.ts` — helper ของ optimistic-lock (`getDocVersion`/`isVersionConflict`/`notifyVersionConflict`)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_news` (บรรทัด 884), `enum_news_status` (บรรทัด 798)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/` — `news.controller.ts` (guard, multipart, `GET tags`), `news.service.ts` (อัพโหลดไฟล์/rollback/cleanup), `news-image.helper.ts` (presigned `image_url`), `news-body.parser.ts`, `public-news.controller.ts` / `public-news.service.ts` (การส่งมอบแบบ anonymous)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` — ชั้น persistence: การตรวจสอบ BU, การ normalize tag, การประทับ `published_at`, optimistic lock ของ `doc_version`, การ filter soft-delete, filter การมองเห็นฝั่ง public
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/news/` — สัญญา request/response รวมถึงคู่ `public/` และ `GET-find-tags-master-data-news.bru`

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/news/data-model) — ตาราง field ของ `tb_news` (รวม `tags` และ `doc_version`), คอลัมน์การกำหนดเป้าหมายแบบ JSONB, `enum_news_status`, ความแตกต่างจาก type `News` ของ SPA และตาราง endpoint
- [UI Screens](/th/platform/news/ui-screens) — list `NewsManagement` (thumbnail, Target, Tags, `NewsroomSummary`, bulk toolbar) และฟอร์ม `NewsEdit` แบบ masthead พร้อม markdown editor, การอัพโหลดรูป, tags และการกำหนดเป้าหมาย BU
- [Permissions](/th/platform/news/permissions) — เมทริกซ์ gate ของ `news.*`, กฎการมองเห็นฝั่งผู้อ่านบน public endpoint และเมทริกซ์กรณีพิเศษสำหรับผู้ทดสอบ
