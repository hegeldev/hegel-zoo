# distribution-reference

[distribution/reference](https://github.com/distribution/reference) is the Go package behind
container image references (`docker.io/library/ubuntu:latest@sha256:...`), used by Docker,
containerd and the registry: `Parse` reads the documented grammar, `ParseNormalizedNamed` adds
the Docker Hub defaults (`docker.io`, `library/`), `FamiliarString` removes them again,
`ParseDockerRef`, `ParseAnyReference`, `WithTag`/`WithDigest`/`TrimNamed`, `Field` for
encoding, `Sort`, `FamiliarMatch`. The pin is `0965666` (2026-04-18, 22 commits after `v0.6.0`).

The repository is Apache-2.0; CONTRIBUTING.md is the distribution project's standard guide (DCO
sign-off) with nothing about AI-written code, and there are no agent instructions. The zoo
keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds, as the external
package `reference_test`, `hegel_test.go` (harness, the `Known` switches, and blank imports of
`crypto/sha256` and `crypto/sha512` so that go-digest's three algorithms are registered, as the
package documents callers must), `hegel_model_test.go` (the grammar and normalization model),
`hegel_gen_test.go` (generators), `hegel_props_test.go` and `hegel_pins_test.go` (one plain
test per bug), and requires `hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive rises to
1.26).

## Oracles

- **The package's own grammar**, the "Grammar" section of the package comment, restated as a
  hand-written scanner (no regular expressions): path components, separators, domain
  components, ports, tags, digests, identifiers. Where the grammar delegates ("`\[ IPv6address
  \]`; rfc3986 appendix-A") the model asks `net/netip`, excluding zones and dotted IPv4 tails
  as regexp.go's comments say. The grammar's `[domain '/'] remote-name` is ambiguous; the model
  takes the first component as the domain whenever it can be one, as the regexp does.
- **The normalization rules** stated in normalize.go's comments: a single component is an
  official image (`docker.io/library/`), a first component that is `localhost`, contains `.` or
  `:`, or has an uppercase letter is a domain, `index.docker.io` is `docker.io`, `library/`
  is added on Docker Hub when the remote name has one component; `ParseDockerRef` keeps the
  digest over the tag and fills in `latest`; `ParseAnyReference` reads identifiers and digests
  first; familiar names drop `docker.io` and a one-component `library/`.
- **go-digest** (`Parse`'s digest validation): registered algorithm, lowercase hex of its size.
- **The laws the API implies**: `Parse(s).String() == s`; a normalized name is a fixed point of
  `ParseNormalizedNamed`, accepted by `ParseNamed` and read the same by `Parse`;
  `ParseNormalizedNamed(FamiliarString(r)) == r`; `WithTag`/`WithDigest`/`TrimNamed` compose;
  `Field` marshals and unmarshals to the same reference; `Sort` orders by the documented rank
  then string, and is independent of input order and a fixed point; `FamiliarMatch` is
  `path.Match` on the familiar string, then on the familiar name.

Generators build names from components with every separator form and the shapes that break
them (leading/trailing/tripled separators, uppercase, spaces), domains from a list (Hub names,
`localhost`, ports, IPv4, bracketed IPv6 valid and not, uppercase, malformed), tags valid and
invalid (128 and 129 characters, leading `.`, `:`/`/`/`@` inside), digests for all three
algorithms with wrong lengths, uppercase hex, unregistered and malformed algorithms, plus bare
identifiers and digests, a few fixed odd strings, and one-byte mutations of a fifth of the
strings.

## Method

| Property | Checks |
|---|---|
| ParseFollowsTheGrammar | `Parse` accepts exactly the grammar's strings, returns the documented sentinel otherwise, yields the grammar's components, `String()` returns the input |
| NormalizeFollowsTheRules | `ParseNormalizedNamed` against the normalization rules; fixed point; `ParseNamed`, `Parse` and the familiar forms agree; the familiar string parses back to the same reference |
| DockerRef | `ParseDockerRef` accepts what `ParseNormalizedNamed` does and returns a tagged xor digested reference, digest winning, `latest` filled in |
| ReferenceAlgebra | `TrimNamed`, `IsNameOnly`, `TagNameOnly`, `Domain`/`Path`, `FamiliarName`, `WithTag` and `WithDigest` (acceptance per grammar, components, `Parse` of the result, composition in both orders), `Field` round trip |
| AnyReference | `ParseAnyReference` against its rules (identifier, digest, else normalized); `Named` iff it has a name; `Field` round trip keeps the type |
| Sort | order, independence of input order, fixed point |
| FamiliarMatch | equals `path.Match` on the familiar string then name, including the error |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (bracketed hosts that are not IPv6 addresses, the familiar forms that read as another
reference, `Field` of a digest-only reference, the error identity of empty and uppercase names
in `ParseNormalizedNamed`); the pins assert the documented behaviour and fail while the bug
exists. `ZOO_COLLECT=1` records mismatches instead of failing and prints the class counts.

## Accepted differences

- `ParseNormalizedNamed("localhost")` and `"example.com:5000"` are official images
  (`docker.io/library/localhost`, `docker.io/library/example.com:5000`): the code's own FIXME
  and the Docker CLI's behaviour; the model follows the code.
- `ParseNormalizedNamed(strings.Repeat("a", 255))` is "too long" though `Parse` accepts the same
  string: the limit is applied to the normalized path (`library/` + name); the model does the
  same.
- `WithDigest` validates the digest against the grammar only, so a reference built with an
  unregistered algorithm has a `String()` that `Parse` rejects; the package tells callers to
  validate digests themselves, and the property checks `Parse` only for registered algorithms.
- Domains are case-sensitive (`Docker.io/foo` is not `docker.io/library/foo`), as the grammar
  allows uppercase in domain components; not judged.
- Bracketed hosts with a dotted IPv4 tail (`[::ffff:1.2.3.4]`, `[::fff:1.2.3.4]`) are rejected
  by both; regexp.go's comment excludes them as "special addresses such as IPv4-Mapped".

## Bugs found

Five, in bugs.toml: a digest-only reference comes back from `Field`'s text round trip as the
repository `sha256` tagged with the hex; the familiar string of `docker.io/foo.bar/baz`,
`docker.io/localhost/baz`, `docker.io/index.docker.io/baz` and `docker.io/library/<64 hex>`
does not parse back to the same reference; a bracketed host may be any run of hex digits and
colons; `ParseNormalizedNamed` does not return the `ErrNameEmpty` and `ErrNameContainsUppercase`
sentinels `Parse` returns; the package grammar misstates two separators (`[-]*`, `[+.-_]`).

## History

- 2026-09-21 (turn 339): target added at 0965666 (v0.6.0+22) with seven properties, 5 pins.
