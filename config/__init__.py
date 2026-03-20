"""
Config Loader – lädt settings.yaml und .env
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Projektroot = zwei Ebenen über config/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# .env laden (falls vorhanden)
load_dotenv(PROJECT_ROOT / ".env")


def load_settings() -> dict:
    """Lädt config/settings.yaml und gibt das Dict zurück."""
    settings_path = PROJECT_ROOT / "config" / "settings.yaml"

    if not settings_path.exists():
        raise FileNotFoundError(f"settings.yaml nicht gefunden: {settings_path}")

    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_credentials_path() -> Path:
    """Gibt den Pfad zur Google OAuth2 credentials.json zurück."""
    cred_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    resolved = PROJECT_ROOT / cred_path

    if not resolved.exists():
        raise FileNotFoundError(
            f"Google credentials nicht gefunden: {resolved}\n"
            f"→ Lade sie aus der Google Cloud Console herunter und lege sie als '{cred_path}' ab."
        )

    return resolved
