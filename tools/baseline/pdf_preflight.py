"""Detect known converter/input incompatibilities before expensive conversion."""
from __future__ import annotations

from collections import Counter
import json

from tools.baseline.conversion_probe import ARTIFACT_SHA256, ROOT, sandbox
from tools.baseline.illustrative_probe import digest


def image_codecs(listing: str) -> Counter:
    codecs = Counter()
    lines = listing.splitlines()
    if len(lines) < 2 or not lines[0].lstrip().startswith('page') or 'enc' not in lines[0]:
        raise ValueError('Unrecognised image inventory')
    for line in lines[2:]:
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) < 14 or not fields[0].isdigit() or not fields[1].isdigit():
            raise ValueError('Unrecognised image inventory row')
        codecs[fields[8]] += 1
    return codecs


def assess(listing: str, converter_sha256: str) -> dict:
    codecs = image_codecs(listing)
    findings = []
    if converter_sha256 == ARTIFACT_SHA256 and codecs['jpx']:
        findings.append({'code': 'converter.jpeg2000_unsupported', 'severity': 'blocking',
                         'affected_image_streams': codecs['jpx'],
                         'explanation': 'This pinned converter was built without OpenJPEG and loses JPEG2000 image content. A different qualified build is required; changing PNG/SVG output does not fix decoding.'})
    return {'status': 'converter_incompatible' if findings else 'known_codec_blocker_not_detected',
            'image_streams_by_encoding': dict(codecs), 'findings': findings,
            'production_qualified': False}


def main() -> int:
    fixture = json.loads((ROOT / 'docs/qualification/fixture-registry.json').read_text())['fixtures'][0]
    source = ROOT / fixture['source_path']
    if digest(source) != fixture['sha256']:
        raise SystemExit('Source checksum mismatch')
    output = ROOT / '.local/qualification/gt-frs102/preflight'
    output.mkdir(parents=True, exist_ok=True)
    proc = sandbox(ROOT / 'tools/baseline', source.parent, output,
                   '/usr/bin/pdfimages', '-list', '/input/' + source.name)
    try:
        if proc.returncode:
            raise ValueError('Image inventory processor failure')
        result = assess(proc.stdout.decode(), ARTIFACT_SHA256)
    except (ValueError, UnicodeError):
        result = {'status': 'unable_to_complete', 'production_qualified': False}
    result.update(schema_version=1, source_sha256=fixture['sha256'], converter_sha256=ARTIFACT_SHA256)
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'known_codec_blocker_not_detected' else 1


if __name__ == '__main__':
    raise SystemExit(main())
