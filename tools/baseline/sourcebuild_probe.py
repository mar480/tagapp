"""Qualify the built converter: codec gate, one report page, then full report."""
from __future__ import annotations

import argparse
import json
import subprocess
import time

from tools.baseline import built_converter
from tools.baseline.conversion_probe import ROOT, sandbox
from tools.baseline.illustrative_probe import compare, digest, public_summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    pins = built_converter.verify()
    gate = json.loads((ROOT / '.local/qualification/image-codecs-sourcebuild/result.json').read_text())
    if gate['converter_sha256'] != pins['binary_sha256'] or len(gate['cases']) != 2 or any(c['status'] != 'image_present' for c in gate['cases']):
        raise SystemExit('Synthetic codec gate has not passed for this build')
    fixture = json.loads((ROOT / 'docs/qualification/fixture-registry.json').read_text())['fixtures'][0]
    source = ROOT / fixture['source_path']
    if digest(source) != fixture['sha256']:
        raise SystemExit('Source checksum mismatch')
    base = ROOT / '.local/qualification/gt-frs102'
    if args.full:
        previous = json.loads((base / 'sourcebuild-page1/result.json').read_text())
        if previous['converter_sha256'] != pins['binary_sha256'] or previous['status'] != 'text_checks_pass_visual_review_pending':
            raise SystemExit('First-page text check must pass before the full report')
    output = base / ('sourcebuild' if args.full else 'sourcebuild-page1'); output.mkdir(exist_ok=True)
    options = ['--tounicode', '1'] + ([] if args.full else ['--first-page', '1', '--last-page', '1'])
    pdftext = [] if args.full else ['-f', '1', '-l', '1']
    result = {'schema_version': 1, 'fixture': fixture['id'], 'source_sha256': fixture['sha256'],
              'converter_sha256': pins['binary_sha256'], 'converter_options': options,
              'runtime': pins['id'], 'production_qualified': False}
    try:
        extracted = sandbox(ROOT / 'tools/baseline', source.parent, output, '/usr/bin/pdftotext', '-layout', *pdftext, '/input/' + source.name, '/output/source.txt')
        started = time.monotonic()
        converted = built_converter.run(source.parent, output, *options, '--dest-dir', '/output', '/input/' + source.name, 'report.html')
        result.update(converter_exit_code=converted.returncode, reference_exit_code=extracted.returncode, converter_wall_seconds=round(time.monotonic() - started, 3), resource_limits={'cpu_seconds': 180, 'wall_seconds': 240, 'address_space_bytes': 2 * 1024**3, 'output_file_bytes': 128 * 1024**2})
        (output / 'converter.log').write_bytes(extracted.stderr + converted.stdout + converted.stderr)
        if extracted.returncode or converted.returncode:
            raise RuntimeError('processor_failure')
        comparison, differences = compare((output / 'source.txt').read_text(), (output / 'report.html').read_text(), fixture['pages'] if args.full else 1)
        result.update(comparison, html_sha256=digest(output / 'report.html'), source_text_sha256=digest(output / 'source.txt'))
        (output / 'private-differences.json').write_text(json.dumps(differences, indent=2) + '\n')
    except subprocess.TimeoutExpired:
        result.update(status='unable_to_complete', reason='wall_time_limit')
    except (RuntimeError, OSError):
        result.update(status='unable_to_complete', reason='processor_or_resource_failure')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(public_summary(result), indent=2))
    return 0 if result['status'] == 'text_checks_pass_visual_review_pending' else 1


if __name__ == '__main__':
    raise SystemExit(main())
