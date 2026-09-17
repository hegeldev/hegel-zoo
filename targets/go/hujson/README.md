# hujson

[tailscale/hujson](https://github.com/tailscale/hujson) is Tailscale's "human JSON" package:
a parser and packer for JWCC (JSON with commas and comments — RFC 8259 plus `//` and `/* */`
comments and trailing commas), an exact syntax tree (`Value`, `Object`, `Array`, `Literal`,
`Extra`), `Standardize`/`Minimize` to standard JSON, a `gofmt`-like `Format`, RFC 6901
`Find` and RFC 6902 `Patch`, used for Tailscale's ACL policy files. About 3 900 lines,
BSD-3-Clause, no tags (the pin is master `b80ff77`, 2026-07-27); README and LICENSE are the
only project documents and say nothing about AI-written code.

## Build

`go test -count=1 -run TestHegel -v .` in the module root (the repository's `go.work` is
removed by the patch so the module builds alone). The patch adds `hegel_test.go` (the model
and the properties) and `hegel_pins_test.go` (one plain test per bug) and requires
`hegel.dev/go/hegel v0.6.33` in go.mod.

## Oracles

- **A model of the JWCC grammar** written in the test: a parser that builds the same syntax
  tree hujson does — values, the whitespace-and-comment extras around each of them, trailing
  commas, byte offsets — following the package's grammar comment and RFC 8259 for literals
  (with the two encoding/json v1 relaxations hujson inherits: invalid UTF-8 and lone
  surrogate escapes in strings). From the tree follow the exact `Pack`, `Standardize`
  (comments blanked byte for byte, trailing commas replaced by a space) and `Minimize`
  outputs, the `All` order, `IsStandard`, and the extra grammar for `Extra.IsValid`.
- **encoding/json**: the standardized text is valid, decodes to the model's value, and
  `json.Compact` of it is `Minimize`.
- **The documented Format contracts**: idempotence, standard input stays standard, the value
  and the comments are preserved (in order; block comments re-indented), every object or
  array is either inlined or fully expanded, trailing commas only in expanded non-standard
  output, one trailing newline, tabs for indentation, no trailing whitespace, at most one
  blank line, no carriage returns.
- **RFC 6901 and RFC 6902**: `Find` and `Patch` against an ordered document model (first
  match on duplicate names, as hujson documents), with random valid patches drawn from the
  current document and deliberate misses and malformed operations.
- **The documented Literal constructors and accessors** (`String` per RFC 8785 with invalid
  UTF-8 mangled, `Int`/`Uint`/`Float` including the NaN/Infinity strings, `Bool`, `Kind`,
  `IsValid`).

## Properties

| Property | Checks |
|---|---|
| ParseBuildsTheExactTree | generated documents: the tree (kinds, literals, extras, trailing commas, offsets) equals the model's; `Pack` and `String` restore the input; `UpdateOffsets` is a no-op after `Parse`; `IsStandard`; `All` and `Range` visit in depth-first order and `Range` stops when told |
| GrammarFollowsJWCC | random and mutated bytes: `Parse` accepts exactly what the model accepts; errors are `hujson: line L, column C: …` with a position inside the input; the convenience functions return the input as is with the same error; accepted inputs get the full tree, Standardize, Minimize and Format checks |
| ExtraIsValidFollowsTheGrammar | `Extra.IsValid` on generated, mutated and random whitespace-and-comment bytes |
| StandardizeKeepsOffsetsAndMinimizeIsCompact | `Standardize` is byte-exactly the documented text (same length, comments blanked, trailing commas → space), valid JSON, the model's value; the in-place method packs the same, is standard and leaves the offsets where they were; `Minimize` = model compact = `json.Compact` of the standard text; offsets correct after both |
| FormatIsIdempotentAndFaithful | the contracts above, plus the output parses (library and model), `Value.Format` packs the same and leaves correct offsets |
| FindFollowsRFC6901 | every pointer to a node resolves to it (first duplicate wins); mutated pointers (missing segments, `-`, out-of-range and malformed indices, unescaped `~`/`/`, no leading slash) resolve exactly as the RFC says |
| PatchFollowsRFC6902 | 1–4 operations drawn from the document (add/remove/replace/move/copy/test, values with comments inside, shuffled members, malformed encodings): failure exactly when the model fails; otherwise the result minimizes to the model's document, packs to parsable HuJSON, formats to the same value, and the original is untouched through `Clone` |
| LiteralConstructorsRoundTrip | `String`/`Int`/`Uint`/`Float`/`Bool` produce valid literals of the right kind that read back; `IsValid`, `Kind` and the accessors on drawn and hand-picked literals (valid or not) match the documentation |
| CloneIsDeep | a clone packs the same with the same offsets; formatting, minimizing, standardizing, patching or scribbling on the clone leaves the original; scribbling on the parsed input leaves the clone |

`Known` switches gate the eight recorded bugs (the generators avoid the shapes; the
convenience functions are called on copies of the input). With them on, the nine properties
run clean at 500 cases in about a second (`HUJSON_COLLECT=1` records mismatches instead of
failing and prints them shortest-first; `HEGEL_VERBOSE=1` turns on the engine's log).

## Bugs (8; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| hujson/1 | Patch `add` with an array index greater than the length appends instead of failing (RFC 6902 §4.1) | medium |
| hujson/2 | `Find` and `Patch` accept an array index with leading zeros: `/01` is element 1 (RFC 6901 §4) | low |
| hujson/3 | Patch refuses `move` onto the same location and `copy` from the root; the RFC forbids only moving into a proper child | low |
| hujson/4 | Patch refuses `replace` at the root while `add` at the root works | low |
| hujson/5 | `Literal.IsValid` accepts objects and arrays; the documentation says null, boolean, string or number | low |
| hujson/6 | `Standardize` and `Format` overwrite the caller's input buffer (comments blanked, tabs written) through Parse's aliasing, leaving it neither input nor output | medium |
| hujson/7 | `Clone` drops a trailing comma that directly follows the last value (`[1,]` → `[1]`): `copyBytes` turns the empty non-nil marker into nil | low |
| hujson/8 | A Patch `test` against a JSON null never succeeds: `equalValue` takes the decoded nil for a decode failure | medium |

How they were found: hujson/1–5 while writing the Find, Patch and Literal properties against
the RFCs and the documentation (hand probes confirmed each before the properties ran);
hujson/6 when the Format property's documents changed between two checks sharing a buffer,
hujson/7 by the Clone property's `Pack` comparison at 200 cases, and hujson/8 by the Patch
property at 500 cases (an `add` made the document `null`, a following `test` checked it).
The collect rounds otherwise found only harness mistakes: line separators drawn into line
comments, `1e400` (which encoding/json refuses to decode), a byte-exact comparison after
Format re-escapes strings.

## Accepted differences (not bugs)

- Strings may hold invalid UTF-8 and lone surrogate escapes (RFC 8259 §8.1 requires UTF-8):
  the source notes encoding/json v1's non-compliance and inherits it. Such names are matched
  bytewise by `Find`'s fast path and as U+FFFD by its slow path; the generators keep object
  names valid UTF-8.
- U+2028/U+2029 are rejected in line comments (they are ambiguous line terminators) but
  accepted in block comments.
- `Format` re-escapes strings (`"A"` → `"A"`) and turns invalid UTF-8 in them into
  U+FFFD, and joins a comment before a comma to the closing bracket when it drops the comma;
  the JSON value and the comment sequence are what the properties compare.
- A comment between a name and its colon, or between a value and its comma, does not by
  itself expand the object (the documentation names the positions after `{`, `[`, `,` and
  before `}`, `]`).
- `remove` at the root is refused; RFC 6902 leaves what would remain undefined.
- Patch `test` equality is encoding/json's: numbers compare as float64, duplicate names keep
  the last value.

## Not tested

The `hujsonfmt` command, comment placement after `Patch` (the source calls it a matter of
taste and documents which comments travel with a member), `alignObjectValues` column
alignment beyond the whitespace discipline, and error message wording beyond the
`line, column` prefix.
