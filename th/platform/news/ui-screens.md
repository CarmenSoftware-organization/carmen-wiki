---
title: News — หน้าจอ UI (UI Screens)
description: list NewsManagement (thumbnail, Target, filter สถานะ, ส่งออก CSV) และฟอร์ม NewsEdit แบบสี่การ์ด — MarkdownEditor, ImageUpload, Publishing และการกำหนดเป้าหมาย BU — พร้อมการ validate และคีย์ลัด
published: true
date: 2026-06-10T15:45:00.000Z
tags: book/platform, news, ui
editor: markdown
dateCreated: 2026-06-10T15:45:00.000Z
---

# News — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `NewsManagement` (`/news`) · `NewsEdit` (`/news/new`, `/news/:id/edit`) &nbsp;·&nbsp; **Layout ของหน้า edit:** สี่การ์ด — Content · Publishing · Targeting · Metadata (เฉพาะเรคคอร์ดที่มีอยู่แล้ว) &nbsp;·&nbsp; **UI เอกลักษณ์:** แท็บ Write/Preview ของ MarkdownEditor · drag-and-drop ของ ImageUpload · multi-select ของ BU หลัง checkbox "global" &nbsp;·&nbsp; **สถานะ UI ที่จดจำ:** key `localStorage` 5 ตัวบนหน้า list &nbsp;·&nbsp; **คีย์ลัด:** Ctrl/Cmd+S save · Escape cancel · Ctrl/Cmd+K โฟกัสช่องค้นหา

## 1. ภาพรวม

News ทำตามรูปแบบ Management/Edit สองหน้าจอมาตรฐานของ SPA โดยมีการเบี่ยงเบนเชิงโครงสร้างหนึ่งจุดบนฝั่ง edit: แทนที่จะเป็นการ์ด details การ์ดเดียว `NewsEdit` วางซ้อน**สี่การ์ด** (Content, Publishing, Targeting, Metadata) เพื่อแยกตัวเนื้อหาบทความออกจาก lifecycle และกลุ่มผู้ชมของมัน หน้า list เป็น `DataTable` ฝั่ง server มาตรฐานพร้อมคอลัมน์เฉพาะของโมดูล: **thumbnail** รูปภาพ, badge **Target** (Global เทียบกับ N BUs) และ timestamp ของ Published/Updated

ทั้งสองหน้าจอมาพร้อม **Debug Sheet** เฉพาะ dev (ปุ่มลอยสีเหลืองอำพัน, เฉพาะ `import.meta.env.DEV`) ที่เปิดเผย raw JSON ของ `GET /api/news` (list) หรือ `GET /api/news/:id` (edit; ไม่มีในโหมด create) ทั้งสองหน้าลงทะเบียนคีย์ลัด global: บน list, Ctrl/Cmd+K โฟกัสช่องค้นหา; บนฟอร์ม, Ctrl/Cmd+S submit ขณะแก้ไขและ Escape ยกเลิกโหมดแก้ไข (เฉพาะ route view/edit ไม่ใช่ create)

## 2. `NewsManagement` — list (`/news`)

### 2.1 Layout และ action บน header

Header: หัวข้อ "News Management" / หัวข้อรอง "Manage announcements and news articles" พร้อมสอง action — **Export** (CSV ฝั่ง client ของหน้าที่โหลดอยู่: Title, Status, URL, Published; ไฟล์ `news-<YYYY-MM-DD>.csv`; disabled ขณะโหลดหรือเมื่อว่าง; *ไม่*ถูก gate ด้วย permission) และ **Add News** (นำทางไป `/news/new`; ถูกห่อด้วย `<Can permission="news.create">`)

### 2.2 การค้นหาและ filter

ช่องค้นหาแบบ debounce (400 ms) เหนือ `title`/`contents` (param `search` ฝั่ง server; highlight สีเหลืองขณะมีคำค้นหา active, ปุ่มเคลียร์แบบ inline) บวก Sheet **Filters** ที่มีกลุ่ม **Status** กลุ่มเดียว — ปุ่ม toggle สามตัว (Draft / Published / Archived; ถูกเติมสีเมื่อเลือก, multi-select) ที่แปลเป็น query `advance` `{ where: { status: { in: [...] } } }` ตัวเลือกที่ active render เป็น chip ที่ลบได้ใต้แถวค้นหาพร้อมลิงก์ "Clear all"; ปุ่ม Filters แสดง badge นับจำนวนขณะมีสถานะใดถูกเลือกอยู่

### 2.3 คอลัมน์

| คอลัมน์ | การ render |
|---|---|
| (รูปภาพ) | Thumbnail ของ `image_url` (fallback แบบ legacy `image`): `h-10`, กว้างสูงสุด 96 px, `object-contain` (รักษา aspect ratio), ขอบมน; ซ่อนตัวเองเมื่อโหลด error กล่อง placeholder `ImageIcon` แบบ muted เมื่อไม่มีรูป |
| Title | ลิงก์ไป `/news/:id/edit`; `(untitled)` เมื่อว่าง |
| Status | Badge — `published` → success (เขียว), `draft` (หรือไม่มี) → secondary, `archived` → outline; label ขึ้นต้นตัวพิมพ์ใหญ่ |
| Target | `business_unit_ids` ไม่ว่าง → ไอคอน Building2 + "N BU(s)"; ว่าง/ไม่มี → badge แบบ outline พร้อมไอคอน Globe + "Global"; sort ไม่ได้ |
| Published | `published_at` เป็น `YYYY-MM-DD HH:mm:ss` (เวลาท้องถิ่นของเบราว์เซอร์), ข้อความเล็กแบบ muted; `-` เมื่อไม่เคย publish |
| Updated | timestamp `audit.updated.at` พร้อมชื่อ actor (`audit.updated.name`) บนบรรทัดถัดไป; `-` เมื่อไม่มี; sort ไม่ได้ |
| (action) | dropdown `⋯` — ดู §2.4 |

sort ค่าเริ่มต้นคือ `published_at:desc` (และ header คอลัมน์คลิกได้) — แต่สังเกตว่า **server override ทุก sort เป็น `updated_at DESC`**; UI ของ sort ปัจจุบันไม่มีผลต่อลำดับ row เลย (ดู [Data Model](./data-model.md) §5) การโหลดครั้งแรก render `TableSkeleton` แบบ 7 คอลัมน์; การโหลดครั้งถัด ๆ ไปวาง scrim "Loading news..." ทับ

list ยังทิ้ง row ที่ถูก soft-delete ฝั่ง client อย่างเงียบ ๆ (`deleted_at` หรือ `audit.deleted.at`) เพราะ endpoint คืนพวกมันมาด้วย

### 2.4 action ของ row และ dialog ลบ

dropdown มี **Edit** (นำทางไป route edit) ถูกห่อด้วย `<Can permission="news.update">` และ **Delete** (สไตล์ destructive) ถูกห่อด้วย `<Can permission="news.delete">` Delete เปิด `ConfirmDialog` ("Delete News — Are you sure you want to delete this news article? This action cannot be undone."); การยืนยันเรียก `DELETE /api/news/:id` (เป็น soft delete ฝั่ง server), toast และ refetch หน้านั้น ไม่มี affordance ลบที่อื่นใดในโมดูล

### 2.5 Empty state และสถานะ UI ที่จดจำ

ผลลัพธ์ว่าง render การ์ด `EmptyState` (ไอคอน Newspaper, หัวข้อ "No news yet"); คำอธิบายแตกต่างกันไป — `No news matching "<term>"` เมื่อมีคำค้นหา active หรือ "Get started by creating your first news article." พร้อม CTA **Add News** แบบ inline เมื่อไม่มีคำค้นหา CTA นี้**ไม่**ถูกห่อด้วย `<Can>` (ดู [Permissions](./permissions.md) §2)

| Key ของ `localStorage` | ชนิดที่จัดเก็บ | จดจำ |
|---|---|---|
| `search_news` | string | คำค้นหา |
| `filters_news` | JSON string array | ตัวเลือก filter สถานะ |
| `page_news` | number string | หน้าปัจจุบัน |
| `perpage_news` | number string | ขนาดหน้า |
| `sort_news` | string | Sort (`column:dir`, ค่าเริ่มต้น `published_at:desc`) |

หน้า edit ไม่จดจำสถานะ UI ใด ๆ

## 3. `NewsEdit` (`/news/new`, `/news/:id/edit`)

### 3.1 โหมด

- **Create** (`/news/new`): หัวข้อ "Add News", การ์ดทั้งสี่แก้ไขได้ทันที (ไม่มี Metadata — ยังไม่มี audit) ตอน submit: `POST /api/news`, toast แล้ว redirect ไป `/news/:id/edit` ของ id ที่สร้าง (`replace: true`) โดย fall back ไปหน้า list เมื่อ response ไม่มี id มา
- **View** (`/news/:id/edit`, ค่าเริ่มต้น): หัวข้อ "News Details" โหลดผ่าน `GET /api/news/:id` (skeleton ระหว่างรอ); ทุก field เป็น read-only — markdown ถูก render, สถานะเป็น badge, รูปที่ save ไว้เป็น preview ขนาดเล็ก header มีลูกศรย้อนกลับไป `/news` และปุ่ม **Edit** ถูกห่อด้วย `<Can permission="news.update">`
- **Edit** (หลังกด toggle): หัวข้อ "Edit News" toggle จะ snapshot ฟอร์มไว้; **Cancel** คืนค่า snapshot (ทิ้งการเลือกรูปที่ค้างอยู่ด้วย) และออกจากโหมดแก้ไข การเปลี่ยนแปลงที่ยังไม่ save — diff ของฟอร์มใด ๆ **หรือ** ไฟล์รูปที่ค้างอยู่ — จะติดอาวุธ navigation guard `useUnsavedChanges` เมื่อ update สำเร็จ หน้าจะ re-fetch และตกกลับเป็นโหมด view

### 3.2 การ์ด Content

| Field | Control ในโหมดแก้ไข | การ validate |
|---|---|---|
| Title * | Text input | จำเป็น — ตรวจสอบตอน blur และก่อน submit ("Title is required") |
| Content (Markdown) | `MarkdownEditor` — แท็บ **Write** (textarea แบบ monospace, ≥200 px, placeholder "Write your news content in Markdown...") และแท็บ **Preview** (`react-markdown` + `remark-gfm`: ตาราง GFM, list, code, blockquote) | ไม่มี — optional |
| Source URL | URL input | เมื่อไม่ว่าง: "Must be a valid http(s) URL" (blur + ก่อน submit) |
| Image | `ImageUpload` (§3.3) | การตรวจสอบ type/ขนาดฝั่ง client |

ในโหมด view markdown ถูก render แบบ read-only ในกล่อง muted (`-` เมื่อว่าง)

### 3.3 component `ImageUpload`

โซน drop เส้นประ ("Drag & drop an image here, or *browse*") ทำหน้าที่เป็น file picker ที่เปิดด้วยคลิก/คีย์บอร์ดไปด้วย การ validate ฝั่ง client จะ toast เมื่อปฏิเสธ: type ที่รับคือ JPEG/PNG/WebP/GIF, ≤5 MB ไฟล์ที่เลือกแล้วแสดง preview แบบ object-URL ในเครื่อง (สูง 64 px, รักษา aspect) พร้อมปุ่ม **Remove** ที่เคลียร์เฉพาะ*การเลือกที่ค้างอยู่*เท่านั้น — รูปที่ save ไว้แล้วลบออกไม่ได้ ทำได้เพียงแทนที่ (ดู [Permissions](./permissions.md) §4) ในโหมด view component นี้ render เพียง preview ของ presigned URL ที่ save ไว้ หรือไม่ render อะไรเลย

ข้อพึงระวังฝั่ง server สองข้อที่ QA ควรรู้: backend ปฏิเสธ **GIF** เพิ่มเติม (`image/gif` ผ่าน picker แต่คืน 400 `BAD_FILE_TYPE`) และรูปที่ใหญ่กว่า **2048×2048 px** (400 `BAD_DIMENSIONS`) — ทั้งคู่ปรากฏเป็น form error "Failed to save news" ไม่ใช่ toast ตอนอัพโหลด

### 3.4 การ์ด Publishing

- **Status** — native select ที่มี Draft / Published / Archived (transition อิสระทุกทิศทาง); render เป็น badge สีในโหมด view
- **Published At** — read-only เสมอ พร้อม helper text: Set automatically by the server when status becomes "Published". SPA ไม่เคยส่ง field นี้; server ประทับมันตอน publish ครั้งแรกและคงไว้หลังจากนั้น ([Data Model](./data-model.md) §2.2)

### 3.5 การ์ด Targeting

- checkbox **"Visible to all business units (global)"** — ติ๊กไว้เป็นค่าเริ่มต้นตอน create ขณะติ๊กอยู่ ไม่มี control ของ BU render และ payload ของการ save ส่ง `business_unit_ids: []`
- การยกเลิกติ๊กเผย **Business Units**: `BusinessUnitMultiSelect` ที่โหลดรายการ BU เต็มหนึ่งครั้ง (`perpage: -1`, เรียงตามชื่อ), มีช่องค้นหา name/code เหนือ list แบบ checkbox และ render ตัวที่เลือกเป็น badge ที่ลบได้ด้านบน
- การ validate ก่อน submit: ไม่ global + ศูนย์ BU → "Select at least one business unit, or enable \"Visible to all business units\"." การติ๊กกล่อง global กลับคืนจะเคลียร์ error

### 3.6 การ์ด Metadata (เฉพาะเรคคอร์ดที่มีอยู่แล้ว)

render เมื่อเรคคอร์ดที่โหลดมามี object `audit`: **Created** และ **Last Updated** แต่ละตัวเป็น `YYYY-MM-DD HH:mm:ss` บวก `by <name>` เมื่อ audit ที่ enrich แล้วมี actor

### 3.7 flow การ save

Save (`Create News` / `Save Changes`, spinner ขณะกำลัง save) submit `{ title, contents?, url?, status, business_unit_ids }` เมื่อมีไฟล์รูปที่ค้างอยู่ service จะสลับเป็น `multipart/form-data` — binary ใน field `image`, `business_unit_ids` ถูก encode เป็น string แบบ JSON และ `Content-Type` แบบ multipart ที่ระบุชัด (จำเป็น: axios instance ตั้งค่าเริ่มต้นเป็น JSON ซึ่งจะ serialize ตัว `FormData` ทิ้งไป) เมื่อไม่มีไฟล์จะส่ง JSON ธรรมดา โดยไม่แตะรูปที่ save ไว้ field error จาก API ผ่าน `parseApiError` map กลับลง field ของฟอร์ม; หลัง update สำเร็จ SPA จะ re-fetch เรคคอร์ด (response ของ `PUT` มีเพียง `{ id, image_url }`)

## 4. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/NewsManagement.tsx` — คอลัมน์, Sheet ของ filter สถานะ, ส่งออก CSV, gate `<Can>`, filter soft-delete ฝั่ง client, key ที่จดจำ
- `../carmen-platform/src/pages/NewsEdit.tsx` — ฟอร์มสี่การ์ด, toggle โหมด, การ validate, payload ของการ save, คีย์ลัด
- `../carmen-platform/src/components/MarkdownEditor.tsx` — แท็บ Write/Preview, preview แบบ GFM, การ render แบบ read-only
- `../carmen-platform/src/components/ImageUpload.tsx` — โซน drop, รายการ accept, เพดาน 5 MB, semantics ของ preview/remove ในเครื่อง
- `../carmen-platform/src/components/BusinessUnitMultiSelect.tsx` — การโหลด BU, การค้นหา, การเลือกแบบ badge
- `../carmen-platform/src/services/newsService.ts` — `buildNewsFormData`, หมายเหตุ `Content-Type` แบบ multipart, การเดิน envelope
- `../carmen-platform/src/components/KeyboardShortcuts.tsx` — binding ของ Ctrl/Cmd+S, Ctrl/Cmd+K, Escape

**Cross-link:** [หน้า landing ของ News](/th/platform/news) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
