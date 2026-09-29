"""Render authored synthetic fixture data, never real accounts, to PDF and XHTML.

The reference XHTML is NOT pdf2htmlEX output and is NOT iXBRL. Expected tags are
unqualified candidates for later tagging/generation tests, not filing facts.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import html
import json
from pathlib import Path
import textwrap
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from tools.baseline.check import ROOT

SPEC = ROOT / "tests/fixtures/synthetic-frs102/report.json"


def display(value: str, unit: str) -> str:
    amount = Decimal(value)
    if not amount.is_finite():
        raise ValueError("Fixture amounts must be finite decimals")
    digits = 0 if unit == "pure" else 2
    if amount != amount.quantize(Decimal(1).scaleb(-digits)):
        raise ValueError("Display would silently round the authored fixture amount")
    formatted = f"{abs(amount):,.{digits}f}"
    return f"({formatted})" if amount < 0 else formatted


def verify_accounting(spec: dict) -> None:
    rows = {r["id"]: r for p in spec["pages"] for r in p["rows"]}
    for year in ("current", "prior"):
        number = lambda key: Decimal(rows[key][year])
        equations = {
            "gross profit": (number("revenue") - number("cost-sales"), number("gross-profit")),
            "operating profit": (number("gross-profit") - number("administration"), number("operating-profit")),
            "profit before tax": (number("operating-profit") - number("interest"), number("profit-before-tax")),
            "profit": (number("profit-before-tax") - number("tax"), number("profit")),
            "current assets": (number("inventory") + number("debtors") + number("cash"), number("current-assets")),
            "net current assets": (number("current-assets") - number("current-creditors"), number("net-current")),
            "assets less liabilities": (number("fixed-assets") + number("net-current"), number("assets-less-current")),
            "net assets": (number("assets-less-current") - number("long-creditors"), number("net-assets")),
            "equity": (number("capital") + number("retained"), number("total-equity")),
            "balance sheet": (number("net-assets"), number("total-equity")),
            "equity movement": (number("opening-equity") + number("equity-profit") - number("dividends"), number("total-equity")),
            "cash movement": (number("operating-cash") + number("capex") + number("new-borrowing") + number("cash-dividends"), number("cash-increase")),
            "closing cash": (number("opening-cash") + number("cash-increase"), number("closing-cash")),
            "cash to balance sheet": (number("closing-cash"), number("cash")),
            "equipment": (number("equipment-opening") + number("equipment-additions") - number("depreciation"), number("equipment-closing")),
            "equipment to balance sheet": (number("equipment-closing"), number("fixed-assets")),
        }
        for name, (left, right) in equations.items():
            if left != right:
                raise ValueError(f"{year}: {name} does not reconcile")


def pdf_text(text: str, x: int, y: int, *, heading: bool = False) -> bytes:
    encoded = text.encode("cp1252").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    font, size = ("F2", 16) if heading else ("F1", 10)
    return f"BT /{font} {size} Tf 1 0 0 1 {x} {y} Tm (".encode() + encoded + b") Tj ET\n"


def build(spec: dict) -> tuple[bytes, bytes, dict]:
    verify_accounting(spec)
    pages = []
    articles = []
    candidates = []
    ids = set()
    def unique(identifier):
        if identifier in ids:
            raise ValueError("Duplicate fixture source identifier")
        ids.add(identifier)
        return identifier
    for page_number, page in enumerate(spec["pages"], 1):
        unique(page["id"])
        stream = bytearray(pdf_text(page["title"], 40, 790, heading=True))
        body = [f'<article class="page" id="{html.escape(page["id"])}"><h1>{html.escape(page["title"])}</h1>']
        y = 750
        for index, paragraph in enumerate(page["paragraphs"], 1):
            identifier = unique(f'{page["id"]}-p{index}')
            body.append(f'<p id="{identifier}">{html.escape(paragraph)}</p>')
            for line in textwrap.wrap(paragraph, width=82):
                stream.extend(pdf_text(line, 40, y)); y -= 15
            y -= 10
        if page["rows"]:
            stream.extend(pdf_text("Description", 40, y))
            for year, x in [("current", 350), ("prior", 465)]:
                stream.extend(pdf_text(str(spec["years"][year]), x, y))
            y -= 22
            body.append(f'<table><thead><tr><th scope="col">Description</th><th scope="col">{spec["years"]["current"]}</th><th scope="col">{spec["years"]["prior"]}</th></tr></thead><tbody>')
            for row in page["rows"]:
                unique(row["id"])
                stream.extend(pdf_text(row["label"], 40, y))
                body.append(f'<tr id="{row["id"]}"><th scope="row">{html.escape(row["label"])}</th>')
                for year, x in [("current", 350), ("prior", 465)]:
                    identifier = unique(row["id"] + "-" + year)
                    shown = display(row[year], row["unit"])
                    stream.extend(pdf_text(shown, x, y))
                    body.append(f'<td id="{identifier}">{shown}</td>')
                    if "expected_tag" in row:
                        tag = row["expected_tag"]
                        date = str(spec["years"][year])
                        candidates.append({"id": identifier, "concept": {"namespace": tag["namespace"], "local_name": tag["local_name"]},
                                           "value": row[year], "displayed_text": shown, "unit": row["unit"], "scale": 0,
                                           "decimals": "0" if row["unit"] == "pure" else "2",
                                           "period": {"instant": date + "-12-31"} if tag["period_type"] == "instant" else {"start": date + "-01-01", "end": date + "-12-31"},
                                           "dimensions": tag["dimensions"], "source": {"page": page_number, "node_id": identifier, "x": x, "baseline_y": y},
                                           "status": "candidate_not_filing_qualified"})
                body.append("</tr>")
                y -= 21
            body.append("</tbody></table>")
        if y < 65:
            raise ValueError(f'Fixture page overflow: {page["id"]}')
        footer = f"SYNTHETIC - NOT FOR FILING | Page {page_number} of {len(spec['pages'])}"
        stream.extend(pdf_text(footer, 40, 30))
        body.append(f"<footer>{footer}</footer></article>")
        pages.append(bytes(stream)); articles.append("\n".join(body))
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               ("<< /Type /Pages /Kids [" + " ".join(f"{5+2*i} 0 R" for i in range(len(pages))) + f"] /Count {len(pages)} >>").encode(),
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
    for i, stream in enumerate(pages):
        objects += [f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {6+2*i} 0 R >>".encode(),
                    b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets = []
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf)); pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets:pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    reference = ('<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" lang="en"><head><meta charset="utf-8"/><title>Synthetic report - not for filing</title><style>body{font-family:Arial,sans-serif;color:#111;background:white}.page{max-width:52rem;padding:2rem;margin:auto;page-break-after:always}table{width:100%;border-collapse:collapse}th,td{padding:.4rem;text-align:right;border-bottom:1px solid #ccc}th:first-child{text-align:left}footer{margin-top:2rem;font-size:.8rem}p{line-height:1.5}</style></head><body>' + "\n".join(articles) + '</body></html>').encode()
    expected = {"schema_version": 1, "fixture": spec["id"], "qualification": "not_for_filing", "facts": candidates}
    return bytes(pdf), reference, expected


def verify_taxonomy(spec: dict, package: Path) -> dict:
    from tools.baseline.taxonomy_probe import inspect_package
    inspect_package(package, spec["taxonomy_sha256"])
    concepts = {}
    with ZipFile(package) as archive:
        for name in archive.namelist():
            if name.endswith(".xsd"):
                schema = ET.fromstring(archive.read(name))
                for element in schema.findall("{http://www.w3.org/2001/XMLSchema}element"):
                    concepts[(schema.get("targetNamespace"), element.get("name"))] = element.attrib
    checked = 0
    for page in spec["pages"]:
        for row in page["rows"]:
            tag = row.get("expected_tag")
            if not tag:
                continue
            concept = concepts.get((tag["namespace"], tag["local_name"]))
            if concept is None or concept.get("{http://www.xbrl.org/2003/instance}periodType") != tag["period_type"]:
                raise ValueError("Missing concept or incompatible period: " + row["id"])
            for dimension in tag["dimensions"]:
                for role in ("dimension", "member"):
                    qname = dimension[role]
                    resolved = concepts.get((qname["namespace"], qname["local_name"]))
                    if resolved is None or (role == "dimension" and resolved.get("substitutionGroup") != "xbrldt:dimensionItem"):
                        raise ValueError("Missing/incorrect dimension identifier: " + row["id"])
            checked += 1
    return {"status": "pass", "candidate_rows": checked, "scope": "Concept existence, period type and dimension identifiers only; dimensional validity not checked"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-taxonomy", action="store_true")
    args = parser.parse_args()
    spec = json.loads(SPEC.read_text())
    pdf, reference, expected = build(spec)
    base = ROOT / ".local/qualification/report-fixture"
    base.mkdir(parents=True, exist_ok=True)
    files = {"report.pdf": pdf, "reference.xhtml": reference, "expected-facts.json": (json.dumps(expected, indent=2) + "\n").encode()}
    for name, content in files.items():(base / name).write_bytes(content)
    result = {"schema_version": 1, "fixture": spec["id"], "pages": len(spec["pages"]), "candidate_facts": len(expected["facts"]),
              "spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(), "files": {n: hashlib.sha256(b).hexdigest() for n, b in files.items()},
              "qualification": "arithmetic checked; not complete statutory accounts or a qualified filing fixture"}
    if args.check_taxonomy:
        result["taxonomy_check"] = verify_taxonomy(spec, ROOT / ".local/downloads/FRC-2026-Taxonomy-v1.0.0.zip")
    (base / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
