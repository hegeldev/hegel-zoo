#!/usr/bin/env python3
"""Inventory every test the zoo's patches add, with its docs, body, README entry and the
bugs whose record names it. Writes properties.jsonl and bugs.jsonl next to this file.

Usage: python3 studies/property-taxonomy/extract.py   (from the zoo root)
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BODY_LIMIT = 120  # lines of body kept per test

PIN_NAME = re.compile(r"known_bug|known_failure|_pin\b|pin_|^pin|Pin[A-Z]|regress|repro|_bug\d*$|bug_\d+", re.I)


def split_patch(text: str) -> dict[str, list[str]]:
    """file path -> added lines (leading '+' stripped), in order; context lines dropped."""
    files: dict[str, list[str]] = {}
    cur: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            path = path[2:] if path.startswith("b/") else path
            cur = files.setdefault(path, [])
        elif line.startswith("+") and not line.startswith("+++") and cur is not None:
            cur.append(line[1:])
    return files


def comment_above(lines: list[str], i: int, markers: tuple[str, ...]) -> str:
    out: list[str] = []
    j = i - 1
    while j >= 0:
        s = lines[j].strip()
        if any(s.startswith(m) for m in markers):
            out.append(s)
            j -= 1
        elif s.startswith("#[") and "test" not in s and "hegel" not in s:
            j -= 1  # other attributes between comment and test attribute
        else:
            break
    out.reverse()
    cleaned = []
    for s in out:
        for m in markers:
            if s.startswith(m):
                s = s[len(m):]
                break
        cleaned.append(s.strip())
    return "\n".join(cleaned).strip()


def block_comment_above(lines: list[str], i: int) -> str:
    """// lines, or a /* ... */ block, directly above line i (TypeScript)."""
    c = comment_above(lines, i, ("///", "//"))
    if c:
        return c
    j = i - 1
    while j >= 0 and not lines[j].strip():
        j -= 1
    if j >= 0 and lines[j].strip().endswith("*/"):
        out = []
        while j >= 0:
            s = lines[j].strip()
            out.append(s.strip("/*").strip(" *"))
            if s.startswith("/*"):
                break
            j -= 1
        out.reverse()
        return "\n".join(x for x in out if x).strip()
    return ""


def body_from(lines: list[str], i: int) -> list[str]:
    """Lines from i until braces balance (naive; ignores strings)."""
    depth = 0
    seen_open = False
    out = []
    for k in range(i, min(len(lines), i + 2000)):
        line = lines[k]
        out.append(line)
        depth += line.count("{") - line.count("}")
        if "{" in line:
            seen_open = True
        if seen_open and depth <= 0:
            break
    return out


RUST_ATTR = re.compile(r"^\s*#\[(hegel::)?test\b")
RUST_SM = re.compile(r"^\s*#\[hegel::state_machine")
RUST_FN = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+(\w+)")
RUST_ITEM = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|impl(?:<[^>]*>)?)\s+(\w+)")


def scan_rust(path: str, lines: list[str]) -> list[dict]:
    props = []
    for i, line in enumerate(lines):
        if RUST_ATTR.match(line) or RUST_SM.match(line):
            is_sm = bool(RUST_SM.match(line))
            is_hegel = "hegel::" in line
            attrs = [line.strip()]
            k = i + 1
            while k < len(lines) and lines[k].strip().startswith("#["):
                attrs.append(lines[k].strip())
                k += 1
            if k >= len(lines):
                continue
            m = (RUST_ITEM if is_sm else RUST_FN).match(lines[k])
            if not m:
                continue
            name = m.group(1)
            body = body_from(lines, k)
            comment = comment_above(lines, i, ("///", "//!", "//"))
            text = "\n".join(body)
            if is_sm:
                kind = "state_machine"
            elif is_hegel:
                kind = "hegel"
            elif re.search(r"Hegel::new\(|\.draw\(|hegel::TestCase|stateful::run", text):
                kind = "hegel"  # closure-style property inside a plain #[test]
                attrs.append("closure-style")
            else:
                kind = "plain"
            props.append(dict(name=name, file=path, kind=kind, attrs=attrs, comment=comment,
                              body=body[:BODY_LIMIT], body_lines=len(body)))
    return props


GO_FN = re.compile(r"^func (Test\w+)\(\w+ \*testing\.T\)")


def scan_go(path: str, lines: list[str]) -> list[dict]:
    props = []
    for i, line in enumerate(lines):
        m = GO_FN.match(line)
        if not m:
            continue
        body = body_from(lines, i)
        text = "\n".join(body)
        kind = "hegel" if ("hegel." in text or "property(" in text) else "plain"
        props.append(dict(name=m.group(1), file=path, kind=kind, attrs=[],
                          comment=comment_above(lines, i, ("//",)), body=body[:BODY_LIMIT], body_lines=len(body)))
    return props


TS_FN = re.compile(r"""^\s*(test|it|property|pin)\(\s*["'`](TestHegel\w*)["'`]""")


def scan_ts(path: str, lines: list[str]) -> list[dict]:
    props = []
    for i, line in enumerate(lines):
        m = TS_FN.match(line)
        if not m:
            continue
        body = body_from(lines, i)
        kind = "plain" if m.group(1) == "pin" else "hegel"
        props.append(dict(name=m.group(2), file=path, kind=kind, attrs=[m.group(1)],
                          comment=block_comment_above(lines, i), body=body[:BODY_LIMIT], body_lines=len(body)))
    return props


SCANNERS = {"rust": scan_rust, "go": scan_go, "typescript": scan_ts}


def readme_entries(readme: str, names: list[str]) -> dict[str, str]:
    """For each test name, the README paragraph/bullet that mentions it (first mention)."""
    out: dict[str, str] = {}
    lines = readme.splitlines()
    for name in names:
        pat = re.compile(r"(?<![\w])" + re.escape(name) + r"(?![\w])")
        for i, line in enumerate(lines):
            if pat.search(line):
                # expand to the bullet/paragraph: back to a line starting the bullet, forward until blank/next bullet
                s = i
                while s > 0 and lines[s].strip() and not re.match(r"^\s*([-*]|\d+\.|\|)", lines[s]) and lines[s - 1].strip():
                    s -= 1
                e = i + 1
                while e < len(lines) and lines[e].strip() and not re.match(r"^\s*([-*]|\d+\.|#)", lines[e]) and (
                        not lines[e].startswith("|") or lines[i].startswith("|")):
                    e += 1
                para = " ".join(x.strip() for x in lines[s:e])
                out[name] = para[:1500]
                break
    return out


def load_toml(p: Path) -> dict:
    if not p.is_file():
        return {}
    try:
        return tomllib.loads(p.read_text())
    except tomllib.TOMLDecodeError as exc:
        print(f"warning: {p}: {exc}", file=sys.stderr)
        return {}


def main() -> None:
    props_all: list[dict] = []
    bugs_all: list[dict] = []
    targets = sorted(p for p in ROOT.glob("targets/*/*") if (p / "target.toml").is_file())
    unmatched: list[str] = []
    for tdir in targets:
        lang, tname = tdir.parent.name, tdir.name
        meta = load_toml(tdir / "target.toml")
        patch = (tdir / "hegel.patch").read_text(errors="replace") if (tdir / "hegel.patch").is_file() else ""
        readme = (tdir / "README.md").read_text(errors="replace") if (tdir / "README.md").is_file() else ""
        files = split_patch(patch)
        props: list[dict] = []
        for path, lines in files.items():
            props.extend(SCANNERS[lang](path, lines))
        for p in props:
            p["target"] = f"{lang}/{tname}"
            p["lang"] = lang
            p["imported"] = "origin" in meta
            p["id"] = f"{lang}/{tname}::{p['name']}"
            p["bugs"] = []
            p["bugs_via_pin"] = []
            if p["kind"] == "plain" and (PIN_NAME.search(p["name"]) or "known" in p["comment"].lower()[:200]):
                p["kind"] = "pin"
            p["named_pin"] = bool(PIN_NAME.search(p["name"]))
            p["bugs_via_mention"] = []
        # state machines that a #[hegel::test] drives: mark the driver as stateful, keep the struct
        # only when no driver mentions it
        by_name = {}
        for p in props:
            by_name.setdefault(p["name"], []).append(p)
        sms = [p for p in props if p["kind"] == "state_machine"]
        for sm in sms:
            drivers = [p for p in props if p["kind"] == "hegel" and any(sm["name"] in l for l in p["body"])]
            for d in drivers:
                d["stateful"] = True
            sm["drivers"] = [d["name"] for d in drivers]
        for p in props:
            p.setdefault("stateful", False)
            text = "\n".join(p["body"])
            if re.search(r"state_machine|stateful::|StateMachine|\.run\(\)|RunStateMachine|run_state_machine|hegel\.(Run|Machine)|machine", text):
                p["stateful"] = True
        names = [p["name"] for p in props]
        entries = readme_entries(readme, names)
        for p in props:
            p["readme"] = entries.get(p["name"], "")
        # bugs
        expected = {}
        for k, v in (meta.get("expected_failures") or {}).items():
            expected[k] = v if isinstance(v, str) else v.get("bug", "")
        for b in load_toml(tdir / "bugs.toml").get("bug", []):
            rec = dict(mentioned_by=[], id=b.get("id", ""), target=f"{lang}/{tname}", lang=lang, title=b.get("title", ""),
                       kind=b.get("kind", ""), severity=b.get("severity", ""), status=b.get("status", ""),
                       test=b.get("test", ""), property=None, pin=None, origin_property=None)
            tests = [rec["test"]] if isinstance(rec["test"], str) else list(rec["test"])
            tests = [t for t in tests if t]
            # also the expected_failures entries pointing at this bug
            tests += [k for k, v in expected.items() if v == rec["id"] and k not in tests]
            found = None
            for t in tests:
                short = t.split("::")[-1]
                cands = by_name.get(short) or by_name.get(t) or []
                if cands:
                    found = cands[0]
                    break
            if found is None:
                if tests:
                    unmatched.append(f"{rec['id']} -> {tests}")
                bugs_all.append(rec)
                continue
            if found["kind"] in ("pin", "plain"):
                rec["pin"] = found["id"]
                # origin: another (non-pin) property named in the pin's comment/body/readme
                hay = found["comment"] + "\n" + "\n".join(found["body"]) + "\n" + found["readme"]
                others = [p for p in props if p["kind"] in ("hegel", "state_machine") and p["name"] != found["name"]]
                origin = None
                m = re.search(r"(?:found by|shrunk from|from|by|via|see)\s+(?:the\s+)?`?(\w+)`?", hay, re.I)
                if m and m.group(1) in by_name and by_name[m.group(1)][0]["kind"] == "hegel":
                    origin = by_name[m.group(1)][0]
                if origin is None:
                    hits = [p for p in others if re.search(r"(?<!\w)" + re.escape(p["name"]) + r"(?!\w)", hay)]
                    if hits:
                        origin = hits[0]
                if origin is not None:
                    rec["origin_property"] = origin["id"]
                    origin["bugs_via_pin"].append(rec["id"])
                found["bugs"].append(rec["id"])
            else:
                rec["property"] = found["id"]
                found["bugs"].append(rec["id"])
            bugs_all.append(rec)
        for b in bugs_all:
            if b["target"] != f"{lang}/{tname}" or b["property"] is not None or not b["id"]:
                continue
            pat = re.compile(r"(?<![\w/])" + re.escape(b["id"]) + r"(?![\w-])")
            # comment and body only: README entries can be slices of a table that mention other bugs
            hits = [p for p in props if p["kind"] == "hegel" and (pat.search(p["comment"]) or pat.search("\n".join(p["body"])))]
            b["mentioned_by"] = [p["id"] for p in hits]
            for p in hits:
                p["bugs_via_mention"].append(b["id"])
        props_all.extend(props)

    with (OUT / "properties.jsonl").open("w") as f:
        for p in props_all:
            f.write(json.dumps(p) + "\n")
    with (OUT / "bugs.jsonl").open("w") as f:
        for b in bugs_all:
            f.write(json.dumps(b) + "\n")

    from collections import Counter
    print("targets", len(targets))
    print("tests by lang/kind", Counter((p["lang"], p["kind"]) for p in props_all))
    print("stateful", sum(p["stateful"] for p in props_all if p["kind"] == "hegel"))
    print("with comment", sum(bool(p["comment"]) for p in props_all), "with readme", sum(bool(p["readme"]) for p in props_all),
          "with either", sum(bool(p["comment"] or p["readme"]) for p in props_all))
    print("bugs", len(bugs_all), "linked to property", sum(b["property"] is not None for b in bugs_all),
          "linked to pin", sum(b["pin"] is not None for b in bugs_all),
          "pin with origin", sum(b["origin_property"] is not None for b in bugs_all),
          "no test", sum(not b["test"] for b in bugs_all), "unmatched", len(unmatched))
    for u in unmatched[:40]:
        print("  unmatched:", u)
    hp = [p for p in props_all if p["kind"] == "hegel"]
    print("hegel props", len(hp), "with bugs (direct)", sum(bool(p["bugs"]) for p in hp),
          "with bugs (direct or via pin)", sum(bool(p["bugs"] or p["bugs_via_pin"]) for p in hp))


if __name__ == "__main__":
    main()
