#!/usr/bin/env python3
"""Catalog Mermaid diagrams in carmen/docs and check EN/TH diagram parity.

Spec: docs/superpowers/specs/2026-09-28-diagrams-from-carmen-design.md §2, §5.3.

  python3 scripts/diagram_catalog.py                 # (re)build .specs/diagram-catalog.md
  python3 scripts/diagram_catalog.py --summary       # print status counts, write nothing
  python3 scripts/diagram_catalog.py --require-done  # exit 1 while any candidate/unmapped remains
  python3 scripts/diagram_catalog.py --check-parity [--baseline FILE]  # label-stripped EN/TH shapes

Decisions live in .specs/diagram-decisions/<module>.tsv as `<id>\t<status>\t<page>`
and override the automatic status on every rebuild, so re-running never loses a
decision. The block between the ALLOW-LIST markers in the catalog is kept verbatim.
"""
import argparse, hashlib, re, sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOCS = ROOT.parent / "carmen" / "docs"
DEFAULT_OUT = ROOT / ".specs" / "diagram-catalog.md"
DEFAULT_DECISIONS = ROOT / ".specs" / "diagram-decisions"
OUT = "out-of-scope"
UNCLOSED = "rejected: unclosed"
SKIP_DIRS = {"node_modules", ".git"}

# Source path (relative to carmen/docs) -> wiki module, or OUT.
# A key matches a path equal to it or under it as a directory; the longest key wins.
# Paths matching no key are "unmapped" and must be resolved by editing this map.
MODULE_MAP = {
    # app/ (newest tree)
    "app/finance/account-code-mapping": "general-ledger",
    "app/finance/currency-management": "master-data",
    "app/finance/department-management": "master-data",
    "app/finance/exchange-rate-management": "master-data",
    "app/guides": OUT,
    "app/inventory-management/fractional-inventory": "inventory",
    "app/inventory-management/inventory-adjustments": "inventory-adjustment",
    "app/inventory-management/inventory-overview": "inventory",
    "app/inventory-management/inventory-transactions": "inventory",
    "app/inventory-management/lot-based-costing": "costing",
    "app/inventory-management/period-end": "inventory",
    "app/inventory-management/physical-count": "physical-count",
    "app/inventory-management/physical-count-management": "physical-count",
    "app/inventory-management/spot-check": "spot-check",
    "app/inventory-management/stock-in": "inventory",
    "app/inventory-management/stock-overview": "inventory",
    "app/inventory-management/transaction-categories": "inventory-adjustment",
    "app/inventory-management/transactions": "inventory",
    "app/operational-planning/recipe-management": "recipe",
    "app/operational-planning/demand-forecasting": OUT,
    "app/operational-planning/inventory-planning": OUT,
    "app/operational-planning/menu-engineering": OUT,
    "app/procurement/credit-note": "purchase-order",
    "app/procurement/goods-received-notes": "good-receive-note",
    "app/procurement/my-approvals": OUT,
    "app/procurement/purchase-orders": "purchase-order",
    "app/procurement/purchase-request-templates": "templates",
    "app/procurement/purchase-requests": "purchase-request",
    "app/product-management/categories": "product",
    "app/product-management/products": "product",
    "app/product-management/units": "master-data",
    "app/reference": OUT,
    "app/shared-methods/inventory-valuation": "costing",
    "app/store-operations/sales-consumption": OUT,
    "app/store-operations/stock-replenishment": "store-requisition",
    "app/store-operations/store-requisitions": "store-requisition",
    "app/store-operations/wastage-reporting": "inventory-adjustment",
    "app/system-administration": "system-config",              # root FD/TS files only; deeper keys still win
    "app/system-administration/account-code-mapping": "general-ledger",
    "app/system-administration/business-rules": OUT,
    "app/system-administration/certifications": OUT,
    "app/system-administration/delivery-points": "master-data",
    "app/system-administration/location-management": "master-data",
    "app/system-administration/monitoring": OUT,
    "app/system-administration/notification-preferences": "reporting-audit",
    "app/system-administration/permission-management": "access-control",
    "app/system-administration/settings": "system-config",
    "app/system-administration/system-integrations": OUT,       # POS integration, no wiki module
    "app/system-administration/user-management": "access-control",
    "app/system-administration/workflow": "system-config",
    "app/template-guide": OUT,
    "app/vendor-management/ARC-2025-001-vendor-management-redesign.md": OUT,
    "app/vendor-management/price-lists": "vendor-pricelist",
    "app/vendor-management/pricelist-templates": "templates",
    "app/vendor-management/requests-for-pricing": "vendor-pricelist",
    "app/vendor-management/vendor-directory": "master-data",
    "app/vendor-management/vendor-portal": "vendor-pricelist",
    # documents/ (older tree)
    "documents/architecture": OUT,
    "documents/cn": "purchase-order",
    "documents/dashboard": "dashboard",
    "documents/grn": "good-receive-note",
    "documents/inv": "inventory",
    "documents/inventory": "inventory",
    "documents/pc": "physical-count",
    "documents/pm": "product",
    "documents/po": "purchase-order",
    "documents/pr": "purchase-request",
    "documents/prt": "templates",
    "documents/sa/features/notification-settings": "reporting-audit",
    "documents/sc": "spot-check",
    "documents/so": "store-requisition",
    "documents/sr": "store-requisition",
    "documents/stakeholders": OUT,
    "documents/store-ops": "store-requisition",
    "documents/vm": "vendor-pricelist",
    "documents/DOCUMENTATION-CATALOG.md": OUT,
    "documents/MERMAID-TEST.md": OUT,
    "documents/SYSTEM-DOCUMENTATION-INDEX.md": OUT,
    "documents/SYSTEM-GAPS-AND-ROADMAP.md": OUT,
    "documents/carmen-erp-system-requirements-documentation.md": OUT,
    "documents/module-spec-template.md": OUT,
    # loose top-level folders
    "Inventory": "inventory",
    "architecture/fifo-calc.md": "costing",
    "carmen-recreation-docs": OUT,                              # prototype screen specifications
    "cn": "purchase-order",
    "good-recive-note-managment": "good-receive-note",
    "inventory-adjustment": "inventory-adjustment",
    "pages/po": "purchase-order",
    "pages/pr": "purchase-request",
    "purchase-order-management": "purchase-order",
    "purchase-request-management": "purchase-request",
    "store-requisitions": "store-requisition",
    "system-overview/Procurement-Process-Flow.md": "purchase-request",
    "technical-specifications/procurement": OUT,                # older duplicate of app/procurement TS
    "use-cases/procurement": "purchase-request",
    "vendor-pricelist-management": "vendor-pricelist",
    "mobile-app": OUT,
    "recipe-module/mobile-app.md": OUT,
    "platform-notification-service": OUT,
    "design/system-architecture.md": OUT,
    "developer-guides": OUT,
    "prd": OUT,
}

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w-]*)")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
NON_STMT = re.compile(r"^(%%|subgraph\b|end\b|classDef\b|class\b|style\b|linkStyle\b|direction\b|click\b)")
DECISION = re.compile(r"^(imported|rejected: (diverges|covered|unverifiable|too-large|render|page-full))$")
PAGE_BY_TYPE = {"erDiagram": "01-data-model", "stateDiagram-v2": "02-business-rules",
                "stateDiagram": "02-business-rules"}
ALLOW_START, ALLOW_END = "<!-- ALLOW-LIST:START -->", "<!-- ALLOW-LIST:END -->"

# spec §2.5 checkpoint: candidate filter applied after dedup, before decisions.
FILTER_TYPES = {"flowchart", "graph", "stateDiagram-v2", "stateDiagram", "erDiagram", "sequenceDiagram"}
PROTOTYPE_HEADING = re.compile(
    r"architecture|component|hierarch|page ?load|context diagram|level 0|deployment|tech stack|navigation|state management|layer")
MAX_STMTS = 25

# spec §5.3 shape hash: constructs stripped to compare EN/TH structure with labels ignored.
NOTE_START = re.compile(r"^note\b")
NOTE_END = re.compile(r"^end note\b")
QUOTED = re.compile(r'"[^"]*"')
EDGE_LABEL = re.compile(r"\|[^|]*\|")
BRACKETED = re.compile(r"\[[^\[\]]*\]|\([^()]*\)|\{[^{}]*\}")
PARTICIPANT_AS = re.compile(r"^(participant|actor)(\s+\S+)\s+as\s+.*$")
SUBGRAPH_LINE = re.compile(r"^subgraph\s+(\S+)")
ENTITY_KEY = re.compile(r"^(PK|FK|UK)$")


@dataclass
class Row:
    id: str
    source: str
    line: int
    heading: str
    dtype: str
    stmts: int
    module: str | None
    page: str = "-"
    status: str = "candidate"


def mermaid_blocks(text):
    """Yield (line_no, heading, body) per ```mermaid fence; body is None when never closed.

    Other fenced blocks are skipped whole, so '# comment' lines inside ```bash are
    not mistaken for headings.
    """
    lines = text.splitlines()
    heading, i = "", 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            h = HEADING.match(lines[i])
            if h:
                heading = h.group(1)
            i += 1
            continue
        fence, info = m.group(1), m.group(2)
        close = re.compile(r"^\s*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$")
        end = next((j for j in range(i + 1, len(lines)) if close.match(lines[j])), None)
        if info == "mermaid":
            yield i + 1, heading, None if end is None else "\n".join(lines[i + 1:end])
        if end is None:
            return
        i = end + 1


def block_id(body):
    return hashlib.sha1(" ".join(body.split()).encode()).hexdigest()[:10]


def _strip_entity_attr(s):
    """erDiagram attribute line: keep only type + name plus any PK/FK/UK keys."""
    toks = s.split()
    if len(toks) < 2:
        return s
    keys = [t for t in toks[2:] if ENTITY_KEY.match(t.rstrip(","))]
    return " ".join(toks[:2] + keys)


def block_shape(body):
    """Hash `body` after stripping human-readable label text (spec §5.3).

    A TH block whose only differences from its EN counterpart are translated
    labels hashes equal; a changed node id / edge / state / participant /
    entity does not.
    """
    lines = body_lines(body)
    dtype = lines[0].split()[0] if lines else "?"
    er = dtype == "erDiagram"
    out = []
    skipping = False
    in_entity = False
    for line in lines:
        if skipping:
            if NOTE_END.match(line):
                skipping = False
            continue
        if NOTE_START.match(line) and ":" not in line:
            out.append("note")
            skipping = True
            continue
        entering = er and line.endswith("{")
        exiting = er and (line == "}" or line.startswith("}"))
        s = QUOTED.sub('""', line)
        if not er:
            s = EDGE_LABEL.sub("||", s)
            prev = None
            while prev != s:
                prev = s
                s = BRACKETED.sub(lambda m: m.group(0)[0] + m.group(0)[-1], s)
        idx = s.find(":")
        if idx != -1:
            s = s[:idx + 1]
        m = PARTICIPANT_AS.match(s)
        if m:
            s = m.group(1) + m.group(2)
        m = SUBGRAPH_LINE.match(s)
        if m:
            s = f"subgraph {m.group(1)}"
        if er and in_entity and not entering and not exiting:
            s = _strip_entity_attr(s)
        out.append(" ".join(s.split()))
        if er:
            in_entity = False if exiting else (True if entering else in_entity)
    return hashlib.sha1(" ".join(out).encode()).hexdigest()[:10]


def body_lines(body):
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    if lines and lines[0] == "---":  # mermaid frontmatter (title/config)
        lines = lines[next((k for k in range(1, len(lines)) if lines[k] == "---"), 0) + 1:]
    return [l for l in lines if not l.startswith("%%")]


def diagram_type(body):
    lines = body_lines(body)
    return lines[0].split()[0] if lines else "?"


def statements(body):
    return max(0, len([l for l in body_lines(body) if not NON_STMT.match(l)]) - 1)


def module_for(rel):
    for key in sorted(MODULE_MAP, key=len, reverse=True):
        if rel == key or rel.startswith(key + "/"):
            return MODULE_MAP[key]
    return None


def suggest_page(module, dtype, wiki_root):
    stem = PAGE_BY_TYPE.get(dtype, "03-user-flow")
    if (wiki_root / "en" / "inventory" / module / f"{stem}.md").is_file():
        return f"{module}/{stem}"
    return f"{module}/(choose)"


def rank(r):
    in_scope = 0 if r.module not in (None, OUT) else 1
    tree = 0 if r.source.startswith("app/") else 2 if r.source.startswith("documents/") else 1
    return (in_scope, tree, r.source, r.line)


def load_decisions(ddir):
    out = {}
    if not ddir.is_dir():
        return out
    for f in sorted(ddir.glob("*.tsv")):
        for n, raw in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip() or raw.startswith("#"):
                continue
            parts = raw.split("\t")
            if len(parts) != 3 or not DECISION.match(parts[1]):
                sys.exit(f"{f}:{n}: expected '<id>\\t<status>\\t<page>' with a valid status, got {raw!r}")
            out[parts[0]] = (parts[1], parts[2], f"{f}:{n}")
    return out


def build(docs, ddir, wiki_root):
    if not docs.is_dir():
        sys.exit(f"carmen docs not found: {docs}")
    rows = []
    for f in sorted(docs.rglob("*.md")):
        if SKIP_DIRS & set(f.parts):
            continue
        rel = f.relative_to(docs).as_posix()
        module = module_for(rel)
        for line, heading, body in mermaid_blocks(f.read_text(encoding="utf-8", errors="replace")):
            if body is None:
                rows.append(Row(block_id(f"{rel}:{line}"), rel, line, heading, "?", 0, module,
                                status=UNCLOSED))
                continue
            rows.append(Row(block_id(body), rel, line, heading, diagram_type(body),
                            statements(body), module))
    for r in rows:
        if r.status != "candidate":
            continue
        if r.module is None:
            r.status = "unmapped"
        elif r.module == OUT:
            r.status = OUT
        else:
            r.page = suggest_page(r.module, r.dtype, wiki_root)
    groups = defaultdict(list)
    for r in rows:
        if r.status != UNCLOSED:
            groups[r.id].append(r)
    survivors = {}
    for rid, g in groups.items():
        g.sort(key=rank)
        survivors[rid] = g[0]
        for r in g[1:]:
            r.status, r.page = f"duplicate of {g[0].source}:{g[0].line}", "-"
    for r in survivors.values():
        if r.status != "candidate":
            continue
        if not r.source.startswith("app/"):
            reason = "not docs/app"
        elif r.dtype not in FILTER_TYPES:
            reason = f"type {r.dtype}"
        elif PROTOTYPE_HEADING.search(r.heading.lower()):
            reason = "prototype heading"
        elif r.stmts > MAX_STMTS:
            reason = f"stmts > {MAX_STMTS}"
        else:
            continue
        r.status, r.page = f"out-of-scope (filter: {reason})", "-"
    for rid, (status, page, where) in load_decisions(ddir).items():
        if rid not in survivors:
            sys.exit(f"{where}: unknown or duplicate-only id {rid}")
        survivors[rid].status, survivors[rid].page = status, page
    return rows


def status_key(status):
    if status.startswith("duplicate of"):
        return "duplicate"
    if status.startswith("out-of-scope (filter:"):
        return "out-of-scope (filter)"
    return status


def summary(rows):
    c = Counter(status_key(r.status) for r in rows)
    return "\n".join(f"| {k} | {v} |" for k, v in sorted(c.items()))


def allow_list(out_path):
    if out_path.is_file():
        t = out_path.read_text(encoding="utf-8")
        a, b = t.find(ALLOW_START), t.find(ALLOW_END)
        if a != -1 and b > a:
            return t[a:b + len(ALLOW_END)]
    return f"{ALLOW_START}\n_Not recorded yet — filled in by the render check (spec §3)._\n{ALLOW_END}"


def cell(s):
    return s.replace("|", "\\|")[:70]


def render(rows, out_path):
    sections = defaultdict(list)
    for r in rows:
        key = r.module if r.module not in (None, OUT) else f"({'unmapped' if r.module is None else OUT})"
        sections[key].append(r)
    order = sorted(k for k in sections if not k.startswith("(")) + sorted(k for k in sections if k.startswith("("))
    parts = [
        "# Diagram Catalog", "",
        "Generated by `scripts/diagram_catalog.py` — do not edit rows by hand. "
        "Record decisions in `.specs/diagram-decisions/<module>.tsv` and rebuild.", "",
        "Spec: `docs/superpowers/specs/2026-09-28-diagrams-from-carmen-design.md`", "",
        "## Syntax allow-list", "", allow_list(out_path), "",
        "## Summary", "", "| status | count |", "|---|---|", summary(rows), "",
    ]
    for k in order:
        parts += [f"## {k}", "", "| id | source:line | type | stmts | heading | wiki page | status |",
                  "|---|---|---|---|---|---|---|"]
        for r in sorted(sections[k], key=lambda r: (r.source, r.line)):
            parts.append(f"| {r.id} | {r.source}:{r.line} | {r.dtype} | {r.stmts} | {cell(r.heading)} "
                         f"| {r.page} | {r.status} |")
        parts.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")


def check_parity(wiki_root, baseline):
    known = set(baseline.read_text(encoding="utf-8").splitlines()) if baseline else set()
    en_root = wiki_root / "en"
    pages = [en_root / "inventory.md"] + sorted((en_root / "inventory").rglob("*.md"))
    new = []
    for en in pages:
        if not en.is_file():
            continue
        rel = en.relative_to(en_root).as_posix()
        eh = [block_shape(b) for _, _, b in mermaid_blocks(en.read_text(encoding="utf-8")) if b is not None]
        th = wiki_root / "th" / rel
        if not th.is_file():
            line = f"NO-TH  {rel} (en={len(eh)})" if eh else None
        else:
            thh = [block_shape(b) for _, _, b in mermaid_blocks(th.read_text(encoding="utf-8")) if b is not None]
            line = None if eh == thh else f"DIFF   {rel} (en={len(eh)} th={len(thh)})"
        if line:
            print(("known  " if line in known else "") + line)
            if line not in known and line.startswith("DIFF"):
                new.append(line)
    print(f"---- parity: {len(new)} new mismatch(es) ----")
    return 1 if new else 0


def main():
    ap = argparse.ArgumentParser(description="Catalog carmen/docs Mermaid diagrams; check EN/TH parity.")
    ap.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    ap.add_argument("--wiki-root", type=Path, default=ROOT)
    ap.add_argument("--summary", action="store_true", help="print status counts only")
    ap.add_argument("--require-done", action="store_true", help="exit 1 while candidate/unmapped rows remain")
    ap.add_argument("--check-parity", action="store_true", help="compare EN vs TH Mermaid blocks")
    ap.add_argument("--baseline", type=Path, help="parity lines to treat as pre-existing")
    a = ap.parse_args()
    if a.check_parity:
        return check_parity(a.wiki_root, a.baseline)
    rows = build(a.docs, a.decisions, a.wiki_root)
    print(summary(rows))
    if a.require_done:
        left = [r for r in rows if r.status in ("candidate", "unmapped")]
        for r in left:
            print(f"OPEN   {r.id} {r.source}:{r.line} [{r.status}]")
        return 1 if left else 0
    if not a.summary:
        render(rows, a.out)
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
