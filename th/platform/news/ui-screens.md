---
title: News — หน้าจอ UI (UI Screens)
description: การ์ด masthead NewsroomSummary + list NewsManagement (thumbnail, Target, Tags, filter สถานะ/tag, ส่งออก CSV, bulk publish/archive/delete) และฟอร์ม NewsEdit แบบ masthead — MarkdownEditor, ImageUpload, Tags, Publish rail — พร้อมการ validate และคีย์ลัด
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, news, ui
editor: markdown
dateCreated: 2026-06-10T15:45:00.000Z
---

# News — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `NewsManagement` (`/news`) · `NewsEdit` (`/news/new`, `/news/:id/edit`) &nbsp;·&nbsp; **ส่วนเสริมของ list:** การ์ด pipeline + lead-story ของ `NewsroomSummary` (endpoint เฉพาะ `GET /api/news/summary` ตั้งแต่ 2026-08-24), การเลือก row แบบ checkbox, bulk Publish/Archive/Delete, **View History** ของ row &nbsp;·&nbsp; **Layout ของหน้า edit:** `NewsMasthead` (cover/สถานะ/reach/title) + การ์ด Article (เนื้อหา, URL, tags) + Publish rail แบบ sticky + การ์ด History (`AuditMeta` แบบเวลาสัมพัทธ์ ตั้งแต่ 2026-08-22) &nbsp;·&nbsp; **เพิ่มใหม่:** **View History** ในแถว header ของหน้า edit (ไม่ได้อยู่ใน masthead) &nbsp;·&nbsp; **UI เอกลักษณ์:** แท็บ Write/Preview ของ MarkdownEditor · drag-and-drop ของ ImageUpload (ตอนนี้อยู่ใน masthead) · ChipInput ของ tags พร้อม autocomplete · multi-select ของ BU หลัง checkbox "global" &nbsp;·&nbsp; **สถานะ UI ที่จดจำ:** key `localStorage` 6 ตัวบนหน้า list &nbsp;·&nbsp; **คีย์ลัด:** Ctrl/Cmd+S save · Escape cancel · Ctrl/Cmd+K โฟกัสช่องค้นหา

## 1. ภาพรวม

News ทำตามรูปแบบ Management/Edit สองหน้าจอมาตรฐานของ SPA โดยมีการเบี่ยงเบนเชิงโครงสร้างทั้งสองฝั่ง หน้า list เพิ่มการ์ด masthead `NewsroomSummary` เหนือตาราง — แถบ pipeline Draft → Published → Archived บวก tile "Latest" ของบทความที่เพิ่ง publish ล่าสุด — และรองรับการเลือก row แบบ checkbox สำหรับ bulk Publish/Archive/Delete ฝั่ง edit แทนที่การ์ดสี่ใบแบบเดิมด้วย `NewsMasthead` (cover, badge สถานะ/reach/state, หัวข้อ) เหนือการ์ด **Article** และ rail **Publish** แบบ sticky เพื่อแยกเนื้อหาบทความออกจาก lifecycle และกลุ่มผู้ชมของมัน

ทั้งสองหน้าจอยังมี action **View History** ข้ามโมดูล (`activity_log.read` ผูก sentinel `clusterId={PLATFORM_SCOPED_RECORD}` เพราะบทความหนึ่งชิ้นกำหนดเป้าหมายได้หลาย business unit จึงไม่มี cluster เดียวของตัวเอง): dropdown action ของ row ในหน้า list (§2.6) และ — บนหน้า edit — แถว header บนสุดข้าง back link ไม่ใช่ actions slot ของการ์ด `NewsMasthead` เอง (§3.1/§3.2) การบันทึกเริ่มตั้งแต่ 2026-08-31 (`AUDIT_RECORDING_STARTED_ON_PHASE_2`)

ทั้งสองหน้าจอมาพร้อม **Debug Sheet** เฉพาะ dev (ปุ่มลอยสีเหลืองอำพัน, เฉพาะ `import.meta.env.DEV`) ที่เปิดเผย raw JSON ของ `GET /api/news` (list) หรือ `GET /api/news/:id` (edit; ไม่มีในโหมด create) ทั้งสองหน้าลงทะเบียนคีย์ลัด global: บน list, Ctrl/Cmd+K โฟกัสช่องค้นหา; บนฟอร์ม, Ctrl/Cmd+S submit ขณะแก้ไขและ Escape ยกเลิกโหมดแก้ไข (เฉพาะ route view/edit ไม่ใช่ create)

## 2. `NewsManagement` — list (`/news`)

### 2.1 Layout และ action บน header

Header (`PageHeader`): หัวข้อ "News Management" / หัวข้อรอง "Manage announcements and news articles" พร้อมสอง action — **Export** (CSV ฝั่ง client ของหน้าที่โหลดอยู่: Title, Status, URL, Published; ไฟล์ `news-<YYYY-MM-DD>.csv`; disabled ขณะโหลดหรือเมื่อว่าง; *ไม่*ถูก gate ด้วย permission) และ **Add News** (นำทางไป `/news/new`; ถูกห่อด้วย `<Can permission="news.create">`)

### 2.2 `NewsroomSummary`

การ์ดที่ render ระหว่าง header กับตาราง **ตั้งแต่ 2026-08-24** สร้างจากการเรียก `GET /api/news/summary` แบบเฉพาะทาง*แยกต่างหาก* (`newsService.getNewsroomSummary()`) ที่ไม่รับ filter parameter ใด ๆ เลย — แทนที่การกวาดฝั่ง client แบบเดิม (`perpage: -1` ทั่วทั้งตาราง รวมผลใน browser ด้วย helper `summarizeNews` ที่ถูกลบไปแล้ว) ผลคือ: ตัวนับ pipeline และบทความนำสะท้อนทั้งโต๊ะทำงานเสมอ ไม่ใช่มุมมอง search/status/tag ปัจจุบัน โดยโครงสร้างไม่ใช่โดย convention เมื่อ refresh ล้มเหลว ตัวเลขล่าสุดที่รู้จะถูกเก็บไว้ (ไม่ถูกเคลียร์) และแสดงข้อความจางลง "couldn't refresh" แทน — pattern เดียวกับแถบ Fleet Capacity ของ `ClusterManagement`:

- **Latest** — บทความที่เพิ่ง *publish* ล่าสุด (ตาม `published_at`): thumbnail ปก (หรือ placeholder), หัวข้อ (ลิงก์ไปหน้า edit ของมัน), label แบบสัมพัทธ์ "Published `<เวลาที่ผ่านมา>`" (`timeAgo`: "just now" / "N min/hour(s) ago" / "yesterday" / "N days/weeks ago" / วันที่แบบ absolute เมื่อเกิน 5 สัปดาห์) และ reach ของมัน (Global หรือ "N BUs") เมื่อยังไม่มีอะไร publish placeholder "Nothing published yet" จะแสดงแทน
- **Pipeline** — ตัวนับสามขั้น (Draft / Published / Archived คั่นด้วย chevron) บวก caption "N articles total" ตัวนับไม่รวม row ที่ soft-delete
- การโหลด (fetch ครั้งแรก ยังไม่มีข้อมูล) render placeholder แบบ skeleton; ความล้มเหลว ณ จุดนั้นสลับทั้งการ์ดเป็น error แบบ inline พร้อมปุ่ม **Retry** (`FetchErrorState`) ความล้มเหลว*ครั้งถัดไป* — หลังจาก summary โหลดสำเร็จมาแล้วครั้งหนึ่ง — จะทำให้ตัวเลขเดิมจางลง (`opacity-70`) แทน และเพิ่มข้อความเล็ก ๆ "couldn't refresh" โดยคงค่าเก่าที่อาจไม่สดไว้บนจอแทนที่จะเคลียร์ทิ้ง ไม่ว่ากรณีใด ตารางด้านล่างยังทำงานอิสระ

### 2.3 การค้นหาและ filter

ช่องค้นหาแบบ debounce (400 ms) เหนือ `title`/`contents` (param `search` ฝั่ง server; highlight สีเหลืองขณะมีคำค้นหา active, ปุ่มเคลียร์แบบ inline) บวก Sheet **Filters** ที่มีสองกลุ่ม:

- **Status** — ปุ่ม toggle สามตัว (Draft / Published / Archived; ถูกเติมสีเมื่อเลือก, multi-select)
- **Tags** — ปุ่ม toggle หนึ่งตัวต่อ tag ที่ไม่ซ้ำที่ใช้อยู่ (fetch ครั้งเดียวผ่าน `GET /api/news/tags`); กลุ่มนี้ render ก็ต่อเมื่อมี tag อย่างน้อยหนึ่งตัวอยู่ที่ไหนสักแห่ง

ทั้งสองกลุ่มแปลเป็น query `advance` เป็น `{ where: { status: { in: [...] }, OR: [{ tags: { array_contains: [tag] } }, ...] } }` ตัวเลือกที่ active render เป็น chip ที่ลบได้ใต้แถวค้นหาพร้อมลิงก์ "Clear all"; ปุ่ม Filters แสดง badge นับจำนวน (0, 1 หรือ 2 — หนึ่งต่อกลุ่มที่มีตัวเลือก active ไม่ใช่ต่อ chip)

### 2.4 คอลัมน์

| คอลัมน์ | การ render |
|---|---|
| (เลือก) | Checkbox แสดงเฉพาะเมื่อ session ถือ `news.update` หรือ `news.delete`; `getRowSelectionLabel` ประกาศ "Select `<title>`" |
| (รูปภาพ) | Thumbnail ของ `image_url` (fallback แบบ legacy `image`): `h-10`, กว้างสูงสุด 96 px, `object-contain` (รักษา aspect ratio), ขอบมน; ซ่อนตัวเองเมื่อโหลด error กล่อง placeholder `ImageIcon` แบบ muted เมื่อไม่มีรูป |
| Title | ลิงก์ไป `/news/:id/edit`; `(untitled)` เมื่อว่าง |
| Status | Badge — `published` → success (เขียว), `draft` (หรือไม่มี) → secondary, `archived` → outline; label ขึ้นต้นตัวพิมพ์ใหญ่ |
| Target | `business_unit_ids` ไม่ว่าง → ไอคอน Building2 + "N BU(s)"; ว่าง/ไม่มี → badge แบบ outline พร้อมไอคอน Globe + "Global"; sort ไม่ได้ |
| Tags | badge สูงสุด 3 ตัวบวก overflow "+N"; `-` เมื่อว่าง; sort ไม่ได้ |
| Published | `published_at` เป็น `YYYY-MM-DD HH:mm:ss` (เวลาท้องถิ่นของเบราว์เซอร์), ข้อความเล็กแบบ muted; `-` เมื่อไม่เคย publish |
| Updated | `AuditMeta` variant "cell" ที่ใช้ร่วมกัน: เวลาสัมพัทธ์ (เช่น "5mo ago", hover เพื่อดู timestamp แบบ absolute) บรรทัดแรก, ชื่อ actor บรรทัดที่สอง; `-` เมื่อเรคคอร์ดไม่เคยถูกแก้ไขจริง (`everEdited` ของ `normalizeAudit` — เรคคอร์ดที่ `updated_at` เท่ากับ `created_at` เฉย ๆ ถือว่ายังไม่เคยแก้ ไม่ใช่ "updated แต่ไม่มีชื่อ"); sort ไม่ได้ |
| (action) | dropdown `⋯` — ดู §2.6 |

sort ค่าเริ่มต้นคือ `published_at:desc` (และ header คอลัมน์คลิกได้) — แต่สังเกตว่า **server override ทุก sort เป็น `updated_at DESC`**; UI ของ sort ปัจจุบันไม่มีผลต่อลำดับ row เลย (ดู [Data Model](/th/platform/news/data-model) §5) คอลัมน์ซ้ายสุด 2–3 คอลัมน์ (เลือก + รูปภาพ บวก Title เมื่อการเลือกเปิดอยู่) จะ sticky ขณะเลื่อนแนวนอน การโหลดครั้งแรก render `TableSkeleton` ตามจำนวนคอลัมน์ปัจจุบัน; การโหลดครั้งถัด ๆ ไปวาง scrim "Loading news..." ทับ

เพราะ query ของ admin list ตอนนี้ filter `deleted_at: null` ฝั่ง server แล้ว (ดู [Data Model](/th/platform/news/data-model) §5) list จึงไม่ต้องซ่อน row ที่ soft-delete อีกต่อไป — filter ฝั่ง client ของ SPA (`deleted_at`/`audit.deleted.at`) ใน `newsService.getAll` ตอนนี้เป็นเพียง no-op เชิงป้องกัน

### 2.5 Toolbar การเลือกแบบ bulk

การเลือก row ตั้งแต่หนึ่งแถวขึ้นไปจะเผย toolbar เหนือตาราง: "N selected", **Publish Selected** และ **Archive Selected** (ทั้งคู่ gate ด้วย `news.update`), **Delete Selected** (gate ด้วย `news.delete`, สไตล์ destructive) และลิงก์ **Clear** การเลือกถูก scope ไว้เฉพาะหน้าปัจจุบันและถูกเคลียร์อัตโนมัติทุกครั้งที่ผลลัพธ์เปลี่ยน (หน้า, ขนาดหน้า, การค้นหา, sort หรือ filter) จึงไม่มีทางถือ row ที่เลื่อนพ้นสายตาไปแล้วได้

แต่ละ action เปิด dialog bulk ร่วมกัน (หัวข้อ/คำอธิบาย/ไอคอนต่างกันไปตาม action — Send/Archive/Trash2) แสดงรายชื่อที่เลือกและต้องพิมพ์รหัสยืนยัน 6 ตัวอักษรแบบสุ่ม (สุ่มใหม่ทุกครั้งที่เปิด) ก่อนปุ่มจะ enable การยืนยันยิง request **หนึ่งครั้งต่อ row ที่เลือก** ผ่าน `Promise.allSettled` — `PUT` พร้อม `{ status: 'published' | 'archived', doc_version }` สำหรับ Publish/Archive, `DELETE` สำหรับ Delete — และรายงาน toast รวม: สำเร็จทั้งหมด ("`<กริยา>` N news article(s)"), ล้มเหลวทั้งหมด หรือคำเตือน "N succeeded, M failed" ไม่มี bulk API endpoint เฉพาะ

### 2.6 action ของ row และ dialog ลบ

dropdown มี **Edit** (นำทางไป route edit) ถูกห่อด้วย `<Can permission="news.update">`; **View History** (เปิด `ActivityTrailSheet` ที่ใช้ร่วมกันสำหรับบทความนี้ ฟีเจอร์ Activity Trail ข้ามโมดูล) ถูกห่อด้วย `<Can permission="activity_log.read" clusterId={PLATFORM_SCOPED_RECORD}>` ใช้ `onSelect` แทน `onClick` เพื่อให้ dropdown menu ปิดเสร็จก่อนแผ่นเปิด ป้องกัน focus trap สองชั้นของ Radix ชนกัน; และ **Delete** (สไตล์ destructive) ถูกห่อด้วย `<Can permission="news.delete">` Delete เปิด `ConfirmDialog` ("Delete News — Are you sure you want to delete this news article? This action cannot be undone."); การยืนยันเรียก `DELETE /api/news/:id` (เป็น soft delete ฝั่ง server และ — ตั้งแต่ 2026-08-20 — ตรวจสอบ permission ฝั่ง server ด้วยเช่นกันบน `news.delete`), toast และ refetch หน้านั้น (พร้อมโหลด `NewsroomSummary` ใหม่) ไม่มี affordance ลบแบบ single-row อื่นใดอีก

### 2.7 Empty state และสถานะ UI ที่จดจำ

ผลลัพธ์ว่าง render `ListEmptyState` ที่รับรู้ filter (ไอคอน `Newspaper`): เมื่อไม่มีทั้งคำค้นหาและ filter ใด active จะแสดง "No news yet" / "Get started by creating your first news article." พร้อม CTA **Add News** แบบ inline — ถูกห่อด้วย `<Can permission="news.create">` ตัวเดียวกับปุ่ม Add ใน header (ดู [Permissions](/th/platform/news/permissions) §2); มิฉะนั้นจะแสดงข้อความ "No matches found" ร่วมกัน ไม่ว่า filter ตัวไหนจะเป็นสาเหตุ

| Key ของ `localStorage` | ชนิดที่จัดเก็บ | จดจำ |
|---|---|---|
| `search_news` | string | คำค้นหา |
| `filters_news` | JSON string array | ตัวเลือก filter สถานะ |
| `tagfilters_news` | JSON string array | ตัวเลือก filter tag |
| `page_news` | number string | หน้าปัจจุบัน |
| `perpage_news` | number string | ขนาดหน้า |
| `sort_news` | string | Sort (`column:dir`, ค่าเริ่มต้น `published_at:desc`) |

หน้า edit ไม่จดจำสถานะ UI ใด ๆ

## 3. `NewsEdit` (`/news/new`, `/news/:id/edit`)

### 3.1 โหมด

แถว header บนสุดถือลิงก์ย้อนกลับ ("← News" ไป `/news`) และ — เฉพาะเรคคอร์ดที่มีอยู่แล้ว — ปุ่ม **View History** ข้ามโมดูล (`<Can permission="activity_log.read" clusterId={PLATFORM_SCOPED_RECORD}>`, เปิด `ActivityTrailSheet` ที่ใช้ร่วมกัน) — สิ่งนี้อยู่ในตัว header ของหน้าเอง ไม่ได้อยู่ใน actions slot ของ `NewsMasthead` (§3.2) ซึ่งมีเฉพาะปุ่ม Edit ด้านล่างนั้น ตัวฟอร์มเองคือ `NewsMasthead` (§3.2) ตามด้วย grid สองคอลัมน์: การ์ด **Article** ฝั่งซ้าย, rail **Publish** แบบ sticky (บวกการ์ด **History**) ฝั่งขวา

- **Create** (`/news/new`): หัวข้อ "Add News" ผ่านตัว title editor ของ masthead; ทั้งสองการ์ดแก้ไขได้ทันที (ไม่มีการ์ด History — ยังไม่มี audit) ตอน submit: `POST /api/news`, toast แล้ว redirect ไป `/news/:id/edit` ของ id ที่สร้าง (`replace: true`) โดย fall back ไปหน้า list เมื่อ response ไม่มี id มา
- **View** (`/news/:id/edit`, ค่าเริ่มต้น): โหลดผ่าน `GET /api/news/:id` (skeleton ระหว่างรอ); ทุก field เป็น read-only — markdown ถูก render, สถานะเป็น badge ใน masthead, รูปที่ save ไว้เป็น banner ของ masthead ช่อง `actions` ของ masthead มีปุ่ม **Edit** ถูกห่อด้วย `<Can permission="news.update">`
- **Edit** (หลังกด toggle): toggle จะ snapshot ฟอร์มไว้; **Cancel** คืนค่า snapshot (ทิ้งการเลือกรูปที่ค้างอยู่ด้วย) และออกจากโหมดแก้ไข การเปลี่ยนแปลงที่ยังไม่ save — diff ของฟอร์มใด ๆ **หรือ** ไฟล์รูปที่ค้างอยู่ — จะติดอาวุธ navigation guard `useUnsavedChanges` และแสดงตัวบ่งชี้ "Unsaved changes" ใน sticky action bar (§3.7) เมื่อ update สำเร็จ หน้าจะ re-fetch และตกกลับเป็นโหมด view

### 3.2 `NewsMasthead`

การ์ดที่รวมสิ่งที่เคยกระจายอยู่หลายการ์ดเข้าด้วยกัน:

- **Cover** — ในโหมดแก้ไข, control `ImageUpload` (ดู §3.4) render แบบ inline; ในโหมด view, รูปที่ save ไว้เป็น banner สูง `h-40`–`h-48` (ซ่อนตัวเองเมื่อโหลด error) หรือกล่อง placeholder แบบ muted (ไอคอน `Newspaper`) เมื่อไม่มีรูป
- **แถว eyebrow** — status `Badge` (success/secondary/outline ตาม §3.5), ตัวบ่งชี้ reach (Globe "Global" หรือ Building2 "N business unit(s)") และ state note ต่อท้าย: `published_at` ที่ format แล้วเมื่อ publish, "Hidden from readers" เมื่อ archived หรือ "Not visible to readers" ขณะเป็น draft
- **Title** — หัวข้อเอง: `<h1>` ในโหมด view หรือ `<input>` ของหัวข้อ (จำเป็น, validate แบบ inline) ในโหมดแก้ไข
- **Actions** — ปุ่ม Edit (โหมด view, เฉพาะเรคคอร์ดที่มีอยู่แล้ว)

### 3.3 การ์ด Article

| Field | Control ในโหมดแก้ไข | การ validate |
|---|---|---|
| Body (Markdown) | `MarkdownEditor` — แท็บ **Write** (textarea แบบ monospace, ≥200 px, placeholder "Write your news content in Markdown...") และแท็บ **Preview** (`react-markdown` + `remark-gfm`: ตาราง GFM, list, code, blockquote) | ไม่มี — optional |
| Source URL | URL input; `ReadOnlyField` ในโหมด view | เมื่อไม่ว่าง: "Must be a valid http(s) URL" (blur + ก่อน submit) |
| Tags | `ChipInput` (§3.4a), disabled นอกโหมดแก้ไข | ไม่มีการ validate ฝั่ง client นอกเหนือกฎการ commit chip; server บังคับ ≤20 tags, ≤40 ตัวอักษรต่อ tag |

ในโหมด view markdown ถูก render แบบ read-only ในกล่อง muted

### 3.4 component `ImageUpload`

โซน drop เส้นประ ("Drag & drop an image here, or *browse*") ทำหน้าที่เป็น file picker ที่เปิดด้วยคลิก/คีย์บอร์ดไปด้วย ตอนนี้ render อยู่ในช่อง cover ของ masthead แทนที่จะเป็นการ์ดของตัวเอง การ validate ฝั่ง client จะ toast เมื่อปฏิเสธ: type ที่รับคือ JPEG/PNG/WebP/GIF, ≤5 MB ไฟล์ที่เลือกแล้วแสดง preview แบบ object-URL ในเครื่องพร้อมปุ่ม **Remove** ที่เคลียร์เฉพาะ*การเลือกที่ค้างอยู่*เท่านั้น — รูปที่ save ไว้แล้วลบออกไม่ได้ ทำได้เพียงแทนที่ (ดู [Permissions](/th/platform/news/permissions) §4)

ข้อพึงระวังฝั่ง server สองข้อที่ QA ควรรู้: backend ปฏิเสธ **GIF** เพิ่มเติม (`image/gif` ผ่าน picker แต่คืน 400 `BAD_FILE_TYPE`) และรูปที่ใหญ่กว่า **2048×2048 px** (400 `BAD_DIMENSIONS`) — ทั้งคู่ปรากฏเป็น form error "Failed to save news" ไม่ใช่ toast ตอนอัพโหลด รูปที่ค้างอยู่ที่ถูกทิ้ง (Cancel, save สำเร็จ หรือ `doc_version` conflict) จะเพิ่มค่า `imageResetSignal` เพื่อให้ preview ภายในของ control ไม่ค้างข้อมูลเก่า

### 3.4a component `ChipInput` (tags)

chip/tag input แบบทั่วไป (`components/ui/chip-input.tsx`) ที่นำมาใช้ซ้ำสำหรับ tags ของ News: ข้อความที่พิมพ์จะ commit เป็น chip ตอน Enter, comma หรือ Tab; Backspace ตอน draft ว่างจะลบ chip ตัวสุดท้าย; รายการ `suggestions` แบบ optional (ที่นี่คือ `GET /api/news/tags` กรองเอา tag ที่เลือกไปแล้วออก) render เป็น datalist ค่าเดินทางเป็น string เดียวที่ join ด้วย comma ภายใน; `NewsEdit` จะ lowercase, trim และ de-duplicate ทุกครั้งที่เปลี่ยนก่อนจัดเก็บเป็น array คำแนะนำ tag ถูก fetch เฉพาะในโหมด create หรือขณะแก้ไขเรคคอร์ดที่มีอยู่แล้ว

### 3.5 Publish rail

- **Status** — native select ที่มี Draft / Published / Archived (transition อิสระทุกทิศทาง); render เป็น badge สีของ masthead ในโหมด view
- **การกำหนดเป้าหมาย** — checkbox **"Visible to all business units"** (ติ๊กไว้เป็นค่าเริ่มต้นตอน create); การยกเลิกติ๊กเผย `BusinessUnitMultiSelect` (โหลดรายการ BU เต็มหนึ่งครั้ง, `perpage: -1`, เรียงตามชื่อ, มีช่องค้นหา name/code และการเลือกแบบ badge ที่ลบได้) การ validate ก่อน submit: ไม่ global + ศูนย์ BU → "Select at least one business unit, or enable \"Visible to all business units\"."; การติ๊กกล่อง global กลับคืนจะเคลียร์ error
- **Published At** — เป็น `ReadOnlyField` เสมอ พร้อม helper text: Set automatically when status becomes "Published". SPA ไม่เคยส่ง field นี้; server ประทับมันตอน publish ครั้งแรกและคงไว้หลังจากนั้น ([Data Model](/th/platform/news/data-model) §2.2)

### 3.6 การ์ด History (เฉพาะเรคคอร์ดที่มีอยู่แล้ว)

render เมื่อ `normalizeAudit()` บนเรคคอร์ดที่โหลดมาให้ actor `created` และ/หรือ `updated` (คือรูปแบบซ้อน `audit.*` หรือ fallback แบบแบน `created_at`/`created_by_name` อย่างใดอย่างหนึ่งที่ response ถืออยู่ — ไม่ใช่แค่ "มี key `audit`" ตรง ๆ) **ตั้งแต่ 2026-08-22** เนื้อหาคือ `AuditMeta` variant "header" ที่ใช้ร่วมกัน ไม่ใช่ตัว render timestamp แบบ absolute ที่เขียนเอง: บรรทัดเดียวอ่านว่า "Created `<เวลาสัมพัทธ์>` by `<name>` · Updated `<เวลาสัมพัทธ์>` by `<name>`" (แต่ละครึ่งถูกละไว้ถ้าไม่เข้าเงื่อนไข — `updated` จะปรากฏก็ต่อเมื่อเรคคอร์ดถูกแก้ไขจริงเท่านั้น) พร้อม timestamp แบบ absolute เต็มรูปแบบเป็น tooltip ตอน hover บนแต่ละครึ่ง อยู่ใต้ Publish rail, sticky คู่กันบน desktop

### 3.7 flow การ save

แถบ sticky ด้านล่าง (แสดงเฉพาะขณะแก้ไข) แสดงตัวบ่งชี้จุด "Unsaved changes" (หรือ "No changes") บวก **Cancel** และ **Save** (`Create News` / `Save Changes`, spinner ขณะกำลัง save, disabled เมื่อไม่มีอะไรเปลี่ยนบนเรคคอร์ดที่มีอยู่แล้ว) Save submit `{ title, contents?, url?, status, business_unit_ids, tags, doc_version? }` เมื่อมีไฟล์รูปที่ค้างอยู่ service จะสลับเป็น `multipart/form-data` — binary ใน field `image`, `business_unit_ids` และ `tags` ถูก encode เป็น string แบบ JSON และ `Content-Type` แบบ multipart ที่ระบุชัด (จำเป็น: axios instance ตั้งค่าเริ่มต้นเป็น JSON ซึ่งจะ serialize ตัว `FormData` ทิ้งไป) เมื่อไม่มีไฟล์จะส่ง JSON ธรรมดา โดยไม่แตะรูปที่ save ไว้

`doc_version` ที่ล้าสมัยตอน update จะคืน 409; SPA แสดง "This record was changed by someone else" ทิ้งการเลือกรูปที่ค้างอยู่ และ refetch เรคคอร์ดแทนที่จะแสดง error การ save แบบทั่วไป field error อื่น ๆ จาก API ผ่าน `parseApiError` map กลับลง field ของฟอร์ม; หลัง update สำเร็จ SPA จะ re-fetch เรคคอร์ด (response ของ `PUT` มีเพียง `{ id, doc_version }` — ดู [Data Model](/th/platform/news/data-model) §6) ปุ่มลอยของ Debug Sheet จะขยับขึ้น (`bottom-20`) ขณะแก้ไขเพื่อไม่ให้ชนกับ sticky action bar

## 4. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/NewsManagement.tsx`, `src/pages/newsManagement/NewsroomSummary.tsx` — คอลัมน์, Sheet ของ filter สถานะ/tag, ส่งออก CSV, bulk toolbar + dialog, gate `<Can>` (รวม View History ของ row), endpoint summary เฉพาะทาง, key ที่จดจำ
- `../carmen-platform/src/pages/NewsEdit.tsx`, `src/pages/newsEdit/NewsMasthead.tsx` — ฟอร์มแบบ masthead + สองคอลัมน์, toggle โหมด, การ validate, payload ของการ save, คีย์ลัด, ปุ่ม View History ในแถว header, การ์ด History ที่ใช้ `AuditMeta`
- `../carmen-platform/src/utils/audit.ts` — `normalizeAudit()` (ลำดับ nested-ก่อน-แบน, การซ่อนด้วย `everEdited`), variant cell/header ของ `AuditMeta` (เวลาสัมพัทธ์ + tooltip แบบ absolute)
- `../carmen-platform/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail,constants}.tsx` — ฟีเจอร์ View History; `AUDIT_RECORDING_STARTED_ON_PHASE_2` (2026-08-31)
- `../carmen-platform/src/utils/permissions.ts` — `PLATFORM_SCOPED_RECORD` sentinel `clusterId` ที่ gate ของ View History ใช้
- `../carmen-platform/src/components/MarkdownEditor.tsx` — แท็บ Write/Preview, preview แบบ GFM, การ render แบบ read-only
- `../carmen-platform/src/components/ImageUpload.tsx` — โซน drop, รายการ accept, เพดาน 5 MB, semantics ของ preview/remove ในเครื่อง
- `../carmen-platform/src/components/ui/chip-input.tsx` — การ parse/join chip ของ tag, การกรอง suggestion, กฎการ commit ด้วยคีย์บอร์ด
- `../carmen-platform/src/components/BusinessUnitMultiSelect.tsx` — การโหลด BU, การค้นหา, การเลือกแบบ badge
- `../carmen-platform/src/components/ReadOnlyField.tsx` — ตัว render field แบบ read-only ที่ใช้ร่วมกันในหน้า edit ที่ redesign แล้ว
- `../carmen-platform/src/services/newsService.ts` — `buildNewsFormData`, `getTags`, หมายเหตุ `Content-Type` แบบ multipart, การเดิน envelope
- `../carmen-platform/src/utils/docVersion.ts` — helper ของ optimistic-lock
- `../carmen-platform/src/components/KeyboardShortcuts.tsx` — binding ของ Ctrl/Cmd+S, Ctrl/Cmd+K, Escape

**Cross-link:** [หน้า landing ของ News](/th/platform/news) &nbsp;·&nbsp; [Data Model](/th/platform/news/data-model) &nbsp;·&nbsp; [Permissions](/th/platform/news/permissions)
