# commons-codec

[Apache Commons Codec](https://github.com/apache/commons-codec) (Apache-2.0), pinned at
`f49b9638` (1.23.0-SNAPSHOT, 2026-09-14): Base16/32/45/58/64 and their streams, Hex and
BinaryCodec; the digest package (crypt(3), MurmurHash2/3, xxHash32, CRC-16/32/32C, Blake3,
DigestUtils, HmacUtils, GitIdentifiers); the net codecs (URL, percent, quoted-printable, RFC 1522 B
and Q); and the phonetic encoders.

The patch adds a Maven module `hegel/` that depends on the library at its pom version (installed
by the setup step with `mvn -DskipTests install`), on `dev.hegel:hegel` 0.6.0 and JUnit 5. The
properties are JUnit tests driven by `Hegel.test`; `Zoo.java` is the small harness shared by the
Java targets (case counts from `HEGEL_TEST_CASES`, a collect mode under `ZOO_COLLECT=1`) and
`ZooListener` prints one `ZOO ok|FAILED <method>` line per test for the judge.

## What is tested

- `BinaryTest` — RFC 4648 bit-accumulator models for Base64 (standard, URL-safe, chunked with
  custom line lengths and separators; also checked against `java.util.Base64`), Base32 (both
  alphabets, custom pads, unpadded decoding), Base16 (both cases, and `Hex`); RFC 9285's formula
  for Base45; a BigInteger model for Base58; the lenient/strict decoding contract (lenient: noise
  before the pad, missing or extra padding, dangling characters; strict, since upstream 8b506a1:
  exactly the canonical form of the instance's own encoder — alphabet, padding, line length and
  separator — with dirty trailing bits, missing padding and another configuration's output
  rejected); the input and output streams
  against the one-shot codecs with random read and write sizes; `BinaryCodec` (since upstream
  7bc15f1 `fromAscii` rejects any character other than `0`/`1` and drops leading bits that do not
  fill a byte) and `Base64.encodeInteger/decodeInteger`.
- `DigestTest` — `Crypt`/`UnixCrypt`/`Md5Crypt`/`Sha2Crypt` against libc's crypt(3) through a
  Python coprocess (skipped when `python3` or its `crypt` module is missing; the documented salt
  grammar, output format, verification with a stored hash, rounds clamping and key zeroing are
  checked regardless); ports of Austin Appleby's MurmurHash3_x86_32, MurmurHash3_x64_128,
  MurmurHash2 and MurmurHash64A and of xxHash32 (including incremental hashing over random chunks
  and the documented `hash32(long...)` equivalences); `PureJavaCrc32`/`PureJavaCrc32C` against
  `java.util.zip`; the nine `Crc16` variants against a bitwise model with the CRC catalogue's
  parameters (check values of "123456789" asserted first); Blake3's entry points against each
  other (XOF prefixes, keyed and KDF modes, the empty-input vector); `DigestUtils` and `HmacUtils`
  against JCA; `GitIdentifiers` blob and tree ids against Git's object format built from random
  trees (nested paths, executable files, symbolic links, non-BMP names for the tree-sort rule).
- `NetTest` — `URLCodec` against the www-form-urlencoded rules and `java.net.URLEncoder`
  (default and custom safe sets, malformed escapes); `PercentCodec` against RFC 3986 with the
  always-encode and plus-for-space options; `QuotedPrintableCodec` non-strict against rules 1-2,
  strict against rules 1-5 (line length, trailing white space, soft breaks, decodability by an
  independent decoder), and `decodeQuotedPrintable` on arbitrary input; `BCodec` and `QCodec`
  encoded words against RFC 1522 for several charsets, and malformed encoded words.
- `LanguageTest` — `Soundex` (the three preconfigured variants and their H/W/vowel rules),
  `RefinedSoundex` and `ColognePhonetic` against models written from the class documentation;
  shape laws for Metaphone, Double Metaphone, Caverphone 1/2, NYSIIS, Daitch-Mokotoff, Match Rating
  and Beider-Morse (code lengths and alphabets, `isEqual` methods, maxCodeLen prefixes, branching).
- `CodecPinsTest` — one plain JUnit test per recorded bug.

## Bugs

See `bugs.toml`: `Base58.getEncodedLength` divides by zero (1); lenient Base32 turns a dangling
character into a phantom byte (2); `Blake3.doFinalize` restarts the output stream on every call,
so the documented KDF example derives two identical keys (3); strict quoted-printable lines reach
77-78 characters (4); a malformed `rounds=` salt is hashed with the salt `rounds` where libc refuses
(5); `ColognePhonetic`'s context rules see punctuation that step 1 is documented to remove (6);
`Nysiis` never runs its documented step 8, so a doubled letter created by step 6 survives (7).

## Notes

- Documentation discrepancies that are not recorded as bugs because a fix would be a
  documentation change: `Base64`'s class Javadoc says the default line length is 76 while the
  builder and `new Base64()` give 0 (no chunking); `Crc16.maxim()`'s Javadoc says init 0xFFFF
  while the code (correctly, per the catalogue's CRC-16/MAXIM-DOW) uses 0x0000;
  `BeiderMorseEncoder.setConcat` is described as choosing between all encodings joined by `|`
  and the first one, while the flag actually decides whether the words of a multi-word name are
  concatenated before encoding (the reference implementation's meaning) and `|` is emitted either
  way; `ColognePhonetic`'s Javadoc describes collapsing equal consecutive codes before removing
  the 0s ("identical consecutive digits can occur after removing the 0 digits") but the output
  buffer forgets a 0, so a consonant code repeated across a vowel is collapsed ("hoffmann" is
  036, "Dieter" 27) - the class's own tests assert that, so the property treats it as ambiguous.
- libc (libxcrypt) rejects any SHA-crypt salt with characters outside `[./0-9A-Za-z]` after the
  prefix; commons-codec cuts the salt at the first such character (Drepper's original cut only at
  `$`). Only the `rounds=` case is recorded, since there the class's own grammar is violated.
- `QuotedPrintableCodec(true).encode` returns `null` for inputs shorter than 3 bytes; upstream's
  tests assert it, so the property accepts it.
- Whitespace-separated Base45 is rejected (RFC 9285 has no whitespace), `' '` is data; the
  property follows the documents.
- 2026-09-17: base bumped f49b96388c2d → eec585d1e821 (2026-09-17, "Fix Blake3 KDF example and clarify finalization semantics"; 1.23.0-SNAPSHOT); 7 bug(s) still reproduce. 21 tests pass.
- 2026-09-18: base bumped eec585d1e821 → 8b506a1ce5f6 (2026-09-17, "Base32 and Base64 STRICT decoding now require the encoder's canonical alphabet, padding, and line separators, and validate streams through EOF. Use LENIENT to retain permissive decoding."; 1.23.0-SNAPSHOT); 7 bug(s) still reproduce. 21 tests pass.
- 2026-09-18: base bumped 8b506a1ce5f6 → 7bc15f1cb49e (2026-09-18, "Reject oversized Beider-Morse input before language guessing"; 1.23.0-SNAPSHOT); 6 bug(s) still reproduce; fixed upstream: commons-codec/1. 21 tests pass.
