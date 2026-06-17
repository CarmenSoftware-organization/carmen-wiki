---
title: หมวดหมู่สินค้า (Product Category)
description: taxonomy สินค้าสามระดับ (หมวดหมู่ > หมวดหมู่ย่อย > กลุ่มสินค้า) ขับเคลื่อนการนำทางแคตตาล็อก การสืบทอดคุณสมบัติ ค่าความคลาดเคลื่อน และ permission filter ตามหมวดหมู่
published: true
date: 2026-05-19T23:55:00.000Z
tags: product, category, taxonomy, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# หมวดหมู่สินค้า (Product Category)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_product_category` → `tb_product_sub_category` → `tb_product_item_group` (**3 ระดับคงที่** ไม่ใช่ self-referential) &nbsp;·&nbsp; **Trigger:** การดูแล taxonomy &nbsp;·&nbsp; **ใช้โดย:** PR / PO / GRN / recipe / รายงาน / การกำหนดสิทธิ์ &nbsp;·&nbsp; **สรุป 1 บรรทัด:** ชั้นการจำแนกประเภทที่ขับเคลื่อนการนำทาง ค่า default ที่สืบทอดมา และค่าความคลาดเคลื่อน

![หมวดหมู่สินค้า (Product Category) screen](/screenshots/product/category.png)

## 1. คืออะไรและใครใช้

หมวดหมู่สินค้าคือชั้นการจำแนกประเภทเหนือข้อมูลหลักของสินค้า สินค้าทุกตัวมี triple `(category, sub_category, item_group)` ซึ่งขับเคลื่อน:

1. **การนำทางแคตตาล็อก** — ผู้ใช้เจาะลึก `Food > Beverage > Coffee Beans` แทนที่จะเลื่อน
2. **การสืบทอดคุณสมบัติ** — tax profile, ค่าความคลาดเคลื่อน, `is_used_in_recipe`, `is_sold_directly` เป็นค่า default ลงตามต้นไม้
3. **การ roll-up รายงานต้นทุน / การสูญเสีย** — food cost, wastage, ความแปรปรวน group ตามหมวดหมู่ทุกระดับ
4. **การกำหนดขอบเขตสิทธิ์** — Purchaser และ Store Keeper สามารถถูกจำกัดให้อยู่ในกิ่งหมวดหมู่

ดูแลโดย persona **Product Admin** อ้างอิงด้วย `category_id` บนทุกแถว `tb_product`

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มหมวดหมู่ระดับบนสุด | Product Management → Category → **New** | `code` ต้องไม่ซ้ำในแถวที่ไม่ถูกลบ |
| เพิ่มหมวดหมู่ย่อย | เปิดหมวดหมู่ → **Add sub-category** | ตั้ง FK `product_category_id` เป็น parent |
| เพิ่มกลุ่มสินค้า (ใบไม้) | เปิดหมวดหมู่ย่อย → **Add item group** | ตั้ง FK `product_subcategory_id` เป็น parent |
| ตั้งค่าความคลาดเคลื่อนของราคา | แก้ระดับใดก็ได้ → `price_deviation_limit` | % cap ของราคา PO เทียบกับราคาหลัก/รับล่าสุด ระดับที่ละเอียดที่สุดชนะ |
| ตั้งค่าความคลาดเคลื่อนของปริมาณ | แก้ระดับใดก็ได้ → `qty_deviation_limit` | % cap ของปริมาณ GRN เทียบกับปริมาณ PO ระดับที่ละเอียดที่สุดชนะ |
| Override tax profile | แก้ระดับใดก็ได้ → `tax_profile_id` / `tax_rate` | กระทบสินค้าใหม่เท่านั้น — สินค้าเดิมเก็บการตั้งค่าที่ snapshot แล้ว |
| toggle `is_used_in_recipe` / `is_sold_directly` | ฟิลด์ flag บนระดับใดก็ได้ | ใช้โดย recipe builder และ POS picker |
| inactivate ใบไม้ | แก้กลุ่มสินค้า → `is_active = false` | ซ่อนจาก picker สินค้าใหม่ สินค้าในประวัติยังแสดง |
| Soft-delete ระดับใดก็ได้ | action **Delete** | บล็อกในขณะที่ยังมี `tb_product` ที่ active อ้างอิงแถว (บังคับใช้ที่ application) |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| "Code already exists" บนหมวดหมู่ | `tb_product_category.code` ไม่ซ้ำในแถวที่ไม่ถูกลบ | เลือก code อื่น หรือ restore แถวที่ soft-delete |
| "Cannot delete — products still reference this" | มีแถว `tb_product` ที่ active ชี้มาที่นี่ | ย้ายสินค้าก่อน แล้วลองใหม่ |
| "Cannot re-parent sub-category" | FK บน `product_subcategory_id` เป็น `NoAction` สินค้าอ้างอิงกลุ่มสินค้าของมัน | ต้อง migrate ข้อมูลด้วยมือ — ไม่ใช่ action ของ UI |
| การเปลี่ยนภาษีไม่สะท้อนบนสินค้าเดิม | tax profile snapshot ตอน save สินค้า | save สินค้าใหม่เพื่อรับค่า default ใหม่ |
| `price_deviation_limit = 0` ไม่บล็อก 0% deviation | `0` หมายถึง "ไม่ได้ตั้งค่าความคลาดเคลื่อน" — fallback ไปที่ค่า default ของ app | ตั้ง `%` บวกเพื่อบังคับ cap จริง |
| ความตั้งใจของลำดับชั้น vs schema | carmen/docs อธิบาย "ลึกได้ถึง 5 ระดับ" schema บังคับ 3 | schema เป็นแหล่งความจริง — 3 ระดับคงที่ (Inferred) |

## 4. Edge Cases

- **3 ระดับคงที่ ไม่ใช่ self-referential** แต่ละระดับมีตารางของตัวเองพร้อม FK ชี้ไปยัง parent — **ไม่มีคอลัมน์ `parent_id` แบบ recursive** เครื่องมือที่สันนิษฐานว่าเป็นต้นไม้ self-referential จะใช้ไม่ได้
- **การสืบทอดคือ `item_group ?? sub_category ?? category ?? app default`** — ระดับที่ละเอียดที่สุดชนะ คำนวณตอน save สินค้า
- **บล็อกการ re-parent** เมื่อสินค้าอ้างอิงกลุ่มสินค้าแล้ว ไม่สามารถย้ายหมวดหมู่ย่อยไปยังหมวดหมู่อื่นได้ — FK `NoAction`
- **Tax profile snapshot** การเปลี่ยน `tax_profile_id` บนหมวดหมู่กระทบเฉพาะสินค้าใหม่ สินค้าเดิมเก็บการตั้งค่าที่ snapshot แล้วจนกว่าจะ save ใหม่
- **ขอบเขตของ code** code ของหมวดหมู่ย่อยและกลุ่มสินค้าไม่ซ้ำภายใน parent (composite `(code, name, deleted_at)`) ไม่ใช่ทั่วโลก
- **ค่าความคลาดเคลื่อน `0`** หมายถึง "ไม่ได้ตั้งค่า" — fallback ไปที่ค่า default ของ application แทนที่จะบล็อก 0% deviation

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema **taxonomy คือสามระดับคงที่** — แต่ละระดับเป็นตารางแยกพร้อม FK ไปยัง parent ไม่ใช่ต้นไม้ self-referential ตัวเดียว

### 5.1 `tb_product_category` (ระดับ 1)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | code สั้น (เช่น `FOOD`, `BEV`, `SUPP`) |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `description` | `String? @db.VarChar` | Yes | ข้อความอิสระ |
| `is_active` | `Boolean?` | Yes | default `true` |
| `price_deviation_limit` | `Decimal(20,5)?` | Yes | % สูงสุดของการเบี่ยงเบนราคา PO (default `0`) |
| `qty_deviation_limit` | `Decimal(20,5)?` | Yes | % สูงสุดของการเบี่ยงเบนปริมาณ GRN จาก PO (default `0`) |
| `is_used_in_recipe` | `Boolean?` | Yes | default ที่สืบทอด (default `true`) |
| `is_sold_directly` | `Boolean?` | Yes | default ที่สืบทอด (default `false`) |
| `tax_profile_id` / `tax_rate` | mixed | Yes | การตั้งค่าภาษี default |
| `note`, `info`, `dimension` | — | Yes | metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, deleted_at])`, `@@unique([code, name, deleted_at])` reverse relation ไปยัง `tb_product_sub_category`, `tb_product_category_comment`, `tb_tax_profile`

### 5.2 `tb_product_sub_category` (ระดับ 2)

| ฟิลด์ | Prisma Type | คำอธิบาย |
|---|---|---|
| `id` | `String @db.Uuid` | Primary key |
| `product_category_id` | `String @db.Uuid` | **FK ไปยัง `tb_product_category`** — parent ในลำดับชั้น |
| `code`, `name`, `description` | `String` | การระบุ |
| `price_deviation_limit` / `qty_deviation_limit` | `Decimal(20,5)?` | Override parent |
| `is_used_in_recipe` / `is_sold_directly` / `is_active` | `Boolean?` | flag overrides |
| `tax_profile_id` / `tax_rate` | mixed | Override ภาษี |
| Audit columns | — | มาตรฐาน |

**Constraints:** `@@unique([code, name, deleted_at])` reverse relation ไปยัง `tb_product_item_group`

### 5.3 `tb_product_item_group` (ระดับ 3 — ใบไม้)

| ฟิลด์ | Prisma Type | คำอธิบาย |
|---|---|---|
| `id` | `String @db.Uuid` | Primary key |
| `product_subcategory_id` | `String @db.Uuid` | **FK ไปยัง `tb_product_sub_category`** — parent |
| `code`, `name`, `description` | `String` | การระบุ |
| `price_deviation_limit` / `qty_deviation_limit` / `is_*` / `tax_*` | mixed | รูปทรงเดียวกับ parent override ระดับละเอียดสุด |
| Audit columns | — | มาตรฐาน |

แต่ละระดับยังมีตาราง `*_comment` สำหรับการอภิปรายและไฟล์แนบ

> **ความลึกของลำดับชั้น** schema กำหนดต้นไม้ไว้ที่สามระดับเป๊ะ ๆ `../carmen/docs/product-management/PROD-Overview.md` อธิบาย "ลึกได้ถึงห้าระดับ" เป็นความตั้งใจ Prisma schema ปัจจุบันบังคับสาม (Inferred — schema เป็นแหล่งความจริง)

## 6. วงจรชีวิต / กติกาทางธุรกิจ

```
1. Product Admin สร้างหมวดหมู่ (code + name ไม่ซ้ำ)
2. เพิ่มหมวดหมู่ย่อยใต้มัน เพิ่มกลุ่มสินค้าใต้หมวดหมู่ย่อยแต่ละตัว
3. ค่า default (tax, ค่าความคลาดเคลื่อน, is_used_in_recipe, is_sold_directly)
   cascade ลงตอน INSERT สามารถ override ที่ระดับใดก็ได้
4. tb_product แต่ละแถวอ้างอิง triple (category, sub_category, item_group)
5. การ deactivate (is_active = false) ซ่อนจาก picker สินค้าใหม่
   สินค้าในประวัติยังแสดง Soft-delete ถูก BLOCK ในขณะที่
   tb_product ยังอ้างอิงแถว (บังคับใช้ที่ application FK = NoAction)
```

- **ความไม่ซ้ำของ code** code หมวดหมู่ไม่ซ้ำในแถวที่ไม่ถูกลบ code หมวดหมู่ย่อย / กลุ่มสินค้าไม่ซ้ำภายใน parent
- **ความสมบูรณ์ของลำดับชั้น** หมวดหมู่ย่อยไม่สามารถ re-parent เมื่อกลุ่มสินค้ามีสินค้าแล้ว — FK `NoAction`
- **การเปลี่ยนภาษี** กระทบสินค้าใหม่เท่านั้น สินค้าเดิมเก็บการตั้งค่าที่ snapshot แล้วจนกว่าจะ save ใหม่
- **ค่าความคลาดเคลื่อน** เปอร์เซ็นต์ 0-100 `0` = "ไม่ได้ตั้งค่าความคลาดเคลื่อน" → fallback ไปที่ค่า default ของ app

## 7. Cross-References

- [product](/th/inventory/product) — สินค้าทุกตัวมี triple `(category, sub_category, item_group)`
- [product/03-user-flow-product-admin](/th/inventory/product/03-user-flow-product-admin) — Product Admin ดูแลต้นไม้
- [purchase-request](/th/inventory/purchase-request) &nbsp;·&nbsp; [purchase-order](/th/inventory/purchase-order) (`price_deviation_limit`) &nbsp;·&nbsp; [good-receive-note](/th/inventory/good-receive-note) (`qty_deviation_limit`)
- [recipe](/th/inventory/recipe) — filter `is_used_in_recipe`
- [access-control/permission](/th/inventory/access-control/permission) — filter ตามหมวดหมู่สำหรับ Purchaser / Store Keeper
- [master-data/tax-profile](/th/inventory/master-data/tax-profile) — การ cascade `tax_profile_id`

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_category` (~1566-1602), `tb_product_sub_category` (~1711-1748), `tb_product_item_group` (~1638-1675), `tb_product_category_comment` (~1604-1636)
- **Frontend:** `../carmen-inventory-frontend-react/routes/product-management/category/`
- **carmen/docs:** `../carmen/docs/product-management/PROD-API-Endpoints-Categories.md`; `../carmen/docs/product-management/PROD-Overview.md`
- **Module landing:** [product](/th/inventory/product) § 3 (แนวคิดสำคัญ Product Category)
