"""Acquire or verify the explicit Companies House schema pins; never submit data."""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
import urllib.request
import xml.etree.ElementTree as ET

from tools.baseline.acquire import store_verified
from tools.baseline.check import ROOT

PIN = ROOT / 'docs/compliance/ch-schema-pins.json'
BASE = ROOT / '.local/qualification/ch-schemas/files'
XSD = '{http://www.w3.org/2001/XMLSchema}'


def safe_path(name: str) -> str:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or any(c in name for c in ('\\', '%', '?', '#', ':')):
        raise ValueError('Unsafe schema path')
    return p.as_posix()


def dependency_path(parent: str, reference: str) -> str:
    parts = urlsplit(reference)
    if parts.scheme or parts.netloc or reference.startswith('/') or any(c in reference for c in ('%', '\\', '?', '#')):
        raise ValueError('Unpinned external schema reference')
    resolved = posixpath.normpath(posixpath.join(str(PurePosixPath(safe_path(parent)).parent), reference))
    return safe_path(resolved)


def verify(pins: dict, base: Path) -> dict[str, Path]:
    files = {}
    for item in pins['files']:
        name = safe_path(item['path'])
        if name in files:
            raise ValueError('Duplicate schema path')
        path = (base / name).resolve()
        if not path.is_relative_to(base.resolve()):
            raise ValueError('Schema escapes local storage')
        data = path.read_bytes()
        if len(data) != item['size_bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Schema checksum mismatch')
        if b'<!DOCTYPE' in data or b'<!ENTITY' in data:
            raise ValueError('Schema document declarations are not permitted')
        doc = ET.fromstring(data)
        if doc.tag != XSD + 'schema' or doc.get('targetNamespace') != item['target_namespace']:
            raise ValueError('Schema namespace mismatch')
        references = [e.get('schemaLocation') for e in doc if e.tag in {XSD + t for t in ('include', 'import', 'redefine')}]
        if references != item['dependencies'] or any(ref is None for ref in references):
            raise ValueError('Schema dependencies differ from pin')
        files[name] = path
    for item in pins['files']:
        for ref in item['dependencies']:
            if dependency_path(item['path'], ref) not in files:
                raise ValueError('Missing pinned schema dependency')
    if not set(pins['roots'].values()) <= files.keys():
        raise ValueError('Missing schema root')
    return files


class OfficialRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def allowed_url(url: str) -> None:
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.netloc != 'xmlgw.companieshouse.gov.uk'
            or not parts.path.startswith('/v1-0/schema/') or parts.query or parts.fragment):
        raise ValueError('Acquisition restricted to official schema URLs')
    safe_path(parts.path[len('/v1-0/schema/'):])
    if not parts.path.endswith('.xsd'):
        raise ValueError('Only schema downloads are permitted')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquire', action='store_true', help='Administrative acquisition only; processing never downloads')
    args = parser.parse_args()
    pins = json.loads(PIN.read_text())
    if args.acquire:
        opener = urllib.request.build_opener(OfficialRedirects())
        for item in pins['files']:
            allowed_url(item['url'])
            target = BASE / safe_path(item['path'])
            if not target.resolve().is_relative_to(BASE.resolve()):
                raise ValueError('Acquisition destination escapes local storage')
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == item['sha256']:
                continue
            with opener.open(item['url'], timeout=30) as response:
                store_verified(response, target, size=item['size_bytes'], digest=item['sha256'])
    files = verify(pins, BASE)
    print(json.dumps({'pinned_files': len(files), 'dependency_closure': 'verified', 'submission_attempted': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
