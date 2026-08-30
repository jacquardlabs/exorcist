# The register — séance output, exorcise input

`/exorcist:seance` writes one JSON file; the human edits it; `/exorcist:exorcise
<path>` works it. It is the approval surface: nothing in it is applied until a human
has marked it so. `scripts/register.py` validates, ranks, and renders it.

```json
{
  "exorcist_register": 1,
  "repo": "jacquardlabs/specdeck",
  "ref": "6a528f8c0d1e…",
  "generated": "2026-08-29T21:04:00Z",
  "receipts": "docs/exorcist/receipts-2026-08-29/",
  "lanes": {"contention": "reported", "dead": "reported", "duplicate": "reported", "strata": "did not report"},
  "ghosts": [
    {
      "id": "G-01",
      "lane": "contention",
      "title": "two ways to read a TOML file",
      "status": "proposed",
      "concepts": ["lockfile._read_toml", "matrix.load_toml"],
      "survivor": "src/specdeck/lockfile.py:41 _read_toml",
      "evidence": [
        {"kind": "grep", "detail": "_read_toml: 4 call sites · load_toml: 2 call sites", "receipt": null},
        {"kind": "tool", "detail": "jscpd clone #3, 14 lines", "receipt": "jscpd.json#duplicates[2]"}
      ],
      "sites": [
        {"path": "src/specdeck/matrix.py", "line": 73, "role": "banish"},
        {"path": "src/specdeck/cli.py", "line": 784, "role": "migrate"}
      ],
      "blast_radius": {"files": 3, "callers": 2, "exported": false, "tests": 1},
      "banishment": "delete matrix.load_toml; point its 2 callers at lockfile._read_toml",
      "confidence": "sourced",
      "hold": null,
      "rank": 1,
      "outcome": null
    }
  ]
}
```

## Fields

- `lane` — `contention` (two or more patterns for one job), `dead` (nothing reaches
  it), `duplicate` (independently written reimplementations, including the same
  point-of-use fix scattered across consumers), `strata` (pass-throughs, single-caller
  indirection, layers that add nothing).
- `status` — `proposed` when the séance writes it. The human sets `approved` or
  `held`. `/exorcist:exorcise` works only `approved` ghosts, or the ids it is handed,
  and sets `banished` or `skipped` with `outcome` filled in.
- `concepts` — the symbols, files, options, dependencies, or vocabularies that stop
  existing. **The score.** Ranking is by this list's length first.
- `survivor` — for contention and duplicate: the one way that remains, `path:line
  name`. Null for dead and strata.
- `evidence` — at least one entry. `kind` is `grep` (a count the lane ran), `tool` (a
  phase-0 receipt, with `receipt` pointing into it as `file#jsonpath`), `trace` (a
  caller chain), or `read` (what the file says at a line — quote it). A ghost with no evidence fails validation.
- `sites` — every location the banishment touches. `role` is `banish` (deleted),
  `migrate` (edited to use the survivor), or `keep` (the survivor, listed so the
  human sees what stays).
- `blast_radius` — files touched, callers rewritten, whether an exported or public
  symbol is involved, tests affected. Ranking tiebreak: smaller first.
- `banishment` — one line, imperative, the whole edit.
- `confidence` — `sourced` when every evidence entry is a count or receipt; `inferred`
  when any is a judgment. Inferred ghosts rank below sourced at equal score.
- `hold` — set by the lane when the ghost is real but must not be applied without a
  human decision: `trust boundary`, `public API`, `behavior change`, `spec conflict`.
  Written as `status: proposed` with `hold` set; the human decides.
- `also` — set by the merge when a second lane reported the same ghost (a banish or
  migrate site at the same path and line); the survivor keeps its lane, absorbs the
  other's evidence, and lists the other lane here.
- `rank` — assigned by `scripts/register.py merge`: concepts desc, then sourced before
  inferred, then blast radius asc.
- `outcome` — written by `/exorcist:exorcise`: what was done, the checks run, or why
  it was skipped.

## Rendering

`scripts/register.py render <file>` prints the markdown the human reads: a ranked
table (id, lane, title, concepts count, blast radius, banishment), then one block per
ghost with its evidence and sites. The JSON is the record; the markdown is a view.
