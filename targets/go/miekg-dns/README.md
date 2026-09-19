# miekg-dns

[miekg/dns](https://github.com/miekg/dns) (BSD-3-Clause), pinned at `2e4905f` (v1.1.73,
2026-09-01): the Go DNS library — presentation and wire forms of some 90 record types, messages
with EDNS(0) and compression, a zone-file parser, DNSSEC and TSIG primitives, client and server.

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and eight test files (package
`dns_test`): `hegel_test.go` (plumbing, the `Known` gates), `hegel_gen_test.go` (names, character
strings and the rdata of 59 record types in presentation form), `hegel_oracle_test.go` (the
dnspython child process), `hegel_records_test.go`, `hegel_names_test.go`, `hegel_messages_test.go`,
`hegel_dnssec_test.go` (the nine properties) and `hegel_pins_test.go` (nineteen pins). **Needs
`python3` with the `dnspython` package (2.8) on PATH**: it is the second implementation everything
is compared with. The whole run takes about six seconds; the library's own tests run in the same
`go test`.

## Properties

| Test | Checks |
|---|---|
| `TestHegelRecordsAgreeWithDnspython` | A record of any of 59 types written in presentation form (escaped names, quoted strings with escapes, every gateway/digest/bitmap variant, RFC 3597 unknown types, TTL units, classes) packs to the same rdata in `NewRR`+`PackRR` and in dnspython; both libraries accept the same texts; `UnpackRR` reads the wire back to a record whose `String()` packs identically; `Len` is the packed size; the record and its wire copy are `IsDuplicate`; dnspython reads the library's wire form to its own text. |
| `TestHegelNamesAgreeWithDnspython` | Escaped, mixed-case names: `PackDomainName` agrees with dnspython's wire form, `UnpackDomainName` text packs back, `CanonicalName` matches dnspython's canonical form, `IsDomainName`/`CountLabel`/`Split`/`NextLabel`/`PrevLabel`/`SplitDomainName` agree with each other and with the wire labels, `CompareDomainName` and `IsSubDomain` agree with dnspython's `fullcompare`/`is_subdomain` for parents, children, case variants and unrelated names. |
| `TestHegelReverseNamesAgreeWithDnspython` | `ReverseAddr` of random IPv4/IPv6 addresses equals dnspython's `reversename`. |
| `TestHegelMessagesAgreeWithDnspython` | Random messages (header bits, questions, records in the three sections, an OPT with random EDNS options, extended rcodes, compression on or off): dnspython reads the packed message to the same header, questions, records and EDNS data; dnspython's re-serialisation unpacks to the same message; `Unpack(Pack)` is the identity and `Pack` is byte-stable; both compression settings agree and the compressed form is not longer; `Msg.Len` is the packed size; `Copy` is equal. |
| `TestHegelTruncateFits` | `Truncate(size)` leaves a message whose packed size fits (or 512), keeps the header, question and OPT, drops records only from the end of the sections, sets TC exactly when it dropped something, and changes nothing when the message already fits. |
| `TestHegelDnssecPrimitivesAgreeWithDnspython` | `HashName` (NSEC3 with random salts and iterations), `DNSKEY.KeyTag` and `ToDS` for SHA-1/256/384 equal dnspython's `nsec3_hash`, `key_id` and `make_ds`. |
| `TestHegelTsigInteroperates` | A message signed with `TsigGenerate` (HMAC-SHA1/224/256/384/512, random keys and fudge) verifies in dnspython with the same MAC and in `TsigVerify`; a message signed by dnspython verifies with `TsigVerify` and unpacks to the same message; a damaged message verifies in neither; a wrong secret fails. |
| `TestHegelZoneParserAgreesWithDnspython` | Generated master files (`$TTL`, `$ORIGIN`, relative/absolute/`@`/blank owners, TTL and class in either order or omitted, parentheses across lines, comments) give the same records from `NewZoneParser` and dnspython's zone reader (per owner/type/class, with dnspython's rrset TTL and duplicate rules), all under the origin. |
| `TestHegelPin...` | One plain test per recorded bug. |

## Bugs

Nineteen, see `bugs.toml`: `Len` overestimates escaped names and strings, base64 fields, empty
type bitmaps and APL prefixes (1); NSEC/NSEC3/CSYNC text with unsorted types cannot be packed (2);
`IsDuplicate`, `CompareDomainName` and `IsSubDomain` compare presentation text, so equal names
and records differ by their escapes or hex case (3); LOC minutes without seconds are rejected (4);
X25 rejects a quoted address (5); an unpacked CAA/URI prints backslashes as escapes and does not
read back (6); IPSECKEY, AMTRELAY and SVCB reject IPv4-mapped IPv6 addresses with an empty error
(7); `CanonicalName` leaves an escaped upper-case letter (8); LOC seconds lose a millisecond to
float truncation (9); LOC altitudes out of range wrap around (10); NSEC3 always packs a hash length
of 20 (11); AMTRELAY with the D bit set packs without its gateway (12); a comment inside the
parentheses of NSEC/NSEC3/CSYNC/RRSIG is a parse error (13); a blank owner before any record
gives an empty owner name (14); `TsigVerify` decrements the ARCOUNT in the caller's buffer (15);
`KeyTag` ignores the RSA/MD5 rule (16); an IPSECKEY record cannot be followed by another record
in a zone file (17); `TsigVerify` refuses every NOTAUTH message unverified (18); CERT type 4 is
spelt `IPIX` instead of `IPKIX` (19).

## Notes

- Names, TXT strings and hex fields are kept in the presentation form they were parsed from;
  `String()` normalises escapes when printing, so two records can print identically and still
  compare unequal (bug 3). The properties therefore compare wire forms, not text.
- dnspython differences that are not judged (the generator avoids them or the check is skipped):
  its class-specific rdata types exist only in class IN (the oracle always parses rdata in IN);
  it validates DS digest lengths for digest types 1-4, rejects empty URI targets (RFC 7553) and
  `no-default-alpn` without `alpn` (RFC 9460), treats TTLs at or above 2^31 as 0 when reading
  a message (RFC 2181), compresses names case-insensitively, keeps the first spelling of a name
  for all records at a zone node, wants the SOA at the origin and CNAMEs alone, ignores
  out-of-zone records, and reads GPOS latitude before longitude; it writes the strings of NAPTR,
  ISDN, HINFO, URI, CAA and X25 through UTF-8 (a `\200` escape becomes two bytes) and does not
  escape backslashes in URI targets, prints HIP servers through IDNA decoding, and truncates
  `0.58*100` to 57 in LOC altitudes (the generator uses exact binary fractions there, which also
  sidesteps bug 9).
- The library rejects APL prefixes with bits set beyond the prefix length and dnspython does not;
  RFC 3123 does not say, so the generator masks its addresses. The library prints the equator as
  `S` and the prime meridian as `W` (RFC 1876's reference code prints `N`/`E`); the wire is the
  same either way.
- Messages with opcode UPDATE are not generated: dnspython reads them with RFC 2136 semantics
  (prerequisite classes, TTLs) rather than as plain sections.
