# Séance — jacquardlabs/exorcist @ d4ffd4e9183e · 2026-08-30T03:25:52Z

21 ghost(s) · 52 concept(s) on the table

| # | id | lane | status | ghost | concepts | radius | banishment |
|---|---|---|---|---|---|---|---|
| 1 | G-12 | duplicate | banished | eight agent prompts each carry the same ${CLAUDE_PLUGIN_ROOT} fallback | 8 | 11f/8c/0t | have the two dispatch commands hand each lane the resolved absolute path of its contract file; drop the 8 "locate under ${CLAUDE_PLUGIN_ROOT} with Glob" clauses |
| 2 | G-18 | strata | banished | four receipts.py CLI knobs no invoker passes, threaded through seven readers | 5 | 9f/0c/0t · exported | delete the --only/--skip/--churn-days/--timeout flags and the only/skip filter branch (412-413, 422-424); pass module constants CHURN_DAYS=180 at 434 and TIMEOUT=300 at the six runner calls 443-453; drop the flags from the module docstring usage line |
| 3 | G-13 | duplicate | banished | four tool wrappers each rewrite run-then-parse-JSON-stdout | 4 | 1f/4c/0t | extend `run` into a `run_json` that parses stdout or returns the failure tuple; drop the 4 startswith guards in _knip/_ruff/_depcruise/_scc |
| 4 | G-01 | contention | banished | two vocabularies for one lane reply — concepts_removed/hold_reason/summary vs concepts/hold/title | 4 | 8f/5c/0t | rename findings.md's concepts_removed→concepts, hold_reason→hold, summary→title and fold its hold values into ghost.md's four; update the 5 prompt files that speak the old names |
| 5 | G-07 | dead | proposed | four evidence-kind aliases no lane has ever emitted | 4 | 1f/0c/0t | delete the `file`, `count`, `search`, and `callers` entries from KIND_ALIASES (scripts/register.py:26), keeping `clone`/`receipt`/`surface`; an unaliased kind already fails validation loudly and the merge keeps the file as written (register.py:260-264) |
| 6 | G-14 | duplicate | proposed | knip's item shape (string or {name}) is known in four places | 3 | 1f/3c/0t | normalize each knip issue item once where the report is parsed (one `_name` that _symbol also uses); drop the 3 inline isinstance re-derivations |
| 7 | G-15 | duplicate | proposed | the ghost example and two field definitions live in both reference files, drifted | 3 | 2f/5c/0t | cut ghost.md to the lane-only rules plus a pointer at reference/register.md; fix register.md:21 (drop the survivor from concepts) and :25 (#duplicates → #clones) |
| 8 | G-10 | dead | banished | two config lines nothing reads: a second version string and an ignore for a directory nothing writes | 2 | 2f/0c/0t | delete `version = "0.1.0"` from pyproject.toml:3 and add `dynamic = ["version"]` to keep [project] PEP 621-valid; delete the `.exorcist/` line from .gitignore:4 |
| 9 | G-02 | contention | proposed | two declarations of the plugin's version and description | 2 | 3f/0c/1t | delete the stale version and description from pyproject [project] (or mark version dynamic); .claude-plugin/plugin.json is the one manifest |
| 10 | G-05 | contention | proposed | two ways to cite a receipt and to name the receipts directory | 2 | 4f/0c/0t | in register.md cite jscpd.json#clones[2] and name the dir docs/exorcist/seance-<date>/receipts, matching ghost.md and what receipts.py writes |
| 11 | G-08 | dead | banished | a `rank` subcommand nothing invokes, documented as the thing that ranks | 2 | 4f/0c/0t | delete the `rank` subcommand — register.py:244 and its :277-280 handler and the :5 usage line — and rewrite reference/register.md:69 to say the rank is assigned by `merge`; keep the `rank()` function, which merge calls |
| 12 | G-03 | contention | proposed | three lists of directories to ignore, and they disagree | 2 | 3f/2c/1t | derive JSCPD_IGNORE's directory globs and the depcruise exclude regex from SKIP_DIRS; delete the two hand-written copies |
| 13 | G-19 | strata | proposed | register.py `rank` subcommand nothing invokes — merge already ranks | 2 | 5f/0c/1t · exported | delete the `rank` subcommand (sub.add_parser at 245, the `if args.cmd == "rank"` branch at 277-280, the usage line at 5) and reword reference/register.md:69 to say merge assigns rank; keep rank() at 106, which merge calls and 3 test assertions pin |
| 14 | G-16 | duplicate | proposed | the ward's three-tier prior-shape search restated in two agent prompts | 2 | 3f/2c/0t | cite ward.md §"Search before writing" from abstraction-hunter step 2 and duplicate-helpers step 2; drop the two restatements of the tiers |
| 15 | G-11 | dead | proposed | a validation branch whose body is `pass` | 1 | 1f/0c/0t | delete scripts/register.py:70-74; the sourced/trace branch has an empty body and validates nothing |
| 16 | G-06 | contention | proposed | the word Strata names two different lanes | 1 | 2f/0c/0t | retitle abstraction-hunter.md's # Strata to its own lane's word (Abstraction); strata stays the wrapper lane's name |
| 17 | G-20 | strata | proposed | a tool-to-argv lookup table whose six entries each map a name to itself | 1 | 2f/0c/0t | delete the on_path dict (104-107) and replace the loop at 108-110 with `if shutil.which(tool): return [tool]`; keep the `sg` alias at 111-112, the one entry that is not an identity |
| 18 | G-17 | duplicate | proposed | the TOML section-header scan is written twice inside analyze() | 1 | 1f/1c/1t | extract `_toml_section(path, content, current)` and call it from both the added-line and context-line branches of analyze |
| 19 | G-21 | strata | proposed | _load, a one-line json.loads wrapper with one caller | 1 | 2f/1c/0t | delete _load (232-233) and inline it at 267 as json.loads(Path(args.path).read_text(encoding=utf-8)) |
| 20 | G-04 | contention | proposed | two ways to run a subprocess in receipts.py | 1 | 2f/1c/1t | replace the bare subprocess.run in tracked_files (receipts.py:65) with the run() helper; every other subprocess in the file already goes through it |
| 21 | G-09 | dead | banished | receipts.detect takes a `root` it never reads | 1 | 4f/3c/1t | delete the `root` parameter of receipts.detect (receipts.py:81) and drop the argument at its 3 call sites — receipts.py:411, tests/test_receipts.py:36 and :40 |

## G-12 — eight agent prompts each carry the same ${CLAUDE_PLUGIN_ROOT} fallback

`duplicate` · `banished` · sourced

**Retires.** `agents/abstraction-hunter.md plugin-root fallback clause`, `agents/dead-code.md plugin-root fallback clause`, `agents/deletion-scout.md plugin-root fallback clause`, `agents/duplicate-helpers.md plugin-root fallback clause`, `agents/intent-tracer.md plugin-root fallback clause`, `agents/pattern-contention.md plugin-root fallback clause`, `agents/threshold-salter.md plugin-root fallback clause`, `agents/wrapper-strata.md plugin-root fallback clause`
**Survivor.** `commands/seance.md:63 the lane-dispatch context (with commands/exorcise.md:63)`

**Evidence.**
- grep: "locate under `${CLAUDE_PLUGIN_ROOT}` with Glob if the bare path fails" — 8 hits, one per agent: abstraction-hunter.md:57, dead-code.md:46, deletion-scout.md:46, duplicate-helpers.md:46, intent-tracer.md:39, pattern-contention.md:51, threshold-salter.md:46, wrapper-strata.md:52
- trace: the dispatch already resolves the root: this lane's prompt arrived as "locate under /Users/bryan/Projects/exorcist", i.e. commands/seance.md:63 substituted the path before the agent ran, so the per-agent fallback is dead text at the point of use
- read: commands/seance.md:60-63 and commands/exorcise.md:60-64 already enumerate what each lane is handed (root, ref, receipts dir, contract) — one more item is the entry point for this fact
- read: commands/ward.md:25 "Locate it with Glob if the variable is unset" is the same fact but at the boundary — the command is the resolver, nothing upstream can hand it a path; kept

**Sites.**
- `agents/abstraction-hunter.md:57` — banish
- `agents/dead-code.md:46` — banish
- `agents/deletion-scout.md:46` — banish
- `agents/duplicate-helpers.md:46` — banish
- `agents/intent-tracer.md:39` — banish
- `agents/pattern-contention.md:51` — banish
- `agents/threshold-salter.md:46` — banish
- `agents/wrapper-strata.md:52` — banish
- `commands/seance.md:63` — migrate
- `commands/exorcise.md:63` — migrate
- `commands/ward.md:25` — keep

**Banishment.** have the two dispatch commands hand each lane the resolved absolute path of its contract file; drop the 8 "locate under ${CLAUDE_PLUGIN_ROOT} with Glob" clauses

**Outcome.** dropped the 8 'locate under ${CLAUDE_PLUGIN_ROOT} with Glob' clauses from agents/*.md Output sections; commands/seance.md:63 and commands/exorcise.md:63 now hand each lane the resolved absolute path of its contract file; checks: manifest: pass (no configured check covers prompt markdown)

## G-18 — four receipts.py CLI knobs no invoker passes, threaded through seven readers

`strata` · `banished` · sourced

**Retires.** `receipts.py --only`, `receipts.py --skip`, `receipts.py --churn-days`, `receipts.py --timeout`, `the args.timeout parameter threaded into all six tool runners`

**Evidence.**
- grep: grep -rn 'scripts/receipts.py' over the tree: 1 invocation (commands/seance.md:39, `--root "$ROOT" --out "$DIR/receipts"`) plus 1 docstring mention in tests/test_receipts.py:2. Flags passed by that one invoker: --root, --out, and --no-fetch conditionally (seance.md:49). --only, --skip, --churn-days, --timeout: 0 passers.
- read: receipts.py:401-404 defines the four flags; 412-413 build `only`/`skip` sets read only at 422 (`if (only and tool not in only) or tool in skip`); args.churn_days is read once (434); args.timeout is read at 443, 445, 447, 449, 451, 453 — six per-tool call sites that all receive the same default 300.
- tool: receipts.py is hotspot #1 (521 lines, score 521) (`hotspots.json#top[0]`)

**Sites.**
- `scripts/receipts.py:401` — banish
- `scripts/receipts.py:402` — banish
- `scripts/receipts.py:403` — banish
- `scripts/receipts.py:404` — banish
- `scripts/receipts.py:412` — banish
- `scripts/receipts.py:422` — banish
- `scripts/receipts.py:434` — migrate
- `scripts/receipts.py:443` — migrate
- `scripts/receipts.py:4` — migrate

**Banishment.** delete the --only/--skip/--churn-days/--timeout flags and the only/skip filter branch (412-413, 422-424); pass module constants CHURN_DAYS=180 at 434 and TIMEOUT=300 at the six runner calls 443-453; drop the flags from the module docstring usage line

**Outcome.** deleted --only/--skip/--churn-days/--timeout and the only/skip filter branch in job(); CHURN_DAYS=180 and TIMEOUT=300 module constants replace args.churn_days and the six args.timeout reads; usage line trimmed; checks: test_receipts: pass, ruff: pass, vermin: pass

## G-13 — four tool wrappers each rewrite run-then-parse-JSON-stdout

`duplicate` · `banished` · sourced

**Retires.** `receipts._knip stdout JSON guard`, `receipts._ruff stdout JSON guard`, `receipts._depcruise stdout JSON guard`, `receipts._scc stdout JSON guard`
**Survivor.** `scripts/receipts.py:127 run`

**Evidence.**
- grep: `err or "no JSON on stdout"` — 4 identical returns at receipts.py:306, 327, 346, 372, each preceded by the same `if not out.strip().startswith(...)` and followed by `json.loads(out)`; the `code, out, err = run(argv, root, timeout)` line above them is identical too
- read: receipts.py:305-307 vs 371-373 differ only in the opener character '{' vs '['; json.loads accepts both, so the shared body needs no mode parameter
- read: receipts.py:260 is a fifth near-copy that swallows non-JSON into [] and still records ast-grep as `ran` rather than `failed` — left off sites deliberately; folding it in would switch its failure mode
- tool: jscpd reported 0 clone pairs at --min-tokens 50; these 3-line bodies sit below its floor, which is why the receipt is silent here (`jscpd.json#clones`)

**Sites.**
- `scripts/receipts.py:305` — banish
- `scripts/receipts.py:326` — banish
- `scripts/receipts.py:345` — banish
- `scripts/receipts.py:371` — banish
- `scripts/receipts.py:127` — keep

**Banishment.** extend `run` into a `run_json` that parses stdout or returns the failure tuple; drop the 4 startswith guards in _knip/_ruff/_depcruise/_scc

**Outcome.** added run_json beside run (parse stdout as JSON or return None, code or 1, err or 'no JSON on stdout'); _knip/_ruff/_depcruise/_scc each dropped their startswith guard and json.loads for one run_json call; _ast_grep's lenient copy left as the register directed; checks: test_receipts: pass, ruff: pass, vermin: pass

## G-01 — two vocabularies for one lane reply — concepts_removed/hold_reason/summary vs concepts/hold/title

`contention` · `banished` · sourced

**Retires.** `concepts_removed`, `hold_reason`, `summary (findings field)`, `the second hold enumeration (implied by intent · blast radius: N consumers)`
**Survivor.** `reference/ghost.md:11 title · :12 concepts · :26 hold — the vocabulary scripts/register.py validates`

**Evidence.**
- grep: concepts_removed: 6 mentions in 5 files (reference/findings.md:19,35; agents/abstraction-hunter.md:59; agents/deletion-scout.md:26; agents/intent-tracer.md:51; agents/threshold-salter.md:49) · concepts: 24 mentions in 8 files (reference/ghost.md 2, reference/register.md 4, scripts/register.py 9, the four séance agents 6, commands/seance.md 3)
- grep: hold_reason: 9 mentions in 5 files (reference/findings.md:20,32,37; commands/exorcise.md:86,134; agents/intent-tracer.md:44,46; agents/threshold-salter.md:37; agents/abstraction-hunter.md:63) · hold as the same field: reference/ghost.md:26, reference/register.md:66, scripts/register.py (4 mentions)
- read: scripts/register.py:30-33 GHOST_REQUIRED = (id, lane, title, status, concepts, evidence, sites, blast_radius, banishment, confidence) — the ghost names are the only ones any code reads; no validator exists for the findings contract, so concepts_removed/hold_reason/summary are enforced by prose alone
- read: two enumerations of one concept: reference/findings.md:37-39 hold values (trust boundary · blast radius: N consumers outside the diff · behavior change · implied by intent) vs reference/ghost.md:42-45 (public API · trust boundary · behavior change · spec conflict) — 2 of 4 shared, 4 unique across the two
- read: commands/exorcise.md speaks both vocabularies in one file: hold_reason at :86 and :134 for a changeset run, hold at :162, :164, :166 for a register run
- trace: git log: reference/findings.md landed in 98cdd21 (exorcise changeset mount); reference/ghost.md and register.md in 223cf3d (séance), and the newest mount c9acde3 (/exorcist:exorcise <register>) speaks the ghost vocabulary — the newer code moved to concepts/hold/title

**Sites.**
- `reference/findings.md:35` — banish
- `agents/abstraction-hunter.md:59` — migrate
- `agents/deletion-scout.md:26` — migrate
- `agents/intent-tracer.md:44` — migrate
- `agents/threshold-salter.md:37` — migrate
- `commands/exorcise.md:86` — migrate
- `reference/ghost.md:12` — keep
- `scripts/register.py:30` — keep

**Banishment.** rename findings.md's concepts_removed→concepts, hold_reason→hold, summary→title and fold its hold values into ghost.md's four; update the 5 prompt files that speak the old names

**Outcome.** reference/findings.md now speaks title/concepts/hold and points at reference/ghost.md for the hold values; ghost.md's hold list gained 'blast radius: N consumers outside the diff' and 'implied by intent'; renamed in agents/abstraction-hunter.md (3), intent-tracer.md (3), threshold-salter.md (2), deletion-scout.md (1), commands/exorcise.md (4); reference/register.md:66 still lists the four séance values — G-15 (not selected) owns reconciling ghost.md with register.md; checks: manifest: pass (no configured check covers prompt markdown)

## G-07 — four evidence-kind aliases no lane has ever emitted

`dead` · `proposed` · inferred

**Retires.** `KIND_ALIASES "file"`, `KIND_ALIASES "count"`, `KIND_ALIASES "search"`, `KIND_ALIASES "callers"`

**Evidence.**
- read: scripts/register.py:25 comments KIND_ALIASES as "What lanes actually write"; docs/verification/seance-specdeck-2026-08-29.md:49-51 enumerates what lanes actually wrote — `read` x33, `clone`, `receipt`, `surface`. `read` was added to the vocabulary, the other three aliased. `file`, `count`, `search`, `callers` are in neither list.
- grep: grep -rn '"count"' / '"search"' over *.py and *.md: 0 hits outside register.py:26. '"file"' 22 hits and '"callers"' 6 hits, every one a site/blast_radius key, never an evidence `kind`. No agent prompt, reference doc, or test emits any of the four.

**Sites.**
- `scripts/register.py:26` — banish

**Banishment.** delete the `file`, `count`, `search`, and `callers` entries from KIND_ALIASES (scripts/register.py:26), keeping `clone`/`receipt`/`surface`; an unaliased kind already fails validation loudly and the merge keeps the file as written (register.py:260-264)

## G-14 — knip's item shape (string or {name}) is known in four places

`duplicate` · `proposed` · sourced

**Retires.** `receipts.py:311 inline knip item unwrap`, `receipts.py:315 inline knip item unwrap`, `receipts.py:316 inline knip item unwrap`
**Survivor.** `scripts/receipts.py:296 _symbol`

**Evidence.**
- grep: `isinstance(x, dict)` on a knip report item — 4 hits in one function's neighbourhood: receipts.py:297 (inside _symbol), 311, 315, 316
- read: receipts.py:315 and 316 are the byte-identical expression `x.get("name") if isinstance(x, dict) else x`; _symbol:297-299 states the same fact and is already called from 312 and 313
- read: receipts.py:311 is the fourth, divergent copy — `x.get("name", f) ... else f` falls back to the issue file rather than the item; role migrate, not banish, because the fallback must be made explicit at the call site
- read: the value enters at receipts.py:307 `data = json.loads(out)`; nothing between the parse and these four readers normalizes an item

**Sites.**
- `scripts/receipts.py:315` — banish
- `scripts/receipts.py:316` — banish
- `scripts/receipts.py:311` — migrate
- `scripts/receipts.py:296` — keep

**Banishment.** normalize each knip issue item once where the report is parsed (one `_name` that _symbol also uses); drop the 3 inline isinstance re-derivations

## G-15 — the ghost example and two field definitions live in both reference files, drifted

`duplicate` · `proposed` · sourced

**Retires.** `reference/ghost.md:7-29 copy of the ghost example JSON`, `reference/ghost.md:40-41 restatement of "concepts is the score"`, `reference/ghost.md:42-45 restatement of the `hold` enum`
**Survivor.** `reference/register.md:42 the Fields section`

**Evidence.**
- grep: the same example ghost ("two ways to read a TOML file", specdeck lockfile/matrix) appears in 2 files — reference/ghost.md:7-29 and reference/register.md:15-38 — plus 2 field definitions (`concepts`, `hold`) stated in both
- read: the copies disagree: ghost.md:14 `"concepts": ["matrix.load_toml"]` vs register.md:21 `["lockfile._read_toml", "matrix.load_toml"]` — register.md's copy lists its own survivor as something that stops existing, contradicting its own definition at register.md:51-52
- read: ghost.md:16 cites `jscpd.json#clones[2]`, register.md:25 cites `jscpd.json#duplicates[2]`; receipts.py:293 writes the key `clones`, so the surviving copy carries a receipt path that does not resolve (`jscpd.json#clones`)
- read: ghost.md:3-5 already names the owner — "register.py merge assigns id, status and rank; the lane supplies the rest, per reference/register.md" — one sentence that makes the trimmed second example unnecessary

**Sites.**
- `reference/ghost.md:7` — banish
- `reference/ghost.md:40` — banish
- `reference/register.md:21` — migrate
- `reference/register.md:25` — migrate
- `reference/register.md:42` — keep

**Banishment.** cut ghost.md to the lane-only rules plus a pointer at reference/register.md; fix register.md:21 (drop the survivor from concepts) and :25 (#duplicates → #clones)

## G-10 — two config lines nothing reads: a second version string and an ignore for a directory nothing writes

`dead` · `banished` · sourced

**Retires.** `pyproject.toml [project].version`, `.gitignore `.exorcist/``

**Evidence.**
- read: pyproject.toml:3 `version = "0.1.0"` against .claude-plugin/plugin.json:4 `"version": "0.4.0"`. [tool.semantic_release] version_variables (pyproject.toml:9) bumps only the manifest, `build_command = ""` means nothing is built from [project], and CI's lint job runs `uv run --no-project`, which opts out of the project table. The stale string is four releases behind and read by nothing.
- grep: grep -rn '\.exorcist' over the tree: 1 hit, the .gitignore:4 line itself. Every output path the mounts write is `docs/exorcist/…` (seance.md:37, exorcise.md:148) or `<tmp>/` (exorcise.md:44, 48, 66).

**Sites.**
- `pyproject.toml:3` — banish
- `.gitignore:4` — banish

**Banishment.** delete `version = "0.1.0"` from pyproject.toml:3 and add `dynamic = ["version"]` to keep [project] PEP 621-valid; delete the `.exorcist/` line from .gitignore:4

**Outcome.** pyproject.toml: version = "0.1.0" replaced by dynamic = ["version"] (plugin.json stays the one manifest; G-02, not selected, will find its pyproject:3 site drifted); .gitignore: dropped .exorcist/; checks: tomllib parse: pass, ruff (reads [tool.ruff]): pass, manifest: pass

## G-02 — two declarations of the plugin's version and description

`contention` · `proposed` · sourced

**Retires.** `pyproject.toml [project].version`, `pyproject.toml [project].description`
**Survivor.** `.claude-plugin/plugin.json:4 version — the file semantic-release bumps and validate_plugin.py checks`

**Evidence.**
- read: pyproject.toml:3 version = "0.1.0" vs .claude-plugin/plugin.json:4 "version": "0.4.0" — three releases of drift (git log shows chore(release) v0.2.0, v0.3.0, v0.4.0 after pyproject was written in 97fc5ae)
- read: pyproject.toml:12 version_variables = [".claude-plugin/plugin.json:version"] with the comment at :9-11 'The version lives in the plugin manifest and is bumped by CI on merge to main — never edit it by hand' — the doc names the survivor
- grep: grep -rn pyproject --exclude-dir=.git . → 1 hit outside scripts/tests: commands/exorcise.md:111, a prose list of files to look in for checks. No [build-system] table and build_command = "" (pyproject.toml:20): nothing reads [project].version or [project].description
- read: scripts/validate_plugin.py:20-28 REQUIRED = (name, description, version, author, repository, license, keywords) validates plugin.json only; tests/test_validate_plugin.py:29 asserts the real manifest and nothing asserts pyproject — one of the two declarations has a test, the other has none

**Sites.**
- `pyproject.toml:3` — banish
- `pyproject.toml:4` — banish
- `.claude-plugin/plugin.json:4` — keep

**Banishment.** delete the stale version and description from pyproject [project] (or mark version dynamic); .claude-plugin/plugin.json is the one manifest

## G-05 — two ways to cite a receipt and to name the receipts directory

`contention` · `proposed` · sourced

**Retires.** `the jscpd.json#duplicates[…] citation form`, `the docs/exorcist/receipts-<date>/ path form`
**Survivor.** `reference/ghost.md:16 jscpd.json#clones[2] · commands/seance.md:37 docs/exorcist/seance-<date>/receipts`

**Evidence.**
- read: reference/register.md:25 cites jscpd.json#duplicates[2] where reference/ghost.md:16 cites jscpd.json#clones[2] for the identical evidence line; scripts/receipts.py:293 writes the key "clones", so #duplicates resolves to nothing in the receipt it names (`jscpd.json#clones`)
- read: reference/register.md:13 shows "receipts": "docs/exorcist/receipts-2026-08-29/" while commands/seance.md:37-39 writes DIR=docs/exorcist/seance-$(date +%Y-%m-%d) and the receipts to $DIR/receipts — the only directory that exists on disk is seance-2026-08-29/receipts
- grep: receipt-key citation form: 6 files (reference/ghost.md:16, agents/dead-code.md:47 knip.json#unused_exports[4], agents/duplicate-helpers.md:17 jscpd.json#clones, agents/wrapper-strata.md:17 ast-grep.json#passthrough and :35 depcruise.json#most_imported, agents/pattern-contention.md:19 depcruise.json#most_imported) · raw-tool-key form: 1 file (reference/register.md:25)

**Sites.**
- `reference/register.md:25` — banish
- `reference/register.md:13` — banish
- `reference/ghost.md:16` — keep
- `scripts/receipts.py:293` — keep

**Banishment.** in register.md cite jscpd.json#clones[2] and name the dir docs/exorcist/seance-<date>/receipts, matching ghost.md and what receipts.py writes

## G-08 — a `rank` subcommand nothing invokes, documented as the thing that ranks

`dead` · `banished` · sourced

**Retires.** `scripts/register.py `rank` subcommand`, `reference/register.md's "assigned by scripts/register.py rank"`

**Evidence.**
- grep: grep -rn 'register.py' over commands/ and reference/: 4 invocations, none of them `rank` — seance.md:75 `merge`, seance.md:77 `render`, exorcise.md:157 `validate`, exorcise.md:201 `render`. The two mounts are the only callers the plugin has.
- read: scripts/register.py:229 — `merge()` ends with `return rank(register)`, so every register is ranked at creation; the CLI branch at :277-280 re-ranks a file nothing changes the concept counts of. reference/register.md:69 says "`rank` — assigned by `scripts/register.py rank`", naming a command no mount runs.

**Sites.**
- `scripts/register.py:244` — banish
- `scripts/register.py:277` — banish
- `scripts/register.py:5` — banish
- `reference/register.md:69` — migrate

**Banishment.** delete the `rank` subcommand — register.py:244 and its :277-280 handler and the :5 usage line — and rewrite reference/register.md:69 to say the rank is assigned by `merge`; keep the `rank()` function, which merge calls

**Outcome.** deleted the rank subcommand (usage line, add_parser, main branch) from scripts/register.py; rank() stays, called by merge and pinned by 3 tests; reference/register.md:69 now credits merge; G-19 (not selected) duplicates this ghost and will find its sites gone; checks: test_register: pass, ruff: pass, vermin: pass, register.py validate: pass

## G-03 — three lists of directories to ignore, and they disagree

`contention` · `proposed` · sourced

**Retires.** `JSCPD_IGNORE's directory globs`, `DEPCRUISE_CONFIG.options.exclude`
**Survivor.** `scripts/receipts.py:41 SKIP_DIRS`

**Evidence.**
- read: scripts/receipts.py:41-44 SKIP_DIRS names 14 directories; :48 JSCPD_IGNORE respells 8 of them as globs; :54 DEPCRUISE_CONFIG exclude respells 5 as a regex (node_modules|dist|build|\.next|coverage) — one concern, three spellings in one file
- grep: they have already drifted: .git, .tox, .mypy_cache, .ruff_cache, .pytest_cache, .turbo, coverage are in SKIP_DIRS but not in JSCPD_IGNORE; .venv, venv, vendor, target, __pycache__ are in SKIP_DIRS but not in the depcruise exclude — 12 of 14 entries are missing from at least one copy
- read: SKIP_DIRS is consumed in code (code_files at :97, the os.walk fallback at :75, so sizes/churn/depcruise inputs honor it) while the other two are string constants handed straight to a tool argv at :277 and :342 — nothing keeps the three in step
- tool: the file the three lists sit in is the largest in the tree at 521 lines (`sizes.json#largest[0]`)

**Sites.**
- `scripts/receipts.py:48` — banish
- `scripts/receipts.py:54` — banish
- `scripts/receipts.py:41` — keep

**Banishment.** derive JSCPD_IGNORE's directory globs and the depcruise exclude regex from SKIP_DIRS; delete the two hand-written copies

## G-19 — register.py `rank` subcommand nothing invokes — merge already ranks

`strata` · `proposed` · sourced

**Retires.** `the `rank` CLI subcommand (parser entry + main branch + usage line)`, `reference/register.md's claim that rank is assigned by `register.py rank``

**Evidence.**
- grep: grep -rn 'scripts/register.py' over the tree: 4 invocations, all in commands/ — merge 1 (seance.md:75), render 2 (seance.md:77, exorcise.md:201), validate 1 (exorcise.md:157), rank 0.
- trace: merge() ends with `return rank(register)` (register.py:229), so every register the seance writes is already ranked; the register run in exorcise.md re-renders after each ghost (line 201) and never re-ranks.
- grep: tests/test_register.py calls the rank() function directly at lines 60, 66 and asserts merge's ranking at 94 — 3 references to rank(), 0 to the subcommand. The function is a `keep` site.

**Sites.**
- `scripts/register.py:245` — banish
- `scripts/register.py:277` — banish
- `scripts/register.py:5` — banish
- `reference/register.md:69` — migrate
- `scripts/register.py:106` — keep

**Banishment.** delete the `rank` subcommand (sub.add_parser at 245, the `if args.cmd == "rank"` branch at 277-280, the usage line at 5) and reword reference/register.md:69 to say merge assigns rank; keep rank() at 106, which merge calls and 3 test assertions pin

## G-16 — the ward's three-tier prior-shape search restated in two agent prompts

`duplicate` · `proposed` · inferred

**Retires.** `agents/abstraction-hunter.md:32-37 copy of the three tiers`, `agents/duplicate-helpers.md:28-30 paraphrase of tiers 1-2`
**Survivor.** `ward.md:20 Search before writing`

**Evidence.**
- grep: "stop at the first hit" + the tier list — 2 files: ward.md:23-28 and abstraction-hunter.md:32-37; tiers 2 and 3 are byte-identical ("The standard library or runtime." / "A guarantee the framework already makes")
- read: agents/duplicate-helpers.md:28-30 states tiers 1-2 in prose ("check the stdlib and the project's own lib/ utils/ shared/ for an incumbent") — a third statement of the same procedure
- grep: the companion two-instance rule is in 3 operative files: ward.md:40, agents/wrapper-strata.md:27, agents/abstraction-hunter.md:24 (README.md:115 and docs/proposal.md:54 are product prose, not procedure)

**Sites.**
- `agents/abstraction-hunter.md:32` — banish
- `agents/duplicate-helpers.md:28` — banish
- `ward.md:20` — keep

**Banishment.** cite ward.md §"Search before writing" from abstraction-hunter step 2 and duplicate-helpers step 2; drop the two restatements of the tiers

## G-11 — a validation branch whose body is `pass`

`dead` · `proposed` · sourced

**Retires.** `register.validate_ghost's sourced/trace check`

**Evidence.**
- read: scripts/register.py:70-74 — `if ghost["confidence"] == "sourced" and any(ev.get("kind") == "trace" and not ev.get("receipt") …): pass  # a trace is sourced when the lane ran it; nothing to check without the tree`. The comment states the check cannot be made; the branch appends nothing to `errors`, and the generator it evaluates is discarded. Removing it changes no return value.
- grep: grep -rn 'trace' over scripts/ and reference/: register.py:24 (the EVIDENCE_KINDS tuple), :26, :71, :74, reference/register.md:56 — lines 71/74 are the only code that inspects a `trace` evidence entry, and they inspect it to do nothing. `validate_ghost` has 1 caller (register.py:93); no test in tests/test_register.py exercises the branch.

**Sites.**
- `scripts/register.py:70` — banish

**Banishment.** delete scripts/register.py:70-74; the sourced/trace branch has an empty body and validates nothing

## G-06 — the word Strata names two different lanes

`contention` · `proposed` · sourced

**Retires.** `the # Strata heading in agents/abstraction-hunter.md`
**Survivor.** `agents/wrapper-strata.md:9 # Strata — the agent whose lane id is strata`

**Evidence.**
- grep: grep -rn '^# Strata' agents/ → 2 hits: agents/abstraction-hunter.md:9 and agents/wrapper-strata.md:9; no other agent heading is used twice
- read: scripts/register.py:22 LANES = ('contention', 'dead', 'duplicate', 'strata') — strata is a register lane id owned by wrapper-strata; abstraction-hunter.md:58 declares lane: "abstraction" per reference/findings.md:11, so its heading names a lane it never reports
- read: every lane already carries two names — pattern-contention→contention, dead-code→dead, duplicate-helpers→duplicate, wrapper-strata→strata, intent-tracer→trace, abstraction-hunter→abstraction, threshold-salter→threshold, deletion-scout→deletion — and the mapping lives only in commands/seance.md:55-66 and commands/exorcise.md:56-64 prose, which is how one word ending up on two agents went unseen

**Sites.**
- `agents/abstraction-hunter.md:9` — banish
- `agents/wrapper-strata.md:9` — keep

**Banishment.** retitle abstraction-hunter.md's # Strata to its own lane's word (Abstraction); strata stays the wrapper lane's name

## G-20 — a tool-to-argv lookup table whose six entries each map a name to itself

`strata` · `proposed` · sourced

**Retires.** `receipts.resolve.on_path`

**Evidence.**
- read: receipts.py:104-107 reads `on_path = {"scc": ["scc"], "ast-grep": ["ast-grep"], "jscpd": ["jscpd"], "knip": ["knip"], "ruff": ["ruff"], "depcruise": ["depcruise"]}` — 6 of 6 entries map key to [key]. Lines 108-110 then loop that one-or-zero-element list and return [name].
- grep: resolve() has 1 call site (receipts.py:437), reached only for the 6 fetchable tools — sizes and churn return earlier at 429-436 — so the `.get(tool, [])` empty default is never taken; collapsing to `if shutil.which(tool): return [tool]` returns None for an unlisted tool exactly as today. 0 tests reference resolve.

**Sites.**
- `scripts/receipts.py:104` — banish
- `scripts/receipts.py:108` — migrate

**Banishment.** delete the on_path dict (104-107) and replace the loop at 108-110 with `if shutil.which(tool): return [tool]`; keep the `sg` alias at 111-112, the one entry that is not an identity

## G-17 — the TOML section-header scan is written twice inside analyze()

`duplicate` · `proposed` · sourced

**Retires.** `tripwires.py:148-151 second [section] scan`
**Survivor.** `scripts/tripwires.py:133 the added-line section scan`

**Evidence.**
- grep: `re.match(r"\s*\[+([^\]]+)\]+", content)` — 2 hits, tripwires.py:134 and 149; each sits under an identical `if _basename(path).endswith(".toml"):` and is followed by the identical `if header: toml_section = header.group(1).strip()`
- read: tripwires.py:133-136 (the `+` branch) and 148-151 (the context-line branch) are 4 byte-identical lines at the same indent; the only difference is the branch they sit in, so a helper needs no flag
- read: both copies are pinned by tests/test_tripwires.py:103 test_dependency_lines_by_manifest — DEPS_DIFF carries `+[tool.ruff]` (added branch) and context `[project]`/`[dependencies]` headers (space branch)
- tool: jscpd reported 0 clone pairs; a 4-line duplicate is below its 50-token floor (`jscpd.json#clones`)

**Sites.**
- `scripts/tripwires.py:148` — banish
- `scripts/tripwires.py:133` — keep

**Banishment.** extract `_toml_section(path, content, current)` and call it from both the added-line and context-line branches of analyze

## G-21 — _load, a one-line json.loads wrapper with one caller

`strata` · `proposed` · sourced

**Retires.** `register._load`

**Evidence.**
- tool: ast-grep flagged register.py:232 _load as a single-call function whose callee is json.loads (`ast-grep.json#single_call_functions[0]`)
- grep: grep -n '_load' scripts/register.py: 2 hits — the definition (232) and 1 caller (267). Its sibling _save has 2 callers (257, 278), so the pair is not symmetric. No test references _load.
- read: register.py:232-233 is `def _load(path): return json.loads(Path(path).read_text(encoding="utf-8"))` — no default, no narrowing, no renamed parameter that the caller does not already have.

**Sites.**
- `scripts/register.py:232` — banish
- `scripts/register.py:267` — migrate

**Banishment.** delete _load (232-233) and inline it at 267 as json.loads(Path(args.path).read_text(encoding=utf-8))

## G-04 — two ways to run a subprocess in receipts.py

`contention` · `proposed` · sourced

**Retires.** `the bare subprocess.run in tracked_files`
**Survivor.** `scripts/receipts.py:127 run()`

**Evidence.**
- grep: run() helper: 8 call sites (scripts/receipts.py:160, 167, 259, 278, 304, 325, 344, 370) · bare subprocess.run: 1 call site (scripts/receipts.py:65), plus the one inside run() itself at :129
- read: receipts.py:64-72 rebuilds what run() already gives: it passes check=True and catches (OSError, CalledProcessError) where run() returns 127 for OSError and hands the exit code back — the only thing the bare call loses is run()'s timeout, and it invokes git the same way churn does at :160
- read: receipts.py:103 documents run() as the file's subprocess idiom ('The argv prefix that runs tool') and every tool receipt from _ast_grep to _scc goes through it; tracked_files is the only holdout

**Sites.**
- `scripts/receipts.py:65` — migrate
- `scripts/receipts.py:127` — keep

**Banishment.** replace the bare subprocess.run in tracked_files (receipts.py:65) with the run() helper; every other subprocess in the file already goes through it

## G-09 — receipts.detect takes a `root` it never reads

`dead` · `banished` · sourced

**Retires.** `receipts.detect `root` parameter`

**Evidence.**
- tool: ruff ARG001 — unused function argument `root`, scripts/receipts.py:81 (the run's only finding) (`ruff.json#findings[0]`)
- grep: grep -rn 'detect(' over *.py: 3 call sites — receipts.py:411 `detect(root, files)`, tests/test_receipts.py:36 and :40, both passing a throwaway `Path(".")`. The body (lines 82-93) reads only `files`; `root` is never dereferenced.

**Sites.**
- `scripts/receipts.py:81` — banish
- `scripts/receipts.py:411` — migrate
- `tests/test_receipts.py:36` — migrate
- `tests/test_receipts.py:40` — migrate

**Banishment.** delete the `root` parameter of receipts.detect (receipts.py:81) and drop the argument at its 3 call sites — receipts.py:411, tests/test_receipts.py:36 and :40

**Outcome.** dropped the unread root parameter from receipts.detect and the argument at receipts.py main and tests/test_receipts.py (2 calls); checks: test_receipts: pass, ruff: pass, vermin: pass
