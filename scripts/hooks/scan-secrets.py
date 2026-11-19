#!/usr/bin/env python3
"""pre_tool_use hook: scan-secrets (matcher: fs_write).

Reads the pending tool event as JSON on stdin and blocks (exit 2, reason on
stderr) when any string in it contains an AWS key, private key, password or
other secret value. Exit 0 allows. Fails CLOSED: if stdin cannot be read or
parsed, or anything unexpected happens, the call is blocked.

Human override: HARNESS_UNLOCK=1 allows the call (human-gated path).
Matched values are never echoed, only the rule name and a location hint.
Python 3 standard library only, no network.
"""
import json
import os
import re
import sys

ALLOW = 0
BLOCK = 2

MAX_FINDINGS = 10

# Rules that match a secret by its own shape.
SHAPE_RULES = [
    ("AWS access key id",
     re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA|AIPA|ABIA|ACCA)[A-Z0-9]{16}\b")),
    ("AWS secret access key",
     re.compile(r"(?i)aws.{0,20}?secret.{0,20}?[\"'\s:=]+[A-Za-z0-9/+=]{40}\b")),
    ("private key block",
     re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY(?: BLOCK)?-----")),
    ("GitHub token",
     re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})\b")),
    ("Slack token",
     re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key",
     re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("JSON Web Token",
     re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("credentials in URL",
     re.compile(r"\b[a-z][a-z0-9+.\-]*://[^\s:/@\"']+:[^\s/@\"']{3,}@[^\s/\"']+", re.I)),
    ("SQL Server connection string password",
     re.compile(r"(?i)\b(?:password|pwd)\s*=\s*[^;\s\"']{4,}\s*;")),
]

_KEYWORDS = (r"(?:password|passwd|pwd|passphrase|secret|secret[_-]?key|client[_-]?secret|"
             r"token|auth[_-]?token|api[_-]?key|apikey|access[_-]?key|private[_-]?key|"
             r"credentials?)")

# key: "value" / key = 'value' where the key ends in a secret keyword.
QUOTED_ASSIGN = re.compile(
    r"(?i)[\w.\-]*" + _KEYWORDS + r"[\"']?\s*(?::|=>|=)\s*[\"']([^\"'\r\n]{8,})[\"']"
)
# .env / ini style: KEY_PASSWORD=value (unquoted, whole line).
ENV_ASSIGN = re.compile(
    r"(?im)^\s*(?:export\s+)?[A-Z0-9_.\-]*" + _KEYWORDS + r"\s*=\s*([^\s\"'#]{8,})\s*$"
)

PLACEHOLDER_HINTS = (
    "${", "{{", "<", "%s", "%(", "process.env", "os.environ", "getenv",
    "secretsmanager", "ssm:", "resolve:", "example", "placeholder", "changeme",
    "change-me", "change_me", "your_", "your-", "yourpassword", "xxxx", "****",
    "redacted", "dummy", "sample", "null", "undefined",
    "none", "unsafe_unwrap", "secretvalue", "fromsecret",
)


def looks_like_reference(value):
    """True for values that point at a secret rather than being one."""
    low = value.strip().lower()
    if not low:
        return True
    if value.startswith(("$", "@", "%")):
        return True
    if low.startswith("arn:"):
        return True
    if any(h in low for h in PLACEHOLDER_HINTS):
        return True
    # Secret ids such as prod/db/credentials or my-app/secret.
    if re.fullmatch(r"[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+", value):
        return True
    # A single repeated character (e.g. ********, 00000000).
    if len(set(value)) == 1:
        return True
    return False


def collect_strings(node, out):
    """Collect every string (keys and values) in the payload."""
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str):
                out.append(k)
            collect_strings(v, out)
    elif isinstance(node, (list, tuple)):
        for v in node:
            collect_strings(v, out)
    elif node is not None and not isinstance(node, (bool, int, float)):
        out.append(str(node))


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def scan_text(text, findings):
    for name, rx in SHAPE_RULES:
        for m in rx.finditer(text):
            token = m.group(0)
            if name == "AWS access key id" and token.upper().endswith("EXAMPLE"):
                continue
            if name == "credentials in URL" and looks_like_reference(
                    token.split(":", 2)[-1].split("@")[0]):
                continue
            if name == "SQL Server connection string password":
                val = token.split("=", 1)[1].rstrip(";").strip()
                if looks_like_reference(val):
                    continue
            findings.append((name, line_of(text, m.start())))
    for name, rx in (("hard-coded secret assignment", QUOTED_ASSIGN),
                     ("hard-coded secret in env-style line", ENV_ASSIGN)):
        for m in rx.finditer(text):
            if looks_like_reference(m.group(1)):
                continue
            findings.append((name, line_of(text, m.start())))


def main():
    if os.environ.get("HARNESS_UNLOCK") == "1":
        return ALLOW

    try:
        raw = sys.stdin.buffer.read()
        if not raw.strip():
            raise ValueError("empty event")
        event = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # fail closed
        sys.stderr.write(
            "scan-secrets: BLOCKED. Could not read the tool event (%s). "
            "Failing closed.\n" % type(exc).__name__
        )
        return BLOCK

    strings = []
    collect_strings(event, strings)

    findings = []
    for s in strings:
        scan_text(s, findings)
        if len(findings) >= MAX_FINDINGS:
            break

    if findings:
        seen = []
        for name, line in findings[:MAX_FINDINGS]:
            item = "%s (line %d of a string in the payload)" % (name, line)
            if item not in seen:
                seen.append(item)
        sys.stderr.write(
            "scan-secrets: BLOCKED. The write appears to contain secret values:\n  - "
            + "\n  - ".join(seen)
            + "\nValues are not shown. Reference the secret from AWS Secrets Manager "
            "or an environment variable instead of writing it. A human can "
            "override with HARNESS_UNLOCK=1.\n"
        )
        return BLOCK
    return ALLOW


if __name__ == "__main__":
    try:
        code = main()
    except BaseException as exc:  # fail closed on any unexpected error
        try:
            sys.stderr.write(
                "scan-secrets: BLOCKED. Internal error (%s). Failing closed.\n"
                % type(exc).__name__
            )
        except Exception:
            pass
        code = BLOCK
    if code == BLOCK:
        sys.exit(2)
    sys.exit(0)
