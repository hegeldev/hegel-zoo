# go/gomega

Hegel property tests for [onsi/gomega](https://github.com/onsi/gomega), the matcher library:
the numeric, collection, map, value and document (JSON, YAML, XML) matchers of the `gomega`
package.

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel` needs nothing
beyond the module.

## Oracle

Models of the documented matcher semantics (the doc comments in matchers.go and the Gomega
reference). BeNumerically is checked against exact rational arithmetic (`big.Rat`) on
numbers of every integer and float kind, with the documented default threshold for `~` on
floats. ConsistOf and ContainElements are multiset matching: the model builds the
element/expectation adjacency (each expectation being Equal, BeNil for a nil argument, or a
matcher) and asks for a maximum bipartite matching; HaveExactElements is position-wise;
ContainElement, HaveEach and BeElementOf follow the wrapping-in-Equal rule. HaveKey and
HaveKeyWithValue are judged against the set of outcomes the map order allows, so that an
order-dependent answer is visible. MatchJSON, MatchYAML and MatchXML are given two spellings
of one generated document (whitespace, key order, `\u` escapes, number spellings, flow and
block YAML, attribute order and quoting, CDATA and character references, self-closing tags,
namespace prefixes) or a document with one leaf changed, and must answer equal or not
accordingly. Every matcher runs under a recover, so a panic is a failure rather than a crash.

## Properties

- `TestHegelNumerically`: `BeNumerically` with every comparator, mixed kinds, thresholds.
- `TestHegelCollections`: `ConsistOf`, `ContainElements`, `HaveExactElements`,
  `ContainElement`, `HaveEach`, `BeElementOf` on slices, arrays, maps and typed slices.
- `TestHegelMaps`: `HaveKey`, `HaveKeyWithValue` (plain keys and key matchers), `BeKeyOf`.
- `TestHegelValues`: `Equal`, `BeIdenticalTo`, `BeZero`, `BeNil`, `HaveLen`, `BeEmpty`,
  `HavePrefix`, `HaveSuffix`, `ContainSubstring`, `MatchRegexp` on strings, byte slices and
  Stringers.
- `TestHegelJSON`, `TestHegelYAML`, `TestHegelXML`: the document matchers.

## Bugs

Fourteen, in `bugs.toml`: BeNumerically converts a signed and an unsigned integer to the
actual's kind (1, medium), wraps the int64 difference for `~`/`==` (2), rounds an integer to
float64 when compared with a float (3), and applies a `==` threshold to integers but not to
floats (14); HaveKeyWithValue with a key matcher judges the first accepted key in map order
(4, medium); MatchJSON ignores json.Unmarshal errors (5, medium) and compares numbers as
float64 (6); MatchXML compares namespace prefixes literally (7); MatchYAML reads the first
document of a stream (8); HaveExactElements' message omits index 0 (9); WithTransform and
Satisfy reject a nil actual for a nillable parameter (10); Equal on two `[]byte` uses
bytes.Equal (11); HaveKey/HaveKeyWithValue error or succeed by map order when the key matcher
errors on a key (12); ContainElement(nil), HaveEach(nil) and HaveKeyWithValue(k, nil) error on
a nil element (13).

## Modelled as recorded, not counted

- BeEquivalentTo converts the actual to the expected's type (300 to uint8 is 44, 1.9 to int is
  1, 65 to string is "A"), as documented.
- MatchXML keeps leaf whitespace (`<a>x</a>` and `<a> x </a>` differ) and compares comments;
  MatchYAML distinguishes `1` from `1.0`, reads `yes` as a string (YAML 1.2) and compares
  integers beyond uint64 as float64.
- BeNumerically on a uintptr is a "Failed to compare" error.
- A single slice argument to ConsistOf, ContainElements, HaveExactElements or BeElementOf is
  flattened into its elements (`ConsistOf([]byte("ab"))` means the two bytes); BeElementOf on a
  map is false; HaveEach on an empty collection errors; a matcher that errors inside ConsistOf
  counts as a non-match.
- HaveExistingField through a nil pointer errors; Succeed on a typed nil error pointer is true.
