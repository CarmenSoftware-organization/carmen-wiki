---
title: Print Template Mapping — หน้าจอ UI (UI Screens)
description: บันทึกประวัติศาสตร์ — PrintTemplateMappingManagement และ PrintTemplateMappingEdit ถูกลบออกจาก carmen-platform เมื่อ 2026-07-24 (commit de11377); ใช้หน้าจอ Form Groups ของ Report Templates แทน
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, print-template-mapping, ui
editor: markdown
dateCreated: 2026-06-10T15:30:00.000Z
---

# Print Template Mapping — หน้าจอ UI (UI Screens)

> **สถานะการใช้งาน (ตรวจสอบล่าสุด 2026-07-29): ทั้งสองหน้าจอด้านล่างถูกลบแล้ว** `PrintTemplateMappingManagement.tsx`, `PrintTemplateMappingEdit.tsx` และ `printTemplateMappingService.ts` ถูกลบออกจาก carmen-platform ใน commit `de11377` ("remove the print template mapping pages", 2026-07-24) พร้อมกับสาม route, รายการ sidebar และรายการ breadcrumb ไม่มีอะไรที่ `/print-template-mapping*` render ใน SPA ปัจจุบัน — เส้นทางนี้ตกไปที่หน้า `*` catch-all `NotFound` หน้านี้บันทึกหน้าจอตามที่เคยเป็นจนถึง 2026-06-10 เพื่อการอ้างอิงเชิงประวัติศาสตร์ สิ่งทดแทนปัจจุบันคือหน้าจอ **Form Groups** (`/report-form-groups`, `ReportFormGroupManagement.tsx`) ภายในโมดูล Report Templates — ดู [Report Templates — UI Screens](/th/platform/report-templates/ui-screens)

## 1. ภาพรวม (เชิงประวัติศาสตร์)

หน้า list (`/print-template-mapping`) เป็นการเบี่ยงเบนโดยเจตนาจากรูปแบบ Management มาตรฐานของ SPA: การ์ดเดียวที่มี sub-table แบบมีเส้นขอบหนึ่งตารางต่อชนิดเอกสาร แทนที่จะเป็น `DataTable` ฝั่ง server หน้า edit (`/print-template-mapping/new`, `/print-template-mapping/:id/edit`) เป็นฟอร์ม view/edit-toggle การ์ดเดียวแบบทั่วไป ซึ่งองค์ประกอบเอกลักษณ์คือ select ของ Report Template ที่ลอยเทมเพลต `kind="print"` ที่ `report_group` ตรงกันขึ้นด้านบน

## 2. `PrintTemplateMappingManagement` — list (เดิม)

การ์ดเดียว: ไอคอน Printer, ชื่อ "Print Template Mapping", หนึ่ง action ("New Mapping" gate ด้วย `print_template_mapping.create`) ตัวกรองเป็นแบบ inline (select ชนิดเอกสาร + checkbox "Active only" ไม่มี Sheet panel ไม่มีการค้นหาข้อความอิสระ) แถวถูกจัดกลุ่มฝั่ง client ตาม `document_type` แต่ละกลุ่มเป็น block มีเส้นขอบ (Template / Display Label / Default / Order / Active / action ของแถว) action ของแถวเป็นปุ่มไอคอน ghost แบบ inline สองปุ่ม (Edit, Delete) แทนที่ dropdown `⋯` มาตรฐาน list นี้ไม่มีสถานะที่จดจำใน `localStorage` และไม่มีการแบ่งหน้าฝั่ง client — endpoint ของ Go ตั้งค่า default `perpage = 10` และหน้านี้ render เฉพาะสิ่งที่มาถึง ตัดทอนแบบเงียบ ๆ เมื่อเกิน 10 mapping ที่ active

## 3. `PrintTemplateMappingEdit` — create/view/edit (เดิม)

โหมด create ตั้งค่า default `is_default = true`, `display_order = 0`, `is_active = true` โหมด view render ทุก field แบบ read-only พร้อมปุ่ม Edit ที่ gate ด้วย `<Can permission="print_template_mapping.update">` โหมด edit เปิดเผย Document Type, Report Template, Display Label, Display Order, Allow/Deny Business Units (text input แบบ CSV), checkbox Default และ checkbox Active select ของ Report Template โหลดเทมเพลตได้สูงสุด 500 ตัวและลอย match ของ `kind === 'print' && report_group === document_type` ขึ้นด้านบนแบบ soft sort ไม่ใช่ hard filter

## 4. สิ่งที่มาแทนที่หน้าจอเหล่านี้

หน้าจอ **Form Groups** (`/report-form-groups`) ตอนนี้ครอบคลุมงาน "เลือก default template ต่อชนิดเอกสาร": หนึ่งการ์ดต่อ `report_group` (จากรายการคงที่ `FORM_REPORT_GROUPS`) แสดงทุกเทมเพลต `template_type = 'form'` ในกลุ่มนั้นพร้อม action "Set as default" (`reportTemplateService.setGroupDefault`) แทน checkbox `is_default` บนฟอร์มของแถว mapping แยกต่างหาก ไม่มีหน้าจอภาพรวมหลายชนิดเอกสารแบบจัดกลุ่ม ไม่มี field Display Label / Display Order และไม่มีการกำหนดขอบเขต BU แบบ allow/deny ต่อ mapping ในสิ่งทดแทน — ดู [Report Templates — UI Screens](/th/platform/report-templates/ui-screens) สำหรับสิ่งที่หน้าจอใหม่ทำจริง

## 5. แหล่งข้อมูลอ้างอิง

- carmen-platform commit `de11377` — การลบ
- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx` — หน้าจอทดแทนปัจจุบัน

**Cross-links:** [หน้าแรก Print Template Mapping](/th/platform/print-template-mapping) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Report Templates — UI Screens](../report-templates/ui-screens.md)
