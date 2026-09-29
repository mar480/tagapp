"""Small public PDFs distinguishing painted glyphs from PDF ActualText metadata."""
from __future__ import annotations

import json
import subprocess

from tools.baseline import built_converter
from tools.baseline.conversion_probe import ROOT, make_pdf, sandbox, UNICODE_MAP
from tools.baseline.illustrative_probe import PageText, digest


def marked_text(painted: str, replacement: str) -> bytes:
    # Author-controlled synthetic strings only, escaped as PDF literal strings.
    literal = painted.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    encoded = (b'\xfe\xff' + replacement.encode('utf-16-be')).hex().encode()
    return b'/Span << /ActualText <' + encoded + b'> >> BDC (' + literal.encode('ascii') + b') Tj EMC'


def fixtures() -> dict:
    prefix = b'BT /F1 12 Tf 50 780 Td '
    return {
        'ordinary-hyphen': (make_pdf(prefix + b'(Alpha-Beta) Tj ET'), 'Alpha-Beta', 'Alpha-Beta'),
        'actualtext-hyphen': (make_pdf(prefix + b'(Alpha) Tj ' + marked_text('-', '\u2011') + b' (Beta) Tj ET'), 'Alpha\u2011Beta', 'Alpha-Beta'),
        'tounicode-hyphen': (make_pdf(prefix + b'(Alpha-Beta) Tj ET', unicode_map=UNICODE_MAP.replace(b'<31> <0031>', b'<2D> <2011>')), 'Alpha\u2011Beta', 'Alpha\u2011Beta'),
        'actualtext-identical': (make_pdf(prefix + marked_text('12.34', '12.34') + b' ET'), '12.34', '12.34'),
        'actualtext-conflicting-number': (make_pdf(prefix + marked_text('12.34', '72.34') + b' ET'), '72.34', '12.34'),
    }


def main() -> int:
    pin = built_converter.verify()
    base = ROOT / '.local/qualification/actualtext'
    inputs = base / 'inputs'; inputs.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (data, expected_reference, expected_html) in fixtures().items():
        source = inputs / (name + '.pdf'); source.write_bytes(data)
        output = base / name; output.mkdir(exist_ok=True)
        row = {'case': name, 'source_sha256': digest(source)}
        try:
            reference = sandbox(ROOT / 'tools/baseline', inputs, output, '/usr/bin/pdftotext', '-layout', '/input/' + source.name, '/output/source.txt')
            converted = built_converter.run(inputs, output, '--tounicode', '1', '--dest-dir', '/output', '/input/' + source.name, 'report.html')
            (output / 'worker.log').write_bytes(reference.stderr + converted.stdout + converted.stderr)
            if reference.returncode or converted.returncode:
                raise RuntimeError('processor_failure')
            collector = PageText(); collector.feed((output / 'report.html').read_text())
            extracted = (output / 'source.txt').read_text().strip()
            html = ''.join(''.join(parts) for _, parts in collector.pages).strip()
            row.update(reference_matches_authored=extracted == expected_reference,
                       html_matches_observed_expectation=html == expected_html,
                       logical_text_preserved=extracted == html,
                       html_sha256=digest(output / 'report.html'))
            row['status'] = 'preserved' if extracted == html else 'semantic_difference'
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            row['status'] = 'unable_to_complete'
        rows.append(row)
    result = {'schema_version': 1, 'scope': 'Public synthetic ActualText regression; mismatches are not approved conversion',
              'converter_sha256': pin['binary_sha256'], 'converter_options': ['--tounicode', '1'],
              'cases': rows, 'production_qualified': False,
              'hypothesis_reproduced': all(r.get('reference_matches_authored') and r.get('html_matches_observed_expectation') for r in rows)}
    (base / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if all(r['status'] == 'preserved' and r.get('reference_matches_authored') for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
