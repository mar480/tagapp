"""Disposable browser-test state; never points at the developer's projects."""
import os
from pathlib import Path
from .test_settings import *  # noqa: F403

base = Path(os.environ['TAGGER_E2E_ROOT'])
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': base / 'test.sqlite3'}}
BLOB_ROOT = base / 'blobs'
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:4173']
