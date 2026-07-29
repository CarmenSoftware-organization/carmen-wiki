---
title: Business Unit — UI Screens
description: BusinessUnitManagement (list) และ BusinessUnitEdit (เซกชันฟอร์ม 9 ส่วน, card Branding, card Users)
published: true
date: 2026-07-29T07:50:16.000Z
tags: book/platform, business-units, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — UI Screens

## 1. At a Glance

- หน้ารายการ: แถบสรุป **Overview** (`BuSummary` — total/active/inactive/archived, จำนวน cluster) แทนที่คอลัมน์ thumbnail logo ต่อแถวที่ถูกลบไปแล้ว, คอลัมน์ audit Created/Updated และ row action Edit/Delete ที่ gate ด้วย `<Can>` แบบ cluster-scoped (`clusterId` = cluster แม่ของ BU) — ไม่มี client-side deletion guard
- Route guard reuse key `cluster.read` / `cluster.create` / `cluster.update` — ไม่มี key `business_unit.*` (ดู [business-units](/th/platform/business-units) §4)
- หน้าแก้ไข **เขียนใหม่ทั้งหมด** จากการ์ด 9 เซกชันในกริดสองคอลัมน์ ให้เป็นเอกสารเดียวแบบ scroll ต่อเนื่อง: hero card (logo/avatar, badge Active/HQ ที่คลิกได้) → 6 กลุ่ม field แบบ inline (Details/Location/Contact/Company/Tax/Date & time) → 4 เซกชันซับซ้อน (Calculation Settings/Number Formats/Branding/Configuration/Database Connection) → 3 การ์ด advanced (Tenant Migrations/Tenant Seed/Interface Entitlement, เฉพาะ BU ที่มีอยู่แล้ว, ทุกคนที่แก้ไข BU ได้เห็นการ์ดเหล่านี้เสมอ — มีเพียง action ที่เปลี่ยนแปลงข้อมูลเท่านั้นที่ gate ด้วย super-admin) → card Users — **ไม่มี toggle read/edit อีกต่อไป** boolean `canEdit` ตัวเดียว gate ทุกอย่าง แถบ sticky ด้านล่างแสดง Save/Cancel; การบันทึกใช้ optimistic lock `doc_version`
- Database Connection **ไม่ใช่ `<pre>` แบบอ่านอย่างเดียวอีกต่อไป** — เป็นฟอร์มไฮบริด: 7 field ที่รู้จัก (host/port/database/schema/user/password/ssl) + field เพิ่มเติมแบบเปิด password ถูก mask พร้อมปุ่ม Reveal ที่ gate ด้วย permission
- ที่อยู่ hotel/company ถูก restructure จาก field เดียว (`hotel_address`/`company_address`) เป็น 10 คอลัมน์ต่อฝั่ง (line1/line2/sub_district/district/city/province/postal_code/country/latitude/longitude)
- Quirk หลัง create ที่เคยมี **ได้รับการแก้ไขแล้ว**: ตอนนี้ navigate ตรงไป `/business-units/:id/edit` (route ที่ลงทะเบียนไว้แล้ว) แทนที่จะไป `/business-units/:id` ที่ไม่มี route รองรับ (แก้พร้อมกับ quirk เดียวกันบน cluster create)
- Endpoint แบบพหูพจน์: `/api-system/business-units`, `/api-system/user/business-units`, `/api-system/user/clusters/:clusterId`, `revealDbPassword`

## 2. References

- ../carmen-platform/src/pages/BusinessUnitManagement.tsx, businessUnitManagement/BuSummary.tsx
- ../carmen-platform/src/pages/BusinessUnitEdit.tsx, businessUnitEdit/{BusinessUnitDocument,HeroName,types}.ts(x), sections/{CalculationSettingsSection,DatabaseConnectionSection,ConfigurationSection,NumberFormatsSection}.tsx
- ../carmen-platform/src/components/{TenantMigrationCard,TenantSeedCard,InterfaceEntitlementCard,BrandingImageUpload}.tsx
- ../carmen-platform/src/utils/dbConnection.ts

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/business-units/ui-screens (เลย์เอาต์เปลี่ยนเป็น one-document แล้ว)
- [ ] Screenshot แต่ละเซกชัน (เลย์เอาต์ใหม่ทั้งหมด — capture เดิมถ้ามีจะ stale)
