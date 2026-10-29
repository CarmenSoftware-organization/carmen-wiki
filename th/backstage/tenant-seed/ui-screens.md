---
title: Tenant Seed — UI Screens
description: หน้า Tenant Seed ทีละส่วน — การ์ดสรุป fleet, ตาราง business unit พร้อม action Check และ Seed ราย row, dialog ยืนยันการเลือก set, บรรทัดความคืบหน้าแบบ batch และการส่งออก CSV
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, tenant-seed, ui-screens
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Tenant Seed — UI Screens

> **At a Glance**
> **หน้าจอ:** 1 หน้า &nbsp;·&nbsp; **Layout:** การ์ดสรุป, แถบ batch (ถ้ามี), ตารางที่ค้นหาได้ &nbsp;·&nbsp; **Dialogs:** `SeedSetPickerDialog` (ใช้สองครั้ง: BU เดียว, ทั้ง fleet) &nbsp;·&nbsp; **การเข้าถึง:** `tenant_seed.read` เพื่อเปิดและ Check; `tenant_seed.apply` เพื่อ Seed &nbsp;·&nbsp; **UI state ที่เก็บถาวร:** ไม่มี

## 1. ภาพรวม

`TenantSeedManagement` ที่ `/tenant-seeds` ใช้รูปแบบเดียวกับคอนโซล Tenant Migrations ที่เป็นต้นแบบ (import `withTooltip` จาก `TenantMigrationManagement`) state ทั้งหมดอยู่ในหน่วยความจำของ React: การโหลดหน้าซ้ำทำให้ลืมผลการ check ทุกอย่าง ไม่มี route สร้าง/แก้ไข; ทางออกเดียวคือลิงก์ BU code ในแต่ละ row (`/business-units/:id/edit`) และปุ่มใน empty state

## 2. `TenantSeedManagement` (`/tenant-seeds`)

### 2.1 การ์ดสรุป fleet (`SeedFleetSummary`)

การ์ดที่มีสามโซน **ซ้าย:** ตัวนับใหญ่ "`seeded / checkable`" (ขีดกลางแทนตัวเลขจนกว่าจะมีการ check) คำบรรยาย "Tenants seeded"; `checkable` นับ BU ที่มีฐานข้อมูล **กลาง:** แถบสามส่วน (เขียว seeded, เหลืองอำพัน missing, แดง error) พร้อม legend; ส่วนเสริมปรากฏเมื่อเกี่ยวข้องเท่านั้น: legend Error เมื่อมี error, "N missing rows" (รวมทุก BU ที่ Missing) และ legend "No DB" ก่อนการ check ครั้งแรกจะแสดง "Not checked yet - run Check all ..." **ขวา:** ปุ่ม action ด้านล่าง

### 2.2 Header actions

| ปุ่ม | พฤติกรรม |
|---|---|
| **Check all** | ตรวจทุก BU ที่มี DB ขนาน 4 ตัว; toast "Checked N business units." หรือ "Checked N - M failed." ถูก disable ขณะมีอะไรกำลังทำงาน |
| **Seed N missing** / **Seed all missing** | เปิด picker ของ fleet (§2.5) ป้ายเป็น "Seed N missing" เมื่อมี N BU ที่ Missing ไม่งั้น "Seed all missing" ถูก disable พร้อม tooltip อธิบายเหตุผลเมื่อ: ผู้ดูไม่มี `tenant_seed.apply`; ยังไม่ได้ check อะไร ("Not checked yet. Run Check all first..."); หรือทุกอย่างที่ check แล้ว seed ครบ ("Every checked tenant is fully seeded - nothing to seed.") |
| **Export** | ดาวน์โหลด `tenant-seeds-YYYY-MM-DD.csv` คอลัมน์ Code, Name, Status, Missing rows, Missing sets (`key present/defined` คั่นด้วยจุลภาค), Last Checked, Error เปิดใช้งานเมื่อโหลด BU แล้วและไม่มีอะไรกำลังทำงาน |

### 2.3 ตาราง

`DataTable` ฝั่ง client, 25 row ต่อหน้า, เรียงเริ่มต้นตาม Code จากน้อยไปมาก, global filter จากช่องค้นหา (โฟกัสด้วย shortcut ค้นหาส่วนกลาง) คอลัมน์:

| คอลัมน์ | เนื้อหา |
|---|---|
| Code | ลิงก์ไปหน้าแก้ไขของ BU |
| Name | |
| Status | Badge: Seeded (เขียว), "N missing" (เหลืองอำพัน), No DB (เทา, tooltip "This business unit has no database pool or schema configured."), Error (แดง), Not checked (outline) ขณะ seeding มีบรรทัดสด `Seeding done/total - <set key>`; row ที่ Error พิมพ์ข้อความของมันด้วย |
| Missing sets | Chip `key present/defined` (ป้ายของ set เป็น tooltip) สำหรับแต่ละ set ที่มีอะไรขาด; ไม่งั้นเป็นขีดกลาง |
| Last Checked | เวลา `HH:MM:SS` ตามเครื่องของการ check ล่าสุดบน row นี้ |
| Actions | **Check** (ไอคอน refresh) บนทุก row ยกเว้น No DB; **Seed** (ไอคอน sprout, primary) เฉพาะ row ที่ Missing |

Check ใช้ได้ด้วย `read`; Seed ถูก disable พร้อม tooltip "Requires the tenant_seed.apply permission." เมื่อไม่มี `apply` ทั้งคู่ถูก disable ขณะ row นั้น, batch หรือ Check all กำลังทำงาน

สถานะ: `TableSkeleton` ระหว่างโหลด BU; alert สีแดงแบบ inline ถ้ารายการ BU โหลดล้มเหลว ("Failed to load business units: ..."); `EmptyState` "No business units" พร้อมปุ่ม "Go to Business Units" เมื่อไม่มี

### 2.4 แถบความคืบหน้า batch

ขณะ Seed-all ทำงาน จะมีบรรทัดสถานะแบบ monospace เหนือตาราง: `BU i/n - CODE` ตามด้วย set ปัจจุบันและ `done/total` ของสตรีมของ BU นั้น

### 2.5 `SeedSetPickerDialog`

คอมโพเนนต์เดียว ใช้สองแบบ

| | BU เดียว (Seed ของ row) | Fleet (Seed ที่ header) |
|---|---|---|
| Title | "Seed default data?" | "Seed all missing tenants?" |
| Description | ระบุชื่อ BU; "Rows that already exist are skipped." | "...across N business units, one at a time ... Leaving this page stops before the next business unit." |
| ตัวเลือก | set ของ BU นั้นที่มี row ขาด | ยูเนียนของทุก BU ที่ Missing; badge "N missing in M BU" |
| ลูกศรขยาย | แสดง key ของ row ที่ขาด | แสดงบรรทัด `BU code - n` |

ทุก set ถูกติ๊กไว้ก่อนทุกครั้งที่เปิด dialog; "Select all / Clear" สลับทั้งหมด ปุ่มยืนยันถูก disable เมื่อเลือกศูนย์ row และแสดง "Seed N rows" การยืนยันปิด dialog ทันที; ความคืบหน้าแสดงบนหน้าแทน เพราะการ await สตรีมยาวภายใน modal จะบล็อก UI

## 3. UI state ที่เก็บถาวร

ไม่มี ไม่มี key ใน `localStorage` ข้อความค้นหา ผลการ check และสตรีมที่กำลังทำงานเป็น state ของหน้าเท่านั้น; การออกจากหน้าจะ abort สตรีมของเบราว์เซอร์และหยุด batch ก่อน BU ถัดไป

## 4. Screenshots

> **TODO:** Screenshots เลื่อนไปทำในชุด screenshot ของ Platform ที่จะมาถึง ดู `.specs/2026-05-17-screenshots-coverage-checklist.md` สำหรับแผนครอบคลุมข้ามโมดูล

## 5. แหล่งอ้างอิง

- `../carmen-backstage/src/pages/TenantSeedManagement.tsx`, `src/pages/tenantSeed/{SeedFleetSummary,SeedSetPickerDialog}.tsx`, `src/pages/tenantSeed/seedRowState.ts`
- i18n: `pages.tenantSeed.*` ใน `src/i18n/en.ts`
- หน้าข้างเคียง: [Tenant Seed](/th/backstage/tenant-seed), [Lifecycle](/th/backstage/tenant-seed/lifecycle); เวอร์ชัน BU เดียวที่ฝังไว้: [Business Units: UI Screens](/th/backstage/business-units/ui-screens) §4.5
