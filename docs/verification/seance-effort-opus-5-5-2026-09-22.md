# Séance lane effort on Opus 5.5 — exorcist @ d4ffd4e, 2026-09-22

Question: with `opus` now resolving to Opus 5.5 (default effort `medium`), should the
4 séance lanes drop from `effort: high` to `medium`? Subject: the tree the
[self-séance](self-seance-2026-08-29.md) surveyed, so its register is the answer key.
Plugin at cd94a8a, loaded from a scratch clone via `--plugin-dir` (confirmed to shadow
the installed copy), invoked as `claude --plugin-dir . -p '/exorcist:seance d4ffd4e'`,
runs sequential.

| Run | Wall clock | Ghosts / concepts | Baseline ghosts recovered |
|---|---|---|---|
| 2026-08-29, prior Opus, `high` | 12 min | 21 / 52 (18 after cross-lane merge) | — |
| Opus 5.5, `medium` | 6.5 min | 14 / 32 | 9 of 18 |
| Opus 5.5, `high` | 10 min | 24 / 59 | 15 of 18 |

Matched by description, not id. `medium` missed every prompt- and doc-level ghost the
baseline had — the `${CLAUDE_PLUGIN_ROOT}` fallback in 8 agents (8 concepts, the
largest), the drifted reference example, the version declared twice, the ward's
search tiers restated, "Strata" naming two lanes — plus `KIND_ALIASES`, the identity
`on_path` table, the duplicated TOML scan, and the bare `subprocess.run`. `high`
missed only the ward restatement, the "Strata" name, and the TOML scan, and found 9
the baseline had not, led by the "entire reply is the array" clause in all 8 agents
(8 concepts).

Verdict: séance lanes stay `high`. `medium` halves wall clock and halves recall, and
what it drops is the highest-concept ghosts. One run per arm; the gap (9 vs 15) is
wide enough that variance is an unlikely explanation.
