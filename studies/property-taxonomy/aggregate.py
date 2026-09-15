#!/usr/bin/env python3
"""Merge out/batch-*.json with properties.jsonl and bugs.jsonl; write classified.jsonl and
print the category tables (markdown) used in the report."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATS = ["roundtrip", "external-oracle", "model-oracle", "stateful-model", "internal-consistency",
        "algebraic-law", "spec-postcondition", "rejection", "robustness", "concurrency", "other"]
NAMES = {"roundtrip": "Round trip", "external-oracle": "External oracle", "model-oracle": "Model oracle",
         "stateful-model": "Stateful model", "internal-consistency": "Internal consistency",
         "algebraic-law": "Algebraic / metamorphic law", "spec-postcondition": "Documented postcondition",
         "rejection": "Rejection of invalid input", "robustness": "Robustness (no crash)",
         "concurrency": "Concurrency", "other": "Other"}

P = {p["id"]: p for p in (json.loads(l) for l in (HERE / "properties.jsonl").open())}
B = {b["id"]: b for b in (json.loads(l) for l in (HERE / "bugs.jsonl").open())}

cls: dict[str, dict] = {}
attr: dict[str, dict] = {}
notes = {}
problems = []
for f in sorted((HERE / "out").glob("batch-*.json")):
    try:
        d = json.loads(f.read_text())
    except json.JSONDecodeError as e:
        problems.append(f"{f.name}: invalid JSON: {e}")
        continue
    for c in d.get("properties", []):
        if c["id"] not in P:
            problems.append(f"{f.name}: unknown property id {c['id']}")
            continue
        if c.get("category") not in CATS:
            problems.append(f"{f.name}: bad category {c.get('category')!r} for {c['id']}")
            c["category"] = "other"
        cls[c["id"]] = c
    for a in d.get("attributions", []):
        if a["bug"] not in B:
            problems.append(f"{f.name}: unknown bug id {a['bug']}")
            continue
        if a.get("property") and a["property"] not in P:
            problems.append(f"{f.name}: attribution to unknown property {a['property']} for {a['bug']}")
            a["property"] = None
            a["basis"] = "none"
        attr[a["bug"]] = a
    notes[f.name] = d.get("batch_notes", "")

props = [p for p in P.values() if p["kind"] in ("hegel", "state_machine")]
missing = [p["id"] for p in props if p["id"] not in cls]
print(f"classified {len(cls)} of {len(props)} properties; {len(missing)} missing; {len(problems)} problems", file=sys.stderr)
for m in problems[:30]:
    print("  ", m, file=sys.stderr)

# bug -> properties credited
credit_record: dict[str, set[str]] = defaultdict(set)   # from records (direct, pin origin, mention)
credit_inferred: dict[str, set[str]] = defaultdict(set)  # classifier inference
for b in B.values():
    if b["property"]:
        credit_record[b["id"]].add(b["property"])
    if b["origin_property"]:
        credit_record[b["id"]].add(b["origin_property"])
    for m in b.get("mentioned_by", []):
        credit_record[b["id"]].add(m)
for bid, a in attr.items():
    if a.get("property"):
        (credit_record if a.get("basis") == "explicit" else credit_inferred)[bid].add(a["property"])

for p in props:
    p["bugs_record"] = sorted({bid for bid, ps in credit_record.items() if p["id"] in ps})
    p["bugs_inferred"] = sorted({bid for bid, ps in credit_inferred.items() if p["id"] in ps} - set(p["bugs_record"]))
    c = cls.get(p["id"], {})
    p["category"] = c.get("category", "unclassified")
    p["tags"] = c.get("tags", [])
    p["confidence"] = c.get("confidence", "")
    p["note"] = c.get("note", "")

with (HERE / "classified.jsonl").open("w") as f:
    for p in props:
        slim = {k: p[k] for k in ("id", "target", "lang", "imported", "name", "file", "kind", "category", "tags",
                                  "confidence", "note", "bugs_record", "bugs_inferred", "named_pin")}
        f.write(json.dumps(slim) + "\n")


def table(rows: list[dict], title: str) -> str:
    n = len(rows)
    out = [f"### {title} ({n} properties)", "",
           "| category | properties | share | found a bug (records) | found a bug (records + inferred) | excl. pins: n | excl. pins: found (records) |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for cat in CATS + ["unclassified"]:
        rs = [p for p in rows if p["category"] == cat]
        if not rs:
            continue
        rec = sum(bool(p["bugs_record"]) for p in rs)
        inf = sum(bool(p["bugs_record"] or p["bugs_inferred"]) for p in rs)
        np = [p for p in rs if "pin" not in p["tags"]]
        nprec = sum(bool(p["bugs_record"]) for p in np)
        out.append(f"| {NAMES.get(cat, cat)} | {len(rs)} | {len(rs)/n:.0%} | {rec} ({rec/len(rs):.0%}) | {inf} ({inf/len(rs):.0%}) | {len(np)} | {nprec} ({(nprec/len(np) if np else 0):.0%}) |")
    rec = sum(bool(p["bugs_record"]) for p in rows)
    inf = sum(bool(p["bugs_record"] or p["bugs_inferred"]) for p in rows)
    np = [p for p in rows if "pin" not in p["tags"]]
    nprec = sum(bool(p["bugs_record"]) for p in np)
    out.append(f"| **all** | {n} | 100% | {rec} ({rec/n:.0%}) | {inf} ({inf/n:.0%}) | {len(np)} | {nprec} ({nprec/len(np):.0%}) |")
    return "\n".join(out) + "\n"


print(table(props, "All languages"))
for lang in ("rust", "go", "typescript"):
    print(table([p for p in props if p["lang"] == lang], lang))
print(table([p for p in props if p["lang"] == "rust" and p["imported"]], "rust, imported from the predecessor"))
print(table([p for p in props if p["lang"] == "rust" and not p["imported"]], "rust, written for the zoo"))

# tags
print("### Tags\n")
tc = Counter(t for p in props for t in p["tags"])
for t, n in tc.most_common():
    rs = [p for p in props if t in p["tags"]]
    rec = sum(bool(p["bugs_record"]) for p in rs)
    print(f"- `{t}`: {n} properties, {rec} ({rec/n:.0%}) found a bug (records)")
print()
print("### Confidence\n")
print(Counter(p["confidence"] for p in props))
print()
print("### Bugs attributed\n")
ba = Counter()
for b in B.values():
    if credit_record.get(b["id"]):
        ba["record"] += 1
    elif credit_inferred.get(b["id"]):
        ba["inferred"] += 1
    elif b["id"] in attr:
        ba["classifier: none"] += 1
    else:
        ba["unattributed"] += 1
print(ba)
print()
print("### Batch notes\n")
for k, v in notes.items():
    print(f"- **{k}**: {v}")
