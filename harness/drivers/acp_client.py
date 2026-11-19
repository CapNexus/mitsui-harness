"""Synchronous ACP client for driving Kiro CLI via the Agent Client Protocol.

Shipped verbatim by harness-bootstrap into every generated harness (`harness/drivers/`)
— the same client this repo's own pipeline uses to talk to Kiro, so a generated harness
never reinvents ACP plumbing: `invoke_kiro(text, agent=..., step=...)` in `agents.py` is
the one call a harness's `run_agent` needs to make.

Transport for the AEW system. Owns a single long-lived ``kiro-cli acp`` subprocess
(the ``initialize`` handshake is paid once) and exposes a *synchronous* API so the
existing sequential Python driver (`aew/workflow/plan_build.py`) is unaffected.

Design (see specs/chores/port-aews-to-kiro-acp.md):
- One shared subprocess, a **fresh session per step** (`session/new` → `session/prompt`).
  Fresh session == clean context == the same statelessness as the old per-process
  headless invocation. Sessions are never reused across steps.
- Artifacts flow through the Python driver (returned strings, files on disk, git
  state) — never through session memory.
- The async ACP library is wrapped behind a synchronous facade backed by a single
  background event loop running on a dedicated thread (no nested loops).
- Client capabilities advertise ``fs``/``terminal`` as false so Kiro uses its own
  built-in tools (matching the old ``--trust-all-tools`` behavior).
- Permissions: ``kiro-cli acp --trust-all-tools`` auto-approves on the agent side; the
  client-side ``request_permission`` handler also auto-allows (gated by
  ``AEW_AUTO_APPROVE``) and logs every approved tool call, since these workflows can
  run destructive tools (shell, file write, git, ``gh pr create``).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Any, List, Optional

import acp
from acp import Client, text_block
from acp.schema import (
    AllowedOutcome,
    ClientCapabilities,
    DeniedOutcome,
    FileSystemCapabilities,
    RequestPermissionResponse,
)

# Plain same-directory import, not a relative one: this file is run standalone inside
# whatever repo the harness was generated for, not necessarily as part of a package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import AuditSink, StepAudit  # noqa: E402

logger = logging.getLogger(__name__)

KIRO_CLI_PATH = os.getenv("KIRO_CLI_PATH", "kiro-cli")

# stop_reason values that are *not* successful completion.
_ERROR_STOP_REASONS = {"max_tokens", "max_turn_requests", "refusal", "cancelled"}


@dataclass
class PromptResult:
    """Result of a single ``session/prompt`` turn."""

    text: str
    stop_reason: str
    usage: Optional[Any] = None
    usage_dict: dict = field(default_factory=dict)
    tool_calls: List[str] = field(default_factory=list)


class _AEWClient(Client):
    """ACP client callbacks: capture the full event stream, auto-approve tools.

    A single instance is shared by the connection. Because the driver is strictly
    sequential (one prompt in flight at a time), a single "active step" audit context
    is safe. Each turn's ``StepAudit`` receives every ACP event verbatim (for the raw
    log) plus structured accumulation (for the summary).
    """

    def __init__(self, auto_approve: bool) -> None:
        self._auto_approve = auto_approve
        self.text_chunks: List[str] = []
        self.tool_calls: List[str] = []
        self.last_usage: Optional[Any] = None
        self._audit: Optional[StepAudit] = None

    def set_audit(self, step_audit: Optional[StepAudit]) -> None:
        self._audit = step_audit

    def reset(self) -> None:
        self.text_chunks.clear()
        self.tool_calls.clear()
        self.last_usage = None

    async def request_permission(
        self, *, session_id: str, tool_call: Any, options: List[Any], **_: Any
    ) -> RequestPermissionResponse:
        title = getattr(tool_call, "title", None) or getattr(tool_call, "tool_call_id", "?")
        if self._audit is not None:
            self._audit.record(
                "request_permission",
                {"tool_call": tool_call, "options": options},
            )

        if not self._auto_approve:
            logger.warning("Denying tool permission (AEW_AUTO_APPROVE not set): %s", title)
            if self._audit is not None:
                self._audit.add_permission(str(title), "denied", None)
                self._audit.record("permission_decision", {"tool": str(title), "decision": "denied"})
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))

        allow = next(
            (o for o in options if o.kind in ("allow_always", "allow_once")),
            options[0] if options else None,
        )
        if allow is None:
            logger.warning("No allow option offered for tool %s; denying", title)
            if self._audit is not None:
                self._audit.add_permission(str(title), "denied", None)
                self._audit.record("permission_decision", {"tool": str(title), "decision": "denied"})
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))

        logger.info("Auto-approving tool call: %s (option=%s)", title, allow.option_id)
        if self._audit is not None:
            self._audit.add_permission(str(title), "allowed", allow.option_id)
            self._audit.record(
                "permission_decision",
                {"tool": str(title), "decision": "allowed", "option": allow.option_id},
            )
        return RequestPermissionResponse(
            outcome=AllowedOutcome(option_id=allow.option_id, outcome="selected")
        )

    async def session_update(self, *, session_id: str, update: Any, **_: Any) -> None:
        kind = getattr(update, "session_update", None)

        if kind == "agent_message_chunk":
            text = getattr(update.content, "text", None)
            if self._audit is not None:
                self._audit.record_text_chunk(
                    f"session_update:{kind}", update, text or "", is_thought=False
                )
            if text:
                self.text_chunks.append(text)
                if self._audit is not None:
                    self._audit.add_assistant_text(text)
        elif kind == "agent_thought_chunk":
            text = getattr(getattr(update, "content", None), "text", None)
            if self._audit is not None:
                self._audit.record_text_chunk(
                    f"session_update:{kind}", update, text or "", is_thought=True
                )
            if text and self._audit is not None:
                self._audit.add_thinking_text(text)
        elif kind in ("tool_call", "tool_call_update"):
            if self._audit is not None:
                self._audit.record(f"session_update:{kind}", update)
            title = getattr(update, "title", "")
            if title:
                self.tool_calls.append(title)
                logger.debug("tool_call: %s", title)
            if self._audit is not None:
                data = update.model_dump(mode="json", by_alias=False, exclude_none=True)
                self._audit.upsert_tool_call(data)
        elif kind == "usage_update":
            if self._audit is not None:
                self._audit.record(f"session_update:{kind}", update)
            self.last_usage = update
            if self._audit is not None:
                self._audit.set_usage(_usage_to_dict(update))
        else:
            # Faithful raw capture of any other update kind.
            if self._audit is not None:
                self._audit.record(f"session_update:{kind or 'unknown'}", update)

    # Client-side fs/terminal are advertised as disabled; Kiro uses its built-in
    # tools. These stubs exist only to satisfy the Client interface.
    async def read_text_file(self, **_: Any) -> Any:  # pragma: no cover - unused
        raise acp.RequestError.method_not_found("fs/read_text_file")

    async def write_text_file(self, **_: Any) -> Any:  # pragma: no cover - unused
        raise acp.RequestError.method_not_found("fs/write_text_file")


def _usage_to_dict(usage: Any) -> dict:
    """Normalize a Usage/UsageUpdate model into a flat token/cost dict."""
    if usage is None:
        return {}
    dump = getattr(usage, "model_dump", None)
    data = dump(mode="json", by_alias=False, exclude_none=True) if callable(dump) else {}
    out = {
        "total_tokens": data.get("total_tokens") or data.get("used") or data.get("size"),
        "input_tokens": data.get("input_tokens"),
        "output_tokens": data.get("output_tokens"),
    }
    if data.get("cost") is not None:
        out["cost"] = data.get("cost")
    return {k: v for k, v in out.items() if v is not None}


class KiroACPClient:
    """Owns a ``kiro-cli acp`` subprocess and exposes a synchronous API.

    Runs a private asyncio event loop on a background thread; all async ACP calls are
    marshaled onto that loop via ``run_coroutine_threadsafe``. This keeps the public
    API synchronous for the sequential driver while using a single, non-nested loop.
    """

    def __init__(
        self,
        agent: str = "default",
        *,
        cwd: Optional[str] = None,
        auto_approve: Optional[bool] = None,
        audit: Optional[AuditSink] = None,
    ) -> None:
        self._agent = agent
        self._cwd = cwd or os.getcwd()
        if auto_approve is None:
            auto_approve = os.getenv("AEW_AUTO_APPROVE", "").lower() in ("1", "true", "yes")
        self._auto_approve = auto_approve
        self._audit = audit

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._conn = None
        self._proc = None
        self._client: Optional[_AEWClient] = None
        self._ctx = None  # the spawn_agent_process async context manager
        self._started = False

    def set_audit(self, audit: Optional[AuditSink]) -> None:
        """Attach (or replace) the audit sink used for subsequent prompts."""
        self._audit = audit

    # --- lifecycle -------------------------------------------------------

    def start(self) -> "KiroACPClient":
        if self._started:
            return self
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, name="kiro-acp-loop", daemon=True)
        self._thread.start()
        self._run(self._start_async())
        self._started = True
        return self

    def _run_loop(self) -> None:
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run(self, coro) -> Any:
        assert self._loop is not None, "client not started"
        fut: Future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        # A stalled turn must not hang the whole run: BOOTSTRAP_STEP_TIMEOUT seconds
        # (default 900) then a TimeoutError the step runner treats as a failed attempt.
        timeout = float(os.getenv("BOOTSTRAP_STEP_TIMEOUT", "900"))
        try:
            return fut.result(timeout=timeout)
        except (TimeoutError, FutureTimeout) as e:
            fut.cancel()
            raise TimeoutError(f"ACP turn exceeded {timeout:.0f}s") from e

    async def _start_async(self) -> None:
        env = os.environ.copy()
        env["BYPASS_TOOL_CONSENT"] = "true"

        args = ["acp", "--agent", self._agent]
        if self._auto_approve:
            args.append("--trust-all-tools")

        self._client = _AEWClient(auto_approve=self._auto_approve)
        self._ctx = acp.spawn_agent_process(
            self._client, KIRO_CLI_PATH, *args, env=env, cwd=self._cwd
        )
        self._conn, self._proc = await self._ctx.__aenter__()

        caps = ClientCapabilities(
            fs=FileSystemCapabilities(read_text_file=False, write_text_file=False),
            terminal=False,
        )
        init = await self._conn.initialize(
            protocol_version=acp.PROTOCOL_VERSION, client_capabilities=caps
        )
        info = init.agent_info
        logger.info(
            "ACP initialized: agent=%s version=%s protocol=%s",
            getattr(info, "name", "?"),
            getattr(info, "version", "?"),
            init.protocol_version,
        )

    def close(self) -> None:
        if not self._started:
            return
        try:
            self._run(self._close_async())
        except Exception as e:  # noqa: BLE001 - best-effort shutdown
            logger.warning("Error during ACP shutdown: %s", e)
        finally:
            if self._loop is not None:
                self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread is not None:
                self._thread.join(timeout=5)
            self._started = False

    async def _close_async(self) -> None:
        if self._ctx is not None:
            try:
                await self._ctx.__aexit__(None, None, None)
            finally:
                self._ctx = None
        # Ensure the subprocess is reaped even if the context manager didn't.
        proc = self._proc
        if proc is not None and proc.returncode is None:
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=5)
            except Exception:  # noqa: BLE001
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass

    # --- sessions --------------------------------------------------------

    def new_session(self, cwd: Optional[str] = None) -> str:
        return self._run(self._new_session_async(cwd or self._cwd))

    async def _new_session_async(self, cwd: str) -> str:
        resp = await self._conn.new_session(cwd=cwd, mcp_servers=[])
        return resp.session_id

    def prompt(
        self,
        session_id: str,
        text: str,
        *,
        step: Optional[str] = None,
        template: Optional[str] = None,
        params: Optional[dict] = None,
    ) -> PromptResult:
        return self._run(self._prompt_async(session_id, text, step, template, params))

    async def _prompt_async(
        self,
        session_id: str,
        text: str,
        step: Optional[str],
        template: Optional[str] = None,
        params: Optional[dict] = None,
    ) -> PromptResult:
        assert self._client is not None
        self._client.reset()

        step_audit: Optional[StepAudit] = None
        if self._audit is not None:
            step_audit = self._audit.start_step(step or template or "prompt")
            step_audit.session_id = session_id
            step_audit.template = template
            step_audit.params = params or {}
            step_audit.record(
                "prompt",
                {
                    "session_id": session_id,
                    "template": template,
                    "params": params or {},
                    "text": text,
                },
            )
        self._client.set_audit(step_audit)

        try:
            resp = await self._conn.prompt(
                session_id=session_id, prompt=[text_block(text)]
            )
            usage_dict = _usage_to_dict(resp.usage) if resp.usage else dict(
                _usage_to_dict(self._client.last_usage)
            )
            if step_audit is not None:
                step_audit.record(
                    "prompt_response",
                    {"stop_reason": resp.stop_reason, "usage": resp.usage},
                )
                step_audit.finalize(resp.stop_reason, usage_dict or None)
            return PromptResult(
                text="".join(self._client.text_chunks).strip(),
                stop_reason=resp.stop_reason,
                usage=resp.usage or self._client.last_usage,
                usage_dict=usage_dict,
                tool_calls=list(self._client.tool_calls),
            )
        finally:
            self._client.set_audit(None)

    def end_session(self, session_id: str) -> None:
        """Discard session state.

        Kiro CLI does not implement ``session/close`` (ACP returns "Method not
        found"), so this is a no-op today. A fresh session is created for the next
        step regardless, which is what guarantees clean context. Kept as an explicit
        seam so callers can pair ``new_session``/``end_session``.
        """
        return None

    # --- context manager -------------------------------------------------

    def __enter__(self) -> "KiroACPClient":
        return self.start()

    def __exit__(self, *exc: Any) -> None:
        self.close()
