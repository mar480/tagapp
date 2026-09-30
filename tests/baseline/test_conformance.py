from pathlib import Path
import stat
import json
from unittest.mock import patch
import tempfile
import unittest
from zipfile import ZipFile, ZipInfo

from tools.baseline.conformance import control_xml, inspect_suite, member_path, summarize_report, summarize_inline_groups


class ConformanceTests(unittest.TestCase):
    def test_archive_paths_reject_escape_and_ambiguous_names(self):
        for name in ('../out', '/out', 'a//b', 'a/./b', 'a\\b', 'a%2fb', 'a:b', 'a?b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                member_path(name)
        self.assertEqual(member_path('suite/test.xml'), 'suite/test.xml')

    def test_control_documents_reject_entity_declarations(self):
        for data in (b'<!DOCTYPE root [<!ENTITY e "expanded">]><root/>', '<!DOCTYPE root><root/>'.encode('utf-16')):
            with self.subTest(data=data), self.assertRaises(ValueError):
                control_xml(data)

    def archive(self, path, root='', target='case.xml', extra=None):
        with ZipFile(path, 'w') as archive:
            archive.writestr('suite/index.xml', f'<testcases root="{root}"><testcase uri="{target}"/></testcases>')
            archive.writestr('suite/case.xml', '<testcase><variation id="one"/><variation id="two"/></testcase>')
            if extra:
                archive.writestr(*extra)

    def test_inventory_counts_actual_variations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'suite.zip'; self.archive(path)
            inventory = inspect_suite(path, 'suite/index.xml')
            self.assertEqual(inventory['testcase_files'], 1)
            self.assertEqual(inventory['expected_variations'], 2)

    def test_external_or_missing_testcases_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'suite.zip'
            for root, target in (('/absolute', 'case.xml'), ('', 'https://example.invalid/case.xml'), ('', 'missing.xml')):
                self.archive(path, root, target)
                with self.subTest(root=root, target=target), self.assertRaises(ValueError):
                    inspect_suite(path, 'suite/index.xml')

    def test_archive_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'suite.zip'
            info = ZipInfo('suite/link'); info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            self.archive(path, extra=(info, '/outside'))
            with self.assertRaises(ValueError):
                inspect_suite(path, 'suite/index.xml')

    def report(self, text, expected=2, exit_code=0):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.csv'
            path.write_text(text)
            return summarize_report(path, expected, exit_code)

    def test_only_complete_successful_runs_pass(self):
        text = 'Testcase,Id,Status,Expected,Actual\ncase.xml,one,pass,valid,valid\ncase.xml,two,pass,invalid,error\n'
        self.assertEqual(self.report(text)['status'], 'passed')
        self.assertEqual(self.report(text, expected=3)['status'], 'unable_to_complete')
        self.assertEqual(self.report(text, exit_code=1)['status'], 'unable_to_complete')
        self.assertEqual(self.report(text.replace('two', 'one'))['status'], 'unable_to_complete')

    def test_complete_failing_or_unchecked_cases_require_review(self):
        for status in ('fail', 'not run', ''):
            result = self.report(f'Testcase,Id,Status\ncase.xml,one,pass\ncase.xml,two,{status}\n')
            self.assertEqual(result['status'], 'review_required')
            self.assertEqual(len(result['nonpassing']), 1)

    def test_group_report_requires_every_selected_identifier(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.csv'
            path.write_text('Testcase,Id,Status\nselected.xml,one,pass\nother.xml,two,not run\n')
            keys = [('selected.xml', 'one')]
            self.assertEqual(summarize_report(path, 1, 0, keys)['status'], 'passed')
            keys.append(('missing.xml', 'three'))
            self.assertEqual(summarize_report(path, 2, 0, keys)['status'], 'unable_to_complete')
            with self.assertRaises(ValueError):
                summarize_report(path, 2, 0, [('selected.xml', 'one')] * 2)

    def test_group_summary_cannot_hide_missing_or_wrong_suite_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            item = {'id': 'inline-suite', 'sha256': 'pinned', 'entry_point': 'index.xml'}
            group = base / 'inline-suite/groups/first'; group.mkdir(parents=True)
            record = {'suite_sha256': 'pinned', 'group': 'first', 'processor_version': '2.44.1',
                      'processor_exit_code': 0, 'wall_seconds': 1}
            (group / 'result.json').write_text(json.dumps(record))
            (group / 'report.csv').write_text('Testcase,Id,Status\ncase.xml,one,pass\n')
            groups = {'first': [('case.xml', 'one')], 'missing': [('missing.xml', 'two')]}
            with patch('tools.baseline.conformance.BASE', base), \
                 patch('tools.baseline.conformance.verify', return_value=base), \
                 patch('tools.baseline.conformance.inline_groups', return_value=groups):
                result = summarize_inline_groups(item, 2)
                self.assertEqual(result['status'], 'unable_to_complete')
                self.assertEqual(result['reported_variations'], 1)
                self.assertEqual(result['expected_variations'], 2)
                groups.pop('missing')
                self.assertEqual(summarize_inline_groups(item, 1)['status'], 'passed')
                with self.assertRaises(ValueError):
                    summarize_inline_groups(item, 2)
                record['suite_sha256'] = 'changed'
                (group / 'result.json').write_text(json.dumps(record))
                self.assertEqual(summarize_inline_groups(item, 1)['status'], 'unable_to_complete')

    def test_missing_report_columns_fail_closed(self):
        with self.assertRaises(ValueError):
            self.report('Id,Status\none,pass\n')


if __name__ == '__main__':
    unittest.main()
