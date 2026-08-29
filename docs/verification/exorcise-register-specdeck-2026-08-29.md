# Exorcise (register mode) verification — specdeck, 2026-08-29

Subject: the [séance register](seance-specdeck-2026-08-29.md) for specdeck @ 6a528f8,
21 ghosts. Invocation (headless, `--plugin-dir`):

```text
/exorcist:exorcise docs/exorcist/seance-2026-08-29/register.json G-21,G-06
```

Result header: `Banished 2 (2 concepts) · Skipped 0 · Untouched 19 (not selected)`.

| Ghost | Banishment applied | Scoped checks |
|---|---|---|
| G-06 bare `"cassettes"` literal ×2 beside `lint.CASSETTE_DIR` | both literals → `CASSETTE_DIR`, added to the existing `lint` import | ruff, ruff format, pytest test_cli+test_lint (106) |
| G-21 `rubric_hash` one-line wrapper, 1 caller | definition deleted; caller writes `fingerprint(rubric_text(criteria))`, the spelling lockfile.py already uses | ruff, ruff format, pytest 4 modules (204) |

Independently verified after the run: `git diff` is 2 files, +4/−8, nothing outside
the sites; both ghosts are `status: banished` with `outcome` filled; the other 19 are
untouched `proposed`; `register.py validate` passes; full `pytest` 1084 passed. No
commit was made. Both ids were plain approvals (no `hold`), and the report said so.

Precondition change made during this run: the clean-tree check is
`--untracked-files=no`, because the register directory itself is untracked.
