"""Render a deployed prompt template and extract an agent's output envelope.

Shipped verbatim by harness-bootstrap into every generated harness (`harness/drivers/`)
— the runtime half of `bootstrap/prompts.py`'s rendering logic, trimmed to what a
deployed harness actually needs: a template under `.kiro/prompts/<name>.md` declares its
inputs in a ``## Variables`` block (``name: $1`` …) or takes one bare ``$ARGUMENTS``, and
its output as one ``<<<NAME>>> … <<<END NAME>>>`` envelope. By the time a template is
deployed here, any ``{{ref:...}}`` it once had was already resolved at build time, so
this module never needs to re-resolve one — only substitute variables and extract the
reply's envelope. A harness's own `run_agent` calls `render(...)` to build the text it
sends to `invoke_kiro` (`agents.py`), and `extract(...)` (or `envelope_name(...)`, when it
doesn't already know which envelope a template declares) to parse the reply.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

_VARS_BLOCK = re.compile(r"^##\s+Variables\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
_VAR_LINE = re.compile(r"^\s*([A-Za-z_][\w]*)\s*:\s*\$(\d+)\s*$", re.M)
_ENVELOPE_OPEN = re.compile(r"<<<([A-Z][A-Z_]*)>>>")


class PromptError(Exception):
    pass


@dataclass
class Rendered:
    name: str
    text: str
    params: Dict[str, str]


def declared_variables(body: str) -> List[str]:
    m = _VARS_BLOCK.search(body)
    if not m:
        return []
    pairs = sorted(((int(n), v) for v, n in _VAR_LINE.findall(m.group(1))))
    return [v for _, v in pairs]


def envelope_name(body: str) -> Optional[str]:
    """The first ``<<<MARKER>>>`` a template's own output contract declares, so a
    generic caller can parse the reply without separately tracking each prompt's
    envelope name."""
    m = _ENVELOPE_OPEN.search(body)
    return m.group(1) if m else None


def _stringify(value: object) -> str:
    if isinstance(value, str):
        return value
    if hasattr(value, "model_dump_json"):
        return value.model_dump_json(indent=2)
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def render(prompts_dir: str, name: str, **values: object) -> Rendered:
    """Render ``<prompts_dir>/<name>.md``.

    A template with a named ``## Variables`` block (``foo: $1`` …) takes exactly those
    keyword arguments, substituted at their ``$1``/``$2``/… placeholders in the body. A
    template declaring none (bare ``$ARGUMENTS``) takes exactly one keyword, ``ARGUMENTS``
    — since the Variables block (including the literal word ``$ARGUMENTS``) is stripped
    before the text is sent, substitution can't happen in place; the value is appended
    instead, under its own heading, which is where the template's own ``## Instructions``
    already told the agent to find it.
    """
    path = os.path.join(prompts_dir, f"{name}.md")
    if not os.path.isfile(path):
        raise PromptError(f"no template {path}")
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    names = declared_variables(body)
    if not names:
        bad = sorted(set(values) - {"ARGUMENTS"})
        if bad:
            raise PromptError(f"template '{name}' takes no named variables, only ARGUMENTS; got {bad}")
        if "ARGUMENTS" not in values:
            raise PromptError(f"template '{name}' needs ARGUMENTS")
        # The Variables block (and its literal "$ARGUMENTS" line) is metadata for the
        # driver, not sent to the agent — so the real value is appended, not substituted.
        text = _VARS_BLOCK.sub("", body, count=1).rstrip() + "\n\n## Input\n\n" + _stringify(values["ARGUMENTS"])
        return Rendered(name=name, text=text, params={"ARGUMENTS": _stringify(values["ARGUMENTS"])})
    missing = [n for n in names if n not in values]
    if missing:
        raise PromptError(f"template '{name}' needs {missing}")
    extra = [k for k in values if k not in names]
    if extra:
        raise PromptError(f"template '{name}' does not declare {extra}")
    params = {n: _stringify(values[n]) for n in names}
    # The Variables block declares inputs for the driver; it is not sent to the agent.
    text = _VARS_BLOCK.sub("", body, count=1)
    text = text.replace("$$", "\0DOLLAR\0")
    by_index = {str(i): params[n] for i, n in enumerate(names, start=1)}
    # One pass, so a value that happens to contain "$2" is never re-substituted.
    text = re.sub(r"\$(\d+)", lambda m: by_index.get(m.group(1), m.group(0)), text)
    text = text.replace("\0DOLLAR\0", "$")
    return Rendered(name=name, text=text, params=params)


def extract(text: str, marker: str) -> Optional[str]:
    """Content of the LAST ``<<<MARKER>>> … <<<END MARKER>>>`` envelope, or None.

    The last one wins: a model that restates the output contract ("reply with
    <<<X>>> ... <<<END X>>>") before answering must not have the restatement parsed.
    """
    found = re.findall(rf"<<<{re.escape(marker)}>>>\s*(.*?)\s*<<<END {re.escape(marker)}>>>",
                       text or "", re.S)
    return found[-1].strip() if found else None
