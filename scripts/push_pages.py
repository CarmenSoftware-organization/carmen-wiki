#!/usr/bin/env python3
"""Push given wiki .md files into the Wiki.js DB via GraphQL pages.update/create.

Bypasses git storage (used when the server's git pull is wedged). Reads
WIKI_API_URL / WIKI_API_TOKEN from scripts/.env. Maps each file
<locale>/inventory/<rest>.md -> (locale, path="inventory/<rest>") and
updates the matching page's content/title/description/tags from its
frontmatter — or creates the page if no existing id is found for that
locale+path.

Usage: python3 scripts/push_pages.py <file.md> [<file.md> ...] [--limit N]
       python3 scripts/push_pages.py --delete <locale>/<path> [...]

In --delete mode the arguments are wiki paths, not files: the pages are
gone from git, so there is nothing on disk left to read. Each argument is
split the same way as a file path (leading <locale>/, no .md suffix) and
the matching page is removed from the Wiki.js DB. A path with no page in
the index is reported as MISSING and is not an error.
"""
import json, os, sys, re, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "scripts", ".env")
for line in open(ENV):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); os.environ.setdefault(k, v)
URL = os.environ["WIKI_API_URL"]; TOKEN = os.environ["WIKI_API_TOKEN"]


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def page_index():
    q = "{ pages { list(orderBy: PATH) { id locale path } } }"
    out = {}
    for p in gql(q)["data"]["pages"]["list"]:
        out[(p["locale"], p["path"])] = p["id"]
    return out


def parse(md):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", md, re.S)
    if not m:
        return {}, md
    fm, body = m.group(1), m.group(2)
    meta = {}
    for line in fm.splitlines():
        mm = re.match(r"^(\w+):\s*(.*)$", line)
        if mm:
            meta[mm.group(1)] = mm.group(2).strip()
    return meta, body.lstrip("\n")


UPDATE = """mutation($id:Int!,$content:String!,$description:String!,$editor:String!,
$isPrivate:Boolean!,$isPublished:Boolean!,$locale:String!,$path:String!,$tags:[String]!,$title:String!){
 pages{ update(id:$id,content:$content,description:$description,editor:$editor,isPrivate:$isPrivate,
 isPublished:$isPublished,locale:$locale,path:$path,publishEndDate:"",publishStartDate:"",
 scriptCss:"",scriptJs:"",tags:$tags,title:$title){ responseResult{succeeded errorCode message} } } }"""

CREATE = """mutation($content:String!,$description:String!,$editor:String!,
$isPrivate:Boolean!,$isPublished:Boolean!,$locale:String!,$path:String!,$tags:[String]!,$title:String!){
 pages{ create(content:$content,description:$description,editor:$editor,isPrivate:$isPrivate,
 isPublished:$isPublished,locale:$locale,path:$path,tags:$tags,title:$title){
 responseResult{succeeded errorCode message} page{id} } } }"""

DELETE = """mutation($id:Int!){ pages{ delete(id:$id){
 responseResult{succeeded errorCode message} } } }"""


def apply_page(gql_fn, pid, page_vars):
    """Create or update one page via GraphQL, chosen by whether `pid` is known.

    `page_vars` holds every field common to both mutations (content,
    description, editor, isPrivate, isPublished, locale, path, tags, title —
    no `id`). Returns (succeeded, response_result_or_None, page_id_or_None):
    on a successful create, page_id is the newly assigned id; on update it is
    the given `pid` unchanged.
    """
    if pid is None:
        res = gql_fn(CREATE, page_vars)
        payload = (((res.get("data") or {}).get("pages") or {}).get("create") or {})
        rr = payload.get("responseResult")
        new_id = (payload.get("page") or {}).get("id")
        return bool(rr and rr["succeeded"]), rr, new_id
    res = gql_fn(UPDATE, {**page_vars, "id": pid})
    rr = (((res.get("data") or {}).get("pages") or {}).get("update") or {}).get("responseResult")
    return bool(rr and rr["succeeded"]), rr, pid


def delete_page(gql_fn, pid):
    """Remove one page from the Wiki.js DB by id.

    Returns (succeeded, response_result_or_None).
    """
    res = gql_fn(DELETE, {"id": pid})
    rr = (((res.get("data") or {}).get("pages") or {}).get("delete") or {}).get("responseResult")
    return bool(rr and rr["succeeded"]), rr


def wiki_path(arg):
    """Split one argument into (locale, path) the way the Wiki.js index keys it."""
    rel = arg.replace("\\", "/")
    locale = rel.split("/")[0]
    path = re.sub(r"^[a-z]{2}/", "", rel)
    if path.endswith(".md"):
        path = path[:-3]
    return locale, path


def delete_main(args):
    idx = page_index()
    deleted = missing = fail = 0
    for a in args:
        locale, path = wiki_path(a)
        pid = idx.get((locale, path))
        if pid is None:
            print(f"MISS  {locale}:{path} (no such page)"); missing += 1
            continue
        ok, rr = delete_page(gql, pid)
        if not ok and (locale, path) not in page_index():
            # Wiki.js removes the DB row first, then syncs its storage targets.
            # A git-storage failure (e.g. the file is already absent from the
            # server's working copy) surfaces as an error even though the page
            # is gone, so re-read the index before believing the failure.
            print(f"DEL   {locale}:{path} (id {pid}) [storage warning: {rr}]"); deleted += 1
        elif ok:
            print(f"DEL   {locale}:{path} (id {pid})"); deleted += 1
        else:
            print(f"FAIL  {locale}:{path} (delete) -> {rr}"); fail += 1
    print(f"---- deleted {deleted}, missing {missing}, failed {fail} ----")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--delete" in sys.argv[1:]:
        return delete_main(args)
    limit = next((int(sys.argv[i + 1]) for i, a in enumerate(sys.argv) if a == "--limit"), None)
    if limit:
        args = args[:limit]
    idx = page_index()
    created = updated = fail = 0
    for f in args:
        rel = f.replace("\\", "/")
        locale = rel.split("/")[0]
        path = re.sub(r"^[a-z]{2}/", "", rel)[:-3]  # drop <locale>/ and .md
        pid = idx.get((locale, path))
        meta, body = parse(open(os.path.join(ROOT, f)).read())
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        page_vars = {"content": body, "description": meta.get("description", ""),
                     "editor": "markdown", "isPrivate": False,
                     "isPublished": str(meta.get("published", "true")).lower() != "false",
                     "locale": locale, "path": path, "tags": tags, "title": meta.get("title", path)}
        ok, rr, result_id = apply_page(gql, pid, page_vars)
        if ok and pid is None:
            print(f"CREATE {locale}:{path} (id {result_id})"); created += 1
        elif ok:
            print(f"OK    {locale}:{path} (id {result_id})"); updated += 1
        else:
            verb = "create" if pid is None else "update"
            print(f"FAIL  {locale}:{path} ({verb}) -> {rr}"); fail += 1
    print(f"---- created {created}, updated {updated}, failed {fail} ----")


if __name__ == "__main__":
    main()
