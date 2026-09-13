# compact_str

[ParkMyCar/compact_str](https://github.com/ParkMyCar/compact_str): the `compact_str` crate (0.10,
main), a `String` replacement that keeps up to 24 bytes inline (`size_of::<String>()`), re-uses a
`String`'s buffer above that, and has a `&'static str` variant from `const_new`.

Written in the zoo (not imported from the predecessor). The crate is the `compact_str/` member of
its repository (the workspace excludes it); only its unit tests (`--lib`) and `tests/hegel.rs` are
run — the crate has no other integration tests, its own fuzzer lives in `fuzz/`.

## What is tested

**`tests/hegel.rs`** — the oracle is `std`: a `String` mirror of every edit, `str`'s case
conversions, decoders and formatting; plus the crate's documented storage contract.
- `edits_match_the_string_model`: a `CompactString` created one of fourteen ways (`new`, `try_new`,
  `From<String>` with spare capacity, `from_string_buffer`, `const_new` of statics below/at/above
  the inline limit, `with_capacity`, `Default`, `FromIterator<char>`, `from_utf8`, `FromStr`,
  `From<Box<str>>`, `From<Cow>` both ways, `From<&String>`) and edited by an arbitrary script
  (`push`, `push_str`, `pop`, `remove`, `insert`, `insert_str`, `truncate`, `clear`, `split_off`,
  `drain` in every range form and consumed every way, `replace_range` in every range form,
  `retain`, `reserve`, `shrink_to`, `shrink_to_fit`, `clone`/`clone_from`, `repeat`,
  `into_string` and back, `from_string_buffer`, `as_mut_str`, `fmt::Write`, `Add`/`AddAssign`,
  every `Extend`) holds the same text as the `String` edited alike. After every step: `as_str`,
  `len`, `as_bytes`, `Deref`, `Display`, `Debug` agree; `capacity ≥ len`; an inline string's
  capacity is exactly 24; a static string's capacity is its length and it is not heap allocated;
  growth follows `reserve`'s rule (no change while it fits, inline if the need fits inline, heap
  otherwise); shortening never touches the capacity (a static `split_off` leaves the cut as
  capacity); `shrink_to` goes inline when the result fits, otherwise to exactly `max(len, min)`
  clamped at the 32-byte minimum heap allocation and never grows; short strings are inline after
  creation, `clone`, `shrink_to_fit`, `repeat` and `From<String>`; `From<String>`,
  `From<Box<str>>`, `from_string_buffer` and `into_string` hand the same buffer (pointer and
  capacity) back and forth; `from_string_buffer` never inlines.
- `out_of_bounds_and_split_chars_are_refused`: every position-taking method panics on an index
  inside a multi-byte char or past the end (and on a reversed range) and leaves the string intact;
  the empty edge cases (`drain(n..n)`, `replace_range(n..n, "")`, `truncate(n + 1)`,
  `insert_str(n, "")`) are no-ops; `try_reserve(usize::MAX)` on a non-empty string is an error.
- `huge_capacities_are_reserve_errors`: for 2^40 ≤ n ≤ 2^56 − 202, `try_with_capacity(n)` and
  `try_reserve(n)` are `Err(ReserveError)`, `with_capacity`, `reserve` and `repeat` panic, and
  the string is untouched.
- `capacities_beyond_56_bits_are_reserve_errors`: the same for n ≥ 2^56 − 1. KNOWN FAILURE
  compact_str/1.
- `comparisons_and_hash_match_str`: `==`, `Ord`, every `PartialEq` impl in both directions
  (`str`, `&str`, `&&str`, `String`, `&String`, `Cow`, `&Cow`, `&CompactString`), `Hash` equal to
  `str`'s (so `HashMap<CompactString, _>` lookups by `&str` work), `BTreeSet` order, `AsRef`/
  `Borrow` views.
- `conversions_round_trip`: into `String`, `Cow` (borrowed from a reference), `Arc<str>`,
  `Rc<str>`, `Box<str>`, `Vec<u8>`, `OsString`, `PathBuf`, `Box<dyn Error>`; `FromIterator` and
  `Extend` in every item type (`&str`, `String`, `Box<str>`, `Cow`, `CompactString`, `char`,
  `&char`), `String`/`Cow` collecting and extending from `CompactString`s; `concat_compact` and
  `join_compact` against `concat`/`join`; `ToCompactString` for strings.
- `case_conversions_match_str`: `to_lowercase`, `to_uppercase`, `from_str_to_lowercase`,
  `from_str_to_uppercase`, `to_ascii_*` equal `str`'s, on an ASCII run (so the word-at-a-time
  ASCII fast path hands over to the char loop) followed by case-interesting text (final sigma,
  ß, İ, ligatures) or arbitrary chars.
- `to_compact_string_matches_display`: every integer and `NonZero` type (plus `MIN`/`MAX`/0),
  `bool`, `char`, a `Display` type through the generic path, a `Display` that fails (`Err(Fmt)`
  from `try_to_compact_string`, a panic from `to_compact_string`, also after partial output);
  `f32`/`f64` round-trip through `parse` bit for bit (the crate uses `zmij`, whose formatting
  is documented to differ from `std`'s at times, so `Display` equality is not asserted).
- `decoding_matches_std`: `from_utf8` agrees with `str::from_utf8` (`valid_up_to`, `error_len`),
  `from_utf8_lossy` with `String::from_utf8_lossy` on text with random bytes spliced in;
  `from_utf16`/`from_utf16_lossy` with `char::decode_utf16`/`String::from_utf16_lossy` on code
  units with surrogates spliced in; `from_utf16le`/`be` and their `_lossy` forms on the same data
  as bytes, aligned and misaligned (the crate has two code paths), with an odd trailing byte (an
  error; one `U+FFFD` in the lossy form).

Text is drawn from an alphabet of ASCII in both cases, ß, İ, ﬁ, Σ/σ/ς, 2-, 3- and 4-byte chars, NUL
and newline, up to 40 chars (160 bytes), so the inline limit (24) and the minimum heap capacity
(32) are crossed constantly.

## Oracles

`std`: `String` (edits, `Drain`, capacities where `String` documents the same), `str` (case
conversion, `from_utf8`, hashing, ordering), `char::decode_utf16`, `Display`/`parse`. The storage
contract comes from the crate's documentation (`with_capacity`, `capacity`, `reserve`,
`shrink_to`, `truncate`, `split_off`, `drain`, `from_string_buffer`, `From<String>`, `const_new`,
`as_static_str`) and its own tests' `assert_allocated_properly`.

## Not tested

The optional integrations (`serde`, `bytes`, `smallvec`, `arbitrary`, `proptest`, `quickcheck`,
`rkyv`, `borsh`, `diesel`, `sqlx`, `zeroize`, …), `no_std`, the `unsafe` byte-level API
(`as_mut_bytes`, `spare_capacity_mut`, `set_len`, `from_utf8_unchecked`), the exact float text
(round trip only), 32-bit targets (where the capacity can live on the heap), out-of-memory. Not
asserted: that a case conversion whose result is shorter than its input (`ﬀ` → `FF`) inlines a
24-byte result — it is sized from the input and stays on the heap; nothing documents otherwise.

## History

- 2026-09-13: written in the zoo against `9696af7f7a94` (2026-07-13, "perf: optimize several parts
  of the creation code path (#494)"; 0.10.0) with hegeltest 0.44.1. Two test defects fixed on the
  way (a 39-digit `u128` is not inline; `drain(a..=b-1)` with `a == b` falls back to the whole
  range). **compact_str/1** on the first run: `try_with_capacity(usize::MAX)` panics on a
  `debug_assert!` in `Capacity::new` instead of returning `ReserveError` (release builds reach
  `unreachable_unchecked` first, undefined behaviour) — reported upstream the day after the pinned
  commit as [#495](https://github.com/ParkMyCar/compact_str/issues/495) with an open partial fix
  (#496); found here independently. Clean otherwise at 3 × 1 000 and 1 × 10 000 cases.
