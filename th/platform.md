---
title: Carmen Platform
description: Overview of the Carmen Platform admin product — entry point for the book.
published: true
date: 2026-09-06T01:00:00.000Z
tags: book/platform, home
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Carmen Platform

คู่มืออ้างอิงสำหรับนักพัฒนาและทีม support ที่ทำงานกับ Carmen Platform admin — tenancy (cluster และ business unit), identity และการเข้าถึง, การส่งมอบเนื้อหา (news และ broadcast), API client, เทมเพลตรายงานและการพิมพ์ และ changelog ของผลิตภัณฑ์

## 1. Tenancy

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Clusters](/th/platform/clusters) | โครงสร้าง cluster ของ tenant และความเป็นเจ้าของ |
| [Business Units](/th/platform/business-units) | จัดการสาขา / business unit ภายใน cluster |

## 2. Identity & Access

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Users](/th/platform/users) | บัญชีผู้ใช้ avatar และการ assign cluster/BU |
| [Platform RBAC](/th/platform/rbac) | permission catalog, role, การ assign ผู้ใช้แบบมี scope และ super-admin bypass |
| [Profile](/th/platform/profile) | โปรไฟล์ของผู้ใช้ที่ล็อกอินอยู่และการเปลี่ยนรหัสผ่าน |

## 3. Content

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [News](/th/platform/news) | ประกาศแบบ markdown พร้อม lifecycle draft → published → archived และการกำหนดเป้าหมายแบบ global หรือราย BU |
| [Broadcasts](/th/platform/broadcasts) | หน้าจอเขียน push notification พร้อม target mode สามแบบ และการส่งทันทีหรือตามกำหนดเวลา |

## 4. Platform

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Applications](/th/platform/applications) | API client ที่ลงทะเบียน, identity แบบ `x-app-id` และการมอบสิทธิ์เข้าถึงตาม `api_name` |
| [SQL Workbench](/th/platform/sql-workbench) | คอนโซล SQL ต่อ tenant — browse/รัน/save/drop view, procedure, และ function กับฐานข้อมูลของ business unit |

## 5. Reporting

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Report Templates](/th/platform/report-templates) | แคตตาล็อกเทมเพลตรายงานแบบ XML พร้อม editor แบบแท็บ และการกำหนดขอบเขตราย BU |

## 6. Product & Shell

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Landing](/th/platform/landing) | หน้าการตลาดสาธารณะที่ `/` — redirect session ที่ authenticated ไปยัง Dashboard ทันที |
| [Dashboard](/th/platform/dashboard) | home hub สำหรับผู้ใช้ที่ signed-in — activity stream รวม + จำนวน active/total ต่อโดเมน |
| [Changelog](/th/platform/changelog) | ประวัติการเปลี่ยนแปลงเวอร์ชัน (สาธารณะ) + version badge |

## 7. การใช้งาน book นี้

- เริ่มจากหน้า home ของแต่ละโมดูลเพื่อภาพรวม
- เจาะลึก sub-pages สำหรับ data model, UI flow, edge cases
- ดู [global wiki landing](/th/home) สำหรับ Inventory book
