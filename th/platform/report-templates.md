---
title: เทมเพลตรายงาน (Report Templates)
description: แคตตาล็อกเทมเพลตรายงานแบบ XML พร้อม editor แบบแท็บ Dialog/Content/Preview การผูก data source กับฐานข้อมูล และการกำหนดขอบเขต business unit แบบ allow/deny
published: true
date: 2026-05-19T22:00:00.000Z
tags: platform/report-templates, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# เทมเพลตรายงาน (Report Templates)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจอ authoring ที่ผู้ดูแลภายในของ Carmen ใช้สร้างและดูแลเทมเพลตรายงานแบบ XML ที่ขับเคลื่อนทุกเอกสารพิมพ์ของแพลตฟอร์ม &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Platform admin และวิศวกร support ของ Carmen &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `report_template` (ฟิลด์: `name`, `description`, `report_group`, `dialog`, `content`, `source_type`, `source_name`, `source_params`, `allow_business_unit`, `deny_business_unit`, `is_standard`, `is_active`, `builder_key`) &nbsp;·&nbsp; **หน้าย่อย:** 2

## 1. ภาพรวม

โมดูล Report Templates คือหน้าจอ authoring สำหรับนิยามรายงานของแพลตฟอร์ม แต่ละแถวใน `report_template` อธิบายเอกสารที่พิมพ์/ส่งออกได้หนึ่งรายการ ได้แก่ ชื่อที่อ่านง่ายสำหรับมนุษย์ แท็ก `report_group` สำหรับการจัดกลุ่มใน picker ตอน runtime payload XML สองชุด (**Dialog XML** ที่นิยาม form ตัวกรองที่แสดงให้ผู้ใช้ปลายทาง และ **Content XML** ที่นิยามผลลัพธ์ที่ render ออกมา) การผูก data source (`source_type` + `source_name` + `source_params`) และฟิลด์ควบคุมการเข้าถึงที่จำกัดว่า business unit ใดจะรันได้ หน้ารายการที่ `/report-templates` (`ReportTemplateManagement.tsx`) เป็นแคตตาล็อกแบบ server-paginated ค้นหาได้ กรองได้ มี facet สำหรับ status/source-type และส่งออก CSV ได้ หน้าแก้ไขที่ `/report-templates/:id/edit` และ `/report-templates/new` (`ReportTemplateEdit.tsx`) เป็น layout สองคอลัมน์ คอลัมน์ซ้ายเป็นข้อมูลเทมเพลต, ขอบเขต BU, metadata และการผูก data source ส่วนคอลัมน์ขวาเป็นแท็บ editor XML และพรีวิว Dialog แบบ live

การผูก data source คือสัญญาตอน runtime เทมเพลตจะอ่านจาก **view** ของฐานข้อมูล (ไม่มีพารามิเตอร์ ตัวกรองทำงานผ่าน WHERE clause ตอน runtime) **function** (พารามิเตอร์แบบ positional ที่ได้จาก `source_params`) หรือ **procedure** (พารามิเตอร์ positional เหมือนกัน บวกกับ INOUT refcursor ต่อท้ายชื่อ `rs` และ procedure มีหน้าที่ใช้ตัวกรองภายในเอง) แต่ละแถวของ `source_params` จะ map ฟิลด์ filter หนึ่งฟิลด์จาก Dialog XML (เช่น `DateFrom`) เข้ากับ type ของ PostgreSQL และธง `nullable` ค่า `source_name` เป็น identifier แบบ plain ที่ไม่มี schema prefix และไม่มี quote — จะถูก resolve กับ schema ของแต่ละ tenant ตอน runtime ตัว probe "Browse in BU" ให้ผู้ดูแลเลือก business unit เป้าหมาย ดึงรายการ views/functions/procedures ที่มีอยู่จริงใน schema ของ tenant นั้น แล้วเลือกแทนที่จะพิมพ์ identifier จากความจำ

เทมเพลตถูกแบ่งเป็น **standard** (Carmen ส่งมอบ/ดูแล) และ **custom** (ต่อลูกค้า) ผ่าน `is_standard` และเป็น **active**/**inactive** ผ่าน `is_active` ทั้งคู่สลับได้ต่อแถวจากหน้า Edit และใช้เป็น facet ของหน้ารายการ Chip-input list `allow_business_unit` และ `deny_business_unit` กำหนดขอบเขตของเทมเพลตให้กับ BU ที่ระบุ (`allow` ว่าง = ทุก BU; `deny` ทับ `allow`) การแก้ไขเทมเพลตแสดงการ validate XML แบบ inline (จำนวนบรรทัด จุดแสดง parse error ต่อแท็บ) และเตือนเรื่องการเปลี่ยนแปลงที่ยังไม่ได้บันทึกผ่านแถบ action ติดล่างและ hook `useUnsavedChanges` รายละเอียดพฤติกรรม UI และตัว schema XML เองอยู่ในหน้าย่อย — หน้า landing นี้เพียงปูทาง

## 2. บริบททางธุรกิจ

แพลตฟอร์มของธุรกิจโรงแรมพิมพ์และส่งอีเมลเอกสารปฏิบัติการจำนวนมาก — purchase order, ใบ GRN, รายการ pick ของ store requisition, รายงานมูลค่าสต็อก, สรุปต้นทุนอาหาร — และ layout ของแต่ละแบบไม่ค่อยเหมือนกันระหว่างลูกค้า กลุ่มแบรนด์ต้องการ logo และที่อยู่ของตน ทีมการเงินอยากให้ประทับอัตราแลกเปลี่ยนไว้ด้านบน บาง property ต้องการเวอร์ชันภาษาไทยควบคู่กับต้นฉบับภาษาอังกฤษ การ hard-code ความหลากหลายทุกแบบลงในโค้ดแอปพลิเคชันจึงไม่ยั่งยืน แพลตฟอร์มจึงแยกนิยามรายงานออกมาเป็นแถว XML ที่วิศวกร support ของ Carmen (ไม่ใช่ลูกค้า) สามารถแก้ไขผ่านหน้าจอ admin นี้ได้

แถว `report_template` จึงทำหน้าที่สองอย่าง ในด้านปฏิบัติการ มันคือ source ที่ runtime ของรายงานเรียกใช้เมื่อผู้ใช้คลิก "print" หรือเปิดรายงาน — Dialog XML render form พารามิเตอร์ Content XML render ผลลัพธ์ และ `source_name`/`source_params` ตัดสินใจว่าจะเรียก object ใดในฐานข้อมูล ในด้านเชิงพาณิชย์ มันคือหน่วยของการ customise การส่งมอบเอกสารพิมพ์ใหม่ให้ลูกค้าหมายถึงการเพิ่ม (หรือ clone) แถวที่นี่ ไม่ใช่การ deploy แอปพลิเคชันซ้ำ การเก็บการ authoring ไว้ใน Platform admin — โดยจำกัดเฉพาะ role ภายใน Carmen สามค่า — ช่วยรักษาสัญญาการ customise นี้ไว้โดยไม่ต้องเปิดเผย XML เบื้องหลังให้ลูกค้าเห็น

## 3. แนวคิดสำคัญ

- **Report template**: หนึ่งแถวใน `report_template` ที่อธิบายเอกสารที่พิมพ์/ส่งออกได้หนึ่งรายการอย่างครบถ้วน ประกอบด้วยฟิลด์ระบุตัวตน (`name`, `description`, `report_group`) payload XML สองชุด (`dialog`, `content`) การผูก data source (`source_type`, `source_name`, `source_params`) ขอบเขต BU (`allow_business_unit`, `deny_business_unit`) และธง lifecycle (`is_standard`, `is_active`, `builder_key`)
- **Dialog XML**: payload XML ที่เก็บในฟิลด์ `dialog` ซึ่ง runtime ของรายงานใช้ render form ตัวกรอง/พารามิเตอร์ที่แสดงให้ผู้ใช้ปลายทางก่อนรันรายงาน แก้ไขในแท็บ **Dialog XML** ของคอลัมน์ขวา พร้อมจำนวนบรรทัดและการ validate แบบ inline
- **Content XML**: payload XML ที่เก็บในฟิลด์ `content` ซึ่งกำหนดวิธี render ผลลัพธ์ของรายงาน แก้ไขในแท็บ **Content XML** ตัว editor รับการอัปโหลด `.frx`, `.xml` หรือ `.txt` ซึ่งสะท้อนว่ารายงานเดิม authored ด้วย `.frx` ของ FastReport แล้ว migrate เข้ามาเป็น XML ที่นี่
- **Preview**: แท็บที่สามของคอลัมน์ขวาที่ render Dialog XML เป็น form แบบ disabled เพื่อให้ผู้สร้างเห็นว่าผู้ใช้ปลายทางจะเห็นอะไรพอดี โดยไม่ต้องรันรายงานจริง
- **Source type**: หนึ่งใน `view`, `function`, หรือ `procedure` view ไม่รับพารามิเตอร์ (runtime ใช้ตัวกรองผ่าน WHERE clause) function และ procedure ต้องประกาศพารามิเตอร์ positional ผ่าน `source_params` procedure ต้องรับ INOUT refcursor ต่อท้าย (ชื่อ default `rs`) เพิ่ม และต้องใช้ตัวกรองภายในเอง
- **Source name**: SQL identifier แบบ plain (ไม่มี schema prefix ไม่มี quote) ที่ระบุชื่อ view/function/procedure ใน schema ของแต่ละ tenant resolve ตอน runtime กับ schema ของ business unit ที่เรียก ต้องระบุเมื่อ `source_type` เป็น `function` หรือ `procedure`
- **Source params**: รายการแบบมีลำดับที่ map ฟิลด์ filter ของ Dialog (`filter` เช่น `DateFrom`) เข้ากับ type ของ PostgreSQL (เช่น `date`, `uuid`, `text`) พร้อมธง `nullable` เก็บเป็น `{ params: [...] }` ว่างสำหรับ source แบบ `view`
- **Allow / Deny business unit**: รายการรหัส BU แบบคั่นด้วย comma สองรายการที่รับผ่าน chip input รายการ `allow` ที่ว่าง แปลว่า "ทุก business unit รันเทมเพลตนี้ได้" รายการ `deny` ทับ `allow`
- **Standard vs. Custom**: ธง `is_standard` แยกเทมเพลตที่ Carmen ส่งมอบ/ดูแล (`Standard`) จากของที่เพิ่มต่อลูกค้า (`Custom`) แสดงเป็น badge ของคอลัมน์ในหน้ารายการ
- **สถานะ Active / Inactive**: ธง `is_active` ควบคุมว่าเทมเพลตจะปรากฏใน picker ตอน runtime หรือไม่ เทมเพลตที่ inactive ยังแก้ไขได้ที่นี่ แต่ผู้ใช้ปลายทางมองไม่เห็น
- **Builder key**: identifier สั้น ๆ ที่ใส่หรือไม่ใส่ก็ได้ (เช่น `pr-summary`) ที่เชื่อมเทมเพลตกับ builder/registration ในโค้ดแอปพลิเคชัน เป็น free-text และยังไม่ได้ validate จาก Platform admin
- **Probe BU picker**: feature สำหรับการพัฒนาในส่วน Source ของหน้า Edit ที่โหลดรายการ views/functions/procedures จริงจาก schema ของ tenant ที่เลือก (`reportTemplateService.listDbObjects`) เพื่อให้ผู้ดูแลเลือก `source_name` จาก dropdown แทนที่จะพิมพ์

## 4. บทบาทและ Persona

Route `/report-templates`, `/report-templates/new`, และ `/report-templates/:id/edit` ถูก gate ด้วย array `allowedRoles` เดียวกัน — Role ภายใน Carmen ระดับ admin สามค่า Role อื่นใดที่ล็อกอินแล้วและเข้า route เหล่านี้จะเห็น `<AccessDenied>` ([[auth-roles]] อธิบายกลไก guard ไว้)

| Role | หน้าที่ |
|---|---|
| `platform_admin` | ผู้ดูแลเต็มรูปแบบของผลิตภัณฑ์ Carmen Platform admin สร้าง แก้ไข เปิด/ปิดใช้งาน และลบเทมเพลตรายงาน กำหนดขอบเขต BU สลับ Standard/Custom |
| `support_manager` | ผู้จัดการ support ของ Carmen สิทธิ์เข้าถึงสำหรับโมดูลนี้เหมือนกับ `platform_admin` — ถูกระบุในทุก array `allowedRoles` ของ report-templates |
| `support_staff` | วิศวกร support ของ Carmen สิทธิ์เข้าถึงเหมือน `support_manager` เป็น role ที่ลงมือ authoring เทมเพลตเฉพาะลูกค้า |

Role ของลูกค้าปลายทาง (ผู้จัดการ property, เจ้าหน้าที่ระดับ BU, ผู้ใช้ปลายทาง) ไม่เข้าถึงโมดูลนี้ — พวกเขาบริโภคผลลัพธ์ของรายงานผ่าน picker ตอน runtime ไม่ใช่ผ่านแคตตาล็อกเทมเพลต

## 5. โมดูลที่เกี่ยวข้อง

- [[auth-roles]] — เป็นเจ้าของกลไก `PrivateRoute` + `hasRole()` ที่ gate route ทั้งสามของ report-templates ให้กับ Role ระดับ admin
- [[business-units]] — เป็นแหล่งของรหัส BU ที่ใช้ใน chip input `allow_business_unit` / `deny_business_unit` และการค้นหา schema ของ tenant ของ "Probe BU" picker
- [[clusters]] — หน้าจอที่ถูก gate ระดับ admin อีกหนึ่งหน้าที่อยู่ใน allow-list เดียวกันกับ report-templates เป็น cross-reference ที่มีประโยชน์ว่าแพลตฟอร์มจัดระเบียบขอบเขตลูกค้าเหนือระดับ BU อย่างไร
- [[users]] — จัดการฟิลด์ `platform_role` บนแต่ละบัญชีผู้ใช้ที่ตัดสินใจในที่สุดว่าใครจะผ่าน gate `allowedRoles` ของโมดูลนี้

## 6. แหล่งข้อมูลอ้างอิง

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/ReportTemplateManagement.tsx`, `../carmen-platform/src/pages/ReportTemplateEdit.tsx`, `../carmen-platform/src/App.tsx`

## 7. หน้าในโมดูลนี้

- [[report-templates/ui-screens|UI Screens]] — ทัวร์ของแท็บ editor XML แบบ CodeMirror (stub — ยังไม่สมบูรณ์), marker การ validate แบบ live, แท็บ Dialog Preview, chip input ของ BU และแถบ action ติดล่างพร้อมตัวบ่งชี้การเปลี่ยนแปลงที่ยังไม่ได้บันทึก
- [[report-templates/xml-spec|XML Spec]] — เอกสารอ้างอิงสำหรับ schema XML ของ Dialog และ Content (stub — ยังไม่สมบูรณ์) — root element, โครงสร้างของ child และ pattern การจับคู่ Label + Date/Lookup ที่ใช้ใน form ตัวกรอง
