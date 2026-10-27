---
title: Report Template — XML Spec
description: โครงสร้าง XML ของ Dialog, Content และ Export (การ map เป็น CSV); element Label/Date/Lookup/Group, Cols/ColSpan และการจับคู่ช่วง From/To
published: true
date: '2026-10-27T15:00:00.000Z'
tags: book/platform, report-templates, xml
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Report Template — XML Spec

## 1. At a Glance

- Dialog root element (`Cols` 1–4) and child structure (`Label`, `Date`, `Lookup`, `Group`, `ColSpan`)
- Content root element and child structure
- Export XML (optional `export_xml`): `<Export>` root, `<Column>` (`Header` + one of `Field` / `Value` / `Expression`), `<Sort>` — the CSV column mapping (§4)
- <Label> + <Date> / <Lookup> pairing and From/To range pairing; a control's own `Label` attribute

## 2. References

- ../carmen-backstage/src/pages/ReportTemplateEdit.tsx

## 3. TODO

- [ ] Add a fully-valid example template
- [ ] List validation error categories
