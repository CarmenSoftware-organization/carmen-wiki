---
title: หน่วยธุรกิจ — Tenant Migrations
description: หน้าจอ fleet-wide /tenant-migrations ย้ายไปเป็นโมดูลระดับบนสุดแล้ว — หน้านี้เหลือเฉพาะการ์ด TenantMigrationCard ต่อ BU ที่ฝังบนแท็บ Technical ของหน้าแก้ไข BU
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, business-units, tenant-migrations
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# หน่วยธุรกิจ — Tenant Migrations

> **ย้ายแล้ว:** หน้าจอ `/tenant-migrations` ระดับ fleet (`TenantMigrationManagement` พร้อม route, nav entry, และ feature key `tenant_migrations` ของตัวเอง) ถูกบันทึกไว้อย่างเต็มรูปแบบที่ **[การย้ายเทแนนต์ (Tenant Migrations)](/th/backstage/tenant-migrations)** และหน้าย่อย [Data Model](/th/backstage/tenant-migrations/data-model) ของมัน หน้านี้เหลือเฉพาะส่วนเดียวของหน้าจอนั้นที่เฉพาะเจาะจงกับ Business Units จริง ๆ คือการ์ด `TenantMigrationCard` ต่อ BU ที่ฝังอยู่

![หน่วยธุรกิจ — Tenant Migrations screen](/screenshots/platform/business-units/tenant-migrations.png)

## 1. การ์ดต่อ BU

แท็บ Technical ของหน้าแก้ไข Business Units ฝัง `TenantMigrationCard` (เฉพาะ BU ที่มีอยู่แล้ว) ซึ่งเป็นเวอร์ชันย่อของหน้าจอระดับ fleet ที่ scope เฉพาะ BU ตัวที่กำลังเปิดอยู่: ตรวจสอบสถานะ migration ของฐานข้อมูล tenant ของ BU นั้นเอง apply migration ที่ค้างผ่านกลไก streamed-progress เดียวกันหลัง confirm dialog เดียวกัน และ — ตั้งแต่ `../carmen-backstage` PR #297 (2026-09-16) — **resolve** migration ที่ค้างได้ผ่าน `TenantMigrationResolveDialog` ตัวเดียวกับที่ตาราง fleet ใช้ การตรวจสอบสถานะที่ล้มเหลวตอนนี้ถูกเก็บไว้บนการ์ด (`role="alert"`, ข้อความดิบ) แทนที่จะถูกกลืนหายไปใน toast สี่วินาที เพื่อให้ปุ่ม Resolve มี error ให้เกาะและมีชื่อ migration ให้กรอกล่วงหน้า รายละเอียดการทัวร์หน้าจอแบบเต็ม — layout, disabled state, ปุ่มสลับดู raw output — บันทึกไว้ที่ [Business Units — UI Screens](/th/backstage/business-units/ui-screens) §4.5 ซึ่งอยู่คู่กับการ์ด advanced พี่น้องที่เหลืออยู่ใบเดียว (Tenant Seed; การ์ดใบที่สามเดิม Interface Entitlement ถูกลบใน PR #286 เมื่อ interface entitlement กลายเป็น licence — ดู [Licenses](/th/backstage/licenses) §3.6)

การ์ดนี้และหน้าจอระดับ fleet เรียก `tenantMigrationService` (`getStatus`, `deployStream`, `resolve`) และ backend controller เดียวกันเป๊ะ — มี implementation ของ "ตรวจสอบสถานะ" "apply migration" และ "resolve" เพียงชุดเดียว ที่แสดงผลจากสองหน้าจอ ดู [การย้ายเทแนนต์ (Tenant Migrations)](/th/backstage/tenant-migrations) §3.5 สำหรับการเปรียบเทียบแบบเต็ม รวมถึงการแก้ไขที่ยืนยันซ้ำแล้ว: ตั้งแต่รอบ 2026-10 ทั้งสองหน้าจอ gate ด้วย key `tenant_migration.*` แทน `isSuperAdmin`: การ์ด render เมื่อมี `tenant_migration.read` เท่านั้น, action Apply/Resolve ต้องมี `tenant_migration.apply` (prop `canApply`) และการตรวจสอบสถานะไม่ต้องใช้ key apply — ดูการ gate ของตาราง fleet เองในโมดูลแบบ standalone ความต่างจริง ๆ มีแค่ว่าการ์ดจะ disable ปุ่มเพิ่มเมื่อ BU ยังไม่ได้ตั้งค่า database pool/schema (`hasDbConnection`) ซึ่งเป็นการตรวจล่วงหน้าที่ตาราง fleet ไม่มี

ไม่มีลิงก์ในแอประหว่างการ์ดนี้กับหน้าจอระดับ fleet ในทิศทางใดเลย คอลัมน์ "Code" ของหน้าจอ fleet เองก็ลิงก์กลับไปหน้าแก้ไข BU นั้นตรง ๆ ไม่ใช่เวอร์ชัน filter ของตัวเอง

## 2. แหล่งข้อมูลอ้างอิง

- `../carmen-backstage/src/components/TenantMigrationCard.tsx` — การ์ดที่ฝังอยู่
- `../carmen-backstage/src/components/TenantMigrationResolveDialog.tsx`, `src/utils/migrationError.ts` — dialog Resolve ที่ใช้ร่วมกันและตัว parse ชื่อ migration
- [Business Units — UI Screens](/th/backstage/business-units/ui-screens) §4.5 — รายละเอียดการทัวร์หน้าจอแบบเต็มของการ์ดนี้ คู่กับ Tenant Seed
- [การย้ายเทแนนต์ (Tenant Migrations)](/th/backstage/tenant-migrations) — เรื่องเต็มของหน้าจอระดับ fleet: layout, action และการ gate, สถานะ migration, ช่องว่างที่ทราบแล้ว, และ data model
