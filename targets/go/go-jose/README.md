# go-jose

[go-jose/go-jose](https://github.com/go-jose/go-jose) v4 (`github.com/go-jose/go-jose/v4`),
JOSE for Go: JWK, JWS, JWE and JWT, against joserfc, the Python implementation of the same
RFCs, reading what go-jose writes and writing what go-jose reads (the same oracle as go/jwx).

## What is tested

**`hegel/hegel_jwk_test.go`** (`JSONWebKey`)
- `TestHegelThumbprintMatchesJoserfc`: `Thumbprint` (RFC 7638) with SHA-256/384/512 of every
  key in the pool (oct of 16 to 64 bytes, RSA 2048, P-256/384/521, Ed25519; public or private)
  is joserfc's thumbprint of the same key.
- `TestHegelKeyJSONReadByJoserfc`: the JSON go-jose writes for a key (public or private; kid,
  alg, use set or not) is `Valid`, is read by joserfc as the same members with the same
  public/private nature (`IsPublic`), and `Public()` writes what joserfc computes as the
  public part.
- `TestHegelJoserfcKeyReadByGoJose`: keys joserfc generates (oct of 8 to 512 bits, RSA, EC,
  OKP; with or without kid) unmarshal, are `Valid`, marshal back to the same JSON, give the
  same public part, and parse inside a `JSONWebKeySet` where `Key(kid)` finds them.

**`hegel/hegel_jws_test.go`** (`NewSigner`, `NewMultiSigner`, `ParseSigned`, `ParseDetached`)
- `TestHegelSignVerifiedByJoserfc`: a compact JWS (HS/RS/PS/ES/EdDSA; payloads of any bytes;
  protected typ, cty and a private member of any JSON type; a kid through the `JSONWebKey`),
  attached or detached, verifies in joserfc with the public key to the same payload with the
  protected header written; go-jose reads its own output back to the same header.
- `TestHegelSignJSONVerifiedByJoserfc`: the full JSON serialization with one to three
  signatures verifies in joserfc against the key set with the same payload and per-signature
  protected headers; one signature gives the flattened form; `VerifyMulti` picks each key.
- `TestHegelJoserfcSignVerifiedByGoJose`: joserfc's compact and JSON (protected or unprotected
  kid) serializations verify with `Verify` to the payload; `Protected`, `Unprotected` and the
  merged `Header` are the ones written; a signature with one bit flipped is refused by both.

**`hegel/hegel_jwe_test.go`** (`NewEncrypter`, `NewMultiEncrypter`, `ParseEncrypted`)
- `TestHegelEncryptDecryptedByJoserfc`: a compact JWE (every key-management algorithm of RFC
  7518 go-jose supports with the pool: dir, A*KW, A*GCMKW, RSA1_5, RSA-OAEP, RSA-OAEP-256,
  ECDH-ES and ECDH-ES+A*KW on P-256/384/521, PBES2-HS*+A*KW; every content encryption; DEF;
  extra protected members) decrypts in joserfc with the private key to the same plaintext with
  the protected header written; go-jose reads its own output back to the same header.
- `TestHegelEncryptJSONDecryptedByJoserfc`: the full JSON serialization for one to three
  recipients (own algorithm and kid each, optional AAD, DEF) decrypts in joserfc against the
  key set to the same plaintext, AAD, protected and per-recipient headers; one recipient gives
  the flattened form; `DecryptMulti` finds each recipient with the merged header.
- `TestHegelJoserfcEncryptDecryptedByGoJose`: joserfc's compact and JSON serializations
  (general and flattened, AAD, an unprotected header, the alg in the protected or the recipient
  header, DEF) parse, `DecryptMulti`/`Decrypt` with any one recipient's key to the plaintext
  with the right index, and the merged header carries everything written (plus what the
  algorithm adds: epk, iv, tag, p2s, p2c).

**`hegel/hegel_jwt_test.go`** (`jwt`)
- `TestHegelTokenSignedReadByJoserfc`: `jwt.Signed(signer).Claims(jwt.Claims{...})
  .Claims(private)` (iss, sub, aud as a string or list, exp/nbf/iat, jti, a private claim of any
  JSON type; typ JWT or not) decodes in joserfc to the same claims and header (empty strings
  are omitted by the builder's omitempty and compared as absent).
- `TestHegelJoserfcTokenReadByGoJose`: joserfc's tokens parse with `jwt.ParseSigned`, their
  `Claims` (into `jwt.Claims` and a map) are the ones encoded with the header written, and a
  token rebuilt from the parsed claims decodes in joserfc to the same claims again.
- `TestHegelValidateMatchesJoserfc`: `Claims.ValidateWithLeeway` with a fixed time accepts a
  token exactly when joserfc's `JWTClaimsRegistry` with the same now and leeway does, for
  exp/nbf/iat around now including the boundaries (the two agree there, unlike jwx).

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles and normalisations

joserfc 1.7.5 in the CI venv (`pip install joserfc==1.7.5`), as one persistent `python3` child
(`hegel/oracle.go`, shared with go/jwx: hex-encoded arguments in, one JSON object out per
request), configured to read a producer rather than police it (unknown header members allowed,
DEF allowed, the PBES2 iteration cap lifted; RFC 7638 thumbprints from the required members;
`jwt.encode` without its default `typ`). The key pool follows RFC 7518 section 3.2: an HMAC key
signs only with hashes no longer than the key (go-jose refuses `invalid key size`). Not judged:
a one-value `aud` is compared as an array (RFC 7519 allows both forms); JSON JWE serializations
whose protected header has non-ASCII text (joserfc re-encodes the protected header before
checking the tag); joserfc's None for an absent per-recipient header is read as `{}`; `dir` and
ECDH-ES are single-recipient only (`NewMultiEncrypter` refuses them, rightly).

## Known bugs (gated)

Four bugs (`bugs.toml`): `Thumbprint` fails and `Valid` is false for symmetric keys, a
documented key type; a symmetric `JSONWebKey` signing key's KeyID is never written as kid (so
multi-signature JSON over HMAC keys cannot be verified with a key set); and header members with
a JSON null value are dropped when parsing. `hegel/known.go` gates them by generated shape;
`HEGEL_NO_KNOWN=1` lifts the gates.

## Not tested

X.509 members (`x5c`, `x5u`, `x5t`), `Header.Certificates`; `EmbedJWK`, nonces and `crit`;
`b64: false`; opaque signers, verifiers and key encrypters; `jwt.Encrypted`,
`SignedAndEncrypted` and nested tokens; `Expected` issuer/subject/audience/ID matching; the
`jose-util` command and the `cipher`, `json` and `cryptosigner` packages directly.

## History

- 2026-09-20: written against 25b55feb059b8b08e16a73c601c8b80571fa5208 (2026-09-03, v4.1.5+1)
  with hegel.dev/go/hegel v0.6.33; 4 bugs.
