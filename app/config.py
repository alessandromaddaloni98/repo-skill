"""Application configuration, loaded from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present (project root).
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")

    # Data paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    ASSETS_DIR = DATA_DIR / "assets"          # asset folders (source of the catalog)
    CATALOG_DIR = DATA_DIR / "catalog"
    SEEN_FILE = CATALOG_DIR / "seen.json"     # ids already seen (NEW badge)
    DOWNLOADS_DIR = BASE_DIR / "downloads"
    # Downloadable capture skill, one folder per agent format.
    # label   = name of the subfolder inside the zip (visible, not hidden)
    # src     = folder in this repo
    # dest    = path where the user has to copy it inside their own project
    SKILL_VARIANTS = [
        {
            "label": "codex",
            "agent": "Codex",
            "src": BASE_DIR / ".agents" / "repo-skill-publish",
            "dest": ".agents/repo-skill-publish/",
        },
        {
            "label": "claude-code",
            "agent": "Claude Code",
            "src": BASE_DIR / ".claude" / "skills" / "repo-skill-publish",
            "dest": ".claude/skills/repo-skill-publish/",
        },
    ]


class DevConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True


class ProdConfig(BaseConfig):
    DEBUG = False


_CONFIGS = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}


def get_config(name: str | None = None) -> type[BaseConfig]:
    name = (name or os.environ.get("FLASK_ENV", "dev")).lower()
    return _CONFIGS.get(name, DevConfig)
