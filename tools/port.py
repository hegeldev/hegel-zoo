#!/usr/bin/env python3
"""Semi-automatic port of predecessor Rust targets to the pinned hegeltest.

  tools/port.py <crate>...             import (if needed), apply, bump, fix, test; finalize if clean
  tools/port.py --finalize <crate>...  after manual fixes in work/: save, metadata, README, check

Per crate the automatic pass does:
  1. tools/import_predecessor.py <crate>       (skipped if targets/rust/<crate> exists)
  2. tools/zoo apply rust/<crate>              (resolves the base sha)
  3. in work/: rewrite the hegeltest line to the pin; `#[hegel::composite] fn f(tc: TestCase)`
     -> `&TestCase`
  4. tools/zoo test --no-apply rust/<crate>
  5. if it compiled and every failure is already expected: finalize (see --finalize)
     otherwise print what is left for a human: compile errors, or failing tests to map to bugs.

Finalize: tools/zoo save; base.version / license from Cargo.toml; hegel.version = pin; README
"What is tested" drafted from the doc comments above each #[hegel::test]; tools/zoo check.
Outcome per crate is one line: PORTED | COMPILE | MAP | APPLY | ERROR.
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
TARGETS = ROOT / "targets" / "rust"
WORK = ROOT / "work" / "rust"
PIN = tomllib.loads((ROOT / "zoo.toml").read_text())["rust"]["version"]
TODAY = dt.date.today().isoformat()

# hegeltest = "x" | hegeltest = { version = "x", .. } | [dev-dependencies.hegeltest] version = "x"
DEP_RE = re.compile(r'^(\s*hegeltest\s*=\s*)(?:"[^"]+"|(\{[^}\n]*?version\s*=\s*)"[^"]+")'
                    r'|^(\[dev-dependencies\.hegeltest\]\n(?:(?!\[)[^\n]*\n)*?version\s*=\s*)"[^"]+"', re.M)
COMPOSITE_RE = re.compile(r"(#\[(?:hegel::)?composite\][^\n]*\n(?:\s*//[^\n]*\n)*\s*(?:pub(?:\([^)]*\))? )?fn \w+(?:<[^>]*>)?\([^)]*?\btc: )(hegel::)?TestCase\b")


def sh(*cmd: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(list(cmd), cwd=cwd, text=True, capture_output=True, check=check)


def rewrite_dep(cargo: Path) -> bool:
    s = cargo.read_text()

    def sub(m: re.Match) -> str:
        if m.group(3):
            return f'{m.group(3)}"{PIN}"'
        if m.group(2):
            return f'{m.group(1)}{m.group(2)}"{PIN}"'
        return f'{m.group(1)}"{PIN}"'
    new, n = DEP_RE.subn(sub, s)
    if n:
        cargo.write_text(new)
    return bool(n)


def fix_composites(root: Path) -> int:
    n = 0
    for f in root.rglob("*.rs"):
        if "target" in f.parts:
            continue
        s = f.read_text(errors="replace")
        new, k = COMPOSITE_RE.subn(lambda m: m.group(1) + "&" + (m.group(2) or "") + "TestCase", s)
        if k:
            f.write_text(new)
            n += k
    return n


PRINT_ERR = re.compile(r"^error\[E0277\]: `([^`]+)` has no printed representation\n\s+--> (\S+?):(\d+):(\d+)", re.M)


def fix_printable(work: Path, log: str, pkg_dir: Path | None = None) -> int:
    """hegeltest 0.33+: drawn values must be printable. For a type defined in the same file, add
    `hegel::PrettyPrintable` to its derive; otherwise wrap the drawn generator expression in
    `.print_as_debug()` and bring `hegel::Generator` into scope. Returns the number of edits."""
    sites: dict[Path, list[tuple[int, int, str]]] = {}
    for m in PRINT_ERR.finditer(log):
        ty, file, line, col = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        # cargo prints paths relative to the package directory it ran in, else the workspace root
        path = next((p for p in (pkg_dir / file, work / file) if p.is_file()), work / file)
        sites.setdefault(path, []).append((line, col, ty.split("::")[-1].split("<")[0]))
    edits = 0
    for f, locs in sites.items():
        if not f.is_file():
            continue
        lines = f.read_text(errors="replace").split("\n")
        derived: set[str] = set()
        need_import = False
        for line, col, tyname in sorted(set(locs), reverse=True):
            # local type with a derive: add PrettyPrintable to it
            m = re.search(rf"^(\s*)#\[derive\(([^)]*)\)\]\n(\s*(?:pub(?:\([^)]*\))? )?(?:enum|struct) {re.escape(tyname)}\b)",
                          "\n".join(lines), re.M)
            # only derive on test-only types: hegel is a dev-dependency, so a derive on a library
            # type breaks the non-test build. Test-only = a file under tests/ or a tests.rs; a
            # type in a library file (even inside a #[cfg(test)] mod) gets the wrap instead.
            in_test_code = bool(m) and (
                "tests" in f.parts or f.name in ("tests.rs", "test.rs") or f.name.endswith("_tests.rs"))
            if m and in_test_code and tyname not in derived:
                if "PrettyPrintable" not in m.group(2):
                    text = "\n".join(lines)
                    text = text[:m.start()] + f"{m.group(1)}#[derive({m.group(2)}, hegel::PrettyPrintable)]\n{m.group(3)}" + text[m.end():]
                    lines = text.split("\n")
                    edits += 1
                derived.add(tyname)
                continue
            # otherwise wrap the generator expression that starts at (line, col)
            i, j = line - 1, col - 1
            if i >= len(lines) or j > len(lines[i]):
                continue
            # find the end of the expression: first ')' or ',' at depth 0 from (i, j), across lines
            depth, k, row = 0, j, i
            end = None
            while row < len(lines):
                s = lines[row]
                while k < len(s):
                    c = s[k]
                    if c in "([{":
                        depth += 1
                    elif c in ")]}":
                        if depth == 0:
                            end = (row, k)
                            break
                        depth -= 1
                    elif c == "," and depth == 0:
                        end = (row, k)
                        break
                    k += 1
                if end:
                    break
                row, k = row + 1, 0
            if not end:
                continue
            er, ec = end
            lines[er] = lines[er][:ec] + ".print_as_debug()" + lines[er][ec:]
            lines[i] = lines[i][:j] + "(" + lines[i][j:]
            # the '(' shifts the end column when on the same line; put the ')' after the expression
            if er == i:
                lines[er] = lines[er][:ec + 1] + ")" + lines[er][ec + 1:]
            else:
                lines[er] = lines[er][:ec] + ")" + lines[er][ec:]
            need_import = True
            edits += 1
        text = "\n".join(lines)
        already = re.search(r"^\s*use hegel::(?:generators::)?(?:\{[^}]*\b|)Generator\b", text, re.M)
        if need_import and not already:
            # The import must land in the module that draws, and never at file scope of library
            # code (hegel is a dev-dependency). Prefer: after a `use hegel::generators…` line;
            # else right after the nearest `mod … {` above the first draw site; else after the
            # first `use` in the file (integration-test files).
            text, n = re.subn(r"^(\s*)(use hegel::generators(?:::\w+)?(?: as \w+)?;)", r"\1\2\n\1use hegel::Generator;", text, count=1, flags=re.M)
            if not n:
                first = min(l for l, _, _ in locs) - 1
                ls = text.split("\n")
                for k in range(min(first, len(ls) - 1), -1, -1):
                    mm = re.match(r"^(\s*)(?:pub(?:\([^)]*\))? )?mod \w+\s*\{\s*$", ls[k])
                    if mm:
                        ls.insert(k + 1, f"{mm.group(1)}    use hegel::Generator;")
                        n = 1
                        break
                text = "\n".join(ls)
            if not n:
                text, n = re.subn(r"^(\s*)(use [^\n]*;)", r"\1\2\n\1use hegel::Generator;", text, count=1, flags=re.M)
            if not n:
                text = "use hegel::Generator;\n" + text
        f.write_text(text)
    return edits


def cargo_meta(pkg_dir: Path, work: Path) -> tuple[str, str]:
    """(version, license) of the package, following workspace inheritance."""
    try:
        pkg = tomllib.loads((pkg_dir / "Cargo.toml").read_text()).get("package", {})
    except Exception:
        return "", ""
    ws = {}
    for cand in (work / "Cargo.toml",):
        try:
            ws = tomllib.loads(cand.read_text()).get("workspace", {}).get("package", {})
        except Exception:
            pass

    def get(k: str) -> str:
        v = pkg.get(k, "")
        if isinstance(v, dict) and v.get("workspace"):
            v = ws.get(k, "")
        return v if isinstance(v, str) else ""
    return get("version"), get("license")


def doc_bullets(root: Path) -> list[str]:
    """One bullet per #[hegel::test], from the /// comment directly above it, grouped by file."""
    out: list[str] = []
    for f in sorted(root.rglob("*.rs")):
        if "target" in f.parts:
            continue
        lines = f.read_text(errors="replace").splitlines()
        items = []
        for i, line in enumerate(lines):
            if not re.match(r"\s*#\[hegel::test", line):
                continue
            m = re.match(r"\s*fn (\w+)", lines[i + 1]) if i + 1 < len(lines) else None
            name = m.group(1) if m else "?"
            doc = []
            j = i - 1
            while j >= 0 and re.match(r"\s*///", lines[j]):
                doc.insert(0, re.sub(r"^\s*///\s?", "", lines[j]))
                j -= 1
            text = " ".join(d for d in doc if d.strip()) or "(no doc comment)"
            items.append(f"- `{name}`: {text}")
        if items:
            out.append(f"**`{f.relative_to(root)}`**")
            out.extend(items)
            out.append("")
    return out


def finalize(crate: str) -> str:
    tdir = TARGETS / crate
    work = WORK / crate
    meta = tomllib.loads((tdir / "target.toml").read_text())
    subdir = meta.get("subdir", "")
    pkg_dir = work / subdir if subdir else work
    r = sh(str(TOOLS / "zoo"), "save", f"rust/{crate}", check=False)
    if r.returncode:
        return f"ERROR   {crate}: save failed: {r.stderr.strip()[-300:]}"
    version, license_ = cargo_meta(pkg_dir, work)
    tt = tdir / "target.toml"
    s = tt.read_text()
    if version and 'version = ""' in s.split("[base]")[1].split("[hegel]")[0]:
        s = s.replace('version = ""', f'version = "{version}"', 1)
    if license_ and 'license = ""' in s:
        s = s.replace('license = ""', f'license = "{license_}"', 1)
    s = re.sub(r'(\[hegel\]\nversion = )"[^"]*"', rf'\g<1>"{PIN}"', s)
    tt.write_text(s)
    # README: replace the "(to write while porting)" stub with drafted bullets, add history line
    rd = tdir / "README.md"
    txt = rd.read_text()
    bullets = "\n".join(doc_bullets(pkg_dir)).strip()
    txt = txt.replace("(to write while porting)", bullets or "(no hegel tests found?)", 1)
    if f"ported to hegeltest {PIN}" not in txt:
        txt = txt.rstrip("\n") + f"\n- {TODAY}: imported into the zoo; ported to hegeltest {PIN}.\n"
    rd.write_text(txt)
    r = sh(str(TOOLS / "zoo"), "check", f"rust/{crate}", check=False)
    if r.returncode:
        return f"ERROR   {crate}: check failed:\n{r.stdout.strip()}"
    # the disk is small and a Rust target/ dir is 1-3 GB: drop the checkout once the patch is saved
    shutil.rmtree(work, ignore_errors=True)
    return f"PORTED  {crate} ({version or '?'}, {license_ or '?'})"


def port(crate: str) -> str:
    tdir = TARGETS / crate
    if not tdir.exists():
        r = sh(str(TOOLS / "import_predecessor.py"), crate, check=False)
        if r.returncode:
            return f"ERROR   {crate}: import: {r.stderr.strip()[-300:]}"
    r = sh(str(TOOLS / "zoo"), "apply", f"rust/{crate}", check=False)
    if r.returncode:
        return f"APPLY   {crate}: {(r.stdout + r.stderr).strip()[-400:]}"
    meta = tomllib.loads((tdir / "target.toml").read_text())
    subdir = meta.get("subdir", "")
    work = WORK / crate
    pkg_dir = work / subdir if subdir else work
    if not rewrite_dep(pkg_dir / "Cargo.toml"):
        # the patch may have put the dev-dependency in another manifest; try them all
        if not any(rewrite_dep(c) for c in work.rglob("Cargo.toml") if "target" not in c.parts):
            return f"ERROR   {crate}: hegeltest dependency line not found"
    nfix = fix_composites(work)
    for _round in range(4):
        r = sh(str(TOOLS / "zoo"), "test", "--no-apply", f"rust/{crate}", check=False)
        out = r.stdout + r.stderr
        log = (WORK / f"{crate}.log").read_text(errors="replace") if (WORK / f"{crate}.log").exists() else ""
        if not PRINT_ERR.search(log) or not fix_printable(work, log, pkg_dir):
            break
        nfix += 1
    if re.search(r"^error(\[E\d+\])?: ", log, re.M) and "test result" not in log:
        errs = sorted(set(re.findall(r"^error(?:\[E\d+\])?: (.{0,110})", log, re.M)))
        return f"COMPILE {crate} ({nfix} composites fixed): " + " | ".join(errs[:6])
    if "BAD " in out:
        fails = re.findall(r"^\s+(FAIL|PASS\?|MISSING|UPSTREAM)\s+(\S+)", out, re.M)
        return f"MAP     {crate}: " + ", ".join(f"{k} {n}" for k, n in fails)
    if "OK " not in out:
        return f"ERROR   {crate}: no verdict: {out.strip()[-400:]}"
    return finalize(crate)


def main(argv: list[str]) -> int:
    fin = "--finalize" in argv
    crates = [a for a in argv if not a.startswith("--")]
    if not crates:
        print(__doc__)
        return 2
    for c in crates:
        try:
            line = finalize(c) if fin else port(c)
        except Exception as e:  # keep going through the batch
            line = f"ERROR   {c}: {e!r}"
        print(line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
