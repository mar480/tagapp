"""Run local rendering/selection diagnostics with report data kept offline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import shutil
import subprocess

from tools.baseline.illustrative_probe import ROOT, digest

BASE = ROOT / '.local/qualification/gt-frs102/browser'
INPUT = ROOT / '.local/qualification/gt-frs102/converted-force-tounicode'
DEPS = ROOT / '.local/tools/browser-probe'


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))


def worker_args(inputs: Path, output: Path, pages: list[int], *, diagnose=False, controls_only=False) -> list[str]:
    node = Path(shutil.which('node') or '/missing').resolve()
    args = ['bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--cap-drop', 'ALL']
    for directory in ('/usr', '/lib', '/lib64', '/etc/fonts'):
        if Path(directory).exists():
            args += ['--ro-bind', directory, directory]
    args += ['--ro-bind', str(node.parent), '/node', '--ro-bind', str(DEPS), '/deps',
             '--ro-bind', str(ROOT / 'tools/baseline/browser_probe.cjs'), '/probe.cjs',
             '--ro-bind', str(inputs), '/input', '--bind', str(output), '/output',
             '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/dev/shm', '--tmpfs', '/tmp', '--dir', '/home',
             '--clearenv', '--setenv', 'HOME', '/home', '--setenv', 'PATH', '/node:/usr/bin',
             '--setenv', 'LANG', 'C.UTF-8', '--setenv', 'PLAYWRIGHT_BROWSERS_PATH', '/deps/browsers',
             '--setenv', 'PROBE_CONTROL_ONLY', '1' if controls_only else '0',
             '--setenv', 'PROBE_DIAGNOSE_SELECTION', '1' if diagnose else '0',
             '--setenv', 'PROBE_PAGES', ','.join(map(str, pages)), '--chdir', '/output', '--', '/node/node', '/probe.cjs']
    return args


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=('png', 'svg-page1', 'sourcebuild-page1', 'sourcebuild'), default='png')
    parser.add_argument('--diagnose-selection', action='store_true', help='Keep separate evidence; inspect caret boundaries without reconversion')
    parser.add_argument('--pages', type=int, nargs='+', help='Limit diagnostic pages (1..108)')
    parser.add_argument('--synthetic-only', action='store_true', help='Run public selection controls without loading any report')
    args = parser.parse_args()
    if args.synthetic_only:
        args.diagnose_selection = True
        if args.pages:
            parser.error('--synthetic-only cannot select report pages')
    if args.pages and (not args.diagnose_selection or any(p < 1 or p > 108 for p in args.pages)):
        parser.error('--pages requires --diagnose-selection and page numbers 1..108')
    candidates = {
        'png': (INPUT, BASE, False),
        'svg-page1': (INPUT.parent / 'background-svg-page1', BASE.parent / 'browser-svg-page1', True),
        'sourcebuild-page1': (INPUT.parent / 'sourcebuild-page1', BASE.parent / 'browser-sourcebuild-page1', True),
        'sourcebuild': (INPUT.parent / 'sourcebuild', BASE.parent / 'browser-sourcebuild', False),
    }
    inputs, base, first_page_only = candidates[args.candidate]
    pages = [1] if first_page_only else [1, 6, 7, 21, 32, 33, 34, 35, 36, 37, 38, 43, 63, 65, 78, 82, 85, 108]
    if args.diagnose_selection:
        base = base.with_name(base.name + '-selection' + ('-pages-' + '-'.join(map(str,args.pages)) if args.pages else ''))
        pages = args.pages or pages
    if args.synthetic_only:
        inputs = ROOT / 'tools/baseline'
        base = ROOT / '.local/qualification/selection-control'
        pages = []
        previous = {'html_sha256': None}
        fixture = {'sha256': None}
    else:
        previous = json.loads((inputs / 'result.json').read_text())
        fixture = json.loads((ROOT / 'docs/qualification/fixture-registry.json').read_text())['fixtures'][0]
        if previous['source_sha256'] != fixture['sha256']:
            raise SystemExit('Conversion source does not match registered fixture')
        if digest(inputs / 'report.html') != previous['html_sha256'] or digest(ROOT / fixture['source_path']) != fixture['sha256']:
            raise SystemExit('Fixture/conversion checksum mismatch; browser not started')
    package = json.loads((DEPS / 'node_modules/playwright/package.json').read_text())
    if package['version'] != '1.63.0':
        raise SystemExit('Browser harness dependency pin mismatch')
    pins = json.loads((ROOT / 'docs/qualification/browser-tool-pins.json').read_text())
    if digest(DEPS / 'package-lock.json') != pins['package_lock_sha256'] or digest(DEPS / pins['browser']['binary_relative_path']) != pins['browser']['binary_sha256']:
        raise SystemExit('Browser dependency checksum mismatch')
    harness_hash = digest(ROOT / 'tools/baseline/browser_probe.cjs')
    base.mkdir(parents=True, exist_ok=True)
    target = base / 'browser-result.json'
    target.unlink(missing_ok=True)
    try:
        proc = subprocess.run(worker_args(inputs, base, pages, diagnose=args.diagnose_selection, controls_only=args.synthetic_only), capture_output=True, timeout=240, preexec_fn=limits)
        (base / 'worker.log').write_bytes(proc.stdout + proc.stderr)
        if proc.returncode or not target.exists():
            result = {'status': 'unable_to_complete', 'reason': 'browser_worker_failed'}
        else:
            result = json.loads(target.read_text())
    except subprocess.TimeoutExpired:
        result = {'status': 'unable_to_complete', 'reason': 'browser_timeout'}
    if digest(ROOT / 'tools/baseline/browser_probe.cjs') != harness_hash:
        result = {'status': 'unable_to_complete', 'reason': 'harness_changed_during_run'}
    result.update(candidate='synthetic' if args.synthetic_only else args.candidate, source_pdf_sha256=fixture['sha256'], html_sha256=previous['html_sha256'],
                  harness_sha256=harness_hash, production_qualified=False)
    target.write_text(json.dumps(result, indent=2) + '\n')
    # Browser result contains counts/coordinates only, never selections or logs.
    print(json.dumps({**{k: v for k, v in result.items() if k not in ('pages', 'selection_diagnostics')},
                      'sampled_pages': len({p['page'] for p in result.get('pages', [])}),
                      'pointer_samples': sum(p['pointer_samples'] for p in result.get('pages', [])),
                      'pointer_matches': sum(p['pointer_matches'] for p in result.get('pages', []))}, indent=2))
    return 0 if result['status'] in ('sampled_pointer_checks_pass', 'synthetic_selection_checks_pass') else 1


if __name__ == '__main__':
    raise SystemExit(main())
