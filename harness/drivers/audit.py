"""Structured audit capture for AEW ACP runs.

Shipped verbatim by harness-bootstrap into every generated harness (`harness/drivers/`),
alongside `acp_client.py` and `agents.py` — the same transport this repo's own pipeline
uses to talk to Kiro, so a generated harness gets the identical redacted, replayable
per-step JSON audit trail, not a reinvention of it.

Every Kiro agent turn over ACP produces a stream of structured JSON events
(assistant text, reasoning, tool calls with inputs/outputs, permission decisions,
token/cost usage). This module records that stream for audit.

Two artifacts per step, under ``agents/{aew_id}/aew_plan_build/audit/``:

- ``NN_{step}.raw.jsonl`` — one JSON object per line, faithful and complete (every
  ACP event in order, values redacted for secrets but never truncated). Replayable.
- ``NN_{step}.summary.json`` — a cleaned, human-readable per-step summary. Large
  fields (tool inputs/outputs, assistant/thinking text) are truncated to previews;
  the full content lives in the raw log.

Plus a run-level ``manifest.json`` (steps, timing, stop reasons, token/cost totals).

Redaction: recursively replaces values of secret-bearing keys and scrubs known
secret substrings (env values such as GITHUB_PAT, KIRO_API_KEY) from all strings.
Full capture, secrets removed.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

REDACTED = "\u00abREDACTED\u00bb"  # «REDACTED»

# Keys whose values are always redacted (case-insensitive substring match).
_SECRET_KEY_PATTERN = re.compile(
    r"(token|secret|password|passwd|api[_-]?key|authorization|auth[_-]?token"
    r"|access[_-]?key|aws[_-]?access|aws[_-]?secret|github[_-]?pat|credential"
    r"|bearer|private[_-]?key)",
    re.IGNORECASE,
)

# Env var names whose *values* are scrubbed from every captured string.
_SECRET_ENV_VARS = (
    "GITHUB_PAT",
    "GH_TOKEN",
    "KIRO_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "CLOUDFLARED_TUNNEL_TOKEN",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
)

# Credential-shaped substrings scrubbed from every captured string, regardless of
# whether the corresponding env var is set. Second layer of defense.
_SECRET_VALUE_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),          # GitHub tokens (ghp_, gho_, ...)
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),         # GitHub fine-grained PAT
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                  # OpenAI-style keys
    re.compile(r"sk-ant-[A-Za-z0-9\-]{20,}"),            # Anthropic keys
    re.compile(r"AKIA[0-9A-Z]{16}"),                     # AWS access key id
    re.compile(r"aws_secret_access_key\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),        # Slack tokens
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),  # JWT
]

# Summary truncation limits (raw log is never truncated).
_SUMMARY_TEXT_LIMIT = 4000
_SUMMARY_FIELD_LIMIT = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secret_values() -> List[str]:
    vals = []
    for name in _SECRET_ENV_VARS:
        v = os.getenv(name)
        if v and len(v) >= 6:  # avoid scrubbing trivially short/empty values
            vals.append(v)
    return vals


def redact(obj: Any, _secrets: Optional[List[str]] = None) -> Any:
    """Recursively redact secret-bearing keys and known secret substrings.

    Does not truncate — only removes secrets. Used for the raw log.
    """
    if _secrets is None:
        _secrets = _secret_values()

    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(k, str) and _SECRET_KEY_PATTERN.search(k):
                out[k] = REDACTED
            else:
                out[k] = redact(v, _secrets)
        return out
    if isinstance(obj, (list, tuple)):
        return [redact(v, _secrets) for v in obj]
    if isinstance(obj, str):
        s = obj
        for secret in _secrets:
            if secret in s:
                s = s.replace(secret, REDACTED)
        for pat in _SECRET_VALUE_PATTERNS:
            s = pat.sub(REDACTED, s)
        return s
    return obj


def _truncate(value: Any, limit: int) -> Any:
    """Truncate strings (and stringify + truncate large non-strings) for summaries."""
    if isinstance(value, str):
        if len(value) > limit:
            return value[:limit] + f"\u2026[truncated {len(value) - limit} chars]"
        return value
    if isinstance(value, (dict, list)):
        try:
            rendered = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            rendered = str(value)
        if len(rendered) > limit:
            return rendered[:limit] + f"\u2026[truncated {len(rendered) - limit} chars]"
        return value
    return value


def _model_to_dict(obj: Any) -> Any:
    """Best-effort, *recursive* convert of an ACP pydantic model to plain JSON data.
    Call sites (e.g. `acp_client.py`'s `request_permission`) often pass a plain dict
    wrapping a model (`{"tool_call": tool_call, ...}`) rather than a model itself, so
    this has to walk dicts/lists too — stopping at the top level left nested models
    unconverted and crashed `json.dumps` in `record()`."""
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        try:
            return dump(mode="json", by_alias=True, exclude_none=True)
        except Exception:  # noqa: BLE001
            pass
    if isinstance(obj, dict):
        return {k: _model_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_model_to_dict(v) for v in obj]
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    return str(obj)


class StepAudit:
    """Accumulates events for a single step and writes raw JSONL + summary JSON."""

    def __init__(self, sink: "AuditSink", index: int, step: str) -> None:
        self._sink = sink
        self.index = index
        self.step = step
        self.session_id: Optional[str] = None
        self.template: Optional[str] = None
        self.params: Dict[str, Any] = {}
        self.started_at = _now_iso()
        self._start_perf = time.perf_counter()
        self.ended_at: Optional[str] = None
        self.duration_ms: Optional[int] = None
        self.stop_reason: Optional[str] = None

        self._seq = 0
        self._raw_path = os.path.join(
            sink.audit_dir, f"{index:02d}_{_slug(step)}.raw.jsonl"
        )
        self._summary_path = os.path.join(
            sink.audit_dir, f"{index:02d}_{_slug(step)}.summary.json"
        )
        self._raw_fh = open(self._raw_path, "a", encoding="utf-8")

        # Streaming redactors guard secrets split across chunk boundaries in the
        # faithful raw log (assistant + thinking streams tracked separately).
        self._msg_redactor = StreamRedactor(sink.secrets)
        self._thought_redactor = StreamRedactor(sink.secrets)

        # Structured accumulators for the summary.
        self.assistant_chunks: List[str] = []
        self.thinking_chunks: List[str] = []
        self.tool_calls: Dict[str, Dict[str, Any]] = {}
        self.tool_call_order: List[str] = []
        self.permissions: List[Dict[str, Any]] = []
        self.usage: Optional[Dict[str, Any]] = None

    # --- raw event log ---------------------------------------------------

    def record(self, event_type: str, payload: Any) -> None:
        """Append one redacted event to the raw JSONL log (never truncated)."""
        self._seq += 1
        line = {
            "ts": _now_iso(),
            "aew_id": self._sink.aew_id,
            "step": self.step,
            "seq": self._seq,
            "type": event_type,
            "payload": redact(_model_to_dict(payload), self._sink.secrets),
        }
        self._raw_fh.write(json.dumps(line, ensure_ascii=False) + "\n")
        self._raw_fh.flush()

    def record_text_chunk(self, event_type: str, payload: Any, text: str, is_thought: bool) -> None:
        """Record a streaming text chunk, redacting across chunk boundaries.

        The chunk's own ``content.text`` is replaced with the stream-redactor's safe
        emission so a secret split across two chunks cannot leak in the raw log.
        """
        redactor = self._thought_redactor if is_thought else self._msg_redactor
        safe_text = redactor.feed(text)
        data = _model_to_dict(payload)
        # Overwrite the text field in the serialized payload with the safe emission.
        content = data.get("content") if isinstance(data, dict) else None
        if isinstance(content, dict):
            content["text"] = safe_text
        self._seq += 1
        line = {
            "ts": _now_iso(),
            "aew_id": self._sink.aew_id,
            "step": self.step,
            "seq": self._seq,
            "type": event_type,
            "payload": redact(data, self._sink.secrets),
        }
        self._raw_fh.write(json.dumps(line, ensure_ascii=False) + "\n")
        self._raw_fh.flush()

    # --- structured accumulation (for summary) ---------------------------

    def add_assistant_text(self, text: str) -> None:
        self.assistant_chunks.append(text)

    def add_thinking_text(self, text: str) -> None:
        self.thinking_chunks.append(text)

    def upsert_tool_call(self, data: Dict[str, Any]) -> None:
        tid = data.get("tool_call_id") or data.get("toolCallId") or f"_{len(self.tool_calls)}"
        existing = self.tool_calls.get(tid)
        if existing is None:
            self.tool_calls[tid] = data
            self.tool_call_order.append(tid)
        else:
            existing.update({k: v for k, v in data.items() if v is not None})

    def add_permission(self, tool: str, decision: str, option: Optional[str]) -> None:
        self.permissions.append({"tool": tool, "decision": decision, "option": option})

    def set_usage(self, usage: Dict[str, Any]) -> None:
        self.usage = usage

    # --- finalize --------------------------------------------------------

    def finalize(self, stop_reason: Optional[str], usage: Optional[Dict[str, Any]]) -> None:
        # Flush any carried streaming tails to the raw log (redacted).
        for redactor, kind in (
            (self._msg_redactor, "agent_message_chunk"),
            (self._thought_redactor, "agent_thought_chunk"),
        ):
            tail = redactor.flush()
            if tail:
                self._seq += 1
                line = {
                    "ts": _now_iso(),
                    "aew_id": self._sink.aew_id,
                    "step": self.step,
                    "seq": self._seq,
                    "type": f"session_update:{kind}:flush",
                    "payload": {"content": {"text": tail, "type": "text"}},
                }
                self._raw_fh.write(json.dumps(line, ensure_ascii=False) + "\n")
                self._raw_fh.flush()

        self.stop_reason = stop_reason
        if usage:
            self.usage = usage
        self.ended_at = _now_iso()
        self.duration_ms = int((time.perf_counter() - self._start_perf) * 1000)

        secrets = self._sink.secrets
        tool_summaries = []
        for tid in self.tool_call_order:
            tc = redact(self.tool_calls[tid], secrets)
            tool_summaries.append(
                {
                    "tool_call_id": tid,
                    "title": tc.get("title"),
                    "kind": tc.get("kind"),
                    "status": tc.get("status"),
                    "raw_input": _truncate(tc.get("raw_input") or tc.get("rawInput"), _SUMMARY_FIELD_LIMIT),
                    "raw_output": _truncate(tc.get("raw_output") or tc.get("rawOutput"), _SUMMARY_FIELD_LIMIT),
                }
            )

        assistant_text = redact("".join(self.assistant_chunks).strip(), secrets)
        thinking_text = redact("".join(self.thinking_chunks).strip(), secrets)

        summary = {
            "aew_id": self._sink.aew_id,
            "index": self.index,
            "step": self.step,
            "template": self.template,
            "params": {
                k: _truncate(redact(v, secrets), _SUMMARY_FIELD_LIMIT)
                for k, v in (self.params or {}).items()
            },
            "session_id": self.session_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "stop_reason": self.stop_reason,
            "assistant_text": _truncate(assistant_text, _SUMMARY_TEXT_LIMIT),
            "thinking_text": _truncate(thinking_text, _SUMMARY_TEXT_LIMIT),
            "tool_calls": tool_summaries,
            "permissions": self.permissions,
            "usage": self.usage,
            "raw_log": os.path.basename(self._raw_path),
        }
        with open(self._summary_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)

        try:
            self._raw_fh.close()
        except Exception:  # noqa: BLE001
            pass

        self._sink._record_step_manifest(summary)


class AuditSink:
    """Owns the audit directory and per-run manifest for one AEW execution."""

    def __init__(self, aew_id: str, base_dir: str, trigger_type: str = "aew_plan_build") -> None:
        """`base_dir` is the audit tree's own root — both shipped callers pass
        `base_dir="agents"`, matching this module's documented `agents/{aew_id}/...`
        layout; it must not also be appended here (that previously produced
        `agents/agents/...`, which `known_files()`'s `agents` skip-dir then had to
        match exactly to stay excluded from PBI grounding — now it doesn't need to)."""
        self.aew_id = aew_id
        self.audit_dir = os.path.join(base_dir, aew_id, trigger_type, "audit")
        os.makedirs(self.audit_dir, exist_ok=True)
        self.secrets = _secret_values()
        self._lock = threading.Lock()
        self._step_index = 0
        self._manifest_steps: List[Dict[str, Any]] = []
        self._manifest_path = os.path.join(self.audit_dir, "manifest.json")
        self._run_started = _now_iso()

    def start_step(self, step: str) -> StepAudit:
        with self._lock:
            self._step_index += 1
            idx = self._step_index
        return StepAudit(self, idx, step)

    def _record_step_manifest(self, summary: Dict[str, Any]) -> None:
        with self._lock:
            self._manifest_steps.append(
                {
                    "index": summary["index"],
                    "step": summary["step"],
                    "template": summary.get("template"),
                    "duration_ms": summary["duration_ms"],
                    "stop_reason": summary["stop_reason"],
                    "tool_call_count": len(summary["tool_calls"]),
                    "usage": summary["usage"],
                    "summary_file": f"{summary['index']:02d}_{_slug(summary['step'])}.summary.json",
                }
            )
            self._write_manifest()

    def _write_manifest(self) -> None:
        totals = {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0}
        # Track whether ACP actually reported any usage. On current Kiro builds the ACP
        # PromptResponse is {stop_reason, usage: null, _meta: null} — no usage is exposed
        # over the protocol at all. (Kiro meters spend in CREDITS, not tokens, and that
        # accounting lives account-side, not on the ACP surface.) So zero totals here
        # mean "not reported over ACP", NOT "zero cost". Surface that honestly; a
        # credit/cost KPI must come from a separate account-side source, not this stream.
        usage_reported = False
        for s in self._manifest_steps:
            u = s.get("usage") or {}
            for k in totals:
                v = u.get(k)
                if isinstance(v, (int, float)):
                    totals[k] += int(v)
                    usage_reported = True
        manifest = {
            "aew_id": self.aew_id,
            "run_started_at": self._run_started,
            "updated_at": _now_iso(),
            "steps": self._manifest_steps,
            "totals": totals,
            "usage_reported": usage_reported,
        }
        with open(self._manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "step"


# Longest credential fragment we guard across streaming chunk boundaries.
_STREAM_CARRY = 120


class StreamRedactor:
    """Redacts secrets from a token stream that may split them across chunks.

    Concatenates a small carried tail with each incoming chunk, redacts the joined
    text, emits everything except a new trailing tail (which is carried forward in
    case a secret straddles the next boundary). Call ``flush()`` at end of stream.
    """

    def __init__(self, secrets: Optional[List[str]] = None) -> None:
        self._secrets = secrets if secrets is not None else _secret_values()
        self._carry = ""

    def feed(self, chunk: str) -> str:
        combined = self._carry + chunk
        redacted = redact(combined, self._secrets)
        # If redaction collapsed length, don't risk slicing mid-marker: carry all.
        if len(redacted) <= _STREAM_CARRY or REDACTED in redacted[-_STREAM_CARRY:]:
            self._carry = redacted
            return ""
        emit = redacted[:-_STREAM_CARRY]
        self._carry = redacted[-_STREAM_CARRY:]
        return emit

    def flush(self) -> str:
        out = redact(self._carry, self._secrets)
        self._carry = ""
        return out
