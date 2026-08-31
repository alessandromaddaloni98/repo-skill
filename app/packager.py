"""Assembly of the downloadable package of an asset.

Folder-based: the asset already lives as a complete folder in data/assets/<slug>/
(skill.json + README.md + files/ + optional cover image). The package is the zip of
the reusable content — README + files/ — without internal metadata (skill.json) or
the cover image (catalog showcase only).
"""
from __future__ import annotations

import zipfile
from pathlib import Path

# Files/dirs to exclude from the zip.
_IGNORE_NAMES = {".DS_Store", "Thumbs.db"}
# Catalog-internal metadata, not part of the reusable package.
_META_NAMES = {"skill.json"}
# Image extensions: showcase material, excluded when at the root of the asset folder.
# (Inside files/ they stay: an asset can be an image itself.)
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}


def zip_asset_dir(
    asset_dir: Path,
    downloads_dir: Path,
    item_id: str,
    exclude_relpaths: set[str] | None = None,
) -> Path:
    """Zip the asset folder into downloads_dir/<item_id>.zip and return the path.

    Includes README.md and everything under files/. Excludes skill.json, the cover
    image (via `exclude_relpaths`) and system artifacts.
    """
    asset_dir = Path(asset_dir)
    downloads_dir = Path(downloads_dir)
    downloads_dir.mkdir(parents=True, exist_ok=True)
    zip_path = downloads_dir / f"{item_id}.zip"
    exclude_relpaths = exclude_relpaths or set()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(asset_dir.rglob("*")):
            if not p.is_file() or p.name in _IGNORE_NAMES or p.name in _META_NAMES:
                continue
            rel = p.relative_to(asset_dir).as_posix()
            if rel in exclude_relpaths:
                continue
            # Images at the folder root = catalog showcase, not part of the package.
            if p.parent == asset_dir and p.suffix.lower() in _IMAGE_EXTS:
                continue
            zf.write(p, rel)
    return zip_path
