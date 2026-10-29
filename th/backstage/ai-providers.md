---
title: AI Providers (ผู้ให้บริการ AI)
description: แค็ตตาล็อกระดับแพลตฟอร์มของผู้ให้บริการ "Ask AI" (Claude, ChatGPT, Gemini ฯลฯ) พร้อม prompt เริ่มต้นและ link template ที่หน้า Purchase Request ใช้ แก้ไขได้จากหน้ารายการเดียวที่ใช้ dialog
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, ai-providers
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# AI Providers (ผู้ให้บริการ AI)

โมดูล **AI Providers** คือแค็ตตาล็อกที่แพลตฟอร์มเป็นเจ้าของ ซึ่งอยู่เบื้องหลังปุ่ม "Ask AI" บนหน้า Purchase Request แต่ละ row คือผู้ช่วยภายนอกหนึ่งราย (Claude, ChatGPT, Gemini, DeepSeek, Grok, Google Search): ชื่อที่แสดง, ไอคอน, URL ที่ปุ่มเปิด และ **default prompt** ที่ถูกส่งหรือคัดลอกไป แค็ตตาล็อกนี้เคย hard-code อยู่ใน inventory frontend; migration `20261027120000_add_ai_provider` ย้ายมาไว้ใน `tb_ai_provider` และ seed ค่าเริ่มต้นหกรายการ เจ้าหน้าที่แพลตฟอร์มแก้ที่นี่ครั้งเดียวแล้วมีผลกับทุก business unit ขณะที่แต่ละ BU ยังเลือกเปิด/ปิด provider และ override prompt ฝั่งตัวเองได้

> **At a Glance**
> **หน้าจอ:** `AiProviderManagement` (+ `AiProviderEditDialog`) &nbsp;·&nbsp; **Route:** `/purchase-request-ai-providers` (`/ai-providers` เดิม redirect มาที่นี่, `App.tsx:400`) &nbsp;·&nbsp; **Nav:** กลุ่ม `navGroup.ai`, `permission: 'ai_provider.read'`, `feature: 'ai_providers'` (`backstageNav.ts:57`) &nbsp;·&nbsp; **Permission key:** `ai_provider.read` / `.create` / `.update` / `.delete` &nbsp;·&nbsp; **API:** `/api-system/ai-providers` &nbsp;·&nbsp; **ตาราง:** `tb_ai_provider` &nbsp;·&nbsp; **หน้าย่อย:** 2 &nbsp;·&nbsp; **e2e suite:** ไม่มี (`../carmen-backstage-e2e` ไม่มี spec ของ ai-provider)

## 1. ภาพรวม

หน้ารายการหนึ่งหน้า กับ dialog สร้าง/แก้ไขหนึ่งอัน ไม่มี route สำหรับหน้ารายละเอียดและไม่มีหน้าแก้ไขแยก รายการแสดง provider ทุกตัว**รวมถึงตัวที่ inactive** (gateway เรียก micro-cluster ด้วย `include_inactive: true` เสมอ, `backstage_ai-providers.service.ts` `findAll`) เรียงตาม `sort_order` หน้าจอตั้งใจให้เล็กเพราะแค็ตตาล็อกเล็ก: seed ไว้หกแถว แก้นาน ๆ ครั้ง

มีสองเรื่องที่ทำให้โมดูลนี้ควรถูก document เกินกว่ารูปแบบ CRUD:

- **placeholder `{query}` เป็นตัวกำหนดว่าปุ่มทำงานอย่างไรสำหรับผู้ใช้ปลายทาง** `url_template` ที่มี `{query}` จะเปิด provider พร้อมใส่ prompt ให้เสร็จ; template ที่ไม่มีจะเปิด provider เฉย ๆ แล้วผู้ใช้วาง prompt ที่ถูกคัดลอกไว้ในคลิปบอร์ด คอลัมน์ "Opens" ของรายการบอกว่าเป็นแบบไหน (§3.2)
- **การเปลี่ยนแปลงมีผลทั่วทั้งระบบ** subtitle ของหน้าเขียนว่า "Changes apply to every business unit." การลบ provider จะซ่อนมันทุกที่; ค่าตั้งราย BU ยังเก็บไว้แต่ถูกเพิกเฉย (ข้อความใน dialog ลบ)

## 2. บริบททางธุรกิจ: ใครใช้ตารางนี้

| ผู้ใช้ | Route | ทำอะไร |
|---|---|---|
| เมนู "Ask AI" ของ Purchase Request | `GET /api/:bu_code/ask-ai/providers` (`application/ask-ai/ask-ai.controller.ts:20,35`) | คืน provider ที่ BU นั้นใช้ได้: active และ `bu override enabled ?? default_enabled_for_bu`; prompt = override ของ BU หรือ `default_prompt` (`resolveBuProviders`, `config_ask-ai/ask-ai-resolve.ts`) ไม่มี `@Permission` โดยตั้งใจ เพื่อให้ role ที่มีแค่ `view_department` ยังเห็นเมนู |
| การตั้งค่า Ask AI ของ BU | `GET/PUT /api/config/:bu_code/ask-ai` (`config_ask-ai.controller.ts:42`) | แสดงเฉพาะ provider ที่ **active** พร้อม override ของ BU (`bu_enabled`, `bu_prompt`); การบันทึกเก็บ `{ providers: { <code>: { enabled?, prompt? } } }` ไว้ใต้ key `ask_ai` ของ `tb_application_config` gate ด้วย `system_admin.business_unit` `view`/`update` override ของ provider ที่ inactive จะถูกเก็บไว้ตอนบันทึก ดังนั้นการ re-activate provider จะคืนค่าที่ BU เลือกไว้ |

ข้อความ prompt รองรับ token `{items}` ซึ่งเป็นตำแหน่งที่ตารางรายการสินค้าจะถูกแทรก; ถ้าไม่มี ตารางจะถูกต่อท้ายหลังบรรทัดว่าง (hint ใน dialog `fieldPromptHint`)

## 3. แนวคิดสำคัญ

### 3.1 ฟิลด์ของ provider

ตารางเต็มอยู่ใน [Data Model](/th/backstage/ai-providers/data-model) โดยสรุป: `code` (key ที่เปลี่ยนไม่ได้), `label`, ไอคอนแบบเลือกได้ (`icon_key` จากรายการปิด **หรือ** `icon_url` โดย URL ชนะ), `url_template`, `default_prompt`, `is_active`, `default_enabled_for_bu`, `sort_order`

### 3.2 Validation (ฝั่ง server)

บังคับใช้ใน micro-cluster (`ai-provider.validation.ts`) และ dialog สะท้อนเพียงบางส่วน (pattern ของ code, ความยาว prompt, ฟิลด์ที่จำเป็น, sort order เป็นจำนวนเต็ม):

| กฎ | ค่า |
|---|---|
| `code` | `^[a-z0-9][a-z0-9_-]{1,49}$` (2-50 ตัวอักษร); จำเป็นตอนสร้าง, **ไม่รับตอน update** |
| `label` | 1-100 ตัวอักษร |
| `icon_key` | หนึ่งใน `claude`, `chatgpt`, `gemini`, `deepseek`, `grok`, `google` หรือ `null` |
| `icon_url` | `https` เท่านั้น, ห้ามมี username/password, สูงสุด 500 ตัวอักษร |
| `url_template` | `https` เท่านั้น, ห้ามมี credential, สูงสุด 500 ตัวอักษร; `{query}` ใช้ได้ **เฉพาะหลัง `?` หรือ `#` ตัวแรก** |
| `default_prompt` | จำเป็นตอนสร้าง; สูงสุด 4000 ตัวอักษร |
| `is_active`, `default_enabled_for_bu` | boolean |
| `sort_order` | จำนวนเต็ม (dialog บังคับเพิ่มเติมว่า `>= 0`) |

### 3.3 Optimistic locking

`PATCH` ส่ง `doc_version` ไปด้วย การ update ใน micro-cluster ใส่ `doc_version` ไว้ใน `where` ของการเขียน ดังนั้นค่าที่เก่าจะไม่ match แถวใดเลยและตอบ `ALREADY_EXISTS` ("AI provider was modified", แสดงผลเป็น 409) dialog จัดการโดยแสดง toast version-conflict มาตรฐาน ปิดตัวเอง และโหลดรายการใหม่ ถ้าไม่ส่ง `doc_version` การเขียน**จะไม่ถูกป้องกัน** (เช็ก `docVersion != null`, `ai-provider.service.ts`); SPA ส่งเสมอ

## 4. Permissions

Gate เป็นเรื่อง RBAC มาตรฐานของ backstage ไม่มีเงื่อนไขพิเศษเฉพาะโมดูล:

| ที่ไหน | การตรวจสอบ |
|---|---|
| Route + sidebar | `ai_provider.read` บวก feature flag `ai_providers` (สถานะเริ่มต้น `active`, `featureFlags.ts:66`) |
| ปุ่ม "Add provider" | `<Can permission="ai_provider.create">` |
| Edit / Delete ของแถว | `<Can permission="ai_provider.update">` / `ai_provider.delete` |
| API อ่าน | `ai_provider.read` ผ่าน `BackstagePermissionGuard` |
| API create / update / delete | write key **บวก** `BackstageWidePermissionGuard` ซึ่งปฏิเสธ grant ที่จำกัดใน cluster: ผ่านได้เฉพาะ super-admin หรือ grant ระดับ backstage ทั้งระบบ (`backstage-wide-permission.guard.ts`) |

การตรวจฝั่ง SPA ทั้งหมดส่ง `BACKSTAGE_SCOPED_RECORD` เพราะ record นี้ไม่ได้อยู่ใน cluster ใด

**Role เริ่มต้น** (`seed.backstage-role-permission.data.ts`): Backstage Admin ถือ `ai_provider.*`; Support Manager และ Support Staff ถือแค่ `ai_provider.read` (เห็นรายการแต่ไม่เห็นปุ่ม); Security Officer ไม่ถือเลยและเจอ `<Forbidden>` ที่ route

## 5. Edge Cases

| กรณี | พฤติกรรม |
|---|---|
| สร้างด้วย `code` ที่ถูกใช้โดย row ที่ยังไม่ถูกลบ | 409 "AI provider code already exists" ส่วน code ของ row ที่ลบแบบ soft ไปแล้วนำกลับมาใช้ได้ (partial unique index `ai_provider_code_live_u`) |
| แก้ code | ฟิลด์ถูก disable ในโหมดแก้ไข; server เพิกเฉย `code` ตอน update |
| Template มี `{query}` ก่อน `?`/`#` | ถูกปฏิเสธ (400) Dialog แสดงแค่ preview แบบ live ไม่ได้ตรวจกฎนี้ จึงได้ error จาก server |
| Prompt เกิน 4000 ตัวอักษร | ปุ่ม Save ถูก disable (ตัวนับเป็นสีแดง); server ก็ปฏิเสธด้วย |
| ตั้งทั้ง `icon_url` และ `icon_key` | แสดง `icon_url`; `icon_key` ยังเก็บไว้ใน row |
| ตั้ง `is_active` เป็น false | provider หายจากเมนูของทุก BU และจากหน้าตั้งค่า BU; override ของ BU ที่เก็บไว้ยังอยู่ |
| Delete | Soft delete (`deleted_at`, `deleted_by_id`); row ไม่แสดงในรายการอีก |

## 6. หน้าย่อย

- [Data Model](/th/backstage/ai-providers/data-model) - คอลัมน์ของ `tb_ai_provider`, index, row ที่ seed, รูปร่าง override ของ BU
- [UI Screens](/th/backstage/ai-providers/ui-screens) - คอลัมน์ของรายการ, ส่วนต่าง ๆ ของ dialog แก้ไข, การยืนยันการลบ, พฤติกรรม responsive

## 7. แหล่งอ้างอิง

- SPA: `../carmen-backstage/src/pages/AiProviderManagement.tsx`, `src/pages/aiProviders/AiProviderEditDialog.tsx`, `src/services/aiProviderService.ts`, `src/types/index.ts` (`AiProvider`, บรรทัด 2154)
- Gateway: `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage_ai-providers/backstage_ai-providers.controller.ts` (`@Controller('api-system/ai-providers')`, บรรทัด 39)
- Micro-service: `apps/micro-cluster/src/cluster/ai-provider/{ai-provider.service.ts,ai-provider.validation.ts}`
- Schema: `packages/prisma-shared-schema-backstage/prisma/schema.prisma` (`model tb_ai_provider`) และ migration `20261027120000_add_ai_provider`
- ที่เกี่ยวข้อง: [Business Units](/th/backstage/business-units), [Feature Flags](/th/backstage/feature-flags)
