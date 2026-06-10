---
title: ข่าวสาร (News)
description: ภาพรวมโมดูล News — ประกาศแบบ markdown พร้อมรูปภาพแบบ optional, lifecycle ของสถานะ draft → published → archived และการกำหนดเป้าหมายแบบ global หรือราย BU เขียนใน admin SPA และส่งมอบผ่าน public endpoint แบบ anonymous
published: true
date: 2026-06-10T15:45:00.000Z
tags: platform/news, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:45:00.000Z
---

# ข่าวสาร (News)

โมดูล **News** จัดการประกาศและบทความสำหรับผู้ใช้แพลตฟอร์ม: เนื้อหา markdown, รูปภาพแบบ optional, URL ของแหล่งที่มา และ lifecycle ของสถานะ `draft → published → archived` กำหนดเป้าหมายแบบ global หรือไปยังรายการ business unit แบบระบุชัด Platform admin SPA คือ**ฝั่งผู้เขียน (authoring)**; การส่งมอบไปยังผู้ใช้ปลายทางเกิดขึ้นผ่านคู่ **public endpoint แบบ anonymous** ที่แยกต่างหาก (`/api/public/news`) ซึ่งเปิดเผยเฉพาะบทความที่ published, ไม่ถูกลบ และเวลาเผยแพร่มาถึงแล้วเท่านั้น (ยังไม่มี client ใน repo ใดบริโภค endpoint เหล่านี้ — ดู §2)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เขียนและจัดการประกาศ — `contents` แบบ markdown, รูปภาพแบบ optional (อัพโหลด multipart → file token ของ MinIO → presigned `image_url`), lifecycle ของสถานะพร้อม `published_at` ที่ server ประทับให้, การกำหนดเป้าหมายแบบ global หรือราย BU &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA, โมดูล news ของ backend-gateway และ news service ของ micro-cluster &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_news` (ตารางเดียว, `business_unit_ids` แบบ JSONB, ไม่มีความสัมพันธ์ FK) &nbsp;·&nbsp; **Endpoint:** `/api/news` (CRUD แบบ authenticated — สังเกตว่าเป็น `/api` **ไม่ใช่** `/api-system`) และ `/api/public/news` (อ่านแบบ anonymous) &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูลนี้ทำตามรูปแบบสองหน้าจอมาตรฐานของ SPA:

- **`/news` → `NewsManagement`** — `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce (title/contents), filter สถานะแบบ Sheet (Draft/Published/Archived), ส่งออก CSV และจดจำสถานะ UI ใน `localStorage` คอลัมน์เฉพาะของโมดูล: **thumbnail รูปภาพ** (รักษา aspect ratio, กว้าง ≤96 px, ไอคอน placeholder เมื่อไม่มีรูป), คอลัมน์ **Target** ที่ render badge "Global" หรือจำนวน "N BUs" และคอลัมน์ timestamp **Published**/**Updated**
- **`/news/new` และ `/news/:id/edit` → `NewsEdit`** — ฟอร์มแบบสี่การ์ด (Content, Publishing, Targeting, Metadata) แทนที่จะเป็นการ์ดเดียวตามปกติ โหมด create แก้ไขได้ทันที; route edit เปิดแบบ read-only อยู่หลัง toggle Edit องค์ประกอบที่เป็นเอกลักษณ์คือ **MarkdownEditor** (แท็บ Write/Preview) และโซน drag-and-drop **ImageUpload**

เรคคอร์ดข่าวหนึ่งตัวคือหนึ่ง row ใน `tb_news`: `title` (จำเป็น), `contents` (markdown), `url` (ลิงก์แหล่งที่มาแบบ optional), รูปภาพที่จัดเก็บเป็น **file token** ของ MinIO (`image_file_token` — API จะ resolve มันเป็น presigned `image_url` และไม่เคยเปิดเผยตัว token), `status`, `published_at` และ `business_unit_ids` (array แบบ JSONB; ว่าง = มองเห็นได้ทุก business unit) ดู [Data Model](/th/platform/news/data-model) สำหรับตาราง field ฉบับเต็มและ [UI Screens](/th/platform/news/ui-screens) สำหรับ walkthrough ของหน้าจอ

ส่วนที่เหลือทั้งหมดเป็นองค์ประกอบมาตรฐานของหน้า Management: `TableSkeleton`, `EmptyState`, toast feedback, navigation guard `useUnsavedChanges`, คีย์ลัด global (Ctrl/Cmd+S save, Escape cancel, Ctrl/Cmd+K โฟกัสช่องค้นหา) และ Debug Sheet เฉพาะ dev

## 2. บริบททางธุรกิจ

News มีไว้เพื่อสื่อสารข้อมูลอัพเดทเชิงปฏิบัติการ — การเปลี่ยนนโยบาย, ประกาศปิดปรับปรุงระบบ, ประกาศของกลุ่มโรงแรม — ไปยังพนักงานของ business unit หนึ่งแห่ง หลายแห่ง หรือทั้งหมด โมดูลแบ่งออกเป็นสองส่วนอย่างชัดเจนโดยมี security model ต่างกัน:

- **Authoring** (SPA นี้ + `/api/news`): CRUD เต็มรูปแบบ ถูก gate ด้วย key `news.*` ของ RBAC สำหรับมนุษย์ และ grant ของ `AppIdGuard` สำหรับ application ที่เรียก ผู้เขียนเห็นทุกเรคคอร์ดไม่ว่าสถานะใด รวมถึง row ที่เป็น draft และ archived
- **Delivery** (`/api/public/news` + `/api/public/news/:id`): **anonymous** — controller ไม่มี authentication guard ใด ๆ เลย มันเสิร์ฟเฉพาะ row ที่ `status = published`, ไม่ถูก soft-delete **และ** `published_at <= now()` เมื่อไม่มี query parameter `bu_id` จะคืนเฉพาะข่าว global; เมื่อมี `bu_id` จะคืนข่าว global บวกข่าวที่กำหนดเป้าหมายไปยัง BU นั้น บทความที่เป็น draft, archived, ถูกลบ หรือลงวันที่อนาคตตอบกลับ 404 — response เดียวกับ id ที่ไม่รู้จัก การมีอยู่ของเรคคอร์ดจึงไม่เคยรั่วไหล

filter `published_at <= now()` หมายความว่าผู้เขียนสามารถ**กำหนดเวลาเผยแพร่ (schedule)** บทความได้โดย publish พร้อม timestamp อนาคตผ่าน API (ตัว SPA เองไม่เคยส่ง `published_at` — ดู §3) ณ 2026-06-10 **ยังไม่มี client ใน repo ใด render public feed**: web frontend ของ Carmen Inventory ไม่มี surface สำหรับข่าว และ `NewsCarousel` บนหน้า home ของ mobile app (`carmen-inventory-mobile/src/components/ui/news-carousel.tsx`) คือ consumer ในอนาคตที่ชัดเจนที่สุด แต่ปัจจุบัน render translation string แบบ hard-code ไม่ใช่ API ให้ปฏิบัติกับ public endpoint เป็นสัญญาการส่งมอบ (delivery contract) ของโมดูล

## 3. แนวคิดสำคัญ

- **Lifecycle ของสถานะ** — `enum_news_status`: `draft` (ค่าเริ่มต้น) → `published` → `archived` select ของสถานะเป็นแบบอิสระ: ค่าใดก็ย้ายไปค่าอื่นใดได้; ไม่มีอะไรใน SPA หรือ backend ห้ามการ un-publish กลับเป็น draft หรือการชุบชีวิต row ที่ archived
- **`published_at` ถูก server ประทับให้ ครั้งเดียว** ตอน create ด้วย `status = published` และตอน transition เข้าสู่ `published` ครั้งแรก micro-cluster จะประทับ `published_at = now()` — แต่เฉพาะเมื่อเรคคอร์ดไม่เคยมีเวลาเผยแพร่มาก่อนเท่านั้น การย้ายกลับเป็น draft หรือ archived **ไม่**เคลียร์ค่านี้ และการ re-publish ภายหลังคงค่าประทับ*เดิม*ไว้ caller ของ API สามารถ set หรือเคลียร์ `published_at` แบบระบุชัดได้; SPA ไม่เคยส่ง field นี้และ render มันแบบ read-only (helper text: Set automatically by the server when status becomes "Published".)
- **Global เทียบกับการกำหนดเป้าหมายราย BU** — `business_unit_ids` คือ array แบบ JSONB ของ UUID ของ BU บนตัว row เอง ไม่ใช่ join table array ว่าง (ค่า default ของคอลัมน์) = global SPA model สิ่งนี้เป็น checkbox "Visible to all business units (global)" ซึ่งเมื่อไม่ติ๊กจะต้องมี BU อย่างน้อยหนึ่งตัวใน multi-select backend ตรวจสอบทุก id กับ row ของ `tb_business_unit` ที่ live อยู่ตอนเขียน แต่จัดเก็บแบบไม่มี FK — ดู [Data Model](/th/platform/news/data-model) §3
- **เนื้อหาแบบ markdown** — `contents` คือ string แบบ markdown ที่แก้ไขในแท็บ Write/Preview (`react-markdown` + `remark-gfm` สำหรับ preview) backend จัดเก็บมันแบบ verbatim; กฎการ render เป็นเรื่องของ consumer แต่ละราย
- **อัพโหลดรูปผ่าน multipart** — create/update รับ `multipart/form-data` โดย binary อยู่ใน field `image` (ภายใต้ multipart, `business_unit_ids` เดินทางเป็น field string ที่ encode เป็น JSON) gateway อัพโหลดไฟล์ไปยัง micro-file (MinIO), จัดเก็บ token ที่คืนมาใน `image_file_token` และทุกการอ่านจะสลับ token เป็น **presigned URL (หมดอายุ 1 ชั่วโมง)** เปิดเผยเป็น `image_url` การแทนที่รูปจะลบไฟล์เก่า; การลบข่าวจะลบไฟล์ของมันแบบ best-effort การเขียนแบบ JSON (ไม่ใช่ multipart) จะไม่แตะรูปเลย — ซึ่งหมายความว่า SPA **ไม่มีวิธีลบรูปออกโดยไม่แทนที่มัน**ด้วย
- **Soft delete ผ่าน audit แบบซ้อน** — `DELETE /api/news/:id` ตั้ง `deleted_at`/`deleted_by_id` interceptor `EnrichAuditUsers` ของ gateway ยุบคอลัมน์ audit แบบแบนหกตัวเป็น object `audit: { created, updated, deleted }` แบบซ้อน (แต่ละตัว `{ at, id, name, avatar }`) และลบ field แบบแบนออก **endpoint ของ admin list ไม่ filter row ที่ถูก soft-delete** — SPA ซ่อนพวกมันฝั่ง client โดยตรวจสอบทั้ง `deleted_at` และ `audit.deleted.at` (การตรวจสอบคู่ครอบคลุม fallback เมื่อการ enrich ล้มเหลวและ payload รุ่นเก่า)

## 4. บทบาทและ Persona

การเข้าถึงถูก gate ด้วย permission ผ่าน [Platform RBAC](/th/platform/rbac) (key `news.*` ทั้งสี่ถูก seed ใน `seed.platform-permission.ts`) ด้วย route guard และ gate `<Can>` ภายในหน้า:

| Surface | Gate | Key |
|---|---|---|
| route `/news` + รายการ sidebar "News" (กลุ่ม Content, ไอคอน Newspaper) | `PrivateRoute` / sidebar filter | `news.read` |
| route `/news/new` | `PrivateRoute` | `news.create` |
| route `/news/:id/edit` | `PrivateRoute` | `news.update` |
| ปุ่ม Add News (header ของหน้า list) | `<Can>` | `news.create` |
| Edit ของ row (dropdown action ในหน้า list) | `<Can>` | `news.update` |
| Delete ของ row (dropdown action ในหน้า list) | `<Can>` | `news.delete` |
| toggle Edit (header ของหน้า edit) | `<Can>` | `news.update` |

เช่นเดียวกับ Applications และ Print Template Mapping, `news.delete` มีอยู่ **เป็น gate ภายในหน้าเท่านั้น** — ไม่มี route ใดต้องการมันและหน้า edit ไม่มี action ลบ; การลบเกิดขึ้นจาก dropdown ของ row ในหน้า list เท่านั้น ปุ่ม Save ของหน้า edit ไม่ถูกห่อ แต่ไปถึงไม่ได้หากไม่มี toggle Edit ที่ถูก gate caller ที่เป็น machine ถูก gate แยกต่างหากด้วย key ของ `AppIdGuard` (`news.findAll`, `news.findOne`, `news.create`, `news.update`, `news.delete`) — คลังศัพท์คนละชุดกับ key ของ RBAC เมทริกซ์ฉบับเต็ม รวมถึง CTA ของ empty-state ที่ไม่ถูก gate อยู่ใน [Permissions](/th/platform/news/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [Business Units](/th/platform/business-units) — การกำหนดเป้าหมายอ้างอิงค่า `tb_business_unit.id`: ถูกตรวจสอบว่าเป็น BU ที่ live อยู่ตอนเขียน จัดเก็บแบบไม่มี FK ใน JSONB multi-select ของการกำหนดเป้าหมายโหลดรายการ BU ทั้งหมดจาก API ของโมดูลนั้น
- [Broadcasts](/th/platform/broadcasts) — คู่เทียบแบบ **push** ของ News ซึ่งเป็นแบบ **pull**: broadcast push การแจ้งเตือนไปยังผู้ใช้ทั้งหมด ผู้ใช้ที่เลือก หรือ business unit หนึ่งแห่ง (ทันทีหรือตามกำหนดเวลา) ขณะที่บทความข่าวนั่งรออยู่ใน `tb_news` ให้ถูก fetch จาก public feed ใช้ Broadcasts เพื่อขัดจังหวะ ใช้ News เพื่อแจ้งข้อมูล
- [Platform RBAC](/th/platform/rbac) — กำหนดและ resolve permission key `news.*` ทั้งสี่ที่ gate surface ของ SPA
- [Applications](/th/platform/applications) — แกน `x-app-id`: ทุกการเรียก `/api/news` ต้องมาจาก application ที่ได้รับ grant `api_name` `news.*` ที่ตรงกัน (หรือ `allow_all`) controller `/api/public/news` แบบ anonymous ไม่ตรวจสอบทั้ง token และ app id

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — route guard `news.*` ทั้งสาม
- `../carmen-platform/src/components/Layout.tsx` — รายการ sidebar "News" (กลุ่ม Content, `news.read`)
- `../carmen-platform/src/pages/NewsManagement.tsx` — หน้า list: คอลัมน์ thumbnail/Target, filter สถานะ, ส่งออก CSV, gate `<Can>`
- `../carmen-platform/src/pages/NewsEdit.tsx` — ฟอร์ม create/view/edit แบบสี่การ์ดและการ validate
- `../carmen-platform/src/services/newsService.ts` — REST client, ตัวสร้าง multipart, การ filter soft-delete ฝั่ง client
- `../carmen-platform/src/components/MarkdownEditor.tsx`, `ImageUpload.tsx`, `BusinessUnitMultiSelect.tsx` — form component ทั้งสามของโมดูล
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_news` (บรรทัด 803), `enum_news_status` (บรรทัด 693)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/` — `news.controller.ts` (guard, multipart), `news.service.ts` (อัพโหลดไฟล์/rollback/cleanup), `news-image.helper.ts` (presigned `image_url`), `news-body.parser.ts`, `public-news.controller.ts` / `public-news.service.ts` (การส่งมอบแบบ anonymous)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` — ชั้น persistence: การตรวจสอบ BU, การประทับ `published_at`, soft delete, filter การมองเห็นฝั่ง public
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/news/` — สัญญา request/response รวมถึงคู่ `public/`

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/news/data-model) — ตาราง field ของ `tb_news`, คอลัมน์การกำหนดเป้าหมายแบบ JSONB, `enum_news_status`, ความแตกต่างจาก type `News` ของ SPA (token เทียบกับ presigned URL, audit แบบซ้อน, การตรวจจับ soft-delete แบบคู่) และตาราง endpoint
- [UI Screens](/th/platform/news/ui-screens) — list `NewsManagement` (thumbnail, Target, filter สถานะ) และฟอร์ม `NewsEdit` แบบสี่การ์ดพร้อม markdown editor, การอัพโหลดรูป และการกำหนดเป้าหมาย BU
- [Permissions](/th/platform/news/permissions) — เมทริกซ์ gate ของ `news.*`, กฎการมองเห็นฝั่งผู้อ่านบน public endpoint และเมทริกซ์กรณีพิเศษสำหรับผู้ทดสอบ
