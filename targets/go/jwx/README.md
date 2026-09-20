# jwx

[lestrrat-go/jwx](https://github.com/lestrrat-go/jwx) v4 (`github.com/lestrrat-go/jwx/v4`),
JOSE for Go: JWK, JWS, JWE and JWT, against joserfc, the Python implementation of the same
RFCs, reading what jwx writes and writing what jwx reads.

## What is tested

**`hegel/hegel_jwk_test.go`** (`jwk`)
- `TestHegelThumbprintMatchesJoserfc`: `Key.Thumbprint` (RFC 7638) with SHA-256/384/512 of
  every key in the pool (oct of 16 to 64 bytes, RSA 2048, P-256/384/521, Ed25519, X25519;
  public or private) is joserfc's thumbprint of the same key.
- `TestHegelKeyJSONReadByJoserfc`: the JSON jwx writes for a key (public or private; kid
  removed, alg or use set) is read by joserfc as the same members, with the same
  public/private nature, and `jwk.PublicKeyOf` writes what joserfc computes as the public part.
- `TestHegelJoserfcKeyReadByJwx`: keys joserfc generates (oct of 8 to 512 bits, RSA, EC, OKP;
  with or without kid) parse with `jwk.ParseKey`, marshal back to the same JSON, give the
  same public part, and parse inside a key set with `jwk.Parse`.

**`hegel/hegel_jws_test.go`** (`jws`)
- `TestHegelSignVerifiedByJoserfc`: a compact JWS from `jws.Sign` (HS/RS/PS/ES/EdDSA and
  `Ed25519`; payloads of any bytes; protected `typ`, `cty` and a private member of any JSON
  type) verifies in joserfc with the public key to the same payload, and the protected header
  joserfc reads is the one written.
- `TestHegelSignJSONVerifiedByJoserfc`: a JSON serialization with one to three signatures
  (`jws.WithJSON`, per-signature protected headers with kids) verifies against the key set,
  with the same payload and per-signature protected headers; one signature gives the flattened
  form, and `jws.Parse` reads its own output.
- `TestHegelJoserfcSignVerifiedByJwx`: joserfc's compact and JSON (protected or unprotected
  kid) serializations verify with `jws.Verify` to the payload, `jws.Parse` reads the same
  protected header, and a signature with one bit flipped is refused by both.

**`hegel/hegel_jwe_test.go`** (`jwe`)
- `TestHegelEncryptDecryptedByJoserfc`: a compact JWE from `jwe.Encrypt` (every key-management
  algorithm of RFC 7518 the key pool supports: dir, A128/192/256KW, A128/192/256GCMKW,
  RSA1_5, RSA-OAEP, RSA-OAEP-256, ECDH-ES and ECDH-ES+A*KW on P-256/384/521 and X25519,
  PBES2-HS*+A*KW; every content encryption; optional DEF compression; extra protected members)
  decrypts in joserfc with the private key to the same plaintext, and the protected header
  joserfc reads is the one written.
- `TestHegelEncryptJSONDecryptedByJoserfc`: a JSON serialization for one to three recipients
  (each with its own algorithm and a per-recipient kid) decrypts against the key set to the
  same plaintext with the same protected and per-recipient headers; one recipient gives the
  flattened form; `jwe.Parse` reads its own output.
- `TestHegelJoserfcEncryptDecryptedByJwx`: joserfc's compact and JSON serializations (general
  and flattened, with AAD, an unprotected header, the alg in the protected or the recipient
  header, DEF) decrypt with `jwe.Decrypt` and any one recipient's key to the plaintext, and
  `jwe.Parse` reads the protected header written (plus what the algorithm adds: epk, iv, tag,
  p2s, p2c) and the number of recipients.

**`hegel/hegel_jwt_test.go`** (`jwt`)
- `TestHegelTokenSignedReadByJoserfc`: a token built with `jwt.New`/`Set` (iss, sub, aud as a
  string, list or empty list, exp/nbf/iat, jti, a private claim of any JSON type) and signed
  with `jwt.Sign` decodes in joserfc to the same claims with a `typ: JWT` header.
- `TestHegelJoserfcTokenReadByJwx`: joserfc's tokens parse and verify with `jwt.Parse`, marshal
  to the same claims, and re-signed with `jwt.Sign` decode in joserfc to the same claims again.
- `TestHegelValidateMatchesJoserfc`: `jwt.Validate` with a fixed clock and an acceptable skew
  accepts a token exactly when joserfc's `JWTClaimsRegistry` with the same now and leeway does,
  for exp/nbf/iat around now, except at now == exp + leeway (RFC 7519 makes the token expired
  there; joserfc still accepts it).

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles and normalisations

joserfc 1.7.5 in the CI venv (`pip install joserfc==1.7.5`), as one persistent `python3` child
(`hegel/oracle.go`: hex-encoded arguments in, one JSON object out per request). The oracle is
configured to read a producer's output rather than to police it: header members joserfc does
not know (`strict_check_header=False`, RFC 7515 lets a producer add private members), DEF in
the allowed algorithms, and joserfc's 300000 cap on the PBES2 iteration count lifted, since jwx
uses OWASP's 600000 (and ignores a `p2c` set in the per-recipient header). RFC 7638 thumbprints
are computed from the required public members only (joserfc's `jwk.thumbprint(dict)` hashes
whatever dict it is given). Not judged: an `aud` claim with one value (RFC 7519 allows the
string and the one-element array; jwx always writes the array, `jwt.WithFlattenAudience` would
change that) is compared as an array; the validation boundary `now == exp + leeway`; JSON JWE
serializations whose protected header has non-ASCII text (joserfc re-encodes the protected
header with `\u` escapes before checking the tag, so a producer's raw UTF-8 header never
verifies in the JSON form; the compact form is fine); joserfc's `recipients[i].header` None for
an absent per-recipient header is read as `{}`.

## Known bugs (gated)

Three bugs (`bugs.toml`): the JSON serialization of an empty ciphertext (an empty plaintext
under AES-GCM) has no `ciphertext` member, which nobody, jwx included, can read; `jwe.Parse`
refuses `"ciphertext": ""` in a JSON serialization while accepting the same message in compact
form; and `Recipient.Headers()` of a flattened serialization mirrors the protected header when
there is no encrypted key (dir, ECDH-ES) and is empty when there is. `hegel/known.go` gates them
by generated shape; `HEGEL_NO_KNOWN=1` lifts the gates.

## Not tested

`jwk` fetching and caching (`jwk.Fetch`, `jwk.Cache`), PEM/DER import and export, key
generation, JWK `x5c`/`x5t` members; `jws` detached and unencoded payloads (`b64: false`,
`crit`), `jws.WithKeySet`/`WithKeyProvider`; `jwe` with AAD written by jwx (`jwe.WithAAD`)
and unprotected headers written by jwx; `jwt` issuer/audience/subject validators, `jwt/openid`,
`jwt.Settings`; the extension modules (ES256K, Ed448, ML-DSA, ML-KEM, X448).

## History

- 2026-09-20: written against e0b0559ed4c0e25340a87d2d9a176ec906d2cd61 (2026-09-17, v4.5.0+2)
  with hegel.dev/go/hegel v0.6.33; 3 bugs.
