"""Inspect the pinned FRC archive and qualify entry-point loading offline.

Administrative tooling only: never used on confidential reports. No extraction,
network acquisition, schema patching or persisted Arelle configuration is performed.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import subprocess
import sys
import tempfile
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from tools.baseline.processor_probe import ROOT, VERSION, findings

PACKAGE_SHA256 = "ae80ae12d9d747ac531150b0051bcd67e7c9acf44313da19105b4cc013566462"
TP = "{http://xbrl.org/2016/taxonomy-package}"
CAT = "{urn:oasis:names:tc:entity:xmlns:xml:catalog}"


def xml(data: bytes) -> ET.Element:
    data.decode("utf-8-sig")
    if b"\0" in data:
        raise ValueError("Only UTF-8 XML metadata is supported")
    if re.search(br"<!\s*(?:DOCTYPE|ENTITY)\b", data, re.IGNORECASE):
        raise ValueError("DTD/entity declarations are not permitted")
    return ET.fromstring(data)


def inspect_package(path: Path, expected_sha256: str) -> dict:
    if path.stat().st_size > 50_000_000:
        raise ValueError("Archive exceeds administrative intake limit")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Archive checksum differs from the approved pin")
    with ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 10_000 or sum(e.file_size for e in entries) > 200_000_000:
            raise ValueError("Archive resource limit exceeded")
        names = set()
        folded = set()
        for entry in entries:
            name = entry.filename.rstrip("/")
            parts = name.split("/")
            if (not name or name.startswith("/") or "\\" in name or ":" in name
                    or any(part in {"", ".", ".."} for part in parts)
                    or any(ord(c) < 32 for c in name)):
                raise ValueError("Unsafe archive member path")
            if name in names or name.casefold() in folded:
                raise ValueError("Ambiguous duplicate archive member")
            names.add(name)
            folded.add(name.casefold())
            kind = stat.S_IFMT(entry.external_attr >> 16)
            if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise ValueError("Archive links/special files are not permitted")
            if entry.flag_bits & 1:
                raise ValueError("Encrypted archive member")
            if entry.file_size > 50_000_000 or entry.file_size > max(1, entry.compress_size) * 1000:
                raise ValueError("Archive member resource limit exceeded")
        manifests = [n for n in names if n.endswith("/META-INF/taxonomyPackage.xml")]
        if len(manifests) != 1:
            raise ValueError("Expected one package manifest")
        manifest_name = manifests[0]
        root = manifest_name.removesuffix("META-INF/taxonomyPackage.xml")
        catalog_name = root + "META-INF/catalog.xml"
        manifest = xml(archive.read(manifest_name))
        catalog = xml(archive.read(catalog_name))
        if manifest.tag != TP + "taxonomyPackage" or catalog.tag != CAT + "catalog":
            raise ValueError("Unexpected package/catalog namespace")
        mappings = []
        for rewrite in catalog:
            if rewrite.tag != CAT + "rewriteURI":
                raise ValueError("Unsupported catalog directive requires review")
            uri = rewrite.attrib["uriStartString"]
            prefix = rewrite.attrib["rewritePrefix"]
            resolved = posixpath.normpath(posixpath.join(root, "META-INF", prefix)) + "/"
            if not resolved.startswith(root) or "\\" in prefix or ":" in prefix:
                raise ValueError("Catalog mapping escapes package root")
            if any(old[0] == uri for old in mappings):
                raise ValueError("Duplicate catalog URI prefix")
            mappings.append((uri, resolved))
        points = []
        for point in manifest.findall(TP + "entryPoints/" + TP + "entryPoint"):
            documents = []
            for document in point.findall(TP + "entryPointDocument"):
                href = document.attrib["href"]
                applicable = sorted((m for m in mappings if href.startswith(m[0])), key=lambda m: len(m[0]), reverse=True)
                if not applicable:
                    raise ValueError("Entry point has no local catalog mapping")
                uri, prefix = applicable[0]
                local = prefix + href[len(uri):]
                if local not in names or not local.startswith(root):
                    raise ValueError("Entry point is missing from package")
                documents.append({"uri": href, "archive_path": local})
            if not documents:
                raise ValueError("Entry point has no documents")
            points.append({"name": point.findtext(TP + "name"), "documents": documents})
        if archive.testzip() is not None:
            raise ValueError("Archive CRC check failed")
        return {"sha256": digest, "size_bytes": path.stat().st_size, "entries": len(entries),
                "uncompressed_bytes": sum(e.file_size for e in entries),
                "identifier": manifest.findtext(TP + "identifier"), "version": manifest.findtext(TP + "version"),
                "entry_points": points, "catalog_mappings": len(mappings)}


def main() -> int:
    package = ROOT / ".local/downloads/FRC-2026-Taxonomy-v1.0.0.zip"
    inspected = inspect_package(package, PACKAGE_SHA256)
    if importlib.metadata.version("arelle-release") != VERSION:
        raise SystemExit("Installed Arelle differs from probe pin")
    base = ROOT / ".local/qualification/taxonomy"
    base.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "package": inspected, "processor": "arelle-release", "processor_version": VERSION,
              "scope": "offline taxonomy load/validation; not filing-profile qualification",
              "network": "unshare --net; Arelle offline; fresh per-case user cache", "cases": []}
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "LANG", "LC_ALL"}}
    for point in inspected["entry_points"]:
        if point["name"] not in {"FRS-101", "FRS-102", "IFRS"}:
            continue
        name = point["name"]
        log = base / (name + ".xml")
        log.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(prefix=name + "-", dir=base) as temporary:
            env["HOME"] = temporary
            command = ["unshare", "--user", "--map-root-user", "--net", "--", sys.executable, "-m", "arelle.CntlrCmdLine",
                       "--packages", str(package), "--file", point["documents"][0]["uri"], "--validate", "--validationExitCode",
                       "--formula", "none", "--internetConnectivity", "offline", "--disablePersistentConfig",
                       "--xdgConfigHome", temporary, "--cacheDirectory", temporary + "/cache", "--logFile", str(log),
                       "--DTS", str(base / (name + "-dts.json"))]
            try:
                proc = subprocess.run(command, capture_output=True, env=env, timeout=90)
                (base / (name + ".log")).write_bytes(proc.stdout + proc.stderr)
                entries = findings(log) if log.is_file() else []
                errors = [e for e in entries if e["level"].lower() in {"error", "critical"}]
                status = "pass" if proc.returncode == 0 and log.exists() and not errors else "unable_to_complete"
                result["cases"].append({"id": name, "status": status, "exit_code": proc.returncode, "findings": entries})
            except subprocess.TimeoutExpired:
                result["cases"].append({"id": name, "status": "unable_to_complete", "reason": "timeout"})
    (base / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if len(result["cases"]) == 3 and all(c["status"] == "pass" for c in result["cases"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
