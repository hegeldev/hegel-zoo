# validator

[go-playground/validator](https://github.com/go-playground/validator) validates structs and
single values from struct tags (about 20,000 stars; the validation layer of Gin, Echo and most
Go web stacks): some 200 baked-in tags (comparisons, cross-field comparisons, the conditional
`required_*`/`excluded_*` family, string formats from `email` to `ulid`), tag parsing with `,`
chains, `|` groups and `0x2C`/`0x7C` escapes, a traversal over nested structs, pointers,
slices and maps (`dive`, `keys`/`endkeys`, `omitempty`, `omitnil`, `omitzero`), namespaced
errors, partial validation and translations. The pin is `6a9b666` (2026-09-20, the tag
`v10.30.5`).

The repository has LICENSE (MIT), a CLAUDE.md of Claude Code guidance for contributors and a
`.github/CONTRIBUTING.md` whose "AI Agents" section welcomes AI-assisted contributions provided
they are attributed (a `Co-Authored-By` trailer, a statement in pull requests and issues);
nothing is forbidden. The zoo keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds `hegel_test.go`
(harness, the `Known` switches, comparisons, cross-field, conditional requirements, unique),
`hegel_formats_test.go` (string formats, substring and set tags), `hegel_traversal_test.go`
(the struct model) and `hegel_pins_test.go` (one plain test per bug), all in the external
package `validator_test`, and requires `hegel.dev/go/hegel v0.6.33` in go.mod (no other
dependency; `time/tzdata` is imported so the `timezone` cases do not depend on the host).

## Oracles

- **The documented semantics of each tag** (doc.go, the README table), restated as small models:
  `len`/`min`/`max`/`eq`/`ne`/`gt`/`gte`/`lt`/`lte` count characters of strings, items of
  slices, arrays and maps and compare numbers and durations; `eqfield`/`nefield`/`gtfield`/...
  compare two fields of one kind (numbers, time.Time; strings and slices for eq/ne) and fail
  (`nefield` passes) across kinds; the twelve `required_*`/`excluded_*` tags follow their
  documented conditions over a string, int, bool, pointer or slice "other" field; `unique`
  over slices of values, pointers and structs with a field parameter and over map values.
- **Independent constructions for the string formats**: values built valid, or mutated
  invalid, by code that does not share the validator's regular expressions — `netip` for
  addresses and prefixes, `net.HardwareAddr` for MACs, `net/url` for URLs, `encoding/base64`
  and `encoding/json`, `time.Format` for `datetime`, check-digit arithmetic for ISBN-10/13,
  ISSN, Luhn and credit cards, `unicode` tables for the alpha/numeric/case classes, generated
  grammars for e-mail, hostnames, FQDNs, UUIDs, ULIDs, semver, JWT, SSN, CVE, EIN, E.164 and
  the colour functions.
- **The `strings` package** for `contains`/`excludes`/`startswith`/... and the `oneof` family,
  with parameters written through the `0x2C`/`0x7C` escapes and single quotes.
- **A model of the traversal**: a fixed `Doc` type (required and min on a string, `dive` over a
  slice and a map with `keys`/`endkeys`, a nested struct, an `omitempty` pointer, a `required`
  pointer, a slice of structs, an `alpha|numeric` group, `max` before `dive`, a skipped field)
  whose expected `(namespace, tag)` set is computed by hand from the documented rules.

## Method

| Property | Checks |
|---|---|
| ComparisonsFollowTheModel | chains of 1-3 comparison tags (some as `a\|b` groups) on strings, ints, uints, floats, durations, slices, maps and arrays report the first failing tag with its parameter through `Var`, and the same through a struct field |
| CrossFieldFollowsTheModel | the six field comparisons through `VarWithValue` and through a two-field struct |
| ConditionalRequirementsFollowTheModel | the twelve conditional tags on a field F beside Other, A and B, with single fields and lists |
| UniqueFollowsTheModel | duplicates, nil pointers and struct fields |
| StringFormatsFollowTheModel | 70 format tags on constructed valid and invalid values |
| SubstringTagsFollowTheModel | substring, prefix/suffix, eq/ne(_ignore_case) and the oneof family with escaped and quoted parameters |
| TraversalFollowsTheModel | `Struct` on a generated `Doc` (by value and by pointer) yields exactly the model's namespaces and tags; `Namespace`/`StructNamespace`/`Field` agree; `StructExcept` drops exactly the named fields' errors and `StructPartial` keeps the named fields' own errors |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (decimal parameters without leading zeros, no string operands for `gtfield`, time.Time
itself for time comparisons, colour alphas the regex accepts, no bracketed IPv6 in
`hostname_port`, bool conditions written `true`/`false`, one field for `excluded_without`, no
apostrophes in `oneof`, no IPv4-mapped IPv6 text, valid SSN areas, FQDN labels not ending in a
hyphen, lower-case UUIDs, ULIDs starting 0-7, base64 data URIs, masked IPv6 prefixes); the
pins assert the correct behaviour and fail while the bug exists.

## Accepted differences

- Panics on bad tags and parameters (`min=1.5` on an int, `eq=-1` on a uint, an unknown tag, an
  empty chain element, `dive` on a scalar) are documented ("this is by design"); the properties
  generate well-formed tags only.
- A struct field named alone in `StructPartial` validates its own tags only, not its inner
  fields: upstream's `TestStructPartial` names `Sub` and expects nothing inside it checked; the
  model follows that.
- `hostname` is the RFC 952 rule (a name starts with a letter), `hostname_rfc1123` the one that
  allows a leading digit; both are modelled as such. `multibyte` accepts the empty string
  (documented as "one or more multibyte characters"); the generator never offers it. `rgb`
  percentages up to 255% are accepted (CSS clamps rather than rejects); the generator stays
  within 100%.
- `numeric` excludes exponents and a bare `.5` (documented as "basic"), `email` requires a
  dotted domain and rejects `a@localhost` and address literals, `credit_card` accepts spaces
  but not hyphens, `issn` requires the hyphen: modelled as documented, not recorded.
- `eq`/`ne` on slices, arrays and maps compare the number of items (documented).

## Bugs found

Seventeen, in bugs.toml: tag parameters read with base 0 (`max=010` is 8, `len=08` panics);
`gtfield` on strings counts bytes where `gt` counts characters; `nefield` panics on a named
time type; the rgba/hsla alpha regex (`0.05` fails, `0X` passes); `hostname_port` rejects
`[::1]:80`; `required_if` compares bools with the text `true` only; `excluded_without` takes one
field where its siblings take a list; `oneof` values cannot contain an apostrophe; `ipv4`
accepts `::ffff:1.2.3.4`; `html_encoded` rejects `&#9;`; `ssn` accepts areas 000/666/9xx;
`unique` panics on a private field; `fqdn` accepts a trailing hyphen; the docs say upper-case
UUIDs fail `uuid` (they pass); `ulid` accepts a first character above 7; `datauri` rejects the
plain RFC 2397 form; `cidrv4` and `cidrv6` disagree on host bits.

## History

- 2026-09-20 (turn 334): target added at 6a9b666 (v10.30.5) with seven properties, 17 pins.
- 2026-09-23: generators rewritten in combinator style: each property draws one case record,
  the format case is a FlatMap from the tag to that format's generator, mutations are a drawn
  enum rendered by a pure switch, and the high-rate skips became generator shape. The old
  `luhn_checksum` oracle expected a number below ten to pass (the validator wants two digits);
  fixed. The `ZOO_COLLECT` collector is gone. No new bug.
