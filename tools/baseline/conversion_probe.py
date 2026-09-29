"""Generate synthetic PDFs and probe the pinned AppImage in a Linux sandbox.

No input-report parameter is provided: this harness is for synthetic data only.
Results are feasibility evidence, not production converter qualification.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import resource
import re
import shutil
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_SHA256 = "11de2583a3abce5f141fd7fafb1fea2c67b15886e546d6b7675c600012e6ab8c"
ARTIFACT_URL = "https://github.com/pdf2htmlEX/pdf2htmlEX/releases/download/v0.18.8.rc1/pdf2htmlEX-0.18.8.rc1-master-20200630-Ubuntu-focal-x86_64.AppImage"


def make_pdf(stream: bytes, *, unicode_map: bytes | None = None) -> bytes:
    """A deterministic single-page PDF, with no external fonts or client data."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> /XObject << /Im1 6 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pixels = zlib.compress(bytes([0, 255] * 32))
    objects.append(b"<< /Type /XObject /Subtype /Image /Width 8 /Height 8 /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode /Length " + str(len(pixels)).encode() + b" >>\nstream\n" + pixels + b"\nendstream")
    if unicode_map is not None:
        objects[3] = objects[3].replace(b" >>", b" /ToUnicode 7 0 R >>")
        objects.append(b"<< /Length " + str(len(unicode_map)).encode() + b" >>\nstream\n" + unicode_map + b"\nendstream")
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, body in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{i} 0 obj\n".encode() + body + b"\nendobj\n")
    start = len(output)
    output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    return bytes(output)


CASES = {
    "financial-text": (
        b"BT /F1 12 Tf 50 780 Td (SYNTHETIC - NOT FOR FILING) Tj 0 -30 Td (Revenue 1,234.50) Tj 0 -20 Td (Comparative 987.00) Tj 0 -20 Td (Loss \\(12.34\\)) Tj 0 -20 Td (Zero 0.00) Tj ET",
        ["1,234.50", "987.00", "(12.34)", "0.00"],
    ),
    "fragmented-number": (
        b"BT /F1 12 Tf 50 780 Td (SYNTHETIC fragmented number) Tj 0 -30 Td [(1,) 0 (234) 0 (.50)] TJ ET",
        ["1,234.50"],
    ),
    "rotated-text": (
        b"BT /F1 12 Tf 0 1 -1 0 100 200 Tm (Rotated 42.75) Tj ET",
        ["42.75"],
    ),
    "image-only": (b"q 200 0 0 200 50 500 cm /Im1 Do Q", []),
    "correct-unicode-map": (b"BT /F1 12 Tf 50 780 Td (Amount 12.34) Tj ET", ["12.34"]),
    "incorrect-unicode-map": (b"BT /F1 12 Tf 50 780 Td (Amount 12.34) Tj ET", ["12.34"]),
}


UNICODE_MAP = b"""/CIDInit /ProcSet findresource begin
12 dict begin
begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /SyntheticMap def
/CMapType 2 def
1 begincodespacerange
<00> <FF>
endcodespacerange
1 beginbfchar
<31> <0031>
endbfchar
endcmap
CMapName currentdict /CMap defineresource pop
end
end"""


class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts: list[str] = []
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "title"}:
            self.hidden += 1
        if tag == "script":
            self.scripts += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "title"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def squash(text: str) -> str:
    return "".join(text.split())


def check_text(expected: list[str], extracted: str) -> dict:
    compact = squash(extracted)
    if not expected:
        return {"status": "unsupported_image_only" if not compact else "unexpected_text", "missing": []}
    missing = [token for token in expected if len(re.findall(r"(?<![0-9.,])" + re.escape(squash(token)) + r"(?![0-9.,])", compact)) != expected.count(token)]
    return {"status": "pass" if not missing else "fail", "missing": missing}


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))


def sandbox(runtime: Path, inputs: Path, output: Path, *command: str) -> subprocess.CompletedProcess:
    args = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL"]
    for path in ("/usr", "/lib", "/lib64"):
        if Path(path).exists():
            args += ["--ro-bind", path, path]
    args += ["--ro-bind", str(runtime), "/app", "--ro-bind", str(inputs), "/input", "--bind", str(output), "/output",
             "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--dir", "/home",
             "--clearenv", "--setenv", "HOME", "/home", "--setenv", "APPDIR", "/app",
             "--setenv", "PATH", "/usr/bin", "--setenv", "LANG", "C.UTF-8", "--chdir", "/output", "--", *command]
    return subprocess.run(args, capture_output=True, timeout=90, preexec_fn=limits)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=ROOT / ".local/downloads/pdf2htmlEX-0.18.8.rc1-focal.AppImage")
    args = parser.parse_args()
    for executable in ("bwrap", "pdftotext", "unsquashfs"):
        if not shutil.which(executable):
            parser.error(f"Required tool unavailable: {executable}")
    if not args.artifact.is_file() or hashlib.sha256(args.artifact.read_bytes()).hexdigest() != ARTIFACT_SHA256:
        parser.error("Converter artefact missing or checksum mismatch; no converter executed")
    base = ROOT / ".local/qualification/conversion"
    inputs = base / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    # Always extract the verified archive into a fresh directory. An existing
    # AppRun tree is not trustworthy merely because the archive hash matches.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="converter-", dir=base) as temporary:
        runtime = Path(temporary) / "runtime"
        subprocess.run(["unsquashfs", "-no-progress", "-o", "188392", "-d", str(runtime), str(args.artifact.resolve())], check=True, stdout=subprocess.DEVNULL)
        evidence = {"schema_version": 1, "artifact_sha256": ARTIFACT_SHA256, "artifact_url": ARTIFACT_URL,
                    "scope": "synthetic feasibility only", "network": "bubblewrap --unshare-all", "production_qualified": False, "cases": []}
        for name, (stream, expected) in CASES.items():
            pdf = inputs / (name + ".pdf")
            mapping = UNICODE_MAP if name == "correct-unicode-map" else UNICODE_MAP.replace(b"<0031>", b"<0037>") if name == "incorrect-unicode-map" else None
            pdf.write_bytes(make_pdf(stream, unicode_map=mapping))
            output = base / name
            output.mkdir(exist_ok=True)
            target = output / "report.html"
            target.unlink(missing_ok=True)
            try:
                before = sandbox(runtime, inputs, output, "/usr/bin/pdftotext", "/input/" + pdf.name, "-")
                proc = sandbox(runtime, inputs, output, "/app/AppRun", "--dest-dir", "/output", "/input/" + pdf.name, "report.html")
                # Diagnostics contain only generated synthetic text in this harness.
                (output / "converter.log").write_bytes(proc.stdout + proc.stderr)
                text = TextCollector()
                if proc.returncode == 0 and target.is_file():
                    text.feed(target.read_text())
                    result = check_text(expected, "".join(text.parts))
                else:
                    result = {"status": "unable_to_complete", "missing": []}
                result.update({"id": name, "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                               "source_text": check_text(expected, before.stdout.decode(errors="replace")) if before.returncode == 0 else {"status": "unable_to_complete"},
                               "exit_code": proc.returncode, "script_elements": text.scripts,
                               "html_sha256": hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None})
            except subprocess.TimeoutExpired:
                result = {"id": name, "status": "unable_to_complete", "reason": "timeout"}
            result["expected"] = "text_mismatch" if name == "incorrect-unicode-map" else "image_only" if name == "image-only" else "text_preserved"
            observed = result["status"]
            source_status = result.get("source_text", {}).get("status")
            expected_status = "fail" if name == "incorrect-unicode-map" else "unsupported_image_only" if name == "image-only" else "pass"
            result["expectation_met"] = observed == expected_status and source_status == expected_status
            evidence["cases"].append(result)
        (base / "result.json").write_text(json.dumps(evidence, indent=2) + "\n")
        print(json.dumps(evidence, indent=2))
        return 0 if all(c["expectation_met"] for c in evidence["cases"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
