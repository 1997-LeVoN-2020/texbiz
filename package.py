"""Build a versioned deploy archive for manual upload to ISPmanager --
see README.md "Деплой на хостинг".

Packages releases/texbiz-deploy-v<VERSION>.zip with the exact layout the
domain root needs: dist/ and src/pyapp/ contents both flattened into the
archive root -- unzip the whole thing directly into the domain root and
both the static site and the Python app land where ISPmanager expects
them, in one step (this hosting plan runs the Python app straight out of
the domain root, no separate subfolder -- see README "2. Python-приложение
для формы").

The archive name is just the VERSION file's contents -- bump VERSION
before running this for a new release. If VERSION wasn't bumped, this
script refuses to overwrite the existing archive for that version instead
of silently clobbering it; old releases under releases/ (gitignored, not
committed) are never overwritten or deleted, so they stay available for
rollback.

Usage:
    python package.py
"""
import zipfile
from pathlib import Path

import build as site_build

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "releases"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def package():
    site_build.build()
    OUT_DIR.mkdir(exist_ok=True)

    out_zip = OUT_DIR / f"texbiz-deploy-v{VERSION}.zip"

    if out_zip.exists():
        raise SystemExit(
            f"==> {out_zip.name} already exists -- refusing to overwrite.\n"
            "    Bump VERSION for a new release, or delete it yourself if this rebuild is intentional."
        )

    print(f"==> Building {out_zip.name}...")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in site_build.DIST.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(site_build.DIST))

        pyapp_dir = ROOT / "src" / "pyapp"
        for path in pyapp_dir.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            zf.write(path, path.relative_to(pyapp_dir))

    print(f"\nDone: {out_zip}")

    releases = sorted(OUT_DIR.glob("texbiz-deploy-v*.zip"), key=lambda p: p.stat().st_mtime)
    print(f"\n==> All releases in {OUT_DIR}/ (oldest first):")
    for r in releases:
        print(f"    {r.name}")


if __name__ == "__main__":
    package()
