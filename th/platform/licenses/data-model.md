---
title: ไลเซนส์ — โมเดลข้อมูล (Data Model)
description: tb_cluster_license กับ view ใบที่ชนะของมัน, tb_business_unit_license กับ view ผลรวมของมัน, join ของ feature-group ใน tb_subscription, และเกณฑ์ใกล้หมดอายุที่ตั้งค่าได้สามค่า
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, licenses, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ไลเซนส์ — โมเดลข้อมูล (Data Model)

> **At a Glance**
> **บัญชีซื้อ:** `tb_cluster_license` (BU quota, ระดับ cluster, ยกเลิกได้) &nbsp;·&nbsp; `tb_business_unit_license` (seats, ระดับ BU, ยกเลิกไม่ได้) &nbsp;·&nbsp; **สัญญา:** `tb_subscription` (หนึ่งแถวต่อคู่ cluster+BU) → `tb_subscription_bu` → `tb_subscription_bu_group` (feature-group entitlement แทนที่ทั้งชุดทุกครั้งที่บันทึก) &nbsp;·&nbsp; **View:** `v_cluster_bu_cap` (หนึ่งแถวต่อ **cluster** — เพดานของใบที่ชนะ) กับ `v_cluster_bu_quota` (หนึ่งแถวต่อ **business unit** — อันดับ + เพดานที่ยืมมาจาก view แรก) เป็นสอง grain ที่ตอบคนละคำถาม อย่าเอามาปนกัน &nbsp;·&nbsp; `v_business_unit_seat` (หนึ่งแถวต่อ BU — ผลรวม ไม่ใช่ใบชนะใบเดียว) &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` บนทั้งสามตารางบัญชี/สัญญา ล็อกแบบ optimistic ทุกการเขียน &nbsp;·&nbsp; **เกณฑ์ใกล้หมดอายุ:** จำนวนวันตั้งค่าได้อิสระสามค่า (`subscription_days`, `bu_quota_days`, `seat_days`) ค่าเริ่มต้น 30 ทั้งหมด แก้ได้จาก Platform Config อ่านได้โดยไม่ต้องมีสิทธิ์

> **แหล่งความจริง:** Prisma schema ฝั่ง backend platform และ migration SQL ที่เขียนด้วยมือ อ่านไฟล์เหล่านี้ก่อนเสมอเมื่อจะเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql`, `20260824000000_add_cap_end_date_to_view/migration.sql`, `20260901020000_cluster_license_cancel/migration.sql`, `20260819000000_bu_user_license/migration.sql`, `20260821130000_subscription_one_bu/migration.sql`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่แหล่งความจริง ตรวจสอบแล้วกับ `carmen-turborepo-backend-v2` HEAD `50cce6953` (2026-09-06) และ `carmen-platform` HEAD `157a65e` (2026-09-04)

## 1. ภาพรวม

สามประเภทการซื้อ สามตาราง ไม่มีตารางแม่ร่วมกัน `tb_cluster_license` คือสิทธิ์ที่ cluster ซื้อไว้ในการสร้าง business unit ได้สูงสุด N หน่วยในช่วงวันที่หนึ่ง — เป็นบัญชีการซื้อล้วน ๆ "แถวไหนชนะตอนนี้" เป็นคำถามที่ฐานข้อมูลตอบด้วย view (§3) ไม่ใช่คอลัมน์บนตาราง `tb_business_unit_license` เป็นรูปแบบเดียวกันลงมาอีกชั้น: สิทธิ์ที่ business unit ซื้อไว้ในการเติมที่นั่งผู้ใช้ได้สูงสุด N ที่ในช่วงวันที่หนึ่ง แต่นับด้วยการ **บวกรวม** ทุกแถวที่ active อยู่ตอนนี้ แทนที่จะเลือกใบชนะใบเดียว (§3.2) — การซื้อที่นั่งสองก้อนพร้อมกันคือความจุที่บวกกันจริง ต่างจาก BU quota ที่การซื้อครั้งที่สองแทนที่ผลของครั้งแรกแทนที่จะบวกเพิ่ม `tb_subscription` เป็นเรคคอร์ดคนละแบบไปเลย: ไม่ใช่บัญชีความจุ แต่เป็นสัญญาเชิงพาณิชย์ระหว่าง cluster กับ business unit หนึ่งหน่วยที่เจาะจง จุดประสงค์เดียวในสคีมานี้คือผูกว่า **feature group** ไหน (นิยามโดย [License Catalog](/th/platform/license-catalog)) ที่สัญญาของ BU นั้นให้สิทธิ์ใช้

ทั้งสามตารางบัญชี/สัญญาพก audit trio, soft delete และตัวนับ `doc_version` แบบ optimistic-concurrency ที่บังคับใช้ทุกครั้งที่เขียน (`PATCH`/`PUT`/endpoint cancel ทุกตัวต้องส่งค่านี้มา และตอบ 409 ถ้าค่าเก่าไปแล้ว)

## 2. เอนทิตี

### 2.1 `tb_cluster_license` — บัญชีซื้อโควตา BU

ใบที่ซื้อไว้หนึ่งใบ ให้สิทธิ์ cluster สร้าง business unit ได้สูงสุด `licensed_bus` หน่วยในช่วง `[start_date, end_date)` schema บรรทัด 1168

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | Primary key, default `gen_random_uuid()` |
| `license_number` | `String @db.VarChar` | ไม่ | ระบบออกให้เป็น `BUQ-YYMM-####`; ไม่รับตอนสร้าง — client ไม่เคยส่งค่านี้มา unique ในหมู่แถวที่ยังไม่ถูกลบผ่าน partial unique index ที่ประกาศในราว SQL เท่านั้น (Prisma เขียน `WHERE` ใน `@@unique` ไม่ได้) |
| `cluster_id` | `String @db.Uuid` | ไม่ | FK ไปที่ `tb_cluster.id` — เจ้าของ |
| `licensed_bus` | `Int` | ไม่ | โควตาที่ใบนี้ให้; `CHECK (licensed_bus >= 0)` |
| `start_date` / `end_date` | `DateTime @db.Timestamptz(6)` | ไม่ | ช่วงคุ้มครอง; `CHECK (end_date > start_date)` การซื้อแบบ "ไม่มีวันหมดอายุ" เขียน sentinel `2099-12-31T23:59:59.999Z` ลงใน `end_date` — ไม่มีคอลัมน์ boolean แยกสำหรับ "perpetual" |
| `reference_no` | `String? @db.VarChar` | ใช่ | เลขอ้างอิงใบสั่งซื้อ (ข้อความอิสระ) |
| `note` | `String?` | ใช่ | ข้อความอิสระ — ยังใช้โดย data migration เพื่อบันทึกที่มาของตัวเลขที่ backfill มา |
| `cancelled_at` | `DateTime? @db.Timestamptz(6)` | ใช่ | เพิ่มโดย `20260901020000_cluster_license_cancel` ไม่เป็น null แปลว่าใบนี้ถูกยกเลิกแล้ว: ยังอยู่ในบัญชีและยังแสดงผล แต่หยุดให้โควตาตั้งแต่เวลานั้น **ไม่มีทางย้อนกลับ** — คืนความคุ้มครองต้องออกใบใหม่ |
| `cancelled_by_id` | `String? @db.Uuid` | ใช่ | ผู้ที่ยกเลิก |
| `cancel_reason` | `String?` | ใช่ | เหตุผล (ข้อความอิสระ, ไม่บังคับ) |
| `doc_version` | `Int` | ไม่ | Default `0`; ตัวนับ optimistic-lock บังคับส่งตอน `PATCH` และตอน `cancel` |
| audit trio + soft delete | — | ใช่ | `created_at`/`created_by_id`/`updated_at`/`updated_by_id`/`deleted_at`/`deleted_by_id` แบบมาตรฐาน |

**Constraint:** `CHECK (licensed_bus >= 0)`, `CHECK (end_date > start_date)`, FK `cluster_id → tb_cluster.id` (`NoAction`/`NoAction`)
**Index:** `(cluster_id, deleted_at)`, `(end_date)`, `(cluster_id, cancelled_at)` (เพิ่มมาพร้อมคอลัมน์ cancel — ใบที่ถูกยกเลิกไม่มีวันชนะอีก คิวรีหาใบที่ชนะจึงข้ามได้ทั้งหมดผ่าน index นี้)

ช่วงวันที่ทับซ้อนกันข้ามแถวเป็นเรื่องปกติ ไม่ใช่ข้อผิดพลาด — การซื้อโควตาเพิ่มกลางสัญญาคือแถวใหม่ที่ช่วงเวลาคาบเกี่ยวกับแถวเดิม (Swagger ของ backend ระบุไว้ตรง ๆ บน endpoint create/list)

### 2.2 `tb_business_unit_license` — บัญชีซื้อที่นั่ง

รูปแบบเดียวกัน ลงมาอีกชั้น schema บรรทัด 1133

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | Primary key |
| `license_number` | `String @db.VarChar` | ไม่ | ระบบออกให้เป็น `SEAT-YYMM-####`; ข้อจำกัด partial-unique-index เดียวกับ §2.1 |
| `business_unit_id` | `String @db.Uuid` | ไม่ | FK ไปที่ `tb_business_unit.id` — เจ้าของ |
| `licensed_users` | `Int` | ไม่ | จำนวนที่นั่งที่ใบนี้ให้; `CHECK (licensed_users >= 0)` |
| `start_date` / `end_date` | `DateTime @db.Timestamptz(6)` | ไม่ | ช่วงคุ้มครอง; `CHECK (end_date > start_date)` **ตารางนี้ไม่มีแนวคิด "ไม่มีวันหมดอายุ" ใน SPA เลย** — สวิตช์ no-expiry ของ `LicensePurchaseForm` ไม่มีให้สำหรับประเภทที่นั่ง (`SEAT_CONFIG.showNoExpiry: false`) |
| `reference_no` | `String? @db.VarChar` | ใช่ | เลขอ้างอิงใบสั่งซื้อ |
| `note` | `String?` | ใช่ | ข้อความอิสระ; แถวที่ migrate มาแล้วจะมี note ขึ้นต้นด้วย `"migrated"` ซึ่ง SPA อ่านค่านี้กลับมาแสดงเป็นป้ายเตือน "ต้องระบุวันหมดอายุ" |
| `doc_version` | `Int` | ไม่ | Default `0` |
| audit trio + soft delete | — | ใช่ | มาตรฐาน |

**Constraint:** `CHECK (licensed_users >= 0)`, `CHECK (end_date > start_date)`, FK `business_unit_id → tb_business_unit.id`
**Index:** `(business_unit_id, deleted_at)`, `(end_date)`

**ตารางนี้ไม่มีคอลัมน์ `cancelled_at`/`cancelled_by_id`/`cancel_reason` เลยสักคอลัมน์เดียว** ใบที่นั่งแก้ไขหรือลบทิ้งได้ (`DELETE`) แต่ยกเลิกไม่ได้เลย — ไม่มี endpoint cancel ทั้งฝั่ง frontend service และฝั่ง backend controller สำหรับตารางนี้ นี่คือช่องว่างความสามารถระหว่างสองประเภทการซื้อจริง ๆ ไม่ใช่ความผิดพลาดที่หน้านี้กำลังชี้ว่าเป็นบั๊ก — doc-comment ของ `licenseKindConfig.ts` เองระบุเหตุผลตรง ๆ ว่า `cancel` เป็น `null` สำหรับ `SEAT_CONFIG` เพราะการอ่านผ่าน union กับ `cancel` จริงของ `ClusterLicenseConfig` จะไม่ผ่าน type-check และการ cast ข้ามไปจะซ่อนการเรียกที่พังตอน runtime

### 2.3 `tb_subscription` และ join ของ feature-group

`tb_subscription` (schema บรรทัด 452) คือหัวสัญญา: `cluster_id`, `subscription_number` (ระบบออกให้เป็น `SUB-YYMM-####`), `start_date`/`end_date`, `status` (`enum_subscription_status`, บรรทัด 723: `active` / `inactive` / `expired`), `doc_version`, audit trio, soft delete `@@unique([cluster_id, subscription_number, deleted_at])`

นับตั้งแต่ migration `20260821130000_subscription_one_bu` สัญญาหนึ่งผูกกับ business unit **เพียงหน่วยเดียว** ผ่าน `tb_subscription_bu` (schema บรรทัด 1257: `subscription_id`, `business_unit_id`, `doc_version`, audit trio, soft delete; `@@unique([subscription_id, business_unit_id, deleted_at])`) — แก้ BU หลังสร้างไม่ได้ (ฟิลด์ `business_unit_id` ของ `SubscriptionForm` แก้ไขได้เฉพาะตอนฟอร์มสร้างเท่านั้น) ลูกของแถว join นั้น คือ `tb_subscription_bu_group` (schema บรรทัด 1336: `subscription_bu_id`, `group_id → tb_license_feature_group.id`, doc_version, audit trio, soft delete; `@@unique([subscription_bu_id, group_id, deleted_at])`) คือที่ที่ feature-group entitlement จริง ๆ อยู่ — นี่คือสิ่งที่ `PUT /subscriptions/:id/groups` แทนที่ทั้งชุดทุกครั้งที่บันทึก schema generation รุ่นก่อนหน้าเคยผูก subscription เข้ากับ feature รายตัวโดยตรงแทน (ถูกถอดโดย `20260901000000_drop_subscription_bu_feature`) ตารางนั้นไม่มีอยู่แล้ว และ UI ของโมดูลนี้ก็ไม่มีตัวเลือกรายฟีเจอร์แบบนั้นอีกต่อไป (§3.2 ของ [หน้าลงจอด](/th/platform/licenses))

`tb_license_feature_group` (schema บรรทัด 1284: `code`, `name`, `description`, `sort_order`, `is_active`, doc_version, audit trio, soft delete) และ `tb_license_feature` (schema บรรทัด 1214) เป็นของและเอกสารอยู่ที่ [License Catalog](/th/platform/license-catalog) — หน้านี้ระบุไว้แค่เพื่อให้เห็นว่า `tb_subscription_bu_group.group_id` ชี้ไปที่อะไร

## 3. View — สอง view ของความจุ และทำไมถึงมีสองตัว

ทั้งคู่นิยามอยู่ใน `20260822000000_add_cluster_license/migration.sql` (`v_cluster_bu_cap` บรรทัด 36, `v_cluster_bu_quota` บรรทัด 55) และแก้เพิ่มโดย `20260824000000_add_cap_end_date_to_view` (เพิ่ม `cap_end_date`) และ `20260901020000_cluster_license_cancel` (เพิ่ม `cancelled_at IS NULL` เข้าตัวกรองใบที่ชนะ บวกคอลัมน์ `winning_license_id`) ทั้งสอง view ตอบ **คำถามคนละคำถามที่คนละ grain** และหน้าที่อ้าง view ผิดตัวจะผิดแบบที่ดูสมเหตุสมผล:

### 3.1 `v_cluster_bu_cap` — หนึ่งแถวต่อ **cluster**

```sql
SELECT c.id AS cluster_id,
       COALESCE(w.licensed_bus, 0)::int AS cap,
       w.end_date                       AS cap_end_date,
       w.id                             AS winning_license_id
FROM tb_cluster c
LEFT JOIN LATERAL (
  SELECT l.id, l.licensed_bus, l.end_date
  FROM tb_cluster_license l
  WHERE l.cluster_id = c.id
    AND l.deleted_at IS NULL
    AND l.cancelled_at IS NULL
    AND l.start_date <= now()
    AND l.end_date > now()
  ORDER BY l.start_date DESC, l.created_at DESC, l.id DESC
  LIMIT 1
) w ON true
WHERE c.deleted_at IS NULL;
```

ทุก cluster ที่ยังอยู่ได้แถวเดียวเสมอ แม้ตัวที่ไม่มี business unit เลยและแม้ตัวที่ไม่มีใบเลย (`cap = 0` ผ่าน `COALESCE`) `LATERAL` join เลือกใบที่ **ชนะ** ใบเดียวที่คุ้มครอง `now()` — ทั้ง `deleted_at` และ (ตั้งแต่ 2026-09-01) `cancelled_at` ต้องเป็น `NULL` และในบรรดาผู้รอดชีวิต `start_date` ใหม่ที่สุดชนะ (เสมอกันแล้วตัดสินด้วย `created_at` แล้วค่อย `id`) นี่คือข้อเท็จจริง *ระดับ cluster*: "cluster นี้มี BU ได้กี่หน่วยตอนนี้ และจนถึงเมื่อไร" `activeLicense()` ฝั่ง frontend (`utils/clusterLicense.ts`) implement ลำดับ tie-break เดียวกันเป๊ะฝั่ง client สำหรับหน้าที่ถือแค่ลิสต์ใบ ไม่ใช่ผลลัพธ์ของ view นี้

### 3.2 `v_cluster_bu_quota` — หนึ่งแถวต่อ **business unit**

```sql
SELECT b.id         AS business_unit_id,
       b.cluster_id AS cluster_id,
       ROW_NUMBER() OVER (
         PARTITION BY b.cluster_id
         ORDER BY COALESCE(b.is_hq, false) DESC, b.created_at ASC, b.id ASC
       )::int       AS rank,
       q.cap        AS cap
FROM tb_business_unit b
JOIN v_cluster_bu_cap q ON q.cluster_id = b.cluster_id
WHERE b.deleted_at IS NULL;
```

นี่คือ **grain คนละแบบไปเลย**: หนึ่งแถวต่อ business unit ไม่ใช่ต่อ cluster มัน join กับ `v_cluster_bu_cap` เพื่อ **ยืม** เพดานมา — ไม่เคยคำนวณกติกาใบที่ชนะเองเลย — และจัดอันดับทุก BU ที่ยังอยู่ในคลัสเตอร์ของมัน (HQ ก่อน แล้วสร้างเก่าสุดก่อน) BU ที่ `rank` เกินเพดานที่ยืมมาคือ **เกินโควตาที่ซื้อไว้** นี่คือสิ่งที่ป้าย "Over limit" ของ SPA (`utils/businessUnitRank.ts`'s `rankBusinessUnits()`/`countOverLimit()`, ใช้โดยแท็บ Business Units ของ [Clusters](/th/platform/clusters) และ `BuQuotaSection` ของโมดูลนี้) ต้องตรงกันทุกอันดับ เพราะป้ายที่ไม่ตรงกับด่านจริง (BU ไหนถูกปฏิเสธจริงตอนสร้าง) แย่กว่าไม่มีป้ายเลย สูตรจัดอันดับถูกทำซ้ำฝั่ง client (แทนที่จะอ่านจาก view นี้ตรง ๆ) เพราะ SPA ต้องใช้กับลิสต์ BU ที่โหลดมาแล้วด้วยเหตุผลอื่น — แต่ใน source ระบุไว้ชัดว่าต้องตรงกับ `ORDER BY` ของ view นี้เป๊ะทุกฟิลด์

**ทำไมถึงมีสอง view แทนที่จะเป็นตัวเดียว:** `v_cluster_bu_cap` ตอบ "โควตาของ cluster คือเท่าไร" (ตัวเลขเดียว ใช้โดยหน้าจอของ cluster เองและโดยแถบสรุปบน `ClusterLicenseDetail`) `v_cluster_bu_quota` ตอบ "*BU ตัวนี้* อยู่ในโควตานั้นไหม" (หนึ่งแถวต่อ BU ใช้โดยหน้าจอที่แสดงรายการ business unit และอยากปักธง BU ที่เกินเส้น) การรวมทั้งสองเป็น view เดียวจะบังคับให้ทุกคิวรีที่แสดงรายการ BU ต้องพก column โควตาของ cluster ที่มันไม่ต้องการ และทุกคิวรีโควตาของ cluster ต้อง join ผ่าน BU ทุกหน่วยที่มันไม่สนใจเป็นรายตัว

### 3.3 `v_business_unit_seat` — หนึ่งแถวต่อ **business unit** แบบผลรวม

นิยามใน `20260819000000_bu_user_license/migration.sql` คู่กับ `tb_business_unit_license` เอง:

```sql
SELECT bu.id         AS business_unit_id,
       bu.cluster_id AS cluster_id,
       coalesce(sum(l.licensed_users) FILTER (
         WHERE l.deleted_at IS NULL
           AND now() >= l.start_date
           AND now() <= l.end_date
       ), 0)::int AS licensed_users
  FROM "tb_business_unit" bu
  LEFT JOIN "tb_business_unit_license" l ON l.business_unit_id = bu.id
 WHERE bu.is_active = true
   AND bu.deleted_at IS NULL
 GROUP BY bu.id, bu.cluster_id;
```

ต่างจาก view ของ cluster ทั้งสองตัวข้างบน view นี้ **บวกรวม** ทุกแถวที่ active อยู่ตอนนี้แทนที่จะเลือกผู้ชนะ — ตรงกับ `sumActiveLicenses()` ของ SPA (§3.1 ของ [หน้าลงจอด](/th/platform/licenses)) มีสองจุดที่ผู้ทดสอบควรสังเกต: การตรวจความคุ้มครองคือ `now() BETWEEN start_date AND end_date` แบบรวมทั้งสองขอบ (ไม่ใช่กติกา exclusive-end ที่คิวรีใบที่ชนะของ `tb_cluster_license` ใช้) และ view นี้กรอง `bu.is_active = true` — business unit ที่ถูกปิดใช้งานจะหายไปจาก view นี้ทั้งหมด แม้ใบของมันจะยังไม่หมดอายุก็ตาม `now()` ที่นี่หมายถึง `transaction_timestamp()` โดยตั้งใจ เพื่อให้ pool/used/already-invited ของคำขอเดียวมาจาก snapshot เดียวกันเสมอ

## 4. ความสัมพันธ์

```
tb_cluster_license.cluster_id            ──>  tb_cluster.id
tb_business_unit_license.business_unit_id ──>  tb_business_unit.id
tb_subscription.cluster_id                ──>  tb_cluster.id
tb_subscription_bu.subscription_id        ──>  tb_subscription.id
tb_subscription_bu.business_unit_id       ──>  tb_business_unit.id
tb_subscription_bu_group.subscription_bu_id ──>  tb_subscription_bu.id
tb_subscription_bu_group.group_id         ──>  tb_license_feature_group.id
*.created_by_id / *.updated_by_id / *.cancelled_by_id / *.deleted_by_id  ──>  tb_user.id  (audit actor)
```

`v_cluster_bu_cap` อ่านแค่ `tb_cluster` กับ `tb_cluster_license` `v_cluster_bu_quota` อ่านเพิ่ม `tb_business_unit` ผ่าน `v_cluster_bu_cap` ไม่ใช่ผ่าน `tb_cluster_license` ตรง ๆ (§3.2) `v_business_unit_seat` อ่านแค่ `tb_business_unit` กับ `tb_business_unit_license` ไม่มีตารางบัญชี/สัญญาตัวไหนใน §2 มี foreign key ชี้ไปหาอีกตัวเลย — โควตา BU ของ cluster, seat pool ของ BU, และสัญญา subscription ของ BU เป็นเรคคอร์ดการซื้อสามชุดที่เป็นอิสระจากกัน บังเอิญมาถูกเรียกดูร่วมกันบนหน้าจอของโมดูลนี้เท่านั้น

## 5. Enum

`enum_subscription_status` (`active` / `inactive` / `expired`) เป็น enum ตัวเดียวที่โมดูลนี้นิยาม และมัน **ไม่ใช่** สิ่งเดียวกับ `state` ที่ผู้เรียกเห็นจริง backend คำนวณ `state` ที่แสดงผล (`SubscriptionState`) จาก `status` บวกเวลาปัจจุบันผ่านฟังก์ชันเดียวที่ใช้ร่วมกัน `deriveSubscriptionState()` (`packages/prisma-shared-schema-platform/src/index.ts`) ใช้เหมือนกันทั้งใน gateway และ `micro-business`:

```
status inactive  → state = 'inactive'   (ตายตัว)
status expired   → state = 'expired'    (ตายตัว)
status active    → state = 'expired' ถ้า end_date < now, ไม่งั้น 'active'
```

SPA ถูกกำชับไม่ให้คำนวณสิ่งนี้เองอีก (doc-comment ของ `src/utils/subscriptionState.ts` เองอ้างโน้ตใน Swagger: "the frontend must not recompute this — use this field directly") มันคำนวณเองแค่ธง "expiring soon" ที่แยกออกไป (ไม่ใช่ enum) จาก `state` บวกเกณฑ์ (§6) เท่านั้น `tb_cluster_license` และ `tb_business_unit_license` ไม่มีคอลัมน์ status เลย สถานะของมัน (`active`/`scheduled`/`expired`/`superseded`/`cancelled`) คำนวณทั้งหมดฝั่ง client จากวันที่ และสำหรับ BU quota จาก `cancelled_at` กับการเทียบใบที่ชนะ (`licenseStatus()`/`statusMap()` ใน `utils/clusterLicense.ts` และ `utils/buLicense.ts`)

## 6. เกณฑ์ใกล้หมดอายุ

จำนวนวันที่ตั้งค่าได้จาก backend สามค่าที่เป็นอิสระต่อกัน ตัดสินว่าเมื่อไรหน้าจอของโมดูลนี้จะขึ้นคำเตือน "ใกล้หมดอายุ" — เป็นค่าที่ผู้ทดสอบเดาจากหน้าจอเองไม่ได้ เพราะข้อเท็จจริงเดียวกันคือ "หมดอายุในอีก 12 วัน" อ่านว่าเร่งด่วนที่เกณฑ์ 30 วัน แต่อ่านว่าธรรมดาที่เกณฑ์ 7 วัน

| ฟิลด์ (`ExpiryThresholdsConfig`) | ควบคุมอะไร | ค่าเริ่มต้น |
|---|---|---|
| `subscription_days` | ตัวนับ expiring-soon ของ `SubscriptionSection`, ป้ายต่อแถวของ `SubscriptionTable`, `IssuedSubscriptionPlate` | 30 |
| `bu_quota_days` | `BuQuotaSection`, ป้าย "Quota Expires" ของ `ClusterLicenseTable`, `IssuedLicensePlate` (โหมด BU-quota), `LicenseHealthStrip` | 30 |
| `seat_days` | ป้ายใกล้หมดอายุแรกสุดต่อแถวและต่อ BU ของ `SeatSection`, `IssuedLicensePlate` (โหมด seat) | 30 |

**แหล่งที่มาและการส่งค่า:** `GET /api-system/platform/expiry-thresholds` (`expiryThresholdService.getAll()`) จงใจ **เปิดให้ผู้ใช้ที่ล็อกอินแล้วทุกคนโดยไม่ต้องตรวจสิทธิ์** — ต่างจาก `platformConfigService.getAll()` ที่ต้องมี `platform_config.read` คอมเมนต์ใน `expiryThresholdService.ts` ระบุเหตุผลตรง ๆ: การกั้น endpoint นี้แบบเดียวกันจะ 403 ผู้ใช้ทั่วไปที่เปิด `/licenses` ทุกคน แล้วปักหมุดพวกเขาไว้ที่ค่าเริ่มต้นในโค้ดตลอดกาลโดยไม่สนใจว่าผู้ดูแลตั้งค่าอะไรไว้จริง ค่าทั้งสามเก็บเป็น JSON object เดียวใต้ key ของ `platform_config` (แก้ได้จากการ์ด Expiry Thresholds ของโมดูล [Platform Config](/th/platform/platform-config) กั้นด้วย `platform_config.manage` เพียงอย่างเดียว — **ไม่ใช่** `license.manage` ซึ่งเป็นคีย์คนละตัวที่กั้นสวิตช์ License Enforcement ที่ไม่เกี่ยวข้องกันบนหน้าจอเดียวกัน; ดูคำแก้ไขใน [Permissions](/th/platform/licenses/permissions) §1) และถูก serve ผ่าน `ExpiryThresholdContext` ซึ่ง merge คำตอบจาก backend ลงบน `DEFAULT_EXPIRY_THRESHOLDS` **ทีละฟิลด์** — backend ที่ยังไม่รู้จักฟิลด์ใหม่จะไม่ทำให้ฟิลด์นั้นกลายเป็น `undefined` แล้วพังเงียบ ๆ ทุกการเปรียบเทียบ (operand ที่เป็น `undefined` ทำให้การเทียบ `<=` ทุกครั้งเป็น `false` ซึ่งจะทำให้ป้ายเตือนหายไปทั้งระบบโดยไม่มี error ให้เห็น) คำขอที่ล้มเหลว (รวมถึง "ยังไม่ล็อกอิน") ตกกลับไปใช้ค่าเริ่มต้นในโค้ดอย่างเงียบ ๆ (ทั้งสามค่า `30`) โดยไม่มี toast — หน้ายังทำงานได้ปกติ แค่หน้าต่างของป้ายเตือนย้อนกลับไปเป็นค่าเก่า

**ผลกระทบต่อแต่ละบัญชี ให้ชัดเจน:**
- **Subscription:** `isExpiringSoon(state, endDate, days)` — เป็น `true` เฉพาะเมื่อ `state` ที่ backend คำนวณมาเป็น `'active'` **และ** `daysLeft <= days` เท่านั้น `state` ที่เป็น `'inactive'` หรือ `'expired'` ไปแล้วไม่มีวันอ่านว่า "expiring soon"
- **BU quota:** `isExpiringSoon(lic, days)` — เป็น `false` เสมอสำหรับใบ perpetual (`end_date >= 2099-01-01`) และสำหรับใบที่ไม่ `'active'` ตาม `licenseStatus()` ตอนนี้ (ใบที่ยกเลิกหรือถูกแทนที่ไม่มีวัน "ใกล้หมดอายุ" มันตายไปแล้ว)
- **Seat:** `isExpiringSoon(lic, days)` — เป็น `false` สำหรับใบที่ไม่ `'active'`; ที่นั่งไม่มีแนวคิด perpetual เลย (§2.2) ดังนั้นใบที่นั่งที่ active ทุกใบมีสิทธิ์เตือนได้ในที่สุด

## 7. ความแตกต่างจาก shape ของ carmen-platform SPA

| Shape ของ SPA | แหล่งที่มาใน SPA | การเก็บใน Prisma | หมายเหตุ |
| --------- | ---------- | -------------- | ----- |
| `LicenseKindConfig.readUsage` คืน `undefined` | `licenseKindConfig.ts` | ไม่มี | `undefined` แปลว่า "ไม่รู้" (ยังไม่ได้ลองอ่านหรืออ่านล้มเหลว); `readUsage` ของประเภทที่นั่งเป็น `null` ตรง ๆ แปลว่าแนวคิดนี้ไม่มีผลกับมันเลย ผู้เรียกต้องไม่แปลงทั้งสองเป็น `0` — ใบที่นั่งไม่มีตัวหารที่มาจากเจ้าของเลย และใบ BU-quota ที่อ่านการใช้งานล้มเหลวไม่ใช่ข้อเท็จจริงเดียวกับ cluster ที่ใช้ BU ไปศูนย์หน่วย |
| `ClusterLicense.is_in_force` | `utils/clusterLicense.ts` `statusMap()` | ไม่ได้เก็บ — คำนวณโดย `winning_license_id` ของ `v_cluster_bu_cap` บน endpoint list/detail ที่ join view นี้ | เชื่อก่อน `activeLicense()` ของ client เสมอเมื่อมีค่านี้ส่งมา; สูตร client มีไว้เป็น fallback สำหรับ load path เดียว (`GET .../licenses` รายคลัสเตอร์) ที่ DTO ยังเก่ากว่าฟิลด์นี้ |
| `FleetLicenseRow` (row shape ของ `PurchaseLicenseTable` ทั้ง fleet) ไม่มี `updated_at` | `PurchaseLicenseTable.tsx` | ทั้ง `BusinessUnitLicenseListRowDto` และ `ClusterLicenseListRowDto` ไม่ส่งค่านี้มาเลย | ไม่ใช่บั๊กที่ต้องแก้ — DTO ของ fleet-list ทั้งสองไม่เคย project `updated_at` เลย CSV export กับคอลัมน์ audit เดียวของตารางนี้จึงโชว์แค่ Created ไม่มี Updated เฉพาะหน้าจอนี้ |
| `group_ids` / `feature_keys` บน `SubscriptionDetail.bu` | `SubscriptionForm.tsx` `load()` | `tb_subscription_bu_group` (join) / การรวมค่าที่ server คำนวณ | `group_ids` อ่านเป็น optional และตกกลับเป็น `[]` — สัญญาที่สร้างก่อนระบบกลุ่มมีอยู่จริงพก `feature_keys` โดยไม่มี `group_ids` และ SPA ต้องไม่ crash ตอนอ่านฟิลด์ที่แถวยุค pre-migration ไม่เคยมี |
| การ merge ของ `ExpiryThresholdsConfig` | `ExpiryThresholdContext.tsx` | ค่า JSON เดียวบนแถว `platform_config` (เป็นของ [Platform Config](/th/platform/platform-config)) | Merge ทีละฟิลด์ลงบนค่าเริ่มต้นในโค้ด ไม่ใช่แทนที่ทั้งก้อน (§6) |

## 8. แหล่งข้อมูลอ้างอิง

REST surface ที่ service ของโมดูลนี้ใช้:

| Method + Path | จุดประสงค์ | หมายเหตุ |
|---|---|---|
| `GET /api-system/clusters/:clusterId/licenses` | รายการใบ BU-quota ของ cluster เดียว | ไม่มี `@RequirePlatformPermission` — ตรวจ scope ภายใน `micro-cluster` |
| `GET /api-system/platform/cluster-licenses` | รายการใบ BU-quota ทั้ง fleet, paginated | ไม่มี `@RequirePlatformPermission`; กรองตาม scope ของผู้เรียก |
| `GET /api-system/platform/cluster-licenses/:id` | ใบ BU-quota หนึ่งใบจาก id ล้วน | ตอบ **403** (ไม่ใช่ 404) เมื่ออยู่นอก scope cluster ที่ผู้เรียกอ่านได้ |
| `POST/PATCH/DELETE /api-system/clusters/:clusterId/licenses[/:id]` | สร้าง/แก้/soft-delete ใบ BU-quota | ทั้งสามต้องมี `subscription.manage` |
| `POST /api-system/clusters/:clusterId/licenses/:id/cancel` | ยกเลิกใบ BU-quota | ต้องมี `subscription.manage`; ย้อนกลับไม่ได้; ต้องส่ง `doc_version` |
| `GET /api-system/business-units/:buId/licenses` | รายการใบที่นั่งของ BU เดียว | ไม่มี `@RequirePlatformPermission` |
| `GET /api-system/platform/business-unit-licenses[/:id]` | รายการใบที่นั่งทั้ง fleet / หนึ่งใบจาก id ล้วน | กติกา scope เดียวกับ fleet route ของ cluster-licence |
| `POST/PATCH/DELETE /api-system/business-units/:buId/licenses[/:id]` | สร้าง/แก้/soft-delete ใบที่นั่ง | ทั้งสามต้องมี `subscription.manage`; **ไม่มี route cancel สำหรับที่นั่งเลย** |
| `GET/POST/PATCH/DELETE /api-system/platform/subscriptions[/:id]` | CRUD ของ subscription | `GET` ต้องมี `subscription.read`; verb เขียนต้องมี `subscription.manage` |
| `PUT /api-system/platform/subscriptions/:id/groups` | แทนที่ชุด feature-group ของสัญญา | ต้องมี `subscription.manage`; ส่งชุดที่ต้องการทั้งหมด ไม่ใช่ diff |
| `GET /api-system/platform/subscriptions/summary` | ยอดรวม subscription ทั้ง fleet แบบไม่กรอง | ต้องมี `subscription.read`; เป็นอิสระจาก filter ของ list ปัจจุบัน |
| `GET /api-system/platform/license-features` | catalog ของ feature (อ่านอย่างเดียว สำหรับการกางแสดงผลของ SPA) | เป็นของ [License Catalog](/th/platform/license-catalog) |
| `GET /api-system/platform/expiry-thresholds` | จำนวนวันตั้งค่าได้สามค่า (§6) | ไม่ต้องมีสิทธิ์ |

**หลัก (แหล่งความจริง):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_subscription` (452), `enum_subscription_status` (723), `tb_business_unit_license` (1133), `tb_cluster_license` (1168), `tb_license_feature` (1214), `tb_subscription_bu` (1257), `tb_license_feature_group` (1284), `tb_subscription_bu_group` (1336)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260819000000_bu_user_license/migration.sql` — `tb_business_unit_license`, `v_business_unit_seat`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql` (บรรทัด 36, 55), `20260824000000_add_cap_end_date_to_view/migration.sql`, `20260901020000_cluster_license_cancel/migration.sql` — `tb_cluster_license`, `v_cluster_bu_cap`, `v_cluster_bu_quota`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260821130000_subscription_one_bu/migration.sql`, `20260831000000_subscription_bu_group/migration.sql`, `20260901000000_drop_subscription_bu_feature/migration.sql` — โมเดลหนึ่ง-BU-ต่อหนึ่ง-subscription และการย้าย feature→group ของ entitlement
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/src/index.ts` — `deriveSubscriptionState()` ฟังก์ชันคำนวณ `state` ตัวเดียวที่ใช้ร่วมกัน (§5)

**รอง (shape ฝั่งผู้บริโภค):**
- `../carmen-platform/src/pages/licenses/licenseKindConfig.ts` — `SEAT_CONFIG`/`BU_QUOTA_CONFIG`
- `../carmen-platform/src/utils/clusterLicense.ts`, `src/utils/buLicense.ts`, `src/utils/subscriptionState.ts` — สามสูตร status/expiring-soon ที่เป็นอิสระต่อกัน
- `../carmen-platform/src/utils/businessUnitRank.ts` — `rankBusinessUnits()`/`countOverLimit()` ต้องตรงกับ `ORDER BY` ของ `v_cluster_bu_quota` เป๊ะ
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx`, `src/services/expiryThresholdService.ts` — การส่งค่าเกณฑ์ (§6)
- `../carmen-platform/src/types/index.ts` — `ClusterLicense`, `BusinessUnitLicense`, `Subscription`, `SubscriptionDetail`, `ExpiryThresholdsConfig`

**ลิงก์ข้าม:** [หน้าลงจอด Licenses](/th/platform/licenses) &nbsp;·&nbsp; [UI Screens](/th/platform/licenses/ui-screens) &nbsp;·&nbsp; [Permissions](/th/platform/licenses/permissions) &nbsp;·&nbsp; [License Catalog](/th/platform/license-catalog) &nbsp;·&nbsp; [Platform Config](/th/platform/platform-config)
