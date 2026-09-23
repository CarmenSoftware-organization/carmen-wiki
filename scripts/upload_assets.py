#!/usr/bin/env python3
"""Upload screenshot PNGs into the Wiki.js Asset Manager, creating folders as needed.

Usage: python3 scripts/upload_assets.py assets/screenshots/<book>/<module>/<file>.png ...

Folder layout (spec 2026-09-23 §2.1):
  inventory -> screenshots/<module>/            URL /screenshots/<module>/<file>
  platform  -> screenshots/platform/<module>/   URL /screenshots/platform/<module>/<file>
Reads WIKI_API_URL / WIKI_API_TOKEN from scripts/.env.
"""
import hashlib, json, os, subprocess, sys, urllib.request
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


def post_upload(png: Path, folder_id: int) -> str:
    """POST the file to /u; returns the HTTP status. The token goes through curl's
    stdin config (-K -) so it never appears in the process list."""
    config = f'header = "Authorization: Bearer {TOKEN}"\n'
    return subprocess.run(
        ["curl", "-sS", "-K", "-", "-o", "/dev/null", "-w", "%{http_code}", "-m", "60",
         "-X", "POST", f"{BASE}/u",
         "-F", f'mediaUpload={{"folderId":{folder_id}}};type=application/json',
         "-F", f"mediaUpload=@{png};type=image/png"],
        input=config, capture_output=True, text=True).stdout


def served_sha256(url: str) -> tuple[int, str]:
    """Status and SHA-256 of what the wiki serves now (cache-busted)."""
    try:
        with urllib.request.urlopen(f"{BASE}{url}?v={os.getpid()}", timeout=30) as r:
            return r.status, hashlib.sha256(r.read()).hexdigest()
    except urllib.error.HTTPError as e:
        return e.code, ""


def upload(png: Path) -> tuple[bool, str]:
    rel = png.resolve().relative_to(ROOT / "assets" / "screenshots")
    book, module = rel.parts[0], rel.parts[1]
    folder = ["screenshots", module] if book == "inventory" else ["screenshots", book, module]
    url = "/" + "/".join(folder + [png.name])
    up = post_upload(png, folder_for(folder))
    status, served = served_sha256(url)
    # A 200 alone also matches a stale asset Wiki.js kept instead of replacing.
    same = served == hashlib.sha256(png.read_bytes()).hexdigest()
    ok = up == "200" and status == 200 and same
    return ok, f"{url} (upload {up}, get {status}, {'content matches' if same else 'CONTENT DIFFERS'})"


def main(argv: list[str]) -> int:
    ok = fail = 0
    for arg in argv:
        p = Path(arg)
        if not p.is_file():
            print(f"SKIP (missing) {arg}")
            continue
        try:
            good, msg = upload(p)
        except (ValueError, IndexError, RuntimeError, OSError) as e:
            # One bad path (e.g. outside assets/screenshots/<book>/<module>/) must not abort the batch.
            good, msg = False, f"{arg} ({type(e).__name__}: {e})"
        print(("OK   " if good else "FAIL ") + msg)
        ok, fail = ok + good, fail + (not good)
    print(f"---- uploaded {ok}, failed {fail} ----")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
