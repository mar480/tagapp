"""Convert the substantial synthetic fixture and compare all monetary occurrences."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from tools.baseline.conversion_probe import ARTIFACT_SHA256, TextCollector, sandbox
from tools.baseline.report_fixture import ROOT, SPEC, build, display


class ReportText(TextCollector):
    def __init__(self):
        super().__init__()
        self.pages = []

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        number = dict(attrs).get("data-page-no")
        if number:
            self.pages.append(int(number, 16))


def amounts(text: str) -> Counter:
    return Counter(re.findall(r"(?<![0-9.,])(?:\([0-9][0-9,]*\.[0-9]{2}\)|[0-9][0-9,]*\.[0-9]{2})(?![0-9.,])", text))


def main() -> int:
    for tool in ("bwrap", "unsquashfs", "pdftotext"):
        if not shutil.which(tool):
            raise SystemExit("Required local qualification tool missing: " + tool)
    artifact = ROOT / ".local/downloads/pdf2htmlEX-0.18.8.rc1-focal.AppImage"
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != ARTIFACT_SHA256:
        raise SystemExit("Converter checksum mismatch")
    spec = json.loads(SPEC.read_text())
    pdf, _, _ = build(spec)
    base = ROOT / ".local/qualification/report-conversion"
    inputs = base / "inputs"
    output = base / "output"
    inputs.mkdir(parents=True, exist_ok=True); output.mkdir(parents=True, exist_ok=True)
    (inputs / "report.pdf").write_bytes(pdf)
    target = output / "report.html"
    target.unlink(missing_ok=True)
    expected = Counter(display(row[year], row["unit"]) for page in spec["pages"] for row in page["rows"] for year in ("current", "prior") if row["unit"] == "GBP")
    result = {"schema_version": 1, "fixture": spec["id"], "source_pdf_sha256": hashlib.sha256(pdf).hexdigest(),
              "converter_sha256": ARTIFACT_SHA256, "expected_pages": len(spec["pages"]),
              "expected_monetary_occurrences": sum(expected.values()), "production_qualified": False}
    try:
        with tempfile.TemporaryDirectory(prefix="converter-", dir=base) as temporary:
            runtime = Path(temporary) / "runtime"
            subprocess.run(["unsquashfs", "-no-progress", "-o", "188392", "-d", str(runtime), str(artifact)], check=True, stdout=subprocess.DEVNULL)
            source = sandbox(runtime, inputs, output, "/usr/bin/pdftotext", "/input/report.pdf", "-")
            converted = sandbox(runtime, inputs, output, "/app/AppRun", "--dest-dir", "/output", "/input/report.pdf", "report.html")
            (output / "converter.log").write_bytes(converted.stdout + converted.stderr)
            if source.returncode or converted.returncode or not target.is_file():
                result.update(status="unable_to_complete", reason="processor failure")
            else:
                collector = ReportText(); collector.feed(target.read_text())
                copied = amounts(" ".join(collector.parts))
                source_amounts = amounts(source.stdout.decode())
                good = copied == expected and source_amounts == expected and sorted(collector.pages) == list(range(1, len(spec["pages"]) + 1))
                result.update(status="pass" if good else "fail", observed_pages=len(collector.pages),
                              copied_monetary_occurrences=sum(copied.values()), missing=dict(expected - copied), unexpected=dict(copied - expected),
                              source_amounts_match=source_amounts == expected, script_elements=collector.scripts,
                              converted_html_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    except subprocess.TimeoutExpired:
        result.update(status="unable_to_complete", reason="timeout")
    (base / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
