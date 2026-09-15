# Classification task (for one batch)

You are classifying property-based tests from the Hegel zoo. Read, in this order:

1. The rubric: `/Users/drmaciver/.local/andon/projects/mw3nhu/notes/taxonomy.md` (categories, tags, tie-breaks).
2. Your batch file `batches/batch-NN.json` (path given in your prompt). It is a JSON list of
   targets. Each target has `target`, `readme_head` (start of the target's README, for
   context), `properties` (the Hegel properties to classify: `id`, `name`, `comment` = doc
   comment above the test, `readme` = the README sentence about it, `body` = the first ~45
   lines of the test, `bugs_direct` = bug ids already linked to it), `pins` (example-based
   tests that pin a bug: `id`, `name`, `comment`, `body`, `bugs_direct`) and `bugs` (bug
   records of the target: `id`, `title`, `kind`, `test`, and any attribution already known:
   `property`, `origin_property`, `mentioned_by`).

Do all of it yourself; do not spawn subagents. Read the batch file in chunks with the Read
tool if it is long (it is JSON on few lines; use offset/limit or `python3 -c` to print
targets one at a time). Do NOT modify anything under `targets/`.

## Output

Write `out/batch-NN.json` (same NN, directory `studies/property-taxonomy/out/`, create it if
needed) as one JSON object:

```json
{
  "properties": [
    {"id": "<property id exactly as given>", "category": "<one rubric key>",
     "tags": ["oracle:external", "stateful", "pin", "doc-contract", "interesting"],
     "confidence": "high|medium|low", "note": "<short; required if category is other or tag interesting>"}
  ],
  "attributions": [
    {"bug": "<bug id>", "property": "<property id or null>", "basis": "explicit|inferred|none",
     "note": "<one clause: why>"}
  ],
  "batch_notes": "<anything systematic you noticed: recurring shapes the rubric misses, targets whose tests are unusual, quality problems>"
}
```

Rules:

- Every property in the batch appears exactly once in `properties`, with its `id` copied
  verbatim. Entries with `state_machine_struct: true` are `#[hegel::state_machine]` structs;
  classify them `stateful-model` (they are the machine a driver test runs) unless clearly
  something else.
- `category` is exactly one rubric key: roundtrip, external-oracle, model-oracle,
  stateful-model, internal-consistency, algebraic-law, spec-postcondition, rejection,
  robustness, concurrency, other. Decide by the *main assertion*, following the rubric's
  tie-breaks. Read the body when the doc is thin or missing.
- `tags` may be empty. Tag `pin` when the property is a narrowed pin of one known bug (names
  like `known_bug_*`, docs saying "KNOWN FAILURE"/"pins", a body that fixes most inputs to
  reproduce one failure). Tag `interesting` for properties that are unusual or creative —
  an oracle nobody would expect, a clever metamorphic relation, a property about something
  other than functional behaviour (performance bounds, allocation, error-message quality,
  API ergonomics) — or that fit no category well; explain in `note`. Aim for the genuinely
  notable few per batch, not a quota.
- `attributions`: one entry per bug in the target whose `property` is null (i.e. its record
  names a pin/example test, or no test). Name the Hegel property in the same target that most
  plausibly exposed it: `basis: explicit` when the pin's comment/body, the bug title/notes or
  the README says so, or `mentioned_by`/`origin_property` already gives it; `inferred` when
  you judge it from the subject (the pin exercises the textinput's placeholder; the only
  property about the placeholder is X); `none` with `property: null` when nothing in the
  batch plausibly produced it (e.g. the bug looks found by reading code or by a deterministic
  example, or the relevant property is not there). Be honest: `inferred` should mean a
  specific property clearly covers the failing behaviour, not a guess.
- Do not invent ids. Do not skip properties. Valid JSON only (no trailing commas, no comments).
- Finish by printing a two-line summary: counts per category, and how many attributions
  were explicit/inferred/none.
