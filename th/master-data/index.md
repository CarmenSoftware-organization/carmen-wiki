---
title: ข้อมูลหลัก (Master Data)
description: ข้อมูลหลักทางธุรกิจที่ถูกอ้างอิงโดยเอกสารธุรกรรมต่าง ๆ — หน่วยนับ แผนก ผู้ขาย สกุลเงิน Profile ภาษี และแคตตาล็อกที่เกี่ยวข้อง
published: true
date: 2026-05-17T12:00:00.000Z
tags: master-data, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ข้อมูลหลัก (Master Data)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แคตตาล็อกของระเบียนที่มีชื่อ (หน่วยนับ ผู้ขาย สกุลเงิน สถานที่ Profile ภาษี รหัสเหตุผล) ที่เอกสารธุรกรรมอ้างอิงผ่าน FK + denormalised snapshot &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Product Admin, Configurator, Sysadmin &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_unit`, `tb_vendor`, `tb_currency` + `tb_exchange_rate`, `tb_tax_profile`, `tb_location` &nbsp;·&nbsp; **หน้าย่อย:** 13

## 1. ภาพรวม

ข้อมูลหลัก (Master Data) คือชุดของระเบียนที่มีชื่อซึ่งเอกสารธุรกรรม *อ้างอิง* แต่ไม่ได้เป็นเจ้าของ หน่วยนับ แผนก สถานที่ จุดส่งของ หน่วยธุรกิจ สกุลเงิน ผู้ขาย Profile ภาษี เงื่อนไขการชำระเงิน ประเภทค่าใช้จ่ายเพิ่ม ประเภทการปรับสต๊อก เหตุผลใบลดหนี้ และเทมเพลต pricelist ทั้งหมดอยู่ที่นี่ แต่ละเอนทิตีเล็กในตัวเอง แต่ทุกตัวถูกอ้างอิงโดยแถวธุรกรรมจำนวนมาก

มีหลักการสองข้อที่ขับเคลื่อนการจัดวางของโมดูลร่ม **snapshot semantics**: เอกสารเก็บ FK ไปยังระเบียนหลัก *พร้อมกับ* สำเนาสำหรับแสดงผลแบบ denormalised (name, rate, code) เพื่อให้เอกสารย้อนหลังยังแสดงผลถูกต้องแม้ระเบียนหลักจะถูกเปลี่ยนชื่อหรือยกเลิกการใช้งานในภายหลัง สอง **soft-delete พร้อม active flag**: ทุกเอนทิตีใช้ `is_active` + `deleted_at` เพื่อปลดระวางระเบียนโดยไม่ทำลาย referential integrity ดังนั้นคำตอบมาตรฐานต่อ "ลบ X" คือ "ยกเลิกการใช้งาน X"

โมดูลร่มนี้ครอบคลุม Prisma schema ทั้งสอง เอนทิตีส่วนใหญ่อยู่ใน schema แบบ **tenant** (ฐานข้อมูลต่อ property) แต่ `business-unit` และ `currency-iso` อยู่ที่ระดับ **platform** (ใช้ร่วมกันข้าม tenant) ส่วน `currency` เป็นแบบผสม — การอ้างอิง ISO อยู่ที่ platform ส่วนรายการสกุลเงินที่เปิดใช้งานและอัตรามีวันที่อยู่ที่ tenant

## 2. กลุ่มผู้ใช้

Product Admin และ Configurator เป็นผู้บริหารจัดการข้อมูลเหล่านี้ Sysadmin กำกับดูแลด้านการเชื่อมต่อและ RBAC และเป็นเจ้าของแต่เพียงผู้เดียวในการตั้งค่า `business-unit` และ `currency-iso` ที่ระดับ platform

## 3. รายการเอนทิตี

| Entity | วัตถุประสงค์ | ผู้บริหารจัดการ |
| ------ | ------------ | ---------------- |
| [unit](./unit.md) | หน่วยนับและการแปลงหน่วยต่อสินค้า | Product Admin |
| [department](./department.md) | แผนกขององค์กรและการ map ผู้ใช้กับแผนก | Product Admin / Sysadmin |
| [location](./location.md) | สถานที่ inventory, direct และ consignment พร้อมพฤติกรรมการนับ | Product Admin |
| [delivery-point](./delivery-point.md) | จุดส่งสินค้าทางกายภาพสำหรับการจัดส่งของผู้ขาย | Product Admin |
| [business-unit](./business-unit.md) | หน่วยปฏิบัติการ — เป็นเจ้าของ calculation method และ default currency | Sysadmin |
| [currency](./currency.md) | สกุลเงินที่เปิดใช้งาน, ISO reference และประวัติอัตราแลกเปลี่ยนแบบมีวันที่ | Product Admin / Sysadmin |
| [exchange-rate](./exchange-rate.md) | ประวัติอัตรา FX แบบมีวันที่ที่ใช้สำหรับ snapshot บนเอกสารและ FX revaluation ของ costing | Product Admin |
| [vendor](./vendor.md) | ผู้ขายพร้อมที่อยู่ ผู้ติดต่อ และ taxonomy ของประเภทธุรกิจ | Product Admin |
| [tax-profile](./tax-profile.md) | นิยามอัตราภาษีแบบมีชื่อ | Product Admin |
| [credit-term](./credit-term.md) | เงื่อนไขการชำระเงินกับผู้ขาย (NET 30, COD, ฯลฯ) | Product Admin |
| [extra-cost-type](./extra-cost-type.md) | หมวด landed cost ของ GRN พร้อมโหมดการจัดสรร | Product Admin |
| [adjustment-type](./adjustment-type.md) | รหัสเหตุผลสำหรับการปรับสต๊อก stock-in / stock-out | Product Admin |
| [credit-note-reason](./credit-note-reason.md) | รหัสเหตุผลสำหรับใบลดหนี้ที่ออกต่อ GRN | Product Admin |

## 4. การพึ่งพาข้ามโมดูล

- [[purchase-request]] ต้องใช้ [[master-data/unit]], [[master-data/department]], [[master-data/location]], [[master-data/vendor]], [[master-data/tax-profile]], [[master-data/currency]], [[master-data/exchange-rate]]
- [[purchase-order]] ต้องใช้ [[master-data/unit]], [[master-data/vendor]], [[master-data/currency]], [[master-data/exchange-rate]], [[master-data/tax-profile]], [[master-data/credit-term]], [[master-data/delivery-point]]
- [[good-receive-note]] ต้องใช้ [[master-data/unit]], [[master-data/vendor]], [[master-data/currency]], [[master-data/exchange-rate]], [[master-data/tax-profile]], [[master-data/extra-cost-type]], [[master-data/credit-note-reason]], [[master-data/delivery-point]], [[master-data/location]]
- [[store-requisition]] ต้องใช้ [[master-data/unit]], [[master-data/location]], [[master-data/department]]
- [[inventory]] ต้องใช้ [[master-data/unit]], [[master-data/location]], [[master-data/business-unit]]
- [[inventory-adjustment]] ต้องใช้ [[master-data/unit]], [[master-data/location]], [[master-data/adjustment-type]], [[master-data/credit-note-reason]]
- [[physical-count]] ต้องใช้ [[master-data/location]], [[master-data/unit]], [[master-data/adjustment-type]]
- [[spot-check]] ต้องใช้ [[master-data/location]], [[master-data/adjustment-type]]
- [[costing]] ต้องใช้ [[master-data/business-unit]] (สำหรับ `calculation_method`), [[master-data/currency]] และ [[master-data/exchange-rate]] (สำหรับ FX revaluation แบบมีวันที่)
- [[vendor-pricelist]] ต้องใช้ [[master-data/vendor]], [[master-data/currency]], [[master-data/tax-profile]], [[templates/price-list]]
- [[product]] ต้องใช้ [[master-data/unit]], [[master-data/tax-profile]]
- [[recipe]] ต้องใช้ [[master-data/unit]]

## 5. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
- **carmen/docs:** `../carmen/docs/settings/locations.md` (อ้างอิงโดย [[master-data/location]] เท่านั้น)
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
