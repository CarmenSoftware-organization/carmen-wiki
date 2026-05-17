---
title: รายงานและการตรวจสอบ (Reporting & Audit)
description: บันทึกกิจกรรม, ไฟล์แนบ, การแจ้งเตือน, การสร้างรายงาน และ dashboard widgets
published: true
date: 2026-05-17T12:00:00.000Z
tags: reporting-audit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# รายงานและการตรวจสอบ (Reporting & Audit)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ระบบโครงสร้างพื้นฐานที่ใช้ร่วมกันสำหรับ activity audit log, ไฟล์แนบแบบ polymorphic, การแจ้งเตือนใน inbox, pipeline ของ report job / template และ widget สำหรับ dashboard &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Auditor (อ่าน), Sysadmin (ตั้งค่า), Platform Admin (ข้าม tenant), ทุกโมดูล (เขียน) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_activity`, `tb_attachment`, `tb_notification`, `tb_report_template` + `tb_report_job`, `tb_widget_dashboard` &nbsp;·&nbsp; **หน้าย่อย:** 8

## 1. ภาพรวม

Reporting and Audit คือร่มของระบบที่ครอบ **เกิดอะไรขึ้น, อะไรถูกแนบ, ใครได้รับการแจ้งเตือน, อะไรถูกส่งออก และอะไรแสดงบน dashboard** ครอบคลุมด้วยห้าเอนทิตี [[reporting-audit/activity]] คือ audit log ของ tenant แบบ append-only — หนึ่งแถวต่อหนึ่งการเปลี่ยนสถานะที่มีความหมาย พร้อม actor, snapshot เก่า/ใหม่, IP และ user agent [[reporting-audit/attachment]] คือเอนทิตีจัดเก็บไฟล์แบบ generic ที่ทุกโมดูลธุรกรรมเชื่อมโยงไปสำหรับใบเสนอราคา, docket, รูปภาพ และเอกสารที่มีลายเซ็น [[reporting-audit/notification]] คือ fan-out ฝั่งแพลตฟอร์มสำหรับข้อความ inbox, message template ที่ใช้ซ้ำได้ และข่าวประกาศ broadcast [[reporting-audit/report]] คือ pipeline สี่ตาราง (tenant jobs + schedules, platform templates + print mappings) ที่ผลิต analytical export และ output ของ "Print" ทุกตัว [[reporting-audit/widget]] คือชั้นการประกอบ dashboard — dashboard ตาม scope, default layout และ workspace ที่บันทึกไว้

ร่มนี้ครอบคลุมทั้งสอง schema `tb_activity`, `tb_attachment`, `tb_report_job`, `tb_report_schedule`, `tb_widget_dashboard`, `tb_widget_default_layout` และ `tb_widget_workspace` อยู่ใน **tenant schema** เพราะแต่ละ tenant เป็นเจ้าของประวัติ audit, ไฟล์, การ execute, schedule และ dashboard ของตนเอง `tb_notification`, `tb_message_format`, `tb_news`, `tb_report_template` และ `tb_print_template_mapping` อยู่ใน **platform schema** เพราะการแจ้งเตือนข้ามขอบเขต BU และ tenant และ report template / print mapping ถูก curate ไว้แบบรวมศูนย์เป็น asset ของแพลตฟอร์ม

เอนทิตีทั้งห้านี้ออกแบบให้เป็น generic / polymorphic โดยตั้งใจ Activity เชื่อมไปยังแถวเป้าหมายผ่าน `(entity_type, entity_id)` แทน FK แบบมี type Attachment ไม่มี discriminator ประเภทเอกสาร — แถวเจ้าของเก็บลิงก์ไว้ Notification ยุบรวมประเภท event หลายแบบเข้าสู่ตาราง inbox เดียว Report template ผูกกับข้อมูลผ่าน `source_type` + `source_name` แทน view แบบมี type Widget item ฝัง config ของตนเป็น JSON ความเป็น generic ที่ตั้งใจนี้คือสิ่งที่ทำให้ทุกโมดูลธุรกรรมต่อเข้ามาที่ร่มได้โดยไม่ขยาย schema surface ตรงนี้

## 2. ผู้ใช้งาน

**Auditor** เป็นเจ้าของเส้นทางการอ่าน — query ประวัติ activity, ตรวจสอบ log การ dispatch notification, ดาวน์โหลด compliance report ที่ตั้งเวลาไว้ **Sysadmin** เป็นเจ้าของฝั่งการตั้งค่า — template, print mapping, schedule, message format, default layout ของ dashboard Platform Admin บริหาร surface ข้าม tenant (โพสต์ข่าว, แคตตาล็อก standard report template)

## 3. รายการเอนทิตี

| เอนทิตี | วัตถุประสงค์ | ดูแลโดย |
| ------ | ------- | ---------- |
| [activity](./activity.md) | Audit log แบบ append-only — บันทึกทุกการเปลี่ยนสถานะพร้อม actor, snapshot, IP, user agent | Auditor (อ่าน) / system (เขียน) |
| [attachment](./attachment.md) | ที่จัดเก็บไฟล์แบบ generic เชื่อมไปยังเอกสารเจ้าของผ่าน polymorphic application FK | ผู้ใช้ของโมดูลเจ้าของ |
| [notification](./notification.md) | inbox ต่อผู้ใช้ + message template ที่ใช้ซ้ำได้ + ข่าวประกาศของแพลตฟอร์ม | Sysadmin / Platform Admin |
| [report](./report.md) | tenant jobs และ schedules ที่อยู่เบื้องหลังของ platform template และ document-type print mapping | Sysadmin / Platform Admin |
| [widget](./widget.md) | Dashboard ส่วนตัว / BU, seed layout เริ่มต้น, workspace สำหรับ data-explorer ที่บันทึกไว้ | ผู้ใช้ / BU Admin / Sysadmin |

## 4. ความเชื่อมโยงข้ามโมดูล

- **ทุกโมดูลธุรกรรม** เขียนไปที่ [[reporting-audit/activity]] ผ่าน audit service ที่ใช้ร่วมกัน [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[costing]], [[vendor-pricelist]], [[product]] และ [[recipe]] ล้วนเป็นแหล่งที่มา
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[store-requisition]], [[vendor-pricelist]], [[recipe]] และ [[product]] ล้วนแนบไฟล์ผ่าน [[reporting-audit/attachment]] (ใบเสนอราคา, docket, รูป, ใบนับสินค้า, สัญญา, ใบทดสอบ yield, รูปสินค้า)
- **โมดูล workflow อนุมัติทั้งหมด** กระตุ้น [[reporting-audit/notification]] ทุกครั้งที่มีการเปลี่ยน stage ของ workflow ชุดผู้รับ resolve โดย runtime ของ [[system-config/workflow]] กับ membership ของ [[access-control/business-unit-user]] และ role type ของแต่ละ stage [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]] และ [[vendor-pricelist]] เป็นแหล่งที่มาทั้งหมด
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]] และ [[vendor-pricelist]] แต่ละโมดูลมีเส้นทาง "Print" ที่ resolve template ของ [[reporting-audit/report]] ผ่าน print mapping ตามประเภทเอกสาร [[inventory]], [[costing]], [[product]] และ [[recipe]] เป็นผู้บริโภคทั่วไปของ analytical report
- Tile ใน [[reporting-audit/widget]] สามารถฝัง template ของ [[reporting-audit/report]] ได้ แหล่งข้อมูลของ tile ครอบคลุมทุกโมดูลธุรกรรมข้างต้น
- [[master-data/business-unit]] กำหนด scope ของการเข้าถึง template / mapping ของ [[reporting-audit/report]] (รายการอนุญาต / ปฏิเสธ BU) และจำกัดการมองเห็น dashboard scope `bu` ของ widget
- [[access-control/user]] resolve `actor_id` / `requested_by_id` / `created_by_id` ในทุกเอนทิตีที่นี่ และตัดสินการมองเห็นสำหรับ dashboard ส่วนตัวและ notification ต่อผู้ใช้
- [[reporting-audit/notification]] บริโภค event ที่เขียนโดย [[reporting-audit/activity]] เพิ่มเติมสำหรับ message format บางตัวที่ขับโดย workflow

## 5. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity`, `tb_attachment`, `tb_report_job`, `tb_report_schedule`, `tb_widget_dashboard`, `tb_widget_default_layout`, `tb_widget_workspace` พร้อม enum `enum_activity_action`, `enum_report_format`, `enum_report_category`, `enum_report_job_status`, `enum_widget_dashboard_scope`, `enum_widget_accent`
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification`, `tb_message_format`, `tb_news`, `tb_report_template`, `tb_print_template_mapping`
- **carmen/docs (ถ้ามี):** `../carmen/docs/workflow-permissions-system.md` — อธิบายการเปลี่ยน stage ของ workflow ที่ขับ notification fan-out ส่วนใหญ่และการเขียน audit log ส่วนใหญ่
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
