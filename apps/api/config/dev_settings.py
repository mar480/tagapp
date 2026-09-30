"""Loopback-only development; explicitly separate from deployment settings."""
import os
import secrets
from pathlib import Path

base = Path(__file__).resolve().parents[3] / ".local/foundation"
base.mkdir(parents=True, exist_ok=True, mode=0o700)
key = base / "development-secret"
if not key.exists():
    try:
        fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "w") as stream:
            stream.write(secrets.token_urlsafe(48))
os.environ.setdefault("TAGGER_SECRET_KEY", key.read_text())
from .settings import *  # noqa: E402,F403

DEBUG = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:4173"]
if os.environ.get("TAGGER_DEV_SQLITE") == "1":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": base / "development.sqlite3"}}
