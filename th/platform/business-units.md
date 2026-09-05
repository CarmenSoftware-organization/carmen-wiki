---
title: หน่วยธุรกิจ (Business Units)
description: เอนทิตีต่อ property/ต่อโรงแรม แก้ไขบนฟอร์มหกแท็บ (General/Location/Formats/Technical/Users/Licenses) ครอบคลุมข้อมูลระบุตัวตน รูปแบบ การผูก database pool และรายชื่อผู้ใช้/license ที่ผูกกับ BU
published: true
date: 2026-09-05T10:00:00.000Z
tags: platform/business-units, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# หน่วยธุรกิจ (Business Units)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจอ authoring ที่ใช้สร้างและตั้งค่าเอนทิตีปฏิบัติการที่ Carmen เรียกว่า **business unit** (BU) — หนึ่งแถวต่อหนึ่งโรงแรม/property/นิติบุคคล พร้อมฟิลด์ที่ขับเคลื่อนทั้งบริบทของ tenant ใน inventory app และการมอบหมาย role/license ของผู้ใช้ในแพลตฟอร์ม &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA; การเข้าถึงของ operator ถูก gate ด้วย **permission key `cluster.*` ที่ reuse มา** ([rbac](/th/platform/rbac)) — ไม่มี key `business_unit.*` &nbsp;·&nbsp; **รายการใน Nav:** `permission: 'cluster.read'` — **ใช้ร่วมกับอีกสองรายการเมนู** ([clusters](/th/platform/clusters) และ [Tenant Migrations](/th/platform/business-units/tenant-migrations)) แทนที่จะมี key เป็นของตัวเอง ดังนั้นชื่อ permission จึงไม่บอกใบ้เลยว่ามันเปิดหน้าจอนี้ได้ด้วย &nbsp;·&nbsp; **Feature flag:** `business_units` ตรวจสอบบนทั้งสาม route หลัง permission gate &nbsp;·&nbsp; **`superAdminOnly`:** ไม่ &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `business_unit` (ฟิลด์ระบุตัวตน `code` — ตอนนี้ระบบสร้างให้เอง — `name`, `alias_name`, `is_hq`, `is_active`; บล็อกข้อมูลติดต่อสำหรับ hotel/company; ฟิลด์ภาษี; ฟิลด์รูปแบบวันที่/เวลา/ตัวเลข; `calculation_method`, `default_currency_id`; `database_pool_id`/`db_schema`; `config[]` แถว key/value; branding `logo_file_token`/`avatar_file_token`) บวกกับ `tb_business_unit_license` (ledger ที่นั่งต่อ BU ที่แทนที่ `max_license_users` เดิม) และตาราง join BU-to-user ที่ถือ `role` ระดับ BU เป็น `admin` หรือ `user` &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

Business unit คือ tenant ปฏิบัติการของ Carmen platform: หนึ่ง BU คือหนึ่งโรงแรม หนึ่ง property หรือหนึ่งนิติบุคคลที่ซื้อ รับ นับ และเบิกใช้ inventory หน้ารายการที่ `/business-units` (`BusinessUnitManagement.tsx`) เป็นแคตตาล็อกแบบ server-paginated ค้นหาได้ มี facet สำหรับ Active/Inactive และรายการที่ถูก soft-delete พร้อมส่งออก CSV ได้ และมีแถบสรุป **Overview** (`BuSummary` ตอนนี้อ่านจาก endpoint สรุปเฉพาะ `GET /api-system/business-units/summary` — จำนวนรวม/active/inactive/archived และจำนวน cluster ที่แตกต่างกันที่ครอบคลุม)

หน้าแก้ไขที่ `/business-units/:id/edit` และ `/business-units/new` (`BusinessUnitEdit.tsx`) ถูกเขียนใหม่ **สองครั้ง** นับตั้งแต่ sync ครั้งก่อน ครั้งแรกจากการ์ด `CollapsibleSection` เก้าใบในกริดสองคอลัมน์ ให้เป็นหน้าเอกสารเดียวแบบแก้ไข-in-place ("one-document") ครั้งที่สอง — ซึ่งเป็นการเปลี่ยนแปลงที่ sync รอบนี้บันทึกไว้ — จากหน้าเอกสารเดียวนั้น ให้เป็น **เอกสารหกแท็บ**: General, Location, Formats, Technical, Users, Licenses อยู่หลังแถบ identity ที่ปักไว้และ `TabStrip` แบบ sticky ยังไม่มี toggle read/edit เลย — boolean `canEdit` ตัวเดียว (`cluster.create` สำหรับ BU ใหม่, `cluster.update` ที่ scope ด้วย `cluster_id` สำหรับ BU ที่มีอยู่แล้ว) gate ทุก field บนทุกแท็บ; แต่ละ field ยังคง commit ตอน blur/Enter และ revert ตอนกด `Escape` ผ่าน control `InlineField` แบบคลิกเพื่อแก้ไขที่ใช้ร่วมกัน เหมือนเดิมทั้งสองรอบการเขียนใหม่ แท็บ Users และ Licenses จะถูกละออกจาก tab strip ทั้งหมดตอนสร้าง BU ใหม่ เพราะทั้งสองต้องมีแถวอยู่แล้วก่อน แถบล่างแบบ sticky แสดง Save Changes/Cancel เมื่อเอกสารมีการเปลี่ยนแปลง (หรือแสดงเสมอตอนสร้างใหม่); `Ctrl/⌘+S` ยังคง save ได้และ `Escape` ยังคง cancel ได้ทั้งหน้าผ่าน shared keyboard-shortcut hook — ยืนยันแล้วว่ายังใช้งานอยู่จริงใน source ปัจจุบัน: shortcut save เช็ก `canEdit` ซ้ำเองก่อนเรียก Save เสมอ (ปุ่ม disable อย่างเดียวไม่ใช่ด่านป้องกัน) ส่วน shortcut cancel จะทำงานเฉพาะกับ BU ที่มีอยู่แล้วและมีการเปลี่ยนแปลงยังไม่บันทึก — ไม่ทำอะไรเลยตอนสร้างใหม่ การบันทึกได้รับการป้องกันด้วย token optimistic-lock `doc_version` แบบเดียวกับ [clusters](/th/platform/clusters)

แต่ละ BU เป็นของ **cluster** หนึ่ง cluster เท่านั้น (foreign key `cluster_id` เลือกจาก dropdown ในแท็บ General) flow "สร้าง BU" เริ่มได้จากหน้ารายการ BU หรือจากหน้าแก้ไข cluster ซึ่ง navigate ไปที่ `/business-units/new?cluster_id=<id>` เพื่อ preselect parent ให้ มีสี่เรื่องที่เปลี่ยนแปลงมากพอที่ต้องพูดถึงตั้งแต่ต้น แต่ละอย่างมีรายละเอียดเต็มในหน้าย่อย:

1. **`code` ไม่ให้ผู้ใช้พิมพ์อีกต่อไป** ฟอร์มสร้างไม่มีช่อง code เลย — backend สุ่มรหัส 8 ตัวอักษรให้ พร้อม retry เมื่อชนกัน; หน้าแก้ไขแสดง code แบบอ่านอย่างเดียว ดู [Data Model](/th/platform/business-units/data-model) §2.1 และ [UI Screens](/th/platform/business-units/ui-screens) §3–4.1
2. **แท็บ Technical มีปุ่มสุ่มชื่อ schema** BU ไม่ถือ credential ฐานข้อมูลของตัวเองอีกต่อไป (`db_connection` หายไปแล้ว) — มันชี้ไปที่ record `tb_database_pool` ที่ใช้ร่วมกัน และระบุ `db_schema` ของตัวเอง ซึ่งปุ่ม "Generate schema" ช่วยเติมชื่อสุ่มที่ชนกันได้ยากมากให้ ดู [UI Screens](/th/platform/business-units/ui-screens) §4.4
3. **Licenses เป็นแท็บของตัวเองแล้ว** แยกออกจาก Users — ที่นั่ง (ledger การซื้อรายตัวต่อ BU) กับรายชื่อผู้ใช้ตอบคำถามคนละเรื่อง จึงไม่ใช้แท็บร่วมกันอีกต่อไป ดู [UI Screens](/th/platform/business-units/ui-screens) §4.7
4. **แท็บ Licenses มีปุ่ม "New subscription"** ที่ gate ด้วย `subscription.manage` แทนที่จะเป็น `canEdit` ของหน้านี้เอง ลิงก์ตรงไปฟอร์ม subscription เต็มหน้าที่ scope ไว้กับ BU และ cluster นี้แล้ว

นอกจากฟิลด์ระบุตัวตนและข้อมูลติดต่อ BU ยังเก็บค่า locale ที่ inventory runtime อ่านจะใช้ — `date_format`, `time_format`, `timezone`, ตัว format แบบ JSON `amount_format`/`quantity_format`/`recipe_format` ที่ default เป็น `th-TH`, `calculation_method` และ `default_currency_id` (dropdown ของสกุลเงินระดับ tenant ของ BU เอง โหลดแบบ lazy เมื่อรู้ `code` ของ BU แล้ว) — บวกกับ array `config[]` ที่เป็นแถว key/value แบบ free-form รายละเอียดต่อฟิลด์และพฤติกรรมของหน้าจออยู่ในหน้าย่อย — หน้า landing นี้เพียงปูทาง

## 2. บริบททางธุรกิจ

ในธุรกิจโรงแรม หน่วยที่เล็กที่สุดที่มีบัญชีของตัวเอง มีสกุลเงินของตัวเอง และมี supply chain ระดับท้องถิ่นของตัวเอง คือ property — โรงแรมเดี่ยวภายในกลุ่มแบรนด์ Carmen จึงโมเดลสิ่งนี้เป็น business unit ทุก inventory transaction (GRN, store requisition, physical count, spot check) อยู่ในขอบเขตของ BU เดียว ทุกรายงานรันกับ schema ของ BU เดียว และผู้ใช้ทุกคนได้รับสิทธิ์เข้าถึง BU หนึ่งหรือมากกว่าหนึ่ง พร้อม role ที่ใช้ภายในแต่ละ BU แถว `business_unit` จึงถือมากกว่าข้อมูลระบุตัวตน มันถือค่า locale ที่ inventory UI แสดง (รูปแบบวันที่และตัวเลข, timezone, default currency) ถือ knob ของการคำนวณต้นทุน (`calculation_method`) ที่ valuation engine ใช้อ้างอิง และถือตัวชี้ (`database_pool_id`/`db_schema`) ไปยังเซิร์ฟเวอร์ฐานข้อมูลที่ใช้ร่วมกันซึ่งโฮสต์ schema ของ tenant นี้ — แพลตฟอร์มไม่เก็บ credential การเชื่อมต่อต่อ BU โดยตรงอีกต่อไป

ที่นั่งก็ไม่ใช่เพดานเดียวอีกต่อไปเช่นกัน จากที่ schema เคยถือ integer `max_license_users` ตัวเดียว ความจุผู้ใช้ของ BU ตอนนี้เป็น ledger การซื้อแบบมีวันที่ (`tb_business_unit_license`) — หนึ่งแถวต่อหนึ่งสัญญาที่นั่ง รวมกันจากทุกแถวที่ active อยู่ในขณะนั้น แท็บ General ของหน้าแก้ไขแสดงตัวเลขที่ได้แบบอ่านอย่างเดียว; แท็บ Licenses เป็นที่ที่แถวการซื้อเหล่านั้นถูกดูจริง (การสร้าง/แก้ไขยังคงทำที่ฟอร์ม License Center เต็มหน้า ไม่ใช่แบบ inline บนหน้านี้)

เนื่องจาก BU ยังเป็นจุดที่ผู้ใช้กลายเป็นมีความหมายในเชิงปฏิบัติการ แท็บ Users ของหน้าแก้ไขจึงทำหน้าที่เป็น workbench สำหรับ assign ผู้ใช้ด้วย แสดงทุกคนที่มีสิทธิ์เข้าถึง BU นี้ พร้อม **BU role** (`admin` หรือ `user`) ที่ orthogonal กับ RBAC assignment ระดับแพลตฟอร์มบนบัญชีผู้ใช้เอง ([rbac](/th/platform/rbac)) สมาชิก BU ใหม่ถูกเลือกจาก cluster ที่เป็นแม่ของ BU นั้น — ผู้ใช้ต้องอยู่ใน cluster ก่อนถึงจะถูกเพิ่มเข้า BU ภายใน cluster ได้ badge "Shared" บนแถวผู้ใช้จะบอกว่าสมาชิกภาพนั้นใช้ร่วมกับ BU อื่นใน cluster เดียวกัน (การลบออกจากที่นี่ที่เดียวจะไม่คืนที่นั่งระดับ cluster) — เป็นของใหม่นับตั้งแต่ sync ครั้งก่อน และขึ้นอยู่กับฟิลด์ที่ backend ส่งมาแบบ optional คือ `frees_seat` ซึ่งอาจยังไม่ถูกเติมในทุก environment

การ์ด advanced ในแท็บ Technical ขยาย BU ให้ไปไกลกว่าการตั้งค่าธรรมดา เข้าสู่งานปฏิบัติการฐานข้อมูลระดับ tenant ไม่เปลี่ยนแปลงการ gate จาก sync ครั้งก่อน: **Tenant Migrations** ตรวจสอบและ apply database schema migration ที่ค้างอยู่กับฐานข้อมูล tenant ของ BU นั้นเอง; **Tenant Seed** รัน seed script กับฐานข้อมูลนั้น; และ **Interface Entitlement** ควบคุมว่า BU นี้มีสิทธิ์แสดง interface/brand ใดบ้าง (เลือกว่างเปล่า = ไม่จำกัด) ไม่มีใบไหน render-gate เลย — ทุกเซสชันที่มีสิทธิ์แก้ไข BU เห็นการ์ดทั้งสามเมื่อ BU มีอยู่แล้ว มีเพียง action ที่*เปลี่ยนแปลงข้อมูล*เท่านั้น (และปุ่ม check status ของสองใบแรก) ที่ต้องการ `isSuperAdmin`

## 3. แนวคิดสำคัญ

- **Business unit (BU)**: หนึ่งแถวใน `business_unit` ที่แทนหนึ่งโรงแรม/property/นิติบุคคล ทุก inventory transaction เป็นของ BU เดียว ทุกรายงานรันกับ BU เดียว
- **Cluster membership**: ทุก BU มี `cluster_id` ที่ไม่ nullable เลือกจาก dropdown ของ cluster ในแท็บ General หน้าแก้ไข cluster สามารถเปิด flow สร้าง BU โดย preselect `cluster_id` ผ่าน query parameter `/business-units/new?cluster_id=<id>`
- **Code (`code`)**: รหัสสั้น ที่ unique **ทั่วทั้งแพลตฟอร์ม** ไม่ใช่แค่ภายใน cluster (partial-unique index ที่เพิ่มมาใหม่ตั้งแต่ sync ครั้งก่อน — ดู [Data Model](/th/platform/business-units/data-model) §2.1) **ไม่ให้ผู้ใช้กรอกอีกต่อไป**: backend สุ่มรหัส Crockford-base32 8 ตัวให้ตอนสร้าง พร้อม retry เมื่อชนกัน; ฟิลด์นี้อ่านอย่างเดียวบนหน้าแก้ไข และ backend เพิกเฉยหากส่งค่ามาตอนอัปเดต
- **HQ flag (`is_hq`)**: ระบุว่า BU นี้เป็นสำนักงานใหญ่ภายใน cluster ของตน — badge "HQ" ที่คลิกได้ในแถบ identity (toggle ได้ตรง ไม่มี checkbox/เซกชันแยก) ความหมายขึ้นอยู่กับโมดูลที่ใช้ค่านี้
- **Active flag (`is_active`)**: สลับว่า BU เปิดใช้งานเชิงปฏิบัติการหรือไม่ — badge ที่คลิกได้ในแถบ identity ไม่ใช่ checkbox ในฟอร์ม BU ที่ inactive ยังแก้ไขได้ในหน้า admin แต่จะถูกกรองออกจากการเลือกตอน runtime ปกติ หน้ารายการแสดง Active/Inactive เป็น chip กรอง
- **ที่อยู่ hotel/company แบบมีโครงสร้าง**: คอลัมน์แบบมีโครงสร้างสิบคอลัมน์ต่อฝั่ง — `*_address_line1`, `*_address_line2`, `*_sub_district`, `*_district`, `*_city`, `*_province`, `*_postal_code`, `*_country`, `*_latitude`, `*_longitude` — ทั้งกลุ่ม Hotel และกลุ่ม Company บนแท็บ Location ปุ่ม **Copy from hotel address** คัดลอก field ที่อยู่ทั้งสิบของ hotel ไปยัง field ของ company แบบทางเดียว
- **Tax information**: `tax_no` และ `branch_no` เก็บเลขประจำตัวผู้เสียภาษีของไทยและรหัสสาขาที่ใช้บนเอกสารพิมพ์
- **รูปแบบวันที่/เวลาและตัวเลข**: `date_format`, `date_time_format`, `time_format`, `long_time_format`, `short_time_format`, `timezone` บวกกับ formatter แบบ JSON `amount_format`/`quantity_format`/`recipe_format`/`perpage_format` — ทั้งหมดอยู่ในแท็บ Formats แต่ละ formatter default เป็น `{"locales":"th-TH","minimumIntegerDigits":2}`
- **Calculation settings**: `calculation_method` (`average`/`fifo` — ใช้โดย inventory valuation engine) และ `default_currency_id` — `<select>` ที่ populate จากตาราง currency ระดับ tenant ของ BU เอง โหลดแบบ lazy เมื่อรู้ code ของ BU แล้ว โดย fallback เป็น input ข้อความอิสระสำหรับ UUID หากดึงข้อมูลไม่สำเร็จ
- **Configuration array (`config[]`)**: รายการแบบมีลำดับของแถว `{ key, value, datatype }` แบบ free-form บนแท็บ Technical เก็บเป็น JSON array ใช้โดย inventory app สำหรับ feature toggle ระดับ BU และการตั้งค่า integration หน้า admin ไม่บังคับ schema
- **Database pool + schema (`database_pool_id`/`db_schema`)**: แทนที่ JSON blob `db_connection` เดิมทั้งหมด BU ชี้ไปที่ record `tb_database_pool` ที่แพลตฟอร์มจัดการร่วมกัน แล้วระบุชื่อ schema ของตัวเองในนั้น host/port/username/password อยู่ที่ record ของ pool เท่านั้น ไม่เคยอยู่บนหน้านี้ ปุ่ม "Generate schema" ช่วยเติมช่อง schema ด้วยชื่อสุ่มขึ้นต้นด้วย `bu_`
- **Branding (logo + avatar)**: แต่ละ BU มี **logo** สี่เหลี่ยมผืนผ้าและ **avatar** สี่เหลี่ยมจัตุรัส เก็บเป็น file token และ API คืนค่าเป็น presigned object ฝังในตัว การอัปโหลดทำบน Branding section ของแท็บ General; หน้ารายการแสดง `BrandMark` avatar เล็ก ๆ ข้างชื่อ BU (นำกลับมาใช้ตั้งแต่ sync ครั้งก่อน ตรงกับการเปลี่ยนแปลงเดียวกันบน [clusters](/th/platform/clusters))
- **Optimistic concurrency (`doc_version`)**: `tb_business_unit` มี counter `doc_version`; หน้าแก้ไขจะส่งค่านี้กลับไปทุกครั้งที่ `PUT` และแสดง toast แจ้ง conflict + โหลดใหม่เมื่อเจอ `409` ที่ล้าหลัง
- **คอลัมน์ audit**: หน้ารายการแสดงคอลัมน์ Created และ Updated (timestamp พร้อมชื่อผู้กระทำ) ตอนนี้ทั้งหน้ารายการและหน้าแก้ไขอ่านค่า audit ทุกตัวผ่าน helper ที่ใช้ร่วมกัน `normalizeAudit()` (`src/utils/audit.ts`) ซึ่งลองอ่าน object `audit` แบบ nested ก่อนเสมอ แล้วค่อย fallback ไปที่ shape แบบ flat รุ่นเก่า (`created_at`/`created_by_name` หรือ `created_by` ฯลฯ) เฉพาะเมื่อค่าฝั่ง nested ไม่มีหรือว่างเปล่า — ไม่ใช่ทางกลับกัน แถว Updated จะแสดงก็ต่อเมื่อ record ถูกแก้ไขจริง ตัดสินจากการมีชื่อผู้แก้ไข หรือ — เมื่อไม่มีชื่อ — เวลาที่ต่างจากเวลาสร้าง ไม่ใช่การเทียบ `updated_at === created_at` ตรง ๆ
- **ที่นั่ง (`tb_business_unit_license`)**: ledger การซื้อแบบมีวันที่ หนึ่งแถวต่อหนึ่งสัญญาที่นั่ง แทนที่ integer `max_license_users` ที่ถูกถอดออก รวมกันจากแถวที่ active เป็นตัวเลข "Max users" แบบอ่านอย่างเดียวบนแท็บ General; ถูกดู (ไม่ใช่แก้ไข) บนแท็บ Licenses ซึ่งลิงก์ออกไปฟอร์ม License Center เต็มหน้าสำหรับสร้าง/แก้ไขแถวจริง
- **BU role (`admin` vs. `user`)**: role ที่ผูกกับการ assign user-BU แต่ละครั้ง เก็บบนแถว join ของ BU-user คู่กับ `is_active` และ `is_default` role นี้ **orthogonal** กับ permission assignment ของ Platform RBAC บนบัญชีผู้ใช้ BU role ควบคุมพฤติกรรมของผู้ใช้ใน inventory app สำหรับ BU นั้น ไม่ใช่การเข้าถึง route ของ admin
- **Pattern เพิ่ม user จาก cluster**: สมาชิก BU ใหม่ถูกเลือกจากรายชื่อผู้ใช้ของ cluster ที่เป็นแม่ — ผู้ใช้ต้องเป็นสมาชิก cluster ก่อนถึงจะถูกเพิ่มเข้า BU ภายใน cluster ได้
- **Soft delete**: BU ถูก soft-delete ผ่าน `deleted_at` / `deleted_by_name` หน้ารายการมี toggle filter "Show soft-deleted business units" ต่างจาก [clusters](/th/platform/clusters) ตรงที่ action Delete ของหน้ารายการ BU ไม่มี client-side dependency guard

## 4. บทบาทและ Persona

การเข้าถึงเป็นแบบ permission-based ([Platform RBAC](/th/platform/rbac)) — แต่มี gotcha ที่สำคัญที่สุดของโมดูลนี้:

> **Gotcha การ reuse key: โมดูล Business Units ไม่มี permission key ของตัวเอง** route `/business-units`, `/business-units/new` และ `/business-units/:id/edit` reuse key **`cluster.read` / `cluster.create` / `cluster.update`**, รายการใน sidebar filter ด้วย `cluster.read` และ gate Delete ภายในหน้าใช้ `cluster.delete` — **ไม่มี key `business_unit.*`** ใน catalog เลย `cluster.read` เพียงตัวเดียวขับเคลื่อนสามรายการ sidebar — Clusters, Business Units และ Tenant Migrations — grant ใดที่เปิดโมดูล Clusters จึงเปิด Business Units และ Tenant Migrations ไปด้วย และแยกทั้งสามออกจากกันด้วย permission อย่างเดียวไม่ได้ (feature flag `business_units`/`tenant_migrations` ด้านล่างเป็นสวิตช์เปิด-ปิดต่อโมดูลตัวเดียวที่เหลืออยู่) grant `cluster.update` ที่ scope ไว้กับ cluster X ครอบคลุมการแก้ไข BU ของ cluster X มุมมองฝั่ง cluster ของ gotcha เดียวกันอยู่ใน [clusters permissions](/th/platform/clusters/permissions) §2

| Surface | ชนิดของ gate | Key | Scoped? |
|---|---|---|---|
| route `/business-units` | `requiredPermission` + `feature` | `cluster.read` + `business_units` | ไม่ |
| route `/business-units/new` | `requiredPermission` + `feature` | `cluster.create` + `business_units` | ไม่ |
| route `/business-units/:id/edit` | `requiredPermission` + `feature` | `cluster.update` + `business_units` | ไม่ |
| รายการ "Business Units" ใน sidebar | filter `permission` + `feature` | `cluster.read` / `business_units` | ไม่ |
| List: ปุ่ม Add Business Unit (หัวหน้าและ empty state) | `<Can>` | `cluster.create` | ไม่ |
| List: action Edit ของ row | `<Can>` | `cluster.update` | ใช่ — `clusterId={row.original.cluster_id}` |
| List: action View History ของ row | `<Can>` | `activity_log.read` | ใช่ — `clusterId={row.original.cluster_id \|\| UNRESOLVED_CLUSTER_ID}` |
| List: action Delete ของ row | `<Can>` | `cluster.delete` | ใช่ — `clusterId={row.original.cluster_id}` |
| หน้าแก้ไข: ทุก field บนทุกแท็บ ยกเว้นสองรายการด้านล่าง | `canEdit = isNew ? hasPermission('cluster.create') : hasPermission('cluster.update', {clusterId})` | `cluster.create` (ใหม่) / `cluster.update` (มีอยู่แล้ว) | ใช่สำหรับ BU ที่มีอยู่แล้ว — `clusterId={formData.cluster_id \|\| UNRESOLVED_CLUSTER_ID}` |
| แท็บ Technical: dropdown Database Pool | `<Can>` ซ้อนอยู่ใน `canEdit` | `database_pool.read` | ไม่ |
| แท็บ Licenses: ปุ่ม New subscription | ผู้เรียก (parent) เป็นคนส่งมา gate แยกจาก `canEdit` | `subscription.manage` | ไม่ |
| หน้าแก้ไข: การมองเห็นการ์ด Tenant Migrations / Tenant Seed / Interface Entitlement | ไม่มี — render เสมอเมื่อ `!isNew` ไม่ขึ้นกับ `canEdit` | — | ไม่ |
| หน้าแก้ไข: action ของการ์ดทั้งสามนั้น (ปุ่ม Deploy/Run/Save รวมถึงปุ่ม check status ของสองใบแรก) | `isSuperAdmin` (เช็กระดับปุ่มภายในแต่ละการ์ด แยกจาก `canEdit`) | — | ไม่ |

gate แบบ scoped (`clusterId`) จะ resolve กับ **cluster แม่** ของ BU — role assignment ที่ scope ไว้กับ cluster A จะ render Edit/Delete/View History ของ row เฉพาะบน BU ที่ `cluster_id` เป็น A เท่านั้น ขณะที่ route guard แบบ unscoped จะผ่านด้วย grant แบบ cluster-scoped ของ cluster ใดก็ได้ หมายเหตุ sentinel `UNRESOLVED_CLUSTER_ID`: เมื่อ `formData.cluster_id` ว่างเปล่า (BU ที่ไม่มี cluster หรือก่อนที่ dropdown Cluster จะมีค่าตอน create) check จะถูกจงใจรักษาไว้ที่ branch แบบ scoped ของ `checkPermission` (fail closed) แทนที่จะตกไปที่ branch แบบกว้าง "cluster ใดก็ได้"

มี permission ที่แคบกว่าอีกตัวหนึ่งซึ่ง gate control หนึ่งตัว**ภายใน**ขอบเขตของ `canEdit`: dropdown Database Pool บนแท็บ Technical ต้องการ `database_pool.read` เพิ่มเติม — เซสชันที่มี `cluster.update` บน BU นี้แต่ไม่มี `database_pool.read` ยังแก้อย่างอื่นได้ทั้งหมด แต่จะเห็นชื่อ pool กับ schema แบบอ่านอย่างเดียวพร้อมหมายเหตุอธิบายเหตุผล อัลกอริทึมการ resolve, ข้อยกเว้น bootstrap และ bypass ของ super-admin อยู่ใน [rbac permissions](/th/platform/rbac/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [clusters](/th/platform/clusters) — ทุก BU เป็นของ cluster หนึ่ง cluster ผ่าน `cluster_id` หน้าแก้ไข cluster เปิด flow สร้าง BU โดย preselect parent ผ่าน query parameter `/business-units/new?cluster_id=<id>` และ key `cluster.*` ที่ gate โมดูลนี้ถูกอธิบายไว้จากฝั่ง cluster ใน [clusters permissions](/th/platform/clusters/permissions)
- [users](/th/platform/users) — เป็นแหล่งของบัญชีผู้ใช้ที่ถูก assign เข้า BU ผ่านแท็บ Users สมาชิก BU ใหม่ถูกดึงจากรายชื่อผู้ใช้ของ cluster ที่เป็นแม่ และการคลิกชื่อจะกระโดดไปหน้าแก้ไข user
- [rbac](/th/platform/rbac) — โมเดล permission เบื้องหลังทุก gate ใน §4: catalog, role, scoped assignment, bypass ของ super-admin และ (§5 ของหน้านั้น) โมเดล role-enum รุ่นเก่าที่เคย gate โมดูลนี้จนถึง 2026-06
- [report-templates](/th/platform/report-templates) — chip input `allow_business_unit` / `deny_business_unit` ที่นั่นกำหนดขอบเขตเทมเพลตรายงานด้วยค่า `code` ของ BU ที่นิยามไว้ที่นี่
- **licenses** (ยังไม่มีหน้า wiki เอกสารเต็ม) — License Center เต็มหน้า (`/licenses/:clusterId`) ที่ปุ่ม Manage/New subscription ของแท็บ Licenses ลิงก์ออกไป แถวการซื้อที่นั่งและโควตา BU ถูกสร้าง/แก้ไขจริงที่นั่น ไม่ใช่บนหน้านี้

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — route ทั้งสามของ BU พร้อม prop `requiredPermission="cluster.*"` และ `feature="business_units"`
- `../carmen-platform/src/components/nav/platformNav.ts` — รายการ "Business Units" ใน sidebar (`permission: 'cluster.read'`, `feature: 'business_units'`); นิยาม nav item อยู่ที่นี่ ไม่ใช่ `Layout.tsx`
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx` และ `businessUnitManagement/BuSummary.tsx` — หน้ารายการ: endpoint สรุปเฉพาะ, filter, ส่งออก CSV, Add/Edit/View History/Delete ที่ gate ด้วย `<Can>` (ไม่มี client-side deletion guard)
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` และ `businessUnitEdit/{BusinessUnitDocument,BusinessUnitTabs,HeroName,BusinessUnitBrandingCard,BusinessUnitUsersCard,BusinessUnitLicensesCard,useBusinessUnitUsers,types,shared}.ts(x)`, `sections/{CalculationSettingsSection,NumberFormatsSection,ConfigurationSection,DatabaseConnectionSection}.tsx` — หน้าแก้ไขหกแท็บ ตรรกะ tab และเนื้อหาทุกแท็บ
- `../carmen-platform/src/utils/{databasePool,buLicense}.ts` — ตัวสุ่มชื่อ schema และการคำนวณ ledger ที่นั่ง (`sumActiveLicenses`, `licenseStatus`)
- `../carmen-platform/src/pages/licenses/useLicenseLedger.ts`, `src/services/businessUnitLicenseService.ts` — read model และ REST client ของแท็บ Licenses
- `../carmen-platform/src/components/{TenantMigrationCard,TenantSeedCard,InterfaceEntitlementCard}.tsx` — การ์ด advanced สามใบ (action ที่เปลี่ยนแปลงข้อมูล ไม่ใช่การมองเห็น ถูก gate ด้วย super-admin); `../carmen-platform/src/services/{tenantMigrationService,tenantSeedService,interfaceEntitlementService,currencyService,databasePoolService}.ts` — REST client ของแต่ละอัน
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — control อัปโหลด logo/avatar ที่ใช้ร่วมกันบน Branding section
- `../carmen-platform/src/services/businessUnitService.ts` — REST client (`/api-system/business-units`, `/summary`, endpoint อัปโหลด `/logo`/`/avatar`, และ endpoint join `/api-system/user/business-units`)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/business-unit/{business-unit.service,business-unit-code.helper}.ts` — การสร้าง `code` ฝั่ง server และ gate โควตา BU/ชื่อซ้ำตอนสร้าง

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/business-units/data-model) — เอกสารอ้างอิงเอนทิตี BU: ฟิลด์ระบุตัวตน บล็อกที่อยู่ hotel/company แบบมีโครงสร้าง ฟิลด์รูปแบบวันที่/เวลา/ตัวเลข การตั้งค่าการคำนวณ array `config[]` แบบ key/value ตัวชี้ `database_pool_id`/`db_schema` ที่แทนที่ `db_connection` branding file token `doc_version` ledger ที่นั่งใหม่ `tb_business_unit_license` และ schema ของตาราง join BU-user
- [UI Screens](/th/platform/business-units/ui-screens) — ทัวร์ของหน้ารายการ (`BusinessUnitManagement`) และหน้าแก้ไขหกแท็บ (`BusinessUnitEdit`): การสร้าง code อัตโนมัติ, ตัวเลือก database pool กับปุ่มสุ่มชื่อ schema, แท็บ Licenses กับปุ่ม New Subscription และตัวบ่งชี้ cluster-seat/Shared badge บนแท็บ Users
- [Tenant Migrations](/th/platform/business-units/tenant-migrations) — หน้าจอ `/tenant-migrations` แบบ standalone ระดับ fleet: สถานะ migration และ console batch-deploy ของทุก BU ในตารางเดียว แยกจาก (แต่ใช้ service ร่วมกับ) การ์ดต่อ BU ในแท็บ Technical ของหน้าแก้ไข
