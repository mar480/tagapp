import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.baseline.publication_guard import scan


class PublicationGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def write(self, name, data):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def test_ignored_material_can_still_be_force_staged_and_is_rejected(self):
        self.write(".gitignore", b"materials/\n")
        self.write("materials/private.txt", b"private document")
        self.assertEqual(scan(self.root, worktree=True), [])
        self.git("add", "-f", "materials/private.txt")
        self.assertEqual(scan(self.root)[0]["category"], "private-or-dependency-directory")

    def test_checks_staged_bytes_even_when_worktree_has_been_cleaned(self):
        marker = b"-----BEGIN " + b"PRIVATE KEY-----"
        self.write("settings.txt", marker)
        self.git("add", "settings.txt")
        self.write("settings.txt", b"clean")
        self.assertEqual(scan(self.root)[0]["category"], "private-key")
        self.assertEqual(scan(self.root, worktree=True), [])

    def test_symlink_is_not_followed(self):
        (self.root / "link").symlink_to("/etc/passwd")
        self.git("add", "link")
        self.assertEqual(scan(self.root)[0]["category"], "non-regular-or-unmerged-index-entry")
        self.assertEqual(scan(self.root, worktree=True)[0]["category"], "non-regular-file-needs-review")

    def test_binary_and_oversized_files_need_review(self):
        self.write("binary", b"a\0b")
        self.write("large", b"a" * 2_000_001)
        self.git("add", ".")
        self.assertEqual({x["category"] for x in scan(self.root)}, {"binary-needs-review", "oversized-needs-review"})

    def test_env_example_and_plain_docs_are_allowed(self):
        self.write(".env.example", b"VALUE=replace-me\n")
        self.write("README.md", b"Public documentation\n")
        self.git("add", ".")
        self.assertEqual(scan(self.root), [])

    def test_deleted_worktree_file_does_not_fail(self):
        self.write("obsolete.txt", b"old")
        self.git("add", ".")
        (self.root / "obsolete.txt").unlink()
        self.assertEqual(scan(self.root, worktree=True), [])


if __name__ == "__main__":
    unittest.main()
