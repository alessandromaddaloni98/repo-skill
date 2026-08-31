"""Flask app factory for repo-skill."""
from flask import Flask, render_template
from markupsafe import Markup

from .config import get_config


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    config = get_config(config_name)
    app.config.from_object(config)

    # Make sure the data directories exist.
    for d in (config.ASSETS_DIR, config.CATALOG_DIR, config.DOWNLOADS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    _register_filters(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    return app


def _register_filters(app: Flask) -> None:
    import markdown as _md

    def render_markdown(text: str | None) -> Markup:
        if not text:
            return Markup("")
        html = _md.markdown(
            text,
            extensions=["fenced_code", "tables", "toc"],
            output_format="html5",
        )
        return Markup(html)

    app.jinja_env.filters["markdown"] = render_markdown


def _register_blueprints(app: Flask) -> None:
    from .blueprints.core import bp as core_bp
    from .blueprints.catalog import bp as catalog_bp
    from .blueprints.download import bp as download_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(download_bp)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500
