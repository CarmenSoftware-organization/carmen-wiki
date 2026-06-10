---
title: Print Template Mapping — หน้าจอ UI (UI Screens)
description: list แบบการ์ดจัดกลุ่ม PrintTemplateMappingManagement (การเบี่ยงเบนโดยเจตนาจากรูปแบบ DataTable) และฟอร์ม view/edit PrintTemplateMappingEdit พร้อม select เทมเพลตที่ลอย match ขึ้นด้านบน
published: true
date: 2026-06-10T15:30:00.000Z
tags: book/platform, print-template-mapping, ui
editor: markdown
dateCreated: 2026-06-10T15:30:00.000Z
---

# Print Template Mapping — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `PrintTemplateMappingManagement` (`/print-template-mapping`) · `PrintTemplateMappingEdit` (`/print-template-mapping/new`, `/print-template-mapping/:id/edit`) &nbsp;·&nbsp; **Layout ของ list:** sub-table แบบการ์ดจัดกลุ่มต่อชนิดเอกสาร — **ไม่ใช่** `DataTable` มาตรฐาน; ไม่มีค้นหา, ไม่มี CSV, ไม่มีตัวควบคุมการแบ่งหน้า &nbsp;·&nbsp; **Layout ของ edit:** การ์ด "Mapping" เดียวพร้อม toggle view/edit &nbsp;·&nbsp; **UI ที่เป็นเอกลักษณ์:** select ของ Report Template ลอย match ของ `kind="print"` + `report_group` พร้อมจำนวน "N match / M total" &nbsp;·&nbsp; **สถานะ UI ที่จดจำ:** ไม่มี

## 1. ภาพรวม

หน้า list เป็น **การเบี่ยงเบนโดยเจตนา** จากรูปแบบ Management มาตรฐานของ SPA (Clusters, Applications, Report Templates): แทนที่จะเป็น `DataTable` ฝั่ง server พร้อมค้นหาแบบ debounce, filter แบบ Sheet, ส่งออก CSV และสถานะที่จดจำใน `localStorage` มัน render การ์ดเดียวที่มี sub-table มีขอบ **ต่อชนิดเอกสารหนึ่งชนิด** ชุดข้อมูล justify การตัดสินใจนี้ — อย่างมากก็มี mapping เพียงหยิบมือต่อชนิดเอกสารแต่ละชนิดในสิบชนิด และเขียนนาน ๆ ครั้ง — และตัวการจัดกลุ่มเอง*คือ*ข้อมูล: "อะไรพิมพ์สำหรับ GRN" คือคำถามที่ operator ถาม และตารางแบนที่ sort ได้จะฝังมันจนหาไม่เจอ trade-off ของการข้ามองค์ประกอบมาตรฐาน (โดยเฉพาะการแบ่งหน้าฝั่ง server ที่ซ่อนอยู่) ถูกชี้ไว้ใน §2.5

หน้า edit เป็นแบบแผนทั่วไป: การ์ด "Mapping" เดียวตามรูปแบบ view/edit-toggle เดียวกับ Applications — โหมด create แก้ไขได้ทันที, route edit เปิดแบบ read-only อยู่หลังปุ่ม Edit ที่ gate ด้วย `<Can>` องค์ประกอบที่เป็นเอกลักษณ์เพียงหนึ่งเดียวของมันคือ select ของ Report Template (§3.3) ซึ่งลอยเทมเพลตที่ตรงกับชนิดเอกสารที่เลือกขึ้นด้านบนแทนที่จะซ่อนตัวที่เหลือ

ทั้งสองหน้าใช้ toast feedback ตอน mutation; หน้า edit ยังลงทะเบียน keyboard shortcut แบบ global เพิ่มเติม (save ทำการ submit ระหว่างแก้ไข, cancel ออกจากโหมดแก้ไข), เปิดใช้งาน navigation guard `useUnsavedChanges` เมื่อมี diff ใด ๆ ระหว่างแก้ไข และมาพร้อม Debug Sheet เฉพาะ dev (§3.4) หน้า list ไม่มี Debug Sheet

## 2. `PrintTemplateMappingManagement` — list (`/print-template-mapping`)

### 2.1 Layout และ header

Card เดียว header มีไอคอน Printer + ชื่อ "Print Template Mapping", subtitle "Map document types (PR/PO/SR/GRN/...) to the FastReport templates used for printing." และหนึ่ง action: **New Mapping** (นำทางไป `/print-template-mapping/new`; ห่อใน `<Can permission="print_template_mapping.create">`)

### 2.2 Filter

ตัวควบคุมแบบ inline บนแถวมีขอบ — ไม่มี panel แบบ Sheet:

- **Document Type** — native select ที่ป้อนข้อมูลโดย `GET .../document-types` ตัวเลือก render เป็น `CODE — Label` พร้อม default เป็น "All" การเลือก refetch list ด้วย `?document_type=`
- **Active only** — checkbox ที่ refetch ด้วย `?active_only=true`

ทั้งคู่เป็น filter ฝั่ง server (ทุกการเปลี่ยนแปลง refetch); ไม่มีการค้นหาแบบ free-text

### 2.3 ตารางแบบจัดกลุ่ม

row ถูกจัดกลุ่มฝั่ง client ตาม `document_type`; กลุ่มเรียงตาม code (`localeCompare`) แต่ละกลุ่ม render บล็อกมีขอบพร้อม header สีจาง — Badge แบบทึบพร้อม code ของชนิด, label ของชนิดที่ resolve จาก lookup ของ document-types และจำนวน "(N mapping(s))" — ตามด้วยตารางธรรมดา:

| คอลัมน์ | การ render |
|---|---|
| Template | `template_name` (ตัวหนา; `-` เมื่อเทมเพลตที่ join หายไป) พร้อม `template_group` เป็นข้อความรองสีจางด้านล่าง |
| Display Label | ข้อความสีจาง, `-` เมื่อว่าง |
| Default | badge "Default" แบบทึบเมื่อ `is_default` ไม่เช่นนั้น `-` |
| Order | `display_order` แบบ monospace |
| Active | badge Active (success) / Inactive (secondary) |
| (action) | ปุ่มไอคอน inline ชิดขวา — ดู §2.4 |

ภายในกลุ่ม row คงลำดับของ server: `display_order` จากน้อยไปมาก โดย `is_default DESC` เป็น tie-break (apply โดย query list ของ Go เมื่อไม่มีการขอ sort) — กล่าวคือ ลำดับเดียวกับที่เมนู "Print as…" จะแสดง

### 2.4 action ของ row และ dialog ลบ

ต่างจาก dropdown `⋯` ของรูปแบบมาตรฐาน, action เป็น**ปุ่มไอคอน ghost แบบ inline** สองตัว: ดินสอ (นำทางไป route edit) ห่อใน `<Can permission="print_template_mapping.update">` และถังขยะแบบ destructive ห่อใน `<Can permission="print_template_mapping.delete">` การลบเปิด `ConfirmDialog` — ชื่อ "Delete Print Template Mapping", คำอธิบาย `Delete mapping "<DOC> → <ชื่อเทมเพลต หรือ UUID ดิบของ report_template_id เมื่อเทมเพลตที่ join หายไป>"? This cannot be undone (soft delete).` — และเมื่อยืนยันจะเรียก `DELETE .../print-template-mappings/:id`, toast แล้ว refetch ไม่มี affordance สำหรับลบบนหน้า edit

### 2.5 สถานะ และต้นทุนขององค์ประกอบที่หายไป

- **Loading** — บรรทัด "Loading…" ธรรมดา (ไม่มี `TableSkeleton`)
- **Error** — banner แบบ destructive แบบ inline ("Failed to load print mappings: …"); การที่ lookup ของ document-types ล้มเหลวแยกต่างหากจะ raise toast
- **Empty** — ข้อความกึ่งกลางธรรมดา: "No mappings yet. Click **New Mapping** to create one." (ข้อความเท่านั้น — ไม่ใช่ปุ่ม จึงไม่มีการรั่วของ CTA ที่ไม่ถูก gate ที่นี่ แม้ประโยคจะอ้างถึงปุ่มที่ session ที่ไม่มี `.create` มองไม่เห็น)
- **ไม่มีสถานะ UI ที่จดจำ** — filter ทั้งสองไม่รอดการ reload; ไม่มีอะไรถูกเขียนลง `localStorage`
- **การแบ่งหน้าที่ซ่อนอยู่** — SPA ไม่ส่ง `page`/`perpage`, endpoint ของ Go default เป็น `perpage = 10` และหน้า render เฉพาะสิ่งที่ส่งมาถึงโดยไม่มี pager หรือตัวนับ เมื่อมี mapping ที่ live มากกว่า 10 ตัว list จะ**ตัดทอนเงียบ ๆ** envelope ของ response ยังอาจซ้อนกันได้ (`data`, `data.data`, …) — หน้า unwrap ระดับ `.data` ได้ลึกสุดห้าชั้นจนกว่าจะพบ array

## 3. `PrintTemplateMappingEdit` (`/print-template-mapping/new`, `/print-template-mapping/:id/edit`)

### 3.1 โหมด create (`/print-template-mapping/new`)

ชื่อ "New Print Template Mapping"; การ์ดแก้ไขได้ทันทีด้วย default `is_default = true`, `display_order = 0`, `is_active = true` อย่างอื่นว่างทั้งหมด การ submit ทำการ validate Document Type และ Report Template (toast ต่อ field ที่ขาด), เรียก `POST`, toast "Mapping created" และ redirect ไปยัง route edit ของ row ใหม่ (`replace: true`) โดย fallback ไปหน้า list เมื่อ response ไม่มี id Cancel นำทางกลับไปหน้า list

### 3.2 โหมด view (`/print-template-mapping/:id/edit`, ค่าเริ่มต้น)

โหลดผ่าน `GET .../:id` และ render ทุก field แบบ read-only: กล่อง static สีจางสำหรับ field ข้อความ (Document Type แสดงเป็น `CODE — Label`, Report Template เป็น `name [report_group]` ที่ resolve จากรายการเทมเพลตที่โหลดไว้ โดย fallback เป็น id ดิบ), รายการ allow/deny เป็น **chip แบบ badge secondary** (หนึ่งตัวต่อ code; `-` เมื่อว่าง) และ Default/Active เป็น badge header มีปุ่ม Back และปุ่ม **Edit** ที่ห่อใน `<Can permission="print_template_mapping.update">` — หากไม่มี key นั้นหน้าจะ read-only ถาวร เนื่องจากแถว Save/Cancel render เฉพาะในโหมดแก้ไข

### 3.3 โหมดแก้ไข — field

toggle Edit ทำ snapshot ของฟอร์ม จากนั้นสลับการ์ดเป็นแก้ไขได้ field (grid สองคอลัมน์):

| Field | Control | หมายเหตุ |
|---|---|---|
| Document Type * | Native select ของตัวเลือก `CODE — Label` จาก endpoint document-types | จำเป็น (toast ก่อน submit) |
| Report Template * | Native select — ดูด้านล่าง | จำเป็น (toast ก่อน submit) |
| Display Label | ช่องข้อความ, placeholder "e.g. Standard PR (A4 Portrait)" | ข้อความช่วยเหลือ: แสดงในเมนู "Print as…" เมื่อมีหลายเทมเพลตสำหรับชนิดเอกสารเดียวกัน |
| Display Order | ช่องตัวเลข | input ที่ไม่ใช่ตัวเลขถูก coerce เป็น 0 |
| Allow Business Units | ช่องข้อความ, placeholder "e.g. T01,T03 (comma-separated, blank = all)" | CSV ของ BU code; parse/trim ตอน save; ค่าว่างส่ง `null` — ซึ่ง**ไม่**เคลียร์รายการที่เก็บไว้ (ดู [Data Model](./data-model.md) §5) |
| Deny Business Units | ช่องข้อความ, placeholder "e.g. T02 (comma-separated, blank = none)" | การจัดการ CSV แบบเดียวกัน |
| Default for this Document Type | Checkbox | Label: "Use this template when the user clicks the legacy "Print" button" |
| Active | Checkbox | |

**select ของ Report Template** โหลดเทมเพลตสูงสุด 500 ตัวครั้งเดียวตอน mount (`reportTemplateService.getAll({ perpage: 500 })`) เมื่อเลือกชนิดเอกสารแล้ว เทมเพลตที่ตรงกับ `kind === 'print' && report_group === document_type` จะ**ลอยขึ้นด้านบน — ที่เหลือยังคงเลือกได้อยู่ด้านล่าง** (เป็น soft sort ไม่ใช่ hard filter แม้ข้อความช่วยเหลือจะบอกว่า "Filtered by report_group matching the document type") placeholder อ่านว่า `Select template (N match / M total)…` (หรือ `(M total)` เมื่อยังไม่เลือกชนิด หรือ `— no templates available —`) และตัวเลือก render เป็น `name [report_group]` การเลือกเทมเพลตที่ไม่ match จึงเป็นไปได้โดย design — มีประโยชน์สำหรับการ reuse ข้าม group และพลาดได้ง่ายโดยบังเอิญ

ตอน save ในโหมดแก้ไข หน้าจะ `PUT` payload ของฟอร์มแบบเต็ม, toast "Changes saved", re-fetch แล้วถอยกลับสู่โหมด view Cancel คืนค่า snapshot ก่อนแก้ไขและออกจากโหมดแก้ไขโดยไม่เรียก server

### 3.4 Debug Sheet (เฉพาะ dev)

บน route edit (ไม่ใช่บน create ไม่ใช่บนหน้า list), build แบบ `import.meta.env.DEV` จะ render ปุ่มลอยสีเหลืองอำพันที่เปิด Sheet พร้อม JSON ดิบของ response `GET .../:id` ครั้งล่าสุดบวกปุ่ม Copy JSON — วิธีที่เร็วที่สุดสำหรับ QA ในการตรวจสอบ field จากการ join ที่ denormalize แล้วและ shape JSONB จริงของรายการ BU

## 4. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/PrintTemplateMappingManagement.tsx` — list แบบจัดกลุ่ม, filter, gate `<Can>`, dialog ลบ, การ unwrap envelope
- `../carmen-platform/src/pages/PrintTemplateMappingEdit.tsx` — สถานะของฟอร์ม, `rowToForm`/`parseList`, logic การลอยเทมเพลต (`matches`, `filteredTemplates`, `matchedCount`), Debug Sheet
- `../carmen-platform/src/services/printTemplateMappingService.ts` — endpoint เบื้องหลังทุก action
- `../carmen-platform/src/services/reportTemplateService.ts` — `ReportTemplate` (`kind`, `report_group`) ที่ select เทมเพลตใช้
- `../micro-report/db/print_template_mapping_repo.go` — การเรียง row แบบ default ฝั่ง server และพฤติกรรม `perpage` ที่ปรากฏใน §2.3/§2.5

**Cross-link:** [หน้า landing ของ Print Template Mapping](/th/platform/print-template-mapping) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Report Templates — UI Screens](../report-templates/ui-screens.md)
