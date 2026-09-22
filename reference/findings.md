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
    "title": "new RetryPolicy class, 1 caller",
    "evidence": "grep -n RetryPolicy src/ → 2 hits: the definition and sendWebhook",
    "action": "revert | inline | reuse | move | delete | hold",
    "target": "src/webhook/sender.ts:30",
    "concepts": ["RetryPolicy"],
    "hold": null,
    "claim": null,
    "next": null
  }
]
```

`title`, `concepts`, and `hold` mean what they mean in `reference/ghost.md`; a finding
is a ghost scoped to one diff.

- `title` — one line, the noun first. No adjectives.
- `evidence` — the command or trace that backs the finding, with its count. A finding
  with no evidence is not a finding.
- `action` — what the command should do. `revert` restores the hunk to its base
  content; `inline` folds a single-caller symbol into its caller; `reuse` swaps new
  code for the existing symbol named in `target`; `move` relocates a fix to the entry
  point in `target`; `delete` removes code the change made unnecessary; `hold` records
  a finding the command must not apply, with `hold` set.
- `target` — `path:line` of the replacement, the entry point, or the caller. `null`
  for `revert`, `delete`, and `hold`.
- `concepts` — what stops existing if the action is taken. This is the score. Empty
  for `hold`.
- `hold` — set only on `hold`, one of the values `reference/ghost.md` lists.
- `claim` — the number of the claim the finding answers to, or `null`. Required on
  `hold: "implied by intent"`.
- `next` — set on every `hold`: one line, what the human or a register run would do.

`scripts/report.py findings <reply>` validates a reply against this contract. A reply
with any invalid finding is a lane that did not report.

A lane with nothing to report returns `[]`.
