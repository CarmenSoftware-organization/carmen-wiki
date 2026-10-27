---
title: AI Providers — Data Model
description: ตาราง tb_ai_provider ใน backstage schema — คอลัมน์, index, provider หกรายการที่ seed ไว้ และวิธีที่ override Ask AI ของ business unit ใน tb_application_config ทำงานร่วมกับตารางนี้
published: true
date: '2026-10-27T15:00:00.000Z'
tags: book/platform, ai-providers, data-model
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# AI Providers — Data Model

> **At a Glance**
> **ตาราง:** เป็นเจ้าของ 1 (`tb_ai_provider`) + อ้างอิง 1 (`tb_application_config` key `ask_ai` ฝั่ง tenant) &nbsp;·&nbsp; **Enum:** ไม่มี &nbsp;·&nbsp; **คอลัมน์ audit:** `doc_version`, `created_*`, `updated_*`, `deleted_*` (soft delete) &nbsp;·&nbsp; **Seed:** 6 row ที่ migration insert &nbsp;·&nbsp; **ความต่างเทียบกับ SPA:** ไม่พบ

> **แหล่งความจริง:** Backend Prisma backstage schema อ่านที่นี่ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` (`model tb_ai_provider`)
> - `.../prisma/migrations/20261027120000_add_ai_provider/migration.sql`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่สร้างอัตโนมัติและไม่ใช่แหล่งอ้างอิงที่แท้จริง

## 1. ภาพรวม

โมดูลนี้เป็นเจ้าของตารางแบบแบนเพียงตารางเดียวใน**ฐานข้อมูล backstage (system)** ไม่ใช่ในฐานข้อมูล tenant ใด ๆ และไม่มี foreign key ส่วนที่คู่กันฝั่ง tenant ไม่ใช่ตารางของตัวเอง: แต่ละ business unit เก็บ override เป็นค่า JSON หนึ่งค่าใน row ของ `tb_application_config` ของ tenant ที่ `key` เป็น `ask_ai` (§2.2)

## 2. Entities

### 2.1 `tb_ai_provider`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
|---|---|---|---|
| **Identity** | | | |
| `id` | `String @id @db.Uuid` (`gen_random_uuid()`) | No | Primary key |
| `code` | `String @db.VarChar(50)` | No | machine key ที่คงที่ เช่น `claude` ถูกอ้างอิงโดย override ของ BU เปลี่ยนไม่ได้หลังสร้าง |
| `label` | `String @db.VarChar(100)` | No | ชื่อที่แสดง |
| `seed_key` | `String? @db.VarChar(100)` | Yes | identity ของ row ที่ seed เป็นเจ้าของ (`db:seed.ai-provider`); `NULL` สำหรับ row ที่สร้างจาก UI |
| **Presentation** | | | |
| `icon_key` | `String? @db.VarChar(30)` | Yes | ไอคอนในตัว: `claude`, `chatgpt`, `gemini`, `deepseek`, `grok`, `google` |
| `icon_url` | `String? @db.VarChar(500)` | Yes | ไอคอน https; มีลำดับเหนือ `icon_key` ใน UI |
| `sort_order` | `Int @default(0)` | No | ลำดับเมนู (น้อยไปมาก) row ใหม่จาก UI ตั้งต้นที่ค่าสูงสุดปัจจุบัน + 10 |
| **Behaviour** | | | |
| `url_template` | `String @db.VarChar(500)` | No | URL แบบ https; `{query}` จะถูกแทนด้วย prompt ที่ encode แล้ว |
| `default_prompt` | `String @db.Text` | No | prompt ที่ใช้เมื่อ BU ไม่มี override `{items}` ระบุตำแหน่งที่ตารางรายการสินค้าจะไปอยู่ |
| `is_active` | `Boolean @default(true)` | No | row ที่ inactive จะถูกซ่อนจากทุก BU |
| `default_enabled_for_bu` | `Boolean @default(false)` | No | BU ที่ไม่เคยเลือกจะเห็น provider นี้หรือไม่ |
| **Audit** | | | |
| `doc_version` | `Int @default(0)` | No | ตัวนับ optimistic-lock เพิ่มขึ้นทุกครั้งที่ update |
| `created_at` / `created_by_id` | `DateTime? @db.Timestamptz(6)` / `String? @db.Uuid` | Yes | audit ตอนสร้าง |
| `updated_at` / `updated_by_id` | เหมือนกัน | Yes | audit การแก้ไขล่าสุด |
| `deleted_at` / `deleted_by_id` | เหมือนกัน | Yes | Soft delete; query กรอง `deleted_at: null` |

**Constraint และ index**

- `@@unique([code, deleted_at], map: "ai_provider_code_u")` และ `@@index([sort_order], map: "idx_ai_provider_sort_order")` (ประกาศใน Prisma)
- **partial unique index** สองตัวมีอยู่เฉพาะใน SQL ของ migration (Prisma ประกาศไม่ได้): `uq_ai_provider_seed_key` บน `(seed_key) WHERE seed_key IS NOT NULL` และ `ai_provider_code_live_u` บน `(code) WHERE deleted_at IS NULL` ตัวหลังคือสิ่งที่ป้องกันไม่ให้มีสอง row ที่ยังไม่ถูกลบและมี `code` เดียวกันจริง ๆ เพราะ composite unique ไม่ได้กัน `NULL deleted_at` ซ้ำ service ก็ตรวจซ้ำก่อน insert ด้วย

**Row ที่ seed** (migration `INSERT`, idempotent): `claude`, `chatgpt`, `gemini`, `deepseek`, `grok`, `google` (label "Google Search") `claude`, `chatgpt` และ `google` ใช้ template แบบ `{query}`; `gemini`, `deepseek` และ `grok` ใช้ URL ธรรมดา จึงเปิดโดยไม่มี prompt ใส่ไว้ให้ แหล่งความจริงของ row คือ `prisma/seed.ai-provider.data.ts`

### 2.2 Override ของ BU (อ้างอิง, ฝั่ง tenant)

เก็บที่ `tb_application_config` โดย `key = 'ask_ai'`:

```
value = { providers: { <code>: { enabled?: boolean, prompt?: string } } }
```

การ parse ทำอย่างระมัดระวัง (`parseAskAiBuConfig`): รูปร่างที่ไม่ใช่ object ให้ config ว่าง, `prompt` ที่ว่างเปล่าจะถูกทิ้ง กฎการ resolve สำหรับหนึ่ง provider และหนึ่ง BU:

```
visible  = provider.is_active AND (override.enabled ?? provider.default_enabled_for_bu)
prompt   = override.prompt OR provider.default_prompt
```

route ทั่วไป `/api/config/:bu_code/:key` ปฏิเสธ key `ask_ai`; เขียนได้ผ่าน `PUT /api/config/:bu_code/ask-ai` เท่านั้น

## 3. ความสัมพันธ์

ไม่มี `tb_ai_provider.code` เป็นการอ้างอิงแบบ soft จาก JSON override; ไม่มี FK และไม่มีอะไร cascade เมื่อลบ provider (override ยังอยู่แต่ถูกเพิกเฉย)

## 4. Enums

ไม่มีในโมดูลนี้ รายการไอคอนเป็นชุดสตริงปิดที่บังคับในโค้ด (`AI_PROVIDER_ICON_KEYS`) ไม่ใช่ enum ของฐานข้อมูล

## 5. ความต่างจากรูปร่างของ SPA carmen-backstage

ไม่พบความต่างเมื่อเทียบกับ interface `AiProvider` ของ SPA (`src/types/index.ts:2154`) ณ 2026-10-27: สิบสองฟิลด์เท่ากัน; `AiProviderInput` ตัด `id`, `doc_version`, `created_at`, `updated_at` ออก type ของ SPA ไม่มี `seed_key` หรือฟิลด์ `*_by_id` เพราะ API ไม่ต้องใช้ใน UI หมายเหตุ response ของ gateway `findAll`/`findOne` ส่ง row ตามที่เก็บผ่านไปตรง ๆ คอลัมน์เพิ่มเติมเหล่านั้นจึงอยู่ใน payload แต่ไม่ได้ใช้

## 6. แหล่งอ้างอิง

- หลัก: `packages/prisma-shared-schema-backstage/prisma/schema.prisma`, migration `20261027120000_add_ai_provider`
- รอง: `../carmen-backstage/src/types/index.ts` (`AiProvider`, `AiProviderInput`)
- โค้ด: `apps/micro-cluster/src/cluster/ai-provider/ai-provider.service.ts`; `apps/backend-gateway/src/config/config_ask-ai/ask-ai-resolve.ts`
- หน้าข้างเคียง: [AI Providers](/th/platform/ai-providers), [UI Screens](/th/platform/ai-providers/ui-screens)
