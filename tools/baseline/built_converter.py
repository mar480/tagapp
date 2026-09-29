"""Run the pinned local source build in its read-only, networkless userspace."""
from __future__ import annotations

import json
import resource
from pathlib import Path
import subprocess

from tools.baseline.conversion_probe import ROOT

ROOTFS = ROOT / '.local/converter-build/rootfs'
PIN = ROOT / 'docs/qualification/converter-build-result.json'


def worker_args(inputs: Path, output: Path, command: list[str]) -> list[str]:
    return ['bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--cap-drop', 'ALL',
            '--ro-bind', str(ROOTFS), '/', '--ro-bind', str(inputs.resolve()), '/input',
            '--bind', str(output.resolve()), '/output', '--proc', '/proc', '--dev', '/dev',
            '--tmpfs', '/tmp', '--tmpfs', '/run', '--clearenv', '--setenv', 'HOME', '/tmp',
            '--setenv', 'PATH', '/usr/local/bin:/usr/bin:/bin', '--setenv', 'LANG', 'C.UTF-8',
            '--chdir', '/output', '--', *command]


def verify() -> dict:
    pins = json.loads(PIN.read_text())
    # Hash inside the namespace: absolute symlinks in the rootfs must never
    # resolve against the host filesystem during verification.
    program = """import hashlib,json,sys
pins=json.load(sys.stdin)
for name,expected in pins['runtime_files'].items():
 with open(name,'rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
 if actual!=expected: raise SystemExit(1)
"""
    output = ROOT / '.local/converter-build/verification'; output.mkdir(exist_ok=True)
    proc = subprocess.run(worker_args(output, output, ['/usr/bin/python3', '-c', program]),
                          input=json.dumps(pins), capture_output=True, text=True, timeout=30)
    if proc.returncode:
        raise ValueError('Source-built converter runtime checksum mismatch')
    return pins


def processing_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))


def run(inputs: Path, output: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(worker_args(inputs, output, ['/usr/local/bin/pdf2htmlEX', *arguments]),
                          capture_output=True, timeout=240, preexec_fn=processing_limits)
