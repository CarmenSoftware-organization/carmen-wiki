---
title: AI Providers — UI Screens
description: คำอธิบายหน้ารายการ AI Providers และ dialog สร้าง/แก้ไข — คอลัมน์, พฤติกรรม responsive, ส่วนของฟอร์ม, validation hint, การยืนยันการลบ และสิ่งที่ไม่ถูกเก็บถาวร
published: true
date: '2026-10-27T15:00:00.000Z'
tags: book/platform, ai-providers, ui-screens
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# AI Providers — UI Screens

> **At a Glance**
> **หน้าจอ:** หน้ารายการ 1 + dialog 1 (สร้างและแก้ไขใช้ร่วมกัน) + confirm การลบ 1 &nbsp;·&nbsp; **Layout การแก้ไข:** dialog เดียวที่เลื่อนได้ สี่ส่วน &nbsp;·&nbsp; **Dialogs:** `AiProviderEditDialog`, `ConfirmDialog` &nbsp;·&nbsp; **การเข้าถึง:** `ai_provider.read` เพื่อดู; create/update/delete ตามแต่ละปุ่ม &nbsp;·&nbsp; **UI state ที่เก็บถาวร:** ไม่มี

## 1. ภาพรวม

โมดูลนี้คือหนึ่งหน้า `AiProviderManagement` ที่ `/purchase-request-ai-providers` ห่อด้วย `Layout` + `PageHeader` ตามปกติ **ไม่มีช่องค้นหา, ไม่มี filter panel, ไม่มี pagination และไม่มีตัวควบคุมการเรียงลำดับ**: แค็ตตาล็อกมีขนาดเล็ก โหลดครบเสมอและเรียงตาม `sort_order` การสร้างและแก้ไขทำใน `AiProviderEditDialog`; ไม่มี route `/new` หรือ `/:id/edit` ชื่อหน้าคือ `nav.aiProviders` ("Purchase Request AI Providers"), subtitle "Changes apply to every business unit."

## 2. `AiProviderManagement` (`/purchase-request-ai-providers`)

### 2.1 Layout

`Card` เดียวที่มีตาราง (`TableSkeleton` ระหว่างโหลดครั้งแรก; `ListEmptyState` "No AI providers yet" เมื่อว่าง) คอลัมน์ พร้อม breakpoint ที่แต่ละคอลัมน์ปรากฏ:

| คอลัมน์ | แสดงเมื่อ | เนื้อหา |
|---|---|---|
| Provider | เสมอ | ไอคอนขนาด 36px (รูป `icon_url` ไม่งั้นใช้ `ProviderIconMark` ในตัวตาม `icon_key`), `label` และ `code` แบบ monospace (ต่ำกว่า `md` จะแสดง hostname ของลิงก์แทน) row ที่ inactive แสดงที่ความโปร่งใส 50% |
| Opens | `md`+ | Hostname ของ `url_template` (token `{query}` ถูกสลับเป็น `q` เพื่อ parse) และ hint: "Prompt pre-filled" (template มี `{query}`) หรือ "Prompt copied to paste" |
| Default prompt | `lg`+ | จำนวนตัวอักษร; บรรทัดที่สองบอก "Shared with N more" เมื่อ provider อื่นมี prompt เหมือนกัน ไม่งั้น "Unique to this provider" Hover แสดง prompt เต็มเป็น tooltip |
| Status | เสมอ | badge `Active` / `Inactive`; ต่ำกว่า `md` จะแสดงค่าเริ่มต้นของ BU เป็นบรรทัดที่สองด้วย |
| Business units | `md`+ | Badge "On by default" หรือ "Opt-in" (จาก `default_enabled_for_bu`) |
| Order | `md`+ | `sort_order` ชิดขวา |
| (actions) | เสมอ | ปุ่มไอคอน Edit และ Delete |

### 2.2 Header actions

"Add provider" เปิด dialog ในโหมดสร้าง แสดงเฉพาะเมื่อมี `ai_provider.create`

### 2.3 Row actions

Edit (ดินสอ) เปิด dialog พร้อม row; Delete (ถังขยะ) เปิด dialog ยืนยัน gate ด้วย `ai_provider.update` และ `ai_provider.delete` ตามลำดับ ทั้งคู่ถูก disable ระหว่างที่กำลังโหลดใหม่

### 2.4 การยืนยันการลบ

`ConfirmDialog` "Delete this AI provider?" พร้อมข้อความ "The provider disappears from every business unit. Per-BU settings are kept but ignored." เมื่อยืนยัน: `DELETE /api-system/ai-providers/:id`, toast สำเร็จ, โหลดรายการใหม่ ถ้าล้มเหลวจะแสดง toast error พร้อมรายละเอียดจาก server

## 3. `AiProviderEditDialog`: โหมดสร้าง

เปิดจาก "Add provider" `code` แก้ไขได้ที่นี่ และที่นี่เท่านั้น ค่าเริ่มต้น: ฟิลด์ข้อความว่าง, ไม่มีไอคอนในตัว, `is_active` เปิด, `default_enabled_for_bu` ปิด, `sort_order` = ค่าสูงสุดปัจจุบัน + 10 (provider ใหม่จึงไปอยู่ท้ายสุด) `POST /api-system/ai-providers` พร้อมฟิลด์ต่าง ๆ บวก `code`; สำเร็จแล้วแสดง toast "created" ปิด dialog และโหลดรายการใหม่

## 4. `AiProviderEditDialog`: โหมดแก้ไข

dialog เดียวกันที่โหลด row เข้ามา `code` ถูก disable `PATCH /api-system/ai-providers/:id` ส่งฟิลด์ที่แก้ได้บวก `doc_version` ของ row; เมื่อเกิด version conflict dialog แสดง toast conflict ที่ใช้ร่วมกัน ปิดตัวเอง และโหลดใหม่ ความล้มเหลวอื่นแสดงเป็น alert สีแดงแบบ inline ที่ด้านบนของ dialog ("Could not save: ...")

หัว dialog แสดง preview ของไอคอนแบบ live (`icon_url` ถ้าขึ้นต้นด้วย `https://` ไม่งั้นใช้ตัวในตัว) ส่วนต่าง ๆ:

### 4.1 Provider (identity)

| ฟิลด์ | Control | หมายเหตุ |
|---|---|---|
| Name (`label`) | text, สูงสุด 100 | จำเป็น |
| Code | text, สูงสุด 50, monospace | เฉพาะตอนสร้าง; ขอบแดง + ข้อความเมื่อไม่ตรง `^[a-z0-9][a-z0-9_-]{1,49}$`; hint "a-z, 0-9, _ or -, 2 to 50 characters. Cannot be changed after creation." |
| Built-in icon | select: None + `claude`, `chatgpt`, `gemini`, `deepseek`, `grok`, `google` (แต่ละตัวมีเครื่องหมายของมัน) | |
| Icon URL | text, placeholder `https://` | hint "https only. When set, it is shown instead of the built-in icon." ไม่ validate ฝั่ง client นอกจาก preview ที่หัว dialog |

### 4.2 Where it opens (link)

`url_template`, monospace, placeholder `https://example.com/search?q={query}` ด้านล่างมีบรรทัด **Preview** แสดง template โดยแทน `{query}` ด้วยข้อความ `sample prompt` ที่ URL-encode แล้ว

### 4.3 Default prompt

textarea แบบ monospace (8 บรรทัด) พร้อมตัวนับ `length/4000` แบบ live ที่เปลี่ยนเป็นสีแดงเมื่อเกินขีดจำกัด hint อธิบาย token `{items}`

### 4.4 Availability

ปุ่มสลับ ON/OFF สองอัน (render เป็น badge ที่มี `role="switch"` เพราะ repo ไม่มี component switch): **Active** (hint "Inactive providers are hidden in every business unit.") และ **On by default for business units** (hint "Applies to business units that have not chosen for themselves.") แล้วตามด้วยช่องตัวเลข **Sort order**

**Save เปิดใช้งานเมื่อ:** ไม่ได้กำลังบันทึกอยู่, `code` ถูกต้อง (จริงเสมอในโหมดแก้ไข), `label`, `url_template` และ `prompt` ไม่ว่างเปล่า, ความยาว prompt ไม่เกิน 4000 และ `sort_order` เป็นจำนวนเต็มไม่ติดลบ

## 5. UI state ที่เก็บถาวร

ไม่มี หน้าไม่เขียน key ของ `localStorage` และ dialog รีเซ็ตทุกฟิลด์ทุกครั้งที่เปิด

## 6. Screenshots

> **TODO:** Screenshots เลื่อนไปทำในชุด screenshot ของ Platform ที่จะมาถึง ดู `.specs/2026-05-17-screenshots-coverage-checklist.md` สำหรับแผนครอบคลุมข้ามโมดูล

## 7. แหล่งอ้างอิง

- `../carmen-backstage/src/pages/AiProviderManagement.tsx` (รายการ), `src/pages/aiProviders/AiProviderEditDialog.tsx` (dialog; `CODE_RE`, `ICON_KEYS`, `PROMPT_MAX` อยู่ต้นไฟล์), `src/services/aiProviderService.ts`
- i18n key: `pages.aiProviders.*` ใน `src/i18n/en.ts`
- หน้าข้างเคียง: [AI Providers](/th/platform/ai-providers), [Data Model](/th/platform/ai-providers/data-model)
