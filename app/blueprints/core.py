"""Core blueprint: home and health check."""
from flask import Blueprint, jsonify, redirect, url_for

bp = Blueprint("core", __name__)


@bp.route("/")
def index():
    # The home page is the catalog.
    return redirect(url_for("catalog.home"))


@bp.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})
