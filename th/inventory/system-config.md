---
title: ระบบและการตั้งค่า (System Configuration)
description: การตั้งค่าระบบสำหรับการไหลของเอกสารและช่วงงวดบัญชี — เวิร์กโฟลว์ ช่วงงวด มิติ การกำหนดเลขที่เอกสาร
published: true
date: 2026-06-09T00:00:00.000Z
tags: system-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ระบบและการตั้งค่า (System Configuration)

> **At a Glance**
> **วัตถุประสงค์โมดูล:** กลไกสำหรับการไหลของเอกสารและช่วงงวดบัญชี — เวิร์กโฟลว์การอนุมัติ ช่วงงวดบัญชี มิติ การกำหนดเลขที่เอกสาร การตั้งค่าแอป เมนู &nbsp;·&nbsp; **กลุ่มเป้าหมาย:** Sysadmin, Workflow Administrator, Finance (ปิดงวด) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_workflow`, `tb_period`, `tb_dimension`, `tb_config_running_code`, `tb_application_config`, `tb_menu` &nbsp;·&nbsp; **หน้าย่อย:** 10

![ระบบและการตั้งค่า (System Configuration) screen](/screenshots/system-config/index.png)

## 1. ภาพรวม

ระบบและการตั้งค่าเป็นโมดูลร่มของ **กลไกการไหลของเอกสารและช่วงงวดบัญชี** ที่ทุกโมดูลธุรกรรมต้องพึ่งพา เวิร์กโฟลว์กำหนดเส้นทางการอนุมัติแบบหลายขั้น พร้อมการกระทำ ผู้รับ และการแสดงผลของฟิลด์ในแต่ละขั้น ช่วงงวดกำหนดปฏิทินบัญชีและควบคุมว่าวันที่ใดของการ post จะถูกอนุญาต มิติคือระบบ custom field ที่ผู้ใช้ขยายได้และแทรกอยู่ในทุกตารางธุรกรรม Running code ขับเคลื่อนการกำหนดเลขที่เอกสาร Application config คือทางออกแบบ key-value ทั่วไป Menu registry ป้อนข้อมูลให้กับ app shell

ทั้งหกเอนทิตีในที่นี้อยู่ระหว่าง [master-data](/th/inventory/master-data) (แคตตาล็อกแบบสถิตย์ — หน่วยนับ ผู้ขาย สกุลเงิน) และเลเยอร์ runtime [access-control](/th/inventory/access-control) (ผู้ใช้ บทบาท สิทธิ์) ในขณะที่ master data ตอบคำถามว่าธุรกรรมกำลังอ้างอิง *อะไร* การตั้งค่าระบบตอบคำถามว่าควรไหล *อย่างไร* ควร post *เมื่อไหร่* และควรพ่วง *มิติพิเศษอะไร* รายการส่วนใหญ่เป็นเจ้าของและแก้ไขโดย Sysadmin; บางส่วน — โดยเฉพาะอย่างยิ่งขั้นเวิร์กโฟลว์และแคตตาล็อกมิติ — มีการปรับแต่งรายวันโดย Workflow Administrator ที่ได้รับมอบหมาย

ทั้งหกเอนทิตีอยู่ใน **tenant** schema ไม่มีเอนทิตีใดที่มี counterpart ในระดับแพลตฟอร์ม — เพราะอธิบายการไหลของเอกสารต่อ property ดังนั้นแต่ละ tenant ได้สำเนาของตัวเอง

## 2. กลุ่มเป้าหมาย

Sysadmin การนิยามเวิร์กโฟลว์อาจมอบหมายให้ persona Workflow Administrator (โดยทั่วไปคือ Finance Manager หรือ Procurement Manager) เพื่อบำรุงรักษาขั้น / ผู้อนุมัติรายวัน Finance เป็นเจ้าของการปิดงวด

## 3. รายการเอนทิตี

| เอนทิตี | วัตถุประสงค์ | จัดการโดย |
| ------ | ------- | ---------- |
| [workflow](/th/inventory/system-config/workflow) | เวิร์กโฟลว์การอนุมัติแบบหลายขั้น พร้อมการกระทำ ผู้รับ และการแสดงผลของฟิลด์ในแต่ละขั้น | Sysadmin / Workflow Admin |
| [period](/th/inventory/system-config/period) | ช่วงงวดบัญชี (open/closed/locked) และ snapshot สต๊อกต่องวด | Sysadmin / Finance |
| [dimension](/th/inventory/system-config/dimension) | Custom field ที่ผู้ใช้นิยามได้ พร้อม matrix การแสดงผลต่อสถานที่ | Sysadmin |
| [running-code](/th/inventory/system-config/running-code) | รูปแบบเลขที่เอกสารต่อประเภทเอกสาร | Sysadmin |
| [application-config](/th/inventory/system-config/application-config) | การตั้งค่า key-value ระดับ tenant + การ override preference ต่อผู้ใช้ | Sysadmin |
| [menu](/th/inventory/system-config/menu) | Registry ของการนำทางที่แสดงผลโดย app shell | Sysadmin |
| [query-dataset](/th/inventory/system-config/query-dataset) | SQL Workbench — เขียน tenant view, stored procedure และ function เป็นแหล่งข้อมูลใช้ซ้ำ | Sysadmin |
| [dashboard-dataset](/th/inventory/system-config/dashboard-dataset) | แคตตาล็อก read-only ของ data feed ที่ลงทะเบียนไว้ในโค้ดสำหรับ widget บนแดชบอร์ด | Sysadmin |
| [config-email](/th/inventory/system-config/config-email) | SMTP profile ต่อ BU สำหรับอีเมลขาออกของระบบ — การแจ้งเตือนเวิร์กโฟลว์ รายงานตามตารางเวลา รีเซ็ตรหัสผ่าน | Sysadmin |
| [document](/th/inventory/system-config/document) | Registry การจัดเก็บไฟล์ scope ตาม tenant — upload, list, download และ delete สำหรับเอกสารที่แนบกับ record ธุรกรรม | Sysadmin |
| [doc-version](/th/inventory/system-config/doc-version) | ตัวกัน concurrency ด้วย `doc_version` — client ต้องส่ง version ปัจจุบันตอนบันทึก ไม่งั้นได้ 409 | Engineering |

## 4. การพึ่งพาข้ามโมดูล

- [purchase-request](/th/inventory/purchase-request) ต้องการ [system-config/workflow](/th/inventory/system-config/workflow) (เส้นทางอนุมัติ PR), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ PR), [system-config/dimension](/th/inventory/system-config/dimension) (การติด tag header/detail ของ PR)
- [purchase-order](/th/inventory/purchase-order) ต้องการ [system-config/workflow](/th/inventory/system-config/workflow) (เส้นทางอนุมัติ PO เมื่อนโยบายกำหนด), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ PO), [system-config/dimension](/th/inventory/system-config/dimension) (การติด tag header/detail ของ PO)
- [good-receive-note](/th/inventory/good-receive-note) ต้องการ [system-config/period](/th/inventory/system-config/period) (การ์ดวันที่ posting), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ GRN), [system-config/dimension](/th/inventory/system-config/dimension) (การติด tag header/detail ของ GRN), [system-config/workflow](/th/inventory/system-config/workflow) (การอนุมัติแบบไม่บังคับ)
- [store-requisition](/th/inventory/store-requisition) ต้องการ [system-config/workflow](/th/inventory/system-config/workflow) (เส้นทางอนุมัติ SR — เวิร์กโฟลว์หลายขั้นแบบมาตรฐาน), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ SR), [system-config/dimension](/th/inventory/system-config/dimension) (การติด tag การออก — โครงการ / event)
- [inventory-adjustment](/th/inventory/inventory-adjustment) ต้องการ [system-config/period](/th/inventory/system-config/period) (การ์ดวันที่ posting), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่ IA / SI / SO), [system-config/dimension](/th/inventory/system-config/dimension) (การติด tag stock-in / stock-out), [system-config/workflow](/th/inventory/system-config/workflow) (การอนุมัติแบบไม่บังคับ)
- [inventory](/th/inventory/inventory) ต้องการ [system-config/period](/th/inventory/system-config/period) (ขอบเขตของงวดบนทุกการเคลื่อนไหว) และ [system-config/dimension](/th/inventory/system-config/dimension) (การจัดสรร cost-centre บน transfer)
- [costing](/th/inventory/costing) ต้องการ [system-config/period](/th/inventory/system-config/period) (เครื่องยนต์ปิด cost เขียน `tb_period_snapshot`)
- [physical-count](/th/inventory/physical-count) ต้องการ [system-config/period](/th/inventory/system-config/period) (เอกสารนับถูกแช่แข็งกับงวด), [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่เอกสารนับ), [system-config/workflow](/th/inventory/system-config/workflow) (การอนุมัติ variance)
- [spot-check](/th/inventory/spot-check) ต้องการ [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่เอกสาร), [system-config/workflow](/th/inventory/system-config/workflow) (การอนุมัติ variance)
- [vendor-pricelist](/th/inventory/vendor-pricelist) ต้องการ [system-config/running-code](/th/inventory/system-config/running-code) (เลขที่อ้างอิง pricelist), [system-config/workflow](/th/inventory/system-config/workflow) (การอนุมัติการเผยแพร่แบบไม่บังคับ), [system-config/dimension](/th/inventory/system-config/dimension) (การติด tag pricelist)
- [system-config/application-config](/th/inventory/system-config/application-config) และ [system-config/menu](/th/inventory/system-config/menu) อ้างอิงโดยทุกโมดูล — application-config ปรับ feature toggle และค่า default ส่วน menu ควบคุมการมองเห็นของการนำทาง

## 5. แหล่งข้อมูลอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` (ประเภทของ role ในเวิร์กโฟลว์และ matrix ของสิทธิ์ที่บริโภคโดย [system-config/workflow](/th/inventory/system-config/workflow))
- **Seed data:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/` — `tb_workflow.json`, `tb_config_running_code.json`, `tb_application_config.json`
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
