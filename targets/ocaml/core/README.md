# core

Jane Street's `core` beyond Base: dates, times and spans, `Percent`, `Bigbuffer`, and the
imperative and functional containers. Built from the `oxcaml` branch, the newest code that builds.

## What is tested

- `date_matches_python`, `date_weekdays_match_python`: `add_days`, `diff`, `day_of_week`, ISO
  weeks, `add_months` clamping, `diff_weekdays` and the weekday rounding functions against
  Python's `datetime` (from 1753, as documented).
- `date_of_string_formats`, `date_printers_roundtrip`, `date_of_string_rejects_invalid_days`:
  every documented input format, the printers read back, invalid days rejected.
- `time_ns_offset_matches_python`, `time_ns_utc_roundtrip`: `of_string_with_utc_offset` against
  Python's `fromisoformat`; the UTC printers read back.
- `ofday_of_string_model`, `ofday_iso8601_model`, `ofday_roundtrip`, `ofday_arithmetic`: 12h and
  24h forms, nanosecond rounding, `add`, `diff`, `small_diff`.
- `span_ns_of_string_model`, `span_ns_rejects_malformed`, `span_ns_roundtrip`, `span_ns_parts`,
  `span_ns_short_string`, `span_float_roundtrip`, `span_float_short_string`.
- `percent_roundtrip`, `percent_to_string_six_digits`, `percent_of_string_model`.
- `bigbuffer_add_substitute_*` against `Stdlib.Buffer.add_substitute`; `bigbuffer_machine`
  against `Buffer`.
- State machines against list models: `Doubly_linked`, `Hash_queue`, `Deque` (with its stable
  indices), `Fdeque`, `Fqueue`, `Union_find`, `Bag`.

## Not tested

Time zones other than UTC, `Time_float` times, `Byte_units`, `Bigstring` (from base_bigstring),
`Command`, bin_prot, and what Base provides.

## History

- 2026-10-09: created at 62384b1e (v0.18~preview.130.106+341), hegel-ocaml 0.26.1; 7 bugs.
