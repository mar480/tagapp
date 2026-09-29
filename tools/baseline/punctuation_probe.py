"""Locate non-breaking-hyphen differences for review; never edit report bytes."""
from __future__ import annotations

from collections import defaultdict
from html.parser import HTMLParser
import json
import xml.etree.ElementTree as ET

from tools.baseline.conversion_probe import ROOT, sandbox
from tools.baseline.illustrative_probe import VOID, digest


class LineText(HTMLParser):
    """Index the pinned converter's text lines; not a general document importer."""
    def __init__(self):
        super().__init__()
        self.page = None
        self.line = None
        self.hidden = 0
        self.stack = []
        self.lines = defaultdict(list)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        previous = (self.page, self.line, self.hidden)
        if 'data-page-no' in attrs:
            self.page = int(attrs['data-page-no'], 16)
            self.line = None
        if self.page is not None and 't' in attrs.get('class', '').split():
            self.line = len(self.lines[self.page])
            self.lines[self.page].append('')
        self.hidden += tag in ('script', 'style')
        if tag not in VOID:
            self.stack.append((tag, previous))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.page, self.line, self.hidden = self.stack[i][1]
                del self.stack[i:]
                break

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.page is not None and self.line is not None and not self.hidden:
            self.lines[self.page][self.line] += data


def proposals(words: list[dict], lines: dict) -> list[dict]:
    """Offer only exact same-page string matches; preserve ambiguity for review.

    Offsets are Python Unicode codepoints, not browser UTF-16 offsets. They refer
    only to the hashed input HTML and are diagnostic locators, not durable anchors.
    """
    result = []
    for word in words:
        reference = word['text']
        if '\u2011' not in reference:
            continue
        painted = reference.replace('\u2011', '-')
        candidates = []
        for line, value in enumerate(lines.get(word['page'], [])):
            start = 0
            while (offset := value.find(painted, start)) >= 0:
                candidates.append({'line': line, 'start': offset, 'end': offset + len(painted),
                                   'hyphen_offsets': [offset + i for i, c in enumerate(reference) if c == '\u2011']})
                start = offset + 1
        result.append({**word, 'painted_candidate': painted,
                       'status': 'unique_candidate' if len(candidates) == 1 else 'ambiguous' if candidates else 'unmatched',
                       'candidates': candidates, 'approval': 'not_reviewed'})
    return result


def main() -> int:
    fixture = json.loads((ROOT / 'docs/qualification/fixture-registry.json').read_text())['fixtures'][0]
    source = ROOT / fixture['source_path']
    conversion = ROOT / '.local/qualification/gt-frs102/sourcebuild'
    previous = json.loads((conversion / 'result.json').read_text())
    if digest(source) != fixture['sha256'] or previous['source_sha256'] != fixture['sha256'] or digest(conversion / 'report.html') != previous['html_sha256']:
        raise SystemExit('Source or conversion checksum mismatch')
    output = ROOT / '.local/qualification/gt-frs102/punctuation'; output.mkdir(exist_ok=True)
    run = sandbox(ROOT / 'tools/baseline', source.parent, output, '/usr/bin/pdftotext', '-bbox-layout', '/input/' + source.name, '/output/words.xhtml')
    (output / 'extractor.log').write_bytes(run.stdout + run.stderr)
    if run.returncode:
        raise SystemExit('Reference extraction failed; no proposals generated')
    xml = ET.parse(output / 'words.xhtml')
    pages = list(xml.iter('{http://www.w3.org/1999/xhtml}page'))
    if len(pages) != fixture['pages']:
        raise SystemExit('Reference page count mismatch')
    words = [{'page': number, 'text': ''.join(word.itertext()), 'bbox': word.attrib}
             for number, page in enumerate(pages, 1)
             for word in page.iter('{http://www.w3.org/1999/xhtml}word')]
    index = LineText(); index.feed((conversion / 'report.html').read_text())
    rows = proposals(words, index.lines)
    private = {'source_sha256': fixture['sha256'], 'html_sha256': previous['html_sha256'],
               'offset_units': 'Unicode codepoints', 'proposals': rows}
    (output / 'private-proposals.json').write_text(json.dumps(private, indent=2) + '\n')
    result = {'schema_version': 1, 'status': 'review_required', 'source_sha256': fixture['sha256'],
              'html_sha256': previous['html_sha256'], 'reference_bbox_sha256': digest(output / 'words.xhtml'),
              'source_codepoint': 'U+2011', 'converted_codepoint': 'U+002D',
              'comparison_after_nfkc': 'U+2010 versus U+002D',
              'occurrences': sum(r['text'].count('\u2011') for r in rows),
              'unique_candidates': sum(r['status'] == 'unique_candidate' for r in rows),
              'ambiguous_candidates': sum(r['status'] == 'ambiguous' for r in rows),
              'unmatched_candidates': sum(r['status'] == 'unmatched' for r in rows),
              'affected_pages': sorted({r['page'] for r in rows}),
              'repairs_applied': 0, 'production_qualified': False}
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 1  # Located candidates still require review and a new document revision.


if __name__ == '__main__':
    raise SystemExit(main())
