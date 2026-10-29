---
title: Tenant Seed (ข้อมูลเริ่มต้นของ Tenant)
description: หน้าจอระดับ fleet ที่ตรวจว่าฐานข้อมูลของ business unit ใดขาดข้อมูล seed พื้นฐาน (running code, template, adjustment type ฯลฯ) และเติมส่วนที่ขาดด้วยการ stream การรัน seed ราย BU
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, tenant-seed
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Tenant Seed (ข้อมูลเริ่มต้นของ Tenant)

business unit ทุกแห่งมีฐานข้อมูล tenant ของตัวเอง tenant ที่เพิ่งสร้างหรืออยู่มานานอาจขาด row พื้นฐานที่แอปพลิเคชัน inventory สมมติว่ามีอยู่: รูปแบบ running code ของเอกสาร, vendor business type, prefix ของ GL journal, notification template, adjustment type และอื่น ๆ **Tenant Seed** คือคอนโซลที่หาช่องว่างเหล่านั้นทั่วทั้ง fleet และเติมให้ โดยสร้างเฉพาะที่ขาด ไม่แตะ row ที่มีอยู่แล้ว มันเป็นคู่ฝั่งข้อมูลของ [Tenant Migrations](/th/backstage/tenant-migrations) ซึ่งดูแลการเปลี่ยน schema

> **At a Glance**
> **หน้าจอ:** `TenantSeedManagement` (+ `SeedFleetSummary`, `SeedSetPickerDialog`) ที่ `/tenant-seeds` &nbsp;·&nbsp; **Nav:** กลุ่ม Organization, เป็นลูกของ Business Units (`parentPath: '/business-units'`), `permission: 'tenant_seed.read'`, `feature: 'tenant_seeds'` (`backstageNav.ts:18`) &nbsp;·&nbsp; **Permission key:** `tenant_seed.read` (สถานะ), `tenant_seed.apply` (seed) &nbsp;·&nbsp; **API:** `GET /api-system/tenant/seeds/:bu_id/status`, `POST /api-system/tenant/seeds/:bu_id/deploy/stream` (NDJSON) &nbsp;·&nbsp; **Kill switch:** env ของ gateway `TENANT_MIGRATION_API_ENABLED` ต้องเป็น true &nbsp;·&nbsp; **Seed set:** 8 &nbsp;·&nbsp; **หน้าย่อย:** 2 &nbsp;·&nbsp; **e2e suite:** ไม่มี

## 1. ภาพรวม

หน้านี้แสดง business unit ทุกแห่งในตารางและเก็บ**สถานะ seed ราย row**ไว้ในหน่วยความจำ: Not checked, Seeded, N missing, No DB หรือ Error ตัวหน้าเองไม่เก็บอะไร; "Check" ขอให้ backend เปรียบเทียบฐานข้อมูล tenant กับนิยาม seed และ "Seed" stream การสร้าง row ที่ขาด ตรรกะเดียวกันที่จำกัดอยู่ที่ BU เดียวก็ถูกฝังเป็น `TenantSeedCard` ในหน้าแก้ไข Business Units ด้วย (แท็บ Technical; ดู [Business Units: UI Screens](/th/backstage/business-units/ui-screens) §4.5)

**seed set** คือกลุ่ม row ที่มีชื่อและมี key คงที่ backend นิยามไว้แปดชุด ตามลำดับนี้ (ลำดับสำคัญเพราะ set legacy-wiring จะชี้ workflow ไปยัง row ที่ set template สร้าง; `seed-sets/index.ts`):

| ลำดับ | Set key | ป้ายที่แสดง | "row" คืออะไร |
|---|---|---|---|
| 1 | `running-code` | Running codes | หนึ่ง row `tb_config_running_code` ต่อ `type` ของเอกสาร |
| 2 | `vendor-business-type` | Vendor business types | หนึ่ง row `tb_vendor_business_type` ต่อชื่อ |
| 3 | `gl-jv-prefix` | GL JV prefixes | หนึ่ง row `tb_gl_jv_prefix` ต่อ code |
| 4 | `email-templates` | Email messages | หนึ่ง entry ภายใน row JSON เดียวของ `tb_application_config` สำหรับ key email-templates (read-modify-write ไม่ใช่ insert) |
| 5 | `notification-templates` | Workflow notification templates | หนึ่ง row `tb_notification_template` ต่อ template code |
| 6 | `notification-templates-legacy` | Workflow notification wiring | สาม action ไม่ใช่ row: `retire-legacy` (retire legacy template ที่ยังไม่ถูกแตะ), `move-reject-previous` (ย้ายช่อง approver ของ reject ไปที่ `previous_step` ใน workflow data), `fill-workflows` (เติม template id ของ workflow) |
| 7 | `adjustment-type` | Adjustment types | หนึ่ง row `tb_adjustment_type` ต่อ code |
| 8 | `pos-sale-adjustment-type` | POS sale adjustment type | adjustment type แบบ stock-out `SALE` ของ POS จับคู่ด้วย `code` เท่านั้น |

row ถือว่า**มีอยู่**ด้วย natural key ในกลุ่ม row ที่ไม่ถูกลบ ความคืบหน้าของ set คือ `present/defined`

## 2. บริบททางธุรกิจ

ค่าเริ่มต้นเปลี่ยนไปตามเวลา: release หนึ่งเพิ่ม running code ใหม่, notification template ใหม่ หรือ system adjustment type ใหม่ tenant ที่มีอยู่แล้วไม่ได้รับค่าเริ่มต้นใหม่จาก schema migration เพราะนั่นคือข้อมูล เจ้าหน้าที่ support จึงต้องการคำตอบสองข้อต่อ BU: "tenant นี้ตามหลังหรือไม่?" (สถานะ ปลอดภัย อ่านอย่างเดียว) และ "ทำให้เป็นปัจจุบัน" (apply) เนื่องจาก apply เขียนลงฐานข้อมูลจริงของลูกค้า จึงเป็น permission แยกจากการดู และ API ทั้งชุดอยู่หลัง kill switch ของ environment (§4)

## 3. แนวคิดสำคัญ

### 3.1 สถานะของ row

| สถานะ | เมื่อใด (`seedRowStatusOf`, `tenantSeed/seedRowState.ts`) |
|---|---|
| No DB | ข้อมูลรายการ BU แสดงว่าไม่มี database pool หรือไม่มี `db_schema` (เมื่อ payload ของรายการไม่มีทั้งสองฟิลด์ SPA จะสมมติว่ามี DB และปล่อยให้ 422 ของ backend แสดงเป็น Error) |
| Error | การ check หรือ seed ล่าสุดของ row นั้นล้มเหลว (ข้อความแสดงบน row) |
| Not checked | ยังไม่ได้โหลดสถานะ |
| N missing | โหลดสถานะแล้วและ `missing` รวมทุก set มากกว่าศูนย์ |
| Seeded | โหลดสถานะแล้วและไม่ขาดอะไร |

row เรียงตามอันดับ badge (Error, Missing, Not checked, No DB, Seeded) เมื่อเรียงคอลัมน์ Status

### 3.2 Idempotence

Seeding สร้างเฉพาะที่ขาด ดังนั้นการรันสองครั้งปลอดภัย event `done` สุดท้ายรายงาน `created` (row ที่สร้างในการรันนี้) และ `skipped` (row ที่นิยามไว้ของ set ที่เลือกซึ่งมีอยู่แล้ว) การรันซ้ำหลังการเชื่อมต่อหลุดคือวิธีกู้คืนที่ตั้งใจไว้

### 3.3 "seed all" หมายถึงอะไร

ไม่มี endpoint "ทุก BU" ฝั่ง server **Seed all missing** คือ SPA วนทีละ BU (ตามลำดับ ไม่ขนาน) โดยใช้สถานะที่มีอยู่แล้ว: เยี่ยมเฉพาะ row ที่ถูกทำเครื่องหมาย Missing อยู่ และจำกัดเฉพาะ set ที่ผู้ปฏิบัติงานติ๊กใน picker การออกจากหน้าจะหยุดวนก่อน BU ถัดไป

## 4. Permissions และ gating

| ชั้น | กฎ |
|---|---|
| Kill switch | `TenantMigrationGuard` throw 403 "Tenant migration API is disabled" เว้นแต่ env ของ gateway `TENANT_MIGRATION_API_ENABLED` เป็น true (ค่าเริ่มต้น false, `config.env.ts:209`) guard ตัวเดียวกันนี้ยังปกป้อง controller ของ Tenant Migrations ด้วย (`tenant-migrations.controller.ts`) |
| เส้นทาง CI | คำขอที่มี header `x-deploy-token` เท่ากับ `TENANT_DEPLOY_TOKEN` ผ่านในฐานะ actor `ci:deploy-token` โดยข้ามการตรวจผู้ใช้ |
| เส้นทางผู้ใช้ | ต้องมี Keycloak session ที่ถูกต้องและ key ของ route: status ต้องมี `tenant_seed.read`, deploy stream ต้องมี `tenant_seed.apply` **grant ที่จำกัดใน cluster ไม่นับ**: ผู้ใช้ต้องเป็น `is_super_admin` หรือมี key ในชุด backstage-wide ของตน |
| SPA | Route และ sidebar: `tenant_seed.read` + feature flag `tenant_seeds` ปุ่ม Seed และ Seed-all ถูก disable พร้อม tooltip "Requires the tenant_seed.apply permission." เว้นแต่ผู้ดูจะมี `tenant_seed.apply`; Check และ Check all ต้องการแค่ `read` |
| Role เริ่มต้น (seed data) | Backstage Admin ถือ `tenant_seed.*`; Support Manager และ Support Staff ถือแค่ `tenant_seed.read`; Security Officer ไม่ถือเลย (`seed.backstage-role-permission.data.ts`) |

ทุกการเรียกจะ log บรรทัด audit `tenant-seed.audit` พร้อม actor (`ci:deploy-token`, `super-admin:<id>` หรือ `backstage-user:<id>`), operation, `bu_id` และผลสำเร็จ

## 5. Edge Cases

| กรณี | พฤติกรรม |
|---|---|
| BU ไม่มี pool/schema | row แสดง No DB ไม่มี action; backend จะตอบ 422 "no database connection configured" |
| `bu_id` ไม่รู้จักหรือถูกลบ | 404; UUID ผิดรูปแบบ: 400 |
| Kill switch ปิด | ทุกการเรียก 403; toast ว่า "Seeding is disabled, or you lack the tenant seed permission." |
| เบราว์เซอร์ปิดกลางสตรีม | gateway unsubscribe เมื่อ**response** ปิด (`res.on('close')`) micro-business ตรวจ flag cancelled ระหว่าง row แต่ยังไม่ได้ตรวจสอบว่า unsubscribe ไปถึงมันผ่าน RPC stream หรือไม่ (คอมเมนต์ใน SPA service ก็ว่าเช่นนั้น) รันซ้ำเพื่อให้เสร็จ; seeding ข้าม row ที่มีอยู่แล้ว |
| Error กลางสตรีมหลังส่ง header แล้ว | เขียนบรรทัด NDJSON `{type:'error'}` แล้วสตรีมจบ; SPA ทำเครื่องหมาย row เป็น Error |

## 6. หน้าย่อย

- [UI Screens](/th/backstage/tenant-seed/ui-screens) - การ์ดสรุป, ตาราง, dialog เลือก set, ความคืบหน้าแบบ batch, การส่งออก CSV
- [Lifecycle](/th/backstage/tenant-seed/lifecycle) - การคำนวณสถานะ, โปรโตคอล NDJSON, ตรรกะสร้างราย set, การยกเลิก

## 7. แหล่งอ้างอิง

- SPA: `../carmen-backstage/src/pages/TenantSeedManagement.tsx`, `src/pages/tenantSeed/*`, `src/services/tenantSeedService.ts`, `src/components/TenantSeedCard.tsx`, `src/utils/seedError.ts`, type ที่ `src/types/index.ts:406`
- Gateway: `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/tenant-seeds/tenant-seeds.controller.ts` (`@Controller('api-system/tenant/seeds')`), guard `src/auth/guards/tenant-migration.guard.ts`
- Micro-business: `apps/micro-business/src/authen/tenant_seed/` (`tenant_seed.service.ts`, `seed-sets/`)
- ที่เกี่ยวข้อง: [Tenant Migrations](/th/backstage/tenant-migrations), [Business Units](/th/backstage/business-units), [Tenant Imports](/th/backstage/tenant-imports)
