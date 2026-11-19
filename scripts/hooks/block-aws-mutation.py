#!/usr/bin/env python3
"""pre_tool_use hook: block-aws-mutation (matcher: execute_bash).

Blocks `cdk deploy|destroy|bootstrap` (and other cdk commands that change
deployed state) and AWS CLI calls that create, change or delete resources.

Contract:
  stdin  : the pending tool event as JSON.
  exit 0 : allow.
  exit 2 : block, reason on stderr.

Fail closed: an unreadable, empty or malformed event, or any internal error,
blocks. The AWS CLI check is an allowlist of read-only operations, so an
unrecognised operation is blocked.

Human override: HARNESS_UNLOCK=1 in this process's environment allows the call.
Only the environment of the hook process counts. `HARNESS_UNLOCK=1 cdk deploy`
typed inside the command does not unlock anything.
"""

import json
import os
import re
import sys

MAX_DEPTH = 6

TOOLS = {"aws", "cdk", "aws-cdk"}

# cdk subcommands that change deployed state or the bootstrap stack.
CDK_DENY = {
    "deploy", "destroy", "bootstrap", "import", "rollback", "gc",
    "watch", "refactor", "publish-assets",
    # mitsui-harness: synth runs locally for unit tests only; these need AWS credentials
    "diff", "drift",
}

# Commands that run another command; we look for the real tool among their args.
WRAPPERS = {
    "sudo", "doas", "env", "time", "nohup", "nice", "command", "exec",
    "builtin", "xargs", "timeout", "stdbuf", "watch", "aws-vault",
    "saml2aws", "runas", "start-process",
}
RUNNERS = {
    "npx", "npm", "pnpm", "yarn", "bunx", "bun", "uv", "uvx", "poetry",
    "pipx", "make", "just", "task", "nx", "turbo", "gmake", "mingw32-make",
}
SHELLS = {
    "sh", "bash", "zsh", "dash", "ksh", "fish", "pwsh", "powershell",
    "cmd", "eval", "ssh",
}
SHELL_KEYWORDS = {"{", "}", "!", "then", "do", "else", "elif", "if", "while", "until"}

# Task-runner targets that deploy (make deploy, npm run deploy:dev, cdk-deploy ...).
DEPLOY_RE = re.compile(r"^(cdk[:_-])?(deploy|destroy|bootstrap)([:_-][\w:-]*)?$")

# aws global options that consume the next token as their value.
AWS_VALUE_OPTS = {
    "--profile", "--region", "--output", "--endpoint-url", "--query",
    "--ca-bundle", "--cli-read-timeout", "--cli-connect-timeout",
    "--color", "--cli-binary-format",
}

READ_PREFIXES = (
    "describe-", "list-", "get-", "batch-get-", "lookup-", "search-",
    "head-", "estimate-", "validate-", "simulate-",
)

# Read-looking operations that return credentials or secret values. The
# harness must never see secrets, so these are blocked too.
SECRET_READS = {
    "get-secret-value", "batch-get-secret-value", "get-login-password",
    "get-session-token", "get-federation-token", "get-authorization-token",
    "get-role-credentials", "get-credentials-for-identity", "get-open-id-token",
    "get-password-data", "get-cluster-credentials",
}


def collect_strings(node, out):
    if isinstance(node, str):
        out.append(node)
        s = node.strip()
        if s[:1] in ("{", "[") and s[-1:] in ("}", "]"):
            try:
                collect_strings(json.loads(s), out)
            except ValueError:
                pass
    elif isinstance(node, dict):
        for v in node.values():
            collect_strings(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_strings(v, out)


def base(token):
    name = re.split(r"[\\/]", token)[-1].lower()
    name = re.sub(r"\.(exe|cmd|bat|ps1)$", "", name)
    if not name.startswith("@"):
        name = re.sub(r"@[^@]*$", "", name)  # npx aws-cdk@latest
    return name


def tokenize(s):
    """Split a command line into segments (lists of words) on ; & | newline ( ) `."""
    segments, cur, buf = [], [], []
    has = False
    quote = None
    i, n = 0, len(s)

    def flush():
        nonlocal buf, has
        if buf or has:
            cur.append("".join(buf))
        buf, has = [], False

    def end_segment():
        nonlocal cur
        flush()
        if cur:
            segments.append(cur)
        cur = []

    while i < n:
        c = s[i]
        if quote == "'":
            if c == "'":
                quote = None
            else:
                buf.append(c)
        elif quote == '"':
            if c == '"':
                quote = None
            elif c == "\\" and i + 1 < n and s[i + 1] in '"\\$`':
                buf.append(s[i + 1])
                i += 1
            else:
                buf.append(c)
        else:
            if c in "'\"":
                quote = c
                has = True
            elif c == "\\" and i + 1 < n and s[i + 1] in " \t\"'":
                buf.append(s[i + 1])
                i += 1
            elif c in " \t\r":
                flush()
            elif c in ";&|\n()`":
                end_segment()
            else:
                buf.append(c)
        i += 1
    end_segment()
    return segments


def check_cdk(rest):
    for t in rest:
        if t.lower() in CDK_DENY:
            return "cdk %s changes deployed AWS state" % t.lower()
    return None


def check_aws(rest):
    pos, flags = [], []
    i = 0
    while i < len(rest):
        t = rest[i]
        if t.startswith("--"):
            name = t.split("=", 1)[0].lower()
            flags.append(name)
            if "=" not in t and name in AWS_VALUE_OPTS:
                i += 1
        elif t.startswith("-") and len(t) > 1:
            flags.append(t.lower())
        else:
            pos.append(t)
        i += 1

    if not pos:
        return None  # aws --version, bare aws
    service = pos[0].lower()
    op = pos[1].lower() if len(pos) > 1 else ""
    if service == "help" or not op or op == "help":
        return None

    if op in SECRET_READS:
        return "aws %s %s reads credentials or secret values" % (service, op)
    if service == "ssm" and op.startswith("get-parameter") and "--with-decryption" in flags:
        return "aws ssm %s --with-decryption reads secret values" % op

    if service == "configure":
        if op in ("list", "get", "list-profiles"):
            return None
        return "aws configure %s changes local CLI configuration" % op
    if service == "s3":
        if op == "ls":
            return None
        return "aws s3 %s is not a read-only listing" % op
    if service == "logs" and op in ("tail", "filter-log-events"):
        return None
    if service == "dynamodb" and op in ("scan", "query"):
        return None
    if op == "wait" or op.startswith(READ_PREFIXES):
        return None
    return "aws %s %s is not on the read-only allowlist" % (service, op)


def check_segment(tokens, depth):
    if depth > MAX_DEPTH:
        return "command nesting too deep to analyse"
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t) or t in SHELL_KEYWORDS:
            i += 1
            continue
        break
    if i >= len(tokens):
        return None

    cmd = base(tokens[i])
    rest = tokens[i + 1:]

    if cmd in ("cdk", "aws-cdk"):
        return check_cdk(rest)
    if cmd == "aws":
        return check_aws(rest)

    if cmd in WRAPPERS or cmd in RUNNERS or cmd in SHELLS:
        # Find the real tool among the arguments (sudo aws ..., npx cdk ...).
        for j, t in enumerate(rest):
            if base(t) in TOOLS:
                r = check_segment(rest[j:], depth + 1)
                if r:
                    return r
                break
        # Quoted command strings (bash -c "...", watch "...", eval "...").
        for t in rest:
            if re.search(r"\s", t):
                r = check_command_string(t, depth + 1)
                if r:
                    return r
        # Task-runner targets (make deploy, npm run deploy:dev).
        if cmd in RUNNERS:
            for t in rest:
                if DEPLOY_RE.match(base(t)) or DEPLOY_RE.match(t.lower()):
                    return "%s target '%s' deploys infrastructure" % (cmd, t)
    return None


def check_command_string(s, depth=0):
    if depth > MAX_DEPTH:
        return "command nesting too deep to analyse"
    for seg in tokenize(s):
        r = check_segment(seg, depth)
        if r:
            return r
    # Command substitutions, including those inside double quotes.
    for m in re.finditer(r"\$\(([^()]*)\)|`([^`]*)`", s):
        inner = m.group(1) if m.group(1) is not None else m.group(2)
        if inner and inner != s:
            r = check_command_string(inner, depth + 1)
            if r:
                return r
    return None


def main():
    if os.environ.get("HARNESS_UNLOCK") == "1":
        sys.stderr.write("block-aws-mutation: HARNESS_UNLOCK=1 set, allowing.\n")
        return 0

    try:
        raw = sys.stdin.buffer.read().decode("utf-8", "replace")
        event = json.loads(raw)
    except Exception as exc:
        sys.stderr.write("block-aws-mutation: cannot read event (%s); blocking.\n" % type(exc).__name__)
        sys.exit(2)

    strings = []
    collect_strings(event, strings)
    if not strings:
        sys.stderr.write("block-aws-mutation: event has no readable content; blocking.\n")
        sys.exit(2)

    for s in strings:
        reason = check_command_string(s)
        if reason:
            sys.stderr.write(
                "block-aws-mutation: blocked. %s. Infrastructure changes go through the "
                "pipeline and a person (set HARNESS_UNLOCK=1 to override).\n" % reason
            )
            sys.exit(2)
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:
        sys.stderr.write("block-aws-mutation: internal error (%s); blocking.\n" % type(exc).__name__)
        sys.exit(2)
    sys.exit(code)
