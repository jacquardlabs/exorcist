---
description: Install the exorcist ward into a project — copy ward.md to .claude/ward.md and import it from CLAUDE.md so its rules govern every future change. Pass `user` to install to ~/.claude instead. Re-run to refresh after a plugin update.
allowed-tools: Bash, Read, Write, Edit
argument-hint: "[user]"
---

# Install the ward

The ward is a standing stance, not an invocation: it takes effect only once CLAUDE.md
imports it. The plugin's copy lives at a version-pinned path that changes on every
release, so the import points at a copy inside the project, and this command keeps that
copy current.

## 1. Resolve the target

`$ARGUMENTS` empty → project scope: `.claude/ward.md`, imported from `./CLAUDE.md`.
`$ARGUMENTS` is `user` → user scope: `~/.claude/ward.md`, imported from `~/.claude/CLAUDE.md`.
Anything else → say the two accepted forms and stop.

For project scope, the project root is the git toplevel (`git rev-parse --show-toplevel`),
or the working directory outside git.

## 2. Copy the ward

Source: `${CLAUDE_PLUGIN_ROOT}/ward.md`. Locate it with Glob if the variable is unset.

If the target already exists and differs, show the diff (`diff <target> <source>`) before
overwriting. Local edits to the target are lost on refresh — say so in one line, and
suggest the project keep its own rules in CLAUDE.md, next to the import, rather than
inside the ward.

Copy the file byte for byte. Do not edit or trim it for the project.

## 3. Add the import

The import line is `@.claude/ward.md` (project) or `@~/.claude/ward.md` (user). If the
CLAUDE.md does not contain it, append:

```markdown

## Ward
@.claude/ward.md
```

Create the CLAUDE.md if it does not exist. If the line is already present, leave the
file untouched.

## 4. Report

One line per action taken — copied, refreshed (with a line count of the diff), import
added, or already current — and the full path of each file touched. Nothing else.
