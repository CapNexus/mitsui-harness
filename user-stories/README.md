# User stories

Working folder for the Well Data Assistant POC features, user stories and dependencies. Narrative source: `../WDA-POC-Feature-List.md`. Decision on tracking: `docs/0001-stories-as-repo-files.md`.

## Layout

```
user-stories/
├── README.md
├── docs/                      Decisions about how we work (numbered)
├── templates/                 feature.md, story.md
├── config/parameters.md       Mitsui values (types A, B) and placeholders
├── dependencies/README.md     DEP-01 to DEP-29 with type, owner, status
├── raid-log.md                Risks, assumptions, issues, decisions (created by F01-S01)
├── evidence/                  Proof for the acceptance matrix, one folder per feature
├── scripts/                   Checkers and generators (created by stories)
└── features/
    ├── README.md              Feature map and story status index
    └── F01-mobilization-governance/
        ├── feature.md
        └── stories/F01-S01-....md
```

## How the harness uses this

1. Pick a story with `status: ready` whose `depends_on_stories` are `done`.
2. Read the story, `config/parameters.md` and the DEP rows it lists.
3. Build against the placeholders. Stop at each `gate:` and ask a human.
4. Run each `verify:` command. Set `status: done` in the same PR only when all pass.
5. If a story needs a type E dependency that is unresolved, ask a human before building.

## Conventions

- Story ID: `F<nn>-S<nn>`. Feature IDs in prose stay `F1` to `F14`. Folder and file names are zero-padded.
- `tier: build` runs in the CapNexus sandbox with no Mitsui dependency. `tier: integrate` needs Mitsui's environment or approval.
- `executor`: `agent` runs end to end, `human` is a human task, `mixed` has both.
- Every acceptance criterion has a `verify:` or a `gate:`.
- Check the trackers with `bash scripts/check-dependency-register.sh` and `bash scripts/check-raid-log.sh` (run from this folder). Each exits non-zero and lists every finding when an item is missing or incomplete.
