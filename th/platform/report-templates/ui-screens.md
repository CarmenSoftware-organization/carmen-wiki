---
title: Report Template — UI Screens
description: Editor XML แบบ CodeMirror, แท็บ preview, chip input, แถบ action ติดล่าง และ gate <Can> ของ report_template.*
published: true
date: 2026-06-10T16:30:00.000Z
tags: book/platform, report-templates, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Report Template — UI Screens

## 1. At a Glance

- Editor CodeMirror สองตัว (Dialog, Content) พร้อม syntax highlighting + folding + search
- Validate แบบ live พร้อม marker บรรทัด/คอลัมน์
- แท็บ Dialog Preview ที่ render form แบบ disabled
- Chip input allow/deny ของ BU
- แถบ action ติดล่างพร้อมตัวบ่งชี้การเปลี่ยนแปลงที่ยังไม่ได้บันทึก
- Gate: route guard `report_template.read` / `.create` / `.update`; Add Template, Edit/Delete ของ row และ toggle Edit ห่อด้วย `<Can>` (session ที่ถือแค่ `report_template.read` เห็น dropdown ของ row ว่างเปล่า)
- Endpoint แบบพหูพจน์: `/api-system/report-templates` (รวม `/db-objects?bu_code=<buCode>`)
- Keyboard shortcut: Ctrl/Cmd+S บันทึก, Escape เปล่า ๆ (ไม่มี modifier) ยกเลิกการแก้ไข

## 2. References

- ../carmen-platform/src/pages/ReportTemplateEdit.tsx
- ../carmen-platform/src/pages/ReportTemplateManagement.tsx

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/report-templates/ui-screens
- [ ] Screenshot แต่ละแท็บ
