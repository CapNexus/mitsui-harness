"""The ACP turn watchdog cuts off a silent turn, not a busy one.

    uv run --with-requirements harness/drivers/requirements.txt python -m unittest discover -s harness/tests -v
"""

from __future__ import annotations

import asyncio
import os
import sys
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))

import acp_client  # noqa: E402


class FakeClient:
    """Stands in for _AEWClient: only the activity clock the watchdog reads."""

    def __init__(self) -> None:
        self.last_activity = 0.0
        self.active_tools: set = set()

    def touch(self) -> None:
        import time

        self.last_activity = time.monotonic()


class WatchdogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.client = acp_client.KiroACPClient()
        self.client._loop = self.loop
        self.fake = FakeClient()
        self.client._client = self.fake
        self._saved = {k: os.environ.get(k) for k in ("BOOTSTRAP_STEP_IDLE_TIMEOUT", "BOOTSTRAP_STEP_TIMEOUT")}

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=2)

    def test_busy_turn_longer_than_idle_limit_is_not_cut_off(self) -> None:
        os.environ["BOOTSTRAP_STEP_IDLE_TIMEOUT"] = "1"
        os.environ["BOOTSTRAP_STEP_TIMEOUT"] = "30"

        async def busy() -> str:
            for _ in range(8):          # 8 x 0.4s = 3.2s of work, more than 3x the idle limit
                await asyncio.sleep(0.4)
                self.fake.touch()
            return "done"

        self.assertEqual(self.client._run(busy()), "done")

    def test_silent_turn_is_cut_off_as_idle(self) -> None:
        os.environ["BOOTSTRAP_STEP_IDLE_TIMEOUT"] = "1"
        os.environ["BOOTSTRAP_STEP_TIMEOUT"] = "30"

        async def silent() -> None:
            await asyncio.sleep(30)

        with self.assertRaises(TimeoutError) as cm:
            self.client._run(silent())
        self.assertIn("idle for 1s", str(cm.exception))

    def test_silent_turn_is_not_cut_off_while_a_tool_is_running(self) -> None:
        os.environ["BOOTSTRAP_STEP_IDLE_TIMEOUT"] = "1"
        os.environ["BOOTSTRAP_STEP_TIMEOUT"] = "30"

        async def long_tool() -> str:
            self.fake.active_tools.add("npm-test")
            await asyncio.sleep(3)      # silent for 3x the idle limit, but a tool is running
            self.fake.active_tools.discard("npm-test")
            return "done"

        self.assertEqual(self.client._run(long_tool()), "done")

    def test_idle_clock_applies_again_once_the_tool_finishes(self) -> None:
        os.environ["BOOTSTRAP_STEP_IDLE_TIMEOUT"] = "1"
        os.environ["BOOTSTRAP_STEP_TIMEOUT"] = "30"

        async def tool_then_silence() -> None:
            self.fake.active_tools.add("t")
            await asyncio.sleep(1.5)
            self.fake.active_tools.discard("t")
            self.fake.touch()
            await asyncio.sleep(30)

        with self.assertRaises(TimeoutError) as cm:
            self.client._run(tool_then_silence())
        self.assertIn("idle for 1s", str(cm.exception))

    def test_tool_tracking_follows_tool_call_status(self) -> None:
        from types import SimpleNamespace

        real = acp_client._AEWClient(auto_approve=False)
        real.track_tool(SimpleNamespace(tool_call_id="a", status="in_progress"))
        real.track_tool(SimpleNamespace(tool_call_id="b", status="pending"))
        self.assertEqual(real.active_tools, {"a", "b"})
        real.track_tool(SimpleNamespace(tool_call_id="a", status="completed"))
        real.track_tool(SimpleNamespace(tool_call_id="b", status="failed"))
        self.assertEqual(real.active_tools, set())
    def test_hard_cap_stops_a_turn_that_keeps_talking(self) -> None:
        os.environ["BOOTSTRAP_STEP_IDLE_TIMEOUT"] = "5"
        os.environ["BOOTSTRAP_STEP_TIMEOUT"] = "1"

        async def endless() -> None:
            while True:
                await asyncio.sleep(0.1)
                self.fake.touch()

        with self.assertRaises(TimeoutError) as cm:
            self.client._run(endless())
        self.assertIn("hard cap", str(cm.exception))

    def test_a_timeout_raised_by_the_turn_itself_is_not_retried_until_the_cap(self) -> None:
        os.environ["BOOTSTRAP_STEP_IDLE_TIMEOUT"] = "5"
        os.environ["BOOTSTRAP_STEP_TIMEOUT"] = "30"

        async def raises() -> None:
            raise TimeoutError("inner")

        import time

        t0 = time.monotonic()
        with self.assertRaises(TimeoutError) as cm:
            self.client._run(raises())
        self.assertEqual(str(cm.exception), "inner")
        self.assertLess(time.monotonic() - t0, 3)

    def test_defaults_allow_a_long_busy_turn(self) -> None:
        self.assertEqual(acp_client.DEFAULT_IDLE_TIMEOUT, 600.0)
        self.assertEqual(acp_client.DEFAULT_MAX_TIMEOUT, 5400.0)
        self.assertEqual(acp_client._env_seconds("NO_SUCH_VARIABLE_SET", 7.0), 7.0)
        os.environ["BOOTSTRAP_STEP_IDLE_TIMEOUT"] = "not a number"
        self.assertEqual(acp_client._env_seconds("BOOTSTRAP_STEP_IDLE_TIMEOUT", 7.0), 7.0)


if __name__ == "__main__":
    unittest.main()
