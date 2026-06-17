---
title: Applications — หน้าจอ UI (UI Screens)
description: list ApplicationManagement และฟอร์ม ApplicationEdit รวมถึง API Names selector แบบ accordion จัดกลุ่มและ fallback แบบ ChipInput ของมัน
published: true
date: 2026-06-17T08:00:00.000Z
tags: book/platform, applications, ui
editor: markdown
dateCreated: 2026-06-10T15:15:00.000Z
---

# Applications — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `ApplicationManagement` (`/applications`) · `ApplicationEdit` (`/applications/new`, `/applications/:id/edit`) &nbsp;·&nbsp; **Layout ของหน้า edit:** การ์ด "Application Details" การ์ดเดียวพร้อม toggle Edit &nbsp;·&nbsp; **UI เอกลักษณ์:** API Names selector — accordion จัดกลุ่มตามโมดูล, ช่อง filter, All/None ต่อโมดูล, label ปุ่มแบบ action อย่างเดียว &nbsp;·&nbsp; **Fallback:** การกรอก free-text แบบ `ChipInput` เมื่อการ fetch catalog ล้มเหลว &nbsp;·&nbsp; **สถานะ UI ที่จดจำ:** key `localStorage` 5 ตัวบนหน้า list

## 1. ภาพรวม

Applications ทำตามรูปแบบ Management/Edit สองหน้าจอมาตรฐานของ SPA (คัดลอกจาก Clusters): list แบบ `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce, filter แบบ Sheet, ส่งออก CSV และจดจำสถานะ; บวกฟอร์ม create/view/edit แบบการ์ดเดียว มีสองสิ่งที่เป็นของโมดูลนี้โดยเฉพาะ อย่างแรกคือการปฏิบัติกับ **App ID** — UUID ของเรคคอร์ดถูกแสดงแบบ read-only ในทั้งสองหน้าจอ เพราะมันคือ credential `x-app-id` ที่ operator ต้องคัดลอกไปใส่ใน configuration ของ client อย่างที่สองคือ **API Names selector** บนฟอร์ม edit ซึ่งเป็น component เอกลักษณ์ของโมดูล (§3.4): accordion ของ key ใน catalog จัดกลุ่มตามโมดูล แสดงเฉพาะขณะที่ "Allow all APIs" ไม่ถูกติ๊ก

ทั้งสองหน้าจอมาพร้อม **Debug Sheet** เฉพาะ dev (ปุ่มลอยสีเหลืองอำพัน, เฉพาะ `import.meta.env.DEV`) ที่เปิดเผย raw JSON ของ `GET /api-system/applications` (list) หรือ `GET /api-system/applications/:id` (edit) — วิธีที่เร็วที่สุดสำหรับ QA ในการยืนยัน envelope จริงและการซ้อนของ audit ทั้งคู่ยังลงทะเบียน global keyboard shortcuts ของ SPA (`useGlobalShortcuts`): บนหน้า list shortcut ค้นหาจะ focus ช่องค้นหา; บนฟอร์ม edit shortcut save จะ submit ขณะกำลังแก้ไข และ shortcut cancel จะออกจากโหมด edit (เฉพาะ route view/edit ไม่ใช่ create)

## 2. `ApplicationManagement` — list (`/applications`)

### 2.1 Layout และ action ใน header

Header: title "Application Management" / subtitle "Manage applications and their API access" พร้อมสอง action — **Export** (CSV ฝั่ง client ของหน้าที่โหลดอยู่: Name, App ID, Description, Access, Status; ไฟล์ `applications-<YYYY-MM-DD>.csv`; ถูก disable ขณะกำลังโหลดหรือว่างเปล่า) และ **Add Application** (นำทางไป `/applications/new`; ห่อด้วย `<Can permission="application.create">`)

### 2.2 การค้นหาและ filter

ช่องค้นหาแบบ debounce (400 ms) เหนือ `name`/`description` (ฝั่ง server ผ่านพารามิเตอร์ `search`; ช่อง input ไฮไลต์เป็นสีเหลืองขณะมี term ทำงานอยู่และมีปุ่ม clear แบบ inline) บวก Sheet **Filters** (description "Filter applications by status and device") ที่มีสองกลุ่ม: กลุ่ม **Status** — ปุ่ม toggle Active/Inactive ที่แปลเป็น query `advance` `{ where: { is_active } }` เมื่อมีการเลือกเพียงตัวเดียวพอดี — และ dropdown **Device** ที่มีตัวเลือก "All devices" (ล้าง filter) บวก `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`); device ที่เลือกจะเพิ่ม `{ where: { device } }` เข้าไปใน clause `advance` เดียวกัน filter ที่ทำงานอยู่แต่ละตัว (ทั้ง status และ device) นับรวมเข้า badge ของ filter และ render เป็น chip ใต้แถวค้นหา พร้อมปุ่มลบต่อ chip และลิงก์ "Clear all"

### 2.3 คอลัมน์

| คอลัมน์ | การ render |
|---|---|
| Name | ลิงก์ไป `/applications/:id/edit` |
| App ID | UUID ของเรคคอร์ดเป็นข้อความ monospace สีจาง ค่าเต็มอยู่ใน attribute `title` ด้วย (tooltip ตอน hover); sort ไม่ได้ |
| Description | ข้อความสีจาง, `-` เมื่อว่าง; sort ไม่ได้ |
| Access | badge แบบ outline ชิดขวา: **All APIs** เมื่อ `allow_all` ไม่เช่นนั้น **N APIs** จาก `api_names.length` (0 เมื่อไม่มี); sort ไม่ได้ |
| Status | badge Active (success) / Inactive (secondary) จาก `is_active` |
| Device | badge แบบ secondary จาก `device`, fallback เป็น `web` เมื่อไม่มี |
| Created | `created_at` (`YYYY-MM-DD HH:mm:ss`, เวลาท้องถิ่นของเบราว์เซอร์) พร้อม `created_by_name` บนบรรทัดถัดไป — flatten จาก shape ซ้อน `audit.created` `{ at, name }` เมื่อ API ซ้อนมา |
| Updated | shape เดียวกันจาก `audit.updated`; render `-` เมื่อ `updated_at === created_at` |
| Actions | dropdown `⋯` — ดู §2.4 |

ค่าเริ่มต้นของการ sort คือ `name:asc` การโหลดครั้งแรก render `TableSkeleton` แบบ 8 คอลัมน์; การโหลดครั้งถัด ๆ ไปวาง scrim "Loading applications..." ทับตารางเดิม

### 2.4 action ของ row และ dialog ลบ

dropdown ของ action มี **Edit** (นำทางไป route edit) ห่อด้วย `<Can permission="application.update">` และ **Delete** (สไตล์ destructive) ห่อด้วย `<Can permission="application.delete">` Delete เปิด `ConfirmDialog` ("Delete Application — Are you sure you want to delete this application? This action cannot be undone."); การยืนยันเรียก `DELETE /api-system/applications/:id`, toast แล้ว refetch หน้านั้น ไม่มี affordance สำหรับลบที่อื่นใดในโมดูลนี้

### 2.5 Empty state และสถานะ UI ที่จดจำ

ผลลัพธ์ว่างเปล่า render การ์ด `EmptyState` (ไอคอน AppWindow) ที่ title เป็น "No applications yet" เสมอ; มีเพียง description ข้างใต้ที่เปลี่ยนไป — `No applications matching "<term>"` เมื่อมี search term ทำงานอยู่ หรือ "Get started by creating your first application." พร้อม CTA **Add Application** แบบ inline เมื่อไม่มี (หมายเหตุ: CTA นี้ *ไม่ได้*ถูกห่อด้วย `<Can>` — ดู [Permissions](./permissions.md))

| Key `localStorage` | ชนิดที่เก็บ | จดจำ |
|---|---|---|
| `search_applications` | string | term การค้นหา |
| `filters_applications` | JSON string array | การเลือก filter ของ Status |
| `devicefilter_applications` | string | การเลือก filter ของ Device (ว่าง = ทุกอุปกรณ์) |
| `page_applications` | number string | หน้าปัจจุบัน |
| `perpage_applications` | number string | ขนาดหน้า |
| `sort_applications` | string | การ sort (`column:dir`, ค่าเริ่มต้น `name:asc`) |

หน้า edit ไม่จดจำสถานะ UI ใด ๆ

## 3. `ApplicationEdit` (`/applications/new`, `/applications/:id/edit`)

### 3.1 โหมด create (`/applications/new`)

Title "Add Application"; การ์ด "Application Details" การ์ดเดียวแก้ไขได้ทันที แถว App ID ไม่มี — UUID มีอยู่หลังจาก server สร้าง row แล้วเท่านั้น ตอน submit SPA validate `name` (required; validate ตอน blur ด้วย โดย error ถูกล้างตอน focus), เรียก `POST /api-system/applications`, toast แล้ว redirect ไป `/applications/:id/edit` ของ id ที่ถูกสร้าง (`replace: true`) โดย fallback ไปหน้า list เมื่อ response ไม่มี id มาด้วย

### 3.2 โหมด view (`/applications/:id/edit`, ค่าเริ่มต้น)

โหลดผ่าน `GET /api-system/applications/:id` (placeholder แบบ skeleton ระหว่างรอ) และ render แบบ read-only: title "Application Details", ทุก field เป็นกล่องสีจางแบบ static, **Status** และ **API Access** เป็น badge (API Access อ่านว่า "All APIs" หรือ "N selected") header มีลูกศรย้อนกลับไป `/applications` และปุ่ม **Edit** ห่อด้วย `<Can permission="application.update">` — ถ้าไม่มี key นั้น หน้านี้จะ read-only ถาวร เพราะ Save เข้าถึงไม่ได้นอกโหมด edit

เมื่อ `allow_all` ปิดอยู่และมี names ที่ได้รับ grant บล็อก **API Names** จะแสดงการเลือกเป็น badge จัดกลุ่มแบบ read-only: หนึ่ง sub-list ต่อโมดูล (`groupApiNames` เหนือ `api_names` ที่โหลดมา) แต่ละ badge มี label เป็น segment ของ action เท่านั้น (`actionOf`) และถือ key เต็มใน attribute `title` ของมัน เมื่อไม่มี names ที่ได้รับ grant จะแสดง `-`

### 3.3 โหมด edit — field

toggle Edit จะ snapshot ฟอร์มปัจจุบัน แล้วสลับการ์ดเป็นแก้ไขได้:

| Field | Control ในโหมด edit | หมายเหตุ |
|---|---|---|
| Name * | Text input | Required; validate ตอน blur + ก่อน submit |
| App ID | — | เป็นกล่อง monospace แบบ read-only แสดง UUID ของเรคคอร์ดเสมอ (ถูกตัดเมื่อจอแคบ); server เป็นผู้ generate แก้ไขไม่ได้เลย |
| Description | Text input | Optional |
| Device | `<select>` ของ `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`) | ค่าเริ่มต้นเป็น `web` (และเป็น fallback เมื่อค่าที่โหลดมาอยู่นอกชุดตัวเลือก); render เป็น Badge แบบ secondary ในโหมด view |
| Active | Checkbox | render เป็น badge Status ในโหมด view |
| Allow all APIs | Checkbox | render เป็น badge API Access ในโหมด view; การติ๊กมันซ่อนบล็อก API Names ทั้งหมด |
| API Names | selector แบบ accordion จัดกลุ่ม (§3.4) | เฉพาะเมื่อ "Allow all APIs" ไม่ถูกติ๊ก |

**Save** (`Save Changes` / `Create Application` พร้อม spinner ขณะกำลังบันทึก) submit ฟอร์ม; **Cancel** คืนค่า snapshot ก่อนแก้ไขและออกจากโหมด edit (ในโหมด create จะนำทางกลับไปหน้า list) การเปลี่ยนแปลงที่ยังไม่บันทึก (diff ใด ๆ เทียบกับ snapshot ขณะแก้ไข) จะเปิดใช้งาน navigation guard `useUnsavedChanges` และ global keyboard shortcuts สั่ง save และ cancel ได้ เมื่ออัพเดทสำเร็จ หน้าจะ **refetch application แล้วถอยกลับสู่โหมด view**

### 3.4 API Names selector

component เอกลักษณ์ของโมดูล render แบบ inline ในฟอร์ม (ไม่มีไฟล์ component แยกต่างหาก) ตัวเลือกมาจาก `GET /api-system/applications/api-catalog` fetch ครั้งเดียวตอน mount; จนกว่ากลุ่มจะมาถึง กล่องจะแสดง "Loading catalog…"

- **Accordion จัดกลุ่มตามโมดูล** — หนึ่ง row แบบพับเก็บได้ต่อ `ApiCatalogGroup` ใน scroll container ที่มีเส้นขอบ (`max-h-80`, ~320 px) header ของแต่ละโมดูลอัดแน่นด้วย: chevron (expand/collapse), ชื่อโมดูล, badge นับ `selected/total` (เปลี่ยนเป็น variant แบบ filled ทันทีที่มีการเลือกอะไรก็ตาม) และปุ่ม **All/None** ที่เลือกหรือล้างทั้งโมดูลในคลิกเดียว
- **ช่อง filter** — match กับชื่อโมดูล *หรือ* `api_name` ใดก็ได้ (ไม่สนตัวพิมพ์ใหญ่เล็ก) การ match ที่ชื่อโมดูลแสดงทั้งกลุ่ม; ไม่เช่นนั้นกลุ่มจะแคบลงเหลือเฉพาะ names ที่ match กลุ่มที่ match จะ **auto-expand** ขณะ filter ทำงานอยู่ (การ toggle chevron ด้วยมือถูกระงับ); filter ที่ไม่ match อะไรเลยแสดง `No API names matching "<term>"`
- **Expand all / Collapse all** — toggle เดียวที่มีผลกับกลุ่มที่*มองเห็น*อยู่ในปัจจุบัน จึงประกอบเข้ากับ filter ได้
- **ปุ่ม toggle ต่อ key** — ภายในกลุ่มที่ expand แล้ว แต่ละ `api_name` เป็นปุ่มเล็กที่มี label เป็น **segment ของ action เท่านั้น** (`actionOf(api)`) โดย key เต็มอยู่ใน attribute `title`; key ที่ถูกเลือก render แบบ filled พร้อม glyph `X` ตัวนับ "N selected" แบบ running อยู่ใต้กล่อง
- **Fallback แบบ `ChipInput`** — ถ้าการ fetch catalog ล้มเหลว (`catalogFailed`) selector จะลดรูปเป็น chip input แบบ free-text ("Type an api_name and press Enter") grant จึงยังแก้ไขได้โดยไม่มี catalog; รายการถูก join ด้วย comma เข้า array `api_names` เดียวกัน

การเลือกอยู่ใน form state แบบแบน (`api_names: string[]`); ตอน save service แปลงมันเป็น `details.add[]` ของ payload การเขียน (semantics แบบ replace — ดู [Data Model](./data-model.md) §5)

## 4. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/ApplicationManagement.tsx` — หน้า list: คอลัมน์, Sheet ของ filter, ส่งออก CSV, gate `<Can>`, การ flatten audit, key ที่จดจำ
- `../carmen-platform/src/pages/ApplicationEdit.tsx` — ฟอร์ม, การแสดง App ID, ทางแยก `allow_all`, accordion selector แบบ inline (≈ บรรทัด 380–550), fallback แบบ ChipInput, flow ของการ save
- `../carmen-platform/src/services/applicationService.ts` — endpoint, `toWritePayload`, `getApiCatalog` พร้อม fallback การจัดกลุ่ม
- `../carmen-platform/src/utils/apiCatalog.ts` — `moduleOf` / `actionOf` / `groupApiNames` (ใช้ร่วมกันโดย selector และมุมมอง badge แบบ read-only)
- `../carmen-platform/CLAUDE.md` — ส่วน "Application Management Specifics" (ความไม่สมมาตรของ read/write, รูปแบบ catalog แบบจัดกลุ่ม)

**Cross-link:** [หน้า landing ของ Applications](/th/platform/applications) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
