---
title: หน่วยธุรกิจ — Tenant Migrations
description: หน้าจอ fleet-wide /tenant-migrations ย้ายไปเป็นโมดูลระดับบนสุดของตัวเองแล้ว — หน้านี้เหลือเฉพาะส่วนที่ยังเฉพาะเจาะจงกับ Business Units จริง ๆ คือการ์ด TenantMigrationCard ต่อ BU ที่ฝังอยู่บนแท็บ Technical ของหน้าแก้ไข
published: true
date: '2026-09-06T19:00:00.000Z'
tags: book/platform, business-units, tenant-migrations
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# หน่วยธุรกิจ — Tenant Migrations

> **ย้ายแล้ว:** หน้าจอ `/tenant-migrations` ระดับ fleet (`TenantMigrationManagement` พร้อม route, nav entry, และ feature key `tenant_migrations` ของตัวเอง) ถูกบันทึกไว้อย่างเต็มรูปแบบที่ **[การย้ายเทแนนต์ (Tenant Migrations)](/th/platform/tenant-migrations)** และหน้าย่อย [Data Model](/th/platform/tenant-migrations/data-model) ของมัน หน้านี้เหลือเฉพาะส่วนเดียวของหน้าจอนั้นที่เฉพาะเจาะจงกับ Business Units จริง ๆ คือการ์ด `TenantMigrationCard` ต่อ BU ที่ฝังอยู่

## 1. การ์ดต่อ BU

แท็บ Technical ของหน้าแก้ไข Business Units ฝัง `TenantMigrationCard` (เฉพาะ BU ที่มีอยู่แล้ว) ซึ่งเป็นเวอร์ชันย่อของหน้าจอระดับ fleet ที่ scope เฉพาะ BU ตัวที่กำลังเปิดอยู่: ตรวจสอบสถานะ migration ของฐานข้อมูล tenant ของ BU นั้นเอง และ apply migration ที่ค้างผ่านกลไก streamed-progress เดียวกัน อยู่หลัง confirm dialog เดียวกัน รายละเอียดการทัวร์หน้าจอแบบเต็ม — layout, disabled state, ปุ่มสลับดู raw output — บันทึกไว้ที่ [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.5 ซึ่งอยู่คู่กับการ์ด advanced พี่น้องอีกสองใบ (Tenant Seed, Interface Entitlement)

การ์ดนี้และหน้าจอระดับ fleet เรียก `tenantMigrationService` (`getStatus`, `deployStream`) และ backend controller เดียวกันเป๊ะ — มี implementation ของ "ตรวจสอบสถานะ" และ "apply migration" เพียงชุดเดียว ที่แสดงผลจากสองหน้าจอ ดู [การย้ายเทแนนต์ (Tenant Migrations)](/th/platform/tenant-migrations) §3.5 สำหรับการเปรียบเทียบแบบเต็ม รวมถึงการแก้ไขที่ยืนยันซ้ำแล้ว: ทั้งสองหน้าจอ gate **ทุก** action รวมถึงการตรวจสอบสถานะแบบอ่านอย่างเดียว ด้วย `isSuperAdmin` เหมือนกัน — การ์ดนี้ไม่ได้หลวมกว่าตาราง fleet ตรงจุดนี้ ความต่างจริง ๆ มีแค่ว่าการ์ดจะ disable ปุ่มเพิ่มเมื่อ BU ยังไม่ได้ตั้งค่า database pool/schema (`hasDbConnection`) ซึ่งเป็นการตรวจล่วงหน้าที่ตาราง fleet ไม่มี

ไม่มีลิงก์ในแอประหว่างการ์ดนี้กับหน้าจอระดับ fleet ในทิศทางใดเลย คอลัมน์ "Code" ของหน้าจอ fleet เองก็ลิงก์กลับไปหน้าแก้ไข BU นั้นตรง ๆ ไม่ใช่เวอร์ชัน filter ของตัวเอง

## 2. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/components/TenantMigrationCard.tsx` — การ์ดที่ฝังอยู่
- [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.5 — รายละเอียดการทัวร์หน้าจอแบบเต็มของการ์ดนี้ คู่กับ Tenant Seed และ Interface Entitlement
- [การย้ายเทแนนต์ (Tenant Migrations)](/th/platform/tenant-migrations) — เรื่องเต็มของหน้าจอระดับ fleet: layout, action และการ gate, สถานะ migration, ช่องว่างที่ทราบแล้ว, และ data model
