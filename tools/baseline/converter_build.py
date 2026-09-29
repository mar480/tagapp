"""Local, unprivileged build userspace; never mount report inputs during builds."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile

from tools.baseline.illustrative_probe import ROOT, digest

BASE = ROOT / '.local/converter-build'
ROOTFS = BASE / 'rootfs'


def unpack(archive: Path, destination: Path, *, rootfs=False):
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        if sum(m.size for m in members) > 1024**3:
            raise ValueError('Archive expansion limit exceeded')
        for member in members:
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts:
                raise ValueError('Unsafe archive path')
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise ValueError('Special archive member refused')
        # Write regular entries before creating links. Never traverse archive
        # symlinks during extraction; absolute links are allowed only in rootfs.
        for member in members:
            path = destination / member.name
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, path.open('xb') as target:
                    shutil.copyfileobj(source, target)
                path.chmod(member.mode & 0o777)
        for member in members:
            if not (member.issym() or member.islnk()):
                continue
            path = destination / member.name
            if any(p.is_symlink() for p in path.parents if p != destination.parent):
                raise ValueError('Link parent traversal refused')
            path.parent.mkdir(parents=True, exist_ok=True)
            if member.islnk():
                target = destination / member.linkname
                if not target.resolve().is_relative_to(destination.resolve()) or not target.is_file():
                    raise ValueError('Unsafe hard link')
                os.link(target, path)
            else:
                if not rootfs and not (path.parent / member.linkname).resolve().is_relative_to(destination.resolve()):
                    raise ValueError('Source symlink escapes archive')
                path.symlink_to(member.linkname)


def prepare():
    pins = json.loads((ROOT / 'docs/qualification/converter-build-sources.json').read_text())
    for item in pins['archives']:
        archive = BASE / 'downloads' / item['filename']
        if archive.stat().st_size != item['size_bytes'] or digest(archive) != item['sha256']:
            raise ValueError('Build input checksum mismatch')
    unpack(BASE / 'downloads/ubuntu-base.tar.gz', ROOTFS, rootfs=True)
    for directory in ('input', 'output'):
        (ROOTFS / directory).mkdir(exist_ok=True)
    sources = ROOTFS / 'build'; sources.mkdir()
    for name in ('pdf2htmlEX', 'poppler', 'poppler-data', 'fontforge'):
        temporary = sources / ('unpack-' + name)
        archive = BASE / 'downloads' / (name + ('.tar.xz' if name == 'poppler' else '.tar.gz'))
        unpack(archive, temporary)
        children = list(temporary.iterdir())
        if len(children) != 1 or not children[0].is_dir():
            raise ValueError('Unexpected source archive root')
        children[0].rename(sources / name); temporary.rmdir()
    # Prevent package installation from attempting to start services.
    policy = ROOTFS / 'usr/sbin/policy-rc.d'
    policy.write_text('#!/bin/sh\nexit 101\n'); policy.chmod(0o755)
    resolver = ROOTFS / 'etc/resolv.conf'
    resolver.unlink(missing_ok=True)
    resolver.write_text(Path('/etc/resolv.conf').read_text())
    (ROOTFS / 'etc/apt/apt.conf.d/99-local-builder').write_text('APT::Sandbox::User "root";\n')
    print('Build rootfs and pinned sources prepared; host packages unchanged.')


def command_args(command: list[str], *, network: bool) -> list[str]:
    args = ['bwrap', '--unshare-all']
    if network:
        args += ['--share-net']
    args += ['--uid', '0', '--gid', '0', '--die-with-parent', '--new-session',
             '--bind', str(ROOTFS), '/', '--proc', '/proc', '--dev', '/dev',
             '--tmpfs', '/tmp', '--tmpfs', '/run', '--clearenv',
             '--setenv', 'PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', '--setenv', 'HOME', '/root',
             '--setenv', 'LANG', 'C.UTF-8', '--setenv', 'DEBIAN_FRONTEND', 'noninteractive',
             '--ro-bind', str(ROOT / 'tools/baseline/converter_compile.sh'), '/compile.sh',
             '--chdir', '/build', '--', *command]
    return args


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'dependencies', 'configure', 'compile', 'version'))
    args = parser.parse_args()
    if args.phase == 'prepare':
        prepare(); return 0
    commands = {
        'dependencies': ['/bin/sh', '-ec', 'mkdir -p /usr/local/share/fonts && apt-get update && apt-get install -y --no-install-recommends build-essential cmake pkg-config gettext ca-certificates libcairo2-dev libpng-dev libjpeg-dev libxml2-dev libopenjp2-7-dev libfontconfig1-dev libfreetype-dev libglib2.0-dev libltdl-dev liblcms2-dev poppler-utils fonts-dejavu-core'],
        'configure': ['/usr/bin/dpkg', '--configure', '-a'],
        'compile': ['/bin/sh', '/compile.sh'],
        'version': ['/usr/local/bin/pdf2htmlEX', '-v'],
    }
    with (BASE / (args.phase + '.log')).open('wb') as log:
        proc = subprocess.run(command_args(commands[args.phase], network=args.phase == 'dependencies'),
                              stdout=log, stderr=subprocess.STDOUT, timeout=1800)
    print(json.dumps({'phase': args.phase, 'exit_code': proc.returncode, 'log': str(BASE / (args.phase + '.log'))}))
    return proc.returncode


if __name__ == '__main__':
    raise SystemExit(main())
