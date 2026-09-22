# The report — exorcise output, consumer input

`/exorcist:exorcise --json <path>` writes one JSON file beside the printed report. It
is the machine contract: a consumer reads it instead of scraping the text, which may
change. `scripts/report.py validate` is the write-time gate. This document governs; a
mismatch between it and the script is a bug in the script.

```json
{
  "contract_version": 1,
  "generated": "2026-09-22T18:04:11Z",
  "branch": "studious/build-42-retry",
  "intent": {"source": "text", "pr": null},
  "claims": [
    {"n": 1, "text": "sendWebhook retries a failed POST up to 3 times with backoff"},
    {"n": 3, "text": "tests cover the retry and give-up paths in tests/test_sender.py"}
  ],
  "scope": {
    "base_ref": "main",
    "base_sha": "6a528f8c0d1e4b2f9a7c3e5d1b0a9f8e7d6c5b4a",
    "head_sha": "c0ffee1234567890abcdef1234567890abcdef12",
    "source": "flag",
    "includes_worktree": true,
    "hunks": 9
  },
  "lanes": {"trace": "reported", "abstraction": "reported", "threshold": "reported", "deletion": "did not report"},
  "single_pass": false,
  "concepts_removed": ["RetryPolicy"],
  "concepts_kept": [{"name": "backoff_delays", "callers": 2}],
  "applied": [
    {
      "lane": "abstraction", "file": "src/http/client.ts", "line": 44, "end_line": 71,
      "title": "RetryPolicy class, 1 caller",
      "evidence": "grep -n RetryPolicy src/ → 2 hits: the definition and sendWebhook",
      "action": "inline", "target": "src/webhook/sender.ts:30", "concepts": ["RetryPolicy"], "hold": null,
      "also": [], "status": "applied", "outcome": "inlined into sendWebhook; deleted the class and its import"
    },
    {
      "lane": "trace", "file": "src/util/format.ts", "line": 3, "end_line": 40,
      "title": "reformatted formatDate",
      "evidence": "claims 1-3: formatDate is not on the webhook path; whitespace-only hunk",
      "action": "revert", "target": null, "concepts": [], "hold": null,
      "also": [], "status": "skipped", "outcome": "skipped: tests/test_format.ts snapshot pins the new formatting"
    }
  ],
  "held": [
    {
      "lane": "trace", "file": "tests/test_sender.py", "line": 88, "end_line": 120,
      "title": "give-up test for sendWebhook",
      "evidence": "claim 3 names the give-up path; revert would remove its only test",
      "action": "hold", "target": null, "concepts": [], "hold": "implied by intent",
      "claim": 3, "next": "nothing; kept because claim 3 entails it", "also": ["deletion"]
    }
  ],
  "checks": [
    {"name": "npm test -- tests/test_sender.py", "outcome": "pass", "detail": null}
  ],
  "tripwires": {
    "added": 212, "removed": 31, "changed": 243, "loc_limit": 200,
    "files": {"changed": 5, "added": ["src/util/backoff.ts"], "deleted": []},
    "new_exports": [{"file": "src/util/backoff.ts", "line": 1, "symbol": "backoff_delays"}],
    "new_deps": [],
    "warnings": ["243 lines changed (+212/-31); warn at 200"]
  },
  "justifications": [
    {"warning": "243 lines changed (+212/-31); warn at 200", "note": "half the added lines are the two tests claim 3 requires"}
  ]
}
```

Every key is required. The counts the text report prints (Traced, Reverted, Held, …)
are not stored; they derive from `applied` and `held`.

## Fields

- `contract_version` — `1`. An integer, matched exactly; there is no range. A
  consumer pins the version it reads and fails on any other.
- `generated` — UTC, `YYYY-MM-DDTHH:MM:SSZ`.
- `branch` — the branch name, or the PR's `headRefName`.
- `intent` — `source` is `text` (the argument), `pr` (a PR's title and body), or
  `branch` (the commit log). `pr` is the PR number when `source` is `pr`, else null.
- `claims` — §1's numbered claims, verbatim: `n` and one line of `text`. Findings
  cite claims by `n`.
- `scope` — what the diff covered, from `report.py resolve-base`. `base_sha` is the
  merge-base of the resolved base and HEAD — the commit the three-dot diff compares
  against and §5 restores from. `base_ref` is the name that was resolved. `source` is
  the rule that chose it: `flag` (`--base`), `pr` (the PR's `baseRefOid`), `upstream`
  (`@{upstream}`, recorded by its name), `main`, or `head~1`. `includes_worktree` is
  true when §2 added `git diff HEAD`. `hunks` is at least 1; an empty diff writes no
  report.
- `lanes` — `trace`, `abstraction`, `threshold`, `deletion`, each `reported` or `did
  not report`. A lane did not report when its reply failed `report.py findings`.
- `single_pass` — true when §3 ran without the Agent tool. Every lane is then
  `reported`, and the evidence is one reader's.
- `concepts_removed` — the `concepts` of every `applied` entry with status `applied`,
  each once. The validator checks set equality.
- `concepts_kept` — new exported symbols that survived (`tripwires.new_exports` minus
  `concepts_removed`), each with `callers`, the count from a grep that was run.
- `applied` — every non-hold finding after §4, in `reference/findings.md` shape, plus
  `also` (the other lanes the dedup merged into it), `status` (`applied` or
  `skipped`), and `outcome` (one line: what was done, or `skipped: <why>`).
- `held` — every hold after §4, in `reference/findings.md` shape with `claim` and
  `next` present, plus `also`. `claim` is the `n` of the claim the hold answers to,
  or null when none does (a trust boundary no claim asked for); it must name an entry
  in `claims`, and `implied by intent` requires it.
- `checks` — §6's checks. `name` is the command exactly as run; `outcome` is `pass` or
  `fail`; `detail` is null on pass and the first failing line on fail. An empty list
  means the project configures no checks.
- `tripwires` — `scripts/tripwires.py`'s JSON object, verbatim.
- `justifications` — exactly one per `tripwires.warnings` entry, matched by exact
  text: `warning` and a one-line `note`, §7's sentence for that wire.

## Writing it

The command drafts the file in its temp directory, runs `report.py validate` on it,
and copies it to the `--json` path only on exit 0. An invalid draft is a failed
report: the errors are printed, the path is left untouched, and nothing is repaired.
Every early stop — a PR head mismatch, a missing intent, an empty diff, a base that
does not resolve — writes no file. A missing file means no report.

A register run takes no `--json`; the register records its own outcome
(`reference/register.md`).

## Versions

| `contract_version` | Change |
|---|---|
| 1 | First contract. |
