#!/usr/bin/env python3
"""guard-answer-key: blocking pre_tool_use hook (matcher: fs_write|execute_bash).

Reads the pending tool event as JSON on stdin.
  exit 0  -> allow
  exit 2  -> block (reason on stderr)

Blocks writes to, and shell commands that modify, the frozen answer-key paths.
Reads are allowed. Fails CLOSED: any problem reading or understanding the event
blocks the call. Human override: HARNESS_UNLOCK=1.

Python 3 standard library only. No network.
"""
import fnmatch
import json
import os
import posixpath
import re
import shlex
import sys

GUARDED = (
    "evals/",
    ".kiro/agents/",
    ".kiro/hooks/",
    "scripts/hooks/",
    "harness/drivers/",
    "harness/audit/",
    # mitsui-harness: the rules and gates an agent must not weaken (review finding)
    ".kiro/steering/",
    ".kiro/prompts/",
    "harness/workflows/",
    "harness/run_story.py",
    "harness/context/",
    "scripts/validate.sh",
    "HARNESS.md",
)
GUARDS = tuple(g.casefold().rstrip("/") for g in GUARDED)

MAX_DEPTH = 6


class Block(Exception):
    pass


# --------------------------------------------------------------------------
# Roots and path normalisation (repo-relative; a guarded name inside an
# unrelated path such as src/evals/ or myevals/ does not match)
# --------------------------------------------------------------------------
ROOTS = []
_MENTION_RE = None


def _slash(p):
    return p.replace("\\", "/").casefold().rstrip("/")


def _find_git_root(start):
    cur = os.path.abspath(start)
    for _ in range(64):
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def init_roots(event_cwd):
    global _MENTION_RE
    cands = []
    try:
        cwd = os.getcwd()
    except OSError:
        cwd = None
    if cwd:
        root = _find_git_root(cwd)
        if root:
            cands.append(root)
        cands.append(cwd)
    for key in ("CLAUDE_PROJECT_DIR", "KIRO_PROJECT_DIR", "PWD"):
        if os.environ.get(key):
            cands.append(os.environ[key])
    if isinstance(event_cwd, str) and event_cwd:
        root = _find_git_root(event_cwd) if os.path.isdir(event_cwd) else None
        if root:
            cands.append(root)
        cands.append(event_cwd)
    for c in cands:
        r = _slash(c)
        if not r:
            continue
        forms = [r]
        m = re.match(r"^([a-z]):(/.*)?$", r)
        if m:
            rest = m.group(2) or ""
            forms += ["/" + m.group(1) + rest, "/mnt/" + m.group(1) + rest]
        for f in forms:
            if f not in ROOTS:
                ROOTS.append(f)
    prefixes = ["", "./"] + [r + "/" for r in ROOTS]
    alts = []
    for g in GUARDS:
        for pre in prefixes:
            alts.append(re.escape(pre + g))
    _MENTION_RE = re.compile(r"(?<![\w.\-/~])(?:" + "|".join(alts) + r")(?:/|(?![\w.\-]))")


def mentions_guard(text):
    return bool(_MENTION_RE.search(text.replace("\\", "/").casefold()))


def norm(p, cwd):
    """Return repo-relative normalised path, empty string for repo root, None if
    outside the repo, '?' if it cannot be resolved (variable expansion, unknown cwd)."""
    s = p.strip().strip("'\"").replace("\\", "/")
    if not s:
        return None
    if "$" in s or "`" in s:
        return "?"
    if s.startswith("~"):
        return None
    cf = s.casefold()
    if cf.startswith("/") or re.match(r"^[a-z]:/", cf):
        for root in ROOTS:
            if cf == root or cf.startswith(root + "/"):
                rel = posixpath.normpath(cf[len(root):].lstrip("/") or ".")
                if rel == ".":
                    return ""
                if rel.startswith(".."):
                    return None
                return rel
        return None
    if cwd == "!":
        return None
    if cwd == "?":
        return "?"
    q = posixpath.normpath(posixpath.join(cwd, cf))
    if q == ".":
        return ""
    if q == ".." or q.startswith("../"):
        return None
    return q


def guarded(tok, cwd, broad=False):
    """True if tok refers to (or, when broad, contains or is a parent of) a guarded path."""
    n = norm(tok, cwd)
    if n is None:
        return False
    if n == "?":
        return True
    if any(c in n for c in "*?["):
        for g in GUARDS:
            if fnmatch.fnmatch(g, n) or fnmatch.fnmatch(g + "/x", n):
                return True
        return False
    for g in GUARDS:
        if n == g or n.startswith(g + "/"):
            return True
        if broad and (n == "" or g.startswith(n + "/")):
            return True
    return False


def resolve_cd(target, cwd):
    if not target or target == "-":
        return "?"
    n = norm(target, cwd)
    if n is None:
        return "!"
    return n


# --------------------------------------------------------------------------
# Shell command analysis
# --------------------------------------------------------------------------
RED = re.compile(r"[0-9]*(?:&>>?|>>?|<<<?|<|>\||>&|<&)")
GLUED = re.compile(r"^[0-9&]*>{1,2}[|&]?(.+)$")
SEP = re.compile(r"^[;&|()]+$")

WRAPPERS = {"sudo", "doas", "env", "command", "nohup", "time", "nice", "xargs",
            "exec", "builtin", "stdbuf", "timeout", "setsid", "ionice"}
VALOPTS = {"-u", "-g", "-n", "-I", "-L", "-P", "-s", "-S", "-C", "-E", "-d"}
CD = {"cd", "pushd", "chdir", "set-location", "sl"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "cmd", "powershell", "pwsh"}
INTERPRETERS = {"python", "python2", "python3", "py", "node", "nodejs", "deno", "bun",
                "perl", "ruby", "php", "lua", "awk", "gawk", "mawk"}

MUT_ANY = {"rm", "rmdir", "unlink", "shred", "mv", "touch", "truncate", "tee", "ln",
           "chmod", "chown", "chgrp", "mkdir", "patch", "mkfifo", "setfacl", "chattr",
           "curl", "wget", "vi", "vim", "nvim", "nano", "emacs", "ed", "ex",
           "del", "erase", "rd", "ren", "rename", "move", "move-item", "remove-item",
           "ri", "set-content", "add-content", "out-file", "new-item", "clear-content",
           "rename-item", "sc", "ac", "ni", "tee-object", "set-itemproperty"}
BROAD = {"rm", "rmdir", "unlink", "shred", "mv", "del", "erase", "rd", "move",
         "move-item", "remove-item", "ri", "rename", "ren", "rename-item"}
DEST_LAST = {"cp", "install", "rsync", "copy", "xcopy", "robocopy", "copy-item",
             "cpi", "scp", "ditto"}

WRITE_MARK = re.compile(
    r"\b(open|write\w*|unlink|remove|rmtree|rename|replace|copy\w*|move|mkdir|chmod|"
    r"truncate|symlink|append\w*|rm|mv|cp|sed|tee|fs|sync|dump|save)\b|>>?|\bw\+?b?['\"]|\s-i\b|\s-pi\b",
    re.I,
)


def cmd_base(tok):
    b = posixpath.basename(tok.replace("\\", "/")).casefold()
    if b.endswith(".exe"):
        b = b[:-4]
    return b


def check_command(text, depth, st):
    if depth > MAX_DEPTH:
        raise Block("shell command nested too deeply to analyse")
    text = text.replace("\n", " ; ").replace("`", " ; ")
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        lex.commenters = ""
        lex.escape = ""
        lex.escapedquotes = ""
        toks = list(lex)
    except ValueError:
        toks = text.split()
    saved_all = st["all"]
    st["all"] = toks
    seg = []
    for t in toks + [";"]:
        if SEP.match(t):
            if seg:
                check_segment(seg, depth, st)
            seg = []
        else:
            seg.append(t)
    st["all"] = saved_all


def check_segment(toks, depth, st):
    args = []
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if RED.fullmatch(t):
            if ">" in t and i + 1 < n and guarded(toks[i + 1], st["cwd"]):
                raise Block("redirect writes to guarded path %r" % toks[i + 1])
            i += 2
            continue
        if re.fullmatch(r"[0-9]+", t) and i + 1 < n and RED.fullmatch(toks[i + 1]):
            i += 1
            continue
        m = GLUED.match(t)
        if m:
            if guarded(m.group(1), st["cwd"]):
                raise Block("redirect writes to guarded path %r" % m.group(1))
            i += 1
            continue
        args.append(t)
        i += 1

    xargs = False
    while args:
        a = args[0]
        if re.match(r"^[A-Za-z_]\w*=", a):
            args.pop(0)
            continue
        b = cmd_base(a)
        if b in WRAPPERS:
            args.pop(0)
            if b == "xargs":
                xargs = True
            while args and args[0].startswith("-"):
                opt = args.pop(0)
                if opt in VALOPTS and args:
                    args.pop(0)
            if b == "timeout" and args and re.fullmatch(r"[\d.]+[smhd]?", args[0]):
                args.pop(0)
            continue
        break
    if not args:
        return

    cmd = cmd_base(args[0])
    rest = args[1:]
    if xargs:
        rest = rest + list(st["all"])
    cwd = st["cwd"]

    def g(tok, broad=False):
        return guarded(tok, cwd, broad)

    def deny(why):
        raise Block("%s: %s" % (cmd, why))

    # cd tracking
    if cmd in CD:
        target = next((a for a in rest if not a.startswith("-")), "")
        st["cwd"] = resolve_cd(target, cwd)
        return

    # nested shells
    if cmd in SHELLS:
        for idx, a in enumerate(rest):
            if re.match(r"^[-/][a-z]*c(ommand)?$", a.casefold()) and idx + 1 < len(rest):
                check_command(" ".join(rest[idx + 1:]), depth + 1, dict(st))
                return
        return
    if cmd == "eval":
        check_command(" ".join(rest), depth + 1, dict(st))
        return

    if cmd == "git":
        check_git(rest, st, deny)
        return

    if cmd == "find":
        if any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf", "-fls") for a in rest):
            for a in rest:
                if a.startswith("-") or a in ("(", "!"):
                    break
                if g(a, True):
                    deny("destructive find over guarded path %r" % a)
        return

    if cmd == "sed":
        inplace = any(re.match(r"^-[A-Za-z]*i[A-Za-z]*(\..*)?$", a) or a.startswith("--in-place") for a in rest)
        if inplace:
            for a in rest:
                if not a.startswith("-") and g(a):
                    deny("in-place edit of guarded path %r" % a)
        return

    if cmd == "dd":
        for a in rest:
            if a.startswith("of=") and g(a[3:]):
                deny("writes to guarded path %r" % a[3:])
        return

    if cmd in DEST_LAST:
        dests = []
        plain = []
        skip = False
        for idx, a in enumerate(rest):
            if skip:
                skip = False
                continue
            if a in ("-t", "--target-directory") and idx + 1 < len(rest):
                dests.append(rest[idx + 1])
                skip = True
                continue
            if a.startswith("--target-directory="):
                dests.append(a.split("=", 1)[1])
                continue
            if a.startswith("-") or re.fullmatch(r"/[A-Za-z]", a):
                continue
            plain.append(a)
        if plain:
            dests.append(plain[-1])
        for d in dests:
            if g(d):
                deny("writes to guarded path %r" % d)
        return

    if cmd in MUT_ANY:
        broad = cmd in BROAD
        for a in rest:
            if a.startswith("-") and "=" not in a:
                continue
            cands = [a]
            if "=" in a:
                cands.append(a.split("=", 1)[1])
            for c in cands:
                if c and g(c, broad):
                    deny("modifies guarded path %r" % c)
        return

    if cmd in INTERPRETERS:
        text = " ".join(rest)
        if re.search(r"(^|\s)-[A-Za-z]*i[A-Za-z]*(\.\S*)?(\s|$)", text) and cmd in ("perl", "ruby"):
            for a in rest:
                if not a.startswith("-") and g(a):
                    deny("in-place edit of guarded path %r" % a)
        if mentions_guard(text) and WRITE_MARK.search(text):
            deny("inline code appears to write to a guarded path")
        return


def check_git(rest, st, deny):
    cwd = st["cwd"]
    i = 0
    while i < len(rest) and rest[i].startswith("-"):
        opt = rest[i]
        if opt == "-C" and i + 1 < len(rest):
            cwd = resolve_cd(rest[i + 1], cwd)
            i += 2
            continue
        if opt in ("-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(rest):
            i += 2
            continue
        i += 1
    if i >= len(rest):
        return
    sub = rest[i]
    sa = rest[i + 1:]

    def g(tok, broad=False):
        return guarded(tok, cwd, broad)

    if sub == "reset" and "--hard" in sa:
        deny("git reset --hard can overwrite guarded paths")
    if sub == "clean":
        dry = any(a in ("-n", "--dry-run") or re.fullmatch(r"-[A-Za-z]*n[A-Za-z]*", a) for a in sa)
        if not dry:
            deny("git clean can delete guarded paths")
    if sub in ("checkout", "restore", "switch"):
        if sub in ("checkout", "switch") and any(a in ("-f", "--force") for a in sa):
            deny("forced %s can overwrite guarded paths" % sub)
        for a in sa:
            if a == "--" or a.startswith("-"):
                continue
            if a in (":/", ":(top)") or g(a, True):
                deny("git %s of guarded path %r" % (sub, a))
    if sub in ("rm", "mv"):
        for a in sa:
            if not a.startswith("-") and g(a, True):
                deny("git %s of guarded path %r" % (sub, a))


# --------------------------------------------------------------------------
# Event handling
# --------------------------------------------------------------------------
def walk(obj, key="", depth=0):
    if depth > 50:
        raise Block("event nested too deeply")
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, str(k), depth + 1)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from walk(v, key, depth + 1)
    elif isinstance(obj, str):
        yield key, obj
        s = obj.lstrip()
        if s[:1] in ("{", "[") and depth < 10:
            try:
                inner = json.loads(s)
            except ValueError:
                return
            yield from walk(inner, key, depth + 1)


def tool_name(event):
    if not isinstance(event, dict):
        return ""
    for k in ("tool_name", "toolName", "tool", "name"):
        v = event.get(k)
        if isinstance(v, dict):
            v = v.get("name")
        if isinstance(v, str) and v:
            return v
    return ""


def tool_kind(name):
    n = name.casefold()
    if re.search(r"write|edit|create|replace|patch|insert|append|save", n):
        return "write"
    if re.search(r"bash|shell|exec|command|terminal|run", n):
        return "shell"
    if re.search(r"read|view|grep|glob|list|search|find|web|fetch", n):
        return "read"
    return "unknown"


def run():
    if os.environ.get("HARNESS_UNLOCK") == "1":
        return
    raw = sys.stdin.buffer.read().decode("utf-8", "replace")
    if not raw.strip():
        raise Block("empty hook input")
    try:
        event = json.loads(raw)
    except ValueError:
        raise Block("hook input is not valid JSON")
    strings = list(walk(event))
    if not strings:
        raise Block("hook input contains no strings to inspect")

    event_cwd = event.get("cwd") if isinstance(event, dict) else None
    init_roots(event_cwd)
    kind = tool_kind(tool_name(event))
    if kind == "read":
        return

    cwd0 = ""
    if isinstance(event_cwd, str) and event_cwd:
        n = norm(event_cwd, "")
        cwd0 = "!" if n is None else n

    if kind in ("write", "unknown"):
        for key, s in strings:
            if "\n" in s or len(s) > 1024:
                continue
            is_pathkey = re.search(r"path|file|dest|target|source|dir", key, re.I)
            if is_pathkey or not re.search(r"\s", s):
                if guarded(s, cwd0):
                    raise Block("write to guarded path %r" % s)

    if kind in ("shell", "unknown"):
        for _key, s in strings:
            check_command(s, 0, {"cwd": cwd0, "all": []})


def main():
    try:
        run()
    except Block as e:
        sys.stderr.write(
            "guard-answer-key: BLOCKED: %s. Frozen paths: %s. "
            "A human can set HARNESS_UNLOCK=1 to override.\n" % (e, ", ".join(GUARDED))
        )
        sys.exit(2)
    except SystemExit:
        raise
    except BaseException as e:  # fail closed
        sys.stderr.write("guard-answer-key: BLOCKED: could not evaluate event (%s: %s)\n" % (type(e).__name__, e))
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
