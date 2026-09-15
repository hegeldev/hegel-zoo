#!/usr/bin/env python3
"""Group targets into classification batches (whole targets per batch) and write
batches/batch-NN.json, each: [{target, readme_head, properties: [...], pins: [...], bugs: [...]}]."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BATCH_CHARS = 260_000  # roughly 65k tokens of input per batch

P = [json.loads(l) for l in (HERE / "properties.jsonl").open()]
B = [json.loads(l) for l in (HERE / "bugs.jsonl").open()]

by_target: dict[str, dict] = {}
for p in P:
    t = by_target.setdefault(p["target"], {"target": p["target"], "properties": [], "pins": [], "bugs": []})
    entry = {
        "id": p["id"], "name": p["name"], "file": p["file"], "comment": p["comment"][:1200],
        "readme": p["readme"][:900], "body": "\n".join(p["body"][:45]),
        "bugs_direct": p["bugs"] + p.get("bugs_via_pin", []) + p.get("bugs_via_mention", []),
    }
    if p["kind"] == "hegel":
        entry["stateful_hint"] = p["stateful"]
        t["properties"].append(entry)
    elif p["kind"] == "state_machine":
        entry["drivers"] = p.get("drivers", [])
        t["properties"].append({**entry, "state_machine_struct": True})
    else:
        if p["bugs"]:  # only pins that carry a bug need attribution
            entry["body"] = "\n".join(p["body"][:20])
            t["pins"].append(entry)
for b in B:
    if b["target"] in by_target:
        by_target[b["target"]]["bugs"].append({k: b[k] for k in ("id", "title", "kind", "severity", "status", "test", "property", "pin", "origin_property", "mentioned_by")})

for t in by_target.values():
    readme = ROOT / "targets" / t["target"] / "README.md"
    t["readme_head"] = readme.read_text(errors="replace")[:2500] if readme.is_file() else ""

out = HERE / "batches"
out.mkdir(exist_ok=True)
for f in out.glob("batch-*.json"):
    f.unlink()
batches: list[list[dict]] = [[]]
size = 0
for t in sorted(by_target.values(), key=lambda t: t["target"]):
    s = len(json.dumps(t))
    if size + s > BATCH_CHARS and batches[-1]:
        batches.append([])
        size = 0
    batches[-1].append(t)
    size += s
for i, b in enumerate(batches, 1):
    (out / f"batch-{i:02d}.json").write_text(json.dumps(b, indent=0))
    print(f"batch-{i:02d}: {len(b)} targets, {sum(len(t['properties']) for t in b)} properties, "
          f"{sum(len(t['pins']) for t in b)} pins with bugs, {sum(len(json.dumps(t)) for t in b)//1000}k chars")
print(len(batches), "batches")
