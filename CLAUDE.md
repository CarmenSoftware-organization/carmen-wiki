# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**carmen-wiki** is a documentation/knowledge-base repository within the Carmen Software organization. The organization builds a hospitality supply chain management platform spanning multiple repositories.

### Related Repositories

- **carmen-turborepo-frontend** — Main frontend (Turborepo monorepo, Bun, Next.js 15, React 19, Tailwind 4, Shadcn/ui)
- **carmen-turborepo-backend-v2** — Main backend (Turborepo monorepo)
- **cmobile** — Mobile PWA (Next.js 15, React 19)
- **carmen-platform** — Admin dashboard (React 18, CRA)
- **mock-backend-mobile** — Mock API (Bun/Elysia)
- **carmen-inventory-wiki** — Inventory system documentation

### Organization Tech Stack

- **Frontend:** React 18/19, TypeScript (strict), Next.js 14/15 App Router, Tailwind CSS, Shadcn/ui + Radix UI, Zustand, React Query, Zod
- **Backend:** NestJS, Elysia/Bun, PostgreSQL
- **Build tooling:** Turborepo, Bun (preferred package manager), ESLint, Vitest
- **Auth:** JWT with refresh tokens, RBAC, x-app-id header validation

### Domain

Hospitality supply chain management — modules include Dashboard, Receiving (GRN), PR Approval, Store Requisition, Stock Take, Spot Check, vendor/product catalogs, and business unit/cluster management.
