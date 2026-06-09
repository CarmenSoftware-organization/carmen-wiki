#!/usr/bin/env bash
# Upload screenshot PNGs to the Wiki.js Asset Manager under screenshots/<module>/.
# Reads WIKI_API_TOKEN from scripts/.env. Folder id is derived from the file's
# parent dir (the wiki module). Usage: scripts/upload_assets.sh <file.png>...
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source scripts/.env; set +a
BASE="${WIKI_BASE:-http://dev.blueledgers.com:3987}"

folder_id() { case "$1" in
  purchase-request) echo 8;; dashboard) echo 9;; good-receive-note) echo 10;;
  inventory) echo 11;; inventory-adjustment) echo 12;; master-data) echo 13;;
  physical-count) echo 14;; product) echo 15;; purchase-order) echo 16;;
  recipe) echo 17;; reporting-audit) echo 18;; spot-check) echo 19;;
  store-requisition) echo 20;; templates) echo 21;; vendor-pricelist) echo 22;;
  access-control) echo 23;; system-config) echo 24;; *) echo "";; esac; }

ok=0; fail=0
for f in "$@"; do
  [ -f "$f" ] || { echo "SKIP (missing): $f"; continue; }
  mod="$(basename "$(dirname "$f")")"; fid="$(folder_id "$mod")"
  if [ -z "$fid" ]; then echo "SKIP (no folder id for '$mod'): $f"; fail=$((fail+1)); continue; fi
  code="$(curl -sS -m 30 -X POST "$BASE/u" \
    -H "Authorization: Bearer $WIKI_API_TOKEN" \
    -F "mediaUpload={\"folderId\":$fid};type=application/json" \
    -F "mediaUpload=@$f;type=image/png" \
    -o /tmp/up.out -w "%{http_code}")"
  url="/screenshots/$mod/$(basename "$f")"
  get="$(curl -sS -m 15 -o /dev/null -w "%{http_code}" "$BASE$url")"
  if [ "$code" = 200 ] && [ "$get" = 200 ]; then echo "OK   $url"; ok=$((ok+1));
  else echo "FAIL ($code/$get) $url : $(cat /tmp/up.out)"; fail=$((fail+1)); fi
done
echo "---- uploaded $ok, failed $fail ----"
