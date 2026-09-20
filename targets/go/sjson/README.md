# sjson

[sjson](https://github.com/tidwall/sjson) is the Go "set a value in a JSON document by path"
library that pairs with gjson (2.7k stars; used wherever gjson is, from tile38 and jj to Caddy
plugins): `Set`, `SetRaw`, `Delete` and their `Bytes`/`Options` variants splice a value into the
document text without building a tree, locating existing values with gjson and building the
missing containers themselves. Its path syntax is gjson's dot syntax plus `-1` (append), a
leading `:` (force a string key) and `\` escapes. The pin is the default branch at `3a21ce7`
(2026-05-19, five commits past v1.2.5).

The repository has README.md and LICENSE (MIT) only; nothing restricts AI-written tests, and the
zoo keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -v .` in the module root. The patch adds `hegel_test.go` (properties) and
`hegel_pins_test.go` (one plain test per bug) and requires `hegel.dev/go/hegel v0.6.33` in
go.mod (the `go` directive moves from 1.14 to 1.26.0 for it; sjson's own dependency on gjson
stays at its pinned v1.14.2). No external oracle process: everything runs in-process.

## Oracles

- **An ordered JSON tree with a model of the path semantics** — every operation is generated
  from a tree (keys drawn from an alphabet full of path metacharacters, numbers in every textual
  form, escapes chosen at random, random whitespace) together with the result it must produce:
  an existing key or index is replaced, a new key appended to the object, an index past the end
  padded with `null`, `-1` appended, a chain of new components builds arrays for numeric parts
  and objects otherwise, a scalar on the way is replaced by the container the next component asks
  for, a non-numeric key on an array is an error, and Delete of anything missing is a no-op that
  returns the input unchanged.
- **encoding/json** — validity of every output, the tree of the values sjson marshals (the
  fallback for unknown types, the U+FFFD replacement for invalid UTF-8), and an ordered token
  decoder that reads sjson's output back into the tree; numbers compare as exact rationals so
  that `1e21` and `1000000000000000000000` agree.
- **gjson** (sjson's own locator) — only to find the byte range of an existing value, so the
  bytes around a replacement can be checked untouched.

## Method

| Property | Checks |
|---|---|
| SetFollowsTheModel | `Set`/`SetBytes`/`SetRaw`/`SetRawBytes`, with `Optimistic` and `ReplaceInPlace`, give the modelled tree (or the modelled error, with the input returned); a replacement keeps every byte around the old value and writes a raw value verbatim |
| DeleteFollowsTheModel | the four `Delete` variants remove the member (including `-1`, the last element) or return the input unchanged when nothing is at the path |
| OptimisticAndInPlaceAgreeWithPlain | `SetOptions{Optimistic}` and `SetBytesOptions{Optimistic, ReplaceInPlace}` on a copy return exactly `Set`'s bytes; likewise the Delete variants |
| ComplexPathsSetEveryMatch | `arr.#.key` sets the key in every element that has it, a wildcard component sets the first key in document order that matches (a rune-based glob model), no match leaves the document as it was, and Delete refuses a complex path with the input unchanged |
| SetThenDeleteRestoresTheDocument | Set of a new key (or an append) then Delete of it gives the tree back; `SetRaw` of an existing value's own raw text is the identity on the bytes |
| NothingPanicsOnArbitraryInput | random bytes, corrupted documents, random paths (digit runs capped, since an index asks for that many nulls) and random values through every entry point; a valid document with a nil error gives valid JSON |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (non-finite floats, strings needing escapes under `ReplaceInPlace`, empty components,
forced keys that hit an array element, `-1` under a scalar, unescaped leading brackets, nested
`#` paths, escaped digits in an index, Delete of a key starting with a quote, `-1` under an
object with a `#` member). With everything gated the properties run clean;
`ZOO_COLLECT=1` prints class counts and the first 25 mismatches instead of failing.

## Accepted differences (not bugs)

- sjson does not validate: on an invalid document the result is whatever the splice gives, and
  the robustness property only asks that nothing panics.
- A complex path with no match, or one gjson answers without a position (`#`, `a|@reverse`,
  modifiers, multipaths), returns the input unchanged with a nil error; the README only promises
  that invalid paths *may* return an error.
- `[]byte` values are written as strings, not base64 as encoding/json would; `float32` values are
  written with the exact decimal of their float64 widening (`0.10000000149011612` for
  `float32(0.1)`); `-0.0` is written `-0`. All read back as the same values.
- Whitespace: a replacement keeps the document's whitespace, but an array that has to be padded
  is rebuilt compact, and an empty document's leading whitespace is dropped.
- Keys with leading zeros (`01`) are indices for sjson and gjson alike.

## Bugs found

Eleven, recorded in `bugs.toml` with a pin test each: a huge index wraps around (a small index is
written, or 2^63 nulls are requested and the process dies: **sjson/1**), NaN and the infinities
written as invalid JSON (sjson/2), `ReplaceInPlace` silently skipping a string that needs escapes
(sjson/3), an empty component that is index 0 or the key "" or an append depending on what exists
(sjson/4), a forced key that hits an array element (sjson/5), `-1` under a scalar making an
object (sjson/6), keys starting with `[`, `{` or `!`-and-a-literal never found and duplicated
(sjson/7), a path
with two `#` segments overwriting the front of the document (**sjson/8**), an index with an
escaped digit appending instead of replacing (sjson/9), Delete of a key that starts with a
quote cutting the members before it or leaving the key without a value (**sjson/10**), and
Delete of `-1` on an object taking a member named `#` for the array length (sjson/11). All found
on 2026-09-20 (turns 325-327) from the model properties and from reading the splice code while
writing them.

## History

- 2026-09-20 (turns 325-327): target created at `3a21ce7`; 11 bugs.
