"""Acquire pinned administrative artefacts into ignored local storage."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

from tools.baseline.check import ROOT


def store_verified(stream, destination: Path, *, size: int, digest: str) -> None:
    """Replace only after bounded streaming and exact verification."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            received = 0
            hasher = hashlib.sha256()
            while block := stream.read(1024 * 1024):
                received += len(block)
                if received > size:
                    raise ValueError("Download exceeds pinned size")
                output.write(block)
                hasher.update(block)
            if received != size or hasher.hexdigest() != digest:
                raise ValueError("Download does not match pinned size and SHA-256")
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    pins = json.loads((ROOT / "docs/qualification/tool-pins.json").read_text())["artifacts"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", choices=[p["id"] for p in pins])
    args = parser.parse_args()
    pin = next(p for p in pins if p["id"] == args.artifact)
    if Path(pin["filename"]).name != pin["filename"] or not pin["url"].startswith("https://"):
        parser.error("Unsafe administrative acquisition pin")
    destination = ROOT / ".local/downloads" / pin["filename"]
    if destination.is_file() and destination.stat().st_size == pin["size_bytes"] and hashlib.sha256(destination.read_bytes()).hexdigest() == pin["sha256"]:
        print(f"Already present and verified: {pin['id']}")
        return 0
    request = urllib.request.Request(pin["url"], headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=30) as response:
        store_verified(response, destination, size=pin["size_bytes"], digest=pin["sha256"])
    print(f"Acquired and verified: {pin['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
