---
title: บันทึกการเปลี่ยนแปลง (Changelog)
description: บันทึกการเปลี่ยนแปลงของแพลตฟอร์มแบบมีเวอร์ชัน — ดึงข้อมูลจาก JSON, เปิดเป็นหน้า public /changelog (ตอนนี้ค้นหาได้แล้ว) เข้าถึงผ่าน version badge ในแถบด้านข้างและหน้า landing page
published: true
date: 2026-09-06T00:00:00.000Z
tags: platform, changelog, versioning, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# บันทึกการเปลี่ยนแปลง (Changelog)

> **สรุปภาพรวม**
> **แหล่งข้อมูลหลัก:** `src/data/changelog.json` &nbsp;·&nbsp; **หน้าสาธารณะ:** `/changelog` (ไม่ต้องยืนยันตัวตน) ตอนนี้มีช่องค้นหาผ่านเวอร์ชัน/หมวดหมู่/รายการ &nbsp;·&nbsp; **จุดเข้าถึง:** `VersionBadge` ในส่วนท้ายของแถบด้านข้าง + landing page &nbsp;·&nbsp; **ไฟล์ที่สร้างอัตโนมัติ:** `CHANGELOG.md` (รูปแบบ Keep a Changelog) &nbsp;·&nbsp; **การปล่อยเวอร์ชัน:** `bun run build:bump [patch|minor|major]` — ตอนนี้เป็นสคริปต์ release เต็มรูปแบบ (`scripts/release.mjs`, 2026-08-05) มี guard ของ branch/working-tree/upstream/tag ประตู typecheck+lint+test และการ commit + tag แบบ annotated ใน git ไม่ใช่แค่ bump แล้ว build เฉย ๆ อีกต่อไป (§5)

## 1. คืออะไร และใครใช้

Changelog คือบันทึกที่มีเวอร์ชันและเปิดเป็น **public** สำหรับสิ่งที่เผยแพร่ในผลิตภัณฑ์ Carmen Platform admin ไฟล์ JSON เดียวคือ (`src/data/changelog.json`) คือแหล่งข้อมูลหลัก โดย React app นำเข้าแบบ static (ไม่มีการดึงข้อมูลขณะ runtime) เพื่อแสดงหน้า `/changelog` และสคริปต์ Node จะสร้าง `CHANGELOG.md` ที่อ่านได้ (รูปแบบ Keep a Changelog) ไว้ที่รูทของ repo ใหม่ทุกครั้ง `CHANGELOG.md` **ห้ามแก้ไขด้วยมือ** — ให้แก้ไขที่ JSON เท่านั้น

**ผู้เขียน:** นักพัฒนา (เพิ่มรายการใต้บัฟเฟอร์ `unreleased` ระหว่างการทำงาน) **ผู้อ่าน:** ทุกคน — หน้านี้เปิดสาธารณะ

## 2. วิธีเก็บข้อมูล

JSON มีบัฟเฟอร์ `unreleased` พร้อมกับ `versions` ที่ออกแล้ว (เรียงล่าสุดก่อน) หมวดหมู่ที่ว่างเปล่าจะถูกละไว้เพื่อให้เขียนง่ายขึ้น:

```
{
  "unreleased": { "Added": ["A feature not yet released"] },
  "versions": [
    {
      "version": "0.1.0",
      "date": "2026-06-01",
      "changes": {
        "Added": ["Public changelog page with version badge"],
        "Fixed": ["Audit dates read from the nested audit object in lists"]
      }
    }
  ]
}
```

หมวดหมู่ใช้ชุด Keep a Changelog แบบเต็ม แสดงตามลำดับนี้: **Added, Changed, Deprecated, Removed, Fixed, Security** รายการการเปลี่ยนแปลงเป็น string ธรรมดา (ไม่มี metadata รายการย่อย) วันที่เขียนในรูปแบบ `YYYY-MM-DD` และแสดง **ตรงตามที่เขียน** — หน้านี้จงใจหลีกเลี่ยง `new Date(value)` เพราะการแปลง string วันที่เป็น UTC midnight จะทำให้วันที่ขยับไปก่อนหน้า 1 วันสำหรับผู้ใช้ที่อยู่ทางตะวันตกของ UTC

## 3. ปรากฏที่ไหนบ้าง

| พื้นที่ | พฤติกรรม |
|---|---|
| หน้า `/changelog` | เส้นทางสาธารณะ; แสดงบล็อก `unreleased` (ถ้ามีข้อมูล) ตามด้วยแต่ละเวอร์ชันที่ออกแล้วโดยเรียงล่าสุดก่อน และถูก filter ด้วยช่องค้นหา (§4) เมื่อมีคำค้นหา active |
| ส่วนท้ายของแถบด้านข้าง | `VersionBadge` แสดง `v{latest}` ลิงก์ไปที่ `/changelog` |
| Landing page | `VersionBadge` อยู่ถัดจากวันที่ build |

เวอร์ชันปัจจุบันสำหรับ badge ดึงมาจาก `versions[0].version` (ค่าสำรอง `0.0.0`) `/changelog` ถูกลงทะเบียนเป็น **public path ใน auth guard** ดังนั้นจึงแสดงผลได้สำหรับผู้เยี่ยมชมที่ยังไม่ได้ลงชื่อเข้าใช้

## 4. การค้นหา

ช่องค้นหา (render เฉพาะเมื่อ changelog มีรายการอยู่บ้าง) filter ทั้งบล็อก `unreleased` และเวอร์ชันที่ออกแล้วขณะพิมพ์ — ไม่มี debounce เพราะทุกอย่างเป็นฝั่ง client เหนือ JSON ที่โหลดไว้แล้ว คำค้นหาจะ match การ์ดของเวอร์ชันหนึ่งหากปรากฏใน **หมายเลขเวอร์ชัน** (เช่น `0.1.1`), **label ของหมวดหมู่** (`Added`, `Fixed`, …) หรือข้อความของ**รายการการเปลี่ยนแปลงใด ๆ** ภายใต้เวอร์ชันนั้น — การ match แม้เพียงหนึ่งในนั้นจะทำให้การ์ดเวอร์ชันทั้งใบยังคงแสดงอยู่ ไม่ใช่แค่บรรทัดที่ match มี empty state สองแบบครอบคลุมกรณีไม่มีเนื้อหา: "No changelog entries yet" (changelog ว่างเปล่าจริง ๆ — ไม่มีเนื้อหาใน `unreleased` และไม่มีเวอร์ชันที่ออกแล้ว) เทียบกับ "No matching entries" (มีรายการอยู่ แต่ไม่มีตัวไหน match กับคำค้นหาปัจจุบัน)

## 5. สำหรับนักพัฒนา

- **เพิ่มการเปลี่ยนแปลง:** แก้ไข `src/data/changelog.json` โดยเพิ่ม string ในหมวดหมู่ที่เหมาะสมภายใน `unreleased` ห้ามแตะ `CHANGELOG.md`
- **ปล่อยเวอร์ชัน:** `bun run build:bump [patch|minor|major]` รันสคริปต์ `scripts/release.mjs` — สคริปต์ที่หนักกว่าชื่อบอกไว้มาก หลัง rewrite เมื่อ 2026-08-05 ตามลำดับมันจะ: (1) อ่านเวอร์ชันปัจจุบันจาก `changelog.json` (แหล่งข้อมูลหลัก — `VersionBadge` อ่านจากตรงนี้ `package.json` แค่สะท้อนตาม) แล้ว fail ทันทีถ้าสองไฟล์นี้ไม่ตรงกัน; (2) ตรวจว่า branch เป็น `main` หรือ `chore/release-*` และ working tree สะอาด; (3) ตรวจว่า branch ไม่ตามหลัง upstream ของมัน (หรือ `origin/main` เป็นค่าสำรองเมื่อไม่มี upstream) โดยใช้ ref ที่ fetch มาแล้วเท่านั้น — ไม่เรียก `git fetch` เลย; (4) fail ถ้า `unreleased` ว่างเปล่า — ไม่มีอะไรให้เลื่อนขึ้น; (5) รับ level จาก CLI argument หรือถ้าไม่ระบุจะถามแบบ interactive โดยไม่มีค่าเริ่มต้น ยกเลิกได้ด้วย Enter หรือ `q` (ไม่มี "patch" โดยปริยายอีกต่อไป); (6) fail ถ้า git tag ของเวอร์ชันเป้าหมายมีอยู่แล้ว; (7) รัน `typecheck`, `lint`, และ `test` เป็นประตูก่อนเริ่ม ถ้าอันไหนไม่ผ่านจะยกเลิกการปล่อยทั้งหมดก่อนแตะไฟล์ใด ๆ; (8) คำนวณและ validate `changelog.json` ที่เลื่อนแล้ว, `package.json` ที่ bump แล้ว, และ `CHANGELOG.md` ที่สร้างใหม่ ก่อนจะเขียนไฟล์ไหนเลย; (9) commit ไฟล์ทั้งสามนั้นด้วย `git commit --only -- <ไฟล์ทั้งสาม>` (`chore(release): vX.Y.Z`) และสร้าง tag แบบ annotated `vX.Y.Z` — โดยไม่แตะสิ่งที่ stage ไว้อื่น; (10) แสดงขั้นตอนถัดไปที่ต้องทำเอง ซึ่งต่างกันตาม branch: บน `main` ให้ push commit และ tag ตรง ๆ; บน branch `chore/release-*` ให้ push branch, เปิด PR, merge ด้วย **merge commit** (ห้าม squash เด็ดขาด — squash จะเขียน commit release ใหม่และทำให้ tag ที่สร้างไว้แล้วลอยค้างอยู่บน commit ที่ไม่มีวันเข้าถึง `main`) แล้วค่อย push tag สคริปต์เองไม่ push อะไรเลย
- **หมายเหตุ public-path:** หากการ refactor ของ route-guard เปลี่ยนวิธีลงรายการ public paths, `/changelog` ต้องยังคงอยู่ใน allowlist มิฉะนั้นหน้าจะ redirect ไปที่หน้าลงชื่อเข้าใช้
- **การค้นหา match เฉพาะข้อความของหมวดหมู่/รายการเท่านั้น** — ไม่ match วันที่ ดังนั้นการค้นหา string วันที่ (เช่น `2026-06-01`) จะไม่แสดงเวอร์ชันนั้นขึ้นมา
