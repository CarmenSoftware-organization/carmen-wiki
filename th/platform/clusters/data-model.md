---
title: Cluster — Data Model
description: Entity ของ cluster, ความสัมพันธ์กับ BU และ user, และ licence ledger ที่มาแทน cap แบบ static เดิม (max_license_bu/max_license_users)
published: true
date: 2026-09-05T04:42:43.000Z
tags: book/platform, clusters, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Data Model

## 1. At a Glance

- Entity `tb_cluster`: field identity (`code`, `name`, `alias_name`), branding file token (`logo_file_token`, `avatar_file_token` — API resolve เป็น presigned object `logo`/`avatar` ฝังในตัว), counter `doc_version Int @default(0)` สำหรับ optimistic lock และ audit/soft-delete trio **ไม่มีคอลัมน์ licence-cap (`max_license_bu`) อีกต่อไป** — ถูกถอดออกจากทั้ง Prisma model และ SPA ทั้งหมด (โค้ดฝั่ง SPA ตัวสุดท้ายที่อ่านค่านี้ถูกลบโดย commit `7fda015`, "ลบโค้ดที่อ่าน max_license_bu ที่เหลือทั้งหมด")
- One-to-many กับ Business Units (`tb_business_unit.cluster_id`) — `tb_business_unit.max_license_users` ก็ถูกถอดออกเช่นกัน (migration `20260821000000_drop_bu_max_license_users`, 2026-08-21) หลัง backfill ข้อมูลเข้า `tb_business_unit_license` แล้ว
- M:N กับ user ผ่าน `tb_cluster_user` (`role` ต่อ cluster: `admin`/`user` — orthogonal กับโมเดล Platform RBAC, ดู [rbac](/th/platform/rbac)) **ไม่มี `parent_bu_id` แล้ว** — ไม่พบ field นี้ใน model ปัจจุบันเลย (grep ทั้ง schema ไม่เจอ) ตรงกับที่ UI ของแท็บ Users ถอด field/column ของ Business Unit ออกไปแล้ว `tb_cluster_user` ยังมี `doc_version` แต่การแก้ไข role แบบ inline ในแท็บ Users ยังไม่ส่งค่านี้ไปด้วย
- **ใหม่ — `tb_cluster_license`:** ledger การซื้อโควตา BU ของ cluster (`licensed_bus`, `start_date`/`end_date`, ฟิลด์ยกเลิก) โควตาที่มีผลคือใบที่ชนะใบเดียว (view `v_cluster_bu_cap` — คนละตัวกับ `v_cluster_bu_quota` ที่ทำหน้าที่จัดอันดับ BU รายตัว ดูรายละเอียดสองตัวนี้ในหน้า en) ไม่ใช่ผลรวม — ไม่มีใบที่ชนะ = โควตา `0` จริง ไม่ใช่ "ไม่จำกัด" กลายเป็น `bu_cap`/`bu_cap_end_date` บน `Cluster` interface แทนที่ `max_license_bu` เดิม
- **ใหม่ — `tb_business_unit_license`:** ledger ที่นั่งต่อ BU ที่รวมยอดผ่าน view `v_business_unit_seat` เป็น `total_max_license_users` ของ cluster — มิตินี้ `null`/ไม่มีใบยังหมายถึง "ไม่จำกัด" (ไม่เหมือนโควตา BU)
- การอัปโหลด branding ผ่าน multipart endpoint เฉพาะ: `POST /api-system/clusters/:id/logo` และ `POST /api-system/clusters/:id/avatar` (ไม่เปลี่ยนแปลง)
- ทั้ง `tb_cluster_license`/`tb_business_unit_license` และ UI ซื้อ/ยกเลิกเต็มรูปแบบเป็นขอบเขตของโมดูล **licenses** — หน้านี้บันทึกเฉพาะรูปร่างฝั่ง cluster ของ ledger เท่านั้น

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma — `model tb_business_unit` (บรรทัด 176), `model tb_cluster` (บรรทัด 270), `model tb_cluster_user` (บรรทัด 299), `model tb_business_unit_license` (บรรทัด 1133), `model tb_cluster_license` (บรรทัด 1168), `enum enum_cluster_user_role` (บรรทัด 718) — เลขบรรทัด ณ 2026-09-05 (source HEAD ของ repo `carmen-turborepo-backend-v2` คือ `e0f7d0b`; ต่างจาก HEAD ของ `carmen-platform` คือ `157a65e` ที่อ้างในหน้า en — คนละ repo กัน ทั้งคู่ถูกต้อง)
- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql — `CREATE VIEW "v_cluster_bu_cap"` (คำนวณ cap จากใบที่ชนะ) และ `CREATE VIEW "v_cluster_bu_quota"` (จัดอันดับ BU รายตัว โดยยืม cap มาจาก view แรก)
- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260901020000_cluster_license_cancel/migration.sql — เพิ่ม `cancelled_at` และ `CREATE OR REPLACE VIEW "v_cluster_bu_cap"` ให้กรอง `cancelled_at IS NULL`
- ../carmen-platform/src/types/index.ts — interface `Cluster` (บรรทัด 26–51, มี `bu_cap`/`bu_used`/`bu_cap_end_date`/`doc_version` — ไม่มี `max_license_bu` แล้ว), `ClusterUser` (บรรทัด 448–464, ไม่มี `parent_bu_id`), `PresignedImage`, `Audit`/`AuditEntry`
- ../carmen-platform/src/utils/docVersion.ts — helper `getDocVersion`/`isVersionConflict`/`notifyVersionConflict`
- ../carmen-platform/src/utils/capacity.ts — `utilization()` (กฎ null/0 = ไม่จำกัด ยังใช้กับมิติที่นั่ง) เทียบกับ `seatUtilization()` (กฎ finite เสมอ ใช้กับโควตา BU ตอนนี้)
- ../carmen-platform/src/utils/businessUnitRank.ts — การจัดอันดับ BU (`is_hq DESC, created_at ASC, id ASC`) ที่ต้องตรงกับ view `v_cluster_bu_quota`
- ../carmen-platform/src/services/clusterService.ts — REST client (`/api-system/clusters`, `/api-system/clusters/summary`)

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/clusters/data-model (รวมตาราง `tb_cluster_license`/`tb_business_unit_license` และตาราง Divergences ที่ปรับใหม่)
- [ ] เพิ่ม entity diagram
