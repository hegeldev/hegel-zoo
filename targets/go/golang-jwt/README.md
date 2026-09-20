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
it in its venv). The patch adds `hegel_test.go` (properties), `hegel_pins_test.go` (one plain
test per bug), `hegel_oracle_test.go` (the joserfc child) and `hegel_keys_test.go` (the key pool),
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
| NumericDatesRoundTrip | `NewNumericDate` truncates to `TimePrecision`, `MarshalJSON` writes the modelled decimal, `UnmarshalJSON` reads it back (exactly at second precision, within the float64 error below); `ClaimStrings` marshal and unmarshal per the model and refuse numbers, objects and mixed arrays |
| ParsingFollowsBase64AndJSON | `DecodeSegment` agrees with the base64url model under every option pair; `ParseUnverified` classifies generated tokens (raw, padded, standard-alphabet, junk characters, dirty trailing bits, broken JSON, missing/unknown/non-string alg, extra dots) exactly as the model of its steps says; nothing panics through `ParseWithClaims` with every claims type on random text |
| SigningMethodsCheckKeysAndSignatures | `Sign` takes exactly its key type (EdDSA: any `crypto.Signer` with an Ed25519 public key; ES: the matching curve), `Verify` takes the matching public key and refuses other types, other keys, altered signatures and other texts; the none method only works with `UnsafeAllowNoneSignatureType` and is refused under `WithValidMethods` |
| RequestExtractorsFindTheToken | `BearerExtractor` (case-insensitive prefix), `HeaderExtractor`, `ArgumentExtractor` (query and form), `MultiExtractor` order and `PostExtractionFilter` find the token where the model says; `ParseFromRequest` verifies it |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (fractions at sub-second precision, pre-epoch fractions, dates beyond 2^63, string-typed
dates, explicit nulls, precisions that are not powers of ten, line breaks in a segment). With everything gated the
properties run clean; `ZOO_COLLECT=1` prints class counts and the first 25 mismatches instead of
failing.

## Accepted differences (not bugs)

- At the default `TimePrecision` of one second a fractional date is floored on parsing, so
  `exp: X.9` expires at `X`; the variable's comment documents the truncation.
- `NumericDate` goes through a float64, so microsecond and nanosecond precisions cannot be exact
  at current epochs (the spacing of float64 near 1.8e9 is 2.4e-7 s); the property allows one
  unit of error there and the README says nothing else.
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
