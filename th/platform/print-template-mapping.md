---
title: การแมปเทมเพลตพิมพ์ (Print Template Mapping)
description: ภาพรวมโมดูล Print Template Mapping — การ route ชนิดเอกสาร (PR, PO, GRN, …) ไปยังเทมเพลตพิมพ์ FastReport พร้อม flag default, การเรียงลำดับการแสดงผล และการกำหนดขอบเขต allow/deny ต่อ BU
published: true
date: 2026-06-10T15:30:00.000Z
tags: platform/print-template-mapping, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:30:00.000Z
---

# การแมปเทมเพลตพิมพ์ (Print Template Mapping)

โมดูล **Print Template Mapping** คือตาราง routing ระหว่างชนิดเอกสารกับ layout การพิมพ์: แต่ละ row บอกว่า "เมื่อเอกสารชนิด X พิมพ์ ให้ render ด้วย `tb_report_template` ตัวนี้" ขณะที่ [Report Templates](/th/platform/report-templates) เป็นฝั่งที่ *เขียน (author)* layout ของ FastReport (row ที่ `kind = "print"`) โมดูลนี้ตัดสินใจว่า *จะใช้ตัวไหน* — ต่อชนิดเอกสาร, ต่อ business unit แบบ optional, โดยมี default หนึ่งตัวต่อชนิดสำหรับปุ่ม Print แบบ legacy และตัวเลือกสำรองแบบเรียงลำดับสำหรับเมนู "Print as…" สัญญา runtime ที่ตั้งใจไว้คือ `GET .../resolve?document_type=X&bu_code=Y` ซึ่งคืน mapping เพียงหนึ่งเดียวเป๊ะ ๆ — แม้ว่าเส้นทางพิมพ์ของ micro-business ในปัจจุบันจะ query ตารางโดยตรงโดยไม่มีการกำหนดขอบเขต BU (ดู [Permissions](/th/platform/print-template-mapping/permissions) §3)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** map ชนิดเอกสาร (PR, PO, GRN, SR, CN, IA, PC, SC, RFQ, INV) ไปยัง report template ที่ `kind="print"` พร้อม `is_default` สำหรับปุ่ม Print แบบ legacy, `display_label`/`display_order` สำหรับเมนู "Print as…" และการกำหนดขอบเขต allow/deny ต่อ BU &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA, Go service ของ micro-report และ flow การพิมพ์เอกสารใน micro-business &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_print_template_mapping` (เป็นเจ้าของ), `tb_report_template` (ถูกอ้างอิง — ดู Report Templates) &nbsp;·&nbsp; **สัญญา runtime:** `GET /api-system/print-template-mappings/resolve` — mapping ที่ active ตัวแรกที่อนุญาต BU เรียงตาม `is_default DESC, display_order ASC` &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

SPA เปิดเผยโมดูลนี้ผ่านสองหน้าจอ:

- **`/print-template-mapping` → `PrintTemplateMappingManagement`** — เป็น **การเบี่ยงเบนโดยเจตนา** จากรูปแบบ Management แบบ `DataTable` ฝั่ง server มาตรฐานของ SPA: การ์ดเดียวที่มี sub-table แบบจัดกลุ่ม หนึ่งกลุ่มต่อชนิดเอกสาร (Badge ของ code + label + จำนวน "N mapping(s)") กรองด้วยเพียง select ชนิดเอกสารและ checkbox "Active only" ไม่มีการค้นหาแบบ debounce, ไม่มีส่งออก CSV, ไม่มีตัวควบคุมการแบ่งหน้า, ไม่มีสถานะ `localStorage` ที่จดจำไว้ — ชุดข้อมูลเล็กและนิ่งพอที่องค์ประกอบหนัก ๆ เหล่านั้นจะกลายเป็นสิ่งรบกวน ดู [UI Screens](/th/platform/print-template-mapping/ui-screens) §1 สำหรับเหตุผลฉบับเต็ม
- **`/print-template-mapping/new` และ `/print-template-mapping/:id/edit` → `PrintTemplateMappingEdit`** — ฟอร์มการ์ดเดียวแบบมาตรฐาน โหมด create แก้ไขได้ทันที; route edit เปิดแบบ read-only อยู่หลัง toggle Edit (รูปแบบ view/edit เดียวกับ Applications) องค์ประกอบที่เป็นเอกลักษณ์ของมันคือ **select ของ Report Template** ซึ่งลอยเทมเพลตที่ตรงกับ `kind = "print"` และ `report_group = <ชนิดเอกสารที่เลือก>` ขึ้นด้านบน พร้อมจำนวน "N match / M total" ใน placeholder

เบื้องหลัง SPA, controller ของ backend-gateway (`api-system/print-template-mappings`) เป็น proxy แบบ authenticated บาง ๆ: ทุกการเรียกถูกส่งต่อผ่าน HTTP ธรรมดาไปยัง **Go service ของ micro-report** (`/api/print-template-mappings/*`) ซึ่งเป็นเจ้าของ CRUD, รายการชนิดเอกสารแบบ canonical และ logic ของ `resolve` ตัว row ของ mapping เองอยู่ใน Postgres schema ของแพลตฟอร์ม (`tb_print_template_mapping`) ซึ่ง Go อ่านผ่าน LEFT JOIN ที่ denormalize ชื่อและ group ของเทมเพลตลงบนแต่ละ row

## 2. บริบททางธุรกิจ

เอกสารของ Carmen พิมพ์ผ่าน FastReport: เมื่อผู้ใช้คลิก **Print** บน PO, GRN หรือ store requisition, backend สร้าง data payload ของเอกสารและต้องรู้ว่า *row ของเทมเพลตตัวไหน* จะ render มัน ในอดีตสิ่งนั้นเป็น naming convention (`"<Type> Document"`); โมดูลนี้แทนที่ convention ด้วยข้อมูลแบบระบุชัด:

- **ปุ่ม Print แบบ legacy** พิมพ์ด้วย mapping ที่ติด flag `is_default` ของชนิดเอกสารนั้น — คลิกเดียว ไม่มีเมนู
- **เมนู "Print as…"** แสดงทุก mapping ที่ active ของชนิดนั้น เรียงตาม `display_order` และติด label ด้วย `display_label` (เช่น "Standard PR (A4 Portrait)") — property หนึ่งจึงเสนอต้นฉบับแนวตั้งบวกตัวเลือกแนวนอนหรือแบบติดแบรนด์ได้
- **รายการ allow/deny ต่อ BU** มีอยู่เพราะ layout แตกต่างกันต่อ property: โรงแรมเรือธงของกลุ่มอาจต้องการสลิป GRN ติดแบรนด์ของตัวเอง ขณะที่ property พี่น้องใช้ตัวมาตรฐาน รายการ allow ที่ว่างหมายถึง "ทุก business unit"; รายการ deny ชนะเสมอ นี่คือ convention การกำหนดขอบเขตเดียวกับที่ `tb_report_template` เองถืออยู่

seed ของแพลตฟอร์ม (`seed.print-templates.ts`) ส่งมอบเทมเพลต `kind="print"` แนวตั้งและแนวนอนอย่างละหนึ่งต่อชนิดเอกสาร และลงทะเบียนตัวแนวตั้งเป็น mapping default ของชนิดนั้น (`display_order 0`) สภาพแวดล้อมใหม่จึงพิมพ์เอกสารได้ทุกชนิดทันทีตั้งแต่แกะกล่อง

## 3. แนวคิดสำคัญ

- **Mapping row** — `(document_type, report_template_id)` บวกการนำเสนอ (`display_label`, `display_order`), flag `is_default`, การกำหนดขอบเขต BU (`allow_business_unit` / `deny_business_unit`) และ `is_active` หลาย row อาจใช้ชนิดเอกสารร่วมกันได้
- **ชนิดเอกสาร** — **รายการที่ hard-code ไว้ใน Go service ของ micro-report** (`model.SupportedDocumentTypes`): PR, PO, GRN, SR, CN, IA, PC, SC, RFQ, INV เสิร์ฟโดย `GET .../document-types` (ซึ่งเติมทุก dropdown ใน SPA) และ **validate ฝั่ง server** — create/update ด้วย code ที่ไม่อยู่ในรายการถูกปฏิเสธด้วย 400 การเพิ่มชนิดเอกสารเป็นการเปลี่ยนโค้ด Go ไม่ใช่การเปลี่ยนข้อมูล
- **Flag default** — "ใช้เทมเพลตนี้เมื่อผู้ใช้คลิกปุ่ม Print แบบ legacy" UI ไม่ห้ามคุณ save default สองตัว แต่ Go service รัน `EnsureSingleDefault` แบบ best-effort หลังทุก create/update ที่ save `is_default = true` โดยลดสถานะ default ตัวอื่นของชนิดเอกสารเดียวกัน สังเกตว่าคอลัมน์นี้ *default เป็น true* — schema, Go และ SPA ตรงกันทั้งหมด ดังนั้น operator ต้องตั้งใจ untick มันสำหรับตัวเลือกสำรอง
- **Display label และ order** — เป็นการนำเสนอล้วน ๆ สำหรับเมนู "Print as…" `display_order` ทำหน้าที่สองอย่างโดยเป็น tie-breaker ของ resolve ในหมู่ row ที่มีค่า `is_default` เท่ากัน
- **รายการ BU แบบ allow/deny** — array JSONB ของ BU code แก้ไขเป็นข้อความคั่นด้วย comma ใน SPA allow ว่าง = ทุก BU; deny ว่าง = ไม่มี; code ที่อยู่ทั้งสองรายการถูก deny (deny ถูกตรวจสอบก่อน) กฎ precedence ฉบับเต็มและ pseudo-code อยู่ใน [Permissions](/th/platform/print-template-mapping/permissions) §3
- **ความสัมพันธ์กับ Report Templates** — mapping ชี้ไปยัง row ของ `tb_report_template` หนึ่งตัว; การจับคู่ที่ตั้งใจไว้คือ `kind = "print"` ที่ `report_group` เท่ากับ code ของชนิดเอกสาร ซึ่งเป็นเหตุผลที่ select เทมเพลตของฟอร์ม edit ลอย match เหล่านั้นขึ้นด้านบน การจับคู่เป็น convention ไม่ใช่ constraint: select ยังคงเสนอทุกเทมเพลต และฐานข้อมูลไม่บังคับ FK ใด ๆ (ดู [Data Model](/th/platform/print-template-mapping/data-model))
- **Resolution** — `resolve(document_type, bu_code)` กรองเหลือ row ที่ active และไม่ถูกลบของชนิดนั้น เรียงตาม `is_default DESC, display_order ASC` และคืน **row แรกที่รายการ BU ของมันอนุญาต `bu_code`** — ดังนั้น default ที่ deny BU นั้นจะตกผ่านเงียบ ๆ ไปยังตัวเลือกสำรองถัดไปที่ได้รับอนุญาต ไม่พบ match คือ 404 — แม้ว่าเส้นทางพิมพ์ของ micro-business ในปัจจุบันจะ query ตารางโดยตรงและข้ามการตรวจสอบ BU (ดู [Permissions](/th/platform/print-template-mapping/permissions) §3)

## 4. บทบาทและ Persona

การเข้าถึงถูก gate ด้วย permission ผ่าน [Platform RBAC](/th/platform/rbac) ด้วย route guard และ gate `<Can>` ภายในหน้า:

| Surface | Gate | Key |
|---|---|---|
| route `/print-template-mapping` + รายการ sidebar "Print Mapping" (กลุ่ม Content, ไอคอน Printer) | `PrivateRoute` / sidebar filter | `print_template_mapping.read` |
| route `/print-template-mapping/new` | `PrivateRoute` | `print_template_mapping.create` |
| route `/print-template-mapping/:id/edit` | `PrivateRoute` | `print_template_mapping.update` |
| ปุ่ม New Mapping (header ของหน้า list) | `<Can>` | `print_template_mapping.create` |
| Edit ของ row (ปุ่มไอคอนดินสอ) | `<Can>` | `print_template_mapping.update` |
| Delete ของ row (ปุ่มไอคอนถังขยะ) | `<Can>` | `print_template_mapping.delete` |
| toggle Edit (header ของหน้า edit) | `<Can>` | `print_template_mapping.update` |

เช่นเดียวกับ Applications, `print_template_mapping.delete` มีอยู่เป็น gate ภายในหน้าเท่านั้น (ไม่มี route ใดต้องการมัน และหน้า edit ไม่มี action ลบ) และปุ่ม Save ของหน้า edit ไม่ถูกห่อแต่ไปถึงไม่ได้หากไม่มี toggle Edit ที่ถูก gate เมทริกซ์ฉบับเต็มบวกกฎ BU ตอน resolve — เรื่องราว authorization ที่สองที่เป็นอิสระ — อยู่ใน [Permissions](/th/platform/print-template-mapping/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [Report Templates](/th/platform/report-templates) — อีกครึ่งหนึ่งของคู่ feature: มันเป็นเจ้าของ `tb_report_template` (ตัว layout, Dialog/Content XML ของพวกมัน, การผูก source และ field `kind`/`report_group` ที่โมดูลนี้ใช้เลือก) หน้า data-model ของโมดูลนั้นกำหนดขอบเขต `tb_print_template_mapping` ออกไปอย่างชัดเจน; โมดูลนี้คือผู้ document มัน
- [Business Units](/th/platform/business-units) — รายการ allow/deny ถือ *code* ของ BU (`tb_business_unit.code`) ป้อนเป็นข้อความอิสระโดยไม่มีการ validate กับทะเบียน BU; การพิมพ์ผิดเพียงแค่ไม่มีวัน match ตอน resolve
- [Platform RBAC](/th/platform/rbac) — กำหนดและ resolve key `print_template_mapping.*` ทั้งสี่ (seed ใน `seed.platform-permission.ts`)

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — route guard `print_template_mapping.*` ทั้งสาม
- `../carmen-platform/src/components/Layout.tsx` — รายการ sidebar "Print Mapping" (กลุ่ม Content, `print_template_mapping.read`)
- `../carmen-platform/src/pages/PrintTemplateMappingManagement.tsx` — list แบบการ์ดจัดกลุ่ม, filter, gate `<Can>`, dialog ลบ
- `../carmen-platform/src/pages/PrintTemplateMappingEdit.tsx` — ฟอร์ม create/view/edit, logic การลอยของ template-select, ช่องกรอก BU แบบ CSV
- `../carmen-platform/src/services/printTemplateMappingService.ts` — REST client และ type `PrintTemplateMapping` / `DocumentType`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_print_template_mapping` (บรรทัด 776), `tb_report_template` (บรรทัด 701)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_print-template-mappings/` — controller/service ของ proxy
- `../micro-report/controller/print_template_mapping_controller.go`, `../micro-report/db/print_template_mapping_repo.go`, `../micro-report/model/print_template_mapping.go` — CRUD, `SupportedDocumentTypes`, `Resolve`, `EnsureSingleDefault`
- `../carmen-turborepo-backend-v2/apps/micro-business/src/common/print-report.helper.ts` — consumer ของการพิมพ์เอกสาร

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/print-template-mapping/data-model) — ตาราง field ของ `tb_print_template_mapping` (ไม่มี unique constraint, ไม่มี FK ระดับ DB), มุมมองฝั่ง FK ของ `tb_report_template` และความแตกต่างระหว่าง Prisma, type ของ SPA และ Go service
- [UI Screens](/th/platform/print-template-mapping/ui-screens) — list แบบการ์ดจัดกลุ่ม (และเหตุผลที่มันเบี่ยงเบนจากรูปแบบ DataTable) และฟอร์มแบบ view/edit-toggle พร้อม select เทมเพลตที่ลอย match ขึ้นด้านบน
- [Permissions](/th/platform/print-template-mapping/permissions) — เมทริกซ์ gate ของ `print_template_mapping.*`, กฎ precedence ของ allow/deny ตอน resolve และเมทริกซ์กรณีพิเศษสำหรับผู้ทดสอบ
