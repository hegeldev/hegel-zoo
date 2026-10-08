# golang-jwt

[golang-jwt/jwt](https://github.com/golang-jwt/jwt) is the Go JWT library (9.2k stars, the
maintained fork of dgrijalva/jwt-go; v5 module `github.com/golang-jwt/jwt/v5`): signing methods
HS/RS/PS/ES 256-512, EdDSA and `none`, a `Parser` with functional options (leeway, required
claims, expected audience/issuer/subject, valid methods, strict or padded base64, JSON numbers),
`MapClaims` and `RegisteredClaims` with `NumericDate` and `ClaimStrings`, a `Validator`, and the
`request` package that extracts tokens from HTTP requests. The pin is the default branch at
`73c870b` (2026-09-14, eight commits past v5.3.1).

The repository has LICENSE (MIT), README, SECURITY.md and a .github with CODEOWNERS and
workflows; nothing restricts AI-written tests, and the zoo keeps its tests in its own patch and
files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root, with `python3` and
[joserfc](https://jose.authlib.org/) 1.7.5 on the path (`pip install joserfc==1.7.5`; CI installs
it in its venv). The patch adds `hegel_test.go` (the wide properties), `hegel_shapes_test.go` (one narrow
property per recorded bug), `hegel_pins_test.go` (one plain test per bug), `hegel_oracle_test.go`
(the joserfc child) and `hegel_keys_test.go` (the key pool),
and requires `hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive moves from 1.21 to
1.26.0 for it; golang-jwt itself has no dependencies).

## Oracles

- **joserfc** (Python, by the author of Authlib, on pyca/cryptography), one persistent child
  driven line by line: it reads every token golang-jwt signs (header, claims and raw payload
  compared) and signs tokens for golang-jwt to parse, for all thirteen algorithms, with keys
  crossing as PEM (RSA, EC, Ed25519) or a JWK dict (oct). Its `JWTClaimsRegistry` is a second
  opinion on exp/nbf/iat validation, away from the one boundary where the two conventions differ
  by design (golang-jwt: expired at `now == exp + leeway`; joserfc: still valid).
- **A model of RFC 7519 claims validation** under a stopped clock: exp, nbf, iat with leeway,
  required exp/nbf, aud (any of / all of, a string or an array, `[""]` and `[]` as missing), iss,
  sub, and ill-typed claims (`ErrInvalidType`), as a set of the sentinel errors `Validate` must
  report — for `MapClaims` read with `json.Unmarshal` and with `UseNumber`, for
  `RegisteredClaims`, and through `Parse` (`ErrTokenInvalidClaims` wrapping the set).
- **Models of the serialisation**: `NumericDate` at each `TimePrecision` (truncation, the decimal
  text, the round trip), `ClaimStrings` under both settings of `MarshalSingleStringAsArray`,
  `RegisteredClaims` with its `omitempty` members; the parser's segment decoding under
  `WithPaddingAllowed`/`WithStrictDecoding` (base64url alphabet, padding, length mod 4, trailing
  bits) and the order of `ParseUnverified`'s checks (malformed before unverifiable, the signature
  segment last).
- **The signing methods' own contracts**: the key types each `Sign`/`Verify` takes, the curve
  check, signature sizes, and that a changed, truncated, extended or empty signature never
  verifies.

## Method

| Property | Checks |
|---|---|
| ValidationFollowsTheModel | `Validator.Validate` reports exactly the modelled sentinel errors for MapClaims (plain and UseNumber) and RegisteredClaims, `Parse` wraps them in `ErrTokenInvalidClaims`, RegisteredClaims rejects exactly the ill-typed documents, joserfc agrees on exp/nbf/iat |
| GoTokensReadInJoserfc | every algorithm × key: joserfc verifies golang-jwt's token with the same header, claims and payload bytes; golang-jwt reads its own token back |
| JoserfcTokensParseInGo | joserfc's tokens parse and verify with the same header and claims (MapClaims and RegisteredClaims, with `WithJSONNumber`, strict and padded decoding); a changed signature/payload/header, another key, a key of the wrong type, an excluded algorithm, an empty key set, a nil or failing Keyfunc all fail with the documented sentinel; a key set holding the right key verifies |
| MapAndRegisteredClaimsAgree | the six `Claims` accessors give the same values from MapClaims and RegisteredClaims for one document; RegisteredClaims marshals to the modelled text and reads back equal under both `MarshalSingleStringAsArray` settings |
| NumericDatesRoundTrip | `NewNumericDate` truncates to `TimePrecision`, `MarshalJSON` writes the modelled decimal, `UnmarshalJSON` reads it back exactly at the precision (under `HEGEL_NO_KNOWN=1` within the float64 error below); `ClaimStrings` marshal and unmarshal per the model and refuse numbers, objects and mixed arrays |
| ParsingFollowsBase64AndJSON | `DecodeSegment` agrees with the base64url model under every option pair; `ParseUnverified` classifies generated tokens (raw, padded, standard-alphabet, junk characters, dirty trailing bits, broken JSON, missing/unknown/non-string alg, extra dots) exactly as the model of its steps says; nothing panics through `ParseWithClaims` with every claims type on random text |
| SigningMethodsCheckKeysAndSignatures | `Sign` takes exactly its key type (EdDSA: any `crypto.Signer` with an Ed25519 public key; ES: the matching curve), `Verify` takes the matching public key and refuses other types, other keys, altered signatures and other texts; the none method only works with `UnsafeAllowNoneSignatureType` and is refused under `WithValidMethods` |
| RequestExtractorsFindTheToken | `BearerExtractor` (case-insensitive prefix), `HeaderExtractor`, `ArgumentExtractor` (query and form), `MultiExtractor` order and `PostExtractionFilter` find the token where the model says; `ParseFromRequest` verifies it |

One narrow property per recorded bug, in `hegel_shapes_test.go`, draws that bug's shape region
with random contents and is judged by the same models: FractionsRoundTripAtTheirPrecision
(golang-jwt/1), PreEpochInstantsMarshalThemselves (/2), DatesBeyondInt64DoNotWrap (/3),
StringDatesAreInvalidTypes (/4), NullClaimsAreAbsentEverywhere (/5),
OddPrecisionsWriteTheirFraction (/6) and LineBreaksInSegmentsAreMalformed (/7). Each is a
deterministic expected failure; under `HEGEL_NO_KNOWN=1` each draws the neighbouring region
instead and passes.

## Known shapes drawn by default

The generators draw the shape of every recorded bug as an explicit alternative beside the plain
ones, and the models say what RFC 7519 and the package's documentation say: a fraction reads
back exactly at its precision, a pre-epoch instant marshals as itself, a date beyond 2^63 is an
instant after any clock (`nbf: 1e19` not yet valid, `exp: 1e19` not expired; `1e400` is the
documented float conversion error in RegisteredClaims and encoding/json's range error in
MapClaims), a quoted number is an invalid type in both claims types, an explicit null is an
absent claim in both, a precision that is not a power of ten writes as many digits as the
fraction needs, and a line break inside a segment is malformed under every option pair. A wide
property that meets a recorded shape fails naming the bug (`collector.mismatch`) and is listed in
`target.toml` as the expected failure mapped to it, beside the pin: ValidationFollowsTheModel
and MapAndRegisteredClaimsAgree shrink to golang-jwt/5 (the null claims; the huge date /3 once
in nine rounds), JoserfcTokensParseInGo and ParsingFollowsBase64AndJSON to /7 (a line break in
a segment), NumericDatesRoundTrip to /1 (the fraction one unit early; /6 in two rounds of
eleven), and GoTokensReadInJoserfc to /3 intermittently (a RegisteredClaims token with a
`1e19` date, under one percent of its cases, so it passes some default-count runs and fails
every 1000-case run). SigningMethodsCheckKeysAndSignatures and RequestExtractorsFindTheToken
reach no recorded shape and pass. `HEGEL_NO_KNOWN=1` (read once into `noKnown`) turns every
switch on: the model then reproduces the package where the bug is a reading of the input
(sub-second truncation, string dates, nulls, line breaks) and the generators stop drawing the
shapes that are regions of the input (pre-epoch fractions, huge dates, odd precisions) - no
case is assumed away, so every property passes. `ZOO_COLLECT=1` prints class counts and the
first 25 mismatches instead of failing.

The generators are package-level values: a date claim is a weighted record (the plain integer
first) with a pure `json()`, string and audience claims likewise, the claims document a
`Composite` of those plus private members and an order tape applied modulo in a pure `render`;
validation options a record; the segment spelling (raw, line break, padded, standard alphabet,
junk character at a position, dirty trailing bits) rendered from the bytes by a pure function;
token and signature mutations edit records applied modulo the live length; the precision and
instant of the round trip a record judged by `modelDateText`.

## Accepted differences (not bugs)

- At the default `TimePrecision` of one second a fractional date is floored on parsing, so
  `exp: X.9` expires at `X`; the variable's comment documents the truncation.
- `NumericDate` goes through a float64, so nanosecond precision cannot be exact at current
  epochs (the spacing of float64 near 1.8e9 is 2.4e-7 s); under `HEGEL_NO_KNOWN=1` the property
  allows one unit of error below at sub-second precisions. By default the one-unit-early read
  at millisecond and microsecond precision is golang-jwt/1's shape (rounding would be exact
  there) and the property expects the exact instant.
- Validation boundaries: expired at `now == exp + leeway` (RFC 7519: "the current date/time MUST
  be before"), valid at `now == nbf - leeway`; joserfc keeps `now == exp + leeway` valid.
- HMAC keys of any length sign and verify (RFC 7518 3.2 asks for at least the hash size); joserfc
  only refuses an empty key. `[]byte` keys, `ed25519.PublicKey` by value and `*ecdsa.PublicKey`
  are the documented shapes; the pointer/value alternatives are `ErrInvalidKeyType`.
- `WithPaddingAllowed` pads the segment itself, so unpadded and correctly padded tokens both
  parse; a lone `=` inside a segment is still malformed. Without it any `=` is malformed.
- A claims segment of `null` parses into an empty MapClaims and validates; `aud: [""]` and
  `aud: []` count as no audience (the code comments say so).
- The none method's `Sign` with a real key and `Verify` without the magic constant return
  `NoneSignatureTypeDisallowedError`, which wraps `ErrTokenUnverifiable`; through `Parse` it is
  wrapped again in `ErrTokenSignatureInvalid`.

## Bugs found

Seven, recorded in `bugs.toml` with a pin test each, six in `NumericDate` and the claims
accessors: a fraction at sub-second precision read one unit early (golang-jwt/1), a pre-epoch fraction
marshalled as another instant (golang-jwt/2), dates at or beyond 2^63 seconds wrapping to the
minimum int64 so `nbf: 1e19` is accepted and `exp: 1e19` expired (**golang-jwt/3**),
RegisteredClaims accepting a string as a date (golang-jwt/4), MapClaims calling an explicit null
an invalid type where its own aud handling and RegisteredClaims read it as absent
(golang-jwt/5), and a `TimePrecision` that is not a power of ten writing too few digits
(golang-jwt/6); the seventh is the parser accepting line breaks inside a token's segments (a token with
newlines in its signature verifies), under `WithStrictDecoding` too (golang-jwt/7). All found on 2026-09-20 (turn 328) from the
round-trip, agreement and parsing properties and from reading `types.go` and `map_claims.go`
while writing the model. The signing and verification paths agreed with joserfc and the
models throughout.

## History

- 2026-09-20 (turn 328): target created at `73c870b`; 7 bugs.
- 2026-10-08 (turn 1305): generators rewritten in combinator style; the seven `Known` switches
  inverted so the recorded shapes are drawn by default and the wide properties are the expected
  failures mapped to the bugs; seven narrow properties added; two latent faults of the old test
  fixed (the clock candidate was drawn from a map iteration, so a case could replay differently;
  the odd-precision skip also skipped the 2 s precision, which never ran).
