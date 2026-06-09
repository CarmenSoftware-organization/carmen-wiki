---
title: เวอร์ชันเอกสาร (Optimistic Concurrency)
description: ฟิลด์ doc_version (integer) ที่ป้องกันการเขียนทับข้อมูลในเอกสาร — ไคลเอนต์ต้องส่งค่าเวอร์ชันปัจจุบันกลับมาพร้อมการบันทึก มิฉะนั้นจะได้รับ 409 Conflict
published: true
date: 2026-06-09T00:00:00.000Z
tags: system-config, concurrency, doc-version, optimistic-lock, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# เวอร์ชันเอกสาร (Optimistic Concurrency)

> **สรุปโดยย่อ**
> **ฟิลด์:** `doc_version` (integer) ในเพย์โหลดการอัปเดตของเอกสาร &nbsp;·&nbsp; **ป้องกัน:** การเขียนทับข้อมูลจากการแก้ไขพร้อมกัน &nbsp;·&nbsp; **เมื่อค่าไม่ตรง:** **409 Conflict** &nbsp;·&nbsp; **ใช้กับ:** ~20 entities สำหรับธุรกรรมและการกำหนดค่า (ดู §3) &nbsp;·&nbsp; **ไม่ใช่** ตัวนับการเรนเดอร์ไฟล์แนบ (ดู §5)

## 1. คืออะไรและใครใช้

`doc_version` คือกลไก **optimistic-concurrency**: เป็น integer ที่เพิ่มขึ้นเรื่อย ๆ ซึ่งเก็บไว้ที่ aggregate root ของเอกสาร การอ่านทุกครั้งจะคืนค่า `doc_version` ปัจจุบัน และทุกการ **อัปเดตต้องส่งค่าเวอร์ชันที่ไคลเอนต์ได้รับมาล่าสุด** เซิร์ฟเวอร์จะเขียนข้อมูลก็ต่อเมื่อค่าเวอร์ชันที่ส่งมายังตรงกับค่าที่จัดเก็บอยู่ — แล้วจึงเพิ่มค่าเวอร์ชัน หากผู้ใช้สองคนเปิดเอกสารเดียวกันและบันทึกพร้อมกัน การบันทึกครั้งที่สองจะล้มเหลวแทนที่จะเขียนทับข้อมูลโดยไม่แจ้งเตือน

กลไกนี้เป็น *optimistic*: ไม่มีการล็อกแถวข้อมูลขณะที่ผู้ใช้กำลังแก้ไข ความขัดแย้งจะถูกตรวจพบเมื่อบันทึก ไม่ใช่การป้องกันล่วงหน้า ซึ่งเหมาะกับการแก้ไขเอกสารที่ใช้เวลานานและความขัดแย้งเกิดขึ้นน้อย แต่มีผลกระทบมากหากเกิดขึ้น

**ตั้งค่าโดย** path การอัปเดตของทุก service (เปิดตัวพร้อมกันทั่ว backend เมื่อ 2026-06-04) **ตรวจสอบโดย** update handler เดียวกัน **แสดงต่อ** ไคลเอนต์ในรูปแบบ `409 Conflict` ที่ต้องจัดการ

## 2. พฤติกรรม

```
function update(id, payload):
    current = load(id)                       # current.doc_version = N
    if payload.doc_version != current.doc_version:
        raise Conflict(409)                  # someone saved first
    apply(payload)
    current.doc_version = N + 1              # bump on success
    save(current)
    return current                           # client reads back N+1
```

ไคลเอนต์ต้องส่งค่า `doc_version` ที่ได้รับจากการอ่านครั้งล่าสุด หลังจากบันทึกสำเร็จ ต้องใช้ค่าเวอร์ชันที่เพิ่มขึ้นซึ่งส่งกลับมาสำหรับการแก้ไขครั้งถัดไป

## 3. Entities ที่มีฟิลด์นี้

| กลุ่ม | Entities |
|---|---|
| การจัดซื้อ | purchase-request, purchase-order, purchase-request-template, request-for-pricing, credit-note |
| การรับสินค้าและสต็อก | good-received-note, stock-in, stock-out |
| การนับ | spot-check |
| การเบิกวัสดุ | store-requisition |
| ราคา | pricelist, pricelist-template |
| Config masters | credit-term, extra-cost-type, running-code, vendor-business-type, recipe-category, recipe-cuisine, recipe-equipment, recipe-equipment-category |

## 4. สถานการณ์ทดสอบ

| # | สถานการณ์เริ่มต้น | การกระทำ | ผลที่คาดหวัง |
|---|---|---|---|
| 1 | ไคลเอนต์ A และ B ทั้งคู่โหลดเอกสารที่ `doc_version = 5` | A บันทึกการเปลี่ยนแปลง | A สำเร็จ; เอกสารเป็น `doc_version = 6` |
| 2 | ต่อจาก #1 | B บันทึกการเปลี่ยนแปลง โดยยังส่ง `doc_version = 5` | **409 Conflict**; การเขียนของ B ถูกปฏิเสธ ไม่มีข้อมูลสูญหาย |
| 3 | ต่อจาก #2 | B ดึงข้อมูลใหม่ (ได้ `doc_version = 6`) นำการแก้ไขมาใส่ใหม่ แล้วบันทึกด้วยค่า `6` | B สำเร็จ; เอกสารเป็น `doc_version = 7` |
| 4 | ไคลเอนต์เดียว | อัปเดตโดยไม่มี `doc_version` หรือส่งค่าเก่า | ถูกปฏิเสธ — ฟิลด์นี้จำเป็นสำหรับ compare-and-set |

## 5. อย่าสับสนกับ

`tb_attachment.doc_version` เป็น **ฟิลด์คนละตัวที่มีความหมายต่างกัน** — มันคือ *ตัวนับการเรนเดอร์ใหม่* สำหรับเอกสารที่สร้างใหม่ (เช่น PDF ที่พิมพ์ซ้ำ) ซึ่งเพิ่มค่าทุกครั้งที่โมดูลเจ้าของสร้างไฟล์ใหม่ และเก็บเวอร์ชันเก่าไว้เพื่อการตรวจสอบ มันไม่ใช่กลไกป้องกันการเขียนพร้อมกัน ดู [reporting-audit/attachment](/th/inventory/reporting-audit/attachment).
