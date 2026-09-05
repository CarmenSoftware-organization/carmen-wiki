---
title: เทมเพลตรายงาน — Form Groups
description: หน้าจอ /report-form-groups (เพิ่มเมื่อ 2026-07-24) ที่แทนที่ list แบบการ์ดจัดกลุ่มของ print-template-mapping — หนึ่งการ์ดต่อ report_group code ที่ตายตัว พร้อม action "set as default" บน tb_report_template.is_default
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, report-templates, form-groups
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# เทมเพลตรายงาน — Form Groups

> **At a Glance**
> **หน้าจอ:** `ReportFormGroupManagement` (`/report-form-groups` เพิ่มเมื่อ 2026-07-24) &nbsp;·&nbsp; **Route gate:** `report_template.read` (reuse — ไม่มี permission key ใหม่) **และ** `feature="report_form_groups"` — key feature ของตัวเอง แยกจาก `report_templates` ของ Report Templates &nbsp;·&nbsp; **Sidebar:** รายการ "Form Groups" ในกลุ่ม Content (`platformNav.ts`) &nbsp;·&nbsp; **แทนที่:** list แบบการ์ดจัดกลุ่มของ [print-template-mapping](/th/platform/print-template-mapping) ที่ถูกลบในสัปดาห์เดียวกัน &nbsp;·&nbsp; **ข้อมูล:** ทุกแถว `tb_report_template` ที่ `template_type = "form"` จัดกลุ่มตาม `report_group` &nbsp;·&nbsp; **ตั้งแต่ 2026-08-22:** แต่ละแถวแสดงบรรทัด audit แบบย่อ (actor ล่าสุด สร้างหรือแก้ไข)

## 1. ภาพรวม

Form Groups เป็นหน้าจอที่ admin เลือก per ชนิดเอกสารว่า form template แบบเอกสารเดี่ยวตัวไหนที่ business unit จะได้เป็น default เมื่อยังไม่ได้เลือกเอง มันแทนที่ list แบบการ์ดจัดกลุ่มของโมดูล [print-template-mapping](/th/platform/print-template-mapping) เองในการเปลี่ยนแปลงเดียวกันเมื่อ 2026-07-23/24 ที่ drop `tb_print_template_mapping` และเพิ่ม `tb_report_template.is_default` — ดูหน้านั้นสำหรับ timeline การถูกลบฉบับเต็ม และ [Report Templates](/th/platform/report-templates) §1/§3 สำหรับคู่คอลัมน์ `template_type`/`is_default` ที่หน้านี้แก้ไข ก่อนหน้านี้หน้าจอนี้ถูกกล่าวถึงแค่ในเนื้อความบนหน้า landing ของ [Report Templates](/th/platform/report-templates) และหน้าเชิงประวัติศาสตร์ของ [print-template-mapping](/th/platform/print-template-mapping)

หน้าจอนี้ fetch เทมเพลตที่ `template_type = "form"` **ทั้งหมด** (paging เป็นชุดละ 500 จนถึงจำนวนรวมที่ server รายงาน เพื่อไม่ให้การจัดกลุ่มทำงานบน fetch ที่ไม่ครบโดยไม่รู้ตัว) แล้วจัดกลุ่มตาม `report_group` มัน reuse permission `report_template.*` ทั้งหมด — ไม่มี key แบบ `report_form_group.*` หรือคล้ายกันใน permission catalog เลย

## 2. Layout ของหน้าจอ

- **Header** — `PageHeader` หัวข้อ "Form Groups" คำบรรยาย "Manage the default form template for each report group"; ปุ่ม **New Form Template** (gate ด้วย `report_template.create`) ที่ navigate ไป `/report-templates/new` พร้อม pre-fill `template_type: "form"`
- **แถบ filter** — ช่องค้นหา (จับคู่ code ของกลุ่มหรือชื่อเทมเพลต) และ checkbox "Active only" ที่ filter แถวภายในแต่ละการ์ด (ไม่ซ่อนการ์ดทั้งใบแม้จะตรงเงื่อนไขอื่น)
- **Grid การ์ดกลุ่ม** (2 คอลัมน์บนจอใหญ่) — หนึ่ง `GroupCard` ต่อกลุ่มรายงาน แต่ละการ์ดแสดง:
  - code ของกลุ่มเป็น badge outline แบบ monospace บวกจำนวนเทมเพลต ("N templates")
  - ปุ่ม **Add** (gate ด้วย `report_template.create`) ที่ pre-fill `report_group` พร้อม `template_type: "form"` ตอน navigate ไปสร้าง
  - banner เตือน ("No default set — pick one.") เมื่อกลุ่มมีเทมเพลตอย่างน้อยหนึ่งตัวแต่ไม่มีตัวไหนเป็น default
  - หนึ่งแถวต่อเทมเพลต: radio button (checked = default ปัจจุบัน), ชื่อเทมเพลตพร้อมบรรทัด audit แบบย่อด้านล่าง (**เพิ่มเมื่อ 2026-08-22**, `f62a90e`) — `latestActor(t)` เลือกว่า created หรือ updated ตัวไหนล่าสุดกว่า แล้ว `<AuditMeta variant="compact">` render เป็น "Created `<relative>` · `<name>`" หรือ "Updated `<relative>` · `<name>`" — badge **Active/Inactive**, badge **Standard/Custom**, ลิงก์ **Edit** ไป `/report-templates/:id/edit`, และ — gate ด้วย `report_template.update` — เมนู kebab พร้อม action เดียวคือ **Activate**/**Deactivate**
  - empty state ("No form templates" / "No form templates in {code} yet.") เมื่อกลุ่ม (หลัง filter) ไม่มีแถวเหลือ
- แถวภายในการ์ดเรียงลำดับ default ก่อน แล้วตามด้วยชื่อ; radio ของ default และกรอบ "Default" เป็นแค่การนำเสนอ — ไม่มีคอลัมน์ badge "Default" แยกต่างหากบนหน้าจอนี้ (badge นั้นอยู่บนหน้ารายการ Report Templates แทน ตาม [Report Templates](/th/platform/report-templates) §1)
- `DevDebugSheet` (dev เท่านั้น) แสดง response ดิบของหน้าแรกจาก API

## 3. การตั้งค่า Default ของกลุ่ม

การคลิก radio ที่ยังไม่ checked จะเปิด confirm dialog ("Set '{name}' as the default for {code}? Replaces '{old name}'." เมื่อมี default เดิมอยู่) การยืนยันจะเรียก `reportTemplateService.setGroupDefault({ current, target })` ซึ่งเป็น **สอง `PUT /api-system/report-templates/:id` ที่เรียงตามลำดับ ไม่ใช่ transaction เดียว** — ตัวแรก `{ is_default: false }` บน default เดิม (ข้ามไปเลยถ้าไม่มี default เดิม) แล้วตามด้วย `{ is_default: true }` บนเป้าหมาย แต่ละตัวพก `doc_version` ของตัวเองสำหรับตรวจ optimistic-lock ความขัดแย้งเวอร์ชัน `409` ในการเรียกใดก็ตามจะเรียก toast `notifyVersionConflict()` ที่ใช้ร่วมกันและ re-fetch รายการทั้งกลุ่มใหม่; ความล้มเหลวอื่นแสดง toast ทั่วไป "Failed to set default" ตามด้วย re-fetch เช่นกัน เพื่อให้ UI สะท้อน state จริงที่เกิดขึ้น

ฐานข้อมูลบังคับ invariant ที่ flow สองขั้นนี้พยายามรักษาไว้: `idx_report_template_default_per_group` เป็น partial unique index บน `tb_report_template(report_group)` `WHERE is_default AND template_type = 'form' AND deleted_at IS NULL` (เพิ่มโดย migration `20260723120000_print_form_default` ตัวเดียวกับที่ drop `tb_print_template_mapping` — ดู [print-template-mapping](/th/platform/print-template-mapping) §1) เพราะสอง `PUT` ไม่ได้อยู่ใน transaction เดียว จึงมีช่วงแคบ ๆ ระหว่างสองการเรียกที่กลุ่มนั้นมี default **เป็นศูนย์** แทนที่จะมีพอดีหนึ่งตัว ว่า request ตั้ง default ของ admin คนที่สองที่เกิดขึ้นพร้อมกันในช่วงเดียวกันจะ fail แบบสะอาด (unique-violation) หรือ race แบบคาดเดาไม่ได้ ยังไม่ได้ทดสอบแยกในรอบนี้ — ระบุเป็น edge case ที่ยังไม่ยืนยันทั้งสองทาง

action kebab **Activate/Deactivate** เป็น `PUT` เดี่ยวแยกต่างหาก (`{ is_active: !t.is_active }` บวก `doc_version`) และมี lock ฝั่ง client ของตัวเอง: การ deactivate default ปัจจุบันของกลุ่มขณะยัง active อยู่ถูก disable ใน menu item (`lockDeactivate = t.is_default && t.is_active`) — admin ต้องมอบหมาย default ใหม่ในกลุ่มก่อนจึงจะ deactivate เทมเพลตที่ถือ default อยู่ได้ การตั้งเทมเพลตที่ **inactive** เป็น default ใหม่ผ่าน radio ก็ถูก disable แยกต่างหาก (`disableRadio = !canWrite || !t.is_active || busy`) พร้อม tooltip ("Activate the template to make it the default") บน label ของ radio — admin ต้อง activate เทมเพลตก่อนจึงจะเป็น default ของกลุ่มได้

## 4. กลุ่มแบบตายตัว vs. Legacy

Grid การ์ดจะ render 12 code ใน `FORM_REPORT_GROUPS` (`carmen-platform/src/constants/reportGroups.ts`: `PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP`) ตามลำดับตายตัวนั้นเสมอ แม้ code หนึ่งจะยังไม่มี form template เลยก็ตาม — เพื่อให้ admin เห็นรายการ ชนิดเอกสารที่ต้องมี default ครบถ้วนตามหลักการเสมอ ไม่ใช่แค่ตัวที่มีข้อมูลอยู่แล้ว ค่า `report_group` ใด ๆ ที่มีอยู่ในข้อมูลแต่ **ไม่** อยู่ในรายการตายตัว ("legacy" code) ก็ยังได้การ์ดของตัวเอง เรียงตามตัวอักษรและต่อท้ายหลัง 12 code ตายตัว แต่จะแสดงเฉพาะเมื่อมีอย่างน้อยหนึ่งแถวที่มองเห็นได้ — legacy code ที่ไม่มีอะไรจะแสดงจะไม่ถูก render เป็นการ์ดว่างแบบที่ code ตายตัวเป็น ภายใต้คำค้นหาที่ active การ์ด code ตายตัวจะถูกเก็บไว้ก็ต่อเมื่อ code เองตรงกับคำค้น หรือยังมีแถวที่ตรงอยู่ — นี่คือกรณีเดียวที่กลุ่มตายตัวจะหายไปจากมุมมอง

## 5. บทบาทและ Persona

| Surface | Gate | Key |
|---|---|---|
| Route `/report-form-groups` | `requiredPermission` + `feature` | `report_template.read` + `report_form_groups` |
| รายการ sidebar "Form Groups" | `permission` + `feature` filter (`platformNav.ts`) | `report_template.read` + `report_form_groups` |
| ปุ่ม **New Form Template** | `hasPermission` | `report_template.create` |
| ปุ่ม **Add** ต่อการ์ด | prop `canCreate` (ตรวจสอบเดียวกัน) | `report_template.create` |
| Radio ตั้ง default, เมนู kebab | prop `canWrite` | `report_template.update` |

ไม่มี **permission** key ใหม่ถูกเพิ่มสำหรับหน้าจอนี้ — ถูก gate ทั้งหมดด้วย catalog `report_template.*` เดียวกันที่บันทึกไว้ครบถ้วน (matrix ของ route, bootstrap exception, ตาราง effective-access) บน [เทมเพลตรายงาน — Permissions](/th/platform/report-templates/permissions) แต่มัน**มี** key **feature** ของตัวเอง (`report_form_groups` แยกจาก `report_templates` ของ Report Templates) — การเปลี่ยน feature flag ของโมดูลหนึ่งไม่กระทบอีกโมดูล session ที่มีแค่ `report_template.read` จะดูได้ทุกกลุ่มและ default ปัจจุบันของทุกเทมเพลต แต่จะไม่เห็นปุ่ม Add ไม่เห็นเมนู kebab และไม่สามารถเลือก radio default ตัวอื่นได้ (render แบบ disabled ไม่ใช่ซ่อน)

## 6. โมดูลที่เกี่ยวข้อง

- [Report Templates](/th/platform/report-templates) — เป็นเจ้าของ `tb_report_template`, คอลัมน์ `template_type`/`is_default`/`report_group` ที่หน้าจอนี้แก้ไข และหน้า Edit ที่ลิงก์ **Edit** ของทุกแถวเปิด
- [Report Templates — Permissions](/th/platform/report-templates/permissions) — matrix gate `report_template.*` ฉบับเต็มที่หน้าจอนี้ reuse โดยไม่เปลี่ยนแปลง
- [print-template-mapping](/th/platform/print-template-mapping) — โมดูลที่ถูกลบซึ่งหน้าจอนี้เข้ามาแทนที่หน้าที่ หน้า landing ของมันบันทึก timeline การถูกลบเมื่อ 2026-07-23/24 ฉบับเต็ม และความสามารถหนึ่งอย่าง (การกำหนดขอบเขต default ต่อ BU) ที่ไม่ได้ย้ายมาด้วย

## 7. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx` — หน้า: paged fetch, การจัดกลุ่ม, filter ค้นหา/active, handler ตั้ง default และ toggle activate
- `../carmen-platform/src/pages/reportFormGroups/GroupCard.tsx` — การ์ดต่อกลุ่ม: radio, บรรทัด audit แบบย่อ (`latestActor()` + `AuditMeta variant="compact"`, เพิ่มเมื่อ 2026-08-22), badge, ลิงก์ Edit, เมนู kebab, empty state, banner ไม่มี default
- `../carmen-platform/src/constants/reportGroups.ts` — `FORM_REPORT_GROUPS` ลำดับ 12 code ตายตัว
- `../carmen-platform/src/services/reportTemplateService.ts` — `setGroupDefault` (สอง `PUT` ตามลำดับ), `getAll`, `update`
- `../carmen-platform/src/utils/docVersion.ts` — `getDocVersion`, `isVersionConflict`, `notifyVersionConflict`
- `../carmen-platform/src/utils/audit.ts` — `latestActor()`
- **แก้ citation ที่ล้าสมัย:** `../carmen-platform/src/App.tsx:323-329` — route `/report-form-groups` (`requiredPermission="report_template.read"`, `feature="report_form_groups"`); `../carmen-platform/src/components/nav/platformNav.ts:25` — รายการ sidebar (ไม่ใช่ `Layout.tsx` ซึ่งไม่ได้นิยาม nav row แล้วในปัจจุบัน)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — คอลัมน์ `is_default`, partial unique index `idx_report_template_default_per_group`

## 8. หน้าในโมดูลนี้

นี่คือ sub-page ของ [Report Templates](/th/platform/report-templates) — ดู §7 ของหน้า landing นั้นสำหรับรายการ sub-page ฉบับเต็ม
