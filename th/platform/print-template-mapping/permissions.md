---
title: Print Template Mapping — สิทธิ์ (Permissions)
description: บันทึกประวัติศาสตร์ — สี่ permission key print_template_mapping.* ถูกลบออกจาก permission catalog ของแพลตฟอร์มเมื่อ 2026-07-23; ไม่มี key ทดแทนสำหรับ Form Groups
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, print-template-mapping, permissions
editor: markdown
dateCreated: 2026-06-10T15:30:00.000Z
---

# Print Template Mapping — สิทธิ์ (Permissions)

> **สถานะการใช้งาน (ตรวจสอบล่าสุด 2026-07-29): key `print_template_mapping.*` ไม่มีอยู่แล้ว** carmen-turborepo-backend-v2 commit `c135bb21e` ลบทั้งสี่แถว (`read`/`create`/`update`/`delete`) ออกจาก `seed.platform-permission.data.ts` และทุกการอ้างอิงถึงมันออกจาก bundle บทบาทใน `seed.platform-role-permission.data.ts` (`platform_admin`, `support_manager`, `support_staff`) ตัว permission catalog เองไม่มี key เหล่านี้อีกต่อไป — บทบาทที่สร้างวันนี้เลือก key เหล่านี้จาก `PermissionPicker` ไม่ได้เลยด้วยซ้ำ เพราะ [Permission Catalog](/th/platform/rbac/ui-screens) แสดงเฉพาะสิ่งที่ backend ส่งกลับมา หน้านี้บันทึกเมทริกซ์ gate เดิมเพื่อการอ้างอิงเชิงประวัติศาสตร์ ดู [Report Templates — Permissions](/th/platform/report-templates/permissions) สำหรับวิธี gate สิ่งทดแทน Form Groups (ใช้ `report_template.*` ซ้ำ — ไม่มี key ใหม่สำหรับมัน)

## 1. ภาพรวม (เชิงประวัติศาสตร์)

โมดูลนี้เคยมีเรื่องราว authorization ที่เป็นอิสระสองเรื่องมาบรรจบกัน: การ gate แบบ Platform RBAC ทั่วไปบนสี่ key `print_template_mapping.*` (ใครเห็น/แก้แถว mapping ได้) และกฎ BU ตอน resolve ที่ฝังอยู่ในแถว mapping เอง (mapping ไหนที่ pipeline การพิมพ์เลือกสำหรับคู่ชนิดเอกสาร + business unit หนึ่ง ๆ) ทั้งสองหายไปแล้ว — key ถูกลบออกจาก catalog และ endpoint `resolve` พร้อม logic ลำดับความสำคัญ allow/deny ของ BU ถูกลบไปพร้อมกับ mapping repo ฝั่ง Go

## 2. เมทริกซ์ gate เดิม

| Surface | Key |
|---|---|
| `/print-template-mapping` | `print_template_mapping.read` |
| `/print-template-mapping/new` | `print_template_mapping.create` |
| `/print-template-mapping/:id/edit` | `print_template_mapping.update` |
| Sidebar "Print Mapping" (กลุ่ม Content) | `print_template_mapping.read` |
| Row Delete | `print_template_mapping.delete` (ภายในหน้าเท่านั้น ไม่มี route ใดต้องการมันเลย) |

## 3. กฎตอน resolve เดิม

Endpoint `resolve(document_type, bu_code)` ที่ถูกลบเคยเรียง mapping ที่ active และไม่ถูกลบสำหรับชนิดเอกสารหนึ่งตาม `is_default DESC, display_order ASC` และคืน row แรกที่รายการ allow/deny ของ BU อนุญาต `bu_code` ของผู้เรียก (ตรวจ deny ก่อน; `bu_code` ที่ว่างข้ามการตรวจ BU ทั้งหมด) logic นี้ รวมถึงช่องว่างที่ทราบแล้วว่าเส้นทางพิมพ์จริงของ micro-business query ตารางโดยตรงโดยไม่ใช้การตรวจ BU ไม่มีผลกับสิ่งใดอีกต่อไป — ทั้งตารางและ endpoint หายไปแล้ว

## 4. สิ่งที่ควบคุมสิ่งทดแทน

หน้าจอ Form Groups (`/report-form-groups`) ถูก gate ด้วย `report_template.read` (route + sidebar) และ `report_template.update` / `.create` สำหรับ action ที่แก้ไข (การตั้ง default ของกลุ่ม, การเพิ่ม form template ใหม่) — มันใช้ key เดิมของโมดูล Report Templates ซ้ำ ไม่ได้สร้าง key ใหม่ ไม่มีกฎ routing ต่อ business unit ในสิ่งทดแทน จึงไม่มีอะไรคล้ายกันให้ทดสอบเรื่องลำดับความสำคัญของ allow/deny BU — ดู [Report Templates — Permissions](/th/platform/report-templates/permissions)

## 5. แหล่งข้อมูลอ้างอิง

- carmen-turborepo-backend-v2 commit `c135bb21e` — การลบสี่ key ออกจาก permission seed และทุก role bundle
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` — catalog seed ปัจจุบัน (ไม่มีแถว `print_template_mapping`)

**Cross-links:** [หน้าแรก Print Template Mapping](/th/platform/print-template-mapping) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Report Templates — Permissions](../report-templates/permissions.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md)
