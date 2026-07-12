#!/bin/bash
# Build a versioned deploy archive (texbiz-deploy-vX.Y.Z.zip) for manual
# upload to ISPmanager -- see README.md "Деплой на хостинг".
#
# Packages exactly what's committed at HEAD (via `git archive`), so it
# automatically stays in sync with .gitignore -- no hand-maintained exclude
# list to fall out of date (.claude/ is excluded separately via
# .gitattributes export-ignore). Uncommitted changes are NOT included;
# commit first if you need them in the release.
#
# The archive name is just the VERSION file's contents -- bump VERSION and
# commit before running this for a new release. If VERSION wasn't bumped,
# the script refuses to overwrite the existing archive for that version
# instead of silently clobbering it; old releases under releases/ (gitignored,
# not committed) are never overwritten or deleted, so they stay available
# for rollback.
#
# Usage:
#   bash build_release.sh

set -e

cd "$(dirname "$0")"

if [ -n "$(git status --porcelain)" ]; then
    echo "==> Warning: working tree has uncommitted changes."
    echo "    build_release.sh packages 'git archive HEAD' -- uncommitted"
    echo "    changes will NOT be in the release archive."
    echo ""
fi

VERSION=$(cat VERSION | tr -d '[:space:]')
OUT_DIR="releases"
OUT_FILE="$OUT_DIR/texbiz-deploy-v${VERSION}.zip"

mkdir -p "$OUT_DIR"

if [ -e "$OUT_FILE" ]; then
    echo "==> $OUT_FILE already exists -- refusing to overwrite."
    echo "    Bump VERSION (and commit) for a new release, or delete it yourself if this rebuild is intentional."
    exit 1
fi

echo "==> Building $OUT_FILE from committed HEAD ($(git rev-parse --short HEAD))..."
git archive --format=zip -o "$OUT_FILE" HEAD

echo ""
echo "Done: $OUT_FILE"
echo ""
echo "==> All releases in $OUT_DIR/ (oldest first):"
ls -1t "$OUT_DIR" | tac
