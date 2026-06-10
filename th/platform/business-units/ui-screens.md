---
title: Business Unit — UI Screens
description: BusinessUnitManagement (list) และ BusinessUnitEdit (เซกชันฟอร์ม 9 ส่วน, card Branding, card Users)
published: true
date: 2026-06-10T16:30:00.000Z
tags: book/platform, business-units, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — UI Screens

## 1. At a Glance

- หน้ารายการตาม convention มาตรฐาน บวกคอลัมน์ thumbnail ของ logo (fallback เป็น avatar), คอลัมน์ audit Created/Updated และ row action Edit/Delete ที่ gate ด้วย `<Can>` แบบ cluster-scoped (`clusterId` = cluster แม่ของ BU)
- Route guard reuse key `cluster.read` / `cluster.create` / `cluster.update` — ไม่มี key `business_unit.*` (ดู [business-units](/th/platform/business-units) §4)
- หน้าแก้ไข: เซกชันฟอร์ม 9 ส่วน (`BusinessUnitFormData` 34 ฟิลด์) ตามด้วย card Branding และ card Users แบบเต็มความกว้าง (render เฉพาะเมื่อ BU มีอยู่แล้ว); toggle Edit ถูก gate ด้วย `cluster.update` + `clusterId`
- Card Branding: อัปโหลด logo/avatar ผ่าน `BrandingImageUpload` — บันทึกทันทีเมื่ออัปโหลด ไม่ขึ้นกับปุ่ม Save
- Quirk หลัง create: navigate ไป `/business-units/:id` ซึ่งไม่ใช่ route ที่ลงทะเบียน — catch-all พา operator ไปลงที่ Dashboard (quirk เดียวกับ cluster create)
- Endpoint แบบพหูพจน์: `/api-system/business-units`, `/api-system/user/business-units`, `/api-system/user/clusters/:clusterId`

## 2. References

- ../carmen-platform/src/pages/BusinessUnitManagement.tsx
- ../carmen-platform/src/pages/BusinessUnitEdit.tsx
- ../carmen-platform/src/components/BrandingImageUpload.tsx

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/business-units/ui-screens
- [ ] Screenshot แต่ละเซกชันของฟอร์ม
