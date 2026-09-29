"""Validate baseline records; optionally verify private inputs or milestone gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def load(root: Path, path: str):
    return json.loads((root / path).read_text())


def validate_profiles(matrix: dict, source_ids: set[str]) -> list[str]:
    errors = []
    ids = [p["id"] for p in matrix["profiles"]]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate profile identifiers")
    frameworks = {f["id"] for f in matrix["frameworks"]}
    if frameworks != {"FRS101", "FRS102", "FRS105", "UK_IFRS"}:
        errors.append("Agreed framework coverage is incomplete")
    if {p["entity"] for p in matrix["profiles"]} != {"company", "llp"}:
        errors.append("Company and LLP candidates are required")
    for p in matrix["profiles"]:
        if not set(p["frameworks_to_assess"]) <= frameworks:
            errors.append(p["id"] + ": unknown framework")
        if not p["source_refs"] or any(ref["source"] not in source_ids for ref in p["source_refs"]):
            errors.append(p["id"] + ": missing source reference")
        cases = [p["positive_case"], *p["negative_cases"]]
        if not p["negative_cases"]:
            errors.append(p["id"] + ": no negative acceptance case")
        # Candidate specifications cannot accidentally enable production.
        if p["production_enabled"] or p["status"] == "qualified":
            if p["status"] != "qualified" or p["eligibility"] != "reviewed":
                errors.append(p["id"] + ": qualification/eligibility is incomplete")
            for case in cases:
                if (case["status"] != "verified" or not case.get("evidence")
                        or not SHA256.fullmatch(case.get("fixture_sha256") or "")):
                    errors.append(case["id"] + ": verified fixture evidence required")
            if not p.get("qualification_record"):
                errors.append(p["id"] + ": independent profile review required")
    return errors


def check(root: Path, *, local: bool = False, require_qualified: bool = False) -> list[str]:
    errors = []
    sources = load(root, "docs/compliance/sources.json")["sources"]
    source_ids = {s["id"] for s in sources}
    if len(source_ids) != len(sources):
        errors.append("Duplicate source identifiers")
    errors += validate_profiles(load(root, "docs/compliance/profile-matrix.json"), source_ids)
    repos = load(root, "docs/qualification/repository-pins.json")["repositories"]
    cake = next(r for r in repos if r["name"] == "cake")
    if cake["commit"] != "9251b790faa65b78d80dbe4528fcdd3aefef1238":
        errors.append("Cake baseline changed without a preservation-contract update")
    if local:
        materials = load(root, "docs/qualification/materials-manifest.json")["files"]
        for item in [*materials, *repos]:
            relative = item.get("path", item.get("bundle_path"))
            path = root / relative
            if not path.is_file():
                errors.append(relative + ": unavailable")
                continue
            hasher = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(block)
            if path.stat().st_size != item["size_bytes"] or hasher.hexdigest() != item["sha256"]:
                errors.append(relative + ": input differs from reviewed bytes")
        for repo in repos:
            mirror = root / (repo["name"] + ".git")
            proc = subprocess.run(["git", "--git-dir=" + str(mirror), "rev-parse", "refs/heads/" + repo["branch"]], capture_output=True, text=True)
            if proc.returncode or proc.stdout.strip() != repo["commit"]:
                errors.append(repo["name"] + ": reviewed branch pin unavailable or changed")
    if require_qualified:
        record = load(root, "docs/milestones/01-status.json")
        for gate in record["gates"]:
            if gate["status"] != "passed" or not gate.get("evidence"):
                errors.append(gate["id"] + ": " + gate["status"])
        if record["status"] != "complete":
            errors.append("Milestone 1 is not complete; dependent milestones remain gated")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-materials", action="store_true")
    parser.add_argument("--require-qualified", action="store_true")
    args = parser.parse_args()
    errors = check(ROOT, local=args.local_materials, require_qualified=args.require_qualified)
    print(json.dumps({"record_consistency": "fail" if errors else "pass", "qualification_gate_checked": args.require_qualified, "local_inputs_checked": args.local_materials, "findings": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
