# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Nature

**carmen-wiki** is a **documentation-only repository** — Markdown knowledge-base content rendered by [Wiki.js](https://js.wiki/). There is no application code, no package manager, no build pipeline, and no test suite in this repo. Do not look for `package.json`, run linters, or attempt builds; tasks here are always content edits.

Work is organized into top-level topic directories (e.g. `inventory/`). Each `.md` file is a standalone wiki page.

## Wiki.js Page Format

Every page must begin with Wiki.js YAML frontmatter. Match the existing pattern in `inventory/calculation-methods.md`:

```yaml
---
title: <Human-readable page title>
description: <One-line summary used by Wiki.js search and previews>
published: true
date: <ISO 8601 timestamp of last edit>
tags: <comma-separated tags>
editor: markdown
dateCreated: <ISO 8601 timestamp of original creation — never change after creation>
---
```

When editing an existing page, update `date` to the current timestamp but leave `dateCreated` untouched. When creating a new page, set both to the same value.

## Documentation Conventions

Conventions established by the existing wiki content — match them when adding or editing pages:

- **Numbered section hierarchy**: top-level sections use `## 1. Title`, `## 2. Title`, with `### 2.1`, `### 2.2` subsections. Keeps cross-references stable.
- **Comparison tables** for design trade-offs (advantages/disadvantages, FIFO vs. Weighted Average, etc.) — prefer tables over prose bullet lists when comparing options.
- **Pseudo-code blocks** (language-agnostic, fenced as ``` with no language tag) for algorithms and data models, rather than real TypeScript/SQL. The wiki documents *platform design*, not implementation in any single repo's stack.
- **Currency in examples**: Thai Baht (`฿`) — Carmen is a Thailand-based hospitality platform.
- **Edge-case sections**: design docs typically end with an "Edge Cases" table and a "Recommendations" section. Preserve this structure.

## Project Context

**carmen-wiki** is the documentation/knowledge-base repository within the Carmen Software organization. The organization builds a hospitality supply chain management platform spanning multiple repositories. This wiki documents *platform design and domain concepts* — it is not tied to one codebase's implementation.

### Related Repositories (subjects of this documentation)

- **carmen-turborepo-frontend** — Main frontend (Turborepo, Bun, Next.js 15, React 19, Tailwind 4, Shadcn/ui)
- **carmen-turborepo-backend-v2** — Main backend (Turborepo)
- **cmobile** — Mobile PWA (Next.js 15, React 19)
- **carmen-platform** — Admin dashboard (React 18, CRA)
- **mock-backend-mobile** — Mock API (Bun/Elysia)
- **carmen-inventory-wiki** — Separate inventory system documentation

### Organization Tech Stack (referenced in design docs)

- **Frontend:** React 18/19, TypeScript (strict), Next.js 14/15 App Router, Tailwind CSS, Shadcn/ui + Radix UI, Zustand, React Query, Zod
- **Backend:** NestJS, Elysia/Bun, PostgreSQL
- **Build tooling:** Turborepo, Bun (preferred package manager), ESLint, Vitest
- **Auth:** JWT with refresh tokens, RBAC, x-app-id header validation

### Domain

Hospitality supply chain management — modules include Dashboard, Receiving (GRN), PR Approval, Store Requisition, Stock Take, Spot Check, vendor/product catalogs, and business unit/cluster management.
