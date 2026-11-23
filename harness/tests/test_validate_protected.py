"""The `protected` stage of scripts/validate.sh on a first story in an empty repository.

Runs the real validator against a throwaway git repo. npm is faked, so only the
protected stage is under test. No Kiro, AWS or network.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VALIDATE = os.path.join(ROOT, "scripts", "validate.sh")
BASH = shutil.which("bash")
NODE = shutil.which("node")

PKG = {"name": "x", "scripts": {"build": "tsc --noEmit"}, "jest": {"coverageThreshold": {"global": {"lines": 80}}}}


def git(cwd: str, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd,
                          check=True, capture_output=True, text=True).stdout.strip()


@unittest.skipUnless(BASH and NODE, "needs bash and node")
class ProtectedStage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.tmp.name, "repo")
        self.bin = os.path.join(self.tmp.name, "bin")
        os.makedirs(self.repo)
        os.makedirs(self.bin)
        git(self.repo, "init", "-q", "-b", "main")
        with open(os.path.join(self.repo, "README.md"), "w") as fh:
            fh.write("# x\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "Initial commit")
        self.base = git(self.repo, "rev-parse", "HEAD")
        with open(os.path.join(self.bin, "npm"), "w", newline="\n") as fh:
            fh.write("#!/usr/bin/env bash\nexit 0\n")
        os.chmod(os.path.join(self.bin, "npm"), 0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def write_pkg(self, scripts_cmd: str = "tsc --noEmit") -> None:
        pkg = {**PKG, "scripts": {"build": scripts_cmd}}
        with open(os.path.join(self.repo, "package.json"), "w") as fh:
            json.dump(pkg, fh)

    def validate(self, scaffold: bool) -> str:
        env = {**os.environ, "HARNESS_TARGET_REPO": self.repo, "VALIDATE_BASE_REF": self.base,
               "VALIDATE_SCAFFOLD": "1" if scaffold else "0",
               "PATH": self.bin + os.pathsep + os.environ["PATH"]}
        r = subprocess.run([BASH, VALIDATE], env=env, capture_output=True, text=True)
        return r.stdout + r.stderr

    def test_new_package_json_passes_in_scaffold_mode_on_empty_repo(self):
        self.write_pkg()
        out = self.validate(scaffold=True)
        self.assertIn("protected PASS", out)
        self.assertIn("package.json is new (absent at the base ref)", out)

    def test_new_package_json_fails_without_scaffold_mode(self):
        self.write_pkg()
        out = self.validate(scaffold=False)
        self.assertIn("protected FAILED", out)
        self.assertIn("package.json section changed: scripts", out)

    def test_existing_package_json_stays_protected_in_scaffold_mode(self):
        self.write_pkg()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base with package.json")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.write_pkg(scripts_cmd="echo weakened")
        out = self.validate(scaffold=True)
        self.assertIn("protected FAILED", out)
        self.assertIn("package.json section changed: scripts", out)


if __name__ == "__main__":
    unittest.main()
