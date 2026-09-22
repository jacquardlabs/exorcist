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
    {"n": 2, "text": "a webhook that exhausts its retries is recorded as failed, not dropped"},
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
      "claim": 3, "next": "nothing; kept because claim 3 entails it", "also": []
    },
    {
      "lane": "trace", "file": null, "line": null, "end_line": null,
      "title": "give-up path never records the failure",
      "evidence": "claim 2 → no hunk writes a failed status: grep -n 'status.*failed' src/webhook/ → 0 hits",
      "action": "hold", "target": null, "concepts": [], "hold": "unmet claim",
      "claim": 2, "next": "write the failed status in sendWebhook's give-up branch, or drop claim 2", "also": []
    }
  ],
  "out_of_intent_files": ["src/util/format.ts"],
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
  against and §5 restores from. `base_ref` is the ref that was resolved, as written:
  the `--base` value, the upstream's name, `main`, or `HEAD~1` — for `pr`, the raw
  `baseRefOid` SHA. `source` is the rule that chose it: `flag` (`--base`), `pr` (the
  PR's `baseRefOid`), `upstream` (`@{upstream}`), `main`, or `head~1`.
  `includes_worktree` is true when §2 added `git diff HEAD`. `hunks` is at least 1; an
  empty diff writes no report.
- `lanes` — `trace`, `abstraction`, `threshold`, `deletion`, each `reported` or `did
  not report`. A lane did not report when its reply failed `report.py findings`.
- `single_pass` — true when §3 ran without the Agent tool: the evidence is one
  reader's. A lane can still be `did not report` when its array failed validation.
- `concepts_removed` — the `concepts` of every `applied` entry with status `applied`,
  each once. The validator checks set equality.
- `concepts_kept` — new exported symbols that survived (`tripwires.new_exports` minus
  `concepts_removed`), each with `callers`, the count from a grep that was run.
- `applied` — every non-hold finding after §4, in `reference/findings.md` shape, plus
  `also` (the other `reported` lanes the dedup merged into it), `status` (`applied` or
  `skipped`), and `outcome` (one line: what was done, or `skipped: <why>`).
- `held` — every hold after §4, in `reference/findings.md` shape with `claim` and
  `next` present, plus `also`. `claim` is the `n` of the claim the hold answers to,
  or null when none does (a trust boundary no claim asked for); it must name an entry
  in `claims`, and `implied by intent` and `unmet claim` require it. An `unmet claim`
  has `file`, `line`, and `end_line` null: it names something the diff lacks. Each
  entry stands alone in a PR body — `title` and `file:line` say what and where,
  `hold` and `evidence` say why (a `behavior change` names the pinning test, a `spec
  conflict` the doc and line), `claim` resolves through `claims` to what it relates
  to, and `next` is the decision. Nothing downstream re-raises a hold.
- `out_of_intent_files` — the files that carry a hunk no claim reaches and nothing
  argues for: the sorted, unique `file` of every trace finding with `action: revert`
  or `hold: trust boundary`, before §4's dedup and before §5's apply. `implied by
  intent` is in intent and `unmet claim` has no file, so neither counts. `spec
  conflict` does not count: its hunk is either one a doc argues for or one a claim
  reaches, and the hold does not say which; the human settles it. A consumer ranks by its length;
  the list keeps the number auditable. `report.py merge` writes it; the command never
  does. Null exactly when `lanes.trace` did not report.

  It stands in for studious plan-drift's `out-of-plan-file` (a changed file no task
  path names). Two differences, both deliberate. It is content-based, not name-based:
  a file no plan line names whose hunks reach a claim is not counted, and a named file
  whose hunks reach none is. It is counted before apply, so it measures how far the
  change strayed, not what was left after exorcise reverted the drift — post-apply
  every candidate would read near zero, and a rollback of the pass does not change
  it. A file an unrequested hunk reverts counts whether the revert applied or was
  skipped, and a §4 guard that turns it into a hold does not uncount it.
- `checks` — §6's checks. `name` is the command exactly as run; `outcome` is `pass` or
  `fail`; `detail` is null on pass and the first failing line on fail. An empty list
  means the project configures no checks.
- `tripwires` — `scripts/tripwires.py`'s JSON object, verbatim.
- `justifications` — exactly one per `tripwires.warnings` entry, matched by exact
  text: `warning` and a one-line `note`, §7's sentence for that wire.

## Writing it

`report.py merge` writes the draft from the lane replies: `lanes`, `single_pass`, the
deduped findings split into `applied` and `held`, `out_of_intent_files`, `scope` and
`tripwires` verbatim. It leaves null what needs judgment — `branch`, `intent`,
`claims`, `concepts_removed`, `concepts_kept`, `checks`, `justifications`, each
`applied[].status` and `outcome` — and the command fills those, adds the §4 guard
conversions to `held`, and runs `report.py validate` on the result. The command
copies it to the `--json` path only on exit 0. An invalid draft is a failed
report: the errors are printed, the path is left untouched, and nothing is repaired.
Every early stop — a PR head mismatch, a missing intent, an empty diff, a base that
does not resolve — writes no file. A missing file means no report.

A register run takes no `--json`; the register records its own outcome
(`reference/register.md`).

## Versions

| `contract_version` | Change |
|---|---|
| 1 | First contract. |
