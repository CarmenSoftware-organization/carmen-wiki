# Nav Groups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render each Wiki.js book's sidebar as named groups of modules (Inventory: 6 groups / 19 modules; Platform: 3 groups / 6 modules) instead of one flat list per book.

**Architecture:** Extend `nav-overrides.yaml` with a `groups:` block per book that replaces the legacy flat `modules:` key. `sync_nav.py:build_tree_from_config()` walks groups → modules and emits a Wiki.js `header` item between module link runs to render the visual grouping. Both books' `home.md` TOCs are rewritten to mirror the group structure.

**Tech Stack:** Python 3, PyYAML, pytest, Wiki.js (GraphQL), Markdown with Wiki.js YAML frontmatter.

**Reference:** See spec at `docs/superpowers/specs/2026-05-19-nav-groups-design.md` for design rationale, decision log, and full group/module assignments.

---

## File map

| File | Action |
|---|---|
| `scripts/test_sync_nav.py` | Modify: migrate 4 existing `build_tree_*` tests to `groups:` schema and add 3 new tests for group behavior |
| `scripts/sync_nav.py` | Modify: rewrite `build_tree_from_config()` (~lines 645–677) to iterate `groups:` instead of `modules:` |
| `scripts/nav-overrides.yaml` | Modify: replace flat `modules:` under both books with `groups:` block |
| `en/inventory/home.md` | Modify: rewrite `## 1. Modules` into 6 group sections, keep `## 7. How to use this book` |
| `th/inventory/home.md` | Modify: same as EN, Thai labels |
| `en/platform/home.md` | Modify: replace skeleton TOC with 3 group sections + How to use |
| `th/platform/home.md` | Modify: same as EN platform (TH copy currently mirrors EN) |

No new files are created.

---

## Task 1: Update tests to drive the new schema (RED)

**Files:**
- Modify: `scripts/test_sync_nav.py:432-521` (existing 4 build_tree tests) and append 3 new tests

This is the only RED phase for the whole plan. Tasks 2 onward verify GREEN.

- [ ] **Step 1.1: Replace the 4 existing `build_tree_*` tests with `groups:` schema versions**

Open `scripts/test_sync_nav.py` and replace the block starting at line 429 (`# ===== Build-mode tree builder tests =====`) through end-of-file with:

```python
# ===== Build-mode tree builder tests =====


def test_build_tree_one_book_one_group_one_module():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "groups": [
                    {
                        "label_en": "Costing & Reporting",
                        "label_th": "Costing & Reporting",
                        "modules": [
                            {"slug": "costing", "label_en": "Costing", "label_th": "Costing"},
                        ],
                    },
                ],
            },
        },
    }
    items_en = build_tree_from_config(config, locale="en")
    # Expected: book-header, home-link, group-header, costing-link
    kinds = [i["kind"] for i in items_en]
    assert kinds == ["header", "link", "header", "link"]
    assert items_en[0]["label"] == "Carmen Inventory"
    assert items_en[1]["target"] == "/en/inventory/home"
    assert items_en[2]["label"] == "Costing & Reporting"
    assert items_en[2]["kind"] == "header"
    assert items_en[3]["target"] == "/en/inventory/costing/home"
    assert items_en[3]["label"] == "Costing"


def test_build_tree_two_books_inserts_divider_between():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "groups": [
                    {
                        "label_en": "Costing & Reporting",
                        "label_th": "Costing & Reporting",
                        "modules": [
                            {"slug": "costing", "label_en": "Costing", "label_th": "Costing"},
                        ],
                    },
                ],
            },
            "platform": {
                "label_en": "Carmen Platform",
                "label_th": "Carmen Platform",
                "home_slug": "home",
                "groups": [
                    {
                        "label_en": "Tenancy",
                        "label_th": "Tenancy",
                        "modules": [
                            {"slug": "clusters", "label_en": "Clusters", "label_th": "Clusters"},
                        ],
                    },
                ],
            },
        },
    }
    items = build_tree_from_config(config, locale="en")
    kinds = [i["kind"] for i in items]
    assert kinds == [
        "header", "link", "header", "link",       # inventory: book hdr, home, group hdr, module
        "divider",                                  # separator
        "header", "link", "header", "link",       # platform: book hdr, home, group hdr, module
    ]


def test_build_tree_th_uses_th_labels_and_paths():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory TH",
                "home_slug": "home",
                "groups": [
                    {
                        "label_en": "Costing & Reporting",
                        "label_th": "ต้นทุนและรายงาน",
                        "modules": [
                            {"slug": "costing", "label_en": "Costing", "label_th": "การคิดต้นทุน"},
                        ],
                    },
                ],
            },
        },
    }
    items_th = build_tree_from_config(config, locale="th")
    assert items_th[0]["label"] == "Carmen Inventory TH"
    assert items_th[1]["target"] == "/th/inventory/home"
    assert items_th[2]["label"] == "ต้นทุนและรายงาน"
    assert items_th[3]["target"] == "/th/inventory/costing/home"
    assert items_th[3]["label"] == "การคิดต้นทุน"


def test_build_tree_link_items_have_uuid_ids():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "groups": [
                    {
                        "label_en": "Costing & Reporting",
                        "label_th": "Costing & Reporting",
                        "modules": [
                            {"slug": "costing", "label_en": "Costing", "label_th": "Costing"},
                        ],
                    },
                ],
            },
        },
    }
    items = build_tree_from_config(config, locale="en")
    ids = [i["id"] for i in items]
    assert all(len(i) == 36 for i in ids)  # UUID4 string length
    assert len(set(ids)) == len(ids)        # all unique


def test_build_tree_multiple_groups_emits_header_per_group():
    """Two groups in one book → group header precedes each module run."""
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "groups": [
                    {
                        "label_en": "Procurement",
                        "label_th": "Procurement",
                        "modules": [
                            {"slug": "purchase-request", "label_en": "PR", "label_th": "PR"},
                            {"slug": "purchase-order", "label_en": "PO", "label_th": "PO"},
                        ],
                    },
                    {
                        "label_en": "Administration",
                        "label_th": "Administration",
                        "modules": [
                            {"slug": "access-control", "label_en": "Access Control", "label_th": "Access Control"},
                        ],
                    },
                ],
            },
        },
    }
    items = build_tree_from_config(config, locale="en")
    # book header, home link, group1 header, 2 module links, group2 header, 1 module link = 7
    assert len(items) == 7
    kinds = [i["kind"] for i in items]
    assert kinds == ["header", "link", "header", "link", "link", "header", "link"]
    labels = [i["label"] for i in items]
    assert labels == [
        "Carmen Inventory",
        "Home",
        "Procurement",
        "PR",
        "PO",
        "Administration",
        "Access Control",
    ]


def test_build_tree_empty_groups_list_emits_book_header_and_home_only():
    """A book with `groups: []` still emits its book header and Home link."""
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "groups": [],
            },
        },
    }
    items = build_tree_from_config(config, locale="en")
    kinds = [i["kind"] for i in items]
    assert kinds == ["header", "link"]
    assert items[0]["label"] == "Carmen Inventory"
    assert items[1]["target"] == "/en/inventory/home"


def test_build_tree_group_with_no_modules_still_emits_header():
    """A group with no `modules:` key (or empty list) still emits its header. Degenerate but valid."""
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "groups": [
                    {"label_en": "Empty Group", "label_th": "Empty Group", "modules": []},
                ],
            },
        },
    }
    items = build_tree_from_config(config, locale="en")
    kinds = [i["kind"] for i in items]
    assert kinds == ["header", "link", "header"]  # book hdr, home, group hdr (no module links)
    assert items[2]["label"] == "Empty Group"
```

- [ ] **Step 1.2: Run the new tests; verify they fail against the un-updated implementation**

Run:
```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
.venv/bin/pytest scripts/test_sync_nav.py -k "build_tree" -v
```

Expected: all 7 `build_tree_*` tests **FAIL**. The 4 tests that previously passed now use `groups:` which the current implementation ignores (it reads `book.get("modules")`), so `build_tree_from_config` returns only `[book-header, home-link]` and the kind/label assertions fail. The 3 new tests fail for the same reason.

If pytest is not installed in the venv, install dev deps first: `.venv/bin/pip install -r scripts/requirements.txt && .venv/bin/pip install pytest`.

- [ ] **Step 1.3: Do NOT commit yet**

Tests are RED — they will go GREEN in Task 2. Commit once after both Task 1 and Task 2 are done.

---

## Task 2: Update `build_tree_from_config` to walk groups (GREEN)

**Files:**
- Modify: `scripts/sync_nav.py:645-677` (function `build_tree_from_config`)

- [ ] **Step 2.1: Replace `build_tree_from_config` body**

In `scripts/sync_nav.py`, replace lines 645–677 (the existing `build_tree_from_config` function body) with:

```python
def build_tree_from_config(
    config: dict[str, Any],
    *,
    locale: str,
) -> list[dict[str, Any]]:
    """Build a Wiki.js nav tree for one locale from the books: config block.

    For each book: emit a book header, a link to /<locale>/<book>/<home_slug>,
    then for each group: emit a group header followed by a link per module
    pointing to /<locale>/<book>/<module>/<home_slug>. A divider separates
    consecutive books.
    """
    label_key = f"label_{locale}"
    items: list[dict[str, Any]] = []
    books = config.get("books") or {}
    for idx, (book_slug, book) in enumerate(books.items()):
        if idx > 0:
            items.append(_new_divider())
        items.append(_new_header(book[label_key]))
        home_slug = book.get("home_slug", "home")
        items.append(
            _new_link(
                "Home",
                f"/{locale}/{book_slug}/{home_slug}",
            )
        )
        for group in book.get("groups") or []:
            items.append(_new_header(group[label_key]))
            for module in group.get("modules") or []:
                items.append(
                    _new_link(
                        module[label_key],
                        f"/{locale}/{book_slug}/{module['slug']}/{home_slug}",
                    )
                )
    return items
```

The only changes from the existing function:
- Outer loop now reads `book.get("groups")` instead of `book.get("modules")`
- A `_new_header(group[label_key])` is emitted before each group's module links
- The inner loop now reads `group.get("modules")` instead of iterating book modules directly
- Docstring updated to describe the new shape

- [ ] **Step 2.2: Run the build_tree tests; verify GREEN**

Run:
```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
.venv/bin/pytest scripts/test_sync_nav.py -k "build_tree" -v
```

Expected: all 7 `build_tree_*` tests **PASS**.

- [ ] **Step 2.3: Run the full test suite to confirm no regressions in mirror-mode tests**

Run:
```bash
.venv/bin/pytest scripts/test_sync_nav.py -v
```

Expected: all tests pass (the mirror-mode tests for `parse_home_headings`, `transform_item`, `resolve_label`, etc., do not depend on the `build_tree_from_config` schema).

- [ ] **Step 2.4: Commit tests + implementation together**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git add scripts/test_sync_nav.py scripts/sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): build_tree_from_config walks groups: instead of flat modules:

Render Wiki.js sidebar with a header item between module link runs to
visually group modules within each book. Update existing build_tree
tests to the groups: schema and add coverage for multi-group books and
degenerate empty-groups / empty-modules cases.
EOF
)"
```

---

## Task 3: Migrate `nav-overrides.yaml` to the `groups:` schema

**Files:**
- Modify: `scripts/nav-overrides.yaml`

- [ ] **Step 3.1: Replace the file contents**

Open `scripts/nav-overrides.yaml` and replace the entire file with:

```yaml
# Configuration for the Wiki.js multi-book navigation tree.
#
# Two sections:
#   - books:    declarative tree used in --mode=build (full rebuild)
#   - headers/links: legacy overrides used in --mode=mirror (legacy default)
#
# Keys must match EXACTLY (case-sensitive).

books:
  inventory:
    label_en: "Carmen Inventory"
    label_th: "Carmen Inventory"
    home_slug: home
    groups:
      - label_en: "Overview"
        label_th: "ภาพรวม"
        modules:
          - slug: dashboard
            label_en: "Dashboard"
            label_th: "Dashboard"
      - label_en: "Procurement"
        label_th: "การจัดซื้อ"
        modules:
          - slug: purchase-request
            label_en: "Purchase Request"
            label_th: "Purchase Request"
          - slug: purchase-order
            label_en: "Purchase Order"
            label_th: "Purchase Order"
          - slug: good-receive-note
            label_en: "Good Receive Note"
            label_th: "Good Receive Note"
          - slug: vendor-pricelist
            label_en: "Vendor Pricelist"
            label_th: "Vendor Pricelist"
      - label_en: "Inventory Operations"
        label_th: "การดำเนินงานคลัง"
        modules:
          - slug: inventory
            label_en: "Inventory"
            label_th: "Inventory"
          - slug: inventory-adjustment
            label_en: "Inventory Adjustment"
            label_th: "Inventory Adjustment"
          - slug: physical-count
            label_en: "Physical Count"
            label_th: "Physical Count"
          - slug: spot-check
            label_en: "Spot Check"
            label_th: "Spot Check"
          - slug: store-requisition
            label_en: "Store Requisition"
            label_th: "Store Requisition"
      - label_en: "Product & Recipe"
        label_th: "สินค้าและสูตร"
        modules:
          - slug: product
            label_en: "Product"
            label_th: "Product"
          - slug: master-data
            label_en: "Master Data"
            label_th: "Master Data"
          - slug: recipe
            label_en: "Recipe"
            label_th: "Recipe"
      - label_en: "Costing & Reporting"
        label_th: "ต้นทุนและรายงาน"
        modules:
          - slug: costing
            label_en: "Costing"
            label_th: "Costing"
          - slug: reporting-audit
            label_en: "Reporting & Audit"
            label_th: "Reporting & Audit"
      - label_en: "Administration"
        label_th: "การดูแลระบบ"
        modules:
          - slug: access-control
            label_en: "Access Control"
            label_th: "Access Control"
          - slug: system-config
            label_en: "System Config"
            label_th: "System Config"
          - slug: templates
            label_en: "Templates"
            label_th: "Templates"

  platform:
    label_en: "Carmen Platform"
    label_th: "Carmen Platform"
    home_slug: home
    groups:
      - label_en: "Tenancy"
        label_th: "Tenancy"
        modules:
          - slug: clusters
            label_en: "Clusters"
            label_th: "Clusters"
          - slug: business-units
            label_en: "Business Units"
            label_th: "Business Units"
      - label_en: "Identity & Access"
        label_th: "Identity & Access"
        modules:
          - slug: users
            label_en: "Users"
            label_th: "Users"
          - slug: auth-roles
            label_en: "Authentication & Roles"
            label_th: "Authentication & Roles"
          - slug: profile
            label_en: "Profile"
            label_th: "Profile"
      - label_en: "Reporting"
        label_th: "Reporting"
        modules:
          - slug: report-templates
            label_en: "Report Templates"
            label_th: "Report Templates"

# Legacy overrides — only consulted in --mode=mirror.
headers: {}
links: {}
```

Notes on the conversion:
- All 19 Inventory modules and 6 Platform modules are preserved — only their container key changed from `modules:` to `groups[N].modules:`
- Module slugs and `label_en` are byte-identical to the previous file (so URLs and EN sidebar labels do not change)
- Group labels are introduced for the first time; TH group labels are translated where natural (เช่น "Procurement" → "การจัดซื้อ"); Platform group labels left in EN initially (see spec § Risks)

- [ ] **Step 3.2: Verify YAML parses with the script's own loader**

Run a dry-run of build mode (no Wiki.js push, requires only the YAML to be valid):

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
source .env  # to set WIKI_API_URL and WIKI_API_TOKEN — sync_nav.py refuses to start without them
.venv/bin/python scripts/sync_nav.py --mode=build --dry-run 2>&1 | head -80
```

Expected output (first ~80 lines): the `[BUILD]` summary line showing item counts and a `[DRY-RUN] tree preview:` block listing all items per locale. The EN tree should contain (in order):
- 1 book header `Carmen Inventory`, 1 link `Home`
- 6 group headers + 19 module links for Inventory
- 1 divider
- 1 book header `Carmen Platform`, 1 link `Home`
- 3 group headers + 6 module links for Platform
- Total EN items: 1 + 1 + (6 + 19) + 1 + 1 + 1 + (3 + 6) = **39 items**
- Same shape for TH: 39 items

The headline line should read `[BUILD]  en: 39 items, th: 39 items`.

If you do not have a `.env` with `WIKI_API_URL` / `WIKI_API_TOKEN` set, the script exits with code 2 before reaching the YAML parse. In that case, export placeholder values so the script proceeds to dry-run:
```bash
WIKI_API_URL=http://placeholder WIKI_API_TOKEN=placeholder \
  .venv/bin/python scripts/sync_nav.py --mode=build --dry-run 2>&1 | head -80
```

- [ ] **Step 3.3: Commit the YAML migration**

```bash
git add scripts/nav-overrides.yaml
git commit -m "$(cat <<'EOF'
scripts(nav-overrides): migrate both books from flat modules: to groups:

Group Inventory's 19 modules into 6 categories (Overview, Procurement,
Inventory Operations, Product & Recipe, Costing & Reporting,
Administration) and Platform's 6 modules into 3 categories (Tenancy,
Identity & Access, Reporting). Module slugs and EN labels unchanged;
TH labels added at the group level.
EOF
)"
```

---

## Task 4: Rewrite Inventory book home.md TOC (EN + TH together)

**Files:**
- Modify: `en/inventory/home.md`
- Modify: `th/inventory/home.md`

The home.md TOC should mirror the sidebar group structure so that readers landing on the book home see the same organization as the sidebar.

- [ ] **Step 4.1: Replace `en/inventory/home.md` contents**

Open `en/inventory/home.md`. Update `date:` to the current date (`2026-05-19T00:00:00.000Z` works) but keep `dateCreated:` unchanged. Then replace the body (line 11 onward, i.e., everything after the frontmatter closing `---`) with:

```markdown
# Carmen Inventory

Reference manual for developers and QA engineers working on the Carmen Inventory ERP — a hospitality supply chain product.

## 1. Overview

| Module | What it covers |
|---|---|
| [Dashboard](/en/inventory/dashboard/home) | Summary views and KPIs |

## 2. Procurement

| Module | What it covers |
|---|---|
| [Purchase Request](/en/inventory/purchase-request/home) | PR approval flow |
| [Purchase Order](/en/inventory/purchase-order/home) | PO lifecycle |
| [Good Receive Note](/en/inventory/good-receive-note/home) | GRN flow, receiving, edge cases |
| [Vendor Pricelist](/en/inventory/vendor-pricelist/home) | Vendor catalog and pricing |

## 3. Inventory Operations

| Module | What it covers |
|---|---|
| [Inventory](/en/inventory/inventory/home) | Stock movements, valuation |
| [Inventory Adjustment](/en/inventory/inventory-adjustment/home) | Manual adjustments and reasons |
| [Physical Count](/en/inventory/physical-count/home) | Count cycles and reconciliation |
| [Spot Check](/en/inventory/spot-check/home) | Random count workflows |
| [Store Requisition](/en/inventory/store-requisition/home) | Inter-store transfers |

## 4. Product & Recipe

| Module | What it covers |
|---|---|
| [Product](/en/inventory/product/home) | Product catalog and attributes |
| [Master Data](/en/inventory/master-data/home) | Reference data and lookups |
| [Recipe](/en/inventory/recipe/home) | Recipe and BOM |

## 5. Costing & Reporting

| Module | What it covers |
|---|---|
| [Costing](/en/inventory/costing/home) | Calculation methods, FIFO, weighted average |
| [Reporting & Audit](/en/inventory/reporting-audit/home) | Reports and audit trail |

## 6. Administration

| Module | What it covers |
|---|---|
| [Access Control](/en/inventory/access-control/home) | Roles, permissions, gates |
| [System Config](/en/inventory/system-config/home) | Tenant-level settings |
| [Templates](/en/inventory/templates/home) | Document templates |

## 7. How to use this book

- Start with the module home page for an overview
- Drill into sub-pages for data models, UI flows, and edge cases
- See the [global wiki landing](/en/home) for the Platform book
```

- [ ] **Step 4.2: Replace `th/inventory/home.md` contents**

Open `th/inventory/home.md`. Update `date:` to `2026-05-19T00:00:00.000Z`. Replace the body with:

```markdown
# Carmen Inventory

คู่มืออ้างอิงสำหรับนักพัฒนาและ QA ที่ทำงานกับ Carmen Inventory ERP — ระบบ supply chain สำหรับโรงแรม

## 1. ภาพรวม

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Dashboard](/th/inventory/dashboard/home) | สรุปและ KPI |

## 2. การจัดซื้อ

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Purchase Request](/th/inventory/purchase-request/home) | กระบวนการอนุมัติ PR |
| [Purchase Order](/th/inventory/purchase-order/home) | วงจรชีวิตของ PO |
| [Good Receive Note](/th/inventory/good-receive-note/home) | กระบวนการรับสินค้า |
| [Vendor Pricelist](/th/inventory/vendor-pricelist/home) | แค็ตตาล็อกและราคาผู้ขาย |

## 3. การดำเนินงานคลัง

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Inventory](/th/inventory/inventory/home) | การเคลื่อนไหวสต็อก การประเมินมูลค่า |
| [Inventory Adjustment](/th/inventory/inventory-adjustment/home) | การปรับสต็อกและเหตุผล |
| [Physical Count](/th/inventory/physical-count/home) | รอบนับสต็อกและการกระทบยอด |
| [Spot Check](/th/inventory/spot-check/home) | การสุ่มนับ |
| [Store Requisition](/th/inventory/store-requisition/home) | โอนสินค้าระหว่างคลัง |

## 4. สินค้าและสูตร

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Product](/th/inventory/product/home) | แค็ตตาล็อกสินค้าและคุณสมบัติ |
| [Master Data](/th/inventory/master-data/home) | ข้อมูลอ้างอิงและ lookups |
| [Recipe](/th/inventory/recipe/home) | สูตรและ BOM |

## 5. ต้นทุนและรายงาน

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Costing](/th/inventory/costing/home) | วิธีคิดต้นทุน FIFO Weighted Average |
| [Reporting & Audit](/th/inventory/reporting-audit/home) | รายงานและ audit trail |

## 6. การดูแลระบบ

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Access Control](/th/inventory/access-control/home) | บทบาท สิทธิ์ การควบคุมการเข้าถึง |
| [System Config](/th/inventory/system-config/home) | การตั้งค่าระดับ tenant |
| [Templates](/th/inventory/templates/home) | เทมเพลตเอกสาร |

## 7. การใช้งาน book นี้

- เริ่มจากหน้า home ของแต่ละโมดูลเพื่อภาพรวม
- เจาะลึก sub-pages สำหรับ data model, UI flow, edge cases
- ดู [global wiki landing](/th/home) สำหรับ Platform book
```

- [ ] **Step 4.3: Verify both files parse and have matching section counts**

Quick sanity check — both files should have 7 `## N. ` headings:

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
grep -c "^## [0-9]\." en/inventory/home.md th/inventory/home.md
```

Expected:
```
en/inventory/home.md:7
th/inventory/home.md:7
```

- [ ] **Step 4.4: Commit Inventory home.md updates**

```bash
git add en/inventory/home.md th/inventory/home.md
git commit -m "$(cat <<'EOF'
docs(inventory/home): rewrite TOC into 6 group sections mirroring sidebar

Replace the flat ## 1. Modules table with one numbered section per
group (Overview, Procurement, Inventory Operations, Product & Recipe,
Costing & Reporting, Administration). Section ordering and group
labels match the sidebar produced by sync_nav --mode=build.
EOF
)"
```

---

## Task 5: Rewrite Platform book home.md TOC (EN + TH)

**Files:**
- Modify: `en/platform/home.md`
- Modify: `th/platform/home.md`

The Platform home is currently a skeleton (`At a Glance` / `References` / `TODO`). Replace it with the same group-section pattern as the Inventory book home so the two are structurally consistent.

- [ ] **Step 5.1: Replace `en/platform/home.md` contents**

Open `en/platform/home.md`. Update `date:` to `2026-05-19T00:00:00.000Z`, keep `dateCreated:` unchanged. Replace the body (line 11 onward) with:

```markdown
# Carmen Platform

Reference manual for developers and support engineers working on the Carmen Platform admin product — cluster, business unit, user, and report-template management.

## 1. Tenancy

| Module | What it covers |
|---|---|
| [Clusters](/en/platform/clusters/home) | Tenant cluster hierarchy and ownership |
| [Business Units](/en/platform/business-units/home) | Property / BU management within a cluster |

## 2. Identity & Access

| Module | What it covers |
|---|---|
| [Users](/en/platform/users/home) | User accounts and BU membership |
| [Authentication & Roles](/en/platform/auth-roles/home) | Sign-in flows and role assignment |
| [Profile](/en/platform/profile/home) | The signed-in user's own profile |

## 3. Reporting

| Module | What it covers |
|---|---|
| [Report Templates](/en/platform/report-templates/home) | Print / export template definitions |

## 4. How to use this book

- Start with the module home page for an overview
- Drill into sub-pages for data models, UI flows, and edge cases
- See the [global wiki landing](/en/home) for the Inventory book
```

- [ ] **Step 5.2: Replace `th/platform/home.md` contents**

Open `th/platform/home.md`. Update `date:` to `2026-05-19T00:00:00.000Z`. Replace the body with:

```markdown
# Carmen Platform

คู่มืออ้างอิงสำหรับนักพัฒนาและทีม support ที่ทำงานกับ Carmen Platform admin — การจัดการ cluster, business unit, ผู้ใช้ และ report template

## 1. Tenancy

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Clusters](/th/platform/clusters/home) | โครงสร้าง cluster ของ tenant และความเป็นเจ้าของ |
| [Business Units](/th/platform/business-units/home) | จัดการสาขา / business unit ภายใน cluster |

## 2. Identity & Access

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Users](/th/platform/users/home) | บัญชีผู้ใช้และการอยู่ใน BU |
| [Authentication & Roles](/th/platform/auth-roles/home) | กระบวนการ sign-in และการกำหนด role |
| [Profile](/th/platform/profile/home) | โปรไฟล์ของผู้ใช้ที่ล็อกอินอยู่ |

## 3. Reporting

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Report Templates](/th/platform/report-templates/home) | นิยามเทมเพลตสำหรับพิมพ์ / export |

## 4. การใช้งาน book นี้

- เริ่มจากหน้า home ของแต่ละโมดูลเพื่อภาพรวม
- เจาะลึก sub-pages สำหรับ data model, UI flow, edge cases
- ดู [global wiki landing](/th/home) สำหรับ Inventory book
```

- [ ] **Step 5.3: Verify section count**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
grep -c "^## [0-9]\." en/platform/home.md th/platform/home.md
```

Expected:
```
en/platform/home.md:4
th/platform/home.md:4
```

- [ ] **Step 5.4: Commit Platform home.md updates**

```bash
git add en/platform/home.md th/platform/home.md
git commit -m "$(cat <<'EOF'
docs(platform/home): replace skeleton TOC with group sections

Drop the At a Glance / References / TODO skeleton in favor of three
group sections (Tenancy, Identity & Access, Reporting) that mirror
the sidebar produced by sync_nav --mode=build. Matches the structure
of the Inventory book home page.
EOF
)"
```

---

## Task 6: Dry-run verification and push to dev Wiki.js (user-driven)

**Files:** None modified — this task verifies the full pipeline and pushes the navigation to the live dev Wiki.js instance.

> **Note for executor:** Step 6.2 mutates shared infrastructure (the dev Wiki.js navigation tree). Pause for explicit user approval before running it, even though earlier tasks were authorized. The user retains the right to inspect the dry-run output first.

- [ ] **Step 6.1: Final dry-run of the full build**

Run from the repo root with `.env` sourced:

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
source .env
.venv/bin/python scripts/sync_nav.py --mode=build --dry-run
```

Expected: `[BUILD]  en: 39 items, th: 39 items` followed by a `[DRY-RUN] tree preview:` block. Scan the preview and confirm:
- Inventory book block: book header `Carmen Inventory` → `Home` link → 6 group headers (`Overview`, `Procurement`, `Inventory Operations`, `Product & Recipe`, `Costing & Reporting`, `Administration`), each followed by its module links
- One `divider` row between the two books
- Platform book block: book header `Carmen Platform` → `Home` link → 3 group headers (`Tenancy`, `Identity & Access`, `Reporting`), each followed by its module links
- The TH locale shows the same shape with `/th/...` targets and Thai group labels for Inventory (and EN labels for Platform groups)

If anything looks off, stop here and re-check the YAML.

- [ ] **Step 6.2: Push to the dev Wiki.js — ASK USER FIRST**

This mutates the live dev Wiki.js navigation tree at `http://dev.blueledgers.com:3987/`. Confirm with the user before running:

> "Dry-run looks correct. Push the new nav tree to the dev Wiki.js now? This replaces the current EN + TH navigation in `--mode=build` (Wiki.js will not retain the old tree)."

On approval:

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
source .env
.venv/bin/python scripts/sync_nav.py --mode=build
```

Expected: `[BUILD]  en: 39 items, th: 39 items` then `[PUSH]   updateTree succeeded.`

If `updateTree` fails: `sync_nav.py` raises `SystemExit` with the GraphQL error code and message. Report the error to the user, do **not** retry blindly — the most likely cause is that Wiki.js navigation mode is not `STATIC`, in which case the user must switch it in the Wiki.js admin UI (Administration → Navigation → Mode = Static).

- [ ] **Step 6.3: Visual verification**

Open `http://dev.blueledgers.com:3987/en/inventory/home` and `http://dev.blueledgers.com:3987/th/inventory/home` in a browser. Confirm:
- Sidebar shows `Carmen Inventory` as a heading, then `Home`, then 6 group headings each followed by its modules in the declared order
- The divider sits between Inventory and Platform
- `Carmen Platform` heading is followed by `Home`, then 3 group headings + modules
- TH locale shows Thai group labels for Inventory
- Clicking any module link navigates to the existing module home page (no 404s)

If any group header is visually indistinguishable from a module link, capture a screenshot and report — the spec § Risks calls out adding a divider before each group header as a follow-up if this happens.

- [ ] **Step 6.4: No additional commit**

The push is a runtime mutation against Wiki.js; nothing on disk changed in this task.

---

## Final checklist

After Task 6, run a final status check:

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git log --oneline -6
git status
.venv/bin/pytest scripts/test_sync_nav.py -v
```

Expected:
- 4 new commits on top of `31a4fe4` (spec commit): test/impl, yaml, inventory home, platform home
- Clean working tree
- All `pytest` tests pass
