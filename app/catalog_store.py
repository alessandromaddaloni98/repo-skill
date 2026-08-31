"""Catalog access (local asset folders in data/assets/).

The single read point for the catalog: every subfolder of ASSETS_DIR holding a
valid `skill.json` is an item. Swap this module to move to a remote store / DB
later without touching the rest of the app.

Expected layout of every asset folder:

    data/assets/<slug>/
      skill.json     # metadata (name, description, type, author, project, files, created_at?)
      README.md      # guide (becomes the `body` field, rendered as markdown by the template)
      files/         # the actual asset files (copied into the downloadable package)

Normalized record exposed to the rest of the app:

    id, name, description, type, author, project,
    body (raw README.md), created_at,
    files: [{filename, relpath, size, role}]
    _dir: Path of the asset folder (internal use: packaging)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

# Files/dirs to ignore when listing the actual asset files.
_IGNORE_NAMES = {".DS_Store", "Thumbs.db"}


def _read_json(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _real_files(asset_dir: Path, skill: dict) -> list[dict]:
    """List ONLY the files actually present on disk under files/.

    skill.json entries with no matching file are ignored (ghost files). The role
    declared in skill.json, when present, is matched by relative path.
    """
    files_dir = asset_dir / "files"
    if not files_dir.is_dir():
        return []

    # Map relpath -> role, when skill.json provides per-file descriptions.
    declared_roles: dict[str, str] = {}
    for entry in skill.get("files") or []:
        if isinstance(entry, dict):
            rel = entry.get("path") or entry.get("relpath") or entry.get("filename")
            if rel:
                declared_roles[str(rel).lstrip("./")] = entry.get("role", "")

    out: list[dict] = []
    for p in sorted(files_dir.rglob("*")):
        if not p.is_file() or p.name in _IGNORE_NAMES:
            continue
        rel = p.relative_to(asset_dir).as_posix()  # e.g. files/models/best.pt
        rel_key = p.relative_to(files_dir).as_posix()  # e.g. models/best.pt
        out.append({
            "filename": p.name,
            "relpath": rel,
            "size": p.stat().st_size,
            "role": declared_roles.get(rel, "") or declared_roles.get(rel_key, ""),
        })
    return out


# Image extensions allowed for the cover image.
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def _cover_image(asset_dir: Path, skill: dict) -> str | None:
    """Relative path of the cover image declared in skill.json.

    Returns the relpath (POSIX, relative to the asset folder) when `image` is
    declared, points at a real file inside the folder and has an allowed image
    extension. Otherwise None → the template falls back to the per-type thumbnail.
    """
    rel = skill.get("image")
    if not rel or not isinstance(rel, str):
        return None
    rel = rel.lstrip("./")
    candidate = (asset_dir / rel).resolve()
    if (
        candidate.is_file()
        and asset_dir.resolve() in candidate.parents
        and candidate.suffix.lower() in _IMAGE_EXTS
    ):
        return candidate.relative_to(asset_dir.resolve()).as_posix()
    return None


def _build_record(asset_dir: Path) -> dict | None:
    """Build the normalized record of an asset folder, or None when invalid."""
    skill = _read_json(asset_dir / "skill.json")
    if skill is None or not skill.get("name"):
        return None

    readme = asset_dir / "README.md"
    body = readme.read_text(encoding="utf-8") if readme.is_file() else None

    created = skill.get("created_at")
    if not created:
        created = datetime.fromtimestamp(asset_dir.stat().st_mtime).isoformat(timespec="seconds")

    typ = skill.get("type", "code")
    if typ not in ("code", "model", "guide", "agent"):
        typ = "code"

    return {
        "id": asset_dir.name,
        "name": skill.get("name", ""),
        "description": skill.get("description", ""),
        "type": typ,
        "author": skill.get("author", ""),
        "project": skill.get("project", ""),
        "body": body,
        "created_at": created,
        "image": _cover_image(asset_dir, skill),
        "files": _real_files(asset_dir, skill),
        "_dir": str(asset_dir),
    }


def load_catalog(assets_dir: Path) -> list[dict]:
    """Return the list of items by scanning the asset folders in assets_dir.

    Skips folders without a valid `skill.json`. Empty catalog when the dir is
    missing. Sorted by created_at descending (newest first).
    """
    assets_dir = Path(assets_dir)
    if not assets_dir.is_dir():
        return []

    records: list[dict] = []
    for child in sorted(assets_dir.iterdir()):
        if not child.is_dir():
            continue
        rec = _build_record(child)
        if rec is not None:
            records.append(rec)

    records.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return records


def get_item(assets_dir: Path, item_id: str) -> dict | None:
    """Find an item by id (= asset folder name)."""
    asset_dir = Path(assets_dir) / item_id
    # Path traversal guard: the id must be a single segment.
    if "/" in item_id or "\\" in item_id or item_id in ("", ".", ".."):
        return None
    if not asset_dir.is_dir():
        return None
    return _build_record(asset_dir)


# --- New-item detection -------------------------------------------------------

def _load_seen(seen_file: Path) -> set[str]:
    try:
        with open(seen_file, encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def new_item_ids(items: list[dict], seen_file: Path) -> set[str]:
    """Ids present in the catalog but not yet recorded as seen."""
    seen = _load_seen(seen_file)
    return {it["id"] for it in items if it.get("id") and it["id"] not in seen}


def mark_seen(items: list[dict], seen_file: Path) -> None:
    """Record every current id as seen."""
    seen = _load_seen(seen_file)
    seen.update(it["id"] for it in items if it.get("id"))
    seen_file.parent.mkdir(parents=True, exist_ok=True)
    with open(seen_file, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, indent=2)
