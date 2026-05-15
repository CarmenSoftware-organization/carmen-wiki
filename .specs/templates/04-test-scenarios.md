---
title: <Module> — Test Scenarios
description: Test cases, edge cases, and Playwright mapping for <module>, organized by persona.
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# <Module> — Test Scenarios

## 1. Overview
<Personas covered + scope of testing.>

## 2. Personas in Scope
- **<Persona>**: <one-line scope of what they do in this module — match index.md Section 4>

## 3. Scenarios by Persona

### 3.1 <Persona A>

#### Happy Path
| # | Scenario | Pre-condition | Steps | Expected |

#### Permission / Authorization
| # | Scenario | Expected behaviour (allow/deny + reason) |

#### Validation / Error
| # | Scenario | Trigger | Expected error |

#### Edge Cases
| # | Scenario | Condition | Expected |

### 3.2 <Persona B>
<Same four sub-sections.>

<Each persona gets the same four sub-sections. Each Section 2/3/4 Business Rule should have at least one corresponding negative test under "Validation / Error" for the persona who would trigger it.>

## 4. Cross-Persona / Handoff Scenarios
<Flows that span multiple personas — Requester submits, Approver reviews, Purchaser converts to PO, etc. One row per handoff scenario.>

## 5. E2E Test Mapping
<Links to specific Playwright specs in `../carmen-inventory-frontend-e2e/tests/`, grouped by persona. Each link includes the test file path + test name + which scenarios from Section 3 it covers.>

## 6. References
- `../carmen-inventory-frontend-e2e/` — Playwright test suite (executable spec).
- `../carmen/docs/<source-folder>/testing.md` if it exists.
