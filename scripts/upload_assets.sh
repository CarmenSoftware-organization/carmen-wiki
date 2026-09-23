#!/usr/bin/env bash
# Kept for muscle memory; the folder-resolving uploader lives in upload_assets.py.
# Usage: scripts/upload_assets.sh assets/screenshots/<book>/<module>/<file>.png...
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/upload_assets.py "$@"
