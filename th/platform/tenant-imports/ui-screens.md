---
title: การนำเข้าเทแนนต์ — หน้าจอ UI (UI Screens)
description: ลำดับสี่หน้าจอของ TenantImportWizard — เลือก business unit, อัปโหลด Preconfig.xlsx, ทบทวนผลตรวจไฟล์, แล้วทำงานทีละขั้นตอนผ่าน StepRail/StepPanel และ CompanyProfilePanel ที่เป้าหมายเป็น platform — พร้อมสิ่งที่แต่ละหน้าจอตรวจ สิ่งที่เกิดขึ้นเมื่อล้มเหลว และย้อนกลับได้หรือไม่
published: true
date: '2026-09-06T23:30:00.000Z'
tags: book/platform, tenant-imports, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การนำเข้าเทแนนต์ — หน้าจอ UI (UI Screens)

> **At a Glance**
> **State machine ของหน้าจอ:** `pick-bu` → `upload` → `check` → `steps` (`type Screen`, `TenantImportWizard.tsx`) &nbsp;·&nbsp; **เปลือกที่ใช้ร่วมกัน:** `Layout`, `PageHeader` (หัวข้อ "Tenant Data Import"), ปุ่มบน header ที่เปิด command palette `BuSwitcher` ที่ใช้ร่วมกัน, `DevDebugSheet` เฉพาะตอน dev &nbsp;·&nbsp; **ไม่มีปุ่มย้อนกลับ:** เมื่อถึง `steps` แล้วไม่มีปุ่มไหนย้อนกลับไป `check` โดยที่ไฟล์ที่โหลดไว้ยังอยู่ — ทางเดียวที่จะย้อนกลับไป `upload` คือผ่าน `BuSwitcher` ซึ่งทิ้งความคืบหน้าทั้งหมดของ wizard ฝั่ง client (§6) &nbsp;·&nbsp; **e2e suite:** ไม่มี — พฤติกรรมทุกอย่างด้านล่างอ่านตรงจาก source ของ `../carmen-platform`

## 1. ภาพรวม

หน้าจอทั้งสี่เดินหน้าทางเดียวอย่างเคร่งครัด ไม่มีอะไรในหน้านี้ที่เข้าถึงได้นอกลำดับ: ไม่มีการเลือก BU โดยไม่ผ่าน `pick-bu`, ไม่มีการตรวจไฟล์โดยไม่มี BU, และไม่มีการทำงานขั้นตอนโดยไม่ผ่านการตรวจไฟล์ก่อน สิ่งที่ต่างกันในแต่ละหน้าจอคือย้อนกลับได้มากแค่ไหนโดยไม่เสียอะไรเกินจำเป็น — อธิบายไว้ทีละหน้าจอด้านล่าง และสรุปไว้ที่ §6

## 2. หน้าจอที่ 1 — เลือก Business Unit (`pick-bu`)

**ถามอะไร:** ยังไม่มีอะไร — มีข้อความกึ่งกลางหน้าจอ ("Pick the business unit that will receive the data," `pages.tenantImport.pickBuHint`) และปุ่ม "Select business unit" ที่เปิด `BuSwitcher` ซึ่งเป็น component เดียวกับที่ [SQL Workbench](/th/platform/sql-workbench) ใช้: พิมพ์เพื่อกรองตาม code/name/cluster, ใช้ลูกศรเลื่อน, กด Enter เพื่อเลือก นี่คือปุ่มเดิมที่ปรากฏบน header ทุกหน้าจอถัดไปด้วย ("BU: `{code}`") — เปิดใหม่จากที่ไหนก็ได้จะรีเซ็ต wizard ทั้งหมด (§6)

**ตรวจอะไร:** ไม่มีอะไร — ยังไม่มีการแตะไฟล์เลย ระหว่างที่แสดงหน้าจอนี้ wizard ยิงคำขอสองตัวพร้อมกันอิสระต่อกัน (`Promise.allSettled`, `TenantImportWizard.tsx`): `businessUnitService.getAll({ perpage: 200 })` เพื่อเติมตัวเลือก และ `preconfigImportService.getSteps()` (`GET /steps`) เพื่อโหลดแคตตาล็อกขั้นตอน ความล้มเหลวของแต่ละอันแยก toast กันเอง และไม่บล็อกอีกอันหนึ่ง — session ที่ list business unit ได้แต่ไม่มี `data_import.manage` ยังเห็นตัวเลือกเติมข้อมูลได้ตามปกติ แต่จะมีแบนเนอร์ error ของแคตตาล็อกรอที่หน้าจอถัดไป (§3)

**เกิดอะไรเมื่อล้มเหลว:** การดึงรายการ BU ล้มเหลว toast error และปล่อยตัวเลือกว่างเปล่า; การดึงแคตตาล็อกล้มเหลว toast error, ตั้ง `catalogError`, และแสดงเป็นแบนเนอร์ค้างเมื่อ wizard ไปถึง `upload` (§3) — wizard ไม่ retry อัตโนมัติทั้งสองกรณี ข้อความของแบนเนอร์เองอาสาบอกสาเหตุที่เป็นไปได้: *"this usually means the platform permission for Preconfig imports has not been granted yet"* (`pages.tenantImport.catalogError`) — จุดแรกที่ควรตรวจเมื่อ session เห็นหน้า Upload ว่างเปล่า

**ข้อสังเกต ไม่ใช่ bug:** การดึง BU ถูกจำกัดที่ `perpage: 200` และ effect อ่านเฉพาะ `.data` จาก response — ฟิลด์ `total`/`paginate` ที่ `ApiListResponse` มี (`types/index.ts:20-24`) ไม่เคยถูกอ่านเลย ต่างจาก [Tenant Migrations](/th/platform/tenant-migrations) (§3.1 ที่นั่น) ที่เตือนชัดเจนเมื่อการดึง 1000 แถวของตัวเองไม่ครอบคลุมทุก business unit ตัวเลือกนี้ไม่มีสัญญาณใด ๆ บนหน้าจอเลยหาก cluster fleet มีเกิน 200 BU — รายการจะหยุดที่ 200 เฉย ๆ โดยไม่บอกอะไร

**ย้อนกลับ:** ง่ายมาก — นี่คือหน้าจอเริ่มต้น และการเปิด `BuSwitcher` ใหม่จากหน้าจอถัดไปจะกลับมาที่นี่ก็ต่อเมื่อ operator เคลียร์การเลือก; การเลือก BU (แม้จะเป็นตัวเดิม) เดินหน้าไป `upload` เสมอ

## 3. หน้าจอที่ 2 — อัปโหลดไฟล์ (`upload`)

**ถามอะไร:** ไฟล์ `.xlsx` หนึ่งไฟล์ ผ่าน `WorkbookDropzone` (`../carmen-platform/src/pages/tenantImport/WorkbookDropzone.tsx`) — ลากวางหรือคลิกเพื่อเลือก สร้างจาก DOM drag event ธรรมดา (คอมเมนต์ของ component เอง: repo ไม่มี `react-dropzone` และฟีเจอร์นี้ต้องไม่เพิ่ม dependency)

**ตรวจอะไร และตรวจที่ไหน:**

- **ฝั่ง client ก่อนส่งคำขอใด ๆ:** ชื่อไฟล์ที่ลากวาง/เลือกต้องลงท้ายด้วย `.xlsx` (ไม่สนตัวพิมพ์) — `WorkbookDropzone.tsx:26-29` นามสกุลผิดจะถูกปฏิเสธด้วย toast ("Only .xlsx workbooks are supported," `pages.tenantImport.onlyXlsx`) และไม่ถึงเครือข่ายเลย
- **ฝั่ง server อิสระ ในทุกคำขอที่รับไฟล์:** `assertXlsx()` (`preconfig-imports.controller.ts:29-36`) ตรวจนามสกุลซ้ำ **และ** ตรวจ MIME type ของ multipart ให้ตรงเป๊ะ (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) **และ** เพดานขนาด 10 MB (`MAX_FILE_SIZE_BYTES`, บรรทัด 11; บังคับซ้ำอิสระโดย limit ของ `FileInterceptor` ของ Multer เองที่แต่ละ route ด้วย) ไฟล์ที่ผ่านการตรวจแค่นามสกุลของเบราว์เซอร์ยังถูก server ปฏิเสธได้ (เช่นไฟล์ที่เปลี่ยนนามสกุลเป็น `.xlsx` แต่ชนิดจริงต่างออกไป หรือไฟล์เกิน 10 MB) — นี่คือกรณีที่ผู้ทดสอบต้องใช้ API ไม่ใช่แค่ UI เพื่อจำลองซ้ำ

ระหว่างที่คำขอ check กำลังทำงาน (`preconfigImportService.check()`) panel จะแสดงสปินเนอร์ "Checking workbook…" แทนที่ dropzone (สถานะ `busy`)

**เกิดอะไรเมื่อล้มเหลว:** การปฏิเสธจาก server (ชนิดผิด เกินขนาด) แสดงเป็น toast ที่สร้างจาก `parseApiError()`; หน้าจอยังอยู่ที่ `upload` และ dropzone ใช้งานได้อีกครั้ง — ไม่มีอะไรเดินหน้าต่อ การ check สำเร็จ (ไม่ว่าจะมีกี่ขั้นตอนที่ออกมาเป็น `ready`) เดินหน้าไป `check` เสมอ พร้อม abort การนำเข้าที่ค้างอยู่และรีเซ็ตสถานะทุกขั้นตอนก่อน (`resetGenerations()`, `TenantImportWizard.tsx`)

**ย้อนกลับ:** การอัปโหลดไฟล์อื่นที่หน้าจอนี้ (ไม่มี "ยกเลิก" แยกต่างหาก — การวางไฟล์ใหม่แค่รัน `check` ซ้ำ) รัน check ใหม่ตั้งแต่ต้นเสมอ ไม่มีอะไรจากความพยายามครั้งก่อนที่หน้าจอนี้สืบทอดต่อ

## 4. หน้าจอที่ 3 — ผลตรวจไฟล์ (`check`)

**แสดงอะไร:** `FileCheckPanel` (`../carmen-platform/src/pages/tenantImport/FileCheckPanel.tsx`) — บรรทัดหัว ("`{sheets}` sheets found · `{ready}` of `{total}` steps ready," `pages.tenantImport.fileSummary`) และตารางหนึ่งแถวต่อหนึ่งขั้นตอนในแคตตาล็อก คอลัมน์ Step / Sheet / Rows / Missing / Status ขั้นตอนที่ไม่ `ready` ยังปรากฏที่นี่แทนที่จะหายไปเงียบ ๆ (คอมเมนต์ของ component เอง) — นี่คือจุดเดียวที่ผู้ทดสอบเห็น**สาเหตุ**ที่ขั้นตอนหนึ่งไม่ไปถึง rail: `sheet_missing` (ไฟล์ไม่มีชีตที่ตรงกัน) หรือ `columns_missing` (มีชีตแต่ขาดคอลัมน์ `required`; คอลัมน์ *ไม่บังคับ* ที่ขาดไม่กันความพร้อมและปรากฏในช่อง Missing เพื่อให้เห็นเฉย ๆ)

**ตรวจอะไร:** ไม่มีอะไรใหม่ที่นี่ — หน้าจอนี้แค่**แสดงผล** `CheckReport` ที่คำขอ `check` ของหน้าจอ `upload` สร้างไว้แล้ว ไม่มีคำขอเกิดขึ้นจากหน้าจอนี้เอง

**การกระทำและเส้นทางความล้มเหลว:**

- **"Continue"** ถูก disabled ตราบใดที่ `readyCount === 0` — ไฟล์ที่ไม่มีขั้นตอนพร้อมแม้แต่ตัวเดียวไปต่อจากหน้าจอนี้ไม่ได้เลย และไม่มีทาง override
- **"Choose another file"** abort การรันที่ค้างอยู่ เคลียร์ไฟล์/รายงาน/สถานะขั้นตอนทั้งหมด แล้วกลับไป `upload` — เป็นทางเดียวในตัว wizard ที่กลับไป `upload` ได้โดยไม่ต้องผ่าน BU switcher

**ย้อนกลับ:** ย้อนได้อิสระในทิศทางเดียวที่ "Choose another file" อนุญาต (กลับไป `upload`); ไม่มีทางกลับมาที่หน้าจอนี้ตัวเดิมได้อีกเมื่อกด "Continue" ไปแล้ว (ดู §6)

## 5. หน้าจอที่ 4 — ขั้นตอน (`steps`)

นี่คือจุดที่ preview และ import เกิดขึ้นจริง ทีละขั้นตอนในแคตตาล็อก แบ่งเป็น `StepRail` (รายการทางซ้าย) กับ `StepPanel` (สิบเอ็ดในสิบสองขั้นตอน) หรือ `CompanyProfilePanel` (เฉพาะ Company Profile, §5.6 ด้านล่าง) ทางขวา

### 5.1 `StepRail` — เลือกว่าจะทำขั้นตอนไหน

รายการแนวตั้งที่ breakpoint ต่ำกว่า `lg` จะยุบเป็น `<select>` (`StepRail.tsx`); เหนือ breakpoint นั้น แต่ละขั้นตอนที่พร้อมเป็นหนึ่งแถวแสดงชื่อ, ไอคอนสถานะ (pending / previewing / previewed / importing / completed / skipped / error แต่ละอันมีไอคอนและสีของตัวเอง), และจำนวนแถว (เมื่อรู้แล้ว) การคลิกแถวสลับ `activeId`; **การสลับแถวไม่ทำให้สถานะของขั้นตอนอื่นหายไปเลย** — preview, options, และ summary ของแต่ละขั้นตอนอยู่อิสระในแมป `states` ของ wizard คีย์ด้วย step id ดังนั้นการกลับไปที่ขั้นตอนที่ preview ไว้ยี่สิบนาทีและอีกสามขั้นตอนก่อนหน้านี้ จะแสดงสถานะที่ทิ้งไว้พอดี

### 5.2 `StepPanel` — preview

**ถามอะไร:** โหมด On-duplicate (`skip` / `upsert` / `error` ค่าเริ่มต้นตาม `default_duplicate_mode` ของแคตตาล็อกสำหรับขั้นตอนนั้น) และเลือกได้ว่าจะ "Soft-delete existing rows first" (`clear_existing`) การกด **Preview** ส่งไฟล์ปัจจุบันและ options ไปที่ `POST /:step_id/preview`

**ตรวจอะไร (ต่อแถว ฝั่ง server):** กฎการแปลงค่าเดียวกับที่อธิบายไว้ใน[หน้า landing](/th/platform/tenant-imports) §3.2 — required/maxLength/allowedValues/number/decimal/boolean — บวก lookup ที่ประกาศไว้ทุกตัว (คอลัมน์คีย์ธรรมชาติที่ resolve เทียบกับตารางอื่น) และทุกคอลัมน์ของแถวลูกที่ related insert ต้องการ (เช่น การแปลงหน่วย Order ของสินค้าต้องการเซลล์ "Order unit" *และ* "Order Conv. Rate" ที่ไม่ว่างทั้งคู่ คู่ที่ไม่ครบจะถูกข้ามอย่างเงียบ ๆ ในฐานะ "สินค้านี้ไม่มีการแปลงหน่วย order" ในขณะที่คู่ที่มีแต่ resolve ไม่ได้จะทำให้ทั้งแถวแม่ล้มเหลว) แถวถูกจัดกลุ่มเป็น `new` / `duplicate` / `error` เทียบกับเนื้อหา**ปัจจุบันจริง**ของตารางเป้าหมาย จับคู่ด้วยคีย์ซ้ำแบบผสมของขั้นตอน ปรับให้ไม่สนช่องว่าง/ตัวพิมพ์

**คำตอบแสดงอะไร:** badge ผลตรวจพร้อมจำนวน (New / Duplicate / Error) ที่ทำหน้าที่เป็นตัวกรองไปในตัว — คลิกหนึ่งหรือหลายอันเพื่อกรองตารางด้านล่างเหลือเฉพาะผลตรวจนั้น; คำบรรยายบอกตรง ๆ ว่ากำลังดู*ตัวอย่าง*มากแค่ไหนเทียบกับยอดจริงของทั้งชีต ("Showing 200 of 2,400 new," `captionText`, `StepPanel.tsx`) — คำตอบของ preview จำกัดที่ 200 แถวต่อกลุ่มผลตรวจ ไม่ใช่ต่อคำตอบทั้งหมด ดังนั้นชีตที่เอียงไปทางผลตรวจเดียวมาก ๆ ก็ยังเห็นตัวอย่างของทุกผลตรวจ ไม่ใช่แค่กลุ่มที่เรียงมาก่อน ช่อง Verdict ของแต่ละแถวแสดงข้อความ error ต่อคอลัมน์แบบอินไลน์เมื่อมี

**"New reference data will be created"** ปรากฏเฉพาะเมื่อ preview พบค่า lookup ที่ไม่มีแถวตรงกันและ lookup นั้นอนุญาตให้สร้างอัตโนมัติ — แสดงทุกค่าที่ต่างกัน จัดกลุ่มตามตาราง/คอลัมน์เป้าหมาย พร้อม checkbox ให้ยอมรับการสร้าง (`accept_lookup_creation`) การติ๊ก checkbox นี้เป็นแค่ความสะดวกฝั่ง client สำหรับการเรียก Import *ครั้งถัดไป*เท่านั้น — §3.3 ของหน้า landing ครอบคลุมว่า server บังคับเรื่องนี้เองอิสระอย่างไร ต่อแถว ไม่ว่าจะ preview อะไรไว้ก็ตาม

**เมื่อล้มเหลว:** คำขอ preview เองล้มเหลว (เครือข่าย, permission, การเชื่อมต่อ) ตั้งขั้นตอนเป็น `error` พร้อมข้อความแสดงอินไลน์และ toast — ไม่มีแถวใดแสดง; options ของขั้นตอนไม่ถูกแตะต้อง ดังนั้นการกด Preview อีกครั้งจะลองใหม่ด้วยค่าเดิม

**ย้อนกลับ:** ได้อิสระ — Preview รันซ้ำได้กี่ครั้งก็ได้ ด้วย options ต่างกันในแต่ละครั้ง การเปลี่ยน options **ใดก็ตาม** (โหมด duplicate, checkbox clear-existing, การยอมรับ lookup) ทำให้ preview ปัจจุบันเป็นโมฆะทันที (`onOptionsChange`, `StepPanel.tsx`) และรีเซ็ตขั้นตอนกลับเป็น `pending` ต้อง Preview ใหม่ก่อน Import จะเปิดใช้อีกครั้ง

### 5.3 กล่องยืนยัน clear-existing

การติ๊ก "Soft-delete existing rows first" **ไม่ได้**ตั้ง `clear_existing` ตรง ๆ — มันเปิดกล่องโต้ตอบที่ต้องยืนยันชัดเจน checkbox เองถูก disabled จนกว่าจะมี preview อย่างน้อยหนึ่งครั้งสำหรับขั้นตอนนั้น (`disabled={running || previewing || (!preview && !clearExisting)}`, `StepPanel.tsx:112`) — ข้อความ "(run a preview first)" อธิบายเหตุผล กล่องโต้ตอบระบุ โดยใช้ตัวเลขที่ preview ล่าสุดคำนวณไว้แล้ว ว่าไม่มีอะไรจะลบ หรือระบุจำนวนแถวของตารางขั้นตอนนั้น (บวกจำนวนแถวลูก เช่นการแปลงหน่วย) ที่จะถูก soft-delete พอดี และต้อง**พิมพ์รหัส business unit ให้ตรงเป๊ะ**ลงในช่องข้อความก่อนปุ่ม "Confirm" จะเปิดใช้ (`clearCodeMatches`, `StepPanel.tsx:112,517`) การยกเลิกติ๊กภายหลังไม่ต้องยืนยันอะไรเลย — เป็นทางออกที่ลดระดับความเสี่ยงเสมอ แม้ว่าการเปลี่ยน options ภายหลังจะทำให้ preview ที่การติ๊กนั้นอิงอยู่เป็นโมฆะไปแล้วก็ตาม

ไม่มีลำดับใดในนี้ที่ server บังคับเลย — ดูหน้า landing §3.3 ว่า `import/stream` เองตรวจหรือไม่ตรวจอะไรบ้าง

### 5.4 Import

**ทำอะไร:** สตรีม `POST /:step_id/import/stream` เป็น NDJSON และแสดง progress bar (`{index} / {total}` อัปเดตอย่างมากทุก 50 แถวหรือครั้งเดียวตอนขอบแบตช์) บวกจำนวนแถวที่ soft-delete เมื่อ event `cleared` มาถึง ปุ่ม Import ถูก disabled ตราบใดที่ยังไม่มี preview, ขณะที่อีกขั้นตอนหนึ่งกำลัง import อยู่ (มีเพียงหนึ่งขั้นตอนที่ stream ได้ในเวลาเดียวกัน — การพยายามครั้งที่สองจะขึ้นข้อความ "Another step is still importing — wait for it to finish before starting this one," `pages.tenantImport.anotherStepImporting`), หรือขณะที่ preview ปัจจุบันยังมีการสร้าง lookup ที่ยังไม่ยอมรับค้างอยู่

**เกิดอะไรเมื่อล้มเหลว:** ความล้มเหลวระดับแถว (ค่าเสีย, lookup ที่ไม่ยอมรับ, constraint ฐานข้อมูล) จะถูกบันทึกใน `summary.failed`/`summary.errors` ของขั้นตอนนั้นและ**ไม่หยุด**การรัน — กลไก retry แบตช์ของตัวนำเข้าเอง (หน้า landing §3.4) คือสิ่งที่กันไม่ให้หนึ่งแถวเสียทำให้อีก 199 แถวในแบตช์เดียวกันล้มเหลวไปด้วย สถานะสุดท้ายของขั้นตอนจะเป็น `completed` ก็ต่อเมื่อ `summary.failed === 0`; มีความล้มเหลวแม้แต่รายการเดียวจะตั้งเป็น `error` พร้อมตัวเลขสรุป (inserted/updated/skipped/failed) ยังแสดงอยู่

**Re-run:** เมื่อขั้นตอนใดก็ตามถูก import แล้ว (`everImported`) มันจะปรากฏใน panel "Run summary" ใต้ rail พร้อมปุ่ม **Re-run** ที่เริ่ม import แบบเดิมซ้ำโดยใช้ options ที่ตั้งไว้ตอนนั้น — ใช้ได้ทุกเวลา รวมถึงหลังจากรันสำเร็จแล้ว ตราบใดที่ไม่มีขั้นตอนอื่นกำลัง import อยู่ การ Re-run ที่ยังเปิด `clear_existing` ไว้จะ soft-delete ซ้ำก่อนเสมอ

**การยกเลิก:** การออกจาก `steps` (สลับ BU, ไฟล์ใหม่, หรือออกจากหน้า) จะ abort สตรีม `fetch` ที่ค้างอยู่ ตามที่อธิบายในหน้า landing §3.4 การทำแบบนี้**ไม่**ย้อนทรานแซกชันแบตช์ที่คอมมิตไปแล้วบน server — มีเพียงแบตช์ที่ยังไม่เริ่มเท่านั้นที่ถูกข้าม และ server ยังคงเขียนแถว audit `tb_activity` บันทึกการรันเป็น `cancelled` พร้อม summary บางส่วนเท่าที่ทำไปได้

### 5.5 รายละเอียดระดับแถวและคำบรรยาย

ตาราง preview/import แสดงหนึ่งคอลัมน์ต่อหนึ่งคีย์ที่ต่างกันซึ่งพบในแถวตัวอย่าง (เรียงตามลำดับที่พบครั้งแรก ดังนั้นคอลัมน์ไม่บังคับที่ว่างในแถว 1 แต่มีค่าในแถว 40 ก็ยังได้คอลัมน์ของตัวเอง) บวกคอลัมน์ Verdict ที่มีข้อความ error ต่อคอลัมน์แบบอินไลน์ ตัวกรองผลตรวจที่กรองจนเหลือศูนย์แถวยังอธิบายตัวเองอยู่ ("No `error` rows in this preview") แทนที่จะแสดงตารางว่างเปล่าโดยไม่มีบริบท

## 6. การย้อนกลับ — ช่องว่างเดียวที่ผู้ทดสอบควรรู้ไว้ก่อน

ไม่มีปุ่มใดบนหน้าจอ `steps` ที่กลับไปที่ `check` (เพื่อดูตารางผลตรวจไฟล์อีกครั้ง) หรือ `upload` (เพื่อโหลดไฟล์อื่น) โดยที่ไฟล์ปัจจุบัน**ยังโหลดค้างอยู่** ทางเดียวที่ย้อนกลับไปหน้าจอก่อนหน้าได้คือ:

- **"Choose another file"** บนหน้าจอ `check` (§4) — เข้าถึงได้ก่อนกด "Continue" เท่านั้น
- **การเปิด `BuSwitcher` ใหม่** (ปุ่ม header "BU: `{code}`" ที่มีทุกหน้าจอ) — การเลือก business unit ใด ๆ แม้จะเป็นตัวที่เลือกอยู่แล้ว จะเคลียร์ไฟล์ รายงานผลตรวจ และสถานะ preview/import ของทุกขั้นตอนอย่างไม่มีเงื่อนไข แล้วกลับไป `upload`

ทั้งสองทางไม่ย้อนแถวที่แบตช์ที่คอมมิตไปแล้วระหว่างการ import ครั้งก่อนบน business unit นั้นเลย — ทั้งคู่รีเซ็ตแค่มุมมองฝั่ง client ของ wizard เท่านั้น ผู้ทดสอบที่ต้องการดูผลตรวจไฟล์อีกครั้งหลังจากเริ่มทำงานกับขั้นตอนแล้ว ต้องอัปโหลดไฟล์เดิมซ้ำ (เรียก `check` ใหม่ ไม่มีผลเสียและทำซ้ำได้เสมอ) แทนที่จะย้อนกลับได้ตรง ๆ

## 7. Panel Company Profile (`CompanyProfilePanel`) — ข้อยกเว้นของทุกอย่างข้างต้น

การเลือกขั้นตอน Company Profile ใน rail จะแสดง `CompanyProfilePanel` แทน `StepPanel` — ใช้ rail ร่วมกัน แต่กลไกที่เหลือไม่เหมือนกับ §5 เลย

**ถามอะไร:** ไม่มีอะไรนอกจากไฟล์และ BU ที่เลือกไว้แล้ว — โหลดอัตโนมัติ (และโหลดใหม่ได้ตามต้องการผ่านปุ่ม "Refresh" ของตัวเอง อิสระจากปุ่ม Preview ของขั้นตอนอื่น)

**แสดงอะไร:** ตาราง diff แบบฟิลด์ต่อฟิลด์ — Field / Current (BU) / Workbook / Status — สร้างจากคำขอ `preview()` เดียวกับที่ขั้นตอนอื่นใช้ แต่อ่านค่าฟิลด์แทนผลตรวจ ทุกฟิลด์โรงแรม/บริษัทที่ชีตแมปไว้ถูกเทียบกับเรกคอร์ดปัจจุบันของ business unit; แถวเสมือน "Default Currency" resolve **รหัส**สกุลเงินในชีตเทียบกับรายการสกุลเงินของ tenant เองเป็น UUID เพิ่มเติม (สถานะ: กำลัง resolve / resolve ไม่ได้ถ้าฐานข้อมูล tenant เข้าไม่ถึง / ไม่พบถ้ายังไม่มีรหัสสกุลเงินนั้น — พร้อมคำแนะนำให้รันขั้นตอน Currency ก่อนแล้วค่อย Refresh / resolve สำเร็จ) "BU Code" แสดงเป็นแถวข้อมูลระบุตัวตนแบบ**อ่านอย่างเดียว**พร้อมแบนเนอร์เตือนเมื่อรหัสในชีตไม่ตรงกับ business unit ที่เลือก — การ apply ไม่เปลี่ยนชื่ออะไรเลย แต่ทุกฟิลด์อื่นที่เปลี่ยนบน panel นี้ยังจะถูกเขียนลงบน BU **ที่เลือกไว้** ไม่ใช่ตัวที่ชีตอธิบาย จึงมีแบนเนอร์นี้ไว้เพื่อกันความผิดพลาดนี้ก่อนที่จะเกิดขึ้นจริง "BU Name" ถูกระบุว่า "Not applied" ด้วยเหตุผลเดียวกัน: ฟิลด์ระบุตัวตนไม่ถูกเขียนกลับจากชีตเลย

**ตรวจอะไรตอน Apply:** ค่า Inventory Cost Type ถ้าเปลี่ยน ต้องเป็นหนึ่งใน `average`/`fifo` (ตรวจฝั่ง client ทันทีก่อนส่งคำขอ; แคตตาล็อกฝั่ง server เองก็ตรวจ constraint เดียวกันอิสระตอน `preview`) การเขียนเองพก `doc_version` สำหรับ optimistic locking — `409` จะโหลดเรกคอร์ดใหม่และสร้าง diff ใหม่แทนที่จะเขียนทับเงียบ ๆ

**เกิดอะไรเมื่อล้มเหลว:** การโหลดล้มเหลวแสดง error แบบอินไลน์และ diff ว่างเปล่า; การ apply ล้มเหลว toast ข้อความจาก server และปล่อย diff ไว้ตามเดิมทุกอย่าง (ไม่มีการเขียนบางส่วน — ทั้งคำขอเป็น `PUT` ครั้งเดียว)

**ย้อนกลับ:** ได้อิสระ — "Refresh" โหลด diff ใหม่ได้ทุกเมื่อ และ "Apply to BU" กดซ้ำได้อีกหลัง apply สำเร็จ (จะ disabled ก็ต่อเมื่อไม่มีอะไรเหลือให้เปลี่ยนแล้วเท่านั้น) ต่างจากทุกขั้นตอนอื่น Company Profile ไม่แตะแมป `states` ของ wizard เองเลย — ไม่ปรากฏใน "Run summary" ไม่นับรวมใน "อีกขั้นตอนกำลัง import" และไม่มีผลต่อ guard unsaved-changes เพราะมันเขียนทันทีแทนที่จะเข้าร่วมโมเดล import แบบ stream เลย ดูหน้า landing §3.5-§3.6 และ §4 ว่าการเขียนนี้ตรวจหรือไม่ตรวจ permission ตัวไหนบ้าง

## 8. แหล่งอ้างอิง

ทุก path เป็น `../carmen-platform` (HEAD `157a65e`) ยกเว้นที่ระบุ `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`)

- `src/pages/TenantImportWizard.tsx` — state machine สี่หน้าจอ, การดึง BU list/แคตตาล็อกพร้อมกัน, generation token ต่อขั้นตอน, และเส้นทาง abort/reset ที่อ้างใน §6
- `src/pages/tenantImport/WorkbookDropzone.tsx:26-29` — การตรวจนามสกุล `.xlsx` ฝั่ง client (§3)
- `src/pages/tenantImport/FileCheckPanel.tsx` — ตารางผลตรวจไฟล์และการกระทำ Continue/Choose-another-file (§4)
- `src/pages/tenantImport/StepRail.tsx` — รายการขั้นตอน/ไอคอนสถานะ และ `<select>` สำรองต่ำกว่า `lg` (§5.1)
- `src/pages/tenantImport/StepPanel.tsx:112,267,517` — เงื่อนไข disabled ของ checkbox clear-existing, การยืนยันด้วยการพิมพ์รหัส BU, และตรรกะตัวกรอง/คำบรรยายผลตรวจ (§5.2-§5.3)
- `src/pages/tenantImport/CompanyProfilePanel.tsx` — ตาราง diff, สถานะการ resolve สกุลเงิน, และแบนเนอร์รหัส BU ไม่ตรงกัน (§7)
- `src/services/preconfigImportService.ts` — รูปแบบคำขอ `check`/`preview`/`importStream`
- `src/i18n/en.ts:3188-3283` (namespace `tenantImport`) — ทุกข้อความ UI ที่อ้างในหน้านี้
- `src/types/index.ts:20-24` (`ApiListResponse`) — ฟิลด์ `total`/`paginate` ที่ไม่ถูกอ่าน อ้างใน §2
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/preconfig-imports/preconfig-imports.controller.ts:11,29-36` — `MAX_FILE_SIZE_BYTES`, `assertXlsx()` (§3)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/preconfig-import/preconfig-import.service.ts` — การตรวจสอบค่า/lookup/แถวลูกที่ Preview และ Import เรียกใช้ (§5.2, §5.4)

**ลิงก์เชื่อมโยง:** [หน้า landing ของ Tenant Imports](/th/platform/tenant-imports) &nbsp;·&nbsp; [Business Units](/th/platform/business-units) &nbsp;·&nbsp; [Tenant Migrations](/th/platform/tenant-migrations)
