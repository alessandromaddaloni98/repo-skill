"""Catalog blueprint: browsable home, filters, search, detail page."""
from flask import Blueprint, abort, current_app, render_template, request

from ..catalog_store import get_item, load_catalog, mark_seen, new_item_ids

bp = Blueprint("catalog", __name__)


def _items():
    return load_catalog(current_app.config["ASSETS_DIR"])


@bp.route("/catalog")
def home():
    items = _items()
    seen_file = current_app.config["SEEN_FILE"]
    new_ids = new_item_ids(items, seen_file)

    q = (request.args.get("q") or "").strip().lower()
    author_filter = request.args.get("author") or ""
    project_filter = request.args.get("project") or ""
    type_filter = request.args.get("type") or ""

    filtered = items
    if author_filter:
        filtered = [i for i in filtered if i.get("author") == author_filter]
    if project_filter:
        filtered = [i for i in filtered if i.get("project") == project_filter]
    if type_filter:
        filtered = [i for i in filtered if i.get("type") == type_filter]
    if q:
        filtered = [
            i for i in filtered
            if q in (i.get("name", "").lower() + " " + i.get("description", "").lower())
        ]

    all_authors = sorted({i.get("author") for i in items if i.get("author")})
    all_projects = sorted({i.get("project") for i in items if i.get("project")})
    all_types = sorted({i.get("type") for i in items if i.get("type")})
    # Search suggestions: name + description + type (custom dropdown, offline).
    suggest = [
        {"name": i.get("name", ""), "description": i.get("description", ""),
         "type": i.get("type", "")}
        for i in items if i.get("name")
    ]

    # Mark as seen after computing the "new" ones for this request.
    mark_seen(items, seen_file)

    return render_template(
        "catalog/home.html",
        items=filtered,
        new_ids=new_ids,
        all_authors=all_authors,
        all_projects=all_projects,
        all_types=all_types,
        suggest=suggest,
        q=q,
        author_filter=author_filter,
        project_filter=project_filter,
        type_filter=type_filter,
        total=len(items),
    )


@bp.route("/catalog/<item_id>")
def detail(item_id):
    item = get_item(current_app.config["ASSETS_DIR"], item_id)
    if not item:
        abort(404)
    return render_template("catalog/detail.html", item=item)
