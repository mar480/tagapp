"""Local-only illustrative PDF conversion. Print metadata, never report text.

Numeric comparison is a diagnostic, not a correctness oracle: both extractors
can share Unicode errors, and DOM text alone does not establish visual fidelity.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata

from tools.baseline.conversion_probe import ARTIFACT_SHA256, ROOT, sandbox

REGISTRY = ROOT / "docs/qualification/fixture-registry.json"
BASE = ROOT / ".local/qualification/gt-frs102/converted"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCK = {"div", "p", "tr", "td", "th", "li", "br"}


class PageText(HTMLParser):
    """Keep inline numeric fragments together, with block/cell boundaries."""
    def __init__(self):
        super().__init__()
        self.stack = []
        self.pages = []
        self.active = None
        self.hidden = 0
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        prior = self.active
        if "data-page-no" in attributes:
            self.pages.append((int(attributes["data-page-no"], 16), []))
            self.active = len(self.pages) - 1
        if tag in BLOCK:
            self.handle_data("\n")
        hidden = tag in {"script", "style", "title"}
        self.hidden += hidden
        self.scripts += tag == "script"
        if tag not in VOID:
            self.stack.append((tag, prior, hidden))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in BLOCK:
            self.handle_data("\n")
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                for _, prior, hidden in reversed(self.stack[index:]):
                    self.active = prior
                    self.hidden -= hidden
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.active is not None and not self.hidden:
            self.pages[self.active][1].append(data)


def numbers(text: str) -> Counter:
    text = unicodedata.normalize("NFKC", text).replace("\u2212", "-")
    # Include numeric runs adjacent to letters (references, units, superscripts).
    # Text-run boundaries differ between the PDF extractor and positioned HTML.
    return Counter(re.findall(r"(?:\(-?\d[\d,]*(?:\.\d+)?%?\)|-?\d[\d,]*(?:\.\d+)?%?)", text))


def characters(text: str) -> Counter:
    return Counter(c for c in unicodedata.normalize("NFKC", text) if not c.isspace())


def compare(source: str, html: str, expected_pages: int) -> tuple[dict, list]:
    original = source.split("\f")
    if original and not original[-1].strip():
        original.pop()
    collector = PageText()
    collector.feed(html)
    by_page = {number: "".join(parts) for number, parts in collector.pages}
    sequence_ok = [n for n, _ in collector.pages] == list(range(1, expected_pages + 1))
    details = []
    summaries = []
    raw_hyphen_changes = []
    for index, text in enumerate(original, 1):
        converted = by_page.get(index, "")
        before, after = numbers(text), numbers(converted)
        missing, added = before - after, after - before
        original_chars, converted_chars = characters(text), characters(converted)
        missing_chars, added_chars = original_chars - converted_chars, converted_chars - original_chars
        source_hyphens = Counter(c for c in text if unicodedata.category(c) == 'Pd')
        html_hyphens = Counter(c for c in converted if unicodedata.category(c) == 'Pd')
        if source_hyphens != html_hyphens:
            raw_hyphen_changes.append({'page': index,
                'source': {f'U+{ord(c):04X}': n for c, n in sorted(source_hyphens.items())},
                'converted': {f'U+{ord(c):04X}': n for c, n in sorted(html_hyphens.items())}})
        replacement = converted.count("\ufffd")
        private_use = sum(unicodedata.category(c) == "Co" for c in converted)
        summaries.append({"page": index, "source_characters": len(text), "converted_characters": len(converted),
                          "source_numeric_occurrences": sum(before.values()), "converted_numeric_occurrences": sum(after.values()),
                          "missing_occurrences": sum(missing.values()), "added_occurrences": sum(added.values()),
                          "replacement_characters": replacement, "private_use_characters": private_use,
                          "missing_characters": sum(missing_chars.values()), "added_characters": sum(added_chars.values())})
        if missing or added or missing_chars or added_chars or source_hyphens != html_hyphens or replacement or private_use or not text.strip() or not converted.strip():
            details.append({"page": index, "missing": dict(missing), "added": dict(added), "replacement_characters": replacement, "private_use_characters": private_use,
                            "missing_characters": dict(missing_chars), "added_characters": dict(added_chars)})
    result = {"raw_hyphen_changes": raw_hyphen_changes, "source_pages": len(original), "converted_pages": len(collector.pages), "page_sequence_matches": sequence_ok,
              "nonempty_source_pages": sum(bool(p.strip()) for p in original), "script_elements": collector.scripts,
              "private_use_characters": sum(p["private_use_characters"] for p in summaries),
              "missing_characters": sum(p["missing_characters"] for p in summaries),
              "added_characters": sum(p["added_characters"] for p in summaries),
              "source_numeric_occurrences": sum(p["source_numeric_occurrences"] for p in summaries),
              "converted_numeric_occurrences": sum(p["converted_numeric_occurrences"] for p in summaries),
              "missing_numeric_occurrences": sum(p["missing_occurrences"] for p in summaries),
              "added_numeric_occurrences": sum(p["added_occurrences"] for p in summaries),
              "pages_requiring_review": [p["page"] for p in details], "pages": summaries,
              "status": "text_checks_pass_visual_review_pending" if not details and sequence_ok and len(original) == expected_pages else "review_required"}
    return result, details


def public_summary(result: dict) -> dict:
    # Explicit allowlist: never forward detailed differences or processor output.
    keys = ("schema_version", "fixture", "status", "reason", "source_sha256", "converter_sha256", "html_sha256",
            "source_text_sha256", "source_pages", "converted_pages", "page_sequence_matches", "nonempty_source_pages",
            "script_elements", "pages_requiring_review", "production_qualified", "private_use_characters",
            "missing_numeric_occurrences", "added_numeric_occurrences", "converter_options",
            "missing_characters", "added_characters", "raw_hyphen_changes", "source_numeric_occurrences", "converted_numeric_occurrences")
    return {key: result[key] for key in keys if key in result}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analyse-existing", action="store_true", help="Recheck only previously hashed outputs")
    parser.add_argument("--tounicode", choices=("auto", "force"), default="auto")
    parser.add_argument('--exercise-known-incompatibility', action='store_true', help='Qualification experiments only: permit a converter with a known input-codec failure')
    args = parser.parse_args()
    base = BASE if args.tounicode == "auto" else BASE.parent / "converted-force-tounicode"
    options = ["--tounicode", "0" if args.tounicode == "auto" else "1"]
    registry = json.loads(REGISTRY.read_text())
    fixture = next(f for f in registry["fixtures"] if f["id"] == registry["principal_fixture"])
    source = ROOT / fixture["source_path"]
    if source.stat().st_size != fixture["size_bytes"] or digest(source) != fixture["sha256"]:
        raise SystemExit("Source checksum/size mismatch; no processing performed")
    if not args.analyse_existing and not args.exercise_known_incompatibility:
        from tools.baseline.pdf_preflight import assess
        preflight_dir = BASE.parent / 'preflight'
        preflight_dir.mkdir(parents=True, exist_ok=True)
        inventory = sandbox(ROOT / 'tools/baseline', source.parent, preflight_dir, '/usr/bin/pdfimages', '-list', '/input/' + source.name)
        try:
            if inventory.returncode:
                raise ValueError('inventory failed')
            checked = assess(inventory.stdout.decode(), ARTIFACT_SHA256)
        except (ValueError, UnicodeError):
            checked = {'status': 'unable_to_complete', 'production_qualified': False}
        if checked['status'] != 'known_codec_blocker_not_detected':
            # Preserve previous conversions/results. A rejected new attempt must
            # not overwrite evidence from earlier explicit qualification runs.
            print(json.dumps(checked, indent=2))
            return 1
    base.mkdir(parents=True, exist_ok=True)
    html, text = base / "report.html", base / "source.txt"
    result = {"schema_version": 1, "fixture": fixture["id"], "source_sha256": fixture["sha256"],
              "converter_sha256": ARTIFACT_SHA256, "converter_options": options, "production_qualified": False}
    try:
        if args.analyse_existing:
            previous = json.loads((base / "result.json").read_text())
            for path, field in ((source, "source_sha256"), (html, "html_sha256"), (text, "source_text_sha256")):
                if digest(path) != previous.get(field):
                    raise SystemExit("Existing input/output checksum mismatch; no comparison performed")
            if previous.get("converter_sha256") != ARTIFACT_SHA256 or previous.get("converter_options", ["--tounicode", "0"]) != options:
                raise SystemExit("Existing converter checksum mismatch")
        else:
            artifact = ROOT / ".local/downloads/pdf2htmlEX-0.18.8.rc1-focal.AppImage"
            if digest(artifact) != ARTIFACT_SHA256:
                raise SystemExit("Converter checksum mismatch; no processing performed")
            html.unlink(missing_ok=True)
            text.unlink(missing_ok=True)
            with tempfile.TemporaryDirectory(prefix="converter-", dir=base) as temporary:
                runtime = Path(temporary) / "runtime"
                subprocess.run(["unsquashfs", "-no-progress", "-o", "188392", "-d", str(runtime), str(artifact)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                extracted = sandbox(runtime, source.parent, base, "/usr/bin/pdftotext", "-layout", "/input/" + source.name, "/output/source.txt")
                converted = sandbox(runtime, source.parent, base, "/app/AppRun", *options, "--dest-dir", "/output", "/input/" + source.name, "report.html")
                (base / "converter.log").write_bytes(extracted.stderr + converted.stdout + converted.stderr)
                if extracted.returncode or converted.returncode or not html.is_file():
                    raise RuntimeError("processor_failure")
        result.update(html_sha256=digest(html), source_text_sha256=digest(text))
        comparison, private = compare(text.read_text(), html.read_text(), fixture["pages"])
        result.update(comparison)
        (base / "private-differences.json").write_text(json.dumps(private, indent=2) + "\n")
    except subprocess.TimeoutExpired:
        result.update(status="unable_to_complete", reason="timeout")
    except (RuntimeError, subprocess.CalledProcessError, OSError):
        result.update(status="unable_to_complete", reason="processor_or_local_io_failure")
    (base / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    (base / "summary.json").write_text(json.dumps(public_summary(result), indent=2) + "\n")
    print(json.dumps(public_summary(result), indent=2))
    return 0 if result["status"] == "text_checks_pass_visual_review_pending" else 1


if __name__ == "__main__":
    raise SystemExit(main())
