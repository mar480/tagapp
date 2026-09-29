"""Inspect the Git index (default) or public worktree without printing values.

This is a conservative publication guard, not a comprehensive secret/PII scanner.
Run before staging AND against the staged index before committing. It does not
install hooks or change Git configuration.
"""
from __future__ import annotations

import argparse
import json
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath

MAX_BYTES = 2_000_000
PRIVATE_ROOTS = {"materials", "tagapp-materials", ".local", "runtime", "storage", "backups"}
PRIVATE_PARTS = {"node_modules", ".venv", "venv", "__pycache__", ".git"}
PRIVATE_SUFFIXES = {".bundle", ".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".pfx", ".gguf", ".safetensors"}
PATTERNS = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "aws-access-key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "jwt-review-required": re.compile(rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
}


def path_findings(name: str) -> list[str]:
    p = PurePosixPath(name)
    findings = []
    if p.is_absolute() or ".." in p.parts:
        findings.append("unsafe-path")
    if (p.parts and p.parts[0] in PRIVATE_ROOTS) or any(
        part in PRIVATE_PARTS or part.endswith(".git") for part in p.parts
    ):
        findings.append("private-or-dependency-directory")
    if p.suffix.lower() in PRIVATE_SUFFIXES or p.name.endswith((".db-journal", ".db-wal", ".db-shm")):
        findings.append("private-artifact")
    if (p.name == ".env" or p.name.startswith(".env.")) and p.name != ".env.example":
        findings.append("environment-secrets-file")
    return findings


def content_findings(data: bytes) -> list[str]:
    if len(data) > MAX_BYTES:
        return ["oversized-needs-review"]
    if b"\0" in data:
        return ["binary-needs-review"]
    return [category for category, pattern in PATTERNS.items() if pattern.search(data)]


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def scan(root: Path, *, worktree: bool = False) -> list[dict[str, str]]:
    results = []
    if worktree:
        entries = [(p, None, None) for p in git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0") if p]
    else:
        entries = []
        for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
            if entry:
                meta, name = entry.split(b"\t", 1)
                mode, oid, stage = meta.split()
                entries.append((name, mode, oid if stage == b"0" else None))
    for raw_name, mode, oid in entries:
        name = raw_name.decode("utf-8", errors="surrogateescape")
        categories = path_findings(name)
        data = None
        if worktree:
            path = root / name
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue  # User deletion is not a publication.
            if not stat.S_ISREG(info.st_mode):
                categories.append("non-regular-file-needs-review")
            elif not categories:
                if info.st_size > MAX_BYTES:
                    categories.append("oversized-needs-review")
                else:
                    data = path.read_bytes()
        elif mode not in (b"100644", b"100755") or oid is None:
            categories.append("non-regular-or-unmerged-index-entry")
        elif not categories:
            if int(git(root, "cat-file", "-s", oid.decode())) > MAX_BYTES:
                categories.append("oversized-needs-review")
            else:
                data = git(root, "cat-file", "blob", oid.decode())
        if data is not None:
            categories.extend(content_findings(data))
        results.extend({"path": name, "category": category} for category in categories)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", action="store_true", help="also inspect public untracked files; respect .gitignore")
    args = parser.parse_args()
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
    findings = scan(root, worktree=args.worktree)
    print(json.dumps({"scope": "worktree" if args.worktree else "index", "findings": findings}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
