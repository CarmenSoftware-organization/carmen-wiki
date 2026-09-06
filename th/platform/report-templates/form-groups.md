---
title: เทมเพลตรายงาน — Form Groups
description: หน้าจอ /report-form-groups ตอนนี้มีโมดูลระดับบนสุดของตัวเองแล้ว — หน้านี้ครอบคลุมเฉพาะส่วนที่ยังเฉพาะเจาะจงกับ Report Templates คือคอลัมน์ tb_report_template ที่ใช้ร่วมกันและการส่งต่อ Add/Edit ระหว่างสองหน้าจอ
published: true
date: 2026-09-06T21:00:00.000Z
tags: book/platform, report-templates, form-groups
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# เทมเพลตรายงาน — Form Groups

> **ย้ายแล้ว:** หน้าจอ `/report-form-groups` (`ReportFormGroupManagement` มี route, รายการ sidebar และ feature key `report_form_groups` เป็นของตัวเอง) ถูก document ไว้ฉบับเต็มที่ **[กลุ่มฟอร์มรายงาน (Report Form Groups)](/th/platform/report-form-groups)** — layout, flow การตั้ง default ของกลุ่ม, กลุ่มตายตัว vs. legacy, บทบาท และกรณีขอบเขต หน้านี้ตอนนี้ครอบคลุมเฉพาะความสัมพันธ์เดียวที่ยังเฉพาะเจาะจงกับ Report Templates จริง ๆ: คอลัมน์ `tb_report_template` ที่ใช้ร่วมกัน และการส่งต่อ Add/Edit ระหว่างสองหน้าจอ

## 1. สิ่งที่ Report Form Groups แก้ไขบนตารางของโมดูลนี้

Report Form Groups แก้ไขคอลัมน์ที่โมดูลนี้เป็นเจ้าของบน `tb_report_template` อยู่สามคอลัมน์เท่านั้น: `template_type` (จำกัดเป็น `"form"` สำหรับทุกอย่างที่แสดงที่นั่น), `report_group` (SPA จำกัดไว้ที่รายการ code ตายตัว 12 ตัวตามที่บันทึกไว้ที่ [กลุ่มฟอร์มรายงาน](/th/platform/report-form-groups) §3.4) และ `is_default` (flag default ของกลุ่ม ตั้งผ่านคู่ `PUT` สองขั้นที่ไม่ใช่ transaction เดียวของหน้าจอนั้นเอง — ดู §3.3 ของมัน) ทุกฟิลด์อื่นบนแถว — payload XML, การผูก data source, ขอบเขต BU, `is_standard`/`is_active` — แก้ไขได้เฉพาะที่นี่เท่านั้น บนหน้า Edit ของโมดูลนี้เอง; Report Form Groups ไม่มี edit surface ของตัวเอง

action Add/Edit ของทั้งสองหน้าจอไปจบที่เดียวกัน ปุ่ม **New Form Template** ที่ header และปุ่ม **Add** ของแต่ละการ์ดบน Report Form Groups navigate ไป `/report-templates/new` — create route ของโมดูลนี้เอง — พร้อม pre-fill `template_type: 'form'` (ปุ่ม **Add** ของการ์ดยัง pre-fill `report_group` ของการ์ดนั้นด้วย) ลิงก์ **Edit** ของทุกแถวบนหน้าจอนั้นเปิด `/report-templates/:id/edit` ซึ่งเป็นหน้า edit ของโมดูลนี้เอง Report Form Groups เป็นมุมมองแบบจัดกลุ่มที่คัดสรรมาบนแถวที่หน้า Edit ของโมดูลนี้เป็นเจ้าของเต็มตัว ไม่ใช่ authoring surface คู่ขนาน

ทั้งสองหน้าจอยังใช้ permission key ร่วมกันซึ่งควรพูดซ้ำจากฝั่งนี้: `/report-templates` และ `/report-form-groups` ทั้งคู่ gate ด้วย `report_template.read` (ดู [Permissions](/th/platform/report-templates/permissions) §7) — grant ที่นี่คือ grant ที่นั่นด้วย สิ่งที่แยกทั้งสองออกจากกันอย่างเป็นอิสระคือ key **feature**: `report_templates` สำหรับโมดูลนี้ `report_form_groups` สำหรับอีกฝั่ง

## 2. แหล่งข้อมูลอ้างอิง

- [กลุ่มฟอร์มรายงาน (Report Form Groups)](/th/platform/report-form-groups) — เอกสารฉบับเต็มของหน้าจอ
- [Report Templates](/th/platform/report-templates) §3 — นิยามฟิลด์ `template_type`/`report_group`/`is_default` ของโมดูลนี้เอง
- [Permissions](/th/platform/report-templates/permissions) — matrix gate `report_template.*` ฉบับเต็มที่ทั้งสองหน้าจอใช้ร่วมกัน
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` — หน้า Edit ที่ใช้ร่วมกัน ซึ่ง action Add/Edit ของทั้งสองหน้าจอเปิด
