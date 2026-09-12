# jiff

[BurntSushi/jiff](https://github.com/BurntSushi/jiff).

## What is tested

**`crates/jiff/src/civil/date.rs`**
- `prop_checked_add_then_sub`: (no doc comment)
- `prop_checked_sub_then_add`: (no doc comment)
- `prop_since_then_add`: (no doc comment)
- `prop_until_then_sub`: (no doc comment)
- `prop_weekday_matches_chrono`: (no doc comment)
- `prop_iso_week_date_roundtrip`: (no doc comment)

**`crates/jiff/src/civil/datetime.rs`**
- `prop_display_fromstr_roundtrip`: (no doc comment)

**`crates/jiff/src/civil/time.rs`**
- `prop_ordering_same_as_civil_nanosecond`: (no doc comment)
- `prop_checked_add_then_sub`: (no doc comment)
- `prop_wrapping_add_then_sub`: (no doc comment)
- `prop_checked_add_equals_wrapping_add`: (no doc comment)
- `prop_checked_sub_equals_wrapping_sub`: (no doc comment)
- `prop_until_then_add`: (no doc comment)
- `prop_until_then_sub`: (no doc comment)
- `prop_since_then_add`: (no doc comment)
- `prop_since_then_sub`: (no doc comment)
- `prop_until_is_since_negated`: (no doc comment)

**`crates/jiff/src/fmt/rfc2822.rs`**
- `prop_print_zoned_then_parse_roundtrip`: (no doc comment)

**`crates/jiff/src/fmt/strtime/mod.rs`**
- `prop_parse_never_panics`: (no doc comment)
- `prop_format_then_strptime_datetime_roundtrip`: (no doc comment)

**`crates/jiff/src/fmt/temporal/mod.rs`**
- `prop_parse_arbitrary_input_never_panics`: (no doc comment)

**`crates/jiff/src/span.rs`**
- `prop_roundtrip_span_nanoseconds`: (no doc comment)
- `prop_display_fromstr_roundtrip_fieldwise`: (no doc comment)

**`crates/jiff/src/timestamp.rs`**
- `prop_unix_seconds_roundtrip`: (no doc comment)
- `prop_nanos_roundtrip_unix`: (no doc comment)
- `prop_timestamp_constant_and_new_are_same1`: (no doc comment)
- `prop_timestamp_constant_and_new_are_same2`: (no doc comment)
- `prop_display_fromstr_roundtrip`: (no doc comment)
- `prop_ordering_same_as_nanosecond`: (no doc comment)

**`crates/jiff/src/zoned.rs`**
- `prop_display_fromstr_roundtrip`: (no doc comment)
- `prop_until_then_sub`: (no doc comment)
- `prop_add_time_span_then_sub`: (no doc comment)

## Oracles

## Not tested

Note: many of upstream's own tests and doc-tests need legacy time-zone names (`US/Eastern`)
from the system tz database (`tzdata-legacy` on Ubuntu); without it they fail and `tools/zoo`
reports them as UPSTREAM.

## History

- 2026-07-19: predecessor base commit `7311a6ac67cf` (0.2.34).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/jiff.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1 (composites by reference; `.print_as_debug()` on draws of jiff types with `use hegel::Generator` in each test module).
