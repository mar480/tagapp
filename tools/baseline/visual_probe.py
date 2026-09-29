"""Create private PDF/HTML page comparisons; numerical metrics are not approval."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import subprocess
import shutil

from tools.baseline.browser_probe import BASE, ROOT
from tools.baseline.conversion_probe import sandbox
from tools.baseline.illustrative_probe import digest


def compare_images(original, rendered) -> dict:
    from PIL import ImageChops, ImageFilter, ImageStat
    a, b = original.convert('RGB'), rendered.convert('RGB')
    if a.size != b.size:
        return {'status': 'size_mismatch', 'pdf_size': list(a.size), 'html_size': list(b.size)}
    difference = ImageChops.difference(a, b)
    maximum = ImageChops.lighter(ImageChops.lighter(*difference.split()[:2]), difference.split()[2])
    changed = sum(maximum.histogram()[33:])
    # Dark/coloured pixels, with a two-pixel geometric tolerance. This is a
    # diagnostic of missing/displaced ink, not a text or semantic comparator.
    def ink(image):
        r, g, b = image.split()
        return ImageChops.darker(ImageChops.darker(r, g), b).point(lambda p: 255 if p < 220 else 0)
    left, right = ink(a), ink(b)
    absent = ImageChops.subtract(left, right.filter(ImageFilter.MaxFilter(5)))
    added = ImageChops.subtract(right, left.filter(ImageFilter.MaxFilter(5)))
    return {'status': 'measured_review_pending', 'pdf_size': list(a.size), 'html_size': list(b.size),
            'mean_absolute_channel_error': round(sum(ImageStat.Stat(difference).mean) / 3, 4),
            'pixels_differing_over_32_fraction': round(changed / (a.width * a.height), 6),
            'unmatched_pdf_ink_fraction': round(absent.histogram()[255] / max(1, left.histogram()[255]), 6),
            'unmatched_html_ink_fraction': round(added.histogram()[255] / max(1, right.histogram()[255]), 6)}


def review_html(rows: list[dict]) -> str:
    cards = []
    for row in rows:
        n = int(row['page'])
        cards.append(f'<section id="page-{n}"><h2>Page {n}</h2><p>{html.escape(row["status"])}</p>'
                     f'<div class="pair"><figure><figcaption>Source PDF</figcaption><a href="pdf-page-{n}.png"><img loading="lazy" src="pdf-page-{n}.png" alt="Source PDF page {n}"></a></figure>'
                     f'<figure><figcaption>Converted HTML</figcaption><a href="html-page-{n}.png"><img loading="lazy" src="html-page-{n}.png" alt="Converted page {n}"></a></figure></div></section>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Local conversion comparison</title><style>
body{font:1rem/1.5 system-ui;margin:2rem;background:#eef1f5;color:#172b42}
main{max-width:1800px;margin:auto}.pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
figure{margin:0}figcaption{font-weight:bold}img{width:100%;background:white}
section{margin-block:3rem}@media(max-width:700px){.pair{grid-template-columns:1fr}}
</style><main><h1>Local conversion comparison</h1>
<p>Private development evidence. Original report contents remain local. Images are
for visual comparison; this is not the tagging application or a filing preview.</p>
<p>Review fonts, figures, columns, clipping, punctuation and missing elements.
Numerical image differences do not establish acceptance. Open an image for full size.</p>
''' + ''.join(cards) + '</main></html>'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=('png', 'sourcebuild'), default='png')
    args = parser.parse_args()
    base = BASE if args.candidate == 'png' else BASE.parent / 'browser-sourcebuild'
    from PIL import Image, __version__ as pillow_version
    browser = json.loads((base / 'browser-result.json').read_text())
    if not browser.get('pages'):
        raise SystemExit('Completed browser screenshots required')
    fixture = json.loads((ROOT / 'docs/qualification/fixture-registry.json').read_text())['fixtures'][0]
    pdf = ROOT / fixture['source_path']
    if digest(pdf) != browser['source_pdf_sha256']:
        raise SystemExit('PDF checksum mismatch')
    reference_file = BASE / 'visual-result.json'
    reference = json.loads(reference_file.read_text()) if args.candidate == 'sourcebuild' and reference_file.exists() else {}
    cached = {p['page']: p for p in reference.get('pages', [])} if reference.get('source_pdf_sha256') == fixture['sha256'] else {}
    rows = []
    reused = 0
    for n in sorted({p['page'] for p in browser['pages']}):
        target = base / f'pdf-page-{n}.png'
        old = BASE / f'pdf-page-{n}.png'
        if n in cached and old.exists() and digest(old) == cached[n].get('pdf_png_sha256'):
            shutil.copyfile(old, target)
            reused += 1
        else:
            proc = sandbox(ROOT / 'tools/baseline', pdf.parent, base, '/usr/bin/pdftoppm',
                           '-f', str(n), '-l', str(n), '-singlefile', '-r', '72', '-png',
                           '/input/' + pdf.name, '/output/pdf-page-' + str(n))
            if proc.returncode or not target.exists():
                rows.append({'page': n, 'status': 'unable_to_complete'})
                continue
        with Image.open(target) as original, Image.open(base / f'html-page-{n}.png') as rendered:
            measurement = compare_images(original, rendered)
        rows.append({'page': n, **measurement, 'pdf_png_sha256': digest(target),
                     'html_png_sha256': digest(base / f'html-page-{n}.png')})
    result = {'schema_version': 1, 'status': 'visual_review_pending', 'production_qualified': False,
              'source_pdf_sha256': fixture['sha256'], 'html_sha256': browser['html_sha256'],
              'pillow_version': pillow_version, 'pdf_rasterizer_sha256': digest(Path('/usr/bin/pdftoppm')),
              'dpi': 72, 'candidate': args.candidate, 'reused_reference_pages': reused, 'pages': rows}
    (base / 'visual-result.json').write_text(json.dumps(result, indent=2) + '\n')
    (base / 'review.html').write_text(review_html(rows))
    print(json.dumps({'status': result['status'], 'pages': len(rows),
                      'measured_pages': sum(r['status'] == 'measured_review_pending' for r in rows),
                      'production_qualified': False}, indent=2))
    return 0 if all(r['status'] == 'measured_review_pending' for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
