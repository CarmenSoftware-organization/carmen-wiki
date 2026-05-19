---
title: Carmen Inventory
description: Carmen Inventory ERP — เอกสารอ้างอิงโมดูลสำหรับนักพัฒนาและทีมทดสอบ
published: true
date: 2026-05-19T00:00:00.000Z
tags: book/inventory, home
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Carmen Inventory

คู่มืออ้างอิงสำหรับนักพัฒนาและ QA ที่ทำงานกับ Carmen Inventory ERP — ระบบ supply chain สำหรับโรงแรม

## 1. ภาพรวม

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Dashboard](/th/inventory/dashboard) | สรุปและ KPI |

## 2. การจัดซื้อ

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Purchase Request](/th/inventory/purchase-request) | กระบวนการอนุมัติ PR |
| [Purchase Order](/th/inventory/purchase-order) | วงจรชีวิตของ PO |
| [Good Receive Note](/th/inventory/good-receive-note) | กระบวนการรับสินค้า |
| [Vendor Pricelist](/th/inventory/vendor-pricelist) | แค็ตตาล็อกและราคาผู้ขาย |

## 3. การดำเนินงานคลัง

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Inventory](/th/inventory/inventory) | การเคลื่อนไหวสต็อก การประเมินมูลค่า |
| [Inventory Adjustment](/th/inventory/inventory-adjustment) | การปรับสต็อกและเหตุผล |
| [Physical Count](/th/inventory/physical-count) | รอบนับสต็อกและการกระทบยอด |
| [Spot Check](/th/inventory/spot-check) | การสุ่มนับ |
| [Store Requisition](/th/inventory/store-requisition) | โอนสินค้าระหว่างคลัง |

## 4. สินค้าและสูตร

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Product](/th/inventory/product) | แค็ตตาล็อกสินค้าและคุณสมบัติ |
| [Master Data](/th/inventory/master-data) | ข้อมูลอ้างอิงและ lookups |
| [Recipe](/th/inventory/recipe) | สูตรและ BOM |

## 5. ต้นทุนและรายงาน

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Costing](/th/inventory/costing) | วิธีคิดต้นทุน FIFO Weighted Average |
| [Reporting & Audit](/th/inventory/reporting-audit) | รายงานและ audit trail |

## 6. การดูแลระบบ

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Access Control](/th/inventory/access-control) | บทบาท สิทธิ์ การควบคุมการเข้าถึง |
| [System Config](/th/inventory/system-config) | การตั้งค่าระดับ tenant |
| [Templates](/th/inventory/templates) | เทมเพลตเอกสาร |

## 7. การใช้งาน book นี้

- เริ่มจากหน้า home ของแต่ละโมดูลเพื่อภาพรวม
- เจาะลึก sub-pages สำหรับ data model, UI flow, edge cases
- ดู [global wiki landing](/th/index) สำหรับ Platform book
