---
title: ข้อมูลหลัก (Master Data)
description: ข้อมูลหลักทางธุรกิจที่ถูกอ้างอิงโดยเอกสารธุรกรรมต่าง ๆ — หน่วยนับ แผนก ผู้ขาย สกุลเงิน Profile ภาษี และแคตตาล็อกที่เกี่ยวข้อง
published: true
date: 2026-05-19T23:55:00.000Z
tags: master-data, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ข้อมูลหลัก (Master Data)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แคตตาล็อกของระเบียนที่มีชื่อ (หน่วยนับ ผู้ขาย สกุลเงิน สถานที่ Profile ภาษี รหัสเหตุผล) ที่เอกสารธุรกรรมอ้างอิงผ่าน FK + denormalised snapshot &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Product Admin, Configurator, Sysadmin &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_unit`, `tb_vendor`, `tb_currency` + `tb_exchange_rate`, `tb_tax_profile`, `tb_location` &nbsp;·&nbsp; **หน้าย่อย:** 13

![ข้อมูลหลัก (Master Data) screen](/screenshots/master-data/index.png)

## 1. ภาพรวม

ข้อมูลหลัก (Master Data) คือชุดของระเบียนที่มีชื่อซึ่งเอกสารธุรกรรม *อ้างอิง* แต่ไม่ได้เป็นเจ้าของ หน่วยนับ แผนก สถานที่ จุดส่งของ หน่วยธุรกิจ สกุลเงิน ผู้ขาย Profile ภาษี เงื่อนไขการชำระเงิน ประเภทค่าใช้จ่ายเพิ่ม ประเภทการปรับสต๊อก เหตุผลใบลดหนี้ และเทมเพลต pricelist ทั้งหมดอยู่ที่นี่ แต่ละเอนทิตีเล็กในตัวเอง แต่ทุกตัวถูกอ้างอิงโดยแถวธุรกรรมจำนวนมาก

มีหลักการสองข้อที่ขับเคลื่อนการจัดวางของโมดูลร่ม **snapshot semantics**: เอกสารเก็บ FK ไปยังระเบียนหลัก *พร้อมกับ* สำเนาสำหรับแสดงผลแบบ denormalised (name, rate, code) เพื่อให้เอกสารย้อนหลังยังแสดงผลถูกต้องแม้ระเบียนหลักจะถูกเปลี่ยนชื่อหรือยกเลิกการใช้งานในภายหลัง สอง **soft-delete พร้อม active flag**: ทุกเอนทิตีใช้ `is_active` + `deleted_at` เพื่อปลดระวางระเบียนโดยไม่ทำลาย referential integrity ดังนั้นคำตอบมาตรฐานต่อ "ลบ X" คือ "ยกเลิกการใช้งาน X"

โมดูลร่มนี้ครอบคลุม Prisma schema ทั้งสอง เอนทิตีส่วนใหญ่อยู่ใน schema แบบ **tenant** (ฐานข้อมูลต่อ property) แต่ `business-unit` และ `currency-iso` อยู่ที่ระดับ **platform** (ใช้ร่วมกันข้าม tenant) ส่วน `currency` เป็นแบบผสม — การอ้างอิง ISO อยู่ที่ platform ส่วนรายการสกุลเงินที่เปิดใช้งานและอัตรามีวันที่อยู่ที่ tenant

## 2. กลุ่มผู้ใช้

Product Admin และ Configurator เป็นผู้บริหารจัดการข้อมูลเหล่านี้ Sysadmin กำกับดูแลด้านการเชื่อมต่อและ RBAC และเป็นเจ้าของแต่เพียงผู้เดียวในการตั้งค่า `business-unit` และ `currency-iso` ที่ระดับ platform

## 3. รายการเอนทิตี

| Entity | วัตถุประสงค์ | ผู้บริหารจัดการ |
| ------ | ------------ | ---------------- |
| [unit](/th/inventory/master-data/unit) | หน่วยนับและการแปลงหน่วยต่อสินค้า | Product Admin |
| [department](/th/inventory/master-data/department) | แผนกขององค์กรและการ map ผู้ใช้กับแผนก | Product Admin / Sysadmin |
| [location](/th/inventory/master-data/location) | สถานที่ inventory, direct และ consignment พร้อมพฤติกรรมการนับ | Product Admin |
| [delivery-point](/th/inventory/master-data/delivery-point) | จุดส่งสินค้าทางกายภาพสำหรับการจัดส่งของผู้ขาย | Product Admin |
| [business-unit](/th/inventory/master-data/business-unit) | หน่วยปฏิบัติการ — เป็นเจ้าของ calculation method และ default currency | Sysadmin |
| [currency](/th/inventory/master-data/currency) | สกุลเงินที่เปิดใช้งาน, ISO reference และประวัติอัตราแลกเปลี่ยนแบบมีวันที่ | Product Admin / Sysadmin |
| [exchange-rate](/th/inventory/master-data/exchange-rate) | ประวัติอัตรา FX แบบมีวันที่ที่ใช้สำหรับ snapshot บนเอกสารและ FX revaluation ของ costing | Product Admin |
| [vendor](/th/inventory/master-data/vendor) | ผู้ขายพร้อมที่อยู่ ผู้ติดต่อ และ taxonomy ของประเภทธุรกิจ | Product Admin |
| [tax-profile](/th/inventory/master-data/tax-profile) | นิยามอัตราภาษีแบบมีชื่อ | Product Admin |
| [credit-term](/th/inventory/master-data/credit-term) | เงื่อนไขการชำระเงินกับผู้ขาย (NET 30, COD, ฯลฯ) | Product Admin |
| [extra-cost-type](/th/inventory/master-data/extra-cost-type) | หมวด landed cost ของ GRN พร้อมโหมดการจัดสรร | Product Admin |
| [adjustment-type](/th/inventory/master-data/adjustment-type) | รหัสเหตุผลสำหรับการปรับสต๊อก stock-in / stock-out | Product Admin |
| [credit-note-reason](/th/inventory/master-data/credit-note-reason) | รหัสเหตุผลสำหรับใบลดหนี้ที่ออกต่อ GRN | Product Admin |

## 4. การพึ่งพาข้ามโมดูล

- [purchase-request](/th/inventory/purchase-request) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/department](/th/inventory/master-data/department), [master-data/location](/th/inventory/master-data/location), [master-data/vendor](/th/inventory/master-data/vendor), [master-data/tax-profile](/th/inventory/master-data/tax-profile), [master-data/currency](/th/inventory/master-data/currency), [master-data/exchange-rate](/th/inventory/master-data/exchange-rate)
- [purchase-order](/th/inventory/purchase-order) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/vendor](/th/inventory/master-data/vendor), [master-data/currency](/th/inventory/master-data/currency), [master-data/exchange-rate](/th/inventory/master-data/exchange-rate), [master-data/tax-profile](/th/inventory/master-data/tax-profile), [master-data/credit-term](/th/inventory/master-data/credit-term), [master-data/delivery-point](/th/inventory/master-data/delivery-point)
- [good-receive-note](/th/inventory/good-receive-note) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/vendor](/th/inventory/master-data/vendor), [master-data/currency](/th/inventory/master-data/currency), [master-data/exchange-rate](/th/inventory/master-data/exchange-rate), [master-data/tax-profile](/th/inventory/master-data/tax-profile), [master-data/extra-cost-type](/th/inventory/master-data/extra-cost-type), [master-data/credit-note-reason](/th/inventory/master-data/credit-note-reason), [master-data/delivery-point](/th/inventory/master-data/delivery-point), [master-data/location](/th/inventory/master-data/location)
- [store-requisition](/th/inventory/store-requisition) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/location](/th/inventory/master-data/location), [master-data/department](/th/inventory/master-data/department)
- [inventory](/th/inventory/inventory) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/location](/th/inventory/master-data/location), [master-data/business-unit](/th/inventory/master-data/business-unit)
- [inventory-adjustment](/th/inventory/inventory-adjustment) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/location](/th/inventory/master-data/location), [master-data/adjustment-type](/th/inventory/master-data/adjustment-type), [master-data/credit-note-reason](/th/inventory/master-data/credit-note-reason)
- [physical-count](/th/inventory/physical-count) ต้องใช้ [master-data/location](/th/inventory/master-data/location), [master-data/unit](/th/inventory/master-data/unit), [master-data/adjustment-type](/th/inventory/master-data/adjustment-type)
- [spot-check](/th/inventory/spot-check) ต้องใช้ [master-data/location](/th/inventory/master-data/location), [master-data/adjustment-type](/th/inventory/master-data/adjustment-type)
- [costing](/th/inventory/costing) ต้องใช้ [master-data/business-unit](/th/inventory/master-data/business-unit) (สำหรับ `calculation_method`), [master-data/currency](/th/inventory/master-data/currency) และ [master-data/exchange-rate](/th/inventory/master-data/exchange-rate) (สำหรับ FX revaluation แบบมีวันที่)
- [vendor-pricelist](/th/inventory/vendor-pricelist) ต้องใช้ [master-data/vendor](/th/inventory/master-data/vendor), [master-data/currency](/th/inventory/master-data/currency), [master-data/tax-profile](/th/inventory/master-data/tax-profile), [templates/price-list](/th/inventory/templates/price-list)
- [product](/th/inventory/product) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/tax-profile](/th/inventory/master-data/tax-profile)
- [recipe](/th/inventory/recipe) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit)

## 5. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
- **carmen/docs:** `../carmen/docs/settings/locations.md` (อ้างอิงโดย [master-data/location](/th/inventory/master-data/location) เท่านั้น)
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
