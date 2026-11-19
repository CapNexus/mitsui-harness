"""Drivers and .kiro/prompts must agree, and every plan_build step must work end to end.

Runs the real `run_plan_build` steps against a throwaway git repo with a fake Kiro that
answers each template the way its output contract requires. No network, no Kiro, no AWS.

    uv run --with-requirements harness/drivers/requirements.txt python -m unittest discover -s harness/tests -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))
os.chdir(ROOT)

import loop_driver  # noqa: E402
import prompts  # noqa: E402
import run_frame  # noqa: E402
import run_plan_build as rpb  # noqa: E402

PROMPTS = os.path.join(ROOT, ".kiro", "prompts")
WORKFLOW = rpb.load_workflow(os.path.join(ROOT, rpb.WORKFLOW_PATH))


def sh(cwd: str, *args: str) -> str:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class FakeKiro:
    """Answers each step like a well-behaved agent and records what it was asked."""

    def __init__(self, repo: str, story: str, weaken_tests: bool = False):
        self.repo, self.story, self.weaken = repo, story, weaken_tests
        self.calls = []

    def __call__(self, text, *, agent, step, template, params):
        self.calls.append({"step": step, "agent": agent, "template": template, "params": params, "text": text})
        r = self.repo
        if step == "classify":
            return '<<<CLASSIFICATION>>>\n{"type": "checker-script", "rationale": "x.", "confidence": "high"}\n<<<END CLASSIFICATION>>>'
        if step == "plan":
            os.makedirs(os.path.join(r, "plans"), exist_ok=True)
            with open(os.path.join(r, "plans", f"{self.story}.md"), "w") as fh:
                fh.write(f"# {self.story}\n\n1. The checker shall exit 0 when ok.txt exists.\n")
            return f"<<<SPEC>>>\nplans/{self.story}.md\n<<<END SPEC>>>"
        if step == "write_tests":
            os.makedirs(os.path.join(r, "test"), exist_ok=True)
            with open(os.path.join(r, "test", "check.test"), "w") as fh:
                fh.write("expects ok.txt\n")
            return ('<<<TESTS>>>\n' + json.dumps({"status": "written", "story_id": self.story,
                    "files": ["test/check.test"], "criteria": [{"criterion": 1, "tests": ["t"]}],
                    "run_command": "x", "observed": "failed", "notes": []}) + '\n<<<END TESTS>>>')
        if step == "implement":
            with open(os.path.join(r, "ok.txt"), "w") as fh:
                fh.write("ok\n")
            if self.weaken:
                with open(os.path.join(r, "test", "check.test"), "w") as fh:
                    fh.write("weakened\n")
            return "done"
        if step == "review":
            return "<<<REVIEW>>>\n- NON-BLOCKING: none\nAPPROVE\n<<<END REVIEW>>>"
        if step in ("commit_tests", "commit"):
            paths = ["test/check.test"] if params.get("scope") == "tests" else ["."]
            sh(r, "git", "add", *paths)
            sh(r, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", step)
            return "committed"
        raise AssertionError(f"unexpected step {step}")


class PlanBuildContract(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="harness-contract-")
        sh(self.repo, "git", "init", "-q", "-b", "main")
        sh(self.repo, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
        self.base = sh(self.repo, "git", "rev-parse", "HEAD")
        self.validator = os.path.join(self.repo, "validate.sh")
        with open(self.validator, "w", newline="\n") as fh:      # fails until implement writes ok.txt
            fh.write(f'#!/usr/bin/env bash\ncd "{self.repo.replace(os.sep, "/")}" && [ -f ok.txt ]\n')

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _run(self, weaken=False):
        kiro = FakeKiro(self.repo, "T-01", weaken_tests=weaken)
        pbc = rpb.PlanBuildContext("T-01", "# T-01: test story", PROMPTS, "builder", "reviewer",
                                   os.path.join(self.repo, ".run"), base_ref=self.base,
                                   repo_dir=self.repo, invoke=kiro, validator=self.validator)
        ctx = {"issue": pbc.issue_text}
        results = []
        for step in WORKFLOW["steps"]:
            results.append(rpb.run_step(WORKFLOW, step, ctx, pbc))
        return kiro, pbc, ctx, results

    def test_full_loop_renders_every_prompt_and_commits(self):
        kiro, pbc, ctx, results = self._run()
        self.assertEqual([r.name for r in results], [s["name"] for s in WORKFLOW["steps"]])
        self.assertTrue(all(r.ok for r in results))
        self.assertEqual(ctx["classification"], "checker-script")
        self.assertTrue(ctx["plan_file_path"].endswith("plans/T-01.md"))
        by_step = {c["step"]: c for c in kiro.calls}
        self.assertEqual(by_step["classify"]["agent"], "reviewer")
        self.assertEqual(by_step["review"]["agent"], "reviewer")
        self.assertEqual(by_step["implement"]["agent"], "builder")
        self.assertIn(ctx["plan_file_path"], by_step["write_tests"]["text"])
        self.assertIn(self.base, by_step["review"]["text"])
        self.assertEqual(by_step["commit_tests"]["params"]["scope"], "tests")
        self.assertEqual(by_step["commit"]["params"]["scope"], "full")
        self.assertIsNotNone(pbc.tests_commit)
        self.assertEqual(len(sh(self.repo, "git", "log", "--oneline", f"{self.base}..HEAD").splitlines()), 2)

    def test_tests_unchanged_catches_weakened_tests(self):
        with self.assertRaises(loop_driver.LoopFailed) as err:
            self._run(weaken=True)
        self.assertEqual(err.exception.step, "tests_unchanged")

    def test_state_round_trip(self):
        pbc = rpb.PlanBuildContext("X", "x", PROMPTS, "builder", "reviewer", "r", base_ref="b", repo_dir=self.repo)
        pbc.tests_commit, pbc.tests_status, pbc.new_test_files = "abc", "written", ["t"]
        clone = rpb.PlanBuildContext("X", "x", PROMPTS, "builder", "reviewer", "other").restore(
            json.loads(json.dumps(pbc.state())))
        self.assertEqual(clone.state(), pbc.state())


class TemplateContract(unittest.TestCase):
    def test_every_plan_template_renders_with_driver_variables(self):
        plan_map = next(s for s in WORKFLOW["steps"] if s["name"] == "plan")["prompt_map"]
        for cls, template in plan_map.items():
            with self.subTest(template=template):
                prompts.render(PROMPTS, template, issue="i", classification=cls)

    def test_frame_prompts_render_with_driver_variables(self):
        sent = []
        real = run_frame.invoke_kiro
        def fake(text, **kw):
            sent.append(kw["template"])
            if kw["template"] == "frame_triage":
                return '<<<TRIAGE>>>\n{"decisions": []}\n<<<END TRIAGE>>>'
            return "<<<DECOMPOSITION>>>\nnot json\n<<<END DECOMPOSITION>>>"

        run_frame.invoke_kiro = fake
        try:
            run_frame.make_triage(PROMPTS, "reviewer")([{"id": "A", "title": "t", "text": "x"}])
            item = {"id": "A", "title": "t", "acceptance_criteria": ["one shall", "two shall"]}
            run_frame.make_decompose(PROMPTS, "reviewer", max_children=4, max_attempts=1)(item)
        finally:
            run_frame.invoke_kiro = real
        self.assertEqual(sent, ["frame_triage", "frame_decompose"])


if __name__ == "__main__":
    unittest.main()
