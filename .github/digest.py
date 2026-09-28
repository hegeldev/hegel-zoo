#!/usr/bin/env python3
"""Digest of a `full run`: what failed, compactly, from the shards' saved output.

Each shard job saves its `tools/zoo test` stdout (out.txt), stderr (err.txt), the shard's
target list (shard) and the exit code (rc) as an artifact named zoo-<lang>-<job index>. This
script, run by the last job, reads them all and prints, for every shard that failed or left
no artifact, the BAD verdict lines with their FAIL/PASS?/MISSING/NOTRUN lines and the failure
excerpts, and for a shard that failed without a verdict for some target (a setup or build
failure) the tail of its output, and ends with a summary (the verdict and FAIL lines of every
BAD target) so that even a cut digest's tail names them all. Sizes are measured as the run log
stores them: every line carries a ~66-character prefix (job name, step name, timestamp) there,
so a line costs LINE_COST on top of its characters, and the whole digest stays under DIGEST_CAP
so measured, which keeps it inside the 200,000 characters of the run's failed-steps log that
its reader keeps (the 2026-09-28 run lost its first 50k this way: 1,643 short lines). Exit
status 1 when any shard failed.

Usage: digest.py <artifacts dir>   with SHARDS_<LANG> env vars holding the JSON shard lists.
"""

import json
import os
import re
import sys
from pathlib import Path

LANGS = ["rust", "go", "typescript", "java"]
LINE_COST = 70
DIGEST_CAP = 170_000  # as measured by cost()
BLOCK_CAP = 12_000
TAIL_CAP = 5_000

VERDICT = re.compile(r"^(OK |BAD) (\S+): ")


def cost(text: str) -> int:
    """The text's size in the run log: its characters plus a prefix per line."""
    return len(text) + LINE_COST * (text.count("\n") + 1)


def cut(text: str, cap: int, where: str = "middle") -> str:
    """Cut text so that cost(result) <= cap, keeping the head and tail (or the tail alone),
    on line boundaries."""
    if cost(text) <= cap:
        return text
    lines = text.splitlines()
    total = len(lines)
    if where == "tail":
        kept, size = [], 200
        for l in reversed(lines):
            if size + cost(l) > cap:
                break
            kept.append(l)
            size += cost(l)
        kept.reverse()
        return "[… " + str(total - len(kept)) + " lines cut]\n" + "\n".join(kept)
    head, tail, size = [], [], 200
    i, j = 0, total - 1
    while i <= j:
        if len(head) <= len(tail):
            if size + cost(lines[i]) > cap:
                break
            head.append(lines[i]); size += cost(lines[i]); i += 1
        else:
            if size + cost(lines[j]) > cap:
                break
            tail.append(lines[j]); size += cost(lines[j]); j -= 1
    tail.reverse()
    return "\n".join(head) + "\n[… " + str(j - i + 1) + " lines cut]\n" + "\n".join(tail)


def blocks(out: str) -> tuple[str, list[tuple[str, str, str]], str]:
    """(preamble, [(flag, target, block text)], trailing text after the last verdict block).
    A block is a verdict line and the indented/excerpt lines up to the next verdict line."""
    lines = out.splitlines()
    starts = [i for i, l in enumerate(lines) if VERDICT.match(l)]
    if not starts:
        return out, [], ""
    pre = "\n".join(lines[: starts[0]])
    result = []
    for k, i in enumerate(starts):
        j = starts[k + 1] if k + 1 < len(starts) else len(lines)
        m = VERDICT.match(lines[i])
        result.append((m.group(1).strip(), m.group(2), "\n".join(lines[i:j])))
    # the last block may end with a build log tail of the *next* target ("no test results
    # parsed" prints the run's tail on stdout before zoo's log line on stderr): split it off
    # at the first non-indented, non-excerpt line after the block's own lines
    flag, target, last = result[-1]
    last_lines = last.splitlines()
    end = 1
    while end < len(last_lines) and (
        last_lines[end].startswith("    ") or last_lines[end].startswith("---- ")
        or last_lines[end].startswith("[…]") or last_lines[end].startswith("… (")
        or in_excerpt(last_lines[:end])
    ):
        end += 1
    result[-1] = (flag, target, "\n".join(last_lines[:end]))
    return pre, result, "\n".join(last_lines[end:])


def in_excerpt(lines: list[str]) -> bool:
    """Whether the lines so far are inside a `---- name ----` excerpt (they run to the next
    verdict, so only a heuristic: an excerpt header seen and no verdict since)."""
    return any(l.startswith("---- ") and l.endswith(" ----") for l in lines)


def main() -> int:
    root = Path(sys.argv[1])
    shards = {}
    for lang in LANGS:
        raw = os.environ.get(f"SHARDS_{lang.upper()}", "[]") or "[]"
        try:
            shards[lang] = json.loads(raw)
        except json.JSONDecodeError:
            shards[lang] = []
    failed = []  # (title, text)
    ok_shards = 0
    bad_targets = []
    summary = []  # every BAD verdict line with its FAIL/PASS?/MISSING/NOTRUN lines, for the trailer
    for lang in LANGS:
        for idx, shard in enumerate(shards[lang]):
            d = root / f"zoo-{lang}-{idx}"
            title = f"{lang} shard {idx} ({shard})"
            if not d.is_dir():
                failed.append((title, "no output saved: the job failed before its test step "
                               "(checkout, toolchain, system packages), or was cancelled"))
                continue
            rc = (d / "rc").read_text().strip() if (d / "rc").exists() else "?"
            out = (d / "out.txt").read_text(errors="replace") if (d / "out.txt").exists() else ""
            err = (d / "err.txt").read_text(errors="replace") if (d / "err.txt").exists() else ""
            if rc == "0":
                ok_shards += 1
                continue
            pre, bs, trailing = blocks(out)
            seen = {t for _, t, _ in bs}
            parts = [f"exit status {rc}"]
            for flag, target, text in bs:
                if flag == "BAD":
                    bad_targets.append(target)
                    parts.append(cut(text, BLOCK_CAP))
                    summary.extend(l for l in text.splitlines()
                                   if VERDICT.match(l) or re.match(r"^\s+(FAIL|PASS\?|MISSING|NOTRUN)\s", l))
            missing = [t for t in shard.split() if t not in seen]
            if missing:
                parts.append("no verdict for: " + " ".join(missing) + " (setup or build failure, or the run stopped)")
                tail = trailing if trailing.strip() else pre
                if tail.strip():
                    parts.append("last output:\n" + cut(tail, TAIL_CAP, "tail"))
                zoo_lines = [l for l in err.splitlines() if l.startswith("zoo:")]
                if zoo_lines:
                    parts.append("zoo's last log lines:\n" + "\n".join(zoo_lines[-8:]))
            elif not any(f == "BAD" for f, _, _ in bs):
                parts.append("every target has an OK verdict, yet the step failed; stderr tail:\n" + cut(err, TAIL_CAP, "tail"))
            failed.append((title, "\n".join(parts)))
    total = sum(len(s) for s in shards.values())
    head = [f"full run digest: {len(failed)} of {total} shards failed, {ok_shards} passed."]
    if bad_targets:
        head.append("BAD targets: " + " ".join(bad_targets))
    if not failed:
        print("\n".join(head))
        return 0
    trailer = "\n==== summary ====\n" + "\n".join(head) + "\n" + "\n".join(summary)
    body = []
    budget = DIGEST_CAP - cost("\n".join(head)) - cost(trailer) - 200
    per = max(2000, budget // len(failed))
    for title, text in failed:
        body.append(f"\n==== {title} ====\n{cut(text, per)}")
    digest = "\n".join(head) + "\n" + "\n".join(body)
    if cost(digest) > DIGEST_CAP - cost(trailer):
        digest = cut(digest, DIGEST_CAP - cost(trailer), "tail")
    print(digest + "\n" + trailer)
    return 1


if __name__ == "__main__":
    sys.exit(main())
