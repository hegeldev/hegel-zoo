# typescript/ipaddr.js — whitequark/ipaddr.js (against Python's ipaddress)

ipaddr.js parses, renders and classifies IPv4 and IPv6 addresses and CIDR ranges (~100M weekly
downloads: Express's `proxy-addr`, `forwarded`, many proxies). The patch checks it against
Python's `ipaddress` module (and glibc `inet_aton` for the loose IPv4 notations it documents)
and pins 5 bugs.

## How it is built

No build: `lib/ipaddr.js` is a plain ES module with no dependencies; Hegel goes under `.hegel/`.
The oracle needs `python3` on PATH (stdlib only: `ipaddress`, `socket`, `json`).

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness. `hegel/oracle.py` is held open for the whole run and answers over two FIFOs (one JSON
line per request, see `hegel/ip.mjs`): `IPv6Address` (zone id split off by the oracle, since
this Python rejects it), `IPv4Address` and `inet_aton`, `ip_interface` for CIDR arithmetic,
network membership, netmask validity, and first-match over a range table.

| Property | What it checks |
|---|---|
| `TestHegelIPv6ParseAndRenderAgreeWithPython` | a generated address in a random rendering (leading zeros, case, `::` over any zero run, an embedded dotted IPv4 tail, a zone id) is valid, parses to the generator's bytes (checked against Python), `toString()` is Python's RFC 5952 form, `toFixedLengthString()` its exploded form, every rendering parses back, and `ipaddr.parse` agrees |
| `TestHegelIPv6RejectionAgreesWithPython` | on mutated addresses and junk, `IPv6.isValid` agrees with Python's acceptance, both readings agree when both accept, and `parse` throws exactly when `isValid` is false |
| `TestHegelIPv4ParseAgreesWithInetAton` | generated renderings in the documented loose notations (hex and octal parts, one to three parts) parse to the model's octets; on mutations `isValid` agrees with `inet_aton`'s acceptance and the octets agree; `isValidFourPartDecimal` matches Python's strict parser |
| `TestHegelCIDRArithmeticAgreesWithPython` | `parseCIDR`, `networkAddressFromCIDR`, `broadcastAddressFromCIDR`, `subnetMaskFromPrefixLength` against `ip_interface`; `prefixLengthFromSubnetMask` inverts the mask and rejects a random non-mask exactly when Python's bit test does; `match()` in both call forms is network membership |
| `TestHegelRangeFollowsTheTable` | `range()` is the first entry of `SpecialRanges` (exported to the oracle as CIDR strings) that contains the address by Python's reckoning, `unicast` otherwise; `subnetMatch` on a mixed IPv4/IPv6 list with a default name |
| `TestHegelByteArrayAndMappedRoundTrips` | `fromByteArray(toByteArray())` is the identity for both families; `toIPv4MappedAddress` is `::ffff:a.b.c.d` by Python, is recognised as mapped, and `toIPv4Address`/`process()` unwrap it in any rendering; `isIPv4MappedAddress` is exactly the `::ffff:0:0/96` test |
| `TestHegelHostileInputNeverCrashes` | on mutated and junk strings all ten `is*` predicates return booleans; `parse`, `parseCIDR`, `process`, `networkAddressFromCIDR`, `broadcastAddressFromCIDR` throw an `ipaddr:` Error exactly when the matching predicate is false; `subnetMaskFromPrefixLength` on odd arguments throws an `ipaddr:` Error or returns a mask of that prefix |

The generators (`hegel/ip.mjs`) bias IPv6 parts to zero runs and to the special prefixes
(mapped, link-local, multicast, ULA, documentation, 6to4, Teredo, SRv6) and IPv4 octets to the
special ranges; mutations insert, delete, replace or duplicate characters from the address
alphabet (`:`, `.`, `%`, `/`, hex digits, `x`, spaces). `ZOO_COLLECT=1` turns mismatches into
`# COLLECT` counts and `HEGEL_TEST_CASES` (default 100) widens the sweep. Known bugs are gated
in `hegel/known.mjs` by the shape of the string (`::a.b.c.d`, a hex/octal/zero-padded tail part)
or of the call; `ZOO_NO_KNOWN=1` lifts the gates.

## Bugs

5 open, all pinned (see `bugs.toml`). In 1000-case sweeps every property agrees with Python on
every case not touched by them:

- `::a.b.c.d` (the deprecated IPv4-compatible form) is read as the IPv4-mapped `::ffff:a.b.c.d`,
  so it is misclassified, unwrapped by `process()`, and does not round-trip (1).
- The embedded IPv4 tail accepts `08`, `010` and `0x10` and reads them in decimal, where the
  IPv4 parser rejects `08` and reads `010` as octal (2).
- `subnetMaskFromPrefixLength("8abc")` is /8 and `("1e1")` is /1: parseInt leniency (3).
- `fromByteArray([1.5, 0, 0, 0])` and `new IPv6([1.5, ...])` are accepted and print `1.5.0.0.0`
  and `1.8::` (4).
- `IPv4.isIPv4` throws for an overflowing two/three-part value or a malformed octal part (5).

## Accepted differences and notes (not counted as bugs)

- The loose IPv4 notations (hex, octal, fewer than four parts) are documented as `inet_aton`
  compatible and are judged against `inet_aton`, not against Python's strict `IPv4Address`;
  `inet_aton`'s acceptance of trailing whitespace is a glibc extension and such strings are
  not judged. A zero-led part with an 8 or 9 is rejected by both.
- `::` may compress a single zero group on input (RFC 4291; Python agrees); `toString()`
  never writes it that way (RFC 5952), and Python's `str()` is the reference for that form.
- Zone ids: this machine's Python rejects them in `IPv6Address`, so the oracle splits `%zone`
  itself and takes the zone as ipaddr.js documents it (letters and digits); a zone with other
  characters is rejected by both. The zone is dropped by the CIDR network/broadcast functions,
  as by Python's `ip_interface(...).network`.
- `range()` follows ipaddr.js's own `SpecialRanges` table in its order (first match wins), not
  Python's `is_private`/`is_reserved` predicates, which draw the lines differently.
- `IPv4.isIPv4` is documented as a pattern check that does not range-check the octets:
  `isIPv4("1.2.3.256")` is true by design and not judged; only its throwing is (bug 5).

## Not tested

The CommonJS consumers (the package is ESM-only), `subnetMatch` with malformed range lists,
the `IPv4`/`IPv6` constructors on strings or typed arrays, performance, and `toIPv4Address` on
non-mapped addresses beyond its documented throw.

## History

- 2026-09-20: created at 74ee4c5 (v3.0.0), 7 properties, 5 bugs.
