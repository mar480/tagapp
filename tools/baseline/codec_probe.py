"""Compare identical synthetic Flate and JPEG2000 images in the pinned converter."""
from __future__ import annotations

import argparse
import base64
from html.parser import HTMLParser
from io import BytesIO
import json
from pathlib import Path
import subprocess
import tempfile
import zlib

from tools.baseline.conversion_probe import ARTIFACT_SHA256, ROOT, sandbox
from tools.baseline.illustrative_probe import digest


def image_pdf(encoded: bytes, filter_name: str) -> bytes:
    if filter_name not in ('FlateDecode', 'JPXDecode'):
        raise ValueError('Unsupported synthetic encoding')
    drawing = b'q 200 0 0 200 20 20 cm /Im1 Do Q'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 240 240] /Resources << /XObject << /Im1 5 0 R >> >> /Contents 4 0 R >>',
               b'<< /Length ' + str(len(drawing)).encode() + b' >>\nstream\n' + drawing + b'\nendstream',
               b'<< /Type /XObject /Subtype /Image /Width 8 /Height 8 /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /' + filter_name.encode() + b' /Length ' + str(len(encoded)).encode() + b' >>\nstream\n' + encoded + b'\nendstream']
    output = bytearray(b'%PDF-1.5\n'); offsets = [0]
    for n, obj in enumerate(objects, 1):
        offsets.append(len(output)); output.extend(f'{n} 0 obj\n'.encode() + obj + b'\nendobj\n')
    start = len(output)
    output.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        output.extend(f'{offset:010d} 00000 n \n'.encode())
    output.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
    return bytes(output)


class Backgrounds(HTMLParser):
    def __init__(self):
        super().__init__(); self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img' and 'bi' in attrs.get('class', '').split():
            value = attrs.get('src', '')
            if value.startswith('data:image/png;base64,'):
                self.images.append(base64.b64decode(value.split(',', 1)[1], validate=True))


def dark_pixels(image) -> int:
    return sum(image.convert('L').histogram()[:128])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', choices=('appimage', 'sourcebuild'), default='appimage')
    args = parser.parse_args()
    sourcebuild = args.runtime == 'sourcebuild'
    converter_hash = ARTIFACT_SHA256
    if sourcebuild:
        from tools.baseline import built_converter
        converter_hash = built_converter.verify()['binary_sha256']
    from PIL import Image, features
    if not features.check_codec('jpg_2000'):
        raise SystemExit('Local JPEG2000 encoder unavailable')
    pixels = bytes(0 if (x // 2 + y // 2) % 2 else 255 for y in range(8) for x in range(8))
    buffer = BytesIO()
    Image.frombytes('L', (8, 8), pixels).save(buffer, format='JPEG2000', irreversible=False)
    if Image.open(BytesIO(buffer.getvalue())).tobytes() != pixels:
        raise SystemExit('Synthetic codec round-trip failed')
    base = ROOT / ('.local/qualification/image-codecs-sourcebuild' if sourcebuild else '.local/qualification/image-codecs')
    inputs = base / 'inputs'; inputs.mkdir(parents=True, exist_ok=True)
    archive = ROOT / '.local/downloads/pdf2htmlEX-0.18.8.rc1-focal.AppImage'
    if not sourcebuild and digest(archive) != ARTIFACT_SHA256:
        raise SystemExit('Converter checksum mismatch')
    rows = []
    with tempfile.TemporaryDirectory(dir=base) as temporary:
        runtime = ROOT / 'tools/baseline' if sourcebuild else Path(temporary) / 'runtime'
        if not sourcebuild:
            subprocess.run(['unsquashfs', '-no-progress', '-o', '188392', '-d', str(runtime), str(archive)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for label, encoded in [('FlateDecode', zlib.compress(pixels)), ('JPXDecode', buffer.getvalue())]:
            pdf = inputs / (label + '.pdf'); pdf.write_bytes(image_pdf(encoded, label))
            output = base / label; output.mkdir(exist_ok=True)
            source = sandbox(runtime, inputs, output, '/usr/bin/pdftoppm', '-singlefile', '-r', '72', '-png', '/input/' + pdf.name, '/output/source')
            options = ['--dest-dir', '/output', '/input/' + pdf.name, 'report.html']
            converted = built_converter.run(inputs, output, *options) if sourcebuild else sandbox(runtime, inputs, output, '/app/AppRun', *options)
            (output / 'converter.log').write_bytes(converted.stdout + converted.stderr)
            if source.returncode or converted.returncode:
                rows.append({'codec': label, 'status': 'unable_to_complete'}); continue
            parser = Backgrounds(); parser.feed((output / 'report.html').read_text())
            source_ink = dark_pixels(Image.open(output / 'source.png'))
            background_ink = sum(dark_pixels(Image.open(BytesIO(raw))) for raw in parser.images)
            rows.append({'codec': label, 'pdf_sha256': digest(pdf), 'source_dark_pixels': source_ink,
                         'background_dark_pixels': background_ink, 'background_images': len(parser.images),
                         'status': 'image_present' if source_ink > 10000 and background_ink > 10000 else 'image_missing'})
    result = {'schema_version': 1, 'scope': 'Synthetic image-presence regression, not visual conformance',
              'converter_sha256': converter_hash, 'runtime': args.runtime, 'decoded_source_pixels_identical': True, 'cases': rows,
              'production_qualified': False}
    (base / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if all(r['status'] == 'image_present' for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
