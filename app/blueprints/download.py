"""Download blueprint: zips and serves the complete asset folder."""
import zipfile
from pathlib import Path

from flask import Blueprint, abort, current_app, send_file

from ..catalog_store import get_item
from ..packager import zip_asset_dir

bp = Blueprint("download", __name__)


SKILL_ROOT = "repo-skill-publish"


def _install_notes(variants) -> str:
    """Instructions bundled in the zip: the destination folders are hidden."""
    lines = [
        "repo-skill - capture skill",
        "=" * 30,
        "",
        "This folder holds the same skill in several formats, one per agent.",
        "Copy ONLY the one for the agent you use (or both) into the project you",
        "want to extract the asset from:",
        "",
    ]
    width = max(len(v["label"]) for v in variants) + 1
    for v in variants:
        lines.append(f"  {v['label'] + '/':<{width}}  ->  {v['dest']}   ({v['agent']})")
    lines += [
        "",
        "The destination folders start with a dot: on macOS and Linux they are",
        "hidden. In Finder you can show them with Cmd + Shift + . (period).",
        "If they do not exist, create them.",
        "",
        "Then ask your agent, from the project that contains the asset:",
        "",
        '  use the repo-skill-publish skill to prepare and publish',
        '  the asset "<asset name>", contained in the files <file_name>',
        "",
    ]
    return "\n".join(lines)


@bp.route("/download-skill")
def skill():
    """Download the capture skill in every supported agent format."""
    variants = [v for v in current_app.config["SKILL_VARIANTS"]
                if Path(v["src"]).is_dir()]
    if not variants:
        abort(404)

    downloads_dir = Path(current_app.config["DOWNLOADS_DIR"])
    downloads_dir.mkdir(parents=True, exist_ok=True)
    zip_path = downloads_dir / f"{SKILL_ROOT}.zip"

    # Root folder with a visible name: the destination paths (.agents/, .claude/)
    # are hidden, so zipping them directly would make the extracted archive look
    # empty. README.txt says where to copy them.
    root = Path(SKILL_ROOT)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(str(root / "README.txt"), _install_notes(variants))
        for v in variants:
            src = Path(v["src"])
            for p in sorted(src.rglob("*")):
                if p.is_file() and p.name not in (".DS_Store", "Thumbs.db"):
                    zf.write(p, root / v["label"] / p.relative_to(src))

    return send_file(zip_path, as_attachment=True,
                     download_name=f"{SKILL_ROOT}.zip")


@bp.route("/download/<item_id>")
def package(item_id):
    item = get_item(current_app.config["ASSETS_DIR"], item_id)
    if not item:
        abort(404)

    asset_dir = Path(item["_dir"])
    # Exclude the cover image: catalog showcase only, not part of the package.
    exclude = {item["image"]} if item.get("image") else set()
    zip_path = zip_asset_dir(
        asset_dir, current_app.config["DOWNLOADS_DIR"], item_id, exclude_relpaths=exclude
    )
    return send_file(zip_path, as_attachment=True, download_name=f"{item_id}.zip")


@bp.route("/asset-image/<item_id>")
def asset_image(item_id):
    """Serve the asset cover image (inline, not as a download)."""
    item = get_item(current_app.config["ASSETS_DIR"], item_id)
    if not item or not item.get("image"):
        abort(404)

    img_path = (Path(item["_dir"]) / item["image"]).resolve()
    if not img_path.is_file() or Path(item["_dir"]).resolve() not in img_path.parents:
        abort(404)

    return send_file(img_path)


@bp.route("/download/<item_id>/file/<path:relpath>")
def single_file(item_id, relpath):
    """Download a single file included in the asset."""
    item = get_item(current_app.config["ASSETS_DIR"], item_id)
    if not item:
        abort(404)

    # Only serves files declared in the record (already filtered as real on disk):
    # prevents path traversal and downloads of unlisted files.
    match = next((f for f in item.get("files") or [] if f["relpath"] == relpath), None)
    if not match:
        abort(404)

    file_path = (Path(item["_dir"]) / relpath).resolve()
    # Defense in depth: the resolved path must stay inside the asset folder.
    if not file_path.is_file() or Path(item["_dir"]).resolve() not in file_path.parents:
        abort(404)

    return send_file(file_path, as_attachment=True, download_name=match["filename"])
