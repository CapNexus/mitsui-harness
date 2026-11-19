"""Kiro CLI invocation for the AEW system (ACP transport).

Shipped verbatim by harness-bootstrap into every generated harness (`harness/drivers/`).
`invoke_kiro(text, agent=step["agent"], step=step["name"], template=prompt_name)` is the
one call a harness's own `run_agent` (the callable `loop_driver.run_loop` /
`frame_driver.run_frame` take) needs to make to run a real, fully audited Kiro turn —
call `set_audit_sink(AuditSink(...))` once at the start of a run first.

Architecture (as actually implemented):
- `aew/workflow/plan_build.py` is a deterministic, sequential Python driver. It calls
  `invoke_kiro(prompt)` once per SDLC step, in a hardcoded order, passing artifacts
  (returned strings, files on disk, git state) from one step to the next.
- Each `invoke_kiro()` call runs a single-purpose Kiro agent turn in a *fresh* ACP
  session (clean context per step — one agent, one purpose).
- The Kiro agent identity (and therefore its tool-grant boundary) is bound at
  subprocess launch via `kiro-cli acp --agent <name>`; ACP's `session/new` has no
  `agent` field, so a session cannot re-select the agent. We therefore keep ONE
  long-lived subprocess PER distinct agent name, keyed in `get_shared_client(agent)`.
  This is what makes the read-only `reviewer` actually run read-only instead of
  inheriting the `default` builder's write/shell grants.
- Transport is the Agent Client Protocol (`kiro-cli acp`, JSON-RPC 2.0 over stdio),
  which preserves Kiro's safety rails, hooks, and built-in tool ecosystem.

Kiro's own LLM is the only model in the loop. All workflow sequencing is plain Python
in `aew/workflow/plan_build.py`.
"""

import os
import sys
from typing import Dict, Optional

# Plain same-directory import, not a relative one: this file is run standalone inside
# whatever repo the harness was generated for, not necessarily as part of a package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acp_client import KIRO_CLI_PATH, KiroACPClient  # noqa: E402  (re-export KIRO_CLI_PATH)
from audit import AuditSink  # noqa: E402

__all__ = [
    "invoke_kiro",
    "KIRO_CLI_PATH",
    "get_shared_client",
    "shutdown_shared_client",
    "set_audit_sink",
]

# Lazily-initialized, process-wide ACP clients, ONE PER AGENT NAME. Each `kiro-cli acp`
# subprocess is launched with `--agent <name>`, which fixes its tool-grant boundary for
# its whole lifetime; ACP `session/new` cannot change the agent. So a distinct agent
# (e.g. the read-only `reviewer`) requires its own subprocess. Each step still gets a
# fresh session on the relevant subprocess (clean context per step).
_shared_clients: Dict[str, KiroACPClient] = {}
_audit_sink: Optional[AuditSink] = None


def set_audit_sink(sink: Optional[AuditSink]) -> None:
    """Register the audit sink for structured capture of every ACP turn.

    Call before the first `invoke_kiro()`. Attached to every existing client and to
    any client started later.
    """
    global _audit_sink
    _audit_sink = sink
    for client in _shared_clients.values():
        client.set_audit(sink)


def get_shared_client(agent: str = "default") -> KiroACPClient:
    """Return the ACP client for ``agent``, starting its subprocess on first use.

    One subprocess per distinct agent name: the agent's tool-grant boundary is fixed
    by ``kiro-cli acp --agent <name>`` at launch and cannot be changed per session, so
    each agent needs its own long-lived subprocess. Subsequent calls with the same
    ``agent`` reuse it.
    """
    client = _shared_clients.get(agent)
    if client is None:
        # `auto_approve=None` (not a hardcoded False) lets KiroACPClient read
        # AEW_AUTO_APPROVE from the environment itself: this file runs inside the
        # *deployed* harness, where the builder/reviewer agents must be able to write
        # files, run tests, and commit — unlike bootstrap/transport/agents.py (harness-
        # bootstrap's own, genuinely read-only internal analyst), which correctly keeps
        # this hardcoded to False regardless of the environment.
        client = KiroACPClient(
            agent=agent, cwd=os.getcwd(), audit=_audit_sink, auto_approve=None
        ).start()
        _shared_clients[agent] = client
    return client


def shutdown_shared_client() -> None:
    """Terminate every ACP subprocess (all agents). Safe to call multiple times."""
    while _shared_clients:
        _, client = _shared_clients.popitem()
        client.close()


def invoke_kiro(
    prompt: str,
    agent: str = "default",
    *,
    step: Optional[str] = None,
    template: Optional[str] = None,
    params: Optional[dict] = None,
) -> str:
    """Run a single Kiro agent turn over ACP and return its assistant text.

    Opens a fresh ACP session (clean context), sends the prompt, drains the update
    stream, and returns the aggregated assistant text. Non-``end_turn`` stop reasons
    (``max_tokens``, ``refusal``, etc.) are surfaced as errors.

    ``step`` labels the per-step audit artifacts. ``template``/``params`` record the
    prompt provenance (which ``.kiro/prompts`` template was rendered and with what
    substituted values) into the audit trail.
    """
    client = get_shared_client(agent)
    session_id = client.new_session(cwd=os.getcwd())
    try:
        result = client.prompt(
            session_id, prompt, step=step, template=template, params=params
        )
        if result.stop_reason != "end_turn":
            raise RuntimeError(f"kiro acp stopped: {result.stop_reason}")
        return result.text.strip()
    finally:
        client.end_session(session_id)
