# typescript/rbush — mourner/rbush (against a brute-force model)

rbush is "a high-performance JavaScript library for 2D spatial indexing of points and rectangles",
an R-tree with bulk loading (OMT) and bulk insertion (STLT), ~4M weekly downloads (Leaflet,
Mapbox, OpenLayers, Turf). The patch checks it against brute force over the multiset of inserted
items and pins 3 bugs.

## How it is built

No build: `index.js` is a plain ES module. Its one runtime dependency, `quickselect`, is installed
into `node_modules` without touching `package-lock.json` (`--no-save --no-package-lock --omit=dev`);
Hegel goes under `.hegel/`.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared harness.
The oracle is the multiset of item *references* the tree should hold, and the README's contract
"items that the given bounding box intersects" read as closed intervals (the code's `intersects`).

| Property | What it checks |
|---|---|
| `TestHegelSearchLikeBruteForce` | random `maxEntries` (default, 4–40, and the clamped values 0–3, negative, `Infinity`, a numeric string) and data format (default objects; a subclass overriding `toBBox`/`compareMinX`/`compareMinY` on `{minLng, minLat, …}`; the same overrides assigned on an instance over `[x0, y0, x1, y1, id]` arrays), then 1–30 steps of `insert` (one or a run), `load` (0–60 items, below and above the minimum fill), `remove` by reference (present, a duplicate reference, or a foreign copy), `remove(copy, equals)` with a JSON copy, `clear`, `toJSON` → `JSON` → `fromJSON` into a fresh tree, and the documented no-ops (`insert`/`remove` of `undefined`, `load` of nothing). After every step: `all()` is the model, three random queries (item boxes, points inside items, the whole plane, inverted boxes, random clusters) `search` exactly the brute-force set and `collides` agrees, and the tree's shape is checked — balanced, every node's bbox exactly the bbox of its children, no node over `maxEntries`, no empty non-root node, every stored item in some leaf exactly once |
| `TestHegelLoadLikeInserts` | `load(data)` and inserting the same items one by one hold the same multiset and answer the same queries; a second `load` into a non-empty tree (STLT) keeps everything; up to `maxEntries` items bulk-load into a single leaf, more need a second level |
| `TestHegelApiSurface` | an empty tree's `all`/`search`/`collides`/`toJSON`; the chainable API; the default `toBBox`/`compareMinX`/`compareMinY`; `fromJSON(toJSON())` with the same `maxEntries` answers like the original and adopts the data object |

Coordinates mix small integers (so items coincide and overlap), decimals, 1e15-scale values,
float32 values, `±Infinity` (upstream's tests call these "empty bboxes"), `-0` and the safe-integer
limits; points, horizontal and vertical lines and rectangles. `ZOO_COLLECT=1` turns mismatches
into `# COLLECT` counts instead of failures; `HEGEL_TEST_CASES` (default 100) widens the sweep.
Known bugs are skipped through the `Known` switches at the top of the file (generator-level: no
fractional or NaN `maxEntries`, no NaN coordinates, no node with more than a few hundred children).

## Bugs

3 open, all pinned (see `bugs.toml`), all in the "unusual but accepted input" class — the core
index answered every random query correctly in 1000-case sweeps:

- `all()` (and `search()` through its containment shortcut) spreads a node's children into
  `push()`, so a node of ~150000 or more children throws `RangeError: Maximum call stack size
  exceeded`, while a plain `search()` of the same leaf works (1).
- `maxEntries` is not validated: `new RBush(NaN)` makes `load()` throw a TypeError from inside the
  bulk build; `new RBush(4.5)` bulk-loads non-leaf nodes of height 1, after which `insert()` or
  `search()` throws (2).
- One item with a NaN or missing coordinate (a misspelt `minx`) turns every ancestor bbox NaN:
  `search`/`collides` find nothing at all, `remove` finds nothing (the bad item included), `all()`
  still lists everything (3).

## Accepted differences and notes (not counted as bugs)

- `toJSON()` returns the live root node (mutating the export mutates the tree; `fromJSON` adopts
  the object, so two trees built from one export share nodes). `±Infinity` does not survive
  `JSON.stringify` (it becomes `null`): an exported *empty* tree has a `±Infinity` bbox, and after
  import its root bbox is `null`s — every query still answers correctly since the bbox is only ever
  widened — and items with infinite coordinates are not found after a JSON round trip. The tests
  round-trip only non-empty, finite trees.
- `maxEntries` below 4 (0, negative, 1–3) is clamped to 4; a numeric string works through
  `Math.max`; `Infinity` gives a single leaf.
- The bulk-load height is one more than needed when N is a power of the node size and
  `Math.log(N) / Math.log(M)` rounds up (`new RBush(5).load(125 items)` has height 4 with a
  single-child root; 6/216 and 7/343 likewise); performance only, not checked.
- Inverted query boxes (`minX > maxX`) are answered by the same closed-interval formula as brute
  force (usually nothing); inverted *items* are not generated — for them `search`'s containment
  shortcut and the formula disagree, which is garbage in.
- `remove(copy, equals)` finds the copy only through the copy's bbox (documented: a copy "of the
  object you need removed"); the tests copy through JSON, or structurally when the bbox is infinite.

## Not tested

The browser bundle (`rbush.js`, `rbush.min.js`, built with rollup), the `viz/` demos, `bench/`,
sibling packages (`rbush-knn`, `kdbush`, `flatbush`).

## History

- 2026-09-17: created at e597127 (v4.0.1), 3 properties, 3 bugs.
