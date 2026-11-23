"""Proposed answers and re-analysis with human answers. Fake agent: no Kiro, AWS or network.

    uv run --with-requirements harness/drivers/requirements.txt python -m unittest discover -s harness/tests -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))
sys.path.insert(0, os.path.join(ROOT, "harness", "studio"))
sys.path.insert(0, os.path.join(ROOT, "harness"))
os.chdir(ROOT)

import prompts  # noqa: E402
import run_story  # noqa: E402
import story_analysis  # noqa: E402
from db import DB  # noqa: E402

REPLY = {"confidence": 70, "dimensions": {}, "summary": "s", "risks": [],
         "questions": ["Which Region?", "What is the VPN peer IP?"],
         "proposed_answers": [{"answer": "ap-northeast-1", "basis": "adr/x.md#region; security", "needs_human": False},
                              {"answer": "Mitsui network team supplies it", "basis": "DEP-05", "needs_human": True}],
         "relevant_docs": [], "recommendation": "start_with_caution"}


class FakeAgent:
    def __init__(self) -> None:
        self.texts = []

    def __call__(self, text, *, agent, step, template, params):
        self.texts.append(text)
        return "<<<ANALYSIS>>>\n" + json.dumps(REPLY) + "\n<<<END ANALYSIS>>>"


def first_story() -> str:
    return sorted(run_story.load_stories())[0]


class AnalyzeWithAnswers(unittest.TestCase):
    def test_prompt_declares_decisions_variable(self):
        body = open(os.path.join(story_analysis.PROMPTS_DIR, "analyze_story.md"), encoding="utf-8").read()
        self.assertEqual(prompts.declared_variables(body), ["story", "docs", "readiness", "decisions"])
        self.assertIn("proposed_answers", body)

    def test_format_decisions_skips_blank_answers(self):
        out = story_analysis.format_decisions([{"question": "Q1", "answer": " A1 "}, {"question": "Q2", "answer": "  "}])
        self.assertEqual(out, "1. Q: Q1\n   A: A1")
        self.assertEqual(story_analysis.format_decisions(None), "(none)")

    def test_first_analysis_has_no_decisions_and_returns_proposals(self):
        agent, sid = FakeAgent(), first_story()
        result = story_analysis.run(sid, agent)
        self.assertIn("### decisions\n\n(none)", agent.texts[0])
        self.assertEqual(result["proposed_answers"][1]["needs_human"], True)
        self.assertEqual(len(result["proposed_answers"]), len(result["questions"]))

    def test_reanalysis_passes_answers_as_decisions(self):
        agent, sid = FakeAgent(), first_story()
        story_analysis.run(sid, agent, decisions=[{"question": "Which Region?", "answer": "ap-northeast-1 only"}])
        self.assertIn("1. Q: Which Region?\n   A: ap-northeast-1 only", agent.texts[0])


class AnswerStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DB(os.path.join(self.tmp.name, "t.db"))

    def tearDown(self):
        self.db._conn.close()
        self.tmp.cleanup()

    def test_save_replaces_and_drops_blank(self):
        self.db.save_answers("S1", [{"question": "Q1", "answer": "A1"}, {"question": "Q2", "answer": "A2"}])
        self.assertEqual([(a["question"], a["answer"]) for a in self.db.answers("S1")], [("Q1", "A1"), ("Q2", "A2")])
        self.db.save_answers("S1", [{"question": "Q1", "answer": "edited"}, {"question": "Q2", "answer": "  "}])
        self.assertEqual([(a["question"], a["answer"]) for a in self.db.answers("S1")], [("Q1", "edited")])

    def test_answers_are_per_story(self):
        self.db.save_answers("S1", [{"question": "Q", "answer": "A"}])
        self.assertEqual(self.db.answers("S2"), [])


class RestartStory(unittest.TestCase):
    def setUp(self):
        import runner as runner_mod
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DB(os.path.join(self.tmp.name, "t.db"))
        self.runner = runner_mod.Runner(self.db)
        self.sid = first_story()

    def tearDown(self):
        self.db._conn.close()
        self.tmp.cleanup()

    def test_discards_latest_analysis_and_keeps_answers(self):
        rid = self.db.create_run(self.sid, "analysis")
        self.db.update_run(rid, status="completed", confidence=90)
        self.db.save_answers(self.sid, [{"question": "Q", "answer": "A"}])
        out = self.runner.restart_story(self.sid)
        self.assertEqual(out["status"], "understand")
        self.assertEqual(self.db.run(rid)["status"], "discarded")
        self.assertEqual(self.db.answers(self.sid)[0]["answer"], "A")

    def test_refuses_an_approved_build(self):
        rid = self.db.create_run(self.sid, "implementation")
        self.db.update_run(rid, status="completed")
        with self.assertRaises(ValueError):
            self.runner.restart_story(self.sid)
        self.assertEqual(self.db.run(rid)["status"], "completed")

    def test_unknown_story(self):
        with self.assertRaises(ValueError):
            self.runner.restart_story("NOPE-S00")


if __name__ == "__main__":
    unittest.main()
