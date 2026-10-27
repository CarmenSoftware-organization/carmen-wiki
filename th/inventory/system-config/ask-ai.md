---
title: Ask AI
description: การตั้งค่าต่อ business unit สำหรับเมนู "Ask AI" บนหน้า Purchase Request — เสนอ AI provider ตัวใดและส่ง prompt อะไร เก็บเป็นแถว ask_ai ใน tb_application_config; แคตตาล็อก provider เป็นของ Backstage
published: true
date: '2026-10-27T15:00:00.000Z'
tags: system-config, ask-ai, purchase-request, configuration, carmen-software
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Ask AI

> **At a Glance**
> **Route:** `/system-admin/ask-ai` &nbsp;·&nbsp; **การจัดเก็บ:** key `ask_ai` ใน `tb_application_config` (ต่อ BU) บนแคตตาล็อก AI provider ระดับแพลตฟอร์ม (`tb_ai_provider`, จัดการใน Backstage) &nbsp;·&nbsp; **Endpoint:** `GET`/`PUT api/config/:bu_code/ask-ai` (การตั้งค่า), `GET api/:bu_code/ask-ai/providers` (สิ่งที่หน้า PR ใช้) &nbsp;·&nbsp; **Permission:** `system_admin.business_unit` `view` / `update` + licence ของ nav `system_admin` &nbsp;·&nbsp; **ผู้ใช้งาน:** ปุ่ม **Ask AI** บนบรรทัดสินค้าของ [purchase-request](/th/inventory/purchase-request) (`pr-ask-ai-menu.tsx`)

## 1. คืออะไรและใครใช้

หน้า PR มี dropdown **Ask AI** การเลือก provider จะสร้าง prompt จาก template ของ provider บวกตารางสินค้าของ PR (`#`, ชื่อสินค้าพร้อมชื่อท้องถิ่น, จำนวนและหน่วย, ราคาที่เสนอพร้อมสกุลเงิน) แล้วเปิดเว็บไซต์ของ provider ในแท็บใหม่โดยใส่ prompt ไว้ล่วงหน้า ชื่อคลังสินค้าไม่ถูกส่งโดยตั้งใจ (`build-pr-ai-query.ts`) ไม่มีอะไรถูกส่งจากเซิร์ฟเวอร์ของ Carmen — เบราว์เซอร์เป็นผู้เปิด URL ของ provider

หน้าจอนี้ให้ Sysadmin ตัดสินใจ **สำหรับ BU ของตนเอง** ว่า provider ที่ active ของแพลตฟอร์มตัวใดจะปรากฏและแต่ละตัวใช้ prompt อะไร **ดูแลโดย** Sysadmin; **แคตตาล็อก provider** (label, icon, URL template, prompt เริ่มต้น, flag เปิดโดยค่าเริ่มต้น, ลำดับการเรียง) ดูแลโดยผู้ดูแลแพลตฟอร์มใน Backstage ([AI providers](/th/platform/ai-providers))

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู provider และสถานะที่มีผลจริง | Ask AI → หนึ่งแถวกะทัดรัดต่อ provider ที่ active | BU ที่ไม่เคยบันทึกจะเห็นค่าเริ่มต้นของแพลตฟอร์ม |
| เปิด/ปิด provider สำหรับ BU นี้ | **Edit** → สวิตช์ในแถว → **Save** | ถ้าไม่มี override provider จะตาม `default_enabled_for_bu` |
| Override prompt ของ provider | **Edit** → ขยายแถว (ทีละแถว) → ข้อความ prompt | ว่าง = ใช้ `default_prompt` ของแพลตฟอร์ม; แถวแสดง prompt ที่มีผลจริง |
| ใช้ตารางสินค้าในตำแหน่งที่เลือกของ prompt | ใส่ `{items}` ใน prompt | ถ้าไม่มี `{items}` ตารางจะถูกต่อท้ายหลังบรรทัดว่าง |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| 422 ตอนบันทึก | ไม่รู้จัก provider code หรือ prompt ยาวเกิน 4000 ตัวอักษร (`PROMPT_MAX`, `config_ask-ai.service.ts:18`) | โหลดหน้าใหม่; ทำ prompt ให้สั้นลง |
| ปุ่ม Ask AI หายจากหน้า PR | ไม่มี provider ที่เปิดอยู่จริงสำหรับ BU (`providers.length === 0` ซ่อนเมนู) | เปิด provider ที่นี่ |
| prompt ถูกคัดลอกไป clipboard แทนที่จะใส่ล่วงหน้า | URL template ของ provider ไม่มี `{query}` หรือ URL ที่เติมแล้วยาวเกิน 8000 ตัวอักษร (`MAX_URL_LENGTH`) | วาง prompt เอง; toast ยืนยันการคัดลอก |
| ไม่มีอะไรเปิด | URL ที่ resolve แล้วไม่ขึ้นต้นด้วย `https://` (เมนูปฏิเสธ) | แก้ URL template ของ provider ใน Backstage |
| route app-config ทั่วไปปฏิเสธ `ask_ai` | key นี้ถูกจัดการโดย endpoint นี้เท่านั้น (`rejectAskAiKey`, `config_app-config.controller.ts:73`); ถูกซ่อนจาก `GET /app-config` ด้วย | ใช้ `/ask-ai` |

## 4. กรณีพิเศษ

- **provider ที่ปิดยังคง override ไว้** การบันทึกไม่เคยลบค่าที่เก็บของ provider ที่แพลตฟอร์มปิดการใช้งานไปแล้ว (BE `7f7fe0843`); `null` หรือสตริงว่างสำหรับ `enabled` / `prompt` ลบเฉพาะฟิลด์นั้น
- **การแยก BU** controller ต้องการให้ `bu_code` ใน path ตรงกับ context ของผู้เรียก (`BuCodePathQueryMatchGuard`) — แก้ใน `7f7fe0843` หลังพบช่องว่างข้าม tenant
- **บันทึกแบบแทนที่ทั้งหมด** `PUT` แทนที่บล็อก override ทั้งก้อน; FE ส่งเฉพาะ provider ที่ draft ต่างจากสถานะที่โหลด (`buildSaveBody`)

---

## 5. รูปแบบข้อมูล (Dev)

```
tb_application_config  key = "ask_ai"
{
  "providers": {
    "<provider code>": { "enabled": true|false, "prompt": "text" }   // ไม่บังคับทั้งสองฟิลด์
  }
}

GET api/config/:bu_code/ask-ai  ->  items[{ code, label, icon_key, icon_url, sort_order,
                                            default_prompt, default_enabled_for_bu,
                                            bu_enabled|null, bu_prompt|null }]   (เฉพาะ provider ที่ active)
GET api/:bu_code/ask-ai/providers -> [{ code, label, icon_key, icon_url, url_template, prompt }]
   effective = is_active AND (bu.enabled ?? default_enabled_for_bu);  prompt = bu.prompt || default_prompt
```

แหล่ง: `apps/backend-gateway/src/config/config_ask-ai/ask-ai-resolve.ts`

## 6. กติกาทางธุรกิจ

- เฉพาะ provider ของแพลตฟอร์มที่ `is_active` เท่านั้นที่ถูก list หรือเสนอ
- การเปิดใช้งานและ prompt ที่มีผลจริงเป็นไปตามกฎ override-ก่อน-แล้วค่อย-default ข้างต้น
- การเขียนต้องมี `system_admin.business_unit.update` และ App ID `askAi.saveConfig`; การอ่านต้องมี `.view` และ `askAi.getConfig` (`config_ask-ai.controller.ts:57-90`)

## 7. ความเชื่อมโยงข้ามโมดูล

- [purchase-request](/th/inventory/purchase-request) — ที่ที่เมนูปรากฏ
- [system-config/application-config](/th/inventory/system-config/application-config) — key `ask_ai` อยู่ใน store นี้แต่เขียนผ่าน route ทั่วไปของมันไม่ได้

## 8. แหล่งอ้างอิง

- **Gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_ask-ai/` (controller, service, `ask-ai-resolve.ts`); `src/application/ask-ai/` (provider สำหรับหน้า PR)
- **Schema:** `packages/prisma-shared-schema-backstage/prisma/schema.prisma` (AI provider, comment ที่บรรทัด 1259); seed `seed.ai-provider.data.ts`
- **Frontend:** `../carmen-frontend/routes/system-admin/ask-ai/` (`ask-ai-component.tsx`, `ask-ai-provider-card.tsx`, `use-ask-ai-config.ts`); `routes/procurement/purchase-request/ai/` (`pr-ask-ai-menu.tsx`, `build-pr-ai-query.ts`, `use-ask-ai-providers.ts`); nav `constant/module-list.ts:793-799`
- **Licence:** `config:ask-ai` → `configuration.app_config` (`permission.route-map.ts:94`)
