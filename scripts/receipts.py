#!/usr/bin/env python3
"""Séance phase 0 — run the zero-config tool core over a tree and write receipts.

    python3 receipts.py --root <worktree> --out <dir> [--no-fetch] [--only a,b] [--skip a,b]

Receipts are JSON files the lanes cite, one per tool, plus `manifest.json` (what ran,
what was skipped and why, the exact command) and `summary.md` (counts and the top
items — read this first). Code owns bookkeeping; the lanes own judgment.

Tools, by detected stack — each one skipped with a reason when it cannot run:
  sizes      stdlib line counts per file, always
  churn      git log file-change counts, always (needs a git history at --root)
  scc        size and complexity, if `scc` is on PATH
  ast-grep   pass-through candidates from rules/, via PATH, `uvx`, or `npx`
  jscpd      copy-paste clones, any language, via PATH or `npx`
  knip       unused files/exports/deps (JS/TS), via PATH or `npx`
  ruff       unused imports/variables/arguments, commented-out code (Python), via PATH or `uvx`
  depcruise  import cycles (JS/TS), via PATH or `npx`

`--no-fetch` restricts to binaries already on PATH. Standard library only, 3.9-compatible.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
RULES = PLUGIN_ROOT / "rules" / "sgconfig.yml"

SKIP_DIRS = {
    "node_modules", ".git", ".venv", "venv", "dist", "build", ".next", "target", "vendor",
    "__pycache__", ".tox", ".mypy_cache", ".ruff_cache", ".pytest_cache", "coverage", ".turbo",
}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}
PY_EXT = {".py"}
CODE_EXT = JS_EXT | PY_EXT | {".go", ".rs", ".rb", ".java", ".kt", ".swift", ".cs", ".php", ".scala", ".c", ".cc", ".cpp", ".h", ".hpp"}
JSCPD_IGNORE = "**/node_modules/**,**/.venv/**,**/venv/**,**/dist/**,**/build/**,**/target/**,**/vendor/**,**/*.min.js,**/*.lock,**/__pycache__/**,**/*.json,**/*.yaml,**/*.yml,**/*.md,**/*.snap"
JSCPD_FORMATS = "python,typescript,tsx,javascript,jsx,go,rust,ruby,java,kotlin,swift,csharp,php,scala,c,cpp,c-header"
DEPCRUISE_CONFIG = {
    "forbidden": [{"name": "no-circular", "severity": "warn", "from": {}, "to": {"circular": True}}],
    "options": {
        "doNotFollow": {"path": "node_modules"},
        "exclude": {"path": "node_modules|dist|build|\\.next|coverage"},
        "tsPreCompilationDeps": True,
    },
}
ALL_TOOLS = ("sizes", "churn", "scc", "ast-grep", "jscpd", "knip", "ruff", "depcruise")


# --- tree -------------------------------------------------------------------------

def tracked_files(root: Path) -> List[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, capture_output=True, text=True, check=True
        ).stdout
        files = [f for f in out.split("\0") if f]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            files.append(os.path.relpath(os.path.join(dirpath, name), root))
    return sorted(files)


def detect(root: Path, files: List[str]) -> Dict[str, Any]:
    exts = Counter(Path(f).suffix for f in files)
    manifests = [f for f in files if Path(f).name in {"package.json", "pyproject.toml", "setup.py", "go.mod", "Cargo.toml"} or Path(f).name.startswith("requirements")]
    stacks = []
    if any(exts[e] for e in JS_EXT) or any(Path(f).name == "package.json" for f in manifests):
        stacks.append("js")
    if exts[".py"] or any(Path(f).name in {"pyproject.toml", "setup.py"} for f in manifests):
        stacks.append("py")
    if exts[".go"]:
        stacks.append("go")
    if exts[".rs"]:
        stacks.append("rs")
    return {"stacks": stacks, "manifests": manifests, "extensions": dict(exts.most_common(12))}


def code_files(files: List[str], exts: set) -> List[str]:
    return [f for f in files if Path(f).suffix in exts and not any(part in SKIP_DIRS for part in Path(f).parts)]


# --- resolution -------------------------------------------------------------------

def resolve(tool: str, fetch: bool) -> Optional[List[str]]:
    """The argv prefix that runs `tool`, or None. PATH first, then a fetching runner."""
    on_path = {
        "scc": ["scc"], "ast-grep": ["ast-grep"], "jscpd": ["jscpd"], "knip": ["knip"],
        "ruff": ["ruff"], "depcruise": ["depcruise"],
    }
    for name in on_path.get(tool, []):
        if shutil.which(name):
            return [name]
    if tool == "ast-grep" and shutil.which("sg"):
        return ["sg"]
    if not fetch:
        return None
    npx = shutil.which("npx")
    uvx = shutil.which("uvx")
    fetched = {
        "ast-grep": ([uvx, "-q", "--from", "ast-grep-cli", "ast-grep"] if uvx else None) or ([npx, "-y", "-p", "@ast-grep/cli", "ast-grep"] if npx else None),
        "jscpd": [npx, "-y", "jscpd"] if npx else None,
        "knip": [npx, "-y", "knip"] if npx else None,
        "ruff": [uvx, "-q", "ruff"] if uvx else None,
        "depcruise": [npx, "-y", "dependency-cruiser"] if npx else None,
    }
    return fetched.get(tool)


def run(argv: List[str], cwd: Path, timeout: int) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"
    except OSError as exc:
        return 127, "", str(exc)
    return proc.returncode, proc.stdout, proc.stderr


# --- stdlib receipts --------------------------------------------------------------

def sizes(root: Path, files: List[str]) -> Dict[str, Any]:
    per_file = []
    by_ext: Counter = Counter()
    for f in code_files(files, CODE_EXT):
        try:
            with open(root / f, "rb") as fh:
                n = sum(1 for _ in fh)
        except OSError:
            continue
        per_file.append({"file": f, "lines": n})
        by_ext[Path(f).suffix] += n
    per_file.sort(key=lambda x: -x["lines"])
    return {
        "files": len(per_file),
        "lines": sum(x["lines"] for x in per_file),
        "by_extension": dict(by_ext.most_common()),
        "largest": per_file[:30],
    }


def churn(root: Path, days: int, files: List[str]) -> Dict[str, Any]:
    code, out, err = run(
        ["git", "log", f"--since={days} days ago", "--name-only", "--format=", "--", "."], root, 120
    )
    if code != 0:
        return {"error": err.strip() or f"git log exited {code}"}
    tracked = set(code_files(files, CODE_EXT))
    counts = Counter(line.strip() for line in out.splitlines() if line.strip() in tracked)
    commits = run(["git", "rev-list", "--count", f"--since={days} days ago", "HEAD"], root, 60)[1].strip()
    return {
        "days": days,
        "commits": int(commits) if commits.isdigit() else None,
        "hottest": [{"file": f, "changes": n} for f, n in counts.most_common(30)],
    }


def hotspots(size: Dict[str, Any], churn_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    lines = {x["file"]: x["lines"] for x in size.get("largest", [])}
    spots = [
        {"file": h["file"], "changes": h["changes"], "lines": lines.get(h["file"]),
         "score": h["changes"] * (lines.get(h["file"]) or 1)}
        for h in churn_data.get("hottest", [])
    ]
    return sorted(spots, key=lambda s: -s["score"])[:15]


# --- pass-through post-filter -----------------------------------------------------

def _dotted(node: ast.AST) -> Optional[str]:
    """`a`, `a.b`, `self.inner.f` — a plain name chain. Anything computed is not a callee
    a caller could reach directly, so it is not a pass-through."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def _py_passthrough(text: str) -> Optional[Dict[str, Any]]:
    try:
        tree = ast.parse(textwrap.dedent(text))
    except SyntaxError:
        return None
    fn = tree.body[0] if tree.body else None
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant) and isinstance(s.value.value, str))]
    if len(body) != 1 or not isinstance(body[0], ast.Return) or not isinstance(body[0].value, ast.Call):
        return None
    call = body[0].value
    a = fn.args
    params = [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs if p.arg not in ("self", "cls")]
    params += [p.arg for p in (a.vararg, a.kwarg) if p is not None]
    passed = [x.id for x in call.args if isinstance(x, ast.Name)]
    passed += [x.value.id for x in call.args if isinstance(x, ast.Starred) and isinstance(x.value, ast.Name)]
    passed += [k.value.id for k in call.keywords if isinstance(k.value, ast.Name)]
    starred = any(isinstance(x, ast.Starred) for x in call.args) or any(k.arg is None for k in call.keywords)
    callee = _dotted(call.func)
    if callee is None:
        return None
    all_named = len(passed) == len(call.args) + len(call.keywords) or starred
    return {
        "name": fn.name,
        "callee": callee,
        "passthrough": bool(all_named and set(passed) <= set(params) and (starred or len(passed) == len(params))),
    }


_TS_FN = re.compile(
    r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\s+(?P<n1>\w+)\s*\((?P<p1>[^)]*)\)|const\s+(?P<n2>\w+)\s*=\s*(?:async\s+)?\((?P<p2>[^)]*)\)\s*=>)\s*\{?\s*(?:return\s+)?(?P<callee>[\w.$]+)\s*\((?P<args>[^)]*)\)",
    re.S,
)


def _ts_passthrough(text: str) -> Optional[Dict[str, Any]]:
    m = _TS_FN.match(text.strip())
    if not m:
        return None
    params = [p.split(":")[0].split("=")[0].strip().lstrip(".") for p in (m.group("p1") or m.group("p2") or "").split(",") if p.strip()]
    args = [a.strip().lstrip(".") for a in (m.group("args") or "").split(",") if a.strip()]
    simple = all(re.fullmatch(r"\w+", a) for a in args)
    return {
        "name": m.group("n1") or m.group("n2"),
        "callee": m.group("callee"),
        "passthrough": bool(simple and args == params),
    }


def classify_match(file: str, text: str) -> Dict[str, Any]:
    info = _py_passthrough(text) if file.endswith(".py") else _ts_passthrough(text)
    return info or {"name": None, "callee": None, "passthrough": False}


# --- tool receipts ----------------------------------------------------------------

def _ast_grep(prefix: List[str], root: Path, timeout: int) -> Tuple[Dict[str, Any], List[str], int, str]:
    argv = [*prefix, "scan", "--config", str(RULES), "--json", "."]
    code, out, err = run(argv, root, timeout)
    matches = json.loads(out) if out.strip().startswith("[") else []
    entries = []
    for m in matches:
        info = classify_match(m["file"], m["text"])
        entries.append({
            "file": m["file"], "line": m["range"]["start"]["line"] + 1, "rule": m.get("ruleId"),
            "name": info["name"], "callee": info["callee"], "passthrough": info["passthrough"],
        })
    entries.sort(key=lambda e: (not e["passthrough"], e["file"], e["line"]))
    return {
        "passthrough": [e for e in entries if e["passthrough"]],
        "single_call_functions": [e for e in entries if not e["passthrough"]],
    }, argv, code, err


def _jscpd(prefix: List[str], root: Path, out_dir: Path, timeout: int) -> Tuple[Dict[str, Any], List[str], int, str]:
    report_dir = out_dir / "jscpd"
    argv = [*prefix, "--reporters", "json", "--output", str(report_dir), "--silent", "--min-tokens", "50", "--format", JSCPD_FORMATS, "--ignore", JSCPD_IGNORE, "."]
    code, _, err = run(argv, root, timeout)
    report = report_dir / "jscpd-report.json"
    if not report.is_file():
        return {}, argv, code or 1, err or "no report written"
    data = json.loads(report.read_text(encoding="utf-8"))
    clones = [
        {
            "a": f"{d['firstFile']['name']}:{d['firstFile']['start']}-{d['firstFile']['end']}",
            "b": f"{d['secondFile']['name']}:{d['secondFile']['start']}-{d['secondFile']['end']}",
            "lines": d.get("lines"), "tokens": d.get("tokens"), "format": d.get("format"),
        }
        for d in data.get("duplicates", [])
    ]
    clones.sort(key=lambda c: -(c["lines"] or 0))
    total = data.get("statistics", {}).get("total", {})
    return {"clones": clones, "duplicated_lines": total.get("duplicatedLines"), "percentage": total.get("percentage")}, argv, 0, err


def _symbol(file: Optional[str], x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return {"file": file, "name": x.get("name"), "line": x.get("line")}
    return {"file": file, "name": x, "line": None}


def _knip(prefix: List[str], root: Path, timeout: int) -> Tuple[Dict[str, Any], List[str], int, str]:
    argv = [*prefix, "--reporter", "json", "--no-progress"]
    code, out, err = run(argv, root, timeout)
    if not out.strip().startswith("{"):
        return {}, argv, code or 1, err or "no JSON on stdout"
    data = json.loads(out)
    unused_files, unused_exports, unused_types, unused_deps, unlisted = [], [], [], [], []
    for issue in data.get("issues", []):
        f = issue.get("file")
        unused_files += [x.get("name", f) if isinstance(x, dict) else f for x in issue.get("files", [])]
        unused_exports += [_symbol(f, x) for x in issue.get("exports", [])]
        unused_types += [_symbol(f, x) for x in issue.get("types", [])]
        for key in ("dependencies", "devDependencies"):
            unused_deps += [{"file": f, "name": x.get("name") if isinstance(x, dict) else x, "kind": key} for x in issue.get(key, [])]
        unlisted += [{"file": f, "name": x.get("name") if isinstance(x, dict) else x} for x in issue.get("unlisted", [])]
    return {
        "unused_files": sorted(set(unused_files)), "unused_exports": unused_exports,
        "unused_types": unused_types, "unused_dependencies": unused_deps, "unlisted": unlisted,
    }, argv, 0, err


def _ruff(prefix: List[str], root: Path, timeout: int) -> Tuple[Dict[str, Any], List[str], int, str]:
    argv = [*prefix, "check", "--select", "F401,F811,F841,F842,ERA001,ARG", "--output-format", "json", "--exit-zero", "--no-cache", "."]
    code, out, err = run(argv, root, timeout)
    if not out.strip().startswith("["):
        return {}, argv, code or 1, err or "no JSON on stdout"
    findings = [
        {"file": os.path.relpath(x["filename"], root) if os.path.isabs(x["filename"]) else x["filename"],
         "line": x["location"]["row"], "code": x["code"], "message": x["message"]}
        for x in json.loads(out)
    ]
    by_code = Counter(x["code"] for x in findings)
    return {"by_code": dict(by_code.most_common()), "findings": findings}, argv, 0, err


def _depcruise(prefix: List[str], root: Path, out_dir: Path, files: List[str], timeout: int) -> Tuple[Dict[str, Any], List[str], int, str]:
    sources = [f for f in code_files(files, JS_EXT) if not re.search(r"\.(test|spec|stories)\.|/__tests__/|\.d\.ts$", f)]
    if not sources:
        return {}, prefix, 1, "no JS/TS source files"
    config = out_dir / "depcruise.config.json"
    config.write_text(json.dumps(DEPCRUISE_CONFIG), encoding="utf-8")
    argv = [*prefix, "--config", str(config), "--output-type", "json", *sources[:2000]]
    code, out, err = run(argv, root, timeout)
    if not out.strip().startswith("{"):
        return {}, argv, code or 1, err or "no JSON on stdout"
    data = json.loads(out)
    summary = data.get("summary", {})
    cycles = []
    seen = set()
    for v in summary.get("violations", []):
        cycle = tuple(c.get("name") if isinstance(c, dict) else c for c in v.get("cycle", []))
        key = frozenset(cycle)
        if cycle and key not in seen:
            seen.add(key)
            cycles.append(list(cycle))
    fan_in: Counter = Counter()
    for m in data.get("modules", []):
        for d in m.get("dependencies", []):
            fan_in[d.get("resolved")] += 1
    return {
        "modules": summary.get("totalCruised"), "dependencies": summary.get("totalDependenciesCruised"),
        "cycles": cycles,
        "most_imported": [{"module": k, "importers": n} for k, n in fan_in.most_common(20) if k and "node_modules" not in k],
    }, argv, 0, err


def _scc(prefix: List[str], root: Path, timeout: int) -> Tuple[Dict[str, Any], List[str], int, str]:
    argv = [*prefix, "--format", "json", "--by-file", "--no-cocomo", "."]
    code, out, err = run(argv, root, timeout)
    if not out.strip().startswith("["):
        return {}, argv, code or 1, err or "no JSON on stdout"
    data = json.loads(out)
    files = [
        {"file": f.get("Location"), "language": lang.get("Name"), "code": f.get("Code"), "complexity": f.get("Complexity")}
        for lang in data
        for f in lang.get("Files", [])
    ]
    files.sort(key=lambda f: -(f["complexity"] or 0))
    return {"languages": [{"name": lang.get("Name"), "files": lang.get("Count"), "code": lang.get("Code"), "complexity": lang.get("Complexity")} for lang in data], "most_complex": files[:30]}, argv, 0, err


# --- orchestration ----------------------------------------------------------------

def applicable(stacks: List[str]) -> Dict[str, Optional[str]]:
    """tool → None when it applies, else the reason it does not."""
    js = "js" in stacks
    py = "py" in stacks
    return {
        "sizes": None, "churn": None, "scc": None, "ast-grep": None if (js or py) else "no JS/TS or Python files",
        "jscpd": None, "knip": None if js else "no JS/TS", "ruff": None if py else "no Python",
        "depcruise": None if js else "no JS/TS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--no-fetch", action="store_true", help="PATH binaries only; never npx/uvx")
    parser.add_argument("--only", default="", help="comma-separated tool names")
    parser.add_argument("--skip", default="", help="comma-separated tool names")
    parser.add_argument("--churn-days", type=int, default=180)
    parser.add_argument("--timeout", type=int, default=300, help="seconds per tool")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    files = tracked_files(root)
    stack = detect(root, files)
    only = {t for t in args.only.split(",") if t}
    skip = {t for t in args.skip.split(",") if t}
    plan = applicable(stack["stacks"])
    manifest: Dict[str, Any] = {"root": str(root), "stack": stack, "tools": {}}
    results: Dict[str, Dict[str, Any]] = {}

    def record(tool: str, status: str, **extra: Any) -> None:
        manifest["tools"][tool] = {"status": status, **extra}

    def job(tool: str) -> None:
        if (only and tool not in only) or tool in skip:
            record(tool, "skipped", reason="excluded by flag")
            return
        if plan[tool]:
            record(tool, "skipped", reason=plan[tool])
            return
        try:
            if tool == "sizes":
                results[tool] = sizes(root, files)
                record(tool, "ran", command="stdlib")
                return
            if tool == "churn":
                results[tool] = churn(root, args.churn_days, files)
                record(tool, "ran" if "error" not in results[tool] else "failed", command="git log", reason=results[tool].get("error"))
                return
            prefix = resolve(tool, fetch=not args.no_fetch)
            if not prefix:
                hint = {"scc": "brew install scc", "ast-grep": "pip install ast-grep-cli / npm i -g @ast-grep/cli"}.get(tool, "not on PATH")
                record(tool, "skipped", reason=f"not on PATH ({hint})" + ("; --no-fetch set" if args.no_fetch else ""))
                return
            if tool == "ast-grep":
                data, argv, code, err = _ast_grep(prefix, root, args.timeout)
            elif tool == "jscpd":
                data, argv, code, err = _jscpd(prefix, root, out, args.timeout)
            elif tool == "knip":
                data, argv, code, err = _knip(prefix, root, args.timeout)
            elif tool == "ruff":
                data, argv, code, err = _ruff(prefix, root, args.timeout)
            elif tool == "depcruise":
                data, argv, code, err = _depcruise(prefix, root, out, files, args.timeout)
            else:
                data, argv, code, err = _scc(prefix, root, args.timeout)
            if data:
                results[tool] = data
                record(tool, "ran", command=" ".join(argv[:6]) + (" …" if len(argv) > 6 else ""), exit=code)
            else:
                record(tool, "failed", command=" ".join(argv[:6]), exit=code, reason=(err or "").strip()[-400:])
        except (json.JSONDecodeError, KeyError, TypeError, OSError) as exc:
            record(tool, "failed", reason=f"{type(exc).__name__}: {exc}"[:400])

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(job, ALL_TOOLS))

    if "sizes" in results and "churn" in results:
        results["hotspots"] = {"top": hotspots(results["sizes"], results["churn"])}
        manifest["tools"]["hotspots"] = {"status": "ran", "command": "sizes x churn"}

    for tool, data in results.items():
        (out / f"{tool}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "summary.md").write_text(summary(manifest, results), encoding="utf-8")
    print(summary(manifest, results))
    return 0


def summary(manifest: Dict[str, Any], results: Dict[str, Dict[str, Any]]) -> str:
    tools = manifest["tools"]
    ran = [t for t, v in tools.items() if v["status"] == "ran"]
    off = [f"{t} ({v.get('reason', v['status'])})" for t, v in tools.items() if v["status"] != "ran"]
    lines = [
        f"# Receipts — {manifest['root']}",
        "",
        f"Stack: {', '.join(manifest['stack']['stacks']) or 'unknown'} · ran: {', '.join(ran)}",
        f"Did not run: {'; '.join(off) if off else 'none'}",
        "",
    ]
    s = results.get("sizes")
    if s:
        lines.append(f"**sizes** {s['files']} files, {s['lines']} lines. Largest: " + ", ".join(f"{x['file']} ({x['lines']})" for x in s["largest"][:8]))
    c = results.get("churn")
    if c and "hottest" in c:
        lines.append(f"**churn** {c['commits']} commits in {c['days']}d. Hottest: " + ", ".join(f"{x['file']} ({x['changes']})" for x in c["hottest"][:8]))
    h = results.get("hotspots")
    if h:
        lines.append("**hotspots** (changes x lines): " + ", ".join(f"{x['file']} ({x['score']})" for x in h["top"][:8]))
    a = results.get("ast-grep")
    if a:
        lines.append(f"**ast-grep** {len(a['passthrough'])} pass-through functions (parameters handed straight to one call), {len(a['single_call_functions'])} single-call functions. Pass-throughs: " + ", ".join(f"{x['file']}:{x['line']} {x['name']}→{x['callee']}" for x in a["passthrough"][:12]))
    j = results.get("jscpd")
    if j:
        lines.append(f"**jscpd** {len(j['clones'])} clone pairs, {j['duplicated_lines']} duplicated lines ({j['percentage']}%). Largest: " + ", ".join(f"{x['a']} ≡ {x['b']} ({x['lines']}l)" for x in j["clones"][:6]))
    k = results.get("knip")
    if k:
        lines.append(f"**knip** {len(k['unused_files'])} unused files, {len(k['unused_exports'])} unused exports, {len(k['unused_types'])} unused types, {len(k['unused_dependencies'])} unused deps, {len(k['unlisted'])} unlisted. Exports: " + ", ".join(f"{x['file']}:{x['line']} {x['name']}" for x in k["unused_exports"][:10]))
    r = results.get("ruff")
    if r:
        lines.append(f"**ruff** {sum(r['by_code'].values())} findings by code {r['by_code']}. First: " + ", ".join(f"{x['file']}:{x['line']} {x['code']}" for x in r["findings"][:10]))
    d = results.get("depcruise")
    if d:
        lines.append(f"**depcruise** {d['modules']} modules, {d['dependencies']} edges, {len(d['cycles'])} cycles. Most imported: " + ", ".join(f"{x['module']} ({x['importers']})" for x in d["most_imported"][:6]) + (". Cycles: " + "; ".join(" → ".join(c) for c in d["cycles"][:4]) if d["cycles"] else ""))
    sc = results.get("scc")
    if sc:
        lines.append("**scc** most complex: " + ", ".join(f"{x['file']} ({x['complexity']})" for x in sc["most_complex"][:8]))
    lines.append("")
    lines.append("Full receipts: one JSON per tool in this directory; cite as `<tool>.json#<path>`.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
