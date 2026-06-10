---
title: Broadcasts — หน้าจอ UI (UI Screens)
description: หน้าจอ BroadcastCompose หน้าเดียว — แท็บ target, UserMultiSelect และ select ของ BU, ตัวนับ title/message, type preset พร้อม input แบบ custom, ส่งทันทีเทียบกับกำหนดเวลา และ dialog ยืนยันราย target mode
published: true
date: 2026-06-10T16:00:00.000Z
tags: book/platform, broadcasts, ui
editor: markdown
dateCreated: 2026-06-10T16:00:00.000Z
---

# Broadcasts — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `BroadcastCompose` (`/broadcasts/new`) — หน้าจอเดียวของโมดูล; ไม่มี route ของ list/edit &nbsp;·&nbsp; **ฟอร์ม:** การ์ด Compose ใบเดียว — แท็บ Target · ตัวเลือกผู้รับแบบมีเงื่อนไข · Title (≤200) · Message (≤2000) · Type preset · แท็บ Send time &nbsp;·&nbsp; **Dialog:** ConfirmDialog ตัวเดียว หัวข้อและสไตล์แตกต่างกันตาม target mode &nbsp;·&nbsp; **คีย์ลัด:** Ctrl/Cmd+S ส่ง · Escape รีเซ็ต &nbsp;·&nbsp; **สถานะ UI ที่จดจำ:** ไม่มี

## 1. ภาพรวม

Broadcasts เป็นโมดูลแบบหน้าจอเดียว: `/broadcasts/new` → `BroadcastCompose`, การ์ด Compose ใบเดียวใต้ header ที่มีไอคอน Megaphone ("Send Broadcast" / "Push a notification to all users, specific users, or a business unit.") ไม่มี list แบบ Management, ไม่มี toggle view/edit, ไม่มีเรคคอร์ดให้กลับมาดู — เป็นด้านกลับโดยเจตนาของโมดูล Platform อื่นทุกตัว เนื่องจากไม่มีอะไรถูกโหลด (นอกจากตัวเลือกของ BU) หน้านี้จึงไม่มี skeleton state และไม่จดจำสถานะ UI ใด ๆ ใน `localStorage`

องค์ประกอบมาตรฐานยังคง apply: `useUnsavedChanges` ติดอาวุธ navigation guard ทันทีที่ field ใดเบี่ยงจากค่า default ของมัน (รวมถึงผู้รับที่เลือกไว้), Ctrl/Cmd+S trigger การส่งและ Escape trigger การรีเซ็ต (ทั้งคู่ถูกระงับขณะการส่งกำลังดำเนินอยู่หรือ dialog ยืนยันเปิดอยู่), error ปรากฏเป็นข้อความสีแดงราย field บวก toast และ Debug Sheet เฉพาะ dev (ปุ่มลอยสีเหลืองอำพัน, `NODE_ENV === 'development'`) แสดง response ล่าสุดของ API พร้อมปุ่ม Copy JSON

## 2. ฟอร์ม Compose

field จากบนลงล่าง; ทุกอย่างยกเว้นแถบแท็บสองแถบเป็น controlled input ธรรมดา

### 2.1 แท็บ Target

แถบ `Tabs` ที่มีสามตัวเลือก — **All users** (ไอคอน Globe, `system_all`, ค่าเริ่มต้น), **Specific users** (ไอคอน Users, `system_users`), **Business Unit** (ไอคอน Building2, `bu`) การสลับแท็บสลับ section แบบมีเงื่อนไขด้านล่างของมัน (ตัวเลือกผู้รับเทียบกับ select ของ BU) แต่**ไม่เคลียร์ state ที่กรอกไว้แล้ว** — ดูกรณีพิเศษเรื่องผู้รับค้าง (stale recipients) ใน [Permissions](./permissions.md) §4

แท็บ system สองตัว render เฉพาะเมื่อ session ถือ `broadcast.send` (`canSendSystem`) โดยมี effect บังคับเป็นโหมด `bu` เมื่อไม่ถือ เนื่องจากตัว route เองต้องการ key เดียวกัน การ gate ภายใน component นี้จึงเป็น defensive code ที่ไปไม่ถึงในวันนี้ — ผู้ใช้ทุกคนที่เปิดหน้านี้ได้เห็นทั้งสามแท็บ

### 2.2 ผู้รับ (เฉพาะ `system_users`)

`UserMultiSelect` — combo box แบบ badge-input ที่หนุนด้วย Users API:

- การพิมพ์ (debounce 400 ms, dropdown เปิดตอน focus — ตัว debounce ยังยิงการค้นหาแบบ query ว่างตอนเปิดด้วย ดังนั้นผู้ใช้ 20 คนแรกมักถูกเติมก่อนการกดคีย์ใด ๆ) ค้นหาผ่าน `userService.getAll({ page: 1, perpage: 20, search })` — 20 ผลลัพธ์แรกที่ match ตามชื่อหรืออีเมล แต่ละตัว render เป็นชื่อเหนืออีเมลแบบ muted ชื่อสำหรับแสดงคือ `firstname middlename lastname` โดย fall back ไป `name`, `email` แล้วจึง id ดิบ
- การคลิกผลลัพธ์เพิ่ม badge ที่ลบได้ (row ที่ถูกเลือกแล้วเป็น disabled และติด tag "Selected"); Backspace ขณะ query ว่างลบ badge ตัวสุดท้าย; Escape ปิด dropdown empty state: "Type to search users" / `No users match "<query>"`; การค้นหาที่ล้มเหลว render error ของ API ที่ parse แล้วแบบ inline ใน dropdown
- การ validate: ต้องมีผู้รับอย่างน้อยหนึ่งคน ("Pick at least one recipient") บังคับใช้ก่อน submit และถูกเคลียร์ทันทีที่มีการเพิ่มหนึ่งคน

### 2.3 Business Unit (เฉพาะ `bu`)

native select ที่โหลดครั้งเดียวตอน mount ผ่าน `businessUnitService.getAll({ page: 1, perpage: 100 })` — สังเกตเพดาน: มีเพียง **BU 100 ตัวแรก**เท่านั้นที่ถูกเสนอ ตัวเลือกถูก filter เป็น BU ที่ active (`is_active !== false`) และ render เป็น `Name (CODE)`; ค่าที่ submit คือ **code** ขณะกำลังโหลด select เป็น disabled พร้อม placeholder "Loading business units…"; การโหลดที่ล้มเหลว render ข้อความ error พร้อมปุ่ม **Retry** แบบ inline ที่ยิง fetch ใหม่ การ validate: จำเป็น ("Choose a business unit")

### 2.4 Title และ Message

| Field | Control | ขีดจำกัด | หมายเหตุ |
|---|---|---|---|
| Title | Text input, placeholder "Scheduled maintenance" | 200 | ตัวนับ `N/200` แบบ live; input ตัดทิ้งแบบ hard ที่ขีดจำกัด (`slice(0, 200)`) ดังนั้น error เรื่องความยาวเกินปกติแล้วไปถึงไม่ได้ด้วยการพิมพ์ จำเป็น ("Title is required") |
| Message | Textarea, 6 แถว, placeholder "The system will be unavailable from 02:00 to 03:00 UTC." | 2000 | ตัวนับ `N/2000` แบบ live, การตัดทิ้งแบบ hard เช่นเดียวกัน จำเป็น ("Message is required") |

ทั้งคู่ถูก trim ก่อนการ validate และการ submit

### 2.5 Type

native select ที่มีห้า preset — Info (ค่าเริ่มต้น), Warning, Critical, Maintenance, **Other…** สี่ตัวแรก resolve ฝั่ง client เป็น `SYS_<PRESET>` (โหมด system) หรือ `BU_<PRESET>` (โหมด BU) ณ เวลา submit การเลือก Other… เผย input ของ custom type (placeholder `CUSTOM_TYPE`) ที่**อัพเปอร์เคสขณะพิมพ์**และ submit แบบ verbatim โดยไม่มี prefix การ validate (เฉพาะ Other…): จำเป็น, ≤50 ตัวอักษร, ต้อง match `[A-Z0-9_]+` ("Use uppercase letters, digits, and underscores only")

### 2.6 Send time

แถบ `Tabs` แถบที่สอง — **Send immediately** (ไอคอน Send, ค่าเริ่มต้น) เทียบกับ **Schedule for later** (ไอคอน Calendar) โหมด schedule เผย input แบบ native `datetime-local`; การ validate ต้องการค่า ("Pick a date and time"), ค่าที่ parse ได้ ("Invalid date/time") และเวลาที่เป็น**อนาคต** ("Scheduled time must be in the future" — ตรวจสอบกับ `Date.now()` ณ เวลา validate) ค่าถูกแปลงเป็น UTC ISO string (`new Date(v).toISOString()`) ใน payload

## 3. flow การส่ง

### 3.1 การ validate → การยืนยัน

ปุ่ม **Send** (footer, `<Can permission="broadcast.send">`; label พลิกเป็น **Schedule** ในโหมด schedule, spinner ขณะกำลังส่ง) รันการ validate ก่อน — ความล้มเหลว mark ตัว field และ toast "Please fix the highlighted fields" เมื่อสำเร็จ `ConfirmDialog` จะเปิด:

| Target mode | หัวข้อ dialog | ปุ่มยืนยัน |
|---|---|---|
| `system_all` | **Send to ALL users?** | สไตล์ **destructive** (สีแดง) |
| `system_users` | Send to N user(s)? | ค่าเริ่มต้น |
| `bu` | Send to {BU name}? (fall back ไปที่ code) | ค่าเริ่มต้น |

คำอธิบายขึ้นต้นด้วยเรื่องเวลา — "Will be delivered immediately." หรือ "Scheduled for `<local datetime>`." — แล้วตามด้วยกลุ่มผู้ชม: หัวข้อที่กำลังถูกส่ง (`system_all`), ชื่อผู้รับห้าคนแรกบวก "and N more" (`system_users`) หรือ "Business unit: Name (CODE)" (`bu`) label ของปุ่มยืนยันคือ **Send** หรือ **Schedule** ให้ตรงกับโหมด

### 3.2 Submit, สำเร็จ, ล้มเหลว

การยืนยัน post `BroadcastBuPayload` ไป `/api/notifications/broadcasts/bu` ในโหมด BU ไม่เช่นนั้น post `BroadcastSystemPayload` ไป `.../broadcasts/system` (พร้อม `userIds` เมื่อมีการเลือกผู้รับไว้ — ดู [Data Model](./data-model.md) §5 สำหรับ shape ของ payload) เมื่อสำเร็จ: toast "Broadcast sent" หรือ "Broadcast scheduled for `<local datetime>`", **ฟอร์มทั้งหมดรีเซ็ต**กลับเป็นค่า default และ raw response ถูกเก็บไว้สำหรับ Debug Sheet เมื่อล้มเหลว: `parseApiError` toast ข้อความและ map field error ใด ๆ ลงบนฟอร์ม; dialog ปิดในทั้งสองกรณี ไม่มีการ redirect — หน้าจอพร้อมสำหรับ broadcast ถัดไป และตัวที่เพิ่งส่งไปมองไม่เห็นที่ไหนเลยใน SPA นี้

### 3.3 รีเซ็ต, คีย์ลัด, guard ของการเปลี่ยนแปลงที่ยังไม่ save

**Reset** (ปุ่ม outline ข้าง Send, หรือ Escape) เคลียร์ฟอร์ม, ผู้รับ และ field error โดยไม่มีการยืนยัน — การปกป้องแบบ confirm-before-discard มีอยู่เฉพาะกับ*การนำทาง*เท่านั้น ผ่าน `useUnsavedChanges` ซึ่งติดอาวุธเมื่อ field ใดต่างจากค่า default ของมัน Ctrl/Cmd+S เทียบเท่ากับการคลิก Send (validate ก่อน แล้วจึง dialog)

## 4. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/BroadcastCompose.tsx` — หน้าจอทั้งหมด: ค่าคงที่ (`TITLE_MAX`, `MESSAGE_MAX`, `TYPE_CUSTOM_RE`), `resolveType`, ตัวสร้าง payload, `validate`, หัวข้อ/คำอธิบายของ dialog ยืนยัน, Debug Sheet
- `../carmen-platform/src/components/UserMultiSelect.tsx` — debounce, ขนาดหน้า, fallback ของชื่อสำหรับแสดง, การโต้ตอบแบบ badge/คีย์บอร์ด
- `../carmen-platform/src/services/broadcastService.ts` — `sendSystem` / `sendBu`
- `../carmen-platform/src/components/KeyboardShortcuts.tsx`, `src/hooks/useUnsavedChanges.ts` — คีย์ลัดและ navigation guard
- `../carmen-platform/src/App.tsx` (route), `src/components/Layout.tsx` ("Send Broadcast", กลุ่ม Content)

**Cross-link:** [หน้า landing ของ Broadcasts](/th/platform/broadcasts) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
