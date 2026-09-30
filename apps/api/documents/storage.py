"""Private blob boundary: storage keys are generated internally, never client paths."""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
from typing import BinaryIO, Protocol
import uuid
from django.conf import settings

@dataclass(frozen=True)
class StoredBlob:
    key: str
    sha256: str
    size_bytes: int

class BlobStore(Protocol):
    def put(self, source: BinaryIO) -> StoredBlob: ...
    def open(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...

class FileSystemBlobStore:
    def __init__(self, root=None):
        self.root = Path(root or settings.BLOB_ROOT).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
    def path(self, key):
        if not re.fullmatch(r"[0-9a-f]{32}", key):
            raise ValueError("Invalid internal storage key")
        return self.root / key
    def put(self, source):
        key = uuid.uuid4().hex
        path = self.path(key)
        digest = hashlib.sha256(); size = 0; created = False
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            created = True
            with os.fdopen(fd, "wb") as target:
                while block := source.read(1024 * 1024):
                    size += len(block)
                    if size > settings.MAX_DOCUMENT_BYTES:
                        raise ValueError("Document exceeds the upload limit")
                    digest.update(block); target.write(block)
                target.flush(); os.fsync(target.fileno())
            return StoredBlob(key, digest.hexdigest(), size)
        except BaseException:
            if created:
                path.unlink(missing_ok=True)
            raise
    def open(self, key):
        return os.fdopen(os.open(self.path(key), os.O_RDONLY | os.O_NOFOLLOW), "rb")
    def delete(self, key):
        self.path(key).unlink(missing_ok=True)

def blob_store() -> BlobStore:
    return FileSystemBlobStore()
