"""`tests_unchanged` accepts Prettier-only differences and still rejects real test edits.

Prettier is replaced by a stand-in that ignores whitespace and trailing commas, so no node,
Kiro, AWS or network is needed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))
os.chdir(ROOT)

import run_plan_build as rpb  # noqa: E402

PATH = "test/a.test.ts"
COMMITTED = "expect(f({a: 1, b: 2}))\n.toBe('x')\n"


def fake_prettier(repo_dir, path, text):
    return re.sub(r",(?=[)\]}])", "", re.sub(r"\s+", "", text.replace('"', "'")))


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", cwd, *args],
                          check=True, capture_output=True, text=True).stdout.strip()


class FormattingOnly(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="harness-fmt-")
        git(self.repo, "init", "-q", "-b", "main")
        os.makedirs(os.path.join(self.repo, "test"))
        self.write(COMMITTED)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "tests")
        self.pbc = rpb.PlanBuildContext("T", "t", os.path.join(ROOT, ".kiro", "prompts"), "b", "r",
                                        os.path.join(self.repo, ".run"), base_ref="HEAD", repo_dir=self.repo)
        self.pbc.tests_commit = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def write(self, text):
        with open(os.path.join(self.repo, PATH), "w", newline="\n") as fh:
            fh.write(text)

    def check(self):
        with mock.patch.object(rpb, "_prettier", fake_prettier):
            return rpb.make_run_check(self.pbc)({"name": "tests_unchanged"}, {})

    def test_unchanged_file_is_byte_identical(self):
        ok, msg = self.check()
        self.assertTrue(ok)
        self.assertIn("byte-identical", msg)

    def test_reformatted_file_passes(self):
        self.write("expect(\n  f({\n    a: 1,\n    b: 2,\n  }),\n).toBe('x');\n".replace(");", ")"))
        ok, msg = self.check()
        self.assertTrue(ok, msg)
        self.assertIn("only by Prettier formatting", msg)

    def test_real_edit_fails_and_names_the_file(self):
        self.write("expect(f({a: 1, b: 2}))\n.toBe('y')\n")
        ok, msg = self.check()
        self.assertFalse(ok)
        self.assertIn(PATH, msg)

    def test_without_prettier_any_difference_fails(self):
        self.write("expect(f({a: 1,\n b: 2}))\n.toBe('x')\n")
        with mock.patch.object(rpb, "_prettier", lambda *a: None):
            ok, _ = rpb.make_run_check(self.pbc)({"name": "tests_unchanged"}, {})
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
