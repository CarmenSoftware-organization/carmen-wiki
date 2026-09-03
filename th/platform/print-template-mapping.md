---
title: การแมปเทมเพลตพิมพ์ (Print Template Mapping)
description: โมดูลที่ถูกลบออกแล้ว — การ routing ชนิดเอกสารไปยังเทมเพลตพิมพ์ถูกลบออกจาก carmen-platform เมื่อ 2026-07-23/24 และถูกรวมเข้ากับ Form Groups ของ Report Templates (report_group + is_default)
published: true
date: 2026-07-29T09:46:00.000Z
tags: platform/print-template-mapping, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:30:00.000Z
---

# การแมปเทมเพลตพิมพ์ (Print Template Mapping)

> **สถานะการใช้งาน (ตรวจสอบล่าสุด 2026-07-29): โมดูลนี้ถูกลบออกแล้ว** ทุกหน้าจอ, route, proxy ฝั่ง backend และตารางฐานข้อมูลที่อธิบายไว้ด้านล่างถูกลบระหว่าง 2026-07-23 ถึง 2026-07-24 ปัญหาการเลือก "ชนิดเอกสาร → เทมเพลต" ที่โมดูลนี้เคยแก้ยังคงอยู่ แต่ตอนนี้ถูกแก้ **ภายใน** [Report Templates](/th/platform/report-templates) ผ่านคู่คอลัมน์ `report_group` + `is_default` และหน้าจอใหม่ [Form Groups](/th/platform/report-templates/form-groups) (`/report-form-groups`) หน้านี้ถูกเก็บไว้เป็นบันทึกประวัติศาสตร์เพื่อให้ลิงก์เก่าและผลการค้นหานำไปสู่คำอธิบาย ไม่ใช่หน้า 404 — อย่าใช้เป็นคู่มือพฤติกรรมปัจจุบัน

ในอดีต โมดูล **Print Template Mapping** คือตาราง routing ระหว่างชนิดเอกสารกับ layout การพิมพ์: แต่ละ row บอกว่า "เมื่อเอกสารชนิด X พิมพ์ ให้ render ด้วย `tb_report_template` ตัวนี้" ขณะที่ [Report Templates](/th/platform/report-templates) เป็นฝั่งที่ *เขียน (author)* layout ของ FastReport โมดูลนี้เป็นผู้ตัดสินใจว่า *จะใช้ตัวไหน* — ต่อชนิดเอกสาร, ต่อ business unit แบบ optional โดยมี default หนึ่งตัวต่อชนิดสำหรับปุ่ม Print แบบ legacy และตัวเลือกสำรองแบบเรียงลำดับสำหรับเมนู "Print as…"

> **At a Glance**
> **สถานะ:** ถูกลบแล้ว (ยืนยัน 2026-07-23/24) &nbsp;·&nbsp; **ลบโดย:** carmen-platform commit `de11377` (หน้า SPA, route, รายการ sidebar, permission key), carmen-turborepo-backend-v2 commit `c135bb21e` (controller/service proxy ของ backend-gateway + แถว permission-seed), migration `20260723120000_print_form_default` (`DROP TABLE tb_print_template_mapping`) &nbsp;·&nbsp; **แทนที่ด้วย:** `tb_report_template.report_group` (รายการ code คงที่ 12 ตัว, `FORM_REPORT_GROUPS`) บวกคอลัมน์ใหม่ `tb_report_template.is_default` แก้ไขจากหน้าจอ **Form Groups** ใหม่ในโมดูล Report Templates &nbsp;·&nbsp; **หน้าย่อย:** 3 (เก็บไว้เพื่ออ้างอิงเชิงประวัติศาสตร์)

## 1. สิ่งที่เคยมีอยู่ และช่วงที่ถูกลบ

โมดูลนี้เปิดเผยผ่านสองหน้าจอ: `/print-template-mapping` (list แบบการ์ดจัดกลุ่ม หนึ่ง sub-table ต่อชนิดเอกสาร) และ `/print-template-mapping/new` + `/print-template-mapping/:id/edit` (ฟอร์ม create/view/edit การ์ดเดียว ซึ่งองค์ประกอบเอกลักษณ์คือ select ของ Report Template ที่ลอยเทมเพลต `kind="print"` ที่ `report_group` ตรงกันขึ้นด้านบน) เบื้องหลัง SPA, controller ของ backend-gateway (`api-system/print-template-mappings`) ส่งต่อทุกการเรียกไปยัง Go service ของ micro-report ซึ่งเป็นเจ้าของ CRUD, รายการชนิดเอกสาร 10 code แบบ canonical และ logic `resolve(document_type, bu_code)` แถวการ routing อยู่ใน platform Postgres schema ในชื่อ `tb_print_template_mapping`

ทั้งหมดนี้ถูกลบในสัปดาห์เดียวกันด้วย commit สองตัว:

- **carmen-platform, commit `de11377`** ("remove the print template mapping pages", 2026-07-24): ลบ `PrintTemplateMappingManagement.tsx`, `PrintTemplateMappingEdit.tsx`, `printTemplateMappingService.ts`, test ของมัน, สาม route `/print-template-mapping*` และ guard `requiredPermission` ใน `App.tsx`, รายการ sidebar "Print Mapping" ใน `Layout.tsx`, และรายการ breadcrumb — ลบ 1,476 บรรทัด เพิ่ม 1 บรรทัด ใน 10 ไฟล์
- **carmen-turborepo-backend-v2, commit `c135bb21e`** ("delete the print-template-mapping module and its reports proxy", 2026-07-23): ลบ controller/service/module `platform_print-template-mappings` ของ backend-gateway (พร้อม spec) และคู่ `reports.controller.ts`/`reports.service.ts` ที่เปิด proxy resolve; ลบสี่แถว `print_template_mapping.*` ออกจาก `seed.platform-permission.data.ts` และทุกการอ้างอิงถึงมันออกจาก bundle บทบาทใน `seed.platform-role-permission.data.ts` (`platform_admin`, `support_manager`, `support_staff`) — ตัว permission catalog เองไม่มี key เหล่านี้อีกต่อไป
- **Migration `20260723120000_print_form_default`** (backend repo เดียวกัน): เพิ่ม `tb_report_template.is_default BOOLEAN NOT NULL DEFAULT false`; backfill จากทุกแถว `tb_print_template_mapping` ที่ active; สร้าง partial unique index `idx_report_template_default_per_group` บน `tb_report_template(report_group)` (`WHERE is_default AND template_type = 'form' AND deleted_at IS NULL`) เพื่อบังคับ "default หนึ่งตัวต่อกลุ่มสำหรับ form template"; เปลี่ยนชื่อ report group `RFQ` เป็น `RFP` สำหรับ form-type template; และจบด้วย `DROP TABLE "tb_print_template_mapping"` ตารางหายไปในระดับ schema ไม่ใช่แค่ไม่ถูกใช้

โฟลเดอร์ collection `platform/print-template-mapping/` ของ Bruno ก็ว่างเปล่าบน branch ปัจจุบันเช่นกัน — ทุกไฟล์ request ถูกย้ายไปที่ `_archived/2026-07-29/platform/print-template-mapping/` โดยผู้ดูแล API-contract ในสัปดาห์เดียวกับที่ wiki pass นี้ทำงาน

## 2. สิ่งที่มาแทนที่

การตัดสินใจ "ชนิดเอกสาร → เทมเพลต" เดียวกันนี้ตอนนี้เกิดขึ้นบน `tb_report_template` เอง:

- `report_group` เป็น code คงที่จาก `FORM_REPORT_GROUPS` (`carmen-platform/src/constants/reportGroups.ts`): `PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP` — 12 code ไม่ใช่ 10 code เดิมของโมดูลนี้ (ได้ `SI`, `SO`, `EOP` เพิ่ม; เสีย `INV`; `RFQ` เปลี่ยนชื่อเป็น `RFP`)
- `template_type = 'form'` ระบุว่าเทมเพลตเป็น layout เอกสารเดี่ยว (`kind = 'print'` เดิม); `template_type = 'list'` คือ `kind = 'report'` เดิม (รายงานวิเคราะห์แบบตาราง) `kind` เองไม่มีอยู่ในชื่อคอลัมน์อีกต่อไป — ดู [Report Templates — Data Model](/th/platform/report-templates/data-model) สำหรับการเปลี่ยนชื่อ
- `is_default` (คอลัมน์ boolean ใหม่ที่อธิบายข้างต้น) ระบุ form template ตัวเดียวที่ business unit จะได้สำหรับ `report_group` เมื่อยังไม่ได้เลือกเอง — บทบาทเดียวกับที่ `tb_print_template_mapping.is_default` เคยทำ เพียงย้ายไปอีกตารางหนึ่งและบังคับความเป็นหนึ่งเดียวด้วย unique index จริงแทนการลด default คู่แข่งแบบ best-effort ของ Go
- หน้าจอ [Form Groups](/th/platform/report-templates/form-groups) ใหม่ (`/report-form-groups`, `ReportFormGroupManagement.tsx`, รายการ sidebar ในกลุ่ม "Content") แทนที่ list แบบการ์ดจัดกลุ่มของ `PrintTemplateMappingManagement`: หนึ่งการ์ดต่อ `report_group` แสดงทุกเทมเพลต `template_type = 'form'` ในกลุ่มนั้น พร้อม action "Set as default" ต่อแถว (`reportTemplateService.setGroupDefault`) แทน checkbox `is_default` บน form ของแถว mapping แยกต่างหาก
- ไม่มีสิ่งเทียบเท่ารายการ allow/deny ต่อ BU ของ mapping row เดิม หรือ endpoint `resolve(document_type, bu_code)` `tb_report_template` ยังคงมีคอลัมน์ `allow_business_unit` / `deny_business_unit` ของตัวเอง (การมองเห็นเทมเพลตแถวนั้นต่อ BU) แต่ไม่มีกลไกใหม่ใดจำลอง "default template ต่างกันต่อ business unit" แบบเดิม — นี่เป็นช่องว่างความสามารถจริงเมื่อเทียบกับโมดูลที่ถูกลบ ไม่ใช่สิ่งที่ pass นี้แก้ไขได้

`/report-form-groups` ไม่ใช่หนึ่งใน 11 unit ของ Platform book ที่ระบุชื่อไว้ — มันถูกบันทึกเป็น sub-page ของ [Report Templates](/th/platform/report-templates) แทน ([Form Groups](/th/platform/report-templates/form-groups)) เช่นเดียวกับที่ sub-page ของโมดูลนี้เองไม่เคยถูกนับเป็น unit แยกต่างหาก

## 3. ส่วนที่เนื้อหาเดิมยังใช้ได้

ไม่มีสิ่งใดในกฎธุรกิจ, permission key, หรือ schema เดิมของโมดูลนี้ที่ยังใช้งานอยู่ ห้ามอ้างอิง permission key `print_template_mapping.*`, route `/print-template-mapping*`, หรือ `tb_print_template_mapping` ในหน้าใหม่ — ทั้งสามหายไปแล้ว หน้าย่อยด้านล่างถูกเก็บไว้เป็นเพียงบันทึกว่าหน้าจอที่ถูกลบเคยทำอะไร สำหรับผู้ที่พยายามทำความเข้าใจการอ้างอิงเก่าที่ยังหลงเหลืออยู่ในโค้ดหรือเอกสารอื่น

## 4. โมดูลที่เกี่ยวข้อง

- [Report Templates](/th/platform/report-templates) — เป็นเจ้าของกลไกทดแทน (`report_group`, `is_default`, หน้าจอ [Form Groups](/th/platform/report-templates/form-groups)) และตาราง `tb_report_template` ที่โมดูลนี้เคยชี้ไปหา
- [Platform RBAC](/th/platform/rbac) — key `print_template_mapping.*` ที่โมดูลนี้ใช้ไม่มีอยู่ใน permission catalog อีกต่อไปเลย (ถูกลบออกจาก seed ไม่ใช่แค่ไม่ถูก assign)
- [Business Units](/th/platform/business-units) — รายการ allow/deny ของโมดูลที่ถูกลบถือ code ของ BU; การกำหนดขอบเขต BU ต่อ mapping แบบนั้นไม่มีสิ่งทดแทน (ดู §2)

## 5. แหล่งข้อมูลอ้างอิง

- carmen-platform commit `de11377` — การลบหน้า SPA, route, รายการ sidebar และการอ้างอิง permission
- carmen-turborepo-backend-v2 commit `c135bb21e` — การลบ proxy ของ backend-gateway และแถว permission-seed
- carmen-turborepo-backend-v2 migration `packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — การเพิ่ม `is_default` บน `tb_report_template`, unique index ใหม่, `DROP TABLE tb_print_template_mapping`
- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx`, `../carmen-platform/src/constants/reportGroups.ts` — หน้าจอทดแทนและรายการ `FORM_REPORT_GROUPS` ปัจจุบัน
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_archived/2026-07-29/platform/print-template-mapping/` — request ของ Bruno ที่ถูก archive สำหรับ endpoint ที่ถูกลบ

## 6. หน้าในโมดูลนี้

หน้าย่อยเหล่านี้อธิบายหน้าจอที่ถูกลบตามที่เคยเป็นจนถึง 2026-06-10 (การ sync ที่ตรวจสอบล่าสุดก่อนถูกลบ) แต่ละหน้าแนบข้อความแจ้งการถูกลบเดียวกัน

- [Data Model](/th/platform/print-template-mapping/data-model) — ตาราง field เดิมของ `tb_print_template_mapping` (ถูก drop แล้ว)
- [UI Screens](/th/platform/print-template-mapping/ui-screens) — list แบบการ์ดจัดกลุ่มเดิมและฟอร์ม view/edit-toggle (ถูกลบแล้ว)
- [Permissions](/th/platform/print-template-mapping/permissions) — เมทริกซ์ gate เดิมของ `print_template_mapping.*` และกฎ BU ตอน resolve (key ถูกลบออกจาก catalog แล้ว)
