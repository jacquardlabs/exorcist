# Findings contract — changeset lanes

Every `/exorcist:exorcise` lane returns one JSON array and nothing else. The command
dedups across lanes by `file` + `line`, then by `target`, and applies in this order of
precedence when two findings claim the same lines: `hold` > `revert` > `delete` >
`inline` > `reuse` > `move`.

```json
[
  {
    "lane": "trace | abstraction | threshold | deletion",
    "file": "src/http/client.ts",
    "line": 44,
    "end_line": 71,
    "summary": "new RetryPolicy class, 1 caller",
    "evidence": "grep -n RetryPolicy src/ → 2 hits: the definition and sendWebhook",
    "action": "revert | inline | reuse | move | delete | hold",
    "target": "src/webhook/sender.ts:30",
    "concepts_removed": ["RetryPolicy"],
    "hold_reason": null
  }
]
```

- `summary` — one line, the noun first. No adjectives.
- `evidence` — the command or trace that backs the finding, with its count. A finding
  with no evidence is not a finding.
- `action` — what the command should do. `revert` restores the hunk to its base
  content; `inline` folds a single-caller symbol into its caller; `reuse` swaps new
  code for the existing symbol named in `target`; `move` relocates a fix to the entry
  point in `target`; `delete` removes code the change made unnecessary; `hold` records
  a finding the command must not apply, with `hold_reason` set.
- `target` — `path:line` of the replacement, the entry point, or the caller. `null`
  for `revert`, `delete`, and `hold`.
- `concepts_removed` — the symbols, files, options, or dependencies that stop existing
  if the action is taken. This is the score. Empty for `hold`.
- `hold_reason` — set only on `hold`: `trust boundary`, `blast radius: N consumers
  outside the diff`, `behavior change`, or `implied by intent` (a test or error path the
  request entails even though no sentence names it).

A lane with nothing to report returns `[]`.
