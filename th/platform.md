---
title: Carmen Platform
description: ภาพรวมของผลิตภัณฑ์ Carmen Platform admin — จุดเริ่มต้นของ book นี้ จัดเรียงตามแถว Dashboard ที่ไม่อยู่ในกลุ่มใด บวกเจ็ดกลุ่ม `groupKey` ของ sidebar ใน SPA เอง (รวมเป็นแปดส่วน) บวก persona cluster-admin แยกต่างหาก
published: true
date: 2026-09-06T23:30:00.000Z
tags: book/platform, home
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Carmen Platform

คู่มืออ้างอิงสำหรับนักพัฒนาและ QA engineer ที่ทำงานกับ Carmen Platform admin — tenancy (cluster และ business unit), การจัดการไลเซนส์, identity และการเข้าถึง, การส่งมอบเนื้อหา, การวิเคราะห์, การจัดตารางเวลา, การตั้งค่าระดับแพลตฟอร์ม และฐานข้อมูลที่ใช้ร่วมกัน

รายการโมดูลด้านล่างเรียงจากบนลงล่างตามลำดับเดียวกับ sidebar ที่ผู้อ่านเพิ่งมาจาก: แถว Dashboard ที่ไม่อยู่ในกลุ่มใดก่อน ตามด้วยเจ็ดกลุ่ม `groupKey` ที่ตัว SPA ใช้สร้าง navigation ของตัวเอง (`../carmen-platform/src/components/nav/platformNav.ts`) — รวมเป็นแปดส่วน — ตามด้วยส่วนสุดท้ายสำหรับคอนโซล cluster-admin — persona แยกต่างหากที่มี nav file เป็นของตัวเอง ไม่ใช่กลุ่มเมนูที่เก้า

## 1. Dashboard

แถวบนสุดของ sidebar เอง — ไม่อยู่ในกลุ่มใด อยู่เหนือทุกกลุ่ม `groupKey` และเข้าถึงได้โดย session ที่ authenticated ทุก session ไม่ว่าจะมีสิทธิ์อะไร

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Dashboard](/th/platform/dashboard) | home hub สำหรับผู้ใช้ที่ signed-in — activity stream รวมทั่ว 6 โดเมน บวกแถบสรุปจำนวน active/total ต่อโดเมนแบบ sticky |

## 2. Organization

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Clusters](/th/platform/clusters) | กลุ่ม tenant ระดับบนสุดที่เป็นเจ้าของ business unit และผู้ใช้ตามไลเซนส์ อ้างอิงจาก license ledger แบบมีวันหมดอายุ |
| [Business Units](/th/platform/business-units) | เอนทิตีต่อสาขา/โรงแรม — ฟอร์มหกแท็บครอบคลุมข้อมูลระบุตัวตน รูปแบบ การผูก database pool และผู้ใช้/license ที่ผูกกับ BU |
| [Tenant Migrations](/th/platform/tenant-migrations) | หน้าจอระดับ fleet ที่ตรวจสอบและ apply schema migration ของฐานข้อมูล tenant ที่ค้างอยู่ทั่วทุก business unit |
| [Tenant Imports](/th/platform/tenant-imports) | wizard ที่นำเข้าข้อมูลหลักจาก `Preconfig.xlsx` เข้าฐานข้อมูล tenant ของหนึ่ง business unit ทีละขั้นตอน |
| [Users](/th/platform/users) | บัญชีผู้ใช้ระดับแพลตฟอร์ม — identity, avatar และการ assign cluster/BU |

## 3. License Management

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Licenses](/th/platform/licenses) | License centre — บัญชีโควตา BU ต่อ cluster, บัญชีที่นั่งต่อ BU และสัญญา subscription ที่พก feature-group entitlement |
| [License Catalog](/th/platform/license-catalog) | แคตตาล็อก feature ที่ขายได้ (Features) และชุดที่จัดไว้ล่วงหน้าที่ขายจากมัน (Bundles) — หน้าจอเดียว สองแท็บ |

## 4. Content

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Report Templates](/th/platform/report-templates) | แคตตาล็อกเทมเพลตรายงานแบบ XML — editor แบบแท็บ, การผูก data source กับฐานข้อมูล, การกำหนดขอบเขต BU แบบ allow/deny, default form ต่อ report group |
| [Report Form Groups](/th/platform/report-form-groups) | การ์ดหนึ่งใบต่อ `report_group` code ที่ตายตัว แต่ละใบแสดง form template พร้อม action ตั้งเป็น default — surface ที่เข้ามาแทนที่โมดูล print-template-mapping ที่ถูกลบไป |
| [News](/th/platform/news) | ประกาศแบบ markdown พร้อม lifecycle draft → published → archived กำหนดเป้าหมายแบบ global หรือราย BU |
| [Broadcasts](/th/platform/broadcasts) | push notification สาม target mode พร้อมการกำหนดเวลา แก้ไข และวงจรชีวิตฝั่งผู้ส่งแบบเต็ม |

## 5. Analytics

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Usage Analytics](/th/platform/usage-analytics) | แดชบอร์ด UI telemetry — StatCard, กราฟรายวัน และ Top List จากอีเวนต์กิจกรรมที่บันทึกไว้ |
| [Activity Events](/th/platform/activity-events) | explorer ของ UI telemetry แบบรายอีเวนต์ — ทุกตัวกรองและคอลัมน์เบื้องหลังอีเวนต์ที่ Usage Analytics สรุปไว้ |

## 6. Scheduling

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Cronjobs](/th/platform/cronjobs) | คอนโซลจัดตารางเวลาของแพลตฟอร์มบนตาราง Cronjob ที่ใช้ร่วมกัน — ประเภทงาน ใครเป็นคนรัน และจุดที่จะเห็นว่า run ไหนล้มเหลว |

## 7. Platform

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Platform Config](/th/platform/platform-config) | หน้าจอเดียว เก้าการ์ด — คำเชิญ การสมัคร ตั้งรหัสผ่านใหม่ การบังคับใช้ license เกณฑ์เตือนใกล้หมดอายุ และอื่น ๆ |
| [Email Settings](/th/platform/email-settings) | โปรไฟล์ผู้ส่ง SMTP ที่ตั้งชื่อได้ และแผนที่เส้นทางที่ตัดสินว่าอีเมลขาออกทั้งห้าเส้นทางใช้โปรไฟล์ไหน |
| [Applications](/th/platform/applications) | API client ที่ลงทะเบียน — identity แบบ `x-app-id` และการมอบสิทธิ์เข้าถึงแบบ allow-all เทียบกับ `api_name` ที่ระบุชัด |
| [Platform RBAC](/th/platform/rbac) | permission catalog, role, การ assign ผู้ใช้แบบมี scope และ super-admin bypass |
| [User Platform](/th/platform/user-platform) | มอบ role แบบ RBAC — ทั้งแพลตฟอร์มหรือเฉพาะ cluster — ให้บัญชีผู้ใช้ที่มีอยู่แล้ว |
| [Super Admins](/th/platform/super-admins) | บัญชีดำ god-mode ของแพลตฟอร์ม — ทะเบียน add/remove ของผู้ใช้ที่ bypass ทุกการตรวจสอบ permission |
| [Feature Flags](/th/platform/feature-flags) | หน้าเดียวที่ตั้งค่าการมองเห็นของทุกฟีเจอร์ (active/inactive/hide) ทั้งฝั่ง Platform admin และ Cluster-admin |

## 8. Database

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Platform Migrations](/th/platform/platform-migrations) | คอนโซลสำหรับ super-admin รัน Prisma migration ต่อฐานข้อมูลแพลตฟอร์มที่ใช้ร่วมกัน พร้อม seed และ drift check |
| [SQL Workbench](/th/platform/sql-workbench) | รัน SQL ใด ๆ ก็ได้ และ browse/สร้าง/drop view, procedure, function กับฐานข้อมูลของ tenant ที่เลือก |
| [Database Pools](/th/platform/database-pools) | ทะเบียน CRUD ของ Postgres connection pool ที่แชร์กันระดับแพลตฟอร์ม — แหล่งเดียวของ credential ฐานข้อมูล tenant |

## 9. คอนโซล Cluster Admin

เข้าถึงที่ `/cluster-admin/:clusterId/*` และสร้างจาก nav file เป็นของตัวเอง `clusterAdminNav.ts` — ไม่ใช่หนึ่งในแปดกลุ่มด้านบน นี่คือ persona ที่สอง ไม่ใช่กลุ่มเมนูเพิ่มเติม: cluster admin แบบ membership-only (ไม่มี permission ระดับแพลตฟอร์มเลย) จะถูกส่งมาที่นี่แทนที่จะเข้ากลุ่มด้านบน และทุก route ในนี้พก id ของคลัสเตอร์ปัจจุบันไปด้วย จึง sidebar ของมันเองไม่สามารถนำทางออกนอกคลัสเตอร์นั้นได้

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Cluster Admin](/th/platform/cluster-admin) | nav และ persona ที่สอง จำกัดอยู่ที่คลัสเตอร์เดียวต่อครั้ง — ไม่มี RBAC permission key ใดในโมดูลนี้เลย กั้นด้วยสมาชิกภาพของคลัสเตอร์แทน |

## 10. Account และ Product Chrome

หน้าที่อยู่นอก sidebar ทั้งหมด — เข้าถึงจาก flow การล็อกอิน เมนู avatar หรือ version badge ไม่ใช่จาก nav ด้านบนทั้งสองชุด

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Profile](/th/platform/profile) | หน้าจัดการตนเองสำหรับผู้ใช้ที่ล็อกอินอยู่ ดูและแก้ไขข้อมูลตัวตนของตน รวมถึงเปลี่ยนรหัสผ่าน |
| [Landing](/th/platform/landing) | หน้าการตลาดสาธารณะที่ `/` — redirect session ที่ authenticated ไปยัง Dashboard ทันที |
| [Changelog](/th/platform/changelog) | บันทึกการเปลี่ยนแปลงของแพลตฟอร์มแบบมีเวอร์ชัน (สาธารณะ) พร้อม version badge |

## 11. การใช้งาน book นี้

- เริ่มจากหน้า landing ของแต่ละโมดูลเพื่อภาพรวม
- เจาะลึก sub-pages ของมันสำหรับ data model, UI flow, edge cases
- ดู [global wiki landing](/th/home) สำหรับ Inventory book
