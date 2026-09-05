---
title: กลุ่มฟอร์มรายงาน (Report Form Groups)
description: The planned top-level home for ReportFormGroupManagement — a grouped-card list of default form templates per report_group — currently documented in full at the report-templates/form-groups sub-page pending relocation.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, report-form-groups
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# กลุ่มฟอร์มรายงาน (Report Form Groups)

## 1. At a Glance

- ReportFormGroupManagement — one card per report_group, "set as default" action on tb_report_template.is_default
- Reuses report_template.read; carries its own report_form_groups feature key
- Content currently lives at report-templates/form-groups.md — see cross-module note

## 2. References

- ../carmen-platform/src/pages/ReportFormGroupManagement.tsx
- ../carmen-platform/src/pages/reportFormGroups/GroupCard.tsx
- ../carmen-platform/src/components/nav/platformNav.ts
- en/platform/report-templates/form-groups.md (existing content pending relocation decision)

## 3. TODO

- [ ] Decide whether to relocate content from report-templates/form-groups.md or keep both — see cross-module note in .specs/resync-platform-2026-09-05-progress.md
- [ ] Fill from source in Task 28
