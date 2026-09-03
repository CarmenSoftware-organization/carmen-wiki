---
title: Applications — หน้าจอ UI (UI Screens)
description: list ApplicationManagement และฟอร์ม ApplicationEdit รวมถึง API Names selector แบบ accordion จัดกลุ่มและ fallback แบบ ChipInput ของมัน
published: true
date: 2026-07-29T07:21:27.000Z
tags: book/platform, applications, ui
editor: markdown
dateCreated: 2026-06-10T15:15:00.000Z
---

# Applications — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `ApplicationManagement` (`/applications`) · `ApplicationEdit` (`/applications/new`, `/applications/:id/edit`) &nbsp;·&nbsp; **ใหม่ตั้งแต่ sync ก่อนหน้า:** แถบสรุป `ApplicationRegistrySummary` (list), `ApplicationIdentityHero` (หน้า edit), App ID + Description ยุบเข้าคอลัมน์ Name (ไม่ใช่คอลัมน์แยกอีกต่อไป), layout ของ edit เขียนใหม่จากการ์ดเดียวเป็น hero + สองคอลัมน์ API-access/Settings, แถบ Save แบบ sticky ด้านล่าง, gate not-found, optimistic locking ด้วย `doc_version` &nbsp;·&nbsp; **Layout ของหน้า edit:** ยังคงเป็น toggle view/edit (ต่างจาก clusters/business-units ที่เขียนใหม่เป็น one-document) &nbsp;·&nbsp; **UI เอกลักษณ์:** API Names selector — accordion จัดกลุ่มตามโมดูล, ช่อง filter, All/None ต่อโมดูล, label ปุ่มแบบ action อย่างเดียว &nbsp;·&nbsp; **Fallback:** การกรอก free-text แบบ `ChipInput` เมื่อการ fetch catalog ล้มเหลว &nbsp;·&nbsp; **สถานะ UI ที่จดจำ:** key `localStorage` 5 ตัวบนหน้า list

## 1. ภาพรวม

Applications ทำตามรูปแบบ Management/Edit สองหน้าจอมาตรฐานของ SPA: list แบบ `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce, filter แบบ Sheet, ส่งออก CSV, แถบสรุป **Registry** และจดจำสถานะ; บวกหน้า create/view/edit ที่ตั้งแต่ sync ก่อนหน้าถูกเขียนใหม่จากการ์ด "Application Details" การ์ดเดียว เป็น `ApplicationIdentityHero` เหนือ layout สองคอลัมน์ **API access** / **Settings** มีสองสิ่งที่ยังคงเป็นของโมดูลนี้โดยเฉพาะ อย่างแรกคือการปฏิบัติกับ **App ID** — UUID ของเรคคอร์ดถูกแสดงแบบ read-only ตอนนี้ผ่าน chip ที่ copy ได้ใน hero (และบนหน้า list อยู่ใต้ชื่อ application แบบ inline) เพราะมันคือ credential `x-app-id` ที่ operator ต้องคัดลอกไปใส่ใน configuration ของ client อย่างที่สองคือ **API Names selector** ซึ่งเป็น component เอกลักษณ์ของโมดูล (§3.4): accordion ของ key ใน catalog จัดกลุ่มตามโมดูล แสดงเฉพาะขณะที่ "Allow all APIs" ไม่ถูกติ๊ก (มี banner เตือนแสดงแทนเมื่อ `allow_all` เปิดอยู่)

ทั้งสองหน้าจอมาพร้อม **Debug Sheet** เฉพาะ dev (ปุ่มลอยสีเหลืองอำพัน, เฉพาะ `import.meta.env.DEV`) ที่เปิดเผย raw JSON ของ `GET /api-system/applications` (list) หรือ `GET /api-system/applications/:id` (edit) — วิธีที่เร็วที่สุดสำหรับ QA ในการยืนยัน envelope จริงและการซ้อนของ audit ทั้งคู่ยังลงทะเบียน global keyboard shortcuts ของ SPA (`useGlobalShortcuts`): บนหน้า list shortcut ค้นหาจะ focus ช่องค้นหา; บนฟอร์ม edit shortcut save จะ submit ขณะกำลังแก้ไข และ shortcut cancel จะออกจากโหมด edit (เฉพาะ route view/edit ไม่ใช่ create)

## 2. `ApplicationManagement` — list (`/applications`)

### 2.1 Layout และ action ใน header

Header (`PageHeader`): title "Application Management" / subtitle "Manage applications and their API access" พร้อมสอง action — **Export** (CSV ฝั่ง client ของหน้าที่โหลดอยู่: Name, App ID, Description, Access, Status; ไฟล์ `applications-<YYYY-MM-DD>.csv`; ถูก disable ขณะกำลังโหลดหรือว่างเปล่า) และ **Add Application** (นำทางไป `/applications/new`; ห่อด้วย `<Can permission="application.create">`) ใต้ header คือแถบสรุป **Registry** (§2.1a) แล้วตามด้วยแถวค้นหา/filter

### 2.1a แถบ Registry

การ์ด `ApplicationRegistrySummary` สรุป **application ทุกตัว** (fetch แบบไม่แบ่งหน้าแยกต่างหาก `perpage: -1` ไม่ใช่แค่หน้าปัจจุบัน):

- จำนวนรวมขนาดใหญ่ พร้อม "`<n>` active" / "`<n>` active · `<n>` inactive" ข้างล่าง
- แถบสัดส่วน **"API access scope"** — full-access (`allow_all`, ใช้สีเตือนเพราะ app ที่ไม่จำกัดควรถูก audit) เทียบกับ scoped (รายการระบุชัด) พร้อม legend; รายการ legend "Full access" จะสลับเป็นไอคอนสามเหลี่ยมเตือนเมื่อจำนวนไม่ใช่ศูนย์
- ส่วนแบ่ง **"Devices"** — หนึ่ง chip ต่อค่า device ที่ใช้งานอยู่ เรียงตาม `web`/`mobile`/`desktop`/`pos` แล้วตามด้วยตัวอักษร แต่ละอันแสดงจำนวน

แสดง skeleton ขณะโหลดและสถานะ error/retry แบบ inline เมื่อ fetch ล้มเหลว — ตารางหลักไม่ได้รับผลกระทบไม่ว่ากรณีใด

### 2.2 การค้นหาและ filter

ช่องค้นหาแบบ debounce (400 ms) เหนือ `name`/`description` (ฝั่ง server ผ่านพารามิเตอร์ `search`) บวก Sheet **Filters** (description "Filter applications by status and device") ที่มีสองกลุ่ม: กลุ่ม **Status** — ปุ่ม toggle Active/Inactive ที่แปลเป็น query `advance` `{ where: { is_active } }` เมื่อมีการเลือกเพียงตัวเดียวพอดี — และ dropdown **Device** ที่มีตัวเลือก "All devices" (ล้าง filter) บวก `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`); device ที่เลือกจะเพิ่ม `{ where: { device } }` เข้าไปใน clause `advance` เดียวกัน filter ที่ทำงานอยู่แต่ละตัว (ทั้ง status และ device) นับรวมเข้า badge ของ filter และ render เป็น chip ใต้แถวค้นหา พร้อมปุ่มลบต่อ chip และลิงก์ "Clear all"

### 2.3 คอลัมน์

**คอลัมน์ App ID และ Description ไม่มีอยู่แยกต่างหากอีกต่อไป** — ทั้งคู่ถูกยุบเข้า Name ซึ่งเป็นการเปลี่ยนแปลง layout ตั้งแต่ sync ก่อนหน้า (สะท้อนตาราง "แบบ report-templates" ที่นำมาใช้ทั่วทั้ง SPA):

| คอลัมน์ | การ render |
|---|---|
| Name | ซ้อนกันเล็ก ๆ: ชื่อ (ลิงก์ไป `/applications/:id/edit`), UUID ของเรคคอร์ดข้างล่างเป็น monospace สีจางพร้อมปุ่ม copy-to-clipboard แบบ inline (สลับไอคอน `Copy`/`Check`, ยืนยัน 2 วินาที, toast ตอน copy) และคำอธิบาย (ถ้ามี) ข้างล่างนั้นด้วยข้อความสีจางขนาดเล็กกว่า |
| Access | badge แบบ outline ชิดขวา: **All APIs** เมื่อ `allow_all` ไม่เช่นนั้น **N APIs** จาก `api_names.length` (0 เมื่อไม่มี); sort ไม่ได้ |
| Device | badge แบบ secondary จาก `device`, fallback เป็น `web` เมื่อไม่มี |
| Status | badge Active (success) / Inactive (secondary) จาก `is_active` |
| Created | `created_at` (`YYYY-MM-DD HH:mm:ss`, เวลาท้องถิ่นของเบราว์เซอร์) พร้อม `created_by_name` บนบรรทัดถัดไป — flatten จาก shape ซ้อน `audit.created` `{ at, name }` เมื่อ API ซ้อนมา |
| Updated | shape เดียวกันจาก `audit.updated`; render `-` เมื่อ `updated_at === created_at` |
| Actions | dropdown `⋯` — ดู §2.4 |

ค่าเริ่มต้นของการ sort คือ `name:asc` การโหลดครั้งแรก render `TableSkeleton` ตามจำนวนคอลัมน์ปัจจุบัน; การโหลดครั้งถัด ๆ ไปวาง scrim "Loading applications..." ทับตารางเดิม

### 2.4 action ของ row และ dialog ลบ

dropdown ของ action มี **Edit** (นำทางไป route edit) ห่อด้วย `<Can permission="application.update">` และ **Delete** (สไตล์ destructive) ห่อด้วย `<Can permission="application.delete">` Delete เปิด `ConfirmDialog` ("Delete Application — Are you sure you want to delete this application? This action cannot be undone."); การยืนยันเรียก `DELETE /api-system/applications/:id`, toast แล้ว refetch หน้านั้น (และ reload แถบ Registry) ไม่มี affordance สำหรับลบที่อื่นใดในโมดูลนี้

### 2.5 Empty state และสถานะ UI ที่จดจำ

ผลลัพธ์ว่างเปล่า render การ์ด `EmptyState` (ไอคอน AppWindow) ที่ title เป็น "No applications yet" เสมอ; มีเพียง description ข้างใต้ที่เปลี่ยนไป — `No applications matching "<term>"` เมื่อมี search term ทำงานอยู่ หรือ "Get started by creating your first application." พร้อม CTA **Add Application** แบบ inline เมื่อไม่มี **แก้ไขจาก sync ก่อนหน้า: CTA นี้ตอนนี้ถูกห่อด้วย `<Can permission="application.create">` แล้ว** เหมือนปุ่ม header — ช่องว่างที่เคยพบใน [Permissions](./permissions.md) ปิดแล้ว

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

Title "Add Application" (`PageHeader`, ไม่มี hero — hero ต้องมี `id` อยู่แล้วสำหรับ chip App ID และบรรทัด audit ของมัน) การ์ดทั้งสอง (API access, Settings) render แบบแก้ไขได้ทันทีใน layout สองคอลัมน์ตามที่อธิบายใน §3.3 ตอน submit SPA validate `name` (required; validate ตอน blur ด้วย โดย error ถูกล้างตอน focus), เรียก `POST /api-system/applications` (payload มี `doc_version: undefined` ซึ่ง client ทิ้งไป), toast แล้ว redirect ไป `/applications/:id/edit` ของ id ที่ถูกสร้าง (`replace: true`) โดย fallback ไปหน้า list เมื่อ response ไม่มี id มาด้วย

### 3.2 โหมด view (`/applications/:id/edit`, ค่าเริ่มต้น)

โหลดผ่าน `GET /api-system/applications/:id` (skeleton แบบ hero + สองการ์ดระหว่างรอ ตรงกับ layout ที่โหลดแล้วเป๊ะ ๆ) สถานะ **not-found** เฉพาะ (ใหม่ตั้งแต่ sync ก่อนหน้า) แทนที่ shell ทั้งหมดด้วย `EmptyState` ("Application not found... Back to applications") เมื่อ id หา record ที่ยังใช้งานอยู่ไม่เจอ แทนที่จะ render หน้า edit ทับข้อมูลว่างเปล่า

เหนือฟอร์มคือ **`ApplicationIdentityHero`**: กล่อง avatar ไอคอน `AppWindow`, ชื่อเป็น `<h1>` ของหน้า, badge Device และ Active/Inactive, chip App ID (monospace พร้อมปุ่ม copy ของตัวเอง) แสดงเมื่อ record มีอยู่แล้ว, บรรทัดสรุปการเข้าถึง ("Full access to every endpoint" สีเตือนพร้อมไอคอนสามเหลี่ยมเตือน หรือ "`<n>` endpoint(s) across `<m>` module(s)" / "No endpoints granted yet" ด้วยข้อความสีจาง) และบรรทัด audit Created/Updated ในโหมด view actions slot ของ hero แสดงปุ่ม **Edit** เดียวห่อด้วย `<Can permission="application.update">` — ถ้าไม่มี key นั้น หน้านี้จะ read-only ถาวร เพราะ Save เข้าถึงไม่ได้นอกโหมด edit

ส่วน body สองคอลัมน์ render แบบ read-only ในโหมด view: การ์ด **API access** แสดง banner เตือน (`allow_all`) หรือเมื่อมี names ที่ได้รับ grant จะแสดง badge จัดกลุ่มแบบ read-only — หนึ่ง sub-list ต่อโมดูล (`groupApiNames` เหนือ `api_names` ที่โหลดมา) แต่ละ badge มี label เป็น segment ของ action เท่านั้น (`actionOf`) และถือ key เต็มใน attribute `title` ของมัน (หรือ "No endpoints granted." เมื่อว่าง) — และการ์ด **Settings** แสดง Name/Description/Device/Status เป็น field/badge แบบ static

### 3.3 โหมด edit — layout สองคอลัมน์

toggle Edit (ปุ่ม action บน hero) จะ snapshot ฟอร์มปัจจุบัน แล้วสลับทั้งสองการ์ดเป็นแก้ไขได้ **การ์ด "Application Details" การ์ดเดียวจาก sync ก่อนหน้าไม่มีอยู่อีกต่อไป** — ฟอร์มตอนนี้เป็น `grid-cols-1 lg:grid-cols-[1fr_minmax(300px,340px)]`: คอลัมน์ซ้ายกว้างถือการ์ด **"API access"** (title + description "Which endpoints this app may call.") พร้อม checkbox `allow_all` และ selector; คอลัมน์ขวาแคบกว่าถือการ์ด **"Settings"** แบบ **sticky** พร้อม field ที่เหลือ:

| Field | Control ในโหมด edit | หมายเหตุ |
|---|---|---|
| Full access to every API (`allow_all`) | Checkbox ในการ์ด API access | label "Full access to every API" พร้อมบรรทัดคำอธิบาย; การติ๊กแทนที่ selector ด้วย banner เตือน (แสดงในโหมด view ด้วย) |
| API Names | selector แบบ accordion จัดกลุ่ม (§3.4) ในการ์ด API access | เฉพาะเมื่อ `allow_all` ไม่ถูกติ๊ก |
| Name * | Text input ในการ์ด Settings | Required; validate ตอน blur + ก่อน submit |
| Description | Text input ในการ์ด Settings | Optional |
| Device | `<select>` ของ `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`) ในการ์ด Settings | ค่าเริ่มต้นเป็น `web` (และเป็น fallback เมื่อค่าที่โหลดมาอยู่นอกชุดตัวเลือก); render เป็น Badge แบบ secondary ตัวพิมพ์ใหญ่แรกในโหมด view |
| Active (`is_active`) | Checkbox ในการ์ด Settings | render เป็น badge Status ในโหมด view |

**App ID ไม่ใช่ field row ของการ์ด Settings อีกต่อไป** — ตอนนี้อยู่เฉพาะใน chip ของ hero (§3.2) ไม่ซ้ำในฟอร์ม

แถบ **sticky ด้านล่าง** (ใหม่ตั้งแต่ sync ก่อนหน้า แทนที่แถว Save/Cancel ในการ์ดเดิม) แสดง **Save Changes** / **Create Application** (พร้อม spinner ขณะบันทึก) และ **Cancel** บวกตัวบ่งชี้ "Unsaved changes" / "No changes" ติดอยู่กับด้านล่างของ viewport ขณะ `editing` เป็น true Cancel คืนค่า snapshot ก่อนแก้ไขและออกจากโหมด edit (ในโหมด create จะนำทางกลับไปหน้า list) การเปลี่ยนแปลงที่ยังไม่บันทึก (diff ใด ๆ เทียบกับ snapshot ขณะแก้ไข) จะเปิดใช้งาน navigation guard `useUnsavedChanges` และ global keyboard shortcuts สั่ง save และ cancel ได้ เมื่ออัพเดทสำเร็จ หน้าจะ **refetch application (รีเฟรช `doc_version` ด้วย) แล้วถอยกลับสู่โหมด view**; การ save ที่ล้าหลัง (`409`) แสดง toast แจ้ง conflict และโหลดใหม่แทนที่จะเขียนทับ

### 3.4 API Names selector

component เอกลักษณ์ของโมดูล render แบบ inline ในการ์ด API access (ไม่มีไฟล์ component แยกต่างหาก) ตัวเลือกมาจาก `GET /api-system/applications/api-catalog` fetch ครั้งเดียวตอน mount; จนกว่ากลุ่มจะมาถึง กล่องจะแสดง "Loading catalog…" และ catalog ที่ว่างเปล่าจริง ๆ ("No API endpoints are defined in the catalog yet.") ตอนนี้แยกออกจากสถานะกำลังโหลดแล้ว (แก้ไขตั้งแต่ sync ก่อนหน้า)

- **Accordion จัดกลุ่มตามโมดูล** — หนึ่ง row ต่อ `ApiCatalogGroup` ใน scroll container ที่มีเส้นขอบ (`max-h-80`, ~320 px) แต่ละ row ของโมดูลเป็น tap target ≥44px จริง (`min-h-11` บน toggle ไม่ใช่ overlay) มันอัดแน่นด้วย: chevron (expand/collapse), ชื่อโมดูล, badge นับ `selected/total` (เปลี่ยนเป็น variant แบบ filled ทันทีที่มีการเลือกอะไรก็ตาม) และปุ่ม **All/None** (มี overlay `HIT_SLOP_44` บนปุ่มขนาดกะทัดรัดนี้ เพราะมีแค่หนึ่งปุ่มต่อ row ของโมดูล) ที่เลือกหรือล้างทั้งโมดูลในคลิกเดียว
- **ช่อง filter** — match กับชื่อโมดูล *หรือ* `api_name` ใดก็ได้ (ไม่สนตัวพิมพ์ใหญ่เล็ก) การ match ที่ชื่อโมดูลแสดงทั้งกลุ่ม; ไม่เช่นนั้นกลุ่มจะแคบลงเหลือเฉพาะ names ที่ match กลุ่มที่ match จะ **auto-expand** ขณะ filter ทำงานอยู่ (การ toggle chevron ด้วยมือถูกระงับ); filter ที่ไม่ match อะไรเลยแสดง `No API names matching "<term>"`
- **Expand all / Collapse all** — toggle เดียวที่มีผลกับกลุ่มที่*มองเห็น*อยู่ในปัจจุบัน จึงประกอบเข้ากับ filter ได้
- **ปุ่ม toggle ต่อ key** — ภายในกลุ่มที่ expand แล้ว แต่ละ `api_name` เป็นปุ่มเล็กที่มี label เป็น **segment ของ action เท่านั้น** (`actionOf(api)`) โดย key เต็มอยู่ใน attribute `title`; key ที่ถูกเลือก render แบบ filled พร้อม glyph `X` **chip เหล่านี้จงใจไม่ได้รับ overlay hit-slop 44px** — ที่ขนาดกะทัดรัด (`h-7`) พร้อม gap ระหว่างแถวแค่ 6px overlay 44px ที่อยู่ตรงกลางจะล้นเกินขอบมากกว่า gap ทำให้ tap zone ของแถวที่อยู่ติดกันแนวตั้งซ้อนทับกัน บน surface ที่มอบสิทธิ์แบบนี้ tap ที่ซ้อนทับอาจมอบ API ผิดตัวได้ จึง chip เหล่านี้ยังคงขนาดเล็กกว่าที่ไม่ซ้อนทับแทน (การตัดสินใจ trade-off ด้าน accessibility ที่จงใจ ไม่ใช่การมองข้าม) ตัวนับ "N selected" แบบ running อยู่ใต้กล่อง
- **Fallback แบบ `ChipInput`** — ถ้าการ fetch catalog ล้มเหลว (`catalogFailed`) selector จะลดรูปเป็น chip input แบบ free-text ("Type an api_name and press Enter") อยู่หลัง banner retry ของ `FetchErrorState` grant จึงยังแก้ไขได้โดยไม่มี catalog; รายการถูก join ด้วย comma เข้า array `api_names` เดียวกัน

การเลือกอยู่ใน form state แบบแบน (`api_names: string[]`); ตอน save service แปลงมันเป็น `details.add[]` ของ payload การเขียน (semantics แบบ replace — ดู [Data Model](./data-model.md) §5)

## 4. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/ApplicationManagement.tsx` และ `applicationManagement/ApplicationRegistrySummary.tsx` — หน้า list: แถบสรุป Registry, การยุบ App-ID/description เข้าคอลัมน์ Name, Sheet ของ filter, ส่งออก CSV, gate `<Can>` (รวม CTA ของ empty-state ที่แก้ไขแล้ว), การ flatten audit, key ที่จดจำ
- `../carmen-platform/src/pages/ApplicationEdit.tsx` และ `applicationEdit/ApplicationIdentityHero.tsx` — การ์ด hero, ฟอร์มสองคอลัมน์ API-access/Settings, ทางแยก `allow_all`, accordion selector แบบ inline, fallback แบบ ChipInput, flow การ save ที่รู้จัก `doc_version`, gate not-found
- `../carmen-platform/src/utils/docVersion.ts` — helper optimistic-lock
- `../carmen-platform/src/services/applicationService.ts` — endpoint, `toWritePayload` (รวม `doc_version`), `getApiCatalog` พร้อม fallback การจัดกลุ่ม
- `../carmen-platform/src/utils/apiCatalog.ts` — `moduleOf` / `actionOf` / `groupApiNames` (ใช้ร่วมกันโดย selector และมุมมอง badge แบบ read-only)
- `../carmen-platform/CLAUDE.md` — ส่วน "Application Management Specifics" (ความไม่สมมาตรของ read/write, รูปแบบ catalog แบบจัดกลุ่ม)

**Cross-link:** [หน้า landing ของ Applications](/th/platform/applications) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
