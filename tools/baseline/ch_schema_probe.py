"""Offline, synthetic transport-schema checks, not filing/profile acceptance."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from tools.baseline.ch_schemas import BASE, PIN, ROOT, verify

ENVELOPE = 'http://www.govtalk.gov.uk/CM/envelope'
HEADER = 'http://xmlgw.companieshouse.gov.uk/Header'
STATUS = 'http://xmlgw.companieshouse.gov.uk'


def envelope(value='1', body=''):
    return f'<GovTalkMessage xmlns="{ENVELOPE}"><EnvelopeVersion>1.0</EnvelopeVersion><Header><MessageDetails><Class>FormSubmission</Class><Qualifier>request</Qualifier><GatewayTest>{value}</GatewayTest></MessageDetails></Header><GovTalkDetails/><Body>{body}</Body></GovTalkMessage>'


def submission():
    # Deliberately not accounts, with no presenter/company credentials. XSD accepts
    # base64 bytes without validating their business meaning or iXBRL content.
    data = base64.b64encode(b'<synthetic-not-accounts/>').decode()
    return f'<FormSubmission xmlns="{HEADER}"><FormHeader><CompanyNumber>0</CompanyNumber><CompanyType>EW</CompanyType><CompanyName>SYNTHETIC NOT FOR FILING</CompanyName><PackageReference>SYNTHETIC</PackageReference><Language>EN</Language><FormIdentifier>Accounts</FormIdentifier><SubmissionNumber>T00001</SubmissionNumber></FormHeader><DateSigned>2026-09-29</DateSigned><Form/><Document><Data>{data}</Data><ContentType>application/xml</ContentType><Category>ACCOUNTS</Category></Document></FormSubmission>'


def cases():
    body = submission()
    rows = [('gateway-' + value, 'envelope', envelope(value), expected)
            for value, expected in [('1', True), ('0', True), ('2', True), ('true', False), ('false', False)]]
    rows += [('wrapper-synthetic-bytes', 'submission', body, True),
             ('wrapper-short-number', 'submission', body.replace('T00001', 'T0001'), False),
             ('wrapper-invalid-alphabet-libxml', 'submission', body.replace('<Data>', '<Data>!'), True),
             ('wrapper-truncated-base64', 'submission', body.replace('</Data>', 'A</Data>'), False),
             ('wrapper-missing-date', 'submission', body.replace('<DateSigned>2026-09-29</DateSigned>', ''), False),
             ('wrapper-wrong-namespace', 'submission', body.replace(HEADER, 'urn:wrong'), False),
             ('envelope-lax-invalid-wrapper', 'envelope', envelope(body=body.replace('T00001', 'T0001')), True),
             ('envelope-lax-unknown-body', 'envelope', envelope(body='<unknown xmlns="urn:synthetic"/>'), True)]
    for code in ('EW', 'SC', 'NI', 'R', 'OC', 'SO', 'NC', 'ZZ'):
        rows.append(('company-type-' + code, 'submission', body.replace('<CompanyType>EW', '<CompanyType>' + code), code != 'ZZ'))
    rows += [('poll-by-submission', 'status', f'<GetSubmissionStatus xmlns="{STATUS}"><SubmissionNumber>T00001</SubmissionNumber><PresenterID>SYNTHETIC</PresenterID></GetSubmissionStatus>', True)]
    for code in ('ACCEPT', 'REJECT', 'PENDING', 'PARKED', 'INTERNAL_FAILURE', 'UNKNOWN'):
        rows.append(('status-' + code.lower(), 'status', f'<SubmissionStatus xmlns="{STATUS}"><Status><SubmissionNumber>T00001</SubmissionNumber><StatusCode>{code}</StatusCode></Status></SubmissionStatus>', code != 'UNKNOWN'))
    rows += [('status-ack', 'status_ack', f'<StatusAck xmlns="{STATUS}"/>', True),
             ('wrong-status-ack-name', 'status_ack', f'<GetStatusAck xmlns="{STATUS}"/>', False)]
    return rows


def strict_base64(value: str) -> bool:
    # Permit XML whitespace, then require canonical encoding. No decoded report
    # bytes are emitted or used as a claim that the attachment is valid iXBRL.
    compact = value.translate(str.maketrans('', '', ' \t\r\n'))
    if len(compact) > 40_000_000:
        return False
    try:
        decoded = base64.b64decode(compact, validate=True)
        return len(decoded) <= 30_000_000 and base64.b64encode(decoded).decode() == compact
    except (ValueError, UnicodeError):
        return False


def worker():
    from lxml import etree
    pins = json.loads(PIN.read_text())
    files = verify(pins, BASE)
    permitted = set(files.values())

    class LocalOnly(etree.Resolver):
        def resolve(self, url, public_id, context):
            parts = urlsplit(url)
            if parts.scheme not in ('', 'file') or parts.netloc or parts.query or parts.fragment:
                raise OSError('External schema resolution refused')
            path = Path(unquote(parts.path)).resolve()
            if path not in permitted:
                raise OSError('Unpinned schema resolution refused')
            return self.resolve_filename(str(path), context)

    parser = etree.XMLParser(no_network=True, resolve_entities=False, load_dtd=False)
    parser.resolvers.add(LocalOnly())
    schemas = {name: etree.XMLSchema(etree.parse(str(files[path]), parser)) for name, path in pins['roots'].items()}
    results = []
    for name, schema, xml, expected in cases():
        doc = etree.fromstring(xml.encode(), parser)
        actual = schemas[schema].validate(doc)
        attachments = doc.findall('.//{' + HEADER + '}Data')
        base64_ok = all(strict_base64(e.text or '') for e in attachments) if attachments else None
        expected_base64 = None if not attachments else name not in ('wrapper-invalid-alphabet-libxml', 'wrapper-truncated-base64')
        results.append({'case': name, 'schema': schema, 'schema_valid': actual, 'expected_schema_valid': expected,
                        'expectation_met': actual == expected and base64_ok == expected_base64, 'strict_base64_valid': base64_ok, 'expected_strict_base64_valid': expected_base64,
                        'codes': sorted({error.type_name for error in schemas[schema].error_log})})
    return {'schema_version': 1, 'status': 'schema_checks_pass' if all(r['expectation_met'] for r in results) else 'unexpected_result',
            'scope': 'Synthetic XSD transport validation only; no valid accounts or authenticated submission',
            'network': 'OS network namespace disabled; pinned local resolver; no_network parser',
            'pin_sha256': hashlib.sha256(PIN.read_bytes()).hexdigest(), 'compiled_roots': len(schemas),
            'verified_files': len(files), 'lxml_version': list(etree.LXML_VERSION), 'libxml_version': list(etree.LIBXML_VERSION),
            'validator_binary_sha256': hashlib.sha256(Path(etree.__file__).read_bytes()).hexdigest(),
            'cases': results, 'submission_attempted': False, 'production_qualified': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(), indent=2)); return 0
    output = ROOT / '.local/qualification/ch-schemas'; output.mkdir(parents=True, exist_ok=True)
    command = ['unshare', '--user', '--map-root-user', '--net', '--', sys.executable, '-m', 'tools.baseline.ch_schema_probe', '--worker']
    env = {key: value for key, value in os.environ.items() if key in ('PATH', 'LANG', 'LC_ALL')}
    try:
        run = subprocess.run(command, env=env, capture_output=True, timeout=30, cwd=ROOT)
        (output / 'worker.log').write_bytes(run.stderr)
        result = json.loads(run.stdout) if run.returncode == 0 else {'status': 'unable_to_complete', 'reason': 'schema_worker_failed'}
    except (subprocess.TimeoutExpired, ValueError):
        result = {'status': 'unable_to_complete', 'reason': 'worker_timeout_or_invalid_result'}
    result.update(production_qualified=False, submission_attempted=False)
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'cases'} | {'cases': len(result.get('cases', []))}, indent=2))
    return 0 if result['status'] == 'schema_checks_pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
