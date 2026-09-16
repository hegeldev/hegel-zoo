# dnsjava

[dnsjava](https://github.com/dnsjava/dnsjava) (`dnsjava:dnsjava`, 3.6.6-SNAPSHOT, pinned at the master commit of
2026-08-30): the Java DNS library — presentation and wire codecs for some 60 record types, names, messages, EDNS options,
TSIG, dynamic update, zones and master files, a cache, DNSSEC signing and verification, plus resolvers and lookups. This
target covers the protocol layer, where the RFCs give an exact model; the networking side (resolvers, DoH, lookups,
zone transfer, the `hosts` and `spi` packages, the `dnssec` validator, the command-line tools) is not exercised.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the library from the pinned tree into
the local Maven repository (Javadoc, sources, checkstyle, spotless, the enforcer, signing, japicmp, JaCoCo, animal
sniffer and the assembly skipped; about a minute). The repository has no CONTRIBUTING file and no AI policy.

## The oracles

- **Round trips through the four forms** — presentation text, plain wire, canonical wire, and a compressed message —
  from generated rdata for 58 record types (`DnsGen`): text reparses to an equal record with identical text, wire and
  canonical wire reparse and are stable, the text of the wire-parsed record equals the original text, the canonical form
  lowercases the owner, `equals`/`compareTo`/`hashCode` agree, Java serialization goes through the wire proxy.
- **Byte-level models**: names against a list of byte labels (label bytes, length, escapes, canonical lowercasing, RFC
  4034 §6.1 canonical order with a hand-written comparator, relativize/concatenate/wild, the 63/255 limits); base16,
  base32hex and base64 against `java.util.Base64` and a hand-rolled base32 model; TTL text and RFC 1982 serial
  arithmetic against sums and modular arithmetic; addresses against `InetAddress`; mnemonic tables round-tripping.
- **Protocol rules**: RFC 1035 header/sections/counts and RRset-boundary truncation (`toWire(max)`), RFC 2136 class/TTL
  encodings for each `Update` operation, RFC 6891 EDNS options (ECS, cookie, NSID, keepalive, EDE, DAU/DHU/N3U, generic),
  RFC 8945 TSIG signing and verification with tampering, RFC 4034/6605 ECDSA P-256 signing and verification with
  expiry/inception/other-key rejection and DS digests, RRset TTL/membership rules, cache credibility rules, RFC 1035 §5
  master-file syntax with `$TTL`/`$ORIGIN`/blank owners/parentheses/comments/`$GENERATE` against a record list built
  from the same choices, and RFC 1034 §4.3.2 / RFC 4592 zone lookups against a model (exact, NODATA, CNAME, delegation
  at or above, DNAME, wildcard at the closest encloser, NXDOMAIN).

## Properties (`RecordsTest`, 4; `MessagesTest`, 4; `ZoneTest`, 2)

- `recordsRoundTripThroughTextAndWire`: a record of a random type (A, AAAA, NS, CNAME, SOA, PTR, HINFO, MX, TXT, RP,
  AFSDB, X25, ISDN, RT, NSAP, NSAP-PTR, SIG, KEY, PX, GPOS, LOC, NXT, SRV, NAPTR, KX, CERT, A6, DNAME, APL, DS, SSHFP,
  IPSECKEY, RRSIG, NSEC, DNSKEY, DHCID, NSEC3, NSEC3PARAM, TLSA, SMIMEA, HIP, CDS, CDNSKEY, OPENPGPKEY, ZONEMD, SVCB,
  HTTPS, SPF, EUI48/EUI64/AMTRELAY and two private types as `\#` generic rdata, URI, CAA, WKS, TKEY-free) with a random
  owner, TTL and class through text, `Master`, wire, canonical wire, a compressed message carrying it twice with different
  owner case, equality variants and serialization.
- `namesFollowTheLabelModel`, `ttlSerialAddressAndMnemonicsMatchTheModels`, `baseEncodingsMatchJavaUtil`: as above;
  also `DNSOutput`/`DNSInput` u8/u16/u32/counted strings and their range checks.
- `messagesRoundTripThroughWire`: random header (id, seven flags, opcode, rcode), 0–2 questions, 0–4 records per
  section sharing suffixes and RRsets, optional OPT with options and extended rcode; parse back (header, extended rcode,
  sections, counts, OPT), wire and text stability, `findRecord`/`findRRset`/`removeRecord`; `toWire(max)` for a random
  `max`: length bound, counts, TC iff a question/answer/authority record was dropped (dropping additional records is
  silent by design), prefix at an RRset boundary, OPT kept; strict `toWire(max, false)` throws iff TC would be set.
- `ednsOptionsAndTsigRoundTrip`: each option alone and inside an OPT record (equality, wire, text, typed accessors, ECS
  wire length); a TSIG-signed message with a random key, key name and HMAC algorithm verifies, and a flipped question
  byte, another key or another key name does not.
- `updatesRRsetsAndTheCacheFollowTheRules`: `Update` add/delete/replace/present/absent against RFC 2136's class/TTL/
  rdata table after a wire trip; `RRset` TTL minimum, membership, `rrs(false)`/`rrs(true)`, `deleteRR`, foreign owner
  or type refused; `Cache.addRecord` with three credibility levels against a best-credibility model, `lookupRecords` at
  and above it, another type, `flushSet`.
- `dnssecSignsAndVerifies`: a P-256 DNSKEY converts back to the key; `sign` gives the right covered type, footprint,
  signer, label count and original TTL; `verify` accepts the set (also reordered, upper-cased, wire-parsed signature)
  and rejects an extra record, expiry, pre-inception, another key; DS digests of the three lengths.
- `masterFilesParseLikeTheModel`: a generated master file (`$TTL` in seconds or units, optional `$ORIGIN`, relative/
  absolute/`@`/blank owners, TTL and class in either order or omitted, lower-case types, parentheses across lines with
  comments, trailing comments, `$GENERATE` for A/AAAA/PTR/CNAME/NS/DNAME with ranges, steps, `$` and `${o,w,b}`) against
  the record list built from the same choices; the parsed records re-read from their own text.
- `zoneLookupsMatchTheModel`: a random zone (apex SOA/NS, data names with 1–4 sets, CNAMEs, delegations with one or two
  NS, DNAMEs, wildcards) holds exactly the model's records, answers 1–6 random queries like the model, `removeRecord` of
  a member shrinks or removes the set, and `toMasterFile()` re-creates the same zone.

Shapes the properties avoid because of known bugs (by id in `bugs.toml`): A6 suffixes are never IPv4-mapped (3, 23) and
have zero prefix bits; `DNSOutput` range checks use 2^bits+1, not 2^bits (5); type bitmaps come from sorted text (7);
LOC uses whole seconds, whole-metre negative altitudes and representable sizes (1, 8, 15); base64/hex fields are valid
and non-empty (4, 9, 22); NSAP has at least one byte (10); SVCB ports are 0–65535, alpn ids `[a-z0-9-]`, values
`[a-z0-9-_./:=]`, records come from text (11, 19, 20, 21); HIP rvservers are absolute (12); signature times are 1971–2100
(13); CAA tags are alphanumeric (14); URI/CAA values are at most 255 octets (24); TXT/HINFO strings are bytes with `\DDD`
escapes, so no UTF-8 is involved (25); TTL text is fully unit-suffixed (26); `$GENERATE` is exercised through `Master`
iteration with `$` or the three-field modifier and widths up to 5 (27, 40, 44); the truncation length bound is skipped
when the OPT record alone does not fit (28); no TSIG under truncation (29, 32); `Update` uses class IN (31); the cache
sees only positive `addRecord` (33, 38); zone queries at empty non-terminals, wildcard NODATA and closer-encloser cases
are skipped (35, 36, 37); `removeRecord` is used on members only (30); TTLs stay below 2^31 (43); strict rendering is
checked only when TC is not preset (45); `RRset.equals` (39), `ReverseMap` (41), `Message.addRecord` with bad sections
(42), `OPTRecord.equals` against `EmptyRecord` (16), CERT mnemonics (17), GPOS out-of-range values (18) and
`ExtendedFlags.CO` (34) are pinned only.

Not tested: `Resolver`/`SimpleResolver`/`ExtendedResolver`, DoH, `Lookup`, `LookupSession`, `ZoneTransferIn`, `hosts`,
`spi`, `config`, the `dnssec` validator package, `NioClient`, the `tools` package, `TKEY`, TSIG over TCP streams.

## Bugs (45 open; each has a pin in `DnsjavaPinsTest`)

| id | severity | what |
|---|---|---|
| dnsjava/1 | medium | LOC prints a negative altitude with a fraction as `-99999.-99m` |
| dnsjava/2 | medium | WKS with no services, or unsorted ports in text, throws ArrayIndexOutOfBounds |
| dnsjava/3 | low | A6 with an IPv4-mapped suffix throws in `toWire`; its text cannot be re-read |
| dnsjava/4 | medium | `base64.fromString` accepts characters outside the alphabet and decodes garbage |
| dnsjava/5 | medium | `DNSOutput.writeU8/U16/U32` accept 2^8/2^16/2^32 and write zero |
| dnsjava/6 | medium | `AAAARecord(Name, int, long, InetAddress)` accepts an IPv4 address (4-byte rdata) |
| dnsjava/7 | low | type bitmaps with out-of-order window blocks are accepted and re-sorted |
| dnsjava/8 | medium | LOC seconds lose their milliseconds in text parsing |
| dnsjava/9 | low | absent base64 fields (empty OPENPGPKEY, RRSIG without signature) NPE in `toString`/`toWire` |
| dnsjava/10 | low | NSAP text `0` throws StringIndexOutOfBounds |
| dnsjava/11 | medium | SVCB `port=` is not range-checked (65536 becomes 0, -1 accepted) |
| dnsjava/12 | low | HIP rvservers ignore the origin; relative names stay relative and `toWire` fails |
| dnsjava/13 | low | RRSIG/SIG times before 1970 are accepted in text and fail in `toWire` |
| dnsjava/14 | low | CAA tags are printed unquoted/unescaped |
| dnsjava/15 | low | LOC sizes beyond 9e9 m overflow the exponent nibble into unreadable wire data |
| dnsjava/16 | low | `OPTRecord.equals` throws ClassCastException for an `EmptyRecord` of type OPT |
| dnsjava/17 | low-medium | CERT certificate-type mnemonics are shifted (1 is IPKIX, not PKIX) |
| dnsjava/18 | medium | GPOS checks longitude against the latitude range and vice versa |
| dnsjava/19 | medium | SVCB alpn values are unescaped once instead of twice (RFC 9460 §7.1.1) |
| dnsjava/20 | low-medium | SVCB values with spaces are printed unescaped; empty alpn ids are accepted |
| dnsjava/21 | low | SVCB rdata from the wire is not validated (key order, duplicates, mandatory) |
| dnsjava/22 | low | empty hex/base32 fields print as nothing and cannot be re-read |
| dnsjava/23 | low | IPv4-mapped IPv6 addresses print as dotted quads in IPv6 fields |
| dnsjava/24 | low | URI/CAA values over 255 octets read from the wire cannot be re-read from text |
| dnsjava/25 | low-medium | `Record.fromString` UTF-8-encodes non-ASCII text twice |
| dnsjava/26 | low | `TTL.parse` drops trailing digits without a unit (`1h30` is 3600) |
| dnsjava/27 | medium | `Generator.expand()` yields one record too few and repeats the first value |
| dnsjava/28 | medium | `Message.toWire(max)` exceeds `max` when the OPT record does not fit; strict mode does not throw |
| dnsjava/29 | low-medium | `Message.getTSIG()` throws IndexOutOfBounds on a truncated message with ARCOUNT > records |
| dnsjava/30 | high | `Zone.removeRecord` of a non-member removes a single-record RRset |
| dnsjava/31 | low | `Update(zone, dclass)` hardcodes class IN in the zone section |
| dnsjava/32 | high | truncation leaves stale compression entries; the TSIG owner is written as a dangling pointer |
| dnsjava/33 | medium | `Cache.addMessage` uses the header rcode only (a BADVERS response is cached as NXRRSET) |
| dnsjava/34 | low-medium | `ExtendedFlags.CO` is 0x8001 instead of 0x4000 |
| dnsjava/35 | medium | wildcards synthesize below an existing closer encloser (RFC 4592) |
| dnsjava/36 | medium | a query at an empty non-terminal answers NXDOMAIN instead of NODATA |
| dnsjava/37 | medium | a wildcard match without the type answers NXDOMAIN instead of NODATA |
| dnsjava/38 | medium | `Cache.addRecord` cannot replace a negative entry of equal credibility |
| dnsjava/39 | low | `RRset.equals`/`hashCode` depend on insertion order |
| dnsjava/40 | low | `$GENERATE` widths beyond int range are truncated instead of refused |
| dnsjava/41 | low | `ReverseMap.fromName` wraps octets above 255 |
| dnsjava/42 | low | `Message.addRecord` with a bad section throws ArrayIndexOutOfBounds |
| dnsjava/43 | low | wire TTLs with the high bit set are kept although text and constructors refuse them |
| dnsjava/44 | medium | `$GENERATE` `${offset}` and `${offset,width}` modifiers are rejected as invalid |
| dnsjava/45 | low | `toWire(max, false)` throws for any message whose TC flag is preset |

Observed and left unrecorded (arguable or cosmetic): compression folds owner case across records; `Master` reuses the
previous record's `Name` object for an equal owner, so a lower-case owner following an upper-case one prints in the
earlier line's case (the property compares owners case-insensitively); the update-message parser turns any zero-length
rdata in the prerequisite/update sections into an `EmptyRecord` whatever its class, so an added `\# 0` record loses its
text (the update property avoids empty rdata); header ids are never 65535; KEY `NOKEY` prints with parentheses over several lines; APL strips trailing zero octets; TSIG fudge is cast to int;
EDE text with an embedded NUL is truncated; `EDNSOption.Code.value` is case-sensitive while the other mnemonic tables are
not; `$GENERATE` does not update the "last owner" used by a following blank-owner line; a merged cache entry keeps the
older expiry; TSIG MAC truncation rounds down.

## History

- 2026-09-16: created (turn 183) at 8bed725c19e2 (3.6.6-SNAPSHOT, 2026-08-30); 45 bugs.
