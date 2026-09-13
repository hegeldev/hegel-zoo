# httpdate

[pyfisch/httpdate](https://github.com/pyfisch/httpdate): HTTP date parsing and formatting
(`parse_http_date`, `fmt_http_date`, `HttpDate`) — IMF-fixdate `Sun, 06 Nov 1994 08:49:37 GMT`
out, and IMF-fixdate, RFC 850 (`Sunday, 06-Nov-94 …`) and asctime (`Sun Nov  6 08:49:37 1994`)
in — with its own civil-calendar arithmetic (musl's `__secs_to_tm` cycle counting one way, a
leap-year count the other) for years 1970..=9999.

Written in the zoo (not imported from the predecessor). No features. The crate's unit tests run
alongside `tests/hegel.rs`.

## What is tested

**`tests/hegel.rs`** — instants are drawn over the whole range with a bias to 1970, 9999, leap
days, century boundaries and day boundaries ± a few seconds; `jiff` is the oracle.
- `instants_print_and_parse_like_jiff`: `HttpDate::from(SystemTime)` prints what jiff's
  `strftime("%a, %d %b %Y %H:%M:%S GMT")` prints (nanoseconds floored), converts back to the
  floored instant, and the three spellings of the instant (IMF-fixdate; RFC 850 rendered as
  `%A, %d-%b-%y …` — accepted as the drawn instant for 1970..=2069, otherwise as the
  1970..=2069 year with the same two digits exactly when that year has the same weekday and,
  for 29 February, is leap; asctime `%a %b %e %H:%M:%S %Y`) parse to it; jiff's RFC 2822 parser
  reads the IMF-fixdate to the same second.
- `imf_fixdate_texts_are_accepted_exactly_when_canonical`: surrounding whitespace is trimmed;
  a mutated IMF-fixdate (one byte replaced, deleted or inserted, a non-ASCII character, two
  positions swapped) is accepted only if it is exactly the canonical rendering of its value
  (checked against jiff's rendering), and a rejected 29-byte text that jiff reads as RFC 2822 is
  never that canonical rendering; the error's `Display` and `io::Error` conversion.
- `component_texts_are_validated`: texts built from arbitrary components (years 0..=9999,
  day 1..=31 of any month, hour/minute/second up to 99, right or arbitrary weekday) in the three
  layouts are accepted exactly when the named year is 1970..=9999, the day exists, the weekday
  is right and the time fields are in range, and then name jiff's instant.
- `ordering_equality_and_hashing_follow_the_instant`: `Ord`/`PartialOrd`/`Eq`/`Hash` of
  `HttpDate` are those of the floored instant; sort and `HashSet` sizes against the model;
  `Display` is injective on instants and re-parses.
- `the_documented_range_is_exact`: `fmt_http_date` panics before the epoch and from
  10000-01-01 on (the struct documents 1970..=9999); `Fri, 31 Dec 9999 23:59:59 GMT` is the
  last value; 1969 and 10000 texts are rejected.

## Oracles

`jiff` 0.2 (`civil::DateTime` arithmetic from the epoch — jiff's `Timestamp` stops at
9999-12-30T22:00Z, two days short of the crate — `strftime` with `%a %A %d %e %b %y %Y %H %M %S`,
the RFC 2822 parser), the RFC 7231 §7.1.1.1 layouts, the crate's documented ranges.

## Not tested

Case-insensitive or otherwise lenient input (open upstream #15 asks for it; the crate is
strict by design), non-GMT zone names (#16, closed as out of scope), `Set-Cookie` dates with
four-digit RFC 850 years (#9), sub-second precision (dropped by design).

## History

- 2026-09-13: written in the zoo against `53df52094835` (2024-12-22, 1.0.3) with hegeltest
  0.44.1 and jiff 0.2. The crate (580 lines) was read first — nothing by eye — and **nothing
  found by the tests**: clean at 100 + 3 × 1 000 + 10 000 cases. Test defect on the way: jiff's
  `Timestamp` range ends two days before the crate's, so the oracle uses `civil::DateTime`
  arithmetic from the epoch.
