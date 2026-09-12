#!/usr/bin/env python3
"""Map a ported target's failing tests to its bug records, then finalize it.

    tools/map.py CRATE TEST=BUG[,intermittent] ... [--sev BUG=low|medium|high ...] [--no-finalize]

For every TEST=BUG pair: adds `"TEST" = "BUG"` (or the intermittent table form) under
`[expected_failures]` in target.toml; sets the bug's `test` field to its first mapped test
if the field is empty; and appends one `[[bug.observed]]` row (pinned commit/version,
zoo.toml's hegel pin, today, "reproduces") to each bug that gained a test. Bugs whose
reproducer must stay `#[ignore]`d (process aborts) are simply not mapped and keep `test = ""`.
Then runs `tools/port.py --finalize CRATE` unless --no-finalize.
"""
import argparse
import datetime
import pathlib
import re
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("crate")
    ap.add_argument("pairs", nargs="*", help="TEST=BUG or TEST=BUG,intermittent")
    ap.add_argument("--sev", action="append", default=[], help="BUG=low|medium|high")
    ap.add_argument("--no-finalize", action="store_true")
    a = ap.parse_args()

    tdir = ROOT / "targets" / "rust" / a.crate
    ttoml, btoml = tdir / "target.toml", tdir / "bugs.toml"
    target = tomllib.loads(ttoml.read_text())
    pin = tomllib.loads((ROOT / "zoo.toml").read_text())["rust"]["version"]
    commit = target["base"]["commit"][:12]
    version = target["base"].get("version", "")
    today = datetime.date.today().isoformat()

    bugs = tomllib.loads(btoml.read_text())
    known = {b["id"] for b in bugs.get("bug", [])}

    # expected failures
    lines = []
    first_test: dict[str, str] = {}
    for pair in a.pairs:
        test, _, bug = pair.partition("=")
        intermittent = bug.endswith(",intermittent")
        bug = bug.removesuffix(",intermittent")
        if bug not in known:
            sys.exit(f"unknown bug {bug}; known: {sorted(known)}")
        if intermittent:
            lines.append(f'"{test}" = {{ bug = "{bug}", intermittent = true }}\n')
        else:
            lines.append(f'"{test}" = "{bug}"\n')
        first_test.setdefault(bug, test)
    s = ttoml.read_text()
    if "[expected_failures]\n" not in s:
        s = s.rstrip("\n") + "\n\n[expected_failures]\n"
    head, _, tail = s.partition("[expected_failures]\n")
    s = head + "[expected_failures]\n" + "".join(lines) + tail
    ttoml.write_text(s)

    # bug rows
    sev = dict(x.split("=", 1) for x in a.sev)
    b = btoml.read_text()
    for bid, test in first_test.items():
        b = re.sub(
            r'(id = "%s"\n(?:.*\n)*?)test = ""' % re.escape(bid),
            lambda m: m.group(1) + 'test = "%s"' % test, b, count=1)
    for bid, level in sev.items():
        b = re.sub(
            r'(id = "%s"\n(?:.*\n)*?)severity = ""' % re.escape(bid),
            lambda m: m.group(1) + 'severity = "%s"' % level, b, count=1)
    # append an observed row to each mapped bug: split on [[bug]] blocks
    blocks = re.split(r"(?m)^(?=\[\[bug\]\]\n)", b)
    out = []
    for blk in blocks:
        m = re.search(r'^id = "([^"]+)"', blk, re.M)
        if m and m.group(1) in first_test and "[[bug.observed]]" not in blk:
            blk = blk.rstrip("\n") + (
                f'\n\n[[bug.observed]]\nversion = "{version}"\ncommit = "{commit}"\n'
                f'hegel = "{pin}"\ndate = "{today}"\nresult = "reproduces"\n\n')
        out.append(blk)
    b = "".join(out).rstrip("\n") + "\n"
    btoml.write_text(b)
    tomllib.loads(btoml.read_text())  # must still parse

    unmapped = known - set(first_test)
    if unmapped:
        print(f"note: {sorted(unmapped)} have no failing test (abort-only reproducer?)")
    if a.no_finalize:
        return 0
    return subprocess.call([str(ROOT / "tools" / "port.py"), "--finalize", a.crate])


if __name__ == "__main__":
    sys.exit(main())
