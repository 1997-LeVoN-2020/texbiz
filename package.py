"""Build a versioned deploy archive pair for manual upload to ISPmanager --
see README.md "Деплой на хостинг".

Packages releases/texbiz-site-v<VERSION>.zip (dist/) and
releases/texbiz-pyapp-v<VERSION>.zip (src/pyapp/). The archive names are
just the VERSION file's contents -- bump VERSION before running this for
a new release. If VERSION wasn't bumped, this script refuses to overwrite
the existing archives for that version instead of silently clobbering
them; old releases under releases/ (gitignored, not committed) are never
overwritten or deleted, so they stay available for rollback.

Usage:
    python package.py
"""
import zipfile
from pathlib import Path

import build as site_build

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "releases"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def zip_dir(src, out):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in src.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            zf.write(path, path.relative_to(src))


def package():
    site_build.build()
    OUT_DIR.mkdir(exist_ok=True)

    site_zip = OUT_DIR / f"texbiz-site-v{VERSION}.zip"
    pyapp_zip = OUT_DIR / f"texbiz-pyapp-v{VERSION}.zip"

    if site_zip.exists() or pyapp_zip.exists():
        raise SystemExit(
            f"==> {site_zip.name} or {pyapp_zip.name} already exists -- refusing to overwrite.\n"
            "    Bump VERSION for a new release, or delete it yourself if this rebuild is intentional."
        )

    print(f"==> Building {site_zip.name} and {pyapp_zip.name}...")
    zip_dir(site_build.DIST, site_zip)
    zip_dir(ROOT / "src" / "pyapp", pyapp_zip)

    print(f"\nDone: {site_zip}, {pyapp_zip}")

    releases = sorted(OUT_DIR.glob("texbiz-site-v*.zip"), key=lambda p: p.stat().st_mtime)
    print(f"\n==> All site releases in {OUT_DIR}/ (oldest first):")
    for r in releases:
        print(f"    {r.name}")


if __name__ == "__main__":
    package()
