#!/usr/bin/env python3
"""Build batches/batch-NN.json (NN given) containing every property not yet classified by any
out/batch-*.json, in the same shape make_batches.py produces, so a further classifier agent
can process the stragglers (e.g. closure-style Rust properties recognised after the first run)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
nn = sys.argv[1]

P = [json.loads(l) for l in (HERE / "properties.jsonl").open()]
B = [json.loads(l) for l in (HERE / "bugs.jsonl").open()]
done: set[str] = set()
for f in (HERE / "out").glob("batch-*.json"):
    for c in json.loads(f.read_text()).get("properties", []):
        done.add(c["id"])

todo = [p for p in P if p["kind"] in ("hegel", "state_machine") and p["id"] not in done]
targets = sorted({p["target"] for p in todo})
out = []
for t in targets:
    entry = {"target": t, "properties": [], "pins": [], "bugs": []}
    for p in P:
        if p["target"] != t:
            continue
        e = {"id": p["id"], "name": p["name"], "file": p["file"], "comment": p["comment"][:1200],
             "readme": p["readme"][:900], "body": "\n".join(p["body"][:45]),
             "bugs_direct": p["bugs"] + p.get("bugs_via_pin", []) + p.get("bugs_via_mention", [])}
        if p["id"] in {q["id"] for q in todo}:
            e["stateful_hint"] = p["stateful"]
            entry["properties"].append(e)
        elif p["kind"] in ("pin", "plain") and p["bugs"]:
            e["body"] = "\n".join(p["body"][:20])
            entry["pins"].append(e)
    for b in B:
        if b["target"] == t:
            entry["bugs"].append({k: b[k] for k in ("id", "title", "kind", "severity", "status", "test", "property", "pin", "origin_property", "mentioned_by")})
    readme = ROOT / "targets" / t / "README.md"
    entry["readme_head"] = readme.read_text(errors="replace")[:2500] if readme.is_file() else ""
    out.append(entry)
(HERE / "batches" / f"batch-{nn}.json").write_text(json.dumps(out, indent=0))
print(f"batch-{nn}: {len(out)} targets, {len(todo)} properties:", [(t, sum(1 for p in todo if p['target'] == t)) for t in targets])
