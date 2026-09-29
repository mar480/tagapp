"""Execute inside the build userspace after compilation; output build metadata."""
import hashlib
import json
from pathlib import Path
import re
import subprocess


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    executable = Path('/usr/local/bin/pdf2htmlEX')
    dependencies = subprocess.check_output(['ldd', str(executable)], text=True)
    if 'not found' in dependencies:
        raise SystemExit('Missing runtime library')
    paths = {str(executable), *re.findall(r'(/\S+)\s+\(', dependencies)}
    for directory in ('/usr/local/share/pdf2htmlEX', '/etc/fonts', '/usr/share/fonts', '/usr/share/fontconfig'):
        paths.update(str(p) for p in Path(directory).rglob('*') if p.is_file())
    version = subprocess.run([str(executable), '-v'], capture_output=True, text=True, check=True)
    manifest = Path('/build/installed-packages.tsv')
    result = {'schema_version': 1, 'id': 'pdf2htmlex-openjpeg-20260929',
              'pdf2htmlex_commit': 'cb7806aecbbee435e086be248fa068fbe3dc24c9',
              'binary_sha256': digest(executable), 'version_output': (version.stdout + version.stderr).strip(),
              'runtime_files': {name: digest(name) for name in sorted(paths)},
              'package_manifest_sha256': digest(manifest), 'production_qualified': False,
              'scope': 'Locally built qualification candidate; no redistribution or production approval'}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
