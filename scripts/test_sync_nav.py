"""Unit tests for sync_nav."""
from pathlib import Path

from scripts.sync_nav import parse_index_headings


def test_parse_index_headings_returns_index_keyed_dict(tmp_path: Path):
    """Headings are returned in index order as a list of strings."""
    index_md = tmp_path / "index.md"
    index_md.write_text(
        "---\ntitle: Home\n---\n\n"
        "# Title\n\n"
        "## 1. First\n\nbody\n\n"
        "## 2. Second\n\nbody\n\n"
        "## 3. Third\n",
        encoding="utf-8",
    )
    assert parse_index_headings(index_md) == ["First", "Second", "Third"]


def test_parse_index_headings_strips_leading_number(tmp_path: Path):
    """Numbering prefix `N. ` is stripped from each heading."""
    index_md = tmp_path / "index.md"
    index_md.write_text("## 1. Procure-to-Pay\n## 2. Inventory\n", encoding="utf-8")
    assert parse_index_headings(index_md) == ["Procure-to-Pay", "Inventory"]


def test_parse_index_headings_ignores_h1_and_h3(tmp_path: Path):
    """Only ## (h2) headings count."""
    index_md = tmp_path / "index.md"
    index_md.write_text(
        "# Top\n## 1. A\n### 1.1 A-sub\n## 2. B\n",
        encoding="utf-8",
    )
    assert parse_index_headings(index_md) == ["A", "B"]


from scripts.sync_nav import build_header_label_map


def test_build_header_label_map_pairs_by_index():
    en = ["About", "Dashboard", "Procure-to-Pay"]
    th = ["เกี่ยวกับ", "แดชบอร์ด", "Procure-to-Pay"]
    assert build_header_label_map(en, th) == {
        "About": "เกี่ยวกับ",
        "Dashboard": "แดชบอร์ด",
        "Procure-to-Pay": "Procure-to-Pay",
    }


def test_build_header_label_map_mismatch_returns_partial_and_warns(caplog):
    """If lists differ in length, pair up to min(len) and log a warning."""
    en = ["A", "B", "C"]
    th = ["ก", "ข"]
    with caplog.at_level("WARNING"):
        out = build_header_label_map(en, th)
    assert out == {"A": "ก", "B": "ข"}
    assert any("index.md heading count" in r.message for r in caplog.records)


from scripts.sync_nav import load_overrides


def test_load_overrides_parses_headers_and_links(tmp_path: Path):
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text(
        'headers:\n'
        '  "Procure-to-Pay": "จัดซื้อ"\n'
        'links:\n'
        '  "https://example.com": "ตัวอย่าง"\n',
        encoding="utf-8",
    )
    out = load_overrides(cfg)
    assert out == {
        "headers": {"Procure-to-Pay": "จัดซื้อ"},
        "links": {"https://example.com": "ตัวอย่าง"},
    }


def test_load_overrides_empty_sections(tmp_path: Path):
    """Empty mappings (`{}`) become empty dicts."""
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text("headers: {}\nlinks: {}\n", encoding="utf-8")
    assert load_overrides(cfg) == {"headers": {}, "links": {}}


def test_load_overrides_missing_section_defaults_to_empty(tmp_path: Path):
    """If `headers:` or `links:` is omitted, default to empty dict."""
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text("headers:\n  A: B\n", encoding="utf-8")
    out = load_overrides(cfg)
    assert out == {"headers": {"A": "B"}, "links": {}}


from scripts.sync_nav import resolve_th_page_title


def _write_md(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntitle: {title}\ndescription: x\npublished: true\n---\n\n# {title}\n",
        encoding="utf-8",
    )


def test_resolve_th_page_title_file_form(tmp_path: Path):
    """target='/th/foo' resolves to th/foo.md if that file exists."""
    _write_md(tmp_path / "th" / "foo.md", "หน้า Foo")
    assert resolve_th_page_title(tmp_path, "/th/foo") == "หน้า Foo"


def test_resolve_th_page_title_folder_form(tmp_path: Path):
    """target='/th/foo' resolves to th/foo/index.md if no th/foo.md exists."""
    _write_md(tmp_path / "th" / "foo" / "index.md", "Foo Index")
    assert resolve_th_page_title(tmp_path, "/th/foo") == "Foo Index"


def test_resolve_th_page_title_prefers_file_over_folder(tmp_path: Path):
    """If both th/foo.md and th/foo/index.md exist, the file wins."""
    _write_md(tmp_path / "th" / "foo.md", "FILE")
    _write_md(tmp_path / "th" / "foo" / "index.md", "FOLDER")
    assert resolve_th_page_title(tmp_path, "/th/foo") == "FILE"


def test_resolve_th_page_title_missing_returns_none(tmp_path: Path):
    """No file exists → None (caller falls back to EN label)."""
    assert resolve_th_page_title(tmp_path, "/th/missing") is None


def test_resolve_th_page_title_handles_subpath(tmp_path: Path):
    """target='/th/foo/bar' resolves to th/foo/bar.md."""
    _write_md(tmp_path / "th" / "foo" / "bar.md", "Bar")
    assert resolve_th_page_title(tmp_path, "/th/foo/bar") == "Bar"


from scripts.sync_nav import resolve_label, LabelSource


def _item(**kw):
    """Build a minimal navigation item dict with sensible defaults."""
    base = {
        "id": "abc",
        "kind": "link",
        "label": "EN Label",
        "icon": "",
        "targetType": "page",
        "target": "/th/foo",
        "visibilityMode": "all",
        "visibilityGroups": [],
    }
    base.update(kw)
    return base


def test_resolve_label_link_page_uses_frontmatter(tmp_path: Path):
    _write_md(tmp_path / "th" / "foo.md", "หน้า Foo")
    label, source = resolve_label(
        _item(),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert label == "หน้า Foo"
    assert source == LabelSource.FRONTMATTER


def test_resolve_label_link_page_missing_falls_back_to_en(tmp_path: Path):
    label, source = resolve_label(
        _item(target="/th/missing", label="Missing"),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert label == "Missing"
    assert source == LabelSource.FALLBACK


def test_resolve_label_header_uses_index_md(tmp_path: Path):
    label, source = resolve_label(
        _item(kind="header", label="Procure-to-Pay", target=""),
        repo_root=tmp_path,
        header_map={"Procure-to-Pay": "จัดซื้อจัดจ้าง"},
        overrides={"headers": {}, "links": {}},
    )
    assert label == "จัดซื้อจัดจ้าง"
    assert source == LabelSource.INDEX_MD


def test_resolve_label_header_falls_back_to_override(tmp_path: Path):
    """index.md doesn't have it → overrides.headers wins."""
    label, source = resolve_label(
        _item(kind="header", label="X", target=""),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {"X": "เอกซ์"}, "links": {}},
    )
    assert label == "เอกซ์"
    assert source == LabelSource.OVERRIDE


def test_resolve_label_header_falls_back_to_en(tmp_path: Path):
    """No index.md match, no override → EN label."""
    label, source = resolve_label(
        _item(kind="header", label="Unknown", target=""),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert label == "Unknown"
    assert source == LabelSource.FALLBACK


def test_resolve_label_link_url_uses_overrides(tmp_path: Path):
    label, source = resolve_label(
        _item(targetType="url", target="https://example.com", label="Example"),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {"https://example.com": "ตัวอย่าง"}},
    )
    assert label == "ตัวอย่าง"
    assert source == LabelSource.OVERRIDE


def test_resolve_label_divider_returns_none(tmp_path: Path):
    label, source = resolve_label(
        _item(kind="divider", label="", target=""),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert label is None
    assert source == LabelSource.NONE


from scripts.sync_nav import compute_diff


def test_compute_diff_empty_to_new():
    """First sync — th_old is empty."""
    th_old = []
    th_new = [_item(target="/th/foo", label="Foo")]
    diff = compute_diff(th_old, th_new)
    assert diff == {"old_count": 0, "new_count": 1, "all_new": True}


def test_compute_diff_replacement():
    """Re-sync — th_old has items, replaced."""
    th_old = [_item(target="/th/foo", label="OLD")]
    th_new = [_item(target="/th/foo", label="NEW")]
    diff = compute_diff(th_old, th_new)
    assert diff == {"old_count": 1, "new_count": 1, "all_new": False}


import uuid as _uuid
from scripts.sync_nav import transform_item


def test_transform_item_link_page_rewrites_target(tmp_path: Path):
    _write_md(tmp_path / "th" / "foo.md", "Foo TH")
    en_item = _item(target="/en/foo", label="Foo")
    new = transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert new["target"] == "/th/foo"
    assert new["label"] == "Foo TH"
    assert new["id"] != en_item["id"]  # fresh UUID
    _uuid.UUID(new["id"], version=4)    # parses as UUIDv4


def test_transform_item_link_url_keeps_target(tmp_path: Path):
    en_item = _item(targetType="url", target="https://example.com", label="Ex")
    new = transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {"https://example.com": "ตัวอย่าง"}},
    )
    assert new["target"] == "https://example.com"
    assert new["label"] == "ตัวอย่าง"


def test_transform_item_header_preserves_target(tmp_path: Path):
    en_item = _item(kind="header", label="Procure-to-Pay", target="")
    new = transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={"Procure-to-Pay": "จัดซื้อ"},
        overrides={"headers": {}, "links": {}},
    )
    assert new["target"] == ""
    assert new["label"] == "จัดซื้อ"
    assert new["kind"] == "header"


def test_transform_item_preserves_icon_and_visibility(tmp_path: Path):
    en_item = _item(
        target="/en/foo",
        icon="mdi-folder",
        visibilityMode="restricted",
        visibilityGroups=[1, 2],
    )
    new = transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert new["icon"] == "mdi-folder"
    assert new["visibilityMode"] == "restricted"
    assert new["visibilityGroups"] == [1, 2]


def test_transform_item_does_not_mutate_input(tmp_path: Path):
    en_item = _item(target="/en/foo", label="Foo")
    original = dict(en_item)
    transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert en_item == original


from scripts.sync_nav import transform_items


def test_transform_items_counts_sources(tmp_path: Path):
    _write_md(tmp_path / "th" / "a.md", "หน้า A")
    en_items = [
        _item(kind="header", label="Procure-to-Pay", target=""),       # index.md
        _item(target="/en/a", label="A"),                              # frontmatter
        _item(target="/en/missing", label="Missing"),                  # fallback
        _item(targetType="url", target="https://x", label="X"),        # override
        _item(kind="divider", label="", target=""),                    # none
    ]
    new_items, counts = transform_items(
        en_items,
        repo_root=tmp_path,
        header_map={"Procure-to-Pay": "จัดซื้อ"},
        overrides={"headers": {}, "links": {"https://x": "เอ็กซ์"}},
    )
    assert len(new_items) == 5
    assert counts == {
        "frontmatter": 1,
        "index.md": 1,
        "override": 1,
        "fallback": 1,
        "none": 1,
    }


from scripts.sync_nav import format_item_line, format_summary


def test_format_item_line_link_page():
    en = _item(target="/en/purchase-request", label="Purchase Request")
    th = _item(target="/th/purchase-request", label="คำขอซื้อ")
    line = format_item_line(en, th, LabelSource.FRONTMATTER)
    assert "/en/purchase-request" in line
    assert "/th/purchase-request" in line
    assert "คำขอซื้อ" in line
    assert "[frontmatter]" in line
    assert line.startswith("  ✓")


def test_format_item_line_fallback_has_warning_marker():
    en = _item(target="/en/missing", label="Missing")
    th = _item(target="/th/missing", label="Missing")
    line = format_item_line(en, th, LabelSource.FALLBACK)
    assert line.startswith("  ⚠")
    assert "[fallback]" in line


def test_format_summary_one_line():
    counts = {
        "frontmatter": 29,
        "index.md": 6,
        "override": 4,
        "fallback": 3,
        "none": 0,
    }
    s = format_summary(42, counts)
    assert "42 items" in s
    assert "29 frontmatter" in s
    assert "6 index.md" in s
    assert "4 override" in s
    assert "3 fallback" in s


from scripts.sync_nav import run_sync


def test_run_sync_full_pipeline(tmp_path: Path):
    """Pure orchestration: given EN items + repo root, produce TH items + counts."""
    # repo layout
    (tmp_path / "th.md").write_text(
        "# Carmen Wiki TH\n\n## 1. Procure-to-Pay\n", encoding="utf-8"
    )
    (tmp_path / "en.md").write_text(
        "# Carmen Wiki EN\n\n## 1. Procure-to-Pay\n", encoding="utf-8"
    )
    _write_md(tmp_path / "th" / "pr.md", "คำขอซื้อ")
    overrides_path = tmp_path / "nav-overrides.yaml"
    overrides_path.write_text("headers: {}\nlinks: {}\n", encoding="utf-8")

    en_items = [
        _item(kind="header", label="Procure-to-Pay", target=""),
        _item(target="/en/pr", label="PR"),
    ]

    th_items, counts = run_sync(
        en_items=en_items,
        repo_root=tmp_path,
        overrides_path=overrides_path,
    )
    assert th_items[0]["label"] == "Procure-to-Pay"  # index.md exact-match self-pair
    assert th_items[1]["target"] == "/th/pr"
    assert th_items[1]["label"] == "คำขอซื้อ"
    assert counts["frontmatter"] == 1
    assert counts["index.md"] == 1


# ===== Build-mode tree builder tests =====


def test_build_tree_one_book_one_group_one_module():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
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
    assert items_en[1]["target"] == "/en/inventory"
    assert items_en[2]["label"] == "Costing & Reporting"
    assert items_en[2]["kind"] == "header"
    assert items_en[3]["target"] == "/en/inventory/costing"
    assert items_en[3]["label"] == "Costing"


def test_build_tree_two_books_inserts_divider_between():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
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
    assert items_th[1]["target"] == "/th/inventory"
    assert items_th[2]["label"] == "ต้นทุนและรายงาน"
    assert items_th[3]["target"] == "/th/inventory/costing"
    assert items_th[3]["label"] == "การคิดต้นทุน"


def test_build_tree_link_items_have_uuid_ids():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
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
                "groups": [],
            },
        },
    }
    items = build_tree_from_config(config, locale="en")
    kinds = [i["kind"] for i in items]
    assert kinds == ["header", "link"]
    assert items[0]["label"] == "Carmen Inventory"
    assert items[1]["target"] == "/en/inventory"


def test_build_tree_group_with_no_modules_still_emits_header():
    """A group with no `modules:` key (or empty list) still emits its header. Degenerate but valid."""
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
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
