---
title: Business Unit — UI Screens
description: BusinessUnitManagement (list) และ BusinessUnitEdit หกแท็บ (General/Location/Formats/Technical/Users/Licenses) — code สร้างอัตโนมัติ ปุ่มสุ่มชื่อ schema และแท็บ Licenses ใหม่
published: true
date: 2026-09-05T07:45:00.000Z
tags: book/platform, business-units, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — UI Screens

## 1. At a Glance

- หน้ารายการ: แถบสรุป **Overview** (`BuSummary`, ตอนนี้อ่านจาก endpoint สรุปเฉพาะ `GET /api-system/business-units/summary`), `BrandMark` avatar เล็ก ๆ ข้างชื่อ BU ในคอลัมน์ Name (กลับมาใหม่), คอลัมน์ audit Created/Updated และ row action **สามรายการ** — Edit / View History (`activity_log.read`, ใหม่) / Delete — ทั้งหมด gate ด้วย `<Can>` แบบ cluster-scoped — ไม่มี client-side deletion guard คอลัมน์ CSV ตัด "Max Licensed Users" ออกแล้ว (ฟิลด์เดิมถูกถอดออกจาก schema)
- Route guard reuse key `cluster.read` / `cluster.create` / `cluster.update` **บวก feature flag `business_units`** — ไม่มี key `business_unit.*` (ดู [business-units](/th/platform/business-units) §4)
- หน้าแก้ไข **เขียนใหม่เป็นครั้งที่สอง** นับตั้งแต่ sync ก่อนหน้า — จากหน้าเอกสารเดียวแบบ scroll ต่อเนื่อง ให้กลายเป็น **เอกสารหกแท็บ**: General (Details รวม Code แบบอ่านอย่างเดียว + Max users แบบอ่านอย่างเดียว, Calculation Settings, Branding) → Location (Hotel/Company/Tax) → Formats (Date & time, Number Formats) → Technical (Configuration, Database Connection ใหม่ทั้งหมด, การ์ด advanced สามใบ) → Users (เฉพาะ BU ที่มีอยู่แล้ว) → Licenses (เฉพาะ BU ที่มีอยู่แล้ว, **แท็บใหม่**) — ยังไม่มี toggle read/edit; boolean `canEdit` ตัวเดียว gate ทุกอย่าง
- **`code` ไม่ให้ผู้ใช้กรอกอีกต่อไป** — backend สุ่มให้ตอนสร้าง ฟอร์มสร้างไม่มีช่อง code เลย หน้าแก้ไขแสดงแบบอ่านอย่างเดียว
- **Database Connection ถูกสร้างใหม่ทั้งหมด** — ไม่มี field host/port/database/user/password/ssl อีกต่อไป (และไม่มีปุ่ม Reveal password ด้วย) แทนที่ด้วย dropdown เลือก Database Pool (gate ด้วย `database_pool.read`) + ช่อง Schema พร้อม**ปุ่ม "Generate schema" สุ่มชื่อ** (`bu_` + ตัวอักษร/ตัวเลขสุ่ม 16 ตัว) เปลี่ยนค่า pool/schema จากค่าที่เคย save ไว้ต้องผ่าน confirm dialog ก่อน
- **แท็บ Licenses ใหม่** แยกออกจาก Users — การ์ดอ่านอย่างเดียวพร้อมปุ่ม Manage licences และปุ่ม **New subscription** (gate ด้วย `subscription.manage`, ใหม่)
- Max users บนแท็บ General ไม่ใช่ integer ที่พิมพ์ได้อีกต่อไป — เป็นผลรวมที่นั่ง active จาก `tb_business_unit_license` แบบอ่านอย่างเดียว

## 2. References

- ../carmen-platform/src/pages/BusinessUnitManagement.tsx, businessUnitManagement/BuSummary.tsx
- ../carmen-platform/src/pages/BusinessUnitEdit.tsx, businessUnitEdit/{BusinessUnitDocument,BusinessUnitTabs,HeroName,BusinessUnitLicensesCard,types}.ts(x), sections/{CalculationSettingsSection,DatabaseConnectionSection,ConfigurationSection,NumberFormatsSection}.tsx
- ../carmen-platform/src/utils/{databasePool,buLicense}.ts — ตัวสุ่มชื่อ schema, การคำนวณ ledger ที่นั่ง
- ../carmen-platform/src/components/{TenantMigrationCard,TenantSeedCard,InterfaceEntitlementCard,BrandingImageUpload}.tsx

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/business-units/ui-screens (เลย์เอาต์เปลี่ยนเป็นหกแท็บแล้ว — เอกสารเดียวที่เคยบันทึกไว้เป็นประวัติศาสตร์ไปแล้ว)
- [ ] Screenshot แต่ละแท็บ (เลย์เอาต์ใหม่ทั้งหมด — capture เดิมถ้ามีจะ stale)
