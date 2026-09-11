#!/usr/bin/env python3
"""Import a crate from DRMacIver/hegel-rust-oss-bug-finding as a raw zoo target.

  tools/import_predecessor.py <crate> [--bugs-crate <name-in-trophies>] [--force]
  tools/import_predecessor.py --list            # crates in PATCHES.md not yet in targets/rust

Writes targets/rust/<crate>/ with:
  target.toml   upstream + base commit from PATCHES.md (abbreviated sha: `zoo fetch` resolves it),
                hegel.version as the patch pins it (0.28.2), empty expected_failures
  hegel.patch   the predecessor patch minus its HEGEL_REPORT.md and .gitignore hunks
  bugs.toml     one [[bug]] per TROPHIES.md row for the crate, test = "" (filled while porting)
  README.md     stub with the provenance line

The result is NOT yet a valid target (zoo check fails on the pin and the sha). Porting it —
`zoo fetch`, bump the dependency, fix API drift, `zoo test`, `zoo save`, name the failing tests
in expected_failures and bugs.toml, write the README — makes it one. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/DRMacIver/hegel-rust-oss-bug-finding/main/"
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "work" / "predecessor"
TARGETS = ROOT / "targets" / "rust"


def fetch(rel: str) -> str:
    p = CACHE / rel
    if not p.is_file():
        p.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(RAW + rel) as r:
            p.write_bytes(r.read())
    return p.read_text()


def toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def patches_index() -> dict[str, dict]:
    """crate -> {upstream, commit, date, subject} from PATCHES.md."""
    out = {}
    for line in fetch("PATCHES.md").splitlines():
        m = re.match(r"^\| `([^`]+)` \| (\S+) \| `([0-9a-f]+)` \| (\d{4}-\d{2}-\d{2}) \| (.*) \|$", line)
        if m:
            out[m.group(1)] = dict(upstream=m.group(2), commit=m.group(3), date=m.group(4), subject=m.group(5).strip())
    return out


def strip_patch(text: str, drop=("HEGEL_REPORT.md", ".gitignore")) -> str:
    parts = re.split(r"(?m)^(?=diff --git )", text)
    keep = []
    for part in parts:
        if not part.strip():
            continue
        m = re.match(r"diff --git a/(\S+) b/", part)
        path = m.group(1) if m else ""
        if Path(path).name in drop:
            continue
        keep.append(part)
    return "".join(keep)


def trophies_for(crate: str) -> list[dict]:
    rows = []
    for line in fetch("TROPHIES.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not re.fullmatch(r"\d+(-\d+)?", cells[0]):
            continue
        num, crate_col, summary, model, status = cells[:5]
        name = re.split(r"[\s(]", crate_col, 1)[0]
        if name == crate or crate_col.startswith(crate + " "):
            rows.append(dict(num=num, crate_col=crate_col, summary=summary, model=model, status=status))
    return rows


def classify(summary: str, status: str) -> tuple[str, str]:
    s = (summary + " " + status).lower()
    if "duplicate" in s or "dupe" in s or "residual of open" in s:
        st = "duplicate"
    else:
        st = "open"
    if "silent" in s and ("corrupt" in s or "wrong" in s or "data" in s):
        kind = "silent-corruption"
    elif "stack overflow" in s or "sigabrt" in s or "abort" in s or "infinite" in s or "oom" in s:
        kind = "abort"
    elif "hang" in s or "deadlock" in s:
        kind = "hang"
    elif "panic" in s:
        kind = "panic"
    elif "roundtrip" in s or "round-trip" in s or "round trip" in s:
        kind = "roundtrip"
    elif "docs" in s or "documented" in s or "documentation" in s:
        kind = "contract"
    elif "disagree" in s or " vs " in s or "differ" in s:
        kind = "differential"
    else:
        kind = "contract"
    return kind, st


def write_target(crate: str, bugs_crate: str, force: bool) -> None:
    idx = patches_index()
    if crate not in idx:
        sys.exit(f"{crate} is not in PATCHES.md")
    info = idx[crate]
    d = TARGETS / crate
    if d.exists() and not force:
        sys.exit(f"{d} exists (use --force to overwrite)")
    d.mkdir(parents=True, exist_ok=True)

    raw = fetch(f"patches/{crate}.patch")
    patch = strip_patch(raw)
    (d / "hegel.patch").write_text(patch)
    m = re.search(r'^\+hegeltest = (?:"([^"]+)"|\{[^}]*version = "([^"]+)")', patch, re.M)
    pin = (m.group(1) or m.group(2)) if m else "0.28.2"
    # workspace member? the patch's Cargo.toml edit tells us where the crate lives
    cargo = re.findall(r"^diff --git a/((?:[^/\n]+/)*)Cargo\.toml b/", patch, re.M)
    subdir = min(cargo, key=len).rstrip("/") if cargo else ""
    upstream_short = re.sub(r"^https://github\.com/", "", info["upstream"])

    (d / "target.toml").write_text(f"""name = {toml_str(crate)}
language = "rust"
upstream = {toml_str(info["upstream"])}
subdir = {toml_str(subdir)}
license = ""
ai_policy_checked = "2026-07-22"
origin = {toml_str(f"DRMacIver/hegel-rust-oss-bug-finding patches/{crate}.patch")}

[base]
commit = {toml_str(info["commit"])}
date = {toml_str(info["date"])}
version = ""

[hegel]
version = {toml_str(pin)}

[run]
setup = []

[expected_failures]
""")

    rows = trophies_for(bugs_crate)
    if rows:
        out = []
        for i, r in enumerate(rows, 1):
            kind, status = classify(r["summary"], r["status"])
            url = re.search(r"https?://\S+", r["status"])
            title = r["summary"].replace("`", "").replace("\\|", "|")
            title = re.sub(r"\s+", " ", title)[:200]
            out.append(f"""[[bug]]
id = {toml_str(f"{crate}/{i}")}
title = {toml_str(title)}
kind = {toml_str(kind)}
severity = ""
test = ""
found = {{ commit = {toml_str(info["commit"])}, version = "", hegel = {toml_str(pin)}, date = {toml_str(info["date"])} }}
status = {toml_str(status)}
upstream_issue = {toml_str(url.group(0) if url else "")}
fixed_in = ""
notes = {toml_str(f"Predecessor trophy #{r['num']} ({r['crate_col']}); found by {r['model']}. Triage there: {r['status']}")}
""")
        (d / "bugs.toml").write_text("\n".join(out))

    (d / "README.md").write_text(f"""# {crate}

[{upstream_short}]({info["upstream"]}).

## What is tested

(to write while porting)

## Oracles

## Not tested

## History

- {info["date"]}: predecessor base commit `{info["commit"]}` ({info["subject"]}).
- 2026-07: tests written with hegeltest {pin} in DRMacIver/hegel-rust-oss-bug-finding (`patches/{crate}.patch`).
""")
    print(f"imported {crate}: {patch.count(chr(10))}-line patch, subdir={subdir!r}, pin {pin}, {len(rows)} bug rows")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("crate", nargs="?")
    ap.add_argument("--bugs-crate", help="name used for the crate in TROPHIES.md if different")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        have = {p.name for p in TARGETS.iterdir()} if TARGETS.is_dir() else set()
        for c in sorted(patches_index()):
            if c not in have:
                print(c)
        return
    if not a.crate:
        ap.error("crate required")
    write_target(a.crate, a.bugs_crate or a.crate, a.force)


if __name__ == "__main__":
    main()
