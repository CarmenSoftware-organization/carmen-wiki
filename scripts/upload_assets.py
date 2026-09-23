#!/usr/bin/env python3
"""Upload screenshot PNGs into the Wiki.js Asset Manager, creating folders as needed.

Usage: python3 scripts/upload_assets.py assets/screenshots/<book>/<module>/<file>.png ...

Folder layout (spec 2026-09-23 §2.1):
  inventory -> screenshots/<module>/            URL /screenshots/<module>/<file>
  platform  -> screenshots/platform/<module>/   URL /screenshots/platform/<module>/<file>
Reads WIKI_API_URL / WIKI_API_TOKEN from scripts/.env.
"""
import json, os, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for line in (ROOT / "scripts" / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)
API = os.environ["WIKI_API_URL"]
TOKEN = os.environ["WIKI_API_TOKEN"]
BASE = os.environ.get("WIKI_BASE", API.rsplit("/graphql", 1)[0])


def gql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.load(r)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def children(parent_id: int) -> dict[str, int]:
    q = "query($p:Int!){assets{folders(parentFolderId:$p){id slug}}}"
    return {f["slug"]: f["id"] for f in gql(q, {"p": parent_id})["assets"]["folders"]}


def ensure_folder(parent_id: int, slug: str) -> int:
    existing = children(parent_id)
    if slug in existing:
        return existing[slug]
    m = ("mutation($p:Int!,$s:String!){assets{createFolder(parentFolderId:$p,slug:$s,name:$s)"
         "{responseResult{succeeded message}}}}")
    res = gql(m, {"p": parent_id, "s": slug})["assets"]["createFolder"]["responseResult"]
    if not res["succeeded"]:
        raise RuntimeError(f"createFolder {slug}: {res['message']}")
    return children(parent_id)[slug]


_cache: dict[tuple[int, str], int] = {}


def folder_for(parts: list[str]) -> int:
    fid = 0  # Asset Manager root
    for slug in parts:
        key = (fid, slug)
        if key not in _cache:
            _cache[key] = ensure_folder(fid, slug)
        fid = _cache[key]
    return fid


def curl_code(args: list[str]) -> str:
    return subprocess.run(["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", *args],
                          capture_output=True, text=True).stdout


def upload(png: Path) -> tuple[bool, str]:
    rel = png.resolve().relative_to(ROOT / "assets" / "screenshots")
    book, module = rel.parts[0], rel.parts[1]
    folder = ["screenshots", module] if book == "inventory" else ["screenshots", book, module]
    fid = folder_for(folder)
    url = "/" + "/".join(folder + [png.name])
    up = curl_code(["-m", "60", "-X", "POST", f"{BASE}/u",
                    "-H", f"Authorization: Bearer {TOKEN}",
                    "-F", f'mediaUpload={{"folderId":{fid}}};type=application/json',
                    "-F", f"mediaUpload=@{png};type=image/png"])
    get = curl_code(["-m", "20", f"{BASE}{url}"])
    return (up == "200" and get == "200", f"{url} (upload {up}, get {get})")


def main(argv: list[str]) -> int:
    ok = fail = 0
    for arg in argv:
        p = Path(arg)
        if not p.is_file():
            print(f"SKIP (missing) {arg}")
            continue
        good, msg = upload(p)
        print(("OK   " if good else "FAIL ") + msg)
        ok, fail = ok + good, fail + (not good)
    print(f"---- uploaded {ok}, failed {fail} ----")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
