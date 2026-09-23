---
title: Business Unit — UI Screens
description: BusinessUnitManagement (list) และ BusinessUnitEdit หกแท็บ — code สร้างอัตโนมัติ, ปุ่มสุ่มชื่อ schema, แท็บ Licenses สองการ์ด (ที่นั่ง+subscription, interface licence), การ์ด advanced สองใบหลังถอด Interface Entitlement
published: true
date: 2026-09-23T10:06:26.000Z
tags: book/platform, business-units, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — UI Screens

![Business Unit — UI Screens screen](/screenshots/platform/business-units/ui-screens.png)

![Business Unit — UI Screens form screen](/screenshots/platform/business-units/ui-screens-form.png)

## 1. At a Glance

- หน้ารายการ **ดีดเลขหน้าเก่าที่เก็บไว้กลับเข้าช่วง** (PR #298, 2026-09-21): `page_business_units` ใน `localStorage` อาจอยู่นานกว่าชุดผลลัพธ์ที่มันเคยใช้ได้ และการขอหน้าเกินหน้าสุดท้ายคืน `200` โดยไม่มีแถว — ซึ่งเคยแทนที่ทั้งตาราง *รวม pager* ทิ้งผู้ปฏิบัติงานไว้กับรายการ "ว่าง" ทั้งที่แถบ Overview ยังนับแถวอยู่ `outOfRangePage()` (`src/utils/pageRange.ts`) คำนวณหน้าสุดท้ายจาก `paginate.total` แล้วขอหน้านั้นใหม่
- หน้ารายการ: แถบสรุป **Overview** (`BuSummary`, ตอนนี้อ่านจาก endpoint สรุปเฉพาะ `GET /api-system/business-units/summary`), `BrandMark` avatar เล็ก ๆ ข้างชื่อ BU ในคอลัมน์ Name (กลับมาใหม่), คอลัมน์ audit Created/Updated และ row action **สามรายการ** — Edit / View History (`activity_log.read`, ใหม่) / Delete — ทั้งหมด gate ด้วย `<Can>` แบบ cluster-scoped — ไม่มี client-side deletion guard คอลัมน์ CSV ตัด "Max Licensed Users" ออกแล้ว (ฟิลด์เดิมถูกถอดออกจาก schema)
- Route guard reuse key `cluster.read` / `cluster.create` / `cluster.update` **บวก feature flag `business_units`** — ไม่มี key `business_unit.*` (ดู [business-units](/th/platform/business-units) §4)
- หน้าแก้ไข **เขียนใหม่เป็นครั้งที่สอง** นับตั้งแต่ sync ก่อนหน้า — จากหน้าเอกสารเดียวแบบ scroll ต่อเนื่อง ให้กลายเป็น **เอกสารหกแท็บ**: General (Details รวม Code แบบอ่านอย่างเดียว + Max users แบบอ่านอย่างเดียว, Calculation Settings, Branding) → Location (Hotel/Company/Tax) → Formats (Date & time, Number Formats) → Technical (Configuration, Database Connection ใหม่ทั้งหมด, การ์ด advanced **สองใบ** — Tenant Migrations และ Tenant Seed; การ์ด **Interface Entitlement** ถูกลบใน PR #286 (2026-09-08) เพราะ interface entitlement กลายเป็น licence ที่ขายจากโมดูล [Licenses](/th/platform/licenses) §3.6) → Users (เฉพาะ BU ที่มีอยู่แล้ว) → Licenses (เฉพาะ BU ที่มีอยู่แล้ว, **แท็บใหม่**) — ยังไม่มี toggle read/edit; boolean `canEdit` ตัวเดียว gate ทุกอย่าง
- **`code` ไม่ให้ผู้ใช้กรอกอีกต่อไป** — backend สุ่มให้ตอนสร้าง ฟอร์มสร้างไม่มีช่อง code เลย หน้าแก้ไขแสดงแบบอ่านอย่างเดียว
- **Database Connection ถูกสร้างใหม่ทั้งหมด** — ไม่มี field host/port/database/user/password/ssl อีกต่อไป (และไม่มีปุ่ม Reveal password ด้วย) แทนที่ด้วย dropdown เลือก Database Pool (gate ด้วย `database_pool.read`) + ช่อง Schema พร้อม**ปุ่ม "Generate schema" สุ่มชื่อ** (`bu_` + ตัวอักษร/ตัวเลขสุ่ม 16 ตัว) เปลี่ยนค่า pool/schema จากค่าที่เคย save ไว้ต้องผ่าน confirm dialog ก่อน
- **แท็บ Licenses** แยกออกจาก Users — ตั้งแต่ PRs #287–#289 (2026-09-09) มี**สองการ์ด**และ badge ของแท็บนับทั้งสอง ledger: การ์ด 1 `BusinessUnitLicensesCard` (สรุปที่นั่งแบบอ่านอย่างเดียว + subscription ทุกใบของ BU นี้บน `LicenseTimeline` ร่วมกัน, ปุ่ม Manage licences และ **New subscription** ที่ gate ด้วย `subscription.manage`) และการ์ด 2 `BusinessUnitInterfaceLicensesCard` (interface licence `INF` ของ BU, badge ทุกตัวมาจาก `in_force` ของ backend — แถวที่ยังอยู่ในช่วงวันที่แต่สัญญาหลักหมดอายุแสดง **Capped by contract**, ปุ่ม **Add interface license** gate ด้วย `subscription.manage` เดียวกัน)
- **Tenant Migrations card** ตั้งแต่ PR #297 (2026-09-16) เก็บ error ของการตรวจสอบสถานะไว้บนการ์ด (`role="alert"`) และมีปุ่ม **Resolve** ที่เปิด `TenantMigrationResolveDialog` ตัวเดียวกับหน้าจอ fleet [Tenant Migrations](/th/platform/tenant-migrations) §3.2a
- หัวคอลัมน์ Key/Label/Type ของ Configuration section และ Name/Email/Username/BU Role/BU Status ของการ์ด Users เรียงใน memory ได้ผ่าน `SortableTableHead` ตั้งแต่ PR #292 (2026-09-09)
- Max users บนแท็บ General ไม่ใช่ integer ที่พิมพ์ได้อีกต่อไป — เป็นผลรวมที่นั่ง active จาก `tb_business_unit_license` แบบอ่านอย่างเดียว
- **ยังใช้งานได้จริงหลังการเขียนใหม่ทั้งสองรอบ**: แต่ละ field ยัง commit ตอน blur/Enter และ revert ตอน `Escape` ผ่าน `InlineField`; แถบล่าง sticky ยังมี `Ctrl/⌘+S` (save, เช็ก `canEdit` ซ้ำเอง) และ `Escape` (cancel — ทำงานเฉพาะ BU ที่มีอยู่แล้วและมีการเปลี่ยนแปลงค้างอยู่ ไม่ทำอะไรตอนสร้างใหม่)

## 2. References

- ../carmen-platform/src/pages/BusinessUnitManagement.tsx, businessUnitManagement/BuSummary.tsx
- ../carmen-platform/src/pages/BusinessUnitEdit.tsx, businessUnitEdit/{BusinessUnitDocument,BusinessUnitTabs,HeroName,BusinessUnitLicensesCard,BusinessUnitInterfaceLicensesCard,LicenseTimeline,useBusinessUnitSubscriptions,types}.ts(x), sections/{CalculationSettingsSection,DatabaseConnectionSection,ConfigurationSection,NumberFormatsSection}.tsx
- ../carmen-platform/src/utils/{databasePool,buLicense,pageRange}.ts — ตัวสุ่มชื่อ schema, การคำนวณ ledger ที่นั่ง, `outOfRangePage()` (PR #298)
- ../carmen-platform/src/components/{TenantMigrationCard,TenantSeedCard,TenantMigrationResolveDialog,SortableTableHead,BrandingImageUpload}.tsx — `InterfaceEntitlementCard.tsx` ถูกลบใน PR #286

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/business-units/ui-screens (เลย์เอาต์เปลี่ยนเป็นหกแท็บแล้ว — เอกสารเดียวที่เคยบันทึกไว้เป็นประวัติศาสตร์ไปแล้ว)
- [ ] Screenshot แต่ละแท็บ (เลย์เอาต์ใหม่ทั้งหมด — capture เดิมถ้ามีจะ stale)
