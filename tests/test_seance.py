#!/usr/bin/env python3
"""The REPO one-liner in commands/seance.md must run on the host sed — BSD on macOS, GNU on CI. Self-running: prints OK."""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

REMOTES = [
    "https://github.com/jacquardlabs/viva.git",
    "https://github.com/jacquardlabs/viva",
    "git@github.com:jacquardlabs/viva.git",
    "git@github.com:jacquardlabs/viva",
    "ssh://git@github.com/jacquardlabs/viva.git",
    "ssh://git@github.com:2222/jacquardlabs/viva.git",
]


def test_repo_one_liner_yields_owner_slash_repo_on_host_sed():
    line = next(ln for ln in (REPO / "commands/seance.md").read_text().splitlines() if ln.startswith("REPO="))
    script = re.search(r"sed -E '([^']+)'", line).group(1)
    for remote in REMOTES:
        run = subprocess.run(["sed", "-E", script], input=remote + "\n", capture_output=True, text=True)
        assert run.returncode == 0 and run.stderr == "", (remote, run.stderr)
        assert run.stdout.strip() == "jacquardlabs/viva", (remote, run.stdout)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
