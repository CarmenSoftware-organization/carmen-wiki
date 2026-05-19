---
title: หน่วยธุรกิจ (Business Units)
description: เอนทิตีต่อ property/ต่อโรงแรม พร้อมฟอร์มหลายเซกชันที่ครอบคลุมข้อมูลระบุตัวตน ข้อมูลติดต่อ ภาษี รูปแบบ การคำนวณ การตั้งค่า การเชื่อมต่อฐานข้อมูล และรายชื่อผู้ใช้ที่ผูกกับ BU
published: true
date: 2026-05-19T12:00:00.000Z
tags: platform/business-units, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# หน่วยธุรกิจ (Business Units)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจอ authoring ที่ใช้สร้างและตั้งค่าเอนทิตีปฏิบัติการที่ Carmen เรียกว่า **business unit** (BU) — หนึ่งแถวต่อหนึ่งโรงแรม/property/นิติบุคคล พร้อมฟิลด์ในฟอร์มที่ขับเคลื่อนทั้งบริบทของ tenant ใน inventory app และการมอบหมาย role ของผู้ใช้ในแพลตฟอร์ม &nbsp;·&nbsp; **กลุ่มผู้ใช้:** ผู้ใช้ที่ล็อกอินแล้วทุกคน — ทั้งผู้ดูแลภายในของ Carmen และผู้จัดการฝั่งลูกค้า &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `business_unit` (ฟิลด์ระบุตัวตน `code`, `name`, `alias_name`, `is_hq`, `is_active`, `max_license_users`; บล็อกข้อมูลติดต่อสำหรับ hotel/company; ฟิลด์ภาษี; ฟิลด์รูปแบบวันที่/เวลา/ตัวเลข; `calculation_method`, `default_currency_id`; `db_connection`; `config[]` แถว key/value) บวกกับตาราง join BU-to-user ที่ถือ `role` ระดับ BU เป็น `admin` หรือ `user` &nbsp;·&nbsp; **หน้าย่อย:** 2

## 1. ภาพรวม

Business unit คือ tenant ปฏิบัติการของ Carmen platform: หนึ่ง BU คือหนึ่งโรงแรม หนึ่ง property หรือหนึ่งนิติบุคคลที่ซื้อ รับ นับ และเบิกใช้ inventory หน้ารายการที่ `/business-units` (`BusinessUnitManagement.tsx`) เป็นแคตตาล็อกแบบ server-paginated ค้นหาได้ มี facet สำหรับ Active/Inactive และรายการที่ถูก soft-delete พร้อมส่งออก CSV ได้ หน้าแก้ไขที่ `/business-units/:id/edit` และ `/business-units/new` (`BusinessUnitEdit.tsx`) แสดงฟอร์ม 9 ส่วนเป็นการ์ดในกริดสองคอลัมน์ — Basic Information, Hotel Information, Company Information, Tax Information, Date/Time Formats, Number Formats, Calculation Settings, Configuration และ Database Connection — ตามด้วย card Users ที่แยกออกมาเพื่อแสดงรายชื่อผู้ที่ถูก assign เข้า BU card Users จะปรากฏหลังจาก BU ถูกสร้างแล้วเท่านั้น การสร้าง BU เป็น flow แบบ "บันทึกก่อนแล้วค่อย assign"

แต่ละ BU เป็นของ **cluster** หนึ่ง cluster เท่านั้น (foreign key `cluster_id` เลือกจาก dropdown) flow "สร้าง BU" เริ่มได้จากหน้ารายการ BU หรือจากหน้าแก้ไข cluster ซึ่ง navigate ไปที่ `/business-units/new?cluster_id=<id>` เพื่อ preselect parent ให้ นอกจากฟิลด์ระบุตัวตนและข้อมูลติดต่อ BU ยังเก็บค่า locale ที่ inventory runtime อ่านจะใช้ — `date_format`, `time_format`, `timezone`, ตัว format แบบ JSON `amount_format`/`quantity_format`/`recipe_format` ที่ default เป็น `th-TH`, `calculation_method` และ `default_currency_id` — บวกกับ array `config[]` ที่เป็นแถว key/value แบบ free-form และบล็อก JSON `db_connection` ที่ชี้ BU ไปยัง schema ของ tenant ของตน รายละเอียดต่อฟิลด์และพฤติกรรมของหน้าจออยู่ในหน้าย่อย — หน้า landing นี้เพียงปูทาง

## 2. บริบททางธุรกิจ

ในธุรกิจโรงแรม หน่วยที่เล็กที่สุดที่มีบัญชีของตัวเอง มีสกุลเงินของตัวเอง และมี supply chain ระดับท้องถิ่นของตัวเอง คือ property — โรงแรมเดี่ยวภายในกลุ่มแบรนด์ Carmen จึงโมเดลสิ่งนี้เป็น business unit ทุก inventory transaction (GRN, store requisition, physical count, spot check) อยู่ในขอบเขตของ BU เดียว ทุกรายงานรันกับ schema ของ BU เดียว และผู้ใช้ทุกคนได้รับสิทธิ์เข้าถึง BU หนึ่งหรือมากกว่าหนึ่ง พร้อม role ที่ใช้ภายในแต่ละ BU แถว `business_unit` จึงถือมากกว่าข้อมูลระบุตัวตน มันถือค่า locale ที่ inventory UI แสดง (รูปแบบวันที่และตัวเลข, timezone, default currency) ถือ knob ของการคำนวณต้นทุน (`calculation_method`) ที่ valuation engine ใช้อ้างอิง ถือการเชื่อมต่อฐานข้อมูลของ tenant ที่แพลตฟอร์มใช้ route query ไปยัง schema ของ property นั้น และถือเพดานสิทธิ์การใช้งาน (`max_license_users`) ที่จำกัดว่าผู้ใช้กี่คนจะล็อกอินได้

เนื่องจาก BU ยังเป็นจุดที่ผู้ใช้กลายเป็นมีความหมายในเชิงปฏิบัติการ หน้าแก้ไขจึงทำหน้าที่เป็น workbench สำหรับ assign ผู้ใช้ด้วย card Users แสดงทุกคนที่มีสิทธิ์เข้าถึง BU นี้ พร้อม **BU role** (`admin` หรือ `user`) ที่ orthogonal กับ role ระดับแพลตฟอร์มบนบัญชีผู้ใช้เอง สมาชิก BU ใหม่ถูกเลือกจาก cluster ที่เป็นแม่ของ BU นั้น — ผู้ใช้ต้องอยู่ใน cluster ก่อนถึงจะถูกเพิ่มเข้า BU ภายใน cluster ได้ ซึ่งช่วยรักษาขอบเขตของ tenant ให้สะอาด ผู้ที่มี login ของแพลตฟอร์มเข้า route เหล่านี้ได้ทั้งหมดในวันนี้ role ระดับแพลตฟอร์มเป็นตัวแยกแยะว่าเขาทำอะไรได้ในโมดูลอื่น (clusters, report templates ฯลฯ) ไม่ใช่ว่าเขาเปิดหน้าแก้ไข BU ได้หรือไม่

## 3. แนวคิดสำคัญ

- **Business unit (BU)**: หนึ่งแถวใน `business_unit` ที่แทนหนึ่งโรงแรม/property/นิติบุคคล ทุก inventory transaction เป็นของ BU เดียว ทุกรายงานรันกับ BU เดียว
- **Cluster membership**: ทุก BU มี `cluster_id` ที่ไม่ nullable เลือกจาก dropdown ของ cluster หน้าแก้ไข cluster สามารถเปิด flow สร้าง BU โดย preselect `cluster_id` ผ่าน query parameter `/business-units/new?cluster_id=<id>`
- **HQ flag (`is_hq`)**: ระบุว่า BU นี้เป็นสำนักงานใหญ่ภายใน cluster ของตน — Boolean ค่าเดียวที่แสดงคู่กับ flag Active ใน Basic Information ความหมายขึ้นอยู่กับโมดูลที่ใช้ค่านี้
- **Active flag (`is_active`)**: สลับว่า BU เปิดใช้งานเชิงปฏิบัติการหรือไม่ BU ที่ inactive ยังแก้ไขได้ในหน้า admin แต่จะถูกกรองออกจากการเลือกตอน runtime ปกติ หน้ารายการแสดง Active/Inactive เป็น chip กรอง
- **Max licensed users (`max_license_users`)**: integer ที่ใส่หรือไม่ใส่ก็ได้ เพื่อจำกัดจำนวนผู้ใช้ที่ assign เข้า BU ได้ ว่าง = ไม่จำกัด
- **Hotel vs. Company information**: บล็อกข้อมูลติดต่อสองบล็อกคู่ขนาน (`hotel_*` และ `company_*` — name, telephone, email, address, ZIP) เพราะตัวตนเชิงปฏิบัติการของ property (hotel) มักต่างจากนิติบุคคลที่ออกใบแจ้งหนี้ (company)
- **Tax information**: `tax_no` และ `branch_no` เก็บเลขประจำตัวผู้เสียภาษีของไทยและรหัสสาขาที่ใช้บนเอกสารพิมพ์
- **Date/Time formats**: `date_format`, `date_time_format`, `time_format`, `long_time_format`, `short_time_format` และ `timezone` ตั้งค่าว่า inventory UI จะ render timestamp ของ BU นี้อย่างไร
- **Number formats**: ตัว format แบบ JSON สามชุด — `amount_format`, `quantity_format`, `recipe_format` — บวกกับ `perpage_format` JSON ที่ขับเคลื่อนค่า default ของ pagination แต่ละ formatter default เป็น `{"locales":"th-TH","minimumIntegerDigits":2}`
- **Calculation settings**: `calculation_method` (วิธีคำนวณต้นทุนของ BU เช่น FIFO/Weighted Average — ใช้โดย inventory valuation engine) และ `default_currency_id` (foreign key ไปยังตารางสกุลเงิน โดย code/name/symbol/decimals ที่ resolve แล้วจะแสดงข้าง ๆ ในโหมดอ่าน)
- **Configuration array (`config[]`)**: รายการแบบมีลำดับของแถว `{ key, value }` แบบ free-form ที่เก็บเป็น JSON array บน BU ใช้โดย inventory app สำหรับ feature toggle ระดับ BU และการตั้งค่า integration หน้า admin ไม่บังคับ schema
- **Database connection (`db_connection`)**: บล็อก JSON ที่เก็บบน BU ที่บอกแพลตฟอร์มว่า transaction ของ BU นี้อยู่ที่ database/schema ใด render เป็นบล็อก `<pre>` แบบ pretty-printed หน้า admin validate แค่ในระดับ JSON เท่านั้น
- **BU role (`admin` vs. `user`)**: role ที่ผูกกับการ assign user-BU แต่ละครั้ง เก็บบนแถว join ของ BU-user คู่กับ `is_active` และ `is_default` ค่าคงที่ `BU_ROLES` ใน `BusinessUnitEdit.tsx` กำหนดสองค่าพอดี role นี้ **orthogonal** กับ role ระดับแพลตฟอร์มบนบัญชีผู้ใช้ BU role ควบคุมพฤติกรรมของผู้ใช้ใน inventory app สำหรับ BU นั้น ไม่ใช่การเข้าถึง route ของ admin
- **Pattern เพิ่ม user จาก cluster**: สมาชิก BU ใหม่ถูกเลือกจากรายชื่อผู้ใช้ของ cluster ที่เป็นแม่ (`clusterUsers`) — ผู้ใช้ต้องเป็นสมาชิก cluster ก่อนถึงจะถูกเพิ่มเข้า BU ภายใน cluster ได้
- **Soft delete**: BU ถูก soft-delete ผ่าน `deleted_at` / `deleted_by_name` หน้ารายการมี toggle filter "Show soft-deleted business units" ที่ทาบ badge แดง `Deleted` และคอลัมน์ "Deleted By" เพิ่มเพื่อ audit

## 4. บทบาทและ Persona

Route `/business-units`, `/business-units/new`, และ `/business-units/:id/edit` ใช้ `PrivateRoute` **โดยไม่มี prop `allowedRoles`** — ยืนยันจากการอ่าน `../carmen-platform/src/App.tsx` และ `../carmen-platform/SITEMAP.md` ผู้ใช้ใด ๆ ที่ถือ session ที่ valid อยู่จะเข้า route เหล่านี้ได้ ไม่มี gate ระดับ role ของแพลตฟอร์มที่ระดับ route และ `BusinessUnitEdit.tsx` ก็ไม่ได้ gate ปุ่มแต่ละปุ่ม (Edit, Delete, Add User, การเปลี่ยน role, การ soft-delete) ตาม role ของแพลตฟอร์มด้วย แนวคิด role เดียวที่หน้านี้ใช้คือค่า `admin`/`user` ระดับ BU ที่ผูกกับการ assign user-BU ภายใน card Users ซึ่งเป็นข้อมูลที่หน้านี้แก้ไข — ไม่ใช่ guard ของมัน

| Persona | สิทธิ์เข้าถึง route | สิ่งที่มักทำที่นี่ |
|---|---|---|
| ผู้ใช้ที่ล็อกอินแล้วทุกคน | เข้าถึงเต็มสำหรับ list, สร้าง, แก้ไข, soft-delete BU และจัดการรายชื่อผู้ใช้ของ BU | ตามบริบทการปฏิบัติการ — วิศวกร support ของ Carmen ตั้งค่า property ใหม่ end-to-end ผู้จัดการฝั่งลูกค้าอัปเดตข้อมูลติดต่อ รูปแบบ และรายชื่อผู้ใช้ใน BU ของตน |

เนื่องจากไม่มี array `allowedRoles` ความรับผิดชอบในการจำกัดว่าใครจะ mutate state ของ BU ปัจจุบันอยู่นอกผลิตภัณฑ์ admin (โดยทั่วไปอยู่ที่ backend API และเวลา provision) หน้าที่อ้างถึงในเซกชัน 5 อธิบายว่าหน้าจอ admin อื่น ๆ ของแพลตฟอร์มถูก gate เข้มงวดกว่าอย่างไร

## 5. โมดูลที่เกี่ยวข้อง

- [[clusters]] — ทุก BU เป็นของ cluster หนึ่ง cluster ผ่าน `cluster_id` หน้าแก้ไข cluster เปิด flow สร้าง BU โดย preselect parent ผ่าน query parameter `/business-units/new?cluster_id=<id>`
- [[users]] — เป็นแหล่งของบัญชีผู้ใช้ที่ถูก assign เข้า BU ผ่าน card Users สมาชิก BU ใหม่ถูกดึงจากรายชื่อผู้ใช้ของ cluster ที่เป็นแม่ และการคลิกชื่อใน card Users จะกระโดดไปหน้าแก้ไข user
- [[auth-roles]] — อธิบายกลไก `PrivateRoute` ที่ gate ทุก route ของแพลตฟอร์ม และเหตุผลที่ route ของ BU เข้าได้โดยผู้ใช้ที่ล็อกอินแล้วทุกคนเนื่องจากไม่มี array `allowedRoles`
- [[report-templates]] — chip input `allow_business_unit` / `deny_business_unit` ที่นั่นกำหนดขอบเขตเทมเพลตรายงานด้วยค่า `code` ของ BU ที่นิยามไว้ที่นี่

## 6. แหล่งข้อมูลอ้างอิง

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/BusinessUnitManagement.tsx`, `../carmen-platform/src/pages/BusinessUnitEdit.tsx`, `../carmen-platform/src/App.tsx`

## 7. หน้าในโมดูลนี้

- [Data Model](./data-model.md) — เอกสารอ้างอิงเอนทิตี BU (stub — ยังไม่สมบูรณ์): ฟิลด์ระบุตัวตน บล็อกข้อมูลติดต่อของ hotel/company ฟิลด์รูปแบบวันที่/เวลา/ตัวเลข การตั้งค่าการคำนวณ array `config[]` แบบ key/value บล็อก JSON `db_connection` และ schema ของตาราง join BU-user
- [UI Screens](./ui-screens.md) — ทัวร์ของหน้ารายการ (`BusinessUnitManagement`) และหน้าแก้ไข (`BusinessUnitEdit`) ทุกเซกชันฟอร์ม (stub — ยังไม่สมบูรณ์) บวกกับ card Users พร้อม select สำหรับ BU role และ dialog เพิ่ม user จาก cluster
