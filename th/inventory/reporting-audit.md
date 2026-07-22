---
title: รายงานและการตรวจสอบ (Reporting & Audit)
description: บันทึกกิจกรรม, ไฟล์แนบเก็บบน MinIO, การแจ้งเตือน, การสร้างรายงาน และ dashboard widget
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# รายงานและการตรวจสอบ (Reporting & Audit)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ระบบโครงสร้างพื้นฐานที่ใช้ร่วมกันสำหรับ activity audit log, ไฟล์แนบเก็บบน MinIO, การแจ้งเตือนใน inbox/broadcast, การสร้างรายงาน และ dashboard widget &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Auditor (อ่าน), Sysadmin (ตั้งค่า), Platform Admin (ข้าม tenant), ทุกโมดูล (เขียน) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_activity`, `tb_file_tag` (ฐานข้อมูล file-service แยกต่างหาก — ไม่ใช่ `tb_attachment` ซึ่งตายแล้ว), `tb_notification` + `tb_broadcast_notification`, `tb_report_template` + `tb_report_job`, `tb_dashboard_bu_widget` + `tb_dashboard_personal_widget` &nbsp;·&nbsp; **หน้าย่อย:** 8

![รายงานและการตรวจสอบ (Reporting & Audit) screen](/screenshots/reporting-audit/activity.png)

## 1. ภาพรวม

Reporting and Audit คือร่มของระบบที่ครอบ **เกิดอะไรขึ้น, อะไรถูกแนบ, ใครได้รับการแจ้งเตือน, อะไรถูกส่งออก และอะไรแสดงบน dashboard** ครอบคลุมด้วยหกเอนทิตี (8 หน้าย่อยเพิ่มมุมมองอ่านอีกสองแบบ: [reporting-audit/history](/th/inventory/reporting-audit/history) เหนือตาราง job ของ `report` และ [reporting-audit/user-activity](/th/inventory/reporting-audit/user-activity) — มุมมองที่กรองมาจาก `activity` ไม่ใช่ตารางแยก) [reporting-audit/activity](/th/inventory/reporting-audit/activity) คือ audit log ของ tenant แบบ append-only — หนึ่งแถวต่อหนึ่งการเปลี่ยนสถานะที่มีความหมาย พร้อม actor, snapshot เก่า/ใหม่, IP และ user agent [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) คือ registry ไฟล์เก็บบน MinIO (`tb_file_tag`, อยู่ในฐานข้อมูล file-service แยกต่างหาก) ที่ทุกโมดูลธุรกรรมเชื่อมโยงไปสำหรับใบเสนอราคา, docket, รูปภาพ และเอกสารที่มีลายเซ็น — `tb_attachment` ของ tenant schema เป็นตารางที่ตายแล้วไม่มีการอ้างอิงจากโค้ดเลย [reporting-audit/notification](/th/inventory/reporting-audit/notification) คือ fan-out ฝั่งแพลตฟอร์มสำหรับข้อความ inbox ส่วนตัว, broadcast ของระบบ/BU, message template ที่ใช้ซ้ำได้ และโพสต์ข่าว [reporting-audit/report](/th/inventory/reporting-audit/report) ครอบคลุมการ render ผ่าน viewer แบบ on-demand, pipeline การ print และตาราง job/history ที่มีอยู่จริงแต่ปัจจุบันไม่มีข้อมูล (ดู implementation status callout ของหน้านั้น); **schedule** ของการเกิดซ้ำไม่ใช่ตาราง tenant เลย — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) สำหรับที่เก็บจริง (ตาราง cron-job แบบ generic ใน service micro-cronjobs แยกต่างหาก) [reporting-audit/widget](/th/inventory/reporting-audit/widget) คือชั้น tile ของ dashboard — widget แบบแชร์ BU และต่อผู้ใช้ที่ผูกกับแคตตาล็อก dataset ที่ลงทะเบียนในโค้ด; ไม่มีฟีเจอร์ saved-query/workspace อยู่ที่ไหนในระบบเลย

ตำแหน่งตารางจริงที่แก้ไขแล้ว: `tb_activity`, `tb_report_job`, `tb_dashboard_bu_widget` และ `tb_dashboard_personal_widget` อยู่ใน **tenant schema** `tb_notification`, `tb_broadcast_notification` + `tb_user_broadcast_action`, `tb_message_format`, `tb_news`, `tb_report_template` และ `tb_print_template_mapping` อยู่ใน **platform schema** Registry ไฟล์ (`tb_file_tag`) อยู่ใน **ฐานข้อมูล file-service แยกต่างหากเป็นที่สาม** Schedule ของรายงานอยู่ใน **ฐานข้อมูลแยกต่างหากเป็นที่สี่** ที่เป็นของ service micro-cronjobs — ไม่ได้อยู่ใน Prisma schema ใดเลย หลายตารางที่เคยบันทึกไว้ที่นี่ยืนยันแล้วว่าตายแล้ว (ไม่มีการอ้างอิงจากโค้ดนอกเหนือจาก schema): `tb_attachment` (tenant), `tb_report_schedule` (tenant), `tb_user_login_session` (platform) และตระกูล `tb_widget_dashboard`/`tb_widget_dashboard_item`/`tb_widget_default_layout`/`tb_widget_workspace` ทั้งหมด (ไม่เคยมีอยู่จริง หรือถูกลบโดย migration `20260521040013_remove_widget_system`)

เอนทิตีที่เหลืออยู่ออกแบบให้เป็น generic / polymorphic โดยตั้งใจ Activity เชื่อมไปยังแถวเป้าหมายผ่าน `(entity_type, entity_id)` แทน FK แบบมี type ไฟล์แนบไม่มี discriminator ประเภทเอกสาร — JSONB array ของแถวเจ้าของเก็บลิงก์ไว้ (`fileToken`) Notification ยุบรวมประเภท event หลายแบบเข้าสู่ตาราง inbox/broadcast Report template ผูกกับข้อมูลผ่าน `source_type` + `source_name` แทน view แบบมี type Widget item ฝัง config ของตนเป็น JSON และอ้างอิงรายการคงที่ในแคตตาล็อก dataset ไม่เคยเป็น query ที่ผู้ใช้เขียนเอง ความเป็น generic ที่ตั้งใจนี้คือสิ่งที่ทำให้ทุกโมดูลธุรกรรมต่อเข้ามาที่ร่มได้โดยไม่ขยาย schema surface ตรงนี้

## 2. ผู้ใช้งาน

**Auditor** เป็นเจ้าของเส้นทางการอ่าน — query ประวัติ activity, ตรวจสอบ log การ dispatch notification **Sysadmin** เป็นเจ้าของฝั่งการตั้งค่า — schedule, message format Platform Admin บริหาร surface ข้าม tenant (โพสต์ข่าว, แคตตาล็อก report template / print mapping — อยู่นอก UI ของ repo นี้ ดู [reporting-audit/report](/th/inventory/reporting-audit/report))

## 3. รายการเอนทิตี

| เอนทิตี | วัตถุประสงค์ | ดูแลโดย |
| ------ | ------- | ---------- |
| [activity](/th/inventory/reporting-audit/activity) | Audit log แบบ append-only — บันทึกทุกการเปลี่ยนสถานะพร้อม actor, snapshot, IP, user agent | Auditor (อ่าน) / system (เขียน) |
| [attachment](/th/inventory/reporting-audit/attachment) | Registry ไฟล์เก็บบน MinIO (`tb_file_tag`, ฐานข้อมูลแยกต่างหาก) เชื่อมไปยังเอกสารเจ้าของผ่าน JSONB array ของ `fileToken` | ผู้ใช้ของโมดูลเจ้าของ |
| [notification](/th/inventory/reporting-audit/notification) | inbox ส่วนตัว + broadcast ของระบบ/BU + message template ที่ใช้ซ้ำได้ + ข่าวประกาศของแพลตฟอร์ม | Sysadmin / Platform Admin |
| [report](/th/inventory/reporting-audit/report) | การ render ผ่าน viewer แบบ on-demand + pipeline print; ตาราง job/history มีอยู่จริงแต่ปัจจุบันไม่มีข้อมูล | Platform Admin (template, mapping) |
| [schedule](/th/inventory/reporting-audit/schedule) | การ fire รายงานแบบเกิดซ้ำ — อยู่เบื้องหลังด้วยตาราง cron-job แบบ generic ใน service micro-cronjobs แยกต่างหาก ไม่ใช่ตาราง tenant | ผู้ใช้ที่ authenticate แล้วคนใดก็ได้ (ไม่พบ gate schedule-admin ที่แยกออกมา) |
| [widget](/th/inventory/reporting-audit/widget) | Tile ของ dashboard ส่วนตัว / BU ที่ผูกกับแคตตาล็อก dataset ที่ลงทะเบียนในโค้ด — ไม่มี default layout, ไม่มี saved query | ผู้ใช้ / สมาชิก BU คนใดก็ได้ |

## 4. ความเชื่อมโยงข้ามโมดูล

- **ทุกโมดูลธุรกรรม** เขียนไปที่ [reporting-audit/activity](/th/inventory/reporting-audit/activity) ผ่าน audit service ที่ใช้ร่วมกัน [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory](/th/inventory/inventory), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [costing](/th/inventory/costing), [vendor-pricelist](/th/inventory/vendor-pricelist), [product](/th/inventory/product) และ [recipe](/th/inventory/recipe) ล้วนเป็นแหล่งที่มา
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [store-requisition](/th/inventory/store-requisition), [vendor-pricelist](/th/inventory/vendor-pricelist), [recipe](/th/inventory/recipe) และ [product](/th/inventory/product) ล้วนแนบไฟล์ผ่าน [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) (ใบเสนอราคา, docket, รูป, ใบนับสินค้า, สัญญา, ใบทดสอบ yield, รูปสินค้า)
- **โมดูล workflow อนุมัติทั้งหมด** กระตุ้น [reporting-audit/notification](/th/inventory/reporting-audit/notification) ทุกครั้งที่มีการเปลี่ยน stage ของ workflow ชุดผู้รับ resolve โดย runtime ของ [system-config/workflow](/th/inventory/system-config/workflow) กับ membership ของ [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) และ role type ของแต่ละ stage [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) และ [vendor-pricelist](/th/inventory/vendor-pricelist) เป็นแหล่งที่มาทั้งหมด
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) และ [vendor-pricelist](/th/inventory/vendor-pricelist) แต่ละโมดูลมีเส้นทาง "Print" ที่ resolve ผ่าน print mapping ตามประเภทเอกสารของ [reporting-audit/report](/th/inventory/reporting-audit/report) [inventory](/th/inventory/inventory), [costing](/th/inventory/costing), [product](/th/inventory/product) และ [recipe](/th/inventory/recipe) เป็นผู้บริโภคทั่วไปของ analytical report
- Tile ของ [reporting-audit/widget](/th/inventory/reporting-audit/widget) ดึงจากแคตตาล็อก [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) ที่ลงทะเบียนในโค้ด — ไม่ใช่จาก template ของ [reporting-audit/report](/th/inventory/reporting-audit/report) ซึ่งเป็นคนละ mechanism เนื้อหา dataset ครอบคลุมทุกโมดูลธุรกรรมข้างต้น
- [master-data/business-unit](/th/inventory/master-data/business-unit) กำหนด scope ของการเข้าถึง template / mapping ของ [reporting-audit/report](/th/inventory/reporting-audit/report) (รายการอนุญาต / ปฏิเสธ BU) และจำกัดการมองเห็น dashboard widget ที่ scope ตาม BU (tenant schema เองคือขอบเขตของ BU)
- [access-control/user](/th/inventory/access-control/user) resolve `actor_id` / `requested_by_id` / `created_by_id` / `user_id` ในทุกเอนทิตีที่นี่ และตัดสินการมองเห็นสำหรับ dashboard ส่วนตัวและ notification ต่อผู้ใช้
- การ fire ของ [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) ส่งมอบผ่าน [reporting-audit/notification](/th/inventory/reporting-audit/notification) (ส่วนตัว, หนึ่งแถวต่อผู้รับ) — ไม่ผ่านตาราง job ของ [reporting-audit/report](/th/inventory/reporting-audit/report) ซึ่งเส้นทางการ fire ไม่เคยเขียนเข้าไปเลย

## 5. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity`, `tb_report_job`, `tb_dashboard_bu_widget`, `tb_dashboard_personal_widget` พร้อม enum `enum_activity_action`, `enum_report_format`, `enum_report_category`, `enum_report_job_status`, `enum_dashboard_widget_type` (`tb_attachment` และ `tb_report_schedule` ก็ประกาศไว้ในนี้เช่นกัน แต่ยืนยันแล้วว่าตายแล้ว — ไม่มีการอ้างอิงจากโค้ดเลย)
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification`, `tb_broadcast_notification`, `tb_user_broadcast_action`, `tb_message_format`, `tb_news` (+ `enum_news_status`), `tb_report_template`, `tb_print_template_mapping` (`tb_user_login_session` ก็ประกาศไว้ในนี้เช่นกัน แต่ยืนยันแล้วว่าตายแล้ว)
- **Prisma file schema (ฐานข้อมูลแยกต่างหาก):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-file/prisma/schema.prisma` — `tb_file_tag`, registry ไฟล์จริงเบื้องหลัง [reporting-audit/attachment](/th/inventory/reporting-audit/attachment)
- **micro-cronjobs (ฐานข้อมูลแยกต่างหาก อยู่นอก Prisma schema ทั้งสอง):** `../micro-cronjobs/internal/model/cronjob.go` — ที่เก็บจริงเบื้องหลัง [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)
- **carmen/docs (ถ้ามี):** `../carmen/docs/workflow-permissions-system.md` — อธิบายการเปลี่ยน stage ของ workflow ที่ขับ notification fan-out ส่วนใหญ่และการเขียน audit log ส่วนใหญ่
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
