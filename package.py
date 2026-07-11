"""Packages the built site and pyapp into versioned zip archives under builds/.

Reads the version from VERSION and refuses to overwrite an archive that
already exists for that version — bump VERSION before packaging again.
Older versioned archives in builds/ are never deleted.

Usage: python package.py
"""
import zipfile
from pathlib import Path

import build as site_build

ROOT = Path(__file__).parent
BUILDS = ROOT / "builds"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def zip_dir(src, out):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in src.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            zf.write(path, path.relative_to(src))


def package():
    site_build.build()
    BUILDS.mkdir(exist_ok=True)

    site_zip = BUILDS / f"texbiz-site-{VERSION}.zip"
    pyapp_zip = BUILDS / f"texbiz-pyapp-{VERSION}.zip"

    if site_zip.exists() or pyapp_zip.exists():
        raise SystemExit(
            f"builds/texbiz-site-{VERSION}.zip or texbiz-pyapp-{VERSION}.zip already exists. "
            "Bump VERSION before packaging a new build -- old versioned archives are never overwritten."
        )

    zip_dir(site_build.DIST, site_zip)
    zip_dir(ROOT / "src" / "pyapp", pyapp_zip)

    print(f"Packaged version {VERSION}:")
    print(f"  {site_zip}")
    print(f"  {pyapp_zip}")


if __name__ == "__main__":
    package()
