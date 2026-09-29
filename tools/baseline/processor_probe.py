"""Exercise an installed Arelle against synthetic iXBRL, with network disabled.

Requires Linux unshare and arelle-release==2.44.1 in the selected interpreter.
This is a processor feasibility probe, not FRC/Companies House qualification.
"""
from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
VERSION = "2.44.1"
SCHEMA = '''<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:t="urn:tagger:synthetic"
 targetNamespace="urn:tagger:synthetic" elementFormDefault="qualified">
 <xs:import namespace="http://www.xbrl.org/2003/instance" schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>
 <xs:element name="Assets" id="Assets" substitutionGroup="xbrli:item" type="xbrli:monetaryItemType" xbrli:periodType="instant" nillable="true"/>
</xs:schema>'''
DOCUMENT = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
 xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:link="http://www.xbrl.org/2003/linkbase"
 xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:iso4217="http://www.xbrl.org/2003/iso4217" xmlns:t="urn:tagger:synthetic">
 <head><title>Synthetic processor probe - not for filing</title></head><body>
 <div style="display:none"><ix:header><ix:references>
 <link:schemaRef xlink:type="simple" xlink:href="taxonomy.xsd"/>
 </ix:references><ix:resources>
 <xbrli:context id="c"><xbrli:entity><xbrli:identifier scheme="urn:tagger:synthetic-entity">SYNTHETIC</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-12-31</xbrli:instant></xbrli:period></xbrli:context>
 <xbrli:unit id="GBP"><xbrli:measure>iso4217:GBP</xbrli:measure></xbrli:unit>
 </ix:resources></ix:header></div>
 <p>Assets <ix:nonFraction name="t:Assets" contextRef="c" unitRef="GBP" decimals="2">VALUE</ix:nonFraction></p>
 </body></html>'''


def findings(log: Path) -> list[dict]:
    tree = ET.parse(log)
    # Only codes and severity enter public evidence; never processor message text.
    return [{"code": e.get("code"), "level": e.get("level")} for e in tree.getroot().iter("entry")]


def main() -> int:
    installed = importlib.metadata.version("arelle-release")
    if installed != VERSION:
        raise SystemExit(f"Expected arelle-release {VERSION}; found {installed}. Requalify before changing the pin.")
    base = ROOT / ".local/qualification/processor"
    base.mkdir(parents=True, exist_ok=True)
    (base / "taxonomy.xsd").write_text(SCHEMA)
    result = {"schema_version": 1, "processor": "arelle-release", "version": VERSION,
              "scope": "synthetic iXBRL/core XBRL only", "network": "unshare --net and offline cache",
              "frc_qualified": False, "companies_house_qualified": False, "cases": []}
    for name, value in [("valid", "12.34"), ("invalid-value", "not-a-number")]:
        source = base / (name + ".xhtml")
        source.write_text(DOCUMENT.replace("VALUE", value))
        log = base / (name + ".xml")
        log.unlink(missing_ok=True)
        args = ["unshare", "--user", "--map-root-user", "--net", "--", sys.executable, "-m", "arelle.CntlrCmdLine",
                "--file", str(source), "--validate", "--validationExitCode", "--formula", "none",
                "--internetConnectivity", "offline", "--disablePersistentConfig", "--xdgConfigHome", str(base / "config"),
                "--logFile", str(log), "--facts", str(base / (name + "-facts.csv"))]
        env = {k: v for k, v in os.environ.items() if k in {"PATH", "LANG", "LC_ALL"}}
        env["HOME"] = str(base)
        try:
            proc = subprocess.run(args, env=env, capture_output=True, timeout=60)
            (base / (name + ".log")).write_bytes(proc.stdout + proc.stderr)
            entries = findings(log) if log.is_file() else []
            errors = [e for e in entries if e["level"] in {"error", "critical", "ERROR", "CRITICAL"}]
            expected = proc.returncode == 0 and not errors if name == "valid" else proc.returncode == 3 and any(e["code"] == "xmlSchema:valueError" for e in errors)
            result["cases"].append({"id": name, "status": "pass" if expected and log.exists() else "fail",
                                    "exit_code": proc.returncode, "findings": entries})
        except subprocess.TimeoutExpired:
            result["cases"].append({"id": name, "status": "unable_to_complete", "reason": "timeout"})
    (base / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if all(c["status"] == "pass" for c in result["cases"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
