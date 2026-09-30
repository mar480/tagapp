"""Bounded intake and offline execution of pinned official XBRL suite data."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import platform
import resource
import re
import stat
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from tools.baseline.acquire import store_verified
from tools.baseline.check import ROOT

PIN = ROOT / 'docs/compliance/xbrl-conformance-pins.json'
BASE = ROOT / '.local/qualification/xbrl-conformance'


def member_path(name):
    if (not name or name.startswith('/') or any(c in name for c in ('\\', ':', '%', '?', '#'))
            or any(p in ('', '.', '..') for p in name.split('/')) or any(ord(c) < 32 for c in name)):
        raise ValueError('Unsafe archive member path')
    return name


def control_xml(data):
    data.decode('utf-8-sig')
    if b'\0' in data:
        raise ValueError('Only UTF-8 suite control XML is supported')
    if re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b', data, re.IGNORECASE):
        raise ValueError('Declarations forbidden in suite control documents')
    return ET.fromstring(data)


def inspect_suite(path: Path, entry_point: str):
    with ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 10_000 or sum(e.file_size for e in entries) > 200_000_000:
            raise ValueError('Suite archive resource limit exceeded')
        names = set()
        for e in entries:
            name = member_path(e.filename.rstrip('/'))
            if name in names:
                raise ValueError('Duplicate archive member')
            names.add(name)
            if stat.S_IFMT(e.external_attr >> 16) not in (0, stat.S_IFREG, stat.S_IFDIR) or e.flag_bits & 1:
                raise ValueError('Archive link, special or encrypted member')
            if e.file_size > 50_000_000 or e.file_size > max(1, e.compress_size) * 1000:
                raise ValueError('Suite member resource limit exceeded')
        if archive.testzip() is not None:
            raise ValueError('Suite CRC failure')
        index = control_xml(archive.read(member_path(entry_point)))
        testcase_paths = []
        for group in index.iter():
            if group.tag.rsplit('}', 1)[-1] != 'testcases':
                continue
            root = group.get('root', '')
            if root.startswith('/') or ':' in root:
                raise ValueError('External testcase root')
            base = posixpath.join(str(PurePosixPath(entry_point).parent), root)
            for child in group:
                if child.tag.rsplit('}', 1)[-1] == 'testcase':
                    raw = child.get('uri', '')
                    # The selected official indexes use only relative references.
                    if raw.startswith('/') or ':' in raw:
                        raise ValueError('External testcase reference')
                    name = member_path(posixpath.normpath(posixpath.join(base, raw)))
                    if name not in names:
                        raise ValueError('Missing referenced testcase')
                    testcase_paths.append(name)
        if not testcase_paths or len(set(testcase_paths)) != len(testcase_paths):
            raise ValueError('Empty or duplicate suite index')
        variations = 0
        for name in testcase_paths:
            case = control_xml(archive.read(name))
            variations += sum(e.tag.rsplit('}', 1)[-1] == 'variation' for e in case.iter())
        if not variations:
            raise ValueError('No suite variations found')
        return {'entry_point': entry_point, 'members': len(entries), 'expanded_bytes': sum(e.file_size for e in entries),
                'testcase_files': len(testcase_paths), 'expected_variations': variations, 'crc': 'passed'}


def verify(item):
    path = BASE / 'downloads' / item['filename']
    if Path(item['filename']).name != item['filename']:
        raise ValueError('Unsafe download name')
    if path.stat().st_size != item['size_bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('Conformance artifact checksum mismatch')
    return path


def prepare_inline_support(item):
    pins = json.loads(PIN.read_text())
    support = pins['inline_support']
    with ZipFile(verify(item)) as archive:
        data = archive.read(member_path(support['nested_member']))
    if len(data) != support['size_bytes'] or hashlib.sha256(data).hexdigest() != support['sha256']:
        raise ValueError('Nested test taxonomy differs from pin')
    destination = BASE / 'downloads' / support['filename']
    if not destination.exists():
        destination.write_bytes(data)
    package = verify(support)
    with ZipFile(package) as archive:
        if archive.testzip() is not None:
            raise ValueError('Nested test taxonomy CRC failure')
        names = set()
        for entry in archive.infolist():
            name = member_path(entry.filename.rstrip('/'))
            if name in names or stat.S_IFMT(entry.external_attr >> 16) not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError('Unsafe nested test taxonomy member')
            names.add(name)
    adapter = verify(next(p for p in pins['support_artifacts'] if p['filename'] == 'testcaseIxExpectedHtmlFixup.py'))
    return package, adapter


def summarize_report(path, expected, exit_code, expected_keys=None):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not {'Id', 'Status', 'Testcase'} <= set(reader.fieldnames or []):
            raise ValueError('Unexpected processor report columns')
        rows = [r for r in reader if r.get('Id')]
    if expected_keys is not None:
        keys = set(expected_keys)
        if len(keys) != expected:
            raise ValueError('Duplicate or incorrect expected variation keys')
        rows = [r for r in rows if (r['Testcase'], r['Id']) in keys]
    counts = Counter(r['Status'] for r in rows)
    identifiers = [(r['Testcase'], r['Id']) for r in rows]
    complete = (len(rows) == expected and exit_code == 0
                and all(case and ident for case, ident in identifiers)
                and len(set(identifiers)) == len(identifiers))
    return {'status': 'passed' if complete and counts == {'pass': expected} else 'review_required' if complete else 'unable_to_complete',
            'reported_variations': len(rows), 'expected_variations': expected, 'counts': dict(counts),
            'nonpassing': [{'testcase': r['Testcase'], 'id': r['Id'], 'status': r['Status'],
                            'expected': r.get('Expected'), 'actual': r.get('Actual')} for r in rows if r['Status'] != 'pass']}


def inline_groups(path, entry_point):
    """Partition the pinned Inline index without rewriting any test data."""
    groups = {}
    with ZipFile(path) as archive:
        index = control_xml(archive.read(entry_point))
        for node in index.iter():
            if node.tag.rsplit('}', 1)[-1] != 'testcase':
                continue
            relative = member_path(node.get('uri', ''))
            group = relative.split('/')[0]
            if not re.fullmatch('[A-Za-z]+', group):
                raise ValueError('Unexpected Inline testcase group')
            case = control_xml(archive.read(str(PurePosixPath(entry_point).parent / 'tests' / relative)))
            for variation in case.iter():
                if variation.tag.rsplit('}', 1)[-1] == 'variation':
                    key = (PurePosixPath(relative).name, variation.get('id') or variation.get('name'))
                    if not key[1]:
                        raise ValueError('Missing variation identifier')
                    groups.setdefault(group, []).append(key)
    keys = [key for group in groups.values() for key in group]
    if not keys or len(keys) != len(set(keys)):
        raise ValueError('Empty or duplicate Inline variation keys')
    return groups


def summarize_inline_groups(item, expected_count):
    groups = inline_groups(verify(item), item['entry_point'])
    if sum(len(keys) for keys in groups.values()) != expected_count:
        raise ValueError('Grouped inventory differs from suite inventory')
    results = []
    counts = Counter()
    for group, keys in groups.items():
        folder = BASE / item['id'] / 'groups' / group
        try:
            record = json.loads((folder / 'result.json').read_text())
            if (record['suite_sha256'] != item['sha256'] or record.get('group') != group
                    or record['processor_version'] != '2.44.1'):
                raise ValueError('Group provenance mismatch')
            result = summarize_report(folder / 'report.csv', len(keys), record['processor_exit_code'], keys)
            result['report_sha256'] = hashlib.sha256((folder / 'report.csv').read_bytes()).hexdigest()
            result['wall_seconds'] = record['wall_seconds']
        except (OSError, ValueError, KeyError):
            result = {'status': 'unable_to_complete', 'expected_variations': len(keys)}
        counts.update(result.get('counts', {}))
        results.append({'group': group, **result})
    complete = all(r['status'] != 'unable_to_complete' for r in results)
    result = {'suite': item['id'], 'suite_sha256': item['sha256'], 'execution': 'indexed groups',
              'status': 'passed' if all(r['status'] == 'passed' for r in results) else
                        'review_required' if complete else 'unable_to_complete',
              'expected_variations': sum(len(keys) for keys in groups.values()),
              'reported_variations': sum(r.get('reported_variations', 0) for r in results),
              'counts': dict(counts), 'groups': results, 'production_qualified': False}
    (BASE / item['id'] / 'grouped-result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def processor_fingerprint():
    """Identify installed processor code/resources without copying third-party bytes."""
    dist = importlib.metadata.distribution('arelle-release')
    files = []
    for relative in sorted(dist.files or (), key=str):
        name = str(relative)
        if not name.startswith('arelle/') or '__pycache__' in relative.parts or name.endswith('.pyc'):
            continue
        data = Path(dist.locate_file(relative)).read_bytes()
        files.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    if not files:
        raise ValueError('Missing processor distribution file list')
    payload = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
    return {'package_files_sha256': hashlib.sha256(payload).hexdigest(), 'file_count': len(files),
            'method': 'sorted arelle/ distribution files, excluding pycache; compact sorted-key JSON path/bytes/sha256',
            'python_version': platform.python_version(),
            'dependency_versions': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()
                                    if d.metadata['Name'] and d.metadata['Name'].lower() in
                                    ('lxml', 'xmlschema', 'elementpath', 'regex', 'isodate', 'pillow', 'numpy')}}


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))


def run_suite(item, inventory, group=None, expected_keys=None):
    if importlib.metadata.version('arelle-release') != '2.44.1':
        raise ValueError('Requalify before changing the Arelle version')
    path = verify(item)
    fingerprint = processor_fingerprint()
    output = BASE / item['id']
    if group:
        output = output / 'groups' / group
    output.mkdir(parents=True, exist_ok=True)
    report = output / 'report.csv'; report.unlink(missing_ok=True)
    log = output / 'log.xml'; log.unlink(missing_ok=True)
    args = ['unshare', '--user', '--map-root-user', '--net', '--', sys.executable, '-m', 'arelle.CntlrCmdLine',
            '--file', str(path) + '/' + item['entry_point'], '--validate', '--formula', 'none',
            '--internetConnectivity', 'offline', '--disablePersistentConfig', '--xdgConfigHome', str(output / 'config'),
            '--testReport', str(report), '--testReportCols', 'Testcase,Id,Status,Expected,Actual', '--logFile', str(log)]
    if group:
        args += ['--testcaseFilter', f'*/tests/{group}/*.xml:*']
    if item['id'] == 'core-suite':
        args += ['--calc', 'xbrl21']
    if item['id'] == 'inline-suite':
        package, adapter = prepare_inline_support(item)
        args += ['--packages', str(package), '--plugins', 'inlineXbrlDocumentSet|' + str(adapter)]
    started = time.monotonic()
    env = {k: v for k, v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL')}
    env['HOME'] = str(output)
    try:
        with (output / 'worker.log').open('wb') as worker_output:
            run = subprocess.run(args, env=env, stdout=worker_output, stderr=subprocess.STDOUT,
                                 timeout=720, preexec_fn=limits)
        if report.exists():
            result = summarize_report(report, len(expected_keys) if expected_keys is not None else inventory['expected_variations'],
                                      run.returncode, expected_keys)
        else:
            result = {'status': 'unable_to_complete', 'reason': 'missing_processor_report'}
        result['processor_exit_code'] = run.returncode
    except (OSError, ValueError, subprocess.TimeoutExpired):
        result = {'status': 'unable_to_complete', 'reason': 'processor_timeout_or_incomplete_report'}
    result.update(suite=item['id'], group=group, suite_sha256=item['sha256'], entry_point=item['entry_point'],
                  processor='arelle-release', processor_version='2.44.1', processor_environment=fingerprint,
                  options=args[args.index('--validate'):], wall_seconds=round(time.monotonic() - started, 3),
                  network='OS network namespace disabled; Arelle offline',
                  resource_limits={'cpu_seconds': 600, 'wall_seconds': 720, 'address_space_bytes': 3 * 1024**3,
                                   'file_bytes': 128 * 1024**2}, production_qualified=False)
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('nonpassing', 'options')}, indent=2))
    return result['status'] == 'passed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--run', choices=('core', 'dimensions', 'inline'))
    parser.add_argument('--acquire', action='store_true')
    parser.add_argument('--inline-group', help='One exact group from the pinned Inline suite index')
    action.add_argument('--summarize-inline', action='store_true')
    action.add_argument('--list-inline-groups', action='store_true')
    args = parser.parse_args()
    if args.inline_group and args.run != 'inline':
        parser.error('--inline-group requires --run inline')
    pins = json.loads(PIN.read_text())
    inventory = {}
    for item in [*pins['artifacts'], *pins.get('support_artifacts', [])]:
        if args.acquire:
            destination = BASE / 'downloads' / item['filename']
            if Path(item['filename']).name != item['filename'] or not item['url'].startswith(('https://www.xbrl.org/', 'https://raw.githubusercontent.com/Arelle/Arelle/2.44.1/')):
                raise ValueError('Unapproved artifact location')
            if not destination.exists():
                with urllib.request.urlopen(item['url'], timeout=30) as response:
                    store_verified(response, destination, size=item['size_bytes'], digest=item['sha256'])
        path = verify(item)
        if 'entry_point' in item:
            inventory[item['id']] = inspect_suite(path, item['entry_point'])
    if not (args.run or args.list_inline_groups):
        (BASE / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    if args.list_inline_groups:
        item = next(p for p in pins['artifacts'] if p['id'] == 'inline-suite')
        print('\n'.join(inline_groups(verify(item), item['entry_point'])))
        return 0
    if args.summarize_inline:
        item = next(p for p in pins['artifacts'] if p['id'] == 'inline-suite')
        result = summarize_inline_groups(item, inventory['inline-suite']['expected_variations'])
        print(json.dumps({k: v for k, v in result.items() if k != 'groups'}, indent=2))
        return 0 if result['status'] == 'passed' else 1
    if args.run:
        item = next(p for p in pins['artifacts'] if p['id'] == args.run + '-suite')
        keys = None
        if args.inline_group:
            groups = inline_groups(verify(item), item['entry_point'])
            if args.inline_group not in groups:
                parser.error('Unknown Inline group')
            keys = groups[args.inline_group]
        return 0 if run_suite(item, inventory[item['id']], args.inline_group, keys) else 1
    print(json.dumps(inventory, indent=2)); return 0


if __name__ == '__main__':
    raise SystemExit(main())
