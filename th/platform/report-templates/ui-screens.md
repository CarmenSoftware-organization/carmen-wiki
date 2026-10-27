---
title: Report Template — UI Screens
description: Editor XML แบบ CodeMirror สามแท็บ, Preview และ Dialog layout editor, sheet เวอร์ชัน, backup/import, chip input, แถบ action ติดล่าง และ gate <Can> ของ report_template.*
published: true
date: '2026-10-27T15:00:00.000Z'
tags: book/platform, report-templates, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Report Template — UI Screens

![Report Template — UI Screens screen](/screenshots/platform/report-templates/ui-screens.png)

![Report Template — UI Screens form screen](/screenshots/platform/report-templates/ui-screens-form.png)

## 1. At a Glance

- Editor CodeMirror สามตัว (Dialog, Content, Export XML) พร้อม syntax highlighting + folding + search
- Validate แบบ live พร้อม marker บรรทัด/คอลัมน์
- แท็บ Preview ที่ render Dialog เป็น form แบบ disabled และกลายเป็น Dialog layout editor แบบลากวาง (ต้องมี viewport อย่างน้อย 768px) ระหว่างแก้ไข; แถบ data-lineage ใต้ชื่อหน้า; sheet **Versions** (ประวัติ, diff, Restore); dialog **Import** และ backup แบบ JSON
- Chip input allow/deny ของ BU
- แถบ action ติดล่างพร้อมตัวบ่งชี้การเปลี่ยนแปลงที่ยังไม่ได้บันทึก
- Gate: route guard `report_template.read` / `.create` / `.update` (**และ** `feature="report_templates"`); Add Template (ทั้ง header **และ** empty-state — ไม่มีตัวใดที่ไม่ถูก gate), Edit/Delete ของ row และ toggle Edit ห่อด้วย `<Can>` (session ที่ถือแค่ `report_template.read` เห็น dropdown ของ row เสนอเฉพาะ **Download backup**); Import ต้องมี `report_template.create`, Restore ของเวอร์ชันต้องมี `report_template.update`
- Endpoint แบบพหูพจน์: `/api-system/report-templates` (รวม `/db-objects?bu_code=<buCode>`)
- Keyboard shortcut: Ctrl/Cmd+S บันทึก, Escape เปล่า ๆ (ไม่มี modifier) ยกเลิกการแก้ไข
- **เพิ่มเมื่อ 2026-07-23 (เดิมชื่อ `kind`):** field `Template Type` (List/Form, จำเป็น) เป็น field แรกของการ์ด Template Info; เมื่อเป็น Form จะโชว์ checkbox `is_default` และ `report_group` แบบ select จากรายการคงที่ `FORM_REPORT_GROUPS` แทน input อิสระ (และบังคับ `is_standard = true` ตอน submit); chip input ของ BU ถูก disable และล้างค่าสำหรับเทมเพลตแบบ Form; หน้ารายการมีคอลัมน์ Template Type ใหม่และ filter ตัวที่สาม (Template Type) และตั้งแต่รอบ 2026-10 มี filter ที่สี่ Calculation Method; default sort เปลี่ยนเป็น `name:asc`
- Not-found gating และ `doc_version` optimistic lock เพิ่มมาที่หน้า edit
- **เพิ่มเมื่อ 2026-08-22:** การ์ด "Metadata" เดิมถูกลบออก — audit ("Created/Updated ... by ...") ย้ายไปแสดงเป็นบรรทัดเดียวใน `PageHeader` แทน (`normalizeAudit()` + `AuditMeta variant="header"`); คอลัมน์ Created/Updated ของหน้ารายการก็เปลี่ยนไปใช้ `auditColumns()`/`AuditMeta` ร่วมกันแบบเดียวกัน (relative time + tooltip แบบ absolute)
- **เพิ่มเมื่อ 2026-08-31 เป็นต้นไป (ข้ามโมดูล):** action **View History** ปรากฏทั้งใน dropdown ของแถวใน list และในแถว `actions` ของ header หน้า edit gate ด้วย `activity_log.read` พร้อม `clusterId={BACKSTAGE_SCOPED_RECORD}`

## 2. References

- ../carmen-backstage/src/pages/ReportTemplateEdit.tsx
- ../carmen-backstage/src/pages/ReportTemplateManagement.tsx
- ../carmen-backstage/src/components/nav/backstageNav.ts (รายการ sidebar — ไม่ใช่ Layout.tsx)

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/report-templates/ui-screens
- [ ] Screenshot แต่ละแท็บ
