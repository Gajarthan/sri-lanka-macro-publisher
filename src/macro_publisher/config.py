"""Project-wide configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Static project settings used across the pipeline."""

    app_name: str = "sri-lanka-macro-publisher"
    user_agent: str = (
        "sri-lanka-macro-publisher/0.1.0 (+https://github.com/your-org/sri-lanka-macro-publisher)"
    )
    http_timeout_seconds: float = 30.0
    history_lookback_days: int = 14
    doa_supported_items: tuple[str, ...] = (
        "Beans",
        "Carrot",
        "Cabbage",
        "Tomato",
        "Brinjal",
        "Snake Gourd",
        "Pumpkin",
        "Green Chilli",
        "Lime",
    )


SETTINGS = Settings()

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
DATA_DIR = REPO_ROOT / "data"
LATEST_DIR = DATA_DIR / "latest"
HISTORY_DIR = DATA_DIR / "history"
NORMALIZED_DIR = DATA_DIR / "normalized"
STATUS_PATH = DATA_DIR / "status.json"
PIPELINE_HISTORY_PATH = DATA_DIR / "pipeline_history.csv"
DOCS_DIR = REPO_ROOT / "docs"
README_ASSETS_DIR = DOCS_DIR / "readme-assets"
