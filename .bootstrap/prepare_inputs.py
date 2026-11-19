"""Stage mitsui-harness planning content as inputs harness-bootstrap reads unmodified.

    uv run --with python-docx --with pypdf --with openpyxl python .bootstrap/prepare_inputs.py

Writes (regenerated each run, never edited by hand):
  .bootstrap/stage/requirements/backlog.json   features F1-F14 + every story, Jira-like JSON
  .bootstrap/stage/code/                       submodule files + the declared toolchain manifest
                                               (the survey reads manifests, never docs)
  harness/context/                             .docx / .pdf / .xlsx sources as Markdown, read by
                                               the harness agents (.kiro/steering/project-context.md)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, ".bootstrap")
STAGE = os.path.join(HERE, "stage")
US = os.path.join(ROOT, "user-stories")
CHUNK = 5500   # harness-bootstrap excerpts 6,000 chars per file (BOOTSTRAP_FILE_CHARS)

FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def read(p: str) -> str:
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def write(p: str, text: str) -> None:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def front_matter(text: str):
    m = FM.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        line = line.split(" #", 1)[0].rstrip()
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def section(body: str, name: str) -> str:
    m = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return m.group(1).strip() if m else ""


# --- requirements -------------------------------------------------------------------------

def feature_list_sections() -> dict:
    """F1..F14 narrative sections from WDA-POC-Feature-List.md, keyed 'F1'."""
    text = read(os.path.join(US, "WDA-POC-Feature-List.md"))
    out = {}
    for m in re.finditer(r"^### (F\d+)\. (.+?)\n(.*?)(?=^### |^## |\Z)", text, re.S | re.M):
        out[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    return out


def build_requirements() -> list:
    items, have_dir = [], set()
    narrative = feature_list_sections()
    fdir = os.path.join(US, "features")
    for d in sorted(os.listdir(fdir)):
        fpath = os.path.join(fdir, d, "feature.md")
        if not os.path.isfile(fpath):
            continue
        meta, body = front_matter(read(fpath))
        fid = meta.get("id") or "F" + str(int(d[1:3]))
        have_dir.add(fid)
        desc = "\n\n".join(x for x in (
            section(body, "Description"),
            "Feature-level acceptance criteria:\n" + section(body, "Feature-level acceptance criteria"),
            "Order: " + (re.search(r"^Order:(.*)$", body, re.M).group(1).strip()
                         if re.search(r"^Order:(.*)$", body, re.M) else ""),
            "Open points:\n" + section(body, "Open points"),
            f"Metadata: sow={meta.get('sow')} due={meta.get('due')} "
            f"depends_on_features={meta.get('depends_on_features')} blocked_by={meta.get('blocked_by')}",
        ) if x.strip())
        items.append({"key": fid, "type": "feature", "title": meta.get("title", d), "description": desc})
        sdir = os.path.join(fdir, d, "stories")
        for s in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
            if not s.endswith(".md"):
                continue
            smeta, sbody = front_matter(read(os.path.join(sdir, s)))
            meta_line = "; ".join(f"{k}: {smeta[k]}" for k in (
                "repo", "tier", "executor", "owner", "status", "sow", "due", "blocked_by",
                "depends_on_stories", "params", "human_gates") if k in smeta)
            text = "\n\n".join(x for x in (
                "Metadata: " + meta_line,
                section(sbody, "Story"),
                "Context:\n" + section(sbody, "Context"),
                "Dependencies:\n" + section(sbody, "Dependencies"),
                "Evidence: " + section(sbody, "Evidence"),
            ) if x.strip())
            items.append({"key": smeta.get("id", s[:7]), "type": "story", "parent": fid,
                          "title": smeta.get("title", s), "description": text,
                          "acceptance_criteria": section(sbody, "Acceptance criteria")})
    # Features with no story files yet (F9-F14): the narrative only, for Frame to elaborate.
    for fid, (title, text) in narrative.items():
        if fid not in have_dir:
            items.append({"key": fid, "type": "feature", "title": title,
                          "description": text + "\n\nMetadata: no stories written yet; elaborate "
                                                "into stories, one repository per story (docs/0002)."})
    return items


# --- context docs ---------------------------------------------------------------------------

def docx_text(p: str) -> str:
    import docx
    d = docx.Document(p)
    lines = []
    for para in d.paragraphs:
        t = para.text.strip()
        if not t:
            continue
        style = (para.style.name or "").lower()
        lvl = re.search(r"heading (\d)", style)
        lines.append(("#" * min(int(lvl.group(1)) + 1, 4) + " " + t) if lvl else t)
    for tbl in d.tables:
        for row in tbl.rows:
            lines.append("| " + " | ".join(c.text.strip().replace("\n", " ") for c in row.cells) + " |")
    return "\n\n".join(lines)


def pdf_text(p: str) -> str:
    from pypdf import PdfReader
    return "\n\n".join((pg.extract_text() or "").strip() for pg in PdfReader(p).pages)


def xlsx_text(p: str) -> str:
    from openpyxl import load_workbook
    wb = load_workbook(p, read_only=True, data_only=True)
    out = []
    for ws in wb.worksheets:
        out.append(f"## Sheet: {ws.title}")
        for row in ws.iter_rows(values_only=True):
            if any(c not in (None, "") for c in row):
                out.append("| " + " | ".join("" if c is None else str(c).replace("\n", " ") for c in row) + " |")
    return "\n".join(out)


def chunks(text: str, limit: int = CHUNK):
    """Split on headings, then on paragraphs, into pieces under ``limit`` chars."""
    parts = re.split(r"(?=^#{1,3} )", text, flags=re.M)
    buf = ""
    for part in parts:
        while len(part) > limit:
            cut = part.rfind("\n\n", 0, limit)
            cut = cut if cut > limit // 3 else limit
            if buf:
                yield buf
                buf = ""
            yield part[:cut]
            part = part[cut:]
        if len(buf) + len(part) > limit and buf:
            yield buf
            buf = ""
        buf += part
    if buf.strip():
        yield buf


def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()[:60]


def stage_doc(src_rel: str, text: str, out_dir: str) -> int:
    pieces = list(chunks(text))
    base = slug(os.path.splitext(os.path.basename(src_rel))[0])
    for i, piece in enumerate(pieces, 1):
        name = f"{base}.md" if len(pieces) == 1 else f"{base}-{i:02d}.md"
        write(os.path.join(out_dir, name),
              f"<!-- source: {src_rel} (part {i}/{len(pieces)}) -->\n\n{piece.strip()}\n")
    return len(pieces)


def build_code_stage(code: str) -> dict:
    for sub in ("project-mep-AWS-Infrastructure", "project-mep-AWS-Code"):
        for dirpath, dirnames, files in os.walk(os.path.join(ROOT, sub)):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "cdk.out")]
            for f in files:
                src = os.path.join(dirpath, f)
                dst = os.path.join(code, os.path.relpath(src, ROOT))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
    # Declared toolchain (ENGINEERING-STANDARDS.md): staged only, F02-S02 creates the real one.
    infra_pkg = os.path.join(code, "project-mep-AWS-Infrastructure", "package.json")
    if not os.path.exists(infra_pkg):
        shutil.copyfile(os.path.join(HERE, "declared", "infrastructure.package.json"), infra_pkg)
    return {}


def build_context(out: str) -> dict:
    """Non-Markdown sources -> one Markdown file each. Markdown sources are read in place."""
    if os.path.isdir(out):
        shutil.rmtree(out)
    counts = {}
    for folder in ("adr", "knowledge", "task-list"):
        for dirpath, _, files in os.walk(os.path.join(ROOT, folder)):
            for f in sorted(files):
                p = os.path.join(dirpath, f)
                rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
                ext = os.path.splitext(f)[1].lower()
                conv = {".docx": docx_text, ".pdf": pdf_text, ".xlsx": xlsx_text}.get(ext)
                if conv is None:
                    continue
                if ext == ".docx" and os.path.isfile(os.path.splitext(p)[0] + ".md"):
                    continue                          # a Markdown copy already exists
                text = conv(p)
                name = slug(os.path.splitext(f)[0].replace(".docx", "")) + ".md"
                write(os.path.join(out, folder, name),
                      f"<!-- Generated from {rel} by .bootstrap/prepare_inputs.py. Do not edit. -->"
                      f"\n\n{text.strip()}\n")
                counts[rel] = len(text)
    return counts


def main() -> None:
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    reqs = build_requirements()
    write(os.path.join(STAGE, "requirements", "backlog.json"), json.dumps({"items": reqs}, indent=2))
    build_code_stage(os.path.join(STAGE, "code"))
    counts = build_context(os.path.join(ROOT, "harness", "context"))
    n_f = sum(1 for i in reqs if i["type"] == "feature")
    print(f"requirements: {n_f} features, {len(reqs) - n_f} stories -> stage/requirements/backlog.json")
    for rel, n in counts.items():
        print(f"  {rel}: {n} chars -> harness/context/")


if __name__ == "__main__":
    sys.exit(main())
