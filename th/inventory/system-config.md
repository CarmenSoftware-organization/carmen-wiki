---
title: ระบบและการตั้งค่า (System Configuration)
description: การตั้งค่าระบบสำหรับการไหลของเอกสารและช่วงงวดบัญชี — workflow, period, running code เป็นหน้าจอจริงที่ใช้งานได้; dimension, menu, application-config และ query-dataset เป็นฟีเจอร์ schema/backend ที่ไม่มี Sysadmin UI ใช้งานได้จริง
published: true
date: 2026-07-29T11:00:00.000Z
tags: system-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ระบบและการตั้งค่า (System Configuration)

> **At a Glance**
> **วัตถุประสงค์โมดูล:** กลไกสำหรับการไหลของเอกสารและช่วงงวดบัญชี — เวิร์กโฟลว์การอนุมัติ ช่วงงวดบัญชี การกำหนดเลขที่เอกสาร บวกแนวคิดหลายตัวที่ provision ไว้ใน schema แต่ยังไม่ implement (มิติ, การตั้งค่าแอปทั่วไป, menu registry) &nbsp;·&nbsp; **กลุ่มเป้าหมาย:** Sysadmin, Workflow Administrator, Finance (ปิดงวด) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_workflow`, `tb_period`, `tb_dimension`, `tb_config_running_code`, `tb_application_config`, `tb_menu`, `tb_business_unit` (ฟิลด์ config), `tb_notification_template`, `tb_activity` &nbsp;·&nbsp; **หน้าย่อย:** 14 &nbsp;·&nbsp; **ตรวจสอบ 2026-07-29: 9 จาก 14 หน้าย่อยอธิบายหน้าจอ Sysadmin ที่มีจริงและเข้าถึงได้ (workflow, period, running-code, config-email, document, dashboard-dataset, company-profile, notification-template, activity-log); dimension และ menu ไม่มี code path เลยนอกจากตาราง schema ที่ dead; application-config และ query-dataset เป็นความสามารถ backend จริงแต่ไม่มีหน้าจอ admin ทั่วไป**

![ระบบและการตั้งค่า (System Configuration) screen](/screenshots/system-config/index.png)

## 1. ภาพรวม

ระบบและการตั้งค่าเป็นโมดูลร่มของ **กลไกการไหลของเอกสารและช่วงงวดบัญชี** ที่ทุกโมดูลธุรกรรมต้องพึ่งพา เวิร์กโฟลว์กำหนดเส้นทางการอนุมัติแบบหลายขั้น พร้อมการกระทำ ผู้รับ และการแสดงผลของฟิลด์ในแต่ละขั้น ช่วงงวดกำหนดปฏิทินบัญชีและควบคุมว่าวันที่ใดของการ post จะถูกอนุญาต (ผ่านหน้าจอ CRUD ธรรมดา — ดู [system-config/period](/th/inventory/system-config/period)) Running code ขับเคลื่อนการกำหนดเลขที่เอกสาร (ผ่าน dialog แก้ JSON ดิบ — ดู [system-config/running-code](/th/inventory/system-config/running-code)) Application config คือตาราง key-value ที่ใช้จริง แต่ถูก consume เป็นราย key โดยฟีเจอร์เฉพาะ (การตั้งค่า SMTP, signature candidates) แทนที่จะผ่าน editor ทั่วไป มิติและ menu registry คือ **สิ่งที่ provision ไว้ใน schema แต่ยังไม่ implement** — ไม่พบ CRUD service หรือ frontend route ใดเลยสำหรับทั้งสอง จากการค้นทั่ว repo ทั้ง `carmen-inventory-frontend-react` และ `carmen-turborepo-backend-v2`

ทั้งหกเอนทิตีในที่นี้อยู่ระหว่าง [master-data](/th/inventory/master-data) (แคตตาล็อกแบบสถิตย์ — หน่วยนับ ผู้ขาย สกุลเงิน) และเลเยอร์ runtime [access-control](/th/inventory/access-control) (ผู้ใช้ บทบาท สิทธิ์) ในขณะที่ master data ตอบคำถามว่าธุรกรรมกำลังอ้างอิง *อะไร* การตั้งค่าระบบตอบคำถามว่าควรไหล *อย่างไร* ควร post *เมื่อไหร่* และควรพ่วง *มิติพิเศษอะไร* — ข้อสุดท้าย ("มิติพิเศษ") ยังคงเป็นเจตนาการออกแบบเท่านั้นในวันนี้ รายการส่วนใหญ่เป็นเจ้าของและแก้ไขโดย Sysadmin; บางส่วน — โดยเฉพาะขั้นเวิร์กโฟลว์ — มีการปรับแต่งรายวันโดย Workflow Administrator ที่ได้รับมอบหมาย

ทั้งหกเอนทิตีอยู่ใน **tenant** schema ไม่มีเอนทิตีใดที่มี counterpart ในระดับแพลตฟอร์ม — เพราะอธิบายการไหลของเอกสารต่อ property ดังนั้นแต่ละ tenant ได้สำเนาของตัวเอง

## 2. กลุ่มเป้าหมาย

Sysadmin การนิยามเวิร์กโฟลว์อาจมอบหมายให้ persona Workflow Administrator (โดยทั่วไปคือ Finance Manager หรือ Procurement Manager) เพื่อบำรุงรักษาขั้น / ผู้อนุมัติรายวัน Finance เป็นเจ้าของการปิดงวด

## 3. รายการเอนทิตี

| เอนทิตี | วัตถุประสงค์ | จัดการโดย | การ implement |
| ------ | ------- | ---------- | --------------- |
| [workflow](/th/inventory/system-config/workflow) | เวิร์กโฟลว์การอนุมัติแบบหลายขั้น พร้อมการกระทำ ผู้รับ และการแสดงผลของฟิลด์ในแต่ละขั้น | Sysadmin / Workflow Admin | หน้าจอจริง |
| [period](/th/inventory/system-config/period) | ช่วงงวดบัญชี (open/closed/locked) และ snapshot สต๊อกต่องวด | Sysadmin / Finance | หน้าจอจริง — CRUD ธรรมดา ไม่มี action Close/Lock/Reopen เฉพาะ |
| [running-code](/th/inventory/system-config/running-code) | รูปแบบเลขที่เอกสารต่อประเภทเอกสาร | Sysadmin | หน้าจอจริง — แก้ JSON ดิบ ไม่มี segment builder |
| [config-email](/th/inventory/system-config/config-email) | SMTP profile ต่อ BU สำหรับอีเมลขาออกของระบบ — การแจ้งเตือนเวิร์กโฟลว์ รายงานตามตารางเวลา รีเซ็ตรหัสผ่าน | Sysadmin ตามข้อตกลง | หน้าจอจริง; **backend ไม่มี permission guard** |
| [document](/th/inventory/system-config/document) | Registry การจัดเก็บไฟล์ scope ตาม tenant — upload, list, download และ delete สำหรับเอกสารที่แนบกับ record ธุรกรรม | Sysadmin | หน้าจอจริง; backed ด้วย `tb_file_tag` + MinIO (ไม่ใช่ `tb_attachment`) |
| [dashboard-dataset](/th/inventory/system-config/dashboard-dataset) | แคตตาล็อก read-only ของ data feed ที่ลงทะเบียนไว้ในโค้ดสำหรับ widget บนแดชบอร์ด | Sysadmin | หน้าจอจริง |
| [company-profile](/th/inventory/system-config/company-profile) | สองหน้าจอ (Company Profile + Default Setting) แก้ไขกลุ่มฟิลด์ที่แยกกันของแถว `tb_business_unit` ปัจจุบัน — identity/ที่อยู่/format และ config PR/SI/PO + การเลือก print-form | Sysadmin | หน้าจอจริง; `/system-admin/business-setting` เป็น redirect ที่ตายแล้วไปยัง Company Profile |
| [notification-template](/th/inventory/system-config/notification-template) | Template ข้อความที่ใช้ซ้ำได้ ถูกเลือกต่อ workflow stage/action/recipient/channel | Sysadmin / Workflow Admin | หน้าจอจริง; **มีแค่ channel `app` เท่านั้นที่ถูก dispatch จริง** — `email` ตั้งค่าได้แต่ถูกเพิกเฉยเงียบ ๆ, `sms`/`line` ไม่มีผู้บริโภคเลย |
| [activity-log](/th/inventory/system-config/activity-log) | UI แบบ list/grid เหนือ audit log ของ tenant (`tb_activity`) พร้อม filter action/entity-type/actor, export, print | Sysadmin / Auditor | หน้าจอจริง; เป็น activity UI *เดียว* ในผลิตภัณฑ์ — โมเดลข้อมูลอยู่ที่ [reporting-audit/activity](/th/inventory/reporting-audit/activity) |
| [application-config](/th/inventory/system-config/application-config) | การตั้งค่า key-value ระดับ tenant + การ override preference ต่อผู้ใช้ | ไม่มีหน้าจอ admin ทั่วไป | ตารางจริง consume เป็นราย key โดยฟีเจอร์ config-email/signature เท่านั้น |
| [query-dataset](/th/inventory/system-config/query-dataset) | SQL Workbench — เขียน tenant view, stored procedure และ function เป็นแหล่งข้อมูลใช้ซ้ำ | ไม่พบหน้าจอ admin | Backend service จริง; **ไม่มี frontend route เลย** |
| [dimension](/th/inventory/system-config/dimension) | Custom field ที่ผู้ใช้นิยามได้ พร้อม matrix การแสดงผลต่อสถานที่ | ไม่มีใคร — ไม่มี CRUD path | Schema เท่านั้น; ไม่พบ service, controller หรือ route |
| [menu](/th/inventory/system-config/menu) | Registry ของการนำทางที่แสดงผลโดย app shell | ไม่มีใคร — ตารางไม่ได้ใช้ | Schema เท่านั้น; ไม่มีการอ้างอิงจากโค้ด non-schema เลย; navigation คือค่าคงที่ใน frontend |
| [doc-version](/th/inventory/system-config/doc-version) | ตัวกัน concurrency ด้วย `doc_version` — client ต้องส่ง version ปัจจุบันตอนบันทึก ไม่งั้นได้ 409 | Engineering | กลไกข้ามโมดูล ไม่ใช่หน้าจอ |

## 4. การพึ่งพาข้ามโมดูล

**การผูก workflow แคบกว่าที่เวอร์ชันก่อนหน้าของรายการนี้เคยระบุไว้** `enum_workflow_type` มีค่าเพียงสามค่า — `purchase_request`, `store_requisition`, `purchase_order` — ยืนยันกับ Prisma schema แล้ว GRN, inventory-adjustment, physical-count, spot-check และ vendor-pricelist **ไม่มี enum member `workflow_type`** และไม่สามารถผูก row `tb_workflow` ได้ ภาษา "การอนุมัติแบบไม่บังคับ" สำหรับโมดูลเหล่านั้นด้านล่างถูกแก้ไขแล้ว เช่นเดียวกัน claim การติด tag ของ [system-config/dimension](/th/inventory/system-config/dimension) ถูกแก้ไขทั่วทั้งโมดูล — คอลัมน์ `dimension` JSONB มีอยู่บนตารางเหล่านี้แต่ไม่พบโค้ดใดอ่านหรือเขียนมันเลย (ดู Implementation status ของหน้านั้น)

- [purchase-request](/th/inventory/purchase-request) ต้องการ [system-config/workflow](/th/inventory/system-config/workflow) (เส้นทางอนุมัติ PR — จริง, `workflow_type = purchase_request`), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ PR) คอลัมน์ `dimension` มีอยู่ ไม่ได้ใช้
- [purchase-order](/th/inventory/purchase-order) ต้องการ [system-config/workflow](/th/inventory/system-config/workflow) (เส้นทางอนุมัติ PO — จริง, `workflow_type = purchase_order` แม้ `tb_purchase_order.workflow_id` จะเป็นฟิลด์ UUID อิสระ ไม่ใช่ relation ของ Prisma ที่ประกาศไว้), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ PO) คอลัมน์ `dimension` มีอยู่ ไม่ได้ใช้
- [good-receive-note](/th/inventory/good-receive-note) ต้องการ [system-config/period](/th/inventory/system-config/period) (การ์ดวันที่ posting), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ GRN) **ไม่มีการผูก workflow** — `goods_received_note` ไม่ใช่ member ของ `enum_workflow_type`
- [store-requisition](/th/inventory/store-requisition) ต้องการ [system-config/workflow](/th/inventory/system-config/workflow) (เส้นทางอนุมัติ SR — จริง, `workflow_type = store_requisition`), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ SR)
- [inventory-adjustment](/th/inventory/inventory-adjustment) ต้องการ [system-config/period](/th/inventory/system-config/period) (การ์ดวันที่ posting), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ IA / SI / SO) **ไม่มีการผูก workflow**
- [inventory](/th/inventory/inventory) ต้องการ [system-config/period](/th/inventory/system-config/period) (ขอบเขตของงวดบนทุกการเคลื่อนไหว) คอลัมน์ `dimension` มีอยู่ ไม่ได้ใช้
- [costing](/th/inventory/costing) ต้องการ [system-config/period](/th/inventory/system-config/period) (เครื่องยนต์ปิด cost เขียน `tb_period_snapshot`)
- [physical-count](/th/inventory/physical-count) ต้องการ [system-config/period](/th/inventory/system-config/period) (เอกสารนับถูกแช่แข็งกับงวด), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่เอกสารนับ) **ไม่มีการผูก workflow**
- [spot-check](/th/inventory/spot-check) ต้องการ [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่เอกสาร) **ไม่มีการผูก workflow**
- [vendor-pricelist](/th/inventory/vendor-pricelist) ต้องการ [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่อ้างอิง pricelist) **ไม่มีการผูก workflow**
- [system-config/application-config](/th/inventory/system-config/application-config) คือตารางจริง แต่ถูก consume เป็นราย key โดยฟีเจอร์เฉพาะ (SMTP config, การตั้งค่า signature) — ไม่ใช่เลเยอร์ feature-flag ทั่วไปที่ทุกโมดูลอ่าน [system-config/menu](/th/inventory/system-config/menu) ไม่มีผู้บริโภคที่ยืนยันได้เลย; navigation คือค่าคงที่ใน frontend แทน

## 5. แหล่งข้อมูลอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` (ประเภทของ role ในเวิร์กโฟลว์และ matrix ของสิทธิ์ที่บริโภคโดย [system-config/workflow](/th/inventory/system-config/workflow))
- **Seed data:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/` — `tb_workflow.json`, `tb_config_running_code.json`, `tb_application_config.json`
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
